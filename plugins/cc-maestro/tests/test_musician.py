import os, sys, json, tempfile, unittest
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ccmaestro import musician

RID = "20260626-120000-test"


class TestMusician(unittest.TestCase):
    def _repo(self, state=None, session=None, live=None, blocked=0):
        """Lay a run out the new way: runs/<rid>/state.json (+ optional pointer / live feed)."""
        repo = tempfile.mkdtemp()
        base = Path(repo) / ".claude" / "ccharness" / "musician"
        if state is not None:
            run = base / "runs" / RID
            run.mkdir(parents=True, exist_ok=True)
            (run / "state.json").write_text(json.dumps(state))
            if session:
                (base / "by-session").mkdir(parents=True, exist_ok=True)
                (base / "by-session" / session).write_text(RID)
            if live:
                (run / "live.log").write_text("\n".join(live) + "\n")
            if blocked:
                (run / "blocked.jsonl").write_text(
                    "\n".join(json.dumps({"direction": f"d{i}", "reason": "r"}) for i in range(blocked)) + "\n")
        return repo

    # --- detection (fallback scan: no session id) ---
    def test_active_musician_detected(self):
        self.assertTrue(musician.is_musician(self._repo({"active": True})))

    def test_inactive_not_musician(self):
        self.assertFalse(musician.is_musician(self._repo({"active": False})))

    def test_plain_repo_not_musician(self):
        self.assertFalse(musician.is_musician(tempfile.mkdtemp()))

    def test_none_cwd_safe(self):
        self.assertFalse(musician.is_musician(None))

    def test_cycle_count(self):
        self.assertEqual(musician.cycle_count(self._repo({"active": True, "cycle": 5})), 5)

    # --- precise resolution via the by-session pointer ---
    def test_pointer_resolution(self):
        repo = self._repo({"active": True, "cycle": 3}, session="sess-xyz")
        self.assertTrue(musician.is_musician(repo, "sess-xyz"))
        self.assertEqual(musician.cycle_count(repo, "sess-xyz"), 3)

    # --- rich info ---
    def test_musician_info_rich(self):
        repo = self._repo(
            {"active": True, "status": "working", "run_id": RID, "cycle": 4,
             "entry": "task", "ultracode": True,
             "input": "fix the flaky login test", "done_when": "test passes 10x in a row"},
            session="s1",
            live=["12:00:01 cycle 4   $ npm test", "12:00:09 cycle 4   ▶ cc-tools:do"],
            blocked=2)
        info = musician.musician_info(repo, "s1")
        self.assertEqual(info["status"], "working")
        self.assertEqual(info["input"], "fix the flaky login test")
        self.assertEqual(info["done_when"], "test passes 10x in a row")
        self.assertEqual(info["cycle"], 4)
        self.assertTrue(info["ultracode"])
        self.assertEqual(info["blocked_count"], 2)
        self.assertEqual(info["last_action"], "12:00:09 cycle 4   ▶ cc-tools:do")

    def test_info_none_when_inactive(self):
        self.assertIsNone(musician.musician_info(self._repo({"active": False})))

    def test_live_tail(self):
        repo = self._repo({"active": True}, session="s2",
                          live=[f"line {i}" for i in range(30)])
        tail = musician.live_tail(repo, "s2", n=5)
        self.assertEqual(tail, [f"line {i}" for i in range(25, 30)])

    # --- cancel (mirrors /musician-cancel) ---
    def test_cancel_run_marks_cancelled_and_drops_pointer(self):
        repo = self._repo({"active": True, "cycle": 2}, session="s-cancel")
        rd = musician.cancel_run(repo, "s-cancel")
        self.assertIsNotNone(rd)
        base = Path(repo) / ".claude" / "ccharness" / "musician"
        st = json.loads((base / "runs" / RID / "state.json").read_text())
        self.assertFalse(st["active"])                                  # hook releases
        self.assertEqual(st["status"], "cancelled")
        self.assertEqual(st["outcome"], "cancelled")
        self.assertFalse((base / "by-session" / "s-cancel").exists())   # pointer dropped
        self.assertTrue((base / "runs" / RID).exists())                 # record kept

    def test_cancel_run_none_when_no_run(self):
        self.assertIsNone(musician.cancel_run(tempfile.mkdtemp()))


if __name__ == "__main__":
    unittest.main()
