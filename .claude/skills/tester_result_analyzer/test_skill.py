from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SKILLS_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT_PATH))

from _test_support import SKILLS_ROOT, SkillTestCase


class TesterResultAnalyzerSkillTests(SkillTestCase):
    def test_cli_supports_help(self) -> None:
        script = SKILLS_ROOT / "tester_result_analyzer" / "tester_result_analyzer.py"

        result = self.run_python_cli(script, "--help")

        self.assert_success(result, "tester result analyzer help")
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_summary_mode_reports_rows_and_sites(self) -> None:
        script = SKILLS_ROOT / "tester_result_analyzer" / "tester_result_analyzer.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "results.csv"
            self.write_text(csv_path, "SITE,1001,1002\n0,1.0,2.0\n1,1.1,2.1\n")

            result = self.run_python_cli(
                script,
                str(csv_path),
                "--kind",
                "csv",
                "--mode",
                "summary",
                "--json",
            )

            self.assert_success(result, "tester result analyzer")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["row_count"], 2)
            self.assertEqual(payload["numeric_test_column_count"], 2)
            self.assertEqual(payload["site_counts"], {"0": 1, "1": 1})

    def test_summary_mode_accepts_report_json_alias(self) -> None:
        script = SKILLS_ROOT / "tester_result_analyzer" / "tester_result_analyzer.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "results.csv"
            self.write_text(csv_path, "SITE,1001,1002\n0,1.0,2.0\n1,1.1,2.1\n")

            result = self.run_python_cli(
                script,
                str(csv_path),
                "--kind",
                "csv",
                "--mode",
                "summary",
                "--report-json",
            )

            self.assert_success(result, "tester result analyzer report-json alias")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["row_count"], 2)
            self.assertEqual(payload["numeric_test_column_count"], 2)
            self.assertEqual(payload["site_counts"], {"0": 1, "1": 1})


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])