from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SKILLS_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT_PATH))

from _test_support import SKILLS_ROOT, SkillTestCase


class SystemControllerLogAnalyzerSkillTests(SkillTestCase):
    def test_cli_supports_help(self) -> None:
        script = SKILLS_ROOT / "system_controller_log_analyzer" / "log_analyzer_agent.py"

        result = self.run_python_cli(script, "--help")

        self.assert_success(result, "system controller log analyzer help")
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_parses_single_failure_entry(self) -> None:
        script = SKILLS_ROOT / "system_controller_log_analyzer" / "log_analyzer_agent.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "system.log"
            self.write_text(
                log_path,
                textwrap.dedent(
                    """\
                    Time: Mon Apr 01 10:00:00 2026
                    Status: FAIL
                    ErrorCode: E001
                    Routine: SampleRoutine
                    Message: First failure
                    File: Sample.cpp
                    Line: 10
                    """
                ),
            )

            result = self.run_python_cli(script, str(log_path), "--json")

            self.assert_success(result, "system controller log analyzer")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["status"], "success")
            self.assertEqual(payload["summary"]["total_entries"], 1)

    def test_accepts_report_json_alias(self) -> None:
        script = SKILLS_ROOT / "system_controller_log_analyzer" / "log_analyzer_agent.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "system.log"
            self.write_text(
                log_path,
                textwrap.dedent(
                    """\
                    Time: Mon Apr 01 10:00:00 2026
                    Status: FAIL
                    ErrorCode: E001
                    Routine: SampleRoutine
                    Message: First failure
                    File: Sample.cpp
                    Line: 10
                    """
                ),
            )

            result = self.run_python_cli(script, str(log_path), "--report-json")

            self.assert_success(result, "system controller log analyzer report-json alias")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["status"], "success")
            self.assertEqual(payload["summary"]["total_entries"], 1)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])