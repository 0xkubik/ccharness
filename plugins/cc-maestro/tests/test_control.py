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

if __name__ == "__main__":
    unittest.main()
