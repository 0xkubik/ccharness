# Fix the root cause, not the symptom — treat the disease, not the fever

A failing test, an error in the log, a wrong value on screen — those are symptoms. The common failure
is to silence the symptom and call it fixed: wrap the throw in a `try/catch`, special-case the one
input that broke, retry until the flake passes, loosen the assertion. The visible complaint goes
away, the actual defect stays, and it resurfaces later wearing a different face. Fix the thing that
produces the symptom, not the symptom.

- **Diagnose before you touch.** Understand *why* the wrong behaviour happens — which invariant broke
  and where — before changing a line. A fix you can't explain the cause of is a guess, and a guess
  usually just moves the symptom.
- **Trace the symptom to its source.** Follow the chain backwards to the first point where reality
  diverges from what the code assumes. That origin is where the fix belongs, even when it's further
  up than where the error surfaced.
- **These are symptom-patches, not fixes** — a `try/catch` that swallows an error instead of
  preventing it, a branch handling the one value that happened to break, a `sleep`/retry papering
  over a race, a null-guard where the null should never have existed, an assertion relaxed to match
  buggy output. If your change makes the complaint disappear without explaining why it occurred,
  you patched a symptom.
- **One cause, many symptoms.** A single root defect often shows up in several places. Once you fix
  the cause, check whether nearby glitches you'd written off were the same bug — and whether removing
  it lets you delete the patches that were compensating for it.
- **When you genuinely can only treat the symptom, say so.** Sometimes the real cause is out of reach
  — a third-party bug, a deadline, a risky change deferred by choice. That's legitimate, but name it:
  mark the workaround as a workaround pointing at the underlying cause, don't present it as a fix.
