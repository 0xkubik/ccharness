---
name: do
description: "Use when you have ONE concrete, well-scoped coding task ready to build autonomously. Not for vague or fork-laden tasks — it refuses those rather than guessing."
---

# do — the strict executor

You are running the **do** pipeline: take ONE concrete task from understood →
built → smoke-checked, then **hand it off to `refactor-review-test`** — stopping with nothing
half-done. It is the foot of the build funnel (what-to-do → how-to-do → do → refactor-review-test)
and also runs standalone on any concrete task. **You own execution; the human owns direction.**
Drive the stages below in order. Do not skip a stage. Do not declare done while the Stage-2
checklist has open items.

**Core invariants — non-negotiable:**
- **Refuse, don't guess** (Stage 0 — and the fork-test stays armed all the way through Stage 4). A technical fork goes to how-to-do; a business / non-technical one it refuses outright; a vague task goes to brainstorming — never a guessed default.
- **Smoke-check before you hand off** (Stage 5). Prove it *runs* — compile / boot / a smoke test — evidence, not assertion. The full verify is `refactor-review-test`'s, not yours.
- **You never commit.** `do` hands off un-committed code; `refactor-review-test` owns the verified local commit.
- **3 strikes on one problem → reset, don't keep patching** (slap) — then pick the fresh approach yourself.

---

## Grounding precondition (the gate — before Stage 0)

Confirm a `## Product North Star` heading exists at the top of `.claude/ccharness/roadmap.md`. **Absent
→ STOP and route to `/roadmap-management`** (cc-tools builds from the goal outward; don't run ungrounded).
Arriving from how-to-do or under the musician, the North Star already exists — the gate just passes.

---

## Stage 0 — Clarity gate (refuse if unclear)

**Arrived here from how-to-do?** Then the fork is already resolved — how-to-do's decision *is* the
direction, and any `decision_axes` it shows were already ruled (the human could have vetoed and
didn't). Pass the gate and proceed; do **not** re-open the choice or route it back up — that's
the how-to-do→do→how-to-do loop. The gate below is for tasks that reach you *without* a
how-to-do decision behind them.

Before touching anything, decide whether this task is safe to execute autonomously. It is
safe **only if all three hold**:

1. **End state is unambiguous** — you can write the acceptance criteria from the task alone,
   without inventing a requirement.
2. **No serious fork** — neither a **business fork** (money, legal, product direction — a
   *what/whether* call, not a build choice) nor a **technical fork** (an architecture, approach,
   or build-scope choice with materially different consequences and no obvious winner).
3. **You have what you need to start** — repo, stack, access, constraints.

If ANY fails → **STOP. Do not implement.** Emit one short block naming exactly what is unclear
or which fork is unresolved, then route by *what* is wrong — this is the funnel talking back
upward, not a dead end:

- **A technical fork** (architecture, approach, or build-scope — materially different options, no
  obvious winner) → hand the task to **`cc-funnel:how-to-do`**, the funnel's decision loop. Resolving
  *how-to-build* forks is how-to-do's lane, not yours; it decides and flows the chosen approach back
  into the build.
- **A business / non-technical fork** (money, legal, product direction — a *what/whether* call) →
  **refuse to run.** It is not yours to decide and not how-to-do's either — its compass picks build
  approaches, not business questions. Name the snag, stop, and leave it to the human. Re-enter do
  only once they've settled it.
- **Pure ambiguity** (you cannot write the acceptance criteria — missing facts, unclear intent,
  *no* genuine fork) → invoke **`superpowers:brainstorming`** to surface what's wanted, or just
  ask the human. This is a clarification, not a decision.

Re-enter do only once the task comes back clear and fork-free.

| Rationalization | Reality |
|---|---|
| "I'm autonomous, so I should just decide." | Autonomy is over *execution*, not *direction*. Choosing between materially different approaches or outcomes is the human's call — not a default to set. |
| "I'll pick a sensible default and note the caveat in the commit." | A defaulted fork is an unmade decision shipped as code. A choice with architectural weight is a fork — route it to how-to-do; a business one (money, legal, direction) is not yours either — refuse and leave it to the human. |
| "The task says 'get it done', so clarifying is disobeying." | "Get it done" is the *what*. It never authorizes guessing the *direction*. Resolving the fork first IS getting it done right. |
| "Clarifying is slow / annoying." | Guessing wrong is far slower. brainstorming resolves the fork in minutes; a wrong rebuild costs hours. |

**Red flags — STOP and run the handoff above:**
- You're about to choose between two real options "to keep moving."
- You're writing "I'll assume…", "defaulting to…", or "they probably want…" about something
  with business or architectural weight.
- You can't state the acceptance criteria without inventing a requirement.
- The task could be built two materially different ways and you'd be choosing for the user.

---

## Stage 1 — Map the codebase (understand the whole project first)

Before scoping the change, build a complete picture of the project — a fresh executor that hasn't
seen this codebase places nothing well until it can see where things live. This mapping is
mechanical, so **dispatch it to a subagent on the `haiku` model** (fast and cheap — the same way
Claude Code's own Explore subagents map a repo) and scope the change from the map it returns. The
two parts below are that subagent's brief; both mandatory:

- **Study the code.** If **codegraph** is indexed for this workspace (its MCP tools are available,
  or a `.codegraph/` index exists), use it to read the structure — modules, dependencies, call
  relationships. If it isn't, fall back to **grep / search** across the tree. Do **not** run
  `codegraph init` yourself — indexing is the user's call; use codegraph when it's already there,
  else grep.
- **Build the full folder tree — always.** Run **`cctree`** (a cc-tools helper — it auto-picks the
  best tree tool installed and leaves out whatever `.gitignore` ignores) to print the whole tree, so
  you can see *everything* in the project: module boundaries, where code lives, the naming and file
  conventions. If `cctree` isn't on PATH (cc-tools not installed), fall back to `tree`, or
  `git ls-files` / `find`. This is mandatory regardless of how small the change is — you place the
  change against this map in Stage 2.

---

## Stage 2 — Scope the work

**Place the change cleanly into the structure you mapped in Stage 1.** Work out how to fit it
**into the existing structure** rather than dropping files wherever is easiest: which module it
extends, what to name things, where new files go. If clean placement needs a **small, obvious
structural move** — e.g. a lone module at the root gains a sibling, so the two move into their own
folder — you **may** make it as part of this change to keep the tree tidy; fold it into the
checklist below as an explicit deliverable. Bound it: it must be warranted by *this* change, not a
licence to refactor the repo — the wider hardening refactor stays `refactor-review-test`'s. A
genuine **structural fork** (materially different layouts, no clear winner, costly to reverse) is
not a routine move — route it to how-to-do like any other fork.

**If you arrived here from how-to-do**, its decision is your starting point: the fork is already
resolved and the approach chosen — turn that decided approach into the checklist, do not
re-litigate the decision or bounce it back up. Produce an explicit, **ordered checklist** of the
concrete deliverables — this is your definition of done for Stage 4 and must stay visible. Then
size the task:

- **trivial / small** → keep the checklist inline.
- **medium / large** → invoke `superpowers:writing-plans` to produce a written plan first.

While scoping, note the signals that drive Stage 3: Is there UI? Is browser/E2E behavior
involved? Is this a long, repetitive grind (many similar edits) or a few targeted changes?
Is there a test harness?

---

## Stage 3 — Select tools

Pick the execution machinery from the Stage-2 signals, then **say your choice out loud**
("Using X because Y") before you start Stage 4.

| Signal | Tool |
|---|---|
| UI / frontend work | `frontend-design` skill |
| Any code change with a test harness | `superpowers:test-driven-development` (red→green→refactor) |
| Many independent subtasks, no shared state | `superpowers:dispatching-parallel-agents` or `superpowers:subagent-driven-development` |
| A written plan, executed in this session | `superpowers:subagent-driven-development` |
| A written plan, separate-session review checkpoints | `superpowers:executing-plans` |
| Web behavior to drive or verify | `playwright` MCP |
| Large, structured fan-out you can justify | a **Workflow** (the Workflow tool) — *autonomous, see note* |
| Inherently sequential work that splits into a clean, repeated iteration step | `ralph-loop` — *see note* |
| Anything else | your own in-session goal-loop (Stage 4) |

**Workflow note:** launch a Workflow when you can **justify** it — a large, structured fan-out
where deterministic orchestration (staged fan-out, per-item verify) earns its token cost. You
may do this **autonomously, without asking the user** — invoking `/do` is itself the
opt-in, so just state your justification out loud and proceed. For only a handful of
independent pieces, prefer subagents (`superpowers:dispatching-parallel-agents`) — they're
lighter; reserve Workflows for genuine scale.

**ralph-loop note:** choose ralph-loop when the work is **inherently sequential** (nothing to
parallelize) **and** it decomposes into a clean, repeatable iteration step the same loop can
grind to completion. ralph-loop is a session-level while-true on a fixed prompt, so make each
iteration **verify its own step**; once the loop finishes, return here for the whole-result
Stage 5 smoke-check and the hand-off to `refactor-review-test`.

---

## Stage 4 — Implement (goal-loop to done)

Execute with the chosen tools. **Your own loop is the engine:** work the Stage-2 checklist top
to bottom and do not stop while any item is open. Use TDD where a test harness exists. This is
where the strike counter and the still-armed fork-test live — see Escalation.

---

## Stage 5 — Smoke-check (does it run?)

Prove the change **runs** — never assert it. Compile / boot it and run a smoke check (or the
quick happy-path test); for UI, load it and see it render. This is the *does-it-even-run* gate
before hand-off — **not** the full verify-to-green, the coverage pass, or review. If the smoke check fails, fix it here (Stage 4 ↔ 5, root cause via
`superpowers:systematic-debugging`) until the change runs; then hand off.

---

## Stage 6 — Hand off to refactor-review-test

The change runs. **Now hand it off — `do` always ends here.** Invoke
**`cc-funnel:refactor-review-test`** on the change you just built; it owns the rest — the full
verify, the behavior-preserving refactor, `/code-review` + `/simplify`, the full test coverage,
and the verified local commit. You do **not** review, simplify, test-to-green, or commit yourself;
handing off un-committed code is the design, not a gap.

Under the musician this hand-off is transparent: the `do → refactor-review-test` chain runs inside
your dispatch and the commit/sha comes back from its end.

---

## Escalation — route upward, never to the human

Past the Stage-0 gate you own the build to its end, and **implementation never escalates to the
human.** The only human touchpoint is the Stage-0 gate (before the build) — past it, `do` runs
straight through to the hand-off (the push offer now lives with `refactor-review-test`, which
commits). Two things still route *upward to the right machinery*, and neither is the user: a
**decision** goes to how-to-do, a **stuck fix** goes to slap.

### A serious technical fork surfaces mid-build → `how-to-do`

The Stage-0 fork-test **does not expire at the gate — it stays armed through Stage 4.** As you
learn the terrain you will hit technical choices that weren't visible at the start. For each,
apply the same test: it is a **serious fork** only when it has **(a)** materially different
consequences, **(b)** no obvious winner, **and (c)** is costly to reverse. All three → stop and
hand it **up to `cc-funnel:how-to-do`**; it's the decision loop (not the user), it rules the fork,
and its fork-free decision flows back into the build. Not all three → it's a **routine call:
decide it yourself and keep moving** — a strict executor keeps momentum on anything it can later
undo. A fork how-to-do has already ruled is fork-free; never send the same one up twice.

*This is a **decision** — a choice between approaches that all work. Distinct from slap below,
which is for an approach that **isn't working.***

### A fix won't take after 3 tries → `slap`

Keep an **explicit running tally per distinct problem** (a specific failing test, build error,
or bug) in your working notes — `problem X: attempt N`. A genuine fix attempt that does not
resolve the problem is one strike.

On the **3rd failed attempt at the same problem**, stop patching and **invoke the
`cc-tools:slap` skill**, handing it that problem's context (what you're trying to do, what you
already tried, why each attempt failed). Work slap's rethink protocol — but **resolve it
yourself**: where slap would present alternatives *to the user* or ask which way to go, *you*
weigh the fresh approaches and pick the best one. Adopt it, continue, and **reset that problem's
tally to zero.** A new, distinct problem starts its own tally.

If slap fires again on the same problem, run it *again* — each time reconsidering the approach
more fundamentally (wrong layer? wrong tool? wrong decomposition? is the whole approach unsound?)
and deciding the next move yourself. Keep driving until the work is done and verified.

---

## Quick reference

Grounding — no `## Product North Star` → **route to `/roadmap-management`**, stop · `0` Gate — technical fork → how-to-do, business → refuse,
vague → brainstorming · `1` Map the codebase — **codegraph if indexed, else grep; always print the
full folder tree via `cctree`** · `2` Scope — place the change cleanly (small structural moves OK, tied to this
change; structural fork → how-to-do) · checklist + size · `3` Tools — route & announce · `4` Build —
goal-loop to done · `5` Smoke-check — does it run? · `6` Hand off → **refactor-review-test** (it owns
verify, review/simplify, full tests, and the commit). `do` never commits.

Mid-build, a serious technical fork (material · no clear winner · costly to reverse) → **how-to-do**; routine/reversible calls you make yourself.
Strike 3 on one problem → **slap**, then pick the fresh approach yourself. Implementation never hands back to the human — re-decide as needed.
