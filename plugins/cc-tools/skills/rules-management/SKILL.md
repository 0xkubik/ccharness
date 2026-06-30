---
name: rules-management
description: Set up the project's rule files — install or refresh the cc-* harness's recommended rules into .claude/rules/, then help capture the project's own custom rules. Use to establish or update the always-loaded guidance Claude reads every session. Runs standalone or as a step of /cc-init.
---

# rules-management — set up the project's rule files

**Explain as you go — don't just execute.** Open by telling the human, in plain language, what this
skill is for and why it matters: rules are the `.claude/rules/*.md` files Claude reads at the start of
**every** session — standing guidance that keeps the agent working the way the project wants. This skill
does two things: installs the harness's **recommended** rules, then helps capture **the project's own**.
As you work each step, say what you're about to do and why *before* you do it — the human should always
understand what's happening and why, not just watch files appear.

## 1 — Install the recommended rules

The harness ships a set of recommended rules inside the **cc-tools plugin**. Plugin-root paths aren't
reliable in skill context, so locate the plugin's `rules/` directory from the installed-plugins
manifest, with a cache-glob fallback — the same way the rest of the harness resolves its own files:

```
cfg="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
root="$(jq -r '.plugins["cc-tools@ccharness"][0].installPath // empty' "$cfg/plugins/installed_plugins.json" 2>/dev/null)"
[ -d "$root/rules" ] || root="$(ls -d "$cfg"/plugins/cache/*/cc-tools/*/ 2>/dev/null | sort -V | tail -1)"
RULES_DIR="$root/rules"
```

If `$RULES_DIR` doesn't resolve to a real directory, say cc-tools couldn't be located and stop — don't
improvise a path. Otherwise explain these are general working guidance (scope discipline, lean files,
git autonomy, plain speech, grounding work in a goal, …) — then:

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
- **Open with the principle and the failure it prevents.** The first paragraph states the rule *and*
  names the mistake it stops — the why, not just the what. A rule with no why gets ignored or
  misapplied.
- **Be concrete and checkable where you can.** Prefer specifics you could verify — "run the tests
  before committing", "two-space indent" — over vague aims like "write good code". When a rule is a
  broad principle, still ground it in what to actually do.
- **Plain language, kept short.** Bullets over prose; lead each point with a **bold imperative**, then
  the detail. Long rules get followed less, not more.
- **Make sure a rule is the right tool.** A rule is always-on context — it can't *force* anything. If
  the guidance must run at a fixed moment (before every commit, after each edit), that's a **hook**,
  not a rule. If it's a multi-step procedure for one kind of task, that's a **skill**, which loads on
  demand. A plain rule with no frontmatter loads every session; add `paths:` frontmatter only to scope
  it to matching files.
- **Don't contradict an existing rule.** Conflicting standing guidance produces arbitrary behaviour —
  reconcile the two or replace the old one; don't stack a contradiction.
