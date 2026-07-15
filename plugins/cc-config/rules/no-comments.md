# Don't comment code by default — only genuinely non-obvious logic

Good code explains itself through clear names and structure. A comment is the exception, not the
habit: most comments either restate what the code already says or drift out of date and start
lying. Default to **no comments**.

- **Make the code readable instead of annotating it.** If a line seems to need a comment to be
  understood, first try a better name, a smaller function, or an earlier return — that usually
  removes the need entirely.
- **Comment only genuinely non-obvious logic** — a surprising edge case, a workaround for an
  outside bug, a non-trivial algorithm, a "this looks wrong but is deliberate" choice. When you do,
  explain **why**, not **what** the line does.
- **No restating the obvious.** `i += 1  # increment i`, banner dividers, and comments that
  paraphrase the next line add noise, not meaning.
- **No commented-out code and no narration of edits** ("changed this", "old version below").
  Version control already remembers — delete it.
- **Match the file and the project.** If a codebase deliberately keeps a comment style or required
  headers — license blocks, docstrings, public-API documentation — follow that. This rule is about
  gratuitous inline comments, not documentation a project intends to have.
