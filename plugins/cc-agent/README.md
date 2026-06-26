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
    not a failure; it is distinct from `blocked`.
  - **blocked** — *tried and couldn't build it*: the `do` subagent hit a business / non-technical
    blocker it refuses, or the technical path is exhausted (how-to-do has no new buildable approach
    left). There is no try-count and no cycle cap — one real blocker closes the run.
- **Open mode requires a roadmap's North Star** (it leans on `what-to-do`). None → `/find-goal` first.
- `/musician-cancel` is the manual brake.
- `--ultracode` forces maximum parallelism in the build (mandatory Workflow + parallel subagents +
  git worktrees). There is **no spend flag** — the musician is bounded by design.

## State directory

Each run gets its OWN folder so many runs in one repo never collide:

```
.claude/ccharness/
  musician/
    runs/<run-id>/            one folder per run  (run-id = UTC YYYYMMDD-HHMMSS-<hex>, sortable)
      state.json             loop control + identity
                             {active, status, run_id, session_id, mode:"musician",
                              entry:"task"|"open", input (the original prompt, verbatim), done_when,
                              cycle, ultracode, awaiting, outcome, …}
      blocked.jsonl          directions handed back during this run
      log.jsonl              one line per cycle
      live.log               live action feed — one line per tool call (see "Watching a run live")
      heartbeat              touched by the hooks each turn/tool call (crash detection)
    by-session/<session-id>  pointer → the active run-id for that session (how the hooks find it)
```

`status` is the human-readable lifecycle label — `working` / `suspended` / `achieved` / `declined`
/ `blocked` / `cancelled`. `outcome` carries the same terminal value (or `null` while
running); `active` + `awaiting` are what the hooks gate on. A non-null `awaiting` object means the
loop is **suspended** on async work or a transient outage — not done, not blocked; the awaited
task's completion notification resumes it.

## Arm & crash recovery

`/musician` runs `skills/musician/arm.sh` first — the deterministic setup the skill used to
hand-write: it parses the flags (`--ultracode` / `--resume <run-id>`), runs the open-mode North-Star
gate, forges the `run_id`, writes `state.json` +
the pointer + the record files, and **scans for crashed runs**. The brain stays in the skill; only
the bookkeeping is in the script.

A musician can't leave a task *accidentally*: while the session lives, the Stop hook re-feeds an
unclosed run. A hard crash (terminal closed, kill, reboot) fires no Stop event — so each working run
keeps a `heartbeat` the hooks refresh. The next `/musician` arm finds any run still `working` whose
heartbeat went **stale** (a crash) and **surfaces it** (`ORPHAN=<id>|<mins>|<input>`); it never
auto-adopts. Resume one deliberately with `/musician --resume <run-id>`.

## Stop hook

A single `Stop` hook drives the loop:

The hook finds THIS session's run via the `by-session/<session-id>` pointer (see `musician-resolve.sh`):

| Situation | `musician-stop.sh` |
| --- | --- |
| this session's run active | blocks (re-feeds one cycle) |
| active but `awaiting` set | yields (suspended — terminal frees, no turn burned) |
| `active:false` (achieved / declined / blocked / cancelled) | yields (session ends) |
| no pointer for this session | yields (the common case — most Stops have no musician) |

It fails **closed** where it matters: if this session has a run pointer but its `state.json` is
unreadable, the hook re-feeds — a live task is never dropped to a parse failure. A Stop from a
session with no pointer simply yields.

## Watching a run live

A musician reasons inside its own session window, invisible from outside. A `PreToolUse` /
`PostToolUse` hook — `musician-observe.sh` — makes the work visible **as it happens**: while a
musician is active for this session, it appends one line per tool call to `live.log` — the
instrument it called (`crux` / `what-to-do` / `how-to-do` / `do`), a shell command, a file edit, a
spawned subagent — with the cycle number. It is a read-only witness: it **never blocks or alters a
tool**, and logging is best-effort (skipped if it can't parse the input).

Follow it from another terminal while the musician works (`musician-watch` tails the newest run):

```
bin/musician-watch        # or: tail -f .claude/ccharness/musician/runs/<run-id>/live.log
```

The model's hidden chain-of-thought is not a tool call and is not captured — its spoken narration
and every action are.

## Dependencies & supervision

- Depends on **cc-tools** (invokes `cc-tools:crux`, `cc-tools:what-to-do`, `cc-tools:how-to-do`,
  `cc-tools:do`, `cc-tools:slap`).
- Supervised by **cc-maestro**: a `musician` state file signals an autonomous, bounded agent with a
  terminal outcome — cc-maestro watches its progress and can cancel it gracefully.
