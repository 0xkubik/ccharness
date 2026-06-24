#!/usr/bin/env bash
# semipilot — Stop hook (the bounded loop's "hard muscle").
#
# While the semipilot state file is ACTIVE for THIS session, re-feed the
# semipilot prompt on every Stop so the bounded loop runs one cycle per turn.
# Unlike autopilot, semipilot ENDS ON ITS OWN: the model flips active:false
# when the milestone is achieved OR it gives up, and THEN this hook (Exit #2)
# allows the stop. This hook only prevents an accidental mid-milestone stop.
#
# Fail CLOSED while active. Allow-the-stop paths (exit 0, no stdout):
#   1. no state file
#   2. state.active == false        (achieved / gave-up / capped / cancelled)
#   3. a DIFFERENT session owns it
set -u

STATE_FILE=".claude/ccharness/semipilot/state.json"
HOOK_INPUT="$(cat 2>/dev/null || true)"

[ -f "$STATE_FILE" ] || exit 0

HOOK_SESSION=""; STATE_SESSION=""; STATE_ACTIVE=""; CYCLE="?"; TARGET="?"
# If stdin or jq is absent, HOOK_SESSION/STATE_* stay empty → the active==false
# and different-session guards below are skipped → we fall through and RE-FEED (fail closed).
if command -v jq >/dev/null 2>&1; then
  HOOK_SESSION="$(printf '%s' "$HOOK_INPUT" | jq -r '.session_id // ""' 2>/dev/null || true)"
  STATE_SESSION="$(jq -r '.session_id // ""'   "$STATE_FILE" 2>/dev/null || true)"
  STATE_ACTIVE="$(jq -r '.active'              "$STATE_FILE" 2>/dev/null || true)"
  CYCLE="$(jq -r '.cycle // "?"'               "$STATE_FILE" 2>/dev/null || echo '?')"
  TARGET="$(jq -r '.target_milestone // "?"'   "$STATE_FILE" 2>/dev/null || echo '?')"
fi

# jq-free fallback for the critical active flag (jq absent, coreutils present):
# without this the achieved/gave-up release (active:false) is invisible and the loop can't self-stop.
if [ -z "$STATE_ACTIVE" ] && command -v grep >/dev/null 2>&1; then
  grep -Eq '"active"[[:space:]]*:[[:space:]]*false' "$STATE_FILE" && STATE_ACTIVE=false
fi

# ultracode flag — grep-detected (jq-independent). Forces max parallelism in the build step.
# (spend is autopilot-only — it lives in cc-agent for --spend-session and in cc-maestro for weekly.)
ULTRA=""
if command -v grep >/dev/null 2>&1; then
  grep -Eq '"ultracode"[[:space:]]*:[[:space:]]*true' "$STATE_FILE" && ULTRA=1
fi

# Exit #2 — milestone achieved / gave up / cancelled.
[ "$STATE_ACTIVE" = "false" ] && exit 0

# Exit #3 — a different session owns the loop.
if [ -n "$STATE_SESSION" ] && [ -n "$HOOK_SESSION" ] && [ "$STATE_SESSION" != "$HOOK_SESSION" ]; then
  exit 0
fi

# --- ACTIVE for this session (or present-but-unparseable) → RE-FEED. Fail closed. ---
REFEED="$(cat <<'PROMPT'
🎯 semipilot is ACTIVE — continue the bounded loop for THIS milestone. Run exactly ONE cycle:
1. Read .claude/ccharness/semipilot/state.json + blocked.jsonl.
2. DONE-CHECK FIRST: survey "now" and judge it against state.done_when. If MET → mark the milestone [x] in roadmap.md, set active:false (atomic temp+mv) with outcome:"achieved", append a final log.jsonl line, report, END THE TURN.
3. GIVE-UP CHECK: if no_progress_streak >= max_no_progress OR cycle >= max_cycles → set active:false with outcome:"gave-up" or "capped", report the blocked queue, END THE TURN.
4. Otherwise run ONE funnel cycle SCOPED to the target milestone: cc-tools:what-to-do (menu as DATA, NO AskUserQuestion) → keep only directions whose `advances` == target milestone and not in blocked.jsonl → auto-pick the top → cc-tools:how-to-do → cc-tools:do → LOCAL commit. Update no_progress_streak (reset on real progress; ++ on blocked/idle/no-movement; a handback from do appends to blocked.jsonl and counts as no-progress), append a log line, bump cycle (atomic), END THE TURN.
You stop ONLY by flipping active:false on achieved/gave-up/capped, or the user runs /semipilot-cancel. Do not otherwise stop.
PROMPT
)"

if [ -n "$ULTRA" ]; then
  REFEED="$REFEED
ULTRACODE (mandatory this run): push parallelism to the max in step 4's build — author a Workflow and/or dispatch parallel subagents rather than working inline, isolate parallel file-mutating work in git worktrees, and verify findings adversarially. These tools are always permitted; --ultracode makes them required, not optional."
fi

if command -v jq >/dev/null 2>&1; then
  jq -n \
    --arg r "$REFEED" \
    --arg m "🎯 semipilot ${TARGET} cycle ${CYCLE}$([ -n "$ULTRA" ] && printf ' [ultracode]') -> continuing (done-check first; /semipilot-cancel to stop)" \
    '{decision:"block", reason:$r, systemMessage:$m}'
else
  FALLBACK_REASON='semipilot is active — run one bounded cycle: read .claude/ccharness/semipilot/state.json, DONE-check first, then give-up check, then one milestone-scoped funnel cycle; flip active:false on achieved/gave-up/capped. /semipilot-cancel to stop.'
  [ -n "$ULTRA" ] && FALLBACK_REASON="$FALLBACK_REASON ULTRACODE: fan out via Workflow + parallel subagents + git worktrees (mandatory)."
  printf '%s' "{\"decision\":\"block\",\"reason\":\"$FALLBACK_REASON\"}"
fi

exit 0
