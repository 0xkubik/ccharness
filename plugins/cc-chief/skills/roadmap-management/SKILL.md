---
name: roadmap-management
description: "Use when the chief works with roadmaps — the product (personal) roadmap of big cross-cutting tasks and the sub-projects' own roadmaps; own the product plane and decompose each big task into per-project subtasks that conform to cc-worker:planning."
argument-hint: "(reference — the rules for the chief's roadmaps)"
user-invocable: false
---

# roadmap-management — the chief's two roadmap planes

The chief works two roadmap planes. The **product roadmap** is yours — the product's own frontier of
big, cross-cutting tasks. Each **project roadmap** is that repo's alone — the concrete work that belongs
strictly to it. Your job bridges them: split the big into the small, and keep both true.

## Rules & concepts — non-negotiable
- **Product roadmap — big tasks, yours.** `roadmap.md` at the product root: a flat list
  under a header stating its altitude, one big cross-cutting task per line, hand-filled;
  Seed a missing one from `example.product-roadmap.md` beside this skill.
- **Project roadmap — strictly that project.** A sub-project's `docs/ccharness/roadmap.md` holds only
  work that belongs to that repo. A subtask lands in the roadmap of the repo it is actually built in.
- **Decompose down, by the planner's rules.** Your responsibility: break each big product task into
  per-project subtasks and deligate to workers.
