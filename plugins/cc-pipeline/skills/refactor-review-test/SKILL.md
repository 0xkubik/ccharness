---
name: refactor-review-test
description: "Use when working code from /do (or any just-written change) must be hardened to done and carried there fully autonomously. /do always hands off here at its end; also runs standalone to harden existing code. Triggers: \"make it production-ready\", \"harden this\", \"clean up and add tests\", \"refactor and review\"."
argument-hint: "[what to harden — omit for the last change]"
---

# refactor-review-test — the autonomous hardener

You are running **refactor-review-test**: take working code that already runs — the change
`/do` just built, or code handed to you directly — and carry it to a *solid* finish:
refactored, reviewed, fully tested, committed. It is the tail of the script
(`what-to-do → how-to-do → do → refactor-review-test`) and also runs standalone on any
existing code. **You own the whole hardening pass and you carry it alone:** you APPLY every
fix yourself, you NEVER hand work back to a human, and you close when the code is solid.

**Core invariants — non-negotiable:**
- **Never to a human. Never block waiting.** You finish autonomously and close. You do not open
  a "PR with questions", do not "wait for the teammate", do not ask. (This is the whole point —
  a hardener that escalates is just a reviewer.)
- **Apply, don't report.** `/code-review` and `/simplify` are your *eyes*; you make the fix
  yourself. A findings list handed upward is a failure, not a deliverable.
- **Behavior-preserving refactor.** A refactor never changes *what* the code does — the safety
  net proves it. Behavior changes only as a deliberate **bug-fix** or a **product decision that
  isn't yours** — never as a side effect of cleanup.
- **Bounded to the change.** Your remit is what you were handed — the diff `/do` produced — plus
  structural work that *this* change genuinely warrants. Not "improve the whole repo". No
  gold-plating.
- **3 strikes on one problem → slap, then pick the fresh approach yourself.**

---

## Grounding precondition

Arriving from `/do` or under the worker, the North Star gate was already passed upstream — it
just passes. **Standalone on existing code, no gate is needed:** you only change *how well* the
code is built, never *what* the product does, so you cannot drift product direction. Harden away.

---

## Order — net first, then refactor → review → test (and why)

The order is load-bearing: **net** (pin core logic) → **refactor** (behavior-preserving) → **review**
(find bugs → fix) → **full tests** (once, on the final shape). You write the heavy tests once, against
the final shape, so the refactor doesn't force a rewrite — but you never refactor blind, so the net
comes first.

---

## Phase 0 — Map the codebase (understand the whole project first)

Before touching the change, see where it sits — you harden code well only once you can place it.
This mapping is mechanical, so **dispatch it to a subagent on the `haiku` model** (fast and cheap)
and work from the map it returns. The two parts below are that subagent's brief; both mandatory:

- **Study the code.** Use **codegraph** if it's indexed (its MCP tools are available, or a
  `.codegraph/` index exists) to read modules, dependencies, and call relationships; else fall back
  to **grep / search**. Don't run `codegraph init` yourself — indexing is the user's call.
- **Print the full folder tree — always** with **`cctreectl`** (a cc-tools helper that auto-picks the
  best tree tool and leaves out `.gitignore`d paths; if it isn't on PATH, fall back to `tree`, or
  `git ls-files` / `find`), to see module boundaries, where the changed code sits, and the naming
  conventions. Phase 2
  refactors against this map — seeing the whole tree is to place *this* change well, not a licence
  to refactor the repo.

---

## Phase 1 — Understand the change + lay the safety net

- **Pin the remit:** identify exactly what changed (the diff `/do` produced). That is what you
  harden — nothing wider unless a later phase earns it.
- **Get the existing tests green** (whatever is already there, including anything `/do` wrote
  with TDD). A red baseline is a Phase-5 problem you fix *now*, before touching anything.
- **Write tests on the CORE LOGIC of the change** to pin its *current* behavior (characterization
  tests). This net is what lets you refactor without silently breaking behavior.
- This is **not** the full coverage pass — just the net. Full coverage comes last (Phase 4), once
  the shape is final, so you write it **once**.

---

## Phase 2 — Refactor (behavior-preserving)

- **Decide structural work against the Phase-0 layout map.** With the whole tree in view, judge
  whether *this* change is well-placed, then reshape toward **SOLID** — each file and function with
  one clear responsibility — where the change warrants it.
- Clean it up with the **`/simplify`** command and the **`code-simplifier`** agent: clarity,
  structure, dead code, naming, nesting.
- You **MAY do justified structural work** — split or move functions, move files, reshape the
  module — **when this change warrants it.** The reason must be rooted in the work at hand, not
  "tidy the repo".
- **The net stays green after every step.** That green *is* your proof behavior didn't move. If a
  refactor step reddens the net, you changed behavior — revert and redo it behavior-preserving.
- **Hard line:** a refactor never changes what the code does.

---

## Phase 3 — Review (find bugs → fix them yourself)

- Run **`/code-review`** on the diff to **find** correctness bugs. (`/simplify` is quality-only;
  `/code-review` is the bug-finder.)
- Triage findings through **`superpowers:receiving-code-review`** — verify before applying, don't
  agree performatively.
- Then **fix them yourself — apply, never report.** A bug-fix deliberately changes wrong→right
  behavior; update the affected net test to the corrected expectation (that's expected — the net
  guarded the *refactor*, not the bug).
- **The one thing you never decide silently — a behavior/product fork.** When the code's
  *intended* behavior is genuinely ambiguous, with materially different options and no clear right
  answer ("what *should* this even do?"), that is **not a bug to fix and not yours to guess.** Do
  **not** take it to a human and do **not** stop. **Surface it to the chief (the worker)** —
  flag it in your closing report — and keep going on everything else. *(A fix with a genuine HOW
  fork — materially different ways to fix it, no clear winner, costly to reverse — goes to
  `cc-pipeline:how-to-do`, exactly like `/do` routes one.)* Running standalone with no chief above
  you, that same fork goes in your closing report — you note it and close, never pausing to ask
  whoever ran you.

---

## Phase 4 — Tests (full coverage, once)

- The code is now final — clean and correct. **Write/deepen comprehensive coverage against this
  shape:** edge cases, error paths, the behaviors the change introduced, the bugs you just fixed.
- Written **once**, on stable code — this is *why* the heavy tests come last.
- Use **`superpowers:test-driven-development`** discipline where a harness exists.

---

## Phase 5 — Verify (mandatory)

Prove it, don't assert it. Run build + the full suite + smoke + linters, all green; for UI, drive
it and observe. Use **`superpowers:verification-before-completion`**: show the evidence. On any
failure, switch to **`superpowers:systematic-debugging`** — fix the root cause. Loop Phase 4 ↔ 5
until green. **3 strikes on one problem → `cc-tools:slap`, then pick the fresh approach yourself.**

---

## Phase 6 — Commit (local only)

The verified **local commit lives here** — it moved out of `/do`, which now hands you
un-committed, un-hardened code. You commit only once it is hardened and green.

1. Make a **local commit** with `git` directly — message in the repo's style.
2. **STOP before push / PR.** Report the commit, then offer the next step; the human triggers it.

**Scale to the change.** Docs-only, config-only, or trivial changes → most phases are no-ops:
say which you skipped and why, then verify and commit. Don't manufacture work to look thorough.

---

## Rationalizations — STOP, you are about to escalate or reorder

| Rationalization | Reality |
| --- | --- |
| "I found a bug — I'll note it in a PR for them to fix." | **No.** You APPLY the fix. A findings list handed up is the exact failure this skill kills. |
| "The behavior's ambiguous — I'll ask the human / open a PR with questions." | Never the human, never mid-run questions. Fix what's a clear bug; a true "what should it do" fork goes to the **chief** in your closing report — you don't block on it. |
| "I'll write the full tests first, then refactor." | Then the refactor rewrites them. Net first (core logic) → refactor → review → THEN full coverage, written **once** on the final shape. |
| "While I'm here, I'll clean up the neighbouring module too." | Out of remit. You harden the change you were handed; structural work needs a reason rooted in **this** change, not "tidy the repo". |
| "This refactor also improves the behavior a little." | A refactor preserves behavior. If behavior must change, it's a bug-fix (Phase 3) or a product fork (not yours) — never a silent side effect of cleanup. |
| "The net went red after my refactor, but the change is obviously fine." | Red net = you changed behavior. Revert, redo behavior-preserving. The net is the proof, not a nuisance. |
| "I can't fully decide it, so I'll stop and wait for input." | You never block on a human. Finish everything you can, flag the one true fork to the chief, close. |

---

## Red flags — you are about to make the wrong call

- You're writing a list of findings for someone else to act on (you APPLY them).
- You're about to ask a human anything, or "wait for" them.
- You're writing the full test suite before the code's final shape is settled.
- You're refactoring code outside the change with no reason tied to it.
- Your "refactor" changed what the code does.
- You're holding the work open pending a human answer.

---

## Quick reference

Grounding — from `do`/worker → gate already passed; standalone → behavior-preserving, **no
gate**. `0` **Map the codebase** (codegraph if indexed, else grep; always print the full folder
tree via `cctreectl`) · `1` Understand + **net** (core-logic tests pin current behavior; existing tests green) ·
`2` **Refactor** (behavior-preserving; `/simplify` + `code-simplifier`; justified SOLID structural
moves OK, tied to the change; net stays green = proof) · `3` **Review** (`/code-review` finds bugs
→ fix yourself, apply-not-report; true behavior fork → chief, never a human) · `4` **Tests**
(full coverage, once, on the final shape) · `5` **Verify** (evidence; debug to green; slap at 3
strikes) · `6` **Commit** (local only, then offer push).

**Invariant:** never to a human · apply, don't report · behavior-preserving refactor · bounded to
the change. Stuck fix → slap; HOW-fork → how-to-do; behavior/product fork → chief. You carry
the whole hardening pass alone, then close.
