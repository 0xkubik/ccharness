# Handle errors loud and at the root — fail fast, fix the cause not the symptom

An error is information. Two failures waste it: swallowing it when you write (a catch that ignores, a
silent empty return) and patching its symptom when you fix (a `try/catch` around the throw, a retry
over a flake). Both hide the defect so it resurfaces later wearing a different face.

- **Fail fast, don't swallow.** Validate at the boundaries and surface errors with context, then let
  them propagate. Never catch-and-ignore, never return a silent empty — an operation that can't do its
  job says so loudly.
- **Diagnose before you touch, then fix at the source.** Understand *why* the wrong behaviour happens
  — which invariant broke and where — and trace it back to the first point where reality diverges from
  what the code assumes. That origin is where the fix belongs. A fix you can't explain the cause of is
  a guess.
- **These are symptom-patches, not fixes** — a `try/catch` that swallows instead of preventing, a
  branch handling the one value that broke, a `sleep`/retry papering over a race, a null-guard where
  the null should never exist, an assertion relaxed to match buggy output. If the complaint disappears
  without explaining why it occurred, you patched a symptom.
- **One cause, many symptoms.** A single root defect often surfaces in several places. Once you fix the
  cause, check whether nearby glitches were the same bug — and delete the patches that were
  compensating for it.
- **When you can only treat the symptom, say so.** Sometimes the cause is out of reach — a third-party
  bug, a deadline, a risky change deferred by choice. Legitimate, but name it: mark the workaround as a
  workaround pointing at the cause, don't present it as a fix.
