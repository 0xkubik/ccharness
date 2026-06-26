# cc-harness

A **layered harness for Claude Code** — three plugins that stack on top of each other to take a
product from "what's the goal?" all the way to committed code, and then run that work
unsupervised across a whole fleet of agents.

```
cc-tools   ──►   cc-agent   ──►   cc-maestro
the skills       the musician      the console
you run          that runs them    that watches them
by hand          for you           all at once
```

- **cc-tools** — the *tools layer*. Single-purpose skills that form a thinking funnel:
  `ground → diverge → decide → build`. You drive them by hand, one step at a time.
- **cc-agent** — the *self-driving layer*. The **musician**: a single agent that takes one piece of
  work, runs the cc-tools funnel to drive it to its own definition of done, then closes itself.
- **cc-maestro** — the *conductor layer*. A console (`ccmaestro`) that watches and controls many
  agents and musicians at once — token burn, stalls, loops, stop/steer.

Everything here is plain Markdown + JSON (instructions for Claude Code) plus a small Python/shell
CLI for the console — no app to build, no compile step.

## The three layers

### 1. cc-tools — the funnel you drive by hand

A product funnel that refuses to skip the thinking:

```
/find-goal  ──►  /what-to-do  ──►  /how-to-do  ──►  /do     (/slap = reset when stuck)
 GROUND          DIVERGE         DECIDE          BUILD
 set the goal    rank where      work out HOW    take one task to
 (North Star)    it could go     to build the    done: built,
 + the roadmap   next (a menu)   pick (one way)  verified, committed
```

- **`/find-goal`** — set the product's goal (its *North Star*) and chart a roadmap of milestones.
  The front door: every other command sends you here first if no goal is set.
- **`/what-to-do`** — survey the product and get a ranked menu of where it could go next.
- **`/how-to-do`** — work out **how** to build the direction you picked (it converges the
  implementation forks into one buildable approach; it doesn't re-pick the direction).
- **`/do`** — take one concrete task to a verified local commit through a gated pipeline.
- **`/slap`** — when a fix is stuck in a rabbit hole, force a step back and a fresh angle.

Full details: [`plugins/cc-tools/README.md`](plugins/cc-tools/README.md).

### 2. cc-agent — the musician that runs the funnel for you

One autonomous loop — the **musician** — the project's brain for **one piece of work**. It plays the
cc-tools instruments (crux → what-to-do → how-to-do → do → refactor-review-test), forges its own falsifiable definition of
done, drives to it, then **closes itself**. Bounded and self-closing: one piece of work, to its end,
then stop. There is no never-stop loop above it.

- **`/musician <prompt>`** — think the task through, then build it. It can **decline or reframe** a
  bad idea rather than build it blindly.
- **`/musician`** (no prompt) — find a direction itself (via what-to-do), then build it.
- **`/musician-cancel`** — the manual brake.

Full details: [`plugins/cc-agent/README.md`](plugins/cc-agent/README.md).

### 3. cc-maestro — the console that supervises the fleet

The `ccmaestro` CLI watches and controls many coding agents and musicians at once:

```bash
ccmaestro ls                      # dashboard: tokens, last activity, watchdog verdict
ccmaestro start "fix flaky test" --repo ~/app
ccmaestro logs <id> --tail 50
ccmaestro stop <id> / steer <id> "do X now" / pause <id> / resume <id>
ccmaestro check --notify          # detect stalled/looping/died; POST changes to a webhook
```

It reads the native `claude agents` registry plus each session's transcript, and adds a
**watchdog** for verdicts the native status doesn't give (stalled, looping, over-budget, died).
Usable both by a human in a terminal and by an external supervising agent. Inside a session,
`/maestro` runs the dashboard.

Full details: [`plugins/cc-maestro/README.md`](plugins/cc-maestro/README.md).

## Install

Add this repo as a plugin marketplace, then install the layers you want:

```
/plugin marketplace add /Users/kubik/nox/misc/claude-code-harness
/plugin install cc-tools@cc-harness
/plugin install cc-agent@cc-harness      # optional — the musician
/plugin install cc-maestro@cc-harness    # optional — the fleet console
```

cc-tools is glue: it routes to skills/plugins you already have (`superpowers`, `frontend-design`,
`playwright`, `code-review`, `commit-commands`, and more). To install those dependencies in one
shot:

```
/cc-init
```

It shows a plan of what's missing, asks you to confirm, then installs only the gaps. Idempotent —
safe to re-run on a new machine.

Then **ground your product once** — every command depends on it:

```
/find-goal
```

## How the layers depend on each other

- **cc-tools** stands alone — the funnel skills work on their own.
- **cc-agent** depends on cc-tools (it invokes the funnel skills) and writes its loop state under
  `.claude/ccharness/`.
- **cc-maestro** observes and controls cc-agent (and any other Claude Code agent); it needs neither
  of the others installed to watch a fleet, but it's most useful supervising musicians.

## Repository layout

```
.claude-plugin/marketplace.json   the marketplace manifest (lists the 3 plugins)
plugins/
  cc-tools/      funnel skills + commands + /cc-init      (README.md)
  cc-agent/      the musician loop + Stop hooks            (README.md)
  cc-maestro/    the ccmaestro CLI + /maestro              (README.md)
docs/
  research/      background notes on agentic loops
  superpowers/   design specs + implementation plans
```

Runtime state for the agent layer lives under `.claude/ccharness/` (git-ignored, except the
roadmap).
