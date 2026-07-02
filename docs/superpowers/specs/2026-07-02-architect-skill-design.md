# Architect skill + diagram reference skills — design

## Purpose

Add a conversation-driven system-design capability to the harness that produces **mostly
diagrams** (with a little connecting text), plus the deep tool knowledge it needs to draw them
well.

Two deliverables:

1. **`architect`** — a skill in `cc-script`, placed in the funnel after the roadmap step. One
   mode: it designs a *new* system together with the user, driven by the user's words, and
   emits diagram files. It never reads the project's code.
2. **Three reference skills** in `cc-instruments` — `mermaid`, `likec4`, `excalidraw`. Each is a
   deep how-to for one diagram format. They have **no slash command**; they exist to be pulled
   in as knowledge when a diagram of that kind is being built.

## Non-goals (explicit)

- **Not** reverse-engineering or explaining an existing codebase. "Walk into an unfamiliar
  project and explain everything with diagrams" is a **separate, later skill** — that is where
  code analysis (codegraph, tree-sitter, dependency graphs) would live. None of that is built
  here.
- The architect **never reads project code**. Context about existing code comes from the user in
  conversation. It may anchor on the roadmap / North Star goal document if present, since that is
  a goal artifact, not code.
- No diagram-rendering pipeline that requires a headless browser is built. Viewing happens in the
  user's VS Code (LikeC4 and Excalidraw extensions) or on GitHub (Mermaid, `.excalidraw.svg`).

## Component 1 — reference skills in cc-instruments

Three command-less skills:

```
plugins/cc-instruments/skills/mermaid/SKILL.md
plugins/cc-instruments/skills/likec4/SKILL.md
plugins/cc-instruments/skills/excalidraw/SKILL.md
```

Each has frontmatter (`name`, `description`) and a body that is a practical, deep guide to
building great diagrams in that format. **No `commands/*.md` file** for any of them — they are not
user-invoked; the `description` is written so the model loads the skill when it is building a
diagram of that type, and the architect loads them explicitly (see below).

Each guide covers: the syntax and every diagram type worth using, idioms for clear diagrams, how
the user views the result, and the install / degradation reality.

- **mermaid** — the zero-install baseline. Renders natively in GitHub markdown and VS Code, no
  tooling required. LLM-native. Cover flowchart, sequence, class, ER, state, and note the
  experimental C4/architecture types honestly.
- **likec4** — a DSL for C4 architecture as code: one model, many consistent views, drill-down
  between them. Cover the `specification` / `model` / `views` blocks, dynamic and deployment
  views, and the `npx likec4` CLI (`start`, `build`, `gen mermaid`). Viewing: the LikeC4 VS Code
  extension; degradation path: `likec4 gen mermaid` for a GitHub-viewable fallback.
- **excalidraw** — hand-drawn-style freeform sketches. Be honest: raw `.excalidraw` JSON is
  painful and error-prone to author by hand; the reliable path builds the scene through a small
  Node helper (`convertToExcalidrawElements` from `@excalidraw/excalidraw`). Save as
  `.excalidraw.svg` so the file both renders on GitHub and stays editable in the
  `pomdtr.excalidraw-editor` VS Code extension. State plainly that Excalidraw is the one format
  that is **not** LLM-native and needs Node.

## Component 2 — architect skill in cc-script

```
plugins/cc-script/skills/architect/SKILL.md
plugins/cc-script/commands/architect.md      # /architect
```

**Behavior — one mode, conversational:**

1. Anchor on the goal: read the roadmap / North Star if present; otherwise start from the user's
   words. Never read project code.
2. Design collaboratively — draw out what the user wants to build through conversation
   (user-led), not by inventing a full system unprompted.
3. Choose the format(s) per need:
   - structured architecture, layered (context → containers → components) → **LikeC4**
   - freeform sketch the user will move around by hand → **Excalidraw**
   - quick, portable, or fallback → **Mermaid**
4. Before drawing, **explicitly load the matching reference skill** from cc-instruments — do not
   rely on ambient auto-pickup, or the deep syntax knowledge silently won't be present.
5. Produce **mostly diagrams**; text is minimal — connective tissue and rationale only, not prose
   walls.
6. Iterate with the user on their feedback.
7. Save output to `docs/architecture/`.

**Funnel placement:** after the roadmap step (find-goal / roadmap-management), before what-to-do.
The chain becomes: set the goal (roadmap) → **design the architecture (architect)** → decide what
to do (what-to-do) → build (do) → harden (refactor-review-test). It is an optional design step,
not mandatory on every run. Update the cc-script README funnel description to include it.

## Cross-plugin dependency

The architect (cc-script) leans on the three reference skills (cc-instruments). If cc-instruments
is not installed, the architect **degrades to Mermaid**, which needs nothing installed and renders
everywhere. The skill states this fallback explicitly.

## Testing

Per the repo's testing philosophy (prose-pinning vs contract): these are prose skills with no
machine-parsed string contracts, so no reflexive prose-invariant tests are added. Add a test only
if a real string contract emerges during implementation.

## Wiring & versions

- Skills are auto-discovered from the `skills/` directories; only `architect` gets a command file.
- Bump `cc-instruments` (three new skills) and `cc-script` (new skill + command + README edit)
  minor versions in their `plugin.json`.
