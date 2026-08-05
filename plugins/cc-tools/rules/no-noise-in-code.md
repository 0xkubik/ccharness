# Leave no noise in code — no gratuitous comments, no narration of the change

Code and its edits should read as the finished state, not a diary. Two kinds of noise creep in:
comments that restate what the code already says, and text that narrates the edit ("was X, now Y").
Both drift out of date and start lying; version control already remembers the history.

- **Make the code readable instead of annotating it.** If a line seems to need a comment, first try a
  better name, a smaller function, or an earlier return — that usually removes the need entirely.
- **Comment only genuinely non-obvious *why*** — a surprising edge case, a workaround for an outside
  bug, a deliberate "looks wrong but isn't". Explain the *why*, never restate the *what*.
- **No restating the obvious, no commented-out code.** `i += 1  # increment i`, banner dividers, and
  dead code left in place are all noise. Delete it.
- **Write the new state, not the story of the change.** Leave the file reading as if it had always been
  this way. No "previously X, now Y", "changed from…", "updated to…" — in code or prose. Just the
  resulting content, described on its own terms.
- **Match the project's real doc conventions.** Where a codebase deliberately keeps docstrings, license
  headers, or public-API docs, follow that. This rule is about gratuitous noise, not documentation a
  project intends to have.
