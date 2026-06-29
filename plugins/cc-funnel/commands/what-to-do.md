---
description: "Set product direction — survey a product and surface where it could go next as a ranked menu of moves (add / finish / rebuild / refactor), scored against the product's goal. Runs with or without a prompt. Requires the product's North Star (set once via /find-goal) — without it, routes you there; with it, reads the North Star and the roadmap (if any) and biases the menu toward the current frontier (the next unbuilt feature). Emits a menu and decides nothing — you pick, then how-to-do decides how."
argument-hint: "[optional theme or area — omit for a full survey]"
---

Invoke the `what-to-do` skill (the direction loop) with this scope:

> $ARGUMENTS

what-to-do is the mouth of the funnel (what-to-do → how-to-do → do → refactor-review-test), grounded by `/find-goal`
upstream. It runs with or without an argument, but it **requires the product's North Star**: if none
is set, it routes you to **`/find-goal`** (which captures it) and stops. With the North Star present,
it reads it — plus the roadmap, if one exists, **biasing the menu toward the current frontier** (the
next unbuilt feature in the list) — and proposes a **ranked menu of
directions** toward the goal; then you pick one and hand it to
`/how-to-do` to decide *how*.
