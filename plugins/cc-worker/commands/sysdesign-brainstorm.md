---
description: "Run the architecture design interview — cyclically draw the system's structure out of the human, top-down from the highest scale to detail, then shape it into the model.c4 tree. Follows the sysdesign rules; never reads the code (context comes from the user's words)."
argument-hint: "[what to design — a system, a feature — or nothing to open the model]"
---

# /sysdesign-brainstorm — draw the architecture out

You design architecture **with** the human by interview, then record it. First **load and follow
`cc-worker:sysdesign`** — its rules (one living `model.c4` tree, significant-only, short English nodes,
root overview → detail) govern the model you build. Load `cc-tools:likec4` for syntax before editing.

Draw the design **out of the user** — you do **not** read the project's code; context comes from their
words.

Run the loop, **top-down**:

1. **Frame the scope.** What are we designing — the whole system, a feature, a subtree? Where does it
   sit in the existing tree?
2. **Ask** — one question at a time via `AskUserQuestion`, from the **highest scale first** (major
   components and how they connect) down toward detail. Options seeded from what they've said.
3. **Confirm the shape before you draw.** Reflect the structure back; only once they affirm it do you
   touch the model.
4. **Record into the tree.** Place / add / expand nodes in `model.c4` per the `sysdesign` rules —
   significant components only, short English nodes, nested root → leaves.
5. **Descend or widen.** Drill into a node they want detailed, or move to the next sibling. Keep going
   until the design is captured.

Stop when the user stops. Never invent structure they didn't affirm; never pad the tree.
