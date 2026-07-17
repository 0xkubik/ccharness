# Write less code — reuse first, then the fewest lines that hit the goal

The best code is the code you didn't write: every line is something to read, test, and maintain
later. The common failure is reaching for a fresh implementation when the codebase, a library, or a
pattern already solves it — and padding today's task with scaffolding for an imagined tomorrow.

- **Reuse before you write.** Scan the tree for what already solves this — an existing module, a
  library, an established pattern — and build on it. Duplicating logic that already exists is a bug,
  not a head start.
- **Least code that hits the goal.** Fewer lines, fewer moving parts, fewer files. When two
  solutions both work, the smaller one wins.
- **Solve today's task only.** No speculative abstractions, config knobs, extra parameters, or
  "we'll probably need this later" scaffolding nobody asked for. (YAGNI — you aren't gonna need it.)
- **Delete what a change makes dead.** When your change orphans code — a now-unused branch, a patch
  the fix made unnecessary — remove it in the same breath. Less code is part of the work.
