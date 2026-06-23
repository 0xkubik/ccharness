# cc-maestro

The conductor of the cc-* harness. The `ccmaestro` CLI watches and controls many
coding agents and autopilots at once.

## Use it

```bash
plugins/cc-maestro/bin/ccmaestro ls            # the dashboard: tokens, last activity, watchdog verdict
plugins/cc-maestro/bin/ccmaestro ls --json     # machine-readable (for an external agent like hermes)
plugins/cc-maestro/bin/ccmaestro start "fix the flaky test" --repo ~/app
plugins/cc-maestro/bin/ccmaestro logs <id> --tail 50
```

Symlink `bin/ccmaestro` onto your PATH to type `ccmaestro` directly. Inside a Claude
Code session, `/maestro` runs the dashboard.

## How it works

- The agent list comes from the native `claude agents --json --all`.
- Per-agent tokens + activity come from each session's transcript under
  `~/.claude/projects/.../<sessionId>.jsonl` (resolved by sessionId).
- The **watchdog** derives verdicts the native status doesn't give: `stalled`
  (no activity past a threshold), `looping` (same tool call repeated),
  `over-budget` (tokens over a cap), `died` (a launched agent gone from the registry).
- `ccmaestro` keeps its own launch records under `~/.ccmaestro/agents/<id>/` and
  merges them with the native list by sessionId. Config: `~/.ccmaestro/config.json`.

## Status

Observe + launch (Phase 2) are built. Control (stop / steer / pause) and reporting
to an external agent are the next plan. See
`docs/superpowers/specs/2026-06-23-cc-maestro-design.md`.
