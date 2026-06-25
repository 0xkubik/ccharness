#!/usr/bin/env bash
# nonstop — Stop hook (the between-pieces layer over the bounded musician).
#
# ADDITIVE and SEPARABLE: the musician (its SKILL and its own Stop hook) is
# untouched. This hook does NOTHING unless nonstop is ARMED — a marker written by
# /nonstop-on, removed by /nonstop-off. When armed AND the musician has just
# CLOSED a piece (its state is active:false), it BLOCKS the stop and asks the
# model to run the cc-agent:nonstop skill, which owns ALL the advance logic
# (record the closed milestone, pick the next, or disarm when done/blocked).
#
# Zones never overlap with musician-stop.sh:
#   musician active:true  -> musician-stop.sh drives (re-feed one cycle); we no-op.
#   musician active:false -> musician-stop.sh releases;  WE block (advance).
#
# Fail OPEN: on any doubt -> exit 0 (no-op). A bug here must never trap the loop —
# the musician's own brakes and /nonstop-off still work. This hook is DUMB: it only
# gates on (marker armed + same session + musician closed); all decisions live in
# the skill.
set -u

NS_STATE=".claude/ccharness/nonstop/state.json"
MUS_STATE=".claude/ccharness/musician/state.json"
HOOK_INPUT="$(cat 2>/dev/null || true)"

# 1. nonstop not armed -> no-op.
[ -f "$NS_STATE" ] || exit 0

NS_ON=""; NS_SESSION=""; HOOK_SESSION=""; MUS_ACTIVE=""
if command -v jq >/dev/null 2>&1; then
  NS_ON="$(jq -r '.on // false'         "$NS_STATE"  2>/dev/null || true)"
  NS_SESSION="$(jq -r '.session_id // ""' "$NS_STATE" 2>/dev/null || true)"
  HOOK_SESSION="$(printf '%s' "$HOOK_INPUT" | jq -r '.session_id // ""' 2>/dev/null || true)"
fi
# jq-free fallback for the armed flag (jq absent, coreutils present).
if [ -z "$NS_ON" ] && command -v grep >/dev/null 2>&1; then
  grep -Eq '"on"[[:space:]]*:[[:space:]]*true' "$NS_STATE" && NS_ON=true
fi
[ "$NS_ON" = "true" ] || exit 0

# 2. A DIFFERENT session armed it -> no-op (only the owner advances). Unknown session on
#    either side (jq absent) -> skip this guard and fall through (the marker is the gate).
if [ -n "$NS_SESSION" ] && [ -n "$HOOK_SESSION" ] && [ "$NS_SESSION" != "$HOOK_SESSION" ]; then
  exit 0
fi

# 3. No musician to advance from (never launched, or /musician-cancel removed the state) -> no-op.
[ -f "$MUS_STATE" ] || exit 0

# 4. Musician still working (active:true, incl. awaiting/suspended) -> its own hook drives; stay silent.
#    Only advance when the musician has CLOSED (active:false). Unknown -> no-op (fail open).
if command -v jq >/dev/null 2>&1; then
  MUS_ACTIVE="$(jq -r '.active' "$MUS_STATE" 2>/dev/null || true)"
fi
if [ -z "$MUS_ACTIVE" ] && command -v grep >/dev/null 2>&1; then
  grep -Eq '"active"[[:space:]]*:[[:space:]]*false' "$MUS_STATE" && MUS_ACTIVE=false
  grep -Eq '"active"[[:space:]]*:[[:space:]]*true'  "$MUS_STATE" && MUS_ACTIVE=true
fi
[ "$MUS_ACTIVE" = "false" ] || exit 0

# 5. Armed + musician CLOSED for this session -> BLOCK and hand off to the skill (which owns the logic).
REASON='🔁 nonstop is ARMED and the musician just CLOSED a milestone — do NOT stop. Run the cc-agent:nonstop skill now to advance the roadmap: it records the closed milestone (mark done or park), picks the next milestone and launches /musician on it, or disarms if the roadmap version is done / the stage is blocked / the musician closed on budget or cancellation. /nonstop-off to disarm; Esc to interrupt.'

if command -v jq >/dev/null 2>&1; then
  jq -n --arg r "$REASON" \
        --arg m "🔁 nonstop -> advancing the roadmap (run cc-agent:nonstop; /nonstop-off to stop)" \
        '{decision:"block", reason:$r, systemMessage:$m}'
else
  printf '%s' "{\"decision\":\"block\",\"reason\":\"$REASON\"}"
fi
exit 0
