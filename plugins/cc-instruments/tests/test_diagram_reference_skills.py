import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
COMMANDS = ROOT / "commands"
REFERENCE_SKILLS = ("mermaid", "likec4", "excalidraw")


class TestDiagramReferenceSkills(unittest.TestCase):
    def test_skill_files_exist(self):
        for name in REFERENCE_SKILLS:
            skill = SKILLS / name / "SKILL.md"
            self.assertTrue(skill.exists(), f"{name} SKILL.md missing")

    def test_frontmatter_names_match(self):
        for name in REFERENCE_SKILLS:
            text = (SKILLS / name / "SKILL.md").read_text()
            self.assertIn(f"name: {name}", text, f"{name} frontmatter name mismatch")

    def test_reference_skills_are_command_less(self):
        for name in REFERENCE_SKILLS:
            self.assertFalse(
                (COMMANDS / f"{name}.md").exists(),
                f"{name} must stay command-less (no commands/{name}.md)",
            )


if __name__ == "__main__":
    unittest.main()
