import json, os, shutil, subprocess, tempfile, unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "autopilot-stop.sh"
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


def repo_with(autopilot=None, semipilot=None):
    repo = tempfile.mkdtemp()
    base = Path(repo) / ".claude" / "ccharness"
    if autopilot is not None:
        (base / "autopilot").mkdir(parents=True, exist_ok=True)
        (base / "autopilot" / "state.json").write_text(json.dumps(autopilot))
    if semipilot is not None:
        (base / "semipilot").mkdir(parents=True, exist_ok=True)
        (base / "semipilot" / "state.json").write_text(json.dumps(semipilot))
    return repo


class TestAutopilotHook(unittest.TestCase):
    def test_no_state_allows_stop(self):
        rc, out = run_hook(repo_with(), {"session_id": SESSION})
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_semipilot_active_yields(self):
        # autopilot active AND a semipilot in flight → autopilot hook must YIELD
        repo = repo_with(
            autopilot={"active": True, "session_id": SESSION, "current_milestone": "M1"},
            semipilot={"active": True, "session_id": SESSION})
        rc, out = run_hook(repo, {"session_id": SESSION})
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_gap_blocks_metastep(self):
        # autopilot active, no semipilot in flight → re-feed the meta-step
        repo = repo_with(
            autopilot={"active": True, "session_id": SESSION, "current_milestone": "M1"},
            semipilot={"active": False, "session_id": SESSION})
        rc, out = run_hook(repo, {"session_id": SESSION})
        self.assertEqual(rc, 0)
        self.assertIn("block", out)
        self.assertIn("meta-step", out)
        d = json.loads(out)
        self.assertEqual(d["decision"], "block")

    def test_gap_no_semipilot_file_blocks(self):
        repo = repo_with(autopilot={"active": True, "session_id": SESSION, "current_milestone": "M1"})
        rc, out = run_hook(repo, {"session_id": SESSION})
        self.assertEqual(rc, 0)
        self.assertIn("block", out)

    def test_autopilot_inactive_allows(self):
        repo = repo_with(autopilot={"active": False, "session_id": SESSION})
        rc, out = run_hook(repo, {"session_id": SESSION})
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_different_session_allows(self):
        repo = repo_with(autopilot={"active": True, "session_id": SESSION, "current_milestone": "M1"})
        rc, out = run_hook(repo, {"session_id": OTHER})
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_jq_unavailable_still_blocks(self):
        # autopilot active, no semipilot in flight, jq off PATH -> must STILL block via fallback.
        repo = repo_with(autopilot={"active": True, "session_id": SESSION,
                                    "current_milestone": "M1"})
        r = subprocess.run(["/bin/bash", str(HOOK)],
                           input=json.dumps({"session_id": SESSION}),
                           cwd=repo, capture_output=True, text=True,
                           env={"PATH": "/nonexistent"})
        self.assertEqual(r.returncode, 0)
        self.assertIn('"decision"', r.stdout)
        self.assertIn("block", r.stdout)

    def test_nojq_partition_yields_when_semipilot_active(self):
        # THE fix: jq absent (coreutils present), a semipilot in flight -> autopilot must YIELD,
        # so the two hooks don't double-block. (Pairs with semipilot's test_nojq_active_true_blocks
        # to prove exactly-one-blocks without jq.)
        repo = repo_with(autopilot={"active": True, "session_id": SESSION, "current_milestone": "M1"},
                         semipilot={"active": True, "session_id": SESSION})
        r = subprocess.run(["/bin/bash", str(HOOK)], input=json.dumps({"session_id": SESSION}),
                           cwd=repo, capture_output=True, text=True, env=nojq_env())
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")

    def test_nojq_hardstop_releases(self):
        # autopilot active:false (hard-stop or cancel) must release without jq.
        repo = repo_with(autopilot={"active": False, "session_id": SESSION})
        r = subprocess.run(["/bin/bash", str(HOOK)], input=json.dumps({"session_id": SESSION}),
                           cwd=repo, capture_output=True, text=True, env=nojq_env())
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
