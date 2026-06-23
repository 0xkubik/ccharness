import json, subprocess, tempfile, unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "autopilot-stop.sh"
SESSION = "11111111-1111-1111-1111-111111111111"
OTHER = "22222222-2222-2222-2222-222222222222"


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
        _, out = run_hook(repo_with(), {"session_id": SESSION})
        self.assertEqual(out.strip(), "")

    def test_semipilot_active_yields(self):
        # autopilot active AND a semipilot in flight → autopilot hook must YIELD
        repo = repo_with(
            autopilot={"active": True, "session_id": SESSION, "current_milestone": "M1"},
            semipilot={"active": True, "session_id": SESSION})
        _, out = run_hook(repo, {"session_id": SESSION})
        self.assertEqual(out.strip(), "")

    def test_gap_blocks_metastep(self):
        # autopilot active, no semipilot in flight → re-feed the meta-step
        repo = repo_with(
            autopilot={"active": True, "session_id": SESSION, "current_milestone": "M1"},
            semipilot={"active": False, "session_id": SESSION})
        rc, out = run_hook(repo, {"session_id": SESSION})
        self.assertIn("block", out)
        self.assertIn("meta-step", out)

    def test_gap_no_semipilot_file_blocks(self):
        repo = repo_with(autopilot={"active": True, "session_id": SESSION, "current_milestone": "M1"})
        _, out = run_hook(repo, {"session_id": SESSION})
        self.assertIn("block", out)

    def test_autopilot_inactive_allows(self):
        repo = repo_with(autopilot={"active": False, "session_id": SESSION})
        _, out = run_hook(repo, {"session_id": SESSION})
        self.assertEqual(out.strip(), "")

    def test_different_session_allows(self):
        repo = repo_with(autopilot={"active": True, "session_id": SESSION, "current_milestone": "M1"})
        _, out = run_hook(repo, {"session_id": OTHER})
        self.assertEqual(out.strip(), "")


if __name__ == "__main__":
    unittest.main()
