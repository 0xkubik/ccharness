# ccharness `/chart-it` — design

**Date:** 2026-06-23
**Status:** approved (brainstorming) → ready for implementation plan
**Plugin:** ccharness (v0.7.0 → adds an 8th command)

## Problem

The harness has a **destination** and a **next step**, but no explicit **route** between them.

- **North Star** (a managed block in `CLAUDE.md`) — the "end": vision · core problem · level. One
  captured point.
- **point-it's menu** — the "next step", *recomputed from scratch every run* out of the gap between
  "where we are now" (Survey) and the North Star.

There is nothing in between. point-it re-guesses the trajectory from the gap on every run, and no
persisted **sequence of milestones** exists. The user wants to sit down **once** and actively think
the project through **far ahead** with the assistant — produce a durable route — and then have
point-it **take that route into account** when it ranks moves.

```
         chart-it   ← writes/revises roadmap.md (the route: now → … → ★)
            │
            ▼  roadmap.md
 point-it ──► grill-it ──► implement-it
 DIVERGE       DECIDE        BUILD
    ▲ reads roadmap, biases ranking toward the CURRENT milestone

 North Star (CLAUDE.md) = WHERE TO · roadmap = BY WHICH ROUTE · point-it = WHICH NEXT STEP
```

`/chart-it` is **not a fourth funnel step**. It is a **second grounding artifact alongside the North
Star** — a thing point-it *reads*, not a stage in `diverge → decide → build`.

## Decisions (locked in brainstorming)

| # | Decision | Choice |
|---|---|---|
| 1 | How point-it consumes the roadmap | **Bias ranking** — a new scoring dimension; never a gate. Off-roadmap moves still surface, just rank lower. |
| 2 | Milestone weight | **Lightweight** — name + `done when …` outcome + one-line theme. No frozen task list; point-it derives concrete moves fresh each run. |
| 3 | Sequence shape | **Sequential** (M1→M2→M3), so "current milestone" is unambiguous. Not parallel tracks. |
| 4 | Storage | `.claude/ccharness/roadmap.md` — honours the existing convention that everything the plugin produces lives under `.claude/ccharness/` (alongside `autopilot/`, `decisions/`). |
| 5 | Git tracking | **Committed.** Narrow `.gitignore` so the roadmap is versioned/shared; runtime state stays ignored. |
| 6 | Current-milestone tracking | `[x]`/`[ ]` checkboxes only; **current = first unchecked**. One source of truth — no separate pointer. |
| 7 | Command name | `/chart-it` (chart a course by the star — in tone with the North Star metaphor). |

## The artifact — `.claude/ccharness/roadmap.md`

Lightweight, sequential milestones. One source of truth for "current" — the first unchecked box.

```markdown
# Roadmap — <product>
<!-- managed by chart-it · edit freely, chart-it re-reads this · captured: <YYYY-MM-DD> · North Star → CLAUDE.md -->

- [x] M1 — <name> · done when: <observable outcome> · theme: <one line>
- [ ] M2 — <name> · done when: <observable outcome> · theme: <one line>   ← current (first unchecked)
- [ ] M3 — <name> · done when: <observable outcome> · theme: <one line>
```

- **`done when:`** is an *observable* outcome (a state the repo/product reaches), not a task list —
  this is what lets point-it judge whether the current milestone is complete.
- **`theme:`** orients the Phase-2 lenses without freezing specific moves.
- **No `[▶]` / `current:` pointer.** Current is *derived* (first `[ ]`). A second marker would desync
  from the checkboxes.

## The new skill — `chart-it`

Borrows the *technique* of `point-it`'s bootstrap interview / `superpowers:brainstorming` — one
question at a time, plain language — but the terminal is **`roadmap.md`, not an implementation plan.**
Do NOT hand off to `writing-plans`.

- **Ph0 — Ground.** Requires a North Star block in `CLAUDE.md`. **Missing → stop and route to
  `/point-it`** (you cannot plan a route without a destination; chart-it plans the route *to* the
  star, it does **not** bootstrap the star — that is point-it's job). Present → read it; it is the
  endpoint.
- **Ph1 — Survey "now".** A short, factual picture of the *current* product from the repo (as
  point-it Ph1). The route spans now → ★, so chart-it needs both ends.
- **Ph2 — Collaborative decomposition (the heart).** chart-it proposes a *draft* sequence of
  lightweight milestones from now → ★, then works through it with the human **one decision at a
  time**: is the sequence right? the granularity? merge / split / reorder? what is the true first
  milestone? Iterates until the human is satisfied. This is where the project gets "thought through
  far ahead."
- **Ph3 — Write.** Writes `.claude/ccharness/roadmap.md` (owning the marker comment, like point-it
  owns the North Star block), confirms back in one line, and stops.

**Re-run = revise (living artifact).** chart-it is normally run once, but a roadmap drifts. A re-run:
re-surveys → shows the current roadmap + progress (which `done when`s now hold) → proposes
adjustments (check off completed, add/split/reorder, drop the obsolete) → rewrites. This is the
analog of point-it's `--reground` for the North Star. Re-running is the supported way to keep the
route honest as reality moves.

## Changes to point-it

Fully backward compatible: **no `roadmap.md` → point-it behaves exactly as today.** When absent it
may emit a one-line nudge ("no roadmap yet — `/chart-it` thinks the route through far ahead"), then
proceed unchanged.

- **Ph0 — Ground.** Additionally read `.claude/ccharness/roadmap.md` if present. Derive the current
  milestone (first unchecked).
- **Ph1 — Survey.** Check whether the **current milestone's `done when:`** already holds.
  - *Interactive:* offer to check it off (advancing current to the next milestone).
  - *Autopilot:* **auto-mark** it complete (point-it judged the outcome met) — no human to confirm
    mid-loop, and current must advance for the loop to walk the route. (See Autopilot below.)
- **Ph2 — Fan-out (now roadmap-aware).** Each of the four move-lenses additionally receives the
  **current (+ next) milestone** as *orienting context* — **not a gate.** The lenses still scan all
  four moves freely and still honour the empty-lane valve and may surface off-roadmap candidates;
  they now also actively look for material that advances the current milestone. *Rationale:* ranking
  can only reorder what the lenses produce. If the lenses are blind to the roadmap, the Ph3
  roadmap-fit boost acts on thin material and fails to steer. This is the scope-resizing fix — the
  roadmap must reach Ph2, not just Ph3.
- **Ph3 — Rank.** Add a scoring dimension **roadmap-fit**:
  - advances the **current** milestone → boost,
  - advances the **next** milestone → light boost,
  - off-roadmap → no boost, **but not hidden** (honest divergence preserved).
  - Menu entries tag the relevant milestone (e.g. `M2`); off-roadmap candidates are marked as such.
- **Invariant intact.** The menu still selects nothing — the roadmap only **reorders**. A menu that
  hides off-roadmap moves, or pre-picks a winner, is a bug.

## Autopilot

Near-free, no separate traversal logic. Autopilot auto-picks the top of the menu; because the
roadmap biases the top toward the current milestone, autopilot **naturally walks the route milestone
by milestone**. When a milestone's `done when:` is met, point-it (in autopilot mode) **auto-marks it
`[x]`**, current advances to the next `[ ]`, and the loop proceeds. The one autopilot-specific rule:
the check-off is **automatic, not a handback** — autopilot never waits for a human, so an interactive
"shall I check this off?" would stall it and current would never advance.

## Storage & git

- Roadmap → `.claude/ccharness/roadmap.md` (plugin-artifact convention).
- **`.gitignore`:** *replace* the current `.claude/ccharness/` line with:
  ```
  .claude/ccharness/*
  !.claude/ccharness/roadmap.md
  ```
  (The bare-directory form cannot be negated; the `/*` form ignores contents while allowing the
  roadmap to be re-included. Replace — do not leave both lines.) Result: `roadmap.md` is tracked;
  `autopilot/` and `decisions/` stay ignored.

## Documentation touchpoints (for the plan)

- **README:** funnel diagram, the commands table (add a `/chart-it` row), and the Layout section all
  need chart-it. Position it as a grounding companion to North Star, *before* the `point-it →
  grill-it → implement-it` flow conceptually.
- **`ccharness-init` dependency table: do NOT touch.** chart-it is **internal** to ccharness, not an
  external orchestrated plugin — it is not an install dependency.
- **`plugin.json`:** bump `version` 0.7.0 → 0.8.0 and extend the description with the 8th command.
- **point-it SKILL.md:** the Ph0/Ph1/Ph2/Ph3 edits above + Quick reference.

## YAGNI — explicitly out of scope

- **No drift-valve lens** in point-it (option-1 "bias", not option-3 "focus + drift valve").
- **Milestones carry no frozen task list** (lightweight outcome + theme only).
- **chart-it does not bootstrap the North Star** (that stays point-it's job).
- **No heavy autopilot traversal logic** — ranking bias does the walking.

## Self-review notes

- No placeholders / TBDs.
- Consistency: current-milestone tracking is checkboxes-only everywhere (the earlier `[▶]` pointer is
  removed); point-it scope is Ph0 + Ph1 + Ph2 + Ph3 (Ph2 added per the steering-rationale above);
  check-off behaviour is split interactive vs autopilot consistently.
- Scope: single implementation plan (one new skill + one new command + targeted point-it edits + docs
  + gitignore). Focused enough; no decomposition needed.
