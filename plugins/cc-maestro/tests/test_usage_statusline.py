"""Tests for the cc-maestro usage bridge (bin/cc-usage-statusline.sh).

The bridge is a statusLine wrapper: it tees Claude Code's rate_limits payload into the global
~/.claude/ccharness/usage.json (honoring $CLAUDE_CONFIG_DIR) and forwards the payload to the
user's real status line. Covers capture, the no-clobber-on-empty rule, downstream passthrough,
and the jq fallback (python3 absent)."""

import json, os, shutil, subprocess, tempfile, unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "cc-usage-statusline.sh"


def payload(proj, with_limits=True):
    d = {"cwd": proj, "model": {"id": "x"}}
    if with_limits:
        d["rate_limits"] = {
            "five_hour": {"used_percentage": 42, "resets_at": 1719240000},
            "seven_day": {"used_percentage": 71, "resets_at": 1719600000},
        }
    return json.dumps(d)


def run(stdin, env_extra=None, path=None):
    env = dict(os.environ)
    if path is not None:
        env["PATH"] = path
    if env_extra:
        env.update(env_extra)
    return subprocess.run(["/bin/bash", str(SCRIPT)], input=stdin,
                          capture_output=True, text=True, env=env)


def usage_path(cfg):
    return Path(cfg) / "ccharness" / "usage.json"


def bin_with(*tools):
    """A PATH dir symlinking only the named tools — to simulate python3-absent."""
    d = tempfile.mkdtemp()
    for t in tools:
        src = shutil.which(t)
        if src:
            os.symlink(src, os.path.join(d, t))
    return d


class TestUsageBridge(unittest.TestCase):
    def setUp(self):
        self.proj = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.proj, ignore_errors=True)
        # Destination is the GLOBAL config dir, not the project — isolate it so the suite
        # never writes the real ~/.claude/ccharness/usage.json. run() inherits os.environ.
        self.cfg = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.cfg, ignore_errors=True)
        prev = os.environ.get("CLAUDE_CONFIG_DIR")
        os.environ["CLAUDE_CONFIG_DIR"] = self.cfg
        self.addCleanup(
            lambda: os.environ.__setitem__("CLAUDE_CONFIG_DIR", prev)
            if prev is not None else os.environ.pop("CLAUDE_CONFIG_DIR", None))

    def test_captures_rate_limits(self):
        run(payload(self.proj), env_extra={"CC_USAGE_DOWNSTREAM": ""})
        data = json.loads(usage_path(self.cfg).read_text())
        self.assertEqual(data["five_hour"]["used_percentage"], 42)
        self.assertEqual(data["seven_day"]["used_percentage"], 71)
        self.assertTrue(data["captured_at"].endswith("Z"))

    def test_empty_payload_keeps_last_good(self):
        run(payload(self.proj), env_extra={"CC_USAGE_DOWNSTREAM": ""})
        run(payload(self.proj, with_limits=False), env_extra={"CC_USAGE_DOWNSTREAM": ""})
        data = json.loads(usage_path(self.cfg).read_text())
        self.assertEqual(data["five_hour"]["used_percentage"], 42)  # not clobbered

    def test_downstream_passthrough(self):
        r = run(payload(self.proj), env_extra={"CC_USAGE_DOWNSTREAM": "cat"})
        self.assertIn('"rate_limits"', r.stdout)  # payload forwarded verbatim

    def test_no_downstream_renders_nothing_but_still_writes(self):
        r = run(payload(self.proj), env_extra={"CC_USAGE_DOWNSTREAM": "definitely-not-installed-xyz"})
        self.assertEqual(r.stdout.strip(), "")
        self.assertTrue(usage_path(self.cfg).exists())

    def test_jq_fallback_without_python3(self):
        if not shutil.which("jq"):
            self.skipTest("jq not available")
        # PATH with jq + coreutils the jq branch needs, but NO python3.
        path = bin_with("jq", "cat", "date", "mkdir", "mv")
        self.addCleanup(shutil.rmtree, path, ignore_errors=True)
        run(payload(self.proj), env_extra={"CC_USAGE_DOWNSTREAM": ""}, path=path)
        data = json.loads(usage_path(self.cfg).read_text())
        self.assertEqual(data["five_hour"]["used_percentage"], 42)
        self.assertEqual(data["source"], "cc-maestro/usage-statusline")


if __name__ == "__main__":
    unittest.main()
