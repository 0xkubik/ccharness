#!/usr/bin/env bash
# musician — observe hook (PreToolUse / PostToolUse). A read-only witness: while a musician is
# ACTIVE for THIS session, it appends one human-readable line per tool call to that run's live.log,
# so the work is visible from outside the agent's own window (which instrument it called, and
# roughly what it is doing). It is NOT part of the loop's control — it NEVER blocks or alters a
# tool: it always exits 0 and writes nothing to stdout. Logging is best-effort; if it can't parse
# the input it stays silent rather than interfere.
#
# Each run lives in runs/<run-id>/; we resolve THIS session's run from the session_id on stdin via
# the per-session pointer (see musician-resolve.sh) and write into that run's folder.
#
# Arg 1: "pre" (about to run a tool) | "post" (a tool just finished).
set -u

MODE="${1:-pre}"
source "${BASH_SOURCE[0]%/*}/musician-resolve.sh"
HOOK_INPUT="$(cat 2>/dev/null || true)"

# Parsing the tool args needs jq; without it, observability is simply skipped (never a safety gate).
command -v jq >/dev/null 2>&1 || exit 0

TOOL="$(printf '%s' "$HOOK_INPUT" | jq -r '.tool_name // ""' 2>/dev/null || true)"
[ -n "$TOOL" ] || exit 0

SID="$(mus_session_from_stdin "$HOOK_INPUT")"
RUN_DIR="$(mus_run_dir "$SID")"
[ -n "$RUN_DIR" ] || exit 0
STATE_FILE="$RUN_DIR/state.json"
LIVE_LOG="$RUN_DIR/live.log"

[ "$(jq -r '.active' "$STATE_FILE" 2>/dev/null)" = "true" ] || exit 0
CYCLE="$(jq -r '.cycle // "?"' "$STATE_FILE" 2>/dev/null || echo '?')"

# Rough human action derived from the tool and its arguments.
case "$TOOL" in
  Skill)
    s="$(printf '%s' "$HOOK_INPUT" | jq -r '.tool_input.skill // .tool_input.name // ""' 2>/dev/null)"
    LABEL="▶ ${s:-skill}" ;;
  Bash)
    c="$(printf '%s' "$HOOK_INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null | tr '\n' ' ' | cut -c1-60)"
    LABEL="\$ ${c}" ;;
  Edit|Write|NotebookEdit)
    f="$(printf '%s' "$HOOK_INPUT" | jq -r '.tool_input.file_path // ""' 2>/dev/null)"
    LABEL="✎ $(basename "${f:-?}")" ;;
  Read)
    f="$(printf '%s' "$HOOK_INPUT" | jq -r '.tool_input.file_path // ""' 2>/dev/null)"
    LABEL="👁 $(basename "${f:-?}")" ;;
  Task|Agent)
    d="$(printf '%s' "$HOOK_INPUT" | jq -r '.tool_input.description // .tool_input.subagent_type // ""' 2>/dev/null)"
    LABEL="⇒ subagent: ${d:-task}" ;;
  *)
    LABEL="$TOOL" ;;
esac

TS="$(date '+%H:%M:%S' 2>/dev/null || echo '--:--:--')"

if [ "$MODE" = "post" ]; then
  # Light completion tick — only for the heavy, slow instruments, to avoid doubling the feed.
  case "$TOOL" in
    Skill|Task|Agent|Bash)
      printf '%s  cycle %s   ✓ %s\n' "$TS" "$CYCLE" "$LABEL" >> "$LIVE_LOG" 2>/dev/null || true ;;
  esac
  exit 0
fi

printf '%s  cycle %s   %s\n' "$TS" "$CYCLE" "$LABEL" >> "$LIVE_LOG" 2>/dev/null || true
exit 0
