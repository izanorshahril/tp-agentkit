from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent
SKILLS_ROOT = SKILL_DIR.parent
REPO_ROOT = SKILL_DIR.parents[2]
LS_UPDATER_ROOT = SKILLS_ROOT / "ls-updater"
for candidate in (SKILLS_ROOT, LS_UPDATER_ROOT):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from ls_updater_audit import is_unit_mismatch, split_unit_prefix  # type: ignore
from ls_updater_csv import parse_csv_row  # type: ignore
from ls_updater_parse import (  # type: ignore
    CSV_FORMAT_SPL,
    EPS,
    clean_token,
    detect_csv_format,
    is_na_token,
    read_csv_preview,
    scale_token_to_exp,
    split_numeric_suffix,
)
from spl_scope_screening import build_scope_screening_from_rows  # type: ignore


ROW_RE = re.compile(r"^\s*(?P<comment>#)?\s*T(?P<tid>\d+)\s*\{(?P<body>.*)$")


def to_display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def find_header(headers, candidates, allow_contains=True):
    for candidate in candidates:
        for header in headers:
            if candidate.lower() == header.lower():
                return header
        if allow_contains:
            for header in headers:
                if candidate.lower() in header.lower():
                    return header
    return None


def resolve_spl_columns(headers):
    unit = find_header(headers, ["ScaledUnit"], allow_contains=False)
    if not unit:
        unit = find_header(headers, ["Unit"], allow_contains=False)
    return {
        "tid": find_header(headers, ["TestNumber", "Test No", "TestID", "TestName"]),
        "ll": find_header(headers, ["Scaled_LSPL", "LSPL", "Lower Limit"]),
        "ul": find_header(headers, ["Scaled_USPL", "USPL", "Upper Limit"]),
        "scale": find_header(headers, ["Scale", "UnitMultiplier"], allow_contains=False),
        "unit": unit,
        "testprogram": find_header(headers, ["TestProgram"], allow_contains=False),
        "parameter": find_header(headers, ["Parameter"], allow_contains=False),
        "comment": find_header(headers, ["Comment"], allow_contains=False),
    }


def parse_csv_records(csv_path: Path):
    headers, _ = read_csv_preview(str(csv_path))
    if not headers:
        raise ValueError(f"Unable to read CSV headers from {csv_path}")
    csv_format = detect_csv_format(headers)
    if csv_format != CSV_FORMAT_SPL:
        raise ValueError(f"Unsupported CSV format for read-only SPL compare: {csv_format}")

    mapping = resolve_spl_columns(headers)
    required = ["tid", "ll", "ul", "scale", "unit"]
    missing_required = [key for key in required if not mapping.get(key)]
    if missing_required:
        raise ValueError(f"Missing required SPL columns in {csv_path}: {', '.join(missing_required)}")

    records = {}
    duplicate_tids = set()
    csv_rows = 0
    rows_with_limits = 0
    testprograms = set()
    screening_rows = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            csv_rows += 1
            record, _, tid = parse_csv_row(row, csv_format, mapping)
            if record is None:
                continue
            rows_with_limits += 1
            screening_rows.append({str(key or ""): str(value or "") for key, value in row.items()})

            tid_text = str(record["tid"]).strip()
            if tid_text in records:
                duplicate_tids.add(tid_text)
                continue

            parameter = row.get(mapping.get("parameter") or "", "") if mapping.get("parameter") else ""
            comment = row.get(mapping.get("comment") or "", "") if mapping.get("comment") else ""
            testprogram = row.get(mapping.get("testprogram") or "", "") if mapping.get("testprogram") else ""
            if testprogram:
                testprograms.add(str(testprogram).strip())
            record["parameter"] = str(parameter).strip()
            record["csv_comment"] = str(comment).strip()
            records[tid_text] = record

    return {
        "records": records,
        "csv_rows": csv_rows,
        "rows_with_limits": rows_with_limits,
        "duplicate_tids": duplicate_tids,
        "csv_testprograms": sorted(testprograms),
        "scope_screening": build_scope_screening_from_rows(screening_rows),
    }


def parse_ls_rows(ls_path: Path):
    rows = {}
    for line_number, line in enumerate(ls_path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        match = ROW_RE.match(line)
        if not match:
            continue
        body = match.group("body")
        comment_match = re.search(r'Comment\s*=\s*"([^"]*)"', body)
        tid = match.group("tid")
        rows.setdefault(tid, []).append(
            {
                "line": line_number,
                "is_commented": bool(match.group("comment")),
                "body": body,
                "ls_comment": comment_match.group(1).strip() if comment_match else "",
            }
        )
    return rows


def parse_env_cell(body: str, env: str):
    match = re.search(rf"\b{re.escape(env)}\((.*?)\)", body)
    if not match:
        return None
    return match.group(1).strip()


def split_limits(env_value: str | None):
    if env_value is None:
        return None, None
    parts = [part.strip() for part in env_value.split(",")]
    if len(parts) == 1 and parts[0] and is_na_token(parts[0]):
        return parts[0], parts[0]
    upper = parts[0] if parts else None
    lower = parts[1] if len(parts) > 1 else None
    return upper, lower


def extract_scaled_unit(*tokens):
    for token in tokens:
        if not token or is_na_token(token):
            continue
        _, suffix = split_numeric_suffix(token)
        suffix = clean_token(suffix)
        if suffix:
            return suffix
    return ""


def parse_token_to_base(token):
    if token is None or is_na_token(token):
        return None
    number_text, suffix = split_numeric_suffix(token)
    if number_text is None:
        return None
    try:
        value = float(number_text)
    except ValueError:
        return None
    suffix = clean_token(suffix)
    prefix, _ = split_unit_prefix(suffix)
    exponent = scale_token_to_exp(prefix)
    return value * (10 ** exponent)


def values_equivalent(left, right):
    if left is None or right is None:
        return False
    return abs(left - right) <= EPS


def build_ls_detail(row, env):
    env_value = parse_env_cell(row["body"], env)
    current_upper, current_lower = split_limits(env_value)
    scaled_unit = extract_scaled_unit(current_upper, current_lower)
    return {
        "line": row["line"],
        "is_commented": row["is_commented"],
        "ls_comment": row["ls_comment"],
        "env_value": env_value,
        "current_upper": current_upper,
        "current_lower": current_lower,
        "ls_scaled_unit": scaled_unit,
        "upper_is_na": is_na_token(current_upper) if current_upper else False,
        "lower_is_na": is_na_token(current_lower) if current_lower else False,
    }


def pick_row_for_env(rows, env):
    active_rows = []
    commented_rows = []
    target_na_rows = []
    other_rows = []
    for row in rows:
        detail = build_ls_detail(row, env)
        if detail["env_value"] is None:
            other_rows.append(detail)
        elif detail["upper_is_na"] and detail["lower_is_na"]:
            target_na_rows.append(detail)
        elif detail["is_commented"]:
            commented_rows.append(detail)
        else:
            active_rows.append(detail)

    if active_rows:
        return "active_in_ls", active_rows[0], active_rows
    if commented_rows:
        return "commented_in_ls", commented_rows[0], commented_rows
    if target_na_rows:
        return "target_env_na", target_na_rows[0], target_na_rows
    if other_rows:
        return "present_other_reason", other_rows[0], other_rows
    return "absent_from_main", None, []


def compact_detail(record, detail=None, reason=None):
    payload = {
        "tid": int(record["tid"]),
        "parameter": record.get("parameter", ""),
        "proposed_upper": record.get("ul", ""),
        "proposed_lower": record.get("ll", ""),
    }
    if detail:
        payload.update(
            {
                "line": detail["line"],
                "ls_comment": detail.get("ls_comment", ""),
                "current_upper": detail.get("current_upper"),
                "current_lower": detail.get("current_lower"),
                "ls_scaled_unit": detail.get("ls_scaled_unit"),
            }
        )
    if reason:
        payload["reason"] = reason
    return payload


def append_example(store, key, item, limit):
    if limit <= 0:
        return
    store.setdefault(key, [])
    if len(store[key]) < limit:
        store[key].append(item)


def compare_case(csv_path: Path, ls_path: Path, env: str, case_name: str | None = None, examples_limit: int = 8):
    csv_info = parse_csv_records(csv_path)
    ls_rows = parse_ls_rows(ls_path)

    examples = {}
    coverage_counts = {
        "active_in_ls": 0,
        "commented_in_ls": 0,
        "target_env_na": 0,
        "present_other_reason": 0,
        "absent_from_main": 0,
    }
    comparison_counts = {
        "changed_rows": 0,
        "unchanged_rows": 0,
        "non_comparable_rows": 0,
        "base_unit_mismatch_rows": 0,
        "partial_na_rows": 0,
        "non_numeric_rows": 0,
    }

    for tid, record in csv_info["records"].items():
        record["tid"] = tid
        rows = ls_rows.get(tid, [])
        coverage_key, chosen, _ = pick_row_for_env(rows, env)
        coverage_counts[coverage_key] += 1

        if coverage_key != "active_in_ls":
            append_example(examples, f"{coverage_key}_examples", compact_detail(record, chosen), examples_limit)
            continue

        append_example(examples, "active_in_ls_examples", compact_detail(record, chosen), examples_limit)

        csv_scaled_unit = record.get("scaled_unit", "")
        ls_scaled_unit = chosen.get("ls_scaled_unit", "")
        if is_unit_mismatch(csv_scaled_unit, ls_scaled_unit):
            comparison_counts["non_comparable_rows"] += 1
            comparison_counts["base_unit_mismatch_rows"] += 1
            append_example(
                examples,
                "base_unit_mismatch_examples",
                compact_detail(record, chosen, reason=f"CSV={csv_scaled_unit} LS={ls_scaled_unit}"),
                examples_limit,
            )
            continue

        current_upper_base = parse_token_to_base(chosen.get("current_upper"))
        current_lower_base = parse_token_to_base(chosen.get("current_lower"))
        if chosen.get("upper_is_na") or chosen.get("lower_is_na"):
            comparison_counts["non_comparable_rows"] += 1
            comparison_counts["partial_na_rows"] += 1
            append_example(
                examples,
                "non_comparable_examples",
                compact_detail(record, chosen, reason="target env has NA in one limit cell"),
                examples_limit,
            )
            continue

        if current_upper_base is None or current_lower_base is None:
            comparison_counts["non_comparable_rows"] += 1
            comparison_counts["non_numeric_rows"] += 1
            append_example(
                examples,
                "non_comparable_examples",
                compact_detail(record, chosen, reason="target env has non-numeric limit text"),
                examples_limit,
            )
            continue

        same_upper = values_equivalent(current_upper_base, record["base_ul"])
        same_lower = values_equivalent(current_lower_base, record["base_ll"])
        if same_upper and same_lower:
            comparison_counts["unchanged_rows"] += 1
            append_example(examples, "unchanged_examples", compact_detail(record, chosen), examples_limit)
            continue

        comparison_counts["changed_rows"] += 1
        append_example(examples, "changed_examples", compact_detail(record, chosen), examples_limit)

    payload = {
        "status": "ok",
        "case": case_name or csv_path.stem,
        "env": env,
        "csv": to_display_path(csv_path),
        "ls": to_display_path(ls_path),
        "csv_rows": csv_info["csv_rows"],
        "rows_with_limits": csv_info["rows_with_limits"],
        "matched_rows": coverage_counts["active_in_ls"],
        "changed_rows": comparison_counts["changed_rows"],
        "unchanged_rows": comparison_counts["unchanged_rows"],
        "non_comparable_rows": comparison_counts["non_comparable_rows"],
        "commented_in_ls": coverage_counts["commented_in_ls"],
        "target_env_na_rows": coverage_counts["target_env_na"],
        "present_other_reason_rows": coverage_counts["present_other_reason"],
        "absent_from_main_rows": coverage_counts["absent_from_main"],
        "ambiguous_multi_occurrence": len(csv_info["duplicate_tids"]),
        "base_unit_mismatch_rows": comparison_counts["base_unit_mismatch_rows"],
        "partial_na_rows": comparison_counts["partial_na_rows"],
        "non_numeric_rows": comparison_counts["non_numeric_rows"],
        "csv_testprograms": csv_info["csv_testprograms"],
        "scope_screening": csv_info["scope_screening"],
        **examples,
    }
    return payload


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Compare an SPL CSV against a target LS file without editing it.")
    parser.add_argument("--csv", required=True, help="Path to the SPL CSV input")
    parser.add_argument("--ls", required=True, help="Path to the target LS file")
    parser.add_argument("--env", required=True, help="Target LS env cell to compare, for example FTC or FTH")
    parser.add_argument("--case-name", help="Optional report label")
    parser.add_argument("--output", help="Optional path to write the pretty JSON report")
    parser.add_argument("--examples-limit", type=int, default=8, help="Maximum examples to keep per bucket")
    parser.add_argument("--report-json", action="store_true", help="Emit compact JSON to stdout for automation")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    csv_path = Path(args.csv).resolve()
    ls_path = Path(args.ls).resolve()

    payload = compare_case(
        csv_path=csv_path,
        ls_path=ls_path,
        env=args.env,
        case_name=args.case_name,
        examples_limit=args.examples_limit,
    )

    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        payload["output"] = to_display_path(output_path)

    if args.report_json:
        print(json.dumps(payload, ensure_ascii=True, separators=(",", ":")))
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())