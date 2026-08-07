from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SKILLS_ROOT.parents[1]


def iter_skill_dirs() -> list[Path]:
    return sorted(
        [path for path in SKILLS_ROOT.iterdir() if path.is_dir() and (path / "SKILL.md").exists()],
        key=lambda path: path.name.lower(),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run skill-local regression suites.")
    parser.add_argument("skills", nargs="*", help="Skill folder names to run. Defaults to all skills.")
    parser.add_argument("--all", action="store_true", help="Run all skill suites.")
    parser.add_argument("--list", action="store_true", help="List available skill names and exit.")
    return parser.parse_args()


def resolve_selected_skill_dirs(skill_names: list[str], run_all: bool) -> list[Path]:
    available = {path.name: path for path in iter_skill_dirs()}
    if run_all and skill_names:
        raise SystemExit("Use either --all or explicit skill names, not both.")

    selected_names = sorted(available) if run_all or not skill_names else skill_names
    unknown = [name for name in selected_names if name not in available]
    if unknown:
        raise SystemExit(f"Unknown skill(s): {', '.join(unknown)}")

    missing_entrypoints = [
        name for name in selected_names if not (available[name] / "test_skill.py").exists()
    ]
    if missing_entrypoints:
        raise SystemExit(f"Missing test_skill.py for: {', '.join(missing_entrypoints)}")

    return [available[name] for name in selected_names]


def run_skill_test(skill_dir: Path) -> int:
    print(f"=== {skill_dir.name} ===")
    completed = subprocess.run(
        [sys.executable, str(skill_dir / "test_skill.py")],
        cwd=str(REPO_ROOT),
    )
    print()
    return completed.returncode


def main() -> int:
    args = parse_args()
    skill_dirs = iter_skill_dirs()

    if args.list:
        for skill_dir in skill_dirs:
            print(skill_dir.name)
        return 0

    selected = resolve_selected_skill_dirs(args.skills, args.all)
    failures: list[str] = []

    for skill_dir in selected:
        if run_skill_test(skill_dir) != 0:
            failures.append(skill_dir.name)

    passed = len(selected) - len(failures)
    print(f"Skill suites run: {len(selected)}")
    print(f"Passed: {passed}")
    print(f"Failed: {len(failures)}")
    if failures:
        print(f"Failed skills: {', '.join(failures)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())