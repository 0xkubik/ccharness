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
