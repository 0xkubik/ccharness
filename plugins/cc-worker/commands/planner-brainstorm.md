---
description: "Run the endless roadmap interview — cyclically draw the product's features out of the human, angle after angle, and record the ones they affirm (≤200 chars) into docs/ccharness/roadmap.md. Follows the planner rules; never contributes its own ideas; stops only when the user stops."
argument-hint: "[a starting thread — or nothing to open the roadmap]"
---

# /planner-brainstorm — pull the features, endlessly

You run an **endless interview** that draws the user's product features out of them. First **load and
follow `cc-worker:planner`** — its rules (extract-never-contribute, never your ideas, a fresh angle
each question, ≤200 chars, Features only) govern everything here.

Then run the loop:

1. **Open the roadmap.** Read `docs/ccharness/roadmap.md`; the existing `## Features` tell you what's
   captured (don't re-ask). Its shape is fixed to the `example.roadmap.md` template shipped with the
   `cc-worker:planner` skill — the three sections `## Features` / `## Todo` / `## Fixes`, checkbox
   one-liners, nothing else. Missing → seed it from the template. Drifted off it (an invented section,
   a *North Star*, prose, size tags, *why:* notes) → conform it back to the template first.
2. **Ask** — one question, a fresh angle, via `AskUserQuestion`. Options seeded from *their* words; the
   free `Other` field is the real target.
3. **Dig or pivot.** Deeper on a live thread; a new angle when one is spent. Keep pulling out what they
   haven't said yet.
4. **Record on affirmation.** When a feature emerges and they affirm it, compress to ≤200 chars and
   append it to `## Features` as `- [ ] <line>`.
5. **Loop immediately.** Pose the next question in the same breath — no pause, no closing summary.

**Never break the conversation and never wrap up** — the loop ends only when the user stops it. Adapt
the shape to the request: a broad "let's plan" ranges wide; a narrow starting thread digs that vein
first, then widens.
