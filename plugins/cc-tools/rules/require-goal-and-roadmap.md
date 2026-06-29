# Don't work ungrounded — run `/find-goal` to set the goal and the road to it first

Before doing substantive work, you need a real goal to aim at — and in this harness the goal isn't
something you guess or hand-wave. It's set by running the **`/find-goal`** skill, which captures the
product's North Star into `CLAUDE.md` and lays out the road to it as a flat, ordered feature list in
`.claude/ccharness/roadmap.md`. Building without that produces motion, not progress — plausible
output that may solve the wrong thing. When the grounding isn't there, **stop and send the user to
`/find-goal`** instead of inferring a goal yourself.

- **A goal is always required, and it must come from `/find-goal`.** Before writing, building, or
  changing anything non-trivial, check for the `## Product North Star` block in `CLAUDE.md` that
  `/find-goal` writes. If it's missing, surface that and ask the user to run `/find-goal` — don't
  infer a goal from thin context and run with it.
- **A roadmap is required once the work is multi-step.** For anything beyond a small, self-contained
  change, there must be the flat, ordered feature list `/find-goal` produces at
  `.claude/ccharness/roadmap.md` — before execution starts. A one-line fix needs only the
  goal; a feature needs both, so route to `/find-goal`.
- **Don't silently fill the gap.** If the goal or the roadmap is missing, say so plainly and point
  the user at `/find-goal` — don't invent one and proceed as though it were given.
- **Trivial and exploratory work is exempt.** Quick questions, reads, and genuine exploration to
  *discover* what the goal should be don't need `/find-goal` up front — that's how you find what to
  set. The gate is for committing to substantive, hard-to-reverse work.
