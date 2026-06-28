# cc-agent

The self-driving agent layer of the cc-* harness. One loop — the **musician**: the project's brain
for ONE piece of work. It plays the cc-funnel instruments (`what-to-do` → `how-to-do` →
`do` → `refactor-review-test`) plus cc-tools's `crux`/`slap`, thinks before it builds, forges its own definition of done, drives to that done, then
**closes**. Bounded and self-closing — there is no never-stop loop above it.

## `/musician` — the bounded performer

Hand it ONE thing to carry to a real finish — a task, a problem, or an idea.

By default it runs in **two phases: shape the idea with you first, then build alone.** It develops the
idea together with you (asking questions, running the thinking instruments), derives its definition of
done, then asks whether you want to review *how* it'll build it before it goes — and only then flips
into the fully autonomous build loop. **`--auto` skips the shaping** and starts autonomous from the
first turn (the old behaviour; this is what `nonstop` passes to walk the roadmap hands-off).

- **With a prompt** (`/musician <task / problem / idea>`): it **thinks first**, sized to the input
  (a fuzzy pain → `crux`; an idea → North-Star fit; a clear task → straight to build). The brain may
  come back **declined** ("not worth it / wrong problem") or reframed, instead of blindly building.
  If it clears, it forges a falsifiable definition of done and builds to it.
- **Without a prompt** (`/musician`): it **finds the work itself** via `what-to-do` (picking the top
  direction *with* you in shaping, or autonomously under `--auto`), then builds that one direction to done.

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
                             {active, status, run_id, session_id, mode:"musician",
                              entry:"task"|"open", phase:"shaping"|"building",
                              input (the original prompt, verbatim), done_when,
                              cycle, ultracode, awaiting, outcome, worktree_helper, …}
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

`arm.sh` is run **deterministically by the `/musician` command's `!` preprocessing** — before the
model's turn even starts — so arming can never be skipped (the failure mode where the model read the
command but didn't load the skill, and no run was created). It is triggered from **exactly one place**
(the command); the skill only reacts to its output and never re-runs it. Because the command's `!`
context has no `CLAUDE_PLUGIN_ROOT`, the command locates `arm.sh` via the install manifest
(`~/.claude/plugins/installed_plugins.json` → the active `cc-agent` `installPath`), falling back to a
highest-version cache glob.

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
| this session's run active, `phase:"building"` | blocks (re-feeds one cycle) |
| active but `phase:"shaping"` | yields (collaborating with the human — normal conversation, no re-feed) |
| active but `awaiting` set | yields (suspended — terminal frees, no turn burned) |
| `active:false` (achieved / declined / blocked / cancelled) | yields (session ends) |
| no pointer for this session | yields (the common case — most Stops have no musician) |

It fails **closed** where it matters: if this session has a run pointer but its `state.json` is
unreadable, the hook re-feeds — a live task is never dropped to a parse failure. A Stop from a
session with no pointer simply yields.

## Build isolation (worktrees)

The musician **conducts from the main tree but builds in a throwaway git worktree**, so its
autonomous building never dirties your working tree mid-flight — only the finished, committed result
lands on your branch. Each build subagent (`cc-funnel:do`, chaining to `refactor-review-test`) is
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
depending on any settings file. A second consecutive `STALE` is treated as an infra failure and
closes `blocked`. The build sees **committed state only** — uncommitted working-tree changes are not
visible to it (the musician builds from your last commit).

Isolation is **per build dispatch**, so a multi-step piece cuts a fresh worktree each build and
integrates as it goes; a single-build piece is exactly "cut a worktree → build → integrate →
remove". A `declined` run never builds, so it creates no worktree. Its absolute path is recorded in
`state.json` as `worktree_helper` so the in-loop calls find it on re-fed turns (where
`${CLAUDE_PLUGIN_ROOT}` isn't set).

## Watching a run live

A musician reasons inside its own session window, invisible from outside. A `PreToolUse` /
`PostToolUse` hook — `musician-observe.sh` — makes the work visible **as it happens**: while a
musician is active for this session, it appends one line per tool call to `live.log` — the
instrument it called (`crux` / `what-to-do` / `how-to-do` / `do` / `refactor-review-test`), a shell command, a file edit, a
spawned subagent — with the cycle number. It is a read-only witness: it **never blocks or alters a
tool**, and logging is best-effort (skipped if it can't parse the input).

Follow it from another terminal while the musician works (`musicians watch` tails the newest run):

```
bin/musicians watch       # or: tail -f .claude/ccharness/musician/runs/<run-id>/live.log
```

The model's hidden chain-of-thought is not a tool call and is not captured — its spoken narration
and every action are.

## Dependencies & supervision

- Depends on **cc-funnel** (invokes `cc-funnel:what-to-do`, `cc-funnel:how-to-do`, `cc-funnel:do`,
  `cc-funnel:refactor-review-test`) and **cc-tools** (invokes `cc-tools:crux`, `cc-tools:slap`).
- Supervised by **cc-maestro**: a `musician` state file signals an autonomous, bounded agent with a
  terminal outcome — cc-maestro watches its progress and can cancel it gracefully.
