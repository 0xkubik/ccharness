---
description: "Scan the project's natural-language prose — README, docs/**, specs, plans, CLAUDE.md, rules, AGENTS, CHANGELOG, roadmap — and surface what looks stale or no longer true so you can decide and fix it. Prose only; code and tests are out of scope. Human-run only; runs standalone or as a step of /cc-init."
argument-hint: "(no arguments)"
---

# docs-management — find the prose that's gone stale

**Explain as you go — don't just execute.** Open by telling the human what this does and why: prose
drifts out of date as a project changes, and stale docs quietly steer later decisions wrong. This
command reads the project's **descriptive prose** and surfaces what looks **no longer true**, so the
human can judge each one — then fixes the confirmed ones. It reads only prose — **code and tests are out
of scope.** Narrate what you're reading and what you suspect as you go, so it's clear what's being
checked and why a thing looks stale.

1. **Detect whether there's anything to check.** It qualifies if there's at least one commit
   (`git rev-list --count HEAD 2>/dev/null`), source files beyond `.claude/` config, or descriptive
   docs. If none of these hold → say "fresh project, nothing described yet — nothing to check" and stop.
2. **Read the descriptive prose only** — `README*`, `docs/**` (including `docs/superpowers/specs/` and
   any plans), `CLAUDE.md`, `.claude/rules/*.md`, `AGENTS.md`, `CHANGELOG*`,
   `docs/ccharness/roadmap.md`, and other top-level descriptive `*.md`.
   **Code and tests are out of scope.**
3. **Distill the load-bearing claims** the prose asserts into a concise, plain-language **digest** — a
   bulleted list of claims, each tagged with its source doc. Not a verbatim retelling; the load-bearing
   assertions only.
4. **Surface the suspected-stale ones.** Check each claim against what the repo actually *is* now (its
   structure, recent commits, your current understanding) and **call out the ones that look outdated or
   contradicted** — naming the doc, what it claims, and why it looks stale. This is the whole point:
   help the human *find* what's no longer true. Then ask, in plain prose (not `AskUserQuestion`):
   "Here's what looks stale — which of these are actually wrong, and is anything else off?" Wait for
   their free-text reply.
5. **Fix the confirmed ones.** For each, apply a **minimal** edit — the smallest diff that makes it true
   again (follow the `keep-files-lean` rule) — or remove the obsolete with confirmation. Report what
   changed.
