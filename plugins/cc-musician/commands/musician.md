---
description: "Hand the project any piece of work — a fix, a change, a feature, a question. /musician is a router: it reads the goal + design, sizes the work, and routes it to the right skill. Flags tune how (--auto acts without asking, --fast, --worktree, --ultracode); the router decides what."
argument-hint: "[task / problem / idea — or nothing to find the work] [--auto] [--fast] [--worktree] [--ultracode]"
---

You were handed this argument:

> $ARGUMENTS

`/musician` is a **router**. It runs in this conversation — there is no arming, no run state, and no
self-perpetuating loop. Read the goal, size the work, route it to the right skill, and let that skill
carry it. **You decide *what* to do; the flags only tune *how*.**

## 1. Ground first

Before deciding anything, read the goal and the design as context:

- `docs/ccharness/roadmap.md` — the North Star + the feature route.
- `docs/ccharness/architecture/` — the architecture.

## 2. Classify the task and route to ONE component

Read the argument and decide what kind of work it is, then route. The router decides the route —
**flags never pick it.** An empty argument means "find the work": route to `cc-script:what-to-do`.

| The task is… | Route to |
| --- | --- |
| a large feature / substantial build | skill `build-large` |
| a medium change | skill `build-medium` |
| a small fix | skill `build-small` |
| designing a new system | `cc-script:architect` |
| a fuzzy pain / "something's off" | `cc-instruments:crux` |
| stuck in a debugging rabbit hole | `cc-instruments:slap` |
| changing the goal / priorities | `cc-script:roadmap-management` |
| "what should I do next" (empty prompt) | `cc-script:what-to-do` |
| rules / cheatsheet / docs / diagrams upkeep | the matching cc-instruments management or diagram skill |

The lower cc-script instruments (`what-to-do`, `how-to-do`, `do`, `refactor-review-test`) are skills in
their own right; the build tiers call them internally. Route straight to one only when the task
obviously **is** that single step.

**When the work is a roadmap item, its section already names the tier:** `## Features` → `build-large`,
`## TODO` → `build-medium`, `## Fixes` → `build-small`.

## 3. North Star gate (build work only)

If the task is build work and `docs/ccharness/roadmap.md` has no `## Product North Star`, don't build:
tell the user to run `/roadmap-management` first to set the goal. Non-build routes (`crux`, `slap`) are
**not** gated — a fuzzy pain can go to `crux` without a North Star.

## 4. Asking vs deciding

- **Default — interactive.** At a genuine fork — including "is this small or medium?" — you MAY ask the
  human with `AskUserQuestion`.
- **`--auto` — decide.** Do **not** ask; resolve every fork yourself.

## 5. Flags — how, not what

Pass the active flags to the chosen skill so it adjusts its weight. Flags stack; they never change the
route.

- `--auto` — act without asking; resolve every fork yourself.
- `--fast` — lighter model, fewer subagents, minimal hardening. Bias to speed.
- `--worktree` — force worktree isolation for the build even on a small/medium change.
- `--ultracode` — maximum fan-out (a Workflow and/or parallel `do` subagents, each worktree-isolated).
  Bias to thoroughness.

## 6. Reconcile after

If the work advanced a roadmap feature, mark it `[x]` under `## Features` (route only — never reorder,
add, or reprioritise). If it shifted the design, update the architecture. Work that touched neither →
no upkeep.
