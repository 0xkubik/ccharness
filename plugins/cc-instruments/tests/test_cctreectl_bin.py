import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin" / "cctreectl"

HAS_TREE_TOOL = bool(shutil.which("eza") or shutil.which("tree"))


class TestCctreeBin(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name).resolve()

    def tearDown(self):
        self.tmp.cleanup()

    def run_bin(self, *args, cwd=None):
        target_cwd = cwd or self.base
        env = dict(os.environ)
        env["PWD"] = str(target_cwd)
        return subprocess.run(
            [str(BIN), *args],
            cwd=str(target_cwd),
            env=env,
            capture_output=True,
            text=True,
        )

    def make_git_repo(self):
        """A repo with a tracked file, a gitignored file, and a nested file."""
        repo = self.base / "proj"
        (repo / "src").mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        (repo / ".gitignore").write_text("ignored.txt\nbuild/\n")
        (repo / "tracked.py").write_text("x = 1\n")
        (repo / "ignored.txt").write_text("secret\n")
        (repo / "src" / "app.py").write_text("y = 2\n")
        (repo / "build").mkdir()
        (repo / "build" / "out.o").write_text("junk\n")
        return repo

    def test_bin_exists_and_executable(self):
        self.assertTrue(BIN.exists(), "bin/cctreectl missing")
        self.assertTrue(os.access(BIN, os.X_OK), "bin/cctreectl not executable")

    def test_help_exits_0(self):
        for arg in ("help", "--help", "-h"):
            r = self.run_bin(arg)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("cctreectl", r.stdout)

    def test_bad_path_exits_1(self):
        r = self.run_bin(str(self.base / "does-not-exist"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("not a directory", r.stderr)

    def test_maps_repo_respecting_gitignore(self):
        # Backend-agnostic: holds for eza (--git-ignore), tree (--gitignore), and the
        # git-ls-files fallback (--exclude-standard) alike.
        repo = self.make_git_repo()
        r = self.run_bin(cwd=repo)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("tracked.py", r.stdout)
        self.assertIn("app.py", r.stdout)
        self.assertNotIn("ignored.txt", r.stdout)
        self.assertNotIn("out.o", r.stdout)

    def test_git_dir_not_descended(self):
        repo = self.make_git_repo()
        r = self.run_bin(cwd=repo)
        self.assertEqual(r.returncode, 0, r.stderr)
        # .git holds HEAD, config, hooks/… — none of it should appear in the map.
        self.assertNotIn("HEAD", r.stdout)

    @unittest.skipIf(HAS_TREE_TOOL, "a tree tool is installed; fallback path not taken")
    def test_fallback_used_when_no_tree_tool(self):
        repo = self.make_git_repo()
        r = self.run_bin(cwd=repo)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("git file list", r.stdout)

    @unittest.skipIf(HAS_TREE_TOOL, "a tree tool is installed; non-git dir would still map")
    def test_non_git_dir_without_tool_exits_1(self):
        bare = self.base / "bare"
        bare.mkdir()
        r = self.run_bin(cwd=bare)
        self.assertEqual(r.returncode, 1)
        self.assertIn("not a git repo", r.stderr)


if __name__ == "__main__":
    unittest.main()
