---
description: "Stop the running ccharness autopilot loop — the one manual brake. Removes the autopilot state so the Stop hook stops re-feeding, then reports how many cycles ran and what's waiting in the blocked review queue."
---

Stop the ccharness autopilot loop. This is the **only** thing that ends it. Do exactly this:

1. If `.claude/ccharness/autopilot/state.json` does **not** exist → say *"No autopilot is running."*
   and stop.
2. Read it for the `cycle` count, then **remove `state.json`** (`rm`). This is what lets the next
   `Stop` end the session — the hook re-feeds only while that file is present and active. (Removing
   it, rather than flipping a flag, also lets a fresh `/autopilot` re-arm cleanly later.)
3. Leave `blocked.jsonl` and `log.jsonl` in place — they are the durable record. Report: **cycles
   run**, and the entries in `.claude/ccharness/autopilot/blocked.jsonl` (the tasks the loop skipped
   for your review — list each one's `direction` + `reason`). If the queue is empty, say so.
