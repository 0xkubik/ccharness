#!/usr/bin/env bash
# musician — Stop hook (the bounded performer's "hard muscle").
#
# While THIS session's musician run is ACTIVE, re-feed the musician prompt on every Stop so the
# loop runs one cycle per turn. The musician ENDS ON ITS OWN: the model flips active:false when the
# work is achieved, declined, or blocked, and THEN this hook allows the stop. This hook
# only prevents an accidental mid-task stop.
#
# Each run lives in its own folder runs/<run-id>/; a per-session pointer by-session/<session_id>
# names it. We resolve THIS session's run from the session_id on stdin (see musician-resolve.sh).
#
# Fail-closed semantics, inverted for the multi-run world:
#   no pointer for this session  -> RELEASE (the common case — most Stops have no musician at all)
#   active == false              -> RELEASE (achieved / declined / blocked / cancelled)
#   awaiting set                 -> RELEASE (suspended on async work / transient outage)
#   pointer exists but state      -> RE-FEED (never drop a live task to an unreadable state)
#     unreadable, or active:true
set -u

source "${BASH_SOURCE[0]%/*}/musician-resolve.sh"
# Slurp stdin with a bash builtin (not `cat`) so resolution survives even a bare PATH.
IFS= read -rd '' HOOK_INPUT || true

SID="$(mus_session_from_stdin "$HOOK_INPUT")"
RUN_DIR="$(mus_run_dir "$SID")"
# No active run for this session → let the turn end.
[ -n "$RUN_DIR" ] || exit 0
STATE_FILE="$RUN_DIR/state.json"

# Slurp once for the pure-bash (no jq/grep/cat) fallback path.
STATE_RAW=""; [ -f "$STATE_FILE" ] && STATE_RAW="$(<"$STATE_FILE")"

STATE_ACTIVE=""; CYCLE="?"; ENTRY="?"
if command -v jq >/dev/null 2>&1; then
  STATE_ACTIVE="$(jq -r '.active'        "$STATE_FILE" 2>/dev/null || true)"
  CYCLE="$(jq -r '.cycle // "?"'         "$STATE_FILE" 2>/dev/null || echo '?')"
  ENTRY="$(jq -r '.entry // "?"'         "$STATE_FILE" 2>/dev/null || echo '?')"
fi
if [ -z "$STATE_ACTIVE" ] && command -v grep >/dev/null 2>&1; then
  grep -Eq '"active"[[:space:]]*:[[:space:]]*false' "$STATE_FILE" && STATE_ACTIVE=false
fi
if [ -z "$STATE_ACTIVE" ]; then
  case "$STATE_RAW" in *'"active": false'*|*'"active":false'*) STATE_ACTIVE=false;; esac
fi

# ultracode flag → mandatory max parallelism in the build step.
ULTRA=""
if command -v grep >/dev/null 2>&1; then
  grep -Eq '"ultracode"[[:space:]]*:[[:space:]]*true' "$STATE_FILE" && ULTRA=1
fi
if [ -z "$ULTRA" ]; then
  case "$STATE_RAW" in *'"ultracode": true'*|*'"ultracode":true'*) ULTRA=1;; esac
fi

# phase → "shaping" (collaborating with the human) vs "building" (autonomous loop). Absent → building
# (back-compat: a run armed before this field re-feeds as before). Only "shaping" changes behaviour.
PHASE=""
if command -v jq >/dev/null 2>&1; then
  PHASE="$(jq -r '.phase // ""' "$STATE_FILE" 2>/dev/null || true)"
fi
if [ -z "$PHASE" ] && command -v grep >/dev/null 2>&1; then
  grep -Eq '"phase"[[:space:]]*:[[:space:]]*"shaping"' "$STATE_FILE" && PHASE=shaping
fi
if [ -z "$PHASE" ]; then
  case "$STATE_RAW" in *'"phase": "shaping"'*|*'"phase":"shaping"'*) PHASE=shaping;; esac
fi

# RELEASE — work finished (achieved / declined / blocked) or cancelled.
[ "$STATE_ACTIVE" = "false" ] && exit 0

# RELEASE — SUSPENDED on async work or a transient external outage. The terminal yields
# (/musician-cancel works again) and no idle re-feed wastes a turn; the awaited task's own
# completion notification re-enters the agent, which clears `awaiting` and resumes.
AWAITING=""
if command -v jq >/dev/null 2>&1; then
  AWAITING="$(jq -r 'if (.awaiting // null) == null then "" else "1" end' "$STATE_FILE" 2>/dev/null || true)"
fi
if [ -z "$AWAITING" ] && command -v grep >/dev/null 2>&1; then
  grep -Eq '"awaiting"[[:space:]]*:[[:space:]]*\{' "$STATE_FILE" && AWAITING=1
fi
if [ -z "$AWAITING" ]; then
  case "$STATE_RAW" in *'"awaiting": {'*|*'"awaiting":{'*) AWAITING=1;; esac
fi
[ -n "$AWAITING" ] && exit 0

# RELEASE — SHAPING phase: the musician is developing the idea WITH the human, not running the
# autonomous loop. End the turn so the human can answer; do NOT re-feed. (AskUserQuestion and normal
# back-and-forth happen here; the musician itself flips phase to "building" at the handoff, and only
# THEN does this hook start re-feeding.) Keep the heartbeat fresh so the live conversation reads alive.
if [ "$PHASE" = "shaping" ]; then
  : > "$RUN_DIR/heartbeat" 2>/dev/null || true
  exit 0
fi

# Heartbeat — this run is alive and working. Refreshing it each turn means a hard crash (no Stop
# event) leaves a STALE heartbeat, which the next `/musician` arm scan reads as a crashed orphan.
: > "$RUN_DIR/heartbeat" 2>/dev/null || true

# --- ACTIVE for this session (or present-but-unparseable) → RE-FEED. Fail closed. ---
REFEED="$(cat <<'PROMPT'
🎼 musician is ACTIVE — continue the bounded loop for THIS piece of work. Run exactly ONE cycle:
1. Read the run state.json + blocked.jsonl in .claude/ccharness/musician/runs/<run-id>/ (resolve <run-id> from .claude/ccharness/musician/by-session/$CLAUDE_CODE_SESSION_ID).
2. BRAIN (only while done_when == ""): you CONDUCT — dispatch a subagent to think it through, sized to the input; never reason the work out in your own context. TASK mode → triage the prompt, dispatch the brain by necessity (a crux subagent for a fuzzy pain / a what-to-do North-Star fit for an idea / skip for a clear task). OPEN mode → dispatch a cc-funnel:what-to-do subagent (menu as DATA, NO AskUserQuestion) → auto-pick the TOP direction. If the brain says leave-it / wrong-problem / intent-changing reframe / (open) nothing worth doing → set active:false outcome:"declined", log why, report, END TURN — do NOT build. Otherwise FORGE a falsifiable done_when and write it to state (atomic).
3. DONE-CHECK: survey "now" and judge against state.done_when. MET → set active:false outcome:"achieved", final log line, report, END TURN.
4. Otherwise build ONE step toward done_when: dispatch a cc-funnel:how-to-do subagent → capture BASE = the main repo current HEAD (run git rev-parse HEAD) → dispatch a cc-funnel:do subagent WITH worktree isolation (Agent isolation:"worktree" — the build, its tools, and its sub-agents all stay in one worktree under .claude/worktrees/; a "cd into a worktree" instruction leaks back to main), instructing it that its FIRST action is to run git reset --hard BASE so it builds on your current HEAD (the worktree base is otherwise out of your control). IT writes the code (you never Edit/Write product code yourself), builds+smoke, chains to refactor-review-test which makes the LOCAL commit INSIDE the worktree (no push). Capture the returned worktreePath + worktreeBranch, then land it via the worktree helper whose absolute path is recorded in state under the worktree_helper key (read it from <run>/state.json): if the build committed, run that helper with [integrate worktreePath worktreeBranch] — it is fast-forward-only (INTEGRATED=sha → on your branch + worktree removed; STALE=branch → the build was NOT on your current HEAD so stale work is refused and the worktree kept → run [discard worktreePath worktreeBranch] and rebuild this step, and a SECOND consecutive STALE → set active:false outcome:"blocked" with reason "build isolation cannot align to HEAD"); if the build produced NO commit, run the helper with [discard worktreePath worktreeBranch]. how-to-do has NO new buildable approach left (technical path exhausted) → set active:false outcome:"blocked", report the blocked queue, END TURN. Async build that cannot finish in-turn → set awaiting and END TURN (no cycle). Handback by kind: business/non-technical blocker do refuses → set active:false outcome:"blocked", report the blocked queue, END TURN; technical fork / stuck (slap twice) → append to blocked.jsonl and re-run how-to-do for a DIFFERENT approach. External transient block → suspend (awaiting). Append a log line, bump cycle (atomic), END TURN.
5. ON ANY CLOSE (achieved/declined/blocked): before END TURN, append ONE past-tense closed-fact line as awareness for the next run — git notes append -m "<built|declined|blocked>: <what> — <why>". NEVER a forward intent (those go to roadmap-proposals.md, not git notes).
You stop ONLY by flipping active:false (achieved/declined/blocked), or the user runs /musician-cancel. The brain may DECLINE before building — that is a success, not a failure. There is no try-count or cycle cap: one real blocker closes blocked. Do not otherwise stop.
PROMPT
)"

if [ -n "$ULTRA" ]; then
  REFEED="$REFEED
ULTRACODE (mandatory this run): push parallelism to the max in step 4's build — author a Workflow and/or dispatch parallel cc-funnel:do subagents, EACH with its own worktree isolation, and integrate each one's branch (via the recorded worktree helper) as it lands; verify findings adversarially. These tools are always permitted; --ultracode makes them required, not optional."
fi

if command -v jq >/dev/null 2>&1; then
  jq -n \
    --arg r "$REFEED" \
    --arg m "🎼 musician (${ENTRY}) cycle ${CYCLE}$([ -n "$ULTRA" ] && printf ' [ultracode]') -> continuing (brain → done-check; /musician-cancel to stop)" \
    '{decision:"block", reason:$r, systemMessage:$m}'
else
  FALLBACK_REASON='musician is active — run one bounded cycle: read your run state.json under .claude/ccharness/musician/runs/<run-id>/ (resolve via by-session/$CLAUDE_CODE_SESSION_ID). You CONDUCT — every work-unit is a dispatched subagent; never think or write code inline. Dispatch the BRAIN while done_when is empty (it may DECLINE before building), then DONE-check, then one build step (dispatch how-to-do -> do subagents; the do subagent runs WITH worktree isolation so the build stays in a worktree and is told to first git reset --hard to your current HEAD, then chains to refactor-review-test which commits INSIDE it; land it with the worktree helper recorded in state.worktree_helper — integrate is ff-only (STALE -> discard + rebuild, 2nd consecutive STALE -> blocked), or discard if no commit; handback: business blocker -> close blocked, technical -> retry how-to-do for a different approach); flip active:false on achieved/declined/blocked; on close git notes append one closed fact (built/declined/blocked + why), never a forward intent. /musician-cancel to stop.'
  [ -n "$ULTRA" ] && FALLBACK_REASON="$FALLBACK_REASON ULTRACODE: fan out via Workflow + parallel subagents + git worktrees (mandatory)."
  printf '%s' "{\"decision\":\"block\",\"reason\":\"$FALLBACK_REASON\"}"
fi

exit 0
