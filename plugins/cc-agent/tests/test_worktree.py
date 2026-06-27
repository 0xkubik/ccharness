import json, subprocess, tempfile, unittest
from pathlib import Path

WT = Path(__file__).resolve().parent.parent / "skills" / "musician" / "worktree.sh"


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)


def run_wt(repo, *args):
    r = subprocess.run(["bash", str(WT), *args], cwd=repo, capture_output=True, text=True)
    out = {}
    for line in r.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k] = v
    return out, r


def make_repo():
    repo = tempfile.mkdtemp()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "user.name", "t")
    (Path(repo) / "CLAUDE.md").write_text("# P\n## Product North Star\nx\n")
    (Path(repo) / "app.txt").write_text("base\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    return repo


def build_worktree(repo, name="agent-x"):
    path = f".claude/worktrees/{name}"
    branch = f"worktree-{name}"
    git(repo, "worktree", "add", "-q", path, "-b", branch)
    wt = Path(repo) / path
    (wt / "app.txt").write_text("base\nfeature\n")
    git(wt, "add", "-A")
    git(wt, "commit", "-qm", "do: feature")
    return path, branch


class TestPrepare(unittest.TestCase):
    def test_sets_gitignore_and_baseref(self):
        repo = make_repo()
        out, _ = run_wt(repo, "prepare")
        self.assertEqual(out.get("PREPARED"), "1")
        self.assertIn(".claude/worktrees/", (Path(repo) / ".gitignore").read_text())
        s = json.loads((Path(repo) / ".claude" / "settings.local.json").read_text())
        self.assertEqual(s["worktree"]["baseRef"], "head")

    def test_idempotent(self):
        repo = make_repo()
        run_wt(repo, "prepare")
        run_wt(repo, "prepare")
        self.assertEqual((Path(repo) / ".gitignore").read_text().count(".claude/worktrees/"), 1)

    def test_merges_existing_settings(self):
        repo = make_repo()
        d = Path(repo) / ".claude"
        d.mkdir(exist_ok=True)
        (d / "settings.local.json").write_text(json.dumps({"permissions": {"allow": ["x"]}}))
        run_wt(repo, "prepare")
        s = json.loads((d / "settings.local.json").read_text())
        self.assertEqual(s["worktree"]["baseRef"], "head")
        self.assertEqual(s["permissions"]["allow"], ["x"])  # untouched

    def test_flags_uncommitted_north_star(self):
        # A build worktree is cut from committed HEAD — an uncommitted North Star would be absent.
        repo = make_repo()
        (Path(repo) / "CLAUDE.md").write_text("# P\n## Product North Star\nCHANGED\n")
        out, _ = run_wt(repo, "prepare")
        self.assertEqual(out.get("GROUNDING_DIRTY"), "1")


class TestIntegrate(unittest.TestCase):
    def test_lands_commit_and_removes_worktree(self):
        repo = make_repo()
        path, branch = build_worktree(repo)
        out, _ = run_wt(repo, "integrate", path, branch)
        self.assertIn("INTEGRATED", out)
        self.assertIn("feature", (Path(repo) / "app.txt").read_text())  # landed on current branch
        self.assertFalse((Path(repo) / path).exists())                  # worktree gone
        self.assertNotIn(branch, git(repo, "branch").stdout)            # branch gone

    def test_conflict_keeps_worktree_and_aborts(self):
        repo = make_repo()
        path, branch = build_worktree(repo)
        # move the current branch so the build's added line conflicts (non-ff, overlapping)
        (Path(repo) / "app.txt").write_text("base\nMAIN-EDIT\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "main edit")
        out, _ = run_wt(repo, "integrate", path, branch)
        self.assertIn("CONFLICT", out)
        self.assertTrue((Path(repo) / path).exists())          # kept for inspection
        self.assertIn(branch, git(repo, "branch").stdout)      # branch kept
        self.assertFalse((Path(repo) / ".git" / "MERGE_HEAD").exists())  # merge aborted cleanly


class TestDiscard(unittest.TestCase):
    def test_removes_dirty_worktree_without_touching_main(self):
        repo = make_repo()
        path = ".claude/worktrees/agent-y"
        branch = "worktree-agent-y"
        git(repo, "worktree", "add", "-q", path, "-b", branch)
        (Path(repo) / path / "app.txt").write_text("uncommitted junk\n")  # dirty
        out, _ = run_wt(repo, "discard", path, branch)
        self.assertEqual(out.get("DISCARDED"), "1")
        self.assertFalse((Path(repo) / path).exists())
        self.assertNotIn(branch, git(repo, "branch").stdout)
        self.assertEqual((Path(repo) / "app.txt").read_text(), "base\n")  # main untouched


if __name__ == "__main__":
    unittest.main()
