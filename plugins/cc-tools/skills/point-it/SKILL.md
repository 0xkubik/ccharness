---
name: point-it
description: "Use when you want product *direction* rather than one answer — to look at a product and surface where it could go next as a ranked menu of moves (new features, finishing half-built work, rebuilding rough parts, paying down tech debt). Invoked by /point-it, with or without a prompt. Requires the product's North Star (set once via /chart-it) — if it's missing, point-it routes you to /chart-it. With it present, point-it reads the North Star (and the roadmap, if one exists, biasing toward the current milestone) and lets you check off (via a built-in choice prompt) which directions to pursue and hand that list to grill-it. It explores and ranks; it never decides *how* — that is grill-it. Not for deciding a known fork (grill-it) or building a task (implement-it)."
---

# point-it — the direction loop

You are running **point-it**: look at a product and produce a **ranked menu of directions** it
could take next. **You do the exploring; the human picks; you never decide.** point-it is the
mouth of the funnel — it generates the agenda the other tools act on. **chart-it grounds it first**
(the North Star + roadmap); point-it then reads that grounding and diverges:

```
chart-it  ─►  point-it  ──►  grill-it  ──►  implement-it
GROUND        DIVERGE        DECIDE         BUILD
North Star    a menu of      one reasoned   one task taken
+ roadmap     directions     decision       to done
(the goal)    (nothing       on a chosen    (committed)
              chosen)        fork
```

Its whole job is to fight the **fortune-cookie failure**: ungrounded "add SSO, add analytics,
add dark mode" lists that fit any product. point-it beats this by anchoring everything to a
**declared destination** — the product's _North Star_, captured once via `/chart-it` — and then
asking only one question: _what moves us toward that goal, and how far?_

**Core invariants — non-negotiable:**

- **Ground before you diverge.** No North Star block in CLAUDE.md → you do NOT guess the
  business and you do NOT bootstrap it here. You **route the human to `/chart-it`** (the grounding
  loop owns goal-setting) and stop. (Phase 0.)
- **Roadmap biases, never gates.** If a roadmap exists, it boosts moves that advance the current
  milestone — but every lane still runs and off-roadmap directions still surface. A menu that hides
  off-roadmap moves is a bug.
- **A menu, never a decision.** point-it ranks and hands off. It never picks the winner — that
  is grill-it. Emitting one recommended direction as "the answer" is a bug.
- **The empty-lane valve.** A move-lens with nothing real to propose says so and stops. It
  never fabricates a direction to fill its slot. A confident proposal on a non-issue is exactly
  the failure mode to avoid (the analog of grill-it's low-conviction valve).
- **Everything is scored against the goal.** Every candidate carries _how much it closes the
  gap to the North Star_, modulated by the product's **Level**. An unscored menu is noise.

---

## The four moves

The signature device. Where grill-it has a **compass** (which way to turn — a _decision_),
point-it has **four moves** (what kind of step to take — an _exploration_). The fan-out covers
exactly these four, each a distinct intent against the current product:

```
   ADD ───────────── new features & steering further
                     "what new capability moves us toward the North Star?"

   FINISH ────────── complete what's half-built
                     "what's started but not carried to done? (stubs, TODOs, dead-ends)"

   REBUILD ───────── redo something better
                     "what works, but we now see a clearly better way to do it?"

   REFACTOR ──────── pay down tech debt
                     "where is the repo messy/debt-laden enough to slow everything else?"
```

ADD and REBUILD push the product _outward/forward_; FINISH and REFACTOR pay down what's
_owed_. A healthy menu usually spans more than one — but the **empty-lane valve** means any
lane that has no genuine candidate reports "nothing here" rather than inventing one.

---

## Phase 0 — Ground (the gate: North Star, then roadmap)

**North Star detection.** Look for a `## Product North Star` heading in the repo-root `CLAUDE.md`.
The **heading** is the stable contract — its marker comment / parenthetical owner may read `point-it`
or `chart-it`, both count.

| State | Path |
| --- | --- |
| **Absent** | **Not grounded — route to `/chart-it` and stop.** point-it does **not** bootstrap the North Star anymore; goal-setting moved to chart-it (the grounding loop). Say: *"No North Star yet — this product has no captured goal, and ccharness builds from the goal outward. Run `/chart-it` to set it (it captures the North Star, then offers to chart the roadmap), then re-issue this command. Your prompt isn't discarded — re-issue it after `/chart-it`."* If a theme/prompt was given, tell the human it did not run and to re-issue `/point-it <their theme>` after — **never silently discard the prompt.** |
| **Present** | **Read it = the goal.** A prompt (if given) scopes the run to a theme/area; no prompt = full survey. Then read the roadmap (below) and proceed to Phase 1. |

**Read the roadmap (if any).** Look for `.claude/ccharness/roadmap.md`. If present, read it and derive
the **current milestone** = the first unchecked `[ ]` box (current-tracking is checkboxes only — no
separate pointer). This biases Phase 2 and Phase 3. If absent, point-it runs exactly as before
(unbiased) — you may emit a one-line nudge *("no roadmap yet — `/chart-it` charts the route far
ahead")*, then proceed.

---

## Phase 1 — Survey (where we are NOW)

Build a short, factual picture of the _current_ product from the repo: `README`, docs,
recent commits, open issues, `CHANGELOG`, and scattered `TODO`/`FIXME`/stub markers. Two or
three paragraphs, not an audit. This is the **"now"**; the North Star is the **"end"**; the
distance between them is the working field every lens explores. Hand this picture to all four
lenses so none re-reads the whole repo from scratch.

**Milestone check (only if a roadmap exists).** Compare the survey against the **current
milestone's `done when:`**. If it now appears met:
- *Interactive run:* offer to check the milestone off (`[ ]` → `[x]` in `roadmap.md`), advancing
  current to the next unchecked milestone.
- *Autopilot run:* **auto-mark it `[x]`** (no human mid-loop to confirm; current must advance for the
  loop to keep walking the route). See autopilot's contract.

---

## Phase 2 — Fan-out (four move-lenses, parallel)

Dispatch four subagents in parallel, one per move. Give each: the **North Star block**, the
**Phase-1 survey**, its **move mandate**, and — **if a roadmap exists** — the **current (+ next)
milestone** as *orienting context*. The milestone is a **steer, not a gate**: each lens still scans
its whole lane freely, still honours the empty-lane valve, and may still surface off-roadmap
candidates — it just also actively looks for material that advances the current milestone. (Ranking
in Phase 3 can only reorder what the lenses produce, so the roadmap must reach them here, not only at
ranking.) Each lens may read deeper _in its own lane_ but stays in that lane — ADD does not propose
refactors, REFACTOR does not propose features.

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

**Lens output contract** (each lens emits 0–N candidates — **0 is a valid, honest answer**):

```
move:          ADD | FINISH | REBUILD | REFACTOR
candidates:    [ {
  title:         <short name of the direction>
  what:          <1–2 sentences: the concrete move>
  why_now:       <how it closes the gap to the North Star>
  goal_fit:      high | med | low      # against Vision + Core problem
  effort:        S | M | L
  reversibility: easy | hard           # weighs more as Level rises
  advances:      <milestone id (e.g. M2) | "off-roadmap">   # only when a roadmap exists
} ]
empty_reason:  <if candidates == [] : why this lane has nothing real here>
```

---

## Phase 3 — Rank (synthesis → the menu)

One pass in the main thread. Collect all candidates, then:

1. **Dedupe / merge** overlapping candidates across lenses (a FINISH and a REBUILD pointing at
   the same thing collapse to one).
2. **Score** each on **goal-fit × effort**, then **adjust for Level** — the same candidate
   ranks differently depending on where the product is:

| Level                     | REBUILD / REFACTOR                                                      | ADD                                      | risk weighting                           |
| ------------------------- | ----------------------------------------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| **1 — no production**     | cheap, encouraged (debt is cheap in a prototype)                        | bold — the product is still being shaped | reversibility barely counts              |
| **2 — production coming** | FINISH + REFACTOR rise (must be release-ready)                          | more careful                             | reversibility starts to count            |
| **3 — in production**     | REBUILD is expensive (live users); favour FINISH/REFACTOR + careful ADD | incremental only                         | reversibility is the dominant multiplier |

3. **Roadmap-fit** (only if a roadmap exists). Apply a final adjustment from each candidate's
   `advances`: advances the **current** milestone → **boost**; the **next** milestone → light boost;
   **off-roadmap → no boost, but never dropped.** This is *bias, not a gate* — a strong off-roadmap
   candidate that ranks high on its own merits still ranks high and still appears. Hiding off-roadmap
   moves is a bug.
4. **Rank** into a single ordered menu. Drop nothing silently — if a strong-looking candidate
   ranks low _because of Level or roadmap-fit_, keep it and say why.

**Menu entry contract:**

```
rank:      <n>
move:      ADD | FINISH | REBUILD | REFACTOR
title:     <direction>
what:      <1–2 sentences>
why_now:   <gap it closes toward the North Star>
milestone: <M2 | off-roadmap>          # only when a roadmap exists — tags the menu line
score:     goal_fit / effort / reversibility  (+ Level and roadmap-fit adjustments if they moved the rank)
```

---

## Phase 4 — Human boundary (check off the work)

How the human chooses depends on whether a never-stop loop is driving you:

**Under autopilot — do NOT interact.** If autopilot invoked you (it says _"produce the menu, I
pick"_) **or** a loop is live (`.claude/ccharness/autopilot/state.json` exists with `active:true`
and `session_id` == this session), emit the ranked menu as **data** and stop — the caller
auto-picks. **Never call `AskUserQuestion` here:** it blocks on a human, and the loop must never
wait. (If that state file is missing, stale, or for another session, treat yourself as
interactive — fail toward asking, never toward blocking a loop.)

**Interactive — let the human check off the work.** Present the ranked menu tightly (one line per
direction, top first, tagged with its move), then collect picks with the built-in
**`AskUserQuestion`** tool so the human _marks_ instead of typing:

- **One question per non-empty lens** (≤4 lenses → ≤4 questions, one `AskUserQuestion` call),
  `multiSelect: true`, `header` = the move (`Add` / `Finish` / `Rebuild` / `Refactor`).
- **Options = that lens's top candidates.** Phase 3 already ranked them; take the top ≤4 (the tool
  caps options at 4). The tool appends its own free-text "Other", so the human can still write one
  in.

The options checked across all lenses form a **list** of directions, each carrying its move tag and
Phase-3 rank. Hand the **whole list** to `cc-tools:grill-it` — **not one at a time**: grill-it
takes the list and scales its depth per move (its Phase 0). Nothing checked → say so and stop; the
human can re-run or pick later.

**point-it still never decides _how_.** It surfaces and ranks; the human marks _what_; grill-it
decides _how_ and flows each into the build. A checkbox is still the human's direction call, not
point-it's.

---

## Quick reference

`0` Ground — `## Product North Star` heading? no → **route to `/chart-it`**, stop (point-it does not
bootstrap it); yes → read = goal, then read `.claude/ccharness/roadmap.md` (current = first `[ ]`) ·
`1` Survey — repo = where we are now; if roadmap, check current milestone's `done when` (interactive:
offer to check off · autopilot: auto-mark) · `2` Fan-out — four lenses (ADD / FINISH / REBUILD /
REFACTOR), parallel, empty-lane valve, **fed the current milestone as a steer (not a gate)** · `3`
Rank — dedupe + score × Level + **roadmap-fit** → menu (off-roadmap never dropped) · `4` Boundary —
interactive: `AskUserQuestion` multiSelect per lens → checked **list** → grill-it; under autopilot:
emit menu as data, **no `AskUserQuestion`**, caller auto-picks.

**Invariant:** point-it diverges and ranks; it never decides _how_. A menu that pre-decides the
approach is a bug — that's grill-it. The human marks _what_; never block a live autopilot loop.
