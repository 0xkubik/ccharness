---
description: "Onboarding orchestrator for the cc-* harness, driven by AskUserQuestion. Opens with an orientation explaining the four plugins (cc-tools, cc-funnel, cc-agent, cc-maestro); Stage 0 installs missing marketplace dependencies and offers the recommended external tools (codegraph, headroom); then it runs three skills behind skip/stop gates — rules-management (recommended + project rules), cheatsheet-management (the reminder cheat-sheet), docs-management (find stale prose) — and finally offers /roadmap-management. Every step is offered and skippable; idempotent — safe to re-run."
argument-hint: "(no arguments)"
---

# cc-init — onboard the harness, explaining as you go

A guided onboarding **orchestrator**. It opens by explaining the harness, installs dependencies itself,
then hands the rest to three focused skills, gating every step with `AskUserQuestion`.
**Explain as you go — don't just run steps.** At each stage, tell the human in plain language what it's
for and why before you act, so it's always clear what's happening and why — not just files changing.

## Wizard flow

- The stages run **in order** but are **independent** — skipping one never breaks a later one.
- Each stage opens with an `AskUserQuestion` gate offering **Do it / Skip this stage / Stop the wizard**
  ("Skip" → next stage; "Stop" → end cleanly). The final stage's gate is **Run now / Not now**. The
  gates live here; the skills this orchestrates are gate-free — they just do the work (their own
  `AskUserQuestion` choices, like *which* rules or *which* cheat-sheet lines, are part of that work).
- It is **idempotent** — re-running re-detects state and acts only on gaps, never silently clobbering.
- Use the `Bash` tool for shell steps. Redirect stdin from `/dev/null` on every `claude plugin …` call
  so a prompt can never hang the session.

---

## Orientation — what the harness is (the four plugins)

Before doing anything, explain the harness to the human in plain language — what the four plugins are,
how they work together, and what's in each. Keep it short and concrete:

- **cc-tools** (this plugin) — the **helpers layer**, usable in any project: `/crux` (unwind a pain or
  doubt into one diagnosis), `/slap` (reset a fix stuck in a rabbit hole), this `/cc-init`, the three
  setup skills it orchestrates (`rules-management`, `cheatsheet-management`, `docs-management`), and a
  set of recommended project rules.
- **cc-funnel** — the **product funnel**: `/roadmap-management` (set the goal + ordered feature list) →
  `/what-to-do` (rank where to go next) → `/how-to-do` (decide one fork) → `/do` (build one task to a
  smoke-checked finish) → `/refactor-review-test` (harden it and commit). A ground → diverge → decide →
  build pipeline.
- **cc-agent** — the **self-driving layer**: `/musician` carries ONE piece of work end to end — it
  thinks first (and may decline a bad idea), plays the funnel instruments, builds in an isolated
  worktree, and closes itself. Bounded, not a never-stop loop.
- **cc-maestro** — the **conductor**: the `ccmaestro` console (`/maestro`) watches and controls many
  running agents at once — token burn, stalls, loops, stop/steer.

Then move into the stages.

---

## Stage 0 — Install dependencies & tools

The cc-funnel funnel is glue: `/what-to-do`, `/how-to-do`, and `/do` route to skills from **other**
plugins. Those plugins are not bundled — this stage installs them.

### The dependency set

All of these live in the official marketplace `claude-plugins-official`
(GitHub source: `anthropics/claude-plugins-official`):

| Plugin | What the harness uses it for |
|---|---|
| `superpowers` | brainstorming, writing/executing plans, TDD, subagents, systematic-debugging, code-review review loop |
| `claude-md-management` | CLAUDE.md upkeep (what-to-do) |
| `frontend-design` | UI build route (do stage 2) |
| `code-simplifier` | the simplify pass (do stage 5) |
| `ralph-loop` | long autonomous build loops (do stage 2) |
| `code-review` | the review pass (do stage 5) |

> **Source of truth:** this table mirrors the "What it orchestrates" section of
> `plugins/cc-funnel/README.md`. If you add or drop a dependency, update **both**.

Missing plugins are not fatal — the harness simply skips those routes. This stage just makes the full
set available.

**1. Check the CLI is available**

```
claude --version < /dev/null
```

If `claude` is not found, **stop** and tell the user the harness must be installed/run via the Claude
Code CLI for this command to work — then print the manual install commands below so they can run them by
hand.

**2. Detect current state**

```
claude plugin marketplace list < /dev/null
claude plugin list < /dev/null
```

From the output determine whether the `claude-plugins-official` marketplace is already configured, and
which of the six plugins above are already installed (any scope counts).

**3. Gate + show the plan.** If nothing is missing, report "all six dependencies already installed —
nothing to do" and move straight on to the recommended external tools below (no gate needed). Otherwise
print a short plan listing the marketplace add (only if not configured) and the **missing** plugins,
noting the already-installed ones will be **skipped**, and state that installation is **user scope**
(`--scope user`) — it changes global Claude Code config, not just this repo. Then gate with
`AskUserQuestion`:

- question: "Install the missing harness dependencies?"
- options: **Install missing** / **Skip this stage** / **Stop the wizard**

On **Skip** → go to Stage 1. On **Stop** → end the wizard.

**4. Install (on "Install missing").** Add the marketplace if it was missing:

```
claude plugin marketplace add anthropics/claude-plugins-official < /dev/null
```

Then install each **missing** plugin (skip the ones already present):

```
claude plugin install <name>@claude-plugins-official --scope user < /dev/null
```

…where `<name>` is each missing entry from the table. Capture the exit code of every install. A non-zero
exit means that install failed (e.g. an unexpected prompt that hit EOF) — do **not** report it as
installed; collect it for the failure list instead.

**5. Report honestly.** Summarize what actually happened: ✅ newly installed (with names), ⏭️ already
present (skipped), ❌ failed, if any — show the command and its output so the user can run it by hand.

> Newly installed plugins load on the **next** Claude Code session. Restart Claude Code (or start a
> fresh session) for the harness to pick them up.

Do not claim success for any plugin whose install you did not see exit `0`.

**6. Offer the recommended external tools.** Two tools the harness benefits from don't live in the
marketplace — they install through their own tooling, not `claude plugin install`:

- **codegraph** — indexed code intelligence: an MCP that searches and explores a codebase, far better
  than raw `grep`/`Read` for "where is X / what calls Y". Repo:
  https://github.com/colbymchenry/codegraph
  - `npm install -g @colbymchenry/codegraph` → `codegraph install` (wires the MCP into Claude Code) →
    `codegraph init` per project to build the index.
- **headroom** — compresses tool outputs, logs, and files before they reach the model (60–95% fewer
  tokens, same answers). Repo: https://github.com/headroomlabs-ai/headroom
  - `pip install "headroom-ai[all]"` → `headroom mcp install`.

Gate with `AskUserQuestion` (`multiSelect: true`): **codegraph** / **headroom** / **Skip both**. Install
only what's picked; **capture each exit code** and report honestly (✅ installed / ❌ failed, with the
command and output) — never claim an install you didn't see exit `0`. Both register an MCP server that
loads on the **next** session. If the user later asks to set up or troubleshoot either tool, start from
its repo link above.

---

## Stage 1 — Set up the rules

Explain why first: rules are the always-loaded guidance Claude reads every session. Gate with
`AskUserQuestion`:

- question: "Set up this project's rules now?"
- options: **Set up rules** / **Skip this stage** / **Stop the wizard**

On **Skip** → go to Stage 2. On **Stop** → end the wizard. On **Set up rules** → **invoke the
`rules-management` skill**: it installs the recommended rules you pick into `.claude/rules/`, then offers
to capture the project's own. It explains itself as it goes.

---

## Stage 2 — Build the reminder cheat-sheet

Explain why first: over a long session the model forgets the tooling it loaded at startup; a small
cheat-sheet, re-surfaced by a hook, keeps it in view. Gate with `AskUserQuestion`:

- question: "Build the reminder cheat-sheet?"
- options: **Build it** / **Skip this stage** / **Stop the wizard**

On **Skip** → go to Stage 3. On **Stop** → end the wizard. On **Build it** → **invoke the
`cheatsheet-management` skill**: it inventories the always-loaded tooling, lets you pick the lines, and
writes `.claude/ccharness/cheatsheet.md`. It explains itself as it goes.

---

## Stage 3 — Check the docs for stale prose

Explain why first: prose drifts out of date and quietly misleads later decisions; this finds what's no
longer true. Gate with `AskUserQuestion`:

- question: "Check this project's docs for stale prose?"
- options: **Check docs** / **Skip this stage** / **Stop the wizard**

On **Skip** → go to Stage 4. On **Stop** → end the wizard. On **Check docs** → **invoke the
`docs-management` skill**: it reads the project's prose, surfaces what looks stale for you to confirm,
and fixes the confirmed ones. (On a fresh project with nothing described yet, the skill says so and does
nothing.) It explains itself as it goes.

---

## Stage 4 — Set the product's direction

**Gate** with `AskUserQuestion`:
- question: "Run /roadmap-management now to set the product's North Star?"
- options: **Run /roadmap-management now** / **Not now**

On **Run /roadmap-management now**, hand off to `/roadmap-management` (it owns the North Star write).
Note for the user: plugins installed in Stage 0 only activate on the next session, but
`/roadmap-management` does not hard-require them, so running it now is safe.
