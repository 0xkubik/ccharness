# cc-tools

> **Layer:** cc-tools is the **helpers layer** of the cc-* harness — philosophy-agnostic tools usable
> in any project, plus the harness's setup wizard and its recommended rules. The product funnel lives
> in **cc-funnel** (which depends on this); **cc-agent** (the musician) and **cc-maestro** (the fleet
> orchestrator) sit above.

Three things, all plain Markdown + JSON (instructions for Claude Code — no app code, no build):

- **`/crux`** and **`/slap`** — two reasoning side doors that work in any project, with or without the funnel.
- **`/cc-init`** — the harness's onboarding wizard.
- **`rules/`** — a set of recommended project rules `/cc-init` installs into `.claude/rules/`.

## Install
```
/plugin marketplace add /Users/kubik/nox/misc/claude-code-harness
/plugin install cc-tools@cc-harness
/cc-init
```
`/cc-init` is a 5-stage setup wizard (each stage skippable): it installs missing dependencies, installs
the recommended rules into this project's `.claude/rules/`, builds the reminder cheat-sheet a hook
re-surfaces every few prompts, reconciles your docs against reality, and offers to run `/roadmap-management`.
Idempotent — re-run any time (e.g. on a new machine).

The product funnel (`/roadmap-management` → `/what-to-do` → `/how-to-do` → `/do` → `/refactor-review-test`)
lives in the **cc-funnel** plugin — install it too if you want the funnel.

## The commands

| Command | What it does | When you reach for it |
|---|---|---|
| **`/crux <pain>`** | The **diagnosis loop.** Unwinds a pain, doubt, or blockage that isn't yet a goal/direction/fork — pins the real problem from your words + the repo, runs a four-lens critical-thinking panel (Jung's Sensation / Intuition / Thinking / Feeling, each committing to a falsifiable check), and converges on ONE diagnosis + angle of attack, not implementation. Autonomous, free-standing (no North Star needed); the deliberate, deeper cousin of `/slap`. | "Something's off — make sense of it." |
| **`/slap`** | The **reset.** When a fix has gone three rounds deep in a rabbit hole, forces a step back: restate the problem, list what was tried, question assumptions, research alternatives, propose a fresh angle. The funnel's `/do` and `/refactor-review-test` invoke it at three strikes. | "Stop digging — rethink this." |
| **`/cc-init`** | **Setup wizard (5 stages).** Driven by your choices, each stage skippable: (1) install missing dependencies from the official marketplace (user scope); (2) install the recommended rules into this project's `.claude/rules/`; (3) build the reminder cheat-sheet a `UserPromptSubmit` hook re-surfaces every third prompt so the project's tools and rules don't fade from attention; (4) reconcile the project's prose docs against your current understanding so stale text doesn't mislead later decisions; (5) offer to run `/roadmap-management`. Idempotent. | "Set this up on a new machine." |

## The rules

`rules/` holds the harness's recommended project rules — standing guidance `/cc-init` offers to install
into a project's `.claude/rules/` (each pickable separately). They cover how to work in a project:
staying in scope, keeping files and the file tree lean, managing git history, avoiding gratuitous
comments, speaking plainly, weighing by importance, and grounding work in a goal before building.

## Layout
- `commands/crux.md` · `skills/crux/SKILL.md` — the diagnosis loop (pin the pain → four-lens Jungian panel → one diagnosis + angle). Free-standing side door; the deliberate cousin of slap.
- `skills/slap/SKILL.md` — the reset protocol, invoked by the funnel's `/do` at three strikes (and by you via `/slap`).
- `commands/cc-init.md` — setup wizard (deps → rules → reminder cheat-sheet → doc reconciliation → /roadmap-management; self-contained, no skill).
- `hooks/hooks.json` · `hooks/cheatsheet-hook.sh` — the `UserPromptSubmit` reminder: re-surfaces the cheat-sheet `/cc-init` builds (`.claude/ccharness/cheatsheet.md`, wrapped in `<cheatsheet>`…`</cheatsheet>`) every third prompt; a no-op until that file exists.
- `rules/*.md` — the recommended project rules `/cc-init` installs.
