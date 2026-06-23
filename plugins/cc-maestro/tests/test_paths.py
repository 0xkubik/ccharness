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
