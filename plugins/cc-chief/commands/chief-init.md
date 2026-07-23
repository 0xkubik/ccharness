---
description: "Chief writes the product root CLAUDE.md from the sub-projects' own CLAUDE.mds plus a North Star drawn from the human. One-shot init, run at the product root."
argument-hint: "(no args — run at the product root)"
---

# /chief-init — the product's orientation

Write the product root `CLAUDE.md` — *what the product IS*. One-shot; the chief owns it.

## What you do
1. **Gather.** List the git-repo subfolders and **read each one's `CLAUDE.md`** — your raw material.
   ```bash
   for d in */; do [ -e "$d/.git" ] && echo "$d"; done
   ```
2. **Ask.** Draw the product's single **North Star** (guiding intent) out of the human — never invent it.
3. **Write on approval.** Compose the file, write it only once they approve.
4. **Create empty product-roadmap.md**. Exaple from `cc-chief/skills/roadmap-management/example.product-roadmap.md`
 to `roadmap.md` near to CLAUDE.md with empty list

## What it holds
- **North Star** — from the human.
- **Description** — a top-level synthesis of the product, assembled from the sub-projects' CLAUDE.mds (the whole, not the parts pasted).
- **Sub-projects** — each with one crisp line: what it is and its role.