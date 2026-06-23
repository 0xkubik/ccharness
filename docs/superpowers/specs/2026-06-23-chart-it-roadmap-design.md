# ccharness `/chart-it` — design

**Date:** 2026-06-23
**Status:** approved (brainstorming) → ready for implementation plan
**Plugin:** ccharness (v0.7.0 → adds an 8th command + moves North Star ownership)

## Problem

Two gaps, one skill closes both.

1. **No route between destination and next step.** The harness has a **North Star** (a managed block
   in `CLAUDE.md` — the "end": vision · core problem · level) and **point-it's menu** (the "next
   step", recomputed from the gap every run). Nothing persists the **sequence of milestones** in
   between, so point-it re-guesses the trajectory each run.
2. **Grounding is owned by the wrong skill.** Today *point-it* bootstraps the North Star as a side
   effect of its first run. The user wants grounding to be a deliberate, up-front act: sit down
   **once**, do the **goal-setting** (целеполагание) and then chart the **route far ahead** — and
   make that the single front door the whole harness depends on.

`/chart-it` is the **grounding loop**: it owns goal-setting → the **North Star**, then continues into
the **roadmap** (the route). Every other product skill depends on the North Star existing and, if it
is missing, **routes the user to `/chart-it`** instead of guessing or bootstrapping.

```
 chart-it   (GROUND — set the goal, then chart the route)
   │  writes North Star → CLAUDE.md   +   roadmap → .claude/ccharness/roadmap.md
   ▼
 point-it ──► grill-it ──► implement-it        (+ slap = tactical reset, exempt)
 DIVERGE       DECIDE        BUILD
   ▲ every product skill: no North Star → routes back to chart-it
   ▲ point-it additionally reads roadmap and biases ranking toward the CURRENT milestone

 North Star = WHERE TO (the goal) · roadmap = BY WHICH ROUTE · point-it = WHICH NEXT STEP
```

## Decisions (locked in brainstorming)

| # | Decision | Choice |
|---|---|---|
| 1 | How point-it consumes the roadmap | **Bias ranking** — a new scoring dimension; never a gate. Off-roadmap moves still surface, just rank lower. |
| 2 | Milestone weight | **Lightweight** — name + `done when …` outcome + one-line theme. No frozen task list. |
| 3 | Sequence shape | **Sequential** (M1→M2→M3), so "current milestone" is unambiguous. Not parallel tracks. |
| 4 | Storage | `.claude/ccharness/roadmap.md` — everything the plugin produces lives under `.claude/ccharness/` (alongside `autopilot/`, `decisions/`). |
| 5 | Git tracking | **Committed.** Narrow `.gitignore` so the roadmap is versioned; runtime state stays ignored. |
| 6 | Current-milestone tracking | `[x]`/`[ ]` checkboxes only; **current = first unchecked**. One source of truth — no separate pointer. |
| 7 | Command name | `/chart-it` (chart the course by the star). |
| 8 | **Grounding owner** | **chart-it owns the North Star** (goal-setting). The bootstrap sub-protocol is **removed from point-it**. The North Star block (format + marker) is a **shared contract**: chart-it writes it; all other skills only *detect* it. |
| 9 | **The hard gate** | **No North Star → route to chart-it**, applied to **all five product skills** (point-it, grill-it, implement-it, autopilot — chart-it itself creates it). The gate checks for the **North Star only**; a missing *roadmap* never gates anything. |
| 10 | **Gate exemptions** | **slap** (tactical reset invoked mid-task — goal-independent) and **ccharness-init** (installs the plugins, runs before any grounding exists) are exempt. Gating them would be incoherent. |

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
- **No `[▶]` / `current:` pointer.** Current is *derived* (first `[ ]`).

## The North Star block (shared contract)

Unchanged in **format**; only its **owner moves** (point-it → chart-it). Everything keys on the
marker comment, so the block chart-it writes must be byte-compatible with what point-it used to
write:

```markdown
## Product North Star (ccharness)
<!-- managed by chart-it · edit freely · captured: <YYYY-MM-DD> -->
- **Vision:** <a few sentences — how the finished product looks at the end>
- **Core problem:** <the main problem the product solves>
- **Level:** <1 — no production · 2 — production exists/coming · 3 — already in production>
```

Detection (used by every gated skill): look for the `Product North Star` heading + the
`managed by ... North Star`-style marker in the repo-root `CLAUDE.md`. (Keep detection tolerant of
the old `managed by point-it` marker so existing repos aren't orphaned — see Migration.)

## The new skill — `chart-it` (the grounding loop)

Borrows the *technique* of `superpowers:brainstorming` / the old point-it bootstrap — one question at
a time, plain language — but the terminal is **`CLAUDE.md` + `roadmap.md`, not an implementation
plan.** Do NOT hand off to `writing-plans`.

- **Ph0 — Goal-setting (целеполагание → North Star).** If no North Star block exists, run the
  goal-setting dialogue (a fuller, collaborative version of the old 3-question bootstrap; the extra
  richness lives in the conversation and feeds the roadmap, but the durable artifact is still the
  stable 3-field block). **chart-it writes the block itself** (owns the marker write). If a block
  already exists, read it; offer `--reground` to revise it.
- **Ph1 — Survey "now".** A short, factual picture of the current product from the repo (as point-it
  Ph1). The route spans now → ★, so chart-it needs both ends.
- **Ph2 — Collaborative decomposition (the heart).** chart-it proposes a *draft* sequence of
  lightweight milestones from now → ★, then works through it with the human **one decision at a
  time**: is the sequence right? the granularity? merge / split / reorder? what is the true first
  milestone? Iterates until the human is satisfied.
- **Ph3 — Write.** Writes `.claude/ccharness/roadmap.md`, confirms back in one line, stops.

**Boundary between the two artifacts.** The North Star (Ph0) is the **mandatory** core that satisfies
the gate for every other skill. The roadmap (Ph1–Ph3) is the **optional-but-encouraged** continuation
— a user bounced here from `/implement-it` for a one-off can capture the North Star and stop, then
re-run their task. So after Ph0, chart-it **offers** to continue into the roadmap rather than forcing
it.

**Re-run = revise (living artifact).** Normally run once; a roadmap drifts. A re-run re-surveys →
shows the roadmap + progress (which `done when`s now hold) → proposes adjustments (check off
completed, add/split/reorder, drop the obsolete) → rewrites. Analog of point-it's `--reground` for
the North Star.

## The hard gate — how each skill enforces it

Every gated skill performs the same first check: **North Star block present in `CLAUDE.md`?** If not,
**stop and route to `/chart-it`** — never bootstrap, never guess, never silently discard the user's
prompt (tell them to re-issue after `/chart-it`).

- **point-it** — Ph0 no longer bootstraps. Missing → route to chart-it. Present → read North Star +
  read `roadmap.md` (if any), then proceed. (Roadmap-aware Ph1/Ph2/Ph3 below.)
- **grill-it** — add a grounding precondition before the proposer fan-out: missing North Star →
  route to chart-it.
- **implement-it** — add a grounding precondition *before* Stage 0 (clarity gate): missing North Star
  → route to chart-it. (This is a deliberate, opinionated cost: a one-off task in a fresh repo first
  requires capturing the North Star. The redirect is graceful and the prompt is preserved.)
- **autopilot** — already refuses without a North Star; change the message from "run /point-it first"
  to "run /chart-it first." (Autopilot also wants a roadmap to walk, but only the North Star gates
  arming.)
- **chart-it** — not gated (it creates the North Star).

**Exempt:** **slap** (tactical reset mid-task) and **ccharness-init** (installs plugins pre-grounding).

## Changes to point-it (roadmap-aware)

Backward compatible w.r.t. the roadmap: **North Star present but no `roadmap.md` → point-it behaves
as today** (just unbiased ranking), optionally emitting a one-line nudge ("no roadmap — `/chart-it`
charts the route far ahead").

- **Ph0** — detect North Star (missing → route to chart-it, per the gate); additionally read
  `roadmap.md` if present; derive the current milestone (first unchecked).
- **Ph1** — check whether the **current milestone's `done when:`** already holds.
  - *Interactive:* offer to check it off (advancing current).
  - *Autopilot:* **auto-mark** complete (no human mid-loop; current must advance for the loop to walk
    the route).
- **Ph2 (now roadmap-aware)** — each of the four move-lenses additionally receives the **current
  (+ next) milestone** as *orienting context* — **not a gate.** Lenses still scan all four moves
  freely, honour the empty-lane valve, and may surface off-roadmap candidates; they now also actively
  look for material that advances the current milestone. *Rationale:* ranking can only reorder what
  the lenses produce — the roadmap must reach Ph2, not just Ph3, or the boost acts on thin material.
- **Ph3 — Rank** — add a **roadmap-fit** dimension: advances **current** milestone → boost; advances
  **next** → light boost; off-roadmap → no boost **but not hidden**. Menu entries tag the relevant
  milestone (e.g. `M2`); off-roadmap candidates are marked as such.
- **Invariant intact** — the menu still selects nothing; the roadmap only reorders.

## Autopilot

Near-free, no separate traversal logic. Autopilot auto-picks the top of the menu; because the roadmap
biases the top toward the current milestone, autopilot **naturally walks the route milestone by
milestone**. When a milestone's `done when:` is met, point-it (in autopilot mode) **auto-marks it
`[x]`**, current advances, the loop proceeds. The check-off is **automatic, not a handback** —
autopilot never waits for a human.

## Storage & git

- Roadmap → `.claude/ccharness/roadmap.md`.
- **`.gitignore`:** *replace* the current `.claude/ccharness/` line with:
  ```
  .claude/ccharness/*
  !.claude/ccharness/roadmap.md
  ```
  (The bare-directory form cannot be negated; `/*` ignores contents while allowing re-inclusion.
  Replace — do not leave both lines.) `roadmap.md` is tracked; `autopilot/` and `decisions/` stay
  ignored.

## Migration / compatibility

- Existing repos have a North Star block marked `managed by point-it`. **Detection must accept both**
  the old (`point-it`) and new (`chart-it`) markers so those repos still pass the gate. chart-it's
  `--reground` (or its next write) updates the marker to `chart-it`; no forced migration.
- No `roadmap.md` anywhere yet → every skill works exactly as before except the North Star bootstrap
  now lives in chart-it.

## Documentation touchpoints (for the plan)

- **README:** funnel diagram (chart-it as the grounding front door), commands table (add `/chart-it`
  row; note the North Star-ownership move and the hard gate), Layout section, and the "few
  boundaries" prose (North Star is now captured by chart-it, not point-it's first run).
- **`ccharness-init` dependency table: do NOT touch** — chart-it is internal, not an external
  orchestrated plugin.
- **`plugin.json`:** bump `version` 0.7.0 → 0.8.0; extend the description with the 8th command and the
  grounding-gate behaviour.
- **point-it SKILL.md:** remove the bootstrap sub-protocol; add the gate route + the roadmap-aware
  Ph0/Ph1/Ph2/Ph3 edits + Quick reference.
- **grill-it / implement-it / autopilot SKILL.md (and command files):** add the grounding
  precondition / update the redirect target to chart-it.

## YAGNI — explicitly out of scope

- **No drift-valve lens** in point-it (option-1 "bias", not "focus + drift valve").
- **Milestones carry no frozen task list.**
- **No new North Star fields** — целеполагание enriches the *conversation* and the roadmap, but the
  durable block stays the stable 3-field contract everything detects.
- **No heavy autopilot traversal logic** — ranking bias does the walking.
- **No forced migration** of old `managed by point-it` markers — detection is tolerant.

## Self-review notes

- No placeholders / TBDs.
- Consistency: current-milestone tracking is checkboxes-only; point-it scope is Ph0+Ph1+Ph2+Ph3;
  check-off is interactive-vs-autopilot split consistently; North Star ownership is chart-it
  everywhere, with tolerant detection for the legacy marker.
- Scope: one new skill + one new command + targeted edits to four existing skills + docs + gitignore.
  Larger than the first draft (the grounding move touches every product skill) but still a single
  coherent implementation plan; no decomposition needed.
