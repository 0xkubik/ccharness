---
name: rulesmaker
description: "Use when writing or rewriting a rule file in .claude/rules/. The house standard every rule here obeys: an imperative title, the failure it prevents, a handful of bold-lead bullets, the exception spelled out — always-on constraints, never a procedure, never stack-specific. Not what a rule demands (its own job) but how it's written."
argument-hint: "<the rule to write or rewrite>"
---

# rulesmaker — how a rule is written here

A rule is an **always-on constraint** on how work is done: loaded with every task, obeyed without being
invoked. Not a skill (summoned for one job), not a procedure (steps in order). Your one job: shape that
constraint by the rules below — and obey them in the rule you write, so it reads like its siblings.

## Rules & concepts

- **Imperative title.** `# <Verb-first demand> — <the sharp clarifier>`. The heading alone must carry the
  rule; everything under it is elaboration. The filename is its kebab-case echo: `write-less-code.md`.
- **Open with the failure.** Two to four lines naming concretely what goes wrong without this rule. A cost
  the reader can feel is a rule that gets kept — motivate first, demand second.
- **One rule, one concern.** One file per concern. If the title needs an "and", it's two rules — split
  them. Never bundle unrelated demands under a vague banner.
- **Bold lead-in per bullet.** Every bullet opens with a two-or-three-word imperative in **bold**, then the
  demand in one to three lines. Four to six bullets — past that, it's a manual.
- **State what must be true, never the order.** A rule holds across every task at once, so it can never
  assume a stage or a next step. No `1 → 2 → 3`, no workflow, no "then run X". That is a skill's job.
- **Name the violation, not just the virtue.** Show what breaking it looks like — `i += 1  # increment i`,
  a `try/catch` that swallows, a branch handling the one value that broke. Concrete anti-patterns close
  the loopholes abstract praise leaves open.
- **Spell the exception, or there is none.** Close with the bullet naming where the rule legitimately
  stops: the documented workaround, the project convention that overrides it, the floor it never crosses.
  An unstated exception gets invented by the reader.
- **No hardcode, no stack.** A rule installs into any repo. Name the **concept** — the project's logger,
  the repo's established workflow, the pattern already there — never a path, a library, a command, or one
  project's specifics.
- **Small enough to re-read.** One screen, under ~30 lines. A rule sits in every context and pays its cost
  every turn; make it worth the tokens.
- **Self-exemplifying, in English.** The rule obeys itself — one demanding brevity is never three
  paragraphs. Prose in English, wrapped near 100 columns, no frontmatter.

## Shape

```
.claude/rules/<verb-first-name>.md

# <Imperative demand> — <clarifier>

<2–4 lines: the failure this prevents, concretely.>

- **<Imperative>.** <the demand, closed and concrete.>
- …
- **<The exception / the floor>.** <where it legitimately stops.>
```
