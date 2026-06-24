import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = ROOT / "rules"
LEAN = RULES_DIR / "keep-files-lean.md"
CC_INIT = ROOT / "commands" / "cc-init.md"


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


class TestCcInitWizard(unittest.TestCase):
    def setUp(self):
        self.text = CC_INIT.read_text() if CC_INIT.exists() else ""

    def test_exists(self):
        self.assertTrue(CC_INIT.exists(), "cc-init.md missing")

    def test_uses_askuserquestion(self):
        self.assertIn("AskUserQuestion", self.text)

    def test_four_stages_present(self):
        low = self.text.lower()
        for marker in ("stage 1", "stage 2", "stage 3", "stage 4"):
            self.assertIn(marker, low)

    def test_stage1_antihang_preserved(self):
        # The </dev/null guard on `claude plugin` calls must survive the rewrite.
        self.assertIn("/dev/null", self.text)

    def test_stage1_user_scope_preserved(self):
        self.assertIn("--scope user", self.text)

    def test_stage2_from_plugin_root_to_project_rules(self):
        self.assertIn("CLAUDE_PLUGIN_ROOT", self.text)
        self.assertIn(".claude/rules/", self.text)

    def test_stage3_prose_only(self):
        self.assertIn("Code and tests are out of scope", self.text)

    def test_stage4_offers_chart_it(self):
        self.assertIn("/chart-it", self.text)

    def test_idempotent_documented(self):
        self.assertIn("idempotent", self.text.lower())


if __name__ == "__main__":
    unittest.main()
