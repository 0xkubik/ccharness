import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUS = (ROOT / "skills" / "musician" / "SKILL.md")


class TestMusicianSkill(unittest.TestCase):
    def setUp(self):
        self.text = MUS.read_text() if MUS.exists() else ""

    def test_exists(self):
        self.assertTrue(MUS.exists(), "musician SKILL.md missing")

    def test_done_check_leads(self):
        self.assertIn("DONE", self.text)
        self.assertIn("done_when", self.text)

    def test_all_four_exits(self):
        # achieved (done), declined (smart no), gave-up/capped (tried, couldn't).
        for token in ("achieved", "declined", "gave-up", "capped"):
            self.assertIn(token, self.text)
        for token in ("max_cycles", "no_progress_streak"):
            self.assertIn(token, self.text)

    def test_decline_is_first_class(self):
        # The load-bearing new exit: the brain can refuse BEFORE building, distinct from gave-up.
        self.assertIn("declined", self.text)
        self.assertIn("decline", self.text.lower())
        # ...and it is fed by the critical-thinking instrument.
        self.assertIn("crux", self.text)

    def test_two_entry_modes(self):
        self.assertIn("Task mode", self.text)
        self.assertIn("Open mode", self.text)
        # what-to-do is the open-mode direction finder.
        self.assertIn("what-to-do", self.text)

    def test_forges_own_done_contract(self):
        # No roadmap milestone to copy `done when` from — the musician manufactures one.
        self.assertIn("forge", self.text.lower())
        self.assertIn("falsifiable", self.text.lower())

    def test_bounded_self_closing(self):
        self.assertIn("bounded", self.text.lower())
        self.assertIn("close", self.text.lower())
        # There is explicitly no never-stop loop above it.
        self.assertIn("never-stop", self.text.lower())

    def test_no_askuserquestion_under_loop(self):
        self.assertIn("AskUserQuestion", self.text)  # must mention it to forbid it

    def test_grounding_gate(self):
        self.assertIn("find-goal", self.text)

    def test_qualified_funnel_skill_names(self):
        # The directly-invoked funnel skills must be referenced by QUALIFIED name.
        for name in ("cc-tools:what-to-do", "cc-tools:how-to-do", "cc-tools:do"):
            self.assertIn(name, self.text)

    def test_musician_state_path(self):
        self.assertIn(".claude/ccharness/musician/", self.text)

    def test_documents_ultracode_no_spend(self):
        # The musician carries --ultracode (mandatory fan-out) ...
        self.assertIn("--ultracode", self.text)
        self.assertIn("worktree", self.text.lower())
        # ... and explicitly has NO spend flag (it is bounded by design; spend is gone).
        self.assertIn("no spend flag", self.text.lower())

    def test_roadmap_upkeep_route_not_goal(self):
        # B: the musician may edit the ROUTE (mark done / add sub-step) within the current version,
        # but the GOAL layer (North Star + version defs) is read-only; future versions are proposals.
        self.assertIn("roadmap-proposals.md", self.text)
        lowered = self.text.lower()
        self.assertIn("route", lowered)       # the musician may edit the route
        self.assertIn("read-only", lowered)   # the goal layer is read-only to it

    def test_awareness_memory_git_notes_only_shrinks(self):
        # Cross-run awareness = closed facts in git notes, written at close, read at arm as a
        # "don't repeat" filter. Forward intentions are fenced OUT of notes (anti-loop) — they
        # keep their human-gated home in roadmap-proposals.md.
        self.assertIn("git notes append", self.text)   # write at close
        self.assertIn("git log --notes", self.text)    # read at arm
        self.assertIn("forward intention", self.text.lower())
        self.assertIn("roadmap-proposals.md", self.text)

    def test_no_autopilot_residue(self):
        # The whole point of the redesign: no autopilot / semipilot / milestone-walking loop left.
        lowered = self.text.lower()
        self.assertNotIn("autopilot", lowered)
        self.assertNotIn("semipilot", lowered)


if __name__ == "__main__":
    unittest.main()
