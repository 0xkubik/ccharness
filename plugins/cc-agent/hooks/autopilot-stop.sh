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

# Run-mode flags. Detected with grep (jq-independent) so they ride along with or without jq.
#   ultracode → force max parallelism this cycle (Workflow + subagents + worktrees, mandatory).
#   spend     → burn the subscription limit: never self-stop; generate work instead of idling.
ULTRA=""; SPEND=""
if command -v grep >/dev/null 2>&1; then
  grep -Eq '"ultracode"[[:space:]]*:[[:space:]]*true' "$STATE_FILE" && ULTRA=1
  grep -Eq '"spend"[[:space:]]*:[[:space:]]*true'     "$STATE_FILE" && SPEND=1
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

# Flag riders, appended to the base meta-step. ULTRACODE forces fan-out; SPEND MODE
# overrides the two soft-idle/stop branches above so the loop keeps burning the limit.
if [ -n "$ULTRA" ]; then
  REFEED="$REFEED
ULTRACODE (mandatory this run): push parallelism to the max. The build inside each milestone MUST fan out — author a Workflow and/or dispatch parallel subagents rather than working inline, isolate parallel file-mutating work in git worktrees, and verify findings adversarially. These tools are always permitted; --ultracode makes them required, not optional. When you arm the next semipilot, set ultracode:true on its state.json so the fan-out carries into that milestone's build."
fi
if [ -n "$SPEND" ]; then
  REFEED="$REFEED
SPEND MODE (burn the subscription limit): the ONLY stops are /autopilot-cancel or the subscription limit itself cutting the session. Two overrides to the meta-step above: (a) an exhausted roadmap is NOT cheap idle — GENERATE fresh work: re-survey with what-to-do for new improvements and extend the roadmap via find-goal, then keep building; (b) a hard dependency-block does NOT stop — park the blocker and mine other workable milestones instead. Honesty guard: route every generated direction through how-to-do (it may reject weak ones) and keep commits LOCAL; if work-gen is genuinely dry, fall back to a LIGHT idle — never manufacture churn to fill time."
fi

if command -v jq >/dev/null 2>&1; then
  jq -n \
    --arg r "$REFEED" \
    --arg m "🛰️ autopilot meta-step @ ${CUR}$([ -n "$ULTRA" ] && printf ' [ultracode]')$([ -n "$SPEND" ] && printf ' [spend]') (semipilot ended; arming next / handling give-up)" \
    '{decision:"block", reason:$r, systemMessage:$m}'
else
  FALLBACK_REASON='autopilot meta-loop active and a semipilot ended — run one meta-step: read semipilot outcome + roadmap, then advance / retry-once / dependency-judge (independent->park+advance, dependent->hard-stop). Cheap-idle if roadmap complete. /autopilot-cancel to stop.'
  [ -n "$ULTRA" ] && FALLBACK_REASON="$FALLBACK_REASON ULTRACODE: fan out via Workflow + parallel subagents + git worktrees (mandatory)."
  [ -n "$SPEND" ] && FALLBACK_REASON="$FALLBACK_REASON SPEND MODE: never self-stop — generate fresh work instead of idling, park blockers instead of hard-stopping; only /autopilot-cancel or the subscription limit stops it."
  printf '%s' "{\"decision\":\"block\",\"reason\":\"$FALLBACK_REASON\"}"
fi

exit 0
