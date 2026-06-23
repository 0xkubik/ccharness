---
description: "Set product direction — survey a product and surface where it could go next as a ranked menu of moves (add / finish / rebuild / refactor), scored against the product's goal. Runs with or without a prompt; first run captures the product's North Star into CLAUDE.md. Emits a menu and decides nothing — you pick, then grill-it decides how."
argument-hint: "[optional theme or area — omit for a full survey]"
---

Invoke the `point-it` skill (the direction loop) with this scope:

> $ARGUMENTS

point-it is the mouth of the funnel (point-it → grill-it → implement-it). It needs no setup and
runs with or without an argument. On its **first run** in a repo it has no destination to aim
at, so it captures the product's **North Star** (vision, core problem, level) into `CLAUDE.md`
and stops. On every run after, it reads that North Star and proposes a **ranked menu of
directions** toward it — then you pick one and hand it to `/grill-it` to decide *how*.
