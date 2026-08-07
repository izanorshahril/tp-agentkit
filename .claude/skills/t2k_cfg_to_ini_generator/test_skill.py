from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SKILLS_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT_PATH))

from _test_support import SKILLS_ROOT, SkillTestCase


class T2KCfgToIniGeneratorSkillTests(SkillTestCase):
    def test_autodetects_otpl_from_cfg_and_writes_ini(self) -> None:
        script = SKILLS_ROOT / "t2k_cfg_to_ini_generator" / "t2k_cfg_to_ini_generator.bat"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cfg_path = root / "sample.cfg"
            ini_path = root / "sample.ini"
            self.write_text(
                cfg_path,
                "tplFile=MainTestPlan/sample.tpl\n"
                "envFile=MainTestPlan/sample.env\n"
                "socFile=MainTestPlan/sample.soc\n"
                "stplFile=MainTestPlan/sample.stpl\n",
            )

            result = self.run_cmd_script(script, str(cfg_path))

            self.assert_success(result, "t2k cfg to ini generator")
            self.assertTrue(ini_path.exists())
            ini_text = ini_path.read_text(encoding="utf-8")
            self.assertIn("[TESTPROGRAMDEFINITION]", ini_text)
            self.assertIn("TestProgramFile=MainTestPlan\\sample.tpl", ini_text)
            self.assertIn("SubTestPlanList=MainTestPlan\\sample.stpl", ini_text)
            self.assertIn("SocketFile=MainTestPlan\\sample.soc", ini_text)
            self.assertIn("EnvFile=MainTestPlan\\sample.env", ini_text)
            self.assertIn("KeepPattern=false", ini_text)

    def test_forced_otpl_without_stplfile_fails(self) -> None:
        script = SKILLS_ROOT / "t2k_cfg_to_ini_generator" / "t2k_cfg_to_ini_generator.bat"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cfg_path = root / "broken.cfg"
            ini_path = root / "broken.ini"
            self.write_text(
                cfg_path,
                "tplFile=MainTestPlan/sample.tpl\n"
                "envFile=MainTestPlan/sample.env\n"
                "socFile=MainTestPlan/sample.soc\n",
            )

            result = self.run_cmd_script(script, str(cfg_path), "OTPL")

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(ini_path.exists())


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])