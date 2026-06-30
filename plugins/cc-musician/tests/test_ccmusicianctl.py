import json, os, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin" / "ccmusicianctl"
ALIAS = ROOT / "bin" / "musiciansctl"
SESSION = "11111111-1111-1111-1111-111111111111"
RUN_ID = "20260627-101500-abcd"
# Where the nonstop Stop hook looks for the armed marker — the bin must write to the SAME path.
NS_MARKER = ".claude/ccharness/nonstop/by-session/" + SESSION


def repo_with_run(active=False, outcome="achieved", session=SESSION, input_="harden the thing"):
    repo = tempfile.mkdtemp()
    base = Path(repo) / ".claude" / "ccharness" / "musician"
    run = base / "runs" / RUN_ID
    run.mkdir(parents=True, exist_ok=True)
    (run / "state.json").write_text(json.dumps({
        "active": active, "status": "closed", "run_id": RUN_ID, "session_id": session,
        "entry": "task", "input": input_, "cycle": 2,
        "started_at": "2026-06-27T08:00:00Z", "outcome": outcome,
    }))
    (run / "live.log").write_text("a tool call\nanother tool call\n")
    (base / "by-session").mkdir(parents=True, exist_ok=True)
    (base / "by-session" / session).write_text(RUN_ID)
    return repo


def run_bin(repo, *args, env_extra=None, strip_env=(), bin=BIN):
    env = dict(os.environ)
    for k in strip_env:
        env.pop(k, None)
    if env_extra:
        env.update(env_extra)
    r = subprocess.run(["/bin/bash", str(bin), *args], cwd=repo,
                       capture_output=True, text=True, env=env)
    return r.returncode, r.stdout, r.stderr


class TestCcmusician(unittest.TestCase):
    # --- grammar is verb-first (info <id>, nonstop <id> on|off), unified with ccconductorctl ---

    def test_nonstop_on_writes_marker_the_hook_reads(self):
        # The integration pin: `nonstop <id> on` arms exactly the file the hook gates on.
        repo = repo_with_run()
        rc, out, _ = run_bin(repo, "nonstop", "20260627", "on")  # by unique prefix
        self.assertEqual(rc, 0)
        marker = Path(repo) / NS_MARKER
        self.assertTrue(marker.exists(), "nonstop marker not written where the hook reads it")
        self.assertTrue(json.loads(marker.read_text())["on"])

    def test_nonstop_off_removes_marker_current_session(self):
        repo = repo_with_run()
        run_bin(repo, "nonstop", RUN_ID, "on")
        rc, out, _ = run_bin(repo, "nonstop", "off", env_extra={"CLAUDE_CODE_SESSION_ID": SESSION})
        self.assertEqual(rc, 0)
        self.assertFalse((Path(repo) / NS_MARKER).exists())

    def test_no_id_without_session_env_fails_loudly(self):
        # The no-id convenience form must NOT silently no-op when the session id isn't in the env.
        repo = repo_with_run()
        rc, out, err = run_bin(repo, "nonstop", "on", strip_env=("CLAUDE_CODE_SESSION_ID",))
        self.assertEqual(rc, 2)
        self.assertIn("nonstop", (out + err).lower())
        self.assertFalse((Path(repo) / NS_MARKER).exists())

    def test_legacy_id_first_form_is_rejected(self):
        # We dropped the old id-first grammar (`<id> info`) in favour of verb-first. Pin that it's gone.
        repo = repo_with_run()
        rc, _, err = run_bin(repo, RUN_ID, "info")
        self.assertEqual(rc, 2)
        self.assertIn("unknown command", err.lower())

    def test_ls_shows_shaping_phase(self):
        # A run active in the collaborative SHAPING phase reads "shaping" (waiting on the human),
        # not "working" (autonomous) — so the fleet view doesn't mislabel a conversation as work.
        repo = tempfile.mkdtemp()
        base = Path(repo) / ".claude" / "ccharness" / "musician"
        run = base / "runs" / RUN_ID
        run.mkdir(parents=True, exist_ok=True)
        (run / "state.json").write_text(json.dumps({
            "active": True, "status": "working", "run_id": RUN_ID, "session_id": SESSION,
            "entry": "task", "phase": "shaping", "input": "discuss the idea", "cycle": 0,
            "started_at": "2026-06-27T08:00:00Z", "outcome": None,
        }))
        rc, out, _ = run_bin(repo, "ls")
        self.assertEqual(rc, 0)
        self.assertIn("shaping", out)

    def test_ls_shows_run_and_nonstop_state(self):
        repo = repo_with_run()
        _, out, _ = run_bin(repo, "ls")
        self.assertIn(RUN_ID, out)
        self.assertIn("achieved", out)
        self.assertRegex(out, r"\boff\b")
        run_bin(repo, "nonstop", RUN_ID, "on")
        _, out2, _ = run_bin(repo, "ls")
        self.assertRegex(out2, r"\bon\b")

    def test_ls_json_is_machine_readable(self):
        # `ls --json` feeds the federated conductor layer — it must emit parseable JSON with the run.
        repo = repo_with_run()
        rc, out, _ = run_bin(repo, "ls", "--json")
        self.assertEqual(rc, 0)
        rows = json.loads(out)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], RUN_ID)
        self.assertEqual(rows[0]["state"], "achieved")
        self.assertEqual(rows[0]["task"], "harden the thing")

    def test_task_progress_shown(self):
        # main's task-list progress survives the grow into ccmusicianctl: ls + info show "N/M".
        repo = tempfile.mkdtemp()
        run = Path(repo) / ".claude/ccharness/musician/runs" / RUN_ID
        run.mkdir(parents=True, exist_ok=True)
        (run / "state.json").write_text(json.dumps({
            "active": True, "run_id": RUN_ID, "session_id": SESSION, "entry": "task",
            "input": "ship it", "phase": "building", "started_at": "2026-06-27T08:00:00Z",
            "outcome": None, "tasks": [
                {"id": 1, "subject": "a", "status": "completed"},
                {"id": 2, "subject": "b", "status": "pending"},
            ],
        }))
        _, out_ls, _ = run_bin(repo, "ls")
        self.assertIn("1/2", out_ls)
        _, out_info, _ = run_bin(repo, "info", RUN_ID)
        self.assertIn("1/2", out_info)

    def test_info_shows_fields(self):
        repo = repo_with_run()
        _, out, _ = run_bin(repo, "info", RUN_ID)
        for token in (RUN_ID, "achieved", SESSION, "harden the thing"):
            self.assertIn(token, out)
        # the blocked-count line was removed with the blocked exit
        self.assertNotRegex(out, r"(?m)^blocked\b")

    def test_unknown_id_errors(self):
        repo = repo_with_run()
        rc, _, err = run_bin(repo, "info", "nope-not-a-run")
        self.assertEqual(rc, 2)
        self.assertIn("no run matches", err)

    def test_watch_no_runs_is_friendly(self):
        repo = tempfile.mkdtemp()
        rc, out, _ = run_bin(repo, "watch")
        self.assertEqual(rc, 0)
        self.assertIn("No musician live feed", out)

    # --- logs: print the tail of a run's live feed, no follow ---

    def test_logs_prints_feed(self):
        repo = repo_with_run()
        rc, out, _ = run_bin(repo, "logs", RUN_ID)
        self.assertEqual(rc, 0)
        self.assertIn("a tool call", out)
        self.assertIn("another tool call", out)

    def test_logs_tail_limits_lines(self):
        repo = repo_with_run()
        rc, out, _ = run_bin(repo, "logs", RUN_ID, "--tail", "1")
        self.assertEqual(rc, 0)
        self.assertIn("another tool call", out)
        self.assertNotIn("a tool call\n", out)

    def test_logs_unknown_id_errors(self):
        repo = repo_with_run()
        rc, _, err = run_bin(repo, "logs", "nope")
        self.assertEqual(rc, 2)
        self.assertIn("no run matches", err)

    # --- stop: soft cancel, the same brake as /musician-cancel but keyed by id from the shell ---

    def test_stop_cancels_run_and_frees_the_hook(self):
        repo = repo_with_run(active=True, outcome=None)
        rc, out, _ = run_bin(repo, "stop", RUN_ID)
        self.assertEqual(rc, 0)
        st = json.loads((Path(repo) / ".claude/ccharness/musician/runs" / RUN_ID / "state.json").read_text())
        self.assertFalse(st["active"])
        self.assertEqual(st["outcome"], "cancelled")
        # the pointer is gone, so the Stop hook (and nonstop) release for that session
        self.assertFalse((Path(repo) / ".claude/ccharness/musician/by-session" / SESSION).exists())

    def test_stop_unknown_id_errors(self):
        repo = repo_with_run()
        rc, _, err = run_bin(repo, "stop", "nope")
        self.assertEqual(rc, 2)
        self.assertIn("no run matches", err)

    # --- start: launch an autonomous musician on the current repo, detached ---

    def test_start_builds_autonomous_launch(self):
        # start spawns `claude -p "/musician --auto <task>"` with bypass perms, recording the exact
        # command it launched. We stub the launcher so no real agent spawns in the test.
        repo = tempfile.mkdtemp()
        rc, out, err = run_bin(repo, "start", "build the thing",
                               env_extra={"CCMUSICIAN_CLAUDE": "true"})
        self.assertEqual(rc, 0, err)
        spawn = Path(repo) / ".claude/ccharness/musician/spawn"
        cmds = list(spawn.glob("*.cmd"))
        self.assertEqual(len(cmds), 1, "start must record the launched command")
        rec = cmds[0].read_text()
        self.assertIn("/musician --auto build the thing", rec)
        self.assertIn("bypassPermissions", rec)
        self.assertIn("--session-id", rec)

    def test_start_requires_a_task(self):
        repo = tempfile.mkdtemp()
        rc, _, err = run_bin(repo, "start", env_extra={"CCMUSICIAN_CLAUDE": "true"})
        self.assertEqual(rc, 2)
        self.assertIn("task", err.lower())

    # --- musicians stays as a thin alias for ccmusicianctl (name absorbed, F4) ---

    def test_musicians_alias_delegates(self):
        self.assertTrue(ALIAS.exists(), "musicians alias must remain")
        repo = repo_with_run()
        rc, out, _ = run_bin(repo, "ls", bin=ALIAS)
        self.assertEqual(rc, 0)
        self.assertIn(RUN_ID, out)


if __name__ == "__main__":
    unittest.main()
