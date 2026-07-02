# cc-script

> **Layer:** cc-script is the **product script** of the cc-* harness — the script skills and commands.
> It depends on **cc-instruments** (the helpers layer: `/crux`, `/slap`, `/cc-init`, project rules). **cc-musician**
> (the musician — its single self-driving loop) sits above it; **cc-conductor** (the fleet orchestrator)
> sits at the top.

A **product harness** for Claude Code: a `ground → diverge → decide → build` script that takes a
product from "what's the goal?" all the way to committed code — and refuses to skip the thinking.

```
/roadmap-management  ──►  /architect  ──►  /what-to-do  ──►  /how-to-do  ──►  /do     (/slap = reset · /crux = unwind a pain — both from cc-instruments)
 GROUND          DESIGN          DIVERGE         DECIDE          BUILD
 set the goal    design the      rank where      work out HOW    take one task to
 (North Star)    architecture    it could go     to build the    done: built,
 + the roadmap   (diagrams)      next (a menu)   pick (one way)  verified, committed
```

`/architect` is the optional design step — it turns intent into architecture diagrams (LikeC4 /
Excalidraw / Mermaid) before you decide what to build.

The script itself is plain Markdown + JSON (instructions for Claude Code — no app code, no build),
plus one small terminal helper, [`ccscriptctl`](#ccscriptctl--terminal-helper), for chores best done from a shell.

## Install
```
/plugin marketplace add /Users/kubik/nox/misc/claude-code-harness
/plugin install cc-instruments@cc-harness
/plugin install cc-script@cc-harness
```
cc-script leans on cc-instruments for `/cc-init`, `/crux`, and `/slap` — install both. Then equip the
harness with the plugins the script orchestrates (see [What it orchestrates](#what-it-orchestrates)):
```
/cc-init
```
`/cc-init` (from cc-instruments) is an onboarding orchestrator (each step skippable, driven by your choices):
it explains the four plugins, installs missing dependencies and recommended tools, then runs three
skills — `/rules-management`, `/cheatsheet-management`, `/docs-management` — and offers to run
`/roadmap-management`. Idempotent — re-run any time (e.g. on a new machine).

Then **ground your product** — every script command depends on it:
```
/roadmap-management
```
This captures the product's *North Star* (the goal) and the ordered feature list (the route to it) into
`.claude/ccharness/roadmap.md` — the goal at the top, the features below. Until a North Star exists, the other commands route you here.

## The commands

| Command | What it does | When you reach for it |
|---|---|---|
| **`/roadmap-management`** | The **grounding loop** — the front door, and the roadmap's keeper across its life. Captures the product's *North Star* (goal-setting: vision · core problem · level) and a **flat, ordered list of features** to it — both saved to `.claude/ccharness/roadmap.md` (North Star at the top, features below, built top to bottom). Charters the roadmap the first run; re-run any time to rethink it freely or fold in one feature (`--force` writes that feature after one confirm). Every other command routes here when no North Star exists. | "Set the goal, then keep the roadmap honest." |
| **`/architect <what>`** | The **design loop.** Designs a new system or feature **with you**, led by your words, into **architecture diagrams** (mostly diagrams, little text). **LikeC4** is the one collapsible backbone — system down to modules/key classes; **Mermaid** covers leaf detail that can't fold in (class internals, a call sequence, a DB schema); **Excalidraw** for freeform sketches. Saved to `docs/architecture/`. Never reads your code; you bring the context. Leans on cc-instruments' diagram references (falls back to Mermaid if it's absent). Optional step between the roadmap and `/what-to-do`. | "Design the architecture before deciding what to build." |
| **`/what-to-do [theme]`** | The **direction loop.** Surveys a product and emits a **ranked menu** of where it could go next — across four moves: **add** (new features), **finish** (half-built work), **rebuild** (redo better), **refactor** (tech debt) — each scored against the product's goal, and **biased toward the roadmap's current frontier** (the next unbuilt feature) if one exists. Requires the *North Star* — no North Star → routes you to `/roadmap-management`. Runs with or without a prompt. Decides nothing — you pick. | "Where should this product go next?" |
| **`/how-to-do <decision>`** | The **decision loop.** Works out HOW to build a picked direction (or resolves a standalone technical fork) — four opposed proposers (MVP / Final / Conventional / Contrarian) argue different ways to build it → cross-examination → synthesis into ONE buildable approach. It decides the *how*, not *whether* (the pick is what-to-do's); a pick that looks wrong it flags rather than overrides. Depth scales to stakes. | "How to build it — and why?" |
| **`/do <task>`** | The **strict executor.** Runs one well-scoped task through a gated pipeline (below) to a **smoke-checked** finish, then **hands off to `/refactor-review-test`**. Requires the *North Star* (routes to `/roadmap-management` if missing). Refuses fork-laden or ambiguous tasks instead of guessing — a technical fork goes back to `/how-to-do`, a non-technical (business) one it refuses outright, pure ambiguity to brainstorming; never declares done with work open; **never commits** (that's refactor-review-test's). | "Build this concrete task." |
| **`/refactor-review-test [target]`** | The **autonomous hardener** — the tail of the script. Takes the change `/do` just built (or existing code) and carries it to a *solid* finish: safety-net tests → behavior-preserving refactor (`/simplify` + `code-simplifier`) → review (`/code-review`) with fixes **applied, not reported** → full test coverage → verified **local commit**. Fully autonomous — it **never hands work back to a human**; a genuine behavior/product fork it flags to the conductor, never asks. `/do` always hands off here; also runs standalone. | "Harden this to done." |

> The script leans on two **cc-instruments** side doors: **`/slap`** (reset a fix stuck in a rabbit hole — `/do`
> and `/refactor-review-test` invoke it at three strikes) and **`/crux`** (unwind a pain/doubt into one
> diagnosis). Both ship in cc-instruments, as does the **`/cc-init`** setup wizard.

## `ccscriptctl` — terminal helper

A tiny CLI for the chores you'd otherwise do by hand — it opens the project's roadmap or
cheat-sheet in your editor, and captures quick roadmap notes straight from the shell, so you don't
have to dig into `.claude/ccharness/` every time:

```
ccscriptctl roadmap open               # open .claude/ccharness/roadmap.md
ccscriptctl roadmap add feat <text>    # note a feature → "## Features" section (the route)
ccscriptctl roadmap add todo <text>    # note a task    → "## TODO" section
ccscriptctl roadmap add backlog <text> # note an idea   → "## Backlog" section
ccscriptctl roadmap add bug <text>     # note a bug     → "## Bugs" section
ccscriptctl roadmap view [what]        # print the roadmap (all | feat|todo|backlog|bug)
ccscriptctl roadmap done <kind> <n>    # mark item <n> in that section done ("[x]")
ccscriptctl roadmap drop <kind> <n>    # remove item <n> from that section, then renumber
ccscriptctl roadmap renumber           # renumber every section's items to 1..N
ccscriptctl roadmap prune              # drop completed ("[x]") items, then renumber
ccscriptctl cheatsheet                 # open .claude/ccharness/cheatsheet.md
```

`roadmap add` appends a numbered item `N. [ ] <text>` under the matching section of `roadmap.md` without
opening an editor — `N` is auto-assigned (the section's highest number + 1), each section numbered
independently. It creates a missing section in its canonical slot (Features → TODO → Backlog → Bugs) and
writes into the same `## Features` route that `/roadmap-management` manages, so a captured feature just
joins the list in order; TODO / Backlog / Bugs are a shell inbox to triage onto the route later with
`/roadmap-management`.

`roadmap view` prints straight to the console — `view all` (the default) dumps the whole file, and
`view feat|todo|backlog|bug` prints just that one section.

`roadmap done <kind> <n>` ticks item `n` in that section (`[ ]` → `[x]`); `roadmap drop <kind> <n>`
removes it and renumbers what's left. Both address items by the number `view` shows.

`roadmap renumber` rewrites every section's items to a contiguous `1..N` in document order — closing
gaps and converting any old `- [ ]` bullets to numbered items (checkbox state preserved). `roadmap
prune` removes the completed (`[x]`) items from every section and then renumbers automatically, so the
list stays tidy. Both leave the North Star block untouched.

It finds `.claude/ccharness/` in the current directory or any parent. `open` hands the file to your
OS default app (`open` / `xdg-open`) and returns immediately — it never blocks, even if `$EDITOR` is a
waiting editor like `code --wait`. On a machine with no desktop opener it falls back to `$VISUAL` /
`$EDITOR`, launched detached.

**You don't symlink it** — once cc-script is installed, `ccscriptctl` is already on your PATH. Claude
Code adds every installed plugin's `bin/` to PATH, exactly like `ccconductorctl` (cc-conductor) and
`musiciansctl` (cc-musician). Just install cc-script (`/plugin install cc-script@ccharness`) and run
`ccscriptctl roadmap open`. (For a standalone terminal outside Claude Code, add the plugin's `bin/` to your
shell PATH yourself.)

## The script

`/roadmap-management` grounds the script; the three loops then chain, each handing its output to the next,
each owning a different kind of thinking:

- **`/roadmap-management`** *grounds* — the front door. It interviews you for the product's **North Star**
  (vision · core problem · level `1/2/3`) and writes it to `CLAUDE.md`, then offers to chart the
  **roadmap** — a **flat, ordered list of features** toward that goal
  (`.claude/ccharness/roadmap.md`). Every other command depends on the North
  Star; without it, they route you here.
- **`/what-to-do`** *diverges* — it generates the agenda. Its menu has **nothing selected**; picking
  is not its job. It reads the North Star and ranks moves *toward it* — **biased toward the roadmap's
  current frontier** (the next unbuilt feature) if one exists — which keeps the menu from
  degenerating into generic feature-list filler.
- **`/how-to-do`** *converges* — you hand it one picked direction (or any fork) and it works out
  **how** to build it, reasoning the implementation forks down to a single buildable approach, then
  flows that straight into `/do`. It doesn't re-pick the direction (that was what-to-do's
  job) — it decides the *how*; and if the pick itself looks wrong, it flags you rather than silently
  overriding. You can redirect, but you don't have to re-approve.
- **`/do`** *builds* — it takes the decided, well-scoped task (handed down by how-to-do, or given
  directly), builds it and smoke-checks that it runs, then **hands off to `/refactor-review-test`**.
- **`/refactor-review-test`** *hardens* — it takes that working change and carries it to a solid
  finish: safety-net tests → behavior-preserving refactor → review-with-fixes → full coverage →
  verified local commit. Fully autonomous — it never hands work back to a human; the commit lives
  here, not in `/do`.

You act at just a few boundaries: set the **North Star** (via `/roadmap-management`) and shape the
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
| **4** | **Smoke-check** | Proves the change *runs* — compile / boot / a smoke test (does-it-even-run), **not** the full verify. Fixes here (3↔4) until it runs. |
| **5** | **Hand off** | Always invokes **`/refactor-review-test`**, which owns the full verify, refactor, review, full tests, and the local commit. `/do` itself never commits. |

**The slap link:** while implementing, do keeps a per-problem strike counter. Three
failed attempts at the same problem → it runs the **`/slap`** protocol (from cc-instruments), picks a fresh
angle *itself*, and keeps going. Implementation never hands back to you — it re-decides the approach
on its own (slapping again as needed) until the work is done and verified. The gate,
verification, and slap are the forcing functions that keep it strict.

**Forks aren't only caught at the gate:** Stage 0's fork-test stays armed through the build, so a
serious technical fork that only surfaces mid-implementation (materially different, no obvious
winner, costly to reverse) also routes up to `/how-to-do` to be decided — never silently guessed.
Routine, reversible calls it just makes, and keeps moving.

## What it orchestrates

The script is glue — it routes to skills/plugins you already have installed: `superpowers`
(brainstorming, plans, TDD, subagents, debugging), `claude-md-management`, `frontend-design`,
`code-simplifier`, `ralph-loop`, and `code-review`. Missing plugins simply mean those routes
aren't taken. (`playwright` for UI verification now ships with Claude Code, and commits/PRs are
handled with `git` directly — so `/cc-init` no longer installs `playwright`, `commit-commands`,
or `gitlab`.)

This list is the **source of truth** for what `/cc-init` installs — its dependency
table mirrors these six plugins. Add or drop a dependency here, and update the table in
`plugins/cc-instruments/commands/cc-init.md` to match.

Beyond the marketplace set, `/cc-init` also **offers** two external MCP tools it doesn't bundle —
[`codegraph`](https://github.com/colbymchenry/codegraph) (indexed code intelligence) and
[`headroom`](https://github.com/headroomlabs-ai/headroom) (token-saving output compression).

## Layout
- `commands/roadmap-management.md` · `commands/what-to-do.md` · `commands/how-to-do.md` · `commands/do.md` · `commands/refactor-review-test.md` — the entry points.
- `skills/roadmap-management/SKILL.md` — the grounding loop (goal-setting → North Star capture, then the sequenced roadmap). The front door every other skill routes to when ungrounded.
- `skills/what-to-do/SKILL.md` — the direction loop (diverge → ranked menu, biased toward the roadmap's current frontier).
- `skills/how-to-do/SKILL.md` — the decision loop (four proposers → synthesis).
- `skills/do/SKILL.md` — the gated executor: builds + smoke-checks, then hands off (the brains).
- `skills/refactor-review-test/SKILL.md` — the autonomous hardener (safety-net → refactor → review → full tests → commit); `/do`'s always-on tail, also standalone.
- `bin/ccscriptctl` — small terminal helper: opens the project's roadmap / cheat-sheet in your editor (`ccscriptctl roadmap open` · `ccscriptctl cheatsheet`), captures quick roadmap notes (`ccscriptctl roadmap add feat|todo|backlog|bug <text>`), prints the roadmap (`ccscriptctl roadmap view [all|feat|todo|backlog|bug]`), ticks or removes items by number (`ccscriptctl roadmap done|drop <kind> <n>`), and tidies it (`ccscriptctl roadmap renumber` · `ccscriptctl roadmap prune`).
