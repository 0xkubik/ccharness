# cc-tools

> **Layer:** cc-tools is the **helpers layer** of the cc-* harness — philosophy-agnostic tools usable
> in any project, plus the harness's setup wizard and its recommended rules. The product funnel lives
> in **cc-funnel** (which depends on this); **cc-agent** (the musician) and **cc-maestro** (the fleet
> orchestrator) sit above.

Plain Markdown + JSON (instructions for Claude Code — no app code, no build):

- **`/crux`** and **`/slap`** — two reasoning side doors that work in any project, with or without the funnel.
- **`/cc-init`** — the harness's onboarding **orchestrator**.
- **`/rules-management`**, **`/cheatsheet-management`**, **`/docs-management`** — the three setup skills `/cc-init` orchestrates, each also runnable on its own.
- **`rules/`** — a set of recommended project rules `/rules-management` installs into `.claude/rules/`.

## Install
```
/plugin marketplace add /Users/kubik/nox/misc/claude-code-harness
/plugin install cc-tools@cc-harness
/cc-init
```
`/cc-init` is an onboarding **orchestrator** (each step skippable): it opens by explaining the four
plugins, installs missing dependencies and the recommended external tools, then runs three skills —
`/rules-management` (recommended + project rules), `/cheatsheet-management` (the reminder cheat-sheet a
hook re-surfaces every few prompts), `/docs-management` (find stale prose) — and offers to run
`/roadmap-management`. Idempotent — re-run any time (e.g. on a new machine).

The product funnel (`/roadmap-management` → `/what-to-do` → `/how-to-do` → `/do` → `/refactor-review-test`)
lives in the **cc-funnel** plugin — install it too if you want the funnel.

## The commands

| Command | What it does | When you reach for it |
|---|---|---|
| **`/crux <pain>`** | The **diagnosis loop.** Unwinds a pain, doubt, or blockage that isn't yet a goal/direction/fork — pins the real problem from your words + the repo, runs a four-lens critical-thinking panel (Jung's Sensation / Intuition / Thinking / Feeling, each committing to a falsifiable check), and converges on ONE diagnosis + angle of attack, not implementation. Autonomous, free-standing (no North Star needed); the deliberate, deeper cousin of `/slap`. | "Something's off — make sense of it." |
| **`/slap`** | The **reset.** When a fix has gone three rounds deep in a rabbit hole, forces a step back: restate the problem, list what was tried, question assumptions, research alternatives, propose a fresh angle. The funnel's `/do` and `/refactor-review-test` invoke it at three strikes. | "Stop digging — rethink this." |
| **`/cc-init`** | **Onboarding orchestrator.** Each step skippable: an orientation on the four plugins, then Stage 0 installs missing dependencies + the recommended external tools (user scope), then it runs `/rules-management`, `/cheatsheet-management`, and `/docs-management` behind skip/stop gates, and offers `/roadmap-management`. Idempotent. | "Set this up on a new machine." |
| **`/rules-management`** | Install/refresh the harness's recommended rules into `.claude/rules/`, then help capture the project's own. | "Set up this project's rules." |
| **`/cheatsheet-management`** | Build/refresh the reminder cheat-sheet (`.claude/ccharness/cheatsheet.md`) the hook re-surfaces every third prompt. | "Refresh the tooling reminder." |
| **`/docs-management`** | Scan the project's prose (README, docs, specs, plans, …) and surface what looks stale for you to fix. | "Find docs that have gone stale." |

## The rules

`rules/` holds the harness's recommended project rules — standing guidance `/rules-management` installs
into a project's `.claude/rules/` (each pickable separately). They cover how to work in a project:
staying in scope, keeping files and the file tree lean, managing git history, avoiding gratuitous
comments, speaking plainly, weighing by importance, and grounding work in a goal before building.

## Layout
- `commands/crux.md` · `skills/crux/SKILL.md` — the diagnosis loop (pin the pain → four-lens Jungian panel → one diagnosis + angle). Free-standing side door; the deliberate cousin of slap.
- `skills/slap/SKILL.md` — the reset protocol, invoked by the funnel's `/do` at three strikes (and by you via `/slap`).
- `commands/cc-init.md` — onboarding orchestrator (orientation → Stage 0 install → rules-management → cheatsheet-management → docs-management → /roadmap-management).
- `commands/rules-management.md` · `skills/rules-management/SKILL.md` — install the recommended rules + capture the project's own.
- `commands/cheatsheet-management.md` · `skills/cheatsheet-management/SKILL.md` — build the reminder cheat-sheet.
- `commands/docs-management.md` · `skills/docs-management/SKILL.md` — find stale prose in the project's docs.
- `hooks/hooks.json` · `hooks/cheatsheet-hook.sh` — the `UserPromptSubmit` reminder: re-surfaces the cheat-sheet `cheatsheet-management` builds (`.claude/ccharness/cheatsheet.md`, wrapped in `<cheatsheet>`…`</cheatsheet>`) every third prompt; a no-op until that file exists.
- `rules/*.md` — the recommended project rules `/rules-management` installs.
