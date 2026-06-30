#!/usr/bin/env bash
# cc-instruments reminder (UserPromptSubmit): every Nth real user prompt, re-surface a short
# cheat-sheet of the tools and rules available in this project, right before the new prompt
# where it's most visible — so they don't fade from the model's attention mid-session.
#
# Dumb by design: it only prints a file that the cheatsheet-management skill generated. No file →
# no-op, so shipping the hook is harmless until that skill has run. Delete or rename the file to turn
# the reminder off.
#
# "Every Nth" is counted from the session transcript, not a counter file, so concurrent sessions
# in the same repo never clobber each other: each session has its own transcript. Real prompts
# carry a "promptSource" key; tool results do not — so that key is the exact prompt count.
set -euo pipefail

SHEET=".claude/ccharness/cheatsheet.md"
EVERY=3

# A UserPromptSubmit hook must always exit 0 (non-zero surfaces an error every prompt; exit 2
# blocks submission). Cheap guards first, before anything that can fail.
[ -f "$SHEET" ] || exit 0

RAW="$(cat 2>/dev/null || true)"

# transcript_path from stdin — jq if present, else a bash-regex fallback (mirrors the musician
# hooks' tool-independent parsing).
TPATH=""
if command -v jq >/dev/null 2>&1; then
  TPATH="$(printf '%s' "$RAW" | jq -r '.transcript_path // ""' 2>/dev/null || true)"
fi
if [ -z "$TPATH" ]; then
  re='"transcript_path"[[:space:]]*:[[:space:]]*"([^"]+)"'
  [[ $RAW =~ $re ]] && TPATH="${BASH_REMATCH[1]}"
fi
[ -n "$TPATH" ] && [ -f "$TPATH" ] || exit 0

# grep -c prints 0 AND exits 1 on no matches — the `|| N=0` keeps set -e from aborting and
# leaves N a clean integer.
N="$(grep -c '"promptSource":' "$TPATH" 2>/dev/null)" || N=0

if [ "$N" -gt 0 ] && [ $((N % EVERY)) -eq 0 ]; then
  cat "$SHEET"
fi
exit 0
