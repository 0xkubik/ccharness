---
description: "Build or refresh the reminder cheat-sheet (.claude/ccharness/cheatsheet.md) a hook re-surfaces every few prompts — a short list of the always-loaded tooling (plugins, skills, agents, MCP) so the model doesn't drift back to its habits mid-session. Runs standalone or as a step of /cc-init."
argument-hint: "(no arguments)"
---

Invoke the `cheatsheet-management` skill with this scope:

> $ARGUMENTS

It explains what it's doing as it goes: inventories the always-loaded tooling, lets you pick the lines
worth keeping, and writes the cheat-sheet the `UserPromptSubmit` hook re-surfaces every third prompt.
