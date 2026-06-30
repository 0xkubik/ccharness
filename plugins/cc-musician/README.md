# cc-musician

The self-driving agent layer of the cc-* harness. One loop — the **musician**: the project's brain
for ONE piece of work. It plays the cc-script instruments (`what-to-do` → `how-to-do` →
`do` → `refactor-review-test`) plus cc-instruments's `crux`/`slap`, thinks before it builds, forges its own definition of done, drives to that done, then
**closes**. Bounded and self-closing — there is no never-stop loop above it.

## `/musician` — the bounded performer

Hand it ONE thing to carry to a real finish — a task, a problem, or an idea.

By default it runs in **two phases: shape the idea with you first, then build alone.** It develops the
idea together with you (asking questions, running the thinking instruments), derives its definition of
done, then asks whether you want to review *how* it'll build it before it goes — and only then flips
into the fully autonomous build loop. **`--auto` skips the shaping** and starts autonomous from the
first turn (the old behaviour; this is what `nonstop` passes to walk the roadmap hands-off).

- **With a prompt** (`/musician <task / problem / idea>`): it **thinks first**, sized to the input
  (a fuzzy pain → `crux`; an idea → North-Star fit; a clear task → straight to build). The brain
  **sharpens a misaimed target** instead of blindly building, but handed work is never refused — it
  forges a falsifiable definition of done and builds to it.
- **Without a prompt** (`/musician`): it **finds the work itself** via `what-to-do` (picking the top
  direction *with* you in shaping, or autonomously under `--auto`), then builds that one direction to done.

It runs as a loop across turns (the Stop hook re-feeds one step per turn while tasks remain), but it
is **bounded**: one piece of work, to its end, then stop. Want another — launch it again.

- **Exits (the only doors out):**
  - **achieved** — the task list is done: every task completed, including the final verify, which
    actually passed.
  - **empty** — *open mode only:* `what-to-do` found nothing worth building (the roadmap frontier is
    exhausted), so there's no direction to pick. Not a refusal of handed work — it's the autonomous
    walker's natural floor, and the signal `nonstop` reads to stop.
  - **cancelled** — `/musician-cancel`. The **only brake on a genuine dead-end**: there is no
    `blocked`/`declined` exit and no give-up. Handed work is always carried toward a build — a `do`
    handback (business blocker or stuck technical path) loops back to `how-to-do` for a different
    approach, never a self-close. If the loop truly can't get past a wall, the human cancels it.
- **Open mode requires a roadmap's North Star** (it leans on `what-to-do`). None → `/roadmap-management` first.
- `/musician-cancel` is the manual brake.
- `--auto` skips the collaborative shaping phase and arms straight into the autonomous build loop.
- `--ultracode` forces maximum parallelism in the build (mandatory Workflow + parallel subagents +
  git worktrees). There is **no spend flag** — the musician is bounded by design.

## State directory

Each run gets its OWN folder so many runs in one repo never collide:

```
.claude/ccharness/
  musician/
    runs/<run-id>/            one folder per run  (run-id = UTC YYYYMMDD-HHMMSS-<hex>, sortable)
      state.json             loop control + identity
                             {active, run_id, session_id, mode:"musician",
                              entry:"task"|"open", phase:"shaping"|"building",
                              input (the original prompt, verbatim),
                              tasks (the ordered plan: [{id, subject, status}], last = verify),
                              ultracode, awaiting, outcome, worktree_helper, …}
      log.jsonl              one line per step (carries which approaches failed this run)
      live.log               live action feed — one line per tool call (see "Watching a run live")
      heartbeat              touched by the hooks each turn/tool call (crash detection)
    by-session/<session-id>  pointer → the active run-id for that session (how the hooks find it)
```

`tasks` is the loop state: an ordered list `[{id, subject, status}]` (status `pending` /
`in_progress` / `completed`) whose LAST item is always a real verification. The hooks re-feed while
any task is incomplete and release when no incomplete task is left (the list is done, or — abnormally
— empty; decomposition happens on the first turn, never via a re-feed). There is **no stored status field** —
the lifecycle label (`working` / `suspended` / `shaping` / `achieved` / `empty` / `cancelled`) is
*derived* from `active` + `awaiting` + `phase` + `outcome`. A non-null `awaiting` object means the
loop is **suspended** on async work or a transient outage — not done, not given up; the awaited
task's completion notification resumes it.

## Arm & crash recovery

`arm.sh` is **run by the model itself** — the `/musician` command's body instructs it to, as its very
first action; it is **not** auto-run by a `!` preprocessing block. Arming is the model's
responsibility (run it once on a fresh `/musician`, skip it on a Stop-hook re-feed where the run
already exists). Because the model's Bash context has no `CLAUDE_PLUGIN_ROOT`, the command tells it to
locate `arm.sh` via the install manifest (`~/.claude/plugins/installed_plugins.json` → the active
`cc-musician` `installPath`), falling back to a highest-version cache glob. The trade-off of
model-mediated arming: a model that skips the instruction creates no run — the `BUSY` idempotency
guard prevents *duplicate* runs, not *skipped* ones.

`arm.sh` parses the flags (`--auto` → arm in the `building` phase, else `shaping`; `--ultracode` /
`--resume <run-id>`), runs the open-mode North-Star gate, enforces **idempotency** (one active run per
session — a second arm is refused as `BUSY=<id>`, so a duplicate run can never be forged), forges the
`run_id`, writes `state.json` + the pointer + the record files, and **scans for crashed runs**. The
brain stays in the skill; only the bookkeeping is in the script.

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
| active, `phase:"building"`, a task still incomplete | blocks (re-feeds the next step) |
| active, building, no incomplete task (list done, or empty) | yields (nothing to do) |
| active but `phase:"shaping"` | yields (collaborating with the human — normal conversation, no re-feed) |
| active but `awaiting` set | yields (suspended — terminal frees, no turn burned) |
| `active:false` (achieved / empty / cancelled) | yields (session ends) |
| no pointer for this session | yields (the common case — most Stops have no musician) |

It fails **closed** where it matters: if this session has a run pointer but its `state.json` is
unreadable, the hook re-feeds — a live task is never dropped to a parse failure. A Stop from a
session with no pointer simply yields.

## Build isolation (worktrees)

The musician **conducts from the main tree but builds in a throwaway git worktree**, so its
autonomous building never dirties your working tree mid-flight — only the finished, committed result
lands on your branch. Each build subagent (`cc-script:do`, chaining to `refactor-review-test`) is
dispatched with the Agent tool's **`isolation:"worktree"`**: the subagent, its tools, and any
sub-agents it spawns all run inside one worktree under `.claude/worktrees/`. (A plain "cd into a
worktree" instruction leaks back to the main tree — a dispatched agent starts at the main root and
`cd` doesn't persist — which is why the harness primitive is the only reliable containment.)

`skills/musician/worktree.sh` owns the deterministic git bookkeeping (so it isn't hand-typed across
re-fed turns):

- `prepare` (once, at arm) — gitignore `.claude/worktrees/` and flag an uncommitted North Star
  (`GROUNDING_DIRTY=1`) that would be absent in the worktree.
- `integrate <path> <branch>` — **fast-forward-only**, the load-bearing guarantee. The build was
  reset onto your current HEAD, so its branch fast-forwards cleanly onto your branch; the worktree +
  branch are then removed. If it is NOT a fast-forward (`STALE`), the build wasn't on your HEAD —
  stale work is **refused, never merged in silently**, and the worktree is kept.
- `discard <path> <branch>` — an abandoned build (handback / dead approach), or a `STALE` one being
  rebuilt: drop the worktree, keeping nothing.

The harness cuts the worktree from a base you don't control (it can be a stale `origin`), so the
conductor doesn't trust it: it captures `BASE = git rev-parse HEAD` and tells the build subagent to
`git reset --hard BASE` as its first action. That — plus the ff-only integrate that refuses anything
not on `BASE` — is what makes "the build always starts from your latest commit" reliable without
depending on any settings file. A persistent `STALE` the loop can't get past is an infra failure —
the human's cue to `/musician-cancel` (there's no self-close). The build sees **committed state
only** — uncommitted working-tree changes are not visible to it (the musician builds from your last commit).

Isolation is **per build dispatch**, so a multi-step piece cuts a fresh worktree each build and
integrates as it goes; a single-build piece is exactly "cut a worktree → build → integrate →
remove". An `empty` run never builds, so it creates no worktree. Its absolute path is recorded in
`state.json` as `worktree_helper` so the in-loop calls find it on re-fed turns (where
`${CLAUDE_PLUGIN_ROOT}` isn't set).

## Watching a run live

A musician reasons inside its own session window, invisible from outside. A `PreToolUse` /
`PostToolUse` hook — `musician-observe.sh` — makes the work visible **as it happens**: while a
musician is active for this session, it appends one line per tool call to `live.log` — the
instrument it called (`crux` / `what-to-do` / `how-to-do` / `do` / `refactor-review-test`), a shell command, a file edit, a
spawned subagent — tagged with the task progress (`[done/total]`). It is a read-only witness: it
**never blocks or alters a tool**, and logging is best-effort (skipped if it can't parse the input).

Follow it from another terminal while the musician works (`ccmusicianctl watch` tails the newest run):

```
bin/ccmusicianctl watch      # or: tail -f .claude/ccharness/musician/runs/<run-id>/live.log
```

The model's hidden chain-of-thought is not a tool call and is not captured — its spoken narration
and every action are.

## Driving a run from the shell (`ccmusicianctl`)

`bin/ccmusicianctl` inspects, steers, and launches this repo's musician runs (the machine-wide view
across every repo is `ccconductorctl`). Its grammar is verb-first, shared with `ccconductorctl`; `musiciansctl`
is a thin alias for the same command.

```
ccmusicianctl ls [--json]                 every run here (id, state, nonstop, age, task)
ccmusicianctl info <id>                   the full card for one run
ccmusicianctl logs <id> [--tail N]        the tail of a run's live feed (no follow)
ccmusicianctl watch [<id>]                follow a run's live feed (newest if no id)
ccmusicianctl start "<task>" [--repo P]   launch an autonomous musician on the repo (detached)
ccmusicianctl stop <id>                   soft-cancel a run (the /musician-cancel brake, by id)
ccmusicianctl nonstop <id> on|off         arm/disarm nonstop for that run's session
```

`start` spawns `claude -p "/musician --auto <task>"` detached, with bypass permissions so it can
build unattended. Several musicians can run on one repo at once — each builds in its own worktree
and keys its state by session, so independent (non-colliding) tasks parallelise freely.

## Dependencies & supervision

- Depends on **cc-script** (invokes `cc-script:what-to-do`, `cc-script:how-to-do`, `cc-script:do`,
  `cc-script:refactor-review-test`) and **cc-instruments** (invokes `cc-instruments:crux`, `cc-instruments:slap`).
- Supervised by **cc-conductor**: a `musician` state file signals an autonomous, bounded agent with a
  terminal outcome — cc-conductor watches its progress and can cancel it gracefully.
