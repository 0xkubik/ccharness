---
description: "Design a new system or feature with the architect — a conversation-driven design loop that turns your intent into architecture diagrams (mostly diagrams, a little text). Sits after the roadmap in the script: set the goal → design the architecture → decide what to do → build. It never reads your code; you bring the context in words. It draws in LikeC4 (structured, layered C4), Excalidraw (freeform sketches), or Mermaid (quick, zero-install), leaning on cc-instruments' diagram references."
argument-hint: "<what you want to design>"
---

Invoke the `architect` skill with what you want to design:

> $ARGUMENTS

The architect designs a **new** system or feature **with you**, led by your words, and emits
**mostly diagrams, a little text**. It sits in the script after `/roadmap-management`: set the goal
→ **design the architecture** → `/what-to-do` → `/do`. It **never reads your code** — bring the
context in words. It picks the format per need — **LikeC4** for structured, layered architecture,
**Excalidraw** for freeform sketches, **Mermaid** for quick and zero-install — and draws on
cc-instruments' diagram references. Diagrams are saved to `docs/architecture/`. If cc-instruments
isn't installed, it falls back to Mermaid, which renders everywhere with nothing installed.
