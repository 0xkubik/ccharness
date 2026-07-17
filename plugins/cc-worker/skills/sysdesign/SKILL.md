---
name: sysdesign
description: "Use for anything about the project's architecture model — shaping, growing, or correcting the structure. Not WHAT to build (that's planner / what-to-do) but HOW the system is shaped: one living LikeC4 tree in docs/ccharness/architecture/model.c4, root overview down to the finest component that matters — never a mirror of the code. Rules and concepts, not a fixed procedure."
argument-hint: "<the architecture to shape, grow, or correct>"
---

# sysdesign — the architecture, as a living tree

You describe and keep true the project's **structure** — not *what* to build (planner / what-to-do),
but *how* it's shaped. The architecture lives as **one living tree** in
`docs/ccharness/architecture/model.c4`; your job is to grow and correct that tree by the rules below.
LikeC4 syntax lives in **`cc-tools:likec4`** — load it before editing.

**Rules & concepts — non-negotiable:**
- **Always inside `model.c4`.** One unified model, in **your own project**, over that **one file**
  only — never scatter `.c4` files or write architecture anywhere else.
- **Isolate the project — ship a `likec4.config.json`.** Next to `model.c4` sits a `likec4.config.json`
  with a unique `name` (e.g. `{ "name": "<product>-<repo>", "title": "…" }`), so this model stands as
  its own LikeC4 project. Create it if it's missing. Without it, LikeC4 merges every config-less `.c4`
  in the workspace into one default project — and a sibling product's model bleeds into your index.
- **A tree, root → leaves.** The root is a **high-level overview of the whole project**. Each node
  nests its components; each component nests its subcomponents — drilling down (LikeC4 component
  nesting) to the **finest component that still matters for reasoning**. One ontology all the way
  down: deeper just means a *smaller component*, never a switch into code. Structure, not a flat list.
- **Everything reachable from the index.** Every component and every view must be reachable by
  navigation starting at the **index** — through drill-down (nesting) or an explicit `navigateTo`. A
  node or view you can't reach from the index is orphaned: wire it to where it belongs, or it doesn't
  exist for the reader. Standalone views (a dynamic flow) especially need a `navigateTo` pointing at them.
- **Components, not code structure — that's codegraph's map.** The tree holds components and their
  relationships. It does **not** mirror the code: inheritance chains, interface / ABI files, helper
  and math libraries, abstract base classes, individual functions — all **OUT**. codegraph already
  maps the code; duplicating it here churns and confuses. A significant implementation *fact* (an RNG
  source, a standard like ERC-7535, a gasless path) lives as a component's **description or a
  relationship** — never as its own code node.
- **Living, not carved.** The tree is dynamic — nodes are **added, edited, and expanded** as the
  system's *shape* changes and is understood better. It is never "done" — but it moves with the
  **architecture**, not with every code edit.
- **Significant only — quantity ≠ quality.** Only architecturally-significant components and their
  real relationships belong. Not every file, class, or function is a node. Fewer, meaningful nodes;
  when in doubt, it stays **OUT**.
- **Short nodes.** The less text inside a component, the better — a crisp title, a minimal
  description. Meaning comes from the tree's **structure**, not prose stuffed in the nodes.
- **English.** Identifiers, titles, descriptions — all English.

---

## Working the tree

- **Place before you add.** Find where a component belongs — whose child it is — and nest it there;
  don't dump new nodes at the root.
- **Add / edit / expand as reality moves.** New component → a node under its parent. Something grew →
  expand it into subcomponents. Drifted, renamed, or gone → correct or prune the node.
- **Wire every new view.** A view reached by drill-down (a scoped element view) is fine as-is; one that
  isn't (a dynamic flow, a cross-cutting view) needs a `navigateTo` to it from the node or view where
  it belongs — so it stays reachable from the index.
- **Deeper only where a design earns it.** Stop at the component level by default. Drill a branch
  deeper only where a specific design genuinely needs it to be reasoned about — and even then as
  finer components, never a code dump.
- Whether the source is the user's design or the actual code, the job is the same: keep the tree
  **true**, and let it grow.