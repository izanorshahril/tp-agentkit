from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SKILLS_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT_PATH))

from _test_support import SKILLS_ROOT, SkillTestCase


class ScrSpecialTpAuditSkillTests(SkillTestCase):
    def test_cli_supports_help(self) -> None:
        script = SKILLS_ROOT / "scr_special_tp_audit" / "scr_special_tp_audit.py"

        result = self.run_python_cli(script, "--help")

        self.assert_success(result, "scr special tp audit help")
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_reports_scr_markers_in_current_overlay(self) -> None:
        script = SKILLS_ROOT / "scr_special_tp_audit" / "scr_special_tp_audit.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            baseline = root / "baseline"
            current = root / "current"
            baseline.mkdir(parents=True, exist_ok=True)
            self.write_text(current / "MainTestPlan" / "FlowSCR.tpl", 'String SCR_MODE = "1";\n')
            self.write_text(current / "TestFunctions" / "Utils.cpp", "SysCUserVars.SCR_MODE = 1;\n")
            self.write_text(current / "TestProgramHistory.txt", "SCR update\n")

            result = self.run_python_cli(
                script,
                "--baseline",
                str(baseline),
                "--current",
                str(current),
                "--report-json",
            )

            self.assert_success(result, "scr special tp audit")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["scr_only_in_current_count"], 1)
            self.assertTrue(payload["has_live_gate"])
            self.assertTrue(payload["history_mentions_scr"])


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])