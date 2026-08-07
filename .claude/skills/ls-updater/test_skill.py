from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SKILLS_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT_PATH))

from _test_support import SKILLS_ROOT, SkillTestCase


class LSUpdaterSkillTests(SkillTestCase):
    def test_cli_supports_help(self) -> None:
        script = SKILLS_ROOT / "ls-updater" / "ls_updater.py"

        result = self.run_python_cli(script, "--help")

        self.assert_success(result, "ls updater help")
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_updates_plain_limit_rows(self) -> None:
        script = SKILLS_ROOT / "ls-updater" / "ls_updater.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "limits.csv"
            ls_path = root / "sample.ls"
            self.write_text(
                csv_path,
                "Expression,Static Low Limit,Static High Limit,Expression Behavior\n"
                "P_12345 : TEST,0.5,1.5,Include\n",
            )
            self.write_text(ls_path, "12345, TEST, 0, V, [0.1, 1.0, 1]\n")

            result = self.run_python_cli(
                script,
                "--csv",
                str(csv_path),
                "--ls",
                str(ls_path),
                "--env",
                "FTC",
                "--silent",
                "--in-place",
                "--report-json",
            )

            self.assert_success(result, "ls updater plain row")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["updated"], 1)
            self.assertTrue(Path(payload["backup"]).exists())
            updated_text = ls_path.read_text(encoding="utf-8")
            self.assertEqual(
                updated_text,
                "12345, TEST, 0, V, [0.5, 1.0, 1] # FTC: LL 0.1->0.5\n",
            )

    def test_reports_no_change_without_editing_limits(self) -> None:
        script = SKILLS_ROOT / "ls-updater" / "ls_updater.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "limits.csv"
            ls_path = root / "sample_same_values.ls"
            original_text = "12345, TEST, 0, V, [0.5, 1.5, 1]\n"
            self.write_text(
                csv_path,
                "Expression,Static Low Limit,Static High Limit,Expression Behavior\n"
                "P_12345 : TEST,0.5,1.5,Include\n",
            )
            self.write_text(ls_path, original_text)

            result = self.run_python_cli(
                script,
                "--csv",
                str(csv_path),
                "--ls",
                str(ls_path),
                "--env",
                "FTC",
                "--silent",
                "--in-place",
                "--report-json",
            )

            self.assert_success(result, "ls updater no change")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["updated"], 0)
            self.assertEqual(payload["not_updated"], 1)
            self.assertIn("no change", payload["unupdated_reasons"]["12345"])
            self.assertEqual(ls_path.read_text(encoding="utf-8"), original_text)

    def test_updates_limitdef_macros(self) -> None:
        script = SKILLS_ROOT / "ls-updater" / "ls_updater.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "limits.csv"
            ls_path = root / "sample_macro.ls"
            self.write_text(
                csv_path,
                "Expression,Static Low Limit,Static High Limit,Expression Behavior\n"
                "P_12345 : TEST,0.5,1.5,Include\n",
            )
            self.write_text(ls_path, "${LimitDef(12345, TEST, 0, V, 0.1, 1.0)}\n")

            result = self.run_python_cli(
                script,
                "--csv",
                str(csv_path),
                "--ls",
                str(ls_path),
                "--env",
                "FTC",
                "--silent",
                "--in-place",
                "--report-json",
            )

            self.assert_success(result, "ls updater macro")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["updated"], 1)
            updated_text = ls_path.read_text(encoding="utf-8")
            self.assertEqual(
                updated_text,
                "${LimitDef(12345, TEST, 0, V, 0.5, 1.0)} # FTC: LL 0.1->0.5\n",
            )

    def test_updates_only_selected_multi_env_column(self) -> None:
        script = SKILLS_ROOT / "ls-updater" / "ls_updater.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "limits.csv"
            ls_path = root / "sample_multi_env.ls"
            self.write_text(
                csv_path,
                "Expression,Static Low Limit,Static High Limit,Expression Behavior\n"
                "P_12345 : TEST,0.5,1.5,Include\n",
            )
            self.write_text(
                ls_path,
                "LimitTable [FTC, FTH]\n"
                "12345, TEST, 0, V, [0.1, 1.0, 1], [0.2, 2.0, 1]\n",
            )

            result = self.run_python_cli(
                script,
                "--csv",
                str(csv_path),
                "--ls",
                str(ls_path),
                "--env",
                "FTC",
                "--silent",
                "--in-place",
                "--report-json",
            )

            self.assert_success(result, "ls updater multi env")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["updated"], 1)
            updated_text = ls_path.read_text(encoding="utf-8")
            self.assertEqual(
                updated_text,
                "LimitTable [FTC, FTH]\n"
                "12345, TEST, 0, V, [0.5, 1.0, 1], [0.2, 2.0, 1] # FTC: LL 0.1->0.5\n",
            )

    def test_updates_uae7_env_block_lines(self) -> None:
        script = SKILLS_ROOT / "ls-updater" / "ls_updater.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "limits.csv"
            ls_path = root / "sample_env_block.ls"
            self.write_text(
                csv_path,
                "TestNumber,Scaled_LSPL,Scaled_USPL,Scale,ScaledUnit\n"
                "12345,0.5,1.5,0,V\n",
            )
            self.write_text(
                ls_path,
                "    T12345      { FTH(       1.0000V,       0.1000V); FTC(       2.0000V,       0.2000V); BranchStatus= 1    ; Comment = \"Sample\"                 ; }   # Demo\n",
            )

            result = self.run_python_cli(
                script,
                "--csv",
                str(csv_path),
                "--ls",
                str(ls_path),
                "--env",
                "FTC",
                "--silent",
                "--in-place",
                "--report-json",
            )

            self.assert_success(result, "ls updater env block")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["updated"], 1)
            updated_text = ls_path.read_text(encoding="utf-8")
            self.assertIn("FTH(       1.0000V,       0.1000V)", updated_text)
            self.assertIn("FTC(       1.5000V,       0.5000V)", updated_text)
            self.assertIn("FTC: LL 0.2000V->0.5000V; UL 2.0000V->1.5000V", updated_text)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])