---
description: "Drive the cc-tools funnel toward ONE roadmap milestone and stop when its `done when:` is met (or give up after N no-progress cycles / a cycle cap). The bounded unit; autopilot wraps it. Needs a roadmap — run /chart-it first."
argument-hint: "[milestone id e.g. M3 — default: current] [--give-up-after N] [--max-cycles N]"
---

Invoke the `semipilot` skill to arm and run the BOUNDED goal-seeking loop, with this argument:

> $ARGUMENTS

semipilot takes ONE roadmap milestone as its goal and drives the funnel (point-it → grill-it →
implement-it) toward it, **stopping itself** the moment the milestone's `done when:` is met. It has a
second exit — **give up** after N cycles with no progress (default 3) or a hard cycle cap (default 20),
the token-burn backstop. No milestone id → the current (first unchecked) milestone. It needs a roadmap;
with none it routes you to **`/chart-it`**. Stop it early with **`/semipilot-cancel`**.
