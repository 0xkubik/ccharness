---
name: build-small
description: "Use for a small, low-risk code change — a fix or tweak that is clear and self-contained. The lightest build tier: make the change and confirm nothing broke, minimal ceremony."
---

# build-small — the light touch

The lightest way to build. Use it for a change that is **small, clear, and low-risk**: a one-liner, a
typo, a narrow fix, a tweak you already understand. No task list, no shaping, no orchestration — just
make the change and check it holds.

**If it isn't actually small, stop and hand up.** The moment the change spreads across several pieces,
needs real thinking, or carries risk you can't eyeball, this is the wrong tier: say so and hand back to
the router for `build-medium` or `build-large`. Forcing a real feature through here is the mistake this
tier invites.

## How it works

1. **Make the change.** A direct `Edit`/`Write` is fine at this tier. If the change would genuinely
   benefit from a smoke-checked, never-commit-unverified pass, dispatch a single `cc-script:do`
   subagent instead — but don't reach for it on a trivial edit.
2. **Confirm nothing broke.** Run the obvious smoke — the touched thing, or the one relevant test. A
   quick check, not a full verification suite.
3. **Reconcile if it mattered.** If the change happened to finish a roadmap feature, mark it `[x]`
   under `## Features` (route only — never reorder, add, or reprioritise). Most small fixes touch
   nothing here; then skip it.

## Flags

- `--fast` — go faster: skip the smoke on a truly trivial edit.
- `--worktree` — make the change in an Agent `isolation:"worktree"` dispatch instead of inline.
- `--ultracode` — rarely meaningful this small; only fan out if there really are independent
  sub-changes.
- `--auto` — don't ask; just make the change.

## Rules

Read and obey `.claude/rules/*.md`. If you dispatch a subagent, tell it to read and obey them too.

There is no run bookkeeping here — this is a one-shot in the conversation. Nothing to arm, nothing to
close.
