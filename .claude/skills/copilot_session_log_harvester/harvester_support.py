from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DEFAULT_ALERT_PROFILE_PATH = Path(__file__).resolve().parent / "alert_profile.json"
TREND_ALERT_THRESHOLD_PCT_POINTS_DEFAULT = 5.0
TREND_ALERT_MIN_PREVIOUS_SESSIONS_DEFAULT = 3
TREND_ALERT_RULES_DEFAULT = {
    "keyword-led": {"label": "keyword-led starters", "direction": "increase"},
    "explicit_mode_in_first_prompt": {"label": "explicit mode in first prompt", "direction": "increase"},
    "source_path_in_first_prompt": {"label": "source path in first prompt", "direction": "increase"},
    "input_path_in_first_prompt": {"label": "input path in first prompt", "direction": "increase"},
    "target_handling_in_first_prompt": {"label": "target handling in first prompt", "direction": "increase"},
    "tool_started_before_second_user_message": {"label": "first-turn self-start proxy", "direction": "increase"},
    "grill_proxy_missing_anchor_without_user_question": {
        "label": "user-facing grill-question gap",
        "direction": "decrease",
    },
}

WINDOWS_USER_HOME_RE = re.compile(r"(?i)([a-z]:[\\/]+users[\\/]+)[^\\/]+")
POSIX_USER_HOME_RE = re.compile(r"(?i)((?:/users/|/home/))[^/]+")


def sanitize_user_path(text: str | Path | None) -> str | None:
    if text is None:
        return None
    sanitized = str(text)
    sanitized = WINDOWS_USER_HOME_RE.sub(r"\1<user>", sanitized)
    sanitized = POSIX_USER_HOME_RE.sub(r"\1<user>", sanitized)
    return sanitized


def _default_watched_metrics() -> dict[str, dict[str, str]]:
    return {metric_name: dict(rule) for metric_name, rule in TREND_ALERT_RULES_DEFAULT.items()}


def _default_alert_profile_payload() -> dict[str, Any]:
    return {
        "threshold_pct_points": TREND_ALERT_THRESHOLD_PCT_POINTS_DEFAULT,
        "min_previous_sessions": TREND_ALERT_MIN_PREVIOUS_SESSIONS_DEFAULT,
        "watched_metrics": _default_watched_metrics(),
    }


def load_json_report(path_text: str | Path | None) -> dict[str, Any] | None:
    if not path_text:
        return None
    path = Path(path_text)
    if not path.exists() or not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def load_alert_profile(alert_profile_path: str | Path | None) -> tuple[dict[str, Any], str | None]:
    profile_path = Path(alert_profile_path).expanduser() if alert_profile_path else DEFAULT_ALERT_PROFILE_PATH

    if not profile_path.exists():
        if alert_profile_path:
            raise FileNotFoundError(f"Alert profile not found: {profile_path}")
        return _default_alert_profile_payload(), None

    try:
        payload = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        if alert_profile_path:
            raise ValueError(f"Could not parse alert profile {profile_path}: {exc}") from exc
        return _default_alert_profile_payload(), None

    if not isinstance(payload, dict):
        if alert_profile_path:
            raise ValueError(f"Alert profile must be a JSON object: {profile_path}")
        return _default_alert_profile_payload(), None

    watched_metrics = payload.get("watched_metrics")
    if not isinstance(watched_metrics, dict) or not watched_metrics:
        watched_metrics = _default_watched_metrics()

    return {
        "threshold_pct_points": float(payload.get("threshold_pct_points") or TREND_ALERT_THRESHOLD_PCT_POINTS_DEFAULT),
        "min_previous_sessions": int(payload.get("min_previous_sessions") or TREND_ALERT_MIN_PREVIOUS_SESSIONS_DEFAULT),
        "watched_metrics": watched_metrics,
    }, sanitize_user_path(profile_path)


def resolve_alert_settings_from_values(
    alert_profile_path: str | Path | None,
    alert_threshold_pct_points: float | None,
    alert_min_previous_sessions: int | None,
) -> dict[str, Any]:
    profile, profile_path = load_alert_profile(alert_profile_path)
    threshold_pct_points = (
        float(alert_threshold_pct_points)
        if alert_threshold_pct_points is not None
        else float(profile.get("threshold_pct_points") or TREND_ALERT_THRESHOLD_PCT_POINTS_DEFAULT)
    )
    min_previous_sessions = (
        int(alert_min_previous_sessions)
        if alert_min_previous_sessions is not None
        else int(profile.get("min_previous_sessions") or TREND_ALERT_MIN_PREVIOUS_SESSIONS_DEFAULT)
    )
    watched_metrics = profile.get("watched_metrics")
    if not isinstance(watched_metrics, dict) or not watched_metrics:
        watched_metrics = _default_watched_metrics()
    return {
        "profile_path": profile_path,
        "threshold_pct_points": threshold_pct_points,
        "min_previous_sessions": min_previous_sessions,
        "watched_metrics": watched_metrics,
    }


def write_text(path_text: str | Path, content: str) -> None:
    path = Path(path_text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")