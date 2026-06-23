# ccmaestro — Control Layer (Phase 3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give `ccmaestro` the ability to *act on* agents, not just watch them: stop, steer (redirect), pause/resume, distinguish a clean finish from a crash, proactively report state changes to an external agent (hermes), and refuse to launch past a fleet-wide concurrency cap.

**Architecture:** Extends the Phase 2 observe layer (already on `main` under `plugins/cc-maestro/`). Control acts through OS signals to an agent's process group (the launcher makes each agent a session/group leader) and through `claude --resume`. Autopilot agents are stopped the same way their own `/autopilot-cancel` does — by removing their state file, not by killing the process. Reporting is pull-first (`ccmaestro check`) with an optional push (a Stop/Notification hook that POSTs to a configured endpoint). No daemon.

**Tech Stack:** Python 3.9+ (stdlib only: adds `signal`, `shlex`, `urllib.request`, `time` to the Phase 2 set). One bash reporting hook. No third-party dependencies.

## Global Constraints

- **Python 3.9, standard library only.** Reporting POSTs use `urllib.request`, never `requests`.
- **Build on the EXISTING Phase 2 modules** in `plugins/cc-maestro/ccmaestro/` — reuse `config`, `paths`, `registry`, `transcript`, `watchdog`, `render`, `launcher`, `autopilot`. Match their existing signatures (read the files first).
- **Signals target the process GROUP.** The launcher spawns with `start_new_session=True`, so each agent's wrapper is a group leader; stop/pause use `os.killpg(pid, sig)` to hit `claude` and its wrapper together. The pid to use is the one `ccmaestro` recorded at launch (`meta["pid"]`), not the native registry pid.
- **Autopilot stop = remove `<cwd>/.claude/ccharness/autopilot/state.json`** (the same graceful mechanism as `/autopilot-cancel`; the Stop hook then lets the loop end). Never SIGKILL an autopilot as the primary path.
- **Steer = stop-then-resume**, never resume-alongside (two processes on one transcript corrupts it): stop the running agent, then `claude --resume <sid> -p "<msg>"`.
- **Permission posture** on resume mirrors launch: default `acceptEdits` + allowlist, `--yolo` → `bypassPermissions`.
- **Atomic writes** for everything `ccmaestro` writes (`paths.atomic_write`): `meta.json`, `events.jsonl` (append via read-modify-write or O_APPEND), `last_snapshot.json`.
- **Test convention** (same as Phase 2): each test file self-bootstraps `sys.path` and runs directly: `python3 plugins/cc-maestro/tests/test_<x>.py -v`. Inject side-effecting callables (signal sender, HTTP poster, subprocess spawner) so tests never signal real processes or make real network calls.
- Spec: `docs/superpowers/specs/2026-06-23-cc-maestro-design.md` (§3.1d reporting, §3.1e intervention, §3.3 autopilot stop, §7a.5 fleet ceilings).

## File Structure (deltas to Phase 2)

```
plugins/cc-maestro/ccmaestro/
  control.py      # NEW: resolve(ident), send_signal(), stop_agent(), pause/resume helpers
  report.py       # NEW: snapshot/diff/record events, post_event()
  launcher.py     # EDIT: record pid in meta; completion wrapper; build_resume_argv()
  watchdog.py     # EDIT: done/crashed verdicts from result.json exit code
  render.py       # EDIT: read result.json -> completed_exit into entry; show done/crashed
  cli.py          # EDIT: add stop/steer/pause/resume/check subcommands
  config.py       # EDIT: add max_concurrent default
  hooks/report-hook.sh   # NEW: Stop/SubagentStop/Notification -> POST endpoint
  hooks/hooks.json       # NEW: register the report hook
  tests/test_control.py test_report.py  # NEW
  (edits to tests/test_launcher.py, test_watchdog.py)
```

---

### Task 1: `control.py` — agent resolution + process-group signals

**Files:**
- Create: `plugins/cc-maestro/ccmaestro/control.py`
- Test: `plugins/cc-maestro/tests/test_control.py`

**Interfaces:**
- Consumes: `registry.merge/native_agents/load_meta_records`, `autopilot.is_autopilot`.
- Produces: `control.resolve(ident, *, native_runner=None) -> dict|None` (find an agent by full sessionId, by 8-char id, or by sessionId prefix; returns `{agent_id, sessionId, pid, cwd, is_autopilot, native, meta, launched_by_ccmaestro}`, preferring `meta["pid"]` then native pid); `control.send_signal(pid, sig, sender=os.killpg) -> bool` (tolerant: returns False on missing pid / dead process / bad value).

- [ ] **Step 1: Write failing test** — create `plugins/cc-maestro/tests/test_control.py`:

```python
import os, sys, json, tempfile, signal, unittest
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

class TestControl(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["CCMAESTRO_HOME"] = self.tmp
        self.claude = tempfile.mkdtemp()
        os.environ["CLAUDE_CONFIG_DIR"] = self.claude
        import importlib, ccmaestro.config, ccmaestro.paths, ccmaestro.registry, ccmaestro.control
        for m in (ccmaestro.config, ccmaestro.paths, ccmaestro.registry, ccmaestro.control):
            importlib.reload(m)
        self.control = ccmaestro.control

    def _native(self, agents):
        return lambda: json.dumps(agents)

    def test_resolve_by_full_session_id(self):
        run = self._native([{"sessionId": "sid-full-123", "pid": 42, "cwd": "/x", "kind": "interactive"}])
        info = self.control.resolve("sid-full-123", native_runner=run)
        self.assertEqual(info["pid"], 42)
        self.assertEqual(info["cwd"], "/x")

    def test_resolve_by_prefix(self):
        run = self._native([{"sessionId": "abcdef1234", "pid": 7, "cwd": "/y", "kind": "interactive"}])
        info = self.control.resolve("abcdef12", native_runner=run)
        self.assertIsNotNone(info)
        self.assertEqual(info["pid"], 7)

    def test_resolve_prefers_meta_pid(self):
        adir = Path(self.tmp) / "agents" / "aid1"; adir.mkdir(parents=True)
        (adir / "meta.json").write_text(json.dumps({"agent_id": "aid1", "sessionId": "s-meta", "pid": 999, "repo": "/r"}))
        run = self._native([{"sessionId": "s-meta", "pid": 1, "cwd": "/r", "kind": "interactive"}])
        info = self.control.resolve("aid1", native_runner=run)
        self.assertEqual(info["pid"], 999)  # meta pid wins
        self.assertTrue(info["launched_by_ccmaestro"])

    def test_resolve_unknown_returns_none(self):
        self.assertIsNone(self.control.resolve("nope", native_runner=self._native([])))

    def test_send_signal_calls_sender(self):
        calls = []
        ok = self.control.send_signal(123, signal.SIGTERM, sender=lambda p, s: calls.append((p, s)))
        self.assertTrue(ok)
        self.assertEqual(calls, [(123, signal.SIGTERM)])

    def test_send_signal_none_pid_false(self):
        self.assertFalse(self.control.send_signal(None, signal.SIGTERM, sender=lambda p, s: None))

    def test_send_signal_dead_process_false(self):
        def boom(p, s): raise ProcessLookupError()
        self.assertFalse(self.control.send_signal(5, signal.SIGTERM, sender=boom))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run, verify it fails**

Run: `python3 plugins/cc-maestro/tests/test_control.py -v`
Expected: FAIL — `No module named 'ccmaestro.control'`.

- [ ] **Step 3: Implement** — create `plugins/cc-maestro/ccmaestro/control.py`:

```python
import os
from . import registry, autopilot as ap

def resolve(ident, *, native_runner=None):
    entries = registry.merge(registry.native_agents(runner=native_runner), registry.load_meta_records())
    for e in entries:
        sid = e.get("sessionId") or ""
        meta = e.get("meta") or {}
        native = e.get("native") or {}
        aid = meta.get("agent_id") or (sid[:8] if sid else None)
        if ident == sid or (aid and ident == aid) or (sid and sid.startswith(ident)):
            cwd = native.get("cwd") or meta.get("repo")
            pid = meta.get("pid") or native.get("pid")
            return {
                "agent_id": aid, "sessionId": sid or None, "pid": pid, "cwd": cwd,
                "is_autopilot": ap.is_autopilot(cwd),
                "native": e.get("native"), "meta": meta or None,
                "launched_by_ccmaestro": e.get("launched_by_ccmaestro", False),
            }
    return None

def send_signal(pid, sig, sender=os.killpg):
    if not pid:
        return False
    try:
        sender(int(pid), sig)
        return True
    except (ProcessLookupError, PermissionError, OSError, ValueError):
        return False
```

- [ ] **Step 4: Run, verify pass**

Run: `python3 plugins/cc-maestro/tests/test_control.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/kubik/nox/misc/claude-code-harness
git add plugins/cc-maestro/ccmaestro/control.py plugins/cc-maestro/tests/test_control.py
git commit -m "feat(ccmaestro): control resolve() + process-group send_signal()"
```

---

### Task 2: Completion marker — record pid + exit code; watchdog `done`/`crashed`

**Files:**
- Modify: `plugins/cc-maestro/ccmaestro/launcher.py`
- Modify: `plugins/cc-maestro/ccmaestro/watchdog.py`
- Modify: `plugins/cc-maestro/ccmaestro/render.py`
- Modify: `plugins/cc-maestro/tests/test_launcher.py`, `plugins/cc-maestro/tests/test_watchdog.py`

**Interfaces:**
- Produces: `launcher.build_spawn_command(argv, result_path) -> list[str]` (pure; returns `["sh","-c", "<claude...>; printf ... $? > result.json"]`). `start()` now spawns via that wrapper and records `meta["pid"]` (the wrapper's pid). `watchdog.verdict` gains: when a ccmaestro-launched agent is gone from native, use `entry.get("completed_exit")` — `0` → `done`, non-None non-zero → `crashed`, `None` → `died`. `render.build_rows` reads `~/.ccmaestro/agents/<id>/result.json` and sets `entry["completed_exit"]`.

- [ ] **Step 1: Write failing tests** — add to `plugins/cc-maestro/tests/test_launcher.py`:

```python
    def test_build_spawn_command_wraps_and_records_exit(self):
        from ccmaestro import launcher
        argv = launcher.build_launch_argv("sid-1", "do x")
        cmd = launcher.build_spawn_command(argv, "/tmp/agents/aid/result.json")
        self.assertEqual(cmd[0], "sh")
        self.assertEqual(cmd[1], "-c")
        self.assertIn("claude", cmd[2])
        self.assertIn("do x", cmd[2])           # task is shell-quoted into the command
        self.assertIn("result.json", cmd[2])    # exit code captured to result file
        self.assertIn("$?", cmd[2])

    def test_build_resume_argv(self):
        from ccmaestro import launcher
        argv = launcher.build_resume_argv("sid-9", "now do y")
        self.assertIn("--resume", argv); self.assertIn("sid-9", argv)
        self.assertIn("-p", argv); self.assertIn("now do y", argv)
        self.assertIn("acceptEdits", argv)
        self.assertNotIn("--session-id", argv)  # resume reuses the existing session
```

and add to `plugins/cc-maestro/tests/test_watchdog.py`:

```python
    def test_completed_exit_zero_is_done(self):
        e = {"native": None, "launched_by_ccmaestro": True, "completed_exit": 0}
        self.assertEqual(watchdog.verdict(summary(), e, CFG, NOW)["status"], "done")

    def test_completed_exit_nonzero_is_crashed(self):
        e = {"native": None, "launched_by_ccmaestro": True, "completed_exit": 2}
        self.assertEqual(watchdog.verdict(summary(), e, CFG, NOW)["status"], "crashed")

    def test_gone_without_result_is_died(self):
        e = {"native": None, "launched_by_ccmaestro": True, "completed_exit": None}
        self.assertEqual(watchdog.verdict(summary(), e, CFG, NOW)["status"], "died")
```

- [ ] **Step 2: Run, verify the new tests fail**

Run: `python3 plugins/cc-maestro/tests/test_launcher.py -v ; python3 plugins/cc-maestro/tests/test_watchdog.py -v`
Expected: the new tests FAIL (`build_spawn_command`/`build_resume_argv` missing; verdict returns "died" not "done"/"crashed").

- [ ] **Step 3: Implement launcher changes** — in `plugins/cc-maestro/ccmaestro/launcher.py`, add `import shlex` at top, add these functions, and rewrite the spawn in `start()`:

```python
def build_spawn_command(argv, result_path):
    inner = shlex.join(argv)
    rp = shlex.quote(str(result_path))
    return ["sh", "-c", f'{inner}; ec=$?; printf \'{{"exit": %s}}\' "$ec" > {rp}']

def build_resume_argv(session_id, message, *, model=None, budget=None, yolo=False):
    argv = ["claude", "--resume", session_id, "-p", message,
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
```

Then change the spawn block in `start()` (currently opens stream.log, calls Popen on `argv`, closes log, returns agent_id) to spawn via the wrapper and record the pid:

```python
    result_path = adir / "result.json"
    log = open(adir / "stream.log", "w")
    proc = subprocess.Popen(build_spawn_command(argv, result_path), cwd=cwd,
                            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True)
    log.close()
    meta["pid"] = proc.pid
    paths.atomic_write(adir / "meta.json", json.dumps(meta, indent=2))
    return agent_id
```

(The first `meta.json` write earlier in `start()` stays; this re-writes it with the pid now known. Both writes are atomic.)

- [ ] **Step 4: Implement watchdog change** — in `plugins/cc-maestro/ccmaestro/watchdog.py`, replace the `died` branch at the top of `verdict()`:

```python
    if entry.get("launched_by_ccmaestro") and entry.get("native") is None:
        ec = entry.get("completed_exit")
        if ec == 0:
            return {"status": "done", "reason": "completed (exit 0)"}
        if ec is not None:
            return {"status": "crashed", "reason": f"exit {ec}"}
        return {"status": "died", "reason": "gone from the agents registry"}
```

- [ ] **Step 5: Implement render change** — in `plugins/cc-maestro/ccmaestro/render.py` `build_rows`, before calling `watchdog.verdict`, read the completion marker and include it in the entry. Add a helper and use it:

```python
import json
from . import watchdog, autopilot as ap, paths

def _completed_exit(meta):
    if not meta or not meta.get("agent_id"):
        return None
    f = paths.agent_dir(meta["agent_id"]) / "result.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text()).get("exit")
    except (json.JSONDecodeError, OSError):
        return None
```

and change the verdict call to pass it:

```python
        v = watchdog.verdict(summary, {**e, "is_autopilot": is_ap, "completed_exit": _completed_exit(meta)}, config, now)
```

- [ ] **Step 6: Run all four affected test files, verify pass**

Run:
```bash
python3 plugins/cc-maestro/tests/test_launcher.py -v
python3 plugins/cc-maestro/tests/test_watchdog.py -v
python3 plugins/cc-maestro/tests/test_render.py -v
```
Expected: all PASS (render still passes — `_completed_exit(None)` returns None for its injected rows).

- [ ] **Step 7: Commit**

```bash
cd /Users/kubik/nox/misc/claude-code-harness
git add plugins/cc-maestro/ccmaestro/launcher.py plugins/cc-maestro/ccmaestro/watchdog.py plugins/cc-maestro/ccmaestro/render.py plugins/cc-maestro/tests/test_launcher.py plugins/cc-maestro/tests/test_watchdog.py
git commit -m "feat(ccmaestro): completion marker -> done/crashed/died; record pid; resume argv"
```

---

### Task 3: `ccmaestro stop <id>` (normal kill + autopilot graceful cancel)

**Files:**
- Modify: `plugins/cc-maestro/ccmaestro/control.py` (add `stop_agent`)
- Modify: `plugins/cc-maestro/ccmaestro/cli.py` (add `stop` subcommand)
- Modify: `plugins/cc-maestro/tests/test_control.py`

**Interfaces:**
- Produces: `control.stop_agent(info, *, sender=os.killpg) -> (str, str)` returning a `(result, detail)` where result is `autopilot-cancelled` | `stopped` | `no-pid` | `not-found`. Autopilot → remove `<cwd>/.claude/ccharness/autopilot/state.json`; else → SIGTERM the process group. CLI: `ccmaestro stop <id>`.

- [ ] **Step 1: Write failing test** — add to `plugins/cc-maestro/tests/test_control.py`:

```python
    def test_stop_autopilot_removes_state(self):
        repo = tempfile.mkdtemp()
        ap_dir = Path(repo) / ".claude" / "ccharness" / "autopilot"; ap_dir.mkdir(parents=True)
        state = ap_dir / "state.json"; state.write_text(json.dumps({"active": True}))
        info = {"is_autopilot": True, "cwd": repo, "pid": 123}
        sent = []
        result, _ = self.control.stop_agent(info, sender=lambda p, s: sent.append((p, s)))
        self.assertEqual(result, "autopilot-cancelled")
        self.assertFalse(state.exists())     # state removed
        self.assertEqual(sent, [])           # process NOT signalled

    def test_stop_normal_signals_group(self):
        import signal as sig
        sent = []
        info = {"is_autopilot": False, "cwd": "/x", "pid": 555}
        result, _ = self.control.stop_agent(info, sender=lambda p, s: sent.append((p, s)))
        self.assertEqual(result, "stopped")
        self.assertEqual(sent, [(555, sig.SIGTERM)])

    def test_stop_no_pid(self):
        result, _ = self.control.stop_agent({"is_autopilot": False, "pid": None}, sender=lambda p, s: None)
        self.assertEqual(result, "no-pid")
```

- [ ] **Step 2: Run, verify the new tests fail**

Run: `python3 plugins/cc-maestro/tests/test_control.py -v`
Expected: the three new tests FAIL (`stop_agent` missing).

- [ ] **Step 3: Implement `stop_agent`** — in `plugins/cc-maestro/ccmaestro/control.py`, add `import signal` at top and:

```python
def stop_agent(info, *, sender=os.killpg):
    if info.get("is_autopilot"):
        from pathlib import Path
        f = Path(info["cwd"]) / ".claude" / "ccharness" / "autopilot" / "state.json"
        try:
            f.unlink()
        except FileNotFoundError:
            return ("autopilot-cancelled", "state already gone")
        except OSError as e:
            return ("not-found", str(e))
        return ("autopilot-cancelled", str(f))
    pid = info.get("pid")
    if not pid:
        return ("no-pid", "no recorded pid")
    if send_signal(pid, signal.SIGTERM, sender=sender):
        return ("stopped", str(pid))
    return ("not-found", "signal failed (process gone?)")
```

- [ ] **Step 4: Wire the `stop` subcommand** — in `plugins/cc-maestro/ccmaestro/cli.py` add (import `from . import control` where the other imports are):

```python
def _stop(args):
    info = control.resolve(args.id)
    if not info:
        print(f"no agent matching {args.id}", file=sys.stderr); return 1
    result, detail = control.stop_agent(info)
    print(f"{args.id}: {result}" + (f" ({detail})" if detail else ""))
    return 0 if result in ("stopped", "autopilot-cancelled") else 1
```

and register in `build_parser()`:

```python
    sp = sub.add_parser("stop", help="stop an agent (autopilot -> graceful cancel)")
    sp.add_argument("id")
    sp.set_defaults(func=_stop)
```

- [ ] **Step 5: Run control tests, verify pass**

Run: `python3 plugins/cc-maestro/tests/test_control.py -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
cd /Users/kubik/nox/misc/claude-code-harness
git add plugins/cc-maestro/ccmaestro/control.py plugins/cc-maestro/ccmaestro/cli.py plugins/cc-maestro/tests/test_control.py
git commit -m "feat(ccmaestro): stop command (SIGTERM group; autopilot graceful cancel)"
```

---

### Task 4: `ccmaestro steer` (stop-then-resume) + `pause`/`resume`

**Files:**
- Modify: `plugins/cc-maestro/ccmaestro/control.py` (add `steer_agent`, `pause_agent`, `resume_agent`)
- Modify: `plugins/cc-maestro/ccmaestro/cli.py` (add `steer`, `pause`, `resume`)
- Modify: `plugins/cc-maestro/tests/test_control.py`

**Interfaces:**
- Produces: `control.steer_agent(info, message, *, sender=os.killpg, spawn=None) -> (str, str)` — stops the running agent (SIGTERM group), then spawns `launcher.build_resume_argv(sessionId, message, ...)` via the same completion wrapper; `spawn` is an injectable `(argv_list, cwd) -> pid`. `control.pause_agent`/`resume_agent(info, *, sender=os.killpg)` send SIGSTOP/SIGCONT to the group. CLI: `ccmaestro steer <id> "<msg>"`, `ccmaestro pause <id>`, `ccmaestro resume <id>`.

- [ ] **Step 1: Write failing test** — add to `plugins/cc-maestro/tests/test_control.py`:

```python
    def test_pause_sends_sigstop(self):
        import signal as sig
        sent = []
        self.control.pause_agent({"pid": 7}, sender=lambda p, s: sent.append((p, s)))
        self.assertEqual(sent, [(7, sig.SIGSTOP)])

    def test_resume_sends_sigcont(self):
        import signal as sig
        sent = []
        self.control.resume_agent({"pid": 7}, sender=lambda p, s: sent.append((p, s)))
        self.assertEqual(sent, [(7, sig.SIGCONT)])

    def test_steer_stops_then_respawns(self):
        import signal as sig
        sent = []; spawned = []
        info = {"is_autopilot": False, "pid": 7, "sessionId": "sid-7", "cwd": "/r",
                "meta": {"agent_id": "aid7", "model": None, "budget": None, "yolo": False}}
        result, _ = self.control.steer_agent(
            info, "go left",
            sender=lambda p, s: sent.append((p, s)),
            spawn=lambda argv, cwd: spawned.append((argv, cwd)) or 4321)
        self.assertEqual(result, "steered")
        self.assertEqual(sent, [(7, sig.SIGTERM)])            # stopped first
        self.assertIn("--resume", spawned[0][0])              # then resumed
        self.assertIn("go left", spawned[0][0])
        self.assertEqual(spawned[0][1], "/r")

    def test_steer_refuses_autopilot(self):
        result, _ = self.control.steer_agent({"is_autopilot": True, "cwd": "/r"}, "x",
                                             sender=lambda p, s: None, spawn=lambda a, c: 1)
        self.assertEqual(result, "refused-autopilot")
```

- [ ] **Step 2: Run, verify the new tests fail**

Run: `python3 plugins/cc-maestro/tests/test_control.py -v`
Expected: the four new tests FAIL.

- [ ] **Step 3: Implement** — in `plugins/cc-maestro/ccmaestro/control.py` add:

```python
def pause_agent(info, *, sender=os.killpg):
    return ("paused", str(info.get("pid"))) if send_signal(info.get("pid"), signal.SIGSTOP, sender=sender) else ("no-pid", "")

def resume_agent(info, *, sender=os.killpg):
    return ("resumed", str(info.get("pid"))) if send_signal(info.get("pid"), signal.SIGCONT, sender=sender) else ("no-pid", "")

def steer_agent(info, message, *, sender=os.killpg, spawn=None):
    if info.get("is_autopilot"):
        return ("refused-autopilot", "redirect an autopilot via its own funnel, not steer")
    sid = info.get("sessionId")
    if not sid:
        return ("no-session", "no sessionId to resume")
    send_signal(info.get("pid"), signal.SIGTERM, sender=sender)  # stop the live run first
    from . import launcher
    meta = info.get("meta") or {}
    argv = launcher.build_resume_argv(sid, message, model=meta.get("model"),
                                      budget=meta.get("budget"), yolo=meta.get("yolo", False))
    spawn = spawn or launcher.spawn_resume
    pid = spawn(argv, info.get("cwd"))
    return ("steered", str(pid))
```

- [ ] **Step 4: Add the production `spawn_resume`** — in `plugins/cc-maestro/ccmaestro/launcher.py` add (this is the non-injected default used by the CLI):

```python
def spawn_resume(argv, cwd):
    import os as _os
    log_dir = paths.STATE_DIR / "agents" / "_resume"
    log_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(argv, cwd=cwd or _os.getcwd(), stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, start_new_session=True)
    return proc.pid
```

(Import `from . import config` is already present as `config`; `paths.STATE_DIR` mirrors `config.STATE_DIR` — use `config.STATE_DIR` if `paths` doesn't re-export it. Read paths.py first and use whichever exists.)

- [ ] **Step 5: Wire CLI** — in `plugins/cc-maestro/ccmaestro/cli.py` add handlers and parsers:

```python
def _steer(args):
    info = control.resolve(args.id)
    if not info:
        print(f"no agent matching {args.id}", file=sys.stderr); return 1
    result, detail = control.steer_agent(info, args.message)
    print(f"{args.id}: {result}" + (f" ({detail})" if detail else ""))
    return 0 if result == "steered" else 1

def _pause(args):
    info = control.resolve(args.id)
    if not info: print(f"no agent matching {args.id}", file=sys.stderr); return 1
    result, _ = control.pause_agent(info); print(f"{args.id}: {result}"); return 0 if result == "paused" else 1

def _resume(args):
    info = control.resolve(args.id)
    if not info: print(f"no agent matching {args.id}", file=sys.stderr); return 1
    result, _ = control.resume_agent(info); print(f"{args.id}: {result}"); return 0 if result == "resumed" else 1
```

and in `build_parser()`:

```python
    se = sub.add_parser("steer", help="stop an agent and resume it with a new instruction")
    se.add_argument("id"); se.add_argument("message"); se.set_defaults(func=_steer)
    pa = sub.add_parser("pause", help="pause an agent (SIGSTOP)"); pa.add_argument("id"); pa.set_defaults(func=_pause)
    re_ = sub.add_parser("resume", help="resume a paused agent (SIGCONT)"); re_.add_argument("id"); re_.set_defaults(func=_resume)
```

- [ ] **Step 6: Run control tests, verify pass**

Run: `python3 plugins/cc-maestro/tests/test_control.py -v`
Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
cd /Users/kubik/nox/misc/claude-code-harness
git add plugins/cc-maestro/ccmaestro/control.py plugins/cc-maestro/ccmaestro/launcher.py plugins/cc-maestro/ccmaestro/cli.py plugins/cc-maestro/tests/test_control.py
git commit -m "feat(ccmaestro): steer (stop-then-resume) + pause/resume"
```

---

### Task 5: Reporting — `ccmaestro check [--notify]` + push hook

**Files:**
- Create: `plugins/cc-maestro/ccmaestro/report.py`
- Create: `plugins/cc-maestro/ccmaestro/hooks/report-hook.sh`
- Create: `plugins/cc-maestro/ccmaestro/hooks/hooks.json`
- Modify: `plugins/cc-maestro/ccmaestro/cli.py` (add `check`)
- Test: `plugins/cc-maestro/tests/test_report.py`

**Interfaces:**
- Produces: `report.snapshot(rows) -> dict[id -> verdict]`; `report.diff(prev, cur) -> list[event]` (event = `{"id","from","to"}` for verdicts that changed or newly appeared, only when the new verdict is not "ok"); `report.record(event)` (append to `~/.ccmaestro/events.jsonl`, atomic); `report.post(url, event, poster=urllib_poster) -> bool`. CLI: `ccmaestro check [--notify]` computes the current rows, diffs against `~/.ccmaestro/last_snapshot.json`, records + (with `--notify` and a configured `report_endpoint`) posts each event, then writes the new snapshot.

- [ ] **Step 1: Write failing test** — create `plugins/cc-maestro/tests/test_report.py`:

```python
import os, sys, json, tempfile, unittest
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

class TestReport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); os.environ["CCMAESTRO_HOME"] = self.tmp
        import importlib, ccmaestro.config, ccmaestro.paths, ccmaestro.report
        for m in (ccmaestro.config, ccmaestro.paths, ccmaestro.report): importlib.reload(m)
        self.report = ccmaestro.report

    def test_snapshot_maps_id_to_verdict(self):
        rows = [{"id": "a", "verdict": "ok"}, {"id": "b", "verdict": "stalled"}]
        self.assertEqual(self.report.snapshot(rows), {"a": "ok", "b": "stalled"})

    def test_diff_reports_new_problem(self):
        events = self.report.diff({"a": "ok"}, {"a": "stalled"})
        self.assertEqual(events, [{"id": "a", "from": "ok", "to": "stalled"}])

    def test_diff_ignores_change_to_ok(self):
        self.assertEqual(self.report.diff({"a": "stalled"}, {"a": "ok"}), [])

    def test_diff_new_agent_problem(self):
        self.assertEqual(self.report.diff({}, {"z": "looping"}), [{"id": "z", "from": None, "to": "looping"}])

    def test_record_appends_jsonl(self):
        self.report.record({"id": "a", "to": "died"})
        self.report.record({"id": "b", "to": "stalled"})
        lines = (Path(self.tmp) / "events.jsonl").read_text().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0])["id"], "a")

    def test_post_calls_poster(self):
        calls = []
        ok = self.report.post("http://hermes/x", {"id": "a"}, poster=lambda u, b: calls.append((u, b)))
        self.assertTrue(ok)
        self.assertEqual(calls[0][0], "http://hermes/x")

    def test_post_no_url_false(self):
        self.assertFalse(self.report.post("", {"id": "a"}, poster=lambda u, b: None))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run, verify it fails**

Run: `python3 plugins/cc-maestro/tests/test_report.py -v`
Expected: FAIL — `No module named 'ccmaestro.report'`.

- [ ] **Step 3: Implement** — create `plugins/cc-maestro/ccmaestro/report.py`:

```python
import json
import urllib.request
from . import config, paths

def snapshot(rows):
    return {r["id"]: r["verdict"] for r in rows}

def diff(prev, cur):
    events = []
    for aid, verdict in cur.items():
        if verdict == "ok":
            continue
        if prev.get(aid) != verdict:
            events.append({"id": aid, "from": prev.get(aid), "to": verdict})
    return events

def record(event):
    f = config.STATE_DIR / "events.jsonl"
    f.parent.mkdir(parents=True, exist_ok=True)
    existing = f.read_text() if f.exists() else ""
    paths.atomic_write(f, existing + json.dumps(event) + "\n")

def _urllib_poster(url, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    urllib.request.urlopen(req, timeout=5).close()

def post(url, event, poster=_urllib_poster):
    if not url:
        return False
    try:
        poster(url, event)
        return True
    except Exception:
        return False
```

- [ ] **Step 4: Wire the `check` subcommand** — in `plugins/cc-maestro/ccmaestro/cli.py` add (import `from . import report`):

```python
def _check(args):
    cfg = config.load_config()
    now = datetime.now(timezone.utc)
    entries = registry.merge(registry.native_agents(), registry.load_meta_records())
    summarizer = lambda sid: transcript.parse_transcript(paths.transcript_path(sid)) if sid else transcript.parse_transcript(None)
    rows = render.build_rows(entries, now, summarizer=summarizer, config=cfg)
    cur = report.snapshot(rows)
    snap_file = config.STATE_DIR / "last_snapshot.json"
    prev = {}
    if snap_file.exists():
        try: prev = json.loads(snap_file.read_text())
        except (json.JSONDecodeError, OSError): prev = {}
    events = report.diff(prev, cur)
    for e in events:
        report.record(e)
        if args.notify and cfg.get("report_endpoint"):
            report.post(cfg["report_endpoint"], e)
    paths.atomic_write(snap_file, json.dumps(cur))
    print(json.dumps(events, indent=2) if args.json else f"{len(events)} new event(s)")
    return 0
```

(add `import json` at top of cli.py if not already imported), and register:

```python
    ck = sub.add_parser("check", help="detect agent state changes; record + optionally notify")
    ck.add_argument("--notify", action="store_true", help="POST new events to report_endpoint")
    ck.add_argument("--json", action="store_true")
    ck.set_defaults(func=_check)
```

- [ ] **Step 5: Create the push hook** — `plugins/cc-maestro/ccmaestro/hooks/report-hook.sh`:

```bash
#!/usr/bin/env bash
# ccmaestro push reporter: forwards Stop/SubagentStop/Notification events to the
# configured report_endpoint so an external agent (hermes) hears about agents
# without polling. No-op when no endpoint is configured.
set -euo pipefail
INPUT="$(cat 2>/dev/null || true)"
CFG="${CCMAESTRO_HOME:-$HOME/.ccmaestro}/config.json"
[ -f "$CFG" ] || exit 0
URL="$(jq -r '.report_endpoint // ""' "$CFG" 2>/dev/null || true)"
[ -n "$URL" ] || exit 0
SID="$(printf '%s' "$INPUT" | jq -r '.session_id // ""' 2>/dev/null || true)"
EVENT="$(printf '%s' "$INPUT" | jq -r '.hook_event_name // ""' 2>/dev/null || true)"
CWD="$(printf '%s' "$INPUT" | jq -r '.cwd // ""' 2>/dev/null || true)"
curl -fsS -m 5 -X POST -H 'Content-Type: application/json' \
  -d "{\"event\":\"$EVENT\",\"session_id\":\"$SID\",\"cwd\":\"$CWD\"}" "$URL" >/dev/null 2>&1 || true
exit 0
```

and `plugins/cc-maestro/ccmaestro/hooks/hooks.json`:

```json
{
  "description": "ccmaestro push reporter — forwards Stop/SubagentStop/Notification to the configured report_endpoint.",
  "hooks": {
    "Stop": [{ "hooks": [{ "type": "command", "command": "bash \"${CLAUDE_PLUGIN_ROOT}/ccmaestro/hooks/report-hook.sh\"" }] }],
    "SubagentStop": [{ "hooks": [{ "type": "command", "command": "bash \"${CLAUDE_PLUGIN_ROOT}/ccmaestro/hooks/report-hook.sh\"" }] }],
    "Notification": [{ "hooks": [{ "type": "command", "command": "bash \"${CLAUDE_PLUGIN_ROOT}/ccmaestro/hooks/report-hook.sh\"" }] }]
  }
}
```

Wait — the plugin's hooks.json must sit at the plugin root's `hooks/` dir (like cc-agent's). Put `hooks.json` and `report-hook.sh` under `plugins/cc-maestro/hooks/` (NOT under `ccmaestro/hooks/`), and the command path becomes `bash "${CLAUDE_PLUGIN_ROOT}/hooks/report-hook.sh"`. **Create them at `plugins/cc-maestro/hooks/`** and use that command path. Make the script executable: `chmod +x plugins/cc-maestro/hooks/report-hook.sh`. Verify syntax: `bash -n plugins/cc-maestro/hooks/report-hook.sh`.

- [ ] **Step 6: Run report tests + hook syntax check**

Run:
```bash
python3 plugins/cc-maestro/tests/test_report.py -v
bash -n plugins/cc-maestro/hooks/report-hook.sh && echo HOOK_OK
jq . plugins/cc-maestro/hooks/hooks.json >/dev/null && echo HOOKS_JSON_OK
```
Expected: tests PASS; `HOOK_OK`; `HOOKS_JSON_OK`.

- [ ] **Step 7: Commit**

```bash
cd /Users/kubik/nox/misc/claude-code-harness
git add plugins/cc-maestro/ccmaestro/report.py plugins/cc-maestro/ccmaestro/cli.py plugins/cc-maestro/hooks plugins/cc-maestro/tests/test_report.py
git commit -m "feat(ccmaestro): check command + events.jsonl + push report hook"
```

---

### Task 6: Fleet-wide concurrency cap + README + final verification

**Files:**
- Modify: `plugins/cc-maestro/ccmaestro/config.py` (add `max_concurrent`)
- Modify: `plugins/cc-maestro/ccmaestro/launcher.py` (`start` refuses past the cap)
- Modify: `plugins/cc-maestro/ccmaestro/cli.py` (`_start` surfaces the refusal)
- Modify: `plugins/cc-maestro/README.md` (document control verbs + reporting)
- Modify: `plugins/cc-maestro/tests/test_launcher.py`

**Interfaces:**
- Produces: `config` default `max_concurrent: 0` (0 = unlimited). `launcher.active_count(runner=None) -> int` (number of native agents currently running). `launcher.start(...)` raises `launcher.FleetFull` when `max_concurrent > 0` and `active_count() >= max_concurrent`. CLI `_start` catches it and prints a clear message (exit 1).

- [ ] **Step 1: Write failing test** — add to `plugins/cc-maestro/tests/test_launcher.py`:

```python
    def test_active_count_counts_native(self):
        from ccmaestro import launcher
        run = lambda: '[{"sessionId":"a"},{"sessionId":"b"}]'
        self.assertEqual(launcher.active_count(runner=run), 2)

    def test_start_raises_when_fleet_full(self):
        import os, tempfile, importlib
        os.environ["CCMAESTRO_HOME"] = tempfile.mkdtemp()
        (Path:=__import__("pathlib").Path)(os.environ["CCMAESTRO_HOME"]).mkdir(exist_ok=True)
        import ccmaestro.config as c; importlib.reload(c)
        (Path(os.environ["CCMAESTRO_HOME"]) / "config.json").write_text('{"max_concurrent": 1}')
        from ccmaestro import launcher; importlib.reload(launcher)
        run = lambda: '[{"sessionId":"a"},{"sessionId":"b"}]'  # 2 active >= cap 1
        with self.assertRaises(launcher.FleetFull):
            launcher.start("x", native_runner=run)
```

(Place this in a small dedicated TestCase class at the bottom of test_launcher.py if the existing class lacks setUp for env isolation — read the file and follow its structure.)

- [ ] **Step 2: Run, verify the new tests fail**

Run: `python3 plugins/cc-maestro/tests/test_launcher.py -v`
Expected: the two new tests FAIL (`active_count`/`FleetFull` missing).

- [ ] **Step 3: Implement** — in `plugins/cc-maestro/ccmaestro/config.py` add `"max_concurrent": 0,` to `DEFAULTS`. In `plugins/cc-maestro/ccmaestro/launcher.py` add (import `from . import config, registry`):

```python
class FleetFull(Exception):
    pass

def active_count(runner=None):
    return len(registry.native_agents(runner=runner))
```

and at the very top of `start(...)` (add a `native_runner=None` keyword param to `start`):

```python
    cfg = config.load_config()
    cap = cfg.get("max_concurrent") or 0
    if cap > 0 and active_count(runner=native_runner) >= cap:
        raise FleetFull(f"fleet at capacity ({cap}); stop an agent before launching another")
```

- [ ] **Step 4: Surface in CLI** — in `plugins/cc-maestro/ccmaestro/cli.py` `_start`, wrap the launch:

```python
def _start(args):
    from . import launcher
    try:
        agent_id = launcher.start(args.task, repo=args.repo, model=args.model,
                                  budget=args.budget, name=args.name, yolo=args.yolo)
    except launcher.FleetFull as e:
        print(str(e), file=sys.stderr); return 1
    print(agent_id); return 0
```

- [ ] **Step 5: Update the README** — in `plugins/cc-maestro/README.md`, add a "Control" section after the "Use it" block:

```markdown
## Control (Phase 3)

```bash
ccmaestro stop <id>              # SIGTERM the agent's group; an autopilot is cancelled gracefully
ccmaestro steer <id> "do X now"  # stop, then resume the session with a new instruction
ccmaestro pause <id> / resume <id>
ccmaestro check --notify         # detect stalled/looping/died/crashed; POST changes to report_endpoint
```

Set `report_endpoint` in `~/.ccmaestro/config.json` to a webhook URL so an external
agent (hermes) is notified — either by `check --notify` (poll) or by the bundled
Stop/Notification hook (push). `max_concurrent` (default 0 = unlimited) caps how many
agents `start` will launch. A finished one-shot now shows `done` (clean) or `crashed`
(non-zero exit) instead of `died`.
```

- [ ] **Step 6: Full suite + live smoke**

Run the full suite:
```bash
cd /Users/kubik/nox/misc/claude-code-harness
for t in plugins/cc-maestro/tests/test_*.py; do python3 "$t" || exit 1; done; echo ALL_GREEN
```
Expected: `ALL_GREEN`.

Live smoke (launch, then stop it via ccmaestro):
```bash
ID=$(plugins/cc-maestro/bin/ccmaestro start "Sleep by counting slowly to 500, one per line." --repo "$PWD" --budget 1)
echo "launched $ID"; sleep 4
plugins/cc-maestro/bin/ccmaestro ls | grep -i "$ID"
plugins/cc-maestro/bin/ccmaestro stop "$ID"
sleep 2
plugins/cc-maestro/bin/ccmaestro ls | grep -i "$ID"   # should now show done/crashed/died, not busy
plugins/cc-maestro/bin/ccmaestro check                 # should record the state change
```
Expected: the agent launches, is stoppable, and `check` reports the change. Include output in the report.

- [ ] **Step 7: Commit**

```bash
cd /Users/kubik/nox/misc/claude-code-harness
git add plugins/cc-maestro
git commit -m "feat(ccmaestro): fleet concurrency cap + README control docs"
```

---

## Self-Review

**Spec coverage (§3.1d, §3.1e, §3.3, §7a.5):**
- §3.1e stop (SIGTERM group) + autopilot graceful cancel → Task 3. ✓
- §3.1e steer = stop-then-resume; pause/resume (SIGSTOP/SIGCONT) → Task 4. ✓
- §3.1d reporting: pull (`check`) + push (hook) + events.jsonl + endpoint POST → Task 5. ✓
- §3.3 autopilot stop via state-file removal (not kill) → Task 3, control.stop_agent. ✓
- Completion marker → done/crashed/died (fixes the Phase 2 "died" cosmetic) → Task 2. ✓
- §7a.5 fleet concurrency cap → Task 6. ✓
- Deferred (stated): the `--remote-control` live-steer spike (steer uses stop-then-resume, which the spec calls the ~90% path); a fleet-wide *spend* ceiling (only the concurrency cap is in v1 — note in README if pursued later).

**Placeholder scan:** none — every step has complete code or exact commands. Two steps say "read the file first and follow its structure" for edits to existing multi-line functions (cli.build_parser, test_launcher classes) — these are precise integration instructions, not placeholders; the exact code to add is given.

**Type/name consistency:** `info` dict shape (`agent_id/sessionId/pid/cwd/is_autopilot/native/meta/launched_by_ccmaestro`) is produced by `control.resolve` and consumed by `stop_agent/steer_agent/pause_agent/resume_agent` identically. `(result, detail)` tuple return is consistent across all control actions and the CLI handlers. `entry["completed_exit"]` is written by `render.build_rows` and read by `watchdog.verdict`. `build_resume_argv`/`build_spawn_command`/`active_count`/`FleetFull` names match between launcher.py and its tests.

**Risk notes:** Task 2 changes how agents are spawned (shell wrapper) — the live smoke in Task 6 exercises the real spawn+stop path end-to-end. Signals are injected in every unit test (no real process is ever signalled in tests). The bash report hook is syntax-checked, not unit-tested (bash); its logic is a thin no-op-unless-configured forwarder.
