import json, os, shutil, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "hooks" / "nonstop-stop.sh"
HOOKS_JSON = ROOT / "hooks" / "hooks.json"
MUS_HOOK = ROOT / "hooks" / "musician-stop.sh"
MUSICIANS = ROOT / "bin" / "musiciansctl"
SESSION = "11111111-1111-1111-1111-111111111111"
OTHER = "22222222-2222-2222-2222-222222222222"
RUN_ID = "20260626-120000-aaaa"


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
        sid = ns.get("session_id", SESSION)
        d = base / "nonstop" / "by-session"
        d.mkdir(parents=True, exist_ok=True)
        (d / sid).write_text(json.dumps(ns))
    if mus is not None:
        run = base / "musician" / "runs" / RUN_ID
        run.mkdir(parents=True, exist_ok=True)
        (run / "state.json").write_text(json.dumps(mus))
        sid = mus.get("session_id")
        if sid:
            (base / "musician" / "by-session").mkdir(parents=True, exist_ok=True)
            (base / "musician" / "by-session" / sid).write_text(RUN_ID)
    return repo


def armed(session=SESSION):
    return {"on": True, "session_id": session}


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
        # Suspended (awaiting set, active still true) -> nonstop must NOT block (no wasted turn on suspend).
        rc, out = run_hook(repo_with(ns=armed(),
                                     mus={"active": True, "session_id": SESSION,
                                          "awaiting": {"what": "scan", "since": "2026-06-25T00:00:00Z"}}),
                           {"session_id": SESSION})
        self.assertEqual(out.strip(), "")

    def test_armed_musician_closed_blocks(self):
        # The core path: armed + musician CLOSED -> block + re-launch the musician (no nonstop skill).
        rc, out = run_hook(repo_with(ns=armed(), mus={"active": False, "session_id": SESSION}),
                           {"session_id": SESSION})
        self.assertEqual(rc, 0)
        self.assertIn("block", out)
        self.assertIn("/musician", out)

    def test_relaunch_is_autonomous(self):
        # nonstop is the autonomous milestone-walker — it must re-launch the musician in --auto so it
        # does NOT pause to collaborate with the human between milestones.
        rc, out = run_hook(repo_with(ns=armed(), mus={"active": False, "session_id": SESSION}),
                           {"session_id": SESSION})
        self.assertIn("--auto", out)

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
    def test_files_exist(self):
        for p in (HOOK, MUSICIANS):
            self.assertTrue(p.exists(), f"missing {p}")

    def test_registered_in_hooks_json(self):
        self.assertIn("nonstop-stop.sh", HOOKS_JSON.read_text())

    def test_musician_untouched_by_nonstop(self):
        # The separation contract: the musician's own hook carries NO nonstop logic.
        self.assertNotIn("nonstop", MUS_HOOK.read_text().lower())

    def test_nonstop_has_no_brain_skill(self):
        # The musician owns ALL the "what to do next" intelligence; nonstop only re-invokes it.
        # A nonstop "advance" skill would duplicate the musician's brain — pin that it stays absent.
        self.assertFalse((ROOT / "skills" / "nonstop").exists(),
                         "nonstop must have no skill — the musician decides what to do next")

    def test_hook_relaunches_musician_not_a_skill(self):
        # The hook's re-feed must re-invoke /musician (open mode), not point at a nonstop skill.
        text = HOOK.read_text()
        self.assertIn("/musician", text)
        self.assertNotIn("cc-musician:nonstop", text)


if __name__ == "__main__":
    unittest.main()
