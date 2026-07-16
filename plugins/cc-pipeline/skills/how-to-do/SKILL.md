---
name: how-to-do
description: "Use when a task carries a real fork — a technical or implementation decision with materially different options and no obvious winner — or when what-to-do hands over picked directions to work out how to build. Fans out four partisan subagents and synthesizes ONE buildable approach. A rigorous replacement for open-ended brainstorming."
argument-hint: "<the fork or question to work through>"
---

## Gate — this is an implementation fork

how-to-do works out **HOW to build something in code**. Confirm the task is that before spending
four poles:

- **Product direction** (what to build / where to go — not how) → `/what-to-do` or `/planner`.
- **Trivial & clear how** (one obvious way to implement) → straight to `cc-pipeline:do`.
- **A real implementation/architecture fork** — materially different ways to build it, no obvious
  winner → you're in the right place. Continue.

## The four poles

Two **orthogonal** axes. Keep each pole on its own axis — Speed argues *less now*, not *reuse*;
Reuse argues *proven/existing*, not *minimal*.

```
              Quality  ("survives prod & 10× — what breaks in 6 months?")
                 │
     Reuse ──────┼────── Build own
 ("already       │       ("off-the-shelf
  solved — what  │        won't fit — what
  do we reuse?") │        do we build?")
                 │
              Speed    ("least that ships the core, soonest")
```

- **Speed** — fastest path to something working. Sacrifices robustness/completeness.
- **Quality** — the version you'd run in prod at 10× load. Sacrifices speed/present simplicity.
- **Reuse** — existing libraries, existing code, proven patterns, match the codebase. Sacrifices
  case-specific optimality.
- **Build own** — bespoke, fit-to-purpose. Sacrifices predictability/speed.

---

## Step 1 — Frame the idea to build

State in one sentence **what is to be built** and the **decision that forks** it. Then write the
**criteria** — what "best" means *for this decision* (e.g. "lowest time-to-first-working" vs "lowest
12-month maintenance"). Derive them from the task; the synthesis (Step 4) scores against exactly
these. Handed a direction from `what-to-do`, this is that direction sharpened into a buildable
question.


## Step 2 — Fan out (four partisan subagents, parallel)

Dispatch four subagents in parallel, one per pole, each on the **`sonnet` model**. Hand each the
framed decision + its pole mandate. **Each runs internally before answering:** propose the strongest
plan under its locked stance → self-attack (where does *this* plan break?) → repair → emit:

```
pole:          Speed | Quality | Reuse | BuildOwn
conviction:    high | medium | low     # low = "this axis doesn't bite here" — say so, don't fake it
approach:      <concrete plan sketch under this stance>
core_bet:      <what it optimizes / the central wager>
sacrifices:    <what it deliberately gives up>
weakest_point: <where it's most vulnerable — honest; synthesis reuses it>
cost:          <rough effort / complexity>
```

## Step 3 — Cross-evaluate the opposite (second round)

Now the poles drop pure partisanship and get honest. Dispatch four subagents in parallel again, each
handed **its own proposal + its axis-opposite's** (Speed⟷Quality, Reuse⟷BuildOwn). Each weighs the
opposite squarely and returns its **real** read — this is where the debate actually happens, opposite
against opposite:

```
pole:           Speed | Quality | Reuse | BuildOwn
opposite:       <the opposing pole>
steelman:       <the opposite's strongest point, put fairly — not a strawman>
concede:        [ where the opposite is genuinely right for THIS task ]
hold:           [ where your stance still wins — grounded reason, not partisan reflex ]
real_position:  <your honest verdict now that you've weighed the opposite>
```

## Step 4 — Synthesize (aggregate all outputs)

One neutral pass, main thread, on your stronger model, over **all outputs — the partisan proposals
and the cross-evals**. Do **not** pick the nicest proposal — **construct** the decision:

1. **Robust core** — what the poles agree on. High confidence; goes in.
2. **Live axes** — where they genuinely disagree. These are the real choices.
3. **Score** the surviving alternatives against the Step-1 criteria; weight out any axis where
   conviction was uniformly low.
4. **Decide** one approach and say why it beat the named alternatives.

```
decision:            <chosen *how* + thin plan sketch>
robust_core:         [ <points that held across poles> ]
beaten_alternatives: [ { alternative, why_not } ]
assumptions:         [ { claim, confidence, kill_signal } ]   # kill_signal = FALSIFIABLE trip-condition ("the library buffers instead of streams"), never a vibe ("if it gets too big")
framing:             ok | reframe(<the *how* was mis-framed — redo Step 1>) | flag_to_human(<the picked direction itself looks wrong — stop, surface, do NOT build>)
```

Keep `decision`'s sketch **thin** — *what* approach won and *why*. The ordered build checklist is
`do`'s job, not synthesis's.