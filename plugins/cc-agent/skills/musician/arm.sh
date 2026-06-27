#!/usr/bin/env bash
# musician arm — deterministic run setup, extracted from SKILL.md so the bookkeeping is exact and
# testable. The brain stays in the skill; this only does the mechanical part. The /musician command
# runs this first and reads its KEY=VALUE output.
#
# Honest seam: the TRIGGER is still model-mediated (the command invokes this); the win is that
# run-id, folders, atomic state, the pointer, heartbeat, and the crash-orphan scan are deterministic
# instead of hand-written JSON. If this helper can't be run, the skill falls back to doing the same
# steps inline.
#
# Usage:  musician-arm.sh "<raw $ARGUMENTS>"
#   Flags in the argument string: --ultracode  --resume <run-id>
#   Everything else = the task/problem prompt (empty -> open mode).
# Env:    CLAUDE_CODE_SESSION_ID — the session that owns the run (required to write the pointer).
#
# Output (stdout, KEY=VALUE lines for the skill to parse):
#   GATE=no-north-star         open mode but no North Star -> route to /find-goal; no run created
#   RESUME_MISSING=<id>        --resume named a run that does not exist
#   RUN_DIR=<path>             the run folder to use this run
#   RUN_ID=<id>
#   ENTRY=task|open
#   RESUMED=<id>               (only with --resume) re-adopted an existing run; continue its loop
#   ORPHAN=<id>|<mins>|<input> a crashed-looking run found (surface to the user); zero or more lines
set -u

MUS=".claude/ccharness/musician"
SID="${CLAUDE_CODE_SESSION_ID:-}"
STALE_MIN=30
# Absolute path to the worktree helper (our sibling). Recorded into state so the in-loop build
# integrate/discard calls can find it on re-fed turns, where ${CLAUDE_PLUGIN_ROOT} is not set.
HELPER="$(cd "$(dirname "$0")" 2>/dev/null && pwd)/worktree.sh"
now_iso() { date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo "1970-01-01T00:00:00Z"; }

# --- parse the argument string: pull known flags, the rest is the prompt ---
ULTRA=false; RESUME=""; PROMPT=""
# -d '' reads the WHOLE argument (incl. any newlines) into the array — a multi-line prompt is not
# truncated; flag detection still works word-by-word (the rejoined prompt normalizes whitespace).
IFS=$' \t\n' read -r -d '' -a _a <<< "${1:-}" || true
_i=0; _n=${#_a[@]}
while [ "$_i" -lt "$_n" ]; do
  case "${_a[$_i]}" in
    --ultracode)     ULTRA=true ;;
    --resume)        _i=$((_i+1)); RESUME="${_a[$_i]:-}" ;;
    *)               PROMPT="${PROMPT:+$PROMPT }${_a[$_i]}" ;;
  esac
  _i=$((_i+1))
done
ENTRY=task; [ -z "$PROMPT" ] && ENTRY=open

mkdir -p "$MUS/by-session" "$MUS/runs" 2>/dev/null || true

# --- resume an explicit run (surface-only crash recovery: the user chose this run) ---
if [ -n "$RESUME" ]; then
  RDIR="$MUS/runs/$RESUME"
  if [ ! -f "$RDIR/state.json" ]; then
    printf 'RESUME_MISSING=%s\n' "$RESUME"; exit 0
  fi
  tmp="$RDIR/state.json.tmp.$$"
  jq --arg sid "$SID" --arg helper "$HELPER" '.active=true | .status="working" | .awaiting=null | .outcome=null | .session_id=$sid | .worktree_helper=$helper' \
     "$RDIR/state.json" > "$tmp" 2>/dev/null && mv "$tmp" "$RDIR/state.json"
  [ -n "$SID" ] && printf '%s' "$RESUME" > "$MUS/by-session/$SID"
  : > "$RDIR/heartbeat"
  printf 'RESUMED=%s\nRUN_DIR=%s\nRUN_ID=%s\nENTRY=%s\n' "$RESUME" "$RDIR" "$RESUME" "$(jq -r '.entry // "open"' "$RDIR/state.json")"
  exit 0
fi

# --- grounding gate: open mode needs a North Star ---
if [ "$ENTRY" = "open" ] && ! grep -q '## Product North Star' CLAUDE.md 2>/dev/null; then
  printf 'GATE=no-north-star\n'; exit 0
fi

# --- forge the run and write its state ---
RUN_ID="$(date -u +%Y%m%d-%H%M%S 2>/dev/null || echo 00000000-000000)-$(printf '%04x' $((RANDOM)))"
RUN_DIR="$MUS/runs/$RUN_ID"
mkdir -p "$RUN_DIR"

tmp="$RUN_DIR/state.json.tmp.$$"
jq -n \
  --arg run_id "$RUN_ID" --arg sid "$SID" --arg input "$PROMPT" --arg entry "$ENTRY" \
  --argjson ultra "$ULTRA" \
  --arg started "$(now_iso)" --arg helper "$HELPER" \
  '{active:true, status:"working", run_id:$run_id, session_id:$sid, mode:"musician",
    entry:$entry, input:$input, done_when:"", cycle:0, ultracode:$ultra,
    started_at:$started, last_surveyed_sha:"", awaiting:null, outcome:null,
    worktree_helper:$helper}' \
  > "$tmp" && mv "$tmp" "$RUN_DIR/state.json"

[ -n "$SID" ] && printf '%s' "$RUN_ID" > "$MUS/by-session/$SID"
: > "$RUN_DIR/blocked.jsonl"; : > "$RUN_DIR/log.jsonl"; : > "$RUN_DIR/heartbeat"

# --- crash-orphan scan: a run still "working", not parked on async, whose heartbeat went stale.
#     Surface it (the user decides whether to /musician --resume <id>); never auto-adopt. ---
if [ -d "$MUS/runs" ]; then
  while IFS= read -r hb; do
    d="${hb%/heartbeat}"
    [ "$d" = "$RUN_DIR" ] && continue
    st="$d/state.json"; [ -f "$st" ] || continue
    [ "$(jq -r '.active' "$st" 2>/dev/null)" = "true" ] || continue
    [ "$(jq -r 'if (.awaiting//null)==null then "" else "1" end' "$st" 2>/dev/null)" = "" ] || continue
    hbt="$(stat -f %m "$hb" 2>/dev/null || stat -c %Y "$hb" 2>/dev/null || echo 0)"
    mins=$(( ( $(date +%s 2>/dev/null || echo 0) - hbt ) / 60 ))
    printf 'ORPHAN=%s|%s|%s\n' "${d##*/}" "$mins" "$(jq -r '.input // ""' "$st" 2>/dev/null)"
  done < <(find "$MUS/runs" -maxdepth 2 -name heartbeat -mmin +"$STALE_MIN" 2>/dev/null)
fi

printf 'RUN_DIR=%s\nRUN_ID=%s\nENTRY=%s\n' "$RUN_DIR" "$RUN_ID" "$ENTRY"
