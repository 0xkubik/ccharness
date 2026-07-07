---
name: likec4
description: "Reference for LikeC4 — a DSL and toolchain for describing software architecture as code (C4-style context / container / component / code), where one model renders many consistent, auto-laid-out views. Covers the language, view kinds, styling, deployment, the CLI, the MCP server, and where the exhaustive syntax lives. Viewed via the LikeC4 VS Code extension; can generate Mermaid."
---

# likec4 — architecture-as-code reference

LikeC4 is a DSL and toolchain for software architecture. You describe one model of a system in `.c4`
files; the toolchain renders many interactive views from it — pan/zoom, drill from a system into its
internals — with automatic layout. Every view is a projection of the same model, so views stay
consistent with each other; layout is computed, not placed by hand.

This file is a map of what LikeC4 offers and what each part is for. The exhaustive, always-current
syntax lives in the official docs and the MCP server — see **Where the full syntax lives**.

## The language

A `.c4` source is organised into top-level blocks. These are the constructs and what each is for:

- **`specification`** — the vocabulary. Declares the *element kinds* the model may use (e.g. `system`,
  `container`, `component`, `actor`, or any custom kind), the *relationship kinds* (e.g. `async`,
  `calls`), *tags* for categorisation, and *custom colors*. A kind must be declared here before the
  model uses it; a kind carries default styling.
- **`model`** — the single source of truth: the actual elements and how they nest. Elements form a
  hierarchical namespace (an element contains child elements), and each carries properties such as
  title, description, technology, and metadata. The nesting is what drill-down navigates.
- **Relationships** — directed connections between elements expressing interaction, data flow, or
  dependency. A relationship can be typed with a relationship kind and carry a technology and a
  description; connections can cross nesting levels. Labels are written once in the model and every
  view inherits them.
- **References and identifiers** — elements are named uniquely within their scope; fully-qualified
  names resolve nested elements. Lexical scoping and hoisting make references unambiguous across the
  model.
- **Tags and metadata** — tags mark elements and relationships for filtering and styling; metadata
  stores arbitrary key–value pairs (including arrays). Both feed queries, view predicates, and tooling.
- **Extending the model (`extend`)** — enriches an existing element (including a nested one) from a
  separate file with more properties, tags, metadata, or relationships. This is how a large model is
  split across multiple files without repetition.

## Views

A view is a projection of the one model into a specific picture. The kinds:

- **Element views** — render an element together with what it contains and connects to; an unscoped
  view is the top-level landscape. Scoping a view at different elements yields the C4
  context / container / component levels from the same model.
- **Dynamic views** — render a scenario as an ordered sequence of steps, with support for parallel
  flows and notes. They describe a specific use case or workflow without changing the logical model.
- **Deployment views** — render the deployment model (below), using the same predicate system as
  logical views.
- **Generated views** — implicit views produced automatically for elements without an explicit view,
  plus relationship browsers, for navigation and discovery with no manual view definition.

Views are shaped by:

- **View predicates** — `include` / `exclude` select which elements and relationships appear, via
  wildcards and filters by kind, tag, or metadata; style rules can be applied conditionally within a
  view. This is how each view decides its own contents and detail level. Automatic layout can be
  tuned per view.
- **Notations** — legend entries explaining what shapes and colors mean, defined globally in the
  specification or locally per view.
- **Organisation and navigation** — views can be grouped into folders by a titling convention;
  elements and relationships can carry `navigateTo` links between views and external links, which is
  what makes drill-down and cross-view navigation work.

## Styling

Controls the visual appearance of elements and relationships: shape, colors, icons, size, opacity,
and borders. Supports theme overrides and conditional style rules (including rules driven by tags or
metadata via view predicates). Styling defaults are set on a kind in the specification and can be
overridden per element or per view.

## Deployment model

A separate top-level model of physical infrastructure, described as hierarchical deployment nodes.
`instanceOf` maps the logical model's elements onto those nodes — i.e. where each component actually
runs. It is kept apart from the logical `model` and is what deployment views render.

## What LikeC4 does not model

LikeC4 describes elements, nesting, and relationships. It does not represent leaf-level implementation
detail — a class's fields and methods, a table's columns, function signatures, low-level design
patterns, or the internals of a call sequence beyond logical workflow steps. That detail lives in
other tools (for example the `mermaid` skill's class, sequence, and ER diagrams).

## Tooling

- **CLI** (run via `npx likec4`, no global install): `start` runs an interactive dev server with hot
  reload; `build` produces a static self-contained site (`--output-single-file` for one HTML file);
  `gen mermaid|dot|d2|plantuml` emits other formats (Mermaid is the GitHub-viewable one); `validate`
  checks the model for errors; `format` canonical-formats the source. `export png` also exists but
  pulls in Playwright and a headless Chromium download; there is no direct SVG export.
- **MCP server** — `npx likec4 mcp` (stdio, `--http` for a port; reads `./src`, no dev server needed)
  exposes tools to query an existing model: an element's incoming/outgoing relationships, paths
  between two elements, elements by tag or metadata. It answers questions about a large model without
  re-reading every `.c4` file.
- **Editors** — the LikeC4 VS Code extension shows a live preview of a `.c4` file in the editor, with
  no server or build.
- **Programmatic and integration surfaces** — a JavaScript/TypeScript API and a `LikeC4Model` codegen
  target; React and Web Component generation for embedding views; a Vite plugin; a Docker image;
  GitHub Actions; and draw.io integration.
- **Project configuration** — config files define project metadata, include/exclude paths, image
  aliases, shared styles, and custom generators; multiple independent projects can live in one
  workspace.

## Viewing

The VS Code extension previews a `.c4` file directly in the editor. `npx likec4 start` serves the same
in a browser; `npx likec4 build` produces a static site to publish or hand off. LikeC4 does not render
inside GitHub markdown — a `.c4` file does not display as a diagram in a PR; `gen mermaid` produces a
GitHub-viewable image target from the model.

## File placement

`.c4` files. When the architect skill is driving the work, they live under
`docs/ccharness/architecture/`, kept together so the model stays a single source of truth.

## Where the full syntax lives

- **Docs, LLM-readable** — `https://likec4.dev/llms.txt` (an index of links) and
  `https://likec4.dev/llms-full.txt` (every page in one file). The same docs are on context7 as the
  `likec4/likec4` library. These are the source of exact, current syntax for every construct above.
- **A built model** — `npx likec4 mcp` (see Tooling) answers structural questions about an existing
  model in natural language.
