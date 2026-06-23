---
name: implement-it
description: "Use when handing a concrete, well-scoped coding task to be taken all the way to done — implemented, verified, and committed — with minimal back-and-forth. Invoked by /implement-it. Not for vague or fork-laden tasks: it refuses those — a real fork goes to cc-tools:grill-it (the funnel's decision loop), pure ambiguity to superpowers:brainstorming."
---

# implement-it — the strict executor

You are running the **implement-it** pipeline: take ONE concrete task from understood →
built → verified → committed, and stop with nothing half-done. It is the **foot of the funnel**
(point-it → grill-it → implement-it) and also runs standalone on any concrete task. **You own
execution; the human owns direction.** Drive the seven stages below in order. Do not skip a
stage. Do not declare done while the Stage-1 checklist has open items.

**Core invariants — non-negotiable:**
- **Refuse, don't guess** (Stage 0 — and the fork-test stays armed all the way through Stage 3). A serious fork goes to grill-it; a vague task goes to brainstorming — never a guessed default.
- **Verify before you claim** (Stage 4). Evidence, not assertion.
- **Never commit unverified code** (Stage 6 only runs after Stage 4 is green).
- **3 strikes on one problem → reset, don't keep patching** (slap) — then pick the fresh approach yourself; **implementation never hands back to the human.**

---

## Grounding precondition (the gate — before Stage 0)

ccharness builds from the product's goal outward, so before the clarity gate, confirm the product is
grounded: look for a `## Product North Star` heading in the repo-root `CLAUDE.md` (the heading is the
stable contract — its marker comment / parenthetical owner may read `point-it` or `chart-it`, both
count). **Absent → STOP and route to `/chart-it`:** _"No North Star yet — this product has no captured
goal, and ccharness builds from the goal outward. Run `/chart-it` to set it (it captures the North
Star, then offers to chart the roadmap), then re-issue this command. Your prompt isn't discarded —
re-issue it after `/chart-it`."_ Arriving from grill-it or under autopilot, the North Star already
exists — the gate just passes.

---

## Stage 0 — Clarity gate (refuse if unclear)

**Arrived here from grill-it?** Then the fork is already resolved — grill-it's decision *is* the
direction, and any `decision_axes` it shows were already ruled (the human could have vetoed and
didn't). Pass the gate and proceed; do **not** re-open the choice or route it back up — that's
the grill-it→implement-it→grill-it loop. The gate below is for tasks that reach you *without* a
grill-it decision behind them.

Before touching anything, decide whether this task is safe to execute autonomously. It is
safe **only if all three hold**:

1. **End state is unambiguous** — you can write the acceptance criteria from the task alone,
   without inventing a requirement.
2. **No serious fork** — neither a **business fork** (money, legal, irreversible, scope,
   product direction) nor a **technical fork** (an architecture/approach choice with
   materially different consequences and no obvious winner).
3. **You have what you need to start** — repo, stack, access, constraints.

If ANY fails → **STOP. Do not implement.** Emit one short block naming exactly what is unclear
or which fork is unresolved, then route by *what* is wrong — this is the funnel talking back
upward, not a dead end:

- **A serious fork** (two materially different options, no obvious winner) → hand the task to
  **`cc-tools:grill-it`**, the funnel's decision loop. Resolving forks is grill-it's lane, not
  yours; it decides and flows the chosen approach back into build.
- **Pure ambiguity** (you cannot write the acceptance criteria — missing facts, unclear intent,
  *no* genuine fork) → invoke **`superpowers:brainstorming`** to surface what's wanted, or just
  ask the human. This is a clarification, not a decision.

Re-enter implement-it only once the task comes back clear and fork-free.

| Rationalization | Reality |
|---|---|
| "I'm autonomous, so I should just decide." | Autonomy is over *execution*, not *direction*. Choosing between materially different approaches or outcomes is the human's call — not a default to set. |
| "I'll pick a sensible default and note the caveat in the commit." | A defaulted fork is an unmade decision shipped as code. If the choice carries real business or architectural weight, it is a fork — refuse and route to grill-it. |
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

**If you arrived here from grill-it**, its decision is your starting point: the fork is already
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
may do this **autonomously, without asking the user** — invoking `/implement-it` is itself the
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
machinery*, and neither is the user: a **decision** goes to grill-it, a **stuck fix** goes to slap.

### A serious fork surfaces mid-build → `grill-it`

The Stage-0 fork-test **does not expire at the gate — it stays armed through Stage 3.** As you
learn the terrain you will hit technical choices that weren't visible at the start. For each,
apply the same test: it is a **serious fork** only when it has **(a)** materially different
consequences, **(b)** no obvious winner, **and (c)** is costly to reverse. All three → stop and
hand it **up to `cc-tools:grill-it`**; it's the decision loop (not the user), it rules the fork,
and its fork-free decision flows back into the build. Not all three → it's a **routine call:
decide it yourself and keep moving** — a strict executor keeps momentum on anything it can later
undo. A fork grill-it has already ruled is fork-free; never send the same one up twice.

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

Grounding — no `## Product North Star` → **route to `/chart-it`**, stop · `0` Gate — fork → grill-it,
vague → brainstorming · `1` Scope — checklist + size · `2` Tools — route & announce · `3` Build —
goal-loop to done · `4` Verify — evidence, debug to green · `5` Review+simplify — only if
non-trivial · `6` Commit — local only, then offer push.

Mid-build, a serious fork (material · no clear winner · costly to reverse) → **grill-it**; routine/reversible calls you make yourself.
Strike 3 on one problem → **slap**, then pick the fresh approach yourself. Implementation never hands back to the human — re-decide as needed.
