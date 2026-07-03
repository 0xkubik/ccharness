---
name: likec4
description: "Use when building a structured software-architecture diagram as code — C4-style context / container / component views with drill-down, one model producing many consistent views with automatic layout. Reach for it over Mermaid when the architecture is layered and you want a single source of truth. Viewed via the LikeC4 VS Code extension; generates Mermaid as a zero-install fallback."
---

# likec4 — architecture as code

LikeC4 is a small DSL for describing software architecture the C4 way (context → container →
component → code). You write **one model** of your system once; the tool renders **many interactive
views** from it — pan/zoom, and drill from a system down into its internals — with **automatic
layout**. You never place boxes by hand.

**Reach for LikeC4 over Mermaid when** the architecture is layered and you want a single source of
truth: one model, many views that stay consistent because they're all projections of the same
elements. Mermaid is per-diagram — each picture is drawn independently and drifts. LikeC4 is the
opposite: change the model once, every view updates. The cost is a real toolchain (Node) and that it
doesn't render inside GitHub markdown. If you need one throwaway diagram that renders in a README,
use the `mermaid` skill instead.

---

## The model — three blocks

Every `.c4` file is three blocks: `specification` (the vocabulary of element kinds you may use),
`model` (the actual elements and how they relate), and `views` (which projections to render) — plus
an optional `deployment` block for infrastructure (see View kinds below).

```
specification {
  element actor { style { shape person } }
  element system
  element component
}
model {
  customer = actor 'Customer'
  saas = system 'Our SaaS' {
    ui = component 'Frontend'
    backend = component 'Backend'
    ui -> backend 'calls over HTTPS'
  }
  customer -> ui 'uses'
}
views {
  view index { include * }        // landscape
  view of saas { include * }      // drill into one system
}
```

- **`specification`** — declares the *kinds* of element you're allowed to use (`actor`, `system`,
  `component` here) and their default styling. You must declare a kind before the model can use it.
  `style { shape person }` is what makes the actor render as a stick figure.
- **`model`** — the single source of truth. `customer = actor 'Customer'` binds an element to an id
  you reference elsewhere. **Elements nest**: `ui` and `backend` live *inside* `saas`, so `saas` is a
  system that contains two components — that nesting is exactly what drill-down navigates.
  **Relationships carry labels**: `ui -> backend 'calls over HTTPS'`. Relationships can cross nesting
  levels (`customer -> ui 'uses'` reaches a component inside the system).
- **`views`** — each `view` projects the one model into a specific picture. `include *` pulls in the
  relevant elements; `view of saas` scopes the picture to that system and its insides. Connections in
  a view **inherit their labels from the model** — you write the label once, in the relationship.

The core idea: **model once, view many.** A landscape view and a drill-into-`saas` view are two
windows onto the same elements, so they can never contradict each other.

---

## View kinds

- **Element view** — `view of X { include * }` renders `X` and what it contains/connects to; a bare
  `view name { include * }` with no `of` is the top-level landscape. This is the C4 context/container/
  component picture, chosen by *what you point `of` at*.
- **Dynamic view** — `dynamic view { ... }` renders a **step-by-step flow scenario** (a sequence of
  interactions, like "user logs in": step 1 → step 2 → …), not a static structure.
- **Deployment view** — `deployment view X { ... }` renders **infrastructure**: where the model's
  software elements actually run. The infrastructure itself is described in a separate top-level
  `deployment { ... }` block (its nodes declared as `deploymentNode` in `specification`, `instanceOf`
  placing the logical elements onto them) — kept apart from the logical `model`.

---

## Down to the code level — one collapsible model, all the way

Nesting is **unlimited** and you declare your own element kinds in `specification` — so the same
model that holds systems and containers can keep going *down into the code*. Declare `module`,
`package`, or `class` kinds and nest them inside a component:

```
specification {
  element component
  element module
}
model {
  api = component 'API' {
    router = module 'Router'
    auth   = module 'Auth'
    router -> auth 'verifies token'
  }
}
views {
  view of api { include * }   // drill into API — its modules and how they link
}
```

That's "one model, many views" carried to the bottom: **one file, foldable from the system down to
modules and key classes**, a drill-down view at each level and `dynamic view`s for the flows between
them. It stays a single source of truth — not a pile of disconnected diagrams.

This `module`/`package` nesting also **doubles as the folder structure** — the on-disk layout
(`api/router/`, `api/auth/`…) is a projection of the model, so the tree is designed once here rather
than kept in sync as a separate artifact.

**Where it stops.** LikeC4 models elements, nesting, and relationships — *not* a class's fields and
methods, the internals of a step-by-step call sequence, or a table's columns. That leaf-level detail
doesn't fold into the model in any tool. Render it separately with the `mermaid` skill
(`classDiagram` / `sequenceDiagram` / `erDiagram`) and hang it off the leaf. Keep this model as the
backbone; use Mermaid only for detail that can't collapse.

---

## CLI — via `npx`, no global install

- `npx likec4 start` — interactive dev server in the browser, hot reload as you edit. The primary
  authoring loop when you don't have the VS Code extension.
- `npx likec4 build -o ./dist` — build a static, self-contained site. Add `--output-single-file` for
  one shareable HTML file.
- `npx likec4 gen mermaid` — emit Mermaid text (the zero-friction, GitHub-viewable fallback).
- `npx likec4 gen dot | d2 | plantuml` — emit other diagram formats.
- `npx likec4 validate` — check the model for errors (broken references, undeclared kinds).
- `npx likec4 format` — canonical-format the `.c4` source.

**The heavy path — call it out before using it.** `npx likec4 export png` works but pulls in
Playwright + a headless Chromium download (large, slow, needs a browser runtime). There is **no
direct SVG export**. Avoid `export png` unless the user explicitly needs raster images; prefer
`build` (a real interactive site) or `gen mermaid` (a static image target) instead.

---

## Viewing — cheapest first

1. **LikeC4 VS Code extension** (primary, cheapest) — opens a live preview of the `.c4` file right in
   the editor. If it's installed, this is how you look at your work; no server, no build.
2. **`npx likec4 start`** — the browser dev server, when there's no extension.
3. **`npx likec4 build`** — a static site to publish or hand off.

It does **not** render inside GitHub markdown. Don't expect a `.c4` file to show as a diagram in a PR.

---

## Degradation — always have a fallback

- **Node present, no viewer** → `npx likec4 gen mermaid` gives a GitHub-viewable diagram with zero
  extra install. Good enough to drop into a README or PR.
- **No Node at all** → don't fight the toolchain. Fall back to the `mermaid` skill and hand-write a
  C4-style Mermaid diagram directly.

The model file is still worth keeping either way — it's the source of truth even when the rendering is
degraded.

---

## File placement

Write `.c4` files. When the architect skill is driving the work, put them under
`docs/ccharness/architecture/`. Keep the model in one place so "one source of truth" stays true.

---

## Quick reference

**Three blocks** — `specification` (element kinds + style) · `model` (elements, nesting,
labelled `->` relationships) · `views` (`view of X { include * }` projections). **Views**: element
(`view of X`) · `dynamic view` (a flow) · `deployment view` (infra). **CLI**: `start` (dev server) ·
`build -o ./dist [--output-single-file]` (site) · `gen mermaid|dot|d2|plantuml` · `validate` ·
`format` · `export png` is the heavy Playwright path, no direct SVG. **View** via the VS Code
extension first, else `start`/`build`; not in GitHub markdown. **Degrade** to `gen mermaid`, or to
the `mermaid` skill if Node is missing.

**Invariant:** one model, many consistent views; declare kinds in `specification` before use; label
relationships in the model and views inherit them.
