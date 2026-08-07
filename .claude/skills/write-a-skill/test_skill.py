from __future__ import annotations

import sys
import unittest
from pathlib import Path


SKILLS_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT_PATH))

from _test_support import SKILLS_ROOT, SkillTestCase


class WriteASkillTests(SkillTestCase):
    def test_skill_contract_is_behavior_only(self) -> None:
        text = self.read_skill_markdown("write-a-skill")
        skill_dir = SKILLS_ROOT / "write-a-skill"
        executable_files = {
            path.name
            for path in skill_dir.iterdir()
            if path.suffix in {".py", ".bat"}
        }

        self.assertIn("status: beta", text)
        self.assertIn("language: markdown", text)
        self.assertIn("Behavior-only skill. No executable script.", text)
        self.assertIn("`.claude/skills/_registry.md`", text)
        self.assertIn("`test_skill.py`", text)
        self.assertIn("prefer local artifact output over GitHub issue creation", text)
        self.assertEqual(executable_files, {"test_skill.py"})


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])