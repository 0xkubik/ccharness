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
