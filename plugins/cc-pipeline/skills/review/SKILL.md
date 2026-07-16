---
name: review
description: "Use to hunt a change for edge cases, vulnerabilities, and correctness bugs — fan out three hunters, verify each finding is real, then FIX it yourself. Never hands a findings list upward. Runs after refactor or standalone. Triggers: \"review this\", \"find bugs\", \"security check\", \"edge cases\"."
argument-hint: "[what to review — omit for the last change]"
---

# review — hunt edge cases, vulns, bugs; fix them

You hunt the change across **three axes — edge cases, vulnerabilities, bugs** — **verify** each
finding is real, and **fix it yourself**. Finding is your *eyes*; the fix is your hands.

**Invariants — non-negotiable:**
- **Verify before you fix.** A finding is a hypothesis until you confirm it reproduces. A fix applied
  to a non-bug is a *new* bug. Triage through `superpowers:receiving-code-review` — no performative
  agreement.
- **Apply, don't report.** You make every fix yourself. A findings list handed up is a failure.
- **Bounded to the change** — the diff you were handed, not the whole repo.

---

## Step 1 — Fan out three hunts (parallel subagents)

Dispatch three subagents in parallel, one per axis, each on the **`sonnet` model**, scoped to the
change. Each hunts hard in its lane and returns findings in the contract below.

- **EDGE** — boundaries and the unexpected: empty / null / zero / one, off-by-one, overflow &
  truncation, unusual or malformed input, ordering & concurrency, partial failure & retries, resource
  exhaustion, timezone / encoding / locale.
- **VULN** — security: injection (SQL / command / path / template), authz & authn gaps, secrets in
  code or logs, unsafe deserialization, SSRF / open redirect, missing input validation, unsafe
  defaults, TOCTOU, risky dependency use.
- **BUG** — correctness: wrong logic, mishandled or swallowed errors, state / lifecycle mistakes, race
  conditions, wrong API contract, leaks. Use **`/code-review`** as this lane's eyes.

**Each hunter returns** (0–N findings):

```
axis:      EDGE | VULN | BUG
findings:  [ {
  title:    <short name>
  where:    <file:line / function>
  what:     <the defect: input/state → wrong outcome>
  severity: high | med | low
  trigger:  <concrete input/condition that hits it>
  fix:      <the correction>
} ]
empty_reason: <if findings == [] : why this lane is clean here>
```

Empty-lane valve: a lane with nothing real says so — **inventing a finding to fill a slot is a bug.**

## Step 2 — Verify (adversarial, one pass)

Main thread, on your stronger model. For each finding, **try to refute it** before you trust it:
does the trigger actually reach the defect, or is it guarded upstream? Confirm it reproduces (a test,
a trace, or a tight argument). Dedupe overlaps across lanes. **Kill false positives** — carry only
confirmed findings forward, ranked by severity.

## Step 3 — Fix (apply, never report)

Fix each confirmed finding yourself. A bug-fix deliberately changes wrong→right behavior; if a safety
net exists (from `refactor`), update the affected test to the corrected expectation.

- **Behavior/product fork** — the code's *intended* behavior is genuinely ambiguous ("what *should*
  this do?"), materially different options, no clear answer → **not yours to guess.** Never a human,
  never stop: flag it to the **chief** in your closing report and keep going. Standalone, no chief →
  note it in the report and close.
- **A fix with a genuine HOW fork** — materially different ways to fix, no clear winner, costly to
  reverse → `cc-pipeline:how-to-do`.
