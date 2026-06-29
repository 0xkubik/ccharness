---
name: find-goal
description: Use when setting up or revising a product's long-horizon direction — the grounding loop that sets the goal and lays out the road to it as an ordered feature list.
---

# find-goal — set the goal, then lay out the road to it

You are the harness's grounding front door: you guide a human to **set the product's goal** (the
**North Star**) and **lay out the route to it** as a **flat, ordered list of features** — both written
to `.claude/ccharness/roadmap.md`, the goal at the top and the features below it, built top to bottom. This is a
**high-stakes conversation**, not a form — every later step builds on it: what-to-do ranks moves
against the goal, the musician builds straight from the roadmap, so a sloppy goal or vague feature
aims every automated step at the wrong target. Run once up front (other product skills route here
when no goal exists); re-run to revise.

**Tell the human this up front, plainly:** this defines what we're building and the order we build it;
many later steps (manual and automated) depend on it; it's worth slowing down for. Then run a real
guided interview — lead with questions, one decision at a time, until the picture is sharp.

**How you ask:**

- **The global goal: ask open questions — do NOT offer pre-baked options.** The goal must come from
  the human's own head, so use plain conversational questions, one at a time. Never hand them a menu
  of product visions to pick from.
- **The features: use `AskUserQuestion`** to ask leading questions with concrete options (plus the
  free-text fallback). This is where you actively steer — "which feature is the core, the very first
  to build?", "does X come before Y, or are they independent?".
- **One decision at a time** (borrow `superpowers:brainstorming`'s technique). The terminal is
  `.claude/ccharness/roadmap.md` — not `writing-plans`.

---

## Phase 0 — The global goal (the North Star) — ask, don't offer

**Detect first.** Look for a `## Product North Star` heading at the top of `.claude/ccharness/roadmap.md`.

| State       | Path                                                                     |
| ----------- | ------------------------------------------------------------------------ |
| **Absent**  | Run the goal-setting questions below, then **write the block yourself**. |
| **Present** | This run is a revision — read it = the current goal, then see below.     |

When the goal already exists, treat the run as a revision, not a fresh start: show the current North
Star back and ask whether to **keep it or rework it** — rework → re-run the questions and overwrite the
North Star block (**leaving the feature list below it intact**); keep → leave it untouched. Either way
you then enter the feature loop, which revises the existing list rather than building from scratch.
**No flag for any of this** — re-running find-goal is always safe: it reads what exists and adapts.

The goal-setting dialogue — open questions only, no multiple-choice. Draw out, one question at a
time, in plain language: what does the finished product look like at the very end — who is it for, and
what does success look like? And **is it already in production (real users), or not yet?** Don't move
on until the answer is concrete. The durable artifact is this stable block — write it as the **opening
of `.claude/ccharness/roadmap.md`** (create the file if needed; full file shape in the format block
below), keeping the vision to **one to three sentences**:

```markdown
## Product North Star

<!-- managed by find-goal · edit freely, the harness re-reads this · captured: <YYYY-MM-DD> -->

<one to three sentences — how the finished product looks at the end, who it's for, what success is>

- **In production?** <yes — live users, move carefully · no — full carte blanche>
```

Confirm the written block back in one line. The goal is **mandatory**; it's what every other skill
detects (the `## Product North Star` heading). Then move into the feature loop.

---

## Phase 1 — Survey "now"

Build a short, factual picture of the current product from the repo: `README`, docs, recent
commits, scattered `TODO`/`FIXME`/stub markers. Two or three paragraphs, not an audit. This is the
"now"; the North Star is the "end"; the ordered features are the steps between them.

---

## Read the musician's proposals first (if any)

Before laying out the features, check `.claude/ccharness/roadmap-proposals.md`. As the musician works it
appends **forward-looking observations** there ("a later feature might need X") — it is barred from
editing the roadmap's goal/ordering layer itself, so this file is how its ideas reach you. Read it and
**surface each as a candidate input** to the feature loop below — never auto-apply; the human decides
what (if anything) lands. Once integrated or dismissed, clear/archive the file. Absent → skip.

---

## Phase 2 — List the features in order (the heart — a loop)

Build the route as a **flat, ordered list of features** — first to build at the top, last at the bottom.
Each feature is a lightweight milestone with a stable global id (`M1`, `M2`, … — continuous, assigned in
order) and `name + done when: <observable outcome>`. The `done when:` must be **observable** — that's
what later lets the musician judge it complete. There are no versions and no stages: **the order _is_ the
plan.** Work the list a few features at a time:

**1. Elicit the next feature(s) with `AskUserQuestion`.** Lead the human: "What's the very first thing
to build?", then "what comes after that?" Keep asking leading questions (with options + free-text), one
decision at a time, until the next feature's shape is clear: what it is, and the observable outcome that
means it's done. The single ordering rule: **need "A before B" → A goes higher in the list**; genuinely
independent features can sit in any order relative to each other — pick a sensible one.

**2. Write it into the roadmap, then urge a review.** Append the feature(s) to
`.claude/ccharness/roadmap.md` (format below) and **strongly suggest the human read it back before you
continue** — "Here's the list so far. Please check it — the musician will build straight off this, top to
bottom. Look right before we keep going?" Don't steamroll past their review.

**3. At each step, ask: continue, rethink, or finish?** Use `AskUserQuestion` to offer three paths:

- **Continue** → elicit the next feature(s) (back to step 1).
- **Rethink already-decided work** → **always offer this.** The human may have spotted a contradiction
  or changed their mind about an earlier feature (or the goal itself). Let them describe what they found,
  then **re-open and revise** the affected features and their order — and the North Star, if the goal
  moved — one decision at a time, rewrite `roadmap.md`, urge a fresh review, then resume. Better to
  re-examine now than build off a roadmap the human no longer believes.
- **Finish** → offered once the list credibly spans the route from "now" to the North Star; goes to
  Phase 3. Before that, only Continue / Rethink.

Iterate until the human is satisfied; reorder, split, or merge features as they react.

---

## Phase 3 — Independent review (a fresh pair of eyes)

When the human chooses to finish, don't just stop — **dispatch one independent reviewer subagent
(read-only)** to pressure-test the finished roadmap as a skeptic. Give it: the **North Star block** and
the **full `.claude/ccharness/roadmap.md`**. Ask it to judge:

- Does the ordered list form a **credible path** from "now" to the North Star — does building it top to
  bottom actually converge on the goal, with no missing feature in between?
- Does the **order respect real dependencies** — is anything placed before something it needs, or
  needlessly held back behind work it doesn't depend on?
- Is every **`done when:` observable**, and does it truly mean that feature is done?
- Name the **contradictions, gaps, and over- or under-scoped features** it finds.

Relay its assessment to the human in plain language and offer to act on it — re-open the loop to
revise the flagged features or the goal, or accept as-is. The review is **advice, not a gate**: the
human decides. Then stop.

---

## The roadmap format (the contract — keep it exact)

Write `.claude/ccharness/roadmap.md` (create the directory if needed). The file **opens with the North
Star** (the goal — Phase 0's block), followed by a **flat, ordered checklist of features** — no
versions, no stages. **Document order is build order**: top to bottom. The **frontier** = the **first
unchecked `[ ]` box** — derived from the checkboxes, no separate pointer.

```markdown
# Roadmap — <product>

## Product North Star

<!-- managed by find-goal · edit freely, find-goal re-reads this · captured: <YYYY-MM-DD> -->

<one to three sentences — the vision>

- **In production?** <yes — live users, move carefully · no — full carte blanche>

---

<!-- Flat ordered feature list — build top to bottom. Frontier = the first unchecked [ ] box. -->

- [ ] M1 — <feature> · done when: <observable outcome>
- [ ] M2 — <feature> · done when: <observable outcome>
- [ ] M3 — <feature> · done when: <observable outcome>
```

Ids stay **stable across re-runs** (the musician references them) and are independent of where a feature
sits in the list — reordering a feature never renumbers it.

---

## Re-run = revise (the roadmap is a living artifact)

Re-running find-goal on a product that already has a goal or roadmap is a revision, not a restart —
and it needs no flag. A re-run: **re-survey** "now" (Phase 1) → **show the current goal, roadmap, and
progress** (which features' `done when:` now hold, where the frontier sits) → **propose adjustments**
one decision at a time (rework the goal, check off completed, add/split/reorder features, drop the
obsolete) → **rewrite** the affected parts of `roadmap.md`, urging a review. Keep ids stable.

**Reason about impact before you rewrite.** A revision ripples: reworking the goal can strand features
that no longer serve it; reordering or dropping a feature shifts the frontier and what the downstream
skills aim at. For each change the human proposes, say plainly what it touches and what follows — so
they revise with eyes open.

---

## Quick reference

`0` Goal — detect `## Product North Star`; absent → **open questions, no options** → write the block
yourself · `1` Survey — repo = "now" · `2` Feature loop — `AskUserQuestion`-led "what's the next thing to
build?", one decision at a time, in build order (_need A before B → A higher_) with stable `Mn` ids +
observable `done when:` → **write to `roadmap.md` and urge a review** → next feature or finish (once the
list credibly reaches the North Star) · re-run = revise the living roadmap.

**Invariant:** find-goal owns the North Star write and lays out the route; it never decides a fork
(how-to-do) or builds a task (do). The roadmap only _biases_ what-to-do — it never gates it.
