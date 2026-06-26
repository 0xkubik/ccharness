# cc-tools

> **Layer:** cc-tools is the **tools layer** of the cc-* harness — the funnel skills and commands.
> **cc-agent** (the musician — its single self-driving loop) sits above it; **cc-maestro** (the fleet
> orchestrator) sits at the top.

A **product harness** for Claude Code: a `ground → diverge → decide → build` funnel that takes a
product from "what's the goal?" all the way to committed code — and refuses to skip the thinking.

```
/find-goal  ──►  /what-to-do  ──►  /how-to-do  ──►  /do     (/slap = reset when stuck · /crux = unwind a pain)
 GROUND          DIVERGE         DECIDE          BUILD
 set the goal    rank where      work out HOW    take one task to
 (North Star)    it could go     to build the    done: built,
 + the roadmap   next (a menu)   pick (one way)  verified, committed
```

Everything here is plain Markdown + JSON (instructions for Claude Code — no app code, no build).

## Install
```
/plugin marketplace add /Users/kubik/nox/misc/claude-code-harness
/plugin install cc-tools@cc-harness
```
Then equip it with the plugins it orchestrates (see [What it orchestrates](#what-it-orchestrates)):
```
/cc-init
```
`/cc-init` is a 5-stage setup wizard (each stage skippable, driven by your choices): it installs
missing dependencies, installs the harness's recommended rules into this project's `.claude/rules/`,
builds the reminder cheat-sheet a hook re-surfaces every few prompts, reconciles your docs against
reality, and offers to run `/find-goal`. Idempotent — re-run any time (e.g. on a new machine).

Then **ground your product once** — every other command depends on it:
```
/find-goal
```
This captures the product's *North Star* (the goal) into `CLAUDE.md` and then offers to chart the
*roadmap* (the milestone route to it). Until a North Star exists, the other commands route you here.

## The commands

| Command | What it does | When you reach for it |
|---|---|---|
| **`/find-goal`** | The **grounding loop** — the front door. Captures the product's *North Star* (goal-setting: vision · core problem · level) into `CLAUDE.md`, then **offers** to chart the *roadmap* — a *layered* route of lightweight milestones (`done when …` + theme): ordered **stages**, with **parallel milestones inside each** (`order → split stages; independent → same stage`), saved to `.claude/ccharness/roadmap.md`. Run once up front; re-run any time to revise — goal or roadmap, no flag. Every other command routes here when no North Star exists. | "Set the goal and plan the project far ahead." |
| **`/what-to-do [theme]`** | The **direction loop.** Surveys a product and emits a **ranked menu** of where it could go next — across four moves: **add** (new features), **finish** (half-built work), **rebuild** (redo better), **refactor** (tech debt) — each scored against the product's goal, and **biased toward the roadmap's current frontier** (the parallel milestones open now) if one exists. Requires the *North Star* — no North Star → routes you to `/find-goal`. Runs with or without a prompt. Decides nothing — you pick. | "Where should this product go next?" |
| **`/how-to-do <decision>`** | The **decision loop.** Works out HOW to build a picked direction (or resolves a standalone technical fork) — four opposed proposers (MVP / Final / Conventional / Contrarian) argue different ways to build it → cross-examination → synthesis into ONE buildable approach. It decides the *how*, not *whether* (the pick is what-to-do's); a pick that looks wrong it flags rather than overrides. Depth scales to stakes. | "How to build it — and why?" |
| **`/do <task>`** | The **strict executor.** Runs one well-scoped task through a gated `0→6` pipeline (below). Requires the *North Star* (routes to `/find-goal` if missing). Refuses fork-laden or ambiguous tasks instead of guessing — a technical fork goes back to `/how-to-do`, a non-technical (business) one it refuses outright, pure ambiguity to brainstorming; never declares done with work open; never commits unverified code. | "Take this concrete task to done." |
| **`/slap`** | The **reset.** When a fix has gone three rounds deep in a rabbit hole, forces a step back: restate the problem, list what was tried, question assumptions, research alternatives, propose a fresh angle. | "Stop digging — rethink this." |
| **`/crux <pain>`** | The **diagnosis loop.** Unwinds a pain, doubt, or blockage that isn't yet a goal/direction/fork — pins the real problem from your words + the repo, runs a four-lens critical-thinking panel (Jung's Sensation / Intuition / Thinking / Feeling, each committing to a falsifiable check), and converges on ONE diagnosis + angle of attack, not implementation. Autonomous, free-standing (no North Star needed); the deliberate, deeper cousin of `/slap`. | "Something's off — make sense of it." |
| **`/cc-init`** | **Setup wizard (5 stages).** Driven by your choices, each stage skippable: (1) install missing dependencies from the official marketplace (user scope); (2) install the harness's recommended rules into this project's `.claude/rules/`; (3) build the reminder cheat-sheet a `UserPromptSubmit` hook re-surfaces every third prompt so the project's tools and rules don't fade from attention; (4) reconcile the project's prose docs against your current understanding so stale text doesn't mislead later decisions; (5) offer to run `/find-goal`. Idempotent. | "Set this up on a new machine." |

## The funnel

`/find-goal` grounds the funnel; the three loops then chain, each handing its output to the next,
each owning a different kind of thinking:

- **`/find-goal`** *grounds* — the front door. It interviews you for the product's **North Star**
  (vision · core problem · level `1/2/3`) and writes it to `CLAUDE.md`, then offers to chart the
  **roadmap** — a *layered* route of lightweight milestones to that goal (ordered stages, parallel
  milestones within each: `.claude/ccharness/roadmap.md`). Every other command depends on the North
  Star; without it, they route you here.
- **`/what-to-do`** *diverges* — it generates the agenda. Its menu has **nothing selected**; picking
  is not its job. It reads the North Star and ranks moves *toward it* — **biased toward the roadmap's
  current frontier** (the parallel milestones open now) if one exists — which keeps the menu from
  degenerating into generic feature-list filler.
- **`/how-to-do`** *converges* — you hand it one picked direction (or any fork) and it works out
  **how** to build it, reasoning the implementation forks down to a single buildable approach, then
  flows that straight into `/do`. It doesn't re-pick the direction (that was what-to-do's
  job) — it decides the *how*; and if the pick itself looks wrong, it flags you rather than silently
  overriding. You can redirect, but you don't have to re-approve.
- **`/do`** *builds* — it takes the decided, well-scoped task (handed down by how-to-do,
  or given directly) and drives it to a verified local commit.

You act at just a few boundaries: set the **North Star** (once, via `/find-goal`) and shape the
**roadmap**, **pick a direction** (the one required choice each cycle), and **trigger the push** at
the end. Everything between flows on its own — you can redirect at any boundary, but you're never
forced to.

## The `/do` pipeline

| # | Stage | What happens |
|---|-------|--------------|
| **0** | **Clarity gate** | Proceeds only if the end state is unambiguous and there's no serious business or technical fork. Otherwise it **refuses** — a technical fork routes back to `/how-to-do` (the decision loop), a business/non-technical one it declines outright, pure ambiguity to `superpowers:brainstorming`. |
| **1** | **Scope** | An ordered checklist of deliverables + a size estimate (large → a written plan via `superpowers:writing-plans`). |
| **2** | **Select tools** | Routes to the right machinery — `frontend-design`, `superpowers` TDD/subagents/plans, `playwright`, `ralph-loop`, or its own goal-loop — and announces the choice. |
| **3** | **Implement** | Its own goal-loop drives the checklist to completion; TDD where a harness exists. |
| **4** | **Verify & debug** | Mandatory. Build/tests/lint (and `playwright` for UI), evidence before claims; `superpowers:systematic-debugging` on failures. Loops 3↔4 until green. |
| **5** | **Review & simplify** *(optional)* | For non-trivial code: `code-review` + the `code-simplifier` agent, triaged through `superpowers:receiving-code-review`. |
| **6** | **Commit** | A local commit via `commit-commands`. Stops before push/PR and offers the next step (GitLab MR or PR, auto-detected from the remote). |

**The slap link:** while implementing, do keeps a per-problem strike counter. Three
failed attempts at the same problem → it runs the **slap** protocol, picks a fresh angle
*itself*, and keeps going. Implementation never hands back to you — it re-decides the approach
on its own (slapping again as needed) until the work is done and verified. The gate,
verification, and slap are the forcing functions that keep it strict.

**Forks aren't only caught at the gate:** Stage 0's fork-test stays armed through the build, so a
serious technical fork that only surfaces mid-implementation (materially different, no obvious
winner, costly to reverse) also routes up to `/how-to-do` to be decided — never silently guessed.
Routine, reversible calls it just makes, and keeps moving.

## What it orchestrates

cc-tools is glue — it routes to skills/plugins you already have installed: `superpowers`
(brainstorming, plans, TDD, subagents, debugging), `claude-md-management`, `frontend-design`,
`code-simplifier`, `ralph-loop`, `code-review`, and `gitlab`. Missing plugins simply mean those
routes aren't taken. (`playwright` for UI verification now ships with Claude Code, and the commit
step works without `commit-commands`, so `/cc-init` no longer installs either.)

This list is the **source of truth** for what `/cc-init` installs — its dependency
table mirrors these seven plugins. Add or drop a dependency here, and update the table in
`commands/cc-init.md` to match.

Beyond the marketplace set, `/cc-init` also **offers** two external MCP tools it doesn't bundle —
[`codegraph`](https://github.com/colbymchenry/codegraph) (indexed code intelligence) and
[`headroom`](https://github.com/headroomlabs-ai/headroom) (token-saving output compression).

## Layout
- `commands/find-goal.md` · `commands/what-to-do.md` · `commands/how-to-do.md` · `commands/do.md` — the entry points.
- `skills/find-goal/SKILL.md` — the grounding loop (goal-setting → North Star capture, then the sequenced roadmap). The front door every other skill routes to when ungrounded.
- `skills/what-to-do/SKILL.md` — the direction loop (diverge → ranked menu, biased toward the roadmap's current frontier).
- `skills/how-to-do/SKILL.md` — the decision loop (four proposers → synthesis).
- `skills/do/SKILL.md` — the gated `0→6` executor (the brains).
- `skills/slap/SKILL.md` — the reset protocol, invoked by do at three strikes (and by you via `/slap`).
- `skills/crux/SKILL.md` · `commands/crux.md` — the diagnosis loop (pin the pain → four-lens Jungian panel → one diagnosis + angle). Free-standing side door; the deliberate cousin of slap.
- `commands/cc-init.md` — setup wizard (deps → rules → reminder cheat-sheet → doc reconciliation → /find-goal; self-contained, no skill).
- `hooks/hooks.json` · `hooks/cheatsheet-hook.sh` — the `UserPromptSubmit` reminder: re-surfaces the cheat-sheet `/cc-init` builds (`.claude/ccharness/cheatsheet.txt`) every third prompt; a no-op until that file exists.
