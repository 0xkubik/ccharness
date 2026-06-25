import os, sys, json, tempfile, unittest
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ccmaestro import musician

class TestMusician(unittest.TestCase):
    def _repo(self, active=None, cycle=None):
        repo = tempfile.mkdtemp()
        d = Path(repo) / ".claude" / "ccharness" / "musician"
        if active is not None or cycle is not None:
            d.mkdir(parents=True, exist_ok=True)
            state = {}
            if active is not None:
                state["active"] = active
            if cycle is not None:
                state["cycle"] = cycle
            (d / "state.json").write_text(json.dumps(state))
        return repo

    def test_active_musician_detected(self):
        self.assertTrue(musician.is_musician(self._repo(active=True)))

    def test_inactive_not_musician(self):
        self.assertFalse(musician.is_musician(self._repo(active=False)))

    def test_plain_repo_not_musician(self):
        self.assertFalse(musician.is_musician(tempfile.mkdtemp()))

    def test_none_cwd_safe(self):
        self.assertFalse(musician.is_musician(None))

    def test_cycle_count(self):
        self.assertEqual(musician.cycle_count(self._repo(active=True, cycle=5)), 5)

if __name__ == "__main__":
    unittest.main()
