#!/usr/bin/env bash
# nonstop — Stop hook (the between-pieces layer over the bounded musician).
#
# ADDITIVE and SEPARABLE: the musician (its SKILL and its own Stop hook) is
# untouched. This hook does NOTHING unless nonstop is ARMED — a per-session marker written by
# `musiciansctl nonstop on`, removed by `musiciansctl nonstop off`. When armed AND the musician has just
# CLOSED a piece (its state is active:false), it BLOCKS the stop and asks the
# model to simply RE-LAUNCH /musician (open mode) for the next piece — or disarm
# if the musician found nothing left. The musician's OWN brain decides WHAT to do
# next (open-mode what-to-do + roadmap + its git-notes awareness); nonstop only
# re-invokes it. There is no nonstop "advance" logic — that would duplicate the
# musician.
#
# Zones never overlap with musician-stop.sh:
#   musician active:true  -> musician-stop.sh drives (re-feed the next step); we no-op.
#   musician active:false -> musician-stop.sh releases;  WE block (re-launch).
#
# Fail OPEN: on any doubt -> exit 0 (no-op). A bug here must never trap the loop —
# the musician's own brakes and `musiciansctl nonstop off` still work. This hook is DUMB: it only
# gates on (marker armed + same session + musician closed); the next-piece decision
# lives in the musician, not here.
set -u

source "${BASH_SOURCE[0]%/*}/musician-resolve.sh"
NS_DIR=".claude/ccharness/nonstop/by-session"
HOOK_INPUT="$(cat 2>/dev/null || true)"
HOOK_SESSION="$(mus_session_from_stdin "$HOOK_INPUT")"

# 1. Unknown session, or nonstop not armed for THIS session -> no-op. The marker path is the session
#    key (one marker per session), so a marker armed in a different session simply isn't found here.
[ -n "$HOOK_SESSION" ] || exit 0
NS_STATE="$NS_DIR/$HOOK_SESSION"
[ -f "$NS_STATE" ] || exit 0

NS_ON=""; MUS_ACTIVE=""
if command -v jq >/dev/null 2>&1; then
  NS_ON="$(jq -r '.on // false' "$NS_STATE" 2>/dev/null || true)"
fi
# jq-free fallback for the armed flag (jq absent, coreutils present).
if [ -z "$NS_ON" ] && command -v grep >/dev/null 2>&1; then
  grep -Eq '"on"[[:space:]]*:[[:space:]]*true' "$NS_STATE" && NS_ON=true
fi
[ "$NS_ON" = "true" ] || exit 0

# 2. No musician run for this session (never launched, or /musician-cancel cleared the pointer) -> no-op.
MUS_DIR="$(mus_run_dir "$HOOK_SESSION")"
[ -n "$MUS_DIR" ] || exit 0
MUS_STATE="$MUS_DIR/state.json"
[ -f "$MUS_STATE" ] || exit 0

# 3. Musician still working (active:true, incl. awaiting/suspended) -> its own hook drives; stay silent.
#    Only advance when the musician has CLOSED (active:false). Unknown -> no-op (fail open).
if command -v jq >/dev/null 2>&1; then
  MUS_ACTIVE="$(jq -r '.active' "$MUS_STATE" 2>/dev/null || true)"
fi
if [ -z "$MUS_ACTIVE" ] && command -v grep >/dev/null 2>&1; then
  grep -Eq '"active"[[:space:]]*:[[:space:]]*false' "$MUS_STATE" && MUS_ACTIVE=false
  grep -Eq '"active"[[:space:]]*:[[:space:]]*true'  "$MUS_STATE" && MUS_ACTIVE=true
fi
[ "$MUS_ACTIVE" = "false" ] || exit 0

# 4. Armed + musician CLOSED for this session -> BLOCK and ask the model to re-launch the musician.
#    The musician's brain decides WHAT to do; we only re-invoke it (or stop on its "nothing left" verdict).
#    The disarm path is baked in concretely ($NS_STATE) so the model needs no bin on PATH to stop the loop.
REASON="🔁 nonstop is ARMED and the musician just CLOSED — do NOT stop. Read its outcome in $MUS_STATE. If outcome is \"empty\" (open mode: nothing left worth building — the roadmap frontier is exhausted), DISARM by deleting the marker file $NS_STATE, then stop. Otherwise (achieved) re-launch the musician for the next piece: invoke /musician --auto (open mode, FULLY AUTONOMOUS) — nonstop is the autonomous milestone-walker, so it must NOT pause to collaborate with the human between milestones; the musician picks the next roadmap milestone itself via what-to-do and its git-notes awareness; you do NOT pick or plan, you only re-invoke. If /musician cannot arm (no North Star), DISARM by deleting $NS_STATE, then stop. To disarm manually: \`musiciansctl nonstop off\`; Esc to interrupt."

if command -v jq >/dev/null 2>&1; then
  jq -n --arg r "$REASON" \
        --arg m "🔁 nonstop -> re-launching the musician for the next piece (open mode; \`musiciansctl nonstop off\` to stop)" \
        '{decision:"block", reason:$r, systemMessage:$m}'
else
  printf '%s' "{\"decision\":\"block\",\"reason\":\"$REASON\"}"
fi
exit 0
