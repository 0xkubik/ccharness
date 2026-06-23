# ccmaestro — Observe Layer (Phase 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `ccmaestro` CLI's observe layer — a single command that shows every Claude Code agent on the machine, how many tokens each has burned, when it was last active, and a watchdog verdict (ok / stalled / looping / over-budget / died) — plus a launcher and a log viewer. Usable by a human in a terminal and by an external agent (hermes) via `--json`.

**Architecture:** A thin Python wrapper over native Claude Code primitives — no daemon. The agent list comes from `claude agents --json --all`; per-agent tokens and activity come from each session's transcript `.jsonl`; the watchdog derives stall/loop/death verdicts that the native status does not provide. `ccmaestro` keeps its own launch records (one `meta.json` per agent it starts) and merges them with the native list by `sessionId`. The watchdog runs on demand inside `ls` (no background process). Control (stop/steer) and reporting are a later plan (Phase 3); this plan is observe + launch.

**Tech Stack:** Python 3.9+ (standard library ONLY: `json`, `subprocess`, `pathlib`, `os`, `datetime`, `argparse`, `unittest`). Lives in `plugins/cc-maestro/`. No third-party dependencies, ever.

## Global Constraints

- **Python 3.9-compatible, standard library only.** No `pip install`, no third-party imports. (System Python is 3.9.6.)
- **Timestamps:** transcript `timestamp` values are ISO strings ending in `Z`; Python 3.9 `datetime.fromisoformat` rejects `Z`. Always parse via `datetime.fromisoformat(s.replace("Z", "+00:00"))` and compare against a tz-aware "now" (`datetime.now(timezone.utc)`).
- **Token source:** sum `line["message"]["usage"]` fields (`input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`) over `type == "assistant"` lines. Do NOT add a telemetry collector.
- **Transcript location:** resolve by `sessionId` via glob `~/.claude/projects/*/<sessionId>.jsonl` (robust to cwd path encoding) — honor `$CLAUDE_CONFIG_DIR` if set (default `~/.claude`).
- **State dir:** global, `~/.ccmaestro/` (honor `$CCMAESTRO_HOME` override for tests): `config.json`, `agents/<id>/meta.json`, `events.jsonl`.
- **Single source of truth:** read native sources every call (never cache tokens/state); `ccmaestro`'s own launch records are authoritative for what it launched, merged with `claude agents --json` by `sessionId`.
- **Atomic writes:** any file `ccmaestro` writes (meta.json, events.jsonl) uses temp-file + `os.replace` (two writers may race).
- **Launch permission posture:** `ccmaestro start` MUST pass a permission mode or a headless agent hangs on the first prompt. Default `acceptEdits` + a curated `--allowedTools` allowlist; `--yolo` opts into `bypassPermissions` (logged, deliberate).
- **Test convention:** each test file self-bootstraps `sys.path` to import the `ccmaestro` package and is run directly: `python3 plugins/cc-maestro/tests/test_<x>.py -v`.
- Spec: `docs/superpowers/specs/2026-06-23-cc-maestro-design.md` (§3 cc-maestro design; §7a open questions resolved: global `~/.ccmaestro/`, concurrency cap deferred to Phase 3).

## File Structure

```
plugins/cc-maestro/
  bin/ccmaestro                 # executable entry: bootstraps sys.path, calls ccmaestro.cli.main()
  ccmaestro/
    __init__.py
    config.py                   # DEFAULTS + load_config() + STATE_DIR
    paths.py                    # transcript_path(sid), agent_dir(id), ensure_state_dir(), atomic_write()
    transcript.py               # parse_transcript(path) -> summary dict
    registry.py                 # native_agents(), load_meta_records(), merge()
    watchdog.py                 # looping(), verdict()
    autopilot.py                # is_autopilot(cwd), autopilot_summary(cwd)
    launcher.py                 # build_launch_argv(), start()
    render.py                   # build_rows(), render_table(), render_json()
    cli.py                      # argparse: ls / start / logs
  commands/maestro.md           # /maestro slash command -> runs `ccmaestro ls`
  tests/
    test_config.py test_paths.py test_transcript.py test_registry.py
    test_watchdog.py test_autopilot.py test_launcher.py test_render.py
  README.md                     # replace the stub
```

---

### Task 1: Package scaffold, config, and paths

**Files:**
- Create: `plugins/cc-maestro/ccmaestro/__init__.py` (empty)
- Create: `plugins/cc-maestro/ccmaestro/config.py`
- Create: `plugins/cc-maestro/ccmaestro/paths.py`
- Test: `plugins/cc-maestro/tests/test_config.py`, `plugins/cc-maestro/tests/test_paths.py`

**Interfaces:**
- Produces: `config.STATE_DIR` (Path), `config.DEFAULTS` (dict), `config.load_config() -> dict`; `paths.transcript_path(session_id) -> Path|None`, `paths.agent_dir(agent_id) -> Path`, `paths.ensure_state_dir()`, `paths.atomic_write(path, text)`.

- [ ] **Step 1: Write failing tests** — create `plugins/cc-maestro/tests/test_config.py`:

```python
import os, sys, json, tempfile, unittest
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["CCMAESTRO_HOME"] = self.tmp
        import importlib, ccmaestro.config as c
        importlib.reload(c)
        self.c = c

    def test_defaults_present(self):
        cfg = self.c.load_config()
        for k in ("stall_min", "tool_stall_min", "loop_n", "loop_window", "token_budget"):
            self.assertIn(k, cfg)
        self.assertEqual(cfg["loop_n"], 4)

    def test_file_overrides_defaults(self):
        (Path(self.tmp) / "config.json").write_text(json.dumps({"loop_n": 9}))
        cfg = self.c.load_config()
        self.assertEqual(cfg["loop_n"], 9)
        self.assertEqual(cfg["stall_min"], 5)  # untouched default

    def test_malformed_config_falls_back(self):
        (Path(self.tmp) / "config.json").write_text("{not json")
        cfg = self.c.load_config()
        self.assertEqual(cfg["loop_n"], 4)

if __name__ == "__main__":
    unittest.main()
```

and `plugins/cc-maestro/tests/test_paths.py`:

```python
import os, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

class TestPaths(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["CCMAESTRO_HOME"] = self.tmp
        self.claude = tempfile.mkdtemp()
        os.environ["CLAUDE_CONFIG_DIR"] = self.claude
        import importlib, ccmaestro.config, ccmaestro.paths
        importlib.reload(ccmaestro.config); importlib.reload(ccmaestro.paths)
        self.p = ccmaestro.paths

    def test_transcript_found_by_session_id(self):
        proj = Path(self.claude) / "projects" / "-Some-Encoded-Cwd"
        proj.mkdir(parents=True)
        sid = "abc-123"
        (proj / f"{sid}.jsonl").write_text("{}")
        found = self.p.transcript_path(sid)
        self.assertIsNotNone(found)
        self.assertEqual(found.name, f"{sid}.jsonl")

    def test_transcript_missing_returns_none(self):
        self.assertIsNone(self.p.transcript_path("does-not-exist"))

    def test_atomic_write_roundtrip(self):
        target = Path(self.tmp) / "x" / "f.txt"
        self.p.atomic_write(target, "hello")
        self.assertEqual(target.read_text(), "hello")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests, verify they fail**

Run: `python3 plugins/cc-maestro/tests/test_config.py -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'ccmaestro'` (package not created yet).

- [ ] **Step 3: Create the package** — `plugins/cc-maestro/ccmaestro/__init__.py` (empty file), then `plugins/cc-maestro/ccmaestro/config.py`:

```python
import json, os
from pathlib import Path

STATE_DIR = Path(os.environ.get("CCMAESTRO_HOME") or (Path.home() / ".ccmaestro"))

DEFAULTS = {
    "stall_min": 5,            # minutes with no new transcript line -> stalled
    "tool_stall_min": 20,      # higher threshold when a tool call is in flight
    "loop_n": 4,               # same (tool, input) repeated this many times -> looping
    "loop_window": 8,          # only consider the last N tool calls
    "token_budget": 0,         # gross tokens over this -> over-budget (0 = disabled)
    "autopilot_stall_min": 30, # autopilot: no new cycle in this many minutes -> stalled
    "report_endpoint": "",     # optional webhook URL (used in Phase 3)
}

def load_config():
    cfg = dict(DEFAULTS)
    f = STATE_DIR / "config.json"
    if f.exists():
        try:
            data = json.loads(f.read_text())
            if isinstance(data, dict):
                cfg.update(data)
        except (json.JSONDecodeError, OSError):
            pass
    return cfg
```

and `plugins/cc-maestro/ccmaestro/paths.py`:

```python
import os
from pathlib import Path
from . import config

def _claude_dir():
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))

def transcript_path(session_id):
    """Locate a session's transcript by sessionId (robust to cwd path encoding)."""
    projects = _claude_dir() / "projects"
    if not projects.exists():
        return None
    matches = sorted(projects.glob(f"*/{session_id}.jsonl"))
    return matches[0] if matches else None

def agent_dir(agent_id):
    return config.STATE_DIR / "agents" / agent_id

def ensure_state_dir():
    (config.STATE_DIR / "agents").mkdir(parents=True, exist_ok=True)

def atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)
```

Note: `config.STATE_DIR` is read at import time, so tests reload the module after setting `$CCMAESTRO_HOME` (they already do).

- [ ] **Step 4: Run both test files, verify they pass**

Run: `python3 plugins/cc-maestro/tests/test_config.py -v && python3 plugins/cc-maestro/tests/test_paths.py -v`
Expected: all tests PASS, output pristine.

- [ ] **Step 5: Commit**

```bash
cd /Users/kubik/nox/misc/claude-code-harness
git add plugins/cc-maestro/ccmaestro plugins/cc-maestro/tests/test_config.py plugins/cc-maestro/tests/test_paths.py
git commit -m "feat(ccmaestro): config + paths (state dir, transcript resolution)"
```

---

### Task 2: Transcript parsing (tokens, activity, tool calls, pending-tool)

**Files:**
- Create: `plugins/cc-maestro/ccmaestro/transcript.py`
- Test: `plugins/cc-maestro/tests/test_transcript.py`

**Interfaces:**
- Consumes: nothing from earlier tasks (pure parser).
- Produces: `transcript.parse_transcript(path) -> dict` with keys: `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, `total_tokens` (ints), `last_activity` (`datetime`|None), `tool_calls` (list of `(name, signature)` tuples in order), `pending_tool` (bool), `assistant_turns` (int). `path=None` or missing file returns the zero-summary.

- [ ] **Step 1: Write failing test** — create `plugins/cc-maestro/tests/test_transcript.py`:

```python
import os, sys, json, tempfile, unittest
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ccmaestro.transcript import parse_transcript

def _line(**kw): return json.dumps(kw)

def _assistant(ts, usage=None, tool=None):
    content = []
    if tool:
        content.append({"type": "tool_use", "id": tool["id"], "name": tool["name"], "input": tool["input"]})
    msg = {"role": "assistant", "content": content}
    if usage: msg["usage"] = usage
    return _line(type="assistant", timestamp=ts, message=msg)

def _tool_result(ts, tool_use_id):
    return _line(type="user", timestamp=ts,
                 message={"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool_use_id, "content": "ok"}]})

class TestTranscript(unittest.TestCase):
    def _write(self, lines):
        fd, p = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
        Path(p).write_text("\n".join(lines) + "\n")
        return p

    def test_missing_file_returns_zero_summary(self):
        s = parse_transcript(None)
        self.assertEqual(s["total_tokens"], 0)
        self.assertIsNone(s["last_activity"])
        self.assertEqual(s["tool_calls"], [])

    def test_sums_usage_across_assistant_turns(self):
        u = {"input_tokens": 10, "output_tokens": 5, "cache_creation_input_tokens": 2, "cache_read_input_tokens": 100}
        p = self._write([_assistant("2026-06-23T10:00:00.000Z", usage=u),
                         _assistant("2026-06-23T10:01:00.000Z", usage=u)])
        s = parse_transcript(p)
        self.assertEqual(s["output_tokens"], 10)
        self.assertEqual(s["total_tokens"], (10+5+2+100)*2)
        self.assertEqual(s["assistant_turns"], 2)

    def test_last_activity_is_latest_timestamp(self):
        p = self._write([_assistant("2026-06-23T10:00:00.000Z", usage={"output_tokens": 1}),
                         _tool_result("2026-06-23T10:05:00.000Z", "t1")])
        s = parse_transcript(p)
        self.assertEqual(s["last_activity"].hour, 10)
        self.assertEqual(s["last_activity"].minute, 5)

    def test_tool_calls_recorded_in_order(self):
        p = self._write([
            _assistant("2026-06-23T10:00:00.000Z", tool={"id": "a", "name": "Bash", "input": {"command": "ls"}}),
            _assistant("2026-06-23T10:00:10.000Z", tool={"id": "b", "name": "Bash", "input": {"command": "ls"}}),
        ])
        s = parse_transcript(p)
        self.assertEqual([n for n, _ in s["tool_calls"]], ["Bash", "Bash"])
        self.assertEqual(s["tool_calls"][0][1], s["tool_calls"][1][1])  # identical signature

    def test_pending_tool_true_when_no_result(self):
        p = self._write([_assistant("2026-06-23T10:00:00.000Z", tool={"id": "x", "name": "Bash", "input": {}})])
        self.assertTrue(parse_transcript(p)["pending_tool"])

    def test_pending_tool_false_when_result_present(self):
        p = self._write([_assistant("2026-06-23T10:00:00.000Z", tool={"id": "x", "name": "Bash", "input": {}}),
                         _tool_result("2026-06-23T10:00:30.000Z", "x")])
        self.assertFalse(parse_transcript(p)["pending_tool"])

    def test_skips_malformed_lines(self):
        p = self._write(["{not json", _assistant("2026-06-23T10:00:00.000Z", usage={"output_tokens": 7})])
        self.assertEqual(parse_transcript(p)["output_tokens"], 7)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run, verify it fails**

Run: `python3 plugins/cc-maestro/tests/test_transcript.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'ccmaestro.transcript'`.

- [ ] **Step 3: Implement** — create `plugins/cc-maestro/ccmaestro/transcript.py`:

```python
import json
from datetime import datetime

_USAGE_KEYS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")

def _parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None

def parse_transcript(path):
    summary = {k: 0 for k in _USAGE_KEYS}
    summary.update({"total_tokens": 0, "last_activity": None,
                    "tool_calls": [], "pending_tool": False, "assistant_turns": 0})
    if not path:
        return summary
    last_ts = None
    last_tool_use_id = None
    seen_result_ids = set()
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = _parse_ts(o.get("timestamp"))
                if ts and (last_ts is None or ts > last_ts):
                    last_ts = ts
                t = o.get("type")
                msg = o.get("message") or {}
                content = msg.get("content") if isinstance(msg, dict) else None
                if t == "assistant":
                    summary["assistant_turns"] += 1
                    usage = msg.get("usage") or {}
                    for k in _USAGE_KEYS:
                        summary[k] += int(usage.get(k) or 0)
                    if isinstance(content, list):
                        for b in content:
                            if isinstance(b, dict) and b.get("type") == "tool_use":
                                sig = json.dumps(b.get("input"), sort_keys=True, default=str)
                                summary["tool_calls"].append((b.get("name"), sig))
                                last_tool_use_id = b.get("id")
                elif t == "user" and isinstance(content, list):
                    for b in content:
                        if isinstance(b, dict) and b.get("type") == "tool_result":
                            rid = b.get("tool_use_id")
                            if rid:
                                seen_result_ids.add(rid)
    except OSError:
        return summary
    summary["total_tokens"] = sum(summary[k] for k in _USAGE_KEYS)
    summary["last_activity"] = last_ts
    summary["pending_tool"] = bool(last_tool_use_id and last_tool_use_id not in seen_result_ids)
    return summary
```

- [ ] **Step 4: Run, verify pass**

Run: `python3 plugins/cc-maestro/tests/test_transcript.py -v`
Expected: all PASS, pristine.

- [ ] **Step 5: Commit**

```bash
cd /Users/kubik/nox/misc/claude-code-harness
git add plugins/cc-maestro/ccmaestro/transcript.py plugins/cc-maestro/tests/test_transcript.py
git commit -m "feat(ccmaestro): transcript parser (tokens, activity, tool calls)"
```

---

### Task 3: Registry (native agents + merge with launch records)

**Files:**
- Create: `plugins/cc-maestro/ccmaestro/registry.py`
- Test: `plugins/cc-maestro/tests/test_registry.py`

**Interfaces:**
- Consumes: `config.STATE_DIR` (Task 1).
- Produces: `registry.native_agents(runner=None) -> list[dict]` (runs `claude agents --json --all`; `runner` is an injectable callable returning the JSON string, for tests); `registry.load_meta_records() -> dict[agent_id, dict]`; `registry.merge(native, meta_records) -> list[dict]` where each entry is `{"sessionId", "native": dict|None, "meta": dict|None, "launched_by_ccmaestro": bool}`.

- [ ] **Step 1: Write failing test** — create `plugins/cc-maestro/tests/test_registry.py`:

```python
import os, sys, json, tempfile, unittest
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["CCMAESTRO_HOME"] = self.tmp
        import importlib, ccmaestro.config, ccmaestro.registry
        importlib.reload(ccmaestro.config); importlib.reload(ccmaestro.registry)
        self.r = ccmaestro.registry

    def test_native_agents_parses_runner_output(self):
        sample = json.dumps([{"sessionId": "s1", "pid": 1, "kind": "interactive", "status": "busy"}])
        agents = self.r.native_agents(runner=lambda: sample)
        self.assertEqual(agents[0]["sessionId"], "s1")

    def test_native_agents_tolerates_failure(self):
        def boom(): raise OSError("claude not found")
        self.assertEqual(self.r.native_agents(runner=boom), [])

    def test_merge_keys_by_session_id(self):
        native = [{"sessionId": "s1", "status": "busy"}]
        meta = {"aid1": {"sessionId": "s1", "task": "fix bug"}}
        merged = {e["sessionId"]: e for e in self.r.merge(native, meta)}
        self.assertTrue(merged["s1"]["launched_by_ccmaestro"])
        self.assertEqual(merged["s1"]["native"]["status"], "busy")
        self.assertEqual(merged["s1"]["meta"]["task"], "fix bug")

    def test_merge_keeps_launched_agent_absent_from_native(self):
        merged = {e["sessionId"]: e for e in self.r.merge([], {"aid": {"sessionId": "gone"}})}
        self.assertIsNone(merged["gone"]["native"])
        self.assertTrue(merged["gone"]["launched_by_ccmaestro"])

    def test_load_meta_records_reads_dirs(self):
        adir = Path(self.tmp) / "agents" / "aid1"
        adir.mkdir(parents=True)
        (adir / "meta.json").write_text(json.dumps({"sessionId": "s9"}))
        recs = self.r.load_meta_records()
        self.assertEqual(recs["aid1"]["sessionId"], "s9")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run, verify it fails**

Run: `python3 plugins/cc-maestro/tests/test_registry.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement** — create `plugins/cc-maestro/ccmaestro/registry.py`:

```python
import json, subprocess
from . import config

def _run_claude_agents():
    return subprocess.run(
        ["claude", "agents", "--json", "--all"],
        capture_output=True, text=True, timeout=30, check=True,
    ).stdout

def native_agents(runner=None):
    runner = runner or _run_claude_agents
    try:
        data = json.loads(runner())
        return data if isinstance(data, list) else []
    except (subprocess.SubprocessError, OSError, ValueError):
        return []

def load_meta_records():
    records = {}
    adir = config.STATE_DIR / "agents"
    if not adir.exists():
        return records
    for d in adir.iterdir():
        f = d / "meta.json"
        if f.exists():
            try:
                records[d.name] = json.loads(f.read_text())
            except (json.JSONDecodeError, OSError):
                pass
    return records

def merge(native, meta_records):
    by_sid = {}
    for a in native:
        sid = a.get("sessionId")
        if sid:
            by_sid[sid] = {"sessionId": sid, "native": a, "meta": None, "launched_by_ccmaestro": False}
    for aid, m in meta_records.items():
        sid = m.get("sessionId") or aid
        entry = by_sid.get(sid)
        if entry:
            entry["meta"] = m
            entry["launched_by_ccmaestro"] = True
        else:
            by_sid[sid] = {"sessionId": sid, "native": None, "meta": m, "launched_by_ccmaestro": True}
    return list(by_sid.values())
```

- [ ] **Step 4: Run, verify pass**

Run: `python3 plugins/cc-maestro/tests/test_registry.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/kubik/nox/misc/claude-code-harness
git add plugins/cc-maestro/ccmaestro/registry.py plugins/cc-maestro/tests/test_registry.py
git commit -m "feat(ccmaestro): agent registry (native list + meta merge)"
```

---

### Task 4: Watchdog (stall / loop / over-budget / died verdicts)

**Files:**
- Create: `plugins/cc-maestro/ccmaestro/watchdog.py`
- Test: `plugins/cc-maestro/tests/test_watchdog.py`

**Interfaces:**
- Consumes: a transcript summary (Task 2 shape), a merged registry entry (Task 3 shape), a config dict (Task 1), and a tz-aware `now`.
- Produces: `watchdog.looping(tool_calls, loop_n, window) -> str|None`; `watchdog.verdict(summary, entry, config, now) -> {"status": str, "reason": str}` where status is one of `ok`, `stalled`, `looping`, `over-budget`, `died`. Precedence: died > looping > over-budget > stalled > ok.

- [ ] **Step 1: Write failing test** — create `plugins/cc-maestro/tests/test_watchdog.py`:

```python
import os, sys, unittest
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ccmaestro import watchdog

NOW = datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc)
CFG = {"stall_min": 5, "tool_stall_min": 20, "loop_n": 4, "loop_window": 8, "token_budget": 1000}

def summary(**kw):
    base = {"total_tokens": 0, "last_activity": NOW, "tool_calls": [], "pending_tool": False}
    base.update(kw); return base

def entry(native=True, launched=False):
    return {"native": {"status": "busy"} if native else None, "launched_by_ccmaestro": launched}

class TestWatchdog(unittest.TestCase):
    def test_healthy_is_ok(self):
        v = watchdog.verdict(summary(), entry(), CFG, NOW)
        self.assertEqual(v["status"], "ok")

    def test_died_when_launched_and_absent_from_native(self):
        v = watchdog.verdict(summary(), entry(native=False, launched=True), CFG, NOW)
        self.assertEqual(v["status"], "died")

    def test_looping_on_repeated_identical_calls(self):
        calls = [("Bash", '{"command":"ls"}')] * 4
        v = watchdog.verdict(summary(tool_calls=calls), entry(), CFG, NOW)
        self.assertEqual(v["status"], "looping")

    def test_not_looping_when_calls_differ(self):
        calls = [("Bash", str(i)) for i in range(6)]
        self.assertIsNone(watchdog.looping(calls, 4, 8))

    def test_over_budget(self):
        v = watchdog.verdict(summary(total_tokens=2000), entry(), CFG, NOW)
        self.assertEqual(v["status"], "over-budget")

    def test_token_budget_zero_disables(self):
        cfg = dict(CFG, token_budget=0)
        v = watchdog.verdict(summary(total_tokens=9_000_000), entry(), cfg, NOW)
        self.assertEqual(v["status"], "ok")

    def test_stalled_when_idle_past_limit(self):
        s = summary(last_activity=NOW - timedelta(minutes=9))
        v = watchdog.verdict(s, entry(), CFG, NOW)
        self.assertEqual(v["status"], "stalled")

    def test_pending_tool_uses_higher_threshold(self):
        s = summary(last_activity=NOW - timedelta(minutes=9), pending_tool=True)
        v = watchdog.verdict(s, entry(), CFG, NOW)  # 9m < tool_stall_min(20) -> not stalled
        self.assertEqual(v["status"], "ok")

    def test_looping_beats_stalled(self):
        s = summary(last_activity=NOW - timedelta(minutes=99), tool_calls=[("Bash", "x")] * 4)
        v = watchdog.verdict(s, entry(), CFG, NOW)
        self.assertEqual(v["status"], "looping")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run, verify it fails**

Run: `python3 plugins/cc-maestro/tests/test_watchdog.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement** — create `plugins/cc-maestro/ccmaestro/watchdog.py`:

```python
def looping(tool_calls, loop_n, window):
    recent = tool_calls[-window:] if window else tool_calls
    if len(recent) < loop_n:
        return None
    last = recent[-1]
    count = 0
    for sig in reversed(recent):
        if sig == last:
            count += 1
        else:
            break
    if count >= loop_n:
        return f"same tool call x{count}: {last[0]}"
    return None

def verdict(summary, entry, config, now):
    if entry.get("launched_by_ccmaestro") and entry.get("native") is None:
        return {"status": "died", "reason": "gone from the agents registry"}
    loop = looping(summary.get("tool_calls", []), config["loop_n"], config["loop_window"])
    if loop:
        return {"status": "looping", "reason": loop}
    budget = config.get("token_budget") or 0
    if budget and summary.get("total_tokens", 0) > budget:
        return {"status": "over-budget", "reason": f"{summary['total_tokens']} tokens > {budget}"}
    la = summary.get("last_activity")
    if la is not None:
        idle_min = (now - la).total_seconds() / 60.0
        limit = config["tool_stall_min"] if summary.get("pending_tool") else config["stall_min"]
        if idle_min > limit:
            kind = "on a tool" if summary.get("pending_tool") else "idle"
            return {"status": "stalled", "reason": f"no activity {idle_min:.0f}m ({kind}, limit {limit}m)"}
    return {"status": "ok", "reason": ""}
```

- [ ] **Step 4: Run, verify pass**

Run: `python3 plugins/cc-maestro/tests/test_watchdog.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/kubik/nox/misc/claude-code-harness
git add plugins/cc-maestro/ccmaestro/watchdog.py plugins/cc-maestro/tests/test_watchdog.py
git commit -m "feat(ccmaestro): watchdog verdicts (stall/loop/over-budget/died)"
```

---

### Task 5: Autopilot awareness

**Files:**
- Create: `plugins/cc-maestro/ccmaestro/autopilot.py`
- Test: `plugins/cc-maestro/tests/test_autopilot.py`

**Interfaces:**
- Consumes: a cwd path (from a registry entry's `native["cwd"]` or `meta["repo"]`).
- Produces: `autopilot.is_autopilot(cwd) -> bool` (true when `<cwd>/.claude/ccharness/autopilot/state.json` exists with `active == true`); `autopilot.cycle_count(cwd) -> int|None` (lines in `<cwd>/.claude/ccharness/autopilot/log.jsonl`, or None if absent). Note the runtime state dir is intentionally still `.claude/ccharness/` after the rename.

- [ ] **Step 1: Write failing test** — create `plugins/cc-maestro/tests/test_autopilot.py`:

```python
import os, sys, json, tempfile, unittest
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ccmaestro import autopilot

class TestAutopilot(unittest.TestCase):
    def _repo(self, active=None, cycles=None):
        repo = tempfile.mkdtemp()
        ap = Path(repo) / ".claude" / "ccharness" / "autopilot"
        if active is not None:
            ap.mkdir(parents=True, exist_ok=True)
            (ap / "state.json").write_text(json.dumps({"active": active, "cycle": 3}))
        if cycles is not None:
            ap.mkdir(parents=True, exist_ok=True)
            (ap / "log.jsonl").write_text("\n".join("{}" for _ in range(cycles)) + "\n")
        return repo

    def test_active_autopilot_detected(self):
        self.assertTrue(autopilot.is_autopilot(self._repo(active=True)))

    def test_inactive_not_autopilot(self):
        self.assertFalse(autopilot.is_autopilot(self._repo(active=False)))

    def test_plain_repo_not_autopilot(self):
        self.assertFalse(autopilot.is_autopilot(tempfile.mkdtemp()))

    def test_none_cwd_safe(self):
        self.assertFalse(autopilot.is_autopilot(None))

    def test_cycle_count(self):
        self.assertEqual(autopilot.cycle_count(self._repo(active=True, cycles=5)), 5)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run, verify it fails**

Run: `python3 plugins/cc-maestro/tests/test_autopilot.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement** — create `plugins/cc-maestro/ccmaestro/autopilot.py`:

```python
import json
from pathlib import Path

def _state_dir(cwd):
    return Path(cwd) / ".claude" / "ccharness" / "autopilot"

def is_autopilot(cwd):
    if not cwd:
        return False
    f = _state_dir(cwd) / "state.json"
    if not f.exists():
        return False
    try:
        return bool(json.loads(f.read_text()).get("active"))
    except (json.JSONDecodeError, OSError):
        return False

def cycle_count(cwd):
    if not cwd:
        return None
    f = _state_dir(cwd) / "log.jsonl"
    if not f.exists():
        return None
    try:
        return sum(1 for line in f.read_text().splitlines() if line.strip())
    except OSError:
        return None
```

- [ ] **Step 4: Run, verify pass**

Run: `python3 plugins/cc-maestro/tests/test_autopilot.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/kubik/nox/misc/claude-code-harness
git add plugins/cc-maestro/ccmaestro/autopilot.py plugins/cc-maestro/tests/test_autopilot.py
git commit -m "feat(ccmaestro): autopilot detection (active state + cycle count)"
```

---

### Task 6: Render rows + `ccmaestro ls` (the dashboard)

**Files:**
- Create: `plugins/cc-maestro/ccmaestro/render.py`
- Create: `plugins/cc-maestro/ccmaestro/cli.py`
- Create: `plugins/cc-maestro/bin/ccmaestro`
- Test: `plugins/cc-maestro/tests/test_render.py`

**Interfaces:**
- Consumes: registry merge (Task 3), transcript summary (Task 2), watchdog verdict (Task 4), autopilot (Task 5).
- Produces: `render.build_rows(entries, now, *, summarizer, config) -> list[dict]` (pure; `summarizer(session_id) -> summary` is injected so tests need no files) where each row has `id, sessionId, kind, status, tokens, last_activity, verdict, reason, cwd, name, autopilot`; `render.render_json(rows) -> str`; `render.render_table(rows) -> str`. `cli.main(argv=None) -> int` implementing `ccmaestro ls [--json]`. `bin/ccmaestro` is the executable entry.

- [ ] **Step 1: Write failing test** — create `plugins/cc-maestro/tests/test_render.py`:

```python
import os, sys, json, unittest
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ccmaestro import render

NOW = datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc)
CFG = {"stall_min": 5, "tool_stall_min": 20, "loop_n": 4, "loop_window": 8, "token_budget": 0}

def make_entry(sid, status="busy", cwd="/tmp/x"):
    return {"sessionId": sid, "launched_by_ccmaestro": False,
            "native": {"sessionId": sid, "status": status, "kind": "interactive", "cwd": cwd, "name": "n"},
            "meta": None}

class TestRender(unittest.TestCase):
    def test_build_rows_includes_tokens_and_verdict(self):
        def summarizer(sid):
            return {"total_tokens": 4200, "last_activity": NOW, "tool_calls": [], "pending_tool": False}
        rows = render.build_rows([make_entry("s1")], NOW, summarizer=summarizer, config=CFG)
        self.assertEqual(rows[0]["tokens"], 4200)
        self.assertEqual(rows[0]["verdict"], "ok")
        self.assertEqual(rows[0]["sessionId"], "s1")

    def test_build_rows_flags_stalled(self):
        def summarizer(sid):
            return {"total_tokens": 1, "last_activity": NOW - timedelta(minutes=30), "tool_calls": [], "pending_tool": False}
        rows = render.build_rows([make_entry("s1")], NOW, summarizer=summarizer, config=CFG)
        self.assertEqual(rows[0]["verdict"], "stalled")

    def test_render_json_is_valid(self):
        rows = [{"id": "a", "verdict": "ok", "tokens": 1}]
        self.assertEqual(json.loads(render.render_json(rows))[0]["verdict"], "ok")

    def test_render_table_has_headers(self):
        out = render.render_table([{"id": "a", "sessionId": "s1", "kind": "task", "tokens": 5,
                                    "last_activity": NOW, "verdict": "ok", "reason": "", "cwd": "/x",
                                    "name": "n", "autopilot": False}])
        self.assertIn("VERDICT", out)
        self.assertIn("TOKENS", out)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run, verify it fails**

Run: `python3 plugins/cc-maestro/tests/test_render.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement render** — create `plugins/cc-maestro/ccmaestro/render.py`:

```python
import json
from . import watchdog, autopilot as ap

def _humanize_age(last, now):
    if last is None:
        return "-"
    secs = (now - last).total_seconds()
    if secs < 90:
        return f"{int(secs)}s"
    if secs < 5400:
        return f"{int(secs // 60)}m"
    return f"{int(secs // 3600)}h"

def _fmt_tokens(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n//1000}k"
    return str(n)

def build_rows(entries, now, *, summarizer, config):
    rows = []
    for e in entries:
        native = e.get("native") or {}
        meta = e.get("meta") or {}
        sid = e.get("sessionId")
        cwd = native.get("cwd") or meta.get("repo")
        summary = summarizer(sid)
        is_ap = ap.is_autopilot(cwd)
        v = watchdog.verdict(summary, e, config, now)
        rows.append({
            "id": (sid or "")[:8],
            "sessionId": sid,
            "kind": "autopilot" if is_ap else (meta.get("kind") or native.get("kind") or "?"),
            "status": native.get("status") or native.get("state") or ("gone" if native == {} else "?"),
            "tokens": summary.get("total_tokens", 0),
            "last_activity": summary.get("last_activity"),
            "verdict": v["status"],
            "reason": v["reason"],
            "cwd": cwd,
            "name": meta.get("task") or native.get("name") or "",
            "autopilot": is_ap,
        })
    return rows

def render_json(rows):
    def default(o):
        return o.isoformat() if hasattr(o, "isoformat") else str(o)
    return json.dumps(rows, default=default, indent=2)

def render_table(rows):
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    header = f"{'ID':8} {'KIND':10} {'STATUS':7} {'TOKENS':>7} {'LAST':>5}  {'VERDICT':10} NAME"
    lines = [header]
    for r in rows:
        lines.append("{id:8} {kind:10} {status:7} {tok:>7} {age:>5}  {verdict:10} {name}".format(
            id=r["id"], kind=str(r["kind"])[:10], status=str(r["status"])[:7],
            tok=_fmt_tokens(r["tokens"]), age=_humanize_age(r["last_activity"], now),
            verdict=r["verdict"], name=(r["name"] or "")[:40]))
        if r["verdict"] != "ok" and r["reason"]:
            lines.append(f"{'':8} └─ {r['reason']}")
    return "\n".join(lines)
```

- [ ] **Step 4: Implement cli + entry point** — create `plugins/cc-maestro/ccmaestro/cli.py`:

```python
import argparse, sys
from datetime import datetime, timezone
from . import config, registry, transcript, paths, render

def _ls(args):
    cfg = config.load_config()
    now = datetime.now(timezone.utc)
    entries = registry.merge(registry.native_agents(), registry.load_meta_records())
    summarizer = lambda sid: transcript.parse_transcript(paths.transcript_path(sid)) if sid else transcript.parse_transcript(None)
    rows = render.build_rows(entries, now, summarizer=summarizer, config=cfg)
    rows.sort(key=lambda r: (r["verdict"] == "ok", r["id"]))  # problems first
    print(render.render_json(rows) if args.json else render.render_table(rows))
    return 0

def build_parser():
    p = argparse.ArgumentParser(prog="ccmaestro", description="Watch and control Claude Code agents.")
    sub = p.add_subparsers(dest="cmd")
    ls = sub.add_parser("ls", help="list all agents with tokens + watchdog verdict")
    ls.add_argument("--json", action="store_true", help="machine-readable output")
    ls.set_defaults(func=_ls)
    return p

def main(argv=None):
    args = build_parser().parse_args(argv)
    if not getattr(args, "func", None):
        build_parser().print_help()
        return 2
    return args.func(args)
```

then create `plugins/cc-maestro/bin/ccmaestro`:

```python
#!/usr/bin/env python3
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
from ccmaestro.cli import main
sys.exit(main())
```

and make it executable:

```bash
chmod +x plugins/cc-maestro/bin/ccmaestro
```

- [ ] **Step 5: Run the unit test + a real smoke test**

Run: `python3 plugins/cc-maestro/tests/test_render.py -v`
Expected: all PASS.

Run (real, against this machine's live agents): `plugins/cc-maestro/bin/ccmaestro ls`
Expected: a table with at least this session listed, a TOKENS column with non-zero numbers, and a VERDICT column. Then `plugins/cc-maestro/bin/ccmaestro ls --json` prints valid JSON (pipe to `python3 -m json.tool` to confirm).

- [ ] **Step 6: Commit**

```bash
cd /Users/kubik/nox/misc/claude-code-harness
git add plugins/cc-maestro/ccmaestro/render.py plugins/cc-maestro/ccmaestro/cli.py plugins/cc-maestro/bin/ccmaestro plugins/cc-maestro/tests/test_render.py
git commit -m "feat(ccmaestro): ls dashboard (rows, table + json render, CLI entry)"
```

---

### Task 7: `ccmaestro start` (launcher) + `ccmaestro logs` + slash command + README

**Files:**
- Create: `plugins/cc-maestro/ccmaestro/launcher.py`
- Modify: `plugins/cc-maestro/ccmaestro/cli.py` (add `start` and `logs` subcommands)
- Create: `plugins/cc-maestro/commands/maestro.md`
- Modify: `plugins/cc-maestro/README.md` (replace the stub)
- Test: `plugins/cc-maestro/tests/test_launcher.py`

**Interfaces:**
- Consumes: `paths` (Task 1), `transcript` (Task 2).
- Produces: `launcher.build_launch_argv(session_id, task, *, model=None, budget=None, yolo=False) -> list[str]` (pure; the exact `claude` argv); `launcher.start(task, *, repo=None, model=None, budget=None, name=None, yolo=False) -> str` (spawns the agent detached, writes `meta.json`, returns the agent id = first 8 chars of a generated session id). CLI gains `ccmaestro start "<task>" [--repo P --model M --budget USD --name N --yolo]` and `ccmaestro logs <id> [--tail N]`.

- [ ] **Step 1: Write failing test** — create `plugins/cc-maestro/tests/test_launcher.py`:

```python
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ccmaestro import launcher

class TestLauncher(unittest.TestCase):
    def test_argv_core_flags(self):
        argv = launcher.build_launch_argv("sid-1", "do the thing")
        self.assertEqual(argv[0], "claude")
        self.assertIn("-p", argv)
        self.assertIn("do the thing", argv)
        self.assertIn("--session-id", argv)
        self.assertIn("sid-1", argv)
        self.assertIn("--output-format", argv)
        self.assertIn("stream-json", argv)
        # default safe posture, NOT bypass
        self.assertIn("--permission-mode", argv)
        self.assertIn("acceptEdits", argv)
        self.assertNotIn("bypassPermissions", argv)

    def test_argv_yolo_uses_bypass(self):
        argv = launcher.build_launch_argv("sid-1", "x", yolo=True)
        self.assertIn("bypassPermissions", argv)
        self.assertNotIn("acceptEdits", argv)

    def test_argv_optional_flags(self):
        argv = launcher.build_launch_argv("sid-1", "x", model="opus", budget=5.0)
        self.assertIn("--model", argv); self.assertIn("opus", argv)
        self.assertIn("--max-budget-usd", argv); self.assertIn("5.0", argv)

    def test_argv_omits_unset_optionals(self):
        argv = launcher.build_launch_argv("sid-1", "x")
        self.assertNotIn("--model", argv)
        self.assertNotIn("--max-budget-usd", argv)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run, verify it fails**

Run: `python3 plugins/cc-maestro/tests/test_launcher.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement launcher** — create `plugins/cc-maestro/ccmaestro/launcher.py`:

```python
import json, os, subprocess, uuid
from datetime import datetime, timezone
from . import paths

# Curated safe Bash subset for unattended-but-restricted runs (acceptEdits handles file edits).
DEFAULT_ALLOWED_TOOLS = "Read,Edit,Write,Glob,Grep,Bash(git status),Bash(git diff:*),Bash(git log:*),Bash(ls:*),Bash(cat:*)"

def build_launch_argv(session_id, task, *, model=None, budget=None, yolo=False):
    argv = ["claude", "-p", task,
            "--session-id", session_id,
            "--output-format", "stream-json", "--include-partial-messages", "--verbose"]
    if yolo:
        argv += ["--permission-mode", "bypassPermissions"]
    else:
        argv += ["--permission-mode", "acceptEdits", "--allowedTools", DEFAULT_ALLOWED_TOOLS]
    if model:
        argv += ["--model", model]
    if budget is not None:
        argv += ["--max-budget-usd", str(budget)]
    return argv

def start(task, *, repo=None, model=None, budget=None, name=None, yolo=False):
    paths.ensure_state_dir()
    session_id = str(uuid.uuid4())
    agent_id = session_id[:8]
    cwd = repo or os.getcwd()
    argv = build_launch_argv(session_id, task, model=model, budget=budget, yolo=yolo)
    adir = paths.agent_dir(agent_id)
    adir.mkdir(parents=True, exist_ok=True)
    meta = {"agent_id": agent_id, "sessionId": session_id, "task": name or task, "repo": cwd,
            "model": model, "budget": budget, "yolo": yolo, "kind": "task",
            "started_at": datetime.now(timezone.utc).isoformat()}
    paths.atomic_write(adir / "meta.json", json.dumps(meta, indent=2))
    log = open(adir / "stream.log", "w")
    subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                     start_new_session=True)
    return agent_id
```

- [ ] **Step 4: Wire `start` and `logs` into the CLI** — in `plugins/cc-maestro/ccmaestro/cli.py`, add these handlers and register them in `build_parser()` (add the imports `from . import launcher` and `from .registry import load_meta_records`):

```python
def _start(args):
    from . import launcher
    agent_id = launcher.start(args.task, repo=args.repo, model=args.model,
                              budget=args.budget, name=args.name, yolo=args.yolo)
    print(agent_id)
    return 0

def _logs(args):
    from . import paths, registry
    meta = registry.load_meta_records().get(args.id)
    sid = meta.get("sessionId") if meta else args.id
    tp = paths.transcript_path(sid)
    if not tp:
        print(f"no transcript found for {args.id}", file=sys.stderr)
        return 1
    lines = tp.read_text().splitlines()
    for line in lines[-args.tail:]:
        print(line)
    return 0
```

and in `build_parser()` add, before `return p`:

```python
    st = sub.add_parser("start", help="launch a new managed agent")
    st.add_argument("task")
    st.add_argument("--repo"); st.add_argument("--model"); st.add_argument("--name")
    st.add_argument("--budget", type=float)
    st.add_argument("--yolo", action="store_true", help="bypass ALL permissions (unattended, dangerous)")
    st.set_defaults(func=_start)
    lg = sub.add_parser("logs", help="print an agent's recent transcript lines")
    lg.add_argument("id")
    lg.add_argument("--tail", type=int, default=40)
    lg.set_defaults(func=_logs)
```

- [ ] **Step 5: Create the slash command** — `plugins/cc-maestro/commands/maestro.md`:

```markdown
---
description: "Show the agent fleet — every Claude Code agent on this machine with its token burn, last activity, and a watchdog verdict (ok / stalled / looping / over-budget / died). Runs the ccmaestro console."
argument-hint: "(no arguments)"
---

# /maestro — the agent console

Run the ccmaestro dashboard and report the result.

Run this command and show the user its output verbatim:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/ccmaestro" ls
```

If the user asks for machine-readable output, run it with `--json`. Do not paraphrase
the table — the columns (tokens, verdict) are the point.
```

- [ ] **Step 6: Replace the README** — overwrite `plugins/cc-maestro/README.md`:

```markdown
# cc-maestro

The conductor of the cc-* harness. The `ccmaestro` CLI watches and controls many
coding agents and autopilots at once.

## Use it

```bash
plugins/cc-maestro/bin/ccmaestro ls            # the dashboard: tokens, last activity, watchdog verdict
plugins/cc-maestro/bin/ccmaestro ls --json     # machine-readable (for an external agent like hermes)
plugins/cc-maestro/bin/ccmaestro start "fix the flaky test" --repo ~/app
plugins/cc-maestro/bin/ccmaestro logs <id> --tail 50
```

Symlink `bin/ccmaestro` onto your PATH to type `ccmaestro` directly. Inside a Claude
Code session, `/maestro` runs the dashboard.

## How it works

- The agent list comes from the native `claude agents --json --all`.
- Per-agent tokens + activity come from each session's transcript under
  `~/.claude/projects/.../<sessionId>.jsonl` (resolved by sessionId).
- The **watchdog** derives verdicts the native status doesn't give: `stalled`
  (no activity past a threshold), `looping` (same tool call repeated),
  `over-budget` (tokens over a cap), `died` (a launched agent gone from the registry).
- `ccmaestro` keeps its own launch records under `~/.ccmaestro/agents/<id>/` and
  merges them with the native list by sessionId. Config: `~/.ccmaestro/config.json`.

## Status

Observe + launch (Phase 2) are built. Control (stop / steer / pause) and reporting
to an external agent are the next plan. See
`docs/superpowers/specs/2026-06-23-cc-maestro-design.md`.
```

- [ ] **Step 7: Run unit tests + real smoke tests**

Run: `python3 plugins/cc-maestro/tests/test_launcher.py -v`
Expected: all PASS.

Real smoke (launches a tiny throwaway agent, then observes it):
```bash
cd /Users/kubik/nox/misc/claude-code-harness
ID=$(plugins/cc-maestro/bin/ccmaestro start "Print the numbers 1 to 5, then stop." --repo "$PWD" --budget 1)
echo "launched $ID"
sleep 8
plugins/cc-maestro/bin/ccmaestro ls | grep -i "$ID" || plugins/cc-maestro/bin/ccmaestro ls
plugins/cc-maestro/bin/ccmaestro logs "$ID" --tail 5
```
Expected: a launched id; the agent appears in `ls` with accruing tokens; `logs` prints transcript lines.

- [ ] **Step 8: Run the FULL test suite once**

Run:
```bash
cd /Users/kubik/nox/misc/claude-code-harness
for t in plugins/cc-maestro/tests/test_*.py; do python3 "$t" || exit 1; done; echo ALL_GREEN
```
Expected: `ALL_GREEN`, output pristine.

- [ ] **Step 9: Commit**

```bash
cd /Users/kubik/nox/misc/claude-code-harness
git add plugins/cc-maestro
git commit -m "feat(ccmaestro): start launcher + logs + /maestro command + README"
```

---

## Self-Review

**Spec coverage (§3 cc-maestro design):**
- §3.1a registry view `ls [--json]` → Task 6. ✓
- §3.1b launcher with permission posture + `--yolo` → Task 7 (build_launch_argv defaults acceptEdits+allowlist; yolo→bypass). ✓
- §3.1c watchdog (stalled/looping/died/over-budget, pending-tool refinement) → Task 4. ✓
- §3.1f logs → Task 7. ✓
- §3.3 autopilot awareness (detect via `.claude/ccharness/autopilot/state.json`, cycle count) → Task 5, surfaced in rows (Task 6). ✓
- §3.4 state files (meta.json, atomic writes, ~/.ccmaestro/) → Tasks 1, 7. ✓
- Token source = transcript usage; transcript resolved by sessionId glob → Tasks 1, 2. ✓
- NOT in this plan (correctly deferred to Phase 3): stop/steer/pause/resume, push reporting + proactive launchd alert, the `--remote-control` spike, fleet-wide concurrency/spend cap. Stated in Architecture + README.

**Placeholder scan:** none — every step has complete code or exact commands. The allowlist string in launcher.py is a concrete starter set (spec open question 7a.4); tune later via config if needed.

**Type/name consistency:** summary dict keys (`total_tokens`, `last_activity`, `tool_calls`, `pending_tool`) are identical across transcript.py (producer), watchdog.py and render.py (consumers), and every test. Registry entry shape (`sessionId`/`native`/`meta`/`launched_by_ccmaestro`) is identical across registry.py, watchdog.py, render.py. `build_launch_argv` / `start` signatures match their tests.

**Risk note:** Task 6/7 smoke tests spawn real `claude -p` agents (small token cost). The watchdog thresholds default conservatively (stall 5m, loop 4) and are config-tunable; defaults may need tuning against real runs — acceptable for v1, surfaced in README/config.
