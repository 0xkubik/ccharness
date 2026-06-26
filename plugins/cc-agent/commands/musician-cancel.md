---
description: "Stop the running musician loop — the manual brake. Clears this session's run pointer so the Stop hook stops re-feeding, marks the run cancelled, then reports cycles run and the blocked queue."
---

Stop the musician loop for THIS session. Do exactly this:

1. Resolve this session's run: `RID="$(cat .claude/ccharness/musician/by-session/$CLAUDE_CODE_SESSION_ID 2>/dev/null)"`.
   If there is no pointer (empty `RID`) → say *"No musician is running."* and stop.
2. Let `RUN=.claude/ccharness/musician/runs/$RID`. Read `RUN/state.json` for the `cycle` count,
   `entry` mode, and `input` (the original prompt it was handed).
3. **Mark the run closed and release the hook:** set `active:false`, `status:"cancelled"`, and
   `outcome:"cancelled"` in `RUN/state.json` (atomic: temp file + `mv`), then **remove the pointer**
   `.claude/ccharness/musician/by-session/$CLAUDE_CODE_SESSION_ID` (`rm`). Either alone frees the
   Stop hook; doing both records the cancellation *and* lets a fresh `/musician` arm cleanly.
4. Leave `RUN/` itself in place — `state.json`, `blocked.jsonl`, `log.jsonl`, and `live.log` are the
   durable record of this run. Report: **cycles run**, the **input** it was working (or "open
   mode"), and the entries in `RUN/blocked.jsonl` (each one's `direction` + `reason`). If the queue
   is empty, say so.
