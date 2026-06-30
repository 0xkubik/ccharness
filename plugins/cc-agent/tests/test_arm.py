import json, os, subprocess, tempfile, time, unittest
from pathlib import Path

ARM = Path(__file__).resolve().parent.parent / "skills" / "musician" / "arm.sh"
SESSION = "aaaa-1111"
MUS = ".claude/ccharness/musician"


def run_arm(repo, arg_string, session=SESSION):
    env = dict(os.environ, CLAUDE_CODE_SESSION_ID=session)
    r = subprocess.run(["bash", str(ARM), arg_string], cwd=repo,
                       capture_output=True, text=True, env=env)
    out = {}
    orphans = []
    for line in r.stdout.splitlines():
        if line.startswith("ORPHAN="):
            orphans.append(line[len("ORPHAN="):])
        elif "=" in line:
            k, v = line.split("=", 1)
            out[k] = v
    return out, orphans, r


def state_of(repo, run_id):
    return json.loads((Path(repo) / MUS / "runs" / run_id / "state.json").read_text())


def with_north_star(repo):
    d = Path(repo) / ".claude" / "ccharness"
    d.mkdir(parents=True, exist_ok=True)
    (d / "roadmap.md").write_text("# Roadmap\n\n## Product North Star\n\nBe great.\n")


class TestArmTaskMode(unittest.TestCase):
    def test_creates_run_and_pointer(self):
        repo = tempfile.mkdtemp()
        out, _, r = run_arm(repo, "fix the flaky login test")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(out["ENTRY"], "task")
        rid = out["RUN_ID"]
        st = state_of(repo, rid)
        self.assertTrue(st["active"])
        self.assertEqual(st["status"], "working")
        self.assertEqual(st["run_id"], rid)
        self.assertEqual(st["session_id"], SESSION)
        # the original prompt, captured verbatim
        self.assertEqual(st["input"], "fix the flaky login test")
        # pointer resolves the session to this run
        ptr = (Path(repo) / MUS / "by-session" / SESSION).read_text()
        self.assertEqual(ptr, rid)
        # heartbeat + record files exist
        for f in ("heartbeat", "log.jsonl", "blocked.jsonl"):
            self.assertTrue((Path(repo) / MUS / "runs" / rid / f).exists())

    def test_records_worktree_helper(self):
        # The in-loop build integrate/discard calls need the helper's path on re-fed turns (no
        # ${CLAUDE_PLUGIN_ROOT} then), so arm records its absolute path into state.
        repo = tempfile.mkdtemp()
        out, _, _ = run_arm(repo, "build something")
        st = state_of(repo, out["RUN_ID"])
        self.assertIn("worktree_helper", st)
        self.assertTrue(st["worktree_helper"].endswith("/worktree.sh"))
        self.assertTrue(Path(st["worktree_helper"]).exists())  # points at the real sibling helper

    def test_flags_parsed_prompt_preserved(self):
        repo = tempfile.mkdtemp()
        out, _, _ = run_arm(repo, "make it fast --ultracode")
        st = state_of(repo, out["RUN_ID"])
        self.assertTrue(st["ultracode"])
        self.assertEqual(st["input"], "make it fast")  # flags stripped from the prompt

    def test_no_give_up_or_cap_bounds(self):
        # The give-up / cycle-cap machinery is gone: no bounds in state, the flags are inert.
        repo = tempfile.mkdtemp()
        out, _, _ = run_arm(repo, "make it fast --max-cycles 5 --give-up-after 2")
        st = state_of(repo, out["RUN_ID"])
        for gone in ("max_cycles", "max_no_progress", "no_progress_streak"):
            self.assertNotIn(gone, st)

    def test_multiline_prompt_not_truncated(self):
        # A pasted multi-line task must not lose everything after line 1 (verbatim-capture intent).
        repo = tempfile.mkdtemp()
        out, _, _ = run_arm(repo, "fix the parser\nit breaks on tabs")
        inp = state_of(repo, out["RUN_ID"])["input"]
        self.assertIn("fix the parser", inp)
        self.assertIn("it breaks on tabs", inp)  # the second line survived

    def test_run_ids_are_unique(self):
        repo = tempfile.mkdtemp()
        a, _, _ = run_arm(repo, "task one")
        b, _, _ = run_arm(repo, "task two", session="bbbb-2222")
        self.assertNotEqual(a["RUN_ID"], b["RUN_ID"])
        # two runs, two folders, two pointers — no collision
        self.assertTrue((Path(repo) / MUS / "runs" / a["RUN_ID"]).exists())
        self.assertTrue((Path(repo) / MUS / "runs" / b["RUN_ID"]).exists())


class TestArmPhase(unittest.TestCase):
    """Default arms into the collaborative SHAPING phase; --auto arms straight into BUILDING."""

    def test_default_task_mode_is_shaping(self):
        repo = tempfile.mkdtemp()
        out, _, _ = run_arm(repo, "fix the flaky login test")
        self.assertEqual(state_of(repo, out["RUN_ID"])["phase"], "shaping")

    def test_default_open_mode_is_shaping(self):
        repo = tempfile.mkdtemp()
        with_north_star(repo)
        out, _, _ = run_arm(repo, "")
        self.assertEqual(state_of(repo, out["RUN_ID"])["phase"], "shaping")

    def test_auto_flag_sets_building(self):
        repo = tempfile.mkdtemp()
        out, _, _ = run_arm(repo, "fix the flaky login test --auto")
        st = state_of(repo, out["RUN_ID"])
        self.assertEqual(st["phase"], "building")
        self.assertEqual(st["input"], "fix the flaky login test")  # flag stripped from the prompt

    def test_auto_open_mode_is_building(self):
        repo = tempfile.mkdtemp()
        with_north_star(repo)
        out, _, _ = run_arm(repo, "--auto")
        st = state_of(repo, out["RUN_ID"])
        self.assertEqual(out["ENTRY"], "open")
        self.assertEqual(st["phase"], "building")

    def test_auto_and_ultracode_coexist(self):
        repo = tempfile.mkdtemp()
        out, _, _ = run_arm(repo, "make it fast --auto --ultracode")
        st = state_of(repo, out["RUN_ID"])
        self.assertEqual(st["phase"], "building")
        self.assertTrue(st["ultracode"])
        self.assertEqual(st["input"], "make it fast")


class TestArmIdempotency(unittest.TestCase):
    """One active run per session — arm refuses a second (BUSY), so no duplicate run can ever exist,
    no matter how many times arm is triggered (a double /musician, command + skill, etc.)."""

    def test_active_run_refuses_second_arm_as_busy(self):
        repo = tempfile.mkdtemp()
        out1, _, _ = run_arm(repo, "first task")
        rid1 = out1["RUN_ID"]
        self.assertTrue(state_of(repo, rid1)["active"])
        # second arm in the SAME session while the first is active → BUSY, pointing at the existing run
        out2, _, _ = run_arm(repo, "second task")
        self.assertEqual(out2.get("BUSY"), rid1)
        self.assertEqual(out2["RUN_ID"], rid1)
        # exactly ONE run folder — no duplicate was forged
        runs = [p for p in (Path(repo) / MUS / "runs").iterdir() if p.is_dir()]
        self.assertEqual(len(runs), 1)

    def test_closed_run_allows_a_fresh_arm(self):
        repo = tempfile.mkdtemp()
        out1, _, _ = run_arm(repo, "first task")
        rid1 = out1["RUN_ID"]
        # close the first run (achieved) — the session is now free for a new one
        st = state_of(repo, rid1); st["active"] = False; st["status"] = "achieved"
        (Path(repo) / MUS / "runs" / rid1 / "state.json").write_text(json.dumps(st))
        out2, _, _ = run_arm(repo, "second task")
        self.assertNotIn("BUSY", out2)
        self.assertNotEqual(out2["RUN_ID"], rid1)
        self.assertEqual(state_of(repo, out2["RUN_ID"])["input"], "second task")


class TestMusicianCommand(unittest.TestCase):
    """The /musician command instructs the MODEL to run arm.sh itself (model-mediated, not a `!`
    auto-run). CLAUDE_PLUGIN_ROOT is absent in that context, so it locates arm.sh via the install
    manifest and passes the user's $ARGUMENTS."""

    def setUp(self):
        self.cmd = (Path(__file__).resolve().parent.parent / "commands" / "musician.md").read_text()

    def test_command_instructs_model_to_run_arm(self):
        # Arm is the model's responsibility now — NO `!` preprocessing auto-runs it.
        self.assertNotIn("!`", self.cmd)              # no ! auto-run block
        self.assertIn("arm.sh", self.cmd)             # the model is told to run arm.sh
        self.assertIn("$ARGUMENTS", self.cmd)         # passing the user's args
        self.assertIn("installed_plugins.json", self.cmd)  # located via the install manifest (no plugin-root)

    def test_command_says_run_arm_once(self):
        # The model runs arm exactly once; it must not re-run it (a second run is refused as BUSY).
        self.assertIn("exactly once", self.cmd)


class TestArmOpenMode(unittest.TestCase):
    def test_open_mode_needs_north_star(self):
        repo = tempfile.mkdtemp()
        out, _, _ = run_arm(repo, "")
        self.assertEqual(out.get("GATE"), "no-north-star")
        self.assertFalse((Path(repo) / MUS / "runs").exists() and
                         any((Path(repo) / MUS / "runs").iterdir()))

    def test_open_mode_with_north_star_arms(self):
        repo = tempfile.mkdtemp()
        with_north_star(repo)
        out, _, _ = run_arm(repo, "")
        self.assertEqual(out["ENTRY"], "open")
        self.assertEqual(state_of(repo, out["RUN_ID"])["input"], "")


class TestArmResume(unittest.TestCase):
    def test_resume_readopts_run(self):
        repo = tempfile.mkdtemp()
        first, _, _ = run_arm(repo, "long task")
        rid = first["RUN_ID"]
        # simulate a close, then a resume from a different (new) session
        st = state_of(repo, rid); st["active"] = False; st["status"] = "blocked"
        (Path(repo) / MUS / "runs" / rid / "state.json").write_text(json.dumps(st))
        out, _, _ = run_arm(repo, f"--resume {rid}", session="new-9999")
        self.assertEqual(out.get("RESUMED"), rid)
        st2 = state_of(repo, rid)
        self.assertTrue(st2["active"])
        self.assertEqual(st2["status"], "working")
        self.assertEqual(st2["session_id"], "new-9999")
        self.assertEqual((Path(repo) / MUS / "by-session" / "new-9999").read_text(), rid)

    def test_resume_missing(self):
        repo = tempfile.mkdtemp()
        out, _, _ = run_arm(repo, "--resume 20990101-000000-zzzz")
        self.assertEqual(out.get("RESUME_MISSING"), "20990101-000000-zzzz")


class TestArmOrphanScan(unittest.TestCase):
    def test_stale_working_run_surfaced(self):
        repo = tempfile.mkdtemp()
        # a previous run left "working" with a stale heartbeat (crash)
        orphan = Path(repo) / MUS / "runs" / "20260626-100000-dead"
        orphan.mkdir(parents=True)
        (orphan / "state.json").write_text(json.dumps(
            {"active": True, "status": "working", "awaiting": None,
             "input": "refactor the parser"}))
        hb = orphan / "heartbeat"; hb.write_text("")
        old = time.time() - 3600  # 60 min ago > 30 min threshold
        os.utime(hb, (old, old))

        out, orphans, _ = run_arm(repo, "a fresh task")
        self.assertTrue(any(o.startswith("20260626-100000-dead|") for o in orphans),
                        f"expected the stale run surfaced, got {orphans}")
        # surface only — it was NOT auto-adopted (pointer points at the NEW run)
        self.assertEqual((Path(repo) / MUS / "by-session" / SESSION).read_text(), out["RUN_ID"])

    def test_shaping_run_not_an_orphan(self):
        repo = tempfile.mkdtemp()
        # a run parked in the collaborative SHAPING phase is waiting on the HUMAN, not crashed
        # autonomous work — a stale heartbeat there must NOT be surfaced as a resumable orphan.
        shaping = Path(repo) / MUS / "runs" / "20260626-080000-talk"
        shaping.mkdir(parents=True)
        (shaping / "state.json").write_text(json.dumps(
            {"active": True, "status": "working", "phase": "shaping",
             "awaiting": None, "input": "discuss this idea"}))
        hb = shaping / "heartbeat"; hb.write_text("")
        old = time.time() - 3600
        os.utime(hb, (old, old))

        _, orphans, _ = run_arm(repo, "fresh task")
        self.assertEqual(orphans, [])

    def test_awaiting_run_not_an_orphan(self):
        repo = tempfile.mkdtemp()
        # a parked (awaiting) run with a stale heartbeat is NOT crashed — must not be surfaced
        parked = Path(repo) / MUS / "runs" / "20260626-090000-park"
        parked.mkdir(parents=True)
        (parked / "state.json").write_text(json.dumps(
            {"active": True, "status": "working",
             "awaiting": {"what": "scan", "since": "x"}, "input": "y"}))
        hb = parked / "heartbeat"; hb.write_text("")
        old = time.time() - 3600
        os.utime(hb, (old, old))

        _, orphans, _ = run_arm(repo, "fresh task")
        self.assertEqual(orphans, [])


if __name__ == "__main__":
    unittest.main()
