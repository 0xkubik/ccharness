# cc-init Wizard Design

**Goal:** Turn `/cc-init` from a single-purpose dependency installer into a 4-stage onboarding
wizard, driven by `AskUserQuestion` so the user steps through it with explicit choices. Each stage
is *offered and skippable*; the command stays idempotent (safe to re-run).

**Scope:** Extend the existing `plugins/cc-tools/commands/cc-init.md` in place — do **not** rewrite
it. Stage 1 keeps all its current robustness verbatim. Plus one new shipped rule file and a small
README touch. This is a markdown-command change, not a code change.

## Stage gating (applies to every stage)

Each stage opens with an `AskUserQuestion` gate offering **{Do it / Skip / Stop the wizard}**.
"Skip" moves to the next stage; "Stop" ends the wizard cleanly. Stages run in order but are
independent — skipping one never breaks a later one. Re-running the wizard re-detects state and only
acts on gaps, never silently clobbering.

## Stage 1 — Dependencies (preserve current behavior)

The existing logic is kept as-is: check the `claude` CLI, detect already-installed plugins, show the
plan of what's missing, install only the gaps from `claude-plugins-official` at **user scope**,
honest exit-code reporting, and `</dev/null` on every `claude plugin …` call (anti-hang). The **only**
change: the "install?" confirmation moves into `AskUserQuestion` for consistency with the other
stages. Do not regress the CLI-missing fallback (print manual commands) or the "load on next session"
note.

## Stage 2 — Install the harness's offered rules (new)

- Shipped rule files live in the plugin at `plugins/cc-tools/rules/*.md` (resolved at runtime via the
  plugin root).
- Seed exactly one real rule now: `keep-files-lean.md` — "every file has a purpose; edit minimally;
  when creating, include only what serves that purpose." (The same rule already codified in the
  user's global `~/.claude/CLAUDE.md`, repackaged as a standalone, always-on rule file with no
  `paths:` frontmatter.) The set is designed to grow; the wizard discovers whatever `*.md` files are
  present, not a hardcoded list.
- The wizard lists the available rules via `AskUserQuestion` (multi-select — which to install) and
  copies the chosen files into the **current project's** `.claude/rules/` (committed to the user's
  repo). If a target file already exists, ask **{overwrite / skip}** — never overwrite silently.

## Stage 3 — Reconcile docs with reality (new; the core stage)

Purpose: stale prose silently steers later AI decisions wrong. This stage checks the project's
**descriptive (prose) artifacts** against the user's current understanding — it never touches code.

1. Detect whether this is a "working project": has commits, or source files beyond `.claude/`
   config, or descriptive docs. A fresh/empty project → skip this stage (nothing is described yet).
2. On "Do it", gather the load-bearing **facts and invariants** the project's prose currently
   asserts — read `README`, `docs/**`, `CLAUDE.md`, `.claude/rules/`, `AGENTS.md`, `CHANGELOG`,
   the roadmap, and other descriptive `*.md`. Code and tests are out of scope.
3. Distill them into a concise plain-language **digest** — a list of claims/invariants, each tagged
   with its source doc. Not a verbatim retelling; the load-bearing assertions only. Print the digest
   into the chat.
4. Ask an open question: "Does this match your current understanding, or is anything off? Write what
   doesn't match." The user replies in free text with the mismatches.
5. Apply **minimal** fixes to the affected docs (per the keep-files-lean rule), or remove the
   obsolete with confirmation. Report what changed.

## Stage 4 — Offer to run /chart-it (new)

Final `AskUserQuestion`: **{Run /chart-it now / Not now}**. On "yes", hand off to `chart-it` (it owns
the North Star write and can run standalone). Caveat surfaced to the user: plugins installed in
Stage 1 only activate next session, but chart-it does not hard-require them, so running now is safe.

## Files touched

- `plugins/cc-tools/commands/cc-init.md` — append Stages 2–4; move confirmations to `AskUserQuestion`.
- `plugins/cc-tools/rules/keep-files-lean.md` — **new** shipped rule (distributed by Stage 2).
- `plugins/cc-tools/README.md` — refresh the cc-init description (now a 4-stage wizard).
- `cc-init.md` frontmatter `description` — update to describe the wizard.

## Out of scope

- Authoring more than the one seed rule (the set grows later).
- Auditing the project's code/tests (Stage 3 is prose-only).
- A global (`~/.claude/rules/`) install target (locked to project `.claude/rules/`).
- Any change to Stage 1's install mechanics beyond the confirmation UI.
