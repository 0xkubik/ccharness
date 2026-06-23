#!/usr/bin/env bash
# ccharness autopilot — Stop hook (the "hard muscle").
#
# While the autopilot state file is ACTIVE for THIS session, this hook re-feeds
# the autopilot prompt on every Stop so the model cannot exit on its own. It is
# the ONLY component that delivers "programmatically incapable of self-stop".
#
# Fail CLOSED: any anomaly encountered while the loop is active re-feeds anyway.
# The ONLY paths that allow the stop (exit 0, no stdout):
#   1. no state file              — autopilot not armed / cancelled by rm
#   2. state.active == false      — cancelled via /autopilot-cancel
#   3. a DIFFERENT session owns it — don't block other sessions in this repo
#
# Fires on `Stop` (main-agent stop) only. The funnel's subagent fan-outs raise
# `SubagentStop`, a different event, so this never fires mid-funnel.
#
# Contract: print a JSON `{"decision":"block","reason":...}` object on stdout to
# block the stop and re-feed `reason`; print nothing and exit 0 to allow it.

set -u

STATE_FILE=".claude/ccharness/autopilot/state.json"

# Read the hook input (JSON on stdin).
HOOK_INPUT="$(cat 2>/dev/null || true)"

# Exit #1 — no state file: autopilot not armed → allow the stop.
[ -f "$STATE_FILE" ] || exit 0

# Parse what we can. Anything unparseable stays empty and is handled fail-closed.
HOOK_SESSION=""
STATE_SESSION=""
STATE_ACTIVE=""
CYCLE="?"
if command -v jq >/dev/null 2>&1; then
  HOOK_SESSION="$(printf '%s' "$HOOK_INPUT" | jq -r '.session_id // ""' 2>/dev/null || true)"
  STATE_SESSION="$(jq -r '.session_id // ""'   "$STATE_FILE" 2>/dev/null || true)"
  STATE_ACTIVE="$(jq -r '.active'              "$STATE_FILE" 2>/dev/null || true)"
  CYCLE="$(jq -r '.cycle // "?"'               "$STATE_FILE" 2>/dev/null || echo '?')"
fi

# Exit #2 — explicitly cancelled (active:false) → allow the stop.
[ "$STATE_ACTIVE" = "false" ] && exit 0

# Exit #3 — a different session owns the loop → don't block this one.
# Enforced ONLY when both ids parsed cleanly; otherwise we fail closed (re-feed)
# rather than risk a silent self-stop of the owning session.
if [ -n "$STATE_SESSION" ] && [ -n "$HOOK_SESSION" ] && [ "$STATE_SESSION" != "$HOOK_SESSION" ]; then
  exit 0
fi

# --- ACTIVE for this session (or present-but-unparseable) → RE-FEED. Fail closed. ---
REFEED="$(cat <<'PROMPT'
🔄 ccharness autopilot is ACTIVE — continue the loop. Do NOT stop. Only the user stops you, via /autopilot-cancel.

Resume the `autopilot` skill for the next cycle:
1. Read .claude/ccharness/autopilot/state.json and .claude/ccharness/autopilot/blocked.jsonl.
2. If the LAST cycle ended by handing back to a human — implement-it asked after slap fired twice, refused an unbuildable/forked task, or point-it stopped to wait for a pick — then APPEND that task to blocked.jsonl (one JSON line: {cycle, direction, reason, slug, ts}) and START A NEW CYCLE from point-it on the next-best direction NOT already in blocked.jsonl. Do not retry the blocked task.
3. Otherwise continue the funnel where it left off (point-it -> grill-it -> implement-it -> local commit), then re-survey.
4. Run exactly ONE cycle this turn: append the outcome to log.jsonl, bump `cycle` in state.json via an atomic write (temp file + mv), then end the turn.

Never declare the autopilot "done". An exhausted product (empty menu, HEAD unchanged since last survey) means a cheap idle cycle — not a stop.
PROMPT
)"

if command -v jq >/dev/null 2>&1; then
  jq -n \
    --arg r "$REFEED" \
    --arg m "🔄 autopilot cycle ${CYCLE} -> continuing (stop blocked; /autopilot-cancel to stop)" \
    '{decision:"block", reason:$r, systemMessage:$m}'
else
  # jq unavailable — still re-feed (fail closed) with minimal single-line JSON.
  printf '%s' '{"decision":"block","reason":"ccharness autopilot is active — continue the loop: read .claude/ccharness/autopilot/state.json and blocked.jsonl, run exactly one funnel cycle, do not stop. Only /autopilot-cancel stops you."}'
fi

exit 0
