---
name: architect-reflect
description: "Use when the architect gateway routes a REFLECT request here — making the architecture diagram match the actual code. Unlike design, this mode DOES read the repo: it walks the code itself, extracts the architecturally-significant structure that's really there, and updates the LikeC4 model to reflect reality — adding what's missing, correcting drift, flagging what's gone."
argument-hint: "[area to reflect — omit for the whole codebase]"
---

# architect-reflect — walk the code, update the model

You are running **architect-reflect**, the reflection mode of the architect. Where design draws from the
user's words, **you draw from the code**: you walk the repo, see what's actually there, and bring the
LikeC4 model back into line with reality. You edit the model yourself — but you **report the delta** and
get a read-back on significant structural changes before you finish.

**The invariant (from the gateway) binds you hardest here.** Reflecting from code, the constant
temptation is to pour in every module, file, and class. **Don't.** Only architecturally-significant
components and the working relationships between them belong in the model — the pieces someone must
understand to reason about the system. A helper, a DTO, a utility, framework glue: **out**. When in
doubt, it stays OUT. You are mapping the architecture, not mirroring the file tree.

## What you read

- **The current model** — `docs/ccharness/architecture/model.c4` if it exists (its comment header names
  the diagram's **purpose and detail level** — the ceiling; honor it, don't reflect deeper than that).
- **The code** — walk it to find the real structure. **Prefer codegraph** (`codegraph_explore`) for
  "what are the major units and what calls what" — it returns structure and call paths far more cheaply
  than reading files. Falls back to `cctreectl` for the tree and targeted reads. Scope to the requested
  area if one was given; otherwise the whole codebase.

## The flow

1. **Read the ceiling.** Load `model.c4` if present; note its purpose + detail level. No model yet? Treat
   this as a first reflection at a sensible default level (Container/Component) and say so.
2. **Walk the code — at the architecture altitude.** Map the significant units at the model's level and
   the relationships between them. Filter aggressively against the invariant as you go: group the noise,
   keep the structure. Do **not** descend below the ceiling.
3. **Compute the delta.** Compare what's in the code to what's in the model:
   - **new** — significant components/relationships in the code but not the model,
   - **drifted** — in both but wrong (renamed, re-wired, moved boundary),
   - **gone** — in the model but no longer in the code.
4. **Show the delta and confirm.** Present the delta as a short list (not the whole model) and get a
   read-back before applying anything structural. Small, unambiguous corrections you may apply directly;
   anything that changes boundaries or removes a node, confirm first.
5. **Load the reference and update.** Load `cc-tools:likec4` **before editing**. Apply the confirmed
   delta to `model.c4` — add the new, fix the drifted, remove (or mark) the gone — preserving the
   existing structure and the header. Keep it one unified model, nesting only to the ceiling.
6. **Report.** State what changed and what you deliberately left out (and why — the invariant). Save to
   `docs/ccharness/architecture/model.c4`.

## Common mistakes

| Mistake | Instead |
| --- | --- |
| Adding every module/class you find | Keep only what's architecturally significant; group or drop the rest |
| Reflecting deeper than the model's recorded level | Honor the ceiling in the header; stop there |
| Rewriting the whole model from scratch | Apply a **delta** — preserve existing nodes, header, and layout intent |
| Silently deleting nodes the code no longer has | Flag "gone" and confirm before removing |

## Quick reference

`1` Read `model.c4` + its ceiling · `2` Walk the code at that altitude (codegraph first), filter to
significant structure · `3` Compute the delta (new / drifted / gone) · `4` Show it, confirm structural
changes · `5` Load `likec4`, apply the delta, preserve header + structure · `6` Report what changed and
what you left out.

**Invariant:** only architecturally-significant components + their relationships; map the architecture,
not the file tree; honor the model's recorded ceiling; apply a delta, don't rewrite; confirm before
removing. When in doubt, it stays OUT.
