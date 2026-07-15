---
description: "Set up the project's rule files — install or refresh the harness's recommended rules into .claude/rules/, then help capture the project's own custom rules. The always-loaded guidance Claude reads every session. Human-run only; runs standalone or as a step of /cc-init."
argument-hint: "(no arguments)"
---

# rules-management — set up the project's rule files

**Explain as you go — don't just execute.** Open by telling the human, in plain language, what this
command is for and why it matters: rules are the `.claude/rules/*.md` files Claude reads at the start of
**every** session — standing guidance that keeps the agent working the way the project wants. This
command does two things: installs the harness's **recommended** rules, then helps capture **the
project's own**. As you work each step, say what you're about to do and why *before* you do it — the
human should always understand what's happening and why, not just watch files appear.

## 1 — Install the recommended rules

The harness ships a set of recommended rules inside the **cc-config plugin**. Plugin-root paths aren't
reliable here, so locate the plugin's `rules/` directory from the installed-plugins manifest, with a
cache-glob fallback — the same way the rest of the harness resolves its own files:

```
cfg="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
root="$(jq -r '.plugins["cc-config@ccharness"][0].installPath // empty' "$cfg/plugins/installed_plugins.json" 2>/dev/null)"
[ -d "$root/rules" ] || root="$(ls -d "$cfg"/plugins/cache/*/cc-config/*/ 2>/dev/null | sort -V | tail -1)"
RULES_DIR="$root/rules"
```

If `$RULES_DIR` doesn't resolve to a real directory, say cc-config couldn't be located and stop — don't
improvise a path. Otherwise explain these are general working guidance (scope discipline, lean files,
git autonomy, plain speech, logging with levels, …) — then:

- **List them:** `ls "$RULES_DIR/"*.md < /dev/null`. Read each file's first heading (`# …`) as its
  human-readable label.
- **Let the human pick** which to install — `AskUserQuestion`, `multiSelect: true`, one option per rule
  (label = its heading; the description says in one line what the rule enforces and why). The tool caps
  a question at **4 options**; with more than four rules, split across several `multiSelect` questions of
  ≤4 options each (≤4 questions per call; balance so none holds fewer than 2). Union the picks.
- **Copy each pick** to `.claude/rules/<filename>` (`mkdir -p .claude/rules` first). **Check for a
  collision first** — if `.claude/rules/<filename>` already exists, gate with `AskUserQuestion`
  (**Overwrite** / **Skip**); never overwrite silently:
  `cp "$RULES_DIR/<file>" .claude/rules/<file>`
- **Report** what was installed / skipped / overwritten. They load on the next session.

## 2 — Capture the project's own rules

The recommended set is generic; a project also has **its own** conventions worth making standing rules.
Explain this, then **offer** to capture them: ask the human, in plain prose, whether there are
project-specific rules they want on record — "how we name things", "always run X before committing",
"never touch Z by hand" — and draw them out **one at a time**. For each one they confirm:

- Phrase it as a proper rule file following **What makes a good rule** below — usually always-on
  (no frontmatter); add `paths:` only if it applies to certain files.
- Write it to `.claude/rules/<kebab-name>.md`, show it back, and confirm before the next.

If they have none, say so and stop — never invent rules they didn't ask for.

## What makes a good rule

A rule is standing context Claude reads at the start of **every** session, so it has to earn that
permanent place: short, concrete, about one thing. Hold every rule — whether you're installing a
recommended one or capturing a project's own — to this shape:

- **One rule, one file, one concern.** Each file carries a single piece of guidance. A second,
  unrelated point is a second rule, not another bullet bolted onto this one.
- **Title = an imperative plus the "why" in one clause.** The first line is `# Do X — <when or why>`
  (e.g. `# Keep files lean — when creating AND when editing`). The heading alone should say what to do
  and in what case.
- **Open with the principle and the failure it prevents — in a sentence or two.** Name the rule *and*
  the mistake it stops, then stop. The why earns adherence; a rationale essay just adds length.
- **Be concrete and checkable.** Prefer specifics you could verify in the code — "two-space indent",
  "run the tests before committing" — over vague aims like "format properly". When a rule is a broad
  principle, still ground it in what to actually do.
- **Cut every line that doesn't earn its place.** A rule is read every session, so length has a cost:
  a bloated file makes Claude *ignore* the rules inside it. For each line ask "would removing this
  cause a mistake?" — if not, drop it. Plain language, bullets over prose, a **bold imperative**
  leading each.
- **Reserve emphasis for the few hard constraints.** A well-placed "IMPORTANT" or "never" lifts
  adherence — but if every line shouts, none of it lands.
- **Make sure a rule is the right tool.** A rule is guidance Claude reads, not something it enforces.
  If the action must run the same way every time (before every commit, after each edit), that's a
  **hook**. A multi-step procedure for one kind of task is a **command**, which the human runs on
  demand. A plain rule with no frontmatter loads every session; add `paths:` frontmatter to scope it to
  matching files.
- **Keep rules honest over time.** Treat them like code: add one when you've had to correct the same
  thing twice, prune one that's being ignored (often the file simply grew too long), and reconcile
  contradictions — conflicting standing guidance makes Claude pick one arbitrarily.
