from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SKILLS_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT_PATH))

from _test_support import SKILLS_ROOT, SkillTestCase


class LocalArtifactCompressSkillTests(SkillTestCase):
    def test_cli_supports_help(self) -> None:
        script = SKILLS_ROOT / "local-artifact-compress" / "local_artifact_compress.py"

        result = self.run_python_cli(script, "--help")

        self.assert_success(result, "local artifact compress help")
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_compacts_markdown_and_preserves_heading(self) -> None:
        script = SKILLS_ROOT / "local-artifact-compress" / "local_artifact_compress.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "artifact.md"
            output_path = root / "artifact.compact.md"
            self.write_text(
                input_path,
                "# Title\n\nPlease note that this is a very simple paragraph in order to demonstrate how the tool can reduce filler wording.\n",
            )

            result = self.run_python_cli(script, str(input_path), "--output", str(output_path), "--json")

            self.assert_success(result, "local artifact compress")
            payload = self.parse_compact_json_output(result)
            self.assertTrue(payload["valid"])
            self.assertTrue(output_path.exists())
            self.assertIn("# Title", output_path.read_text(encoding="utf-8"))

    def test_accepts_report_json_alias(self) -> None:
        script = SKILLS_ROOT / "local-artifact-compress" / "local_artifact_compress.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "artifact.md"
            output_path = root / "artifact.compact.md"
            self.write_text(
                input_path,
                "# Title\n\nPlease note that this is a very simple paragraph in order to demonstrate how the tool can reduce filler wording.\n",
            )

            result = self.run_python_cli(script, str(input_path), "--output", str(output_path), "--report-json")

            self.assert_success(result, "local artifact compress report-json alias")
            payload = self.parse_compact_json_output(result)
            self.assertTrue(payload["valid"])
            self.assertTrue(output_path.exists())
            self.assertIn("# Title", output_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])