import os, sys, unittest
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ccmaestro import watchdog

NOW = datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc)
CFG = {"stall_min": 5, "tool_stall_min": 20, "loop_n": 4, "loop_window": 8, "token_budget": 1000, "autopilot_stall_min": 30}

def summary(**kw):
    base = {"total_tokens": 0, "last_activity": NOW, "tool_calls": [], "pending_tool": False}
    base.update(kw); return base

def entry(native=True, launched=False):
    return {"native": {"status": "busy"} if native else None, "launched_by_ccmaestro": launched}

class TestWatchdog(unittest.TestCase):
    def test_healthy_is_ok(self):
        v = watchdog.verdict(summary(), entry(), CFG, NOW)
        self.assertEqual(v["status"], "ok")

    def test_died_when_launched_and_absent_from_native(self):
        v = watchdog.verdict(summary(), entry(native=False, launched=True), CFG, NOW)
        self.assertEqual(v["status"], "died")

    def test_looping_on_repeated_identical_calls(self):
        calls = [("Bash", '{"command":"ls"}')] * 4
        v = watchdog.verdict(summary(tool_calls=calls), entry(), CFG, NOW)
        self.assertEqual(v["status"], "looping")

    def test_not_looping_when_calls_differ(self):
        calls = [("Bash", str(i)) for i in range(6)]
        self.assertIsNone(watchdog.looping(calls, 4, 8))

    def test_over_budget(self):
        v = watchdog.verdict(summary(total_tokens=2000), entry(), CFG, NOW)
        self.assertEqual(v["status"], "over-budget")

    def test_token_budget_zero_disables(self):
        cfg = dict(CFG, token_budget=0)
        v = watchdog.verdict(summary(total_tokens=9_000_000), entry(), cfg, NOW)
        self.assertEqual(v["status"], "ok")

    def test_stalled_when_idle_past_limit(self):
        s = summary(last_activity=NOW - timedelta(minutes=9))
        v = watchdog.verdict(s, entry(), CFG, NOW)
        self.assertEqual(v["status"], "stalled")

    def test_pending_tool_uses_higher_threshold(self):
        s = summary(last_activity=NOW - timedelta(minutes=9), pending_tool=True)
        v = watchdog.verdict(s, entry(), CFG, NOW)  # 9m < tool_stall_min(20) -> not stalled
        self.assertEqual(v["status"], "ok")

    def test_looping_beats_stalled(self):
        s = summary(last_activity=NOW - timedelta(minutes=99), tool_calls=[("Bash", "x")] * 4)
        v = watchdog.verdict(s, entry(), CFG, NOW)
        self.assertEqual(v["status"], "looping")

    def test_autopilot_idle_under_threshold_is_ok(self):
        s = summary(last_activity=NOW - timedelta(minutes=10))
        e = {**entry(), "is_autopilot": True}
        v = watchdog.verdict(s, e, CFG, NOW)
        self.assertEqual(v["status"], "ok")

    def test_autopilot_idle_over_threshold_is_stalled(self):
        s = summary(last_activity=NOW - timedelta(minutes=40))
        e = {**entry(), "is_autopilot": True}
        v = watchdog.verdict(s, e, CFG, NOW)
        self.assertEqual(v["status"], "stalled")

    def test_completed_exit_zero_is_done(self):
        e = {"native": None, "launched_by_ccmaestro": True, "completed_exit": 0}
        self.assertEqual(watchdog.verdict(summary(), e, CFG, NOW)["status"], "done")

    def test_completed_exit_nonzero_is_crashed(self):
        e = {"native": None, "launched_by_ccmaestro": True, "completed_exit": 2}
        self.assertEqual(watchdog.verdict(summary(), e, CFG, NOW)["status"], "crashed")

    def test_gone_without_result_is_died(self):
        e = {"native": None, "launched_by_ccmaestro": True, "completed_exit": None}
        self.assertEqual(watchdog.verdict(summary(), e, CFG, NOW)["status"], "died")

if __name__ == "__main__":
    unittest.main()
