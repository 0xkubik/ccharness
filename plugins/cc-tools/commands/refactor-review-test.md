---
description: "Hand working code (the change /do just built, or existing code) to the autonomous hardener — it carries it to a solid finish: safety-net tests, behavior-preserving refactor (/simplify + code-simplifier), review (/code-review) with fixes applied not reported, full test coverage, and a verified local commit. Fully autonomous — never hands work back to a human."
argument-hint: "[target]"
---

Invoke the `refactor-review-test` skill (the autonomous hardener) on this target (default: the
change `/do` just built / the current working change):

> $ARGUMENTS

It owns the whole hardening pass and carries it alone — net (pin core logic) → behavior-preserving
refactor → review with fixes **applied, not reported** → full test coverage → verify → **local
commit**. It **never hands work back to a human**: a stuck fix goes to `/slap`, a genuine HOW-fork
to `/how-to-do`, and a true behavior/product fork it flags to the conductor (the musician) in its
closing report — never as a mid-run question. It stops before push/PR and offers it; you trigger.
