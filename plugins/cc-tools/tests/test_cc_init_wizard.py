import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = ROOT / "rules"
LEAN = RULES_DIR / "keep-files-lean.md"


class TestSeedRule(unittest.TestCase):
    def setUp(self):
        self.text = LEAN.read_text() if LEAN.exists() else ""

    def test_rules_dir_exists(self):
        self.assertTrue(RULES_DIR.is_dir(), "plugins/cc-tools/rules/ missing")

    def test_seed_rule_exists(self):
        self.assertTrue(LEAN.exists(), "keep-files-lean.md missing")

    def test_always_on_no_paths_frontmatter(self):
        # No `paths:` frontmatter => the rule loads every session (always-on), not path-scoped.
        self.assertNotIn("paths:", self.text)

    def test_covers_create_and_edit(self):
        low = self.text.lower()
        self.assertIn("creating a file", low)
        self.assertIn("editing a file", low)

    def test_minimal_diff_principle(self):
        self.assertIn("smallest diff", self.text.lower())


if __name__ == "__main__":
    unittest.main()
