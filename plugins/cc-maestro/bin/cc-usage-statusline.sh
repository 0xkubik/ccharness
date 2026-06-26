#!/usr/bin/env bash
# cc-maestro usage bridge — a statusLine wrapper that captures Claude Code's usage limits.
#
# A running Claude Code session cannot query its own remaining subscription budget: /usage is
# TUI-only, and there is no CLI flag, file, hook field, or env var that exposes it. The ONE
# channel that sees it is the statusLine stdin payload, which carries `rate_limits.five_hour` and
# `rate_limits.seven_day` (used_percentage + resets_at). This script sits in `statusLine.command`,
# tees that payload into the GLOBAL ~/.claude/ccharness/usage.json (honoring $CLAUDE_CONFIG_DIR),
# then forwards it verbatim to your real status line so your display is unchanged. The path is
# global, not per-project, because the rate limits are account-wide: a single shared file lets a
# cc-agent musician in ANY project read it to gate expensive work on remaining headroom.
#
# Install: set settings.json -> statusLine.command to this script's path. Your previous status
# line keeps working: it runs as the downstream, taken from $CC_USAGE_DOWNSTREAM (default
# "ccstatusline" if on PATH). Set CC_USAGE_DOWNSTREAM="" to render nothing downstream.
#
# Best-effort and fail-open: any failure here must never break or blank-error your status line.
set -u

PAYLOAD="$(cat 2>/dev/null || true)"

# --- capture rate_limits → usage.json (only when present, so we never clobber last-good data
#     with the empty payloads sent before the first API response / for non-Pro-Max accounts) ---
write_usage() {
  if command -v python3 >/dev/null 2>&1; then
    CC_USAGE_PAYLOAD="$PAYLOAD" python3 -c '
import json, os, sys, tempfile, datetime
try:
    d = json.loads(os.environ.get("CC_USAGE_PAYLOAD", ""))
except Exception:
    sys.exit(0)
rl = d.get("rate_limits")
if not rl:
    sys.exit(0)  # no usage data this render — keep the last good snapshot
cfg = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
out_dir = os.path.join(cfg, "ccharness")
try:
    os.makedirs(out_dir, exist_ok=True)
    body = {
        "captured_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "five_hour": rl.get("five_hour"),
        "seven_day": rl.get("seven_day"),
        "source": "cc-maestro/usage-statusline",
    }
    fd, tmp = tempfile.mkstemp(dir=out_dir, prefix=".usage.", suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(body, f)
    os.replace(tmp, os.path.join(out_dir, "usage.json"))
except Exception:
    pass
' 2>/dev/null
    return
  fi
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$PAYLOAD" | jq -e '.rate_limits != null' >/dev/null 2>&1 || return
    local od ts tmp
    od="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/ccharness"
    mkdir -p "$od" 2>/dev/null || return
    ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    tmp="$od/.usage.$$.json"
    printf '%s' "$PAYLOAD" | jq -c --arg ts "$ts" \
      '{captured_at:$ts, five_hour:.rate_limits.five_hour, seven_day:.rate_limits.seven_day, source:"cc-maestro/usage-statusline"}' \
      > "$tmp" 2>/dev/null && mv "$tmp" "$od/usage.json" 2>/dev/null
    return
  fi
  # neither python3 nor jq — skip the capture, still render the status line below.
}

# --- forward the payload to your real status line so the display is untouched ---
render_downstream() {
  local cmd="${CC_USAGE_DOWNSTREAM-ccstatusline}"
  [ -n "$cmd" ] || return 0                       # explicitly disabled → render nothing
  command -v "${cmd%% *}" >/dev/null 2>&1 || return 0  # downstream not installed → nothing
  printf '%s' "$PAYLOAD" | $cmd
}

write_usage
render_downstream
exit 0
