import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMI = (ROOT / "skills" / "semipilot" / "SKILL.md")


class TestSemipilotSkill(unittest.TestCase):
    def setUp(self):
        self.text = SEMI.read_text() if SEMI.exists() else ""

    def test_exists(self):
        self.assertTrue(SEMI.exists(), "semipilot SKILL.md missing")

    def test_done_check_leads(self):
        self.assertIn("DONE", self.text)
        self.assertIn("done_when", self.text)

    def test_two_exits(self):
        for token in ("achieved", "gave-up", "max_cycles", "no_progress_streak"):
            self.assertIn(token, self.text)

    def test_milestone_scoped_pick(self):
        self.assertIn("advances", self.text)
        self.assertIn("blocked.jsonl", self.text)

    def test_no_askuserquestion_under_loop(self):
        self.assertIn("AskUserQuestion", self.text)  # must mention it to forbid it

    def test_roadmap_gate(self):
        self.assertIn("chart-it", self.text)

    def test_qualified_funnel_skill_names(self):
        # The directly-invoked funnel skills must be referenced by QUALIFIED name.
        for name in ("cc-tools:point-it", "cc-tools:grill-it", "cc-tools:implement-it"):
            self.assertIn(name, self.text)

    def test_semipilot_state_path(self):
        self.assertIn(".claude/ccharness/semipilot/", self.text)


if __name__ == "__main__":
    unittest.main()
