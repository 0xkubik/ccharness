# Musician observability + per-run isolation + crash fuse

**Purpose:** make a running musician's work visible from outside *live* (which instruments it
calls and roughly what it's doing), give each run its own folder so many runs don't collide, and
make the loop impossible to leave *accidentally* — without removing its deliberate exits.

## Why

- A musician reasons inside its own session window. From outside you can't see what it's doing or
  which instruments (`crux` / `what-to-do` / `how-to-do` / `do`) it calls.
- There is one shared `musician/state.json`. A second run in the same repo overwrites it, and the
  first run's Stop hook then sees a different owner and silently drops the work. Multiple runs in
  one repo are impossible today.
- The Stop hook re-feeds while active (fail-closed) — but only if a Stop event fires. A hard crash
  (terminal closed, kill, reboot) fires no event, so a half-done run is orphaned with nothing to
  resume it.

## Scope (three separable units, landed in order)

### Piece 1 — live observe hook (additive, safe)
- New `PreToolUse` hook (+ light `PostToolUse`) in cc-agent. Fires on every tool call,
  independent of the skill — **does not touch SKILL.md**.
- While a musician is active for this session, it appends one human-readable line per tool call to
  the run's `live.log`: timestamp, cycle, the instrument/tool, and a rough action derived from the
  tool args (Skill→which skill, Bash→command head, Edit/Write→file, Task→subagent).
- A tiny `watch` helper tails the active run's `live.log` for live viewing (`tail -f` works too).
- The model's hidden chain-of-thought is out of reach (not a tool call); spoken narration + every
  action are covered. That is enough for "see its work and which aces it calls."

### Piece 2 — per-run folders + capture the input prompt
New layout:
```
.claude/ccharness/musician/
  runs/
    <run-id>/                 run-id = YYYYMMDD-HHMMSS-<4hex>  (sortable, unique, readable)
      state.json              loop control + identity (run_id, session_id, input, …)
      log.jsonl               one line per cycle
      blocked.jsonl           handbacks this run
      live.log                live observe feed (piece 1)
  by-session/
    <session_id>              pointer → the active run-id for this session (hooks resolve O(1))
```
- Shared product/budget files stay outside `musician/` (roadmap*.md; global usage.json).
- The original prompt the musician received is written verbatim into `runs/<id>/state.json.input`
  at arm, and surfaces in the live feed / record.
- **Blast radius:** cc-maestro (`control.py`, `musician.py`, `render.py`, `watchdog.py`), the
  `musician-cancel` command, and `nonstop-stop.sh` all read the single `musician/state.json`.
  Contain it: keep a stable resolution to the active run (a `current` pointer / mirror) so those
  consumers keep working unchanged. Making cc-maestro enumerate `runs/*` is a later unit (piece 4
  flag), not this change.

### Piece 3 — ARM script + status model + crash fuse
- Extract deterministic bookkeeping into `arm.sh`: generate run-id, mkdir the run folder, write
  state atomically, write the by-session pointer, parse flags, grep the North Star. The skill stays
  the *brain*; the slash command runs `arm.sh` first. (Honest seam: the trigger is still
  model-mediated — the win is deterministic, testable bookkeeping, not model-free arm.)
- Status model: keep ≥3 states — **running / awaiting (parked on async) / closed-with-outcome** —
  plus crash-orphan detection. Do not collapse to binary; `awaiting` is the load-bearing
  anti-busy-wait state.
- Crash fuse / recovery:
  - **Soft accidental exit** (turn ended, session alive): Stop hook re-feeds immediately — already
    works.
  - **Hard crash** (no event fires): caught on the next start. A `SessionStart` hook (or the next
    `/musician` arm) scans `runs/*` for a run still `running` whose **heartbeat** (`last_seen`,
    touched by the Stop and observe hooks each turn/tool call) is stale → resume it. Per-run folders
    are what make an orphan distinguishable from a live run.
- **Budget out of the musician:** it no longer reads usage.json and the `stopped-budget` exit is
  removed — the musician doesn't know about budget. Deliberate exits remaining:
  **achieved / declined / gave-up / capped.**

## Exit semantics (the discriminator)
"Can't exit without finishing" means **can't exit *accidentally*** — a fuse against glitches/crashes
— NOT "must always achieve." The deliberate doors stay: a smart *declined* and an honest *gave-up*
are successes the brain is for. Removing them recreates the infinite-loop failure the redesign
killed.

## Invariants to pin in tests (proof the refactor didn't amputate behaviour)
- All exit doors still exist: achieved / declined / gave-up / capped.
- `awaiting` still releases the Stop hook (no busy-wait).
- A `running` orphan with a stale heartbeat is resumed on the next start.
- The observe hook logs only when a musician is active for *this* session.
- Fail-closed: jq-absent still blocks while active.

## Sequencing
Land 1 → 2 → 3 as separate commits, each with a cc-agent `plugin.json` version bump and test
updates. Piece 3 depends on piece 2's per-run folders.
