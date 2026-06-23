# cc-agent

The self-driving agent layer of the cc-* harness. Two modes — **semipilot** (the bounded unit)
and **autopilot** (the meta-loop wrapper over it):

## Modes

### `/semipilot` — bounded, one-milestone unit

Drives the cc-tools funnel (point-it → grill-it → implement-it) toward **one roadmap milestone**
and **stops itself** when that milestone's `done when:` is met — or gives up after N no-progress
cycles / a hard cycle cap.

- Requires a roadmap (`.claude/ccharness/roadmap.md`). No roadmap → `/chart-it` first.
- Two exits: **achieved** (done-check met → marks `[x]` in roadmap) or **gave-up / capped**
  (streak ≥ `max_no_progress` or `cycle ≥ max_cycles`).
- `/semipilot-cancel` is the manual brake.

### `/autopilot` — meta-loop over semipilot

Arms a fresh semipilot on the current milestone; when it finishes, advances to the next —
walking the roadmap milestone by milestone. The funnel logic lives entirely inside semipilot;
autopilot only decides which milestone runs next and what to do when one fails.

- **Requires a roadmap.** No roadmap (or no North Star) → `/chart-it` first. The old
  "drive directly toward the North Star without a roadmap" path is removed.
- **Give-up ladder:** if a semipilot gives up → retry once → if still stuck, judge whether
  the next milestone **depends** on the stuck one:
  - **Independent** → park the stuck milestone (add to parked queue) and advance.
  - **Dependent** → **HARD STOP**: autopilot sets itself inactive, reports, and ends the session.
- **Two ways autopilot stops:** `/autopilot-cancel` (manual brake, works any time) OR a hard
  dependency block (a legitimate self-stop — no longer only cancel can end it).
- When the roadmap is exhausted (all milestones done or parked), autopilot cheap-idles — it
  never stops on its own in the normal case; new milestones added via `/chart-it` are picked
  up on the next idle cycle.

## State directories (layered)

```
.claude/ccharness/
  semipilot/
    state.json     inner loop control — one milestone in flight
                   {active, session_id, mode, target_milestone, done_when, cycle,
                    no_progress_streak, max_no_progress, max_cycles, outcome, …}
    blocked.jsonl  skipped DIRECTIONS within the current milestone (cycle-level)
    log.jsonl      one line per semipilot cycle
  autopilot/
    state.json     outer meta-loop control — current milestone + retry counter
                   {active, session_id, mode, current_milestone, current_retries,
                    max_retries, outcome, …}
    blocked.jsonl  PARKED MILESTONES queue (milestone-level — repurposed from directions)
    log.jsonl      one line per meta-step (advanced / retried / parked / blocked-stop / idle)
```

Two-level logging: semipilot logs cycle detail; autopilot logs milestone-level events.
Parked milestones live in `autopilot/blocked.jsonl` (not in `roadmap.md`), so the roadmap
file format is unchanged.

## Hook partition

Two `Stop` hooks run on every stop event, partitioned so **exactly one ever blocks**:

| Situation | `semipilot-stop.sh` | `autopilot-stop.sh` | Result |
| --- | --- | --- | --- |
| semipilot active | blocks (re-feeds cycle) | yields | semipilot drives |
| semipilot inactive, autopilot active | yields | blocks (re-feeds meta-step) | autopilot re-arms |
| both inactive | yields | yields | session ends |

This ensures no double-feed while a milestone is in flight, and the autopilot hook only acts
in the gap between milestones.

## Dependencies & supervision

- Depends on **cc-tools** (invokes `cc-tools:point-it`, `cc-tools:grill-it`,
  `cc-tools:implement-it`, `cc-tools:slap`).
- Supervised by **cc-maestro**: a `semipilot` state file signals a bounded agent (terminal
  outcome); an `autopilot` state file signals the meta-loop (can reach `blocked` self-stop
  in addition to cancel).
