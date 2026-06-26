#!/usr/bin/env bash
# musician — observe hook (PreToolUse / PostToolUse). A read-only witness: while a musician is
# ACTIVE for THIS session, it appends one human-readable line per tool call to the run's live log,
# so the work is visible from outside the agent's own window (which instrument it called, and
# roughly what it is doing). It is NOT part of the loop's control — it NEVER blocks or alters a
# tool: it always exits 0 and writes nothing to stdout. Logging is best-effort; if it can't parse
# the input it stays silent rather than interfere.
#
# Arg 1: "pre" (about to run a tool) | "post" (a tool just finished).
set -u

MODE="${1:-pre}"
STATE_FILE=".claude/ccharness/musician/state.json"
LIVE_LOG=".claude/ccharness/musician/live.log"

HOOK_INPUT="$(cat 2>/dev/null || true)"
[ -f "$STATE_FILE" ] || exit 0

# Witness only when a musician is ACTIVE and owned by THIS session. Parsing needs jq; without it,
# logging is simply skipped (it is observability, never a safety gate — the Stop hook is the gate).
command -v jq >/dev/null 2>&1 || exit 0

TOOL="$(printf '%s' "$HOOK_INPUT" | jq -r '.tool_name // ""' 2>/dev/null || true)"
[ -n "$TOOL" ] || exit 0
[ "$(jq -r '.active' "$STATE_FILE" 2>/dev/null)" = "true" ] || exit 0

HOOK_SESSION="$(printf '%s' "$HOOK_INPUT" | jq -r '.session_id // ""' 2>/dev/null || true)"
STATE_SESSION="$(jq -r '.session_id // ""' "$STATE_FILE" 2>/dev/null || true)"
if [ -n "$STATE_SESSION" ] && [ -n "$HOOK_SESSION" ] && [ "$STATE_SESSION" != "$HOOK_SESSION" ]; then
  exit 0
fi

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
