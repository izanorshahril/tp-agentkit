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


class TpDiffCompareSkillTests(SkillTestCase):
    def test_cli_supports_help(self) -> None:
        script = SKILLS_ROOT / "tp_diff_compare" / "tp_diff_compare.py"

        result = self.run_python_cli(script, "--help")

        self.assert_success(result, "tp diff compare help")
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_reports_changed_and_current_only_files(self) -> None:
        script = SKILLS_ROOT / "tp_diff_compare" / "tp_diff_compare.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            baseline = root / "baseline"
            current = root / "current"
            self.write_text(baseline / "MainTestPlan" / "foo.tpl", "old_value\n")
            self.write_text(current / "MainTestPlan" / "foo.tpl", "new_value\n")
            self.write_text(current / "MainTestPlan" / "bar.tpl", "only current\n")

            result = self.run_python_cli(
                script,
                "--baseline",
                str(baseline),
                "--current",
                str(current),
                "--report-json",
            )

            self.assert_success(result, "tp diff compare")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["counts"]["baseline_files"], 1)
            self.assertEqual(payload["counts"]["current_files"], 2)
            self.assertEqual(payload["counts"]["shared_files"], 1)
            self.assertEqual(payload["counts"]["changed_files"], 1)
            self.assertEqual(payload["counts"]["only_current_files"], 1)

    def test_filter_ext_limits_compare_scope(self) -> None:
        script = SKILLS_ROOT / "tp_diff_compare" / "tp_diff_compare.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            baseline = root / "baseline"
            current = root / "current"
            self.write_text(baseline / "MainTestPlan" / "foo.tpl", "old_value\n")
            self.write_text(current / "MainTestPlan" / "foo.tpl", "new_value\n")
            self.write_text(baseline / "MainTestPlan" / "limits.ls", "same_value\n")
            self.write_text(current / "MainTestPlan" / "limits.ls", "same_value\n")

            result = self.run_python_cli(
                script,
                "--baseline",
                str(baseline),
                "--current",
                str(current),
                "--filter-ext",
                ".ls",
                "--report-json",
            )

            self.assert_success(result, "tp diff compare filter ext")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["counts"]["baseline_files"], 1)
            self.assertEqual(payload["counts"]["current_files"], 1)
            self.assertEqual(payload["counts"]["shared_files"], 1)
            self.assertEqual(payload["counts"]["changed_files"], 0)
            self.assertEqual(payload["counts"]["only_current_files"], 0)

    def test_html_cross_check_smoke(self) -> None:
        script = SKILLS_ROOT / "tp_diff_compare" / "tp_diff_compare.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            baseline = root / "baseline"
            current = root / "current"
            report = root / "report.html"
            baseline_file = baseline / "MainTestPlan" / "foo.tpl"
            current_file = current / "MainTestPlan" / "foo.tpl"
            self.write_text(baseline_file, "old_value\n")
            self.write_text(current_file, "new_value\n")

            baseline_display = str(baseline.resolve()).replace("/", "\\")
            current_display = str(current.resolve()).replace("/", "\\")
            self.write_text(
                report,
                textwrap.dedent(
                    f"""\
                    <html>
                    <head><title>Sample TP Diff</title></head>
                    <body>
                    Left base folder: {baseline_display}<br>
                    Right base folder: {current_display}<br>
                    Mode: Folder Compare<br>
                    File: MainTestPlan/foo.tpl &nbsp;
                    <table>
                    <tr><td>1</td><td>old_value</td><td></td><td>1</td><td>new_value</td></tr>
                    </table>
                    </body>
                    </html>
                    """
                ),
            )

            result = self.run_python_cli(
                script,
                "--baseline",
                str(baseline),
                "--current",
                str(current),
                "--compare-html",
                str(report),
                "--report-json",
            )

            self.assert_success(result, "tp diff compare html cross check")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["counts"]["changed_files"], 1)
            self.assertEqual(payload["html_cross_check"]["matching_paths"], 1)
            self.assertFalse(payload["html_cross_check"]["missing_from_html"])
            self.assertFalse(payload["html_cross_check"]["html_only"])


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])