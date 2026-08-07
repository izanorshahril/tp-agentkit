from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def render_trend_metric(metric: dict[str, Any]) -> str:
    name = str(metric.get("metric") or "unknown").replace("_", " ")
    current_count = int(metric.get("current_count") or 0)
    current_pct = float(metric.get("current_pct") or 0.0)
    previous_count = int(metric.get("previous_count") or 0)
    previous_pct = float(metric.get("previous_pct") or 0.0)
    delta_pct_points = float(metric.get("delta_pct_points") or 0.0)
    return (
        f"- {name}: {current_count} ({current_pct}%) vs previous {previous_count} ({previous_pct}%), "
        f"delta {delta_pct_points:+.2f} pt"
    )


def render_trend_alert(alert: dict[str, Any]) -> str:
    return (
        f"- {alert['kind']}: {alert['label']} moved {float(alert['delta_pct_points']):+.2f} pt "
        f"({float(alert['current_pct']):.2f}% now vs {float(alert['previous_pct']):.2f}% before)"
    )


def render_recent_guardrail_window(window: dict[str, Any], *, markdown: bool = False) -> str:
    flagged_count = len(window.get("flagged_sessions") or [])
    approval_misses = ((window.get("tp_edits_without_approval") or {}).get("count") or 0)
    grill_misses = ((window.get("risky_tp_edits_without_grill_proxy") or {}).get("count") or 0)
    grill_question_gaps = ((window.get("grill_proxy_missing_anchor_without_user_question") or {}).get("count") or 0)
    partial_validation_gaps = (
        (window.get("partial_validation_without_verified_unverified_pattern") or {}).get("count") or 0
    )
    if markdown:
        return (
            f"- latest {window.get('window_size')} sessions: {flagged_count} flagged session(s), "
            f"{window.get('tp_edit_sessions', 0)} tp edit session(s), {approval_misses} approval miss(es), "
            f"{grill_misses} grill-proxy miss(es), {grill_question_gaps} user-facing grill-question gap(s), {partial_validation_gaps} partial-validation wording gap(s)"
        )
    return (
        f"- latest {window.get('window_size')} sessions: `{flagged_count}` flagged session(s), "
        f"`{window.get('tp_edit_sessions', 0)}` tp edit session(s), `{approval_misses}` approval miss(es), "
        f"`{grill_misses}` grill-proxy miss(es), `{grill_question_gaps}` user-facing grill-question gap(s), `{partial_validation_gaps}` partial-validation wording gap(s)"
    )


def render_markdown(report: dict[str, Any], include_frontmatter: bool = False) -> str:
    lines: list[str] = []
    if include_frontmatter:
        lines.extend(
            [
                "---",
                "status: ready",
                "verified: yes",
                f"date: {datetime.now(timezone.utc).date().isoformat()}",
                "scope: Harvest summary from GitHub Copilot debug session logs for TP-AgentKit maintenance",
                "---",
                "",
            ]
        )
    lines.append("# Copilot Session Log Harvest")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- sessions scanned: {report['sessions_scanned']}")
    lines.append(f"- input tokens: {report['totals']['input_tokens']}")
    lines.append(f"- output tokens: {report['totals']['output_tokens']}")
    lines.append(f"- tool calls: {report['totals']['tool_calls']}")
    lines.append(f"- first session: {report['time_span']['first_session_started_at'] or 'n/a'}")
    lines.append(f"- last session: {report['time_span']['last_session_ended_at'] or 'n/a'}")
    lines.append("")

    def add_ranked_section(title: str, items: list[dict[str, Any]], label_key: str) -> None:
        lines.append(f"## {title}")
        lines.append("")
        if not items:
            lines.append("- none")
            lines.append("")
            return
        for item in items:
            lines.append(f"- {item[label_key]}: {item['count']}")
        lines.append("")

    add_ranked_section("Top Models", report["top_models"], "name")
    add_ranked_section("Top Tools", report["top_tools"], "name")

    lines.append("## Intake Patterns")
    lines.append("")
    intake_patterns = report.get("intake_patterns") or {}
    starter_styles = intake_patterns.get("starter_styles") or []
    likely_modes = intake_patterns.get("likely_modes") or []
    likely_intents = intake_patterns.get("likely_intents") or []
    if starter_styles:
        for item in starter_styles:
            lines.append(f"- starter style {item['name']}: {item['count']}")
    else:
        lines.append("- starter style data: none")
    if likely_modes:
        for item in likely_modes:
            lines.append(f"- likely mode {item['name']}: {item['count']}")
    else:
        lines.append("- likely mode data: none")
    if likely_intents:
        for item in likely_intents:
            lines.append(f"- likely intent {item['name']}: {item['count']}")
    else:
        lines.append("- likely intent data: none")
    lines.append("")

    lines.append("## First-Turn Signals")
    lines.append("")
    first_turn_signals = report.get("first_turn_signals") or {}
    for label, item in first_turn_signals.items():
        readable = label.replace("_", " ")
        lines.append(f"- {readable}: {item['count']} ({item['pct']}%)")
    lines.append("")

    lines.append("## Workflow Guardrails")
    lines.append("")
    guardrails = report.get("workflow_guardrails") or {}
    lines.append(f"- tp edit sessions: {guardrails.get('tp_edit_sessions', 0)}")
    lines.append(f"- risky tp edit sessions: {guardrails.get('risky_tp_edit_sessions', 0)}")
    lines.append(f"- partial validation sessions: {guardrails.get('partial_validation_sessions', 0)}")
    recent_windows = guardrails.get("recent_windows") or []
    for item in recent_windows:
        lines.append(render_recent_guardrail_window(item, markdown=True))
    for label in (
        "tp_edits_without_approval",
        "risky_tp_edits_without_grill_proxy",
        "grill_proxy_missing_anchor_without_user_question",
        "partial_validation_without_verified_unverified_pattern",
    ):
        item = guardrails.get(label) or {"count": 0, "pct": 0.0, "total": 0}
        readable = label.replace("_", " ")
        lines.append(f"- {readable}: {item['count']} of {item['total']} relevant session(s) ({item['pct']}%)")
    flagged_sessions = guardrails.get("flagged_sessions") or []
    if flagged_sessions:
        for item in flagged_sessions:
            lines.append(f"- flagged session {item['session_id']}: {', '.join(item['flags'])}")
    else:
        lines.append("- flagged sessions: none")
    lines.append("")

    lines.append("## Trend Vs Previous")
    lines.append("")
    trend = report.get("trend_vs_previous") or {}
    if trend.get("status") == "ok":
        lines.append(f"- previous generated at: {trend.get('previous_generated_at') or 'n/a'}")
        lines.append(f"- previous sessions scanned: {trend.get('previous_sessions_scanned')}")
        lines.append(f"- current sessions scanned: {trend.get('current_sessions_scanned')}")
        for item in trend.get("starter_style_share") or []:
            lines.append(render_trend_metric(item))
        for item in trend.get("first_turn_signal_share") or []:
            lines.append(render_trend_metric(item))
        for item in trend.get("workflow_guardrail_share") or []:
            lines.append(render_trend_metric(item))
    else:
        lines.append(f"- {trend.get('reason') or 'No previous trend baseline available.'}")
    lines.append("")

    lines.append("## Trend Alerts")
    lines.append("")
    trend_alerts = report.get("trend_alerts") or {}
    if trend_alerts.get("status") == "ok":
        lines.append(
            f"- threshold: {trend_alerts.get('threshold_pct_points')} pct points; "
            f"minimum previous sessions: {trend_alerts.get('min_previous_sessions')}"
        )
        if trend_alerts.get("profile_path"):
            lines.append(f"- profile: {trend_alerts.get('profile_path')}")
        alerts = trend_alerts.get("alerts") or []
        if alerts:
            for item in alerts:
                lines.append(render_trend_alert(item))
        else:
            lines.append("- no watched metrics crossed the alert threshold in this run")
    else:
        lines.append(f"- {trend_alerts.get('reason') or 'Trend alerts are unavailable.'}")
    lines.append("")

    lines.append("## Top Tool Bigrams")
    lines.append("")
    if report["top_tool_bigrams"]:
        for item in report["top_tool_bigrams"]:
            lines.append(f"- {' -> '.join(item['pattern'])}: {item['count']}")
    else:
        lines.append("- none")
    lines.append("")

    add_ranked_section("Top Read Files", report["top_read_files"], "path")
    add_ranked_section("Top Edited Files", report["top_edited_files"], "path")

    lines.append("## Repeated User Request Previews")
    lines.append("")
    if report["top_user_requests"]:
        for item in report["top_user_requests"]:
            lines.append(f"- {item['preview']}: {item['count']}")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("## Knowledge Candidates")
    lines.append("")
    if report["knowledge_candidates"]:
        for item in report["knowledge_candidates"]:
            lines.append(
                f"- {item['path']}: touches={item['touches']}, reads={item['read_count']}, edits={item['edit_count']}"
            )
    else:
        lines.append("- none")
    lines.append("")

    lines.append("## Artifact Promotion Candidates")
    lines.append("")
    artifact_candidates = report.get("artifact_promotion_candidates") or []
    if artifact_candidates:
        for item in artifact_candidates:
            lines.append(
                "- "
                f"{item['path']}: touches={item['touches']}, reads={item['read_count']}, edits={item['edit_count']}, "
                f"tp_sessions={item['tp_sessions']}, tp_edit_sessions={item['tp_edit_sessions']}"
            )
    else:
        lines.append("- none")
    lines.append("")

    lines.append("## Automation Candidates")
    lines.append("")
    if report["automation_candidates"]:
        for item in report["automation_candidates"]:
            lines.append(f"- {' -> '.join(item['pattern'])}: {item['count']}")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("## Sessions")
    lines.append("")
    for session in report["sessions"]:
        lines.append(f"### {session['session_id']}")
        lines.append("")
        lines.append(f"- started: {session['started_at'] or 'n/a'}")
        lines.append(f"- ended: {session['ended_at'] or 'n/a'}")
        lines.append(f"- duration seconds: {session['duration_seconds'] if session['duration_seconds'] is not None else 'n/a'}")
        lines.append(f"- first user preview: {session['first_user_preview'] or 'n/a'}")
        lines.append(f"- starter style: {session['starter_style'] or 'unknown'}")
        lines.append(f"- likely mode: {session['inferred_mode'] or 'unknown'}")
        lines.append(f"- likely intent: {session['inferred_intent'] or 'generic'}")
        lines.append(
            f"- tool started before second user message: {'yes' if session['tool_started_before_second_user_message'] else 'no'}"
        )
        lines.append(f"- tp edit observed: {'yes' if session['has_tp_edit'] else 'no'}")
        if session['has_tp_edit']:
            lines.append(
                f"- approval before first tp edit: {'yes' if session['approval_before_first_tp_edit'] else 'no'}"
            )
            lines.append(
                f"- grill proxy before first tp edit: {'yes' if session['grill_proxy_before_first_tp_edit'] else 'no'}"
            )
        if session['guardrail_flags']:
            lines.append(f"- guardrail flags: {', '.join(session['guardrail_flags'])}")
        lines.append(f"- input tokens: {session['input_tokens']}")
        lines.append(f"- output tokens: {session['output_tokens']}")
        lines.append(f"- tool calls: {session['tool_call_count']}")
        lines.append("")

    lines.append("## Notes")
    lines.append("")
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def render_closeout_markdown(
    report: dict[str, Any],
    markdown_output: str | None,
    json_output: str | None,
) -> str:
    lines = [
        "---",
        "status: ready",
        "verified: yes",
        f"date: {datetime.now(timezone.utc).date().isoformat()}",
        "scope: Rolling repo-maintenance closeout refresh driven by the latest Copilot session harvest",
        "---",
        "",
        "# Repo Maintenance Closeout Refresh",
        "",
        "## Harvest Refresh",
        "",
        f"- log root: `{report['log_root']}`",
        f"- sessions scanned: `{report['sessions_scanned']}`",
        f"- input tokens: `{report['totals']['input_tokens']}`",
        f"- output tokens: `{report['totals']['output_tokens']}`",
        f"- tool calls: `{report['totals']['tool_calls']}`",
    ]

    if markdown_output:
        lines.append(f"- latest markdown harvest: `{markdown_output}`")
    if json_output:
        lines.append(f"- latest JSON harvest: `{json_output}`")
    lines.extend(["", "## Priority Review", ""])

    knowledge_candidates = report.get("knowledge_candidates") or []
    if knowledge_candidates:
        for item in knowledge_candidates[:5]:
            lines.append(
                f"- knowledge candidate: `{item['path']}` with `{item['touches']}` touches"
            )
    else:
        lines.append("- no durable knowledge candidates surfaced in this run")

    artifact_candidates = report.get("artifact_promotion_candidates") or []
    if artifact_candidates:
        for item in artifact_candidates[:5]:
            lines.append(
                "- artifact promotion candidate: "
                f"`{item['path']}` with `{item['touches']}` touches across `{item['tp_sessions']}` tp session(s)"
            )
    else:
        lines.append("- no TP-artifact promotion candidates surfaced in this run")

    lines.extend(["", "## Automation Watch", ""])
    automation_candidates = report.get("automation_candidates") or []
    if automation_candidates:
        for item in automation_candidates[:5]:
            lines.append(
                f"- repeated tool chain: `{' -> '.join(item['pattern'])}` seen `{item['count']}` times"
            )
    else:
        lines.append("- no repeated automation candidates met the reporting threshold in this run")

    lines.extend(["", "## Intake Signals", ""])
    first_turn_signals = report.get("first_turn_signals") or {}
    starter_styles = (report.get("intake_patterns") or {}).get("starter_styles") or []
    if starter_styles:
        for item in starter_styles[:3]:
            lines.append(f"- starter style: `{item['name']}` seen `{item['count']}` times")
    for label in (
        "explicit_mode_in_first_prompt",
        "source_path_in_first_prompt",
        "input_path_in_first_prompt",
        "target_handling_in_first_prompt",
        "tool_started_before_second_user_message",
    ):
        item = first_turn_signals.get(label)
        if not item:
            continue
        readable = label.replace("_", " ")
        lines.append(f"- {readable}: `{item['count']}` session(s), `{item['pct']}`%")

    lines.extend(["", "## Protocol Watch", ""])
    guardrails = report.get("workflow_guardrails") or {}
    recent_windows = guardrails.get("recent_windows") or []
    for item in recent_windows:
        lines.append(render_recent_guardrail_window(item))
    for label in (
        "tp_edits_without_approval",
        "risky_tp_edits_without_grill_proxy",
        "grill_proxy_missing_anchor_without_user_question",
        "partial_validation_without_verified_unverified_pattern",
    ):
        item = guardrails.get(label) or {"count": 0, "pct": 0.0, "total": 0}
        readable = label.replace("_", " ")
        lines.append(f"- {readable}: `{item['count']}` of `{item['total']}` relevant session(s), `{item['pct']}`%")
    flagged_sessions = guardrails.get("flagged_sessions") or []
    if flagged_sessions:
        for item in flagged_sessions[:5]:
            lines.append(f"- flagged session: `{item['session_id']}` -> `{', '.join(item['flags'])}`")
    else:
        lines.append("- no protocol guardrail flags surfaced in this run")
    if recent_windows:
        largest_window = recent_windows[-1]
        historical_burden = len(flagged_sessions) - len(largest_window.get("flagged_sessions") or [])
        if historical_burden > 0:
            lines.append(
                f"- older-than-latest `{largest_window['window_size']}` sessions still contribute `{historical_burden}` flagged session(s) to the full rolling sample"
            )

    lines.extend(["", "## Trend Watch", ""])
    trend = report.get("trend_vs_previous") or {}
    if trend.get("status") == "ok":
        lines.append(f"- previous report generated at: `{trend.get('previous_generated_at') or 'n/a'}`")
        starter_style_lookup = {
            item.get("metric"): item for item in trend.get("starter_style_share") or []
        }
        first_turn_lookup = {
            item.get("metric"): item for item in trend.get("first_turn_signal_share") or []
        }
        workflow_guardrail_lookup = {
            item.get("metric"): item for item in trend.get("workflow_guardrail_share") or []
        }
        for metric_name in ("keyword-led", "natural-language"):
            item = starter_style_lookup.get(metric_name)
            if item:
                lines.append(
                    f"- {metric_name} starters: `{item['current_count']}` now vs `{item['previous_count']}` before, `{item['delta_pct_points']:+.2f}` pt"
                )
        item = first_turn_lookup.get("tool_started_before_second_user_message")
        if item:
            lines.append(
                f"- first-turn self-start proxy: `{item['current_count']}` now vs `{item['previous_count']}` before, `{item['delta_pct_points']:+.2f}` pt"
            )
        item = first_turn_lookup.get("source_path_in_first_prompt")
        if item:
            lines.append(
                f"- source path in first prompt: `{item['current_count']}` now vs `{item['previous_count']}` before, `{item['delta_pct_points']:+.2f}` pt"
            )
        item = workflow_guardrail_lookup.get("grill_proxy_missing_anchor_without_user_question")
        if item:
            lines.append(
                f"- user-facing grill-question gap: `{item['current_count']}` now vs `{item['previous_count']}` before, `{item['delta_pct_points']:+.2f}` pt"
            )
    else:
        lines.append(f"- {trend.get('reason') or 'No previous trend baseline available.'}")

    lines.extend(["", "## Trend Alerts", ""])
    trend_alerts = report.get("trend_alerts") or {}
    if trend_alerts.get("status") == "ok":
        lines.append(
            f"- threshold: `{trend_alerts.get('threshold_pct_points')}` pct points; minimum previous sessions: `{trend_alerts.get('min_previous_sessions')}`"
        )
        if trend_alerts.get("profile_path"):
            lines.append(f"- profile: `{trend_alerts.get('profile_path')}`")
        alerts = trend_alerts.get("alerts") or []
        if alerts:
            for item in alerts[:5]:
                lines.append(render_trend_alert(item))
        else:
            lines.append("- no watched metrics crossed the alert threshold in this run")
    else:
        lines.append(f"- {trend_alerts.get('reason') or 'Trend alerts are unavailable.'}")

    lines.extend(
        [
            "",
            "## Standard Follow-Through",
            "",
            "- promote only cross-session, reusable findings into `.claude/knowledge/`, tasks, or skills",
            "- harvest reusable lessons out of touched `.claude/artifacts/current_task/` TP artifacts when they capture repeatable structure, validation, or workflow decisions",
            "- keep raw `testprogram/` and `references/` files out of durable harvesting unless a human intentionally summarizes them first",
            "- refresh `.claude/artifacts/current_task/INDEX.md` when this session created or renamed durable active artifacts",
            "- archive completed current-task notes separately; this refresh does not auto-move history",
            "- do not modify `testprogram/` as part of repo-maintenance closeout unless the user explicitly requested it",
            "",
            "## Limits",
            "",
            "- this rolling note is a helper summary, not the canonical archival closeout record for a major delivery",
            "- future session capture is still pull-based: rerun the task or script when you want a fresh summary",
            "- first-turn signal counts are heuristics; they do not prove complete user satisfaction or zero follow-up need",
            "- trend deltas compare this run against one prior JSON baseline, not against an all-time historical average",
            "- trend alerts are threshold-driven helpers; they do not replace human review of context and session mix",
            "",
        ]
    )
    return "\n".join(lines)