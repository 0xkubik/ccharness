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

## Control (Phase 3)

```bash
ccmaestro stop <id>              # SIGTERM the agent's group; an autopilot is cancelled gracefully
ccmaestro steer <id> "do X now"  # stop, then resume the session with a new instruction
ccmaestro pause <id> / resume <id>
ccmaestro check --notify         # detect stalled/looping/died/crashed; POST changes to report_endpoint
```

Set `report_endpoint` in `~/.ccmaestro/config.json` to a webhook URL so an external
agent (hermes) is notified — either by `check --notify` (poll) or by the bundled
Stop/Notification hook (push). `max_concurrent` (default 0 = unlimited) caps how many
agents `start` will launch. A finished one-shot now shows `done` (clean) or `crashed`
(non-zero exit) instead of `died`.

## Spend the weekly limit

```bash
ccmaestro spend-weekly "optional focus" --repo ~/app --yolo   # run ~a week, relaunching across resets
ccmaestro spend-weekly --horizon-days 3                       # shorter horizon
```

`--spend-session` (a cc-agent flag) makes one autopilot run flat-out until the **5-hour**
subscription window cuts the session. `spend-weekly` is the cc-maestro half: it relaunches
`/autopilot --spend-session` each time that session dies, spanning the 5-hour resets until a
**7-day** wall-clock horizon — so the whole *weekly* limit gets spent.

It can't read the remaining budget or the reset time (those reach a status-line script only, never
headless `claude -p`), so it never tries to *detect* the limit. It classifies each death from two
signals it **can** see: if `autopilot/state.json` is gone/inactive the user ran `/autopilot-cancel`
→ **STOP** (the brake); a session that ran a while then died is a presumed limit → wait, relaunch;
one that dies fast is a crash → exponential backoff, give up after a few. Knobs (`spend_*`) live in
`~/.ccmaestro/config.json`.

Unattended autopilot commits locally, so it needs `--yolo` (or a broadened allowlist) to run the
git commands. **Durability caveat:** the supervisor is a foreground process — background it
(`nohup … &`) yourself; a week-long run won't survive a reboot or machine sleep on its own yet.

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

Observe + launch (Phase 2) and control + reporting (Phase 3) are implemented. The only
remaining optional item is a `--remote-control` live mid-turn steer spike (not yet
scheduled). See `docs/superpowers/specs/2026-06-23-cc-maestro-design.md`.
