from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SKILLS_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT_PATH))

from _test_support import REPO_ROOT, SKILLS_ROOT, SkillTestCase


class DiffConverterSkillTests(SkillTestCase):
    def test_cli_entry_points_support_help(self) -> None:
        scripts = [
            SKILLS_ROOT / "diff-converter" / "html_diff_converter.py",
            SKILLS_ROOT / "diff-converter" / "winmerge_html_diff.py",
        ]

        for script in scripts:
            with self.subTest(script=script.relative_to(REPO_ROOT).as_posix()):
                result = self.run_python_cli(script, "--help")
                self.assert_success(result, f"help for {script.name}")
                self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_html_diff_converter_smoke(self) -> None:
        script = SKILLS_ROOT / "diff-converter" / "html_diff_converter.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "sample.html"
            output_path = root / "sample.patch"
            self.write_text(
                report,
                textwrap.dedent(
                    """\
                    <html>
                    <head><title>Sample TP Diff</title></head>
                    <body>
                    Left base folder: C:\\baseline<br>
                    Right base folder: C:\\current<br>
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

            result = self.run_python_cli(script, str(report), "--format", "patch", "--output", str(output_path))

            self.assert_success(result, "html diff converter smoke")
            self.assertTrue(output_path.exists())


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])