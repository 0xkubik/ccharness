---
name: build-medium
description: "Use for a medium change — real work across a few pieces, but not a whole feature. Lighter than the full pipeline: one or two build passes and a light check, no heavy task-list decomposition."
---

# build-medium — real work, not a whole feature

The middle weight. Use it for a change bigger than a one-line fix but smaller than a feature — a
handful of edits that hang together into one coherent change. No shaping phase, no formal task list;
just do the work in a pass or two and check it.

**If it grows into a real feature** — several deliverables, a fork worth deciding, a build worth
hardening and verifying properly — hand up to `build-large`. **If it turns out trivial**, drop to
`build-small`.

## How it works

1. **Build it in one or two `cc-script:do` passes.** Code changes go through `do`, not inline — this
   tier is big enough that `do`'s smoke and never-commit-unverified guarantees earn their keep. Split
   into a second `do` pass only if the work genuinely has two distinct pieces.
2. **Light check.** Confirm the change works — run the relevant app path or tests. Not the full
   hardening pipeline; a real but proportionate check.
3. **Reconcile.** If the change advanced a roadmap feature, mark it `[x]` under `## Features` (route,
   never goal — never reorder, add, or reprioritise features).

## Isolation

Default to dispatching the `cc-script:do` with the Agent tool's `isolation:"worktree"` when the change
touches enough that dirtying the main tree mid-flight is a real risk. A small, self-contained medium
change may run without it. `--worktree` forces isolation either way.

## Flags

- `--fast` — lighter model, fewer passes, minimal check.
- `--worktree` — force worktree isolation for the build.
- `--ultracode` — fan out `do` across the change's independent pieces (each its own
  `isolation:"worktree"`).
- `--auto` — resolve every fork yourself; no `AskUserQuestion`. Without it, ask the human at a genuine
  fork.

## Rules

Read and obey `.claude/rules/*.md`, and tell every dispatched subagent to read and obey them too.

There is no run bookkeeping — the work is carried in the conversation, not an armed loop.
