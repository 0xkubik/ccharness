import json, subprocess, tempfile, unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "musician-observe.sh"
SESSION = "11111111-1111-1111-1111-111111111111"
OTHER = "22222222-2222-2222-2222-222222222222"
RUN_ID = "20260626-120000-aaaa"


def repo_with(state=None, run_id=RUN_ID):
    """Lay out a run: runs/<run-id>/state.json + a by-session/<session_id> pointer."""
    repo = tempfile.mkdtemp()
    if state is not None:
        base = Path(repo) / ".claude" / "ccharness" / "musician"
        (base / "runs" / run_id).mkdir(parents=True, exist_ok=True)
        (base / "runs" / run_id / "state.json").write_text(json.dumps(state))
        sid = state.get("session_id")
        if sid:
            (base / "by-session").mkdir(parents=True, exist_ok=True)
            (base / "by-session" / sid).write_text(run_id)
    return repo


def run_observe(repo, stdin_obj, mode="pre"):
    r = subprocess.run(["bash", str(HOOK), mode], input=json.dumps(stdin_obj),
                       cwd=repo, capture_output=True, text=True)
    return r.returncode, r.stdout


def live_log(repo, run_id=RUN_ID):
    p = Path(repo) / ".claude" / "ccharness" / "musician" / "runs" / run_id / "live.log"
    return p.read_text() if p.exists() else ""


class TestObserveHook(unittest.TestCase):
    def test_no_state_no_log_no_block(self):
        # No musician here → witness nothing, and crucially never block the tool.
        repo = repo_with()
        rc, out = run_observe(repo, {"session_id": SESSION, "tool_name": "Bash",
                                     "tool_input": {"command": "ls"}})
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")
        self.assertEqual(live_log(repo), "")

    def test_active_session_logs_skill(self):
        repo = repo_with({"active": True, "session_id": SESSION, "cycle": 2})
        rc, out = run_observe(repo, {"session_id": SESSION, "tool_name": "Skill",
                                     "tool_input": {"skill": "cc-funnel:how-to-do"}})
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")  # a PreToolUse witness must not emit a decision
        log = live_log(repo)
        self.assertIn("cc-funnel:how-to-do", log)
        self.assertIn("cycle 2", log)

    def test_active_session_logs_bash_head(self):
        repo = repo_with({"active": True, "session_id": SESSION, "cycle": 1})
        run_observe(repo, {"session_id": SESSION, "tool_name": "Bash",
                           "tool_input": {"command": "npm test --silent"}})
        self.assertIn("npm test", live_log(repo))

    def test_active_session_logs_edit_basename(self):
        repo = repo_with({"active": True, "session_id": SESSION, "cycle": 1})
        run_observe(repo, {"session_id": SESSION, "tool_name": "Edit",
                           "tool_input": {"file_path": "/deep/path/SKILL.md"}})
        log = live_log(repo)
        self.assertIn("SKILL.md", log)
        self.assertNotIn("/deep/path", log)  # basename only, not the full path

    def test_inactive_no_log(self):
        repo = repo_with({"active": False, "session_id": SESSION})
        run_observe(repo, {"session_id": SESSION, "tool_name": "Bash",
                           "tool_input": {"command": "ls"}})
        self.assertEqual(live_log(repo), "")

    def test_different_session_no_log(self):
        repo = repo_with({"active": True, "session_id": SESSION})
        run_observe(repo, {"session_id": OTHER, "tool_name": "Bash",
                           "tool_input": {"command": "ls"}})
        self.assertEqual(live_log(repo), "")

    def test_post_ticks_heavy_tool(self):
        repo = repo_with({"active": True, "session_id": SESSION, "cycle": 3})
        run_observe(repo, {"session_id": SESSION, "tool_name": "Skill",
                           "tool_input": {"skill": "cc-funnel:do"}}, mode="post")
        log = live_log(repo)
        self.assertIn("cc-funnel:do", log)
        self.assertIn("✓", log)  # ✓ completion tick

    def test_post_silent_for_light_tool(self):
        # Light post: a finished Read/Edit should not double the feed with a tick.
        repo = repo_with({"active": True, "session_id": SESSION, "cycle": 3})
        run_observe(repo, {"session_id": SESSION, "tool_name": "Read",
                           "tool_input": {"file_path": "/x/y.py"}}, mode="post")
        self.assertEqual(live_log(repo), "")

    def test_never_blocks_active(self):
        repo = repo_with({"active": True, "session_id": SESSION, "cycle": 1})
        rc, out = run_observe(repo, {"session_id": SESSION, "tool_name": "Edit",
                                     "tool_input": {"file_path": "/a/b.ts"}})
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")


if __name__ == "__main__":
    unittest.main()
