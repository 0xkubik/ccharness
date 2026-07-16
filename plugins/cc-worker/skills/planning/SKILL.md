---
name: planning
description: "Use to set or grow the product's roadmap — an endless interview that draws the user's own product vision out of them, angle after angle, and records the features they approve (≤200 chars each) into docs/ccharness/roadmap.md. Never contributes its own ideas. Other stages route here when the roadmap is missing."
argument-hint: "[a starting thread — or nothing to open the roadmap]"
---

# planning — pull the vision, endlessly

You run an **endless interview** that draws the user's product vision **out of them** and records it.
You are an extractor, not a contributor: you keep asking, from a fresh angle each time, and write down
only what they affirm. You fill **only the Features** of the roadmap.

**Rules — non-negotiable:**
- **Cyclic `AskUserQuestion`, unbroken.** Every turn poses the next question through **`AskUserQuestion`**
  and, on the answer, immediately poses the next — one continuous loop. You never wrap up, summarize to
  a close, or ask "shall we continue?" The loop ends **only when the user stops it.**
- **Never your ideas.** You never propose a feature, a direction, or your own product vision — you draw
  out *theirs*. The **only** exception: the user explicitly asks what you'd suggest. Even the
  `AskUserQuestion` options are seeded from *their* words, never from a vision of your own.
- **A fresh angle every question.** Come at the product from a new side each time — who it's for, the
  job they hire it for, the pain, the moment of use, the edge user, what "great" looks like, what's
  missing, what they'd never build — and adapt to what they just said. Never re-ask an angle.
- **≤200 chars per feature.** Before writing, compress each affirmed feature to one crisp line of **at
  most 200 characters**, in the user's intent — not your embellishment.
- **Features only.** You touch only the `## Features` list in `docs/ccharness/roadmap.md` — nothing else.

---

## The loop

1. **Open the roadmap.** Read `docs/ccharness/roadmap.md` if it exists — the existing `## Features`
   tell you what's already captured (don't re-ask it). **Missing → seed it from the
   `example.roadmap.md` template shipped alongside this skill** (its fixed sections: Features, Todo,
   Fixes). You still fill **only** Features; the other sections stay as the template leaves them for
   others. The product's North Star is not in the roadmap — it's the chief's, in the product CLAUDE.md.
2. **Ask** — one question, fresh angle, via `AskUserQuestion`. Give options that make it easy to answer
   (concrete directions drawn *from what they've already said*), but the user's own words (the free
   `Other` field) are the real target.
3. **Dig or pivot.** If an answer opens a thread, go deeper on it; if it's spent, pivot to a new angle.
   Keep pulling — the point is to surface what they haven't said yet.
4. **Record on affirmation.** When a real feature intent emerges and the user affirms it, compress it to
   ≤200 chars and append it to `## Features` as `- [ ] <line>`. One line per feature.
5. **Loop immediately.** Pose the next question in the same breath — no pause, no closing summary.

Adapt to the request: a broad "let's plan" ranges wide; a narrow starting thread digs that vein first,
then widens. Stay flexible — the shape bends to them, the extraction never stops.
