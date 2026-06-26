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

# Heartbeat — this run is alive and working. Refreshing it each turn means a hard crash (no Stop
# event) leaves a STALE heartbeat, which the next `/musician` arm scan reads as a crashed orphan.
: > "$RUN_DIR/heartbeat" 2>/dev/null || true

# --- ACTIVE for this session (or present-but-unparseable) → RE-FEED. Fail closed. ---
REFEED="$(cat <<'PROMPT'
🎼 musician is ACTIVE — continue the bounded loop for THIS piece of work. Run exactly ONE cycle:
1. Read the run state.json + blocked.jsonl in .claude/ccharness/musician/runs/<run-id>/ (resolve <run-id> from .claude/ccharness/musician/by-session/$CLAUDE_CODE_SESSION_ID).
2. BRAIN (only while done_when == ""): think it through, sized to the input. TASK mode → triage the prompt, run the brain by necessity (crux for a fuzzy pain / North-Star fit for an idea / skip for a clear task). OPEN mode → cc-tools:what-to-do (menu as DATA, NO AskUserQuestion) → auto-pick the TOP direction. If the brain says leave-it / wrong-problem / intent-changing reframe / (open) nothing worth doing → set active:false outcome:"declined", log why, report, END TURN — do NOT build. Otherwise FORGE a falsifiable done_when and write it to state (atomic).
3. DONE-CHECK: survey "now" and judge against state.done_when. MET → set active:false outcome:"achieved", final log line, report, END TURN.
4. Otherwise build ONE step toward done_when: cc-tools:how-to-do → cc-tools:do → verify → LOCAL commit (no push). how-to-do has NO new buildable approach left (technical path exhausted) → set active:false outcome:"blocked", report the blocked queue, END TURN. Async build that cannot finish in-turn → set awaiting and END TURN (no cycle). Handback by kind: business/non-technical blocker do refuses → set active:false outcome:"blocked", report the blocked queue, END TURN; technical fork / stuck (slap twice) → append to blocked.jsonl and re-run how-to-do for a DIFFERENT approach. External transient block → suspend (awaiting). Append a log line, bump cycle (atomic), END TURN.
5. ON ANY CLOSE (achieved/declined/blocked): before END TURN, append ONE past-tense closed-fact line as awareness for the next run — git notes append -m "<built|declined|blocked>: <what> — <why>". NEVER a forward intent (those go to roadmap-proposals.md, not git notes).
You stop ONLY by flipping active:false (achieved/declined/blocked), or the user runs /musician-cancel. The brain may DECLINE before building — that is a success, not a failure. There is no try-count or cycle cap: one real blocker closes blocked. Do not otherwise stop.
PROMPT
)"

if [ -n "$ULTRA" ]; then
  REFEED="$REFEED
ULTRACODE (mandatory this run): push parallelism to the max in step 5's build — author a Workflow and/or dispatch parallel subagents rather than working inline, isolate parallel file-mutating work in git worktrees, and verify findings adversarially. These tools are always permitted; --ultracode makes them required, not optional."
fi

if command -v jq >/dev/null 2>&1; then
  jq -n \
    --arg r "$REFEED" \
    --arg m "🎼 musician (${ENTRY}) cycle ${CYCLE}$([ -n "$ULTRA" ] && printf ' [ultracode]') -> continuing (brain → done-check; /musician-cancel to stop)" \
    '{decision:"block", reason:$r, systemMessage:$m}'
else
  FALLBACK_REASON='musician is active — run one bounded cycle: read your run state.json under .claude/ccharness/musician/runs/<run-id>/ (resolve via by-session/$CLAUDE_CODE_SESSION_ID), run the BRAIN while done_when is empty (it may DECLINE before building), then DONE-check, then one build step (how-to-do -> do -> local commit; handback: business blocker -> close blocked, technical -> retry how-to-do for a different approach); flip active:false on achieved/declined/blocked; on close git notes append one closed fact (built/declined/blocked + why), never a forward intent. /musician-cancel to stop.'
  [ -n "$ULTRA" ] && FALLBACK_REASON="$FALLBACK_REASON ULTRACODE: fan out via Workflow + parallel subagents + git worktrees (mandatory)."
  printf '%s' "{\"decision\":\"block\",\"reason\":\"$FALLBACK_REASON\"}"
fi

exit 0
