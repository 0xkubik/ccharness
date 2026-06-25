---
description: "Disarm nonstop — the musician finishes the current milestone and then stops instead of picking the next. The hard mid-milestone brake is Esc (or /musician-cancel)."
---

Disarm nonstop. Do exactly this:

1. If `.claude/ccharness/nonstop/state.json` does **not** exist → say *"Nonstop is not armed."* and stop.
2. Read it for the `current` milestone (for the report), then **remove the file** (`rm`). The nonstop Stop
   hook becomes a no-op, so when the current milestone closes the musician stops instead of advancing.
   Leave `parked.jsonl` in place — it is the durable record.
3. Report: nonstop disarmed; if a milestone is mid-run (`current` set), it finishes and then stops. Note
   the parked queue in `.claude/ccharness/nonstop/parked.jsonl` if any.

This is the **soft** stop (finish the current milestone, then halt). To interrupt mid-milestone, press
**Esc**, or use `/musician-cancel`.
