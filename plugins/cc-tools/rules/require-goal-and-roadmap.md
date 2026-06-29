# Don't work ungrounded — run `/roadmap-management` to set the goal and the road to it first

Before doing substantive work, you need a real goal to aim at — and in this harness the goal isn't
something you guess or hand-wave. It's set by running the **`/roadmap-management`** skill, which captures the
product's North Star and lays out the road to it as a flat, ordered feature list — both in
`.claude/ccharness/roadmap.md` (the North Star at the top, the features below). Building without that
produces motion, not progress — plausible
output that may solve the wrong thing. When the grounding isn't there, **stop and send the user to
`/roadmap-management`** instead of inferring a goal yourself.

- **A goal is always required, and it must come from `/roadmap-management`.** Before writing, building, or
  changing anything non-trivial, check for the `## Product North Star` block at the top of
  `.claude/ccharness/roadmap.md` that `/roadmap-management` writes. If it's missing, surface that and ask the
  user to run `/roadmap-management` — don't infer a goal from thin context and run with it.
- **A feature list is required once the work is multi-step.** For anything beyond a small,
  self-contained change, the flat, ordered feature list `/roadmap-management` writes below the North Star in
  `.claude/ccharness/roadmap.md` must exist before execution starts. A one-line fix needs only the
  North Star at the top; a feature needs the list too, so route to `/roadmap-management`.
- **Don't silently fill the gap.** If the goal or the roadmap is missing, say so plainly and point
  the user at `/roadmap-management` — don't invent one and proceed as though it were given.
- **Trivial and exploratory work is exempt.** Quick questions, reads, and genuine exploration to
  *discover* what the goal should be don't need `/roadmap-management` up front — that's how you find what to
  set. The gate is for committing to substantive, hard-to-reverse work.
