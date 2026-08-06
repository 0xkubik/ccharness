---
name: slap
description: Reset approach when stuck in a debugging rabbit hole. Forces a step back to rethink the problem from scratch.
argument-hint: "[optional context about the bug]"
---

# STOP. Step back. Rethink.

You just got slapped. This means you've been digging deeper and deeper into a bug fix that isn't working. More of the same approach will not help.

## What you must do RIGHT NOW:

### 1. State the problem in one sentence

Write one clear sentence: what are you trying to achieve, and what exactly goes wrong?

### 2. List what you already tried

Bullet list of approaches you've attempted. Be honest — acknowledge what didn't work and why.

### 3. Question your assumptions

Ask yourself:

- Am I even looking at the right file / layer / service?
- Is the error message actually pointing to the root cause, or is it a symptom?
- Am I fighting the framework instead of working with it?
- Is there a version mismatch or config issue I'm ignoring?

### 4. Research alternatives

Before writing any more code:

- **Search the codebase** for how similar problems were solved elsewhere in this project
- **Search the web** for the exact error message or the pattern you're trying to implement
- **Check if a library exists** that solves this — don't reinvent the wheel
- **Look at how other projects** handle this same problem
- **Read the docs** for the tool/framework you're using — not StackOverflow, the actual docs

### 5. Propose a fresh approach

Present 2-3 alternative approaches to the user. For each:

- What would you do differently?
- Why might it work when the current approach doesn't?
- What's the trade-off?

## Rules after a slap:

- Do NOT continue with the same approach
- Do NOT add more workarounds or patches
- Do NOT say "let me try one more thing" with a variation of what you already tried
- DO take a fundamentally different angle
- DO ask the user if you're unsure which direction to go
