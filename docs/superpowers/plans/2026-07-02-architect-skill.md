# Architect skill + diagram reference skills — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a conversation-driven system-design skill (`architect`) to cc-script, plus three deep diagram-format reference skills (`mermaid`, `likec4`, `excalidraw`) to cc-instruments that it draws on.

**Architecture:** The deliverables are prose skills — Markdown `SKILL.md` files, no app code. The three reference skills are command-less (auto-loaded as knowledge, precedent: `slap`). The architect is a normal funnel skill with a `/architect` command, placed after the roadmap step. The architect explicitly loads the relevant reference skill before drawing; if cc-instruments is absent it degrades to Mermaid.

**Tech Stack:** Markdown + YAML frontmatter (Claude Code skills), JSON (`plugin.json`), Python `unittest` (existing test pattern). No new runtime code.

## Global Constraints

- **Skills are auto-discovered** from each plugin's `skills/<name>/SKILL.md`. Only `architect` gets a `commands/<name>.md` file; the three reference skills get **none** (command-less, like `slap`).
- **Frontmatter** on every SKILL.md: `name` (matches the directory) and `description` (rich, written so the model auto-loads the skill when relevant). Command files use `description` + `argument-hint`.
- **Diagram-first:** every skill's output guidance favours diagrams; text is connective tissue only.
- **The architect never reads project code.** It may read the goal doc `.claude/ccharness/roadmap.md` (a goal artifact, not code) and `.claude/rules/` if present.
- **Versions live only in each `plugin.json`** — `marketplace.json` carries no per-plugin version. Bump cc-instruments `0.25.0 → 0.26.0` and cc-script `0.14.0 → 0.15.0`.
- **Viewing reality (state honestly in the skills):** Mermaid renders zero-install in GitHub markdown + VS Code; LikeC4 needs the LikeC4 VS Code extension (or `npx likec4 start`/`build`), `gen mermaid` is its zero-install fallback; Excalidraw is **not** LLM-native — build scenes via a Node helper and save `.excalidraw.svg` (renders on GitHub, editable in `pomdtr.excalidraw-editor`).
- **Tests:** follow the repo's minimal pattern (`test_funnel_skill_invariants.py`) — existence checks and real string contracts only; no prose-invariant pinning.
- Work happens in the current worktree; commit after each task.

---

### Task 1: `mermaid` reference skill (cc-instruments)

**Files:**
- Create: `plugins/cc-instruments/skills/mermaid/SKILL.md`

**Interfaces:**
- Produces: a command-less skill named `mermaid`, loadable by the architect and by any session building a Mermaid diagram.

- [ ] **Step 1: Write `plugins/cc-instruments/skills/mermaid/SKILL.md`**

Frontmatter (exact):

```yaml
---
name: mermaid
description: "Use when building a diagram in Mermaid — flowchart, sequence, class, ER, or state — or when you need a diagram that renders with zero install directly in GitHub markdown and VS Code. The zero-friction baseline diagram format; reach for it when portability and instant viewing matter more than rich layout or drill-down."
---
```

Body must cover, with a minimal working snippet for each:
- **What / when:** zero-install; a fenced ` ```mermaid ` block renders natively on GitHub and in VS Code (built-in preview / Markdown extension). This is the baseline — no tooling, no browser, no build.
- **Diagram types** (one small example each): `flowchart TD` (nodes, edges, `subgraph` grouping), `sequenceDiagram` (participants, `->>`, `activate`/`alt`), `classDiagram` (classes, relations), `erDiagram` (entities, cardinality), `stateDiagram-v2`.
- **Honesty:** the `C4Context` / `architecture-beta` types exist but are experimental and degrade on large graphs — for real C4 prefer the `likec4` skill; use plain `flowchart` with styled `subgraph`s for layered pictures here.
- **Idioms for clear diagrams:** set direction, group with `subgraph`, label edges meaningfully, cap node count per view, use `classDef`/`class` for styling, split a busy picture into several focused diagrams.
- **Viewing:** save inside `.md` files as fenced ` ```mermaid ` blocks; renders on push to GitHub and in VS Code preview.
- **Degradation:** none needed — Mermaid is itself the fallback other formats degrade to.

- [ ] **Step 2: Verify the skill is well-formed**

Run:
```bash
cd plugins/cc-instruments && test -f skills/mermaid/SKILL.md && head -4 skills/mermaid/SKILL.md
```
Expected: file exists; first lines show the `---` frontmatter with `name: mermaid`.

- [ ] **Step 3: Commit**

```bash
git add plugins/cc-instruments/skills/mermaid/SKILL.md
git commit -m "feat(cc-instruments): mermaid diagram reference skill"
```

---

### Task 2: `likec4` reference skill (cc-instruments)

**Files:**
- Create: `plugins/cc-instruments/skills/likec4/SKILL.md`

**Interfaces:**
- Produces: a command-less skill named `likec4`.

- [ ] **Step 1: Write `plugins/cc-instruments/skills/likec4/SKILL.md`**

Frontmatter (exact):

```yaml
---
name: likec4
description: "Use when building a structured software-architecture diagram as code — C4-style context / container / component views with drill-down, one model producing many consistent views with automatic layout. Reach for it over Mermaid when the architecture is layered and you want a single source of truth. Viewed via the LikeC4 VS Code extension; generates Mermaid as a zero-install fallback."
---
```

Body must cover, with a concrete example:
- **What / when:** a DSL for C4 architecture as code. You write one model; the tool renders many interactive views (pan/zoom, drill from a system into its internals) with auto-layout. Choose it over Mermaid for layered architecture and a single source of truth.
- **Model structure** — the three blocks, with this minimal full example:

```likec4
specification {
  element actor { style { shape person } }
  element system
  element component
}
model {
  customer = actor 'Customer'
  saas = system 'Our SaaS' {
    ui = component 'Frontend'
    backend = component 'Backend'
    ui -> backend 'calls over HTTPS'
  }
  customer -> ui 'uses'
}
views {
  view index { include * }        // landscape
  view of saas { include * }      // drill into one system
}
```

- **View kinds:** element views (`view of X { include * }`), `dynamic view` (a step-by-step flow), `deployment` view (infrastructure).
- **CLI (via `npx`, no global install):** `npx likec4 start` (interactive dev server in the browser), `npx likec4 build -o ./dist` (static site; `--output-single-file` for one HTML), `npx likec4 gen mermaid` (text fallback), `npx likec4 validate` / `format`. Note `likec4 export png` works but pulls Playwright/Chromium — call it out as the heavy path.
- **Viewing:** the **LikeC4 VS Code extension** previews `.c4` files in the editor (cheapest); otherwise `start` or `build`.
- **Degradation:** `gen mermaid` yields a GitHub-viewable diagram with zero install; if Node is unavailable, fall back to the `mermaid` skill.
- **File placement:** `.c4` files (in `docs/architecture/` when driven by the architect).

- [ ] **Step 2: Verify the skill is well-formed**

Run:
```bash
cd plugins/cc-instruments && test -f skills/likec4/SKILL.md && head -4 skills/likec4/SKILL.md
```
Expected: file exists; frontmatter shows `name: likec4`.

- [ ] **Step 3: Commit**

```bash
git add plugins/cc-instruments/skills/likec4/SKILL.md
git commit -m "feat(cc-instruments): likec4 diagram reference skill"
```

---

### Task 3: `excalidraw` reference skill + reference-skills test (cc-instruments)

**Files:**
- Create: `plugins/cc-instruments/skills/excalidraw/SKILL.md`
- Create: `plugins/cc-instruments/tests/test_diagram_reference_skills.py`

**Interfaces:**
- Consumes: the `mermaid/` and `likec4/` skill directories from Tasks 1–2.
- Produces: a command-less skill named `excalidraw`; a test asserting all three reference skills exist and stay command-less.

- [ ] **Step 1: Write `plugins/cc-instruments/skills/excalidraw/SKILL.md`**

Frontmatter (exact):

```yaml
---
name: excalidraw
description: "Use when building a freeform, hand-drawn-style diagram or sketch the user will rearrange by hand — whiteboard-style design, not structured architecture-as-code. Unlike Mermaid and LikeC4, Excalidraw is not LLM-native: build scenes through the Node helper and save as .excalidraw.svg so the file renders on GitHub and stays editable in the pomdtr.excalidraw-editor VS Code extension."
---
```

Body must cover:
- **What / when:** hand-drawn-style whiteboard diagrams for freeform sketching — design ideas the user moves around by hand. Not for structured architecture (use `likec4`).
- **Honesty up front:** raw `.excalidraw` JSON is painful and error-prone to author by hand (every element needs `id`, `seed`, `versionNonce`, `groupIds`, `boundElements`, `roundness`, `angle`…). **Do not hand-write raw JSON.**
- **Reliable path — Node helper:** build a skeleton (minimal fields) and expand it with `convertToExcalidrawElements()` from `@excalidraw/excalidraw`; normalise with `restoreElements()`. Include a minimal Node snippet showing skeleton → `convertToExcalidrawElements` → write `.excalidraw`.
- **Saving for viewing:** save as **`.excalidraw.svg`** — it renders as an image on GitHub *and* stays editable in the `pomdtr.excalidraw-editor` VS Code extension. Plain `.excalidraw` also opens on excalidraw.com.
- **Mermaid→Excalidraw bridge:** `@excalidraw/mermaid-to-excalidraw` (`parseMermaidToExcalidraw`) can turn Mermaid into editable elements, **but it needs a browser DOM** — only usable with a Node+browser/jsdom environment, not on a bare machine. Offer it only as an optional upgrade; the default is the Node helper, or the user converting on excalidraw.com.
- **Degradation:** if Node is unavailable, fall back to the `mermaid` skill for the sketch.
- **File placement:** `docs/architecture/` when driven by the architect.

- [ ] **Step 2: Write `plugins/cc-instruments/tests/test_diagram_reference_skills.py`**

```python
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
COMMANDS = ROOT / "commands"
REFERENCE_SKILLS = ("mermaid", "likec4", "excalidraw")


class TestDiagramReferenceSkills(unittest.TestCase):
    def test_skill_files_exist(self):
        for name in REFERENCE_SKILLS:
            skill = SKILLS / name / "SKILL.md"
            self.assertTrue(skill.exists(), f"{name} SKILL.md missing")

    def test_frontmatter_names_match(self):
        for name in REFERENCE_SKILLS:
            text = (SKILLS / name / "SKILL.md").read_text()
            self.assertIn(f"name: {name}", text, f"{name} frontmatter name mismatch")

    def test_reference_skills_are_command_less(self):
        for name in REFERENCE_SKILLS:
            self.assertFalse(
                (COMMANDS / f"{name}.md").exists(),
                f"{name} must stay command-less (no commands/{name}.md)",
            )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test — expect PASS**

Run:
```bash
cd plugins/cc-instruments && python -m pytest tests/test_diagram_reference_skills.py -v
```
Expected: 3 passed (all three skills exist, names match, none has a command file).

- [ ] **Step 4: Bump cc-instruments version + description**

In `plugins/cc-instruments/.claude-plugin/plugin.json`: set `"version": "0.26.0"`, and append to the description one clause noting the three diagram references, e.g.: `plus command-less diagram references (mermaid / likec4 / excalidraw) that the cc-script architect draws on.`

- [ ] **Step 5: Commit**

```bash
git add plugins/cc-instruments/skills/excalidraw/SKILL.md plugins/cc-instruments/tests/test_diagram_reference_skills.py plugins/cc-instruments/.claude-plugin/plugin.json
git commit -m "feat(cc-instruments): excalidraw diagram reference skill + reference-skills test"
```

---

### Task 4: `architect` skill + command (cc-script)

**Files:**
- Create: `plugins/cc-script/skills/architect/SKILL.md`
- Create: `plugins/cc-script/commands/architect.md`
- Modify: `plugins/cc-script/tests/test_funnel_skill_invariants.py` (add architect existence check)

**Interfaces:**
- Consumes: the `mermaid`, `likec4`, `excalidraw` reference skills (Tasks 1–3), loaded explicitly.
- Produces: a `/architect` command and an `architect` skill placed in the funnel after the roadmap step.

- [ ] **Step 1: Write `plugins/cc-script/skills/architect/SKILL.md`**

Frontmatter (exact):

```yaml
---
name: architect
description: "Use when designing a NEW system or feature together with the user, driven by conversation — turning intent into architecture diagrams (mostly diagrams, a little text). Sits in the cc-script funnel after the roadmap: goal set → design the architecture → decide what to do → build. Never reads project code; context comes from the user's words. Draws in LikeC4, Excalidraw, or Mermaid, chosen per need."
argument-hint: "<what you want to design>"
---
```

Body must cover:
- **Role, one line:** you are the architect — you design a *new* system/feature *with* the user, led by their words, and emit **mostly diagrams, a little text**. You never read the project's code.
- **What you may read:** the goal doc `.claude/ccharness/roadmap.md` (North Star / roadmap) if present, and `.claude/rules/` if present (obey project rules like the other script skills). Nothing else from the repo — no source files.
- **Flow (numbered):**
  1. Anchor: read the roadmap/North Star if present; otherwise start from the user's words.
  2. Draw out intent conversationally — user-led; ask what they want to design, the pieces, the boundaries. Do not invent a full system unprompted.
  3. Pick the format(s) per need — **LikeC4** for structured, layered architecture (context → containers → components, with drill-down); **Excalidraw** for a freeform sketch the user will move by hand; **Mermaid** for quick, portable, or fallback.
  4. **Before drawing, explicitly load the matching reference skill** from cc-instruments (`mermaid` / `likec4` / `excalidraw`) — do not rely on ambient auto-pickup, or the deep syntax knowledge won't be present.
  5. Produce the diagrams; keep text to connective tissue and rationale only.
  6. Iterate with the user on their feedback.
  7. Save output to `docs/architecture/`.
- **Cross-plugin degradation:** the reference skills live in cc-instruments; if it isn't installed, degrade to **Mermaid**, which needs nothing installed and renders everywhere.
- **Funnel boundary:** you are the optional *design* step after the roadmap and before `/what-to-do`; you shape the architecture, you don't rank directions or build. Hand the design forward; the user redirects at the boundary.

- [ ] **Step 2: Write `plugins/cc-script/commands/architect.md`**

```markdown
---
description: "Design a new system or feature with the architect — a conversation-driven design loop that turns your intent into architecture diagrams (mostly diagrams, a little text). Sits after the roadmap in the script: set the goal → design the architecture → decide what to do → build. It never reads your code; you bring the context in words. It draws in LikeC4 (structured, layered C4), Excalidraw (freeform sketches), or Mermaid (quick, zero-install), leaning on cc-instruments' diagram references."
argument-hint: "<what you want to design>"
---

Invoke the `architect` skill with what you want to design:

> $ARGUMENTS

The architect designs a **new** system or feature **with you**, led by your words, and emits
**mostly diagrams, a little text**. It sits in the script after `/roadmap-management`: set the goal
→ **design the architecture** → `/what-to-do` → `/do`. It **never reads your code** — bring the
context in words. It picks the format per need — **LikeC4** for structured, layered architecture,
**Excalidraw** for freeform sketches, **Mermaid** for quick and zero-install — and draws on
cc-instruments' diagram references. Diagrams are saved to `docs/architecture/`. If cc-instruments
isn't installed, it falls back to Mermaid, which renders everywhere with nothing installed.
```

- [ ] **Step 3: Add architect existence check to the funnel test**

In `plugins/cc-script/tests/test_funnel_skill_invariants.py`, add after the `RRT` path constant:

```python
ARCHITECT = ROOT / "skills" / "architect" / "SKILL.md"
```

and add this test class before the `if __name__` block:

```python
class TestArchitectSkill(unittest.TestCase):
    def test_exists(self):
        self.assertTrue(ARCHITECT.exists(), "architect SKILL.md missing")
```

- [ ] **Step 4: Run the funnel test — expect PASS**

Run:
```bash
cd plugins/cc-script && python -m pytest tests/test_funnel_skill_invariants.py -v
```
Expected: all tests pass, including `TestArchitectSkill::test_exists`.

- [ ] **Step 5: Commit**

```bash
git add plugins/cc-script/skills/architect/SKILL.md plugins/cc-script/commands/architect.md plugins/cc-script/tests/test_funnel_skill_invariants.py
git commit -m "feat(cc-script): architect skill — conversation-driven design to diagrams"
```

---

### Task 5: Wire architect into the funnel docs + versions

**Files:**
- Modify: `plugins/cc-script/README.md` (funnel diagram + commands table)
- Modify: `plugins/cc-script/.claude-plugin/plugin.json` (version + description)
- Modify: `.claude-plugin/marketplace.json` (cc-script description)

**Interfaces:**
- Consumes: the `/architect` command from Task 4.

- [ ] **Step 1: Insert architect into the README funnel diagram**

In `plugins/cc-script/README.md`, update the ASCII funnel so `/architect` sits between
`/roadmap-management` and `/what-to-do`, e.g.:

```
/roadmap-management ─► /architect ─► /what-to-do ─► /how-to-do ─► /do
 GROUND               DESIGN         DIVERGE         DECIDE        BUILD
 set the goal         design the     rank where      work out HOW  take one task
 (North Star)         architecture   it could go     to build the  to done
 + the roadmap        (diagrams)     next (a menu)   pick          
```

Keep the existing `(/slap = reset · /crux = unwind a pain …)` note as-is.

- [ ] **Step 2: Add an architect row to the README commands table**

Add, after the `/roadmap-management` row:

```markdown
| **`/architect <what>`** | The **design loop.** Designs a new system or feature **with you**, led by your words, into **architecture diagrams** (mostly diagrams, little text) — LikeC4 for structured layered C4, Excalidraw for freeform sketches, Mermaid for quick/zero-install — saved to `docs/architecture/`. Never reads your code; you bring the context. Optional step between the roadmap and `/what-to-do`. | "Design the architecture before deciding what to build." |
```

- [ ] **Step 3: Bump cc-script version + description**

In `plugins/cc-script/.claude-plugin/plugin.json`: set `"version": "0.15.0"`, and add one clause to the description naming `/architect` as the design step after the roadmap (e.g. after the `/roadmap-management` clause: `/architect designs the architecture into diagrams (LikeC4 / Excalidraw / Mermaid);`).

- [ ] **Step 4: Update the marketplace description for cc-script**

In `.claude-plugin/marketplace.json`, add a matching `/architect` clause to the cc-script `description` string so the marketplace listing mentions it.

- [ ] **Step 5: Verify JSON is valid**

Run:
```bash
cd /Users/kubik/nox/misc/claude-code-harness/.claude/worktrees/architect-skill
python -c "import json; json.load(open('plugins/cc-script/.claude-plugin/plugin.json')); json.load(open('.claude-plugin/marketplace.json')); print('JSON OK')"
```
Expected: `JSON OK`.

- [ ] **Step 6: Commit**

```bash
git add plugins/cc-script/README.md plugins/cc-script/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "docs(cc-script): wire /architect into the funnel + bump version"
```

---

### Task 6: Full test sweep

**Files:** none (verification only)

- [ ] **Step 1: Run both plugins' test suites**

Run:
```bash
cd /Users/kubik/nox/misc/claude-code-harness/.claude/worktrees/architect-skill
python -m pytest plugins/cc-instruments/tests plugins/cc-script/tests -q
```
Expected: all tests pass (the pre-existing suites plus the new `test_diagram_reference_skills.py` and the architect existence check). If any pre-existing test was already failing before this work, note it and confirm it is unrelated.

- [ ] **Step 2: Confirm the file layout**

Run:
```bash
ls plugins/cc-instruments/skills/{mermaid,likec4,excalidraw}/SKILL.md
ls plugins/cc-script/skills/architect/SKILL.md plugins/cc-script/commands/architect.md
ls plugins/cc-instruments/commands/ | grep -E 'mermaid|likec4|excalidraw' && echo "ERROR: reference skill has a command" || echo "OK: reference skills command-less"
```
Expected: all skill files present; `OK: reference skills command-less`.

## Self-Review

- **Spec coverage:** three reference skills (Tasks 1–3) ✓; command-less, precedent `slap` ✓; architect skill + command in cc-script after roadmap (Task 4) ✓; single conversational mode, never reads code (Task 4 body) ✓; explicit reference-skill loading + Mermaid degradation (Task 4) ✓; format-per-need LikeC4/Excalidraw/Mermaid (Tasks 1–4) ✓; output to `docs/architecture/` (Tasks 1–4) ✓; honest Excalidraw non-LLM-native + Node helper (Task 3) ✓; funnel placement in README (Task 5) ✓; cross-plugin dependency + degradation stated (Task 4) ✓; version bumps both plugins (Tasks 3, 5) ✓; minimal tests matching repo pattern (Tasks 3, 4) ✓. Non-goal (reverse-engineering / codegraph) is deliberately absent ✓.
- **Placeholder scan:** frontmatter is given verbatim; content outlines carry the actual technical facts (no "TBD"); test code is complete.
- **Type/name consistency:** skill directory names (`mermaid`, `likec4`, `excalidraw`, `architect`) match their frontmatter `name:` and the test constants; versions `0.26.0` / `0.15.0` are used consistently.
