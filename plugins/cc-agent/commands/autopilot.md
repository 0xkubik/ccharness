---
description: "Walk the roadmap milestone by milestone via semipilot — arms a fresh /semipilot on the current milestone, and when it finishes advances to the next (with a retry-once, then a stage-test: same-stage sibling → park+advance, else hard-stop). Requires a roadmap (/chart-it first). Stops on /autopilot-cancel OR a hard dependency block."
argument-hint: "[optional focus — passed to each semipilot cycle]"
---

Invoke the `autopilot` skill to **arm the meta-loop**, with this focus:

> $ARGUMENTS

autopilot is a **meta-loop over semipilot**: it arms `/semipilot` on the current milestone, waits
for it to finish, then advances to the next — walking the roadmap milestone by milestone. The funnel
logic (point-it → grill-it → implement-it) lives inside semipilot; autopilot only decides **which
milestone to run next, and what to do when one fails.**

**Requires a roadmap.** No North Star → run `/chart-it` first. North Star but no roadmap → run
`/chart-it` to chart the route. (The old "drive directly toward the North Star without a roadmap"
path is removed.)

**Give-up ladder** — when a semipilot gives up on a milestone, autopilot:
1. **Retries once** (re-arms a fresh semipilot on the same milestone).
2. If it gives up again, the **stage test** reads the dependency straight off the roadmap's layers
   (no guessing): is another open milestone in the **same `## Stage`** as the stuck one?
   - **Independent** (a same-stage sibling is still open) → parks the stuck milestone (adds it to the
     parked queue) and advances to that sibling.
   - **Dependent** (the stuck one is the last open milestone in its stage → the next work is in a later
     stage that needs this one) → **HARD STOP**: sets itself inactive, reports the stuck milestone and
     the parked queue, and ends the session.

**Two ways it stops:**
- **`/autopilot-cancel`** — the manual brake, works at any time.
- **Hard dependency block** — a dependent milestone proved unbeatable after a retry; autopilot
  stops itself and reports.

A `Stop` hook re-feeds the meta-step between milestones; a separate `Stop` hook drives each
semipilot cycle. Exactly one hook is active at a time (the two-hook partition).
