from __future__ import annotations

import re
from typing import Any


TARGET_CPK_MIN = 3.5
TARGET_CPK_MAX = 4.0
TARGET_FAIL_PERCENT_MIN = 0.00002
TARGET_FAIL_PERCENT_MAX = 0.00004

HARD_SCOPE_REVIEW_KEYS = [
    "matching_tests",
    "delta_tests",
    "kelvin_tests",
    "continuity_tests",
    "ns_na_uv_marker_tests",
    "code_read_tests",
    "temperature_tests",
    "unbin_tests",
]

SOFT_SCOPE_REVIEW_KEYS = [
    "continuity_end_tests",
    "low_cpk_with_observed_fails",
    "yield_loss_above_target",
    "insufficient_modality_rows",
]

ALL_SCOPE_KEYS = HARD_SCOPE_REVIEW_KEYS + [
    "continuity_open_tests",
    "continuity_short_tests",
] + SOFT_SCOPE_REVIEW_KEYS

TOKEN_SPLIT_RE = re.compile(r"[^A-Z0-9]+")
FAIL_PERCENT_HEADERS = ("Fail%", "%Fail", "Good Fail%")


def tokenize_text(*values: str) -> set[str]:
    combined = " ".join(str(value or "") for value in values).upper()
    return {token for token in TOKEN_SPLIT_RE.split(combined) if token}


def parse_number(value: str) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("%"):
        text = text[:-1].strip()
    try:
        return float(text)
    except ValueError:
        return None


def choose_cpk_value(row: dict[str, str]) -> float | None:
    for key in ("Cpkn_SPL", "Cpk_SPL", "Cpkn_SL", "Cpk_SL", "Cpkn", "Cpk"):
        value = parse_number(row.get(key, ""))
        if value is not None:
            return value
    return None


def total_observed_fails(row: dict[str, str]) -> float:
    total = 0.0
    for key in ("NumGoodFails", "NumGoodLowerFails", "NumGoodUpperFails"):
        value = parse_number(row.get(key, ""))
        if value is not None:
            total += value
    return total


def choose_fail_percent(row: dict[str, str]) -> float | None:
    for key in FAIL_PERCENT_HEADERS:
        value = parse_number(row.get(key, ""))
        if value is not None:
            return value
    return None


def classify_scope_flags(row: dict[str, str]) -> set[str]:
    parameter = str(row.get("Parameter", "") or "")
    comment = str(row.get("Comment", "") or "")
    tokens = tokenize_text(parameter, comment)
    raw_parameter = parameter.upper()
    compact_parameter = raw_parameter.replace("_", "").replace(" ", "")
    flags: set[str] = set()

    if any("MATCH" in token for token in tokens) or "MATCH" in compact_parameter:
        flags.add("matching_tests")
    if any(token.startswith("DELTA") for token in tokens):
        flags.add("delta_tests")
    if any(token.startswith("KELVIN") for token in tokens):
        flags.add("kelvin_tests")

    is_continuity = (
        raw_parameter.startswith("OPEN_")
        or raw_parameter.startswith("SHORT_")
        or raw_parameter.startswith("CONT_")
        or any(token.startswith("CONT") for token in tokens)
        or "CONTINUITY" in tokens
    )
    if is_continuity:
        flags.add("continuity_tests")
        if raw_parameter.startswith("OPEN_") or "OPEN" in tokens:
            flags.add("continuity_open_tests")
        if raw_parameter.startswith("SHORT_") or "SHORT" in tokens:
            flags.add("continuity_short_tests")
        if raw_parameter.endswith("_END") or "END" in tokens:
            flags.add("continuity_end_tests")

    if {"NS", "NA", "UV"} & tokens:
        flags.add("ns_na_uv_marker_tests")
    if ({"CODE", "READ"} <= tokens) or "CODEREAD" in compact_parameter or "READCODE" in compact_parameter:
        flags.add("code_read_tests")
    if any(token.startswith("TEMP") for token in tokens) or "TEMPERATURE" in tokens:
        flags.add("temperature_tests")
    if any(token.startswith("UNBIN") for token in tokens):
        flags.add("unbin_tests")
    if "MODALITY" in tokens and "INSUFFICIENT" in tokens:
        flags.add("insufficient_modality_rows")

    cpk_value = choose_cpk_value(row)
    if cpk_value is not None and cpk_value < TARGET_CPK_MIN and total_observed_fails(row) > 0:
        flags.add("low_cpk_with_observed_fails")

    fail_percent = choose_fail_percent(row)
    if fail_percent is not None and fail_percent > TARGET_FAIL_PERCENT_MAX:
        flags.add("yield_loss_above_target")

    return flags


def build_scope_screening_from_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    if not rows:
        return {}

    flag_counts = {key: 0 for key in ALL_SCOPE_KEYS}
    examples = {key: [] for key in ALL_SCOPE_KEYS}
    flagged_row_count = 0

    for row in rows:
        flags = classify_scope_flags(row)
        if not flags:
            continue
        flagged_row_count += 1
        example = {
            "test_number": str(row.get("TestNumber", row.get("TestID", "")) or ""),
            "parameter": str(row.get("Parameter", "") or ""),
        }
        comment = str(row.get("Comment", "") or "").strip()
        if comment:
            example["comment"] = comment
        for flag in flags:
            flag_counts[flag] += 1
            if len(examples[flag]) < 5:
                examples[flag].append(example)

    requires_scope_review = any(flag_counts[key] for key in HARD_SCOPE_REVIEW_KEYS)
    recommended_actions: list[str] = []
    if requires_scope_review:
        recommended_actions.append(
            "Filter or separately review matching, delta, kelvin, continuity, NS/nA/UV, code-read, temperature, and unbin tests before any bulk SPL update."
        )
    if flag_counts["continuity_tests"]:
        recommended_actions.append(
            "Keep continuity open and continuity short on separate review paths; continuity short usually keeps the current limit."
        )
    if flag_counts["continuity_end_tests"]:
        recommended_actions.append(
            "Hold continuity end tests at the current limit unless the user explicitly asks for a separate continuity-end review."
        )
    if flag_counts["low_cpk_with_observed_fails"] or flag_counts["yield_loss_above_target"]:
        recommended_actions.append(
            "Hold low-Cpk rows with observed fails and rows above about 0.00004% per-test yield loss for manual review."
        )

    return {
        "enabled": True,
        "checklist_version": "spl_implementation_heuristics_20260423",
        "screened_rows": len(rows),
        "flagged_rows": flagged_row_count,
        "target_cpk_range": {"min": TARGET_CPK_MIN, "max": TARGET_CPK_MAX},
        "per_test_yield_loss_target_percent": {
            "min": TARGET_FAIL_PERCENT_MIN,
            "max": TARGET_FAIL_PERCENT_MAX,
            "reference": TARGET_FAIL_PERCENT_MIN,
        },
        "requires_scope_review": requires_scope_review,
        "flag_counts": flag_counts,
        "flag_examples": {key: value for key, value in examples.items() if value},
        "recommended_actions": recommended_actions,
    }