# cc-agent

The self-driving agent layer of the cc-* harness. One loop — the **musician**: the project's brain
for ONE piece of work. It plays the cc-tools instruments (`crux` → `what-to-do` → `how-to-do` →
`do`), thinks before it builds, forges its own definition of done, drives to that done, then
**closes**. Bounded and self-closing — there is no never-stop loop above it.

## `/musician` — the bounded performer

Hand it ONE thing to carry to a real finish — a task, a problem, or an idea.

- **With a prompt** (`/musician <task / problem / idea>`): it **thinks first**, sized to the input
  (a fuzzy pain → `crux`; an idea → North-Star fit; a clear task → straight to build). The brain may
  come back **declined** ("not worth it / wrong problem") or reframed, instead of blindly building.
  If it clears, it forges a falsifiable definition of done and builds to it.
- **Without a prompt** (`/musician`): it **finds the work itself** via `what-to-do` (auto-picking the
  top direction — no human in the loop), then builds that one direction to done.

It runs as a loop across turns (the Stop hook re-feeds one cycle per turn), but it is **bounded**:
one piece of work, to its end, then stop. Want another — launch it again.

- **Exits (the only doors out):**
  - **achieved** — the done-check is met.
  - **declined** — the brain ruled the work shouldn't happen (leave-it / wrong problem / an
    intent-changing reframe, or — in open mode — nothing worth doing). A smart "no" is a success,
    not a failure; it is distinct from `gave-up`.
  - **gave-up / capped** — *tried and couldn't*: `no_progress_streak ≥ max_no_progress` (default 3)
    or `cycle ≥ max_cycles` (default 20).
- **Open mode requires a roadmap's North Star** (it leans on `what-to-do`). None → `/find-goal` first.
- `/musician-cancel` is the manual brake.
- `--ultracode` forces maximum parallelism in the build (mandatory Workflow + parallel subagents +
  git worktrees). There is **no spend flag** — the musician is bounded by design.

## State directory

```
.claude/ccharness/
  musician/
    state.json     loop control for the one piece of work in flight
                   {active, session_id, mode:"musician", entry:"task"|"open", input,
                    done_when, cycle, no_progress_streak, max_no_progress, max_cycles,
                    ultracode, awaiting, outcome, …}
    blocked.jsonl  directions handed back during this piece of work
    log.jsonl      one line per cycle
```

`outcome` is one of `achieved` / `declined` / `gave-up` / `capped` (or `null`
while running). A non-null `awaiting` object means the loop is **suspended** on async work or a
transient outage — not done, not given up; the awaited task's completion notification resumes it.

## Stop hook

A single `Stop` hook drives the loop:

| Situation | `musician-stop.sh` |
| --- | --- |
| musician active for this session | blocks (re-feeds one cycle) |
| active but `awaiting` set | yields (suspended — terminal frees, no turn burned) |
| `active:false` (achieved / declined / gave-up / capped / cancelled) | yields (session ends) |
| no state / a different session owns it | yields |

It fails **closed**: while a musician state file is active for this session (or present but
unparseable), the hook re-feeds — so a real task is never accidentally dropped mid-flight.

## Dependencies & supervision

- Depends on **cc-tools** (invokes `cc-tools:crux`, `cc-tools:what-to-do`, `cc-tools:how-to-do`,
  `cc-tools:do`, `cc-tools:slap`).
- Supervised by **cc-maestro**: a `musician` state file signals an autonomous, bounded agent with a
  terminal outcome — cc-maestro watches its progress and can cancel it gracefully.
