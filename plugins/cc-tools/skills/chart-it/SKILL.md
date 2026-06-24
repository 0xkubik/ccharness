---
name: chart-it
description: Use when setting up or revising a product's long-horizon direction — the grounding loop that sets the goal and versions the road to it.
---

Guides a human to **set the product's goal** and **version the route to it** (v0 → v1 → v2 → …).
Captures the **North Star** (the goal) into `CLAUDE.md`, then builds a `.claude/ccharness/roadmap.md`
organized as **versions of the product** — and, inside each version, the features broken down into
ordered work **stages**. Invoked by `/chart-it`. Run once up front (every other product skill routes
here when no goal exists); re-run to revise. The roadmap then biases point-it toward the current
frontier and feeds the autopilot/semipilot loops.

# chart-it — set the goal, then version the road to it

You are the harness's **grounding front door**, and this is a **high-stakes conversation**, not a
form to fill in. What you capture here decides the product's whole direction — point-it ranks moves
against it, and autopilot/semipilot will **build, milestone by milestone, off the roadmap you write**.
A sloppy goal or a vague version makes every later automated step aim at the wrong target.

**Tell the human this up front, plainly:** this defines what we're building and the order we build it;
many later steps (manual and automated) depend on it; it's worth slowing down for. Then run a real
guided interview — **lead with questions**, one decision at a time, until the picture is sharp.

**How you ask:**

- **The global goal: ask open questions — do NOT offer pre-baked options.** The goal must come from
  the human's own head, so use plain conversational questions, one at a time. Never hand them a menu
  of product visions to pick from.
- **The versions: use `AskUserQuestion`** to ask leading questions with concrete options (plus the
  free-text fallback). This is where you actively steer — "for v0, which of these is the core?", "does
  the product at v0 look more like X or Y?".
- **One decision at a time** (borrow `superpowers:brainstorming`'s technique). The terminal is
  `CLAUDE.md` + `roadmap.md` — **not** `writing-plans`.

---

## Phase 0 — The global goal (the North Star) — ask, don't offer

**Detect first.** Look for a `## Product North Star` heading in the repo-root `CLAUDE.md`.

| State            | Path                                                                                    |
| ---------------- | --------------------------------------------------------------------------------------- |
| **Present**      | Read it = the goal. Offer `--reground` to revise. Continue to the version loop.         |
| **Absent**       | Run the goal-setting questions below, then **write the block yourself**.                |
| **`--reground`** | Re-run the questions, overwrite the block (preserve the rest of `CLAUDE.md`), continue. |

**The goal-setting dialogue — open questions only, no multiple-choice.** Draw out, one question at a
time, in plain language: what does the finished product look like at the very end — who is it for, and
what does success look like? And **is it already in production (real users), or not yet?** Don't move
on until the answer is concrete. The **durable artifact** is this stable block — append it to the project-root `CLAUDE.md`,
**preserving everything already there**:

```markdown
## Product North Star (cc-tools)

<!-- managed by chart-it · edit freely, the harness re-reads this · captured: <YYYY-MM-DD> -->

- **Vision:** <a few sentences — how the finished product looks at the end>
- **In production?** <yes — live users, move carefully · no — full carte blanche>
```

Confirm the written block back in one line. The goal is **mandatory**; it's what every other skill
detects. Then move into the version loop.

---

## Phase 1 — Survey "now"

Build a short, factual picture of the **current** product from the repo: `README`, docs, recent
commits, scattered `TODO`/`FIXME`/stub markers. Two or three paragraphs, not an audit. This is the
**"now"**; the North Star is the **"end"**; the versions are the steps between them.

---

## Phase 2 — Version the product (the heart — a loop)

Walk the product forward **one version at a time**, starting at **v0 (MVP)**. A version is a recognizable
state of the _product_ — "what a user would see and do at this point" — not a pile of tasks. For
**each** version, in order:

**1. Elicit the version with `AskUserQuestion`.** Lead the human: "What do you want to see in **v0** —
which features, and what does the product look and feel like at that point?" Keep asking leading
questions (with options + free-text) until the version's shape is clear: its headline features, what's
deliberately _out_, and how it looks to a user. Then do the same for v1, v2, …

**2. Break the version's features into ordered stages.** Before moving on, decompose **this version's**
features into work **stages** so the human can see the rough path of work inside the version. The
single rule: **need "A before B" → put them in different stages; independent → same stage** (parallel,
any order within a stage). Each feature lands as a lightweight milestone with a **stable global id**
(`M1`, `M2`, … — continuous across all versions) and `name + done when: <observable outcome> + theme:
<one line>`. The `done when:` must be **observable** — that's what later lets the loops judge it
complete. Don't manufacture parallelism that isn't there; a genuinely linear version is one milestone
per stage.

**3. Write this version into the roadmap, then urge a review.** Append the version's section to
`.claude/ccharness/roadmap.md` (format below) and **strongly suggest the human read it back before you
continue** — "Here's v0 laid out as stages. Please check it — the loops will build straight off this.
Look right before we move to v1?" Don't steamroll past their review.

**4. At the version boundary, ask: continue, rethink, or finish?** Every time a version is written,
use `AskUserQuestion` to offer three paths:

- **Continue** → elicit the next version (back to step 1).
- **Rethink already-decided work** → **always offer this.** The human may have spotted a contradiction
  or changed their mind about an earlier version (or the goal itself). Let them describe what they
  found, then **re-open and revise** the affected versions and stages — and the North Star, if the goal
  moved — one decision at a time, rewrite `roadmap.md`, urge a fresh review, then resume. Better to
  re-examine now than build off a roadmap the human no longer believes.
- **Finish** → only offered once v0, v1, and v2 all exist (a minimum of three versions); goes to
  Phase 3. Before that, only Continue / Rethink.

Iterate within each version until the human is satisfied; re-stage, split, or merge as they react.

---

## Phase 3 — Independent review (a fresh pair of eyes)

When the human chooses to finish, don't just stop — **dispatch one independent reviewer subagent
(read-only)** to pressure-test the finished roadmap as a skeptic. Give it: the **North Star block** and
the **full `.claude/ccharness/roadmap.md`**. Ask it to judge:

- Do the versions form a **credible path** from "now" to the North Star — does v0 → v1 → v2 … actually
  converge on the goal, with no missing version in between?
- Is **each version a coherent product state** a user would recognize — not a random bag of features?
- Do the **stages respect real dependencies** — anything in the same stage that secretly needs a
  sibling (split it), or split across stages with no real order (merge them)?
- Is every **`done when:` observable**, and does it truly mean that milestone is done?
- Name the **contradictions, gaps, and over- or under-scoped versions** it finds.

Relay its assessment to the human in plain language and **offer to act on it** — re-open the loop to
revise the flagged versions/stages/goal, or accept as-is. The review is **advice, not a gate**: the
human decides. Then stop.

---

## The roadmap format (the contract — keep it exact)

Write `.claude/ccharness/roadmap.md` (create the directory if needed). **Versions** are top-level
(`# vN`) human-facing milestones of the product; inside each, ordered `## Stage` bands hold the
parallel milestones. Milestones are listed in **document order** (v0's stages first, then v1's, …) =
a valid sequential walk. The **frontier** = the unchecked `[ ]` milestones of the **earliest `## Stage`
(in document order) that still has any** — derived from the checkboxes, no separate pointer. The
`← current` marker is only a reader's hint.

```markdown
# Roadmap — <product>

<!-- managed by chart-it · edit freely, chart-it re-reads this · captured: <YYYY-MM-DD> · North Star → CLAUDE.md -->
<!-- VERSIONS over STAGES: versions (v0,v1,…) are the product's milestones; inside each, `## Stage` bands run in order, milestones within a stage are parallel (any order). -->
<!-- Frontier = unchecked milestones of the earliest `## Stage` in document order that still has any. No stage headings = legacy line. -->

# v0 — <name> · <one line: what the product is/looks like at v0>

## Stage 1 — <theme> ← current (earliest stage with unchecked work)

- [ ] M1 — <feature> · done when: <observable outcome> · theme: <one line>

## Stage 2 — <theme> (parallel — any order within the stage)

- [ ] M2 — <feature> · done when: <observable outcome> · theme: <one line>
- [ ] M3 — <feature> · done when: <observable outcome> · theme: <one line>

# v1 — <name> · <one line>

## Stage 3 — <theme>

- [ ] M4 — <feature> · done when: <observable outcome> · theme: <one line>
```

Ids stay **stable across re-runs** (semipilot/autopilot reference them) and are independent of which
stage or version a milestone sits in. **No `## Stage` headings at all = legacy line** = each milestone
is its own stage = the frontier is always the first unchecked box (old linear behaviour, unchanged).

---

## Re-run = revise (the roadmap is a living artifact)

A re-run: **re-survey** "now" (Phase 1) → **show the roadmap + progress** (which milestones' `done
when:` now hold, where the frontier sits) → **propose adjustments** one decision at a time (check off
completed, add/split/reorder milestones, stages, or whole versions, drop the obsolete) → **rewrite**
`roadmap.md`, urging a review per touched version. Keep ids stable. `--reground` is the same idea for
the North Star.

---

## Quick reference

`0` Goal — detect `## Product North Star`; absent → **open questions, no options** → write the block
yourself · `1` Survey — repo = "now" · `2` Version loop — for v0, v1, v2, … (min three before offering
to finish): `AskUserQuestion`-led "what's in this version?" → break its features into ordered `## Stage`
bands (_order → split stages; independent → same stage_) with stable `Mn` ids + observable `done when:`
→ **write the version to `roadmap.md` and urge a review** → next version or finish · re-run = revise
the living roadmap.

**Invariant:** chart-it owns the North Star write and versions the route; it never decides a fork
(grill-it) or builds a task (implement-it). The roadmap only _biases_ point-it — it never gates it.
