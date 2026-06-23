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

if __name__ == "__main__":
    unittest.main()
