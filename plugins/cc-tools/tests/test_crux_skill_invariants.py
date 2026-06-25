import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRUX = ROOT / "skills" / "crux" / "SKILL.md"
CRUX_CMD = ROOT / "commands" / "crux.md"


class TestCruxSkill(unittest.TestCase):
    def setUp(self):
        self.text = CRUX.read_text() if CRUX.exists() else ""
        self.lower = self.text.lower()

    def test_exists(self):
        self.assertTrue(CRUX.exists(), "crux SKILL.md missing")

    def test_four_jungian_lenses(self):
        # The engine is the four Jungian functions — all four must be present.
        for fn in ("Sensation", "Intuition", "Thinking", "Feeling"):
            self.assertIn(fn, self.text, f"crux lens {fn} missing")

    def test_anti_philosophy_check_field(self):
        # Every lens commits to a falsifiable check, governed by the low-conviction valve.
        self.assertIn("conviction", self.lower)
        self.assertIn("low-conviction valve", self.lower)
        self.assertIn("falsifiable", self.lower)

    def test_converge_not_catalogue(self):
        # crux's reason for existing: ONE diagnosis card, never a checklist of considerations.
        self.assertIn("converge", self.lower)
        self.assertIn("catalogue", self.lower)
        self.assertIn("diagnosis card", self.lower)

    def test_autonomous_interrogates_problem(self):
        # It interrogates the problem, not the human — no clarifying-question bounce.
        self.assertIn("interrogate the problem, never the human", self.lower)

    def test_free_standing_no_north_star_gate(self):
        # Unlike the funnel skills, crux must NOT acquire a North Star grounding gate.
        self.assertIn("no grounding gate", self.lower)

    def test_offers_handoff_not_forced(self):
        # The angle can flow to how-to-do / do, but the handoff is offered, not forced.
        self.assertIn("how-to-do", self.lower)

    def test_command_wrapper_exists(self):
        self.assertTrue(CRUX_CMD.exists(), "crux command wrapper missing")


if __name__ == "__main__":
    unittest.main()
