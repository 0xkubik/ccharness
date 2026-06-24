import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ccmaestro import spend

# A week-long --spend-weekly supervisor relaunches a `claude -p /autopilot --spend-session`
# session each time it dies, classifying WHY it died from two fully-knowable signals:
#   - is autopilot/state.json still active?  (gone/inactive => user ran /autopilot-cancel)
#   - did the session run a while then die, or die fast?  (sustained => presumed limit; fast => crash)
# spend_verdict is a PURE function (no I/O), exactly like watchdog.verdict.

CFG = {
    "fast_death_s": 120,     # a session that dies under this ran too briefly to be a limit hit -> crash
    "max_fast_deaths": 4,    # this many consecutive fast deaths -> give up (the loop is broken)
    "horizon_s": 604800,     # 7 days wall clock -> the weekly stop
    "limit_wait_s": 1800,    # blind probe interval after a presumed limit hit
    "crash_base_s": 60,      # crash backoff base
    "crash_max_s": 900,      # crash backoff ceiling
}


def verdict(**kw):
    base = dict(state_active=True, run_duration_s=3600, fast_death_streak=0, elapsed_total_s=0, config=CFG)
    base.update(kw)
    return spend.spend_verdict(**base)


class TestSpendVerdict(unittest.TestCase):
    def test_cancelled_when_state_inactive(self):
        # autopilot/state.json gone or active:false => /autopilot-cancel => STOP the supervisor.
        self.assertEqual(verdict(state_active=False)["action"], "STOP")

    def test_cancel_beats_everything(self):
        # Even a healthy sustained run within the horizon must STOP if the user cancelled.
        v = verdict(state_active=False, run_duration_s=99999, elapsed_total_s=0)
        self.assertEqual(v["action"], "STOP")

    def test_weekly_horizon_stops(self):
        v = verdict(elapsed_total_s=CFG["horizon_s"] + 1)
        self.assertEqual(v["action"], "STOP")

    def test_sustained_death_is_presumed_limit_relaunch(self):
        v = verdict(run_duration_s=4000, fast_death_streak=0)
        self.assertEqual(v["action"], "RELAUNCH")

    def test_fast_death_backs_off(self):
        v = verdict(run_duration_s=10, fast_death_streak=0)
        self.assertEqual(v["action"], "BACKOFF")

    def test_fast_death_streak_hits_cap_gives_up(self):
        # 3 prior fast deaths + this one = 4 = max_fast_deaths -> GIVE_UP.
        v = verdict(run_duration_s=10, fast_death_streak=3)
        self.assertEqual(v["action"], "GIVE_UP")

    def test_horizon_beats_death_classification(self):
        v = verdict(run_duration_s=10, fast_death_streak=0, elapsed_total_s=CFG["horizon_s"] + 1)
        self.assertEqual(v["action"], "STOP")

    def test_sustained_run_resets_streak_via_relaunch(self):
        # A sustained run should relaunch even if there were earlier fast deaths
        # (the wrapper resets the streak on RELAUNCH).
        v = verdict(run_duration_s=4000, fast_death_streak=3)
        self.assertEqual(v["action"], "RELAUNCH")


class TestSpendWait(unittest.TestCase):
    def test_relaunch_waits_limit_interval(self):
        self.assertEqual(spend.next_wait_s("RELAUNCH", 0, CFG), CFG["limit_wait_s"])

    def test_backoff_is_exponential(self):
        self.assertEqual(spend.next_wait_s("BACKOFF", 0, CFG), 60)
        self.assertEqual(spend.next_wait_s("BACKOFF", 1, CFG), 120)
        self.assertEqual(spend.next_wait_s("BACKOFF", 2, CFG), 240)

    def test_backoff_caps(self):
        self.assertEqual(spend.next_wait_s("BACKOFF", 99, CFG), CFG["crash_max_s"])

    def test_stop_and_giveup_wait_zero(self):
        self.assertEqual(spend.next_wait_s("STOP", 0, CFG), 0)
        self.assertEqual(spend.next_wait_s("GIVE_UP", 5, CFG), 0)


import json, tempfile
from pathlib import Path


class _Clock:
    """Monotonic fake: only the injected _launch advances it (sleep is a no-op in tests)."""
    def __init__(self): self.t = 0.0
    def __call__(self): return self.t
    def advance(self, dt): self.t += dt


def _repo_with_active_autopilot():
    repo = tempfile.mkdtemp()
    d = Path(repo) / ".claude" / "ccharness" / "autopilot"
    d.mkdir(parents=True, exist_ok=True)
    (d / "state.json").write_text(json.dumps({"active": True, "session_id": "x"}))
    return repo


class TestSpendLoop(unittest.TestCase):
    """The thin side-effecting wrapper, exercised with injected launch/clock/sleep (no subprocess)."""

    def test_cancel_during_session_stops_supervisor(self):
        # THE safety case: user runs /autopilot-cancel (removes state.json) -> supervisor must STOP,
        # never relaunch. We simulate cancel by deleting the state file inside the fake launch.
        repo = _repo_with_active_autopilot()
        clock = _Clock()
        slept = []

        def fake_launch(argv, cwd):
            clock.advance(4000)  # ran a sustained stretch...
            (Path(repo) / ".claude" / "ccharness" / "autopilot" / "state.json").unlink()  # ...then cancelled
            return 0

        res = spend.run_spend_weekly("/autopilot --spend-session", repo=repo,
                                     _launch=fake_launch, _now=clock, _sleep=slept.append, log=lambda *a: None)
        self.assertEqual(res["launches"], 1)
        self.assertEqual(res["final"]["action"], "STOP")
        self.assertEqual(slept, [])  # never slept to relaunch

    def test_sustained_runs_relaunch_until_weekly_horizon(self):
        repo = _repo_with_active_autopilot()
        clock = _Clock()

        def fake_launch(argv, cwd):
            clock.advance(40000)  # sustained run (>> fast_death_s); state stays active
            return 0

        res = spend.run_spend_weekly("/autopilot --spend-session", repo=repo, horizon_days=1,
                                     _launch=fake_launch, _now=clock, _sleep=lambda s: None, log=lambda *a: None)
        # 40000s/launch, horizon 86400s -> elapsed crosses on the 3rd launch.
        self.assertEqual(res["launches"], 3)
        self.assertEqual(res["final"]["action"], "STOP")
        self.assertIn("horizon", res["final"]["reason"])

    def test_repeated_fast_deaths_give_up(self):
        repo = _repo_with_active_autopilot()
        clock = _Clock()

        def fake_launch(argv, cwd):
            clock.advance(10)  # fast death every time (< fast_death_s=120), state stays active
            return 1

        res = spend.run_spend_weekly("/autopilot --spend-session", repo=repo,
                                     _launch=fake_launch, _now=clock, _sleep=lambda s: None, log=lambda *a: None)
        self.assertEqual(res["launches"], 4)  # default max_fast_deaths
        self.assertEqual(res["final"]["action"], "GIVE_UP")


class TestSpendCli(unittest.TestCase):
    def test_parser_wires_spend_weekly(self):
        from ccmaestro import cli
        args = cli.build_parser().parse_args(["spend-weekly", "polish the UI", "--horizon-days", "3"])
        self.assertEqual(args.focus, "polish the UI")
        self.assertEqual(args.horizon_days, 3.0)
        self.assertTrue(callable(args.func))

    def test_dispatch_builds_spend_session_task(self):
        from ccmaestro import cli, spend
        captured = {}

        def fake_run(task, **kw):
            captured["task"] = task; captured.update(kw); return {"final": {"action": "STOP"}}

        orig = spend.run_spend_weekly
        spend.run_spend_weekly = fake_run
        try:
            args = cli.build_parser().parse_args(["spend-weekly", "ship M3", "--yolo"])
            args.func(args)
        finally:
            spend.run_spend_weekly = orig
        self.assertEqual(captured["task"], "/autopilot --spend-session ship M3")
        self.assertTrue(captured["yolo"])


if __name__ == "__main__":
    unittest.main()
