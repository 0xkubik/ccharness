---
name: do
description: "Use when you have ONE concrete, well-scoped coding task ready to build autonomously. Builds it by a tight set of writing rules — reuse-first, least code, modular bricks, SOLID, no comments, graded logs. Refuses vague or fork-laden tasks rather than guessing."
argument-hint: "<one concrete, well-scoped task>"
---

## Gate — clear how to build

Build only when it's clear **HOW**. Check before writing a line:

- **Carries a real fork** (materially different ways to implement, no obvious winner) →
  `cc-pipeline:how-to-do` to think it through first.
- **Vague** (you can't state the acceptance criteria) → clarify via `superpowers:brainstorming`.
- **Business/product fork** (money, legal, direction) → not yours; back to the human.
- **Trivial & clear** — one sensible way to build it → proceed.

## Prepare the ground

First **map the project** — run `git ls-files | xargs wc -l` to list every tracked file with its
line count. It shows where the new code belongs and which files are fat enough to need a seat cleared
first. Then judge how the new code lands in the **existing** project:

- **Fits as-is** → build.
- **Needs a seat first** — it only lands cleanly if existing code is reshaped to receive it (a seam
  to open, an interface to extract, a module boundary to move, a tangle in the way) → hand to
  **`cc-pipeline:refactor`** first (**behavior-preserving**, scoped to *making room for this code,
  not tidying the repo*), then build on the prepared ground.

## The writing rules (very important)

- **Reuse before you write.** Scan the tree for what already solves this — a library, an existing
  module, a pattern in the codebase. The best code is the code you didn't write.
- **Least code that hits the goal.** Fewer lines, fewer moving parts. Solve today's task only — no
  scaffolding for imagined futures.
- **Modular reusable bricks, then aggregate.** Build small single-purpose units and compose them —
  never one big blob. Each brick does one job, has a clear interface, and is usable elsewhere.
- **SOLID, briefly:** one responsibility per unit · open to extension, closed to modification ·
  implementations stay substitutable · interfaces narrow and focused · depend on abstractions, not
  concretions.
- **No comments.** Clear names and structure carry the meaning; only genuinely non-obvious *why*
  (a workaround, a deliberate surprise) earns a line — never restating *what* the code does.
- **Log every action, graded, in the present.** Put a log line on each real step at the level it
  deserves (**error / warn / info / debug**), phrased as the action **underway** — `"connecting to
  X…"`, `"writing N rows…"` — not past-tense `"connected"` / `"wrote"`. Never log secrets; bulky
  dumps stay at `debug`.
- **Match the surrounding code.** Read the neighbours first — naming, layout, error style, idioms — 
  and write code that looks like it was already there. Consistency with the codebase beats your 
  personal preference.
- **Fail fast, don't swallow.** Validate at the boundaries, surface errors with context, let them propagate — 
  never catch-and-ignore or return a silent empty. An operation that can't do its job says so loudly.
- **Write new state not a change.** When editing a file do not write what changed and why, 
  just change the behavior without explanation why it changed and what was before.