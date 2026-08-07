from __future__ import annotations

from typing import Any


TREND_STARTER_STYLE_NAMES = ("keyword-led", "natural-language", "structured-anchor")
TREND_FIRST_TURN_SIGNAL_NAMES = (
    "explicit_mode_in_first_prompt",
    "source_path_in_first_prompt",
    "input_path_in_first_prompt",
    "target_handling_in_first_prompt",
    "tool_started_before_second_user_message",
)
TREND_WORKFLOW_GUARDRAIL_NAMES = (
    "tp_edits_without_approval",
    "risky_tp_edits_without_grill_proxy",
    "grill_proxy_missing_anchor_without_user_question",
    "partial_validation_without_verified_unverified_pattern",
)


def ranked_item_count(items: list[dict[str, Any]], target_name: str, label_key: str = "name") -> int:
    for item in items:
        if str(item.get(label_key) or "") == target_name:
            return int(item.get("count") or 0)
    return 0


def build_share_trend_metric(
    metric_name: str,
    current_count: int,
    current_total: int,
    previous_count: int,
    previous_total: int,
) -> dict[str, Any]:
    current_pct = 0.0 if current_total <= 0 else round((current_count / current_total) * 100.0, 2)
    previous_pct = 0.0 if previous_total <= 0 else round((previous_count / previous_total) * 100.0, 2)
    return {
        "metric": metric_name,
        "current_count": current_count,
        "current_pct": current_pct,
        "previous_count": previous_count,
        "previous_pct": previous_pct,
        "delta_count": current_count - previous_count,
        "delta_pct_points": round(current_pct - previous_pct, 2),
    }


def build_trend_vs_previous(report: dict[str, Any], previous_report: dict[str, Any] | None) -> dict[str, Any]:
    if not previous_report:
        return {
            "status": "unavailable",
            "reason": "No previous JSON report was available for comparison.",
        }

    previous_sessions = int(previous_report.get("sessions_scanned") or 0)
    current_sessions = int(report.get("sessions_scanned") or 0)
    if previous_sessions <= 0:
        return {
            "status": "unavailable",
            "reason": "Previous JSON report did not contain a comparable sessions_scanned value.",
        }

    previous_intake_patterns = previous_report.get("intake_patterns") or {}
    current_intake_patterns = report.get("intake_patterns") or {}
    previous_first_turn = previous_report.get("first_turn_signals") or {}
    current_first_turn = report.get("first_turn_signals") or {}
    previous_workflow_guardrails = previous_report.get("workflow_guardrails") or {}
    current_workflow_guardrails = report.get("workflow_guardrails") or {}

    starter_style_trends: list[dict[str, Any]] = []
    for name in TREND_STARTER_STYLE_NAMES:
        starter_style_trends.append(
            build_share_trend_metric(
                name,
                ranked_item_count(current_intake_patterns.get("starter_styles") or [], name),
                current_sessions,
                ranked_item_count(previous_intake_patterns.get("starter_styles") or [], name),
                previous_sessions,
            )
        )

    first_turn_trends: list[dict[str, Any]] = []
    for name in TREND_FIRST_TURN_SIGNAL_NAMES:
        current_metric = current_first_turn.get(name) or {}
        previous_metric = previous_first_turn.get(name) or {}
        first_turn_trends.append(
            build_share_trend_metric(
                name,
                int(current_metric.get("count") or 0),
                current_sessions,
                int(previous_metric.get("count") or 0),
                previous_sessions,
            )
        )

    workflow_guardrail_trends: list[dict[str, Any]] = []
    for name in TREND_WORKFLOW_GUARDRAIL_NAMES:
        current_metric = current_workflow_guardrails.get(name) or {}
        previous_metric = previous_workflow_guardrails.get(name) or {}
        workflow_guardrail_trends.append(
            build_share_trend_metric(
                name,
                int(current_metric.get("count") or 0),
                int(current_metric.get("total") or 0),
                int(previous_metric.get("count") or 0),
                int(previous_metric.get("total") or 0),
            )
        )

    return {
        "status": "ok",
        "previous_generated_at": previous_report.get("generated_at"),
        "previous_sessions_scanned": previous_sessions,
        "current_sessions_scanned": current_sessions,
        "starter_style_share": starter_style_trends,
        "first_turn_signal_share": first_turn_trends,
        "workflow_guardrail_share": workflow_guardrail_trends,
    }


def build_trend_alerts(
    trend: dict[str, Any],
    threshold_pct_points: float,
    min_previous_sessions: int,
    watched_metrics: dict[str, Any],
    profile_path: str | None,
) -> dict[str, Any]:
    if trend.get("status") != "ok":
        return {
            "status": "unavailable",
            "reason": trend.get("reason") or "Trend comparison is unavailable.",
            "threshold_pct_points": threshold_pct_points,
            "min_previous_sessions": min_previous_sessions,
            "profile_path": profile_path,
            "watched_metrics": sorted(watched_metrics),
            "alerts": [],
        }

    previous_sessions = int(trend.get("previous_sessions_scanned") or 0)
    if previous_sessions < min_previous_sessions:
        return {
            "status": "unavailable",
            "reason": (
                f"Previous sessions_scanned value {previous_sessions} is below the configured alert floor "
                f"of {min_previous_sessions}."
            ),
            "threshold_pct_points": threshold_pct_points,
            "min_previous_sessions": min_previous_sessions,
            "profile_path": profile_path,
            "watched_metrics": sorted(watched_metrics),
            "alerts": [],
        }

    metric_lookup: dict[str, dict[str, Any]] = {}
    for item in trend.get("starter_style_share") or []:
        metric_lookup[str(item.get("metric") or "")] = item
    for item in trend.get("first_turn_signal_share") or []:
        metric_lookup[str(item.get("metric") or "")] = item
    for item in trend.get("workflow_guardrail_share") or []:
        metric_lookup[str(item.get("metric") or "")] = item

    alerts: list[dict[str, Any]] = []
    for metric_name, rule in watched_metrics.items():
        item = metric_lookup.get(metric_name)
        if not item:
            continue
        delta_pct_points = float(item.get("delta_pct_points") or 0.0)
        if abs(delta_pct_points) < threshold_pct_points:
            continue

        direction = str(rule.get("direction") or "increase")
        if direction == "increase":
            alert_kind = "improvement" if delta_pct_points > 0 else "regression"
        elif direction == "decrease":
            alert_kind = "improvement" if delta_pct_points < 0 else "regression"
        else:
            alert_kind = "shift"

        alerts.append(
            {
                "metric": metric_name,
                "label": rule.get("label") or metric_name,
                "kind": alert_kind,
                "current_count": int(item.get("current_count") or 0),
                "current_pct": float(item.get("current_pct") or 0.0),
                "previous_count": int(item.get("previous_count") or 0),
                "previous_pct": float(item.get("previous_pct") or 0.0),
                "delta_pct_points": round(delta_pct_points, 2),
            }
        )

    alerts.sort(key=lambda item: (abs(float(item["delta_pct_points"])), item["label"]), reverse=True)
    return {
        "status": "ok",
        "threshold_pct_points": threshold_pct_points,
        "min_previous_sessions": min_previous_sessions,
        "profile_path": profile_path,
        "watched_metrics": sorted(watched_metrics),
        "alerts": alerts,
    }