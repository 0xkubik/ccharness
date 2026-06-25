import json, os, shutil, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "hooks" / "nonstop-stop.sh"
HOOKS_JSON = ROOT / "hooks" / "hooks.json"
MUS_HOOK = ROOT / "hooks" / "musician-stop.sh"
SKILL = ROOT / "skills" / "nonstop" / "SKILL.md"
CMD_ON = ROOT / "commands" / "nonstop-on.md"
CMD_OFF = ROOT / "commands" / "nonstop-off.md"
SESSION = "11111111-1111-1111-1111-111111111111"
OTHER = "22222222-2222-2222-2222-222222222222"


def nojq_env():
    """PATH with coreutils (cat, grep) symlinked but NOT jq."""
    tmpbin = tempfile.mkdtemp()
    for tool in ("cat", "grep"):
        src = shutil.which(tool)
        if src:
            os.symlink(src, os.path.join(tmpbin, tool))
    return {"PATH": tmpbin}


def run_hook(repo, stdin_obj, env=None):
    kw = dict(input=json.dumps(stdin_obj), cwd=repo, capture_output=True, text=True)
    if env is not None:
        kw["env"] = env
    r = subprocess.run(["/bin/bash", str(HOOK)], **kw)
    return r.returncode, r.stdout


def repo_with(ns=None, mus=None):
    repo = tempfile.mkdtemp()
    base = Path(repo) / ".claude" / "ccharness"
    if ns is not None:
        (base / "nonstop").mkdir(parents=True, exist_ok=True)
        (base / "nonstop" / "state.json").write_text(json.dumps(ns))
    if mus is not None:
        (base / "musician").mkdir(parents=True, exist_ok=True)
        (base / "musician" / "state.json").write_text(json.dumps(mus))
    return repo


def armed(session=SESSION):
    return {"on": True, "session_id": session, "current": None}


class TestNonstopHook(unittest.TestCase):
    def test_no_nonstop_state_noop(self):
        # No marker at all -> the hook is a pure no-op (the musician behaves exactly as before).
        rc, out = run_hook(repo_with(mus={"active": False}), {"session_id": SESSION})
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_disarmed_noop(self):
        rc, out = run_hook(repo_with(ns={"on": False, "session_id": SESSION},
                                     mus={"active": False}), {"session_id": SESSION})
        self.assertEqual(out.strip(), "")

    def test_armed_no_musician_noop(self):
        # Armed but no musician closed yet (e.g. cancel removed the state) -> nothing to advance.
        rc, out = run_hook(repo_with(ns=armed(), mus=None), {"session_id": SESSION})
        self.assertEqual(out.strip(), "")

    def test_armed_musician_active_noop(self):
        # Mid-milestone: the musician's OWN hook drives; nonstop stays silent (zones don't overlap).
        rc, out = run_hook(repo_with(ns=armed(), mus={"active": True, "session_id": SESSION}),
                           {"session_id": SESSION})
        self.assertEqual(out.strip(), "")

    def test_armed_musician_awaiting_noop(self):
        # Suspended (awaiting set, active still true) -> nonstop must NOT block (no quota burn on suspend).
        rc, out = run_hook(repo_with(ns=armed(),
                                     mus={"active": True, "session_id": SESSION,
                                          "awaiting": {"what": "scan", "since": "2026-06-25T00:00:00Z"}}),
                           {"session_id": SESSION})
        self.assertEqual(out.strip(), "")

    def test_armed_musician_closed_blocks(self):
        # The core path: armed + musician CLOSED -> block + hand off to the skill.
        rc, out = run_hook(repo_with(ns=armed(), mus={"active": False, "session_id": SESSION}),
                           {"session_id": SESSION})
        self.assertEqual(rc, 0)
        self.assertIn("block", out)
        self.assertIn("cc-agent:nonstop", out)

    def test_different_session_noop(self):
        # A nonstop armed in another session must not fire here.
        rc, out = run_hook(repo_with(ns=armed(OTHER), mus={"active": False, "session_id": SESSION}),
                           {"session_id": SESSION})
        self.assertEqual(out.strip(), "")

    def test_nojq_armed_closed_blocks(self):
        # jq absent (coreutils present): armed + closed must STILL block via the grep fallback.
        repo = repo_with(ns=armed(), mus={"active": False, "session_id": SESSION})
        rc, out = run_hook(repo, {"session_id": SESSION}, env=nojq_env())
        self.assertIn("block", out)

    def test_nojq_armed_active_noop(self):
        # jq absent: an active musician still yields a no-op (the grep fallback reads active:true).
        repo = repo_with(ns=armed(), mus={"active": True, "session_id": SESSION})
        rc, out = run_hook(repo, {"session_id": SESSION}, env=nojq_env())
        self.assertEqual(out.strip(), "")


class TestNonstopInvariants(unittest.TestCase):
    def setUp(self):
        self.skill = SKILL.read_text() if SKILL.exists() else ""

    def test_files_exist(self):
        for p in (HOOK, SKILL, CMD_ON, CMD_OFF):
            self.assertTrue(p.exists(), f"missing {p}")

    def test_registered_in_hooks_json(self):
        self.assertIn("nonstop-stop.sh", HOOKS_JSON.read_text())

    def test_musician_untouched_by_nonstop(self):
        # The separation contract: the musician's own hook carries NO nonstop logic.
        self.assertNotIn("nonstop", MUS_HOOK.read_text().lower())

    def test_skill_is_the_authority(self):
        # nonstop owns "what's done" via its own `current`, not a fuzzy match of the musician input.
        self.assertIn("current", self.skill)
        self.assertIn("authority", self.skill.lower())

    def test_skill_records_then_picks(self):
        lowered = self.skill.lower()
        self.assertIn("[x]", self.skill)          # mark achieved milestone done
        self.assertIn("park", lowered)            # park stuck milestones
        self.assertIn("no retry", lowered)        # ...without retry this run
        self.assertIn("frontier", lowered)        # pick the next in the frontier

    def test_skill_disarm_conditions(self):
        lowered = self.skill.lower()
        self.assertIn("disarm", lowered)
        self.assertIn("blocked", lowered)         # stage blocked -> stop (ordered stages)

    def test_skill_goal_layer_read_only(self):
        # Same split as the musician: may edit the route ([x]); the goal layer stays read-only.
        self.assertIn("read-only", self.skill.lower())

    def test_skill_delegates_to_musician(self):
        # nonstop never builds; it hands the milestone to the untouched musician.
        self.assertIn("/musician", self.skill)


if __name__ == "__main__":
    unittest.main()
