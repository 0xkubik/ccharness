# ccharness `/autopilot` — design

**Date:** 2026-06-23
**Status:** approved (brainstorming) → ready for implementation plan
**Plugin:** ccharness (v0.6.0 → adds a 6th command)

## Problem

The ccharness funnel is four separate skills run by hand:

```
point-it  ──►  grill-it  ──►  implement-it   (+ slap when a fix is stuck)
DIVERGE        DECIDE         BUILD
```

The user wants to fuse the funnel into **one command** — `/autopilot` — that runs the
funnel in a **continuous loop**: pick a direction, decide how, build it, commit, re-survey,
repeat. It must run **forever until manually stopped**, and be **programmatically incapable
of stopping on its own initiative**. The only stop is the user's hand.

## The core tension

The funnel is deliberately built with **three human-handback points**:

1. **point-it** ends at a ranked menu and waits — *"the human picks; you never decide"* is a
  core invariant.
2. **implement-it (Stage 0)** refuses to build a task that is too ambiguous or carries an
  unresolved fork — it hands back.

(grill-it already auto-flows into implement-it, so it is not a handback.)

"Loop forever, never self-stop" collides with all three. **Resolution (decided):
*skip & log, then advance*.** At each handback the autopilot does **not** stop:

- point-it's pick → **auto-pick** the top-ranked direction.
- an unbuildable/forked task → **log to a blocked queue** and advance to the next direction.

The loop never halts; weak or unresolvable tasks are skipped (and recorded for review), not
forced and not allowed to stop the loop.

## Why a Stop-hook, not a Workflow or an in-skill loop

The discriminating requirement is *"programmatically incapable of self-stop."*


| Mechanism                            | Can the model self-stop?                                                                                                                                                                                                                                                            | Verdict                         |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| **Stop hook re-feed**                | **No** — the hook intercepts every stop and re-feeds the prompt; the model literally cannot exit.                                                                                                                                                                                   | **Chosen.**                     |
| `while-true` inside the skill        | Yes — the model can decide "done" and stop.                                                                                                                                                                                                                                         | Rejected.                       |
| ScheduleWakeup / cron self-re-invoke | Yes — model can skip scheduling the next tick. Polling, wrong shape.                                                                                                                                                                                                                | Rejected.                       |
| **Workflow** (`while(true)` script)  | **Yes, structurally** — hard **1000-agent lifetime cap** + budget-exhaustion throw mean it self-terminates after ~50 cycles. Also runs **headless in the background**, so the user loses live watch + redirect (which the funnel's "human rules by interrupting" model depends on). | Rejected as the **outer** loop. |


"Never stop" *means* "block the exit," and a Stop hook is the direct mechanism for that — not a
workaround. Because this loop has **no completion promise and no max-iterations** (it is
never-stop by design), the hook is far simpler than ralph-loop's (~15 lines vs ~200 — no
transcript parsing, no promise detection, no iteration math).

**Workflow is not discarded — it moves one layer in.** implement-it (Stage 2) already lists a
Workflow as a tool for a large structured fan-out *within* a build. So: the **outer forever-loop
is the hook**; a **Workflow is an inner per-cycle tool** the funnel reaches for when a step earns
it. They are not competitors at the same layer.

## Architecture — three parts + one stop

### 1. Stop hook — the hard muscle

`plugins/ccharness/hooks/autopilot-stop.sh`, wired via `plugins/ccharness/hooks/hooks.json`
on the `**Stop`** event only.

- `Stop` fires on **main-agent** stop. The funnel's subagent fan-outs (point-it's 4 lenses,
grill-it's 4 poles/grilling) raise `**SubagentStop`**, a *different* event — so the hook does
**not** fire mid-funnel.
- Reads `.claude/ccharness/autopilot/state.json`.
- **Allows the stop (`exit 0`) in exactly three cases — the only legitimate exits:**
  1. state file absent,
  2. state explicitly cancelled (`active: false` / file removed),
  3. the hook's `session_id` ≠ the state's `session_id` (a different session must not be blocked).
- **Fail CLOSED everywhere else.** While autopilot is active for this session, **any anomaly
re-feeds anyway** (corrupt field, missing transcript, jq error). This is the deliberate
inversion of ralph's stop-hook, which `exit 0`s on ~8 anomaly branches — every one of those is
a silent self-stop, the exact failure we must prevent.
  - *Corrupted-state tradeoff:* if the file exists but cannot be parsed for `session_id`, the
  hook still re-feeds (fails closed). Mitigated by atomic writes (temp + `mv`); the user can
  always clear it with `/autopilot-cancel`.
- On re-feed, emits `{"decision":"block","reason":"<re-feed prompt>"}`.

**The re-feed prompt is load-bearing and self-healing.** It does not merely say "run the
funnel." It says, in effect:

> Autopilot is active (cycle N). Read `.claude/ccharness/autopilot/state.json` and
> `blocked.jsonl`. If the **last cycle ended by handing back** (slap×2, an unbuildable/forked
> task, or awaiting a pick), **log that task to `blocked.jsonl` and start a NEW cycle from
> point-it** on the next-best **unblocked** direction. Otherwise continue the funnel. Never
> stop — the human stops you via `/autopilot-cancel`.

This recovers even when a sub-skill's emphatic "ask the human" wins inside the turn: the turn
ends, the hook re-feeds this prompt, and the next turn converts the handback into skip-and-log.

### 2. `autopilot` skill — the soft brain

`plugins/ccharness/skills/autopilot/SKILL.md`. Orchestrates **one cycle** per turn:

```
read state.json + blocked.jsonl
  → point-it : survey + rank menu → AUTO-PICK top-ranked direction NOT in blocked.jsonl
  → grill-it : decide HOW (already auto-flows into implement-it)
  → implement-it : build → verify → commit LOCALLY (no push)
  → convert the 3 handbacks to skip-and-log:
       unbuildable / unresolvable fork  → append to blocked.jsonl, advance
       slap fired 2× with no progress   → append to blocked.jsonl, advance
       point-it "pick one"              → auto-picked above, never waits
  → append cycle result to log.jsonl, bump cycle counter (atomic write), end turn
  → (Stop hook re-feeds → next cycle)
```

The skill **overrides the sub-skills' handbacks in its own context** — it does **not** modify
point-it / grill-it / implement-it / slap, which stay usable standalone.

**Two guardrails:**

- **Blocked queue = point-it exclusion list.** point-it re-surveys the live repo each cycle, so
a blocked direction would keep ranking #1 forever. Auto-pick filters against `blocked.jsonl`
and takes the next unblocked entry.
- **Cheap idle.** When the menu is empty (every lane hits point-it's empty-valve) **and** `HEAD`
equals `state.last_surveyed_sha` (nothing changed since the last survey), the cycle
short-circuits — **no 4-agent fan-out** — appends an `idle` record, and ends the turn. The loop
still never stops, but an exhausted product does not become a token bonfire.

### 3. State files — continuity

Under `.claude/ccharness/autopilot/` (runtime state — must be gitignored):

- `state.json` — `{ active: bool, session_id, cycle: int, started_at, last_surveyed_sha, focus? }`.
Written atomically (temp + `mv`).
- `blocked.jsonl` — one line per skipped task: `{ cycle, direction, reason, slug, ts }`. Serves
double duty as the **review queue** and the **point-it exclusion list**.
- `log.jsonl` — one line per cycle: `{ cycle, picked, outcome: committed|blocked|idle, sha?, ts }`.

### 4. `/autopilot-cancel` — the one manual stop

`plugins/ccharness/commands/autopilot-cancel.md`. Removes (or flips `active:false` in)
`state.json`, reports the final cycle count and the size of the blocked queue. **This is the only
way the loop ever ends.** (The user can also always interrupt/redirect live with Esc — that is
the human steering, not the loop self-stopping.)

### Entry: `/autopilot`

`plugins/ccharness/commands/autopilot.md`. Arms the loop:

1. **North Star precondition.** Autopilot needs a destination, and point-it's first-run
  bootstrap is a 3-question *interview* that does not belong inside a never-stop loop. If
   `CLAUDE.md` has no North Star block (point-it's `<!-- managed by point-it` marker),
   `/autopilot` **refuses to arm** and tells the user to run `/point-it` once first.
2. Write `state.json` (`active:true`, this `session_id`, `cycle:0`).
3. Invoke the `autopilot` skill for cycle 1. The Stop hook takes over from there.

Optional argument: `/autopilot [focus]` — a theme that scopes point-it's survey each cycle
(stored as `state.focus`).

## Decided defaults

1. **North Star is a precondition** — refuse to arm without it (no interview inside the loop).
2. **Push stays manual** — each cycle commits locally only, matching implement-it Stage 6.
3. **One commit per cycle, then re-survey** — each cycle is one full funnel pass; the next cycle
  re-surveys the changed repo (self-correcting), rather than draining the whole menu first.

## Requirement traceability — "can never self-stop"

- The model cannot exit: the `Stop` hook re-feeds on every stop while `state.json` is active.
- The model cannot "decide it's done": even an intentional stop is blocked.
- A sub-skill's "ask the human" cannot leak a stop: the self-healing re-feed converts it to
skip-and-log on the next turn.
- A transient anomaly cannot kill it: the hook fails **closed**.
- No iteration cap, no budget cap, no completion promise: nothing auto-terminates it.
- The **only** stop is `/autopilot-cancel` (or the user deleting `state.json`).

## Accepted risk

With no cap and no self-stop, once the high-value moves are exhausted the loop will keep
grinding marginal directions — cheaply (idle short-circuit) but indefinitely — until
`/autopilot-cancel`. This is the explicit ask, not a defect.

## Out of scope

- Pushing / opening PRs automatically (push stays manual).
- A `/autopilot-status` reader (the user can `cat` the state files; revisit if wanted).
- Any max-cycles or budget cap (contradicts the never-stop requirement).
- Modifying the four funnel sub-skills (they stay unchanged).

## Components to build


| File                                                                                   | Role                                                             |
| -------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| `plugins/ccharness/commands/autopilot.md`                                              | arm the loop (North Star gate → write state → cycle 1)           |
| `plugins/ccharness/commands/autopilot-cancel.md`                                       | the one manual stop                                              |
| `plugins/ccharness/skills/autopilot/SKILL.md`                                          | the soft brain — orchestrate one cycle, skip-and-log, guardrails |
| `plugins/ccharness/hooks/hooks.json`                                                   | wire the `Stop` hook                                             |
| `plugins/ccharness/hooks/autopilot-stop.sh`                                            | the hard muscle — fail-closed re-feed                            |
| `.gitignore`                                                                           | ignore `.claude/ccharness/` runtime state (verify current state) |
| `plugins/ccharness/.claude-plugin/plugin.json`, `README.md`, marketplace `description` | document the 6th command                                         |


