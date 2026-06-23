# cc-agent

The self-driving agent layer of the cc-* harness. `/autopilot` runs the cc-tools
funnel (point-it -> grill-it -> implement-it) in a continuous loop, committing one
improvement per cycle. It never stops on its own — a Stop hook re-feeds the loop;
only `/autopilot-cancel` halts it.

- Depends on **cc-tools** (it invokes `cc-tools:point-it`, `cc-tools:grill-it`,
  `cc-tools:implement-it`).
- Runtime state lives under `.claude/ccharness/autopilot/` (path kept stable across
  the rename): `state.json` (loop control), `log.jsonl` (cycle history),
  `blocked.jsonl` (review queue + point-it exclusion list).
- Supervised by **cc-maestro**, which treats an autopilot as a special agent:
  "done" = a new `log.jsonl` cycle; "stop" = cancel, not a raw kill.
