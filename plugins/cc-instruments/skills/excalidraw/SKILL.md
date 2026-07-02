---
name: excalidraw
description: "Use when building a freeform, hand-drawn-style diagram or sketch the user will rearrange by hand — whiteboard-style design, not structured architecture-as-code. Unlike Mermaid and LikeC4, Excalidraw is not LLM-native: build scenes through the Node helper, which writes plain .excalidraw JSON (editable in the pomdtr.excalidraw-editor VS Code extension); export to .excalidraw.svg via that extension when the diagram also needs to render on GitHub."
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

## Saving — what the Node helper can and can't produce

The Node helper writes **plain `.excalidraw` JSON**. That file opens for editing on excalidraw.com
and in the **`pomdtr.excalidraw-editor`** VS Code extension (open it there and drag things around).
It does **not** render as an image inline on GitHub — it's a working/editable file, not a picture.

To get a **`.excalidraw.svg`** — which renders as an image on GitHub *and* keeps the scene embedded
so it stays editable in that extension — you need a rendering step the bare Node helper can't do:
Excalidraw's `exportToSvg()` requires a browser DOM (same limitation as the Mermaid→Excalidraw
bridge below). In practice, export the SVG from the **`pomdtr.excalidraw-editor`** extension (it has
an "export to SVG" that embeds the scene), or from excalidraw.com. Only reach for it in a
Node+browser/`jsdom` setup.

Rule of thumb: from a plain CLI, hand off the **`.excalidraw`** JSON (editable, needs the extension
to view); produce **`.excalidraw.svg`** only when a browser/extension is available and the file must
also show up in a repo/README.

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
`docs/architecture/<name>.excalidraw`, or `.excalidraw.svg` if a browser/extension export is
available). Otherwise place it where the human is working, next to the doc or README it illustrates.

## Quick reference

Whiteboard sketch the human rearranges → excalidraw · structured model-as-code → `likec4` · quick
text diagram → `mermaid`. Never hand-write the JSON: build a **skeleton** →
`convertToExcalidrawElements()` (→ `restoreElements()` when merging existing elements) → wrap in
`{ type, version: 2, source, elements, appState, files }` → write plain **`.excalidraw`** JSON
(editable in `pomdtr.excalidraw-editor`; not a GitHub-rendered image). **`.excalidraw.svg`** (renders
on GitHub + stays editable) needs a browser/extension export — not the bare Node helper.
Mermaid→Excalidraw needs a browser DOM — optional only. No Node → fall back to `mermaid`.
Architect-driven → `docs/architecture/`.
