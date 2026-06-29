---
description: "Set up the project's rule files — install or refresh the harness's recommended rules into .claude/rules/, then help capture the project's own custom rules. The always-loaded guidance Claude reads every session. Runs standalone or as a step of /cc-init."
argument-hint: "(no arguments)"
---

Invoke the `rules-management` skill with this scope:

> $ARGUMENTS

It explains what it's doing as it goes: installs the harness's recommended rules into
`.claude/rules/` (you pick which), then offers to capture the project's own conventions as rule files
too. Rules are the standing guidance Claude reads at the start of every session.
