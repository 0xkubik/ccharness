# Design: semipilot (the bounded unit) + autopilot rebuilt as a wrapper over it

**Date:** 2026-06-23
**Status:** Draft for review (revised — autopilot is now a thin wrapper over semipilot)
**Plugin:** `cc-agent` (layer 2 — self-driving agents)

## Bottom line

Two self-driving modes, where **semipilot is the base unit and autopilot is a thin
meta-loop on top of it**:

- **`/semipilot`** — drives the cc-tools funnel (point-it → grill-it → implement-it) toward
  **one roadmap milestone**, and **stops itself** when that milestone's `done when:` is met
  (or gives up after N no-progress cycles / a hard cap). The funnel cycle and the
  done-detection live here, once.
- **`/autopilot`** — no longer contains its own funnel cycle. It becomes a **wrapper**:
  it runs a semipilot on the current milestone, and **as soon as that semipilot finishes,
  it arms a fresh semipilot on the next milestone** — walking the roadmap milestone by
  milestone. The never-stop behavior becomes "keep spawning semipilots."

```
/autopilot   (meta-loop)  ── arms ──►  semipilot (milestone M1) ─ done ─┐
     ▲                                                                   │
     └──────────── arms next ◄──── semipilot (milestone M2) ◄────────────┘  …until the
                                                                             roadmap ends
```

This removes the duplication the first draft would have had: the funnel loop existed in
autopilot AND would be re-implemented in semipilot. Now it lives only in semipilot;
autopilot just decides **which milestone to run next, and what to do when one fails.**

## Decisions settled with the user

1. **Goal source = a roadmap milestone** (reuses each milestone's observable `done when:`).
2. **semipilot give-up exit = N no-progress cycles → stop**, plus a hard cycle cap (token-burn backstop).
3. **semipilot is a separate skill + command** (the prose discipline is the inverse of a never-stop loop).
4. **No double-confirm of "done"** — one soft model judgment + the cap.
5. **A dedicated `/semipilot-cancel`.**
6. **autopilot is rebuilt as a wrapper over semipilot** (not a parallel mode).
7. **When a milestone's semipilot gives up, autopilot:**
   **retries the milestone once**; if it gives up again, it **judges whether the remaining
   milestones depend on the stuck one** — **independent → park it and advance**;
   **dependent → stop the whole autopilot and exit.**
8. **autopilot now requires a roadmap** (no roadmap → route to `/chart-it`). The old
   "no roadmap → drive directly toward the North Star" path is removed.

Consequence of (7): **the new autopilot can stop on its own** (the dependent-block case).
So "only `/autopilot-cancel` stops it" is no longer absolute — there is now a legitimate
self-stop when the route is hard-blocked. The prose must say so.

---

## 1. What it reuses vs. what is new

**Reused (verified in the repo, 2026-06-23):**

- **The funnel** — `cc-tools:point-it / grill-it / implement-it / slap`, by qualified name.
- **The milestone `done when:` judgment** — point-it Phase 1 already compares the live
  survey to the current milestone's `done when:` and auto-marks it `[x]` under a loop. A
  **soft model judgment** over an *observable* outcome (chart-it requires it observable),
  not a hard test. semipilot promotes it to the first action of every cycle and its primary exit.
- **The Stop-hook re-feed pattern** — a hook re-feeds while `state.active == true` and its
  Exit #2 (`active == false`) releases the stop. Both modes flip `active:false` to end.
- **The skip-and-log discipline** — handbacks become a line in a `blocked.jsonl` queue, never a wait.
- **The atomic state-write pattern** — temp file + `mv`, session-scoped via `$CLAUDE_CODE_SESSION_ID`.

**New:**

1. **semipilot's done-first cycle + give-up exit** (a bounded loop — autopilot never had one).
2. **autopilot as a meta-loop** — it arms/re-arms semipilots instead of running the funnel itself.
3. **The two-hook partition** — semipilot's hook drives while a milestone is in flight;
   autopilot's hook only acts in the gap between milestones (re-arm / advance / park / stop).
4. **The give-up ladder** — retry-once → dependency judgment → skip-or-stop (decision 7).
5. **A milestone-dependency judgment** — a soft model read of the roadmap ("does the next
   milestone need the stuck one?").

---

## 2. semipilot — the base bounded unit

### 2.1 Command

```
/semipilot                 drive the CURRENT milestone (first unchecked [ ]) to done, then stop
/semipilot M3              drive a specific milestone; warn if it is not the current one
/semipilot M3 --give-up-after 3 --max-cycles 20    override the two thresholds
/semipilot-cancel          the manual brake
```

### 2.2 Arming

1. **Roadmap gate.** Needs `.claude/ccharness/roadmap.md`. No North Star → route to
   `/chart-it`. North Star but no roadmap → route to `/chart-it` to chart the route. Roadmap
   present → resolve the target milestone (the id given, else the current = first unchecked),
   copy its `done when:` into state.
2. **Nested-awareness.** If `.claude/ccharness/autopilot/state.json` is active for this
   session, semipilot is running **under autopilot** — it stays terse on exit (its log line
   is the handback; autopilot narrates). Standalone → it gives the full terminal report.
3. **Write `semipilot/state.json` atomically** (temp + `mv`) for this session:
   ```json
   {
     "active": true, "session_id": "<this>", "mode": "semipilot",
     "target_milestone": "M3", "done_when": "<copied from roadmap.md>",
     "cycle": 0, "no_progress_streak": 0, "max_no_progress": 3, "max_cycles": 20,
     "started_at": "<UTC now>", "last_surveyed_sha": "", "outcome": null
   }
   ```
   Touch `semipilot/blocked.jsonl` and `semipilot/log.jsonl` if missing.
4. **Announce the target** (milestone + `done when:`) and run cycle 1.

### 2.3 One cycle (done-check leads)

```
1. READ   semipilot/state.json + semipilot/blocked.jsonl
2. DONE?  Survey "now" (point-it Phase 1), judge against state.done_when.
          MET → active:false, outcome:"achieved", mark the milestone [x] in roadmap.md,
                 final log line, (terse if nested / full report if standalone), END TURN.
3. GIVE-UP?  no_progress_streak >= max_no_progress  OR  cycle >= max_cycles
          → active:false, outcome:"gave-up" | "capped", final log line, report blocked queue,
            END TURN.
4. POINT  cc-tools:point-it — menu as DATA ("I pick — do NOT call AskUserQuestion").
          Keep ONLY directions whose `advances` == target milestone AND not in blocked.jsonl.
          → auto-pick the top such direction.   NONE qualify → no-progress cycle: streak++, go to 8.
5. DECIDE cc-tools:grill-it on that direction → one decision (auto-flows to build)
6. BUILD  cc-tools:implement-it → build → verify → commit LOCALLY (no push)
          handback (unbuildable/forked, or slap-twice) → append to blocked.jsonl, no-progress cycle.
7. PROGRESS?  committed work that moves done_when closer → streak = 0
              otherwise (blocked / idle / committed-but-no-movement) → streak++
8. LOG    log.jsonl line {cycle, target, picked, outcome, moved_goal, streak, sha?, ts};
          bump cycle (atomic).
9. END TURN → the semipilot hook re-feeds for the next cycle.
```

**Why point-it is milestone-scoped here (step 4).** Under autopilot the roadmap only
*biases*; semipilot **filters** to milestone-advancing directions. A cycle that finds none is
itself a no-progress signal — that is how "all paths to the goal are blocked" feeds the same
give-up counter as "N cycles produced nothing."

### 2.4 semipilot's two exits

- **achieved** — done judged met (single soft judgment + cap backstop). Marks `[x]`, sets
  `active:false`, reports.
- **gave-up / capped** — `no_progress_streak >= max_no_progress` (default 3) or
  `cycle >= max_cycles` (default 20). Sets `active:false`, reports the blocked queue.

`outcome` is the handoff signal autopilot reads.

---

## 3. autopilot — rebuilt as the meta-loop

### 3.1 Command

```
/autopilot [focus]   arm the meta-loop: walk the roadmap milestone by milestone via semipilot
/autopilot-cancel    the manual brake (still the primary stop)
```

### 3.2 Arming

1. **Roadmap gate (now required).** No North Star → `/chart-it`. North Star but no roadmap →
   `/chart-it` to chart the route. (The old no-roadmap, direct-to-North-Star path is removed.)
2. **Write `autopilot/state.json`** (the OUTER state) for this session:
   ```json
   {
     "active": true, "session_id": "<this>", "mode": "autopilot",
     "current_milestone": "M1", "current_retries": 0, "max_retries": 1,
     "started_at": "<UTC now>", "outcome": null
   }
   ```
3. **Arm the first semipilot** on the current milestone (write `semipilot/state.json` as in
   2.2, nested). Touch `autopilot/log.jsonl` (milestone-level history) and
   `autopilot/blocked.jsonl` (the **parked-milestones** queue).
4. Announce: walking the roadmap from the current milestone; stops on `/autopilot-cancel`
   **or** a hard dependency block; then the first semipilot cycle runs.

### 3.3 The meta-cycle (runs only in the gap between milestones)

When a semipilot has gone inactive and autopilot is still active, the autopilot hook
re-feeds this meta-step (read `semipilot/state.json.outcome`):

```
outcome == achieved:
    milestone is now [x]. current_retries = 0.
    next = first unchecked milestone NOT in autopilot/blocked.jsonl (parked set)
    next exists → set current_milestone=next, arm a fresh semipilot on it, END TURN.
    none left  → roadmap exhausted → CHEAP IDLE (never stop; a new /chart-it milestone is
                  picked up on a later idle cycle). Log "roadmap-complete-idle". END TURN.

outcome == gave-up | capped:
    current_retries == 0 → THE RETRY: current_retries = 1, re-arm a fresh semipilot on the
                            SAME milestone, END TURN.
    current_retries == 1 → DEPENDENCY JUDGMENT (read the roadmap):
        does the next unchecked milestone DEPEND on the stuck one?
          INDEPENDENT → park the stuck milestone (append to autopilot/blocked.jsonl),
                         current_retries = 0, advance current to the next non-parked
                         unchecked milestone, arm a fresh semipilot, END TURN.
          DEPENDENT   → HARD STOP: set autopilot active:false, outcome:"blocked",
                         report the stuck milestone + the parked queue, END TURN. (hook releases)
```

Every meta-step appends one line to `autopilot/log.jsonl`
(`{milestone, action: advanced|retried|parked|blocked-stop|idle, ts}`) via an atomic write.

### 3.4 The dependency judgment

A **soft model judgment** over the lightweight roadmap text (each milestone is
`name + done when: + theme`): "can the next unchecked milestone be done **without** the
stuck one?" v1 judges the **immediate next** milestone (independent → advance to it,
dependent → stop). chart-it already builds roadmaps to be sequential ("does each milestone
unlock the next?"), so **dependent is the common case and stop is the common failure exit**;
the independent-skip is the exception the user asked to support. (A future refinement could
scan for the *first* independent milestone rather than only the next — out of scope for v1.)

### 3.5 autopilot's outcomes

- **Looping** (normal) — milestone done → next milestone.
- **Cheap idle** — roadmap exhausted (all milestones `[x]` or parked); never stops, waits
  for new milestones or `/autopilot-cancel`.
- **Hard stop + exit** (NEW) — a dependent milestone proved unbeatable after a retry. A
  legitimate self-stop. Reports and ends.
- **Cancelled** — `/autopilot-cancel` at any time (still the primary brake).

---

## 4. The two-hook partition (the mechanism)

Two Stop hooks, both fire on every Stop, partitioned by which state is active so **exactly
one ever blocks**:

| Situation | `semipilot-stop.sh` | `autopilot-stop.sh` | Result |
| --- | --- | --- | --- |
| semipilot active | **block** (re-feed semipilot cycle) | yield (semipilot active) | semipilot drives |
| semipilot inactive, autopilot active | yield (inactive) | **block** (re-feed meta-step) | autopilot re-arms |
| both inactive | yield | yield | session ends |

- `semipilot-stop.sh`: blocks while `semipilot/state.json` is active for this session; else exit 0.
- `autopilot-stop.sh`: blocks while `autopilot/state.json` is active for this session **AND
  `semipilot/state.json` is NOT active**; else exit 0. (The added "semipilot not active"
  guard is what makes it yield mid-milestone and act only in the gap.)

Both keep the existing fail-closed posture and the three allow-the-stop exits (no state file
/ `active == false` / a different session owns it). Stop hooks **stack** (verified in the
cc-maestro notes); since at most one blocks, there is no double-feed.

---

## 5. State & files (layered)

```
.claude/ccharness/
  semipilot/
    state.json     inner loop control (one milestone)
    blocked.jsonl  skipped DIRECTIONS within a milestone (cycle-level)
    log.jsonl      one line per cycle
  autopilot/
    state.json     outer meta-loop control (current milestone + retry counter)
    blocked.jsonl  PARKED MILESTONES (milestone-level) — repurposed
    log.jsonl      one line per meta-step (advanced / retried / parked / blocked-stop / idle)
```

Two-level logging falls out naturally: semipilot logs cycle detail; autopilot logs
milestone-level events. Parked-ness lives in `autopilot/blocked.jsonl` (not in `roadmap.md`),
so the roadmap file format is unchanged; the report surfaces parked milestones to the human.

---

## 6. Files to add / change

**New:**
- `plugins/cc-agent/commands/semipilot.md`, `semipilot-cancel.md`
- `plugins/cc-agent/skills/semipilot/SKILL.md`
- `plugins/cc-agent/hooks/semipilot-stop.sh`

**Rewritten (not merely touched):**
- `plugins/cc-agent/skills/autopilot/SKILL.md` — from "embed the funnel cycle" to "meta-loop
  over semipilot" (the give-up ladder, dependency judgment, roadmap-required, the new hard stop).
- `plugins/cc-agent/hooks/autopilot-stop.sh` — add the "yield while semipilot active" guard
  and the meta-step re-feed prompt.
- `plugins/cc-agent/commands/autopilot.md` — roadmap-required; "stops on cancel OR hard block."

**Changed:**
- `plugins/cc-agent/hooks/hooks.json` — add the second `Stop` entry for `semipilot-stop.sh`.
- `plugins/cc-agent/.claude-plugin/plugin.json`, `README.md` — document both modes.

**Not touched:** the cc-tools funnel skills; the installer (commands/skills/hooks are
auto-discovered; only `hooks.json` needs the manual entry).

---

## 7. cc-maestro awareness (forward-compat note, not built here)

When cc-maestro (a stub today) is built: a `semipilot` state file = a **bounded** agent
(terminal `outcome`); an `autopilot` state file = the meta-loop, whose "done" is a milestone
log line and which can now also reach a terminal `blocked` outcome. Out of scope here; nothing
in this build depends on maestro.

---

## 8. Explicitly NOT building (YAGNI)

- No free-text goals (milestone-sourced only).
- No double-confirm of "done."
- No new Stop *mechanism* (the `active:false` release path suffices for both modes).
- No explicit dependency metadata in `roadmap.md` (a soft judgment over existing text).
- No "find the first independent milestone" scan (v1 judges the next milestone only).
- No per-model cost accounting (cycle caps are the spend backstop).
- No no-roadmap autopilot fallback (removed by decision 8).

---

## 9. Risks & verify-first

- **Soft done-judgment** (early stop / never-done) — backstopped by observable `done when:`,
  a fresh survey each cycle, and `max_cycles`.
- **Soft dependency judgment** — could skip a truly-dependent milestone; the next semipilot
  then likely gives up too and the ladder re-applies, and the human sees the parked queue.
  Accepted for v1; tune against real runs.
- **Two-hook partition** — verify the guard: while semipilot is active the autopilot hook
  must stay dormant (no double-feed); in the gap exactly the autopilot hook re-arms. Test by
  arming `/autopilot` and watching one full milestone → advance transition.
- **The new hard stop** — verify a dependent-blocked roadmap actually ends the session (sets
  `autopilot active:false`) and is not re-fed.
- **Cross-plugin skill calls** — semipilot calls `cc-tools:*` exactly as autopilot did.

---

## 10. Build sequence

- **Phase 1 — semipilot, standalone.** SKILL (done-first cycle, two exits, nested-awareness),
  `/semipilot` + `/semipilot-cancel`, `semipilot-stop.sh`, register it in `hooks.json`. Verify
  it drives one milestone and stops both ways (achieved / gave-up).
- **Phase 2 — autopilot rebuilt as the wrapper.** Rewrite the autopilot SKILL to the meta-loop
  + give-up ladder; add the "yield while semipilot active" guard to `autopilot-stop.sh`; update
  the command. Verify the two-hook partition and the milestone→milestone walk.
- **Phase 3 — the give-up ladder end-to-end.** Verify retry-once, the dependency judgment
  (independent→advance, dependent→hard-stop), and parked-milestone reporting.
- **Phase 4 — docs.** `plugin.json` + `README.md`.

---

## 11. Testing approach

- **semipilot exits.** Fixture roadmap: (a) an already-met milestone → first cycle stops
  `achieved`; (b) a milestone whose only directions are pre-seeded in `blocked.jsonl` → stops
  `gave-up` after `max_no_progress`; (c) a tiny reachable milestone → a few cycles then
  `achieved` + `[x]`.
- **autopilot walk.** Two reachable milestones → semipilot completes M1, autopilot arms M2,
  completes it, then roadmap-complete idle.
- **Give-up ladder.** A milestone that always gives up: assert one retry, then — with an
  independent next milestone, advance + park; with a dependent next milestone, hard-stop +
  exit. Assert the parked queue and the stop report.
- **Hook coexistence.** Arm each mode; assert the partition (semipilot active → autopilot hook
  yields; gap → autopilot hook re-arms; both inactive → session ends).
- **Cancel.** `/semipilot-cancel` and `/autopilot-cancel` each end their loop and report.
