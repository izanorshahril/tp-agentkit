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


class PinKeyCheckerSkillTests(SkillTestCase):
    def test_cli_supports_help(self) -> None:
        script = SKILLS_ROOT / "pin_key_checker" / "pin_key_checker.py"

        result = self.run_python_cli(script, "--help")

        self.assert_success(result, "pin key checker help")
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_accepts_matching_pin_root_and_measurement_key(self) -> None:
        script = SKILLS_ROOT / "pin_key_checker" / "pin_key_checker.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            tp_dir = Path(temp_dir) / "tp"
            tpl_path = tp_dir / "SubTestPlans" / "sample.tpl"
            self.write_text(
                tpl_path,
                textwrap.dedent(
                    """\
                    StorePinMeasurement {
                        PinName = "VBAT__NA_MMXHB_PMU"
                        MeasValue = "VBAT_main"
                    }
                    """
                ),
            )

            result = self.run_python_cli(script, str(tp_dir), "--report-json")

            self.assert_success(result, "pin key checker")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["mismatches"], 0)
            self.assertEqual(payload["files_checked"], 1)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])