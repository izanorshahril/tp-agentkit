from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SKILLS_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT_PATH))

from _test_support import SKILLS_ROOT, SkillTestCase


class SPLReadonlyCompareSkillTests(SkillTestCase):
    def test_cli_supports_help(self) -> None:
        script = SKILLS_ROOT / "spl-readonly-compare" / "spl_readonly_compare.py"

        result = self.run_python_cli(script, "--help")

        self.assert_success(result, "spl readonly compare help")
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_reports_review_buckets_without_editing_tp(self) -> None:
        script = SKILLS_ROOT / "spl-readonly-compare" / "spl_readonly_compare.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "approved_spl.csv"
            ls_path = root / "Main.ls"
            output_path = root / "readonly_report.json"
            self.write_text(
                csv_path,
                "TestNumber,Parameter,Scaled_LSPL,Scaled_USPL,Scale,ScaledUnit,Comment\n"
                "100,REG_A,0.4000,1.4000,0,V,changed\n"
                "101,REG_B,0.1000,1.0000,0,V,unchanged\n"
                "102,REG_C,0.2000,2.0000,0,V,commented\n"
                "103,REG_D,0.3000,3.0000,0,V,target na\n"
                "104,REG_E,0.4000,4.0000,0,V,absent\n"
                "105,REG_F,0.5000,5.0000,0,V,partial na\n"
                "106,REG_G,40,60,0,%,percent alias\n",
            )
            self.write_text(
                ls_path,
                "T100 { FTC(1.5000V, 0.5000V); }\n"
                "T101 { FTC(1.0000V, 0.1000V); }\n"
                "# T102 { FTC(2.0000V, 0.2000V); }\n"
                "T103 { FTC(NA); }\n"
                "T105 { FTC(5.0000V, NA); }\n"
                "T106 { FTC(60pct, 40pct); }\n",
            )

            result = self.run_python_cli(
                script,
                "--csv",
                str(csv_path),
                "--ls",
                str(ls_path),
                "--env",
                "FTC",
                "--case-name",
                "fixture",
                "--output",
                str(output_path),
                "--report-json",
            )

            self.assert_success(result, "spl readonly compare buckets")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["case"], "fixture")
            self.assertEqual(payload["rows_with_limits"], 7)
            self.assertEqual(payload["matched_rows"], 4)
            self.assertEqual(payload["changed_rows"], 1)
            self.assertEqual(payload["unchanged_rows"], 2)
            self.assertEqual(payload["non_comparable_rows"], 1)
            self.assertEqual(payload["commented_in_ls"], 1)
            self.assertEqual(payload["target_env_na_rows"], 1)
            self.assertEqual(payload["absent_from_main_rows"], 1)
            self.assertEqual(payload["base_unit_mismatch_rows"], 0)
            self.assertEqual(payload["partial_na_rows"], 1)
            self.assertEqual(payload["output"].lower(), str(output_path).replace("\\", "/").lower())
            self.assertTrue(output_path.exists())
            self.assertIn("target env has NA in one limit cell", str(payload["non_comparable_examples"]))


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])