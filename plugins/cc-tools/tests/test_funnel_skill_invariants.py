import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIND_GOAL = ROOT / "skills" / "find-goal" / "SKILL.md"
WHAT_TO_DO = ROOT / "skills" / "what-to-do" / "SKILL.md"


class TestFindGoalSkill(unittest.TestCase):
    def setUp(self):
        self.text = FIND_GOAL.read_text() if FIND_GOAL.exists() else ""

    def test_exists(self):
        self.assertTrue(FIND_GOAL.exists(), "find-goal SKILL.md missing")

    def test_owns_north_star_write(self):
        # find-goal owns the shared North Star contract block.
        self.assertIn("## Product North Star", self.text)

    def test_layered_stage_format(self):
        # The roadmap is layered into `## Stage` bands — the format every consumer reads.
        self.assertIn("## Stage", self.text)

    def test_frontier_replaces_pointer(self):
        self.assertIn("frontier", self.text.lower())

    def test_stage_rule(self):
        # The governing rule: order → split stages; independent → same stage.
        self.assertIn("same stage", self.text.lower())

    def test_document_order_canonical(self):
        # Doc order = a valid sequential walk, so "first unchecked" stays well-defined.
        self.assertIn("document order", self.text.lower())

    def test_legacy_line_compat(self):
        # A roadmap with no stage headings must still behave like the old linear one.
        self.assertIn("legacy", self.text.lower())


class TestWhatToDoSkill(unittest.TestCase):
    def setUp(self):
        self.text = WHAT_TO_DO.read_text() if WHAT_TO_DO.exists() else ""

    def test_exists(self):
        self.assertTrue(WHAT_TO_DO.exists(), "what-to-do SKILL.md missing")

    def test_reads_frontier(self):
        self.assertIn("frontier", self.text.lower())
        self.assertIn("## Stage", self.text)

    def test_roadmap_biases_never_gates(self):
        # off-roadmap moves are never dropped.
        self.assertIn("off-roadmap", self.text)

    def test_qualified_handoff(self):
        self.assertIn("cc-tools:how-to-do", self.text)


if __name__ == "__main__":
    unittest.main()
