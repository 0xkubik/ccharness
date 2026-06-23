# cc-* 3-Plugin Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the single `ccharness` plugin into a visible 3-layer hierarchy — `cc-tools` (the funnel skills), `cc-agent` (autopilot extracted), `cc-maestro` (a stub for the console built in the next plan) — with zero change to any skill's behavior.

**Architecture:** Pure structural refactor. `git mv` the `ccharness` plugin to `cc-tools`, lift the autopilot skill + its two commands + its Stop hook out into a new `cc-agent` plugin, repoint cross-plugin skill references to the `cc-tools:` namespace, scaffold an empty `cc-maestro` plugin, and update the marketplace + installer + READMEs. Control flows top-down (`cc-maestro` → `cc-agent` → `cc-tools`); usage flows bottom-up.

**Tech Stack:** Claude Code plugins (JSON manifests + Markdown skills/commands + a bash Stop hook). Verification via `jq`, `grep`, and `claude --plugin-dir`.

## Global Constraints

- **Pure restructure — NO behavior change** to any skill's or hook's logic. Only names, paths, and cross-references move.
- **Preserve git history:** use `git mv` for every move/rename (never delete+recreate).
- **Runtime state dir path stays `.claude/ccharness/`** (locked decision #2 in the spec). Do NOT rewrite `.claude/ccharness` occurrences — those are the live state directory, intentionally stable. Only the *plugin name* and the *`ccharness:` skill namespace* change.
- **Cross-plugin skill references use the `cc-tools:` namespace** (e.g. `cc-tools:grill-it`).
- **Three plugin directories under `plugins/`:** `cc-tools`, `cc-agent`, `cc-maestro`. `cc-agent` depends on `cc-tools` (its autopilot skill invokes cc-tools skills). `cc-maestro` is an empty scaffold in this plan.
- Spec: `docs/superpowers/specs/2026-06-23-cc-maestro-design.md` (§4 cc-agent, §5 cc-tools, §8 Phase 0–1).

---

### Task 1: Rename the `ccharness` plugin directory → `cc-tools`

**Files:**
- Move: `plugins/ccharness/` → `plugins/cc-tools/` (whole tree)
- Modify: `plugins/cc-tools/.claude-plugin/plugin.json`

**Interfaces:**
- Produces: the `cc-tools` plugin directory (still containing the autopilot files at this point — removed in Task 2).

- [ ] **Step 1: Move the directory (history-preserving)**

```bash
cd /Users/kubik/nox/misc/claude-code-harness
git mv plugins/ccharness plugins/cc-tools
```

- [ ] **Step 2: Rewrite the plugin manifest** — replace the entire contents of `plugins/cc-tools/.claude-plugin/plugin.json` with:

```json
{
  "name": "cc-tools",
  "version": "0.9.0",
  "description": "cc-tools — the tools layer of the cc-* harness: single-purpose product skills. /chart-it captures the product's North Star and charts a roadmap; /point-it ranks where a product could go next; /grill-it thinks one fork through to ONE decision; /implement-it drives one task to done via a gated 0→6 pipeline; /slap resets a stuck fix. Driven by cc-agent (autopilot) and supervised by cc-maestro.",
  "author": {
    "name": "kubik",
    "email": "dev@noxlabs.xyz"
  }
}
```

- [ ] **Step 3: Verify the manifest parses and the dir moved**

Run: `jq . plugins/cc-tools/.claude-plugin/plugin.json >/dev/null && echo OK; ls plugins/cc-tools/skills`
Expected: `OK`, then the skill dirs listed (`autopilot chart-it grill-it implement-it point-it slap`).

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: rename ccharness plugin -> cc-tools"
```

---

### Task 2: Extract the `cc-agent` plugin (autopilot) out of `cc-tools`

**Files:**
- Create: `plugins/cc-agent/.claude-plugin/plugin.json`
- Move: `plugins/cc-tools/skills/autopilot/` → `plugins/cc-agent/skills/autopilot/`
- Move: `plugins/cc-tools/commands/autopilot.md` → `plugins/cc-agent/commands/autopilot.md`
- Move: `plugins/cc-tools/commands/autopilot-cancel.md` → `plugins/cc-agent/commands/autopilot-cancel.md`
- Move: `plugins/cc-tools/hooks/` → `plugins/cc-agent/hooks/` (contains `autopilot-stop.sh` + `hooks.json`; the whole `hooks/` dir is autopilot-only)

**Interfaces:**
- Consumes: the `cc-tools` dir from Task 1.
- Produces: the `cc-agent` plugin holding the autopilot skill, its two commands, and the never-stop Stop hook. The `hooks.json` `command` uses `${CLAUDE_PLUGIN_ROOT}` so it keeps working after the move (resolves to cc-agent's root). After this task `cc-tools` has no `hooks/` dir and no autopilot files.

- [ ] **Step 1: Create the cc-agent skeleton and move the files**

```bash
cd /Users/kubik/nox/misc/claude-code-harness
mkdir -p plugins/cc-agent/.claude-plugin plugins/cc-agent/skills plugins/cc-agent/commands
git mv plugins/cc-tools/skills/autopilot plugins/cc-agent/skills/autopilot
git mv plugins/cc-tools/commands/autopilot.md plugins/cc-agent/commands/autopilot.md
git mv plugins/cc-tools/commands/autopilot-cancel.md plugins/cc-agent/commands/autopilot-cancel.md
git mv plugins/cc-tools/hooks plugins/cc-agent/hooks
```

- [ ] **Step 2: Write the cc-agent manifest** — create `plugins/cc-agent/.claude-plugin/plugin.json`:

```json
{
  "name": "cc-agent",
  "version": "0.1.0",
  "description": "cc-agent — the self-driving agent layer: /autopilot runs the cc-tools funnel (point-it -> grill-it -> implement-it) in a never-stop loop that only /autopilot-cancel halts, enforced by a Stop hook. Depends on cc-tools.",
  "author": {
    "name": "kubik",
    "email": "dev@noxlabs.xyz"
  }
}
```

- [ ] **Step 3: Verify the split**

Run:
```bash
jq . plugins/cc-agent/.claude-plugin/plugin.json >/dev/null && echo MANIFEST_OK
ls plugins/cc-agent/skills plugins/cc-agent/commands plugins/cc-agent/hooks
test ! -e plugins/cc-tools/hooks && test ! -e plugins/cc-tools/skills/autopilot && echo CC_TOOLS_CLEAN
```
Expected: `MANIFEST_OK`; `autopilot`, `autopilot.md autopilot-cancel.md`, `autopilot-stop.sh hooks.json`; then `CC_TOOLS_CLEAN`.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: extract autopilot into cc-agent plugin"
```

---

### Task 3: Repoint cross-plugin skill references to `cc-tools:`

**Files:**
- Modify: `plugins/cc-agent/skills/autopilot/SKILL.md` (3 refs)
- Modify: `plugins/cc-tools/skills/grill-it/SKILL.md` (2 refs)
- Modify: `plugins/cc-tools/skills/implement-it/SKILL.md` (4 refs)
- Modify: `plugins/cc-tools/skills/point-it/SKILL.md` (1 ref)

**Interfaces:**
- Consumes: the two plugin dirs from Tasks 1–2.
- Produces: every `ccharness:<skill>` cross-reference rewritten to `cc-tools:<skill>` (all targets — grill-it, implement-it, point-it, slap — live in cc-tools). This is the reference that lets cc-agent's autopilot invoke the funnel after the split.

- [ ] **Step 1: Rewrite the namespaced references**

```bash
cd /Users/kubik/nox/misc/claude-code-harness
grep -rl "ccharness:" plugins | while read -r f; do
  sed -i '' 's/ccharness:/cc-tools:/g' "$f"
done
```

- [ ] **Step 2: Verify no stale namespaced refs remain, and the live state path is untouched**

Run:
```bash
grep -rn "ccharness:" plugins && echo "STALE REFS FOUND" || echo "NO_STALE_REFS"
grep -rc "\.claude/ccharness" plugins | grep -v ':0' | wc -l
```
Expected: `NO_STALE_REFS` (grep finds nothing), and the second command prints a non-zero count — confirming the `.claude/ccharness` runtime-state paths were intentionally left in place.

- [ ] **Step 3: Spot-check the autopilot skill resolves to cc-tools**

Run: `grep -n "cc-tools:" plugins/cc-agent/skills/autopilot/SKILL.md`
Expected: lines showing `cc-tools:point-it`, `cc-tools:grill-it`, `cc-tools:implement-it`.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: repoint cross-plugin skill refs to cc-tools namespace"
```

---

### Task 4: Scaffold the `cc-maestro` stub plugin

**Files:**
- Create: `plugins/cc-maestro/.claude-plugin/plugin.json`
- Create: `plugins/cc-maestro/README.md`

**Interfaces:**
- Produces: a valid (empty-of-skills) `cc-maestro` plugin so the marketplace can list the full hierarchy now; the `ccmaestro` CLI + commands land in the next plan.

- [ ] **Step 1: Write the stub manifest** — create `plugins/cc-maestro/.claude-plugin/plugin.json`:

```json
{
  "name": "cc-maestro",
  "version": "0.0.1",
  "description": "cc-maestro — the conductor layer: the `ccmaestro` console observes and controls many coding agents and autopilots at once (token burn, stalls, loops, stop/steer), usable by a human in a terminal and by an external agent. Scaffolding only; the CLI is built in the cc-maestro tool plan.",
  "author": {
    "name": "kubik",
    "email": "dev@noxlabs.xyz"
  }
}
```

- [ ] **Step 2: Write the README placeholder** — create `plugins/cc-maestro/README.md`:

```markdown
# cc-maestro

The conductor of the cc-* harness. The `ccmaestro` CLI watches and controls many
coding agents and autopilots at once — token burn, stalls, loops, silent deaths —
and lets both a human (in a terminal) and an external agent launch, stop, and
steer them.

**Status:** scaffold. The CLI and commands are built by the cc-maestro tool plan
(`docs/superpowers/plans/`). See the design at
`docs/superpowers/specs/2026-06-23-cc-maestro-design.md`.
```

- [ ] **Step 3: Verify the manifest parses**

Run: `jq . plugins/cc-maestro/.claude-plugin/plugin.json >/dev/null && echo OK`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: scaffold cc-maestro plugin (conductor layer stub)"
```

---

### Task 5: Update `marketplace.json` to list all three plugins

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: the three plugin dirs.
- Produces: a marketplace listing `cc-tools`, `cc-agent`, `cc-maestro`. NOTE: the marketplace `name` changes from `ccharness` to `cc-harness`; after this, the user re-syncs the marketplace (Task 7) for Claude Code to pick up the new layout.

- [ ] **Step 1: Replace the entire file** `.claude-plugin/marketplace.json` with:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-marketplace.json",
  "name": "cc-harness",
  "description": "cc-harness — a layered harness for Claude Code: cc-tools (single-purpose product skills) -> cc-agent (autopilot, one self-driving agent) -> cc-maestro (the ccmaestro console that watches and controls many agents at once).",
  "owner": {
    "name": "kubik",
    "email": "dev@noxlabs.xyz"
  },
  "plugins": [
    {
      "name": "cc-tools",
      "description": "The tools layer: /chart-it, /point-it, /grill-it, /implement-it, /slap — single-purpose product skills forming a ground -> diverge -> decide -> build funnel. Zero-config.",
      "author": { "name": "kubik" },
      "category": "workflow",
      "source": "./plugins/cc-tools"
    },
    {
      "name": "cc-agent",
      "description": "The self-driving agent layer: /autopilot runs the cc-tools funnel in a never-stop loop that only /autopilot-cancel halts. Depends on cc-tools.",
      "author": { "name": "kubik" },
      "category": "workflow",
      "source": "./plugins/cc-agent"
    },
    {
      "name": "cc-maestro",
      "description": "The conductor layer: the ccmaestro console observes and controls many coding agents and autopilots at once (tokens, stalls, loops, stop/steer).",
      "author": { "name": "kubik" },
      "category": "workflow",
      "source": "./plugins/cc-maestro"
    }
  ]
}
```

- [ ] **Step 2: Verify JSON and entry count**

Run: `jq '.plugins | length' .claude-plugin/marketplace.json`
Expected: `3`

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "refactor: list cc-tools/cc-agent/cc-maestro in marketplace"
```

---

### Task 6: Update the installer command and the plugin READMEs

**Files:**
- Move: `plugins/cc-tools/commands/ccharness-init.md` → `plugins/cc-tools/commands/cc-init.md`
- Modify: `plugins/cc-tools/commands/cc-init.md` (prose only)
- Modify: `plugins/cc-tools/README.md` (prose only)
- Create: `plugins/cc-agent/README.md`

**Interfaces:**
- Consumes: the renamed plugins.
- Produces: the installer renamed to `/cc-init` with prose referring to the new structure (its *function* — installing the external dependency plugins like `superpowers` — is unchanged), and READMEs describing the 3-layer hierarchy. **`.claude/ccharness/` runtime paths in prose are preserved.**

- [ ] **Step 1: Rename the installer command**

```bash
cd /Users/kubik/nox/misc/claude-code-harness
git mv plugins/cc-tools/commands/ccharness-init.md plugins/cc-tools/commands/cc-init.md
```

- [ ] **Step 2: Update the installer prose** — in `plugins/cc-tools/commands/cc-init.md`, make these exact replacements (leave the external-dependency table and any `.claude/ccharness/` paths unchanged):
  - Heading `# ccharness-init — equip the harness with the plugins it orchestrates` → `# cc-init — equip the harness with the plugins it orchestrates`
  - The sentence `ccharness is glue: ...route to skills from **other** plugins.` → `cc-tools is glue: \`/point-it\`, \`/grill-it\`, and \`/implement-it\` route to skills from **other** plugins.`
  - The "Source of truth" line `\`plugins/ccharness/README.md\`` → `\`plugins/cc-tools/README.md\``
  - Any remaining standalone product-name mention of the plugin `ccharness` (NOT the `.claude/ccharness` path) → `cc-tools`.

- [ ] **Step 3: Update `plugins/cc-tools/README.md` prose** — replace standalone plugin-name mentions of `ccharness` with `cc-tools`, add a short top note that this is the **tools layer** of the cc-* hierarchy (with `cc-agent` above it and `cc-maestro` at the top), and **preserve every `.claude/ccharness/` path** verbatim (those are the live state dir). Remove autopilot-specific sections that now live in cc-agent (move that prose to the cc-agent README in Step 4).

- [ ] **Step 4: Create `plugins/cc-agent/README.md`:**

```markdown
# cc-agent

The self-driving agent layer of the cc-* harness. `/autopilot` runs the cc-tools
funnel (point-it -> grill-it -> implement-it) in a continuous loop, committing one
improvement per cycle. It never stops on its own — a Stop hook re-feeds the loop;
only `/autopilot-cancel` halts it.

- Depends on **cc-tools** (it invokes `cc-tools:point-it`, `cc-tools:grill-it`,
  `cc-tools:implement-it`).
- Runtime state lives under `.claude/ccharness/autopilot/` (path kept stable across
  the rename): `state.json` (loop control), `log.jsonl` (cycle history),
  `blocked.jsonl` (review queue + point-it exclusion list).
- Supervised by **cc-maestro**, which treats an autopilot as a special agent:
  "done" = a new `log.jsonl` cycle; "stop" = cancel, not a raw kill.
```

- [ ] **Step 5: Verify naming**

Run:
```bash
cd /Users/kubik/nox/misc/claude-code-harness
echo "--- stale plugin-name 'ccharness' in commands/readmes (path refs are OK) ---"
grep -rn "ccharness" plugins/cc-tools/commands plugins/cc-tools/README.md plugins/cc-agent/README.md | grep -v "\.claude/ccharness" || echo "NONE"
echo "--- installer renamed ---"
test -e plugins/cc-tools/commands/cc-init.md && test ! -e plugins/cc-tools/commands/ccharness-init.md && echo RENAMED
```
Expected: `NONE` (no plugin-name mentions left; only `.claude/ccharness/` paths survive), then `RENAMED`.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "docs: rename installer to cc-init and update plugin READMEs"
```

---

### Task 7: End-to-end verification that the restructure loads and works

**Files:** none (verification + the marketplace re-sync the user performs).

**Interfaces:**
- Consumes: everything from Tasks 1–6.
- Produces: confirmation that all three plugins load, the autopilot skill resolves `cc-tools:*` across the plugin boundary, and the Stop hook still fires.

- [ ] **Step 1: Static checks (all JSON valid, no stale refs)**

Run:
```bash
cd /Users/kubik/nox/misc/claude-code-harness
for f in .claude-plugin/marketplace.json plugins/*/.claude-plugin/plugin.json; do jq . "$f" >/dev/null && echo "OK $f"; done
grep -rn "ccharness:" plugins && echo "FAIL: stale namespace" || echo "OK: no stale namespace"
```
Expected: one `OK <path>` per manifest (4 lines), then `OK: no stale namespace`.

- [ ] **Step 2: Headless load check (plugins parse + skills register)**

Run:
```bash
cd /Users/kubik/nox/misc/claude-code-harness
claude --plugin-dir plugins/cc-tools --plugin-dir plugins/cc-agent --plugin-dir plugins/cc-maestro \
  -p "List the slash commands you have available from loaded plugins, one per line." 2>&1 | tail -30
```
Expected: output that includes `point-it`, `grill-it`, `implement-it`, `chart-it`, `slap`, `cc-init` (from cc-tools) and `autopilot`, `autopilot-cancel` (from cc-agent), with no plugin-load errors. (If load errors appear, fix the offending manifest/skill before proceeding.)

- [ ] **Step 3: Manual smoke test — cross-plugin resolution + Stop hook**

Do this in a real interactive Claude Code session (plugin hooks need the full runtime):
1. Re-sync the marketplace so Claude Code sees the new layout: in a session run `/plugin marketplace add /Users/kubik/nox/misc/claude-code-harness` (or refresh it if already added), then enable `cc-tools`, `cc-agent`, `cc-maestro`.
2. Run `/point-it` on any repo — confirm it runs (cc-tools loads).
3. Run `/autopilot` for ONE cycle on a throwaway change, confirm it invokes `cc-tools:point-it` / `grill-it` / `implement-it` without "skill not found", then `/autopilot-cancel`. This proves cross-plugin skill resolution AND that the relocated Stop hook re-feeds and cancels correctly.

Expected: the funnel skills resolve from inside cc-agent's autopilot, and cancel reports cycle count cleanly.

- [ ] **Step 4: Update the auto-memory index** (the structure note is now stale)

Edit `/Users/kubik/.claude/projects/-Users-kubik-nox-misc-claude-code-harness/memory/MEMORY.md`: update the `ccharness pivot` line to note the harness is now 3 plugins (`cc-tools` / `cc-agent` / `cc-maestro`), and update `harness repo layout` to "marketplace of 3 plugins (cc-tools, cc-agent, cc-maestro)". (No commit — memory lives outside the repo.)

- [ ] **Step 5: Final commit (if Step 4 touched anything in-repo, otherwise skip)**

```bash
cd /Users/kubik/nox/misc/claude-code-harness
git status --short
```
Expected: clean (all task commits already made). The restructure is complete.

---

## Self-Review

**Spec coverage (§4, §5, §8 Phase 0–1):**
- §5 cc-tools rename → Tasks 1, 3, 6. ✓
- §4 cc-agent extraction (skill + 2 commands + Stop hook + plugin.json + installer-aware) → Tasks 2, 6. ✓
- Cross-plugin `cc-tools:` refs verified to resolve → Tasks 3, 7. ✓
- Runtime state path kept stable (decision #2) → Global Constraints + verified in Tasks 3, 6. ✓
- cc-maestro registered in the hierarchy now (stub) → Tasks 4, 5. ✓
- "installer learns the new structure" → Task 6 (its function—installing external deps—is unchanged; only naming updates). ✓

**Placeholder scan:** No TBD/TODO; every step has exact commands or full file contents. README prose edits in Task 6 Steps 2–3 are find→replace instructions with explicit preserve rules (acceptable — the source files are long and pre-exist; the edits are enumerated, not vague).

**Type/name consistency:** plugin names `cc-tools` / `cc-agent` / `cc-maestro`, command `cc-init`, namespace `cc-tools:`, marketplace `cc-harness`, state path `.claude/ccharness/` (unchanged) — used identically across all tasks.

**Known caveat (not a gap):** changing the marketplace `name` to `cc-harness` may require the user to re-add/refresh the marketplace (Task 7 Step 3 covers this). The plugin *cache* under `~/.claude/plugins/` may need a refresh for the rename to take effect at runtime.
