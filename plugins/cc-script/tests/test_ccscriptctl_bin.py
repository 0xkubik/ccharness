import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin" / "ccscriptctl"


class TestCcfunnelBin(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name).resolve()
        self.proj = self.base / "proj"
        self.ccdir = self.proj / ".claude" / "ccharness"
        self.ccdir.mkdir(parents=True)
        (self.ccdir / "roadmap.md").write_text("# Roadmap\n")
        (self.ccdir / "cheatsheet.md").write_text("# Cheats\n")
        # A fake editor that records the path it was told to open.
        self.opened = self.base / "opened"
        self.fake_editor = self.base / "fake_editor"
        self.fake_editor.write_text(
            '#!/usr/bin/env bash\nprintf "%s" "$1" > ' f'"{self.opened}"\n'
        )
        self.fake_editor.chmod(0o755)

    def tearDown(self):
        self.tmp.cleanup()

    def run_bin(self, *args, cwd=None, env_extra=None):
        target_cwd = cwd or self.proj
        env = dict(os.environ)
        env["EDITOR"] = str(self.fake_editor)
        env["PWD"] = str(target_cwd)
        env.pop("VISUAL", None)
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            [str(BIN), *args],
            cwd=str(target_cwd),
            env=env,
            capture_output=True,
            text=True,
        )

    def test_bin_exists_and_executable(self):
        self.assertTrue(BIN.exists(), "bin/ccscriptctl missing")
        self.assertTrue(os.access(BIN, os.X_OK), "bin/ccscriptctl not executable")

    def test_opens_roadmap(self):
        r = self.run_bin("roadmap")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.opened.read_text(), str(self.ccdir / "roadmap.md"))

    def test_opens_cheatsheet(self):
        r = self.run_bin("cheatsheet")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.opened.read_text(), str(self.ccdir / "cheatsheet.md"))

    def test_walks_up_from_subdir(self):
        deep = self.proj / "a" / "b" / "c"
        deep.mkdir(parents=True)
        r = self.run_bin("roadmap", cwd=deep)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.opened.read_text(), str(self.ccdir / "roadmap.md"))

    def test_visual_takes_priority_over_editor(self):
        visual = self.base / "fake_visual"
        marker = self.base / "vis_opened"
        visual.write_text('#!/usr/bin/env bash\nprintf "%s" "$1" > ' f'"{marker}"\n')
        visual.chmod(0o755)
        r = self.run_bin("roadmap", env_extra={"VISUAL": str(visual)})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(marker.read_text(), str(self.ccdir / "roadmap.md"))
        self.assertFalse(self.opened.exists(), "$EDITOR ran even though $VISUAL was set")

    def test_missing_file_exits_1_with_hint(self):
        (self.ccdir / "cheatsheet.md").unlink()
        r = self.run_bin("cheatsheet")
        self.assertEqual(r.returncode, 1)
        self.assertIn("/cheatsheet-management", r.stderr)

    def test_no_ccharness_exits_1(self):
        bare = self.base / "bare"
        bare.mkdir()
        r = self.run_bin("roadmap", cwd=bare)
        self.assertEqual(r.returncode, 1)
        self.assertIn("/roadmap-management", r.stderr)

    def test_unknown_command_exits_2(self):
        r = self.run_bin("bogus")
        self.assertEqual(r.returncode, 2)
        self.assertIn("Usage:", r.stderr)

    def test_help_exits_0(self):
        r = self.run_bin("help")
        self.assertEqual(r.returncode, 0)
        self.assertIn("ccscriptctl", r.stdout)


if __name__ == "__main__":
    unittest.main()
