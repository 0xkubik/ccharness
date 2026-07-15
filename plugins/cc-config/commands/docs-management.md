---
description: "Scan the project's natural-language prose — README, docs/**, specs, plans, CLAUDE.md, rules, AGENTS, CHANGELOG, roadmap — and surface what looks stale or no longer true so you can decide and fix it. Prose only; code and tests are out of scope. Runs standalone or as a step of /cc-init."
argument-hint: "(no arguments)"
---

Invoke the `docs-management` skill with this scope:

> $ARGUMENTS

It explains what it's doing as it goes: reads the project's descriptive prose, distills the claims it
makes, and calls out the ones that look outdated for you to confirm — then fixes the confirmed ones
with minimal edits. Code and tests are out of scope.
