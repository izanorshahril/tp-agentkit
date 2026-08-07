from __future__ import annotations

import sys
import unittest
from pathlib import Path


SKILLS_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT_PATH))

from _test_support import SKILLS_ROOT, SkillTestCase


class GrillMeSkillTests(SkillTestCase):
    def test_skill_contract_is_behavior_only(self) -> None:
        text = self.read_skill_markdown("grill-me")
        skill_dir = SKILLS_ROOT / "grill-me"
        executable_files = {
            path.name
            for path in skill_dir.iterdir()
            if path.suffix in {".py", ".bat"}
        }

        self.assertIn("status: beta", text)
        self.assertIn("language: markdown", text)
        self.assertIn("Behavior-only skill. No executable script.", text)
        self.assertIn("medium-risk and high-risk", text)
        self.assertIn("user-facing pressure-test", text)
        self.assertIn("ask the user one question at a time", text)
        self.assertIn("recommended answer", text)
        self.assertIn("do not treat internal self-grilling as a complete grill pass", text)
        self.assertIn("limits-only claims", text)
        self.assertIn("release gating", text)
        self.assertIn("STDF CSV analysis", text)
        self.assertIn("interactive schema questioning", text)
        self.assertIn("authority for USL/LSL", text)
        self.assertIn("preserve that lesson in durable repo knowledge", text)
        self.assertEqual(executable_files, {"test_skill.py"})


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])