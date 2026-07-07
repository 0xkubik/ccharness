# Musician Router Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `/musician` from one heavy end-to-end conductor into a thin router that sizes its response to the work (small fix → full feature), always grounded in `roadmap.md` + architecture.

**Architecture:** The `/musician` command becomes a thin router that runs in the normal conversation (no self-driving loop). It reads the goal + design, classifies the task, and routes to one of three new build-tier skills (`build-large` / `build-medium` / `build-small`) or to any existing plugin skill. Flags tune *how*, never *what*. All run machinery (arm, state, hooks, nonstop, cancel, ccmusicianctl) is deleted.

**Tech Stack:** Claude Code plugin (Markdown skills + slash command + `plugin.json` manifest), Python `unittest` for the one contract test. Bash only where a skill dispatches subagents (via the Agent tool, not scripts).

## Global Constraints

- Plugin: `plugins/cc-musician/`. Marketplace entry in `.claude-plugin/marketplace.json`.
- Skill frontmatter names are a hard contract — the command routes to skills by these exact names: `build-large`, `build-medium`, `build-small`.
- Flag tokens are exact and lowercase: `--auto`, `--fast`, `--worktree`, `--ultracode`.
- Roadmap path: `docs/ccharness/roadmap.md` (North Star heading is `## Product North Star`). Architecture path: `docs/ccharness/architecture/`.
- Project rules in `.claude/rules/*.md` bind: no gratuitous comments, keep files lean, stay in scope, keep the tree clean, manage git history autonomously.
- Skill-invariant tests are kept ONLY where a string is a real text↔code contract (per the repo's testing stance) — do not add prose-pinning tests.
- Isolation uses the Agent tool's `isolation:"worktree"` directly — there is NO worktree helper script.
- **Out of scope (known follow-up):** `cc-conductor` observes musician runs via the deleted run state; after this plan its musician-watching is dead code. Do NOT touch `cc-conductor` here — it is a separate task.

---

### Task 1: Strip the run machinery from cc-musician

Delete the self-driving-run substrate and the heavy conductor skill. After this task the plugin still has the old `commands/musician.md` (rewritten in Task 5) but no skill, hooks, run scripts, or their tests.

**Files:**
- Delete: `plugins/cc-musician/skills/musician/` (whole dir: `SKILL.md`, `arm.sh`, `worktree.sh`)
- Delete: `plugins/cc-musician/hooks/` (whole dir: `musician-stop.sh`, `nonstop-stop.sh`, `musician-observe.sh`, `musician-resolve.sh`, `hooks.json`)
- Delete: `plugins/cc-musician/commands/musician-cancel.md`
- Delete: `plugins/cc-musician/bin/` (whole dir: `ccmusicianctl`)
- Delete: `plugins/cc-musician/tests/test_arm.py`, `test_worktree.py`, `test_musician_hook.py`, `test_observe_hook.py`, `test_nonstop_hook.py`, `test_ccmusicianctl.py`, `test_skill_invariants.py`

- [ ] **Step 1: Remove the files**

```bash
cd plugins/cc-musician
git rm -r skills/musician hooks bin commands/musician-cancel.md
git rm tests/test_arm.py tests/test_worktree.py tests/test_musician_hook.py \
       tests/test_observe_hook.py tests/test_nonstop_hook.py \
       tests/test_ccmusicianctl.py tests/test_skill_invariants.py
```

- [ ] **Step 2: Verify no dangling references remain inside the plugin**

Run:
```bash
cd plugins/cc-musician
grep -rn -e "arm.sh" -e "worktree.sh" -e "state.json" -e "nonstop" -e "ccmusicianctl" \
        -e "musician-cancel" -e "by-session" -e "heartbeat" -e "awaiting" \
        . --include=*.md --include=*.json | grep -v "^./commands/musician.md"
```
Expected: no output (the only remaining references are in the still-old `commands/musician.md`, which Task 5 rewrites — those are excluded above).

- [ ] **Step 3: Verify the tests directory is empty and the plugin dir is clean**

Run: `ls plugins/cc-musician/tests/ && ls plugins/cc-musician/`
Expected: `tests/` is empty (or contains only `__pycache__`); plugin dir has `.claude-plugin/`, `commands/`, `README.md` and no `skills/ hooks/ bin/`.

- [ ] **Step 4: Commit**

```bash
git add -A plugins/cc-musician
git commit -m "refactor(musician): strip the self-driving run machinery

Remove arm/state/hooks/nonstop/cancel/ccmusicianctl and the heavy
conductor skill — the router replaces them. cc-conductor's musician
view is now dead code, handled separately."
```

---

### Task 2: Create the `build-small` tier skill

The lightest tier: make the fix and confirm nothing broke. Minimal ceremony.

**Files:**
- Create: `plugins/cc-musician/skills/build-small/SKILL.md`

**Interfaces:**
- Produces: a skill whose frontmatter `name` is exactly `build-small` (the router invokes it by this name).

- [ ] **Step 1: Write the skill file**

Frontmatter (exact):
```markdown
---
name: build-small
description: "Use for a small, low-risk code change — a fix or tweak that is clear and self-contained. The lightest build tier: make the change and confirm nothing broke, minimal ceremony."
---
```

Body must cover, in plain language (lean — only what serves the purpose):
- **What this tier is for:** a clear, small, low-risk change. If it turns out bigger or riskier than it looked, say so and hand back up to a heavier tier (name `build-medium`/`build-large`) rather than forcing it.
- **How it works:** no task list, no shaping. Make the change (a direct `Edit`/`Write`, or a single `cc-script:do` dispatch if the change benefits from `do`'s smoke/verify), then run a quick check that nothing broke (the obvious smoke: run the touched thing / the relevant test).
- **Flags it honors:** `--fast` → skip even the smoke if trivial and go faster; `--worktree` → make the change in an Agent `isolation:"worktree"` dispatch instead of inline; `--ultracode` → rarely relevant at this tier, but if set, fan out only if there genuinely are independent sub-changes; `--auto` → don't ask, just do it.
- **Rules:** read and obey `.claude/rules/*.md`; if you dispatch a subagent, tell it to do the same.
- **No run bookkeeping** — this is a one-shot in the conversation; nothing to arm or close.

- [ ] **Step 2: Verify frontmatter name**

Run: `grep -m1 '^name:' plugins/cc-musician/skills/build-small/SKILL.md`
Expected: `name: build-small`

- [ ] **Step 3: Commit**

```bash
git add plugins/cc-musician/skills/build-small/SKILL.md
git commit -m "feat(musician): add build-small tier skill"
```

---

### Task 3: Create the `build-medium` tier skill

The middle tier: a real change that needs a couple of build passes but not full decomposition.

**Files:**
- Create: `plugins/cc-musician/skills/build-medium/SKILL.md`

**Interfaces:**
- Produces: a skill whose frontmatter `name` is exactly `build-medium`.

- [ ] **Step 1: Write the skill file**

Frontmatter (exact):
```markdown
---
name: build-medium
description: "Use for a medium change — real work across a few pieces, but not a whole feature. Lighter than the full pipeline: one or two build passes and a light check, no heavy task-list decomposition."
---
```

Body must cover (lean):
- **What this tier is for:** a change bigger than a one-line fix but smaller than a feature — a handful of edits that hang together. If it grows into a real feature, hand up to `build-large`.
- **How it works:** no shaping phase and no formal task list. Do the work in one or two `cc-script:do` dispatches (code changes go through `do`, not inline — this tier is big enough that `do`'s smoke/verify earns its keep), then a light check that the change works (run the app path / the relevant tests). No mandatory heavy hardening.
- **Isolation:** default is a `cc-script:do` dispatch with Agent `isolation:"worktree"` when the change touches enough that dirtying the main tree mid-flight is a risk; a small self-contained medium change may run without it. `--worktree` forces isolation.
- **Flags it honors:** `--fast` → lighter model / fewer passes / minimal check; `--worktree` → force isolation; `--ultracode` → fan out `do` across independent pieces; `--auto` → resolve forks yourself, no `AskUserQuestion`.
- **Roadmap upkeep:** if the change advanced a roadmap feature, mark it `[x]` at the end (route, never goal — never reorder or add features).
- **Rules:** read/obey `.claude/rules/*.md` and pass them to every dispatched subagent.

- [ ] **Step 2: Verify frontmatter name**

Run: `grep -m1 '^name:' plugins/cc-musician/skills/build-medium/SKILL.md`
Expected: `name: build-medium`

- [ ] **Step 3: Commit**

```bash
git add plugins/cc-musician/skills/build-medium/SKILL.md
git commit -m "feat(musician): add build-medium tier skill"
```

---

### Task 4: Create the `build-large` tier skill

The full-weight tier. This is the home of the heavy orchestration the router no longer holds — the essential guts of the old musician build loop, minus the run machinery.

**Files:**
- Create: `plugins/cc-musician/skills/build-large/SKILL.md`

**Interfaces:**
- Produces: a skill whose frontmatter `name` is exactly `build-large`.

- [ ] **Step 1: Write the skill file**

Frontmatter (exact):
```markdown
---
name: build-large
description: "Use for a large feature or substantial build — the full pipeline. Break the work into an ordered task list, build in an isolated worktree, harden, run a real final verification, then reconcile the roadmap."
---
```

Body must cover (lean but complete — these are the invariants carried over from the old conductor):
- **What this tier is for:** a real feature / substantial build worth the full weight.
- **Decompose:** break the work into an ordered task list (each item a single dispatched unit); the building is ONE segment (one `do` dispatch in one worktree builds all pieces and hardens once), never a build task per commit. The LAST task is ALWAYS a real verification of the observable outcome.
- **Conduct, never perform:** every code change goes through a `cc-script:do` subagent — never inline `Edit`/`Write` on product code. Your own notes (task list, roadmap marks) you write directly.
- **Build in an isolated worktree:** dispatch the build with the Agent tool's `isolation:"worktree"` and `model:"opus"`; capture `BASE = git rev-parse HEAD` first and tell the subagent its first action is `git reset --hard <BASE>`, then `do` → chain `cc-script:refactor-review-test` which makes one local commit inside the worktree. Integrate fast-forward-only onto local `main`; if it won't fast-forward (base moved / not on main), discard and rebuild — never merge stale work silently. (Integration is done with plain git — `git merge --ff-only <branch>` then remove the worktree — since there is no helper script.)
- **Verification gate:** the run isn't done until the final verify task runs a REAL check and passes. A failed verify appends fix tasks; it never closes.
- **Roadmap upkeep:** mark finished features `[x]` (route only); if the work reveals the goal itself is wrong, surface it (`/roadmap-management`) — never edit the goal.
- **Flags:** `--fast` → fewer/cheaper passes where safe; `--worktree` → already the default here; `--ultracode` → maximum fan-out (a Workflow and/or parallel `do` subagents, each `isolation:"worktree"`, each ff-integrated as it lands); `--auto` → resolve every fork yourself, no `AskUserQuestion`; without `--auto`, ask the human at genuine forks.
- **Rules:** read/obey `.claude/rules/*.md` and tell every dispatched subagent (brain and build) to read and obey them.
- **No run bookkeeping:** there is no `arm`, `state.json`, `awaiting`, or Stop-hook loop — the work is carried in the conversation, turn by turn.

- [ ] **Step 2: Verify frontmatter name and that no run-machinery terms leaked in**

Run:
```bash
grep -m1 '^name:' plugins/cc-musician/skills/build-large/SKILL.md
grep -c -e "state.json" -e "arm.sh" -e "awaiting" -e "nonstop" \
   plugins/cc-musician/skills/build-large/SKILL.md
```
Expected: `name: build-large`, and `0` for the machinery terms.

- [ ] **Step 3: Commit**

```bash
git add plugins/cc-musician/skills/build-large/SKILL.md
git commit -m "feat(musician): add build-large tier skill (full pipeline)"
```

---

### Task 5: Rewrite `commands/musician.md` as the router

Replace the arm-first command with routing instructions.

**Files:**
- Modify (full rewrite): `plugins/cc-musician/commands/musician.md`

**Interfaces:**
- Consumes: the three tier skill names from Tasks 2–4 (`build-small`, `build-medium`, `build-large`) and the existing plugin skills (`cc-script:architect`, `cc-instruments:crux`, `cc-instruments:slap`, `cc-script:roadmap-management`, `cc-script:what-to-do`, and the cc-script/cc-instruments management + diagram skills).

- [ ] **Step 1: Write the command file**

Frontmatter:
```markdown
---
description: "Hand the project any piece of work — a fix, a change, a feature, a question. /musician is a router: it reads the goal + design, sizes the work, and routes it to the right skill. Flags tune how (--auto acts without asking, --fast, --worktree, --ultracode); the router decides what."
argument-hint: "[task / problem / idea — or nothing to find the work] [--auto] [--fast] [--worktree] [--ultracode]"
---
```

Body must instruct the model to (plain language, lean):
1. **Ground first:** read `docs/ccharness/roadmap.md` (North Star + features) and the architecture under `docs/ccharness/architecture/` as context before deciding anything.
2. **Classify the task from its text and route to ONE component** — the router decides *what*; flags never pick the route. Include this route table verbatim:

   | The task is… | Route to |
   | --- | --- |
   | a large feature / substantial build | skill `build-large` |
   | a medium change | skill `build-medium` |
   | a small fix | skill `build-small` |
   | designing a new system | `cc-script:architect` |
   | a fuzzy pain / "something's off" | `cc-instruments:crux` |
   | stuck in a debugging rabbit hole | `cc-instruments:slap` |
   | changing the goal / priorities | `cc-script:roadmap-management` |
   | "what should I do next" (empty prompt) | `cc-script:what-to-do` |
   | rules / cheatsheet / docs / diagrams upkeep | the matching cc-instruments management or diagram skill |

3. **North Star gate:** if the task is build work and the roadmap has no `## Product North Star`, tell the user to run `/roadmap-management` first; don't build. Non-build routes (`crux`, `slap`) are not gated.
4. **Asking vs deciding:** by default, interactive — at a genuine fork (including "is this small or medium?") you MAY ask the human with `AskUserQuestion`. With `--auto`, do NOT ask — resolve every fork yourself.
5. **Flags = how, not what** — list them: `--auto` (act without asking), `--fast` (lighter/faster), `--worktree` (force isolation), `--ultracode` (maximum fan-out). Pass the active flags to the chosen skill so it adjusts its weight. Flags stack; they never change the route.
6. **Reconcile after:** if the work advanced a roadmap feature or shifted the design, update `roadmap.md` / the architecture (mark a feature done, note a design shift). Work that touched neither → no upkeep.
7. **No run bookkeeping:** there is no arming, no state, no self-perpetuating loop, no `/musician-cancel`. `/musician` runs in the conversation.

- [ ] **Step 2: Verify the command names every route and flag**

Run:
```bash
cd plugins/cc-musician
grep -c -e "build-large" -e "build-medium" -e "build-small" \
        -e "\-\-auto" -e "\-\-fast" -e "\-\-worktree" -e "\-\-ultracode" \
        -e "roadmap" commands/musician.md
grep -c -e "arm.sh" -e "state.json" -e "musician-cancel" commands/musician.md
```
Expected: first grep prints a positive count for each; second grep prints `0`.

- [ ] **Step 3: Commit**

```bash
git add plugins/cc-musician/commands/musician.md
git commit -m "feat(musician): rewrite the command as a thin router"
```

---

### Task 6: Update manifests and README

Bring `plugin.json`, the marketplace entry, and the README in line with the router design.

**Files:**
- Modify: `plugins/cc-musician/.claude-plugin/plugin.json` (description + version bump)
- Modify: `.claude-plugin/marketplace.json` (the `cc-musician` entry description)
- Modify (rewrite): `plugins/cc-musician/README.md`

- [ ] **Step 1: Rewrite `plugin.json` description and bump the version**

Set `description` to a plain summary of the router (thin router: reads roadmap + architecture, sizes the work, routes to build-large/medium/small or any plugin skill; flags tune how — `--auto` acts without asking, `--fast`/`--worktree`/`--ultracode`; no run machinery, no self-driving loop). Bump `version` from `0.26.0` to `0.27.0`.

- [ ] **Step 2: Rewrite the `cc-musician` entry in `marketplace.json`**

Replace its `description` with the same plain router summary (one paragraph, matching the style of the other entries).

- [ ] **Step 3: Rewrite `README.md`**

Rewrite to describe the router: what `/musician` is now (one entry point that routes by task size to build tiers or to any plugin skill), the three tiers, the flags (how, not what), and that there is no persistent loop. Remove all mention of arm/state/nonstop/shaping/cancel. Keep it lean.

- [ ] **Step 4: Verify manifests are valid JSON and version bumped**

Run:
```bash
python3 -c "import json,sys; json.load(open('plugins/cc-musician/.claude-plugin/plugin.json')); json.load(open('.claude-plugin/marketplace.json')); print('json ok')"
grep '"version"' plugins/cc-musician/.claude-plugin/plugin.json
```
Expected: `json ok`; version shows `0.27.0`.

- [ ] **Step 5: Commit**

```bash
git add plugins/cc-musician/.claude-plugin/plugin.json .claude-plugin/marketplace.json plugins/cc-musician/README.md
git commit -m "docs(musician): update manifests and README for the router"
```

---

### Task 7: Add the router contract test

One lean test guards the real text↔code contracts: the three tier skills exist with the exact names the command routes to, the command names every flag, and no run-machinery token lingers anywhere in the plugin. This is not prose-pinning — it guards names the router depends on and the completeness of the deletion.

**Files:**
- Create: `plugins/cc-musician/tests/test_router_invariants.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CMD = ROOT / "commands" / "musician.md"
SKILLS = ROOT / "skills"
TIERS = ("build-large", "build-medium", "build-small")


class TestRouterInvariants(unittest.TestCase):
    def test_tier_skills_exist_with_exact_names(self):
        for tier in TIERS:
            skill = SKILLS / tier / "SKILL.md"
            self.assertTrue(skill.is_file(), f"{tier} SKILL.md missing")
            first = next(
                (ln for ln in skill.read_text().splitlines() if ln.startswith("name:")),
                "",
            )
            self.assertEqual(first.strip(), f"name: {tier}")

    def test_command_routes_to_every_tier(self):
        text = CMD.read_text()
        for tier in TIERS:
            self.assertIn(tier, text, f"command does not route to {tier}")

    def test_command_names_every_flag(self):
        text = CMD.read_text()
        for flag in ("--auto", "--fast", "--worktree", "--ultracode"):
            self.assertIn(flag, text, f"command does not mention {flag}")

    def test_no_run_machinery_left_in_plugin(self):
        gone = ("arm.sh", "state.json", "nonstop", "ccmusicianctl",
                "musician-cancel", "by-session", "awaiting")
        for path in ROOT.rglob("*"):
            if path.suffix not in (".md", ".json", ".py"):
                continue
            if path.name == "test_router_invariants.py":
                continue
            body = path.read_text()
            for token in gone:
                self.assertNotIn(token, body, f"{token} still in {path}")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test**

Run: `cd plugins/cc-musician && python3 -m unittest tests.test_router_invariants -v`
Expected: all four tests PASS (Tasks 1–6 already satisfy them). If `test_no_run_machinery_left_in_plugin` fails, a deletion or rewrite missed a token — fix that file, don't weaken the test.

- [ ] **Step 3: Commit**

```bash
git add plugins/cc-musician/tests/test_router_invariants.py
git commit -m "test(musician): pin router route/flag names and deletion completeness"
```

---

## Notes for the implementer

- **cc-conductor is deliberately untouched.** Its `ccconductor/musician.py`, the musician parts of its conductor skill, and its musician tests now read run state that no longer exists — that is a known, separate follow-up, not a regression to fix here.
- **Stale docs elsewhere** (`docs/specs/2026-06-30-product-maestro-and-ccmusician.md`, `plugins/cc-script/README.md`, `plugins/cc-script/skills/what-to-do/SKILL.md`) mention the old musician loop/nonstop. Leave them for the same follow-up unless a task above explicitly changes them.
- **Order matters loosely:** Tasks 2–4 (skills) before Task 5 (command) so the router's routes exist; Task 7 last so it validates the finished surface. Between Task 1 and Task 5 the old `commands/musician.md` still references the deleted `arm.sh` — that is expected and harmless during the plan (nobody invokes it mid-build); Task 5 fixes it.
```
