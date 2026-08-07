from __future__ import annotations

import argparse
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Harvest GitHub Copilot debug session logs into compact maintenance summaries."
    )
    parser.add_argument(
        "log_root",
        nargs="?",
        default="",
        help="Optional path to debug-logs root, a session folder, or a main.jsonl file. If omitted, auto-detect from local VS Code workspaceStorage.",
    )
    parser.add_argument(
        "--workspace-root",
        default=str(REPO_ROOT),
        help="Workspace root used to normalize file paths. Defaults to this repo root.",
    )
    parser.add_argument(
        "--max-sessions",
        type=int,
        default=0,
        help="Optional cap on how many newest sessions to include. 0 means all sessions.",
    )
    parser.add_argument(
        "--preview-chars",
        type=int,
        default=180,
        help="Max characters stored for user-message previews.",
    )
    parser.add_argument("--report-json", action="store_true", help="Print compact JSON to stdout.")
    parser.add_argument("--report-markdown", action="store_true", help="Print markdown report to stdout.")
    parser.add_argument("--json-output", help="Optional path to write the JSON report.")
    parser.add_argument("--markdown-output", help="Optional path to write the markdown report.")
    parser.add_argument(
        "--compare-json",
        help="Optional prior JSON report to compare against for trend reporting. If omitted, an existing --json-output file is used when available.",
    )
    parser.add_argument(
        "--alert-profile",
        help="Optional JSON alert profile that defines watched metrics and default alert thresholds.",
    )
    parser.add_argument(
        "--alert-threshold-pct-points",
        type=float,
        default=None,
        help="Minimum percentage-point movement required before a watched trend metric is emitted as an alert.",
    )
    parser.add_argument(
        "--alert-min-previous-sessions",
        type=int,
        default=None,
        help="Minimum previous sessions_scanned value required before trend alerts are considered reliable enough to emit.",
    )
    parser.add_argument(
        "--closeout-output",
        help="Optional path to write a rolling repo-maintenance closeout summary based on the latest harvest.",
    )
    return parser.parse_args()


def main() -> int:
    try:
        from .harvest_pipeline import HarvestConfig, OutputTargets, emit_harvest, run_harvest
    except ImportError:
        from harvest_pipeline import HarvestConfig, OutputTargets, emit_harvest, run_harvest

    args = parse_args()
    config = HarvestConfig(
        workspace_root=Path(args.workspace_root),
        log_root=Path(args.log_root) if args.log_root else None,
        max_sessions=args.max_sessions,
        preview_chars=args.preview_chars,
        compare_json=Path(args.compare_json or args.json_output) if (args.compare_json or args.json_output) else None,
        alert_profile=Path(args.alert_profile) if args.alert_profile else None,
        alert_threshold_pct_points=args.alert_threshold_pct_points,
        alert_min_previous_sessions=args.alert_min_previous_sessions,
    )
    outputs = OutputTargets(
        json_output=Path(args.json_output) if args.json_output else None,
        markdown_output=Path(args.markdown_output) if args.markdown_output else None,
        closeout_output=Path(args.closeout_output) if args.closeout_output else None,
        stdout_format=(
            "json"
            if args.report_json
            else "markdown"
            if args.report_markdown or not (args.json_output or args.markdown_output)
            else None
        ),
    )

    run = run_harvest(config, outputs)
    emit_harvest(run, outputs)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())