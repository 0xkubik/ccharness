---
name: do
description: "Use when handing a concrete, well-scoped coding task to be taken all the way to done — implemented, verified, and committed. Not for vague or fork-laden tasks — it refuses those rather than guessing."
---

# do — the strict executor

You are running the **do** pipeline: take ONE concrete task from understood →
built → verified → committed, and stop with nothing half-done. It is the foot of the funnel
(what-to-do → how-to-do → do) and also runs standalone on any concrete task. **You own
execution; the human owns direction.** Drive the seven stages below in order. Do not skip a
stage. Do not declare done while the Stage-1 checklist has open items.

**Core invariants — non-negotiable:**
- **Refuse, don't guess** (Stage 0 — and the fork-test stays armed all the way through Stage 3). A technical fork goes to how-to-do; a business / non-technical one it refuses outright; a vague task goes to brainstorming — never a guessed default.
- **Verify before you claim** (Stage 4). Evidence, not assertion.
- **Never commit unverified code** (Stage 6 only runs after Stage 4 is green).
- **3 strikes on one problem → reset, don't keep patching** (slap) — then pick the fresh approach yourself; **implementation never hands back to the human.**

---

## Grounding precondition (the gate — before Stage 0)

Confirm a `## Product North Star` heading exists in repo-root `CLAUDE.md`. **Absent → STOP and route
to `/find-goal`** (cc-tools builds from the goal outward; don't run ungrounded). Arriving from how-to-do
or under the musician, the North Star already exists — the gate just passes.

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
  obvious winner) → hand the task to **`cc-tools:how-to-do`**, the funnel's decision loop. Resolving
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

## Stage 1 — Scope the work

**If you arrived here from how-to-do**, its decision is your starting point: the fork is already
resolved and the approach chosen — turn that decided approach into the checklist, do not
re-litigate the decision or bounce it back up. Produce an explicit, **ordered checklist** of the
concrete deliverables — this is your definition of done for Stage 3 and must stay visible. Then
size the task:

- **trivial / small** → keep the checklist inline.
- **medium / large** → invoke `superpowers:writing-plans` to produce a written plan first.

While scoping, note the signals that drive Stage 2: Is there UI? Is browser/E2E behavior
involved? Is this a long, repetitive grind (many similar edits) or a few targeted changes?
Is there a test harness?

---

## Stage 2 — Select tools

Pick the execution machinery from the Stage-1 signals, then **say your choice out loud**
("Using X because Y") before you start Stage 3.

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
| Anything else | your own in-session goal-loop (Stage 3) |

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
Stage 4 verify and Stage 6 commit.

---

## Stage 3 — Implement (goal-loop to done)

Execute with the chosen tools. **Your own loop is the engine:** work the Stage-1 checklist top
to bottom and do not stop while any item is open. Use TDD where a test harness exists. This is
where the strike counter and the still-armed fork-test live — see Escalation.

---

## Stage 4 — Verify & debug (mandatory)

Prove it works — never assert it. Run the build, the tests, and the linters; for UI, drive it
through `playwright` and observe the actual result. Use `superpowers:verification-before-completion`:
show the evidence, don't claim. On any failure, switch to `superpowers:systematic-debugging` —
fix the root cause, not the symptom. Loop Stage 3 ↔ 4 until green.

---

## Stage 5 — Review & simplify (optional)

Run this **only if the task produced non-trivial code.** Skip it for docs-only, config-only, or
trivial changes — and say why you skipped. When it applies:

1. `code-review:code-review` on the diff — correctness.
2. The `code-simplifier` agent on the changed code — clarity and maintainability.
3. Triage the findings through `superpowers:receiving-code-review` — verify before applying;
   don't agree performatively.

If you change anything, return to Stage 4 and re-verify.

---

## Stage 6 — Commit (local only)

1. Make a **local commit** with `commit-commands:commit` (it crafts the message; honor the
   repo's commit conventions).
2. **STOP before push / PR / MR.** Do not push or open a merge request.
3. Report the commit, then offer the next step — auto-detected from the git remote: a GitLab
   remote → the `gitlab` MR tools; otherwise `commit-commands:commit-push-pr`. The human
   triggers it.

---

## Escalation — route upward, never to the human

Past the Stage-0 gate you own the build to its end, and **implementation never escalates to the
human.** The only human touchpoints are the Stage-0 gate (before the build) and the optional
push offer (after Stage 6) — never the middle. Two things still route *upward to the right
machinery*, and neither is the user: a **decision** goes to how-to-do, a **stuck fix** goes to slap.

### A serious technical fork surfaces mid-build → `how-to-do`

The Stage-0 fork-test **does not expire at the gate — it stays armed through Stage 3.** As you
learn the terrain you will hit technical choices that weren't visible at the start. For each,
apply the same test: it is a **serious fork** only when it has **(a)** materially different
consequences, **(b)** no obvious winner, **and (c)** is costly to reverse. All three → stop and
hand it **up to `cc-tools:how-to-do`**; it's the decision loop (not the user), it rules the fork,
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

Grounding — no `## Product North Star` → **route to `/find-goal`**, stop · `0` Gate — technical fork → how-to-do, business → refuse,
vague → brainstorming · `1` Scope — checklist + size · `2` Tools — route & announce · `3` Build —
goal-loop to done · `4` Verify — evidence, debug to green · `5` Review+simplify — only if
non-trivial · `6` Commit — local only, then offer push.

Mid-build, a serious technical fork (material · no clear winner · costly to reverse) → **how-to-do**; routine/reversible calls you make yourself.
Strike 3 on one problem → **slap**, then pick the fresh approach yourself. Implementation never hands back to the human — re-decide as needed.
