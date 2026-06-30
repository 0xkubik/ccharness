# cc-conductor

The conductor of the cc-* harness. The `ccconductorctl` CLI watches and controls many
coding agents and musicians at once.

## Use it

```bash
plugins/cc-conductor/bin/ccconductorctl ls            # the dashboard: tokens, last activity, watchdog verdict
plugins/cc-conductor/bin/ccconductorctl ls --json     # machine-readable (for an external agent like hermes)
plugins/cc-conductor/bin/ccconductorctl musician      # every running musician: status, goal, what it's doing
plugins/cc-conductor/bin/ccconductorctl musician <id> # one musician in full + its live action feed
plugins/cc-conductor/bin/ccconductorctl start "fix the flaky test" --repo ~/app
plugins/cc-conductor/bin/ccconductorctl logs <id> --tail 50
```

A **musician** row in `ls` carries its run detail — status, task progress (`done/total`), the
current task, and its latest action from the live feed. `ccconductorctl musician` is the dedicated view:
what was asked, the progress, the current task, and a tail of `live.log` (what it's doing right now).
conductor reads the per-run layout (`runs/<run-id>/` via the `by-session` pointer), so it sees every
run even when several share a repo.

Symlink `bin/ccconductorctl` onto your PATH to type `ccconductorctl` directly. Inside a Claude
Code session, `/conductor` runs the dashboard.

## Control (Phase 3)

```bash
ccconductorctl stop <id>              # SIGTERM the agent's group; a musician is cancelled gracefully
ccconductorctl steer <id> "do X now"  # stop, then resume the session with a new instruction
ccconductorctl pause <id> / resume <id>
ccconductorctl check --notify         # detect stalled/looping/died/crashed; POST changes to report_endpoint
```

Set `report_endpoint` in `~/.ccconductor/config.json` to a webhook URL so an external
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
- `ccconductorctl` keeps its own launch records under `~/.ccconductor/agents/<id>/` and
  merges them with the native list by sessionId. Config: `~/.ccconductor/config.json`.

## Usage-limits bridge (optional)

`bin/cc-usage-statusline.sh` captures your remaining **subscription** budget into a file
budget-aware control can read. Budget is a **cc-conductor-layer** concern now, not an individual
agent's — the cc-musician musician is budget-blind by design, so this is the data source for the
conductor to gate the fleet on remaining headroom. A running session can't query its own limits —
`/usage` is TUI-only and there is no CLI/file/hook/env for it. The **only** channel that carries
it is the statusLine stdin payload (`rate_limits.five_hour` / `rate_limits.seven_day`: used % +
reset time). This script sits in `statusLine.command`, tees those numbers into the global
`~/.claude/ccharness/usage.json` (honoring `$CLAUDE_CONFIG_DIR`; one shared file, since the limits
are account-wide), then forwards the payload to your real status line — so your display is unchanged.

Install — point `statusLine.command` at it (wraps your existing status line):

```jsonc
// ~/.claude/settings.json
"statusLine": { "type": "command",
  "command": "/abs/path/to/cc-conductor/bin/cc-usage-statusline.sh" }
```

Your previous status line keeps rendering: it runs downstream from `$CC_USAGE_DOWNSTREAM`
(default `ccstatusline` if on PATH; set to `""` to render nothing). Best-effort and fail-open —
a capture failure never breaks your status line. Caveats: only interactive sessions render a
status line (headless `claude -p` does not, so it writes no usage there); `rate_limits` is
Pro/Max-only and absent until the session's first API response.

## Status

Observe + launch (Phase 2) and control + reporting (Phase 3) are implemented. The only
remaining optional item is a `--remote-control` live mid-turn steer spike (not yet
scheduled). See `docs/superpowers/specs/2026-06-23-cc-conductor-design.md`.
