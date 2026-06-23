import os, sys, json, unittest
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ccmaestro import render

NOW = datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc)
CFG = {"stall_min": 5, "tool_stall_min": 20, "loop_n": 4, "loop_window": 8, "token_budget": 0}

def make_entry(sid, status="busy", cwd="/tmp/x"):
    return {"sessionId": sid, "launched_by_ccmaestro": False,
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

    def test_render_table_has_headers(self):
        out = render.render_table([{"id": "a", "sessionId": "s1", "kind": "task", "tokens": 5,
                                    "last_activity": NOW, "verdict": "ok", "reason": "", "cwd": "/x",
                                    "name": "n", "autopilot": False}])
        self.assertIn("VERDICT", out)
        self.assertIn("TOKENS", out)

if __name__ == "__main__":
    unittest.main()
