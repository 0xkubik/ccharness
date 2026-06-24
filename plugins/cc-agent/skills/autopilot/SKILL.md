---
name: autopilot
description: Use when you want the cc-tools funnel to run autonomously milestone by milestone — autopilot is a thin meta-loop over semipilot: it arms a fresh semipilot per roadmap milestone and, in the gap between milestones, advances/retries/parks/stops based on the give-up ladder. Requires a roadmap (run /find-goal first). Invoked by /autopilot; the primary brake is /autopilot-cancel, though a hard dependency block can also stop it legitimately. Optional flags — `--ultracode` (force maximum parallelism: mandatory Workflow + subagents + worktrees in every build) and `--spend-session` (never self-stop; generate work instead of idling and park instead of hard-stopping, so it runs until the subscription limit cuts the session). Weekly spend is a separate cc-maestro supervisor, not a flag here.
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

The funnel cycle (what-to-do → how-to-do → do) lives **only in semipilot**. autopilot sees
only the milestone-level outcome (`achieved` / `gave-up` / `capped`) and acts on it.

## Arm (only when invoked by `/autopilot` — the user starting the loop)

When `/autopilot` invokes you to arm, do this before the first semipilot cycle:

1. **Roadmap gate (now required).** Check `.claude/ccharness/roadmap.md`.
   - No `## Product North Star` in `CLAUDE.md` → do not arm; tell the user _"No North Star yet —
     run `/find-goal` first."_ No state written; the Stop hook lets this turn end normally.
   - North Star present but no roadmap file → do not arm; tell the user _"No roadmap yet — run
     `/find-goal` to chart the route, then `/autopilot`."_ No state written.
   - Roadmap present → resolve the current milestone = the **first unchecked `[ ]` in document order**
     (under a layered roadmap that's a milestone on the current stage's frontier), continue to step 2.

   (The old no-roadmap, direct-to-North-Star path is removed. Roadmap is required.)

2. **Parse run-mode flags from `$ARGUMENTS`** (everything that is not a flag is the focus passed
   through to each semipilot cycle):
   - `--ultracode` → `ultracode: true`. Forces maximum parallelism in every build (Workflow +
     parallel subagents + git worktrees, mandatory). See **Ultracode mode** below.
   - `--spend-session` → `spend: true`. Run flat-out until the subscription limit cuts the session;
     never self-stop for a soft reason. See **Spend mode** below. (Weekly spend is a separate
     cc-maestro supervisor that relaunches this `--spend-session` loop across session resets — there
     is no `--spend-weekly` flag here.)
   - Neither present → both default `false` (the normal bounded behaviour).

3. **Write `autopilot/state.json` atomically** (temp file + `mv`) for this session.
   Get the id from `$CLAUDE_CODE_SESSION_ID`:
   ```json
   {
     "active": true,
     "session_id": "<this>",
     "mode": "autopilot",
     "current_milestone": "M1",
     "current_retries": 0,
     "max_retries": 1,
     "ultracode": false,
     "spend": false,
     "started_at": "<UTC now>",
     "outcome": null
   }
   ```
   Set `ultracode` / `spend` to `true` per the flags parsed in step 2. Touch `autopilot/log.jsonl`
   (milestone-level history) and `autopilot/blocked.jsonl` (the **parked-milestones** queue) if missing.

4. **Arm the first semipilot** on the current milestone: write `semipilot/state.json` (nested,
   as in §2.2 of the spec — semipilot will be running under autopilot so it stays terse on exit).
   **Propagate `ultracode`**: if the autopilot run is ultracode, set `ultracode: true` on the nested
   semipilot state too, so each milestone's build fans out. (Do **not** propagate `spend` — spend is
   an autopilot-level never-stop policy; the nested semipilot keeps its normal bounded exits, and
   giving up just parks the milestone for autopilot to handle.)

5. Announce: walking the roadmap from the current milestone — note `[ultracode]` / `[spend]` if set.
   Stops on `/autopilot-cancel` **or** a hard dependency block (in spend mode, only `/autopilot-cancel`
   or the subscription limit). Then the first semipilot cycle runs.

When the Stop hook **re-feeds** you (the normal in-gap path), skip arming: `autopilot/state.json`
already exists. Read `semipilot/state.json.outcome` and run the meta-cycle below.

## The meta-cycle (runs only in the gap between milestones)

When a semipilot has gone inactive (`active:false`) and autopilot is still active, the autopilot
Stop hook re-feeds this meta-step. Read `semipilot/state.json` for the outcome:

```
Two derived terms drive the whole cycle:
- **FRONTIER STAGE** = the earliest `## Stage` that still has any unchecked `[ ]` milestone.
- **NEXT()** = the first unchecked, **non-parked** milestone of the FRONTIER STAGE (document order).
  NEXT **never crosses into a later stage while the frontier stage still holds unfinished work** — and
  a **parked** milestone counts as unfinished (it stays `[ ]`), so it keeps its stage frontier-open.
  This is what keeps autopilot's position and what-to-do's frontier on the same stage.

**ADVANCE-OR-STALL** (both outcomes below end here):
    NEXT() exists                          → current_milestone = NEXT(), arm a fresh semipilot, END TURN.
    else, a LATER stage has a workable      → those stages DEPEND on the stuck frontier stage →
      (unchecked, non-parked) milestone        HARD STOP: active:false, outcome:"blocked",
                                               report the parked blocker(s) + queue, END TURN.
    else (every milestone is [x] or parked) → roadmap exhausted → CHEAP IDLE (never stop),
                                               log "roadmap-complete-idle", END TURN.

outcome == achieved:
    milestone is [x]. current_retries = 0. → run ADVANCE-OR-STALL.

outcome == gave-up | capped:
    current_retries == 0 → set current_retries = 1, re-arm semipilot on the SAME milestone, END TURN.
    current_retries == 1 → STAGE TEST: park the stuck milestone (autopilot/blocked.jsonl),
                           current_retries = 0, → run ADVANCE-OR-STALL.
        NEXT() exists = a workable **same-stage** sibling = INDEPENDENT (same stage = parallel by
            find-goal's contract) → advance to it.
        no NEXT() but a later stage has workable milestones = DEPENDENT (the stuck one was the last
            workable in its stage; later stages need it) → HARD STOP.
```

Every meta-step appends one line to `autopilot/log.jsonl`
(`{milestone, action: advanced|retried|parked|blocked-stop|idle, ts}`) via an atomic write.

**The give-up ladder in plain words:**

1. semipilot gives up on a milestone → **retry the milestone once** (`current_retries` goes 0→1).
2. Second give-up on the same milestone → **the STAGE TEST decides whether the next milestone depends
   on the stuck one** (structural, not a guess — the roadmap's stages already encode it):
   - **Independent** (a sibling in the *same stage* is still open) → park the stuck milestone (log it
     to `autopilot/blocked.jsonl`), advance to that same-stage sibling.
   - **Dependent** (the stuck one is the last open milestone in its stage, so the only remaining work
     lives in a later stage that needs this one) → **HARD STOP**: the path is blocked and continuing
     would be pointless. *But only if a later stage actually has workable milestones* — if parking
     leaves nothing workable anywhere (all `[x]` or parked), that's exhaustion → **CHEAP IDLE**, never
     a stop.

The retry is a single re-arm of semipilot (`current_retries: 1, max_retries: 1`). No further
retries — once the ladder exhausts its one retry, it moves to dependency judgment.

## Dependency judgment — the STAGE TEST (spec §3.4)

The roadmap is **layered**: ordered `## Stage` bands, with parallel milestones inside each. That
structure *is* the dependency answer — no guessing needed. The DEPEND question "can the next
milestone be done without the stuck one?" becomes a **structural lookup**:

- **Another unchecked, non-parked milestone shares the stuck one's stage → INDEPENDENT.** Same stage
  means parallel by find-goal's contract ("order → split stages; independent → same stage"), so the
  sibling can proceed. Park the stuck one, advance to the sibling.
- **The stuck one is the last open milestone in its stage → DEPENDENT.** If the only remaining work is
  in a *later* stage (which exists precisely because it needs this one finished) → HARD STOP. If
  parking instead leaves **nothing workable anywhere** (all `[x]` or parked) → that's roadmap
  exhaustion → **CHEAP IDLE**, not a stop. (ADVANCE-OR-STALL above is the authoritative three-way.)

This replaces the old soft-model guess with a rule that reads straight off the roadmap.

- **Legacy roadmaps (no `## Stage` headings):** *frontier-tracking* is unchanged — each milestone is
  its own stage, so the frontier is always the single first-unchecked box. The **give-up ladder is
  stricter**, though: with no stage there is never a same-stage sibling, so a double-give-up that
  leaves workable milestones ahead is **always DEPENDENT → HARD STOP** (and parking the very last
  milestone is exhaustion → CHEAP IDLE, as always — never a wrongful stop). The old soft-judgment that
  could occasionally rule the *next* milestone independent and park-skip it is gone — declare an
  explicit `## Stage` with parallel milestones if you want that skip. (This is the one behaviour
  change for heading-less roadmaps.)
- If a same-stage sibling *seems* to actually need the stuck one, that's a **mis-grouped roadmap**, not
  an autopilot bug — fix it in `/find-goal` (split the stage). autopilot trusts the stage structure.

## Cheap idle (roadmap exhausted)

When all milestones are `[x]` or parked (`autopilot/blocked.jsonl`): enter **cheap idle** — never
stop, never spin a full semipilot cycle. Log an `idle` line to `autopilot/log.jsonl` and end the
turn. The Stop hook re-feeds; the next idle cycle is cheap because there is nothing to do. A new
milestone added by `/find-goal` is picked up on a later idle cycle.

This is not "the product is done, I should stop." Cheap idle keeps the loop alive without burning
tokens. Only `/autopilot-cancel` or a HARD STOP ends it.

## Ultracode mode (`--ultracode`)

A **plus**, not a switch: parallelism, subagents, Workflow, and worktrees are *always* allowed and
you should reach for them whenever they help. `--ultracode` raises that from "use when useful" to
**"use to the maximum, mandatory"** — it does not unlock anything new, it removes the discretion.

When `ultracode` is set (the Stop hook injects this each cycle), every milestone's **build step**
must fan out instead of running inline:
- **author a Workflow and/or dispatch parallel subagents** for the build — never do serially what can
  be split;
- **isolate parallel file-mutating work in git worktrees** so concurrent agents don't collide;
- **verify findings adversarially** (independent checker agents).

Insert this at the **loop/build level** — i.e. how the milestone's work is carried out — not by
fighting `do`'s gated 0→6 pipeline. The flag propagates to each nested semipilot so the
fan-out happens inside the cycle where the building actually occurs.

## Spend mode (`--spend-session`)

The goal: **keep working until the subscription limit runs out.** A running loop cannot read its own
remaining budget (the limit is server-side; nothing local exposes it), so spend mode does **not** try
to detect the limit. It simply **never self-stops for a soft reason** and keeps generating real work;
the subscription limit cutting the session is the natural — and only — terminator besides
`/autopilot-cancel`.

autopilot already never self-stops except a hard dependency-block, so spend mode changes exactly two
branches of the meta-cycle (the Stop hook injects these):
1. **Exhausted roadmap is NOT cheap idle → GENERATE work.** Re-survey with `what-to-do` for new
   improvements, extend the roadmap via `find-goal`, then keep building. Idling would burn ~zero
   tokens, which defeats the purpose.
2. **A hard dependency-block does NOT stop → park + mine.** Park the blocker (as today) and advance
   to any other workable milestone instead of hard-stopping. Under spend, the dependency block is no
   longer a legitimate self-stop.

**Honesty + churn guard (important).** Burning the full limit is *best-effort, bounded by how much
real work exists* — say so; do not pretend otherwise. To avoid a week-long run degenerating into
hundreds of junk commits:
- route every generated direction through `how-to-do`, which can **reject** weak work;
- keep every commit **LOCAL** (reviewable / revertable), as the normal loop already does;
- when work-generation is genuinely **dry** (nothing worth doing passes how-to-do), fall back to a
  **light idle** for that cycle — never lower the bar or manufacture churn just to fill time.

The only stops in spend mode are **`/autopilot-cancel`** and the **subscription limit** itself.

## Outcomes (§3.5)

| Outcome | What happens |
| --- | --- |
| **Looping** (normal) | milestone done → advance → arm next semipilot |
| **Cheap idle** | roadmap exhausted (all `[x]` or parked); never stops, waits for new milestones or cancel |
| **Hard stop + exit** (NEW) | a dependency block: either a milestone gave up twice with no same-stage sibling, **or** advancing would cross into a later stage while the frontier stage still holds a parked (unbeatable) milestone. autopilot sets `active:false`, outcome `"blocked"`, reports the blocker + parked queue, and the hook releases |
| **Cancelled** | `/autopilot-cancel` at any time (still the primary brake) |
| **Spend** (`--spend-session`) | cheap idle → work-generation; hard stop → park + mine; the only stops are `/autopilot-cancel` or the subscription limit cutting the session |

**The hard stop is a legitimate self-stop — except under spend mode.** Normally "Only
`/autopilot-cancel` stops it" is no longer absolute: the one legitimate self-stop is a **dependency
block** (a milestone that gave up twice and now gates the rest of the route). Everything else (a hard
task, an empty funnel menu, a cycle cap) feeds the give-up ladder or cheap idle — not a self-stop.
**Under `--spend-session` even the hard stop is off**: park the blocker and keep mining, so the only
terminators are `/autopilot-cancel` and the subscription limit.

## Rationalizations — STOP, the loop is trying to die

| Rationalization | Reality |
| --- | --- |
| "This milestone is blocked — I should surface it and wait." | Surfacing ≠ waiting. The give-up ladder handles it: retry once, then park or HARD STOP. Never wait mid-cycle. |
| "The roadmap is done — there's nothing left." | Roadmap exhausted → cheap idle. You do not stop. |
| "I'll just pause to confirm the dependency judgment with the user." | The judgment is the structural STAGE TEST (read it off the roadmap): make the call, then advance or hard-stop. No confirmation pauses. |
| "semipilot ended, so I should end too." | semipilot ending is the *trigger* for the meta-cycle, not a stop signal. Read the outcome and act. |

## Red flags — you are about to wrongly stop

- You're writing "I'll stop here…" after a semipilot completes — read the outcome, run the meta-cycle.
- You're treating `gave-up` as an autopilot exit without working through the give-up ladder first.
- You're declaring "roadmap complete" as a reason to end — that's cheap idle territory.
- `current_retries` has only gone to 1 but you haven't run the dependency judgment yet.

**The only self-stops are (a) the user running `/autopilot-cancel`, or (b) the HARD STOP path
(dependent-block after retry). Everything else continues.** Under **`--spend-session`** even (b) is
removed — park the blocker and keep mining; only `/autopilot-cancel` or the subscription limit stops.

## Quick reference

Arm: roadmap required (no North Star / no roadmap → `/find-goal`) · write outer `autopilot/state.json`
(`current_milestone, current_retries:0, max_retries:1, mode:"autopilot"`) · arm first semipilot ·
touch `autopilot/log.jsonl` + `autopilot/blocked.jsonl`.

Meta-cycle (in the gap), both outcomes end in **ADVANCE-OR-STALL**. `NEXT()` = first unchecked,
non-parked milestone of the **FRONTIER STAGE** (earliest `## Stage` with unchecked work; never crosses
into a later stage while the frontier stage still holds unfinished/parked work): NEXT() exists → arm
it; else a later stage has workable milestones → **HARD STOP** (dependent block); else all `[x]`/parked
→ **CHEAP IDLE**. `achieved` → ADVANCE-OR-STALL. `gave-up|capped` + `current_retries==0` → retry once;
+ `==1` → **STAGE TEST**: park the stuck one → ADVANCE-OR-STALL (same-stage sibling = INDEPENDENT;
none but later work = DEPENDENT → HARD STOP).

**Invariant:** autopilot acts only between milestones. The funnel cycle lives in semipilot; autopilot
decides which milestone comes next and what to do when one fails.
