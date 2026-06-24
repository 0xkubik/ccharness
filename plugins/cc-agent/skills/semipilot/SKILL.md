---
name: semipilot
description: Use when driving the cc-tools funnel toward ONE roadmap milestone and stopping when its `done when:` is met (or giving up after N no-progress cycles / a cycle cap). The bounded unit; autopilot wraps it. Invoked by /semipilot. Needs a roadmap — routes to /find-goal if absent. Not the never-stop autopilot; not a single task (do). Optional `--ultracode` flag forces maximum parallelism in the build (mandatory Workflow + subagents + worktrees); there is no spend flag here (spend is autopilot-only).
---

# semipilot — the bounded done-first loop

You are running **semipilot**: drive the cc-tools funnel toward **one roadmap milestone** and
**stop yourself** when its `done when:` is met — or give up cleanly after N no-progress cycles
or a hard cycle cap. You are the **inverse of autopilot**: where autopilot never stops on its own,
semipilot has a clear exit and uses it. The Stop hook re-feeds you each turn; your job is to
check done **first**, build only when not done, and exit when the signal is clear.

**Core principle — done-check leads every cycle, not build.** Under autopilot the loop lives by
building. Under semipilot the loop lives by checking: if the milestone is done, you stop. Only
when it is NOT done do you pick → decide → build. This inversion is what makes semipilot bounded.

## Arm (only when invoked by `/semipilot` — not when the hook re-feeds)

When `/semipilot` first invokes you, do this before cycle 1:

1. **Roadmap gate.** Look for `.claude/ccharness/roadmap.md`.
   - No `## Product North Star` in repo-root `CLAUDE.md` → do **not** arm. Tell the user
     _"No North Star yet — run `/find-goal` once to set it and chart the roadmap, then `/semipilot`."_
     No state file is written; the hook lets this turn end normally.
   - North Star present but no roadmap → tell the user _"No roadmap yet — run `/find-goal` to
     build one, then `/semipilot`."_ Same: no state, normal exit.
   - Roadmap present → resolve the **target milestone**: the id passed as argument (e.g. `M3`),
     or if none, the **current** = the first unchecked `[ ]` milestone **in document order** (under a
     layered roadmap that's a milestone on the current stage's frontier). Copy its `done when:` text
     into state.
2. **Nested-awareness.** Check `.claude/ccharness/autopilot/state.json`. If it exists and its
   `active == true` and its `session_id` matches `$CLAUDE_CODE_SESSION_ID`, semipilot is running
   **under autopilot**. In that mode, exit reports are terse (one log line + outcome). Standalone
   → give the full terminal report.
3. **Parse run-mode flags from `$ARGUMENTS`.** Besides the milestone id and the existing
   `--give-up-after N` / `--max-cycles N`, accept **`--ultracode`** → `ultracode: true`: forces
   maximum parallelism in the build step (Workflow + parallel subagents + git worktrees, mandatory).
   Absent → `false`. (There is **no spend flag on semipilot** — spend is an autopilot-level never-stop
   policy. When autopilot arms a nested semipilot it propagates only `ultracode`.) See **Ultracode
   mode** below.
4. **Write `semipilot/state.json` atomically** (temp file + `mv`). Create
   `.claude/ccharness/semipilot/` if missing:
   ```json
   {
     "active": true,
     "session_id": "<$CLAUDE_CODE_SESSION_ID>",
     "mode": "semipilot",
     "target_milestone": "M3",
     "done_when": "<copied verbatim from roadmap.md>",
     "cycle": 0,
     "no_progress_streak": 0,
     "max_no_progress": 3,
     "max_cycles": 20,
     "ultracode": false,
     "started_at": "<UTC now>",
     "last_surveyed_sha": "",
     "awaiting": null,
     "headroom_floor_pct": 15,
     "outcome": null
   }
   ```
   `awaiting` stays `null` in normal operation; you set it to a small object only when the
   loop suspends on a long-running async build (see **Awaiting** below). `headroom_floor_pct`
   is the remaining-budget % below which you stop launching expensive/async work (see
   **Headroom** below).
   Set `ultracode: true` if `--ultracode` was passed (or propagated from autopilot). Touch
   `semipilot/blocked.jsonl` and `semipilot/log.jsonl` if missing.
5. **Announce** the target milestone and its `done when:` (note `[ultracode]` if set), then run cycle 1.

When the Stop hook **re-feeds** you (the normal in-loop path): `state.json` already exists —
skip arming, run the next cycle directly.

## One cycle (done-check leads)

```
0. RESUMING? If state.awaiting is set and the awaited task just completed (its notification
          re-entered you), CLEAR awaiting (atomic) and continue — the build's result is now in.
1. READ   semipilot/state.json + semipilot/blocked.jsonl + semipilot/../usage.json (headroom).
          HEADROOM = min(100 - five_hour.used_%, 100 - seven_day.used_%) from a FRESH usage.json
          (<~10 min old). Below state.headroom_floor_pct → "low headroom" gate is ON this cycle
          (see Headroom): no expensive/async launches. Stale/absent → unknown: stay conservative.
2. DONE?  Survey "now" (what-to-do Phase 1), judge against state.done_when.
          MET → active:false, outcome:"achieved", mark milestone [x] in roadmap.md, final log line,
                 (terse if nested / full report if standalone), END TURN.
3. GIVE-UP?  no_progress_streak >= max_no_progress  OR  cycle >= max_cycles
          → active:false, outcome:"gave-up" | "capped", final log line, report blocked queue, END TURN.
4. POINT  cc-tools:what-to-do — menu as DATA ("I pick — do NOT call AskUserQuestion").
          Keep ONLY directions whose `advances` == target milestone AND not in blocked.jsonl.
          → auto-pick the top.   NONE qualify → no-progress cycle: streak++, go to 8.
5. DECIDE cc-tools:how-to-do on that direction → one buildable approach (decides the *how*)
6. BUILD  cc-tools:do → verify → LOCAL commit (no push)
          LOW HEADROOM (step 1 gate ON)? do NOT launch an expensive/long-async build — prefer a
            cheap step, or suspend (awaiting) until reset, or report and stop. See Headroom.
          ASYNC build (launched a long background task — scan/fuzz/external run — that can't
            finish in-turn, and no parallel in-turn work is worth running) → set awaiting:{what,
            since} (atomic), log a "suspended" line, END TURN. NOT a cycle, NOT a streak tick.
            (Hook releases on awaiting; the task's completion notification resumes you at step 0.)
          handback (unbuildable/forked, or slap-twice) → append to blocked.jsonl, no-progress cycle.
          EXTERNAL transient block (API 5xx/outage, rate-limit, network — NOT a path problem)
            → treat as a suspension like async: set awaiting (or log "blocked-external"),
            END TURN, do NOT streak++. Resume when it clears.
7. PROGRESS?  committed work that moves done_when closer → streak = 0
              otherwise → streak++
8. LOG    log.jsonl line {cycle, target, picked, outcome, moved_goal, streak, sha?, ts}; bump cycle (atomic).
9. END TURN → the semipilot hook re-feeds (unless awaiting was set in 6 — then it released).
```

## Awaiting — suspend on long async work, don't busy-wait

A `do` build can launch work that does NOT finish inside the turn: a scan, a fuzz campaign, an
external run. The cycle is "one funnel iteration per turn," but that work is asynchronous — so
**do not spin status-check cycles waiting for it.** That busy-wait is the failure mode: the Stop
hook re-feeds every turn, each re-feed is a full model turn on the subscription, and dozens of
"still running" cycles burn quota and march the cycle cap for nothing — while also keeping the
terminal blocked so `/semipilot-cancel` can't get in.

Instead, **suspend**:

1. When the build is async and there is no independent in-turn work worth doing in parallel,
   write `awaiting` to state (atomic): `{"what": "<task ids / what you launched>", "since":
   "<UTC now>"}`. Log a `"suspended"` line. **END THE TURN.**
2. The Stop hook sees `awaiting` and **releases** (it does not re-feed). The session goes idle:
   the terminal yields to the user (cancel works), and no quota is spent waiting.
3. When the awaited task completes, **its own completion notification re-enters you** (this is
   how background tasks work — they re-invoke on exit, idle or not). At step 0 of the next cycle
   you clear `awaiting` and judge the result.

Rules:
- **Only suspend when there's no parallel work.** If you can keep building toward the milestone
  in-turn while the async task runs, keep cycling — don't suspend a productive loop.
- **`awaiting` is neither a cycle nor a streak tick.** It's a suspension. Do not bump `cycle`,
  do not touch `no_progress_streak`. A launched-and-running build is progress pending, not a
  stall — counting it toward give-up would abandon real work in flight.
- **Use it only for work that will notify on completion** (a harness-tracked background task).
  For external work the harness can't observe, set a fallback wake instead of relying on a
  notification, or you will stall in `awaiting` forever.
- **A transient EXTERNAL block is a suspension, not a give-up.** An API 5xx/outage, a rate
  limit, a network failure — none of these mean "no path to the goal exists." Suspend (set
  `awaiting` or log `blocked-external`), do NOT streak++. Reserve `no_progress_streak` for a
  genuine handback or an empty qualifying-direction set. This is what keeps `gave-up` honest:
  it fires only when the WORK is blocked, never when the API is merely busy.

## Headroom — spend the budget, don't exhaust it

semipilot runs on the owner's **subscription** (5-hour + weekly limits), and a long build (a
scan, a fuzz run) burns the same quota the owner needs. A running session can't read its
remaining budget directly — the only source is the statusLine payload, surfaced by the cc-tools
usage bridge into `.claude/ccharness/usage.json` (`five_hour` / `seven_day`: `used_percentage` +
`resets_at`). At cycle start (step 1) read it and compute **headroom** = the smaller of the two
remaining percentages (`100 - used_percentage`).

Act on it:
- **Healthy** (headroom ≥ floor, default 15%): operate normally.
- **Low headroom** (below `headroom_floor_pct`): the gate is ON — do **not** launch an
  expensive or long-async build this cycle. Prefer a cheap step that still advances the
  milestone; if the only available work is expensive, **suspend** (set `awaiting` with a note
  like `"low headroom — waiting for reset"`) or report and stop — don't spend the last of the
  budget and strand the owner. The `resets_at` timestamps tell you when it refills.
- **Unknown** (usage.json absent or stale — e.g. headless `claude -p`, where no statusLine
  renders, or pre-first-response): you have no real number. Stay conservative — heed any system
  "approaching limit" warning, and don't kick off unbounded expensive async on a blind budget.

Always note the headroom (or "unknown") in the cycle log line, so the trace shows what you knew.
This is a **gate on launching cost**, never a loop exit: low headroom suspends or defers, it
does not set `gave-up`.

## Milestone-scoped, not roadmap-biased

Under autopilot, the roadmap **biases** what-to-do toward the current frontier — but it does not
filter out anything. Under semipilot, what-to-do is **filtered**: you keep ONLY directions whose
`advances` field matches the target milestone. An empty filtered set is itself a no-progress
signal — it feeds the same `no_progress_streak` counter as a failed build. This is how "all paths
to the goal are blocked" eventually reaches the give-up exit without spinning.

The **direction filter** is target-only. The **milestone done-check** (what-to-do Phase 1) is not: if a
*sibling* frontier milestone's `done when:` is observably met, marking it `[x]` is a truthful state
update and is fine — semipilot still only ever *targets*, *builds toward*, and *exits on* its own
milestone. A sibling getting checked off as a side effect just saves autopilot a later cycle.

**Do not re-pick directions already in `blocked.jsonl`** — the slug/direction is the exclusion key.
Append to `blocked.jsonl` whenever do hands back (unbuildable, forked, or slap fired
twice with no progress). The blocked queue is never a stop; it is the asynchronous handoff to the
human.

## The two exits

- **achieved** — `done_when` judged MET on a live survey (soft model judgment over an observable
  outcome). Sets `active:false`, `outcome:"achieved"`, marks the milestone `[x]` in `roadmap.md`,
  writes the final log line, then reports. No double-confirm: one survey judgment is enough; the
  `max_cycles` cap is the backstop against early false positives.
- **gave-up / capped** — `no_progress_streak >= max_no_progress` (default 3) OR `cycle >=
  max_cycles` (default 20). Sets `active:false`, `outcome:"gave-up"` or `outcome:"capped"`,
  writes the final log line, and reports the full `blocked.jsonl` queue so the human sees every
  skipped direction. The `outcome` field is the handoff signal autopilot reads when semipilot
  finishes under it.

Setting `active:false` in state is what releases the Stop hook on the two **terminal** exits.

There is also a **non-terminal** release: **suspended** (`awaiting` set, or a `blocked-external`
condition). The loop is NOT done and has NOT given up — it is parked on async work or a transient
outage. The hook releases on `awaiting` too (so the turn yields without churn), but `active` stays
`true` and `outcome` stays `null`: this is a pause, not an exit. The awaited task's completion
notification resumes the loop. See **Awaiting**.

## Rationalizations — STOP, the cycle is trying to skip the done-check

| Rationalization | Reality |
| --- | --- |
| "I just built something — skip the done-check and build more." | Done-check **leads every cycle**, before any pick. The milestone may be met after the last commit. |
| "The `done_when` is hard to judge — I'll keep building to be safe." | Soft judgment over an observable outcome is explicit. If it is unobservable, that is a find-goal problem, not a reason to loop forever. |
| "I'll ask the user whether we're done (`AskUserQuestion`)." | **Forbidden.** `AskUserQuestion` blocks the loop on a human; the Stop hook re-feeds you on a turn boundary. The done judgment is yours. `AskUserQuestion` must **not** be called at any point inside the semipilot cycle. |
| "No qualifying directions — I'll pick from the full roadmap instead." | Empty filtered set = no-progress cycle. streak++. Go to step 8. |
| "The streak is high but I feel progress is near — skip the give-up check." | The give-up thresholds exist exactly for this feeling. Trust `no_progress_streak` and `max_cycles`. |
| "My async build is still running — I'll spin a cycle each turn to check on it." | **No — suspend.** Set `awaiting` and END THE TURN; the hook releases and the task's completion notification resumes you. Busy-wait cycles burn quota, march the cap, and block `/semipilot-cancel`. |
| "The API is 529-ing / rate-limited, so I'm stuck — streak++ toward give-up." | A transient external outage is NOT a no-progress tick. Suspend (`awaiting` / `blocked-external`), do not streak++. `gave-up` is for blocked WORK, not a busy API. |

## Red flags — you are about to make the wrong call

- You're running the cycle without doing the done-check first (step 2 must come before step 4).
- **what-to-do is about to call `AskUserQuestion`** (the interactive checkbox) — forbid it; emit menu as data, auto-pick.
- You're picking a direction that is already in `blocked.jsonl`.
- You're picking a direction whose `advances` does not match the target milestone.
- You're continuing the loop after setting `active:false` (both exits END TURN immediately).
- You're writing a full report when nested under autopilot (terse only in nested mode).

## How it actually stops

Two terminal ways and only two: **achieved** (done-check met) and **gave-up / capped** (thresholds
exceeded). Both set `active:false` and END TURN immediately. The Stop hook then lets the session
end. There is no other self-stop. The user can also force a stop at any time via `/semipilot-cancel`
(removes `state.json`, same release path).

Distinct from stopping: **suspending** (`awaiting`) releases the turn WITHOUT ending the loop —
`active` stays `true`, and the awaited task's completion notification resumes it. That is the path
for long async builds and transient outages; it is not an exit.

## Ultracode mode (`--ultracode`)

A **plus**, not a switch. Parallelism, subagents, Workflow, and worktrees are *always* allowed and
you should use them whenever they help; `--ultracode` raises that to **mandatory, maximised**. When
`ultracode` is set in state (the Stop hook injects this each cycle), step 6's **build** must fan out:
author a Workflow and/or dispatch parallel subagents instead of building inline, isolate parallel
file-mutating work in **git worktrees**, and verify findings adversarially. Apply this at the
build level — don't fight `do`'s gated pipeline. The done-check, give-up, and cap exits are
unchanged; ultracode only affects *how* the build is carried out.

## Quick reference

`1` read state + blocked + usage.json (**headroom** = min remaining %; below floor → no expensive/async
launch) · `2` **DONE?** survey → if MET stop achieved · `3` **GIVE-UP?** streak/cap
→ if hit stop gave-up/capped · `4` what-to-do DATA, filter to `advances`==milestone, auto-pick top ·
`5` how-to-do → buildable approach (the *how*) · `6` do → local commit (no push) · `7` progress? streak=0 or
streak++ · `8` log + bump cycle (atomic) · `9` end turn → hook re-feeds. Handback → **append
blocked.jsonl + no-progress cycle**, never wait. Async build / external outage → **set `awaiting`,
END TURN (suspend, no cycle/streak), resume on the task's completion notification** — never busy-wait.
No done-check → wrong. `AskUserQuestion` → forbidden.

**Invariant:** done-check leads every cycle; the loop exits on its own when the milestone is met or
the give-up thresholds fire. `active:false` is the only door out.
