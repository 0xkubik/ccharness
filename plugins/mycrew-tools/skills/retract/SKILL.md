---
name: retract
description: "Use when the human declares recorded information wrong or dead ('X is not true', 'there will be no X') — hunts every place that states it across the repo's docs, CLAUDE.mds, and persistent memory, then surgically deletes or corrects exactly that information and reports every touched spot. Removes only what was named, never rewrites around it."
argument-hint: "<the wrong information — one claim, e.g. 'there will be no post versioning'>"
---

# retract — hunt wrong information down and take it out

The human tells you a recorded fact is no longer true. Your one job: find **every** place that
states it, remove or correct **exactly** that, and account for each cut. You are a scalpel, not a
rewrite.

## Rules & concepts

- **One claim per call.** The argument names one wrong fact. Handed something vague ("the docs are
  stale") → ask what exactly is wrong; never sweep-and-guess.
- **Hunt everywhere, by meaning.** Search every knowledge surface the project has: the docs tree
  (features and notes, specs, the architecture model), every CLAUDE.md up to the product root,
  sibling doc repos of the product, and persistent memory. Search by meaning, not one literal
  string — the fact hides under synonyms, translations, and derived phrasing (versioning → versions,
  immutable, a new version beside the old). Stop only when new searches stop finding new places.
- **Surgical edits.** Take out the sentence, bullet, node, or line that states the retracted fact —
  nothing around it. Correct instead of delete when the human gave the replacement truth ("no
  versioning — posts are edited in place"). A file that exists only for that fact is deleted whole.
- **The features exception.** `features.md` lines are normally never deleted — an explicit human
  retraction is the ONE exception: the retracted feature line goes.
- **Dependents are flagged, not rewritten.** Content that doesn't state the fact but builds on it (a
  flow that assumes versions exist) — flag it in the report for the human to decide; touching it is
  a new task, not this one.
- **Memory too.** Matching persistent memories are corrected or deleted the same way, and their
  MEMORY.md index lines with them.
- **Never invent.** The replacement text is only what the human said. No new product ideas ride in
  on a correction.
- **Account for every cut.** Report each touched spot — the file, what was removed or changed — and
  each flagged dependent left alone. An edit not in the report didn't happen.

## Litmus

A hit gets edited only if it **states** the retracted fact. States it → cut or correct. Builds on
it → flag. Merely nearby → leave.
