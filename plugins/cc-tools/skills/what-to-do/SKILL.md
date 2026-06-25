---
name: what-to-do
description: "Use when you want to find product direction — to look at a product and surface where it could go next as a ranked menu of moves (new features, finishing half-built work, rebuilding rough parts, paying down tech debt)."
---

Invoked by /what-to-do, with or without a prompt. Requires the product's North Star (set once via /find-goal) — if it's missing, what-to-do routes you there. With it present, what-to-do reads the North Star (and the roadmap, if one exists, biasing toward the current frontier — the parallel milestones open right now) and lets you check off (via a built-in choice prompt) which directions to pursue and hand that list to how-to-do. It explores and ranks; it never decides _how_ — that is how-to-do. Not for deciding a known fork (how-to-do) or building a task (do).

# what-to-do — the direction loop

You are running **what-to-do**: look at a product and produce a **ranked menu of directions** it could
take next. **You do the exploring; the human picks; you never decide.** what-to-do is the mouth of the
funnel — it generates the agenda the other tools act on.
The funnel:
**find-goal** grounds the goal → **what-to-do** fans out a menu (nothing chosen) → **how-to-do** decides _how_ (one way) → **do** builds one task to done (committed).

Its whole job is to fight the **fortune-cookie failure** — ungrounded "add SSO, add analytics, add
dark mode" lists that fit any product — by anchoring every move to the **North Star** and asking one
question: _what moves us toward that goal, and how far?_

**Core rules — non-negotiable:**

- **Roadmap biases, never gates.** It boosts moves on the current **frontier**, but every lane still
  runs — **a menu that hides off-roadmap moves is a bug.**
- **A menu, never a decision.** what-to-do ranks and hands off; it never picks the winner (that's
  how-to-do) — **emitting one recommended direction as "the answer" is a bug.**
- **The empty-lane valve.** A lens with nothing real says so — **fabricating a direction to fill its
  slot is a bug.**
- **Scored against the goal.** Every candidate carries how much it closes the gap to the North Star,
  modulated by **whether the product is in production** (live → move carefully; pre-production → full
  carte blanche). An unscored menu is noise.

---

## The four moves

The signature device. The fan-out always covers exactly these four, each a distinct intent against the
current product (full hunting mandates in Phase 2):

- **ADD** — new capability / steering further: _"what moves us toward the North Star?"_
- **FINISH** — complete what's half-built: _"what did we start and not carry to done?"_
- **REBUILD** — redo something a clearly better way: _"what works but we now know how to do properly?"_
- **REFACTOR** — pay down debt that slows everything: _"where is the mess expensive?"_

ADD and REBUILD push the product _forward_; FINISH and REFACTOR pay down what's _owed_. A healthy menu
usually spans more than one — the **empty-lane valve** keeps any barren lane honest.

---

## Phase 0 — Ground (the gate: North Star, then roadmap)

**North Star detection.** Look for a `## Product North Star` heading in the repo-root `CLAUDE.md`.
The **heading** is the stable contract — its marker comment / parenthetical owner may read `what-to-do`
or `find-goal`, both count.

| State       | Path                                                                                                                                                                                                                                                                      |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Absent**  | **Not grounded — route to `/find-goal` and stop.** Say _"No North Star yet — run `/find-goal` to set the goal, then re-issue this."_ If a prompt was given, tell the human it didn't run and to re-issue `/what-to-do <theme>` after — **never silently discard the prompt.** |
| **Present** | **Read it = the goal.** A prompt (if given) scopes the run to a theme/area; no prompt = full survey. Then read the roadmap (below) and proceed to Phase 1.                                                                                                                |

**Read the roadmap (if any).** Look for `.claude/ccharness/roadmap.md`. If present, read it and derive
the **frontier** = the unchecked `[ ]` milestones of the **earliest `## Stage` that still has any
unchecked box** (tracking is checkboxes only — no separate pointer; the frontier is a _set_, often
just one). A roadmap with **no stage headings** is a legacy line → each milestone its own stage → the
frontier is exactly the first unchecked box (unchanged behaviour). The frontier biases Phase 2 and
Phase 3. If absent, what-to-do runs exactly as before (unbiased) — you may emit a one-line nudge _("no
roadmap yet — `/find-goal` charts the route far ahead")_, then proceed.

---

## Phase 1 — Survey (where we are NOW)

Build a short, factual picture of the _current_ product from the repo: `README`, docs, recent commits and scattered `TODO`/`FIXME`/stub markers. Two or three paragraphs, not an audit. This is the **"now"**; the North Star is the **"end"**; the distance between them is the working field every lens explores. Hand this picture to all four lenses so none re-reads the whole repo from scratch.

**Milestone check (only if a roadmap exists).** Compare the survey against the `done when:` of **each
frontier milestone** (there may be several parallel ones). For every one that now appears met:

- _Interactive run:_ offer to check it off (`[ ]` → `[x]` in `roadmap.md`). When the **last**
  unchecked milestone of the current stage gets checked, the frontier advances to the next stage.
- _Under the musician:_ **auto-mark it** `[x]` (no human mid-loop to confirm). See the musician's
  contract.

---

## Phase 2 — Fan-out (four move-lenses, parallel)

Dispatch four subagents in parallel, one per move. Give each: the **North Star block**, the
**Phase-1 survey**, its **move mandate**, and — **if a roadmap exists** — the **current frontier
milestones (+ the next stage's)** as _orienting context_. The frontier is a **steer, not a gate**:
each lens still scans its whole lane freely, still honours the empty-lane valve, and may still surface
off-roadmap candidates — it just also actively looks for material that advances _any_ frontier
milestone. (Ranking in Phase 3 can only reorder what the lenses produce, so the roadmap must reach
them here, not only at ranking.) Each lens may read deeper _in its own lane_ but stays in that lane —
ADD does not propose refactors, REFACTOR does not propose features.

**Lens mandates:**

- **ADD** — new capability that advances the North Star. Ask _"what's missing that moves us
  toward the vision?"_ Includes bigger directional bets ("steering further"), not just small
  features.
- **FINISH** — half-built things to carry to done. Ask _"what did we start and not finish?"_
  Hunt stubs, dead-ends, partial flows, dangling TODOs.
- **REBUILD** — working things with a clearly better redo. Ask _"what works but we now know how
  to do properly?"_ Must name the better way, not just "it's ugly."
- **REFACTOR** — structural debt slowing everything else. Ask _"where is the mess expensive?"_
  Only debt with real drag — not cosmetic nits.

**Lens output contract** (each lens emits 0–N candidates):

```
move:          ADD | FINISH | REBUILD | REFACTOR
candidates:    [ {
  title:         <short name of the direction>
  what:          <1–2 sentences: the concrete move>
  why_now:       <how it closes the gap to the North Star>
  goal_fit:      high | med | low      # against the North Star
  effort:        S | M | L
  reversibility: easy | hard           # weighs more once the product is in production
  advances:      <milestone id (e.g. M2) | "off-roadmap">   # only when a roadmap exists
} ]
empty_reason:  <if candidates == [] : why this lane has nothing real here>
```

---

## Phase 3 — Rank (synthesis → the menu)

One pass in the main thread. Collect all candidates, then:

1. **Dedupe / merge** overlapping candidates across lenses (a FINISH and a REBUILD pointing at
   the same thing collapse to one).
2. **Score** each on **goal-fit × effort**, then **adjust for production-state** — the one boolean
   from the North Star (**is the product in production?**) swings the same candidate:

| In production?           | REBUILD / REFACTOR                                                                   | ADD                                      | risk weighting                           |
| ------------------------ | ------------------------------------------------------------------------------------ | ---------------------------------------- | ---------------------------------------- |
| **No — carte blanche**   | cheap, encouraged (debt is cheap pre-production)                                     | bold — the product is still being shaped | reversibility barely counts              |
| **Yes — move carefully** | REBUILD is expensive (live users); favour FINISH/REFACTOR + careful, incremental ADD | incremental only                         | reversibility is the dominant multiplier |

1. **Roadmap-fit** (only if a roadmap exists). Apply a final adjustment from each candidate's
   `advances`: advances **any frontier** milestone → **boost**; a **next-stage** milestone → light
   boost; **off-roadmap → no boost, but never dropped.** This is _bias, not a gate_ — a strong
   off-roadmap candidate that ranks high on its own merits still ranks high and still appears.
2. **Rank** into a single ordered menu. Drop nothing silently — if a strong-looking candidate
   ranks low _because of production-caution or roadmap-fit_, keep it and say why.

**Menu entry contract:**

```
rank:      <n>
move:      ADD | FINISH | REBUILD | REFACTOR
title:     <direction>
what:      <1–2 sentences>
why_now:   <gap it closes toward the North Star>
milestone: <M2 | off-roadmap>          # only when a roadmap exists — tags the menu line
score:     goal_fit / effort / reversibility  (+ production-caution and roadmap-fit adjustments if they moved the rank)
```

---

## Phase 4 — Human boundary (check off the work)

How the human chooses depends on whether a musician loop is driving you:

**Under the musician — do NOT interact.** The musician in open mode runs what-to-do to find its own
direction and must never be blocked on a human. If a musician loop is live
(`.claude/ccharness/musician/state.json` exists with `active:true` and `session_id` == this
session), emit the ranked menu as **data** and stop — the caller auto-picks. **Never call
`AskUserQuestion` here:** it blocks on a human, and the loop must never wait. (If that state file is
missing, stale, or for another session, treat yourself as interactive — fail toward asking, never
toward blocking a loop.)

**Interactive — let the human check off the work.** Present the ranked menu tightly (one line per
direction, top first, tagged with its move), then collect picks with the built-in
**`AskUserQuestion`** tool so the human *marks* instead of typing:

- **One question per non-empty lens** (≤4 lenses → ≤4 questions, one `AskUserQuestion` call),
  `multiSelect: true`, `header` = the move (`Add` / `Finish` / `Rebuild` / `Refactor`).
- **Options = that lens's top candidates.** Phase 3 already ranked them; take the top ≤4 (the tool
  caps options at 4). The tool appends its own free-text "Other", so the human can still write one
  in.

The options checked across all lenses form a **list** of directions, each carrying its move tag and
Phase-3 rank. Hand the **whole list** to `cc-tools:how-to-do` — **not one at a time**: how-to-do
takes the list and scales its depth per move (its Phase 0). Nothing checked → say so and stop; the
human can re-run or pick later.

**what-to-do still never decides _how_.** It surfaces and ranks; the human marks _what_; how-to-do
decides _how_ and flows each into the build. A checkbox is still the human's direction call, not
what-to-do's.

---

## Quick reference

`0` Ground — `## Product North Star` heading? no → **route to `/find-goal`**, stop; yes → read = goal, then read `.claude/ccharness/roadmap.md` (**frontier** = unchecked
`[ ]` of the earliest open `## Stage`; no headings = first `[ ]`) · `1` Survey — repo = where we are
now; if roadmap, check **each frontier milestone's** `done when` (interactive: offer to check off ·
under the musician: auto-mark) · `2` Fan-out — four lenses (ADD / FINISH / REBUILD / REFACTOR), parallel,
empty-lane valve, **fed the frontier milestones as a steer (not a gate)** · `3`
Rank — dedupe + score + **production-caution** (in production → careful; not → carte blanche) +
**roadmap-fit** → menu (off-roadmap never dropped) · `4` Boundary — interactive: `AskUserQuestion`
multiSelect per lens → checked **list** → how-to-do; under the musician: emit menu as data, **no
`AskUserQuestion`**, caller auto-picks.

**Invariant:** what-to-do diverges and ranks; it never decides _how_. A menu that pre-decides the
approach is a bug — that's how-to-do. The human marks _what_; never block a live musician loop.
