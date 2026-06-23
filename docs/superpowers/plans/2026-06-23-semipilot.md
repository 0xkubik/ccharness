# semipilot + autopilot-wrapper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `/semipilot` — a bounded loop that drives the cc-tools funnel toward ONE roadmap milestone and stops itself when met (or gives up) — and rebuild `/autopilot` as a thin meta-loop that arms a fresh semipilot per milestone, walking the roadmap.

**Architecture:** Two Stop hooks partition by which state file is active, so exactly one drives per turn: `semipilot-stop.sh` re-feeds the bounded cycle while a milestone is in flight; `autopilot-stop.sh` re-feeds a meta-step only in the gap between milestones (advance / retry-once / dependency-judge → park+advance or hard-stop / cheap-idle). The funnel cycle and done-detection live once, in the semipilot skill. State is layered under `.claude/ccharness/{semipilot,autopilot}/`.

**Tech Stack:** Bash hooks (`jq`, fail-closed, atomic temp+`mv`); Markdown SKILL/command files; Python `unittest` (stdlib) tests that subprocess the bash hooks. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-06-23-semipilot-design.md` (authoritative for the detailed prose; this plan sequences and verifies the build).

## Global Constraints

- **State paths stay under `.claude/ccharness/`** (the directory name is kept stable across the cc-* rename): `semipilot/{state.json,blocked.jsonl,log.jsonl}` and `autopilot/{state.json,blocked.jsonl,log.jsonl}`.
- **Hooks fail CLOSED**: while a loop is active, any parse anomaly re-feeds rather than allowing a silent stop. Allow-the-stop only on the explicit exits.
- **Session scoping**: a loop is owned by the session whose id is in its `state.json`; the skill writes `$CLAUDE_CODE_SESSION_ID` there. Hooks compare against the `session_id` on stdin.
- **Atomic writes**: every `state.json` mutation is temp-file + `mv`.
- **Skills call the funnel by qualified name**: `cc-tools:point-it`, `cc-tools:grill-it`, `cc-tools:implement-it`, `cc-tools:slap`.
- **Defaults**: `max_no_progress = 3`, `max_cycles = 20`, `max_retries = 1`.
- **No `AskUserQuestion` under any loop** (it blocks on a human); point-it must emit its menu as data.
- **Plugin**: everything lives in `plugins/cc-agent/`. Commands/skills/hooks are auto-discovered; only `hooks.json` needs a manual entry.

---

## File Structure

| File | Responsibility |
| --- | --- |
| `plugins/cc-agent/hooks/semipilot-stop.sh` | **New.** Re-feed the bounded semipilot cycle while its state is active for this session. |
| `plugins/cc-agent/hooks/autopilot-stop.sh` | **Rewrite.** Yield while a semipilot is active; in the gap, re-feed the meta-step. |
| `plugins/cc-agent/hooks/hooks.json` | **Modify.** Register a second `Stop` entry for `semipilot-stop.sh`. |
| `plugins/cc-agent/skills/semipilot/SKILL.md` | **New.** The bounded-loop discipline: done-first cycle, two exits, milestone-scoped pick. |
| `plugins/cc-agent/skills/autopilot/SKILL.md` | **Rewrite.** The meta-loop: arm-first-semipilot + the give-up ladder. |
| `plugins/cc-agent/commands/semipilot.md` | **New.** Arm `/semipilot`. |
| `plugins/cc-agent/commands/semipilot-cancel.md` | **New.** The manual brake. |
| `plugins/cc-agent/commands/autopilot.md` | **Modify.** Roadmap-required; "stops on cancel OR hard block." |
| `plugins/cc-agent/.claude-plugin/plugin.json` | **Modify.** Mention both modes. |
| `plugins/cc-agent/README.md` | **Modify.** Document both modes + layered state. |
| `plugins/cc-agent/tests/test_semipilot_hook.py` | **New.** Hook decision tests. |
| `plugins/cc-agent/tests/test_autopilot_hook.py` | **New.** Partition + meta-step tests. |

---

## Task 1: semipilot Stop hook + registration

**Files:**
- Create: `plugins/cc-agent/hooks/semipilot-stop.sh`
- Modify: `plugins/cc-agent/hooks/hooks.json`
- Test: `plugins/cc-agent/tests/test_semipilot_hook.py`

**Interfaces:**
- Consumes: hook stdin JSON `{session_id}`; reads `.claude/ccharness/semipilot/state.json` fields `{active, session_id, cycle, target_milestone}`.
- Produces: on block, stdout JSON `{"decision":"block","reason":<refeed>,"systemMessage":<msg>}`; on allow, exit 0 with empty stdout. (autopilot-stop.sh in Task 4 reads the same `semipilot/state.json.active`.)

- [ ] **Step 1: Write the failing test**

Create `plugins/cc-agent/tests/test_semipilot_hook.py`:

```python
import json, subprocess, tempfile, unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "semipilot-stop.sh"
SESSION = "11111111-1111-1111-1111-111111111111"
OTHER = "22222222-2222-2222-2222-222222222222"


def run_hook(repo, stdin_obj):
    r = subprocess.run(["bash", str(HOOK)], input=json.dumps(stdin_obj),
                       cwd=repo, capture_output=True, text=True)
    return r.returncode, r.stdout


def repo_with(state=None):
    repo = tempfile.mkdtemp()
    if state is not None:
        d = Path(repo) / ".claude" / "ccharness" / "semipilot"
        d.mkdir(parents=True, exist_ok=True)
        (d / "state.json").write_text(json.dumps(state))
    return repo


class TestSemipilotHook(unittest.TestCase):
    def test_no_state_allows_stop(self):
        rc, out = run_hook(repo_with(), {"session_id": SESSION})
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_active_same_session_blocks(self):
        repo = repo_with({"active": True, "session_id": SESSION,
                          "cycle": 2, "target_milestone": "M2"})
        rc, out = run_hook(repo, {"session_id": SESSION})
        self.assertEqual(rc, 0)
        self.assertIn('"decision"', out)
        self.assertIn("block", out)

    def test_inactive_allows_stop(self):
        repo = repo_with({"active": False, "session_id": SESSION})
        _, out = run_hook(repo, {"session_id": SESSION})
        self.assertEqual(out.strip(), "")

    def test_different_session_allows_stop(self):
        repo = repo_with({"active": True, "session_id": SESSION})
        _, out = run_hook(repo, {"session_id": OTHER})
        self.assertEqual(out.strip(), "")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd plugins/cc-agent && python -m pytest tests/test_semipilot_hook.py -v`
Expected: FAIL — the hook file does not exist yet (bash: cannot open `semipilot-stop.sh`), so the "blocks" assertion fails.

- [ ] **Step 3: Write the hook**

Create `plugins/cc-agent/hooks/semipilot-stop.sh`:

```bash
#!/usr/bin/env bash
# semipilot — Stop hook (the bounded loop's "hard muscle").
#
# While the semipilot state file is ACTIVE for THIS session, re-feed the
# semipilot prompt on every Stop so the bounded loop runs one cycle per turn.
# Unlike autopilot, semipilot ENDS ON ITS OWN: the model flips active:false
# when the milestone is achieved OR it gives up, and THEN this hook (Exit #2)
# allows the stop. This hook only prevents an accidental mid-milestone stop.
#
# Fail CLOSED while active. Allow-the-stop paths (exit 0, no stdout):
#   1. no state file
#   2. state.active == false        (achieved / gave-up / capped / cancelled)
#   3. a DIFFERENT session owns it
set -u

STATE_FILE=".claude/ccharness/semipilot/state.json"
HOOK_INPUT="$(cat 2>/dev/null || true)"

[ -f "$STATE_FILE" ] || exit 0

HOOK_SESSION=""; STATE_SESSION=""; STATE_ACTIVE=""; CYCLE="?"; TARGET="?"
if command -v jq >/dev/null 2>&1; then
  HOOK_SESSION="$(printf '%s' "$HOOK_INPUT" | jq -r '.session_id // ""' 2>/dev/null || true)"
  STATE_SESSION="$(jq -r '.session_id // ""'   "$STATE_FILE" 2>/dev/null || true)"
  STATE_ACTIVE="$(jq -r '.active'              "$STATE_FILE" 2>/dev/null || true)"
  CYCLE="$(jq -r '.cycle // "?"'               "$STATE_FILE" 2>/dev/null || echo '?')"
  TARGET="$(jq -r '.target_milestone // "?"'   "$STATE_FILE" 2>/dev/null || echo '?')"
fi

# Exit #2 — milestone achieved / gave up / cancelled.
[ "$STATE_ACTIVE" = "false" ] && exit 0

# Exit #3 — a different session owns the loop.
if [ -n "$STATE_SESSION" ] && [ -n "$HOOK_SESSION" ] && [ "$STATE_SESSION" != "$HOOK_SESSION" ]; then
  exit 0
fi

# --- ACTIVE for this session (or present-but-unparseable) → RE-FEED. Fail closed. ---
REFEED="$(cat <<'PROMPT'
🎯 semipilot is ACTIVE — continue the bounded loop for THIS milestone. Run exactly ONE cycle:
1. Read .claude/ccharness/semipilot/state.json + blocked.jsonl.
2. DONE-CHECK FIRST: survey "now" and judge it against state.done_when. If MET → mark the milestone [x] in roadmap.md, set active:false (atomic temp+mv) with outcome:"achieved", append a final log.jsonl line, report, END THE TURN.
3. GIVE-UP CHECK: if no_progress_streak >= max_no_progress OR cycle >= max_cycles → set active:false with outcome:"gave-up" or "capped", report the blocked queue, END THE TURN.
4. Otherwise run ONE funnel cycle SCOPED to the target milestone: cc-tools:point-it (menu as DATA, NO AskUserQuestion) → keep only directions whose `advances` == target milestone and not in blocked.jsonl → auto-pick the top → cc-tools:grill-it → cc-tools:implement-it → LOCAL commit. Update no_progress_streak (reset on real progress; ++ on blocked/idle/no-movement; a handback from implement-it appends to blocked.jsonl and counts as no-progress), append a log line, bump cycle (atomic), END THE TURN.
You stop ONLY by flipping active:false on achieved/gave-up/capped, or the user runs /semipilot-cancel. Do not otherwise stop.
PROMPT
)"

if command -v jq >/dev/null 2>&1; then
  jq -n \
    --arg r "$REFEED" \
    --arg m "🎯 semipilot ${TARGET} cycle ${CYCLE} -> continuing (done-check first; /semipilot-cancel to stop)" \
    '{decision:"block", reason:$r, systemMessage:$m}'
else
  printf '%s' '{"decision":"block","reason":"semipilot is active — run one bounded cycle: read .claude/ccharness/semipilot/state.json, DONE-check first, then give-up check, then one milestone-scoped funnel cycle; flip active:false on achieved/gave-up/capped. /semipilot-cancel to stop."}'
fi

exit 0
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd plugins/cc-agent && python -m pytest tests/test_semipilot_hook.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Register the hook in `hooks.json`**

Replace `plugins/cc-agent/hooks/hooks.json` with:

```json
{
  "description": "cc-agent Stop hooks: autopilot meta-loop + semipilot bounded loop. Exactly one re-feeds per turn (semipilot while a milestone is in flight; autopilot in the gap).",
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/autopilot-stop.sh\""
          }
        ]
      },
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/semipilot-stop.sh\""
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 6: Commit**

```bash
git add plugins/cc-agent/hooks/semipilot-stop.sh plugins/cc-agent/hooks/hooks.json plugins/cc-agent/tests/test_semipilot_hook.py
git commit -m "feat(cc-agent): semipilot Stop hook + registration + tests"
```

---

## Task 2: semipilot SKILL.md

**Files:**
- Create: `plugins/cc-agent/skills/semipilot/SKILL.md`
- Test: structural grep (below)

**Interfaces:**
- Consumes: the funnel skills `cc-tools:*`; the roadmap at `.claude/ccharness/roadmap.md`; `$CLAUDE_CODE_SESSION_ID`.
- Produces: writes `.claude/ccharness/semipilot/state.json` with the schema in spec §2.2 (`active, session_id, mode:"semipilot", target_milestone, done_when, cycle, no_progress_streak, max_no_progress, max_cycles, started_at, last_surveyed_sha, outcome`). autopilot's skill (Task 5) reads `outcome` and arms this same state.

- [ ] **Step 1: Write the failing structural test**

Create `plugins/cc-agent/tests/test_skill_invariants.py` (this file also covers Task 5; add the semipilot block now):

```python
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMI = (ROOT / "skills" / "semipilot" / "SKILL.md")


class TestSemipilotSkill(unittest.TestCase):
    def setUp(self):
        self.text = SEMI.read_text() if SEMI.exists() else ""

    def test_exists(self):
        self.assertTrue(SEMI.exists(), "semipilot SKILL.md missing")

    def test_done_check_leads(self):
        self.assertIn("DONE", self.text)
        self.assertIn("done_when", self.text)

    def test_two_exits(self):
        for token in ("achieved", "gave-up", "max_cycles", "no_progress_streak"):
            self.assertIn(token, self.text)

    def test_milestone_scoped_pick(self):
        self.assertIn("advances", self.text)
        self.assertIn("blocked.jsonl", self.text)

    def test_no_askuserquestion_under_loop(self):
        self.assertIn("AskUserQuestion", self.text)  # must mention it to forbid it

    def test_roadmap_gate(self):
        self.assertIn("chart-it", self.text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd plugins/cc-agent && python -m pytest tests/test_skill_invariants.py -v`
Expected: FAIL — `test_exists` fails (file missing) and the others fail on empty text.

- [ ] **Step 3: Write the SKILL**

Create `plugins/cc-agent/skills/semipilot/SKILL.md` following spec §2 (arm, the done-first cycle, the two exits, milestone-scoped pick, nested-awareness). It MUST contain:

- **Frontmatter** `name: semipilot` + a `description:` matching the command's one-liner.
- **Arm section** (spec §2.2): roadmap gate (no North Star → route `/chart-it`; North Star but no roadmap → `/chart-it`; else resolve target = arg id or current first-unchecked, copy its `done when:`); nested-awareness (if `.claude/ccharness/autopilot/state.json` is active for this session, stay terse on exit); atomic state write with the §2.2 schema; touch `blocked.jsonl`/`log.jsonl`.
- **One cycle** — paste this block verbatim:

```
1. READ   semipilot/state.json + semipilot/blocked.jsonl
2. DONE?  Survey "now" (point-it Phase 1), judge against state.done_when.
          MET → active:false, outcome:"achieved", mark milestone [x] in roadmap.md, final log line,
                 (terse if nested / full report if standalone), END TURN.
3. GIVE-UP?  no_progress_streak >= max_no_progress  OR  cycle >= max_cycles
          → active:false, outcome:"gave-up" | "capped", final log line, report blocked queue, END TURN.
4. POINT  cc-tools:point-it — menu as DATA ("I pick — do NOT call AskUserQuestion").
          Keep ONLY directions whose `advances` == target milestone AND not in blocked.jsonl.
          → auto-pick the top.   NONE qualify → no-progress cycle: streak++, go to 8.
5. DECIDE cc-tools:grill-it on that direction → one decision
6. BUILD  cc-tools:implement-it → verify → LOCAL commit (no push)
          handback (unbuildable/forked, or slap-twice) → append to blocked.jsonl, no-progress cycle.
7. PROGRESS?  committed work that moves done_when closer → streak = 0
              otherwise → streak++
8. LOG    log.jsonl line {cycle, target, picked, outcome, moved_goal, streak, sha?, ts}; bump cycle (atomic).
9. END TURN → the semipilot hook re-feeds.
```

- **A "milestone-scoped, not roadmap-biased" note** (spec §2.3): semipilot FILTERS to milestone-advancing directions; an empty filtered set is itself a no-progress signal.
- **The two exits** (spec §2.4) and an explicit "no double-confirm of done."

- [ ] **Step 4: Run the structural test to verify it passes**

Run: `cd plugins/cc-agent && python -m pytest tests/test_skill_invariants.py::TestSemipilotSkill -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/cc-agent/skills/semipilot/SKILL.md plugins/cc-agent/tests/test_skill_invariants.py
git commit -m "feat(cc-agent): semipilot skill — bounded done-first loop"
```

---

## Task 3: /semipilot + /semipilot-cancel commands

**Files:**
- Create: `plugins/cc-agent/commands/semipilot.md`, `plugins/cc-agent/commands/semipilot-cancel.md`

**Interfaces:**
- Consumes: the `semipilot` skill; `.claude/ccharness/semipilot/state.json`.
- Produces: nothing other tasks consume.

- [ ] **Step 1: Write `/semipilot`**

Create `plugins/cc-agent/commands/semipilot.md`:

```markdown
---
description: "Drive the cc-tools funnel toward ONE roadmap milestone and stop when its `done when:` is met (or give up after N no-progress cycles / a cycle cap). The bounded unit; autopilot wraps it. Needs a roadmap — run /chart-it first."
argument-hint: "[milestone id e.g. M3 — default: current] [--give-up-after N] [--max-cycles N]"
---

Invoke the `semipilot` skill to arm and run the BOUNDED goal-seeking loop, with this argument:

> $ARGUMENTS

semipilot takes ONE roadmap milestone as its goal and drives the funnel (point-it → grill-it →
implement-it) toward it, **stopping itself** the moment the milestone's `done when:` is met. It has a
second exit — **give up** after N cycles with no progress (default 3) or a hard cycle cap (default 20),
the token-burn backstop. No milestone id → the current (first unchecked) milestone. It needs a roadmap;
with none it routes you to **`/chart-it`**. Stop it early with **`/semipilot-cancel`**.
```

- [ ] **Step 2: Write `/semipilot-cancel`**

Create `plugins/cc-agent/commands/semipilot-cancel.md`:

```markdown
---
description: "Stop the running semipilot loop — the manual brake. Removes the semipilot state so the Stop hook stops re-feeding, then reports cycles run and the blocked queue."
---

Stop the semipilot loop. Do exactly this:

1. If `.claude/ccharness/semipilot/state.json` does **not** exist → say *"No semipilot is running."* and stop.
2. Read it for the `cycle` count and `target_milestone`, then **remove `state.json`** (`rm`). This lets the
   next `Stop` end the turn — the hook re-feeds only while that file is present and active. (Removing it,
   rather than flipping a flag, lets a fresh `/semipilot` re-arm cleanly.)
3. Leave `blocked.jsonl` and `log.jsonl` in place — they are the durable record. Report: **cycles run**,
   the **target milestone**, and the entries in `.claude/ccharness/semipilot/blocked.jsonl` (each one's
   `direction` + `reason`). If the queue is empty, say so.
```

- [ ] **Step 3: Verify frontmatter parses (sanity)**

Run: `head -3 plugins/cc-agent/commands/semipilot.md plugins/cc-agent/commands/semipilot-cancel.md`
Expected: each shows a `---` / `description:` frontmatter opening.

- [ ] **Step 4: Commit**

```bash
git add plugins/cc-agent/commands/semipilot.md plugins/cc-agent/commands/semipilot-cancel.md
git commit -m "feat(cc-agent): /semipilot + /semipilot-cancel commands"
```

---

## Task 4: autopilot Stop hook rewrite (the partition + meta-step)

**Files:**
- Modify: `plugins/cc-agent/hooks/autopilot-stop.sh`
- Test: `plugins/cc-agent/tests/test_autopilot_hook.py`

**Interfaces:**
- Consumes: hook stdin `{session_id}`; `.claude/ccharness/autopilot/state.json` `{active, session_id, current_milestone}`; `.claude/ccharness/semipilot/state.json` `{active}` (the partition guard).
- Produces: on block, the meta-step refeed JSON; on allow, exit 0 empty.

- [ ] **Step 1: Write the failing test**

Create `plugins/cc-agent/tests/test_autopilot_hook.py`:

```python
import json, subprocess, tempfile, unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "autopilot-stop.sh"
SESSION = "11111111-1111-1111-1111-111111111111"
OTHER = "22222222-2222-2222-2222-222222222222"


def run_hook(repo, stdin_obj):
    r = subprocess.run(["bash", str(HOOK)], input=json.dumps(stdin_obj),
                       cwd=repo, capture_output=True, text=True)
    return r.returncode, r.stdout


def repo_with(autopilot=None, semipilot=None):
    repo = tempfile.mkdtemp()
    base = Path(repo) / ".claude" / "ccharness"
    if autopilot is not None:
        (base / "autopilot").mkdir(parents=True, exist_ok=True)
        (base / "autopilot" / "state.json").write_text(json.dumps(autopilot))
    if semipilot is not None:
        (base / "semipilot").mkdir(parents=True, exist_ok=True)
        (base / "semipilot" / "state.json").write_text(json.dumps(semipilot))
    return repo


class TestAutopilotHook(unittest.TestCase):
    def test_no_state_allows_stop(self):
        _, out = run_hook(repo_with(), {"session_id": SESSION})
        self.assertEqual(out.strip(), "")

    def test_semipilot_active_yields(self):
        # autopilot active AND a semipilot in flight → autopilot hook must YIELD
        repo = repo_with(
            autopilot={"active": True, "session_id": SESSION, "current_milestone": "M1"},
            semipilot={"active": True, "session_id": SESSION})
        _, out = run_hook(repo, {"session_id": SESSION})
        self.assertEqual(out.strip(), "")

    def test_gap_blocks_metastep(self):
        # autopilot active, no semipilot in flight → re-feed the meta-step
        repo = repo_with(
            autopilot={"active": True, "session_id": SESSION, "current_milestone": "M1"},
            semipilot={"active": False, "session_id": SESSION})
        rc, out = run_hook(repo, {"session_id": SESSION})
        self.assertIn("block", out)
        self.assertIn("meta-step", out)

    def test_gap_no_semipilot_file_blocks(self):
        repo = repo_with(autopilot={"active": True, "session_id": SESSION, "current_milestone": "M1"})
        _, out = run_hook(repo, {"session_id": SESSION})
        self.assertIn("block", out)

    def test_autopilot_inactive_allows(self):
        repo = repo_with(autopilot={"active": False, "session_id": SESSION})
        _, out = run_hook(repo, {"session_id": SESSION})
        self.assertEqual(out.strip(), "")

    def test_different_session_allows(self):
        repo = repo_with(autopilot={"active": True, "session_id": SESSION, "current_milestone": "M1"})
        _, out = run_hook(repo, {"session_id": OTHER})
        self.assertEqual(out.strip(), "")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd plugins/cc-agent && python -m pytest tests/test_autopilot_hook.py -v`
Expected: FAIL — the current hook has no semipilot-yield guard (`test_semipilot_active_yields` blocks instead of yielding) and no "meta-step" wording (`test_gap_blocks_metastep` fails).

- [ ] **Step 3: Rewrite the hook**

Replace `plugins/cc-agent/hooks/autopilot-stop.sh` with:

```bash
#!/usr/bin/env bash
# autopilot — Stop hook (the meta-loop's "hard muscle").
#
# autopilot is a WRAPPER over semipilot: it walks the roadmap milestone by
# milestone by arming a fresh semipilot for each. This hook re-feeds the
# META-STEP only in the GAP between milestones — while autopilot is active AND
# no semipilot is in flight. While a semipilot is active, THIS hook yields and
# semipilot-stop.sh drives, so exactly one hook blocks per turn.
#
# Fail CLOSED while active. Allow-the-stop paths (exit 0, no stdout):
#   1. no autopilot state file
#   2. autopilot active == false          (cancelled, or hard-stopped on a dependent block)
#   3. a DIFFERENT session owns autopilot
#   4. a semipilot is ACTIVE for this session  (yield; semipilot-stop.sh drives)
set -u

STATE_FILE=".claude/ccharness/autopilot/state.json"
SEMI_FILE=".claude/ccharness/semipilot/state.json"
HOOK_INPUT="$(cat 2>/dev/null || true)"

[ -f "$STATE_FILE" ] || exit 0

HOOK_SESSION=""; STATE_SESSION=""; STATE_ACTIVE=""; CUR="?"; SEMI_ACTIVE=""
if command -v jq >/dev/null 2>&1; then
  HOOK_SESSION="$(printf '%s' "$HOOK_INPUT" | jq -r '.session_id // ""' 2>/dev/null || true)"
  STATE_SESSION="$(jq -r '.session_id // ""'   "$STATE_FILE" 2>/dev/null || true)"
  STATE_ACTIVE="$(jq -r '.active'              "$STATE_FILE" 2>/dev/null || true)"
  CUR="$(jq -r '.current_milestone // "?"'     "$STATE_FILE" 2>/dev/null || echo '?')"
  [ -f "$SEMI_FILE" ] && SEMI_ACTIVE="$(jq -r '.active' "$SEMI_FILE" 2>/dev/null || true)"
fi

# Exit #2 — autopilot cancelled or hard-stopped.
[ "$STATE_ACTIVE" = "false" ] && exit 0

# Exit #3 — a different session owns the meta-loop.
if [ -n "$STATE_SESSION" ] && [ -n "$HOOK_SESSION" ] && [ "$STATE_SESSION" != "$HOOK_SESSION" ]; then
  exit 0
fi

# Exit #4 — a semipilot is in flight → yield; its hook drives this turn.
[ "$SEMI_ACTIVE" = "true" ] && exit 0

# --- autopilot active AND no semipilot in flight → RE-FEED the META-STEP. Fail closed. ---
REFEED="$(cat <<'PROMPT'
🛰️ autopilot meta-loop is ACTIVE and a semipilot just ended — run ONE meta-step:
1. Read .claude/ccharness/semipilot/state.json (its `outcome`), .claude/ccharness/autopilot/state.json, autopilot/blocked.jsonl (parked milestones), and .claude/ccharness/roadmap.md.
2. outcome == "achieved": the milestone is now [x]. Set current_retries=0. next = first unchecked milestone NOT in autopilot/blocked.jsonl. next exists → set current_milestone=next and ARM a fresh semipilot on it (write .claude/ccharness/semipilot/state.json active:true, atomic). none → roadmap complete → CHEAP IDLE: log "roadmap-complete-idle", do NOT stop, END THE TURN.
3. outcome == "gave-up" | "capped":
   - current_retries == 0 → RETRY ONCE: set current_retries=1, re-arm a fresh semipilot on the SAME milestone.
   - current_retries == 1 → judge the roadmap: does the next unchecked milestone DEPEND on the stuck one? INDEPENDENT → park it (append to autopilot/blocked.jsonl), reset current_retries=0, advance to the next non-parked unchecked milestone, arm a fresh semipilot. DEPENDENT → HARD STOP: set autopilot active:false with outcome:"blocked", report the stuck milestone + parked queue, END THE TURN.
4. Append one line to autopilot/log.jsonl {milestone, action, ts} (atomic) and END THE TURN.
Never declare autopilot "done" except the HARD STOP in 3. An exhausted roadmap is a cheap idle, not a stop. /autopilot-cancel also stops it.
PROMPT
)"

if command -v jq >/dev/null 2>&1; then
  jq -n \
    --arg r "$REFEED" \
    --arg m "🛰️ autopilot meta-step @ ${CUR} (semipilot ended; arming next / handling give-up)" \
    '{decision:"block", reason:$r, systemMessage:$m}'
else
  printf '%s' '{"decision":"block","reason":"autopilot meta-loop active and a semipilot ended — run one meta-step: read semipilot outcome + roadmap, then advance / retry-once / dependency-judge (independent->park+advance, dependent->hard-stop). Cheap-idle if roadmap complete. /autopilot-cancel to stop."}'
fi

exit 0
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd plugins/cc-agent && python -m pytest tests/test_autopilot_hook.py -v`
Expected: PASS (6 passed).

- [ ] **Step 5: Run BOTH hook tests together (partition sanity)**

Run: `cd plugins/cc-agent && python -m pytest tests/test_semipilot_hook.py tests/test_autopilot_hook.py -v`
Expected: PASS (10 passed) — confirms the two hooks' decisions are consistent.

- [ ] **Step 6: Commit**

```bash
git add plugins/cc-agent/hooks/autopilot-stop.sh plugins/cc-agent/tests/test_autopilot_hook.py
git commit -m "feat(cc-agent): autopilot Stop hook -> meta-loop (yield-while-semipilot + meta-step)"
```

---

## Task 5: autopilot SKILL.md rewrite (the meta-loop)

**Files:**
- Modify: `plugins/cc-agent/skills/autopilot/SKILL.md`
- Test: add a `TestAutopilotSkill` class to `plugins/cc-agent/tests/test_skill_invariants.py`

**Interfaces:**
- Consumes: the `semipilot` skill/state; the roadmap.
- Produces: writes `.claude/ccharness/autopilot/state.json` per spec §3.2 (`active, session_id, mode:"autopilot", current_milestone, current_retries, max_retries, started_at, outcome`); arms `semipilot/state.json`.

- [ ] **Step 1: Add the failing structural test**

Append to `plugins/cc-agent/tests/test_skill_invariants.py`:

```python
AUTO = (ROOT / "skills" / "autopilot" / "SKILL.md")


class TestAutopilotSkill(unittest.TestCase):
    def setUp(self):
        self.text = AUTO.read_text()

    def test_is_meta_loop_over_semipilot(self):
        self.assertIn("semipilot", self.text)

    def test_give_up_ladder(self):
        for token in ("current_retries", "retry", "DEPEND", "park", "HARD STOP"):
            self.assertIn(token, self.text)

    def test_roadmap_required(self):
        self.assertIn("chart-it", self.text)

    def test_idle_on_exhaustion(self):
        self.assertIn("idle", self.text)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd plugins/cc-agent && python -m pytest tests/test_skill_invariants.py::TestAutopilotSkill -v`
Expected: FAIL — the current autopilot SKILL embeds the funnel cycle and has no `current_retries` / `DEPEND` / `HARD STOP` wording.

- [ ] **Step 3: Rewrite the SKILL**

Replace `plugins/cc-agent/skills/autopilot/SKILL.md` following spec §3. Keep `name: autopilot` frontmatter and an updated `description:`. It MUST contain:

- **Framing**: autopilot is a thin meta-loop over semipilot; it no longer runs the funnel itself.
- **Arm** (spec §3.2): roadmap REQUIRED (no North Star → `/chart-it`; North Star but no roadmap → `/chart-it`); write the §3.2 outer `state.json` (with `current_retries:0, max_retries:1`); arm the first semipilot on the current milestone (nested); touch `autopilot/log.jsonl` + `autopilot/blocked.jsonl` (the parked-milestones queue).
- **The meta-cycle** — paste this block verbatim:

```
outcome == achieved:
    milestone is [x]. current_retries = 0.
    next = first unchecked milestone NOT in autopilot/blocked.jsonl
    next exists → current_milestone = next, arm a fresh semipilot, END TURN.
    none left  → roadmap exhausted → CHEAP IDLE (never stop), log "roadmap-complete-idle", END TURN.

outcome == gave-up | capped:
    current_retries == 0 → set current_retries = 1, re-arm semipilot on the SAME milestone, END TURN.
    current_retries == 1 → does the next unchecked milestone DEPEND on the stuck one?
        INDEPENDENT → park it (autopilot/blocked.jsonl), current_retries = 0,
                       advance to next non-parked unchecked, arm semipilot, END TURN.
        DEPENDENT   → HARD STOP: autopilot active:false, outcome:"blocked",
                       report stuck milestone + parked queue, END TURN.
```

- **The dependency judgment** (spec §3.4): a soft model read of the lightweight roadmap text; v1 judges the immediate next milestone; dependent is the common case.
- **Outcomes** (spec §3.5): looping / cheap-idle / **hard-stop+exit (new)** / cancelled. State explicitly that the hard stop is a legitimate self-stop — "only `/autopilot-cancel` stops it" is no longer absolute.
- **Remove** all the old embedded funnel-cycle prose (point-it/grill-it/implement-it per-cycle) — that now lives in semipilot.

- [ ] **Step 4: Run the structural test to verify it passes**

Run: `cd plugins/cc-agent && python -m pytest tests/test_skill_invariants.py -v`
Expected: PASS (both skill classes).

- [ ] **Step 5: Commit**

```bash
git add plugins/cc-agent/skills/autopilot/SKILL.md plugins/cc-agent/tests/test_skill_invariants.py
git commit -m "feat(cc-agent): autopilot skill -> meta-loop over semipilot (give-up ladder)"
```

---

## Task 6: command + plugin docs

**Files:**
- Modify: `plugins/cc-agent/commands/autopilot.md`, `plugins/cc-agent/.claude-plugin/plugin.json`, `plugins/cc-agent/README.md`

**Interfaces:** none consumed by other tasks (documentation).

- [ ] **Step 1: Update `/autopilot` command prose**

Edit `plugins/cc-agent/commands/autopilot.md`: change the body so it states autopilot **walks the roadmap milestone by milestone via semipilot**, **requires a roadmap** (no roadmap → `/chart-it`), and **stops on `/autopilot-cancel` OR a hard dependency block**. Remove the old "refuses to arm without a North Star; runs toward the North Star directly with no roadmap" wording. Keep the `description:` frontmatter accurate to this.

- [ ] **Step 2: Update `plugin.json` description**

Edit `plugins/cc-agent/.claude-plugin/plugin.json` `description` to:

```
cc-agent — the self-driving agent layer: /semipilot drives the cc-tools funnel toward ONE roadmap milestone and stops; /autopilot wraps it as a meta-loop walking the whole roadmap (retry-once, then dependency-judge: park+advance or hard-stop). Two Stop hooks partition by active state. Depends on cc-tools.
```

- [ ] **Step 3: Update `README.md`**

Edit `plugins/cc-agent/README.md` to document: the two modes (semipilot = bounded unit, autopilot = wrapper); the give-up ladder; the layered state dirs (`.claude/ccharness/semipilot/` cycle-level, `.claude/ccharness/autopilot/` milestone-level with `blocked.jsonl` = parked milestones); the two-hook partition; and that autopilot can now hard-stop on a dependent block.

- [ ] **Step 4: Verify the whole cc-agent test suite passes**

Run: `cd plugins/cc-agent && python -m pytest tests/ -v`
Expected: PASS (all hook + skill-invariant tests).

- [ ] **Step 5: Commit**

```bash
git add plugins/cc-agent/commands/autopilot.md plugins/cc-agent/.claude-plugin/plugin.json plugins/cc-agent/README.md
git commit -m "docs(cc-agent): document semipilot + autopilot-wrapper, layered state"
```

---

## Final verification (end-to-end smoke, manual)

Not a unit test — a behavioral check on a throwaway repo with a roadmap:

- [ ] On a scratch repo with a North Star + a 2-milestone roadmap whose M1 `done when:` is already met: run `/semipilot` → it stops `achieved` on the first cycle and marks M1 `[x]`.
- [ ] Point `/semipilot M2` at a milestone with no buildable direction → it stops `gave-up` after `max_no_progress` cycles and reports the blocked queue.
- [ ] Run `/autopilot` on the same roadmap → it completes M1 via semipilot, the autopilot hook arms M2, and on roadmap exhaustion it cheap-idles (never stops).
- [ ] Force a give-up on a milestone whose next milestone is dependent → assert one retry, then a HARD STOP that ends the session; confirm `/autopilot-cancel` also ends a live loop and reports the parked queue.
- [ ] Confirm the partition live: while a semipilot cycle runs, the autopilot hook stays dormant (no double re-feed in the systemMessage stream).

---

## Self-Review

**Spec coverage:** §2 semipilot (Tasks 1–3) · §3 autopilot meta-loop + give-up ladder (Tasks 4–5) · §4 two-hook partition (Tasks 1, 4 + tests) · §5 layered state (Task 2/5 schemas, Task 6 README) · §6 file changes (all tasks) · §10 build sequence (task order). The cc-maestro forward-compat note (§7) is intentionally not built (out of scope).

**Placeholder scan:** hook bodies and test code are complete and runnable; SKILL prose tasks give exact required sections + verbatim cycle/ladder blocks + structural tests rather than "write the prose" hand-waves.

**Type consistency:** state schemas match across tasks — semipilot `{active, session_id, mode, target_milestone, done_when, cycle, no_progress_streak, max_no_progress, max_cycles, last_surveyed_sha, outcome}`; autopilot `{active, session_id, mode, current_milestone, current_retries, max_retries, outcome}`. The hooks read exactly the fields the skills write (`active`, `session_id`, `current_milestone`, semipilot `.active`).
