---
description: "Hand one concrete, well-scoped task to the strict executor — it drives the task from understood → built → smoke-checked through a gated pipeline, then hands off to refactor-review-test (which verifies, refactors, reviews, tests, and commits), refusing fork-laden tasks instead of guessing."
argument-hint: "<task>"
---

Invoke the `do` skill (the strict executor pipeline) with this task:

> $ARGUMENTS

do is the foot of the funnel and builds from the product's goal outward, so it first
checks the product is grounded: **no North Star → it routes you to `/roadmap-management`** to set one, then
re-issue the task (arriving from how-to-do or under the musician, the North Star already exists). Past
that, it will **refuse to start** rather than guess: an unresolved technical fork hands off to
`/how-to-do` (the funnel's decision loop); a business / non-technical one it declines outright; a
merely vague task goes to `superpowers:brainstorming`.
