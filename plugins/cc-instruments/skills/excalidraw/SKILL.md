---
name: excalidraw
description: "Use when building a freeform, hand-drawn-style diagram or sketch the user will rearrange by hand — whiteboard-style design, not structured architecture-as-code. Unlike Mermaid and LikeC4, Excalidraw is not LLM-native: build scenes through the Node helper and save as .excalidraw.svg so the file renders on GitHub and stays editable in the pomdtr.excalidraw-editor VS Code extension."
---

# excalidraw — hand-drawn diagrams the human moves by hand

You are producing an **Excalidraw** scene: a freeform, hand-drawn-style whiteboard sketch the
human will drag, regroup, and redraw by hand. Use this when the value is in *movable, loose
shapes* — design ideas in flux, a rough system sketch, boxes-and-arrows you expect the human to
rearrange.

**Not for structured architecture.** If the diagram is a real system model that should live as
code (typed nodes, relations, generated views), stop and use the **`likec4`** skill. If you just
need a clean flow/sequence/ER diagram from text, the **`mermaid`** skill is simpler. Excalidraw
is the whiteboard, not the source of truth.

## The one honest warning: don't hand-write the JSON

Excalidraw's `.excalidraw` file is JSON, but authoring it by hand is painful and error-prone.
Every element carries fields you will get subtly wrong — `id`, `seed`, `versionNonce`, `version`,
`groupIds`, `boundElements`, `roundness`, `angle`, `strokeColor`, `fillStyle`, and more — and
arrow↔shape bindings must cross-reference by `id` on both ends. A single missing or stale field
gives you a scene that opens blank or with detached arrows.

**Do NOT hand-write raw Excalidraw JSON.** Build a *skeleton* and let the official library
expand it.

## The reliable path — a small Node helper

`@excalidraw/excalidraw` ships `convertToExcalidrawElements()`, which takes a **skeleton** (a few
human-friendly fields per element) and fills in every required field with correct defaults and
valid bindings. Then wrap the result in the top-level file schema and write it out.

```js
// npm i @excalidraw/excalidraw
import { convertToExcalidrawElements } from "@excalidraw/excalidraw";
import { writeFileSync } from "node:fs";

// Skeleton: minimal fields. Ids are yours to reference for bindings.
const skeleton = [
  { type: "rectangle", id: "box-a", x: 100, y: 100, width: 180, height: 80,
    label: { text: "Client" } },
  { type: "rectangle", id: "box-b", x: 460, y: 100, width: 180, height: 80,
    label: { text: "API" } },
  { type: "arrow", x: 280, y: 140, width: 180, height: 0,
    start: { id: "box-a" }, end: { id: "box-b" }, label: { text: "request" } },
];

const elements = convertToExcalidrawElements(skeleton);

const scene = {
  type: "excalidraw",
  version: 2,
  source: "cc-instruments:excalidraw",
  elements,
  appState: { viewBackgroundColor: "#ffffff" },
  files: {},
};

writeFileSync("diagram.excalidraw", JSON.stringify(scene, null, 2));
```

`convertToExcalidrawElements` handles the fiddly parts: giving each element its `id`/`seed`/
`version`, turning a `label` into a bound text element, and wiring `boundElements` on both the
arrow and the shapes it connects. You supply intent; it supplies correctness.

If you're editing or merging elements from an existing file, run them through
`restoreElements(elements, null)` (also from `@excalidraw/excalidraw`) first — it normalises
older or partial elements up to the current schema so nothing opens broken.

### The element shapes you'll actually use

- `type`: `rectangle` · `ellipse` · `diamond` · `arrow` · `line` · `text`.
- Position/size: `x`, `y` (top-left, pixels) and `width`, `height`. Arrows/lines also read
  width/height as their span; give them a nonzero extent in the direction they travel.
- Text: a standalone `{ type: "text", x, y, text }`, or — better for shapes — a `label: { text }`
  on a rectangle/ellipse/diamond/arrow, which binds the text to the shape so it moves with it.
- Bindings: an `arrow` with `start: { id }` / `end: { id }` attaches to those shapes; the
  converter writes the reciprocal `boundElements` back onto the shapes. Point an arrow at a
  fixed coordinate instead by giving `start`/`end` a `{ x, y }` (or omitting them).

### Top-level file schema

```json
{ "type": "excalidraw", "version": 2, "source": "...",
  "elements": [ /* full elements from convertToExcalidrawElements */ ],
  "appState": {}, "files": {} }
```

`elements` is the only field that must be fully populated; `appState` and `files` can be empty
objects for a fresh scene.

## Saving so it's viewable AND editable

Save as **`.excalidraw.svg`**. This is the sweet spot: it renders as a normal image on GitHub
and in previews, **and** Excalidraw embeds the scene inside the SVG so it stays fully editable in
the **`pomdtr.excalidraw-editor`** VS Code extension (open the `.excalidraw.svg` there and drag
things around). The plain **`.excalidraw`** JSON also opens for editing on excalidraw.com and in
that extension — it just doesn't render as an image inline.

Rule of thumb: hand off `.excalidraw.svg` when the file should show up in a repo/README and stay
editable; keep the plain `.excalidraw` when it's purely a working file.

## Optional upgrade: Mermaid → Excalidraw

If the human already has a Mermaid diagram and wants it as movable Excalidraw elements,
`@excalidraw/mermaid-to-excalidraw` exposes `parseMermaidToExcalidraw(definition)`, which returns
skeleton elements you can pass to `convertToExcalidrawElements`.

**Caveat that decides the default:** this parser needs a **browser DOM** (it drives Mermaid's
renderer), so it does *not* run on a bare Node machine — you'd need Node with a browser or a
`jsdom`/headless-browser setup. So offer it only as an optional upgrade. The default is the Node
helper above, or telling the user to paste their Mermaid into the **"Mermaid to Excalidraw"**
converter built into excalidraw.com's UI, then drag the result.

## When Node isn't available

If you can't run Node (no package install, no runtime), don't try to hand-author the JSON — fall
back to the **`mermaid`** skill and produce the sketch there. A correct Mermaid diagram beats a
broken Excalidraw file.

## File placement

When the **architect** skill drives the diagram, write it under **`docs/architecture/`** (e.g.
`docs/architecture/<name>.excalidraw.svg`). Otherwise place it where the human is working, next
to the doc or README it illustrates.

## Quick reference

Whiteboard sketch the human rearranges → excalidraw · structured model-as-code → `likec4` · quick
text diagram → `mermaid`. Never hand-write the JSON: build a **skeleton** →
`convertToExcalidrawElements()` (→ `restoreElements()` when merging existing elements) → wrap in
`{ type, version: 2, source, elements, appState, files }` → write **`.excalidraw.svg`** (renders
on GitHub + editable in `pomdtr.excalidraw-editor`). Mermaid→Excalidraw needs a browser DOM —
optional only. No Node → fall back to `mermaid`. Architect-driven → `docs/architecture/`.
