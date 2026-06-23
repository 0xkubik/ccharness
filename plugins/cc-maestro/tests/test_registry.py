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
