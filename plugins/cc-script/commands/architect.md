---
description: "Design a new system or feature with the architect — a conversation-driven design loop that turns your intent into architecture diagrams (mostly diagrams, a little text). It first asks what the diagram is for and how deep it should go, then interviews the design out of you. Sits after the roadmap in the script: set the goal → design the architecture → decide what to do → build. It never reads your code; you bring the context in words. By default the whole design lives in one unified LikeC4 .c4 file, detail reached through component nesting; other formats only if you ask."
argument-hint: "<what you want to design>"
---

Invoke the `architect` skill with what you want to design:

> $ARGUMENTS

The architect designs a **new** system or feature **with you** and emits **mostly diagrams, a little
text**. Like `/roadmap-management`, it **interviews you first** — one decision at a time — and draws
the design out of you, confirming the shape before it draws a thing; it never runs ahead. It **starts
by asking what the diagram is for and how deep it should go** (Context / Container / Component / Code),
holds that level as the ceiling, and records it in the model. It sits in the script after
`/roadmap-management`: set the goal → **design the architecture** → `/what-to-do` → `/do`. It **never
reads your code** — bring the context in words. **By default the whole design lives in one unified
LikeC4 `.c4` model** — from the system down to whatever level you agreed — with all detail reached
through component nesting; it reaches for **Mermaid** (leaf detail that can't fold in — a class's
fields, a call sequence, a DB schema) or **Excalidraw** (freeform sketches) **only if you ask**.
Diagrams are saved to `docs/ccharness/architecture/`. If cc-instruments isn't installed, it falls back
to Mermaid, which renders everywhere with nothing installed.
