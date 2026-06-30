import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = ROOT / "rules"
LEAN = RULES_DIR / "keep-files-lean.md"
CC_INIT = ROOT / "commands" / "cc-init.md"
SKILLS = ROOT / "skills"
RULES_SKILL = SKILLS / "rules-management" / "SKILL.md"
CHEATSHEET_SKILL = SKILLS / "cheatsheet-management" / "SKILL.md"
DOCS_SKILL = SKILLS / "docs-management" / "SKILL.md"


class TestSeedRule(unittest.TestCase):
    def setUp(self):
        self.text = LEAN.read_text() if LEAN.exists() else ""

    def test_rules_dir_exists(self):
        self.assertTrue(RULES_DIR.is_dir(), "plugins/cc-instruments/rules/ missing")

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
        "keep-the-tree-clean.md",
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

    def test_keep_tree_clean_places_bounds_and_routes_forks(self):
        low = (RULES_DIR / "keep-the-tree-clean.md").read_text().lower()
        self.assertIn("where it belongs", low)  # place each change by the layout
        self.assertIn("bound it to this change", low)  # not a repo-wide reorg
        self.assertIn("structural fork", low)  # a real layout fork is decided, not guessed


class TestCcInitOrchestrator(unittest.TestCase):
    def setUp(self):
        self.text = CC_INIT.read_text() if CC_INIT.exists() else ""

    def test_exists(self):
        self.assertTrue(CC_INIT.exists(), "cc-init.md missing")

    def test_uses_askuserquestion(self):
        self.assertIn("AskUserQuestion", self.text)

    def test_orientation_explains_four_plugins(self):
        # The new opening: explain the four plugins before doing anything.
        for plugin in ("cc-instruments", "cc-script", "cc-musician", "cc-conductor"):
            self.assertIn(plugin, self.text)

    def test_orchestrates_three_skills(self):
        # init is now an orchestrator: Stage 0 installs inline, then it invokes the three skills.
        self.assertIn("## Stage 0", self.text)
        for skill in ("rules-management", "cheatsheet-management", "docs-management"):
            self.assertIn(skill, self.text)

    def test_install_stays_inline(self):
        # Dependency install stays in init (Stage 0), with its anti-hang + user-scope guards.
        self.assertIn("--scope user", self.text)
        self.assertIn("/dev/null", self.text)

    def test_offers_external_codegraph_and_headroom(self):
        self.assertIn("https://github.com/colbymchenry/codegraph", self.text)
        self.assertIn("https://github.com/headroomlabs-ai/headroom", self.text)
        self.assertIn("npm install -g @colbymchenry/codegraph", self.text)
        self.assertIn('pip install "headroom-ai[all]"', self.text)

    def test_dropped_plugins_absent_from_install_set(self):
        for name in ("playwright", "commit-commands", "gitlab", "GitLab"):
            self.assertNotIn(name, self.text)

    def test_no_usage_bridge(self):
        self.assertNotIn("cc-usage-statusline.sh", self.text)
        self.assertNotIn("CC_USAGE_DOWNSTREAM", self.text)

    def test_offers_roadmap_management(self):
        self.assertIn("/roadmap-management", self.text)

    def test_idempotent_documented(self):
        self.assertIn("idempotent", self.text.lower())

    def test_explains_as_it_goes(self):
        # The user's requirement: explain what each step does and why, not just execute.
        self.assertIn("explain as you go", self.text.lower())


class TestRulesSkill(unittest.TestCase):
    def setUp(self):
        self.text = RULES_SKILL.read_text() if RULES_SKILL.exists() else ""

    def test_exists(self):
        self.assertTrue(RULES_SKILL.exists(), "rules-management SKILL.md missing")

    def test_resolves_plugin_rules_robustly_into_project_rules(self):
        # CLAUDE_PLUGIN_ROOT is unreliable in skill context (issue #9354) — the skill must locate
        # cc-instruments' rules/ via installed_plugins.json + cache-glob fallback, then copy into the project.
        self.assertIn("installed_plugins.json", self.text)
        self.assertNotIn("CLAUDE_PLUGIN_ROOT", self.text)  # the env-var bet that would silently fail
        self.assertIn(".claude/rules/", self.text)

    def test_batches_rules_under_four_option_cap(self):
        # rules/ ships >4 rules; AskUserQuestion caps a question at 4 options → must batch.
        self.assertGreater(len(list(RULES_DIR.glob("*.md"))), 4)
        self.assertIn("4 options", self.text.lower())

    def test_captures_project_own_rules(self):
        # The added step: after the recommended set, capture the project's own rules.
        self.assertIn("project's own", self.text.lower())

    def test_explains_as_it_goes(self):
        self.assertIn("explain as you go", self.text.lower())


class TestCheatsheetSkill(unittest.TestCase):
    def setUp(self):
        self.text = CHEATSHEET_SKILL.read_text() if CHEATSHEET_SKILL.exists() else ""

    def test_exists(self):
        self.assertTrue(CHEATSHEET_SKILL.exists(), "cheatsheet-management SKILL.md missing")

    def test_builds_width_capped_sheet(self):
        low = self.text.lower()
        self.assertIn("cheat-sheet", low)
        self.assertIn(".claude/ccharness/cheatsheet.md", self.text)
        self.assertIn("80 characters", low)
        self.assertIn("claude mcp list", self.text)

    def test_fixed_marker_structure(self):
        self.assertIn("<cheatsheet>", self.text)
        self.assertIn("</cheatsheet>", self.text)

    def test_user_selected_paginated_with_justification(self):
        low = self.text.lower()
        self.assertIn("multiselect", low)
        self.assertIn("paginated", low)
        self.assertIn("only the ticked lines are written", low)
        self.assertIn("justification", low)
        self.assertIn("what you saw", low)

    def test_excludes_project_specifics(self):
        low = self.text.lower()
        self.assertIn("nothing project-specific", low)
        for src in ("plugins", "skills", "agents", "mcp"):
            self.assertIn(src, low)

    def test_explains_as_it_goes(self):
        self.assertIn("explain as you go", self.text.lower())


class TestDocsSkill(unittest.TestCase):
    def setUp(self):
        self.text = DOCS_SKILL.read_text() if DOCS_SKILL.exists() else ""

    def test_exists(self):
        self.assertTrue(DOCS_SKILL.exists(), "docs-management SKILL.md missing")

    def test_prose_only(self):
        self.assertIn("Code and tests are out of scope", self.text)

    def test_scans_specs_and_plans(self):
        # The user explicitly asked for specs and plans to be in scope.
        low = self.text.lower()
        self.assertIn("specs", low)
        self.assertIn("plans", low)

    def test_finds_stale(self):
        # The framing shift: surface what's stale for the human, not a silent reconcile.
        self.assertIn("stale", self.text.lower())

    def test_explains_as_it_goes(self):
        self.assertIn("explain as you go", self.text.lower())


if __name__ == "__main__":
    unittest.main()
