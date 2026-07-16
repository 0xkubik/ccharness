---
description: "Onboarding orchestrator for the cc-* harness, driven by AskUserQuestion. Ships in cc-config (the front desk). Opens with an orientation explaining the plugins (cc-config, cc-tools, cc-pipeline, cc-worker, cc-chief); Stage 0 installs missing marketplace dependencies and offers the recommended external tools (codegraph, headroom); then it runs three cc-config commands behind skip/stop gates — rules-management (recommended + project rules), cheatsheet-management (the reminder cheat-sheet), docs-management (find stale prose) — and finally offers /planner-brainstorm. Every step is offered and skippable; idempotent — safe to re-run."
argument-hint: "(no arguments)"
---

# cc-init — onboard the harness, explaining as you go

A guided onboarding **orchestrator**. It opens by explaining the harness, installs dependencies itself,
then hands the rest to three focused commands, gating every step with `AskUserQuestion`.
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

## Orientation — what the harness is (the plugins)

Before doing anything, explain the harness to the human in plain language — what the plugins are,
how they work together, and what's in each. Keep it short and concrete:

- **cc-config** (this plugin) — the **front desk**, the thing you run first: this `/cc-init`, the three
  setup commands it orchestrates (`/rules-management`, `/cheatsheet-management`, `/docs-management`), a
  set of recommended project rules, and the cheat-sheet reminder hook. Commands only — config is the
  human's to run; the model never invokes it. Installs and maintains the harness itself.
- **cc-tools** — the **primitives layer**, usable in any project: `/slap` (reset a fix stuck in a
  rabbit hole), `/likec4` (draw C4 architecture-as-code), `/reminder` (pin one rule file as a hard
  constraint), and `cctreectl` (map the project tree).
- **cc-pipeline** — the **build pipeline**: `/what-to-do` (rank where to go next) → `/how-to-do`
  (decide one fork) → `/do` (build one task by the writing rules) → `/refactor` → `/review` → `/test`
  (harden it). A diverge → decide → build → harden pipeline.
- **cc-worker** — the **second pilot**: hand `/worker` any piece of work and it adapts — reading the
  goal and design and reaching for the right skills to carry it out. Also houses `/planner-brainstorm` (draw the
  product's features out of the human) and `/sysdesign-brainstorm` (draw the architecture out into a living tree).
  Ships as a skill and a native subagent, so it works in the conversation or is delegated a task on its own.
- **cc-chief** — the **top brain**: `/chief` orchestrates the workers across a product's sub-projects
  (each a git repo under the current folder) — it keeps each sub-project's roadmap true and sequences
  the cross-repo work, dispatching workers as native subagents. It conducts; the workers build.

Then move into the stages.

---

## Stage 0 — Install dependencies & tools

The cc-pipeline is glue: `/what-to-do`, `/how-to-do`, and `/do` route to skills from **other**
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
> `plugins/cc-pipeline/README.md`. If you add or drop a dependency, update **both**.

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

**6. Offer the recommended external tools.** A few tools the harness benefits from don't live in the
marketplace — they install through their own tooling, not `claude plugin install`:

- **codegraph** — indexed code intelligence: an MCP that searches and explores a codebase, far better
  than raw `grep`/`Read` for "where is X / what calls Y". Repo:
  https://github.com/colbymchenry/codegraph
  - `npm install -g @colbymchenry/codegraph` → `codegraph install` (wires the MCP into Claude Code) →
    `codegraph init` per project to build the index.
- **headroom** — compresses tool outputs, logs, and files before they reach the model (60–95% fewer
  tokens, same answers). Repo: https://github.com/headroomlabs-ai/headroom
  - `pip install "headroom-ai[all]"` → `headroom mcp install`.
- **eza** — a tree-capable `ls`. The `cctreectl` helper uses it (or `tree`) to draw the project's folder
  tree, respecting `.gitignore`, for the "Map the codebase" step in `/do` and `/refactor`.
  Without a tree tool `cctreectl` still works — it falls back to a flat git file list — so this just buys
  the nicer tree view. Repo: https://github.com/eza-community/eza
  - `brew install eza` (macOS) or `cargo install eza` — or install the classic `tree` instead.

Gate with `AskUserQuestion` (`multiSelect: true`): **codegraph** / **headroom** / **eza** / **Skip all**.
Install only what's picked; **capture each exit code** and report honestly (✅ installed / ❌ failed, with
the command and output) — never claim an install you didn't see exit `0`. codegraph and headroom each
register an MCP server that loads on the **next** session; eza is a plain CLI and works immediately. If
the user later asks to set up or troubleshoot any of these, start from its repo link above.

---

## Stage 1 — Set up the rules

Explain why first: rules are the always-loaded guidance Claude reads every session. Gate with
`AskUserQuestion`:

- question: "Set up this project's rules now?"
- options: **Set up rules** / **Skip this stage** / **Stop the wizard**

On **Skip** → go to Stage 2. On **Stop** → end the wizard. On **Set up rules** → **read and follow
`${CLAUDE_PLUGIN_ROOT}/commands/rules-management.md`** (that command IS this step): it installs the
recommended rules you pick into `.claude/rules/`, then offers to capture the project's own. It explains
itself as it goes.

---

## Stage 2 — Build the reminder cheat-sheet

Explain why first: over a long session the model forgets the tooling it loaded at startup; a small
cheat-sheet, re-surfaced by a hook, keeps it in view. Gate with `AskUserQuestion`:

- question: "Build the reminder cheat-sheet?"
- options: **Build it** / **Skip this stage** / **Stop the wizard**

On **Skip** → go to Stage 3. On **Stop** → end the wizard. On **Build it** → **read and follow
`${CLAUDE_PLUGIN_ROOT}/commands/cheatsheet-management.md`** (that command IS this step): it inventories
the always-loaded tooling, lets you pick the lines, and writes `.claude/ccharness/cheatsheet.md`. It
explains itself as it goes.

---

## Stage 3 — Check the docs for stale prose

Explain why first: prose drifts out of date and quietly misleads later decisions; this finds what's no
longer true. Gate with `AskUserQuestion`:

- question: "Check this project's docs for stale prose?"
- options: **Check docs** / **Skip this stage** / **Stop the wizard**

On **Skip** → go to Stage 4. On **Stop** → end the wizard. On **Check docs** → **read and follow
`${CLAUDE_PLUGIN_ROOT}/commands/docs-management.md`** (that command IS this step): it reads the project's
prose, surfaces what looks stale for you to confirm, and fixes the confirmed ones. (On a fresh project
with nothing described yet, the command says so and does nothing.) It explains itself as it goes.

---

## Stage 4 — Set the product's direction

**Gate** with `AskUserQuestion`:
- question: "Run /planner-brainstorm now to start the product's roadmap?"
- options: **Run /planner-brainstorm now** / **Not now**

On **Run /planner-brainstorm now**, hand off to `/planner-brainstorm` (it draws the product's features out of you into the roadmap).
Note for the user: plugins installed in Stage 0 only activate on the next session, but
`/planner-brainstorm` does not hard-require them, so running it now is safe.
