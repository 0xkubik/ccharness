# Musician as a router — design

**Purpose:** turn `/musician` from one heavy end-to-end conductor into a thin router that sizes its
response to the work — from a small fix to a full feature — and always works against `roadmap.md` and
the architecture.

## The problem

Today `/musician` runs one fixed, heavy machine on everything: a shaping phase, a decomposed task
list, a mandatory isolated worktree, a mandatory final verify, git-notes awareness, and a
self-perpetuating Stop-hook loop that re-feeds itself turn after turn. That is right for a big feature
and far too much for a small fix — it goes at every task "like a nuclear bomb." The heavy machine is
also a single rigid pipeline: the command *is* the orchestration, so there is no room to just do a
small thing.

## The shape

`/musician` becomes a **thin router** that runs in the normal conversation. It reads the goal and the
design, decides *what kind of work* the task is, and hands it to the right component. Flags only tune
*how* the work is done, never *what*. There is no self-driving loop and no run bookkeeping — multi-step
work is carried in the conversation, turn by turn, with the human present.

Three ideas hold it together:

1. **The command decides *what*, flags decide *how*.** The router reads the prompt and picks the
   route itself. Flags (`--auto`, `--fast`, `--worktree`, `--ultracode`) are meta about how to carry
   it out; they never pick the route.
2. **Every call is grounded in `roadmap.md` + architecture.** The router reads them as context before
   acting, and reconciles them after if the work touched them.
3. **Weight matches the work.** A small fix is light; a big feature is heavy. The router routes to a
   tier that carries the right weight instead of forcing one weight on everything.

## The router — `/musician <task> [flags]`

The command body is routing instructions. Each `/musician` call:

1. **Reads context:** `docs/ccharness/roadmap.md` (North Star + features) and the architecture
   (`docs/ccharness/architecture/`), as grounding.
2. **Classifies the task** from its text and routes to one component (below). An empty prompt routes
   to `what-to-do` ("what should I do next").
3. **Dispatches** to the chosen skill/component and lets it carry the work.
4. **Reconciles after:** if the work advanced a roadmap feature or shifted the design, it updates
   `roadmap.md` / the architecture (mark a feature done, note a design shift). Work that touched
   neither → no upkeep.

**North Star gate:** when the task is build work and there is no `## Product North Star` in the
roadmap, the router sends the user to `/roadmap-management` first (matches today's gate). Non-build
routes (`crux`, `slap`) are not gated.

**Asking vs deciding:** by default the router is interactive — at a genuine fork (including "is this
small or medium?") it may ask the human with `AskUserQuestion`. `--auto` forbids asking: the router
resolves every fork itself.

## The route menu

The menu is **every skill in the plugins**, plus three new build tiers. The router picks one:

| The task is… | Route to |
| --- | --- |
| a large feature / substantial build | **build-large** (new tier skill) |
| a medium change | **build-medium** (new tier skill) |
| a small fix | **build-small** (new tier skill) |
| designing a new system | `cc-script:architect` |
| a fuzzy pain / "something's off" | `cc-instruments:crux` |
| stuck in a debugging rabbit hole | `cc-instruments:slap` |
| changing the goal / priorities | `cc-script:roadmap-management` |
| "what should I do next" (empty prompt) | `cc-script:what-to-do` |
| rules / cheatsheet / docs / diagrams upkeep | the matching cc-instruments management or diagram skill |

The lower cc-script instruments (`what-to-do`, `how-to-do`, `do`, `refactor-review-test`) remain their
own skills; the tier skills call them internally as needed. The router may also call them directly
when the task obviously *is* that one step.

## The three build tiers (separate skills)

Each tier is its own skill and assembles its own behavior for the concrete task. They differ by how
much weight they carry:

- **build-large** — full weight. Break the work into an ordered task list, build in an **isolated
  worktree**, harden via `refactor-review-test`, run a **real final verification**, then reconcile the
  roadmap. This inherits the current musician's build guarantees: code changes go through a
  `cc-script:do` subagent (never inline), and the run isn't "done" until a real check passes. This is
  the home of the heavy orchestration the router itself no longer holds.
- **build-medium** — lighter. One or two `do` passes, a light check that it works, no heavy
  decomposition or task list.
- **build-small** — lightest. Make the fix and confirm nothing broke. Minimal ceremony; may edit
  directly or dispatch a single `do`, as fits.

Isolation, when a tier needs it, uses the Agent tool's `isolation:"worktree"` directly — there is no
worktree helper script.

## Flags — how, not what

- `--auto` — act without asking; resolve every fork yourself. (Default: interactive, ask at real
  forks.) This is **not** a persistent loop — just autonomy of decision within the conversation.
- `--fast` — fast mode: lighter model, fewer subagents, minimal hardening. Bias to speed.
- `--worktree` — force worktree isolation for the build even on a small/medium change.
- `--ultracode` — maximum fan-out: a Workflow and/or parallel `do` subagents, each worktree-isolated.
  Bias to thoroughness.

Any tier respects any flag. Flags stack.

## What gets deleted

The self-driving-run machinery goes entirely — the user has never used arm or nonstop, so there is no
reason to keep it:

- `skills/musician/SKILL.md` (the heavy conductor skill) and its `arm.sh`, `worktree.sh`
- run bookkeeping: `state.json`, `runs/`, `by-session`, `heartbeat`
- hooks: `musician-stop.sh` (the re-feed loop), `nonstop-stop.sh`, `musician-observe.sh`,
  `musician-resolve.sh`, and `hooks.json`
- `commands/musician-cancel.md`, `bin/ccmusicianctl`
- the tests covering all of the above (`test_arm.py`, `test_worktree.py`, `test_musician_hook.py`,
  `test_observe_hook.py`, `test_nonstop_hook.py`, and the run-machinery parts of
  `test_ccmusicianctl.py` / `test_skill_invariants.py`)

## What `cc-musician` contains after

- `commands/musician.md` — the router
- `skills/build-large/`, `skills/build-medium/`, `skills/build-small/` — the three tier skills
- tests for the new skills/router as warranted (skill-invariant tests only where a string is a real
  text↔code contract)

`cc-script` and `cc-instruments` are untouched — they simply become routes.

## Non-goals

- No persistent multi-turn loop, no arm/state/heartbeat, no nonstop, no `/musician-cancel`.
- No git-notes awareness layer (it belonged to the multi-run loop).
- No shaping phase as a distinct mode (the default interactive router already asks when it needs to).
- No changes to the cc-script / cc-instruments skills themselves.
