import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRUX = ROOT / "skills" / "crux" / "SKILL.md"
CRUX_CMD = ROOT / "commands" / "crux.md"


class TestCruxSkill(unittest.TestCase):
    def test_exists(self):
        self.assertTrue(CRUX.exists(), "crux SKILL.md missing")

    def test_command_wrapper_exists(self):
        self.assertTrue(CRUX_CMD.exists(), "crux command wrapper missing")


if __name__ == "__main__":
    unittest.main()
