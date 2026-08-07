from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal

import harvester_discovery
import harvester_rendering
import harvester_reporting
import harvester_support
import harvester_trends


SKILLS_ROOT = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))


LATEST_MARKDOWN_RELATIVE = Path(".claude/artifacts/current_task/tp-agentkit-copilot-session-harvest-latest.md")
LATEST_JSON_RELATIVE = Path(".claude/artifacts/current_task/tp-agentkit-copilot-session-harvest-latest.json")
LATEST_CLOSEOUT_RELATIVE = Path(".claude/artifacts/current_task/tp-agentkit-repo-maintenance-closeout-latest.md")
StdoutFormat = Literal["json", "markdown"]


@dataclass(frozen=True)
class HarvestConfig:
    workspace_root: Path
    log_root: Path | None = None
    max_sessions: int = 0
    preview_chars: int = 180
    compare_json: Path | None = None
    alert_profile: Path | None = None
    alert_threshold_pct_points: float | None = None
    alert_min_previous_sessions: int | None = None


@dataclass(frozen=True)
class OutputTargets:
    json_output: Path | None = None
    markdown_output: Path | None = None
    closeout_output: Path | None = None
    stdout_format: StdoutFormat | None = None


@dataclass(frozen=True)
class HarvestRun:
    report: dict[str, Any]
    markdown_text: str
    artifact_markdown: str
    closeout_text: str | None = None


def derive_default_output_paths(workspace_root: Path) -> dict[str, Path]:
    root = workspace_root.expanduser().resolve(strict=False)
    return {
        "markdown": root / LATEST_MARKDOWN_RELATIVE,
        "json": root / LATEST_JSON_RELATIVE,
        "closeout": root / LATEST_CLOSEOUT_RELATIVE,
    }


def run_harvest(config: HarvestConfig, outputs: OutputTargets | None = None) -> HarvestRun:
    workspace_root = config.workspace_root.expanduser().resolve(strict=False)
    if config.log_root:
        debug_root = harvester_discovery.resolve_debug_root(str(config.log_root))
        auto_detected = False
    else:
        debug_root = harvester_discovery.auto_detect_debug_root(workspace_root)
        auto_detected = True

    previous_report = harvester_support.load_json_report(config.compare_json)
    alert_settings = harvester_support.resolve_alert_settings_from_values(
        config.alert_profile,
        config.alert_threshold_pct_points,
        config.alert_min_previous_sessions,
    )

    session_dirs = harvester_discovery.iter_session_dirs(debug_root)
    report = harvester_reporting.build_report(session_dirs, workspace_root, config.preview_chars, config.max_sessions)
    report["log_root"] = harvester_support.sanitize_user_path(str(debug_root)) or ""
    report["trend_vs_previous"] = harvester_trends.build_trend_vs_previous(report, previous_report)
    report["trend_alerts"] = harvester_trends.build_trend_alerts(
        report["trend_vs_previous"],
        float(alert_settings["threshold_pct_points"]),
        int(alert_settings["min_previous_sessions"]),
        dict(alert_settings["watched_metrics"]),
        alert_settings.get("profile_path"),
    )
    if auto_detected:
        report["notes"].append("Log root was auto-detected from local VS Code workspaceStorage.")

    markdown_text = harvester_rendering.render_markdown(report)
    artifact_markdown = harvester_rendering.render_markdown(report, include_frontmatter=True)
    closeout_text = None
    if outputs and outputs.closeout_output:
        closeout_text = harvester_rendering.render_closeout_markdown(
            report,
            str(outputs.markdown_output) if outputs.markdown_output else None,
            str(outputs.json_output) if outputs.json_output else None,
        )
    return HarvestRun(
        report=report,
        markdown_text=markdown_text,
        artifact_markdown=artifact_markdown,
        closeout_text=closeout_text,
    )


def emit_harvest(
    run: HarvestRun,
    outputs: OutputTargets,
    *,
    writer: Callable[[str | Path, str], None] | None = None,
    print_fn: Callable[[str], None] = print,
) -> None:
    write_output = writer or harvester_support.write_text

    if outputs.json_output:
        write_output(outputs.json_output, json.dumps(run.report, indent=2) + "\n")

    if outputs.markdown_output:
        write_output(outputs.markdown_output, run.artifact_markdown + "\n")

    if outputs.closeout_output:
        closeout_text = run.closeout_text or harvester_rendering.render_closeout_markdown(
            run.report,
            str(outputs.markdown_output) if outputs.markdown_output else None,
            str(outputs.json_output) if outputs.json_output else None,
        )
        write_output(outputs.closeout_output, closeout_text + "\n")

    if outputs.stdout_format == "json":
        print_fn(json.dumps(run.report, separators=(",", ":")))
    elif outputs.stdout_format == "markdown":
        print_fn(run.markdown_text)