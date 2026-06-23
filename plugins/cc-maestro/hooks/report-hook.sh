#!/usr/bin/env bash
# ccmaestro push reporter: forwards Stop/SubagentStop/Notification events to the
# configured report_endpoint so an external agent (hermes) hears about agents
# without polling. No-op when no endpoint is configured.
set -euo pipefail
INPUT="$(cat 2>/dev/null || true)"
CFG="${CCMAESTRO_HOME:-$HOME/.ccmaestro}/config.json"
[ -f "$CFG" ] || exit 0
URL="$(jq -r '.report_endpoint // ""' "$CFG" 2>/dev/null || true)"
[ -n "$URL" ] || exit 0
SID="$(printf '%s' "$INPUT" | jq -r '.session_id // ""' 2>/dev/null || true)"
EVENT="$(printf '%s' "$INPUT" | jq -r '.hook_event_name // ""' 2>/dev/null || true)"
CWD="$(printf '%s' "$INPUT" | jq -r '.cwd // ""' 2>/dev/null || true)"
curl -fsS -m 5 -X POST -H 'Content-Type: application/json' \
  -d "{\"event\":\"$EVENT\",\"session_id\":\"$SID\",\"cwd\":\"$CWD\"}" "$URL" >/dev/null 2>&1 || true
exit 0
