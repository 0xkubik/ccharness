#!/usr/bin/env bash
# autopilot — Stop hook (the meta-loop's "hard muscle").
#
# autopilot is a WRAPPER over semipilot: it walks the roadmap milestone by
# milestone by arming a fresh semipilot for each. This hook re-feeds the
# META-STEP only in the GAP between milestones — while autopilot is active AND
# no semipilot is in flight. While a semipilot is active, THIS hook yields and
# semipilot-stop.sh drives, so exactly one hook blocks per turn.
#
# Fail CLOSED while active. Allow-the-stop paths (exit 0, no stdout):
#   1. no autopilot state file
#   2. autopilot active == false          (cancelled, or hard-stopped on a dependent block)
#   3. a DIFFERENT session owns autopilot
#   4. a semipilot is ACTIVE for this session  (yield; semipilot-stop.sh drives)
set -u

STATE_FILE=".claude/ccharness/autopilot/state.json"
SEMI_FILE=".claude/ccharness/semipilot/state.json"
HOOK_INPUT="$(cat 2>/dev/null || true)"

[ -f "$STATE_FILE" ] || exit 0

HOOK_SESSION=""; STATE_SESSION=""; STATE_ACTIVE=""; CUR="?"; SEMI_ACTIVE=""
if command -v jq >/dev/null 2>&1; then
  HOOK_SESSION="$(printf '%s' "$HOOK_INPUT" | jq -r '.session_id // ""' 2>/dev/null || true)"
  STATE_SESSION="$(jq -r '.session_id // ""'   "$STATE_FILE" 2>/dev/null || true)"
  STATE_ACTIVE="$(jq -r '.active'              "$STATE_FILE" 2>/dev/null || true)"
  CUR="$(jq -r '.current_milestone // "?"'     "$STATE_FILE" 2>/dev/null || echo '?')"
  [ -f "$SEMI_FILE" ] && SEMI_ACTIVE="$(jq -r '.active' "$SEMI_FILE" 2>/dev/null || true)"
fi

# jq-free fallbacks for the two CRITICAL flags (jq absent, coreutils present):
# STATE_ACTIVE=false lets a hard-stop/cancel release; SEMI_ACTIVE=true preserves the
# partition (autopilot must YIELD while a semipilot is in flight) instead of double-blocking.
if [ -z "$STATE_ACTIVE" ] && command -v grep >/dev/null 2>&1; then
  grep -Eq '"active"[[:space:]]*:[[:space:]]*false' "$STATE_FILE" && STATE_ACTIVE=false
fi
if [ -z "$SEMI_ACTIVE" ] && [ -f "$SEMI_FILE" ] && command -v grep >/dev/null 2>&1; then
  grep -Eq '"active"[[:space:]]*:[[:space:]]*true' "$SEMI_FILE" && SEMI_ACTIVE=true
fi

# Exit #2 — autopilot cancelled or hard-stopped.
[ "$STATE_ACTIVE" = "false" ] && exit 0

# Exit #3 — a different session owns the meta-loop.
if [ -n "$STATE_SESSION" ] && [ -n "$HOOK_SESSION" ] && [ "$STATE_SESSION" != "$HOOK_SESSION" ]; then
  exit 0
fi

# Exit #4 — a semipilot is in flight → yield; its hook drives this turn.
# NOTE: keys on the semipilot active flag alone (assumes ONE autonomous loop per
# session/checkout). A semipilot active for a DIFFERENT session in this repo would
# also make us yield — acceptable under the one-loop-per-session assumption.
[ "$SEMI_ACTIVE" = "true" ] && exit 0

# --- autopilot active AND no semipilot in flight → RE-FEED the META-STEP. Fail closed. ---
REFEED="$(cat <<'PROMPT'
🛰️ autopilot meta-loop is ACTIVE and a semipilot just ended — run ONE meta-step:
1. Read .claude/ccharness/semipilot/state.json (its `outcome`), .claude/ccharness/autopilot/state.json, autopilot/blocked.jsonl (parked milestones), and .claude/ccharness/roadmap.md.
2. outcome == "achieved": the milestone is now [x]. Set current_retries=0. next = first unchecked milestone NOT in autopilot/blocked.jsonl. next exists → set current_milestone=next and ARM a fresh semipilot on it (write .claude/ccharness/semipilot/state.json active:true, atomic). none → roadmap complete → CHEAP IDLE: log "roadmap-complete-idle", do NOT stop, END THE TURN.
3. outcome == "gave-up" | "capped":
   - current_retries == 0 → RETRY ONCE: set current_retries=1, re-arm a fresh semipilot on the SAME milestone.
   - current_retries == 1 → judge the roadmap: does the next unchecked milestone DEPEND on the stuck one? INDEPENDENT → park it (append to autopilot/blocked.jsonl), reset current_retries=0, advance to the next non-parked unchecked milestone, arm a fresh semipilot. DEPENDENT → HARD STOP: set autopilot active:false with outcome:"blocked", report the stuck milestone + parked queue, END THE TURN.
4. Append one line to autopilot/log.jsonl {milestone, action, ts} (atomic) and END THE TURN.
Never declare autopilot "done" except the HARD STOP in 3. An exhausted roadmap is a cheap idle, not a stop. /autopilot-cancel also stops it.
PROMPT
)"

if command -v jq >/dev/null 2>&1; then
  jq -n \
    --arg r "$REFEED" \
    --arg m "🛰️ autopilot meta-step @ ${CUR} (semipilot ended; arming next / handling give-up)" \
    '{decision:"block", reason:$r, systemMessage:$m}'
else
  printf '%s' '{"decision":"block","reason":"autopilot meta-loop active and a semipilot ended — run one meta-step: read semipilot outcome + roadmap, then advance / retry-once / dependency-judge (independent->park+advance, dependent->hard-stop). Cheap-idle if roadmap complete. /autopilot-cancel to stop."}'
fi

exit 0
