---
name: grill-it
description: Use when a task carries a real fork — a business or technical decision with materially different options and no obvious winner — or when an idea must be thought through before building, or when point-it hands over a checked list of directions to decide. Turns the question (or each list item) into ONE reasoned decision via four opposed proposers (a compass) → cross-examination → synthesis, scaling depth to stakes and to each item's move. A faster, more rigorous replacement for open-ended brainstorming. The human rules only at the boundaries.
---

# grill-it — the decision loop

You are running **grill-it**: turn an open question or a fork-laden task into ONE
well-reasoned decision — crisp enough to wave through or redirect at a glance — then flow it
into the build. **You do the thinking; the human owns direction and rules at the boundaries.**

**One fork or a list.** Standalone (`/grill-it <decision>`) you get one fork. From **point-it**
you get a **list** of checked directions, each tagged with its move (ADD / FINISH / REBUILD /
REFACTOR). See the whole list at once — so you can order and relate the items — then decide each,
**scaling depth to the move** (Phase 0). One decision per item; the list is only the wrapper.
Phases 0–3 describe deciding ONE item; **Phase 4** says how the list flows out to the build.

The engine is _structured disagreement_. Four proposers each argue a fixed corner of the
decision space and **pull hard in their own direction** — they never compromise. They are then
grilled against each other. Objectivity lives in exactly ONE place: the final synthesis.
Anywhere else a "balanced" voice is a bug — four balanced voices collapse to the same mush and
leave nothing to decide.

**Core invariants — non-negotiable:**

- **Proposers stay partisan.** No pole is ever asked to "be objective" or "weigh both sides."
  That is synthesis's job, and only synthesis's.
- **Convergence must be earned, not instructed.** Agreement that _survives_ the grilling is
  signal; agreement _imposed_ by a "be balanced" prompt is noise.
- **Depth scales to stakes.** The full grill is for irreversible/expensive decisions. Cheap,
  reversible ones take the fast path — or grill-it doesn't run at all.
- **Synthesis is load-bearing.** All decision quality lives there. It scores against explicit
  criteria and carries its assumptions forward; it never just "picks the nicest essay."

**Grounding precondition (the gate).** Before anything else, confirm the product is grounded: look
for a `## Product North Star` heading in the repo-root `CLAUDE.md` (the heading is the stable
contract — its marker comment / parenthetical owner may read `point-it` or `chart-it`, both count).
**Absent → stop and route to `/chart-it`:** _"No North Star yet — this product has no captured goal,
and ccharness builds from the goal outward. Run `/chart-it` to set it (it captures the North Star,
then offers to chart the roadmap), then re-issue this command. Your prompt isn't discarded — re-issue
it after `/chart-it`."_ grill-it leans on the North Star's **Level** to set its depth (Phase 0), so
it does not run ungrounded.

---

## The compass

```
                 N · Final / Robust
          "build the version that survives prod & 10×"
                          │
  W · Conventional ───────┼─────── E · Contrarian
  "reuse, boring, proven, │    "question the framing,
   matches the codebase"  │     the non-obvious approach"
                          │
                 S · MVP / Minimal
          "smallest thing that delivers the core value"
                          │
                   CENTRE · synthesis
```

Two **orthogonal** axes: **N–S = how much we invest now** (scope/maturity); **W–E = how we
approach it** (convention vs invention). Keep them clean — each pole pulls on its own axis
only. S argues _less_, not _boring_. W argues _proven_, not _small_. If a pole drifts onto the
other axis you have lost the orthogonality that makes the four genuinely distinct.

---

## Phase 0 — Triage (frame + pick depth)

**If you were handed a list** (from point-it), split it by move first: **ADD / REBUILD** are the
*heavy* items — each gets its own full triage below. **FINISH / REFACTOR** are the *light* items —
group them and give the group one quick pass, not four-proposer grilling. Decide the heavy items
individually; clear the light group together. Then, per item:

Before spawning anyone, do two things:

1. **Frame the decision in one sentence**, and write the **synthesis criteria** — what "best"
   means _for this specific decision_ (e.g. "lowest time-to-first-working" vs "lowest 12-month
   maintenance"). Synthesis scores against these; derive them from the task, don't default them.
2. **Classify the door** (after Bezos):

| Door                                          | Path           | What runs                                                                                                                     |
| --------------------------------------------- | -------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **Reversible & low-stakes** (most tasks)      | **Fast path**  | Skip the compass. Produce ONE direct proposal, take it to the human. The full grill is the expensive case, never the default. |
| **Material stakes, reversible**               | **Compass**    | Phase 1 + Synthesis. No cross-examination.                                                                                    |
| **Irreversible / expensive / hard to unwind** | **Full grill** | Phase 1 + Phase 2 + Synthesis.                                                                                                |

**Seed the door from the move.** A point-it tag is a depth prior — let the move set the *default*
door, then let the stakes-test above refine it:

| Move                      | Default door             | Why                                                                                          |
| ------------------------- | ------------------------ | -------------------------------------------------------------------------------------------- |
| **ADD** / **REBUILD**     | **Compass → Full grill** | reshapes or extends the product — materially different options, real forks; grill it properly |
| **FINISH** / **REFACTOR** | **Fast path → light**    | closes a debt with a usually-obvious best way — analyse it, don't grill it                    |

The prior is not a cage: a FINISH hiding a real fork (two genuinely different ways to finish) can
climb to the compass; an obvious ADD can drop to the fast path. **Level** (from the North Star)
pushes the same way — a REBUILD in production earns more depth than one in a prototype.

If the task is actually unambiguous with no fork → say so and hand it straight to
`ccharness:implement-it` (the funnel's build stage). It doesn't need a decision loop, it just
needs building.

---

## Phase 1 — Compass (4 partisan proposers, parallel)

Dispatch four subagents in parallel, one per pole. Hand each the framed decision and its pole's
mandate. **Each proposer runs this internal pipeline before answering:**

1. **Propose** the strongest plan under its locked stance.
2. **Self-attack** — find where _this concrete proposal_ breaks (failure modes, hidden
   assumptions, cost). Attack the _execution_, never the stance itself.
3. **Repair** — strengthen it.
4. **Emit** the contract below.

**Pole mandates:**

- **N — Final/Robust:** the version you'd be unashamed of in prod at 10× load. Ask _"what breaks
  in six months?"_ Sacrifices speed and present-day simplicity.
- **S — MVP/Minimal:** the smallest thing that delivers the core value. Ask _"what's the least
  that actually works?"_ May challenge whether to do it at all. Sacrifices completeness and robustness.
- **W — Conventional:** reuse existing patterns, boring proven tech, match the codebase. Ask
  _"how is this already solved? what do we reuse?"_ Sacrifices novelty and case-specific optimality.
- **E — Contrarian:** question the framing; find the non-obvious or inverted approach. Ask
  _"what if the obvious solution is wrong, or unnecessary?"_ Sacrifices predictability and safety.

**Proposer output contract:**

```
pole:          N | S | W | E
conviction:    high | medium | low     # low = "this axis doesn't bite for this task" — say so
approach:      <concrete plan sketch under this stance>
core_bet:      <the central wager / what it optimizes>
assumptions:   [ { claim, confidence: 0–1 } ]
sacrifices:    <what it deliberately gives up>
weakest_point: <where this is most vulnerable — honest; it is reused downstream>
cost:          <rough effort / complexity>
```

**The low-conviction valve — this is what makes "always 4" safe.** If a pole has no real case
for this task (a bugfix has no genuine MVP-vs-Final tension), it must say so via `conviction:
low` and stop — **NOT fabricate an argument to justify its existence.** A confident argument on
a non-issue is exactly the "too-strong argument" failure mode. Synthesis reads uniformly-low
conviction on an axis as "no tension here" and weights it out.

---

## Phase 2 — The grilling (full grill only, parallel)

Hand each pole its **opposite's** Phase-1 output — N↔S, W↔E. The opposite is the sharpest
counter on that axis. The pole **stays partisan** — it is not switching sides or balancing.
It emits:

```
pole: …    vs: <opposite>
attack:    <hit the opposite's weakest_point>
defense:   <rebut the opposite's implied critique of me>
ledger:
  conceded: [ <points I now grant my opposite> ]
  held:     [ { point, why_i_hold } ]
refined_approach: <my plan, battle-tested — still partisan>
```

**The ledger is the prize.** A point a pole _concedes to its opposite under pressure_ is robust
— even the maximalist granted it. A point _held_ against the opposite is a live decision axis
the human will rule on. This — not a "balanced final opinion" — is what grilling the poles buys.

---

## Phase 3 — Synthesis (the one objective step)

One neutral pass (you, in the main thread). Inputs: the refined poles + (if Phase 2 ran) the
four ledgers. Do NOT pick the nicest proposal — **construct** the decision:

1. **Robust core** = points poles converged on _through the grilling_ (mutual concessions). High
   confidence; these go in.
2. **Live axes** = points held in disagreement. These are the real choices.
3. **Score** the surviving alternatives against the Phase-0 criteria. Weight out any axis where
   conviction was uniformly low.
4. **Decide** — pick the point on the compass and justify _why it beat the named alternatives_.
5. **Guard rights:** if every pole is weak, or they all attack the same framing → **reframe**
   and restart Phase 0. If there is no real difference → **collapse** to one proposal. Synthesis
   is allowed to refuse to choose between four bad options.

**Synthesis output contract:**

```
decision:            <chosen direction + plan sketch>
robust_core:         [ <points that converged through the grilling> ]
beaten_alternatives: [ { alternative, why_not } ]
assumptions:         [ { claim, confidence, kill_signal } ]   # kill_signal = a FALSIFIABLE trip-condition: "a single export > 50k rows" or "the library buffers instead of streams" — NEVER "if it gets too big"
decision_axes:       [ { axis, options, recommendation } ]    # held disagreements — grill-it rules each; human can veto
framing:             ok | reframe(<why>)
```

`assumptions[].kill_signal` is the **load-bearing field for not getting carried by the wind.**
During the build, reality is re-checked against these — so each one must be _falsifiable_: a
condition a fresh reader could confirm true or false by looking, never a vibe. A vague kill_signal
can't be checked and protects nothing; a sharp one ("the library buffers instead of streams")
catches the drift the moment it surfaces. This is why Phase 4 persists them to disk.

Keep `decision`'s plan sketch **thin** — _what_ approach won and _why_. The ordered build
checklist (and any written plan) is **implement-it's** Stage 1, not synthesis's job: grill-it
decides the direction, implement-it plans and builds it. Don't do its work here.

---

## Phase 4 — Hand off to build (flow through, veto-able)

The human's directional choice already happened upstream — the pick(s) that opened this
decision. So grill-it does **not** stop for a fresh approval. It **resolves every open axis
itself** and flows the decided, fork-free approach straight into the build.

**For one item** (a standalone fork, or one entry of a list), in one pass:

1. **Persist the decision record** to `.claude/ccharness/decisions/<slug>.md` — the synthesis
   contract verbatim (`decision`, `robust_core`, `assumptions` + their `kill_signal`s,
   `beaten_alternatives`). This is the durable artifact the build re-checks against; it must
   outlive this context, because drift surfaces long after the decision scrolls out of view.
2. Present, tightly:
   - the **decision** and its one-line justification,
   - the **decision_axes** — each with _your_ ruling and why, recommendation first (you decide
     them; you do not hand the human a quiz to fill in),
   - the **assumptions** it rests on (each with its `kill_signal`).
3. Hand the decided approach to **`ccharness:implement-it`** (the funnel's build stage) by
   default, **without waiting** — and make the veto cheap and explicit, e.g.:
   _"Building this via implement-it unless you redirect — say so to change direction, or to stop
   at the decision."_

**For a list** (from point-it): first **order and relate** the items — rank order by default,
but pull dependencies earlier and fold any that overlap. Then walk the list, running the
per-item pass above for each: **one decision record, one implement-it hand-off, one veto line —
per item.** Heavy items (ADD/REBUILD) are decided individually; the light FINISH/REFACTOR group
is reasoned in one pass but still **fans out to a per-item build** so each lands as its own
commit. The cadence is **autonomous, veto-only** by default — the human curated the list by
checking boxes, so you don't re-ask between items; you build them in rank order and they
interrupt to redirect or stop any one. (5 checked boxes ⇒ up to 5 decisions ⇒ 5 local commits.)

The human rules by **interrupting**, not by being asked. On a redirect → fold their ruling into
Phase 0 and re-run only what changed. (Invoked standalone via `/grill-it` for just a decision?
The same veto is your stop — say so and grill-it ends at the decision instead of building.)

---

## Quick reference

`0` Triage — (list? split heavy ADD/REBUILD from light FINISH/REFACTOR) frame + criteria + pick
depth **seeded by move** (ADD/REBUILD grill properly · FINISH/REFACTOR light), fast path the floor ·
`1` Compass — 4 partisan poles, parallel, low-conviction valve · `2` Grill — opposites cross-examine, harvest
the ledger (full grill only) · `3` Synthesis — the one objective pass: robust core + live axes +
scored decision · `4` Hand off — per item: persist record, resolve axes, flow into implement-it (veto per item); a
**list** → order/relate, then one decision + one commit per item, autonomous veto-only.

**Invariant:** proposers pull, synthesis judges. A balanced proposer is a bug.
