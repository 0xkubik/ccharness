---
name: what-to-do
description: "Use when you want to find product direction — surface where a product could go next as a ranked menu of moves (new features, finishing half-built work, rebuilding rough parts, paying down tech debt). Fans out four subagents and aggregates their output."
argument-hint: "[optional focus — or nothing to survey the whole product]"
---

## Gate — ground before you fan out

- **The roadmap** — `docs/ccharness/roadmap.md`. **Missing or no features yet → route to `/planner-brainstorm`**
  first (it grounds the feature list). Present → read the `## Features` **frontier** (first unchecked
  `[ ]`) as the steer.
- **The file list** — `git ls-files | xargs wc -l` (every tracked file with its line count). Shared
  ground handed to every lens. Then fan out.

## Step 1 — Fan out (four subagents, parallel)

Dispatch four subagents in parallel, one per move, each on the **`sonnet` model**. Give each: its
**move mandate**, the **North Star** (if any), the **frontier milestone** as *orienting steer, not a
gate*, and the **file list**. Each explores the repo **in its own lane** and returns candidates in the
contract below.

- **ADD** — new capability that advances the North Star. _"What's missing that moves us toward the
  vision?"_ Includes bigger directional bets, not just small features.
- **FINISH** — half-built things to carry to done. _"What did we start and not finish?"_ Stubs,
  dead-ends, partial flows, dangling TODOs.
- **REBUILD** — working things with a clearly better redo. _"What works but we now know how to do
  properly?"_ Must name the better way, not just "it's ugly."
- **REFACTOR** — structural debt slowing everything else. _"Where is the mess expensive?"_ Real
  drag only, not cosmetic nits.

**Each lens returns** (0–N candidates):

```
move:          ADD | FINISH | REBUILD | REFACTOR
candidates:    [ {
  title:         <short name>
  what:          <1–2 sentences: the concrete move>
  why_now:       <how it closes the gap to the North Star>
  goal_fit:      high | med | low
  effort:        S | M | L
  reversibility: easy | hard
  advances:      <frontier feature it advances | "off-roadmap">   # only if a roadmap exists
} ]
empty_reason:  <if candidates == [] : why this lane has nothing real here>
```

## Step 2 — Aggregate → the menu

One pass, main thread. Collect all candidates, then **dedupe/merge** overlaps (a FINISH and a
REBUILD on the same thing collapse to one) → **score** on goal-fit × effort, weighing reversibility
more if the product is **live** (pre-production → carte blanche) → **rank** into one ordered menu.
Roadmap-fit is a bias: advancing the frontier boosts, **off-roadmap is never dropped.** Drop nothing
silently — if a strong candidate ranks low from production-caution or roadmap-fit, keep it and say why.

```
rank:      <n>
move:      ADD | FINISH | REBUILD | REFACTOR
title:     <direction>
what:      <1–2 sentences>
why_now:   <gap it closes toward the North Star>
score:     goal_fit / effort / reversibility  (+ any adjustment that moved the rank)
```