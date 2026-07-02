---
name: roadmap-management
description: Use to create OR maintain a product's roadmap (the North Star goal + ordered feature list in .claude/ccharness/roadmap.md) at any point in its life — set it up the first time, rethink it freely on a re-run, or fold in a single new feature (pass --force to formulate and write that feature after one confirm, skipping the discussion).
---

# roadmap-management — own the product's roadmap across its life

You own `.claude/ccharness/roadmap.md`: the product's **North Star** (the goal) at the top, and a
**flat, ordered list of features** (the route to it) in a `## Features` section below — plus three
capture sections (`## TODO`, `## Backlog`, `## Bugs`) shared with the `ccscriptctl roadmap add` helper.
Every later step builds on this file — what-to-do ranks moves against the goal, the musician builds
straight off the feature list — so a sloppy goal or vague feature aims every automated step at the
wrong target.

**This is not a run-once form.** You charter the roadmap the first time, and then you keep it honest as
the product changes: rethink it, or fold in a new feature, whenever the human comes back. So you run in
one of **four modes** — pick the right one before you do anything else.

**How you work (all modes):** lead with questions, **one decision at a time** (borrow
`superpowers:brainstorming`'s technique), in plain language. The terminal is
`.claude/ccharness/roadmap.md` — never `writing-plans`. You own the North Star write and lay out the
route; you never decide a fork (how-to-do) or build a task (do).

---

## Pick the mode first (dispatch)

Look at three things: is there already a `## Product North Star` at the top of
`.claude/ccharness/roadmap.md`? did the human bring **one concrete feature to add**, or just a general
"let's revise"? was **`--force`** passed?

| What you see                                                          | Mode                                                        |
| -------------------------------------------------------------------- | ---------------------------------------------------------- |
| **No North Star yet** (first run)                                    | **Mode 1 — Charter**: goal → features → review             |
| Goal exists · **no concrete feature** (empty prompt, or "rethink X") | **Mode 2 — Open revision**: free-form, no pipeline         |
| Goal exists · **one concrete feature** to add · no `--force`         | **Mode 3 — Add a feature**: think it through, record one line |
| Goal exists · one concrete feature · **`--force`**                   | **Mode 4 — Add a feature, fast**: formulate, show, one confirm, write |

**When you can't tell Mode 2 from Mode 3** — a prompt like "rethink the export flow" could be a general
revision *or* a single feature to add — **ask the human which**, don't guess and run the wrong pipeline.
`--force` only means anything with a concrete feature (Mode 4); passed with no feature, ignore it.

---

## Mode 1 — Charter (first run): goal → features → review

The roadmap doesn't exist yet. This is the full grounding interview — a **high-stakes conversation**,
not a form. Tell the human up front, plainly: this defines what we're building and the order we build
it; many later steps depend on it; it's worth slowing down for. Then run it in three steps. (If the
human arrived with a specific feature in mind, **don't discard it** — acknowledge it and fold it into
the charter; it becomes one of the features in Step 2, placed where it belongs.)

**Step 1 — Set the North Star (the goal). Ask open questions; do NOT offer pre-baked options** — the
goal must come from the human's own head. One question at a time, in plain language: what does the
finished product look like at the very end — who is it for, what does success look like? And **is it
already in production (real users), or not yet?** Don't move on until the answer is concrete. Then write
the North Star block (shape in **The roadmap file** below), keeping the vision to **one to three
sentences**, as the opening of `.claude/ccharness/roadmap.md` (create the file if needed). Confirm it
back in one line. The goal is **mandatory** — it's what every other skill detects.

**Step 2 — List the features in order.** First build a short, factual picture of the current product
from the repo (`README`, docs, recent commits, `TODO`/`FIXME`/stub markers) — two or three paragraphs,
the "now"; the North Star is the "end"; the ordered features are the steps between. Then loop, a few
features at a time, with `AskUserQuestion`:

1. **Elicit the next feature(s).** Lead: "What's the very first thing to build?", then "what comes
   after that?" Keep asking (options + free-text), one decision at a time, until the feature's shape is
   clear — concretely what it is. Ordering rule: **need "A before B"
   → A goes higher in the list**; genuinely independent features can sit in any order — pick a sensible one.
2. **Write it in, then urge a review.** Append the feature(s) — **one line each** (format below; never
   wrap a feature onto a second line or add sub-bullets) — and **strongly suggest the
   human read it back** — "the musician builds straight off this, top to bottom. Look right before we
   keep going?" Don't steamroll past their review.
3. **Continue / rethink / finish?** Offer three paths: **Continue** (next feature) · **Rethink** (re-open
   and revise earlier features, their order, or the goal — always offer this) · **Finish** (only once the
   list credibly spans the route from "now" to the North Star).

**Step 3 — Independent review.** When the human finishes, **dispatch one read-only reviewer subagent** to
pressure-test the roadmap as a skeptic. Give it the North Star block and the full `roadmap.md`. Ask it
to judge: does the ordered list form a **credible path** to the North Star, with no missing feature?
does the **order respect real dependencies**? is every feature **stated clearly enough to build**? what
are the contradictions, gaps, over- or under-scoped features? Relay it plainly and offer to act — the review is
**advice, not a gate**: the human decides. Then stop.

---

## Mode 2 — Open revision (re-run, no fixed pipeline)

The roadmap exists and the human wants to **rethink something** — not add one specific feature, just
look at what's there and change their mind. **No phases, no pipeline — the human drives; help them see
what they actually want.** Re-survey "now", then show them the current state: the North Star, the
feature list, and **progress** — which features are checked off, where the frontier (first unchecked
box) sits. Then revise whatever they raise — rework the goal, reorder, reword a feature, split or merge,
check off what's done, drop the obsolete — **one decision at a time**, writing each agreed change to
`roadmap.md`.

**Reason about impact before you rewrite.** A revision ripples: reworking the goal can strand features
that no longer serve it; reordering or dropping a feature shifts the frontier and what downstream skills
aim at. Say plainly what each change touches. Urge a read-back once you've changed
much. Stop when the human is satisfied — no forced review, no minimum.

**Triage the capture inbox.** `## TODO`, `## Backlog`, and `## Bugs` collect quick notes dropped in from
the terminal (`ccscriptctl roadmap add …`). On a revision, look them over: promote what belongs on the
route into `## Features` at the right spot, leave the rest where it is, drop the obsolete. This is the
only place raw captures get turned into charted features — one decision at a time, as always.

---

## Mode 3 — Add a feature (think it through, then record one line)

The human brought **one concrete feature** to add. Don't just append it — help them see it clearly first:

- **Why** — does it actually move the product toward the North Star? If it doesn't, say so plainly.
- **How** — the rough shape of building it, enough to phrase the feature concretely (not a plan).
- **When** — where in the ordered list it belongs: what must come before it, what it unblocks.

Then, **only if the human approves it**, append **one line** — `- [ ] <feature>` — at the right position
in the `## Features` list. Confirm the line back. If the thinking shows it's premature or
off-goal, don't force it into the list — drop it. The human decides.

---

## Mode 4 — Add a feature, fast (`--force`)

Same target as Mode 3 — add one feature — but the human wants it written **without the discussion. Skip
the why/how/when.** Formulate the feature yourself into one well-phrased line — `- [ ] <feature>` —
placed at a sensible position in the `## Features` list. **Then show the exact line and where it will
go, and ask "write this? (ok / not ok)".** Write it only on **ok**; on "not ok", take their correction.

`--force` skips the *discussion*, **never the confirm** — you formulate and propose, but you never
silently autowrite. One show-and-confirm gate always stands.

---

## The roadmap file (the contract — keep it exact)

`.claude/ccharness/roadmap.md` (create the directory if needed). The file **opens with the North Star**
(the goal), then **four sections in this fixed order — `## Features`, `## TODO`, `## Backlog`,
`## Bugs`** — each a checklist. `## Features` is the charted route: a **flat, ordered list** where
**document order is build order** (top to bottom) and the **frontier** = the **first unchecked `[ ]` box
under `## Features`** (no separate pointer). The other three are a **capture inbox** — quick notes
dropped in from the terminal with `ccscriptctl roadmap add todo|backlog|bug <text>`, for you to triage
onto the route on a re-run.

```markdown
# Roadmap — <product>

## Product North Star

<!-- managed by roadmap-management · edit freely, roadmap-management re-reads this · captured: <YYYY-MM-DD> -->

<one to three sentences — the vision: how the finished product looks, who it's for, what success is>

- **In production?** <yes — live users, move carefully · no — full carte blanche>

---

## Features

<!-- The charted route — build top to bottom. Frontier = the first unchecked [ ] box here. -->

- [ ] <feature>
- [ ] <feature>
- [ ] <feature>

## TODO

<!-- Near-term concrete tasks — also captured via `ccscriptctl roadmap add todo`. -->

## Backlog

<!-- Someday / maybe — also captured via `ccscriptctl roadmap add backlog`. -->

## Bugs

<!-- Known defects — also captured via `ccscriptctl roadmap add bug`. -->
```

**Each feature is exactly one line** — a single `- [ ] <feature>` and nothing else. No `done when:`
clause, no wrapping onto a second line, no sub-bullets, no indented notes, no multi-line description.
State the feature concretely enough to know it when it's built. If it won't fit on one line, it's too
big or too wordy: tighten the wording, or split it into two features — never spill it across lines.

Features are simply appended **in order** into `## Features` — no ids to assign or keep stable, tracking
is checkboxes only. `## TODO`, `## Backlog`, and `## Bugs` hold the same one-line `- [ ] <text>` shape
and are shared with `ccscriptctl roadmap add`. Every other skill detects grounding by the
`## Product North Star` heading.

---

## Quick reference

`dispatch` — no North Star → **Mode 1**; goal + no feature → **Mode 2**; goal + one feature → **Mode 3**
(or **Mode 4** with `--force`); can't tell 2 vs 3 → **ask** · **Mode 1** Charter — open-question goal
(1–3 sentences) → survey + feature loop (`AskUserQuestion`, one at a time, _need A before B → A higher_,
one line each `- [ ] <feature>` into `## Features`, urge review) → independent reviewer · **Mode 2** Open revision —
show goal + list + progress, triage the capture inbox, revise free-form, one decision at a time, reason about ripple · **Mode 3**
Add a feature — why / how / when → one line if approved · **Mode 4** `--force` — formulate → **show +
"ok?"** → write (never silent).

**Invariant:** roadmap-management owns the North Star write and lays out the route; it never decides a
fork (how-to-do) or builds a task (do). The roadmap only _biases_ what-to-do — it never gates it. Even
under `--force`, a feature is shown and confirmed before it's written.
