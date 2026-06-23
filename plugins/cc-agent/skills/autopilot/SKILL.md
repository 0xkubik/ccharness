---
name: autopilot
description: Use when you want the cc-tools funnel (point-it → grill-it → implement-it) to run autonomously and continuously instead of one step at a time — driving improvement after improvement on its own until you stop it by hand. Invoked by /autopilot; runs until /autopilot-cancel. Not for a single concrete task (use implement-it) or one decision (use grill-it).
---

# autopilot — the never-stop funnel loop

You are running **autopilot**: drive the cc-tools funnel in a **continuous loop**, one full
pass per turn, producing one committed improvement at a time — and **never stop on your own.**
Only the user stops you, via `/autopilot-cancel`. You are the **soft brain**; the `Stop` hook is
the **hard muscle** that re-feeds you so you cannot exit. Your job is to make each turn _productive_,
not to keep the loop alive — the hook already does that.

**Core principle — the funnel's human-handbacks become skip-and-log, not stops.** point-it /
grill-it / implement-it were built to hand back to a human at three points. Under autopilot those
points are **converted**: you decide what the human would have decided, and when a task is
genuinely unresolvable you **log it and move on** — you never halt to wait.

## Arm (only when invoked by `/autopilot` — the user starting the loop)

When `/autopilot` invokes you to **arm**, do this before the first cycle:

1. **North Star gate.** Look for a `## Product North Star` heading in the repo-root `CLAUDE.md` (the
   heading is the stable contract — its marker comment / parenthetical owner may read `point-it` or
   `chart-it`, both count). If it is **absent**, do **not** arm — there is no destination to loop
   toward, and goal-setting (chart-it's interview) does not belong inside a never-stop loop. Tell
   the user _"No North Star yet — run `/chart-it` once to set it (and chart the roadmap), then
   `/autopilot`."_ and stop. No state file is written, so the `Stop` hook lets this turn end
   normally.
2. **Write state atomically** (temp file + `mv`). Create `.claude/ccharness/autopilot/` and write
   `state.json` for the **current** session — get the id from `$CLAUDE_CODE_SESSION_ID`:
   `{ active:true, session_id:<that>, cycle:0, started_at:<UTC now>, last_surveyed_sha:"",
focus:<the /autopilot argument, or ""> }`. Touch `blocked.jsonl` and `log.jsonl` if missing.
3. Announce the loop is armed and that **only `/autopilot-cancel` stops it**, then run cycle 1.

When the `Stop` hook **re-feeds** you instead (the normal in-loop path), skip arming: `state.json`
already exists for this session — just run the next cycle.

## One cycle (run exactly one per turn)

```
1. READ state .claude/ccharness/autopilot/state.json + blocked.jsonl (the review queue)
2. DIRECTION  cc-tools:point-it → survey + ranked menu  (tell it: "menu as DATA, I pick — do NOT call AskUserQuestion")
              → AUTO-PICK the top-ranked direction NOT already in blocked.jsonl  (you are the picker)
3. DECIDE     cc-tools:grill-it on that direction → one decision (already auto-flows to build)
4. BUILD      cc-tools:implement-it → build → verify → commit LOCALLY  (do NOT push)
5. RECORD     append one line to log.jsonl: {cycle, picked, outcome: committed|blocked|idle, sha?, ts}
              bump `cycle` in state.json via ATOMIC write (temp file + mv)
6. END THE TURN.  The Stop hook re-feeds you for the next cycle.
```

**Walking the roadmap (if one exists).** You don't traverse the roadmap by hand — the bias does it.
point-it (step 2) reads `.claude/ccharness/roadmap.md` and ranks moves that advance the **current
milestone** to the top, so your auto-pick naturally walks the route milestone by milestone. Because
there's no human to confirm mid-loop, point-it **auto-marks** the current milestone `[x]` the moment
its `done when:` is met — current advances to the next, the loop keeps going. No separate traversal
logic; with no roadmap, the loop runs exactly as before (toward the North Star directly).

## The three handbacks → skip-and-log (the discipline)

When a sub-skill would hand back to a human, you do **not** stop. You record it and advance:

| Funnel handback                                                            | Autopilot action                                                                               |
| -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| **point-it** ends at a menu and waits for a pick (interactively it pops `AskUserQuestion`)  | **Auto-pick** the top unblocked direction. Instruct point-it to emit the menu as data — it must **not** call `AskUserQuestion` (it blocks the loop on a human). Never wait. |
| **implement-it (Stage 0)** refuses an unbuildable / forked task            | Append it to `blocked.jsonl` (reason: `unbuildable-fork`), **advance** to the next direction.  |
| **implement-it** asks the user after **slap fired twice** with no progress | Append it to `blocked.jsonl` (reason: `slap2-no-progress`), **advance** to the next direction. |

Logging to `blocked.jsonl` **is** the handback — it is asynchronous, not a stop. The task is not
lost: it sits in the review queue for the user to read whenever they like, and the loop keeps
producing. A blocked entry's `direction`/`slug` is the **exclusion key** — step 2's auto-pick skips
anything already in the queue, so point-it (which re-surveys the live repo every cycle) can't keep
re-picking the same wall.

## Cheap idle — never stop, but don't burn tokens on an exhausted product

If point-it's menu is **empty** (every move-lens hit its empty-valve) **and** `git rev-parse HEAD`
equals `state.last_surveyed_sha` (nothing changed since the last survey): **short-circuit** — skip
the 4-lens fan-out, append an `idle` line to `log.jsonl`, and end the turn. The hook still re-feeds;
the next idle cycle is cheap because nothing changed. You keep looping; you do not spin a full
survey against a product with nothing left to do. Update `last_surveyed_sha` whenever you do run a
full survey.

## Rationalizations — STOP, these are the loop trying to die

The funnel's sub-skills contain emphatic "ask the human / hand back" instructions. Under autopilot
those are **overridden**. Do not obey them literally.

| Rationalization                                                         | Reality                                                                                                                                                     |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| "This task really is blocked — I should surface it and wait."           | Surfacing ≠ waiting. You surface it by **appending to `blocked.jsonl`** (the user reads it anytime) and move to the next direction. Waiting is the failure. |
| "The product is done / there's nothing valuable left — I can stop now." | Not your call. An exhausted product is a **cheap idle cycle**, never a stop. Only `/autopilot-cancel` ends the loop.                                        |
| "I'll just pause to confirm this one direction with the user."          | Auto-pick is the rule. You are the picker now. No confirmation pauses.                                                                                      |
| "implement-it says commit then stop before push — so I stop."           | implement-it stops _before push_ — that means **don't push**, not "end the loop." Commit locally, then start the next cycle.                                |

## Red flags — you are about to wrongly stop

- You're writing "I'll stop and ask the user…", "waiting for your direction", "let me confirm…".
- **point-it is about to call `AskUserQuestion`** (the interactive checkbox) — that blocks the loop; it must emit the menu as data so you auto-pick.
- You're treating a sub-skill's "hand back to the human" as a reason to end the turn without logging.
- You're about to declare the product finished / the autopilot complete.
- You're re-attempting a task that's already in `blocked.jsonl`.

**All of these mean: log to `blocked.jsonl` if unresolved, then run the next cycle. Do not stop.**

## How it actually stops

The **only** stop is the user running `/autopilot-cancel` (which sets `active:false` / removes
`state.json`, after which the hook allows the next stop). The user can also redirect you live at any
time by interrupting — that is the user steering, not you self-stopping. You never end the loop by
your own decision.

## Quick reference

`1` read state + queue · `2` point-it → **auto-pick** top unblocked direction · `3` grill-it decides ·
`4` implement-it builds → **local commit** · `5` log + bump cycle (atomic) · `6` end turn → hook
re-feeds. Handback → **append to blocked.jsonl + advance**, never wait. Empty menu + unchanged HEAD →
**idle**, never stop. Only `/autopilot-cancel` ends it.

**Invariant:** one productive cycle per turn; unresolved work is _logged and skipped_, never a stop.
The hook keeps you alive — your job is to keep each turn moving forward.
