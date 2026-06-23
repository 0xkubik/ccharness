import os, sys, json, tempfile, unittest
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

class TestReport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        _prev = {k: os.environ.get(k) for k in ("CCMAESTRO_HOME",)}
        def _restore():
            for k, v in _prev.items():
                if v is None: os.environ.pop(k, None)
                else: os.environ[k] = v
        self.addCleanup(_restore)
        os.environ["CCMAESTRO_HOME"] = self.tmp
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

    def test_post_swallows_poster_exception(self):
        def boom(u, b): raise RuntimeError("hermes down")
        self.assertFalse(self.report.post("http://x", {"id": "a"}, poster=boom))

if __name__ == "__main__":
    unittest.main()
