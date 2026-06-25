---
description: "Arm nonstop — the musician walks the roadmap milestone by milestone instead of stopping after one. Writes the nonstop marker, then launches the first milestone. Disarm with /nonstop-off; Esc interrupts."
---

Arm nonstop roadmap-walking. Do exactly this:

1. **Require a roadmap.** No `.claude/ccharness/roadmap.md` → say *"No roadmap yet — run `/find-goal`
   first, then `/nonstop-on`."* and stop. Nonstop walks the roadmap; without one there is nothing to walk.
2. **Write the marker** `.claude/ccharness/nonstop/state.json` atomically (temp file + `mv`; create the
   directory if missing):
   ```json
   { "on": true, "session_id": "<$CLAUDE_CODE_SESSION_ID>", "armed_at": "<UTC now>", "current": null }
   ```
3. **Announce** that nonstop is armed, then **invoke the `cc-agent:nonstop` skill** to pick the first
   milestone and launch the musician on it. From there the nonstop Stop hook advances automatically after
   each milestone closes.

To stop: `/nonstop-off` (finishes the current milestone, then stops) or **Esc** (interrupt now). The
hard mid-milestone brake remains `/musician-cancel`.
