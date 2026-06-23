---
description: "Hand one concrete, well-scoped task to the strict executor — it drives the task from understood → built → verified → committed through a gated 0→6 pipeline, refusing fork-laden tasks instead of guessing."
argument-hint: "<task>"
---

Invoke the `implement-it` skill (the strict executor pipeline) with this task:

> $ARGUMENTS

No setup is required — implement-it is zero-config and works on any task or repo. It will
**refuse to start** rather than guess: an unresolved business/technical fork hands off to
`/grill-it` (the funnel's decision loop), while a merely vague task goes to
`superpowers:brainstorming`.
