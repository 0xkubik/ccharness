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
- **The tree's one axis: runtime interaction.** The tree answers a single question — *what talks to,
  calls, or depends on what, at run time.* Every node is a thing that **exists and interacts when the
  system runs** (a service, a process, a datastore, a deployed contract, an external system); every
  edge is a runtime interaction (calls, reads, publishes, forwards). This axis is the whole discipline
  below: a node that doesn't interact at run time, or an edge that isn't a runtime interaction, does
  not belong.
- **Always inside `model.c4`.** One unified model, in **your own project**, over that **one file**
  only — never scatter `.c4` files or write architecture anywhere else.
- **Isolate the project — ship a `likec4.config.json`.** Next to `model.c4` sits a `likec4.config.json`
  with a unique `name` (e.g. `{ "name": "<product>-<repo>", "title": "…" }`), so this model stands as
  its own LikeC4 project. Create it if it's missing. Without it, LikeC4 merges every config-less `.c4`
  in the workspace into one default project — and a sibling product's model bleeds into your index.
- **A tree, root → leaves — down one axis.** The root is a **high-level overview of the whole
  project**. Each node nests the finer *interacting* parts inside it (LikeC4 component nesting), down
  to the **finest interacting unit that still matters for reasoning**. Deeper means a smaller
  interacting unit of the **same** runtime-interaction axis — never a jump to a different axis (code
  structure, type hierarchy, deployment topology). Structure, not a flat list.
- **Everything reachable from the index.** Every component and every view must be reachable by
  navigation starting at the **index** — through drill-down (nesting) or an explicit `navigateTo`. A
  node or view you can't reach from the index is orphaned: wire it to where it belongs, or it doesn't
  exist for the reader. Standalone views (a dynamic flow) especially need a `navigateTo` pointing at them.
- **Code structure is a different axis — OUT.** Inheritance / `extends` / `is`, interface / ABI files,
  helper and math libraries, mixins, abstract base classes or base contracts, individual functions —
  these describe *how the source is organized to be reused*, not *what interacts at run time*. They are
  never nodes and never edges. **Litmus:** if you'd label an edge `extends` / `inherits` / `is`, or a
  node is *abstract / not deployed / a stateless helper lib*, it's the code axis — leave it OUT.
  codegraph already maps the code; if a code-structure picture is ever genuinely needed it is a
  **separate generated diagram**, never hand-carved into this tree. A significant implementation *fact*
  (an RNG source, a standard like ERC-7535, a gasless path) lives as a component's **description or a
  relationship** — never as its own code node.
- **Map the leaf to the domain's real unit.** A node is whatever independently **exists and interacts
  in this domain**: a running service or process (a backend), a deployed contract (on-chain), a
  datastore, an external system. Do **not** turn source groupings — folders, `src/*` dirs, packages,
  base classes — into nodes; they are code organization, not interacting units.
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
- **One altitude per view.** A scoped view shows one zoom-level — a parent and the interacting units
  one level inside it. Don't put a deployed unit and its abstract base, or a service and another
  store's internals, in the same view; mixed altitudes are what make a diagram read as "half
  architecture, half code."
- **Deeper only where a design earns it.** Stop at the component level by default. Drill a branch
  deeper only where a specific design genuinely needs it to be reasoned about — and even then as
  finer components, never a code dump.
- Whether the source is the user's design or the actual code, the job is the same: keep the tree
  **true**, and let it grow.