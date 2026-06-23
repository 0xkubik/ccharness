---
name: chart-it
description: Use when setting up or revising a product's long-horizon direction — the grounding loop. Captures the product's North Star (goal-setting / целеполагание) into CLAUDE.md, then charts a layered roadmap of lightweight milestones (ordered stages, parallel milestones within each) from where the product is now to that goal. Invoked by /chart-it. Run once up front (every other product skill routes here when no North Star exists); re-run to revise as the route drifts. The roadmap then biases point-it's ranking toward the current frontier (the parallel milestones open now). Not for deciding a fork (grill-it) or building a task (implement-it).
---

# chart-it — the grounding loop

You are running **chart-it**: the harness's **grounding front door**. You do two things, in order —
capture the product's **North Star** (the goal — *целеполагание*), then chart the **roadmap** (the
layered route to it). The whole funnel depends on the North Star existing; when it is missing,
every other product skill sends the human **here**.

```
 chart-it   (GROUND — set the goal, then chart the route)
   │  writes North Star → CLAUDE.md   +   roadmap → .claude/ccharness/roadmap.md
   ▼
 point-it ──► grill-it ──► implement-it        (+ slap = tactical reset)
 DIVERGE       DECIDE        BUILD
   ▲ every product skill: no North Star → routes back here
   ▲ point-it additionally reads the roadmap and biases its menu toward the CURRENT FRONTIER

 North Star = WHERE TO (the goal) · roadmap = BY WHICH ROUTE · point-it = WHICH NEXT STEP
```

The roadmap is **layered**: a sequence of **stages** that run in order, with one or more
**milestones inside each stage that are parallel** (no order between them). The single rule that
shapes it: **need "A before B" → put them in different stages; independent → same stage.** This is
what lets the route show real structure — what blocks what, what can go at once — instead of forcing
everything onto one line. (A roadmap with *no* stage headings is just the degenerate case: a plain
line, each milestone its own stage — its **frontier-tracking** is exactly the old linear roadmap;
only autopilot's give-up ladder runs stricter without stages.)

**Core invariants — non-negotiable:**

- **chart-it OWNS the North Star write.** The `## Product North Star` block (heading + marker +
  fields) is a **shared contract** every other skill detects. You produce it; they only read it. A
  generic helper won't reliably reproduce the exact block — own this write.
- **North Star is mandatory; the roadmap is optional-but-encouraged.** After capturing the star,
  **offer** the roadmap — never force it. Someone bounced here for a one-off task can take just the
  star and leave; the star alone satisfies the gate for every other skill.
- **Milestones are lightweight.** Each carries a **stable global id** (`M1`, `M2`, …) and is `name +
  done when: <observable outcome> + theme: <one line>` — **no frozen task list.** point-it derives
  the concrete moves fresh each run; you only fix the *stages, the sequence, and the outcomes*. Ids
  stay stable across re-runs (semipilot/autopilot reference them) and are independent of which stage a
  milestone sits in.
- **The roadmap is layered; the FRONTIER replaces the single pointer.** Milestones group into
  ordered `## Stage N` bands; milestones within a stage are parallel. The **frontier** = the
  unchecked `[ ]` milestones of the **earliest stage that still has any unchecked milestone**; a
  stage opens only once the one before it is fully `[x]`. The frontier is **derived from checkboxes —
  one source of truth, no separate pointer** (same invariant as before, just a *set* not a single
  box). Milestones are written **in document order** = a valid sequential walk (stage 1's, then stage
  2's, …), so "first unchecked in document order" is still a well-defined single milestone for the
  loops that take one at a time. **No stage headings = legacy line** = each milestone its own stage =
  frontier is always exactly the first unchecked box (old behaviour, unchanged).
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

This is where the project gets thought through **far ahead**. Propose a **draft layered route** —
milestones grouped into ordered **stages** — from *now* → ★, then work through it **with the human,
one decision at a time**. The governing question at every step: **does this need to come before that
(→ separate stages), or are they independent (→ same stage, parallel)?**

- Is the **stage sequence** right — does each stage genuinely unlock the next?
- Within a stage, are the milestones **truly independent** — can they really be done in any order, or
  in parallel? If one secretly needs another, split them into two stages. (This is what later lets
  autopilot treat same-stage milestones as safe to reorder/park.)
- Is the **granularity** right — split a milestone that hides two outcomes, merge two that are really
  one; split a stage that bundles a real dependency, merge two stages that have no order between them.
- What is the **current stage** (the earliest with unfinished work) and its **frontier**?
- Reorder anything mis-staged; drop anything that doesn't serve the North Star.

Iterate until the human is satisfied. Give each milestone a **stable id** and land it as `id — name ·
done when: <observable outcome> · theme: <one line>`. The `done when:` must be **observable** (a state
the repo/product reaches) — that's what later lets point-it judge whether a frontier milestone is
complete. When the product really *is* linear, one milestone per stage is fine — don't manufacture
parallelism that isn't there (YAGNI); layering earns its keep only where work genuinely forks.

---

## Phase 3 — Write the roadmap

Write `.claude/ccharness/roadmap.md` (create the directory if needed) in the **layered format
below**, confirm in one line, then **stop**. Stages are `## Stage N` headings; milestones are
checkboxes under them, listed in document order (stage 1's first). The `← current` marker is only a
reader's hint — the **authoritative** current stage is always *derived*: the earliest stage with an
unchecked box.

```markdown
# Roadmap — <product>
<!-- managed by chart-it · edit freely, chart-it re-reads this · captured: <YYYY-MM-DD> · North Star → CLAUDE.md -->
<!-- LAYERED: stages run in order; milestones inside a stage are parallel (any order). -->
<!-- Frontier = unchecked milestones of the earliest stage that still has any. No stage headings = legacy line. -->

## Stage 1 — <theme>            ← current (earliest stage with unchecked work)
- [ ] M1 — <name> · done when: <observable outcome> · theme: <one line>

## Stage 2 — <theme>            (parallel — any order within the stage)
- [ ] M2 — <name> · done when: <observable outcome> · theme: <one line>
- [ ] M3 — <name> · done when: <observable outcome> · theme: <one line>

## Stage 3 — <theme>
- [ ] M4 — <name> · done when: <observable outcome> · theme: <one line>
```

(A genuinely linear product collapses to one milestone per stage — or simply omit the stage headings
for the legacy plain list; both track the frontier identically to the old sequential roadmap.)

---

## Re-run = revise (the roadmap is a living artifact)

chart-it is normally run **once**, but a roadmap drifts. A re-run:

1. **Re-survey** the current product (Phase 1 again).
2. **Show the roadmap + progress** — which milestones' `done when:` now hold, and where the
   **frontier** sits (it advances to the next stage only once the current stage is fully `[x]`).
3. **Propose adjustments** — check off completed milestones, add / split / reorder milestones **and
   stages**, move a milestone between stages, drop the obsolete — one decision at a time. Keep ids
   stable; only the loops' downstream state references them.
4. **Rewrite** `roadmap.md`.

This is the analog of `--reground` for the North Star: re-running is the supported way to keep the
route honest as reality moves.

---

## Quick reference

`0` Goal-setting — detect `## Product North Star`; absent → 3-question dialogue → **write the block
yourself** → offer the roadmap (don't force) · `1` Survey — repo = where we are now · `2` Decompose —
draft **layered** route now→★ (stages in order, parallel milestones within: *order → split stages,
independent → same stage*), refine one decision at a time (lightweight: id + name + `done when` +
theme) · `3` Write — `.claude/ccharness/roadmap.md` in the `## Stage N` format, frontier = earliest
open stage, stop · re-run = revise the living roadmap (advance the frontier as stages complete).

**Invariant:** chart-it owns the North Star write and charts the route; it never decides a fork
(grill-it) or builds a task (implement-it). The roadmap only *biases* point-it — it never gates it.
