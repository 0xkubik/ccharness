import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROADMAP_MANAGEMENT = ROOT / "skills" / "roadmap-management" / "SKILL.md"
WHAT_TO_DO = ROOT / "skills" / "what-to-do" / "SKILL.md"
DO = ROOT / "skills" / "do" / "SKILL.md"
RRT = ROOT / "skills" / "refactor-review-test" / "SKILL.md"
ARCHITECT = ROOT / "skills" / "architect" / "SKILL.md"


class TestRoadmapManagementSkill(unittest.TestCase):
    def setUp(self):
        self.text = ROADMAP_MANAGEMENT.read_text() if ROADMAP_MANAGEMENT.exists() else ""

    def test_exists(self):
        self.assertTrue(ROADMAP_MANAGEMENT.exists(), "roadmap-management SKILL.md missing")

    def test_owns_north_star_write(self):
        # roadmap-management owns the shared North Star contract block.
        self.assertIn("## Product North Star", self.text)


class TestWhatToDoSkill(unittest.TestCase):
    def test_exists(self):
        self.assertTrue(WHAT_TO_DO.exists(), "what-to-do SKILL.md missing")


class TestDoSkill(unittest.TestCase):
    def test_exists(self):
        self.assertTrue(DO.exists(), "do SKILL.md missing")


class TestRefactorReviewTestSkill(unittest.TestCase):
    def test_exists(self):
        self.assertTrue(RRT.exists(), "refactor-review-test SKILL.md missing")


class TestArchitectSkill(unittest.TestCase):
    def test_exists(self):
        self.assertTrue(ARCHITECT.exists(), "architect SKILL.md missing")


if __name__ == "__main__":
    unittest.main()
