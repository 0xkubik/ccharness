---
name: refactor
description: "Use to reshape working code toward the do writing rules WITHOUT changing what it does — gate that it works, find where the rules are violated, fix them, gate that the logic is unchanged. Runs before/after /do or standalone. Triggers: \"refactor this\", \"clean up\", \"tidy the structure\"."
argument-hint: "[what to refactor — omit for the last change]"
---

# refactor — enforce the rules, preserve the behavior

You take working code and reshape it to obey the **`do` writing rules** — **without changing what it
does**. You APPLY every change yourself. A gate proves the code works before you start; a gate proves
the logic is unchanged before you finish.

**Invariants — non-negotiable:**
- **Behavior-preserving.** A refactor never changes *what* the code does. Behavior changes only as a
  deliberate bug-fix or a product decision — never a side effect of cleanup. (Bug-finding is `review`.)
- **Bounded to the change.** Your remit is what you were handed, plus structural work *this* change
  genuinely warrants. Not "improve the whole repo." No gold-plating.
- **Apply, don't report.** You make every fix yourself; a findings list handed up is a failure.
- **3 strikes on one problem → `cc-tools:slap`, then pick the fresh approach yourself.**

---

## Gate — the code must already work

You reshape **working** code only. Confirm it runs before you touch it — build / boot / existing tests
green / a smoke check. Evidence, not assumption.

- **It works** → proceed.
- **It's broken** (won't build, tests red, doesn't run) → **not a refactor job.** A refactor has
  nothing to preserve yet. Fixing broken behavior is `review` (bugs) or `do` (unbuilt) — route there.

---

## Map the codebase

See where the code sits before you touch it — you reshape well, and spot reuse, only once you can
place it. Mechanical, so **dispatch it to a subagent on the `haiku` model** and work from its map:

- **Study the code** — **codegraph** if indexed (else **grep**) for modules, dependencies, call
  relationships.

---

## Lay the safety net

- **Get existing tests green** (whatever's there). A red baseline is fixed *now*, before touching anything.
- **Write characterization tests on the core logic** to pin its *current* behavior. This net is what
  lets you reshape without silently moving behavior — it is the before-half of the exit gate.
- Not full coverage — just the net. Comprehensive coverage is the `test` stage.

---

## Refactor to the `do` rules

Read the **writing rules in `cc-pipeline:do`** — they are the standard this code must meet. Walk the
code against each, **find where it violates them**, and fix it in place:

- **Reuse** — duplicated logic, or a hand-rolled thing a library/existing module already does →
  collapse to the reuse.
- **Least code** — dead code, redundant paths, abstraction built for needs nobody has → cut.
- **Modular bricks** — a blob doing many jobs → split into single-purpose units with clear
  interfaces, then aggregate.
- **SOLID** — mixed responsibilities, fat interfaces, concretion-coupling → separate, narrow, invert.
- **No comments** — comments restating *what* the code does → delete; let the name and structure
  carry it (keep only genuine *why*).
- **Graded logs** — missing, one-level, or past-tense logging → put graded present-tense logs on each
  action (`"doing X…"`, not `"did X"`).

Use **`/simplify`** and the **`code-simplifier`** agent as your eyes for clarity, dead code, naming,
nesting. Structural moves (split/move functions, move files) are fine **when this change warrants
them** — reason rooted in the work, not "tidy the repo." **The net stays green after every step** —
that green is your running proof behavior didn't move.

---

## Gate — before vs after: the logic is unchanged

Before you close, prove the reshape was behavior-preserving:

- **The net is green** — every characterization test still passes on the new shape.
- **Compare before ↔ after** — walk the change and confirm the *logic* is identical: same inputs →
  same outputs, same side effects, same order of external calls. Only *how* it's written moved.
- **Any divergence** = you changed behavior, not just structure. **Revert that step and redo it
  behavior-preserving** — a refactor that alters what the code does is a failed refactor, not a bug-fix.