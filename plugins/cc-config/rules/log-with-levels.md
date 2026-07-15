# Log with graded severity — give each message the level it deserves

Code that logs everything at one level — or only with bare prints — is useless when it matters: at 3am
you can't tell a routine step from the failure that broke the run. Whenever you add logging, **grade it**:
pick the severity that matches what the message actually means, so the important lines stand out and the
noise can be filtered away.

- **Use the project's logger, not bare output.** Reach for the language or framework's logging facility
  and its level API — not `print` / `console.log` / `echo`. Match whatever the codebase already uses.
- **Pick the level by what the message means:**
  - **error** — an operation failed and something needs attention.
  - **warn** — recovered or degraded, but suspicious; worth noticing.
  - **info** — a normal, meaningful milestone (started, finished, connected).
  - **debug** — detail useful only while diagnosing; silent in normal runs.
- **Log at boundaries and failures, not every line.** The start and end of a real operation, external
  calls, and caught errors — not a running commentary on ordinary control flow. Logging is not commenting.
- **Give the message context, not just a value.** Say what happened plus the key identifiers ("checkout
  failed for order 42: upstream timeout") so a single line is useful without the surrounding code.
- **Never log secrets, and keep bulky dumps at debug.** Credentials, tokens, and personal data stay out
  of logs entirely; large diagnostic payloads go behind `debug`, never `info`.
