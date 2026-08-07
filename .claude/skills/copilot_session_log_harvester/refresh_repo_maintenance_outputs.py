from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

from harvest_pipeline import HarvestConfig, HarvestRun, OutputTargets, derive_default_output_paths, emit_harvest, run_harvest


REPO_ROOT = Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh the rolling Copilot session harvest outputs used for TP-AgentKit repo-maintenance closeout."
    )
    parser.add_argument(
        "--log-root",
        help="Optional explicit debug-logs root, session folder, or main.jsonl path. Defaults to harvester auto-detection.",
    )
    parser.add_argument(
        "--workspace-root",
        default=str(REPO_ROOT),
        help="Workspace root used for output locations and file normalization. Defaults to this repo root.",
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
    parser.add_argument(
        "--compare-json",
        help="Optional prior JSON report to compare against before overwriting the rolling JSON output.",
    )
    parser.add_argument(
        "--alert-profile",
        help="Optional JSON alert profile that defines watched metrics and default thresholds.",
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
        "--harvest-only",
        action="store_true",
        help="Refresh only the rolling markdown and JSON harvest outputs, and skip the closeout helper note.",
    )
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--report-json", action="store_true", help="Print compact JSON to stdout.")
    output_group.add_argument("--report-markdown", action="store_true", help="Print markdown report to stdout.")
    return parser.parse_args()


def build_output_targets(
    workspace_root: Path,
    harvest_only: bool,
    stdout_format: str | None = None,
) -> OutputTargets:
    output_paths = derive_default_output_paths(workspace_root)
    return OutputTargets(
        markdown_output=output_paths["markdown"],
        json_output=output_paths["json"],
        closeout_output=None if harvest_only else output_paths["closeout"],
        stdout_format=stdout_format,
    )


def build_config(args: argparse.Namespace, workspace_root: Path, outputs: OutputTargets) -> HarvestConfig:
    return HarvestConfig(
        workspace_root=workspace_root,
        log_root=Path(args.log_root) if args.log_root else None,
        max_sessions=args.max_sessions,
        preview_chars=args.preview_chars,
        compare_json=Path(args.compare_json) if args.compare_json else outputs.json_output,
        alert_profile=Path(args.alert_profile) if args.alert_profile else None,
        alert_threshold_pct_points=args.alert_threshold_pct_points,
        alert_min_previous_sessions=args.alert_min_previous_sessions,
    )


def print_summary(outputs: OutputTargets) -> None:
    print(f"refreshed harvest markdown: {outputs.markdown_output}")
    print(f"refreshed harvest json: {outputs.json_output}")
    if outputs.closeout_output:
        print(f"refreshed closeout note: {outputs.closeout_output}")


def run_refresh(
    args: argparse.Namespace,
    *,
    runner: Callable[[HarvestConfig, OutputTargets], HarvestRun] = run_harvest,
    emitter: Callable[[HarvestRun, OutputTargets], None] = emit_harvest,
    summary_printer: Callable[[OutputTargets], None] = print_summary,
) -> int:
    workspace_root = Path(args.workspace_root).expanduser().resolve(strict=False)
    outputs = build_output_targets(
        workspace_root,
        args.harvest_only,
        stdout_format=(
            "json"
            if args.report_json
            else "markdown"
            if args.report_markdown
            else None
        ),
    )
    config = build_config(args, workspace_root, outputs)
    run = runner(config, outputs)
    emitter(run, outputs)
    if not outputs.stdout_format:
        summary_printer(outputs)
    return 0


def main() -> int:
    return run_refresh(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())