import json, os, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin" / "musicians"
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
    (run / "blocked.jsonl").write_text("")
    (run / "live.log").write_text("a tool call\n")
    (base / "by-session").mkdir(parents=True, exist_ok=True)
    (base / "by-session" / session).write_text(RUN_ID)
    return repo


def run_bin(repo, *args, env_extra=None, strip_env=()):
    env = dict(os.environ)
    for k in strip_env:
        env.pop(k, None)
    if env_extra:
        env.update(env_extra)
    r = subprocess.run(["/bin/bash", str(BIN), *args], cwd=repo,
                       capture_output=True, text=True, env=env)
    return r.returncode, r.stdout, r.stderr


class TestMusicians(unittest.TestCase):
    def test_nonstop_on_writes_marker_the_hook_reads(self):
        # The integration pin: `musicians <id> nonstop on` arms exactly the file the hook gates on.
        repo = repo_with_run()
        rc, out, _ = run_bin(repo, "20260627", "nonstop", "on")  # by unique prefix
        self.assertEqual(rc, 0)
        marker = Path(repo) / NS_MARKER
        self.assertTrue(marker.exists(), "nonstop marker not written where the hook reads it")
        self.assertTrue(json.loads(marker.read_text())["on"])

    def test_nonstop_off_removes_marker_current_session(self):
        repo = repo_with_run()
        run_bin(repo, RUN_ID, "nonstop", "on")
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

    def test_ls_shows_run_and_nonstop_state(self):
        repo = repo_with_run()
        _, out, _ = run_bin(repo, "ls")
        self.assertIn(RUN_ID, out)
        self.assertIn("achieved", out)
        self.assertRegex(out, r"\boff\b")
        run_bin(repo, RUN_ID, "nonstop", "on")
        _, out2, _ = run_bin(repo, "ls")
        self.assertRegex(out2, r"\bon\b")

    def test_info_shows_fields(self):
        repo = repo_with_run()
        _, out, _ = run_bin(repo, RUN_ID, "info")
        for token in (RUN_ID, "achieved", SESSION, "harden the thing"):
            self.assertIn(token, out)
        # blocked count renders as a single 0 (empty blocked.jsonl must not print "0\n0").
        self.assertRegex(out, r"(?m)^blocked\s+0$")
        self.assertNotIn("0\n0", out)

    def test_unknown_id_errors(self):
        repo = repo_with_run()
        rc, _, err = run_bin(repo, "nope-not-a-run", "info")
        self.assertEqual(rc, 2)
        self.assertIn("no run matches", err)

    def test_watch_no_runs_is_friendly(self):
        repo = tempfile.mkdtemp()
        rc, out, _ = run_bin(repo, "watch")
        self.assertEqual(rc, 0)
        self.assertIn("No musician live feed", out)


if __name__ == "__main__":
    unittest.main()
