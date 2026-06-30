import os, sys, json, tempfile, unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ccconductor import render

NOW = datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc)
CFG = {"stall_min": 5, "tool_stall_min": 20, "musician_stall_min": 30,
       "loop_n": 4, "loop_window": 8, "token_budget": 0}

def make_entry(sid, status="busy", cwd="/tmp/x"):
    return {"sessionId": sid, "launched_by_ccconductorctl": False,
            "native": {"sessionId": sid, "status": status, "kind": "interactive", "cwd": cwd, "name": "n"},
            "meta": None}

class TestRender(unittest.TestCase):
    def test_build_rows_includes_tokens_and_verdict(self):
        def summarizer(sid):
            return {"total_tokens": 4200, "last_activity": NOW, "tool_calls": [], "pending_tool": False}
        rows = render.build_rows([make_entry("s1")], NOW, summarizer=summarizer, config=CFG)
        self.assertEqual(rows[0]["tokens"], 4200)
        self.assertEqual(rows[0]["verdict"], "ok")
        self.assertEqual(rows[0]["sessionId"], "s1")

    def test_build_rows_flags_stalled(self):
        def summarizer(sid):
            return {"total_tokens": 1, "last_activity": NOW - timedelta(minutes=30), "tool_calls": [], "pending_tool": False}
        rows = render.build_rows([make_entry("s1")], NOW, summarizer=summarizer, config=CFG)
        self.assertEqual(rows[0]["verdict"], "stalled")

    def test_render_json_is_valid(self):
        rows = [{"id": "a", "verdict": "ok", "tokens": 1}]
        self.assertEqual(json.loads(render.render_json(rows))[0]["verdict"], "ok")

    def test_musician_row_enriched(self):
        repo = tempfile.mkdtemp()
        run = Path(repo) / ".claude" / "ccharness" / "musician" / "runs" / "r1"
        run.mkdir(parents=True)
        (run / "state.json").write_text(json.dumps(
            {"active": True, "run_id": "r1", "input": "do X",
             "tasks": [{"id": 1, "subject": "build the X widget", "status": "completed"},
                       {"id": 2, "subject": "wire X into the page", "status": "in_progress"},
                       {"id": 3, "subject": "verify X works", "status": "pending"}]}))
        (run / "live.log").write_text("12:00 ▶ cc-script:do\n")
        bys = Path(repo) / ".claude" / "ccharness" / "musician" / "by-session"
        bys.mkdir(parents=True)
        (bys / "s1").write_text("r1")

        def summarizer(sid):
            return {"total_tokens": 10, "last_activity": NOW, "tool_calls": [], "pending_tool": False}
        rows = render.build_rows([make_entry("s1", cwd=repo)], NOW, summarizer=summarizer, config=CFG)
        self.assertEqual(rows[0]["kind"], "musician")
        self.assertIsNotNone(rows[0]["musician"])
        self.assertEqual((rows[0]["musician"]["done"], rows[0]["musician"]["total"]), (1, 3))
        out = render.render_table(rows, NOW)
        self.assertIn("1/3 tasks", out)             # progress, not a cycle count
        self.assertIn("doing:", out)
        self.assertIn("wire X into the page", out)  # the current (in_progress) task
        # the detail view shows what was asked + the live feed
        detail = render.render_musician_detail(rows[0], NOW)
        self.assertIn("do X", detail)
        self.assertIn("cc-script:do", detail)

    def test_render_table_has_headers(self):
        out = render.render_table([{"id": "a", "sessionId": "s1", "kind": "task", "tokens": 5,
                                    "last_activity": NOW, "verdict": "ok", "reason": "", "cwd": "/x",
                                    "name": "n", "musician": False}])
        self.assertIn("VERDICT", out)
        self.assertIn("TOKENS", out)

if __name__ == "__main__":
    unittest.main()
