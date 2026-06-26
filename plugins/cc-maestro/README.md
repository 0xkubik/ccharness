# cc-maestro

The conductor of the cc-* harness. The `ccmaestro` CLI watches and controls many
coding agents and musicians at once.

## Use it

```bash
plugins/cc-maestro/bin/ccmaestro ls            # the dashboard: tokens, last activity, watchdog verdict
plugins/cc-maestro/bin/ccmaestro ls --json     # machine-readable (for an external agent like hermes)
plugins/cc-maestro/bin/ccmaestro start "fix the flaky test" --repo ~/app
plugins/cc-maestro/bin/ccmaestro logs <id> --tail 50
```

Symlink `bin/ccmaestro` onto your PATH to type `ccmaestro` directly. Inside a Claude
Code session, `/maestro` runs the dashboard.

## Control (Phase 3)

```bash
ccmaestro stop <id>              # SIGTERM the agent's group; a musician is cancelled gracefully
ccmaestro steer <id> "do X now"  # stop, then resume the session with a new instruction
ccmaestro pause <id> / resume <id>
ccmaestro check --notify         # detect stalled/looping/died/crashed; POST changes to report_endpoint
```

Set `report_endpoint` in `~/.ccmaestro/config.json` to a webhook URL so an external
agent (hermes) is notified — either by `check --notify` (poll) or by the bundled
Stop/Notification hook (push). `max_concurrent` (default 0 = unlimited) caps how many
agents `start` will launch. A finished one-shot now shows `done` (clean) or `crashed`
(non-zero exit) instead of `died`.

## How it works

- The agent list comes from the native `claude agents --json --all`.
- Per-agent tokens + activity come from each session's transcript under
  `~/.claude/projects/.../<sessionId>.jsonl` (resolved by sessionId).
- The **watchdog** derives verdicts the native status doesn't give: `stalled`
  (no activity past a threshold), `looping` (same tool call repeated),
  `over-budget` (tokens over a cap), `died` (a launched agent gone from the registry).
- `ccmaestro` keeps its own launch records under `~/.ccmaestro/agents/<id>/` and
  merges them with the native list by sessionId. Config: `~/.ccmaestro/config.json`.

## Usage-limits bridge (optional)

`bin/cc-usage-statusline.sh` lets the cc-agent musician see your remaining subscription
budget so it won't spend the last of your quota on an expensive build. A running session can't
query that itself — `/usage` is TUI-only and there is no CLI/file/hook/env for it. The **only**
channel that carries it is the statusLine stdin payload (`rate_limits.five_hour` /
`rate_limits.seven_day`: used % + reset time). This script sits in `statusLine.command`, tees
those numbers into the global `~/.claude/ccharness/usage.json` (honoring `$CLAUDE_CONFIG_DIR`;
one shared file, since the limits are account-wide), then forwards the payload to your real
status line — so your display is unchanged.

Install — point `statusLine.command` at it (wraps your existing status line):

```jsonc
// ~/.claude/settings.json
"statusLine": { "type": "command",
  "command": "/abs/path/to/cc-maestro/bin/cc-usage-statusline.sh" }
```

Your previous status line keeps rendering: it runs downstream from `$CC_USAGE_DOWNSTREAM`
(default `ccstatusline` if on PATH; set to `""` to render nothing). Best-effort and fail-open —
a capture failure never breaks your status line. Caveats: only interactive sessions render a
status line (headless `claude -p` does not, so the musician falls back to a token estimate there);
`rate_limits` is Pro/Max-only and absent until the session's first API response.

## Status

Observe + launch (Phase 2) and control + reporting (Phase 3) are implemented. The only
remaining optional item is a `--remote-control` live mid-turn steer spike (not yet
scheduled). See `docs/superpowers/specs/2026-06-23-cc-maestro-design.md`.
