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
        self.assertIn("find-goal", self.text)

    def test_qualified_funnel_skill_names(self):
        # The directly-invoked funnel skills must be referenced by QUALIFIED name.
        for name in ("cc-tools:what-to-do", "cc-tools:how-to-do", "cc-tools:do"):
            self.assertIn(name, self.text)

    def test_semipilot_state_path(self):
        self.assertIn(".claude/ccharness/semipilot/", self.text)

    def test_frontier_aware_target(self):
        # Under a layered roadmap the default target = first unchecked in document order
        # (a current-stage frontier member). Both terms must be present.
        self.assertIn("document order", self.text)
        self.assertIn("frontier", self.text.lower())

    def test_documents_ultracode_only(self):
        # semipilot carries --ultracode (mandatory fan-out) ...
        self.assertIn("--ultracode", self.text)
        self.assertIn("worktree", self.text.lower())
        # ... and explicitly has NO spend flag (spend is autopilot-only).
        self.assertIn("no spend flag", self.text.lower())


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
        self.assertIn("find-goal", self.text)

    def test_idle_on_exhaustion(self):
        self.assertIn("idle", self.text)

    def test_dependency_is_structural_stage_test(self):
        # The v1 soft-model dependency guess is replaced by a structural read off the
        # roadmap's `## Stage` layers: same stage = independent, last-in-stage = dependent.
        self.assertIn("STAGE TEST", self.text)
        self.assertIn("same stage", self.text.lower())
        self.assertIn("document order", self.text.lower())

    def test_advance_stays_in_frontier_stage(self):
        # Advancing (after success OR after parking) must not cross a stage boundary while the
        # frontier stage still holds unfinished/parked work — a later stage gated by parked work
        # is a dependency block (HARD STOP), not a milestone to jump to.
        self.assertIn("FRONTIER STAGE", self.text)
        self.assertIn("ADVANCE-OR-STALL", self.text)
        self.assertIn("parked", self.text.lower())

    def test_documents_run_mode_flags(self):
        # Both flags must be parsed and documented.
        self.assertIn("--ultracode", self.text)
        self.assertIn("--spend-session", self.text)
        self.assertIn("worktree", self.text.lower())
        # Spend mode's two real overrides on autopilot (NOT "kill the caps"):
        # exhausted roadmap -> generate work (not cheap idle), and hard-block -> park + mine.
        self.assertIn("Spend mode", self.text)
        self.assertIn("subscription limit", self.text.lower())
        # State fields the arm step must write.
        self.assertIn('"ultracode"', self.text)
        self.assertIn('"spend"', self.text)


if __name__ == "__main__":
    unittest.main()
