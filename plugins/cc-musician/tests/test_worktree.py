import subprocess, tempfile, unittest
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
    # integrate lands on `main`, so the repo's default branch must be main (git defaults to master on
    # older versions). Point unborn HEAD at main before the first commit creates it.
    git(repo, "symbolic-ref", "HEAD", "refs/heads/main")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "user.name", "t")
    d = Path(repo) / ".claude" / "ccharness"
    d.mkdir(parents=True, exist_ok=True)
    (d / "roadmap.md").write_text("# Roadmap\n\n## Product North Star\n\nx\n")
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
    def test_sets_gitignore_no_settings(self):
        # prepare gitignores the worktree dir but does NOT touch any settings file — the build's base
        # is forced per-dispatch by a reset (not a settings.baseRef that might not be read this run).
        repo = make_repo()
        out, _ = run_wt(repo, "prepare")
        self.assertEqual(out.get("PREPARED"), "1")
        self.assertIn(".claude/worktrees/", (Path(repo) / ".gitignore").read_text())
        self.assertFalse((Path(repo) / ".claude" / "settings.local.json").exists())
        self.assertFalse((Path(repo) / ".claude" / "settings.json").exists())

    def test_idempotent(self):
        repo = make_repo()
        run_wt(repo, "prepare")
        run_wt(repo, "prepare")
        self.assertEqual((Path(repo) / ".gitignore").read_text().count(".claude/worktrees/"), 1)

    def test_flags_uncommitted_north_star(self):
        # A build worktree is cut from committed HEAD — an uncommitted North Star / roadmap is absent.
        repo = make_repo()
        (Path(repo) / ".claude" / "ccharness" / "roadmap.md").write_text(
            "# Roadmap\n\n## Product North Star\n\nCHANGED\n")
        out, _ = run_wt(repo, "prepare")
        self.assertEqual(out.get("GROUNDING_DIRTY"), "1")


class TestIntegrate(unittest.TestCase):
    def test_lands_commit_and_removes_worktree(self):
        repo = make_repo()
        path, branch = build_worktree(repo)
        out, _ = run_wt(repo, "integrate", path, branch)
        self.assertIn("INTEGRATED", out)
        self.assertIn("feature", (Path(repo) / "app.txt").read_text())  # landed on local main
        self.assertFalse((Path(repo) / path).exists())                  # worktree gone
        self.assertNotIn(branch, git(repo, "branch").stdout)            # branch gone

    def test_refuses_when_not_on_main(self):
        # Integration lands on LOCAL main, so main must be the checked-out branch. Off main, integrate
        # REFUSES: report STALE/not-on-main, keep the worktree + branch, and never touch main.
        repo = make_repo()
        path, branch = build_worktree(repo)
        git(repo, "checkout", "-q", "-b", "feat")  # conductor wandered off main
        main_before = git(repo, "rev-parse", "main").stdout.strip()
        out, _ = run_wt(repo, "integrate", path, branch)
        self.assertIn("STALE", out)
        self.assertEqual(out.get("REASON"), "not-on-main")
        self.assertTrue((Path(repo) / path).exists())            # worktree kept
        self.assertIn(branch, git(repo, "branch").stdout)        # branch kept
        self.assertEqual(git(repo, "rev-parse", "main").stdout.strip(), main_before)  # main untouched

    def test_stale_base_is_not_merged_and_worktree_kept(self):
        # If the build branch is NOT a fast-forward of the current HEAD (its base is stale — the
        # per-dispatch reset was skipped, or HEAD moved), integrate must REFUSE: keep the worktree,
        # report STALE, and never silently merge stale work onto the branch.
        repo = make_repo()
        path, branch = build_worktree(repo)
        # advance the current branch so the build branch is behind -> no fast-forward
        (Path(repo) / "other.txt").write_text("main moved on\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "main moved")
        head_before = git(repo, "rev-parse", "HEAD").stdout.strip()
        out, _ = run_wt(repo, "integrate", path, branch)
        self.assertIn("STALE", out)
        self.assertTrue((Path(repo) / path).exists())          # kept for inspection / rebuild
        self.assertIn(branch, git(repo, "branch").stdout)      # branch kept
        self.assertFalse((Path(repo) / ".git" / "MERGE_HEAD").exists())  # no half-merge left
        self.assertEqual(git(repo, "rev-parse", "HEAD").stdout.strip(), head_before)  # branch untouched


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
