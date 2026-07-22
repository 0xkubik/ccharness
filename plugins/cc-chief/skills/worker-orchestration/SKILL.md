---
name: worker-orchestration
description: "Use when the chief dispatches workers — spawn a worker subagent per task, run several on one repo (each self-isolates in its own worktree), require a plain-human report from each, and sequence who depends on whom provider-first."
argument-hint: "(reference — the rules for orchestrating workers)"
user-invocable: false
---

# worker-orchestration — how the chief runs the workers

The chief builds nothing; the **worker** is your only instrument. You carry every piece of work by
spawning a worker and handing it the task, then sequence them so the product advances. These are the
rules for that.

## Rules & concepts — non-negotiable
- **Spawn and hand off.** Every piece of work is a **worker** subagent (Agent tool, `subagent_type:
  "worker"`, `--auto`). Hand it the task, its sub-project path, and the cross-repo context it can't see
  itself — then let it decompose and build.
- **Several per repo is fine.** You may run more than one worker on the same sub-project at once — each
  **isolates itself in its own worktree**, so parallel workers never collide.
- **Demand a human report.** Require each worker to report back **in plain human language**: what it did, 
  what problems it hit, and what forks it resolved. You steer by that report, never by reading its code.
- **Sequence the dependencies.** Work out who depends on whom and build it into the plan. Independent
  pieces run in parallel; a dependent one waits — **provider first**: the provider worker commits the
  interface (that committed code IS the contract) before the consumer builds against it.
- **Collect and advance.** A finished provider unblocks its consumers; keep dispatching until the
  frontier moves or all that's left is blocked, then report up.
