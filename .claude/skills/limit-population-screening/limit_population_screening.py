from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SKILLS_ROOT = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))

LS_UPDATER_ROOT = SKILLS_ROOT / "ls-updater"
if str(LS_UPDATER_ROOT) not in sys.path:
    sys.path.insert(0, str(LS_UPDATER_ROOT))

from ls_updater_audit import split_unit_prefix  # type: ignore
from spl_scope_screening import classify_scope_flags  # type: ignore


CSV_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
MULTIPLIER = {
    "": 1.0,
    "p": 1e-12,
    "n": 1e-9,
    "u": 1e-6,
    "m": 1e-3,
    "k": 1e3,
    "g": 1e9,
}
TARGET_CPK_MIN = 3.5
TARGET_CPK_MAX = 4.0
TARGET_TOTAL_YIELD_LOSS_PCT = 0.1
TARGET_PER_TEST_YIELD_LOSS_PCT = 0.00002
KEEP_ACTION = "keep_candidate"
KEEPISH_ACTIONS = {"keep_candidate", "manual_review_duplicate_keepish"}
REVERT_ACTION = "revert_candidate"
TEST_PATTERN = re.compile(r"^\s*(T\d+)\b")
NUMERIC_PATTERN = re.compile(r"^(?P<number>[+-]?\d+(?:\.\d+)?)(?P<suffix>.*)$")
END_TOKENS = ("_END", " END", "CONTINUITY_END")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Screen changed .ls limits against population statistics and compare action-table populations."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    replay_parser = subparsers.add_parser(
        "replay-bundle",
        help="Run a saved verify/followup/compare bundle from one replay config JSON.",
    )
    replay_parser.add_argument("--replay-json", required=True, type=Path, help="Replay config JSON.")
    replay_parser.add_argument("--report-json", action="store_true", help="Emit compact JSON summary on stdout.")

    verify_parser = subparsers.add_parser("verify", help="Score changed .ls rows against one population stats CSV.")
    verify_parser.add_argument("--cases-json", required=True, type=Path, help="JSON file describing one or more cases.")
    verify_parser.add_argument("--stats-csv", required=True, type=Path, help="Population statistics CSV.")
    verify_parser.add_argument("--dataset-label", default="population", help="Population label used in the report.")
    verify_parser.add_argument("--output-json", type=Path, help="Optional JSON output path.")
    verify_parser.add_argument("--output-md", type=Path, help="Optional markdown output path.")
    verify_parser.add_argument("--report-json", action="store_true", help="Emit compact JSON summary on stdout.")

    followup_parser = subparsers.add_parser("followup", help="Convert a verify report into a row-level action table.")
    followup_parser.add_argument("--verify-json", required=True, type=Path, help="Input JSON from the verify subcommand.")
    followup_parser.add_argument("--membership-json", required=True, type=Path, help="JSON mapping of case labels to bulk/review CSVs.")
    followup_parser.add_argument("--output-json", type=Path, help="Optional JSON output path.")
    followup_parser.add_argument("--output-md", type=Path, help="Optional markdown output path.")
    followup_parser.add_argument("--output-csv", type=Path, help="Optional action-table CSV output path.")
    followup_parser.add_argument("--report-json", action="store_true", help="Emit compact JSON summary on stdout.")

    compare_parser = subparsers.add_parser(
        "compare-populations",
        help="Compare two action tables with matching family/test keys.",
    )
    compare_parser.add_argument("--left-action-csv", required=True, type=Path, help="Left action-table CSV.")
    compare_parser.add_argument("--right-action-csv", required=True, type=Path, help="Right action-table CSV.")
    compare_parser.add_argument("--left-label", default="left", help="Display label for the left population.")
    compare_parser.add_argument("--right-label", default="right", help="Display label for the right population.")
    compare_parser.add_argument("--output-json", type=Path, help="Optional JSON output path.")
    compare_parser.add_argument("--output-md", type=Path, help="Optional markdown output path.")
    compare_parser.add_argument("--output-csv", type=Path, help="Optional diff CSV output path.")
    compare_parser.add_argument("--report-json", action="store_true", help="Emit compact JSON summary on stdout.")
    return parser.parse_args()


def resolve_path(path: Path, base_dir: Path) -> Path:
    return path if path.is_absolute() else (base_dir / path).resolve()


def emit_compact_json(enabled: bool, payload: dict[str, Any]) -> None:
    if enabled:
        print(json.dumps(payload, ensure_ascii=True, separators=(",", ":")))


def write_json(path: Path | None, payload: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_text(path: Path | None, text: str) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv_rows(path: Path | None, rows: list[dict[str, Any]]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def normalize_dataset_label(label: str) -> str:
    cleaned = "".join(character.lower() if character.isalnum() else "_" for character in label.strip())
    collapsed = "_".join(part for part in cleaned.split("_") if part)
    return collapsed or "population"


def parse_float(text: Any) -> float | None:
    if text is None:
        return None
    stripped = str(text).strip().replace("%", "")
    if not stripped or stripped.upper() == "NA":
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


def rounded(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(value, digits)


def pct(value: float | None, digits: int = 8) -> float | None:
    return None if value is None else round(value * 100.0, digits)


def normal_cdf(z_value: float) -> float:
    return 0.5 * math.erfc(-z_value / math.sqrt(2.0))


def projected_fail_probability(
    mean_value: float | None,
    sigma_value: float | None,
    lower_limit: float | None,
    upper_limit: float | None,
) -> float | None:
    if mean_value is None or sigma_value is None:
        return None
    if lower_limit is None and upper_limit is None:
        return 0.0
    if sigma_value < 0:
        return None
    if sigma_value == 0:
        violates_lower = lower_limit is not None and mean_value < lower_limit
        violates_upper = upper_limit is not None and mean_value > upper_limit
        return 1.0 if violates_lower or violates_upper else 0.0

    probability = 0.0
    if lower_limit is not None:
        probability += normal_cdf((lower_limit - mean_value) / sigma_value)
    if upper_limit is not None:
        probability += 1.0 - normal_cdf((upper_limit - mean_value) / sigma_value)
    return max(0.0, min(1.0, probability))


def projected_cpk(
    mean_value: float | None,
    sigma_value: float | None,
    lower_limit: float | None,
    upper_limit: float | None,
) -> float | None:
    if mean_value is None or sigma_value is None or sigma_value <= 0:
        return None
    terms: list[float] = []
    if lower_limit is not None:
        terms.append((mean_value - lower_limit) / (3.0 * sigma_value))
    if upper_limit is not None:
        terms.append((upper_limit - mean_value) / (3.0 * sigma_value))
    return min(terms) if terms else None


def classify_cpk(cpk_value: float | None) -> str:
    if cpk_value is None:
        return "unscorable"
    if cpk_value < TARGET_CPK_MIN:
        return "below_target"
    if cpk_value <= TARGET_CPK_MAX:
        return "within_target"
    return "above_target"


def parse_token(raw_token: str) -> dict[str, Any]:
    stripped = raw_token.strip()
    result: dict[str, Any] = {
        "raw": raw_token,
        "text": stripped,
        "is_numeric": False,
        "numeric_text": None,
        "value": None,
        "suffix": "",
        "trailing_space": raw_token != raw_token.rstrip(),
    }
    if not stripped or stripped.upper() == "NA":
        return result
    match = NUMERIC_PATTERN.match(stripped)
    if not match:
        return result
    result.update(
        {
            "is_numeric": True,
            "numeric_text": match.group("number"),
            "value": float(match.group("number")),
            "suffix": match.group("suffix"),
        }
    )
    return result


def parse_field_body(body: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if "," not in body:
        token = parse_token(body)
        return token, dict(token)
    upper_raw, lower_raw = body.split(",", 1)
    return parse_token(upper_raw), parse_token(lower_raw)


def load_field_records(file_path: Path, field_name: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    field_pattern = re.compile(rf"{re.escape(field_name)}\((?P<body>.*?)\);")
    records: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    with file_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            test_match = TEST_PATTERN.match(line)
            if not test_match:
                continue
            field_match = field_pattern.search(line)
            if not field_match:
                continue
            test_id = test_match.group(1)
            if test_id in records:
                duplicates.append(test_id)
            upper, lower = parse_field_body(field_match.group("body"))
            records[test_id] = {
                "line_number": line_number,
                "line": line.rstrip("\n"),
                "UL": upper,
                "LL": lower,
            }
    return records, duplicates


def test_sort_key(test_id: str) -> int:
    text = str(test_id)
    return int(text[1:] if text.startswith("T") else text)


def extract_comment_from_line(line: str) -> str:
    if "Comment =" not in line:
        return ""
    tail = line.split("Comment =", 1)[1]
    if ";" in tail:
        tail = tail.split(";", 1)[0]
    return tail.strip().strip('"')


def try_read_csv_rows(csv_path: Path) -> tuple[list[dict[str, str]], list[str]]:
    last_error: Exception | None = None
    for encoding in CSV_ENCODINGS:
        try:
            with csv_path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                headers = list(reader.fieldnames or [])
                rows = [{str(key or ""): str(value or "") for key, value in row.items()} for row in reader]
                return rows, headers
        except (OSError, UnicodeDecodeError) as exc:
            last_error = exc
            continue
    if last_error is not None:
        raise last_error
    return [], []


def find_header(headers: list[str], candidates: list[str]) -> str:
    normalized = {header.strip().casefold(): header for header in headers}
    for candidate in candidates:
        match = normalized.get(candidate.casefold())
        if match:
            return match
    return ""


def value_to_base(number_text: Any, unit_text: str | None) -> tuple[float | None, str]:
    value = parse_float(number_text)
    prefix, base_unit = split_unit_prefix(unit_text or "")
    if value is None:
        return None, base_unit
    return value * MULTIPLIER[prefix], base_unit


def ls_token_to_base(token: dict[str, Any]) -> tuple[float | None, str]:
    if not token.get("is_numeric"):
        return None, ""
    return value_to_base(token.get("numeric_text"), token.get("suffix") or "")


def load_cases(cases_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(cases_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "cases" in payload:
        cases = payload["cases"]
    elif isinstance(payload, list):
        cases = payload
    else:
        cases = [payload]
    base_dir = cases_path.parent
    normalized: list[dict[str, Any]] = []
    for case in cases:
        normalized.append(
            {
                "label": str(case["label"]),
                "program": str(case["program"]),
                "field": str(case["field"]),
                "baseline": resolve_path(Path(str(case["baseline_ls"])), base_dir),
                "current": resolve_path(Path(str(case["current_ls"])), base_dir),
            }
        )
    return normalized


def load_replay_config(replay_path: Path) -> dict[str, Any]:
    payload = json.loads(replay_path.read_text(encoding="utf-8"))
    base_dir = replay_path.parent

    cases_json = resolve_path(Path(str(payload["cases_json"])), base_dir)
    membership_json = resolve_path(Path(str(payload["membership_json"])), base_dir)
    dataset_runs: list[dict[str, Any]] = []
    for run in payload.get("dataset_runs", []):
        dataset_runs.append(
            {
                "dataset_label": str(run["dataset_label"]),
                "stats_csv": resolve_path(Path(str(run["stats_csv"])), base_dir),
                "verify_json": resolve_path(Path(str(run["verify_json"])), base_dir),
                "verify_md": resolve_path(Path(str(run["verify_md"])), base_dir),
                "followup_json": resolve_path(Path(str(run["followup_json"])), base_dir),
                "followup_md": resolve_path(Path(str(run["followup_md"])), base_dir),
                "action_csv": resolve_path(Path(str(run["action_csv"])), base_dir),
            }
        )

    comparisons: list[dict[str, Any]] = []
    for run in payload.get("comparisons", []):
        comparisons.append(
            {
                "label": str(run.get("label", "comparison")),
                "left_action_csv": resolve_path(Path(str(run["left_action_csv"])), base_dir),
                "right_action_csv": resolve_path(Path(str(run["right_action_csv"])), base_dir),
                "left_label": str(run["left_label"]),
                "right_label": str(run["right_label"]),
                "output_json": resolve_path(Path(str(run["output_json"])), base_dir),
                "output_md": resolve_path(Path(str(run["output_md"])), base_dir),
                "output_csv": resolve_path(Path(str(run["output_csv"])), base_dir),
            }
        )

    return {
        "label": str(payload.get("label", replay_path.stem)),
        "cases_json": cases_json,
        "membership_json": membership_json,
        "dataset_runs": dataset_runs,
        "comparisons": comparisons,
    }


def build_stats_index(stats_path: Path) -> tuple[dict[tuple[str, str], dict[str, str]], dict[str, str], str | None]:
    rows, headers = try_read_csv_rows(stats_path)
    required_headers = {
        "program": find_header(headers, ["TestProgram"]),
        "test": find_header(headers, ["TestNumber", "TestID"]),
        "name": find_header(headers, ["TestName", "Parameter"]),
        "unit": find_header(headers, ["ParameterUnit", "ScaledUnit"]),
        "average": find_header(headers, ["Average", "Mean"]),
        "deviation": find_header(headers, ["Deviation", "StDev", "StdDev", "Sigma"]),
        "executions": find_header(headers, ["Executions", "NumPartsAfterDataFilter"]),
    }
    missing = [name for name, header in required_headers.items() if name != "executions" and not header]
    if missing:
        raise RuntimeError(f"Missing required stats headers: {missing}")
    failures_header = find_header(headers, ["Failures", "NumGoodFails"])

    stats_index: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        program = str(row.get(required_headers["program"], "")).strip()
        test_id = str(row.get(required_headers["test"], "")).strip()
        if not program or not test_id:
            continue
        stats_index[(program, test_id)] = row
    return stats_index, required_headers, failures_header or None


def analyze_case(
    case: dict[str, Any],
    stats_index: dict[tuple[str, str], dict[str, str]],
    stats_headers: dict[str, str],
    failures_header: str | None,
) -> dict[str, Any]:
    baseline_records, baseline_duplicates = load_field_records(case["baseline"], case["field"])
    current_records, current_duplicates = load_field_records(case["current"], case["field"])
    duplicate_tid_union = sorted(set(baseline_duplicates) | set(current_duplicates), key=test_sort_key)

    changed_entries: list[dict[str, Any]] = []
    missing_stats: list[str] = []
    unit_mismatches: list[dict[str, str]] = []
    summary = Counter()
    total_incremental_fail_pct = 0.0
    total_current_fail_pct = 0.0

    shared_tests = sorted(set(baseline_records) & set(current_records), key=test_sort_key)
    for test_key in shared_tests:
        baseline_record = baseline_records[test_key]
        current_record = current_records[test_key]

        baseline_ul, baseline_ul_unit = ls_token_to_base(baseline_record["UL"])
        baseline_ll, baseline_ll_unit = ls_token_to_base(baseline_record["LL"])
        current_ul, current_ul_unit = ls_token_to_base(current_record["UL"])
        current_ll, current_ll_unit = ls_token_to_base(current_record["LL"])

        if baseline_ul == current_ul and baseline_ll == current_ll:
            continue

        summary["changed_tests_total"] += 1
        test_number = test_key[1:]
        stats_row = stats_index.get((str(case["program"]), test_number))
        if stats_row is None:
            missing_stats.append(test_number)
            summary["missing_stats_rows"] += 1
            continue

        stats_unit = str(stats_row.get(stats_headers["unit"], "")).strip()
        mean_value, stats_base_unit = value_to_base(stats_row.get(stats_headers["average"]), stats_unit)
        sigma_value, _ = value_to_base(stats_row.get(stats_headers["deviation"]), stats_unit)

        expected_units = {unit for unit in [baseline_ul_unit, baseline_ll_unit, current_ul_unit, current_ll_unit] if unit}
        if stats_base_unit and expected_units and stats_base_unit not in expected_units:
            unit_mismatches.append(
                {
                    "test_id": test_number,
                    "stats_unit": stats_unit,
                    "stats_base_unit": stats_base_unit,
                    "ls_units": ", ".join(sorted(expected_units)),
                }
            )
            summary["unit_mismatch_rows"] += 1
            continue

        baseline_fail_probability = projected_fail_probability(mean_value, sigma_value, baseline_ll, baseline_ul)
        current_fail_probability = projected_fail_probability(mean_value, sigma_value, current_ll, current_ul)
        current_cpk_value = projected_cpk(mean_value, sigma_value, current_ll, current_ul)
        baseline_cpk_value = projected_cpk(mean_value, sigma_value, baseline_ll, baseline_ul)

        incremental_fail_probability = None
        if baseline_fail_probability is not None and current_fail_probability is not None:
            incremental_fail_probability = max(0.0, current_fail_probability - baseline_fail_probability)

        cpk_bucket = classify_cpk(current_cpk_value)
        summary["analyzed_tests"] += 1
        summary[f"cpk_{cpk_bucket}"] += 1
        if incremental_fail_probability is not None:
            total_incremental_fail_pct += incremental_fail_probability * 100.0
            if incremental_fail_probability * 100.0 > TARGET_PER_TEST_YIELD_LOSS_PCT:
                summary["per_test_yield_above_target"] += 1
        if current_fail_probability is not None:
            total_current_fail_pct += current_fail_probability * 100.0

        changed_entries.append(
            {
                "family": case["label"],
                "program": case["program"],
                "test_id": test_number,
                "test_name": str(stats_row.get(stats_headers["name"], "")).strip(),
                "comment": extract_comment_from_line(current_record.get("line", "")),
                "stats_unit": stats_unit,
                "executions": parse_float(stats_row.get(stats_headers["executions"], "")) if stats_headers.get("executions") else None,
                "observed_failures": parse_float(stats_row.get(failures_header)) if failures_header else None,
                "mean_in_stats_unit": rounded(parse_float(stats_row.get(stats_headers["average"])), 6),
                "sigma_in_stats_unit": rounded(parse_float(stats_row.get(stats_headers["deviation"])), 6),
                "baseline_limits": {
                    "ul_text": baseline_record["UL"]["text"],
                    "ll_text": baseline_record["LL"]["text"],
                },
                "current_limits": {
                    "ul_text": current_record["UL"]["text"],
                    "ll_text": current_record["LL"]["text"],
                },
                "projected_baseline_cpk": rounded(baseline_cpk_value, 6),
                "projected_current_cpk": rounded(current_cpk_value, 6),
                "cpk_bucket": cpk_bucket,
                "projected_baseline_fail_pct": pct(baseline_fail_probability, 8),
                "projected_current_fail_pct": pct(current_fail_probability, 8),
                "projected_incremental_fail_pct": pct(incremental_fail_probability, 8),
            }
        )

    changed_entries.sort(key=lambda entry: (entry["projected_current_cpk"] is None, entry["projected_current_cpk"] or float("inf")))
    return {
        "label": case["label"],
        "program": case["program"],
        "field": case["field"],
        "baseline_path": str(case["baseline"]),
        "current_path": str(case["current"]),
        "baseline_duplicates": baseline_duplicates,
        "current_duplicates": current_duplicates,
        "duplicate_tid_union": duplicate_tid_union,
        "missing_stats_test_ids": missing_stats,
        "unit_mismatches": unit_mismatches,
        "summary": {
            "changed_tests_total": summary["changed_tests_total"],
            "analyzed_tests": summary["analyzed_tests"],
            "missing_stats_rows": summary["missing_stats_rows"],
            "unit_mismatch_rows": summary["unit_mismatch_rows"],
            "duplicate_tid_count": len(duplicate_tid_union),
            "cpk_below_target": summary["cpk_below_target"],
            "cpk_within_target": summary["cpk_within_target"],
            "cpk_above_target": summary["cpk_above_target"],
            "cpk_unscorable": summary["cpk_unscorable"],
            "per_test_yield_above_target": summary["per_test_yield_above_target"],
            "projected_total_incremental_yield_loss_pct": round(total_incremental_fail_pct, 8),
            "projected_total_current_fail_pct": round(total_current_fail_pct, 8),
            "meets_total_yield_target": total_incremental_fail_pct <= TARGET_TOTAL_YIELD_LOSS_PCT,
        },
        "entries": sorted(changed_entries, key=lambda entry: int(str(entry["test_id"]))),
        "lowest_projected_cpk": changed_entries[:10],
        "highest_incremental_yield_loss": sorted(
            changed_entries,
            key=lambda entry: entry["projected_incremental_fail_pct"] if entry["projected_incremental_fail_pct"] is not None else -1.0,
            reverse=True,
        )[:10],
    }


def render_verify_markdown(report: dict[str, Any]) -> str:
    overall = report["overall_summary"]
    lines = [
        "# Limit Population Screening Verify",
        "",
        f"- dataset: `{report['dataset_label']}`",
        f"- cases: `{len(report['cases'])}`",
        f"- changed rows: `{overall['changed_tests_total']}`",
        f"- analyzed rows: `{overall['analyzed_tests']}`",
        f"- projected incremental yield loss: `{overall['projected_total_incremental_yield_loss_pct']:.8f}%`",
        f"- meets `{TARGET_TOTAL_YIELD_LOSS_PCT}%` total target: `{'yes' if overall['meets_total_yield_target'] else 'no'}`",
        "",
        "## Per Case",
    ]
    for case in report["cases"]:
        summary = case["summary"]
        lines.extend(
            [
                f"### {case['label']}",
                f"- changed rows: `{summary['changed_tests_total']}`; analyzed: `{summary['analyzed_tests']}`",
                f"- Cpk below/within/above/unscorable: `{summary['cpk_below_target']}` / `{summary['cpk_within_target']}` / `{summary['cpk_above_target']}` / `{summary['cpk_unscorable']}`",
                f"- projected incremental yield loss: `{summary['projected_total_incremental_yield_loss_pct']:.8f}%`",
                f"- duplicate TIDs: `{summary['duplicate_tid_count']}`",
                "",
            ]
        )
    return "\n".join(lines)


def run_verify(args: argparse.Namespace) -> int:
    cases = load_cases(args.cases_json.resolve())
    stats_csv = args.stats_csv.resolve()
    stats_index, stats_headers, failures_header = build_stats_index(stats_csv)
    case_reports = [analyze_case(case, stats_index, stats_headers, failures_header) for case in cases]

    overall = Counter()
    for case in case_reports:
        summary = case["summary"]
        for key, value in summary.items():
            if isinstance(value, bool):
                continue
            overall[key] += value

    report = {
        "status": "ok",
        "mode": "verify",
        "dataset_label": normalize_dataset_label(args.dataset_label),
        "stats_csv": str(stats_csv),
        "cases": case_reports,
        "overall_summary": {
            "changed_tests_total": overall["changed_tests_total"],
            "analyzed_tests": overall["analyzed_tests"],
            "missing_stats_rows": overall["missing_stats_rows"],
            "unit_mismatch_rows": overall["unit_mismatch_rows"],
            "duplicate_tid_count": overall["duplicate_tid_count"],
            "cpk_below_target": overall["cpk_below_target"],
            "cpk_within_target": overall["cpk_within_target"],
            "cpk_above_target": overall["cpk_above_target"],
            "cpk_unscorable": overall["cpk_unscorable"],
            "per_test_yield_above_target": overall["per_test_yield_above_target"],
            "projected_total_incremental_yield_loss_pct": round(float(overall["projected_total_incremental_yield_loss_pct"]), 8),
            "projected_total_current_fail_pct": round(float(overall["projected_total_current_fail_pct"]), 8),
            "meets_total_yield_target": float(overall["projected_total_incremental_yield_loss_pct"]) <= TARGET_TOTAL_YIELD_LOSS_PCT,
        },
    }

    output_json = args.output_json.resolve() if args.output_json else None
    output_md = args.output_md.resolve() if args.output_md else None
    write_json(output_json, report)
    write_text(output_md, render_verify_markdown(report))
    emit_compact_json(
        args.report_json,
        {
            "status": "ok",
            "mode": "verify",
            "cases": len(case_reports),
            "changed_tests_total": report["overall_summary"]["changed_tests_total"],
            "analyzed_tests": report["overall_summary"]["analyzed_tests"],
            "output_json": None if output_json is None else output_json.as_posix(),
            "output_md": None if output_md is None else output_md.as_posix(),
        },
    )
    return 0


def run_replay_bundle(args: argparse.Namespace) -> int:
    config = load_replay_config(args.replay_json.resolve())
    dataset_summaries: dict[str, dict[str, Any]] = {}
    comparison_summaries: dict[str, dict[str, Any]] = {}

    for run in config["dataset_runs"]:
        run_verify(
            argparse.Namespace(
                cases_json=Path(run["cases_json"]) if "cases_json" in run else config["cases_json"],
                stats_csv=run["stats_csv"],
                dataset_label=run["dataset_label"],
                output_json=run["verify_json"],
                output_md=run["verify_md"],
                report_json=False,
            )
        )
        run_followup(
            argparse.Namespace(
                verify_json=run["verify_json"],
                membership_json=config["membership_json"],
                output_json=run["followup_json"],
                output_md=run["followup_md"],
                output_csv=run["action_csv"],
                report_json=False,
            )
        )

        verify_report = json.loads(run["verify_json"].read_text(encoding="utf-8"))
        followup_report = json.loads(run["followup_json"].read_text(encoding="utf-8"))
        dataset_summaries[run["dataset_label"]] = {
            "changed_tests_total": verify_report["overall_summary"]["changed_tests_total"],
            "analyzed_tests": verify_report["overall_summary"]["analyzed_tests"],
            "action_counts": followup_report["action_counts"],
            "verify_json": run["verify_json"].as_posix(),
            "followup_json": run["followup_json"].as_posix(),
            "action_csv": run["action_csv"].as_posix(),
        }

    for run in config["comparisons"]:
        run_compare_populations(
            argparse.Namespace(
                left_action_csv=run["left_action_csv"],
                right_action_csv=run["right_action_csv"],
                left_label=run["left_label"],
                right_label=run["right_label"],
                output_json=run["output_json"],
                output_md=run["output_md"],
                output_csv=run["output_csv"],
                report_json=False,
            )
        )
        comparison_report = json.loads(run["output_json"].read_text(encoding="utf-8"))
        comparison_summaries[run["label"]] = {
            "row_count": comparison_report["row_count"],
            "same_action_count": comparison_report["same_action_count"],
            "changed_action_count": comparison_report["changed_action_count"],
            "output_json": run["output_json"].as_posix(),
        }

    emit_compact_json(
        args.report_json,
        {
            "status": "ok",
            "mode": "replay-bundle",
            "replay_label": config["label"],
            "dataset_runs": dataset_summaries,
            "comparisons": comparison_summaries,
        },
    )
    return 0


def load_membership_mapping(path: Path) -> dict[str, dict[str, Path | None]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases_payload: Any = payload.get("cases") if isinstance(payload, dict) and "cases" in payload else payload
    mapping: dict[str, dict[str, Path | None]] = {}
    base_dir = path.parent
    if isinstance(cases_payload, list):
        for item in cases_payload:
            label = str(item["label"])
            mapping[label] = {
                "bulk_csv": resolve_path(Path(item["bulk_csv"]), base_dir) if item.get("bulk_csv") else None,
                "review_csv": resolve_path(Path(item["review_csv"]), base_dir) if item.get("review_csv") else None,
            }
    elif isinstance(cases_payload, dict):
        for label, item in cases_payload.items():
            mapping[str(label)] = {
                "bulk_csv": resolve_path(Path(item["bulk_csv"]), base_dir) if item.get("bulk_csv") else None,
                "review_csv": resolve_path(Path(item["review_csv"]), base_dir) if item.get("review_csv") else None,
            }
    else:
        raise RuntimeError("Unsupported membership JSON structure.")
    return mapping


def load_case_source_index(mapping: dict[str, dict[str, Path | None]]) -> dict[str, dict[str, dict[str, Any]]]:
    source_index: dict[str, dict[str, dict[str, Any]]] = {}
    for label, config in mapping.items():
        family_index: dict[str, dict[str, Any]] = {}
        for bucket, path in (("bulk", config.get("bulk_csv")), ("review", config.get("review_csv"))):
            if path is None:
                continue
            rows, headers = try_read_csv_rows(path)
            test_header = find_header(headers, ["TestNumber", "TestID"])
            if not test_header:
                continue
            for row in rows:
                test_id = str(row.get(test_header, "")).strip()
                if not test_id or test_id in family_index:
                    continue
                family_index[test_id] = {"bucket": bucket, "row": row}
        source_index[label] = family_index
    return source_index


def detect_end_family(entry: dict[str, Any], source_row: dict[str, str] | None) -> bool:
    texts = [str(entry.get("test_name", "") or "").upper(), str(entry.get("comment", "") or "").upper()]
    if source_row is not None:
        texts.append(str(source_row.get("Parameter", "") or "").upper())
        texts.append(str(source_row.get("Comment", "") or "").upper())
    return any(token in text for token in END_TOKENS for text in texts)


def classify_action(
    entry: dict[str, Any],
    source_bucket: str,
    duplicate_tids: set[str],
    source_row: dict[str, str] | None,
    end_family: bool,
) -> tuple[str, str]:
    del source_row
    test_id = str(entry["test_id"])
    current_cpk = entry.get("projected_current_cpk")
    incremental_yield = entry.get("projected_incremental_fail_pct")
    is_unscorable = current_cpk is None
    below_target = is_unscorable or float(current_cpk) < TARGET_CPK_MIN
    yield_above_target = incremental_yield is not None and float(incremental_yield) > TARGET_PER_TEST_YIELD_LOSS_PCT

    if not below_target and not yield_above_target:
        if test_id in duplicate_tids:
            return "manual_review_duplicate_keepish", "Meets target but duplicated TID in .ls"
        return KEEP_ACTION, "Meets Cpk and per-test yield target"

    if test_id in duplicate_tids:
        return "manual_review_duplicate", "Problem row on duplicated TID in .ls"
    if source_bucket == "review":
        return "manual_review_review_subset", "Already held out of the screened bulk subset"
    if end_family:
        return "manual_review_end_family", "END-family row should be reviewed separately"
    if is_unscorable:
        return "manual_review_unscorable", "Projected Cpk is unscorable"
    if below_target and yield_above_target:
        return REVERT_ACTION, "Below Cpk target and above per-test yield target"
    if below_target:
        return REVERT_ACTION, "Below Cpk target"
    return REVERT_ACTION, "Above per-test yield target"


def summarize_entries(entries: list[dict[str, Any]]) -> dict[str, Any]:
    summary = Counter()
    total_incremental = 0.0
    for entry in entries:
        summary["rows"] += 1
        current_cpk = entry.get("projected_current_cpk")
        if current_cpk is None:
            summary["cpk_unscorable"] += 1
        elif float(current_cpk) < TARGET_CPK_MIN:
            summary["cpk_below_target"] += 1
        else:
            summary["cpk_at_or_above_target"] += 1
        incremental = entry.get("projected_incremental_fail_pct")
        if incremental is not None:
            total_incremental += float(incremental)
            if float(incremental) > TARGET_PER_TEST_YIELD_LOSS_PCT:
                summary["yield_above_target"] += 1
        action = str(entry.get("action", ""))
        if action:
            summary[f"action::{action}"] += 1
    return {
        "rows": summary["rows"],
        "cpk_below_target": summary["cpk_below_target"],
        "cpk_at_or_above_target": summary["cpk_at_or_above_target"],
        "cpk_unscorable": summary["cpk_unscorable"],
        "yield_above_target": summary["yield_above_target"],
        "projected_total_incremental_yield_loss_pct": round(total_incremental, 8),
        "meets_total_yield_target": total_incremental <= TARGET_TOTAL_YIELD_LOSS_PCT,
        "action_counts": {
            key.split("::", 1)[1]: count
            for key, count in sorted(summary.items())
            if key.startswith("action::")
        },
    }


def build_scenarios(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    scenarios = {
        "all_changed": entries,
        "bulk_membership_only": [entry for entry in entries if entry["source_bucket"] == "bulk"],
        "bulk_minus_end_family": [entry for entry in entries if entry["source_bucket"] == "bulk" and not entry["end_family"]],
        "keep_candidates_only": [entry for entry in entries if entry["action"] == KEEP_ACTION],
    }
    return {name: summarize_entries(rows) for name, rows in scenarios.items()}


def to_action_csv_row(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "family": entry["family"],
        "test_id": entry["test_id"],
        "test_name": entry["test_name"],
        "comment": entry["comment"],
        "source_bucket": entry["source_bucket"],
        "scope_flags": ",".join(entry["scope_flags"]),
        "end_family": entry["end_family"],
        "duplicate_tid": entry["duplicate_tid"],
        "projected_current_cpk": entry["projected_current_cpk"],
        "projected_incremental_fail_pct": entry["projected_incremental_fail_pct"],
        "projected_current_fail_pct": entry["projected_current_fail_pct"],
        "baseline_ll": entry["baseline_limits"]["ll_text"],
        "baseline_ul": entry["baseline_limits"]["ul_text"],
        "current_ll": entry["current_limits"]["ll_text"],
        "current_ul": entry["current_limits"]["ul_text"],
        "action": entry["action"],
        "action_reason": entry["action_reason"],
    }


def render_followup_markdown(report: dict[str, Any]) -> str:
    lines = ["# Limit Population Screening Follow-Up", "", "## Action Counts"]
    action_counts = Counter()
    for case in report["cases"]:
        action_counts.update(case["scenario_summaries"]["all_changed"]["action_counts"])
    for action, count in sorted(action_counts.items()):
        lines.append(f"- `{action}`: `{count}`")
    lines.extend(["", "## Per Case"])
    for case in report["cases"]:
        lines.append(f"### {case['label']}")
        for scenario_name in ["all_changed", "bulk_membership_only", "bulk_minus_end_family", "keep_candidates_only"]:
            summary = case["scenario_summaries"][scenario_name]
            lines.append(
                f"- `{scenario_name}`: rows `{summary['rows']}`, below-target Cpk `{summary['cpk_below_target']}`, incremental loss `{summary['projected_total_incremental_yield_loss_pct']:.8f}%`"
            )
        lines.append("")
    return "\n".join(lines)


def run_followup(args: argparse.Namespace) -> int:
    verify_report = json.loads(args.verify_json.resolve().read_text(encoding="utf-8"))
    membership_mapping = load_membership_mapping(args.membership_json.resolve())
    source_index = load_case_source_index(membership_mapping)

    all_entries: list[dict[str, Any]] = []
    case_reports: list[dict[str, Any]] = []
    overall_action_counts = Counter()

    for case in verify_report["cases"]:
        label = str(case["label"])
        duplicate_tids = {tid[1:] if str(tid).startswith("T") else str(tid) for tid in case.get("duplicate_tid_union", [])}
        family_source_index = source_index.get(label, {})
        enriched_entries: list[dict[str, Any]] = []
        for entry in case["entries"]:
            test_id = str(entry["test_id"])
            source_record = family_source_index.get(test_id)
            source_bucket = str(source_record["bucket"]) if source_record else "unmapped"
            source_row = source_record["row"] if source_record else None
            scope_flags = sorted(classify_scope_flags(source_row)) if source_row else []
            end_family = detect_end_family(entry, source_row)
            action, action_reason = classify_action(entry, source_bucket, duplicate_tids, source_row, end_family)

            enriched = dict(entry)
            enriched.update(
                {
                    "source_bucket": source_bucket,
                    "scope_flags": scope_flags,
                    "end_family": end_family,
                    "duplicate_tid": test_id in duplicate_tids,
                    "action": action,
                    "action_reason": action_reason,
                }
            )
            enriched_entries.append(enriched)
            all_entries.append(enriched)
            overall_action_counts[action] += 1

        case_reports.append(
            {
                "label": label,
                "field": case["field"],
                "scenario_summaries": build_scenarios(enriched_entries),
                "enriched_entries": enriched_entries,
            }
        )

    top_incremental_rows = sorted(
        all_entries,
        key=lambda entry: entry["projected_incremental_fail_pct"] if entry["projected_incremental_fail_pct"] is not None else -1.0,
        reverse=True,
    )[:10]
    lowest_cpk_rows = sorted(
        all_entries,
        key=lambda entry: entry["projected_current_cpk"] if entry["projected_current_cpk"] is not None else float("inf"),
    )[:10]

    followup_report = {
        "status": "ok",
        "mode": "followup",
        "dataset_label": verify_report.get("dataset_label", "population"),
        "source_verify_json": str(args.verify_json.resolve()),
        "cases": case_reports,
        "action_counts": dict(sorted(overall_action_counts.items())),
        "top_incremental_rows": top_incremental_rows,
        "lowest_cpk_rows": lowest_cpk_rows,
    }

    csv_rows = [to_action_csv_row(entry) for entry in sorted(all_entries, key=lambda item: (item["family"], int(str(item["test_id"]))))]
    output_json = args.output_json.resolve() if args.output_json else None
    output_md = args.output_md.resolve() if args.output_md else None
    output_csv = args.output_csv.resolve() if args.output_csv else None
    write_json(output_json, followup_report)
    write_text(output_md, render_followup_markdown(followup_report))
    write_csv_rows(output_csv, csv_rows)

    emit_compact_json(
        args.report_json,
        {
            "status": "ok",
            "mode": "followup",
            "rows": len(csv_rows),
            "action_counts": dict(sorted(overall_action_counts.items())),
            "output_json": None if output_json is None else output_json.as_posix(),
            "output_md": None if output_md is None else output_md.as_posix(),
            "output_csv": None if output_csv is None else output_csv.as_posix(),
        },
    )
    return 0


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    rows, _ = try_read_csv_rows(path)
    return rows


def row_key(row: dict[str, str]) -> tuple[str, str]:
    return (str(row["family"]), str(row["test_id"]))


def to_bool(text: Any) -> bool:
    return str(text).strip().lower() == "true"


def build_action_index(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {row_key(row): row for row in rows}


def family_counts(rows: list[dict[str, str]]) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = {}
    for row in rows:
        family = row["family"]
        counts.setdefault(family, Counter())[row["action"]] += 1
    return {
        family: {
            KEEP_ACTION: counter.get(KEEP_ACTION, 0),
            "manual_review": sum(count for action, count in counter.items() if action.startswith("manual_review")),
            REVERT_ACTION: counter.get(REVERT_ACTION, 0),
        }
        for family, counter in sorted(counts.items())
    }


def render_compare_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Limit Population Screening Compare",
        "",
        f"- left label: `{summary['left_label']}`",
        f"- right label: `{summary['right_label']}`",
        f"- rows: `{summary['row_count']}`",
        f"- same action: `{summary['same_action_count']}`",
        f"- changed action: `{summary['changed_action_count']}`",
        "",
        "## Action Pairs",
    ]
    for pair, count in sorted(summary["pair_counts"].items()):
        lines.append(f"- `{pair}`: `{count}`")
    return "\n".join(lines)


def run_compare_populations(args: argparse.Namespace) -> int:
    left_rows = read_csv_rows(args.left_action_csv.resolve())
    right_rows = read_csv_rows(args.right_action_csv.resolve())
    left_index = build_action_index(left_rows)
    right_index = build_action_index(right_rows)
    left_keys = set(left_index)
    right_keys = set(right_index)
    if left_keys != right_keys:
        raise RuntimeError("Action tables do not align on family/test_id keys.")

    diff_rows: list[dict[str, Any]] = []
    pair_counts = Counter()
    same_action_count = 0
    changed_action_count = 0

    for key in sorted(left_keys, key=lambda item: (item[0], test_sort_key(item[1]))):
        left = left_index[key]
        right = right_index[key]
        pair = f"{left['action']} -> {right['action']}"
        pair_counts[pair] += 1
        if left["action"] == right["action"]:
            same_action_count += 1
        else:
            changed_action_count += 1
        diff_rows.append(
            {
                "family": left["family"],
                "test_id": left["test_id"],
                "test_name": left["test_name"],
                "comment": left["comment"],
                "source_bucket": left["source_bucket"],
                "scope_flags": left["scope_flags"],
                "duplicate_tid": to_bool(left["duplicate_tid"]),
                "end_family": to_bool(left["end_family"]),
                "left_action": left["action"],
                "right_action": right["action"],
                "action_changed": left["action"] != right["action"],
                "left_projected_current_cpk": parse_float(left["projected_current_cpk"]),
                "right_projected_current_cpk": parse_float(right["projected_current_cpk"]),
                "left_projected_incremental_fail_pct": parse_float(left["projected_incremental_fail_pct"]),
                "right_projected_incremental_fail_pct": parse_float(right["projected_incremental_fail_pct"]),
                "left_reason": left["action_reason"],
                "right_reason": right["action_reason"],
            }
        )

    summary = {
        "status": "ok",
        "mode": "compare-populations",
        "left_label": args.left_label,
        "right_label": args.right_label,
        "row_count": len(diff_rows),
        "same_action_count": same_action_count,
        "changed_action_count": changed_action_count,
        "pair_counts": dict(sorted(pair_counts.items())),
        "left_family_counts": family_counts(left_rows),
        "right_family_counts": family_counts(right_rows),
    }

    output_json = args.output_json.resolve() if args.output_json else None
    output_md = args.output_md.resolve() if args.output_md else None
    output_csv = args.output_csv.resolve() if args.output_csv else None
    write_json(output_json, summary)
    write_text(output_md, render_compare_markdown(summary))
    write_csv_rows(output_csv, diff_rows)

    emit_compact_json(
        args.report_json,
        {
            "status": "ok",
            "mode": "compare-populations",
            "row_count": len(diff_rows),
            "same_action_count": same_action_count,
            "changed_action_count": changed_action_count,
            "pair_counts": dict(sorted(pair_counts.items())),
            "output_json": None if output_json is None else output_json.as_posix(),
            "output_md": None if output_md is None else output_md.as_posix(),
            "output_csv": None if output_csv is None else output_csv.as_posix(),
        },
    )
    return 0


def main() -> int:
    args = parse_args()
    if args.command == "replay-bundle":
        return run_replay_bundle(args)
    if args.command == "verify":
        return run_verify(args)
    if args.command == "followup":
        return run_followup(args)
    if args.command == "compare-populations":
        return run_compare_populations(args)
    raise RuntimeError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())