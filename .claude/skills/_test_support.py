from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from importlib.machinery import ModuleSpec
from pathlib import Path
from typing import Any, cast


SKILLS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SKILLS_ROOT.parents[1]


class SkillTestCase(unittest.TestCase):
    maxDiff = None

    def run_python_cli(
        self,
        script: Path,
        *args: str,
        cwd: Path | None = None,
        timeout: int = 45,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), *args],
            cwd=str(cwd or REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def run_cmd_script(
        self,
        script: Path,
        *args: str,
        cwd: Path | None = None,
        timeout: int = 45,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["cmd.exe", "/c", str(script), *args],
            cwd=str(cwd or REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def assert_success(self, result: subprocess.CompletedProcess[str], context: str) -> None:
        if result.returncode != 0:
            self.fail(
                f"{context} failed with exit code {result.returncode}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )

    def write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def parse_compact_json_output(self, result: subprocess.CompletedProcess[str]) -> Any:
        text = result.stdout.strip()
        self.assertTrue(text, "Expected JSON output on stdout.")
        self.assertNotIn("\n", text)
        self.assertNotIn("\r", text)
        return cast(Any, json.loads(text))

    def read_skill_markdown(self, skill_name: str) -> str:
        return (SKILLS_ROOT / skill_name / "SKILL.md").read_text(encoding="utf-8")

    def load_module(self, module_name: str, module_path: Path) -> Any:
        raw_spec = importlib.util.spec_from_file_location(module_name, module_path)
        self.assertIsNotNone(raw_spec)
        spec = cast(ModuleSpec, raw_spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module


__all__ = ["REPO_ROOT", "SKILLS_ROOT", "SkillTestCase"]