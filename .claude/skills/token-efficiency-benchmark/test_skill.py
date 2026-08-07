from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


SKILLS_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT_PATH))

from _test_support import SKILLS_ROOT, SkillTestCase


class TokenEfficiencyBenchmarkSkillTests(SkillTestCase):
    def test_cli_supports_help(self) -> None:
        script = SKILLS_ROOT / "token-efficiency-benchmark" / "token_efficiency_benchmark.py"

        result = self.run_python_cli(script, "--help")

        self.assert_success(result, "token efficiency benchmark help")
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_writes_markdown_report(self) -> None:
        script = SKILLS_ROOT / "token-efficiency-benchmark" / "token_efficiency_benchmark.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "token-efficiency-proof.md"

            result = self.run_python_cli(
                script,
                "--output-markdown",
                str(output_path),
                timeout=120,
            )

            self.assert_success(result, "token efficiency benchmark")
            self.assertTrue(output_path.exists())
            report_text = output_path.read_text(encoding="utf-8")
            self.assertIn("# TP-AgentKit Token Efficiency Proof", report_text)
            self.assertIn(f"Date: {datetime.now(timezone.utc).date().isoformat()}", report_text)
            self.assertIn("## Runtime Sanity Results", report_text)
            self.assertIn("token_efficiency_benchmark", report_text)
            self.assertIn(
                ".claude/skills/token-efficiency-benchmark/token_efficiency_benchmark.py",
                report_text,
            )

    def test_skip_runtime_sanity_omits_runtime_section(self) -> None:
        script = SKILLS_ROOT / "token-efficiency-benchmark" / "token_efficiency_benchmark.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "token-efficiency-proof.md"

            result = self.run_python_cli(
                script,
                "--skip-runtime-sanity",
                "--output-markdown",
                str(output_path),
                timeout=120,
            )

            self.assert_success(result, "token efficiency benchmark without runtime sanity")
            report_text = output_path.read_text(encoding="utf-8")
            self.assertNotIn("## Runtime Sanity Results", report_text)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])