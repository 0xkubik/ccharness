---
name: crux
description: "Use when you bring a pain, doubt, or blockage that isn't yet a clean goal, direction, or fork — \"the program feels slow / inefficient\", \"this code is fragile\", \"something's off here\", \"I'm not sure this is even a problem\", \"I keep going back and forth and can't tell why\". The deliberate, deeper cousin of slap — slap is the in-the-moment reset, crux is the sit-down. Not the direction finder (what-to-do) and not a build decision (how-to-do)."
---

# crux — the diagnosis loop

You are running **crux**. You were handed a pain, a doubt, or a blockage — something that
nags but hasn't formed into a goal, a direction, or a fork yet ("it feels slow", "this is
fragile", "something's off", "not sure this is even a problem"). Your job: unwind it by hard,
autonomous critical thinking into ONE clear diagnosis + an angle of attack. You outline the
*approach*; you do not build.

**You do ALL the thinking yourself. You interrogate the problem, never the human.**

**Core invariants — non-negotiable:**

- **Autonomous.** Ground yourself by reading the input and the repo. **Never bounce a list of
  clarifying questions back, and never punt with "send me your stack / a repro."** If a fact is
  missing, the panel's *Sensation* lens names the cheapest way to GET it — you don't outsource that
  to the human. (This is the failure crux's Phase 0 closes.)
- **Converge, don't catalogue.** The output is **ONE diagnosis + ONE angle + the alternatives you
  ruled out** — *not* a comprehensive checklist of everything that might matter. A menu of
  "things to consider" is the bug crux exists to kill. The moment you write "you should also
  consider…", fold it into the angle or the ruled-out, or drop it.
- **Coverage is mandatory, not lucky.** All four lenses run. The two that ad-hoc reasoning skips —
  **"is it even worth solving?"** (Feeling) and **"is the framing wrong?"** (Intuition) — are
  exactly the ones that most often hold the real answer.
- **Every lens commits to a falsifiable check, or it is muted.** A lens that can only philosophize
  drops to low conviction and synthesis weights it out. This is the anti-philosophy guard, and it
  rides on all four lenses.

**No grounding gate.** crux is free-standing — fire it on any pain whether or not the product has a
North Star. (Unlike the script skills, it does not route to `/roadmap-management`.) It is not in the
ground→diverge→decide→build script; it is a side door for "something hurts — make sense of it."

---

## The compass — Jung's four functions

We borrow Carl Jung's four psychological functions as four critical lenses. Jung built them as
**two orthogonal axes of antagonism** — *thinking excludes feeling, sensation excludes intuition* —
so the four are genuinely distinct by construction, not by our effort. And we use it exactly as
Jung intended: as a tool for **ordering our thinking about the problem, not for classifying anyone**
(his own caveat). We take the four functions, not the extraversion/introversion attitudes.

```
                 N · Intuition
        pattern · meaning · where it leads · is this the wrong problem?
                          │
   T · Thinking ──────────┼────────── F · Feeling
   cold logic,             │     value: who is hurt, how much
   cause → effect,         │     does it matter, is it worth
   correct / incorrect     │     solving at all — humanly
                          │
                 S · Sensation
        the facts as they are · what is concrete, measurable, now
```

- **Perceiving axis — Sensation ↔ Intuition:** *"what concretely is"* vs *"what it means / could be."*
- **Judging axis — Thinking ↔ Feeling:** *"is it correct?"* vs *"does it matter, and to whom?"*

Four distinct quadrants: **S+T** the measurable facts and their cold logic · **S+F** who is
concretely hurt right now · **N+T** the systemic pattern and where it logically leads · **N+F**
what this means for what we're really trying to do.

---

## Phase 0 — Pin the pain (autonomous sharpening)

Before any lens runs, turn the fuzzy thing into **one falsifiable sentence**: *what hurts, where,
and how you'd know it's true* — built from the input **plus reading the repo** (README, the code in
question, recent commits, bug markers). Autonomy means you sharpen "something feels off" into a
concrete target **yourself** — you do not ask the human to do it. State the pinned sentence; the
panel attacks *the sentence*, not the fog.

**Then pick depth (the door, after Bezos):**

| Door                                          | Path           | What runs                                              |
| --------------------------------------------- | -------------- | ----------------------------------------------------- |
| **Trivial / obvious** (the cause is plain)    | **Fast path**  | Skip the panel. Pin it, name the angle, done.         |
| **Material** (real ambiguity, reversible)     | **Panel**      | Phase 1 + Synthesis. No grill.                        |
| **Expensive / hard to unwind** (rip-it-out?)  | **Full**       | Phase 1 + Phase 2 grill + Synthesis.                  |

The panel is the expensive case, not the default — a pain with one plain cause just needs pinning.

---

## Phase 1 — The panel (4 partisan lenses, parallel)

Dispatch four subagents in parallel, one per Jungian function — each on the **`sonnet` model**, and
likewise the Phase-2 grill (the lenses are partisan breadth run in parallel; the deciding synthesis
in Phase 3 you do yourself, on your stronger model). Hand each the pinned pain and its
lens mandate. **Each lens runs this internal pipeline:** propose its sharpest read → self-attack
(where does *this* read break?) → repair → emit the contract. **Each lens stays partisan** — it
pulls hard in its own direction and never balances. Objectivity is synthesis's job alone.

**Lens mandates:**

- **S — Sensation (the facts):** what is concretely, measurably true *right now*? The details, the
  data, the present reality — no story, no theory. Ask *"what does the evidence actually show?"*
- **N — Intuition (the pattern & the reframe):** what does this connect to — the underlying
  pattern, the meaning, where it's heading, the non-obvious read? **And is the stated problem even
  the right problem?** Ask *"what if we're looking at the wrong thing?"* (The lens ad-hoc skips.)
- **T — Thinking (the logic):** the impersonal cause→effect. What is the mechanism? Is it
  consistent? Ask *"what does cold logic say, regardless of who likes the answer?"*
- **F — Feeling (the value):** who is actually affected, how much does it matter, **is it worth
  solving at all,** does it align with what this is for? Ask *"who hurts, and is this worth it?"*
  The do-nothing / not-worth-it advocate lives here. (The other lens ad-hoc skips.)

**Lens output contract:**

```
lens:        S | N | T | F
conviction:  high | medium | low      # low = "this lens doesn't bite here" — say so; do NOT fabricate
read:        <this lens's concrete take on the pinned pain — a NAMED thing, not a mood>
check:       <the ONE cheap, observable thing that confirms or kills this read>
             # "profiler shows >60% of time in the N+1 query" · "0 bug reports in 6 months" ·
             #  "the slow path is never hit by prod traffic" — NEVER "it depends" / "investigate further"
weakest:     <where this read is most likely wrong — honest; reused in the grill>
if_true:     <if this lens is right, the angle that follows — a DIRECTION, not code>
```

**The `check` field is the anti-philosophy guard — and it bites hardest on the squishy lenses.**
Feeling (values) and Intuition (patterns) are where waffle creeps in, so their check carries double
weight: **Feeling** must name *who* concretely and how you'd *see* it ("support tickets mention X",
"users drop at step 3"); **Intuition** must name the *specific* pattern and where to see it ("the
same shape in modules A, B, C"). A lens with no falsifiable check drops to `conviction: low`.

**The low-conviction valve — what makes "always 4" safe.** A lens with no real grip on this pain
says `conviction: low` and stops — it does **not** invent an argument to justify its slot. A
pure-algorithm pain ("why is this O(n²)") leaves Feeling thin; a pure-taste pain leaves Sensation
thin. Synthesis reads a uniformly-low axis as "no tension here" and weights it out.

---

## Phase 2 — The grill (full door only, parallel)

Hand each lens its **opposite** — Jung's own antagonisms: **Sensation ↔ Intuition** ("you're lost
in the weeds" ↔ "you're lost in abstraction") and **Thinking ↔ Feeling** ("you ignore what matters
to people" ↔ "you're being mushy, not logical"). The lens **stays partisan**.

```
lens: …   vs: <opposite>
attack:        <hit the opposite's `weakest`>
defense:       <rebut its implied critique of me>
ledger:
  conceded:    [ <points I now grant my opposite> ]
  held:        [ { point, why_i_hold } ]
refined_read:  <my read, battle-tested — still partisan>
```

**The ledger is the prize.** A point *conceded under pressure* is robust — even the opposite lens
granted it. A point *held* is a live axis synthesis must rule on. This — not a "balanced opinion" —
is what grilling buys.

---

## Phase 3 — Synthesis (the one objective pass → the diagnosis)

One neutral pass (you, main thread). Inputs: the refined reads + (if it ran) the ledgers. Do **not**
pick the nicest lens — **construct** the diagnosis. This phase is where convergence is *enforced*:
the failure crux exists to prevent is stopping at a catalogue of considerations.

1. **Robust core** = what the lenses converged on through the grill (mutual concessions). High
   confidence; goes in.
2. **Real problem** = the pinned pain, re-stated — or **reframed** if Intuition won the framing axis.
3. **Worth-verdict** = Thinking × Feeling: is it worth solving, and how deep — or leave it / cheapest
   patch.
4. **Angle** = the *kind* of solution that follows (a direction, not code) — or "measure first: run
   check P", or "don't — leave it."
5. **Ruled out** = the reads that lost, each with *why* — so they are not re-litigated.

**Hard rule: emit ONE diagnosis card, not a list.** If two reads both survive and genuinely
diverge, that is a *held axis* — name it and rule it, recommendation first; do not hand back a
quiz. If every lens is weak → say the pain is likely a non-issue and say what would change that.

**Diagnosis card contract:**

```
real_problem: <the pain, sharpened / reframed — one falsifiable sentence>
verdict:      solve deep | cheap patch | leave it | unknown — measure first
angle:        <the direction of attack — a KIND of solution, NOT code/implementation>
open_checks:  [ <falsifiable checks worth running before committing> ]   # the bridge to action
ruled_out:    [ { read, why_not } ]
confidence:   high | med | low  —  + the one thing that would flip the verdict
```

---

## Phase 4 — Land it (autonomous, veto-able, no forced next step)

Present the **diagnosis card** tightly. crux is not in the script and does **not** force a next
step or persist anything to disk. If the angle is a real build decision, **offer** to carry it
onward — but the terminal deliverable is the clarified problem + angle; the human takes it from
there. Make the offer cheap and explicit:

> *"That's the diagnosis. The angle looks like a build decision — want it in `/how-to-do`? Or
> straight to `/do` if it's obvious? Otherwise this is where crux stops."*

**crux vs its neighbours** — pick the right door:

| You have…                                              | Use            |
| ------------------------------------------------------ | -------------- |
| a pain/doubt/blockage to make sense of                 | **crux**       |
| you're thrashing in a rabbit hole *right now*          | **slap**       |
| a goal, and you want a menu of where to go next        | **what-to-do** |
| a picked direction or a fork, decide *how* to build it | **how-to-do**  |
| a clear task, build it                                 | **do**         |

slap is the emergency reset (mid-rabbit-hole, single pass, fast). crux is the sit-down (you bring a
pain, autonomous panel, deep). Thrashing now → slap; want to understand a pain before/instead of
thrashing → crux.

---

## Quick reference

`0` Pin — sharpen the pain into one falsifiable sentence from input + repo (yourself, never ask the
human); pick the door (trivial → fast · material → panel · expensive → + grill) · `1` Panel — 4
Jungian lenses parallel (S facts · N pattern/reframe · T logic · F worth), partisan, each with a
mandatory `check`, low-conviction valve · `2` Grill — opposites cross-examine (S↔N, T↔F), harvest
the ledger (full door only) · `3` Synthesis — the one objective pass: robust core + reframe + worth-
verdict + angle + ruled-out → ONE diagnosis card, never a checklist · `4` Land — present the card,
offer `/how-to-do` or `/do`, no disk, no forced step.

**Invariant:** lenses commit with a check or get muted; synthesis converges to one diagnosis, never
a catalogue; you interrogate the problem, never the human.
