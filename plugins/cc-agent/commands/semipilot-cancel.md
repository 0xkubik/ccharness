---
description: "Stop the running semipilot loop — the manual brake. Removes the semipilot state so the Stop hook stops re-feeding, then reports cycles run and the blocked queue."
---

Stop the semipilot loop. Do exactly this:

1. If `.claude/ccharness/semipilot/state.json` does **not** exist → say *"No semipilot is running."* and stop.
2. Read it for the `cycle` count and `target_milestone`, then **remove `state.json`** (`rm`). This lets the
   next `Stop` end the turn — the hook re-feeds only while that file is present and active. (Removing it,
   rather than flipping a flag, lets a fresh `/semipilot` re-arm cleanly.)
3. Leave `blocked.jsonl` and `log.jsonl` in place — they are the durable record. Report: **cycles run**,
   the **target milestone**, and the entries in `.claude/ccharness/semipilot/blocked.jsonl` (each one's
   `direction` + `reason`). If the queue is empty, say so.
