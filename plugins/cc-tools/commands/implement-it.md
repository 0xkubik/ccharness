---
description: "Hand one concrete, well-scoped task to the strict executor — it drives the task from understood → built → verified → committed through a gated 0→6 pipeline, refusing fork-laden tasks instead of guessing."
argument-hint: "<task>"
---

Invoke the `implement-it` skill (the strict executor pipeline) with this task:

> $ARGUMENTS

implement-it is the foot of the funnel and builds from the product's goal outward, so it first
checks the product is grounded: **no North Star → it routes you to `/chart-it`** to set one, then
re-issue the task (arriving from grill-it or under autopilot, the North Star already exists). Past
that, it will **refuse to start** rather than guess: an unresolved business/technical fork hands off
to `/grill-it` (the funnel's decision loop), while a merely vague task goes to
`superpowers:brainstorming`.
