from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SKILLS_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT_PATH))

from _test_support import REPO_ROOT, SKILLS_ROOT, SkillTestCase


def resolve_local_spl_reference(pattern: str) -> Path:
    matches = sorted((REPO_ROOT / "references" / "SPL").glob(pattern))
    if len(matches) != 1:
        raise AssertionError(f"Expected exactly one local SPL reference matching {pattern}, found {len(matches)}")
    return matches[0]


class SPLLimitWorkflowSkillTests(SkillTestCase):
    def test_shared_io_support_loads_cp1252_csv_rows_and_display_path(self) -> None:
        module = self.load_module(
            "io_support_under_test",
            SKILLS_ROOT / "_io_support.py",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "approved_spl.csv"
            csv_path.write_bytes(
                "TestNumber,Comment\n12345,Price € guard\n".encode("cp1252")
            )

            headers, first_row = module.read_csv_preview(csv_path)
            rows = module.read_csv_dict_rows(csv_path)

            self.assertEqual(headers, ["TestNumber", "Comment"])
            self.assertEqual(first_row, ["12345", "Price € guard"])
            self.assertEqual(rows[0]["Comment"], "Price € guard")
            self.assertEqual(module.to_display_path(csv_path), str(csv_path).replace("\\", "/"))

    def test_cli_supports_help(self) -> None:
        script = SKILLS_ROOT / "spl-limit-workflow" / "spl_limit_workflow.py"

        result = self.run_python_cli(script, "--help")

        self.assert_success(result, "spl limit workflow help")
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_reports_ready_for_ls_updater_when_anchors_are_complete(self) -> None:
        script = SKILLS_ROOT / "spl-limit-workflow" / "spl_limit_workflow.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "approved_spl.csv"
            ls_path = root / "Main.ls"
            self.write_text(
                csv_path,
                "TestNumber,Scaled_LSPL,Scaled_USPL,Scale,ScaledUnit\n"
                "12345,0.5,1.5,,V\n",
            )
            self.write_text(ls_path, "12345, TEST, 0, V, [0.1, 1.0, 1]\n")

            result = self.run_python_cli(
                script,
                "--input",
                str(csv_path),
                "--source-tp",
                "testprogram/UAE7FC016CA01_0012",
                "--ls",
                str(ls_path),
                "--env",
                "FTC",
                "--approval-status",
                "approved",
                "--target-handling",
                "copied-revision",
                "--report-json",
            )

        self.assert_success(result, "spl limit workflow ready path")
        payload = self.parse_compact_json_output(result)
        self.assertEqual(payload["workflow_stage"], "ready_for_ls_updater")
        self.assertTrue(payload["ready_for_update"])
        self.assertEqual(payload["primary_input"]["kind"], "spl_csv")
        self.assertFalse(payload["missing_anchors"])
        self.assertIn(".claude/skills/ls-updater/ls_updater.py", payload["recommended_command"])
        self.assertIn("--env FTC", payload["recommended_command"])

    def test_scope_screen_requires_review_before_bulk_update(self) -> None:
        script = SKILLS_ROOT / "spl-limit-workflow" / "spl_limit_workflow.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "approved_spl.csv"
            ls_path = root / "Main.ls"
            self.write_text(
                csv_path,
                "TestNumber,Parameter,Scaled_LSPL,Scaled_USPL,Scale,ScaledUnit,Comment,Cpkn_SPL,NumGoodFails,Fail%\n"
                "105,OPEN_GND32,-0.95,-0.40,0,V,JF success,2.80,5,0.00010%\n"
                "106,SHORT_VDD,0,0.25,0,V,JF success,4.10,0,0.00000%\n"
                "107,CONT_BDG1_END,-0.80,-0.35,0,V,JF success,4.10,0,0.00000%\n"
                "108,ADCOFFS_MATCHSI,0,1,0,LSB,Modality=1 is insufficient,4.10,0,0.00000%\n"
                "109,KELVIN_SENSE,1,2,0,V,No valid data values,4.10,0,0.00000%\n"
                "110,IDD_DELTA,1,2,0,mA,JF success,4.10,0,0.00000%\n"
                "111,TEMP_MON,-40,125,0,C,JF success,4.10,0,0.00000%\n",
            )
            self.write_text(ls_path, "105, TEST, 0, V, [0.1, 1.0, 1]\n")

            result = self.run_python_cli(
                script,
                "--input",
                str(csv_path),
                "--source-tp",
                "testprogram/UAE7FC016CA01_0012",
                "--ls",
                str(ls_path),
                "--env",
                "FTC",
                "--approval-status",
                "approved",
                "--target-handling",
                "copied-revision",
                "--report-json",
            )

        self.assert_success(result, "spl limit workflow scope screen path")
        payload = self.parse_compact_json_output(result)
        self.assertEqual(payload["workflow_stage"], "scope_review_needed")
        self.assertFalse(payload["ready_for_update"])
        self.assertFalse(payload["recommended_command"])
        self.assertIn("generic bulk SPL update", payload["blockers"][0])
        screening = payload["primary_input"]["scope_screening"]
        self.assertTrue(screening["requires_scope_review"])
        self.assertGreaterEqual(screening["flag_counts"]["continuity_tests"], 1)
        self.assertGreaterEqual(screening["flag_counts"]["continuity_end_tests"], 1)
        self.assertGreaterEqual(screening["flag_counts"]["kelvin_tests"], 1)
        self.assertGreaterEqual(screening["flag_counts"]["delta_tests"], 1)
        self.assertGreaterEqual(screening["flag_counts"]["matching_tests"], 1)
        self.assertGreaterEqual(screening["flag_counts"]["temperature_tests"], 1)
        self.assertGreaterEqual(screening["flag_counts"]["low_cpk_with_observed_fails"], 1)
        self.assertGreaterEqual(screening["flag_counts"]["yield_loss_above_target"], 1)
        checklist = {item["id"]: item for item in payload["intake_checklist"]}
        self.assertEqual(checklist["bulk_scope_screen"]["status"], "warn")
        self.assertEqual(checklist["continuity_split"]["status"], "warn")
        self.assertEqual(checklist["cpk_yield_review"]["status"], "warn")
        self.assertIn("continuity_end_tests", checklist["cpk_yield_review"]["flag_counts"])

    def test_can_write_conservative_screened_bulk_and_review_csvs(self) -> None:
        script = SKILLS_ROOT / "spl-limit-workflow" / "spl_limit_workflow.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "approved_spl.csv"
            ls_path = root / "Main.ls"
            bulk_path = root / "approved_spl.bulk.csv"
            review_path = root / "approved_spl.review.csv"
            self.write_text(
                csv_path,
                "TestNumber,Parameter,Scaled_LSPL,Scaled_USPL,Scale,ScaledUnit,Comment,Cpkn_SPL,NumGoodFails,Fail%\n"
                "105,REG_VOUT,0.9,1.1,0,V,JF success,4.10,0,0.00000%\n"
                "106,SHORT_VDD,0,0.25,0,V,JF success,4.10,0,0.00000%\n",
            )
            self.write_text(ls_path, "105, TEST, 0, V, [0.1, 1.0, 1]\n")

            result = self.run_python_cli(
                script,
                "--input",
                str(csv_path),
                "--source-tp",
                "testprogram/UAE7FC016CA01_0012",
                "--ls",
                str(ls_path),
                "--env",
                "FTC",
                "--approval-status",
                "approved",
                "--target-handling",
                "copied-revision",
                "--bulk-output",
                str(bulk_path),
                "--review-output",
                str(review_path),
                "--report-json",
            )

            self.assert_success(result, "spl limit workflow screened export path")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["workflow_stage"], "scope_review_needed")
            screened_outputs = payload["screened_outputs"]
            self.assertEqual(screened_outputs["status"], "ok")
            self.assertEqual(screened_outputs["bulk_row_count"], 1)
            self.assertEqual(screened_outputs["review_row_count"], 1)
            self.assertTrue(screened_outputs["bulk_ready_for_update"])
            self.assertIn(str(bulk_path).replace("\\", "/"), screened_outputs["screened_recommended_command"])

            bulk_result = self.run_python_cli(
                script,
                "--input",
                str(bulk_path),
                "--source-tp",
                "testprogram/UAE7FC016CA01_0012",
                "--ls",
                str(ls_path),
                "--env",
                "FTC",
                "--approval-status",
                "approved",
                "--target-handling",
                "copied-revision",
                "--report-json",
            )

        self.assert_success(bulk_result, "spl limit workflow screened bulk ready path")
        bulk_payload = self.parse_compact_json_output(bulk_result)
        self.assertEqual(bulk_payload["workflow_stage"], "ready_for_ls_updater")
        self.assertTrue(bulk_payload["ready_for_update"])

    def test_screened_bulk_excludes_rows_the_target_ls_cannot_update(self) -> None:
        script = SKILLS_ROOT / "spl-limit-workflow" / "spl_limit_workflow.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "approved_spl.csv"
            ls_path = root / "Main.ls"
            bulk_path = root / "approved_spl.bulk.csv"
            review_path = root / "approved_spl.review.csv"
            self.write_text(
                csv_path,
                "TestNumber,Parameter,Scaled_LSPL,Scaled_USPL,Scale,ScaledUnit,Comment,Cpkn_SPL,NumGoodFails,Fail%\n"
                "105,REG_VOUT_105,0.9,1.1,0,V,JF success,4.10,0,0.00000%\n"
                "106,REG_VOUT_106,0.9,1.1,0,V,JF success,4.10,0,0.00000%\n"
                "107,REG_VOUT_107,0.9,1.1,0,V,JF success,4.10,0,0.00000%\n"
                "108,REG_VOUT_108,0.9,1.1,0,V,JF success,4.10,0,0.00000%\n"
                "109,REG_VOUT_109,0.9,1.1,0,V,JF success,4.10,0,0.00000%\n",
            )
            self.write_text(
                ls_path,
                "T105 { FTC(1.000V, 0.500V); }\n"
                "# T106 { FTC(1.000V, 0.500V); }\n"
                "T107 { FTH(1.000V, 0.500V); }\n"
                "T108 { FTC(1.000V); }\n",
            )

            result = self.run_python_cli(
                script,
                "--input",
                str(csv_path),
                "--source-tp",
                "testprogram/UAE7FC016CA01_0012",
                "--ls",
                str(ls_path),
                "--env",
                "FTC",
                "--approval-status",
                "approved",
                "--target-handling",
                "copied-revision",
                "--bulk-output",
                str(bulk_path),
                "--review-output",
                str(review_path),
                "--report-json",
            )

            self.assert_success(result, "spl limit workflow ls-aware screened export path")
            payload = self.parse_compact_json_output(result)
            screened_outputs = payload["screened_outputs"]
            self.assertEqual(screened_outputs["status"], "ok")
            self.assertEqual(screened_outputs["bulk_row_count"], 1)
            self.assertEqual(screened_outputs["review_row_count"], 4)
            self.assertTrue(screened_outputs["ls_screening_enabled"])
            self.assertEqual(
                screened_outputs["review_reason_counts"],
                {
                    "absent_from_main": 1,
                    "commented_in_ls": 1,
                    "missing_ll_ul_in_ls": 1,
                    "target_env_missing_in_ls": 1,
                },
            )

            bulk_result = self.run_python_cli(
                script,
                "--input",
                str(bulk_path),
                "--source-tp",
                "testprogram/UAE7FC016CA01_0012",
                "--ls",
                str(ls_path),
                "--env",
                "FTC",
                "--approval-status",
                "approved",
                "--target-handling",
                "copied-revision",
                "--report-json",
            )

        self.assert_success(bulk_result, "spl limit workflow ls-aware screened bulk ready path")
        bulk_payload = self.parse_compact_json_output(bulk_result)
        self.assertEqual(bulk_payload["workflow_stage"], "ready_for_ls_updater")
        self.assertTrue(bulk_payload["ready_for_update"])

    def test_keeps_unknown_approval_in_review_stage(self) -> None:
        script = SKILLS_ROOT / "spl-limit-workflow" / "spl_limit_workflow.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "candidate_spl.csv"
            self.write_text(
                csv_path,
                "TestNumber,Scaled_LSPL,Scaled_USPL,Scale,ScaledUnit\n"
                "12345,0.5,1.5,,V\n",
            )

            result = self.run_python_cli(
                script,
                "--input",
                str(csv_path),
                "--report-json",
            )

        self.assert_success(result, "spl limit workflow review stage")
        payload = self.parse_compact_json_output(result)
        self.assertEqual(payload["workflow_stage"], "review_before_update")
        self.assertFalse(payload["ready_for_update"])
        self.assertIn("approval_status", payload["missing_anchors"])
        self.assertIn("review-only", payload["recommended_follow_up"][0].lower())
        self.assertFalse(payload["recommended_command"])

    def test_flags_workbook_as_export_needed(self) -> None:
        script = SKILLS_ROOT / "spl-limit-workflow" / "spl_limit_workflow.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workbook_path = root / "spl_export.xlsx"
            self.write_text(workbook_path, "placeholder")

            result = self.run_python_cli(
                script,
                "--input",
                str(workbook_path),
                "--report-json",
            )

        self.assert_success(result, "spl limit workflow workbook stage")
        payload = self.parse_compact_json_output(result)
        self.assertEqual(payload["workflow_stage"], "export_csv_needed")
        self.assertFalse(payload["ready_for_update"])
        self.assertEqual(payload["primary_input"]["kind"], "ye_workbook")
        self.assertIn("Export the approved workbook to CSV before using ls-updater.", payload["blockers"])

    def test_real_reference_spl_csvs_expose_schema_hints(self) -> None:
        script = SKILLS_ROOT / "spl-limit-workflow" / "spl_limit_workflow.py"

        cases = [
            (REPO_ROOT / "references" / "SPL" / "SPL.UAE7_FH_SPL_16April26.csv", "%Fail", ""),
            (REPO_ROOT / "references" / "SPL" / "SPL.UAE7_FC_SPL_17April26.csv", "Fail%", ""),
            (REPO_ROOT / "references" / "SPL" / "SPL.SPL_UR7B_FT.20251030_170637.csv", "", ""),
            (REPO_ROOT / "references" / "SPL" / "SPL.SPL_UR7E_FT_300K_12Nov25.20251112_102355_Update.csv", "%Fail", ""),
            (REPO_ROOT / "references" / "SPL" / "SPL.UR6E_FT_SPL_300K.20251028_105041.csv", "%Fail", ""),
            (resolve_local_spl_reference("SPL_UBE6_FT_Rev_0014_*_Final.csv"), "Good Fail%", "Seq"),
        ]

        for csv_path, expected_fail_header, expected_row_order_column in cases:
            result = self.run_python_cli(
                script,
                "--input",
                str(csv_path),
                "--report-json",
            )

            self.assert_success(result, f"spl limit workflow real schema path {csv_path.name}")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["primary_input"]["kind"], "spl_csv")
            self.assertEqual(payload["workflow_stage"], "review_before_update")
            schema_summary = payload["primary_input"]["schema_summary"]
            self.assertEqual(schema_summary["test_program_column"], "TestProgram")
            self.assertEqual(schema_summary["update_limit_columns"], ["Scaled_LSPL", "Scaled_USPL"])
            self.assertEqual(schema_summary["current_limit_columns"], ["Scaled_LSL", "Scaled_USL"])
            self.assertEqual(schema_summary["fail_column"], expected_fail_header)
            self.assertEqual(schema_summary["row_order_column"], expected_row_order_column)
            self.assertIn("ScaledUnit", schema_summary["unit_columns"])
            self.assertIn("Scale", schema_summary["unit_columns"])

    def test_scope_screen_reads_good_fail_percent_alias(self) -> None:
        script = SKILLS_ROOT / "spl-limit-workflow" / "spl_limit_workflow.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "approved_spl.csv"
            ls_path = root / "Main.ls"
            self.write_text(
                csv_path,
                "Seq,TestProgram,TestNumber,Parameter,Scaled_LSPL,Scaled_USPL,ScaledUnit,Comment,Cpkn_SPL,NumGoodFails,Good Fail%,Scale\n"
                "1,UBE6FH108AA101,1000,SHORT_VDD,0,1,uA,JF success,4.10,0,0.00000%,6\n"
                "2,UBE6FH108AA101,1001,IDD_DELTA,0,1,uA,JF success,2.80,3,0.00010%,6\n",
            )
            self.write_text(ls_path, "1000, TEST, 0, V, [0.1, 1.0, 1]\n")

            result = self.run_python_cli(
                script,
                "--input",
                str(csv_path),
                "--source-tp",
                "testprogram/UBE8FH008AA01_0004",
                "--ls",
                str(ls_path),
                "--env",
                "FTH",
                "--approval-status",
                "approved",
                "--target-handling",
                "copied-revision",
                "--report-json",
            )

        self.assert_success(result, "spl limit workflow good fail alias path")
        payload = self.parse_compact_json_output(result)
        self.assertEqual(payload["workflow_stage"], "scope_review_needed")
        screening = payload["primary_input"]["scope_screening"]
        self.assertGreaterEqual(screening["flag_counts"]["delta_tests"], 1)
        self.assertGreaterEqual(screening["flag_counts"]["low_cpk_with_observed_fails"], 1)
        self.assertGreaterEqual(screening["flag_counts"]["yield_loss_above_target"], 1)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])