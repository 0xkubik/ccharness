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

    def test_three_exits_no_giveup_or_cap(self):
        # The doors out: achieved (done), declined (smart no BEFORE building), blocked
        # (do tried and couldn't — business blocker or exhausted technical path).
        for token in ("achieved", "declined", "blocked"):
            self.assertIn(token, self.text)
        # The give-up / cycle-cap machinery was removed — it must not creep back.
        for gone in ("gave-up", "capped", "max_cycles", "no_progress_streak"):
            self.assertNotIn(gone, self.text)

    def test_collaborative_shaping_default(self):
        # Default: a collaborative SHAPING phase (idea developed WITH the human) precedes the
        # autonomous BUILDING phase. --auto skips shaping and goes straight to autonomy.
        self.assertIn("--auto", self.text)
        lowered = self.text.lower()
        self.assertIn("shaping", lowered)
        self.assertIn("building", lowered)

    def test_musician_state_path(self):
        self.assertIn(".claude/ccharness/musician/", self.text)

    def test_per_run_folders_and_pointer(self):
        # Each run is isolated in its own folder, resolved via a per-session pointer.
        self.assertIn("run_id", self.text)
        self.assertIn("runs/", self.text)
        self.assertIn("by-session", self.text)

    def test_captures_input_prompt_verbatim(self):
        # The original prompt the musician was handed is recorded verbatim in the run.
        self.assertIn("input", self.text)
        self.assertIn("verbatim", self.text.lower())

    def test_arm_delegated_to_script(self):
        # The deterministic bookkeeping lives in arm.sh; the skill delegates to it.
        self.assertIn("arm.sh", self.text)
        self.assertTrue((ROOT / "skills" / "musician" / "arm.sh").exists(), "arm.sh missing")

    def test_status_and_heartbeat(self):
        # Explicit lifecycle label + the crash-fuse heartbeat the next arm scans.
        self.assertIn("status", self.text.lower())
        self.assertIn("heartbeat", self.text.lower())

    def test_crash_orphan_surface_only(self):
        # Crash recovery surfaces an orphan and lets the user resume — it never auto-adopts.
        self.assertIn("--resume", self.text)
        self.assertIn("ORPHAN", self.text)
        self.assertIn("auto-adopt", self.text.lower())

    def test_documents_ultracode_no_spend(self):
        # The musician carries --ultracode (mandatory fan-out) ...
        self.assertIn("--ultracode", self.text)
        self.assertIn("worktree", self.text.lower())
        # ... and explicitly has NO spend flag (it is bounded by design; spend is gone).
        self.assertIn("no spend flag", self.text.lower())

    def test_build_runs_in_isolated_worktree(self):
        # The build (and only the build) runs in a throwaway worktree so it never dirties the main
        # tree; the conductor stays in main and integrates the result via the helper.
        self.assertIn('isolation:"worktree"', self.text)
        self.assertIn("worktree.sh", self.text)
        lowered = self.text.lower()
        self.assertIn("integrate", lowered)
        self.assertIn("discard", lowered)
        # The helper path is recorded in state so re-fed turns (no plugin-root env) can find it.
        self.assertIn("worktree_helper", self.text)
        # The build is forced onto the current HEAD per-dispatch (reset), and integrate is ff-only
        # so a stale build can't land silently.
        self.assertIn("reset --hard", self.text)
        self.assertIn("STALE", self.text)
        # The finished build is integrated onto the LOCAL main branch (not just "the current branch").
        self.assertIn("local `main`", self.text)


if __name__ == "__main__":
    unittest.main()
