#!/usr/bin/env bash
# musician — Stop hook (the bounded performer's "hard muscle").
#
# While the musician state file is ACTIVE for THIS session, re-feed the musician
# prompt on every Stop so the loop runs one cycle per turn. The musician ENDS ON
# ITS OWN: the model flips active:false when the work is achieved, declined, given
# up, capped, or budget-stopped, and THEN this hook (Exit #2) allows the stop. This
# hook only prevents an accidental mid-task stop. There is no second hook and no
# meta-loop — the musician is the only cc-agent loop.
#
# Fail CLOSED while active. Allow-the-stop paths (exit 0, no stdout):
#   1. no state file
#   2. state.active == false        (achieved / declined / gave-up / capped / stopped-budget / cancelled)
#   3. a DIFFERENT session owns it
#   4. state.awaiting is set         (suspended on async work / transient outage)
set -u

STATE_FILE=".claude/ccharness/musician/state.json"
HOOK_INPUT="$(cat 2>/dev/null || true)"

[ -f "$STATE_FILE" ] || exit 0

HOOK_SESSION=""; STATE_SESSION=""; STATE_ACTIVE=""; CYCLE="?"; ENTRY="?"
# If stdin or jq is absent, HOOK_SESSION/STATE_* stay empty → the active==false
# and different-session guards below are skipped → we fall through and RE-FEED (fail closed).
if command -v jq >/dev/null 2>&1; then
  HOOK_SESSION="$(printf '%s' "$HOOK_INPUT" | jq -r '.session_id // ""' 2>/dev/null || true)"
  STATE_SESSION="$(jq -r '.session_id // ""'   "$STATE_FILE" 2>/dev/null || true)"
  STATE_ACTIVE="$(jq -r '.active'              "$STATE_FILE" 2>/dev/null || true)"
  CYCLE="$(jq -r '.cycle // "?"'               "$STATE_FILE" 2>/dev/null || echo '?')"
  ENTRY="$(jq -r '.entry // "?"'               "$STATE_FILE" 2>/dev/null || echo '?')"
fi

# jq-free fallback for the critical active flag (jq absent, coreutils present):
# without this the achieved/declined/gave-up release (active:false) is invisible and the loop can't self-stop.
if [ -z "$STATE_ACTIVE" ] && command -v grep >/dev/null 2>&1; then
  grep -Eq '"active"[[:space:]]*:[[:space:]]*false' "$STATE_FILE" && STATE_ACTIVE=false
fi

# ultracode flag — grep-detected (jq-independent). Forces max parallelism in the build step.
# (There is no spend flag — the musician is bounded by design.)
ULTRA=""
if command -v grep >/dev/null 2>&1; then
  grep -Eq '"ultracode"[[:space:]]*:[[:space:]]*true' "$STATE_FILE" && ULTRA=1
fi

# Exit #2 — work finished (achieved / declined / gave-up / capped / stopped-budget) or cancelled.
[ "$STATE_ACTIVE" = "false" ] && exit 0

# Exit #3 — a different session owns the loop.
if [ -n "$STATE_SESSION" ] && [ -n "$HOOK_SESSION" ] && [ "$STATE_SESSION" != "$HOOK_SESSION" ]; then
  exit 0
fi

# Exit #4 — the loop is SUSPENDED on a long-running async build or a transient external outage.
# RELEASE the turn so the terminal yields to the user (/musician-cancel works again) and no idle
# re-feed burns subscription quota. The awaited task's OWN completion notification re-enters the
# agent, which clears `awaiting` and resumes. `awaiting` is a non-null object the agent sets;
# null/absent → normal loop. Only the agent sets/clears it, so a stale marker is cleared on resume.
AWAITING=""
if command -v jq >/dev/null 2>&1; then
  AWAITING="$(jq -r 'if (.awaiting // null) == null then "" else "1" end' "$STATE_FILE" 2>/dev/null || true)"
fi
if [ -z "$AWAITING" ] && command -v grep >/dev/null 2>&1; then
  grep -Eq '"awaiting"[[:space:]]*:[[:space:]]*\{' "$STATE_FILE" && AWAITING=1
fi
[ -n "$AWAITING" ] && exit 0

# --- ACTIVE for this session (or present-but-unparseable) → RE-FEED. Fail closed. ---
REFEED="$(cat <<'PROMPT'
🎼 musician is ACTIVE — continue the bounded loop for THIS piece of work. Run exactly ONE cycle:
1. Read .claude/ccharness/musician/state.json + blocked.jsonl + ../usage.json (headroom).
2. BUDGET: from a fresh usage.json, weekly used_% >= weekly_stop_pct → set active:false outcome:"stopped-budget", report seven_day.resets_at, END TURN. Else 5h remaining < headroom_floor_pct → set awaiting and END TURN. Else either window below floor → no expensive/async launches this cycle.
3. BRAIN (only while done_when == ""): think it through, sized to the input. TASK mode → triage the prompt, run the brain by necessity (crux for a fuzzy pain / North-Star fit for an idea / skip for a clear task). OPEN mode → cc-tools:what-to-do (menu as DATA, NO AskUserQuestion) → auto-pick the TOP direction. If the brain says leave-it / wrong-problem / intent-changing reframe / (open) nothing worth doing → set active:false outcome:"declined", log why, report, END TURN — do NOT build. Otherwise FORGE a falsifiable done_when and write it to state (atomic).
4. DONE-CHECK: survey "now" and judge against state.done_when. MET → set active:false outcome:"achieved", final log line, report, END TURN.
5. GIVE-UP CHECK: no_progress_streak >= max_no_progress OR cycle >= max_cycles → set active:false outcome:"gave-up"|"capped", report the blocked queue, END TURN.
6. Otherwise build ONE step toward done_when: cc-tools:how-to-do → cc-tools:do → verify → LOCAL commit (no push). Async build that cannot finish in-turn → set awaiting and END TURN (no cycle/streak). Handback (unbuildable/forked, or slap twice) → append to blocked.jsonl, no-progress cycle. External transient block → suspend (awaiting), do not streak++. Update no_progress_streak (reset on real progress; ++ on blocked/idle), append a log line, bump cycle (atomic), END TURN.
You stop ONLY by flipping active:false (achieved/declined/gave-up/capped/stopped-budget), or the user runs /musician-cancel. The brain may DECLINE before building — that is a success, not a give-up. Do not otherwise stop.
PROMPT
)"

if [ -n "$ULTRA" ]; then
  REFEED="$REFEED
ULTRACODE (mandatory this run): push parallelism to the max in step 6's build — author a Workflow and/or dispatch parallel subagents rather than working inline, isolate parallel file-mutating work in git worktrees, and verify findings adversarially. These tools are always permitted; --ultracode makes them required, not optional."
fi

if command -v jq >/dev/null 2>&1; then
  jq -n \
    --arg r "$REFEED" \
    --arg m "🎼 musician (${ENTRY}) cycle ${CYCLE}$([ -n "$ULTRA" ] && printf ' [ultracode]') -> continuing (brain → done-check; /musician-cancel to stop)" \
    '{decision:"block", reason:$r, systemMessage:$m}'
else
  FALLBACK_REASON='musician is active — run one bounded cycle: read .claude/ccharness/musician/state.json, check budget, run the BRAIN while done_when is empty (it may DECLINE before building), then DONE-check, then give-up check, then one build step (how-to-do -> do -> local commit); flip active:false on achieved/declined/gave-up/capped/stopped-budget. /musician-cancel to stop.'
  [ -n "$ULTRA" ] && FALLBACK_REASON="$FALLBACK_REASON ULTRACODE: fan out via Workflow + parallel subagents + git worktrees (mandatory)."
  printf '%s' "{\"decision\":\"block\",\"reason\":\"$FALLBACK_REASON\"}"
fi

exit 0
