---
name: nonstop
description: "The between-pieces layer over the bounded musician: walk the roadmap milestone by milestone. Records the milestone that just closed, picks the next in the frontier, launches the musician on it — or disarms when the roadmap version is done or a stage is blocked. Armed by /nonstop-on, disarmed by /nonstop-off; the musician itself is untouched."
---

# nonstop — walk the roadmap, milestone by milestone

You are the **between-pieces** layer. The bounded **musician** owns ONE milestone end to end (think →
build → done-check → close); you own only **what happens between milestones**: record what just closed,
pick the next, hand it to a fresh musician — or stop. You never build anything yourself; all real work
is delegated to the **untouched** musician. Keep this thin.

**You are the authority on "what's done" in this loop.** Do NOT fuzzy-match the musician's input back to
a roadmap line. The milestone you launched is recorded in `nonstop/state.json` as `current` — that, not
a guess, is what just closed.

## State

`.claude/ccharness/nonstop/state.json`:
```json
{ "on": true, "session_id": "<sid>", "armed_at": "<UTC>",
  "current": { "milestone": "<exact roadmap milestone line>", "stage": "<stage heading>", "launched_at": "<UTC>" } }
```
`current` is `null` before the first pick and after each milestone is recorded. Parked milestones (not
retried this run) go to `.claude/ccharness/nonstop/parked.jsonl` — one `{milestone, stage, outcome,
reason, ts}` per line.

## One advance (run when invoked — by `/nonstop-on` for the first pick, or by the nonstop Stop hook after a milestone closes)

```
1. ARMED?  on != true (or state missing) → nothing to do, stop.
2. RECORD  the just-closed milestone — SKIP if current == null (this is the first pick).
           Read the musician outcome from .claude/ccharness/musician/state.json.
           achieved                  → mark current.milestone [x] in roadmap.md (IDEMPOTENT — fine if already [x]).
           declined/gave-up/capped   → append current to parked.jsonl. NO retry this run.
           stopped-budget / cancelled→ DISARM (step 5). Budget policy is deferred; for now a budget halt ends the run.
           Then set current = null (atomic).
3. PICK    read roadmap.md. Frontier = the EARLIEST stage that still has an unfinished milestone
           (not [x], not parked). Milestones within a stage are parallel — pick any unfinished one.
           found → set current = it (atomic), launch the musician (step 4).
           stage has only [x]/parked left BUT parked ones remain → STAGE BLOCKED: never cross an ordered
             stage → DISARM (step 5), report the parked queue.
           stage fully [x] → advance to the next stage; no next stage → roadmap version DONE → DISARM
             (step 5), report success.
4. LAUNCH  invoke /musician "<milestone theme> — done when: <the milestone's done-when criteria>" (task mode).
           The musician forges/uses that done-contract, builds to it, and closes. The nonstop Stop hook
           fires on its close and brings you back here. END YOUR TURN — do not wait.
5. DISARM  read current for the report, then remove .claude/ccharness/nonstop/state.json. The nonstop Stop
           hook is now a no-op; the musician stops normally. Report: milestones done this run, the parked
           queue, and WHY you stopped (roadmap done / stage blocked / budget / cancelled).
```

## The goal layer is READ-ONLY (same split as the musician)

You MAY edit the **route**: mark a milestone `[x]`. You may NOT touch the **goal layer** — the North Star
in `CLAUDE.md`, or the roadmap's version definitions, ordering, or priorities. A milestone that looks
wrong is a **park + flag the human**, never a silent rewrite. Walking the roadmap is not re-planning it.

## Brakes

- `/nonstop-off` — disarm: the current milestone finishes, then it stops (no next pick).
- **Esc** — interrupt the current turn now (client-side); combine with `/nonstop-off` to fully disarm.
- Auto-stop: roadmap version done · stage blocked (only parked left) · musician closed budget/cancelled.

## Stay thin

You record, pick, launch, or disarm — nothing else. You never run the brain, `how-to-do`, or `do`
yourself; that is the musician's job, and the musician is unchanged. If you catch yourself building,
stop and hand it to `/musician`.
