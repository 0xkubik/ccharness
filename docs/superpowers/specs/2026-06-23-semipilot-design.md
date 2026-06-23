# Design: semipilot — the bounded, goal-seeking loop

**Date:** 2026-06-23
**Status:** Draft for review
**Plugin:** `cc-agent` (layer 2 — self-driving agents, alongside autopilot)

## Bottom line

A new self-driving mode, **`/semipilot`**, that takes **one roadmap milestone** as its
goal and drives the cc-tools funnel (point-it → grill-it → implement-it) **until that
milestone is done — then stops on its own** and reports.

It is the mirror image of `autopilot`:

| | **autopilot** (exists) | **semipilot** (new) |
| --- | --- | --- |
| Horizon | the whole roadmap, toward the North Star | **one milestone** |
| Stopping | never on its own (only `/autopilot-cancel`) | **stops itself** when the goal is met, or gives up |
| Discipline | "never declare done" | "**check done first**, stop cleanly when met" |
| Exhaustion | cheap idle cycle forever | a **give-up** exit (bounded) |

The defining new piece is the one thing autopilot was engineered to prevent:
**detecting "goal achieved" and ending the loop cleanly.** Everything else reuses
autopilot's plumbing (the funnel, the state-file pattern, the Stop-hook pattern, the
skip-and-log blocked queue).

This was settled with the user up front (the genuine forks):

1. **Goal source = a roadmap milestone** (reuses each milestone's observable `done when:`).
2. **Give-up exit = N cycles with no progress → stop**, plus a hard cycle cap as a
   token-burn backstop.
3. **Architecture = a separate skill + command** (`/semipilot`, not a flag on autopilot),
   because the prose discipline is the opposite of autopilot's.
4. No double-confirm of "done" (a single soft model judgment is enough; the cap backstops it).
5. A dedicated `/semipilot-cancel` (not a generalized brake).

---

## 1. What it reuses vs. what is new

**Reused (verified in the repo, 2026-06-23):**

- **The funnel** — `cc-tools:point-it`, `cc-tools:grill-it`, `cc-tools:implement-it`,
  `cc-tools:slap`, called by qualified name (same as autopilot does).
- **The milestone `done when:` judgment** — point-it Phase 1 already compares the live
  survey against the current milestone's `done when:` and, under a loop, auto-marks it
  `[x]`. This is a **soft model judgment** over an *observable* outcome (chart-it requires
  `done when:` to be observable), not a hard test. semipilot reuses exactly this judgment —
  but promotes it to the **first action of every cycle** and the primary exit.
- **The Stop-hook pattern** — `autopilot-stop.sh` re-feeds while `state.active == true`,
  and its Exit #2 (`state.active == false`) already releases the stop. So semipilot needs
  **no new hook mechanism**: the model flips `active:false` on either exit and the
  hook lets the turn end.
- **The skip-and-log discipline** — funnel handbacks become a line in a `blocked.jsonl`
  review queue, never a wait.
- **The atomic state-write pattern** — temp file + `mv`, session-scoped via
  `$CLAUDE_CODE_SESSION_ID`.

**New:**

1. **Done-first cycle order** — judge the goal met *before* doing funnel work each cycle.
2. **A give-up exit** — a single "no-progress streak" counter; autopilot deliberately has
   no such exit.
3. **Milestone-scoped direction picking** — point-it's menu is filtered to directions that
   advance *this* milestone (off-milestone moves don't count), so the loop is bounded to
   the goal, not the whole product.
4. **A clean terminal report** — achieved / gave-up / capped, with the blocked queue.

---

## 2. Command surface

```
/semipilot                 drive the CURRENT milestone (first unchecked [ ]) to done, then stop
/semipilot M3              drive a specific milestone; if it is not the current one, warn
                           (the roadmap is sequential) and proceed only on the current unless
                           the user re-confirms
/semipilot M3 --give-up-after 3 --max-cycles 20    override the two thresholds

/semipilot-cancel          the manual brake (mirrors /autopilot-cancel)
```

- The goal is **always a milestone**, so its `done when:` is the success condition.
- No argument → the current milestone. This is the natural default (the roadmap is
  sequential; you complete the current one before the next).

---

## 3. Arming (only when invoked by `/semipilot`)

1. **Roadmap gate (stricter than autopilot's North Star gate).** semipilot targets a
   milestone, so it needs a **roadmap**, which needs a **North Star**. Look for
   `.claude/ccharness/roadmap.md`.
   - No North Star → route to `/chart-it` (set the star, then chart the route), stop.
   - North Star but no roadmap → route to `/chart-it` to chart the route, stop.
   - Roadmap present → resolve the **target milestone**: the `--`/positional id if given,
     else the current (first unchecked `[ ]`). Copy its `done when:` text into state.
2. **Write state atomically** (temp + `mv`) under `.claude/ccharness/semipilot/state.json`
   for the current session (id from `$CLAUDE_CODE_SESSION_ID`):
   ```json
   {
     "active": true,
     "session_id": "<this>",
     "mode": "semipilot",
     "target_milestone": "M3",
     "done_when": "<observable condition copied from roadmap.md>",
     "cycle": 0,
     "no_progress_streak": 0,
     "max_no_progress": 3,
     "max_cycles": 20,
     "started_at": "<UTC now>",
     "last_surveyed_sha": "",
     "outcome": null
   }
   ```
   Touch `blocked.jsonl` and `log.jsonl` if missing.
3. **Announce the target.** State which milestone it is driving and its `done when:`, so the
   destination is visible, that only `/semipilot-cancel` stops it early, and then run cycle 1.

When the Stop hook **re-feeds** instead (normal in-loop path), skip arming and run the next cycle.

---

## 4. One cycle (run exactly one per turn)

The order is the inversion of autopilot: **the done-check leads.**

```
1. READ   semipilot/state.json + semipilot/blocked.jsonl
2. DONE?  Survey "now" (point-it Phase 1) and judge it against state.done_when.
          MET → set active:false, outcome:"achieved", mark the milestone [x] in roadmap.md,
                 append a final log line, ANNOUNCE the win, END THE TURN. (hook releases)
3. GIVE-UP?  no_progress_streak >= max_no_progress  OR  cycle >= max_cycles
          → set active:false, outcome:"gave-up" | "capped", append a final log line,
            REPORT what is in blocked.jsonl, END THE TURN. (hook releases)
4. POINT  cc-tools:point-it — menu as DATA ("I pick — do NOT call AskUserQuestion").
          Keep ONLY directions whose `advances` == target milestone AND not in blocked.jsonl.
          → auto-pick the top such direction.
          NONE qualify → this is a no-progress cycle: no_progress_streak++, go to step 8.
5. DECIDE cc-tools:grill-it on that direction → one decision (auto-flows to build)
6. BUILD  cc-tools:implement-it → build → verify → commit LOCALLY (do NOT push)
          - handback (unbuildable/forked, or slap fired twice) → append to blocked.jsonl,
            count this as a no-progress cycle.
7. PROGRESS?  committed work that moves target's `done when:` closer → no_progress_streak = 0
              otherwise (blocked / idle / committed-but-no-movement)  → no_progress_streak++
8. LOG    append one line to log.jsonl:
          {cycle, target, picked, outcome: committed|blocked|idle, moved_goal: true|false,
           streak, sha?, ts}
          bump `cycle` in state.json via ATOMIC write (temp + mv)
9. END THE TURN. The Stop hook re-feeds for the next cycle.
```

**Why point-it is milestone-scoped here (step 4).** Under autopilot the roadmap only
*biases* the menu; off-roadmap moves still get taken. semipilot is bounded to ONE goal, so
it **filters** to milestone-advancing directions. A cycle that finds none is itself a
no-progress signal — this is how "all paths to the goal are blocked" feeds the same
give-up counter as "N cycles produced nothing."

---

## 5. The two exits (the heart)

**Success — goal achieved.** The model judges `done_when` met at the top of a cycle. It is a
single soft judgment (no double-confirm, per the decision) over an observable outcome,
backstopped by the cap. On success it marks the milestone `[x]` (so a later `/autopilot` or
`/semipilot` sees the route advanced), sets `active:false`, and reports.

**Give-up — one counter, two causes.** `no_progress_streak` increments on any cycle that
fails to move the goal:
- point-it surfaces no unblocked milestone-advancing direction, **or**
- the picked direction lands in `blocked.jsonl` (unbuildable/forked, or slap-twice), **or**
- a commit happened but the model judges it did not move `done_when` closer.

It resets to 0 on a cycle that genuinely advances the goal. `streak >= max_no_progress`
(default 3) → stop with `outcome:"gave-up"`. Independently, `cycle >= max_cycles`
(default 20) → stop with `outcome:"capped"` — the hard token-burn backstop the user asked
for. Both thresholds are overridable on the command line.

This is the load-bearing difference from autopilot, whose exhaustion path is "cheap idle
cycle, forever." A bounded loop **must** have this exit or it is just autopilot with extra
steps.

---

## 6. Plumbing (separate from autopilot)

A sibling state dir keeps the two modes from colliding (a session runs at most one loop,
but separate files make each mode's history and queue independent):

```
.claude/ccharness/semipilot/
  state.json     loop control (section 3)
  blocked.jsonl  skipped directions for review (its own, not shared with autopilot)
  log.jsonl      one line per cycle
```

**Hook — `semipilot-stop.sh`.** A focused near-clone of `autopilot-stop.sh`:
same `set -u`, same fail-closed posture, same three allow-the-stop exits (no state file /
`active == false` / a different session owns it), but it reads
`.claude/ccharness/semipilot/state.json` and re-feeds the **semipilot** prompt
(*"check done first → check give-up → run exactly one milestone-scoped cycle → flip
active:false on either exit"*). Two small, obviously-correct hooks beat one branching hook.

**Registration.** Add a second entry to the existing `Stop` array in
`plugins/cc-agent/hooks/hooks.json` pointing at `semipilot-stop.sh`. Stop hooks **stack**
(verified in the cc-maestro design notes): each reads stdin and emits its own decision; at
most one mode is active per session, so only one ever blocks — the other sees inactive
state and exits 0.

**Cancel — `/semipilot-cancel`.** Mirrors `/autopilot-cancel` exactly, against the
semipilot state: if `semipilot/state.json` is absent → "No semipilot is running."; else read
the `cycle` count, `rm` the state file (so the next Stop ends the turn and a fresh
`/semipilot` can re-arm cleanly), leave `blocked.jsonl` / `log.jsonl` as the durable record,
and report cycles run + the blocked queue (each entry's `direction` + `reason`).

---

## 7. Files to add / change

**New:**
- `plugins/cc-agent/commands/semipilot.md` — the arm command (`$ARGUMENTS` = optional
  milestone id + threshold flags).
- `plugins/cc-agent/commands/semipilot-cancel.md` — the brake.
- `plugins/cc-agent/skills/semipilot/SKILL.md` — the bounded-loop discipline (done-first,
  milestone-scoped pick, two exits, skip-and-log).
- `plugins/cc-agent/hooks/semipilot-stop.sh` — the re-feed hook.

**Changed:**
- `plugins/cc-agent/hooks/hooks.json` — add the second `Stop` hook entry.
- `plugins/cc-agent/.claude-plugin/plugin.json` — mention semipilot in the description.
- `plugins/cc-agent/README.md` — document the second mode and its state dir.

**Not touched:** the autopilot skill/command/hook (semipilot is additive), the cc-tools
funnel skills, the installer (a new command/skill/hook inside an existing plugin is
auto-discovered; only `hooks.json` needs the manual entry).

---

## 8. cc-maestro awareness (forward-compat note, not built here)

cc-maestro (still a stub per the harness design) tags an agent as `autopilot` by detecting
its armed state file. When maestro is built, it should treat a `semipilot` state file as a
**bounded** agent whose "done" is a real terminal state (`outcome != null`), unlike
autopilot's never-done. This is a note for the maestro design, **out of scope** for this
build. No work here depends on maestro existing.

---

## 9. Explicitly NOT building (YAGNI)

- No change to autopilot — it stays the never-stop, whole-roadmap driver.
- No new Stop *mechanism* — the existing `active:false` release path suffices.
- No free-text goals (the user chose milestone-sourced goals).
- No double-confirm of "done" — one soft judgment + the cap is enough.
- No generalized brake — a dedicated `/semipilot-cancel`.
- No per-model cost accounting — the cycle cap is the spend backstop.

---

## 10. Risks & verify-first

- **Soft done-judgment false-positive (early stop).** Mitigated by: `done when:` is required
  observable; the check runs each cycle against a fresh survey; cost of a false "done" is
  just an early stop the user can re-run. Accepted (no double-confirm by decision).
- **Soft done-judgment false-negative (never declares done).** Backstopped by `max_cycles`.
- **"Moved the goal closer?" is also a soft judgment** feeding the streak. Backstopped by the
  cap; tune `max_no_progress` against real runs.
- **Two Stop hooks both firing.** Safe as long as at most one mode is armed per session;
  the inactive hook exits 0. Verify after wiring: arm semipilot, confirm the autopilot hook
  stays dormant and vice-versa.
- **Cross-plugin skill calls.** semipilot calls `cc-tools:*` exactly as autopilot does —
  same resolution path, already working.

---

## 11. Build sequence

- **Phase 1 — skill + state.** Write `semipilot/SKILL.md` (done-first cycle, two exits,
  milestone-scoped pick) and the `/semipilot` arm command with the roadmap gate and state write.
- **Phase 2 — hook + cancel.** Clone `autopilot-stop.sh` → `semipilot-stop.sh`, register it
  in `hooks.json`, write `/semipilot-cancel`.
- **Phase 3 — wire-up docs.** Update `plugin.json` + `README.md`.
- **Phase 4 — verify end-to-end.** On a repo with a roadmap: arm `/semipilot` on a small
  milestone, watch it run cycles, force the success exit (milestone met → stops, marks `[x]`),
  force the give-up exit (point at an unreachable milestone → stops after `max_no_progress`),
  and confirm `/semipilot-cancel` ends a live loop and reports the queue.

---

## 12. Testing approach

- **The two exits (the new logic).** The give-up counter and the done-check are prose
  discipline executed by the model, so the test is behavioral: a fixture roadmap with (a) an
  already-met milestone → first cycle stops `achieved`; (b) a milestone whose only directions
  are pre-seeded in `blocked.jsonl` → stops `gave-up` after `max_no_progress`; (c) a tiny
  reachable milestone → runs a few cycles then stops `achieved` and marks `[x]`.
- **Hook coexistence.** Arm each mode in turn; assert the other mode's hook does not block.
- **Cancel.** Arm `/semipilot`, run a cycle, `/semipilot-cancel`, assert the next Stop ends
  the turn and the report lists cycles + blocked entries.
