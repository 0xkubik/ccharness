---
name: sysdesign
description: "Use for anything about the project's architecture model — shaping, growing, or correcting the structure. Not WHAT to build (that's planner / what-to-do) but HOW the system is shaped: one living LikeC4 tree in docs/ccharness/architecture/model.c4, root overview down to implementation detail. Rules and concepts, not a fixed procedure."
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
- **A tree, root → leaves.** The root is a **high-level overview of the whole project**. Each node
  nests its components; each component nests its subcomponents — drilling down (LikeC4 component
  nesting) to the implementation detail that earns a node. Structure, not a flat list.
- **Living, not carved.** The tree is dynamic — nodes are **added, edited, and expanded** as the
  system grows and is understood better. It is never "done"; it moves with the code.
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
- **Detail only where it earns it.** Drill a branch down to implementation detail only where that
  detail is architecturally significant; leave the rest shallow.
- Whether the source is the user's design or the actual code, the job is the same: keep the tree
  **true**, and let it grow.