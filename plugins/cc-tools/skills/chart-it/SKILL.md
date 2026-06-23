---
name: chart-it
description: Use when setting up or revising a product's long-horizon direction — the grounding loop. Captures the product's North Star (goal-setting / целеполагание) into CLAUDE.md, then charts a sequenced roadmap of lightweight milestones from where the product is now to that goal. Invoked by /chart-it. Run once up front (every other product skill routes here when no North Star exists); re-run to revise as the route drifts. The roadmap then biases point-it's ranking toward the current milestone. Not for deciding a fork (grill-it) or building a task (implement-it).
---

# chart-it — the grounding loop

You are running **chart-it**: the harness's **grounding front door**. You do two things, in order —
capture the product's **North Star** (the goal — *целеполагание*), then chart the **roadmap** (the
sequenced route to it). The whole funnel depends on the North Star existing; when it is missing,
every other product skill sends the human **here**.

```
 chart-it   (GROUND — set the goal, then chart the route)
   │  writes North Star → CLAUDE.md   +   roadmap → .claude/ccharness/roadmap.md
   ▼
 point-it ──► grill-it ──► implement-it        (+ slap = tactical reset)
 DIVERGE       DECIDE        BUILD
   ▲ every product skill: no North Star → routes back here
   ▲ point-it additionally reads the roadmap and biases its menu toward the CURRENT milestone

 North Star = WHERE TO (the goal) · roadmap = BY WHICH ROUTE · point-it = WHICH NEXT STEP
```

**Core invariants — non-negotiable:**

- **chart-it OWNS the North Star write.** The `## Product North Star` block (heading + marker +
  fields) is a **shared contract** every other skill detects. You produce it; they only read it. A
  generic helper won't reliably reproduce the exact block — own this write.
- **North Star is mandatory; the roadmap is optional-but-encouraged.** After capturing the star,
  **offer** the roadmap — never force it. Someone bounced here for a one-off task can take just the
  star and leave; the star alone satisfies the gate for every other skill.
- **Milestones are lightweight.** Each is `name + done when: <observable outcome> + theme: <one
  line>` — **no frozen task list.** point-it derives the concrete moves fresh each run; you only fix
  the *sequence and the outcomes*.
- **The roadmap is sequential.** Current milestone = **first unchecked box**. One source of truth —
  no separate pointer.
- **Collaborate, one decision at a time** (borrow `superpowers:brainstorming`'s technique). The
  terminal is `CLAUDE.md` + `roadmap.md` — **NOT** `writing-plans`.

---

## Phase 0 — Goal-setting (the North Star)

**North Star detection.** Look for a `## Product North Star` heading in the repo-root `CLAUDE.md`.
The **heading** is the stable contract — its marker comment / parenthetical owner may read `point-it`
or `chart-it`, both count.

| State | Path |
| --- | --- |
| **Present** | Read it = the goal. Offer `--reground` to revise (re-run the interview, overwrite the block). Then continue to the roadmap offer below. |
| **Absent** | Run the goal-setting dialogue, then **write the block yourself** (below). |
| **`--reground` requested** | Re-run the interview, overwrite the block (preserving the rest of `CLAUDE.md`), continue. |

**The goal-setting dialogue.** Borrow `superpowers:brainstorming`'s technique — one question at a
time, plain language — but **keep it able to be a fast 3-answer capture**: someone bounced here from
`/implement-it` for a one-off shouldn't face a long dialogue before their task. Ask for exactly these
three, one at a time:

1. **Vision** — a few sentences: what the finished product looks like at the end.
2. **Core problem** — the main problem this product solves.
3. **Level** — `1` no production · `2` production exists / is coming · `3` already in production.

You *may* go deeper collaboratively (objectives, who it's for, what success looks like) — that
richness feeds the roadmap in Phase 2 — but the **durable artifact is the stable 3-field block**.
Then write it, appending to the project-root `CLAUDE.md` and **preserving everything already there**:

```markdown
## Product North Star (cc-tools)
<!-- managed by chart-it · edit freely, the harness re-reads this · captured: <YYYY-MM-DD> -->
- **Vision:** <a few sentences — how the finished product looks at the end>
- **Core problem:** <the main problem the product solves>
- **Level:** <1 — no production · 2 — production exists/coming · 3 — already in production>
```

Confirm the written block back in one line.

**Then offer the roadmap — don't force it:**

> "North Star captured. Want me to chart the **roadmap** now — the milestone route from here to that
> goal? (Or stop here and chart it later with `/chart-it`.)"

Decline → **stop** (the star alone is enough to unblock the rest of the harness). Accept — or chart-it
was run with a star *already present* — → continue to Phase 1.

---

## Phase 1 — Survey "now"

Build a short, factual picture of the **current** product from the repo: `README`, docs, recent
commits, `CHANGELOG`, scattered `TODO`/`FIXME`/stub markers. Two or three paragraphs, not an audit.
This is the **"now"**; the North Star is the **"end"**; the route runs between them — you need both
ends to chart it.

---

## Phase 2 — Collaborative decomposition (the heart)

This is where the project gets thought through **far ahead**. Propose a **draft sequence** of
lightweight milestones from *now* → ★, then work through it **with the human, one decision at a
time**:

- Is the **sequence** right — does each milestone unlock the next?
- Is the **granularity** right — split a milestone that hides two outcomes, merge two that are really
  one?
- What is the **true first milestone** (the current one)?
- Reorder anything that's mis-sequenced; drop anything that doesn't serve the North Star.

Iterate until the human is satisfied. Each milestone lands as `name + done when: <observable outcome>
+ theme: <one line>`. The `done when:` must be **observable** (a state the repo/product reaches) —
that's what later lets point-it judge whether the current milestone is complete.

---

## Phase 3 — Write the roadmap

Write `.claude/ccharness/roadmap.md` (create the directory if needed), first milestone **current**
(first unchecked), confirm in one line, then **stop**:

```markdown
# Roadmap — <product>
<!-- managed by chart-it · edit freely, chart-it re-reads this · captured: <YYYY-MM-DD> · North Star → CLAUDE.md -->

- [ ] M1 — <name> · done when: <observable outcome> · theme: <one line>   ← current (first unchecked)
- [ ] M2 — <name> · done when: <observable outcome> · theme: <one line>
- [ ] M3 — <name> · done when: <observable outcome> · theme: <one line>
```

---

## Re-run = revise (the roadmap is a living artifact)

chart-it is normally run **once**, but a roadmap drifts. A re-run:

1. **Re-survey** the current product (Phase 1 again).
2. **Show the roadmap + progress** — which milestones' `done when:` now hold.
3. **Propose adjustments** — check off completed milestones, add / split / reorder, drop the
   obsolete — and work them through one decision at a time.
4. **Rewrite** `roadmap.md`.

This is the analog of `--reground` for the North Star: re-running is the supported way to keep the
route honest as reality moves.

---

## Quick reference

`0` Goal-setting — detect `## Product North Star`; absent → 3-question dialogue → **write the block
yourself** → offer the roadmap (don't force) · `1` Survey — repo = where we are now · `2` Decompose —
draft milestone sequence now→★, refine with the human one decision at a time (lightweight: name +
`done when` + theme) · `3` Write — `.claude/ccharness/roadmap.md`, current = first unchecked, stop ·
re-run = revise the living roadmap.

**Invariant:** chart-it owns the North Star write and charts the route; it never decides a fork
(grill-it) or builds a task (implement-it). The roadmap only *biases* point-it — it never gates it.
