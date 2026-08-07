from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Clone an RDK launch-package file set from one job token to another.")
    parser.add_argument("--root", required=True, help="TP root folder")
    parser.add_argument("--source-job", required=True, help="Existing job token to clone from")
    parser.add_argument("--target-job", required=True, help="New job token to create")
    parser.add_argument("--write", action="store_true", help="Write cloned files; otherwise dry-run only")
    parser.add_argument("--report-json", action="store_true", help="Emit one-line JSON summary")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        raise SystemExit(f"Root folder not found: {root}")

    source_job = args.source_job
    target_job = args.target_job

    source_files = [
        root / "MainTestPlan" / f"{source_job}.tpl",
        root / "MainTestPlan" / f"{source_job}.cfg",
        root / "MainTestPlan" / f"{source_job}.env",
        root / "MainTestPlan" / f"{source_job}.soc",
        root / f"{source_job}.ini",
    ]

    missing = [str(path).replace("\\", "/") for path in source_files if not path.is_file()]
    if missing:
        raise SystemExit("Missing source files:\n" + "\n".join(missing))

    planned = []
    for source_path in source_files:
        target_name = source_path.name.replace(source_job, target_job)
        if source_path.parent.name == "MainTestPlan":
            target_path = root / "MainTestPlan" / target_name
        else:
            target_path = root / target_name
        planned.append((source_path, target_path))

    summary = {
        "root": str(root).replace("\\", "/"),
        "source_job": source_job,
        "target_job": target_job,
        "write": args.write,
        "files": [str(target.relative_to(root)).replace("\\", "/") for _, target in planned],
    }

    if args.write:
        for source_path, target_path in planned:
            text = source_path.read_text(encoding="utf-8", errors="ignore")
            text = text.replace(source_job, target_job)
            target_path.write_text(text, encoding="utf-8")

    if args.report_json:
        print(json.dumps(summary, separators=(",", ":")))
        return 0

    print("RDK Job Clone")
    print(f"Root:       {summary['root']}")
    print(f"Source job: {source_job}")
    print(f"Target job: {target_job}")
    print(f"Write mode: {args.write}")
    print()
    print("Target files:")
    for rel in summary["files"]:
        print(f"- {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())