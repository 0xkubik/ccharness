import os, sys, json, tempfile, unittest
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ccmaestro import autopilot

class TestAutopilot(unittest.TestCase):
    def _repo(self, active=None, cycles=None):
        repo = tempfile.mkdtemp()
        ap = Path(repo) / ".claude" / "ccharness" / "autopilot"
        if active is not None:
            ap.mkdir(parents=True, exist_ok=True)
            (ap / "state.json").write_text(json.dumps({"active": active, "cycle": 3}))
        if cycles is not None:
            ap.mkdir(parents=True, exist_ok=True)
            (ap / "log.jsonl").write_text("\n".join("{}" for _ in range(cycles)) + "\n")
        return repo

    def test_active_autopilot_detected(self):
        self.assertTrue(autopilot.is_autopilot(self._repo(active=True)))

    def test_inactive_not_autopilot(self):
        self.assertFalse(autopilot.is_autopilot(self._repo(active=False)))

    def test_plain_repo_not_autopilot(self):
        self.assertFalse(autopilot.is_autopilot(tempfile.mkdtemp()))

    def test_none_cwd_safe(self):
        self.assertFalse(autopilot.is_autopilot(None))

    def test_cycle_count(self):
        self.assertEqual(autopilot.cycle_count(self._repo(active=True, cycles=5)), 5)

if __name__ == "__main__":
    unittest.main()
