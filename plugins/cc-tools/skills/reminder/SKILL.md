---
name: reminder
description: Use when one rule — or all of a project's rules — must be strictly obeyed for the work that follows. Invoked as /reminder with an @-path to a single rule file (repo .claude/rules/ or a global ~/.claude/rules/ file), or bare /reminder to pin every rule in the project's .claude/rules/. Re-reads the rule(s) fresh from disk and pins them as hard, non-negotiable constraints for the coming steps.
argument-hint: "[@path/to/rule.md] — omit to pin all project rules"
---

# Reminder — pin the rule(s), hard

Your only job is to make a rule (or all of them) freshly binding for the work that follows — not to
act on anything else yet. **Always re-read from disk**; never rely on content already in context —
the point is a fresh read that reactivates the rule.

## Which rule(s)

- **A path was given** (via `@` or as an argument) → that ONE rule. Resolve it:
  - repo-local, e.g. `.claude/rules/no-comments.md`
  - global, e.g. `~/.claude/rules/<name>.md`

  Re-read that file now. If it doesn't resolve to a real file, say so and stop — never invent or
  paraphrase a rule you didn't read.
- **No argument** (bare `/reminder`) → EVERY rule in the **project's** `.claude/rules/`. List the
  files (`ls .claude/rules/*.md`) and read each. If that directory is absent or empty, say so and stop.

## What to emit

For **each** rule, one compact block:

1. **Rule:** its name — the file's `# ` heading, or the filename.
2. **Imperative:** its core demand, in one or two lines, in your own words.

Then a **single closing commitment**: one line stating you will strictly obey them — letter and
spirit — from the next step onward.

Then **stop**. Don't restate whole files, add commentary, or start other work.
