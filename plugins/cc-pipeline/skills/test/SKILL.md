---
name: test
description: "Use to cover a change with high-value tests on the final, settled code — quality over quantity, tested from the outside, fast, with shared fixtures. Prunes stale tests too. Runs after review or standalone. Triggers: \"add tests\", \"cover this\", \"write the tests\"."
argument-hint: "[what to test — omit for the last change]"
---

# test — high-value coverage, not test count

You cover the change with **the fewest tests that buy the most confidence**, written against the
**final** shape (after `refactor`/`review`, so you write them once). Quality is the goal — a big test
count is not.

**Invariants — non-negotiable:**
- **Coverage, not count.** Confidence per test is what matters; padding the number is a bug.
- **Bounded + scaled to the change.** Cover what the change introduced and the bugs just fixed, not
  the whole repo. Trivial / docs / config change → little or none; say what you skipped and why.
- **3 strikes on one problem → `cc-tools:slap`, then pick the fresh approach yourself.**

---

## The test-writing rules

- **Fewer tests, more coverage.** Choose the tests that each buy the most confidence — one good
  behavioral test beats ten redundant ones. Cover the space, don't tile it.
- **Test the most important functionality.** Critical paths, the behaviors that hurt most if they
  break, and the bugs `review` just fixed — first and hardest. Not every trivial getter.
- **Test from the outside.** Assert on **public behavior** — inputs → outputs and observable effects
  through the public interface — never on internal variables or private structure. Renaming a
  variable inside a function must **not** break a test. Black-box tests survive refactors *because*
  they don't know the internals.
- **Fixtures and helpers.** Factor setup into shared **fixtures and helpers** — build the world once,
  reuse it. No copy-pasted setup; each test reads as one clear intent.
- **Fast.** Tests must run fast — in-memory over I/O, fakes over network, the narrowest level that
  buys the same confidence. A slow suite stops being run.
- **Prune and edit old tests.** The suite is code — maintain it. **Delete** tests that no longer earn
  their place (duplicated, covering removed behavior, brittle from coupling to internals); **update**
  the ones whose expectations changed for a real reason. Fewer honest tests beat a green wall of dead
  and brittle ones.

Follow the project's existing harness and conventions; use **`superpowers:test-driven-development`**
discipline where one fits.

---

## Make it green

Run the suite — the new tests and the whole set — and get it **green**, fast. A test that can't pass
against correct code is a bad test, not a bug; fix the test. On a genuine failure, root-cause via
`superpowers:systematic-debugging`.