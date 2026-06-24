import json, os, shutil, subprocess, tempfile, unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "semipilot-stop.sh"
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
        d = Path(repo) / ".claude" / "ccharness" / "semipilot"
        d.mkdir(parents=True, exist_ok=True)
        (d / "state.json").write_text(json.dumps(state))
    return repo


class TestSemipilotHook(unittest.TestCase):
    def test_no_state_allows_stop(self):
        rc, out = run_hook(repo_with(), {"session_id": SESSION})
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_active_same_session_blocks(self):
        repo = repo_with({"active": True, "session_id": SESSION,
                          "cycle": 2, "target_milestone": "M2"})
        rc, out = run_hook(repo, {"session_id": SESSION})
        self.assertEqual(rc, 0)
        self.assertIn('"decision"', out)
        self.assertIn("block", out)

    def test_inactive_allows_stop(self):
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
        # The semipilot half of the no-jq partition: an active semipilot still blocks.
        repo = repo_with({"active": True, "session_id": SESSION})
        r = subprocess.run(["/bin/bash", str(HOOK)], input=json.dumps({"session_id": SESSION}),
                           cwd=repo, capture_output=True, text=True, env=nojq_env())
        self.assertIn("block", r.stdout)


class TestSemipilotFlags(unittest.TestCase):
    """semipilot carries --ultracode only (spend is autopilot-only, lives in cc-maestro for weekly)."""

    def test_baseline_has_no_ultracode(self):
        repo = repo_with({"active": True, "session_id": SESSION, "cycle": 1, "target_milestone": "M2"})
        rc, out = run_hook(repo, {"session_id": SESSION})
        self.assertIn("block", out)
        self.assertNotIn("ULTRACODE", out)

    def test_ultracode_injects_block(self):
        repo = repo_with({"active": True, "session_id": SESSION, "cycle": 1,
                          "target_milestone": "M2", "ultracode": True})
        rc, out = run_hook(repo, {"session_id": SESSION})
        self.assertIn("ULTRACODE", out)
        self.assertIn("Workflow", out)

    def test_ultracode_survives_without_jq(self):
        repo = repo_with({"active": True, "session_id": SESSION, "cycle": 1,
                          "target_milestone": "M2", "ultracode": True})
        r = subprocess.run(["/bin/bash", str(HOOK)], input=json.dumps({"session_id": SESSION}),
                           cwd=repo, capture_output=True, text=True, env=nojq_env())
        self.assertIn("ULTRACODE", r.stdout)


if __name__ == "__main__":
    unittest.main()
