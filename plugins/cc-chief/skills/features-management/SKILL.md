---
name: features-management
description: "Use when the chief works with features — the product (personal) features file of big cross-cutting capabilities and the sub-projects' own feature states; own the product plane and decompose each big feature into per-project features that conform to cc-setup:feature-management."
argument-hint: "(reference — the rules for the chief's feature planes)"
user-invocable: false
---

# features-management — the chief's two feature planes

The chief works two feature planes. The **product features** are yours — the product's own declarative
state of big, cross-cutting capabilities. Each **project features file** is that repo's alone — the
concrete state that belongs strictly to it. Your job bridges them: split the big into the small, and
keep both true.

## Rules & concepts — non-negotiable
- **Product features — big capabilities, yours.** `features.md` at the product root: a flat numbered
  checkbox list, one big cross-cutting capability per line, hand-filled;
  seed a missing one from `example.product-features.md` beside this skill.
- **Project features — strictly that project.** A sub-project's `docs/features/features.md` holds only
  what belongs to that repo. A decomposed feature lands in the file of the repo it is actually built in.
- **Declarative, accumulating.** Both planes are desired state — the code is pulled toward them. A
  shipped feature is marked `[x]`, **never deleted**; the lists only grow.
- **Decompose down, by the feature-management rules.** Your responsibility: break each big product
  feature into per-project features (per `cc-setup:feature-management`) and delegate to workers.
