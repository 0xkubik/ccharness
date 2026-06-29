# cc-harness

A **layered harness for Claude Code** — four plugins that stack on top of each other to take a
product from "what's the goal?" all the way to committed code, and then run that work
unsupervised across a whole fleet of agents.

```
cc-tools + cc-funnel   ──►   cc-agent   ──►   cc-maestro
the helpers & funnel         the musician      the console
you run                      that runs them    that watches them
by hand                      for you           all at once
```

- **cc-tools** — the *helpers layer*. Philosophy-agnostic side doors (`/crux`, `/slap`), the
  `/cc-init` setup wizard, and the harness's recommended project rules. Usable in any project.
- **cc-funnel** — the *funnel layer*. Single-purpose skills that form a thinking funnel:
  `ground → diverge → decide → build`. You drive them by hand, one step at a time. Depends on cc-tools.
- **cc-agent** — the *self-driving layer*. The **musician**: a single agent that takes one piece of
  work, runs the cc-funnel funnel to drive it to its own definition of done, then closes itself.
- **cc-maestro** — the *conductor layer*. A console (`ccmaestro`) that watches and controls many
  agents and musicians at once — token burn, stalls, loops, stop/steer.

Everything here is plain Markdown + JSON (instructions for Claude Code) plus a small Python/shell
CLI for the console — no app to build, no compile step.

## The layers

### 1. cc-tools & cc-funnel — what you drive by hand

**cc-tools** gives you two reasoning side doors that work in any project — **`/crux`** (unwind a pain
or doubt into one diagnosis) and **`/slap`** (reset a fix stuck in a rabbit hole) — plus the
**`/cc-init`** setup wizard and the harness's recommended project rules.

**cc-funnel** is a product funnel that refuses to skip the thinking:

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
- **`/slap`** — when a fix is stuck in a rabbit hole, force a step back and a fresh angle (cc-tools).

Full details: [`plugins/cc-funnel/README.md`](plugins/cc-funnel/README.md) (the funnel) and
[`plugins/cc-tools/README.md`](plugins/cc-tools/README.md) (the helpers).

### 2. cc-agent — the musician that runs the funnel for you

One autonomous loop — the **musician** — the project's brain for **one piece of work**. It plays the
cc-funnel instruments (what-to-do → how-to-do → do → refactor-review-test) plus cc-tools's crux/slap, forges its own falsifiable definition of
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
/plugin install cc-funnel@cc-harness     # the product funnel (depends on cc-tools)
/plugin install cc-agent@cc-harness      # optional — the musician
/plugin install cc-maestro@cc-harness    # optional — the fleet console
```

The cc-funnel funnel is glue: it routes to skills/plugins you already have (`superpowers`, `frontend-design`,
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

- **cc-tools** stands alone — the `/crux`, `/slap`, and `/cc-init` helpers work on their own.
- **cc-funnel** depends on cc-tools (it routes stuck fixes to `/slap`); the funnel skills are otherwise self-contained.
- **cc-agent** depends on cc-funnel (it invokes the funnel skills) and cc-tools (`/crux`, `/slap`), and writes its loop state under
  `.claude/ccharness/`.
- **cc-maestro** observes and controls cc-agent (and any other Claude Code agent); it needs neither
  of the others installed to watch a fleet, but it's most useful supervising musicians.

## Repository layout

```
.claude-plugin/marketplace.json   the marketplace manifest (lists the 4 plugins)
plugins/
  cc-tools/      /crux + /slap + /cc-init + rules          (README.md)
  cc-funnel/     funnel skills + commands                  (README.md)
  cc-agent/      the musician loop + Stop hooks            (README.md)
  cc-maestro/    the ccmaestro CLI + /maestro              (README.md)
docs/
  research/      background notes on agentic loops
  superpowers/   design specs + implementation plans
```

Runtime state for the agent layer lives under `.claude/ccharness/` (git-ignored, except the
roadmap).
