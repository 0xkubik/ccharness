import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS_JSON = ROOT / "hooks" / "hooks.json"
HOOK = ROOT / "hooks" / "cheatsheet-hook.sh"

SHEET_REL = ".claude/ccharness/cheatsheet.md"
SHEET_BODY = (
    "<cheatsheet>\n"
    "Search code: prefer the indexed MCP search over raw grep\n"
    "Edits: follow .claude/rules\n"
    "</cheatsheet>\n"
)
MARKER = "<cheatsheet>"


def _transcript(path: Path, prompts: int, tool_results: int = 0):
    """Write a JSONL transcript with `prompts` real user prompts (carry promptSource) and
    `tool_results` tool-result turns (type:user but no promptSource — must NOT be counted)."""
    lines = []
    for i in range(prompts):
        lines.append(json.dumps({"type": "user", "promptSource": "user",
                                 "message": {"role": "user", "content": f"q{i}"}}))
    for i in range(tool_results):
        lines.append(json.dumps({"type": "user", "toolUseResult": "ok",
                                 "message": {"role": "user",
                                             "content": [{"type": "tool_result"}]}}))
    path.write_text("\n".join(lines) + ("\n" if lines else ""))


def _run(project: Path, transcript: Path):
    payload = json.dumps({
        "session_id": "test-session",
        "hook_event_name": "UserPromptSubmit",
        "transcript_path": str(transcript),
        "prompt": "hello",
    })
    return subprocess.run(["bash", str(HOOK)], input=payload, cwd=str(project),
                          capture_output=True, text=True)


class TestHookWiring(unittest.TestCase):
    def test_hooks_json_registers_userpromptsubmit(self):
        cfg = json.loads(HOOKS_JSON.read_text())
        self.assertIn("UserPromptSubmit", cfg.get("hooks", {}))
        blob = json.dumps(cfg)
        self.assertIn("cheatsheet-hook.sh", blob)
        self.assertIn("CLAUDE_PLUGIN_ROOT", blob)

    def test_hook_is_executable(self):
        self.assertTrue(HOOK.exists(), "cheatsheet-hook.sh missing")
        self.assertTrue(os.stat(HOOK).st_mode & stat.S_IXUSR, "hook must be executable")


class TestHookBehaviour(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        (self.project / ".claude" / "ccharness").mkdir(parents=True)
        self.sheet = self.project / SHEET_REL
        self.sheet.write_text(SHEET_BODY)
        self.transcript = self.project / "transcript.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def _expect(self, prompts, should_inject, tool_results=0):
        _transcript(self.transcript, prompts, tool_results)
        r = _run(self.project, self.transcript)
        self.assertEqual(r.returncode, 0, f"hook must always exit 0 (n={prompts}); stderr={r.stderr}")
        if should_inject:
            self.assertIn(MARKER, r.stdout, f"expected reminder at n={prompts}")
            self.assertIn("indexed MCP search", r.stdout)
        else:
            self.assertEqual(r.stdout.strip(), "", f"expected silence at n={prompts}, got: {r.stdout!r}")

    def test_injects_only_every_third_prompt(self):
        for n, inject in [(0, False), (1, False), (2, False), (3, True),
                          (4, False), (5, False), (6, True)]:
            with self.subTest(prompts=n):
                self._expect(n, inject)

    def test_tool_results_are_not_counted(self):
        # 2 real prompts + 5 tool results => count is 2, not 7 => no injection.
        self._expect(2, should_inject=False, tool_results=5)
        # 3 real prompts + 5 tool results => count is 3 => injection.
        self._expect(3, should_inject=True, tool_results=5)

    def test_noop_without_cheatsheet_file(self):
        self.sheet.unlink()
        _transcript(self.transcript, 3)
        r = _run(self.project, self.transcript)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "", "no cheat-sheet file => no-op even on the third prompt")

    def test_noop_when_transcript_missing(self):
        r = _run(self.project, self.project / "does-not-exist.jsonl")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
