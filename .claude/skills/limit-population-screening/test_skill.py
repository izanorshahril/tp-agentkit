from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILLS_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT_PATH))

from _test_support import SKILLS_ROOT, SkillTestCase


class LimitPopulationScreeningSkillTests(SkillTestCase):
    def test_cli_supports_help(self) -> None:
        script = SKILLS_ROOT / "limit-population-screening" / "limit_population_screening.py"

        result = self.run_python_cli(script, "--help")

        self.assert_success(result, "limit population screening help")
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_verify_followup_and_compare_smoke(self) -> None:
        script = SKILLS_ROOT / "limit-population-screening" / "limit_population_screening.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            baseline_ls = root / "baseline.ls"
            current_ls = root / "current.ls"
            stats_csv = root / "stats.csv"
            cases_json = root / "cases.json"
            bulk_csv = root / "bulk.csv"
            review_csv = root / "review.csv"
            membership_json = root / "membership.json"
            verify_json = root / "verify.json"
            verify_md = root / "verify.md"
            followup_json = root / "followup.json"
            followup_md = root / "followup.md"
            followup_csv = root / "action_table.csv"
            compare_json = root / "compare.json"
            compare_md = root / "compare.md"
            compare_csv = root / "compare.csv"
            modified_action_csv = root / "action_table_modified.csv"

            self.write_text(
                baseline_ls,
                "\n".join(
                    [
                        'T100 { FTC(10.0V, 0.0V); Comment = "KEEP"; }',
                        'T101 { FTC(10.0V, 0.0V); Comment = "REVIEW"; }',
                        'T102 { FTC(10.0V, 0.0V); Comment = "DUP"; }',
                    ]
                )
                + "\n",
            )
            self.write_text(
                current_ls,
                "\n".join(
                    [
                        'T100 { FTC(9.0V, 1.0V); Comment = "KEEP"; }',
                        'T101 { FTC(5.6V, 4.4V); Comment = "REVIEW_END"; }',
                        'T102 { FTC(5.3V, 4.7V); Comment = "DUP"; }',
                        'T102 { FTC(5.3V, 4.7V); Comment = "DUP SECOND"; }',
                    ]
                )
                + "\n",
            )
            self.write_text(
                stats_csv,
                "\n".join(
                    [
                        "TestProgram,TestNumber,TestName,ParameterUnit,Average,Deviation,Executions,Failures",
                        "DEMO,100,KEEP_ROW,V,5.0,0.3,100,0",
                        "DEMO,101,REVIEW_ROW,V,5.0,0.3,100,0",
                        "DEMO,102,DUP_ROW,V,5.0,0.2,100,0",
                    ]
                )
                + "\n",
            )
            cases_json.write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "label": "CASE1",
                                "program": "DEMO",
                                "field": "FTC",
                                "baseline_ls": baseline_ls.name,
                                "current_ls": current_ls.name,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            self.write_text(
                bulk_csv,
                "\n".join(
                    [
                        "TestNumber,Parameter,Comment,Cpk_SPL,Fail%",
                        "100,ANALOG_KEEP,,4.2,0",
                        "102,ANALOG_DUP,,0.5,0.10",
                    ]
                )
                + "\n",
            )
            self.write_text(
                review_csv,
                "\n".join(
                    [
                        "TestNumber,Parameter,Comment,Cpk_SPL,Fail%",
                        "101,CONT_SIGNAL_END,hold for review,0.6,0.10",
                    ]
                )
                + "\n",
            )
            membership_json.write_text(
                json.dumps({"CASE1": {"bulk_csv": bulk_csv.name, "review_csv": review_csv.name}}),
                encoding="utf-8",
            )

            verify_result = self.run_python_cli(
                script,
                "verify",
                "--cases-json",
                str(cases_json),
                "--stats-csv",
                str(stats_csv),
                "--dataset-label",
                "smoke",
                "--output-json",
                str(verify_json),
                "--output-md",
                str(verify_md),
                "--report-json",
            )
            self.assert_success(verify_result, "limit population screening verify")
            verify_payload = self.parse_compact_json_output(verify_result)
            self.assertEqual(verify_payload["status"], "ok")
            self.assertEqual(verify_payload["mode"], "verify")
            self.assertEqual(verify_payload["changed_tests_total"], 3)
            self.assertTrue(verify_json.exists())
            self.assertTrue(verify_md.exists())

            followup_result = self.run_python_cli(
                script,
                "followup",
                "--verify-json",
                str(verify_json),
                "--membership-json",
                str(membership_json),
                "--output-json",
                str(followup_json),
                "--output-md",
                str(followup_md),
                "--output-csv",
                str(followup_csv),
                "--report-json",
            )
            self.assert_success(followup_result, "limit population screening followup")
            followup_payload = self.parse_compact_json_output(followup_result)
            self.assertEqual(followup_payload["status"], "ok")
            self.assertEqual(followup_payload["mode"], "followup")
            self.assertEqual(followup_payload["action_counts"]["keep_candidate"], 1)
            self.assertEqual(followup_payload["action_counts"]["manual_review_review_subset"], 1)
            self.assertEqual(followup_payload["action_counts"]["manual_review_duplicate"], 1)
            self.assertTrue(followup_csv.exists())

            with followup_csv.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            for row in rows:
                if row["test_id"] == "100":
                    row["action"] = "revert_candidate"
                    row["action_reason"] = "Modified for compare smoke"
            with modified_action_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)

            compare_result = self.run_python_cli(
                script,
                "compare-populations",
                "--left-action-csv",
                str(followup_csv),
                "--right-action-csv",
                str(modified_action_csv),
                "--left-label",
                "goodpop",
                "--right-label",
                "allpop",
                "--output-json",
                str(compare_json),
                "--output-md",
                str(compare_md),
                "--output-csv",
                str(compare_csv),
                "--report-json",
            )
            self.assert_success(compare_result, "limit population screening compare")
            compare_payload = self.parse_compact_json_output(compare_result)
            self.assertEqual(compare_payload["status"], "ok")
            self.assertEqual(compare_payload["mode"], "compare-populations")
            self.assertEqual(compare_payload["row_count"], 3)
            self.assertEqual(compare_payload["changed_action_count"], 1)
            self.assertEqual(compare_payload["pair_counts"]["keep_candidate -> revert_candidate"], 1)
            self.assertTrue(compare_csv.exists())

    def test_replay_bundle_smoke(self) -> None:
        script = SKILLS_ROOT / "limit-population-screening" / "limit_population_screening.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            baseline_ls = root / "baseline.ls"
            current_ls = root / "current.ls"
            stats_csv = root / "stats.csv"
            cases_json = root / "cases.json"
            bulk_csv = root / "bulk.csv"
            membership_json = root / "membership.json"
            replay_json = root / "replay.json"
            verify_json = root / "verify.json"
            verify_md = root / "verify.md"
            followup_json = root / "followup.json"
            followup_md = root / "followup.md"
            action_csv = root / "action.csv"

            self.write_text(
                baseline_ls,
                'T100 { FTC(10.0V, 0.0V); Comment = "KEEP"; }\n'
                'T101 { FTC(10.0V, 0.0V); Comment = "REVIEW"; }\n',
            )
            self.write_text(
                current_ls,
                'T100 { FTC(9.0V, 1.0V); Comment = "KEEP"; }\n'
                'T101 { FTC(5.6V, 4.4V); Comment = "REVIEW_END"; }\n',
            )
            self.write_text(
                stats_csv,
                "\n".join(
                    [
                        "TestProgram,TestNumber,TestName,ParameterUnit,Average,Deviation,Executions,Failures",
                        "DEMO,100,KEEP_ROW,V,5.0,0.3,100,0",
                        "DEMO,101,REVIEW_ROW,V,5.0,0.3,100,0",
                    ]
                )
                + "\n",
            )
            cases_json.write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "label": "CASE1",
                                "program": "DEMO",
                                "field": "FTC",
                                "baseline_ls": baseline_ls.name,
                                "current_ls": current_ls.name,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            self.write_text(
                bulk_csv,
                "\n".join(
                    [
                        "TestNumber,Parameter,Comment,Cpk_SPL,Fail%",
                        "100,ANALOG_KEEP,,4.2,0",
                        "101,CONT_SIGNAL_END,hold for review,0.6,0.10",
                    ]
                )
                + "\n",
            )
            membership_json.write_text(
                json.dumps({"CASE1": {"bulk_csv": bulk_csv.name}}),
                encoding="utf-8",
            )
            replay_json.write_text(
                json.dumps(
                    {
                        "label": "smoke_bundle",
                        "cases_json": cases_json.name,
                        "membership_json": membership_json.name,
                        "dataset_runs": [
                            {
                                "dataset_label": "smoke",
                                "stats_csv": stats_csv.name,
                                "verify_json": verify_json.name,
                                "verify_md": verify_md.name,
                                "followup_json": followup_json.name,
                                "followup_md": followup_md.name,
                                "action_csv": action_csv.name,
                            }
                        ],
                        "comparisons": [],
                    }
                ),
                encoding="utf-8",
            )

            replay_result = self.run_python_cli(
                script,
                "replay-bundle",
                "--replay-json",
                str(replay_json),
                "--report-json",
            )
            self.assert_success(replay_result, "limit population screening replay bundle")
            replay_payload = self.parse_compact_json_output(replay_result)
            self.assertEqual(replay_payload["status"], "ok")
            self.assertEqual(replay_payload["mode"], "replay-bundle")
            self.assertEqual(replay_payload["replay_label"], "smoke_bundle")
            self.assertEqual(replay_payload["dataset_runs"]["smoke"]["changed_tests_total"], 2)
            self.assertEqual(replay_payload["dataset_runs"]["smoke"]["action_counts"]["manual_review_end_family"], 1)
            self.assertTrue(verify_json.exists())
            self.assertTrue(followup_json.exists())
            self.assertTrue(action_csv.exists())


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])