---
name: build-large
description: "Use for a large feature or substantial build — the full pipeline. Break the work into an ordered task list, build in an isolated worktree, harden, run a real final verification, then reconcile the roadmap."
---

# build-large — the full pipeline

The full weight, for a **real feature or substantial build**. You are a **conductor, not a performer**:
you break the work down, dispatch each unit to a subagent, and judge — through a real verification —
when it is truly done. You **never write product code yourself**; every code change goes through a
`cc-script:do` subagent. Your own bookkeeping — the task list, roadmap marks — you write directly.

The work is carried in the conversation, turn by turn. There is no armed run and no self-perpetuating
loop — just the pipeline below, driven to a verified finish.

## Decompose into a task list

Break the work into an **ordered list of concrete subtasks**, each a single dispatched unit — a think
(`cc-script:how-to-do` / `cc-instruments:crux`), the **build segment**, or the final **verify**. Mirror
the list to the native task tool so the human can see it.

**The building is ONE segment, not one task per commit.** A single `cc-script:do` dispatch, in one
worktree, builds all the pieces and hardens them once at the end. So the list is the think tasks the
work genuinely needs, then **one** build task, then verify. The **last task is ALWAYS a real
verification** of the observable outcome — that single rule is what keeps "implemented = done" from
sneaking in.

## Build in an isolated worktree

Every build runs in its own throwaway git worktree, so the build never dirties the main tree and only
the finished, committed result lands on local `main`.

- **Capture the base first:** `BASE = git rev-parse HEAD`.
- **Dispatch isolated, on the strong model:** dispatch the build subagent (`cc-script:do`) with the
  Agent tool's `isolation:"worktree"` and `model:"opus"`. Tell it its **first action** is
  `git reset --hard <BASE>` (the harness may cut the worktree from a stale base), then it writes the
  code + smoke for every piece and chains `cc-script:refactor-review-test`, which makes **one** local
  commit inside the worktree.
- **You stay on `main`.** Never enter the worktree yourself.
- **Integrate fast-forward-only.** From the main tree, fast-forward the worktree's branch onto local
  `main` (`git merge --ff-only <worktreeBranch>`), then remove the worktree
  (`git worktree remove <worktreePath>`). If it won't fast-forward — the base moved, or you're not on
  `main` — **discard and rebuild this step; never merge stale work silently.** A wall you can't get
  past is the human's call to stop, not a self-close.

## Verification — the gate that keeps "done" honest

The last task is a REAL dispatched check of the observable outcome — run the app, run the full tests,
check the thing the work was meant to make true. Not a glance at the diff.

- **Verify passes** → the list is done; the feature is built.
- **Verify fails** → do **not** call it done. **Append fix task(s)** and keep going. The work closes
  only after a real verification has passed.

## Roadmap upkeep — the route, never the goal

When the work maps to `docs/ccharness/roadmap.md`, mark finished features `[x]` under `## Features`
when they are observably done. Never reorder features, add a future feature, or reprioritise — that
layer is `roadmap-management`'s, set with the human. If the work reveals the **goal itself** is wrong,
don't act on it — surface it (*"the real target looks different — revise via `/roadmap-management`?"*)
and let the human decide.

## Flags

- `--fast` — fewer / cheaper passes where it's safe to.
- `--worktree` — already the default here.
- `--ultracode` — **maximum fan-out:** author a **Workflow** and/or dispatch **parallel** `cc-script:do`
  subagents, each with its own `isolation:"worktree"`, each fast-forward-integrated as it lands. Verify
  findings adversarially. This is the one exception to the single-build-segment rule.
- `--auto` — resolve every fork yourself; no `AskUserQuestion`. Without it, ask the human at a genuine
  fork (an ambiguous approach, a real design choice).

## Rules

Read and obey `.claude/rules/*.md` yourself, and tell **every** dispatched subagent — brain and build —
to read and obey them before doing the work. The rules are git-tracked, so they ride into every build
worktree; point each subagent at the files rather than pasting their text.
