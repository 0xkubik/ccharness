---
name: supervising-coding-agents
description: Use when you must watch, launch, stop, steer, or report on the Claude Code coding agents (the "fleet") running on this machine — e.g. you are an orchestrator/overseer agent, you need each agent's token burn or last activity, you suspect one is stuck/looping/stopped, or you must launch or redirect agents on someone's behalf.
---

# Supervising coding agents with ccconductorctl

## Overview

`ccconductorctl` is the console for the fleet of Claude Code coding agents on this machine. One tool: **see them, launch them, stop/redirect them, and report on them** — usable from a terminal by a human and programmatically by another agent (e.g. hermes). It wraps the native `claude agents` registry + each session's transcript and adds the judgments the native status lacks (stuck / looping / dead).

**Do not reinvent this** with `ps`, `claude agents --json` raw, or transcript grepping — `ccconductorctl` already does it.

The CLI is `ccconductorctl` (binary at `plugins/cc-conductor/bin/ccconductorctl`; symlink it onto PATH, or inside a Claude Code session use `"${CLAUDE_PLUGIN_ROOT}/bin/ccconductorctl"`). Every command takes `--json` where it makes sense — **always use `--json` when you are an agent parsing the output.**

## The loop: observe → diagnose → act → report

1. **Observe** — `ccconductorctl ls --json` lists every agent.
2. **Diagnose** — read each row's `verdict`.
3. **Act** — `stop` / `steer` / `pause` the ones that need it; `start` new work.
4. **Report** — `ccconductorctl check --notify` pushes state changes to your endpoint.

## Quick reference

| Command | What it does |
|---|---|
| `ccconductorctl ls [--json]` | All agents: tokens, last activity, verdict, cwd, name (musician rows carry status / task progress / current task / latest action) |
| `ccconductorctl musician [<id>] [--json]` | Running musicians in detail: status, what was asked, task progress (`done/total`), the current task, and a tail of the live action feed (what it's doing now). Omit `<id>` to list all |
| `ccconductorctl start "<task>" [--repo P] [--model M] [--budget USD] [--name N] [--yolo]` | Launch a managed agent; prints its `id` |
| `ccconductorctl logs <id> [--tail N]` | Print an agent's recent transcript lines |
| `ccconductorctl stop <id>` | Stop an agent (a musician is cancelled gracefully, not killed) |
| `ccconductorctl steer <id> "<message>"` | Stop it, then resume the session with a new instruction |
| `ccconductorctl pause <id>` / `resume <id>` | Freeze / unfreeze (SIGSTOP / SIGCONT) |
| `ccconductorctl check [--notify] [--json]` | Detect state changes; record to events.jsonl; POST to the webhook with `--notify` |

`<id>` is the short 8-char id shown in `ls` (a sessionId prefix also works).

## Verdicts (the `verdict` field)

- `ok` — healthy.
- `stalled` — no new activity past the threshold (a musician uses a longer one). Maybe stuck — check `logs`.
- `looping` — same tool call repeated; almost always needs a `steer` or `stop`.
- `over-budget` — tokens over the configured cap.
- `died` — a launched agent vanished from the registry with no clean exit (also what an agent **you stopped** shows — that's expected, the process is genuinely gone).
- `done` / `crashed` — a launched one-shot finished cleanly (exit 0) / with a non-zero exit.

The `reason` field explains each non-ok verdict. `ls` sorts problems first.

## Reporting to an external agent (e.g. hermes)

Set the webhook once in `~/.ccconductor/config.json`:

```json
{ "report_endpoint": "https://hermes.example/agent-events", "max_concurrent": 8 }
```

Then hermes hears about agents either way:
- **Pull:** call `ccconductorctl check --notify` on a schedule (cron / loop). It POSTs each new problem event.
- **Push:** the bundled Stop/Notification hook POSTs as agents finish or need attention (active once the plugin is installed).

Other tunables in that file: `stall_min`, `tool_stall_min`, `musician_stall_min`, `loop_n`, `token_budget` (0 = off), `max_concurrent` (0 = unlimited).

## Safety

- **Permission posture on launch:** default is `acceptEdits` + a safe command allowlist — enough to work unattended without hanging on a prompt. `--yolo` removes ALL permission checks (`bypassPermissions`): a loaded gun for an unattended agent — use only deliberately.
- **`max_concurrent`** caps how many agents `start` will launch; `start` refuses past it.

## Common mistakes

- **Launching with raw `claude` instead of `ccconductorctl start`** — raw runs still appear in `ls`, but you lose the launch metadata and clean control. Launch through `ccconductorctl`.
- **Parsing the human table** — use `--json`; the table is for humans.
- **`steer` on a musician** — refused on purpose. Redirect a musician through its own script / `/musician-cancel`, not `steer`.
- **Treating `died` after your own `stop` as an error** — it isn't; the agent is gone as intended.
- **Expecting `check` to push without setup** — it only POSTs with `--notify` AND a `report_endpoint` configured.
