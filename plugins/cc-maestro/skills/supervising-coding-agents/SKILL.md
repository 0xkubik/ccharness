---
name: supervising-coding-agents
description: Use when you must watch, launch, stop, steer, or report on the Claude Code coding agents (the "fleet") running on this machine — e.g. you are an orchestrator/overseer agent, you need each agent's token burn or last activity, you suspect one is stuck/looping/stopped, or you must launch or redirect agents on someone's behalf.
---

# Supervising coding agents with ccmaestro

## Overview

`ccmaestro` is the console for the fleet of Claude Code coding agents on this machine. One tool: **see them, launch them, stop/redirect them, and report on them** — usable from a terminal by a human and programmatically by another agent (e.g. hermes). It wraps the native `claude agents` registry + each session's transcript and adds the judgments the native status lacks (stuck / looping / dead).

**Do not reinvent this** with `ps`, `claude agents --json` raw, or transcript grepping — `ccmaestro` already does it.

The CLI is `ccmaestro` (binary at `plugins/cc-maestro/bin/ccmaestro`; symlink it onto PATH, or inside a Claude Code session use `"${CLAUDE_PLUGIN_ROOT}/bin/ccmaestro"`). Every command takes `--json` where it makes sense — **always use `--json` when you are an agent parsing the output.**

## The loop: observe → diagnose → act → report

1. **Observe** — `ccmaestro ls --json` lists every agent.
2. **Diagnose** — read each row's `verdict`.
3. **Act** — `stop` / `steer` / `pause` the ones that need it; `start` new work.
4. **Report** — `ccmaestro check --notify` pushes state changes to your endpoint.

## Quick reference

| Command | What it does |
|---|---|
| `ccmaestro ls [--json]` | All agents: tokens, last activity, verdict, cwd, name |
| `ccmaestro start "<task>" [--repo P] [--model M] [--budget USD] [--name N] [--yolo]` | Launch a managed agent; prints its `id` |
| `ccmaestro logs <id> [--tail N]` | Print an agent's recent transcript lines |
| `ccmaestro stop <id>` | Stop an agent (an autopilot is cancelled gracefully, not killed) |
| `ccmaestro steer <id> "<message>"` | Stop it, then resume the session with a new instruction |
| `ccmaestro pause <id>` / `resume <id>` | Freeze / unfreeze (SIGSTOP / SIGCONT) |
| `ccmaestro check [--notify] [--json]` | Detect state changes; record to events.jsonl; POST to the webhook with `--notify` |

`<id>` is the short 8-char id shown in `ls` (a sessionId prefix also works).

## Verdicts (the `verdict` field)

- `ok` — healthy.
- `stalled` — no new activity past the threshold (autopilots use a longer one). Maybe stuck — check `logs`.
- `looping` — same tool call repeated; almost always needs a `steer` or `stop`.
- `over-budget` — tokens over the configured cap.
- `died` — a launched agent vanished from the registry with no clean exit (also what an agent **you stopped** shows — that's expected, the process is genuinely gone).
- `done` / `crashed` — a launched one-shot finished cleanly (exit 0) / with a non-zero exit.

The `reason` field explains each non-ok verdict. `ls` sorts problems first.

## Reporting to an external agent (e.g. hermes)

Set the webhook once in `~/.ccmaestro/config.json`:

```json
{ "report_endpoint": "https://hermes.example/agent-events", "max_concurrent": 8 }
```

Then hermes hears about agents either way:
- **Pull:** call `ccmaestro check --notify` on a schedule (cron / loop). It POSTs each new problem event.
- **Push:** the bundled Stop/Notification hook POSTs as agents finish or need attention (active once the plugin is installed).

Other tunables in that file: `stall_min`, `tool_stall_min`, `autopilot_stall_min`, `loop_n`, `token_budget` (0 = off), `max_concurrent` (0 = unlimited).

## Safety

- **Permission posture on launch:** default is `acceptEdits` + a safe command allowlist — enough to work unattended without hanging on a prompt. `--yolo` removes ALL permission checks (`bypassPermissions`): a loaded gun for an unattended agent — use only deliberately.
- **`max_concurrent`** caps how many agents `start` will launch; `start` refuses past it.

## Common mistakes

- **Launching with raw `claude` instead of `ccmaestro start`** — raw runs still appear in `ls`, but you lose the launch metadata and clean control. Launch through `ccmaestro`.
- **Parsing the human table** — use `--json`; the table is for humans.
- **`steer` on an autopilot** — refused on purpose. Redirect an autopilot through its own funnel / `/autopilot-cancel`, not `steer`.
- **Treating `died` after your own `stop` as an error** — it isn't; the agent is gone as intended.
- **Expecting `check` to push without setup** — it only POSTs with `--notify` AND a `report_endpoint` configured.
