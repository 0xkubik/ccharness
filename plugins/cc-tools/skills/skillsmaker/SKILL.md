---
name: skillsmaker
description: "Use when writing or rewriting a SKILL.md in this repo. The house standard every skill here obeys: crisp sentences, bulletproof imperatives, small, concept-rules — never numbered stages — and no hardcode. Not what a skill does (its own job) but how it's written. Rules and concepts, not a fixed procedure."
argument-hint: "<the skill to write or rewrite>"
---

# skillsmaker — how a skill is written here

A skill is a **standing constraint**, not a script. It hands the model the invariants that must hold for
one kind of work, then trusts it to fly. Your one job: shape that constraint by the rules below — and
obey them in the skill you write, so it reads like its siblings.

## Rules & concepts — non-negotiable

- **Crisp sentences.** Short, declarative, one idea a line. Cut every word that carries no load. Density
  over prose — a lozenge beats a paragraph.
- **Rules, not stages.** State what must be **true**, never a numbered `1 → 2 → 3` of what to do next.
  Steps ossify and go stale; invariants hold. Name sections by concept (`Gate`, `Ground first`,
  `Rules & concepts`) — never `Step 1`. A skill that scripts the order is a checklist, not a skill.
- **Invariants first.** Open the body with the non-negotiables — a `## Rules & concepts — non-negotiable`
  block, or an `**Invariants — non-negotiable:**` line. Everything after serves them.
- **Small.** One screen — aim under ~70 lines. Past that you're explaining, not ruling. Cut, or split a
  sibling reference file out beside `SKILL.md` (a template, an example) and point to it by name.
- **Bulletproof.** Close every loophole: `never`, `always`, the one exception spelled out inline. A rule
  the model can rationalize around is not a rule. Route forks out instead of guessing; add a `## Litmus`
  the reader can self-check against.
- **No hardcode.** Name the **concept** — the target, the roadmap, the model — not baked-in file lists,
  magic values, or "then run X" the skill can't know. The invocation supplies the particulars. Hardcode
  rots; concepts hold. Only stable infra (a canonical path, a fixed subagent model) may be literal.
- **Bold lead-in per rule.** Every bullet opens with a two-or-three-word imperative in **bold**, then the
  rule. Skimmable at a glance, memorable as a slogan.
- **Frontmatter earns the load.** `name` is the invocation. `description` is the only line the router
  reads — pack it: open with **"Use when…"**, then the mechanism and what it guarantees. `argument-hint`
  shows what to pass (`<required>` vs `[optional]`). A pure reference drops `argument-hint`.
- **Self-exemplifying.** The skill obeys its own rules. One preaching brevity in a wall of prose is wrong.
- **English.** Identifiers, titles, prose — all English.

## Shape

```
skills/<name>/SKILL.md         # optional sibling: a template or example beside it

---
name: <one word>
description: "Use when … — <mechanism + what it guarantees, one packed sentence>"
argument-hint: "<what to pass>"     # omit for a pure reference
---

# <name> — <tagline>

<2–4 line opener: the identity, the one job, the trust.>

## Rules & concepts — non-negotiable
- **<Imperative>.** <the rule, crisp and closed.>
- …

## Litmus
<one or two self-checks the reader runs before shipping.>
```

## Litmus

- Strip the examples — does the model still know what's **forbidden**? Rules survive; prose doesn't.
- Delete any line — is a constraint lost? If not, it was filler. Cut it.
- Does it read like `Step 1 → 2 → 3`? Rewrite it as invariants.
