---
description: "Set up or revise a product's long-horizon direction — the grounding loop. Captures the product's North Star (goal-setting) into CLAUDE.md, then lays out a flat, ordered list of features (built top to bottom) from where the product is now to that goal. Run once up front; re-run to revise. Every other cc-tools skill routes here when no North Star exists; what-to-do then biases its menu toward the current frontier."
argument-hint: "[no arguments needed — re-run any time to revise]"
---

Invoke the `find-goal` skill (the grounding loop) with this scope:

> $ARGUMENTS

find-goal is the harness's **grounding front door**. On a fresh repo it captures the product's
**North Star** (vision · core problem · level) into `CLAUDE.md`, then **offers** to lay out the
**roadmap** — a **flat, ordered list of features** (`.claude/ccharness/roadmap.md`), built top to
bottom, from where the product is now to that North Star. Other product skills (`what-to-do`, `how-to-do`, `do`,
`musician`) route here when no North Star exists. Re-run any time to revise — the goal or the roadmap;
find-goal reads what already exists and adapts, no flag needed.
