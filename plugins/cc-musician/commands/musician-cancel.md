---
description: "Stop the running musician loop — the manual brake. Clears this session's run pointer so the Stop hook stops re-feeding, marks the run cancelled, then reports task progress."
---

Stop the musician loop for THIS session. Do exactly this:

1. Resolve this session's run: `RID="$(cat .claude/ccharness/musician/by-session/$CLAUDE_CODE_SESSION_ID 2>/dev/null)"`.
   If there is no pointer (empty `RID`) → say *"No musician is running."* and stop.
2. Let `RUN=.claude/ccharness/musician/runs/$RID`. Read `RUN/state.json` for the `tasks` progress
   (how many `completed` of the total), `entry` mode, and `input` (the original prompt it was handed).
3. **Mark the run closed and release the hook:** set `active:false` and `outcome:"cancelled"` in
   `RUN/state.json` (atomic: temp file + `mv`), then **remove the pointer**
   `.claude/ccharness/musician/by-session/$CLAUDE_CODE_SESSION_ID` (`rm`). Either alone frees the
   Stop hook; doing both records the cancellation *and* lets a fresh `/musician` arm cleanly.
4. **Clean up build isolation:** run `git worktree prune` (clears stale entries for already-removed
   worktrees). If a build was mid-flight when cancelled, a worktree may remain under
   `.claude/worktrees/` — list any with `git worktree list` and report them so the user can remove
   them (`git worktree remove --force <path>`). Don't force-remove blindly: another session's
   musician may own one.
5. Leave `RUN/` itself in place — `state.json`, `log.jsonl`, and `live.log` are the
   durable record of this run. Report: **tasks done** (N of M), the **input** it was working (or "open
   mode"), and any **leftover worktree** from step 4.
