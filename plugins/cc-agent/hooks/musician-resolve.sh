# musician run resolution — sourced by the Stop, observe, and nonstop hooks.
#
# Each musician run lives in its own folder, runs/<run-id>/, so many runs in one repo don't
# collide. A tiny per-session pointer, by-session/<session_id>, names the active run for a session,
# so a hook can find THIS session's run in O(1) from the session_id on its stdin.
#
# Pure bash builtins (regex, $(<file)) — works even with no jq/grep/cat on PATH, so the hooks that
# source this stay tool-independent.
MUS_DIR=".claude/ccharness/musician"

# mus_session_from_stdin <raw-stdin-json>  ->  echoes the session_id (jq if present, else bash regex)
mus_session_from_stdin() {
  local raw="$1" sid=""
  if command -v jq >/dev/null 2>&1; then
    sid="$(printf '%s' "$raw" | jq -r '.session_id // ""' 2>/dev/null || true)"
  fi
  if [ -z "$sid" ]; then
    local re='"session_id"[[:space:]]*:[[:space:]]*"([^"]+)"'
    [[ $raw =~ $re ]] && sid="${BASH_REMATCH[1]}"
  fi
  printf '%s' "$sid"
}

# mus_run_dir <session_id>  ->  echoes runs/<run-id> for that session's active run, or "" if none.
mus_run_dir() {
  local sid="$1"
  [ -n "$sid" ] || return 0
  local ptr="$MUS_DIR/by-session/$sid"
  [ -f "$ptr" ] || return 0
  local rid; rid="$(<"$ptr")"
  [ -n "$rid" ] || return 0
  printf '%s' "$MUS_DIR/runs/$rid"
}
