# cc-init Wizard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `/cc-init` into a 4-stage, `AskUserQuestion`-driven onboarding wizard
(deps → install rules → reconcile docs-vs-reality → offer `/chart-it`), and ship the first
distributable rule file.

**Architecture:** Extend the existing markdown command `plugins/cc-tools/commands/cc-init.md` in
place — Stage 1's install logic is preserved verbatim, Stages 2–4 are appended, and confirmations
move to `AskUserQuestion`. A new bundled rule file (`plugins/cc-tools/rules/keep-files-lean.md`) is
the payload Stage 2 copies into the user's project `.claude/rules/`, resolved at runtime via
`${CLAUDE_PLUGIN_ROOT}/rules/`. Verification follows the repo's established pattern: string-presence
invariant tests over the markdown (`plugins/cc-tools/tests/`), run with `python3 -m pytest`.

**Tech Stack:** Claude Code plugin (Markdown command + `.md` rule file), Python `unittest`/`pytest`
for structural invariants, `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths.

## Global Constraints

- **Extend in place — do NOT rewrite the file from scratch.** Stage 1 keeps every current behavior:
  `claude --version` CLI check with manual-commands fallback, state detection, install only the gaps,
  `--scope user`, honest exit-code reporting, `< /dev/null` on every `claude plugin …` call, and the
  "load on next session" note.
- **Each stage is offered and skippable.** Every stage opens with an `AskUserQuestion` gate offering
  **Do it / Skip / Stop wizard** (the last stage's gate is **Run now / Not now**). The command must
  remain **idempotent** (re-detect state, act only on gaps, never silently clobber).
- **Stage 2 install target is the project `.claude/rules/`** (committed to the user's repo) — NOT
  `~/.claude/rules/`. Rules are read from `${CLAUDE_PLUGIN_ROOT}/rules/`. On a name collision, ask
  **Overwrite / Skip** — never overwrite silently.
- **Stage 3 is prose-only.** It reads descriptive docs (`README`, `docs/**`, `CLAUDE.md`,
  `.claude/rules/`, `AGENTS.md`, `CHANGELOG`, the roadmap, other descriptive `*.md`). **Code and
  tests are out of scope.** It produces a digest of claims/invariants, the user free-texts the
  mismatches, and fixes are applied as minimal diffs.
- **Only one seed rule now** (`keep-files-lean.md`); the wizard discovers whatever `*.md` are in the
  bundled `rules/` dir rather than hardcoding a list.
- Command instructions and user-facing question text are in **English** (the plugin is distributed
  broadly; matches the existing command).
- Run tests from `plugins/cc-tools/`: `python3 -m pytest tests/ -q`. Baseline today: 11 passed.

---

### Task 1: Ship the seed rule `keep-files-lean.md`

**Files:**
- Create: `plugins/cc-tools/rules/keep-files-lean.md`
- Create: `plugins/cc-tools/tests/test_cc_init_wizard.py`

**Interfaces:**
- Produces: the bundled rule file at `rules/keep-files-lean.md` and the test module
  `tests/test_cc_init_wizard.py` (Task 2 adds a second class to this same module).

- [ ] **Step 1: Write the failing test** — create `plugins/cc-tools/tests/test_cc_init_wizard.py`:

```python
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = ROOT / "rules"
LEAN = RULES_DIR / "keep-files-lean.md"


class TestSeedRule(unittest.TestCase):
    def setUp(self):
        self.text = LEAN.read_text() if LEAN.exists() else ""

    def test_rules_dir_exists(self):
        self.assertTrue(RULES_DIR.is_dir(), "plugins/cc-tools/rules/ missing")

    def test_seed_rule_exists(self):
        self.assertTrue(LEAN.exists(), "keep-files-lean.md missing")

    def test_always_on_no_paths_frontmatter(self):
        # No `paths:` frontmatter => the rule loads every session (always-on), not path-scoped.
        self.assertNotIn("paths:", self.text)

    def test_covers_create_and_edit(self):
        low = self.text.lower()
        self.assertIn("creating a file", low)
        self.assertIn("editing a file", low)

    def test_minimal_diff_principle(self):
        self.assertIn("smallest diff", self.text.lower())
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd plugins/cc-tools && python3 -m pytest tests/test_cc_init_wizard.py -q`
Expected: FAIL — `plugins/cc-tools/rules/ missing` / `keep-files-lean.md missing`.

- [ ] **Step 3: Create the rule file** — `plugins/cc-tools/rules/keep-files-lean.md` with exactly:

```markdown
# Keep files lean — when creating AND when editing

Every file has a purpose. What earns a place in it is whatever serves that purpose; everything else
stays out. This applies to NEW files you write and to edits of existing ones.

**Creating a file:** fix its purpose first, in one sentence, then write only what advances that
purpose. Run every line through that filter — drop background that merely came up in conversation,
tangents, and "nice to have" extras. Lean and on-point beats thorough-but-bloated.

**Editing a file:** change ONLY what was asked for. The default is the smallest diff that satisfies
the request — not a rewrite, not a "cleanup", not a restructure.

- **Scope = the request and the file's purpose, NOT the conversation.** Discussing something at
  length does not mean it belongs in the file. Don't pour the chat into the document.
- **Preserve what's already there (when editing).** Keep existing wording, structure, order, and
  formatting untouched outside the lines you were asked to change. Leave the rest byte-for-byte.
- **No unsolicited additions.** Don't add sections, examples, caveats, or boilerplate that weren't
  asked for or don't serve the file's purpose.
- **WHY is context for the one edit, not a brief to expand.** When someone explains why they're
  making a change, use it to get that single edit right — not as license to write or rewrite more.
- **If a bigger rewrite really seems warranted, STOP and propose it separately** — say what and why,
  and let the human decide. Never fold a large rewrite into a small-edit request.
- When unsure about scope, do less and ask.
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd plugins/cc-tools && python3 -m pytest tests/test_cc_init_wizard.py -q`
Expected: PASS (5 tests in `TestSeedRule`).

- [ ] **Step 5: Commit**

```bash
git add plugins/cc-tools/rules/keep-files-lean.md plugins/cc-tools/tests/test_cc_init_wizard.py
git commit -m "feat(cc-tools): ship keep-files-lean as a distributable rule + invariant test"
```

---

### Task 2: Rewrite `cc-init.md` into the 4-stage wizard

**Files:**
- Modify: `plugins/cc-tools/commands/cc-init.md` (frontmatter `description` + body)
- Modify: `plugins/cc-tools/tests/test_cc_init_wizard.py` (add `TestCcInitWizard`)
- Modify: `plugins/cc-tools/README.md` (cc-init description → 4-stage wizard)

**Interfaces:**
- Consumes: `rules/keep-files-lean.md` from Task 1 (the payload Stage 2 lists + copies).
- Produces: the 4-stage command. Must contain these exact marker strings (the test contract):
  `AskUserQuestion`, `Stage 1`, `Stage 2`, `Stage 3`, `Stage 4`, `/dev/null`, `--scope user`,
  `CLAUDE_PLUGIN_ROOT`, `.claude/rules/`, `Code and tests are out of scope`, `/chart-it`,
  `idempotent`.

- [ ] **Step 1: Write the failing test** — append to `plugins/cc-tools/tests/test_cc_init_wizard.py`:

```python
CC_INIT = ROOT / "commands" / "cc-init.md"


class TestCcInitWizard(unittest.TestCase):
    def setUp(self):
        self.text = CC_INIT.read_text() if CC_INIT.exists() else ""

    def test_exists(self):
        self.assertTrue(CC_INIT.exists(), "cc-init.md missing")

    def test_uses_askuserquestion(self):
        self.assertIn("AskUserQuestion", self.text)

    def test_four_stages_present(self):
        low = self.text.lower()
        for marker in ("stage 1", "stage 2", "stage 3", "stage 4"):
            self.assertIn(marker, low)

    def test_stage1_antihang_preserved(self):
        # The </dev/null guard on `claude plugin` calls must survive the rewrite.
        self.assertIn("/dev/null", self.text)

    def test_stage1_user_scope_preserved(self):
        self.assertIn("--scope user", self.text)

    def test_stage2_from_plugin_root_to_project_rules(self):
        self.assertIn("CLAUDE_PLUGIN_ROOT", self.text)
        self.assertIn(".claude/rules/", self.text)

    def test_stage3_prose_only(self):
        self.assertIn("Code and tests are out of scope", self.text)

    def test_stage4_offers_chart_it(self):
        self.assertIn("/chart-it", self.text)

    def test_idempotent_documented(self):
        self.assertIn("idempotent", self.text.lower())
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd plugins/cc-tools && python3 -m pytest tests/test_cc_init_wizard.py::TestCcInitWizard -q`
Expected: FAIL — current `cc-init.md` has no `AskUserQuestion`, no `Stage 2/3/4`, no
`CLAUDE_PLUGIN_ROOT`, etc.

- [ ] **Step 3: Update the frontmatter `description`** of `plugins/cc-tools/commands/cc-init.md` to:

```yaml
description: "4-stage onboarding wizard for the cc-* harness, driven by AskUserQuestion. Stage 1 installs missing marketplace dependencies; Stage 2 installs the harness's recommended rules into this project's .claude/rules/; Stage 3 reconciles the project's prose docs against your current understanding so stale text doesn't mislead later decisions; Stage 4 offers to run /chart-it. Every stage is offered and skippable; idempotent — safe to re-run."
```

- [ ] **Step 4: Add the wizard preamble** after the existing intro, before the procedure. Write a
  `## Wizard flow` section stating: the command runs four stages **in order**; each stage opens with
  an `AskUserQuestion` gate offering **Do it / Skip / Stop wizard** ("Skip" → next stage, "Stop" →
  end cleanly); stages are independent so skipping one never breaks a later one; the command is
  **idempotent** — re-running re-detects state and acts only on gaps, never silently clobbering.

- [ ] **Step 5: Convert Stage 1 to a gated stage (keep all mechanics).** Wrap the *existing*
  procedure (CLI check, detect state, plan, install gaps, honest report) under a `### Stage 1 —
  Install missing dependencies` heading. Replace the plain "ask the user to confirm" wording with an
  `AskUserQuestion` gate:
  - question: `"Install the missing harness dependencies?"`
  - options: `Install missing` / `Skip this stage` / `Stop the wizard`
  Keep verbatim: `claude --version < /dev/null`, the CLI-missing fallback that prints the manual
  commands, `claude plugin marketplace list/add < /dev/null`, `claude plugin install
  <name>@claude-plugins-official --scope user < /dev/null`, exit-code honesty, and the
  "load on the next session" restart note. Keep the existing "nothing missing → report and skip"
  early exit.

- [ ] **Step 6: Add Stage 2 — install the harness's rules.** Write `### Stage 2 — Install
  recommended rules` instructing:
  1. Gate via `AskUserQuestion`: question `"Install the harness's recommended rules into this
     project?"`, options `Install rules` / `Skip this stage` / `Stop the wizard`.
  2. List the available rule files: `ls "${CLAUDE_PLUGIN_ROOT}/rules/"*.md`. For each, read its first
     heading line as a label.
  3. Offer them via `AskUserQuestion` with `multiSelect: true` — the user picks which to install.
  4. For each selected rule, the target is `.claude/rules/<filename>` in the **current project**
     (create `.claude/rules/` if absent). If the target already exists, ask `AskUserQuestion`
     **Overwrite / Skip** — never overwrite silently. Copy with
     `cp "${CLAUDE_PLUGIN_ROOT}/rules/<file>" .claude/rules/<file>`.
  5. Report which rules were installed, skipped, or overwritten, and note they load on the next
     session.

- [ ] **Step 7: Add Stage 3 — reconcile docs with reality.** Write `### Stage 3 — Reconcile docs
  with reality` instructing:
  1. Detect whether this is a "working project": `git rev-list --count HEAD 2>/dev/null` > 0, OR
     source files exist beyond `.claude/`, OR descriptive docs exist. If none → print "fresh project,
     nothing described yet — skipping" and move on (no gate).
  2. Gate via `AskUserQuestion`: question `"Reconcile this project's docs against your current
     understanding?"`, options `Reconcile / Skip this stage / Stop the wizard`.
  3. On `Reconcile`: read the descriptive prose only — `README*`, `docs/**`, `CLAUDE.md`,
     `.claude/rules/*.md`, `AGENTS.md`, `CHANGELOG*`, `.claude/ccharness/roadmap.md`, and other
     top-level descriptive `*.md`. **Code and tests are out of scope.**
  4. Distill the load-bearing **facts and invariants** the prose asserts into a concise
     plain-language digest — a bulleted list of claims, each tagged with its source doc. Not a
     verbatim retelling. Print the digest into the chat.
  5. Ask an open question (plain prose, not `AskUserQuestion`): *"Does this match your current
     understanding, or is anything off? Write what doesn't match."* Wait for the user's free-text
     reply.
  6. For each mismatch, apply a **minimal** edit to the affected doc (smallest diff; per the
     keep-files-lean rule) or remove the obsolete with confirmation. Report what changed.

- [ ] **Step 8: Add Stage 4 — offer `/chart-it`.** Write `### Stage 4 — Set the product's direction`
  instructing: gate via `AskUserQuestion`: question `"Run /chart-it now to set the product's North
  Star?"`, options `Run /chart-it now` / `Not now`. On `Run`, hand off to `/chart-it`. Note to the
  user: dependencies installed in Stage 1 only activate next session, but `/chart-it` does not
  hard-require them, so running now is safe.

- [ ] **Step 9: Run the wizard tests to verify they pass**

Run: `cd plugins/cc-tools && python3 -m pytest tests/test_cc_init_wizard.py -q`
Expected: PASS (all `TestSeedRule` + `TestCcInitWizard` tests).

- [ ] **Step 10: Update the README.** In `plugins/cc-tools/README.md`, update the `/cc-init`
  description to: a 4-stage onboarding wizard (deps → rules → docs reconciliation → offer
  `/chart-it`), driven by `AskUserQuestion`, each stage skippable, idempotent. Do **not** alter the
  dependency table itself (the cc-init ↔ README "source of truth" dependency list is unchanged).

- [ ] **Step 11: Run the full cc-tools suite + plugin smoke check**

Run: `cd plugins/cc-tools && python3 -m pytest tests/ -q`
Expected: PASS (the original 11 + the new wizard tests).

Run: `claude plugin validate ./plugins/cc-tools < /dev/null` (from repo root, if the subcommand is
available). Expected: validates OK (a bundled non-component `rules/` asset dir is fine; at most an
ignorable note). If `validate` is unavailable, skip — the invariant suite is the gate.

- [ ] **Step 12: Commit**

```bash
git add plugins/cc-tools/commands/cc-init.md plugins/cc-tools/tests/test_cc_init_wizard.py plugins/cc-tools/README.md
git commit -m "feat(cc-tools): cc-init becomes a 4-stage AskUserQuestion wizard (deps, rules, doc reconciliation, chart-it)"
```

---

## Self-Review

**Spec coverage:**
- Stage gating (Do/Skip/Stop, idempotent) → Task 2 Steps 4–8 + `test_idempotent_documented`. ✓
- Stage 1 preserved (anti-hang, user scope, fallback, honest report) → Task 2 Step 5 +
  `test_stage1_antihang_preserved` / `test_stage1_user_scope_preserved`. ✓
- Stage 2 (bundled rules → project `.claude/rules/`, multi-select, overwrite/skip) → Task 1 (payload)
  + Task 2 Step 6 + `test_stage2_from_plugin_root_to_project_rules`. ✓
- Stage 3 (prose-only digest + free-text + minimal fixes; working-project detection) → Task 2 Step 7
  + `test_stage3_prose_only`. ✓
- Stage 4 (offer `/chart-it`, standalone-safe caveat) → Task 2 Step 8 + `test_stage4_offers_chart_it`. ✓
- Seed rule `keep-files-lean.md`, always-on, create+edit → Task 1 + `TestSeedRule`. ✓
- README refresh → Task 2 Step 10. ✓

**Placeholder scan:** none — full rule content and full test code are inline; command stages are
specified by concrete instructions plus the exact marker strings the tests pin.

**Type/string consistency:** the marker strings asserted in `TestCcInitWizard` (`Stage 1`–`Stage 4`,
`AskUserQuestion`, `/dev/null`, `--scope user`, `CLAUDE_PLUGIN_ROOT`, `.claude/rules/`, `Code and
tests are out of scope`, `/chart-it`, `idempotent`) are each produced by a named Task 2 step. The
test module path `tests/test_cc_init_wizard.py` and `RULES_DIR`/`LEAN`/`CC_INIT` constants are
consistent across Task 1 and Task 2.
