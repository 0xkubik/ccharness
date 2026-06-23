---
name: point-it
description: "Use when you want product *direction* rather than one answer — to look at a product and surface where it could go next as a ranked menu of moves (new features, finishing half-built work, rebuilding rough parts, paying down tech debt). Invoked by /point-it, with or without a prompt. First run in a repo captures the product's North Star into CLAUDE.md; later runs let you check off (via a built-in choice prompt) which directions to pursue and hand that list to grill-it. It explores and ranks; it never decides *how* — that is grill-it. Not for deciding a known fork (grill-it) or building a task (implement-it)."
---

# point-it — the direction loop

You are running **point-it**: look at a product and produce a **ranked menu of directions** it
could take next. **You do the exploring; the human picks; you never decide.** point-it is the
mouth of the funnel — it generates the agenda the other tools act on:

```
point-it  ──►  grill-it  ──►  implement-it
DIVERGE        DECIDE         BUILD
a menu of      one reasoned   one task taken
directions     decision       to done
(nothing       on a chosen    (committed)
 chosen)       fork
```

Its whole job is to fight the **fortune-cookie failure**: ungrounded "add SSO, add analytics,
add dark mode" lists that fit any product. point-it beats this by anchoring everything to a
**declared destination** — the product's _North Star_, captured once in CLAUDE.md — and then
asking only one question: _what moves us toward that goal, and how far?_

**Core invariants — non-negotiable:**

- **Ground before you diverge.** No North Star block in CLAUDE.md → you do NOT guess the
  business. You run the bootstrap interview and write the block first. (Phase 0.)
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

## Phase 0 — Ground (detect the North Star, or capture it)

Look for the North Star block in the repo's root `CLAUDE.md` — detect it by its marker
comment (`<!-- managed by point-it`). Then branch:

| State                                                                                 | Path                                                                                                                                               |
| ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **No block** (first run)                                                              | **Bootstrap** — run the interview below, write the block, and **stop.** The destination is now fixed; the next `/point-it` run does the real work. |
| **Block exists**                                                                      | **Read it = the goal.** A prompt (if given) scopes the run to a theme/area; no prompt = full survey. Then proceed to Phase 1.                      |
| **Block exists but stale** (old `captured:` date, or the human says "the goal moved") | Offer `--reground` → re-run the bootstrap interview, overwrite the block, continue.                                                                |

**First run _with_ a prompt** (a theme was given but no block exists yet): you can't aim without
a destination, so capture the North Star first — then tell the human their prompt did not run
and to re-issue `/point-it <their theme>` now that the goal exists. **Never silently discard the
prompt.**

### Bootstrap sub-protocol (first run only)

Borrow the _technique_ of `superpowers:brainstorming` — one question at a time, plain
language — but the terminal is **a CLAUDE.md block, not an implementation plan.** Do NOT hand
off to `writing-plans`. Ask for exactly these three, one at a time:

1. **Vision** — a few sentences: what does the finished product look like at the end?
2. **Core problem** — what is the main problem this product solves?
3. **Level** — `1` no production · `2` production exists / is coming · `3` already in production.

Then **write the block yourself**, appending it to the project-root `CLAUDE.md` and preserving
everything already there:

```markdown
## Product North Star (ccharness:point-it)

<!-- managed by point-it · edit freely, point-it re-reads this · captured: <YYYY-MM-DD> -->

- **Vision:** <a few sentences — how the finished product looks at the end>
- **Core problem:** <the main problem the product solves>
- **Level:** <1 — no production · 2 — production exists/coming · 3 — already in production>
```

**Own this write.** point-it's Phase-0 detection keys on this exact marker comment, so point-it
must produce it — a generic helper won't reliably reproduce it. The `claude-md-management` tools
are the wrong shape for this: `/revise-claude-md` is for session-learnings one-liners, and
`claude-md-improver` audits/scores existing files — neither inserts a verbatim block. Reach for
`claude-md-improver` _afterward_ only if you also want the rest of `CLAUDE.md` tidied; it is not
the path that writes the North Star.

Confirm the written block back to the human in one line, then **stop** — bootstrap does not
continue into a survey on the same run.

---

## Phase 1 — Survey (where we are NOW)

Build a short, factual picture of the _current_ product from the repo: `README`, docs,
recent commits, open issues, `CHANGELOG`, and scattered `TODO`/`FIXME`/stub markers. Two or
three paragraphs, not an audit. This is the **"now"**; the North Star is the **"end"**; the
distance between them is the working field every lens explores. Hand this picture to all four
lenses so none re-reads the whole repo from scratch.

---

## Phase 2 — Fan-out (four move-lenses, parallel)

Dispatch four subagents in parallel, one per move. Give each: the **North Star block**, the
**Phase-1 survey**, and its **move mandate**. Each lens may read deeper _in its own lane_ but
stays in that lane — ADD does not propose refactors, REFACTOR does not propose features.

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

3. **Rank** into a single ordered menu. Drop nothing silently — if a strong-looking candidate
   ranks low _because of Level_, keep it and say why.

**Menu entry contract:**

```
rank:     <n>
move:     ADD | FINISH | REBUILD | REFACTOR
title:    <direction>
what:     <1–2 sentences>
why_now:  <gap it closes toward the North Star>
score:    goal_fit / effort / reversibility  (and the Level adjustment if it moved the rank)
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
  in.и

The options checked across all lenses form a **list** of directions, each carrying its move tag and
Phase-3 rank. Hand the **whole list** to `ccharness:grill-it` — **not one at a time**: grill-it
takes the list and scales its depth per move (its Phase 0). Nothing checked → say so and stop; the
human can re-run or pick later.

**point-it still never decides _how_.** It surfaces and ranks; the human marks _what_; grill-it
decides _how_ and flows each into the build. A checkbox is still the human's direction call, not
point-it's.

---

## Quick reference

`0` Ground — North Star block? no → bootstrap interview → write to CLAUDE.md → **stop**; yes →
read = goal · `1` Survey — repo = where we are now · `2` Fan-out — four lenses (ADD / FINISH /
REBUILD / REFACTOR), parallel, empty-lane valve · `3` Rank — dedupe + score × Level → menu ·
`4` Boundary — interactive: `AskUserQuestion` multiSelect per lens → checked **list** → grill-it;
under autopilot: emit menu as data, **no `AskUserQuestion`**, caller auto-picks.

**Invariant:** point-it diverges and ranks; it never decides _how_. A menu that pre-decides the
approach is a bug — that's grill-it. The human marks _what_; never block a live autopilot loop.
