---
description: "Hand the project ONE thing to carry to a real finish — a task, problem, or idea. The musician thinks it through (and may DECLINE or reframe a bad idea), forges its own definition of done, builds to that done via the cc-funnel pipeline, then closes. With a prompt: think → build. Without one: find a direction itself via what-to-do → build. Bounded and self-closing."
argument-hint: "[task / problem / idea — or nothing to let it find the work] [--auto] [--ultracode]"
---

You were handed this argument:

> $ARGUMENTS

**First action — arm the run yourself.** Arming is *not* auto-run; **you** run it. Only here, on a
fresh `/musician` (never on a Stop-hook re-feed, where the run already exists). Run this **exactly
once**, as your first Bash command — it locates `arm.sh` via the install manifest (`$CLAUDE_PLUGIN_ROOT`
is empty here) and passes your argument to it:

```bash
cfg="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"; r="$(jq -r '.plugins["cc-agent@ccharness"][0].installPath // empty' "$cfg/plugins/installed_plugins.json" 2>/dev/null)"; a="$r/skills/musician/arm.sh"; [ -f "$a" ] || a="$(ls "$cfg"/plugins/cache/*/cc-agent/*/skills/musician/arm.sh 2>/dev/null | sort -V | tail -1)"; [ -f "$a" ] && bash "$a" "$ARGUMENTS" || echo "MUSICIAN_ARM_ERROR: could not locate arm.sh under $cfg/plugins — report this, do not improvise"
```

It creates (or re-adopts) the run and prints `KEY=VALUE` lines. Then **invoke the `musician` skill and
follow it**, reacting to that arm output:

- `RUN_DIR` / `RUN_ID` / `ENTRY` → your run; `phase:"shaping"|"building"` → fork on it.
- `GATE=no-north-star` → tell the user to run `/roadmap-management`; do not proceed.
- `ORPHAN=…` → surface it (resume with `/musician --resume <id>`); don't auto-adopt.
- `RESUMED=…` / `RESUME_MISSING=…` → continue that run / report missing.
- `BUSY=<id>` → this session already has an ACTIVE run; tell the user to `/musician-cancel` it first.
- `MUSICIAN_ARM_ERROR` → report it; do **not** improvise a hand-written run.

**Run `arm.sh` exactly once.** After it has run, do not run it again this turn — a second run is
refused as a duplicate (`BUSY`). The skill's Arm step reacts to this output; it does not re-arm.

The musician is the project's brain for ONE piece of work. It plays the cc-funnel instruments
(`what-to-do` → `how-to-do` → `do` → `refactor-review-test`) plus cc-tools's `crux`/`slap`, and drives
the work to a REAL finish, then **closes**.

- **With a prompt** (a task/problem/idea): it **thinks first** — sized to the input — and may come
  back **declined** ("not worth it / wrong problem") or reframed, rather than blindly building. If it
  clears, it forges a falsifiable definition of done and builds to it.
- **Without a prompt:** it **finds the work itself** via `what-to-do` (auto-picking the top
  direction), then builds that one direction to done.

By default it **shapes the idea with you first, then builds alone.** Before any building it develops
the idea together with you — asking questions, running the thinking instruments — then derives its
definition of done and asks whether you want to review *how* it'll build it (run `how-to-do` and get
your approval) or just go. Only after that does it flip into the fully autonomous build loop.
**`--auto` skips the shaping** and goes straight to autonomy from the first turn (the old behaviour;
this is what `nonstop` uses to walk the roadmap hands-off).

It is **bounded and self-closing**: one piece of work, to its end, then stop — there is no
never-stop loop above it. Exits: **achieved** (done), **declined** (the brain said no — a success,
not a failure), **blocked** (tried, couldn't build it — a business blocker or an exhausted technical
path; no try-count, no cycle cap). Open mode
needs the North Star — with none it routes you to **`/roadmap-management`**.

`--ultracode` forces maximum parallelism in the build step (mandatory Workflow + parallel subagents +
git worktrees). There is **no spend flag** — the musician is bounded by design. Stop it early with
**`/musician-cancel`**.
