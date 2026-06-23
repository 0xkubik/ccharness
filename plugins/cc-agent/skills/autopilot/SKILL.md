---
name: autopilot
description: Use when you want the cc-tools funnel to run autonomously milestone by milestone — autopilot is a thin meta-loop over semipilot: it arms a fresh semipilot per roadmap milestone and, in the gap between milestones, advances/retries/parks/stops based on the give-up ladder. Requires a roadmap (run /chart-it first). Invoked by /autopilot; the primary brake is /autopilot-cancel, though a hard dependency block can also stop it legitimately.
---

# autopilot — the meta-loop over semipilot

You are running **autopilot**: a **thin meta-loop** that walks the roadmap milestone by milestone by
arming a fresh **semipilot** on each one. You do **not** run the cc-tools funnel yourself — that is
semipilot's job. Your job is to decide **which milestone to run next**, and **what to do when one
fails**.

```
/autopilot   (meta-loop)  ── arms ──►  semipilot (milestone M1) ─ done ─┐
     ▲                                                                   │
     └──────────── arms next ◄──── semipilot (milestone M2) ◄────────────┘  …until the
                                                                             roadmap ends or
                                                                             a hard block hits
```

The funnel cycle (point-it → grill-it → implement-it) lives **only in semipilot**. autopilot sees
only the milestone-level outcome (`achieved` / `gave-up` / `capped`) and acts on it.

## Arm (only when invoked by `/autopilot` — the user starting the loop)

When `/autopilot` invokes you to arm, do this before the first semipilot cycle:

1. **Roadmap gate (now required).** Check `.claude/ccharness/roadmap.md`.
   - No `## Product North Star` in `CLAUDE.md` → do not arm; tell the user _"No North Star yet —
     run `/chart-it` first."_ No state written; the Stop hook lets this turn end normally.
   - North Star present but no roadmap file → do not arm; tell the user _"No roadmap yet — run
     `/chart-it` to chart the route, then `/autopilot`."_ No state written.
   - Roadmap present → resolve the current milestone (first unchecked `[ ]`), continue to step 2.

   (The old no-roadmap, direct-to-North-Star path is removed. Roadmap is required.)

2. **Write `autopilot/state.json` atomically** (temp file + `mv`) for this session.
   Get the id from `$CLAUDE_CODE_SESSION_ID`:
   ```json
   {
     "active": true,
     "session_id": "<this>",
     "mode": "autopilot",
     "current_milestone": "M1",
     "current_retries": 0,
     "max_retries": 1,
     "started_at": "<UTC now>",
     "outcome": null
   }
   ```
   Touch `autopilot/log.jsonl` (milestone-level history) and `autopilot/blocked.jsonl`
   (the **parked-milestones** queue) if missing.

3. **Arm the first semipilot** on the current milestone: write `semipilot/state.json` (nested,
   as in §2.2 of the spec — semipilot will be running under autopilot so it stays terse on exit).

4. Announce: walking the roadmap from the current milestone. Stops on `/autopilot-cancel`
   **or** a hard dependency block. Then the first semipilot cycle runs.

When the Stop hook **re-feeds** you (the normal in-gap path), skip arming: `autopilot/state.json`
already exists. Read `semipilot/state.json.outcome` and run the meta-cycle below.

## The meta-cycle (runs only in the gap between milestones)

When a semipilot has gone inactive (`active:false`) and autopilot is still active, the autopilot
Stop hook re-feeds this meta-step. Read `semipilot/state.json` for the outcome:

```
outcome == achieved:
    milestone is [x]. current_retries = 0.
    next = first unchecked milestone NOT in autopilot/blocked.jsonl
    next exists → current_milestone = next, arm a fresh semipilot, END TURN.
    none left  → roadmap exhausted → CHEAP IDLE (never stop), log "roadmap-complete-idle", END TURN.

outcome == gave-up | capped:
    current_retries == 0 → set current_retries = 1, re-arm semipilot on the SAME milestone, END TURN.
    current_retries == 1 → does the next unchecked milestone DEPEND on the stuck one?
        INDEPENDENT → park it (autopilot/blocked.jsonl), current_retries = 0,
                       advance to next non-parked unchecked, arm semipilot, END TURN.
        DEPENDENT   → HARD STOP: autopilot active:false, outcome:"blocked",
                       report stuck milestone + parked queue, END TURN.
```

Every meta-step appends one line to `autopilot/log.jsonl`
(`{milestone, action: advanced|retried|parked|blocked-stop|idle, ts}`) via an atomic write.

**The give-up ladder in plain words:**

1. semipilot gives up on a milestone → **retry the milestone once** (`current_retries` goes 0→1).
2. Second give-up on the same milestone → **judge whether the next milestone depends on the stuck one**:
   - **Independent** → park the stuck milestone (log it to `autopilot/blocked.jsonl`), advance to the
     next non-parked milestone.
   - **Dependent** → **HARD STOP**: the path is blocked and continuing would be pointless.

The retry is a single re-arm of semipilot (`current_retries: 1, max_retries: 1`). No further
retries — once the ladder exhausts its one retry, it moves to dependency judgment.

## Dependency judgment (spec §3.4)

A **soft model judgment** over the lightweight roadmap text (each milestone is
`name + done when: + theme`): "can the next unchecked milestone be done **without** the stuck one?"

- v1 judges the **immediate next** unchecked milestone only.
- chart-it builds roadmaps to be sequential ("each milestone unlocks the next"), so **dependent is
  the common case** — HARD STOP is the common failure exit; the independent-skip is the exception.
- A future refinement could scan for the *first* independent milestone rather than only the next.
  Out of scope for v1.

## Cheap idle (roadmap exhausted)

When all milestones are `[x]` or parked (`autopilot/blocked.jsonl`): enter **cheap idle** — never
stop, never spin a full semipilot cycle. Log an `idle` line to `autopilot/log.jsonl` and end the
turn. The Stop hook re-feeds; the next idle cycle is cheap because there is nothing to do. A new
milestone added by `/chart-it` is picked up on a later idle cycle.

This is not "the product is done, I should stop." Cheap idle keeps the loop alive without burning
tokens. Only `/autopilot-cancel` or a HARD STOP ends it.

## Outcomes (§3.5)

| Outcome | What happens |
| --- | --- |
| **Looping** (normal) | milestone done → advance → arm next semipilot |
| **Cheap idle** | roadmap exhausted (all `[x]` or parked); never stops, waits for new milestones or cancel |
| **Hard stop + exit** (NEW) | dependent milestone proved unbeatable after a retry; autopilot sets `active:false`, outcome `"blocked"`, reports the stuck milestone and parked queue, and the hook releases |
| **Cancelled** | `/autopilot-cancel` at any time (still the primary brake) |

**The hard stop is a legitimate self-stop.** "Only `/autopilot-cancel` stops it" is no longer
absolute. The one legitimate self-stop is: a dependent milestone that semipilot gave up on twice.
Everything else (a hard task, an empty funnel menu, a cycle cap) feeds the give-up ladder or cheap
idle — not a self-stop.

## Rationalizations — STOP, the loop is trying to die

| Rationalization | Reality |
| --- | --- |
| "This milestone is blocked — I should surface it and wait." | Surfacing ≠ waiting. The give-up ladder handles it: retry once, then park or HARD STOP. Never wait mid-cycle. |
| "The roadmap is done — there's nothing left." | Roadmap exhausted → cheap idle. You do not stop. |
| "I'll just pause to confirm the dependency judgment with the user." | The judgment is soft-model: make the call, then advance or hard-stop. No confirmation pauses. |
| "semipilot ended, so I should end too." | semipilot ending is the *trigger* for the meta-cycle, not a stop signal. Read the outcome and act. |

## Red flags — you are about to wrongly stop

- You're writing "I'll stop here…" after a semipilot completes — read the outcome, run the meta-cycle.
- You're treating `gave-up` as an autopilot exit without working through the give-up ladder first.
- You're declaring "roadmap complete" as a reason to end — that's cheap idle territory.
- `current_retries` has only gone to 1 but you haven't run the dependency judgment yet.

**The only self-stops are (a) the user running `/autopilot-cancel`, or (b) the HARD STOP path
(dependent-block after retry). Everything else continues.**

## Quick reference

Arm: roadmap required (no North Star / no roadmap → `/chart-it`) · write outer `autopilot/state.json`
(`current_milestone, current_retries:0, max_retries:1, mode:"autopilot"`) · arm first semipilot ·
touch `autopilot/log.jsonl` + `autopilot/blocked.jsonl`.

Meta-cycle (in the gap): `achieved` → advance + arm next; `gave-up|capped` + `current_retries==0`
→ retry the same milestone once; + `current_retries==1` → DEPEND judgment → park+advance (INDEPENDENT)
or HARD STOP (DEPENDENT). Roadmap exhausted → CHEAP IDLE.

**Invariant:** autopilot acts only between milestones. The funnel cycle lives in semipilot; autopilot
decides which milestone comes next and what to do when one fails.
