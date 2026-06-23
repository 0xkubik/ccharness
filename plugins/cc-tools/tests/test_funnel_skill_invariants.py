import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHART = ROOT / "skills" / "chart-it" / "SKILL.md"
POINT = ROOT / "skills" / "point-it" / "SKILL.md"


class TestChartItSkill(unittest.TestCase):
    def setUp(self):
        self.text = CHART.read_text() if CHART.exists() else ""

    def test_exists(self):
        self.assertTrue(CHART.exists(), "chart-it SKILL.md missing")

    def test_owns_north_star_write(self):
        # chart-it owns the shared North Star contract block.
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


class TestPointItSkill(unittest.TestCase):
    def setUp(self):
        self.text = POINT.read_text() if POINT.exists() else ""

    def test_exists(self):
        self.assertTrue(POINT.exists(), "point-it SKILL.md missing")

    def test_reads_frontier(self):
        self.assertIn("frontier", self.text.lower())
        self.assertIn("## Stage", self.text)

    def test_roadmap_biases_never_gates(self):
        # off-roadmap moves are never dropped.
        self.assertIn("off-roadmap", self.text)

    def test_qualified_handoff(self):
        self.assertIn("cc-tools:grill-it", self.text)


if __name__ == "__main__":
    unittest.main()
