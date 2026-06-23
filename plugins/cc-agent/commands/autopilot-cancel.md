---
description: "Stop the running autopilot loop — the manual brake. Removes the autopilot state AND any in-flight nested semipilot so the Stop hooks stop re-feeding, then reports the milestone it was on, meta-steps run, and the parked-milestone queue."
---

Stop the autopilot loop. This is the manual brake. Do exactly this:

1. If `.claude/ccharness/autopilot/state.json` does **not** exist → say *"No autopilot is running."*
   and stop.
2. Read it for the **current milestone** (`current_milestone`), then **remove `state.json`** (`rm`).
   This is what lets the next `Stop` end the session — the meta-loop hook re-feeds only while that
   file is present and active. (Removing it, rather than flipping a flag, also lets a fresh
   `/autopilot` re-arm cleanly later.)
3. **Also remove `.claude/ccharness/semipilot/state.json` if it exists.** autopilot arms a nested
   semipilot for each milestone; if one is mid-milestone, its **own** Stop hook would keep re-feeding
   even after the outer state is gone. Removing it stops the in-flight milestone too — this is why
   `/autopilot-cancel` (not just `/semipilot-cancel`) fully stops an autopilot run.
4. Leave the `log.jsonl` files and `blocked.jsonl` in place — they are the durable record.
5. Report: the **milestone it was on** (`current_milestone` from step 2), the number of **meta-steps
   run** (count the lines in `.claude/ccharness/autopilot/log.jsonl`), and the **parked milestones**
   in `.claude/ccharness/autopilot/blocked.jsonl` (list each entry's `milestone` + `reason` — these
   are milestones the loop gave up on and skipped, for your review). If the parked queue is empty,
   say so.
