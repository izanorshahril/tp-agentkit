from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SKILLS_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT_PATH))

from _test_support import SKILLS_ROOT, SkillTestCase


class RDKJobCloneSkillTests(SkillTestCase):
    def test_cli_supports_help(self) -> None:
        script = SKILLS_ROOT / "rdk_job_clone" / "rdk_job_clone.py"

        result = self.run_python_cli(script, "--help")

        self.assert_success(result, "rdk job clone help")
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_dry_run_reports_expected_cloned_files(self) -> None:
        script = SKILLS_ROOT / "rdk_job_clone" / "rdk_job_clone.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            main_test_plan = root / "MainTestPlan"
            source_job = "JOB123"
            self.write_text(main_test_plan / f"{source_job}.tpl", "TPL JOB123\n")
            self.write_text(main_test_plan / f"{source_job}.cfg", "CFG JOB123\n")
            self.write_text(main_test_plan / f"{source_job}.env", "ENV JOB123\n")
            self.write_text(main_test_plan / f"{source_job}.soc", "SOC JOB123\n")
            self.write_text(root / f"{source_job}.ini", "INI JOB123\n")

            result = self.run_python_cli(
                script,
                "--root",
                str(root),
                "--source-job",
                source_job,
                "--target-job",
                "JOB124",
                "--report-json",
            )

            self.assert_success(result, "rdk job clone")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(len(payload["files"]), 5)
            self.assertFalse((main_test_plan / "JOB124.tpl").exists())


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])