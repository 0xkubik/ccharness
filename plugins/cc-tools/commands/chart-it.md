---
description: "Set up or revise a product's long-horizon direction — the grounding loop. Captures the product's North Star (goal-setting) into CLAUDE.md, then charts a layered roadmap of lightweight milestones (sequential stages, parallel milestones within each) from where the product is now to that goal. Run once up front; re-run to revise. Every other cc-tools skill routes here when no North Star exists; point-it then biases its menu toward the current frontier."
argument-hint: "[--reground to revise the North Star, or omit]"
---

Invoke the `chart-it` skill (the grounding loop) with this scope:

> $ARGUMENTS

chart-it is the harness's **grounding front door**. On a fresh repo it captures the product's
**North Star** (vision · core problem · level) into `CLAUDE.md`, then **offers** to chart the
**roadmap** — a *layered* route of lightweight milestones (`.claude/ccharness/roadmap.md`): ordered
**stages**, with **parallel milestones inside each** (`order → split stages; independent → same
stage`), from where the product is now to that North Star. Other product skills (`point-it`, `grill-it`, `implement-it`,
`autopilot`) route here when no North Star exists. Re-run any time to revise the roadmap, or pass
`--reground` to revise the North Star itself as the route drifts.
