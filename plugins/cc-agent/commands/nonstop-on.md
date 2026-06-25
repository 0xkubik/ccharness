---
description: "Arm nonstop — the musician walks the roadmap milestone by milestone instead of stopping after one. Writes the nonstop marker, then launches the first piece in open mode. Disarm with /nonstop-off; Esc interrupts."
---

Arm nonstop roadmap-walking. Do exactly this:

1. **Require a roadmap.** No `.claude/ccharness/roadmap.md` → say *"No roadmap yet — run `/find-goal`
   first, then `/nonstop-on`."* and stop. Nonstop walks the roadmap; without one there is nothing to walk.
2. **Write the marker** `.claude/ccharness/nonstop/state.json` atomically (temp file + `mv`; create the
   directory if missing):
   ```json
   { "on": true, "session_id": "<$CLAUDE_CODE_SESSION_ID>", "armed_at": "<UTC now>" }
   ```
3. **Announce** that nonstop is armed, then **launch the first piece**: invoke `/musician` with **no
   prompt** (open mode). The musician picks the next roadmap milestone itself and drives it to done. From
   there the nonstop Stop hook re-launches `/musician` after each piece closes — until the musician finds
   nothing left (it declines) or you disarm.

Nonstop never decides the work — the musician's own brain does. To stop: `/nonstop-off` (finishes the
current milestone, then stops) or **Esc** (interrupt now). The hard mid-milestone brake remains
`/musician-cancel`.
