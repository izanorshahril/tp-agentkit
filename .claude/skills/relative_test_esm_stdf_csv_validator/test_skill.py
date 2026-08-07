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


class RelativeTestEsmStdfCsvValidatorSkillTests(SkillTestCase):
    def test_cli_supports_help(self) -> None:
        script = SKILLS_ROOT / "relative_test_esm_stdf_csv_validator" / "relative_test_esm_stdf_csv_validator.py"

        result = self.run_python_cli(script, "--help")

        self.assert_success(result, "relative test validator help")
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_loop_csv_reports_one_matched_pair(self) -> None:
        script = SKILLS_ROOT / "relative_test_esm_stdf_csv_validator" / "relative_test_esm_stdf_csv_validator.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            list_path = root / "RelativePairs.h"
            loop_csv = root / "loop.csv"
            self.write_text(
                list_path,
                textwrap.dedent(
                    """\
                    const int TestIDs[] = {1001};
                    const int JudgeIDs[] = {9001};
                    """
                ),
            )
            self.write_text(loop_csv, "1001,9001\n1.0,0.0\n1.2,0.70710678\n")

            result = self.run_python_cli(
                script,
                "--loop-csv",
                str(loop_csv),
                "--list",
                str(list_path),
                "--test-symbol",
                "TestIDs",
                "--judge-symbol",
                "JudgeIDs",
                "--report-json",
            )

            self.assert_success(result, "relative test loop validator")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["summary"]["matched_pairs"], 1)
            self.assertEqual(payload["top"][0]["test_id"], 1001)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])