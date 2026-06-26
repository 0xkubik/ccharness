---
description: "5-stage onboarding wizard for the cc-* harness, driven by AskUserQuestion. Stage 1 installs missing marketplace dependencies and offers the recommended external tools (codegraph, headroom); Stage 2 installs the harness's recommended rules into this project's .claude/rules/; Stage 3 builds the reminder cheat-sheet a UserPromptSubmit hook re-surfaces every few prompts so the project's tools and rules don't fade from attention; Stage 4 reconciles the project's prose docs against your current understanding so stale text doesn't mislead later decisions; Stage 5 offers to run /find-goal. Every stage is offered and skippable; idempotent — safe to re-run."
argument-hint: "(no arguments)"
---

# cc-init — set up the harness in five guided stages

A guided onboarding wizard. It runs five stages in order, each gated by an `AskUserQuestion` prompt
so you choose what happens at every step:

1. **Install dependencies** — the marketplace plugins the harness orchestrates.
2. **Install rules** — the harness's recommended rule files, into this project's `.claude/rules/`.
3. **Build the reminder cheat-sheet** — scan what's installed (MCP servers, rules, skills) and
   write a short cheat-sheet a hook re-surfaces every few prompts so it doesn't fade from context.
4. **Reconcile docs with reality** — check the project's prose docs against your current
   understanding so stale text doesn't quietly steer later decisions.
5. **Offer `/find-goal`** — set the product's North Star.

## Wizard flow

- The stages run **in order** but are **independent** — skipping one never breaks a later one.
- Each stage opens with an `AskUserQuestion` gate offering **Do it / Skip this stage / Stop the
  wizard** ("Skip" → next stage; "Stop" → end cleanly). The final stage's gate is **Run now / Not
  now**.
- The command is **idempotent** — re-running re-detects state and acts only on gaps, never silently
  clobbering anything.
- Use the `Bash` tool for shell steps. Redirect stdin from `/dev/null` on every `claude plugin …`
  call so a prompt can never hang the session.

---

## Stage 1 — Install missing dependencies

cc-tools is glue: `/what-to-do`, `/how-to-do`, and `/do` route to skills from **other**
plugins. Those plugins are not bundled — this stage installs them.

### The dependency set

All of these live in the official marketplace `claude-plugins-official`
(GitHub source: `anthropics/claude-plugins-official`):

| Plugin | What the harness uses it for |
|---|---|
| `superpowers` | brainstorming, writing/executing plans, TDD, subagents, systematic-debugging, code-review review loop |
| `claude-md-management` | North Star capture / CLAUDE.md upkeep (what-to-do) |
| `frontend-design` | UI build route (do stage 2) |
| `code-simplifier` | the simplify pass (do stage 5) |
| `ralph-loop` | long autonomous build loops (do stage 2) |
| `code-review` | the review pass (do stage 5) |
| `gitlab` | GitLab MR path at push time (do stage 6) |

> **Source of truth:** this table mirrors the "What it orchestrates" section of
> `plugins/cc-tools/README.md`. If you add or drop a dependency, update **both**.

Missing plugins are not fatal — the harness simply skips those routes. This stage just makes the
full set available.

**1. Check the CLI is available**

```
claude --version < /dev/null
```

If `claude` is not found, **stop** and tell the user the harness must be installed/run via the
Claude Code CLI for this command to work — then print the manual install commands below so they can
run them by hand.

**2. Detect current state**

```
claude plugin marketplace list < /dev/null
claude plugin list < /dev/null
```

From the output determine:
- whether the `claude-plugins-official` marketplace is already configured, and
- which of the seven plugins above are already installed (any scope counts).

**3. Gate + show the plan.** If nothing is missing, report "all seven dependencies already installed
— nothing to do" and move straight on to the recommended external tools below (no gate needed). Otherwise print a short plan
listing the marketplace add (only if not configured) and the **missing** plugins, noting the
already-installed ones will be **skipped**, and state that installation is **user scope**
(`--scope user`) — it changes global Claude Code config, not just this repo. Then gate with
`AskUserQuestion`:

- question: "Install the missing harness dependencies?"
- options: **Install missing** / **Skip this stage** / **Stop the wizard**

On **Skip** → go to Stage 2. On **Stop** → end the wizard.

**4. Install (on "Install missing").** Add the marketplace if it was missing:

```
claude plugin marketplace add anthropics/claude-plugins-official < /dev/null
```

Then install each **missing** plugin (skip the ones already present):

```
claude plugin install <name>@claude-plugins-official --scope user < /dev/null
```

…where `<name>` is each missing entry from the table. Capture the exit code of every install. A
non-zero exit means that install failed (e.g. an unexpected prompt that hit EOF) — do **not** report
it as installed; collect it for the failure list instead.

**5. Report honestly.** Summarize what actually happened:
- ✅ newly installed (with the names),
- ⏭️  already present (skipped),
- ❌ failed, if any — show the command and its output so the user can run it by hand.

> Newly installed plugins load on the **next** Claude Code session. Restart Claude Code (or start a
> fresh session) for the harness to pick them up.

Do not claim success for any plugin whose install you did not see exit `0`.

**6. Offer the recommended external tools.** Two tools the harness benefits from don't live in the
marketplace — they install through their own tooling, not `claude plugin install`:

- **codegraph** — indexed code intelligence: an MCP that searches and explores a codebase, far
  better than raw `grep`/`Read` for "where is X / what calls Y". Repo:
  https://github.com/colbymchenry/codegraph
  - `npm install -g @colbymchenry/codegraph` → `codegraph install` (wires the MCP into Claude
    Code) → `codegraph init` per project to build the index.
- **headroom** — compresses tool outputs, logs, and files before they reach the model (60–95%
  fewer tokens, same answers). Repo: https://github.com/headroomlabs-ai/headroom
  - `pip install "headroom-ai[all]"` → `headroom mcp install`.

Gate with `AskUserQuestion` (`multiSelect: true`): **codegraph** / **headroom** / **Skip both**.
Install only what's picked; **capture each exit code** and report honestly (✅ installed / ❌ failed,
with the command and output) — never claim an install you didn't see exit `0`. Both register an MCP
server that loads on the **next** session. If the user later asks to set up or troubleshoot either
tool, start from its repo link above.

---

## Stage 2 — Install recommended rules

The harness ships rule files (the `.claude/rules/` instructions Claude reads every session). This
stage copies the ones you pick into **this project's** `.claude/rules/` (committed to your repo).

**1. Gate** with `AskUserQuestion`:
- question: "Install the harness's recommended rules into this project?"
- options: **Install rules** / **Skip this stage** / **Stop the wizard**

On **Skip** → go to Stage 3. On **Stop** → end the wizard.

**2. List the available rules.**

```
ls "${CLAUDE_PLUGIN_ROOT}/rules/"*.md < /dev/null
```

For each file, read its first heading line (`# …`) to use as a human-readable label.

**3. Let the user choose** which to install with `AskUserQuestion`, `multiSelect: true` — one
option per rule file (label = its heading) — so the user can install any subset. The tool caps each
question at **4 options**; when there are more than four rules, split them across several
`multiSelect` questions of ≤4 options each (up to 4 questions ride in one `AskUserQuestion` call;
balance the batches so no question holds fewer than 2 options). Union the picks across all questions.

**4. Copy each selected rule** to `.claude/rules/<filename>` in the current project (create
`.claude/rules/` if it doesn't exist). **Before copying, check for a collision:** if
`.claude/rules/<filename>` already exists, gate with `AskUserQuestion` (**Overwrite** / **Skip**) —
never overwrite silently. Then:

```
mkdir -p .claude/rules
cp "${CLAUDE_PLUGIN_ROOT}/rules/<file>" .claude/rules/<file>
```

**5. Report** which rules were installed, skipped, or overwritten. Note they load on the next
session.

---

## Stage 3 — Build the reminder cheat-sheet

Over a long session the model's attention to the project's tools and rules fades — it drifts back
to its habitual moves (raw `grep`/`Read` instead of an indexed code search, ignoring a project
rule). This stage writes a short cheat-sheet that a shipped `UserPromptSubmit` hook re-surfaces
**every third prompt**, near the end of the context where it's most visible. The hook is dumb — it
just prints this file; all the intelligence happens here, once.

**1. Gate** with `AskUserQuestion`:
- question: "Build the reminder cheat-sheet for this project?"
- options: **Build it** / **Skip this stage** / **Stop the wizard**

On **Skip** → go to Stage 4. On **Stop** → end the wizard.

**2. Take inventory of what's actually available here** — three sources:
- **MCP servers** — the tools this session is connected to (cross-check with
  `claude mcp list < /dev/null`); flag the ones worth preferring over a built-in (an indexed code
  search over raw `grep`, a docs fetcher over memory).
- **Rules** — `ls .claude/rules/*.md < /dev/null`; read each `# ` heading for what it governs.
- **Skills** — the installed plugin skills worth reaching for (e.g. `/slap`, `/crux`, the funnel).

**3. Distill into a tiny cheat-sheet** — a handful of lines, each in the shape *situation →
preferred move*, plain and specific to THIS project. Keep it short (aim for ≤10 lines); a long
sheet becomes wallpaper the model also learns to skip.

**4. Enforce the width limit — strictly ≤ 80 characters per line.** The model is unreliable at
counting characters, so verify mechanically after drafting and fix any offender — re-run until it
prints nothing:

```
awk 'length > 80 {print NR": "length" chars"}' .claude/ccharness/cheatsheet.txt
```

**5. Write it** to `.claude/ccharness/cheatsheet.txt` (create `.claude/ccharness/` if needed). If
the file already exists, show the current contents and gate (**Overwrite** / **Keep current**)
before replacing — never clobber silently.

**6. Report** what you wrote and how it behaves: active from the **next** session, injected on
every third of your prompts; to turn it off, delete or rename `.claude/ccharness/cheatsheet.txt`
(the hook is a no-op without it).

---

## Stage 4 — Reconcile docs with reality

Stale prose quietly steers later decisions wrong. This stage checks the project's **descriptive
docs** against your current understanding. It reads only prose — **Code and tests are out of
scope.**

**1. Detect whether this is a working project.** It qualifies if any of these holds: there is at
least one commit —

```
git rev-list --count HEAD 2>/dev/null
```

— or there are source files beyond `.claude/` config, or descriptive docs exist. If none of these
hold → print "fresh project, nothing described yet — skipping" and go to Stage 5 (no gate).

**2. Gate** with `AskUserQuestion`:
- question: "Reconcile this project's docs against your current understanding?"
- options: **Reconcile** / **Skip this stage** / **Stop the wizard**

On **Skip** → go to Stage 5. On **Stop** → end the wizard.

**3. Read the descriptive prose only** — `README*`, `docs/**`, `CLAUDE.md`, `.claude/rules/*.md`,
`AGENTS.md`, `CHANGELOG*`, `.claude/ccharness/roadmap.md`, and other top-level descriptive `*.md`.
**Code and tests are out of scope.**

**4. Distill the load-bearing facts and invariants** the prose asserts into a concise,
plain-language **digest** — a bulleted list of claims, each tagged with its source doc. Not a
verbatim retelling; the load-bearing assertions only. Print the digest into the chat.

**5. Ask, in plain prose (not `AskUserQuestion`):** "Does this match your current understanding, or
is anything off? Write what doesn't match." Wait for the user's free-text reply.

**6. Fix the mismatches.** For each one, apply a **minimal** edit to the affected doc (the smallest
diff that fixes it — follow the `keep-files-lean` rule), or remove the obsolete with confirmation.
Report what changed.

---

## Stage 5 — Set the product's direction

**Gate** with `AskUserQuestion`:
- question: "Run /find-goal now to set the product's North Star?"
- options: **Run /find-goal now** / **Not now**

On **Run /find-goal now**, hand off to `/find-goal` (it owns the North Star write). Note for the user:
plugins installed in Stage 1 only activate on the next session, but `/find-goal` does not
hard-require them, so running it now is safe.
