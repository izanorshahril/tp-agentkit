from __future__ import annotations

import sys
import unittest
from pathlib import Path


SKILLS_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT_PATH))

from _test_support import SKILLS_ROOT, SkillTestCase


class VerificationBeforeCompletionSkillTests(SkillTestCase):
    def test_skill_contract_is_behavior_only(self) -> None:
        text = self.read_skill_markdown("verification-before-completion")
        skill_dir = SKILLS_ROOT / "verification-before-completion"
        executable_files = {
            path.name
            for path in skill_dir.iterdir()
            if path.suffix in {".py", ".bat"}
        }

        self.assertIn("status: beta", text)
        self.assertIn("language: markdown", text)
        self.assertIn("Behavior-only skill. No executable script.", text)
        self.assertIn("## TP Evidence Map", text)
        self.assertIn("## Partial-Validation Rule", text)
        self.assertIn("No positive completion claim without fresh task-specific evidence.", text)
        self.assertEqual(executable_files, {"test_skill.py"})


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])