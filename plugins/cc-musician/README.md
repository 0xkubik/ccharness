# cc-musician

The router layer of the cc-* harness. `/musician` is **one entry point for any piece of work** — a
small fix, a medium change, a whole feature, or a question. It reads the goal and the design, sizes the
task, and routes it to the right skill. The router decides *what*; flags only tune *how*. It runs in
the conversation — there is no arming, no run state, and no self-perpetuating loop.

## `/musician <task> [flags]`

1. **Grounds** in the goal (`docs/ccharness/roadmap.md` — the North Star + feature route) and the
   design (`docs/ccharness/architecture/`).
2. **Classifies** the task and routes it to one component.
3. **Reconciles** after: if the work advanced a roadmap feature or shifted the design, it updates the
   roadmap / architecture. Otherwise nothing.

An empty prompt means "find the work" — it routes to `what-to-do`.

## The routes

| The task is… | Route to |
| --- | --- |
| a large feature / substantial build | `build-large` |
| a medium change | `build-medium` |
| a small fix | `build-small` |
| designing a new system | `cc-script:architect` |
| a fuzzy pain / "something's off" | `cc-instruments:crux` |
| stuck in a debugging rabbit hole | `cc-instruments:slap` |
| changing the goal / priorities | `cc-script:roadmap-management` |
| "what should I do next" | `cc-script:what-to-do` |
| rules / cheatsheet / docs / diagrams upkeep | the matching cc-instruments skill |

The whole plugin menu is reachable — the table is the common routes, not the limit.

## The three build tiers

Each is its own skill and assembles its own weight for the concrete task:

- **build-large** — the full pipeline: decompose into a task list, build in an isolated worktree,
  harden, run a real final verification, reconcile the roadmap. Code changes go through a `do`
  subagent; nothing is "done" until a real check passes.
- **build-medium** — lighter: one or two `do` passes and a proportionate check, no heavy
  decomposition.
- **build-small** — lightest: make the fix and confirm nothing broke, minimal ceremony.

## Flags — how, not what

- `--auto` — act without asking; resolve every fork yourself. (Default: ask at a genuine fork.)
- `--fast` — lighter model, fewer subagents, minimal hardening.
- `--worktree` — force worktree isolation for the build even on a small/medium change.
- `--ultracode` — maximum fan-out (a Workflow and/or parallel `do` subagents, each worktree-isolated).

Flags stack; they never change the route.

## Build isolation

When a tier isolates a build, it uses the Agent tool's `isolation:"worktree"` directly and
fast-forward-integrates the result onto local `main`. There is no helper script and no run state.

Depends on **cc-script** and **cc-instruments**.
