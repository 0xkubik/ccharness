# cc-harness

A **layered harness for Claude Code** — four plugins that stack on top of each other to take a
product from "what's the goal?" all the way to committed code, and then run that work
unsupervised across a whole fleet of agents.

```
cc-instruments + cc-script   ──►   cc-musician   ──►   cc-conductor
the helpers & script         the musician      the console
you run                      that runs them    that watches them
by hand                      for you           all at once
```

- **cc-instruments** — the *helpers layer*. Philosophy-agnostic side doors (`/crux`, `/slap`), the
  `/cc-init` setup wizard, and the harness's recommended project rules. Usable in any project.
- **cc-script** — the *script layer*. Single-purpose skills that form a thinking script:
  `ground → diverge → decide → build`. You drive them by hand, one step at a time. Depends on cc-instruments.
- **cc-musician** — the *self-driving layer*. The **musician**: a single agent that takes one piece of
  work, runs the cc-script to drive it to its own definition of done, then closes itself.
- **cc-conductor** — the *conductor layer*. A console (`ccconductorctl`) that watches and controls many
  agents and musicians at once — token burn, stalls, loops, stop/steer.

Everything here is plain Markdown + JSON (instructions for Claude Code) plus a small Python/shell
CLI for the console — no app to build, no compile step.

## The layers

### 1. cc-instruments & cc-script — what you drive by hand

**cc-instruments** gives you two reasoning side doors that work in any project — **`/crux`** (unwind a pain
or doubt into one diagnosis) and **`/slap`** (reset a fix stuck in a rabbit hole) — plus the
**`/cc-init`** setup wizard and the harness's recommended project rules.

**cc-script** is a product script that refuses to skip the thinking:

```
/roadmap-management  ──►  /what-to-do  ──►  /how-to-do  ──►  /do     (/slap = reset when stuck)
 GROUND          DIVERGE         DECIDE          BUILD
 set the goal    rank where      work out HOW    take one task to
 (North Star)    it could go     to build the    done: built,
 + the roadmap   next (a menu)   pick (one way)  verified, committed
```

- **`/roadmap-management`** — set the product's goal (its *North Star*) and chart a roadmap of milestones.
  The front door: every other command sends you here first if no goal is set.
- **`/what-to-do`** — survey the product and get a ranked menu of where it could go next.
- **`/how-to-do`** — work out **how** to build the direction you picked (it converges the
  implementation forks into one buildable approach; it doesn't re-pick the direction).
- **`/do`** — take one concrete task to a verified local commit through a gated pipeline.
- **`/slap`** — when a fix is stuck in a rabbit hole, force a step back and a fresh angle (cc-instruments).

Full details: [`plugins/cc-script/README.md`](plugins/cc-script/README.md) (the script) and
[`plugins/cc-instruments/README.md`](plugins/cc-instruments/README.md) (the helpers).

### 2. cc-musician — the musician that runs the script for you

One autonomous loop — the **musician** — the project's brain for **one piece of work**. It plays the
cc-script instruments (what-to-do → how-to-do → do → refactor-review-test) plus cc-instruments's crux/slap, forges its own falsifiable definition of
done, drives to it, then **closes itself**. Bounded and self-closing: one piece of work, to its end,
then stop. There is no never-stop loop above it.

- **`/musician <prompt>`** — think the task through, then build it. It can **decline or reframe** a
  bad idea rather than build it blindly.
- **`/musician`** (no prompt) — find a direction itself (via what-to-do), then build it.
- **`/musician-cancel`** — the manual brake.

Full details: [`plugins/cc-musician/README.md`](plugins/cc-musician/README.md).

### 3. cc-conductor — the console that supervises the fleet

The `ccconductorctl` CLI watches and controls many coding agents and musicians at once:

```bash
ccconductorctl ls                      # dashboard: tokens, last activity, watchdog verdict
ccconductorctl start "fix flaky test" --repo ~/app
ccconductorctl logs <id> --tail 50
ccconductorctl stop <id> / steer <id> "do X now" / pause <id> / resume <id>
ccconductorctl check --notify          # detect stalled/looping/died; POST changes to a webhook
```

It reads the native `claude agents` registry plus each session's transcript, and adds a
**watchdog** for verdicts the native status doesn't give (stalled, looping, over-budget, died).
Usable both by a human in a terminal and by an external supervising agent. Inside a session,
`/conductor` runs the dashboard.

Full details: [`plugins/cc-conductor/README.md`](plugins/cc-conductor/README.md).

## Install

Add this repo as a plugin marketplace, then install the layers you want:

```
/plugin marketplace add /Users/kubik/nox/misc/claude-code-harness
/plugin install cc-instruments@cc-harness
/plugin install cc-script@cc-harness     # the product script (depends on cc-instruments)
/plugin install cc-musician@cc-harness      # optional — the musician
/plugin install cc-conductor@cc-harness    # optional — the fleet console
```

The cc-script is glue: it routes to skills/plugins you already have (`superpowers`, `frontend-design`,
`playwright`, `code-review`, `commit-commands`, and more). To install those dependencies in one
shot:

```
/cc-init
```

It shows a plan of what's missing, asks you to confirm, then installs only the gaps. Idempotent —
safe to re-run on a new machine.

Then **ground your product once** — every command depends on it:

```
/roadmap-management
```

## How the layers depend on each other

- **cc-instruments** stands alone — the `/crux`, `/slap`, and `/cc-init` helpers work on their own.
- **cc-script** depends on cc-instruments (it routes stuck fixes to `/slap`); the script skills are otherwise self-contained.
- **cc-musician** depends on cc-script (it invokes the script skills) and cc-instruments (`/crux`, `/slap`), and writes its loop state under
  `.claude/ccharness/`.
- **cc-conductor** observes and controls cc-musician (and any other Claude Code agent); it needs neither
  of the others installed to watch a fleet, but it's most useful supervising musicians.

## Repository layout

```
.claude-plugin/marketplace.json   the marketplace manifest (lists the 4 plugins)
plugins/
  cc-instruments/      /crux + /slap + /cc-init + rules          (README.md)
  cc-script/     script skills + commands                  (README.md)
  cc-musician/      the musician loop + Stop hooks            (README.md)
  cc-conductor/    the ccconductorctl CLI + /conductor              (README.md)
docs/
  research/      background notes on agentic loops
  superpowers/   design specs + implementation plans
```

Runtime state for the agent layer lives under `.claude/ccharness/` (git-ignored, except the
roadmap).
