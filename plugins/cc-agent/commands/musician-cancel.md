---
description: "Stop the running musician loop — the manual brake. Removes the musician state so the Stop hook stops re-feeding, then reports cycles run and the blocked queue."
---

Stop the musician loop. Do exactly this:

1. If `.claude/ccharness/musician/state.json` does **not** exist → say *"No musician is running."* and stop.
2. Read it for the `cycle` count, `entry` mode, and `input`, then **remove `state.json`** (`rm`). This
   lets the next `Stop` end the turn — the hook re-feeds only while that file is present and active.
   (Removing it, rather than flipping a flag, lets a fresh `/musician` re-arm cleanly.)
3. Leave `blocked.jsonl` and `log.jsonl` in place — they are the durable record. Report: **cycles run**,
   the **input** it was working (or "open mode"), and the entries in
   `.claude/ccharness/musician/blocked.jsonl` (each one's `direction` + `reason`). If the queue is empty, say so.
