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
