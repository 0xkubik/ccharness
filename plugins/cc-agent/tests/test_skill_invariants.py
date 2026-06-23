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

    def test_frontier_aware_target(self):
        # Under a layered roadmap the default target = first unchecked in document order
        # (a current-stage frontier member). Both terms must be present.
        self.assertIn("document order", self.text)
        self.assertIn("frontier", self.text.lower())


AUTO = (ROOT / "skills" / "autopilot" / "SKILL.md")


class TestAutopilotSkill(unittest.TestCase):
    def setUp(self):
        self.text = AUTO.read_text() if AUTO.exists() else ""

    def test_exists(self):
        self.assertTrue(AUTO.exists(), "autopilot SKILL.md missing")

    def test_is_meta_loop_over_semipilot(self):
        self.assertIn("semipilot", self.text)

    def test_give_up_ladder(self):
        for token in ("current_retries", "retry", "DEPEND", "park", "HARD STOP"):
            self.assertIn(token, self.text)

    def test_roadmap_required(self):
        self.assertIn("chart-it", self.text)

    def test_idle_on_exhaustion(self):
        self.assertIn("idle", self.text)

    def test_dependency_is_structural_stage_test(self):
        # The v1 soft-model dependency guess is replaced by a structural read off the
        # roadmap's `## Stage` layers: same stage = independent, last-in-stage = dependent.
        self.assertIn("STAGE TEST", self.text)
        self.assertIn("same stage", self.text.lower())
        self.assertIn("document order", self.text.lower())


if __name__ == "__main__":
    unittest.main()
