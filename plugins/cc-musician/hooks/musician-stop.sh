#!/usr/bin/env bash
# musician — Stop hook (the bounded performer's "hard muscle").
#
# While THIS session's musician run is ACTIVE, re-feed the musician prompt on every Stop so it does
# the next step of its task list. The musician's `tasks` array IS the loop state: the hook re-feeds
# while any task is incomplete and releases when the list is done. The musician also flips
# active:false on the last task; this hook is the hard backstop against an accidental mid-list stop.
#
# Each run lives in its own folder runs/<run-id>/; a per-session pointer by-session/<session_id>
# names it. We resolve THIS session's run from the session_id on stdin (see musician-resolve.sh).
#
# Fail-closed semantics, inverted for the multi-run world:
#   no pointer for this session  -> RELEASE (the common case — most Stops have no musician at all)
#   active == false              -> RELEASE (achieved / empty / cancelled)
#   awaiting set                 -> RELEASE (suspended on async work / transient outage)
#   phase == shaping             -> RELEASE (collaborating with the human, not looping)
#   no incomplete task remains   -> RELEASE (all tasks completed, OR the list is empty — nothing to do)
#   a task is still incomplete   -> RE-FEED (do the next step)
#   state unreadable (no file /  -> RE-FEED (fail-closed: never drop a live task to a parse failure)
#     no jq to parse the array)
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

STATE_ACTIVE=""; DONE="?"; TOTAL="?"; ENTRY="?"
if command -v jq >/dev/null 2>&1; then
  STATE_ACTIVE="$(jq -r '.active'                                       "$STATE_FILE" 2>/dev/null || true)"
  ENTRY="$(jq -r '.entry // "?"'                                        "$STATE_FILE" 2>/dev/null || echo '?')"
  DONE="$(jq -r '[(.tasks // [])[] | select(.status=="completed")] | length' "$STATE_FILE" 2>/dev/null || echo '?')"
  TOTAL="$(jq -r '(.tasks // []) | length'                              "$STATE_FILE" 2>/dev/null || echo '?')"
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

# RELEASE — work finished (achieved / empty) or cancelled.
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

# RELEASE — nothing left to do: NO incomplete task remains (every task completed, OR the list is
# empty). The musician decomposes on its FIRST turn (arm / --auto / handoff), never via a re-feed, so
# a re-fed turn always has tasks — an empty list at a turn boundary means "done / nothing to do" and
# releases (it is never an endless re-feed; the musician should close, but empty is a release either
# way). Pure bash cannot parse the array, so with no jq this is skipped and we fall through to RE-FEED
# — fail-closed on an UNREADABLE state (missing file / no jq), never on a definite empty one.
if command -v jq >/dev/null 2>&1 && \
   jq -e 'all((.tasks // [])[]; .status == "completed")' "$STATE_FILE" >/dev/null 2>&1; then
  exit 0
fi

# Heartbeat — this run is alive and working. Refreshing it each turn means a hard crash (no Stop
# event) leaves a STALE heartbeat, which the next `/musician` arm scan reads as a crashed orphan.
: > "$RUN_DIR/heartbeat" 2>/dev/null || true

# --- ACTIVE for this session with tasks still open (or present-but-unparseable) → RE-FEED. ---
REFEED="$(cat <<'PROMPT'
🎼 musician is ACTIVE — carry THIS piece of work one step further. You run ONE step per turn; this hook re-feeds you while tasks remain and releases when the list is done. You CONDUCT — every work-unit is a dispatched subagent and you never write product code yourself. Do ONE step:
1. Read your run state.json + log.jsonl in .claude/ccharness/musician/runs/<run-id>/ (resolve <run-id> from .claude/ccharness/musician/by-session/$CLAUDE_CODE_SESSION_ID). The `tasks` array IS your plan and your progress; log.jsonl carries which approaches already failed this run.
2. tasks EMPTY → DECOMPOSE: break this piece of work into an ordered list of concrete subtasks, each executable as ONE dispatched unit; the LAST task is ALWAYS a real verification of the observable "done". OPEN mode → first dispatch a cc-script:what-to-do subagent (menu as DATA, NO AskUserQuestion), auto-pick the TOP direction, then decompose THAT; nothing worth building (frontier exhausted) → set active:false outcome:"empty", report, END TURN. Write the list to state.tasks (atomic) AND mirror it to the native task tool so the human sees it. NEVER refuse handed work — sharpen a misaimed target, then decompose.
3. tasks REMAIN → take the FIRST incomplete one (in_progress, else first pending), mark it in_progress, and DO it. Dispatch the right instrument: cc-script:do for a build, cc-script:how-to-do for a real fork, cc-instruments:crux for a fuzzy pain. A BUILD runs worktree-isolated: capture BASE = git rev-parse HEAD → dispatch the cc-script:do subagent with Agent isolation:"worktree", model:"opus", told its FIRST action is git reset --hard BASE; it writes the code + smoke-checks, then chains to cc-script:refactor-review-test which makes the LOCAL commit INSIDE the worktree (no push); land it ff-only via the helper at state.worktree_helper (integrate → INTEGRATED=sha; STALE → discard + rebuild this step; no commit → discard). Then mark the task completed in state.tasks AND the native task tool.
   • VERIFY task → dispatch a REAL check of the observable outcome (run/check it, do not vibe). PASSED → mark it completed. FAILED → do NOT complete it; APPEND remediation task(s) to the list (it stays incomplete) and continue. A run closes ONLY after a real verify has passed — this is how "done" stays honest.
   • Backgrounded async that will not return IN THIS TURN → leave the task in_progress, set awaiting, and END TURN on the SAME turn you dispatch (decide this AT dispatch; never end a turn active-and-not-awaiting while a backgrounded build still runs — that burns one wasted, empty re-feed). The completion notification resumes you, where you clear awaiting and judge the result.
   • Handback (do could not build it) → re-dispatch cc-script:how-to-do for a DIFFERENT approach (failed approaches are in log.jsonl); never self-close. A transient external block (5xx/rate-limit) → suspend (awaiting). A true dead-end is for the human to run /musician-cancel.
4. Completed the LAST task (the list is now ALL done) → in ONE atomic state write set active:false and outcome:"achieved" (do not split closing from completing the task); append one git notes line — git notes append -m "built: <what> — <why>" (closed past only, NEVER a forward intent); report; END TURN.
5. Append a log.jsonl line and END TURN. The hook re-feeds while any task is incomplete.
You stop ONLY by finishing the list (active:false, outcome:"achieved"), open-mode "empty", or /musician-cancel. Handed work is never refused. There is no try-count and no step cap.
PROMPT
)"

if [ -n "$ULTRA" ]; then
  REFEED="$REFEED
ULTRACODE (mandatory this run): push parallelism to the max on the build tasks — author a Workflow and/or dispatch parallel cc-script:do subagents, EACH with its own worktree isolation, and integrate each one's branch (via the recorded worktree helper) as it lands; verify findings adversarially. These tools are always permitted; --ultracode makes them required, not optional."
fi

if command -v jq >/dev/null 2>&1; then
  jq -n \
    --arg r "$REFEED" \
    --arg m "🎼 musician (${ENTRY}) ${DONE}/${TOTAL} tasks$([ -n "$ULTRA" ] && printf ' [ultracode]') -> next step (decompose → do next task → close; /musician-cancel to stop)" \
    '{decision:"block", reason:$r, systemMessage:$m}'
else
  FALLBACK_REASON='musician is active — do the next step. Read your run state.json under .claude/ccharness/musician/runs/<run-id>/ (resolve via by-session/$CLAUDE_CODE_SESSION_ID); the `tasks` array is your plan + progress. You CONDUCT — every work-unit is a dispatched subagent; never write code inline. If tasks is EMPTY, DECOMPOSE the work into an ordered subtask list whose LAST item is a real verification, write it to state.tasks, and mirror it to the native task tool (open mode with nothing to build -> active:false outcome:"empty"). Otherwise take the first incomplete task, mark it in_progress, and DO it via the right instrument; a build runs WITH worktree isolation (git reset --hard to your current HEAD first, chains to refactor-review-test which commits INSIDE it, landed ff-only via state.worktree_helper — STALE -> discard + rebuild, no commit -> discard), then mark it completed. A VERIFY task that FAILS appends fix tasks (never marked done); a backgrounded build sets awaiting and ENDS THE TURN on the same turn you dispatch; a handback re-runs how-to-do for a DIFFERENT approach (never a self-close). When the LAST task completes, set active:false outcome:"achieved" in one write and git notes append one closed fact (built: + why). A true dead-end is the human'"'"'s /musician-cancel.'
  [ -n "$ULTRA" ] && FALLBACK_REASON="$FALLBACK_REASON ULTRACODE: fan out via Workflow + parallel subagents + git worktrees (mandatory)."
  printf '%s' "{\"decision\":\"block\",\"reason\":\"$FALLBACK_REASON\"}"
fi

exit 0
