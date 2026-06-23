---
description: "Install the Claude Code plugins this harness orchestrates. Detects what's already present, shows a plan of what's missing, waits for your confirmation, then installs only the gaps from the official marketplace (user scope). Idempotent — safe to run any time, e.g. when setting up a new machine."
argument-hint: "(no arguments)"
---

# cc-init — equip the harness with the plugins it orchestrates

cc-tools is glue: `/point-it`, `/grill-it`, and `/implement-it` route to skills from
**other** plugins. Those plugins are not bundled — this command installs them.

## The dependency set

All of these live in the official marketplace `claude-plugins-official`
(GitHub source: `anthropics/claude-plugins-official`):

| Plugin | What the harness uses it for |
|---|---|
| `superpowers` | brainstorming, writing/executing plans, TDD, subagents, systematic-debugging, code-review review loop |
| `claude-md-management` | North Star capture / CLAUDE.md upkeep (point-it) |
| `frontend-design` | UI build route (implement-it stage 2) |
| `playwright` | browser-driven verification of UI (implement-it stage 4) |
| `code-simplifier` | the simplify pass (implement-it stage 5) |
| `ralph-loop` | long autonomous build loops (implement-it stage 2) |
| `code-review` | the review pass (implement-it stage 5) |
| `commit-commands` | the local commit + push/PR step (implement-it stage 6) |
| `gitlab` | GitLab MR path at push time (implement-it stage 6) |

> **Source of truth:** this table mirrors the "What it orchestrates" section of
> `plugins/cc-tools/README.md`. If you add or drop a dependency, update **both**.

Missing plugins are not fatal — the harness simply skips those routes. This command
just makes the full set available.

## Procedure

Run this as a strict, evidence-driven sequence. Use the `Bash` tool for every step.
Redirect stdin from `/dev/null` on every `claude plugin …` call so a prompt can never
hang the session.

### 1. Check the CLI is available

```
claude --version < /dev/null
```

If `claude` is not found, **stop** and tell the user the harness must be installed/run
via the Claude Code CLI for this command to work — then print the manual commands from
step 4 so they can run them by hand.

### 2. Detect current state

```
claude plugin marketplace list < /dev/null
claude plugin list < /dev/null
```

From the output determine:
- whether the `claude-plugins-official` marketplace is already configured, and
- which of the nine plugins above are already installed (any scope counts).

### 3. Show the plan and get confirmation

Print a short plan listing:
- the marketplace add (only if not already configured), and
- the plugins that are **missing** (the ones to install), explicitly noting the
  already-installed ones will be **skipped**.

State that installation is **user scope** (`--scope user`) — it changes global Claude
Code config, not just this repo. Then **ask the user to confirm** before proceeding.

If nothing is missing, report "all nine dependencies already installed — nothing to do"
and stop (no confirmation needed).

### 4. Install (after confirmation)

Add the marketplace if it was missing:

```
claude plugin marketplace add anthropics/claude-plugins-official < /dev/null
```

Then install each **missing** plugin (skip the ones already present):

```
claude plugin install <name>@claude-plugins-official --scope user < /dev/null
```

…where `<name>` is each missing entry from the table. Capture the exit code of every
install. A non-zero exit means that install failed (e.g. an unexpected prompt that hit
EOF) — do **not** report it as installed; collect it for the failure list instead.

### 5. Report honestly

Summarize what actually happened:
- ✅ newly installed (with the names),
- ⏭️  already present (skipped),
- ❌ failed, if any — show the command and its output so the user can run it by hand.

Then add the restart note:

> Newly installed plugins load on the **next** Claude Code session. Restart Claude Code
> (or start a fresh session) for the harness to pick them up.

Do not claim success for any plugin whose install you did not see exit `0`.
