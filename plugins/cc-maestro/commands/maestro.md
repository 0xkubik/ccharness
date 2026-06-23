---
description: "Show the agent fleet — every Claude Code agent on this machine with its token burn, last activity, and a watchdog verdict (ok / stalled / looping / over-budget / died). Runs the ccmaestro console."
argument-hint: "(no arguments)"
---

# /maestro — the agent console

Run the ccmaestro dashboard and report the result.

Run this command and show the user its output verbatim:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/ccmaestro" ls
```

If the user asks for machine-readable output, run it with `--json`. Do not paraphrase
the table — the columns (tokens, verdict) are the point.
