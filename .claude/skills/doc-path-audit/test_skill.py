from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SKILLS_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT_PATH))

from _test_support import SKILLS_ROOT, SkillTestCase


class DocPathAuditSkillTests(SkillTestCase):
    def test_shared_io_support_scans_targets_and_displays_workspace_relative_paths(self) -> None:
        module = self.load_module(
            "io_support_scan_under_test",
            SKILLS_ROOT / "_io_support.py",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs = root / "docs"
            references = root / "references"
            self.write_text(docs / "note.md", "sample\n")
            self.write_text(references / "sample.txt", "sample\n")

            scanned = module.iter_scan_files(
                [str(docs), str(references / "sample.txt")],
                (".md", ".txt"),
            )

            self.assertEqual(
                [path.name for path in scanned],
                ["note.md", "sample.txt"],
            )
            self.assertEqual(module.display_path(docs / "note.md", root), "docs/note.md")
            self.assertEqual(module.iter_relative_files(docs, "*.md"), ["note.md"])

    def test_cli_supports_help(self) -> None:
        script = SKILLS_ROOT / "doc-path-audit" / "doc_path_audit.py"

        result = self.run_python_cli(script, "--help")

        self.assert_success(result, "doc path audit help")
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_classifies_missing_and_non_missing_reference_kinds(self) -> None:
        script = SKILLS_ROOT / "doc-path-audit" / "doc_path_audit.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "references" / "log").mkdir(parents=True)
            (root / "testprogram" / "sample").mkdir(parents=True)
            (root / "references" / "log" / "SystemController_Error.log").write_text(
                "sample",
                encoding="utf-8",
            )

            self.write_text(
                root / "docs" / "audit.md",
                textwrap.dedent(
                    """\
                    - `references/log/SystemController_Error.log`
                    - `references/missing.xlsx`
                    - historical input: `references/old.xlsx` (not present in current workspace)
                    - use `references/<limits-file>.csv`
                    - `testprogram/sample`
                    - python tool.py input.txt --output .claude/artifacts/current_task/report.md
                    """
                ),
            )
            self.write_text(
                root / "docs" / "report.json",
                json.dumps(
                    {
                        "report_path": "references/missing.html",
                        "baseline": "testprogram/sample",
                    }
                ),
            )

            result = self.run_python_cli(
                script,
                str(root / "docs"),
                "--workspace-root",
                str(root),
                "--report-json",
            )

            self.assert_success(result, "doc path audit")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["status"], "success")
            self.assertEqual(payload["scanned_files"], 2)
            self.assertEqual(payload["counts"], {
                "existing": 3,
                "historical": 1,
                "missing": 2,
                "output_path": 1,
                "placeholder": 1,
            })
            self.assertEqual(payload["unresolved_count"], 2)
            unresolved_paths = {item["path"] for item in payload["unresolved"]}
            self.assertEqual(
                unresolved_paths,
                {"references/missing.xlsx", "references/missing.html"},
            )

    def test_handles_markdown_links_and_backticked_paths_with_spaces(self) -> None:
        script = SKILLS_ROOT / "doc-path-audit" / "doc_path_audit.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "references" / "Beyond Compare").mkdir(parents=True)
            (root / "testprogram" / "sample").mkdir(parents=True)
            (root / "references" / "Beyond Compare" / "Sample_Diff.html").write_text(
                "sample",
                encoding="utf-8",
            )
            (root / "testprogram" / "sample" / "Main.tpl").write_text(
                "sample",
                encoding="utf-8",
            )

            self.write_text(
                root / "docs" / "links.md",
                textwrap.dedent(
                    """\
                    - [sample flow](testprogram/sample/Main.tpl#L10)
                    - `references/Beyond Compare/Sample_Diff.html`
                    """
                ),
            )

            result = self.run_python_cli(
                script,
                str(root / "docs"),
                "--workspace-root",
                str(root),
                "--report-json",
            )

            self.assert_success(result, "doc path audit markdown link handling")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["counts"], {
                "existing": 2,
                "historical": 0,
                "missing": 0,
                "output_path": 0,
                "placeholder": 0,
            })
            self.assertEqual(payload["unresolved_count"], 0)

    def test_keeps_existing_backticked_paths_with_and_in_filename(self) -> None:
        script = SKILLS_ROOT / "doc-path-audit" / "doc_path_audit.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "references").mkdir(parents=True)
            (root / "references" / "Board and Bench.txt").write_text(
                "sample",
                encoding="utf-8",
            )

            self.write_text(
                root / "docs" / "and-path.md",
                "- `references/Board and Bench.txt`\n",
            )

            result = self.run_python_cli(
                script,
                str(root / "docs"),
                "--workspace-root",
                str(root),
                "--report-json",
            )

            self.assert_success(result, "doc path audit preserves filenames containing and")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["counts"], {
                "existing": 1,
                "historical": 0,
                "missing": 0,
                "output_path": 0,
                "placeholder": 0,
            })
            self.assertEqual(payload["unresolved_count"], 0)

    def test_uses_nearby_historical_note_for_following_bullets(self) -> None:
        script = SKILLS_ROOT / "doc-path-audit" / "doc_path_audit.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_text(
                root / "docs" / "history.md",
                textwrap.dedent(
                    """\
                    Current-workspace note: the files below are not retained in the current workspace snapshot.

                    - `references/stdf/missing-loop.txt`
                    """
                ),
            )

            result = self.run_python_cli(
                script,
                str(root / "docs"),
                "--workspace-root",
                str(root),
                "--report-json",
            )

            self.assert_success(result, "doc path audit historical context handling")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["counts"], {
                "existing": 0,
                "historical": 1,
                "missing": 0,
                "output_path": 0,
                "placeholder": 0,
            })
            self.assertEqual(payload["unresolved_count"], 0)

    def test_classifies_output_locations_and_wildcard_patterns(self) -> None:
        script = SKILLS_ROOT / "doc-path-audit" / "doc_path_audit.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_text(
                root / "docs" / "outputs.md",
                textwrap.dedent(
                    """\
                    - output folder: `.claude/artifacts/current_task/out/`
                    - rebuilt folder: `.claude/artifacts/current_task/rebuilt/`
                    - example artifact path: `.claude/artifacts/current_task/example/Main.ls.patch`
                    - captured output: `.claude/artifacts/current_task/out.json`
                    - `references/_tmp_blank_only_review.html`
                    - tracked wildcard surface: `.claude/skills/*.py`
                    """
                ),
            )

            result = self.run_python_cli(
                script,
                str(root / "docs"),
                "--workspace-root",
                str(root),
                "--report-json",
            )

            self.assert_success(result, "doc path audit output and wildcard handling")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["counts"], {
                "existing": 0,
                "historical": 0,
                "missing": 0,
                "output_path": 5,
                "placeholder": 1,
            })
            self.assertEqual(payload["unresolved_count"], 0)

    def test_classifies_quoted_output_path_with_spaces_as_output_path(self) -> None:
        script = SKILLS_ROOT / "doc-path-audit" / "doc_path_audit.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_text(
                root / "docs" / "quoted-output.md",
                'Run: tool --output ".claude/artifacts/current_task/My Report.md"\n',
            )

            result = self.run_python_cli(
                script,
                str(root / "docs"),
                "--workspace-root",
                str(root),
                "--report-json",
            )

            self.assert_success(result, "doc path audit quoted output path handling")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["counts"], {
                "existing": 0,
                "historical": 0,
                "missing": 0,
                "output_path": 1,
                "placeholder": 0,
            })
            self.assertEqual(payload["unresolved_count"], 0)

    def test_splits_multiple_paths_and_classifies_examples_and_generated_artifacts(self) -> None:
        script = SKILLS_ROOT / "doc-path-audit" / "doc_path_audit.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "testprogram" / "UR7T_0016").mkdir(parents=True)
            (root / "testprogram" / "UR7S_0021").mkdir(parents=True)

            self.write_text(
                root / "docs" / "mixed.md",
                textwrap.dedent(
                    """\
                    source: "Verified duplicate-test implementation in testprogram/UR7T_0016 and testprogram/UR7S_0021"
                    When asked "what are the relative tests in testprogram/&lt;program&gt;?"
                    Example: testprogram/UR78FA008BE01_0134
                    CREATE .claude/artifacts/current_task/plan.md with:
                    python tool.py --csv references/sample.csv --list references/list.h
                    """
                ),
            )

            result = self.run_python_cli(
                script,
                str(root / "docs"),
                "--workspace-root",
                str(root),
                "--report-json",
            )

            self.assert_success(result, "doc path audit example and generated artifact handling")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["counts"], {
                "existing": 2,
                "historical": 0,
                "missing": 0,
                "output_path": 1,
                "placeholder": 4,
            })
            self.assertEqual(payload["unresolved_count"], 0)

    def test_treats_skill_current_task_examples_as_placeholders(self) -> None:
        script = SKILLS_ROOT / "doc-path-audit" / "doc_path_audit.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_doc = root / ".claude" / "skills" / "example" / "SKILL.md"
            self.write_text(
                skill_doc,
                textwrap.dedent(
                    """\
                    python tool.py \
                      .claude/artifacts/current_task/repo-learning-summary.md \
                      --in-place \
                      --report-json
                    """
                ),
            )

            result = self.run_python_cli(
                script,
                str(root / ".claude" / "skills"),
                "--workspace-root",
                str(root),
                "--report-json",
            )

            self.assert_success(result, "doc path audit skill current-task example handling")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["counts"], {
                "existing": 0,
                "historical": 0,
                "missing": 0,
                "output_path": 0,
                "placeholder": 1,
            })
            self.assertEqual(payload["unresolved_count"], 0)

    def test_treats_archive_machine_output_paths_as_historical(self) -> None:
        script = SKILLS_ROOT / "doc-path-audit" / "doc_path_audit.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive_json = root / ".claude" / "artifacts" / "archive" / "report.json"
            self.write_text(
                archive_json,
                json.dumps({"report_path": "references/missing.html"}),
            )

            result = self.run_python_cli(
                script,
                str(root / ".claude" / "artifacts" / "archive"),
                "--workspace-root",
                str(root),
                "--report-json",
            )

            self.assert_success(result, "doc path audit archive machine output handling")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["counts"], {
                "existing": 0,
                "historical": 1,
                "missing": 0,
                "output_path": 0,
                "placeholder": 0,
            })
            self.assertEqual(payload["unresolved_count"], 0)

    def test_treats_archive_markdown_paths_as_historical(self) -> None:
        script = SKILLS_ROOT / "doc-path-audit" / "doc_path_audit.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive_note = root / ".claude" / "artifacts" / "archive" / "note.md"
            self.write_text(
                archive_note,
                textwrap.dedent(
                    """\
                    Historical delivery notes:
                    - `.claude/artifacts/current_task/old-note.md`
                    - `testprogram/URX8_0002_Unconfirmed`
                    - `USER_WORKFLOW.md`
                    """
                ),
            )

            result = self.run_python_cli(
                script,
                str(root / ".claude" / "artifacts" / "archive"),
                "--workspace-root",
                str(root),
                "--report-json",
            )

            self.assert_success(result, "doc path audit archive markdown handling")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["counts"], {
                "existing": 0,
                "historical": 3,
                "missing": 0,
                "output_path": 0,
                "placeholder": 0,
            })
            self.assertEqual(payload["unresolved_count"], 0)

    def test_classifies_relative_archive_source_paths_as_historical(self) -> None:
        module = self.load_module(
            "doc_path_audit_relative_archive",
            SKILLS_ROOT / "doc-path-audit" / "doc_path_audit.py",
        )

        classification, exists = module.classify_candidate(
            "testprogram/URX8_0002_Unconfirmed",
            "- `testprogram/URX8_0002_Unconfirmed`",
            ["- `testprogram/URX8_0002_Unconfirmed`"],
            Path("C:/Temp/nonexistent-workspace"),
            set(),
            Path(".claude/artifacts/archive/note.md"),
        )

        self.assertEqual(classification, "historical")
        self.assertFalse(exists)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])