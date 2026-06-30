# Don't work ungrounded — run `/roadmap-management` to set the goal and the road to it first

Before substantive work you need a real goal to aim at, and in this harness it isn't something you
guess — it's set by the **`/roadmap-management`** skill, which writes the product's North Star to
`.claude/ccharness/roadmap.md`. Building without it produces motion, not progress, so when the goal
is missing, stop and send the user to `/roadmap-management` instead of inferring one.

- **A goal is always required, and it must come from `/roadmap-management`.** Before writing, building, or
  changing anything non-trivial, check for the `## Product North Star` block at the top of
  `.claude/ccharness/roadmap.md`. If it's missing, surface that and ask the user to run
  `/roadmap-management` — don't infer a goal from thin context and run with it.
- **A feature list is required once the work is multi-step.** For anything beyond a small,
  self-contained change, the flat, ordered feature list `/roadmap-management` writes below the North Star in
  `.claude/ccharness/roadmap.md` must exist before execution starts. A one-line fix needs only the
  North Star at the top; a feature needs the list too, so route to `/roadmap-management`.
- **Trivial and exploratory work is exempt.** Quick questions, reads, and genuine exploration to
  *discover* what the goal should be don't need `/roadmap-management` up front — that's how you find what to
  set. The gate is for committing to substantive, hard-to-reverse work.
