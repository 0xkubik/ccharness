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


class TestDistributableRules(unittest.TestCase):
    """Every file in rules/ must be wizard-installable: a bare, always-on rule whose first line is
    the `# ` heading the cc-init Stage 2 multiselect shows as its label."""

    EXPECTED = (
        "keep-files-lean.md",
        "no-comments.md",
        "require-goal-and-roadmap.md",
        "speak-plainly.md",
        "manage-git-history.md",
        "weigh-by-importance.md",
        "stay-in-scope.md",
    )

    def rule_files(self):
        return sorted(RULES_DIR.glob("*.md"))

    def test_expected_rules_present(self):
        names = {p.name for p in self.rule_files()}
        for expected in self.EXPECTED:
            self.assertIn(expected, names, f"{expected} missing from rules/")

    def test_each_rule_first_line_is_heading(self):
        for p in self.rule_files():
            first = p.read_text().splitlines()[0]
            self.assertTrue(
                first.startswith("# "),
                f"{p.name}: first line must be a '# ' heading (the wizard's label)",
            )

    def test_each_rule_always_on(self):
        # No `paths:` frontmatter => every rule loads every session, not path-scoped.
        for p in self.rule_files():
            self.assertNotIn("paths:", p.read_text(), f"{p.name}: must ship always-on")

    def test_no_comments_keeps_nonobvious_exception(self):
        low = (RULES_DIR / "no-comments.md").read_text().lower()
        self.assertIn("non-obvious", low)  # the carve-out, not an absolute ban
        self.assertIn("why", low)  # explain why, not what

    def test_grounding_rule_is_tiered(self):
        low = (RULES_DIR / "require-goal-and-roadmap.md").read_text().lower()
        self.assertIn("goal", low)
        self.assertIn("roadmap", low)
        self.assertIn("multi-step", low)  # roadmap gates only multi-step => won't break goal-only flows

    def test_speak_plainly_fresh_self_contained_and_language_agnostic(self):
        low = (RULES_DIR / "speak-plainly.md").read_text().lower()
        self.assertIn("plain", low)
        self.assertIn("self-contained", low)  # the fresh-eyes final answer
        self.assertNotIn("russian", low)  # distributable => no user-specific language coupling

    def test_git_autonomy_covers_full_flow_without_asking(self):
        low = (RULES_DIR / "manage-git-history.md").read_text().lower()
        for action in ("branch", "commit", "push"):
            self.assertIn(action, low)
        self.assertIn("never ask", low)  # the autonomy promise: own git, never ask

    def test_weigh_by_importance_decouples_recency(self):
        low = (RULES_DIR / "weigh-by-importance.md").read_text().lower()
        self.assertIn("importance", low)
        self.assertIn("recen", low)  # recency / recent — importance decoupled from recency

    def test_stay_in_scope_forbids_creep_and_building_ahead(self):
        low = (RULES_DIR / "stay-in-scope.md").read_text().lower()
        self.assertIn("scope", low)
        self.assertIn("exactly what was asked", low)  # the boundary: only the request
        self.assertIn("future", low)  # don't build ahead for imagined needs (YAGNI)


class TestCcInitWizard(unittest.TestCase):
    def setUp(self):
        self.text = CC_INIT.read_text() if CC_INIT.exists() else ""

    def test_exists(self):
        self.assertTrue(CC_INIT.exists(), "cc-init.md missing")

    def test_uses_askuserquestion(self):
        self.assertIn("AskUserQuestion", self.text)

    def test_five_stages_present(self):
        low = self.text.lower()
        for marker in ("## stage 1", "## stage 2", "## stage 3", "## stage 4", "## stage 5"):
            self.assertIn(marker, low)
        self.assertNotIn("## stage 6", low)

    def test_cheatsheet_stage_builds_width_capped_sheet(self):
        # Stage 3 generates the reminder cheat-sheet the UserPromptSubmit hook prints.
        low = self.text.lower()
        self.assertIn("cheat-sheet", low)
        self.assertIn(".claude/ccharness/cheatsheet.txt", self.text)
        self.assertIn("80 characters", low)  # the hard per-line width limit
        self.assertIn("claude mcp list", self.text)  # inventories installed MCP servers

    def test_stage1_antihang_preserved(self):
        # The </dev/null guard on `claude plugin` calls must survive the rewrite.
        self.assertIn("/dev/null", self.text)

    def test_stage1_user_scope_preserved(self):
        self.assertIn("--scope user", self.text)

    def test_offers_external_codegraph_and_headroom(self):
        # Stage 1 also offers the two non-marketplace MCP tools, with real repos + install commands.
        self.assertIn("https://github.com/colbymchenry/codegraph", self.text)
        self.assertIn("https://github.com/headroomlabs-ai/headroom", self.text)
        self.assertIn("npm install -g @colbymchenry/codegraph", self.text)
        self.assertIn('pip install "headroom-ai[all]"', self.text)

    def test_playwright_and_commit_commands_dropped_from_install_set(self):
        # playwright now ships with Claude Code; commits are handled directly — neither is installed.
        self.assertNotIn("playwright", self.text)
        self.assertNotIn("commit-commands", self.text)

    def test_stage2_from_plugin_root_to_project_rules(self):
        self.assertIn("CLAUDE_PLUGIN_ROOT", self.text)
        self.assertIn(".claude/rules/", self.text)

    def test_stage2_batches_rules_under_four_option_cap(self):
        # rules/ already ships >4 rules, but AskUserQuestion caps a question at 4 options. Stage 2
        # must batch across several multiSelect questions, not cram every rule into one question.
        self.assertGreater(len(list(RULES_DIR.glob("*.md"))), 4)
        self.assertIn("4 options", self.text.lower())

    def test_no_usage_bridge_stage(self):
        # The usage bridge moved to cc-maestro: cc-init must not reference it any more.
        self.assertNotIn("cc-usage-statusline.sh", self.text)
        self.assertNotIn("CC_USAGE_DOWNSTREAM", self.text)

    def test_doc_reconcile_prose_only(self):
        self.assertIn("Code and tests are out of scope", self.text)

    def test_offers_find_goal(self):
        self.assertIn("/find-goal", self.text)

    def test_idempotent_documented(self):
        self.assertIn("idempotent", self.text.lower())


if __name__ == "__main__":
    unittest.main()
