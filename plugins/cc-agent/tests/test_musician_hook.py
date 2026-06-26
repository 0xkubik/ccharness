import json, os, shutil, subprocess, tempfile, unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "musician-stop.sh"
SESSION = "11111111-1111-1111-1111-111111111111"
OTHER = "22222222-2222-2222-2222-222222222222"


def nojq_env():
    """PATH with coreutils (cat, grep) symlinked but NOT jq — simulates jq-absent/coreutils-present."""
    tmpbin = tempfile.mkdtemp()
    for tool in ("cat", "grep"):
        src = shutil.which(tool)
        if src:
            os.symlink(src, os.path.join(tmpbin, tool))
    return {"PATH": tmpbin}


def run_hook(repo, stdin_obj):
    r = subprocess.run(["bash", str(HOOK)], input=json.dumps(stdin_obj),
                       cwd=repo, capture_output=True, text=True)
    return r.returncode, r.stdout


def repo_with(state=None):
    repo = tempfile.mkdtemp()
    if state is not None:
        d = Path(repo) / ".claude" / "ccharness" / "musician"
        d.mkdir(parents=True, exist_ok=True)
        (d / "state.json").write_text(json.dumps(state))
    return repo


class TestMusicianHook(unittest.TestCase):
    def test_no_state_allows_stop(self):
        rc, out = run_hook(repo_with(), {"session_id": SESSION})
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_active_same_session_blocks(self):
        repo = repo_with({"active": True, "session_id": SESSION,
                          "cycle": 2, "entry": "task"})
        rc, out = run_hook(repo, {"session_id": SESSION})
        self.assertEqual(rc, 0)
        self.assertIn('"decision"', out)
        self.assertIn("block", out)

    def test_inactive_allows_stop(self):
        # active:false — the musician self-closed (achieved/declined/gave-up/capped).
        repo = repo_with({"active": False, "session_id": SESSION})
        rc, out = run_hook(repo, {"session_id": SESSION})
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_different_session_allows_stop(self):
        repo = repo_with({"active": True, "session_id": SESSION})
        rc, out = run_hook(repo, {"session_id": OTHER})
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_jq_unavailable_still_blocks(self):
        # With jq off PATH the hook must STILL block (fail closed) via the printf fallback.
        repo = repo_with({"active": True, "session_id": SESSION})
        r = subprocess.run(["/bin/bash", str(HOOK)],
                           input=json.dumps({"session_id": SESSION}),
                           cwd=repo, capture_output=True, text=True,
                           env={"PATH": "/nonexistent"})
        self.assertEqual(r.returncode, 0)
        self.assertIn('"decision"', r.stdout)
        self.assertIn("block", r.stdout)

    def test_nojq_active_false_releases(self):
        # jq absent (coreutils present): active:false must STILL release via the grep fallback.
        repo = repo_with({"active": False, "session_id": SESSION})
        r = subprocess.run(["/bin/bash", str(HOOK)], input=json.dumps({"session_id": SESSION}),
                           cwd=repo, capture_output=True, text=True, env=nojq_env())
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")

    def test_nojq_active_true_blocks(self):
        # jq absent (coreutils present): an active musician still blocks (fail closed).
        repo = repo_with({"active": True, "session_id": SESSION})
        r = subprocess.run(["/bin/bash", str(HOOK)], input=json.dumps({"session_id": SESSION}),
                           cwd=repo, capture_output=True, text=True, env=nojq_env())
        self.assertIn("block", r.stdout)

    def test_awaiting_releases_stop(self):
        # An active loop SUSPENDED on async work (awaiting set) must RELEASE, not re-feed —
        # so the terminal yields and no idle cycle is wasted.
        repo = repo_with({"active": True, "session_id": SESSION, "cycle": 2, "entry": "task",
                          "awaiting": {"what": "scan task xyz", "since": "2026-06-25T13:38:00Z"}})
        rc, out = run_hook(repo, {"session_id": SESSION})
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_awaiting_null_still_blocks(self):
        # awaiting:null is the normal state — must still re-feed (block).
        repo = repo_with({"active": True, "session_id": SESSION, "cycle": 2,
                          "entry": "task", "awaiting": None})
        rc, out = run_hook(repo, {"session_id": SESSION})
        self.assertIn("block", out)

    def test_awaiting_releases_without_jq(self):
        # jq absent (coreutils present): the awaiting release must still fire via the grep fallback.
        repo = repo_with({"active": True, "session_id": SESSION, "cycle": 2, "entry": "task",
                          "awaiting": {"what": "scan", "since": "2026-06-25T13:38:00Z"}})
        r = subprocess.run(["/bin/bash", str(HOOK)], input=json.dumps({"session_id": SESSION}),
                           cwd=repo, capture_output=True, text=True, env=nojq_env())
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")


class TestMusicianFlags(unittest.TestCase):
    """The musician carries --ultracode only. There is NO spend flag (it is bounded by design)."""

    def test_baseline_has_no_ultracode(self):
        repo = repo_with({"active": True, "session_id": SESSION, "cycle": 1, "entry": "task"})
        rc, out = run_hook(repo, {"session_id": SESSION})
        self.assertIn("block", out)
        self.assertNotIn("ULTRACODE", out)

    def test_no_spend_in_refeed(self):
        # spend mode is gone — the re-feed must never inject it. (Note: "suspend" is fine —
        # that is the awaiting mechanism; we forbid the spend-MODE tokens specifically.)
        repo = repo_with({"active": True, "session_id": SESSION, "cycle": 1, "entry": "open"})
        rc, out = run_hook(repo, {"session_id": SESSION})
        self.assertNotIn("SPEND MODE", out.upper())
        self.assertNotIn("spend-session", out.lower())

    def test_ultracode_injects_block(self):
        repo = repo_with({"active": True, "session_id": SESSION, "cycle": 1,
                          "entry": "task", "ultracode": True})
        rc, out = run_hook(repo, {"session_id": SESSION})
        self.assertIn("ULTRACODE", out)
        self.assertIn("Workflow", out)

    def test_ultracode_survives_without_jq(self):
        repo = repo_with({"active": True, "session_id": SESSION, "cycle": 1,
                          "entry": "task", "ultracode": True})
        r = subprocess.run(["/bin/bash", str(HOOK)], input=json.dumps({"session_id": SESSION}),
                           cwd=repo, capture_output=True, text=True, env=nojq_env())
        self.assertIn("ULTRACODE", r.stdout)


class TestMusicianRefeedContent(unittest.TestCase):
    """The re-feed must carry the musician's load-bearing behaviours."""

    def _refeed(self):
        repo = repo_with({"active": True, "session_id": SESSION, "cycle": 1, "entry": "task"})
        _, out = run_hook(repo, {"session_id": SESSION})
        return out

    def test_refeed_mentions_brain_and_decline(self):
        out = self._refeed()
        self.assertIn("BRAIN", out)
        self.assertIn("declined", out)

    def test_refeed_done_check_leads_build(self):
        out = self._refeed()
        self.assertIn("done_when", out)
        self.assertIn("DONE-CHECK", out)

    def test_refeed_writes_awareness_note_on_close(self):
        # The close-write must live in the re-fed checklist, not only the SKILL: most closes run
        # under the hook, so a write absent here would silently skip — worse than no memory.
        out = self._refeed()
        self.assertIn("git notes append", out)


if __name__ == "__main__":
    unittest.main()
