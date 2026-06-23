# ccharness

A **product harness** for Claude Code: a `diverge → decide → build` funnel that takes a product
from "where could this go?" all the way to committed code — and refuses to skip the thinking.

```
/point-it  ──►  /grill-it  ──►  /implement-it        (/slap = reset when stuck)
 DIVERGE         DECIDE           BUILD
 rank where      think one        take one task to
 it could go     fork through     done: built,
 next (a menu)   to ONE answer    verified, committed
```

Everything here is plain Markdown + JSON (instructions for Claude Code — no app code, no build).

## Install
```
/plugin marketplace add /Users/kubik/nox/misc/claude-code-harness
/plugin install ccharness@ccharness
```
Then equip it with the plugins it orchestrates (see [What it orchestrates](#what-it-orchestrates)):
```
/ccharness-init
```
This shows a plan of what's missing, asks you to confirm, then installs the gaps from the
official marketplace. Idempotent — re-run it any time (e.g. on a new machine).

## The commands

| Command | What it does | When you reach for it |
|---|---|---|
| **`/point-it [theme]`** | The **direction loop.** Surveys a product and emits a **ranked menu** of where it could go next — across four moves: **add** (new features), **finish** (half-built work), **rebuild** (redo better), **refactor** (tech debt) — each scored against the product's goal. On its **first run** it captures the product's *North Star* into `CLAUDE.md`; later runs propose paths toward it. Runs with or without a prompt. Decides nothing — you pick. | "Where should this product go next?" |
| **`/grill-it <decision>`** | The **decision loop.** Turns a fork-laden question into ONE reasoned decision via four opposed proposers (MVP / Final / Conventional / Contrarian) → cross-examination → synthesis. Depth scales to stakes. | "Which way — and why?" |
| **`/implement-it <task>`** | The **strict executor.** Runs one well-scoped task through a gated `0→6` pipeline (below). Refuses fork-laden or ambiguous tasks instead of guessing — a real fork goes back to `/grill-it`, pure ambiguity to brainstorming; never declares done with work open; never commits unverified code. | "Take this concrete task to done." |
| **`/slap`** | The **reset.** When a fix has gone three rounds deep in a rabbit hole, forces a step back: restate the problem, list what was tried, question assumptions, research alternatives, propose a fresh angle. | "Stop digging — rethink this." |
| **`/autopilot [focus]`** | The **loop.** Runs the whole funnel autonomously, cycle after cycle: auto-pick the top direction → grill-it decides → implement-it builds to a local commit → re-survey → repeat. Converts the funnel's human-handbacks into **skip-and-log** (unresolvable tasks go to a review queue). **Never stops on its own** — a `Stop` hook re-feeds it. Needs a North Star (run `/point-it` once first). | "Just keep improving this — I'll stop you." |
| **`/autopilot-cancel`** | The **brake.** The one manual stop for the loop — clears the autopilot state so the `Stop` hook lets the session end, and reports the cycle count and the blocked review queue. | "Stop the autopilot." |
| **`/ccharness-init`** | **Setup.** Installs the plugins the harness orchestrates (see below) from the official marketplace — detects what's missing, shows a plan, confirms, installs only the gaps (user scope). Idempotent. | "Set this up on a new machine." |

## The funnel

The three loops chain. Each hands its output to the next, and each owns a different kind of
thinking:

- **`/point-it`** *diverges* — it generates the agenda. Its menu has **nothing selected**;
  picking is not its job. On a first run in a repo it has no destination, so it interviews you
  for the product's **North Star** (vision · core problem · level `1/2/3`) and writes it to
  `CLAUDE.md`. Every later run reads that North Star and ranks moves *toward it* — which is what
  keeps the menu from degenerating into generic feature-list filler.
- **`/grill-it`** *converges* — you hand it one picked direction (or any fork) and it reasons it
  down to a single decision, then flows that decision straight into `/implement-it`. You can
  redirect, but you don't have to re-approve.
- **`/implement-it`** *builds* — it takes the decided, well-scoped task (handed down by grill-it,
  or given directly) and drives it to a verified local commit.

You act at just a few boundaries: confirm the **North Star** (first run only), **pick a
direction** (the one required choice), and **trigger the push** at the end. Everything between
flows on its own — you can redirect at any boundary, but you're never forced to.

## Autopilot — the funnel on a loop

`/autopilot` fuses the whole funnel into **one continuous loop** and runs it autonomously: each
cycle auto-picks the top-ranked direction toward the North Star, decides *how* with grill-it,
builds it to a **local commit** with implement-it, then re-surveys the changed repo and goes
again. The funnel's human-handbacks are **converted to skip-and-log** — a task it can't resolve (an
unbuildable fork, or one `slap` couldn't crack in two resets) is appended to a **blocked review
queue** and skipped, never waited on. When the menu is exhausted and nothing has changed, the cycle
idles cheaply instead of spinning the full survey.

**It cannot stop on its own.** A `Stop` hook re-feeds the loop on every turn, so the model can't
exit by deciding it's "done" — the only brake is **`/autopilot-cancel`** (you can also interrupt to
redirect at any time). It refuses to arm without a North Star, so run `/point-it` once first.

Loop state lives under `.claude/ccharness/autopilot/` (gitignored): `state.json` (the live loop),
`blocked.jsonl` (the review queue — what got skipped and why), and `log.jsonl` (one line per
cycle). `/autopilot-cancel` reports the cycle count and what's waiting in the queue.

## The `/implement-it` pipeline

| # | Stage | What happens |
|---|-------|--------------|
| **0** | **Clarity gate** | Proceeds only if the end state is unambiguous and there's no serious business or technical fork. Otherwise it **refuses** — a real fork routes back to `/grill-it` (the decision loop), pure ambiguity to `superpowers:brainstorming`. |
| **1** | **Scope** | An ordered checklist of deliverables + a size estimate (large → a written plan via `superpowers:writing-plans`). |
| **2** | **Select tools** | Routes to the right machinery — `frontend-design`, `superpowers` TDD/subagents/plans, `playwright`, `ralph-loop`, or its own goal-loop — and announces the choice. |
| **3** | **Implement** | Its own goal-loop drives the checklist to completion; TDD where a harness exists. |
| **4** | **Verify & debug** | Mandatory. Build/tests/lint (and `playwright` for UI), evidence before claims; `superpowers:systematic-debugging` on failures. Loops 3↔4 until green. |
| **5** | **Review & simplify** *(optional)* | For non-trivial code: `code-review` + the `code-simplifier` agent, triaged through `superpowers:receiving-code-review`. |
| **6** | **Commit** | A local commit via `commit-commands`. Stops before push/PR and offers the next step (GitLab MR or PR, auto-detected from the remote). |

**The slap link:** while implementing, implement-it keeps a per-problem strike counter. Three
failed attempts at the same problem → it runs the **slap** protocol, picks a fresh angle
*itself*, and keeps going. Implementation never hands back to you — it re-decides the approach
on its own (slapping again as needed) until the work is done and verified. The gate,
verification, and slap are the forcing functions that keep it strict.

**Forks aren't only caught at the gate:** Stage 0's fork-test stays armed through the build, so a
serious technical fork that only surfaces mid-implementation (materially different, no obvious
winner, costly to reverse) also routes up to `/grill-it` to be decided — never silently guessed.
Routine, reversible calls it just makes, and keeps moving.

## What it orchestrates

ccharness is glue — it routes to skills/plugins you already have installed: `superpowers`
(brainstorming, plans, TDD, subagents, debugging), `claude-md-management`, `frontend-design`,
`playwright`, `code-simplifier`, `ralph-loop`, `code-review`, `commit-commands`, and `gitlab`.
Missing plugins simply mean those routes aren't taken.

This list is the **source of truth** for what `/ccharness-init` installs — its dependency
table mirrors these nine plugins. Add or drop a dependency here, and update the table in
`commands/ccharness-init.md` to match.

## Layout
- `commands/point-it.md` · `commands/grill-it.md` · `commands/implement-it.md` — the entry points.
- `skills/point-it/SKILL.md` — the direction loop (diverge → ranked menu; North Star capture).
- `skills/grill-it/SKILL.md` — the decision loop (four proposers → synthesis).
- `skills/implement-it/SKILL.md` — the gated `0→6` executor (the brains).
- `skills/slap/SKILL.md` — the reset protocol, invoked by implement-it at three strikes (and by you via `/slap`).
- `commands/autopilot.md` · `commands/autopilot-cancel.md` — arm / stop the never-stop loop.
- `skills/autopilot/SKILL.md` — the loop's soft brain (one cycle per turn; auto-pick; skip-and-log; cheap idle).
- `hooks/hooks.json` · `hooks/autopilot-stop.sh` — the `Stop` hook (the hard muscle) that re-feeds the loop so it can't self-stop.
- `commands/ccharness-init.md` — setup: installs the orchestrated plugins (self-contained, no skill).
