---
description: "Drive the cc-tools funnel toward ONE roadmap milestone and stop when its `done when:` is met (or give up after N no-progress cycles / a cycle cap). The bounded unit; autopilot wraps it. Needs a roadmap — run /find-goal first."
argument-hint: "[milestone id e.g. M3 — default: current] [--give-up-after N] [--max-cycles N] [--ultracode]"
---

Invoke the `semipilot` skill to arm and run the BOUNDED goal-seeking loop, with this argument:

> $ARGUMENTS

`--ultracode` forces maximum parallelism in the build step (mandatory Workflow + parallel subagents +
git worktrees). There is no spend flag on semipilot — spend is an autopilot-level never-stop policy.

semipilot takes ONE roadmap milestone as its goal and drives the funnel (what-to-do → how-to-do →
do) toward it, **stopping itself** the moment the milestone's `done when:` is met. It has a
second exit — **give up** after N cycles with no progress (default 3) or a hard cycle cap (default 20),
the token-burn backstop. No milestone id → the current (first unchecked in document order) milestone. It needs a roadmap;
with none it routes you to **`/find-goal`**. Stop it early with **`/semipilot-cancel`**.
