import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin" / "ccscriptctl"

# Tools the script itself shells out to — symlinked into a curated PATH when a
# test needs to simulate a machine with no desktop opener (open / xdg-open).
SCRIPT_DEPS = ["bash", "dirname", "grep", "mktemp", "awk", "mv", "tail", "cat", "nohup"]


def _marker_script(marker):
    return '#!/usr/bin/env bash\nprintf "%s" "$1" > ' f'"{marker}"\n'


class TestCcfunnelBin(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name).resolve()
        self.proj = self.base / "proj"
        self.ccdir = self.proj / ".claude" / "ccharness"
        self.ccdir.mkdir(parents=True)
        (self.ccdir / "roadmap.md").write_text("# Roadmap\n")
        (self.ccdir / "cheatsheet.md").write_text("# Cheats\n")
        # `open` and `$EDITOR` each record the path they were told to open, into
        # their own marker file, so a test can tell which path the script took.
        self.opened = self.base / "opened"
        self.edited = self.base / "edited"
        self.fakebin = self.base / "fakebin"
        self.fakebin.mkdir()
        self.fake_open = self.fakebin / "open"
        self.fake_open.write_text(_marker_script(self.opened))
        self.fake_open.chmod(0o755)
        self.fake_editor = self.base / "fake_editor"
        self.fake_editor.write_text(_marker_script(self.edited))
        self.fake_editor.chmod(0o755)

    def tearDown(self):
        self.tmp.cleanup()

    def _no_opener_path(self):
        # A PATH with the script's deps but no `open` / `xdg-open`, so the
        # $VISUAL/$EDITOR fallback branch is exercised.
        d = self.base / "coreutils"
        if not d.exists():
            d.mkdir()
            for tool in SCRIPT_DEPS:
                real = shutil.which(tool)
                if real:
                    (d / tool).symlink_to(real)
        return str(d)

    def run_bin(self, *args, cwd=None, env_extra=None, no_opener=False):
        target_cwd = cwd or self.proj
        env = dict(os.environ)
        env["EDITOR"] = str(self.fake_editor)
        env["PWD"] = str(target_cwd)
        env.pop("VISUAL", None)
        if no_opener:
            env["PATH"] = self._no_opener_path()
        else:
            env["PATH"] = str(self.fakebin) + os.pathsep + env.get("PATH", "")
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            [str(BIN), *args],
            cwd=str(target_cwd),
            env=env,
            capture_output=True,
            text=True,
        )

    def wait_for(self, path, timeout=4.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if Path(path).exists():
                return True
            time.sleep(0.02)
        return False

    def test_bin_exists_and_executable(self):
        self.assertTrue(BIN.exists(), "bin/ccscriptctl missing")
        self.assertTrue(os.access(BIN, os.X_OK), "bin/ccscriptctl not executable")

    def test_opens_roadmap(self):
        r = self.run_bin("roadmap", "open")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.opened.read_text(), str(self.ccdir / "roadmap.md"))

    def test_bare_roadmap_needs_subcommand(self):
        r = self.run_bin("roadmap")
        self.assertEqual(r.returncode, 2)
        self.assertIn("subcommand", r.stderr)
        self.assertFalse(self.opened.exists(), "bare roadmap opened an editor")

    def test_opens_cheatsheet(self):
        r = self.run_bin("cheatsheet")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.opened.read_text(), str(self.ccdir / "cheatsheet.md"))

    def test_walks_up_from_subdir(self):
        deep = self.proj / "a" / "b" / "c"
        deep.mkdir(parents=True)
        r = self.run_bin("roadmap", "open", cwd=deep)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.opened.read_text(), str(self.ccdir / "roadmap.md"))

    def test_opener_returns_despite_hanging_editor(self):
        # The bug: a blocking $EDITOR (e.g. `code --wait`) made `open` hang. The
        # desktop opener must win and the command must return, not wait.
        hang = self.base / "hang_editor"
        hang.write_text("#!/usr/bin/env bash\nsleep 30\n")
        hang.chmod(0o755)
        r = subprocess.run(
            [str(BIN), "roadmap", "open"],
            cwd=str(self.proj),
            env={
                **os.environ,
                "EDITOR": str(hang),
                "VISUAL": str(hang),
                "PWD": str(self.proj),
                "PATH": str(self.fakebin) + os.pathsep + os.environ.get("PATH", ""),
            },
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.opened.read_text(), str(self.ccdir / "roadmap.md"))
        self.assertFalse(self.edited.exists(), "blocking editor ran despite an opener")

    def test_fallback_to_editor_without_opener(self):
        # No desktop opener on PATH → fall back to $EDITOR, launched detached.
        r = self.run_bin("roadmap", "open", no_opener=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(self.wait_for(self.edited), "editor fallback never ran")
        self.assertEqual(self.edited.read_text(), str(self.ccdir / "roadmap.md"))

    def test_visual_beats_editor_without_opener(self):
        vis = self.base / "fake_visual"
        vismark = self.base / "vis_opened"
        vis.write_text(_marker_script(vismark))
        vis.chmod(0o755)
        r = self.run_bin("roadmap", "open", no_opener=True, env_extra={"VISUAL": str(vis)})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(self.wait_for(vismark), "$VISUAL fallback never ran")
        self.assertEqual(vismark.read_text(), str(self.ccdir / "roadmap.md"))
        self.assertFalse(self.edited.exists(), "$EDITOR ran even though $VISUAL was set")

    def test_missing_file_exits_1_with_hint(self):
        (self.ccdir / "cheatsheet.md").unlink()
        r = self.run_bin("cheatsheet")
        self.assertEqual(r.returncode, 1)
        self.assertIn("/cheatsheet-management", r.stderr)

    def test_no_ccharness_exits_1(self):
        bare = self.base / "bare"
        bare.mkdir()
        r = self.run_bin("roadmap", "open", cwd=bare)
        self.assertEqual(r.returncode, 1)
        self.assertIn("/roadmap-management", r.stderr)

    def test_unknown_command_exits_2(self):
        r = self.run_bin("bogus")
        self.assertEqual(r.returncode, 2)
        self.assertIn("Usage:", r.stderr)

    def test_help_exits_0(self):
        r = self.run_bin("help")
        self.assertEqual(r.returncode, 0)
        self.assertIn("ccscriptctl", r.stdout)

    def roadmap_text(self):
        return (self.ccdir / "roadmap.md").read_text()

    def test_add_creates_section_and_appends(self):
        r = self.run_bin("roadmap", "add", "bug", "crash", "on", "empty", "export")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = self.roadmap_text()
        self.assertIn("## Bugs", text)
        self.assertIn("- [ ] crash on empty export", text)
        self.assertFalse(self.opened.exists(), "add opened an editor")

    def test_add_maps_kinds_to_sections(self):
        self.run_bin("roadmap", "add", "feat", "dark mode")
        self.run_bin("roadmap", "add", "todo", "wire up CI")
        self.run_bin("roadmap", "add", "backlog", "i18n someday")
        text = self.roadmap_text()
        self.assertIn("## Features", text)
        self.assertIn("- [ ] dark mode", text)
        self.assertIn("## TODO", text)
        self.assertIn("- [ ] wire up CI", text)
        self.assertIn("## Backlog", text)
        self.assertIn("- [ ] i18n someday", text)

    def test_add_creates_sections_in_canonical_order(self):
        # Add out of order; sections must still land Features → TODO → Backlog → Bugs.
        self.run_bin("roadmap", "add", "bug", "a bug")
        self.run_bin("roadmap", "add", "backlog", "an idea")
        self.run_bin("roadmap", "add", "feat", "a feature")
        self.run_bin("roadmap", "add", "todo", "a task")
        text = self.roadmap_text()
        order = [text.index(h) for h in ("## Features", "## TODO", "## Backlog", "## Bugs")]
        self.assertEqual(order, sorted(order), "sections not in canonical order")

    def test_add_appends_within_existing_section(self):
        self.run_bin("roadmap", "add", "bug", "first")
        self.run_bin("roadmap", "add", "bug", "second")
        text = self.roadmap_text()
        self.assertEqual(text.count("## Bugs"), 1, "duplicate section created")
        self.assertLess(
            text.index("- [ ] first"),
            text.index("- [ ] second"),
            "second note not appended after first",
        )

    def test_add_feat_appends_into_existing_features_block(self):
        (self.ccdir / "roadmap.md").write_text(
            "# Roadmap\n\n## Features\n\n- [ ] build it\n\n## Bugs\n\n- [ ] a bug\n"
        )
        self.run_bin("roadmap", "add", "feat", "new idea")
        text = self.roadmap_text()
        self.assertEqual(text.count("## Features"), 1)
        # New feature joins the route, above the Bugs section.
        self.assertLess(text.index("- [ ] new idea"), text.index("## Bugs"))
        self.assertLess(text.index("- [ ] build it"), text.index("- [ ] new idea"))

    def test_add_bug_lands_below_features_route(self):
        (self.ccdir / "roadmap.md").write_text(
            "# Roadmap\n\n## Features\n\n- [ ] build it\n"
        )
        self.run_bin("roadmap", "add", "bug", "crash")
        text = self.roadmap_text()
        self.assertLess(text.index("- [ ] build it"), text.index("## Bugs"))

    def test_add_preserves_backslashes(self):
        # Text with backslashes must land literally — no escape processing, no
        # split lines that break the one-line-per-item invariant.
        self.run_bin("roadmap", "add", "bug", r"path C:\temp\nope crashes")
        self.run_bin("roadmap", "add", "bug", r"also D:\down")  # append-within path
        text = self.roadmap_text()
        self.assertIn(r"- [ ] path C:\temp\nope crashes", text)
        self.assertIn(r"- [ ] also D:\down", text)

    def test_add_unknown_kind_exits_2(self):
        r = self.run_bin("roadmap", "add", "chore", "something")
        self.assertEqual(r.returncode, 2)
        self.assertIn("bug", r.stderr)

    def test_add_without_text_exits_2(self):
        r = self.run_bin("roadmap", "add", "bug")
        self.assertEqual(r.returncode, 2)

    def test_add_missing_roadmap_exits_1(self):
        (self.ccdir / "roadmap.md").unlink()
        r = self.run_bin("roadmap", "add", "bug", "x")
        self.assertEqual(r.returncode, 1)
        self.assertIn("/roadmap-management", r.stderr)

    def test_unknown_roadmap_subcommand_exits_2(self):
        r = self.run_bin("roadmap", "bogus")
        self.assertEqual(r.returncode, 2)
        self.assertIn("subcommand", r.stderr)

    def _seed_roadmap(self):
        (self.ccdir / "roadmap.md").write_text(
            "# Roadmap\n\n## Features\n\n- [ ] a\n- [ ] b\n\n"
            "## TODO\n\n- [ ] t\n\n## Backlog\n\n## Bugs\n\n- [ ] x\n"
        )

    def test_view_all_prints_whole_file(self):
        self._seed_roadmap()
        r = self.run_bin("roadmap", "view", "all")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, self.roadmap_text())

    def test_view_defaults_to_all(self):
        self._seed_roadmap()
        r = self.run_bin("roadmap", "view")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, self.roadmap_text())

    def test_view_section_prints_only_that_section(self):
        self._seed_roadmap()
        r = self.run_bin("roadmap", "view", "feat")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "## Features\n\n- [ ] a\n- [ ] b\n")

    def test_view_section_not_duplicated(self):
        self._seed_roadmap()
        r = self.run_bin("roadmap", "view", "todo")
        self.assertEqual(r.stdout.count("## TODO"), 1, "section printed twice")
        self.assertIn("- [ ] t", r.stdout)

    def test_view_missing_section_notes_and_exits_0(self):
        (self.ccdir / "roadmap.md").write_text("# Roadmap\n")
        r = self.run_bin("roadmap", "view", "bug")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")
        self.assertIn("## Bugs", r.stderr)

    def test_view_unknown_kind_exits_2(self):
        self._seed_roadmap()
        r = self.run_bin("roadmap", "view", "zzz")
        self.assertEqual(r.returncode, 2)
        self.assertIn("unknown view", r.stderr)


if __name__ == "__main__":
    unittest.main()
