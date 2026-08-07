from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SKILLS_ROOT = Path(__file__).resolve().parents[1]
LS_UPDATER_ROOT = SKILLS_ROOT / "ls-updater"
for candidate in (SKILLS_ROOT, LS_UPDATER_ROOT):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from ls_updater_csv import parse_csv_row  # type: ignore
from ls_updater_parse import CSV_FORMAT_OPLUS, CSV_FORMAT_SPL, CSV_FORMAT_SPAT, detect_csv_format, read_csv_preview, split_macro_args, split_top_level_commas  # type: ignore
from _io_support import read_csv_dict_rows, to_display_path
from spl_scope_screening import HARD_SCOPE_REVIEW_KEYS, build_scope_screening_from_rows, classify_scope_flags  # type: ignore


KNOWLEDGE_PATHS = [
    ".claude/knowledge/spl_workflow_and_methodology.md",
    ".claude/knowledge/spl_csv_schema.md",
    ".claude/knowledge/spl_reference_families.md",
    ".claude/knowledge/limit_env_mapping.md",
    ".claude/knowledge/constraints.md",
]

UPDATE_SOURCE_KINDS = {"spl_csv", "spat_csv", "o_plus_csv"}
REVIEW_SOURCE_KINDS = {"ye_workbook", "html_report", "text_report", "pdf_report"}

REGEX_MACRO_CALL = re.compile(r"\$\{\s*(\w+)\s*\((.*?)\)\s*\}")
REGEX_TABLE_TID = re.compile(r"^\s*(\d+)\s*,")
REGEX_ENV_BLOCK_TID = re.compile(r"^\s*T(\d+)\b")
REGEX_ENV_CELL = re.compile(r"\b([A-Z]{3})\(([^)]*)\)")
KNOWN_ENV_NAMES = {
    "FTC",
    "FTH",
    "FTR",
    "FTA",
    "QAC",
    "QAH",
    "QAR",
    "EWC",
    "EWH",
    "EWA",
    "EWR",
}


def find_exact_header(headers: list[str], candidates: list[str]) -> str:
    header_map = {header.strip().casefold(): header for header in headers}
    for candidate in candidates:
        match = header_map.get(candidate.casefold())
        if match:
            return match
    return ""


def present_headers(headers: list[str], candidates: list[str]) -> list[str]:
    found: list[str] = []
    for candidate in candidates:
        match = find_exact_header(headers, [candidate])
        if match:
            found.append(match)
    return found


def build_csv_schema_summary(headers: list[str], csv_format: str | None) -> dict[str, Any]:
    if csv_format == CSV_FORMAT_SPL:
        return {
            "row_order_column": find_exact_header(headers, ["Seq"]),
            "test_program_column": find_exact_header(headers, ["TestProgram"]),
            "test_number_column": find_exact_header(headers, ["TestNumber", "TestID"]),
            "parameter_column": find_exact_header(headers, ["Parameter"]),
            "update_limit_columns": present_headers(headers, ["Scaled_LSPL", "Scaled_USPL"]),
            "current_limit_columns": present_headers(headers, ["Scaled_LSL", "Scaled_USL"]),
            "raw_limit_columns": present_headers(headers, ["LSL", "USL", "LSPL", "USPL"]),
            "unit_columns": present_headers(headers, ["ScaledUnit", "ParameterUnit", "PreferredUnit", "Scale"]),
            "comment_column": find_exact_header(headers, ["Comment"]),
            "fail_column": find_exact_header(headers, ["Fail%", "%Fail", "Good Fail%"]),
            "notes": [
                "Use Scaled_LSPL and Scaled_USPL as the default TP update source when the CSV is approved.",
                "Do not rely on one fail-rate header spelling or on the field being present at all; real YE exports vary between Fail%, %Fail, Good Fail%, or no fail-rate column.",
                "Prefer the CSV TestProgram field over filename tokens when confirming the target TP variant.",
            ],
        }
    return {}
def build_scope_screening(path: Path, csv_format: str | None) -> dict[str, Any]:
    if csv_format not in {CSV_FORMAT_SPL, CSV_FORMAT_SPAT, CSV_FORMAT_OPLUS}:
        return {}

    rows = read_csv_dict_rows(path)
    return build_scope_screening_from_rows(rows)


def resolve_spl_columns(headers: list[str]) -> dict[str, str]:
    unit = find_exact_header(headers, ["ScaledUnit"])
    if not unit:
        unit = find_exact_header(headers, ["Unit"])
    return {
        "tid": find_exact_header(headers, ["TestNumber", "TestID"]),
        "ll": find_exact_header(headers, ["Scaled_LSPL", "LSPL", "Lower Limit"]),
        "ul": find_exact_header(headers, ["Scaled_USPL", "USPL", "Upper Limit"]),
        "scale": find_exact_header(headers, ["Scale", "UnitMultiplier"]),
        "unit": unit,
    }


def extract_tid_from_ls_line(line: str) -> tuple[str, str]:
    macro_match = REGEX_MACRO_CALL.search(line)
    if macro_match:
        raw_args = split_macro_args(macro_match.group(2))
        args_list = [arg.strip() for arg in raw_args]
        if args_list:
            return args_list[0].replace('"', "").strip(), "macro"

    env_match = REGEX_ENV_BLOCK_TID.match(line)
    if env_match:
        return env_match.group(1), "env_block"

    table_match = REGEX_TABLE_TID.match(line)
    if table_match:
        return table_match.group(1), "table"

    return "", ""


def parse_ls_screening_rows(ls_path: Path) -> dict[str, list[dict[str, Any]]]:
    rows_by_tid: dict[str, list[dict[str, Any]]] = {}
    for line_number, line in enumerate(ls_path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        commented = line.lstrip().startswith("#")
        candidate = line.lstrip("#").lstrip() if commented else line
        tid, row_kind = extract_tid_from_ls_line(candidate)
        if not tid:
            continue
        rows_by_tid.setdefault(tid, []).append(
            {
                "line": line_number,
                "kind": row_kind,
                "commented": commented,
                "text": candidate,
            }
        )
    return rows_by_tid


def find_target_env_cell(line: str, env: str) -> str | None:
    target_env = (env or "").upper()
    for match in REGEX_ENV_CELL.finditer(line):
        env_name = match.group(1).upper()
        if env_name not in KNOWN_ENV_NAMES:
            continue
        if target_env and target_env != "ALL" and env_name != target_env:
            continue
        return match.group(2).strip()
    return None


def has_parsable_env_limits(env_value: str | None) -> bool:
    if env_value is None:
        return False
    return re.match(
        r"(?P<pre_ul>\s*)(?P<ul>[^,]+?)(?P<post_ul>\s*),(?P<pre_ll>\s*)(?P<ll>.+?)(?P<post_ll>\s*)$",
        env_value,
    ) is not None


def classify_ls_row_for_screening(row: dict[str, Any], env: str) -> str:
    if row["commented"]:
        return "commented_in_ls"

    if row["kind"] == "macro":
        return "active_in_ls"

    if row["kind"] == "table":
        parts = split_top_level_commas(row["text"])
        if len(parts) < 5 or "[" not in row["text"] or "]" not in row["text"]:
            return "missing_ll_ul_in_ls"
        return "active_in_ls"

    if row["kind"] == "env_block":
        env_value = find_target_env_cell(row["text"], env)
        if env_value is None:
            return "target_env_missing_in_ls"
        if not has_parsable_env_limits(env_value):
            return "missing_ll_ul_in_ls"
        return "active_in_ls"

    return "present_other_reason"


def classify_tid_against_ls(rows_by_tid: dict[str, list[dict[str, Any]]], tid: str, env: str) -> str:
    rows = rows_by_tid.get(tid, [])
    if not rows:
        return "absent_from_main"

    by_status: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        status = classify_ls_row_for_screening(row, env)
        by_status.setdefault(status, []).append(row)

    for status in [
        "active_in_ls",
        "commented_in_ls",
        "missing_ll_ul_in_ls",
        "target_env_missing_in_ls",
        "present_other_reason",
    ]:
        if by_status.get(status):
            return status
    return "absent_from_main"


def write_csv_rows(output_path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_screened_outputs(
    primary_input: dict[str, Any] | None,
    bulk_output_path: str,
    review_output_path: str,
    can_build_command: bool,
    args: argparse.Namespace,
) -> dict[str, Any]:
    if not primary_input:
        return {}
    if primary_input.get("kind") != "spl_csv":
        return {
            "status": "skipped",
            "reason": "screened CSV export currently supports SPL CSV inputs only.",
        }

    input_path = Path(primary_input["path"])
    headers, _ = read_csv_preview(str(input_path))
    if not headers:
        return {
            "status": "skipped",
            "reason": "could not read CSV headers for screened export.",
        }

    rows = read_csv_dict_rows(input_path)
    mapping = resolve_spl_columns(headers)
    rows_by_tid: dict[str, list[dict[str, Any]]] = {}
    ls_screening_enabled = bool(args.ls_path and args.env and Path(args.ls_path).exists())
    if ls_screening_enabled:
        rows_by_tid = parse_ls_screening_rows(Path(args.ls_path))

    bulk_rows: list[dict[str, str]] = []
    review_rows: list[dict[str, str]] = []
    review_reason_counts: Counter[str] = Counter()
    for row in rows:
        flags = classify_scope_flags(row)
        if flags:
            review_rows.append(row)
            review_reason_counts["scope_review_flags"] += 1
            continue

        record, reason, tid = parse_csv_row(row, CSV_FORMAT_SPL, mapping)
        if record is None:
            review_rows.append(row)
            review_reason_counts[reason or "invalid_csv_row"] += 1
            continue

        if ls_screening_enabled:
            ls_status = classify_tid_against_ls(rows_by_tid, str(tid), args.env)
            if ls_status != "active_in_ls":
                review_rows.append(row)
                review_reason_counts[ls_status] += 1
                continue

        bulk_rows.append(row)

    bulk_path = Path(bulk_output_path) if bulk_output_path else None
    review_path = Path(review_output_path) if review_output_path else None
    if bulk_path is not None:
        write_csv_rows(bulk_path, headers, bulk_rows)
    if review_path is not None:
        write_csv_rows(review_path, headers, review_rows)

    bulk_ready_for_update = bool(bulk_rows) and can_build_command and bulk_path is not None
    screened_command = ""
    if bulk_ready_for_update:
        screened_command = build_ls_updater_command(args, to_display_path(bulk_path))

    return {
        "status": "ok",
        "strategy": "conservative_exclude_flagged_and_ls_unupdatable_rows",
        "screened_rows": len(rows),
        "bulk_row_count": len(bulk_rows),
        "review_row_count": len(review_rows),
        "bulk_path": to_display_path(bulk_path) if bulk_path is not None else "",
        "review_path": to_display_path(review_path) if review_path is not None else "",
        "bulk_ready_for_update": bulk_ready_for_update,
        "screened_recommended_command": screened_command,
        "ls_screening_enabled": ls_screening_enabled,
        "review_reason_counts": dict(sorted(review_reason_counts.items())),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify SPL or SPAT limit inputs into the safest TP-AgentKit next step."
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        help="Input artifact path (repeatable or comma-separated).",
    )
    parser.add_argument("--source-tp", default="", help="Source TP folder or revision under testprogram/.")
    parser.add_argument("--ls", dest="ls_path", default="", help="Target .ls file path when known.")
    parser.add_argument("--env", default="", help="Approved environment scope such as FTC, FTR, FTH, EWC, EWR, EWH, or ALL.")
    parser.add_argument(
        "--approval-status",
        choices=["approved", "proposed", "unknown"],
        default="unknown",
        help="Whether the provided limits are already approved for TP implementation.",
    )
    parser.add_argument(
        "--target-handling",
        choices=["copied-revision", "in-place", "unknown"],
        default="unknown",
        help="Whether the TP work should use a copied revision or in-place handling.",
    )
    parser.add_argument(
        "--mode",
        choices=["analysis-only", "review-only", "edit"],
        default="",
        help="Optional explicit mode override.",
    )
    parser.add_argument(
        "--bulk-output",
        default="",
        help="Optional path for a conservative bulk-update CSV that excludes all flagged review rows.",
    )
    parser.add_argument(
        "--review-output",
        default="",
        help="Optional path for a review CSV containing every flagged row that was kept out of the bulk path.",
    )
    parser.add_argument("--report-json", action="store_true", help="Emit compact JSON to stdout.")
    return parser.parse_args()
def split_inputs(values: list[str]) -> list[Path]:
    resolved: list[Path] = []
    for value in values:
        for part in str(value).split(","):
            candidate = part.strip().strip('"')
            if candidate:
                resolved.append(Path(candidate))
    return resolved


def classify_input(path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {
        "path": to_display_path(path),
        "exists": path.exists(),
        "kind": "unknown",
        "csv_format": "",
    }
    if not path.exists():
        info["kind"] = "missing"
        return info

    suffix = path.suffix.lower()
    if suffix == ".csv":
        headers, _ = read_csv_preview(str(path))
        if headers is None:
            info["kind"] = "csv_unreadable"
            return info
        csv_format = detect_csv_format(headers)
        info["csv_format"] = csv_format or ""
        info["header_columns"] = headers
        info["schema_summary"] = build_csv_schema_summary(headers, csv_format)
        info["scope_screening"] = build_scope_screening(path, csv_format)
        if csv_format == CSV_FORMAT_SPL:
            info["kind"] = "spl_csv"
        elif csv_format == CSV_FORMAT_SPAT:
            info["kind"] = "spat_csv"
        elif csv_format == CSV_FORMAT_OPLUS:
            info["kind"] = "o_plus_csv"
        else:
            info["kind"] = "unknown_csv"
        return info

    if suffix in {".xlsx", ".xls"}:
        info["kind"] = "ye_workbook"
        return info
    if suffix in {".html", ".htm"}:
        info["kind"] = "html_report"
        return info
    if suffix in {".txt", ".md"}:
        info["kind"] = "text_report"
        return info
    if suffix == ".pdf":
        info["kind"] = "pdf_report"
        return info
    info["kind"] = f"{suffix[1:]}_file" if suffix else "file"
    return info


def infer_mode(explicit_mode: str, approval_status: str, detected_inputs: list[dict[str, Any]]) -> str:
    if explicit_mode:
        return explicit_mode
    input_kinds = {item["kind"] for item in detected_inputs}
    if approval_status == "approved" and input_kinds & UPDATE_SOURCE_KINDS:
        return "edit"
    if input_kinds & (UPDATE_SOURCE_KINDS | REVIEW_SOURCE_KINDS):
        return "review-only"
    return "analysis-only"


def determine_missing_anchors(args: argparse.Namespace, detected_inputs: list[dict[str, Any]]) -> list[str]:
    missing: list[str] = []
    input_kinds = {item["kind"] for item in detected_inputs}
    has_update_source = bool(input_kinds & UPDATE_SOURCE_KINDS)
    has_review_source = bool(input_kinds & REVIEW_SOURCE_KINDS)

    if not detected_inputs:
        missing.append("inputs")
        return missing

    if has_update_source:
        if args.approval_status == "unknown":
            missing.append("approval_status")
        if not args.source_tp:
            missing.append("source_tp")
        if args.target_handling == "unknown":
            missing.append("target_handling")
        if not args.ls_path:
            missing.append("ls_path")
        if not args.env:
            missing.append("env")
    elif has_review_source:
        if args.approval_status == "unknown":
            missing.append("approval_status")
    else:
        missing.append("inputs")
    return missing


def determine_stage(args: argparse.Namespace, detected_inputs: list[dict[str, Any]]) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    notes: list[str] = []
    if not detected_inputs:
        return "missing_inputs", ["No input artifacts were provided."], notes

    input_kinds = {item["kind"] for item in detected_inputs}
    if "missing" in input_kinds:
        blockers.append("One or more input artifact paths do not exist.")
    if "csv_unreadable" in input_kinds:
        blockers.append("At least one CSV input could not be read with the supported encodings.")
    if "unknown_csv" in input_kinds:
        blockers.append("At least one CSV input does not match the known SPL, SPAT, or O+ column patterns.")

    has_update_source = bool(input_kinds & UPDATE_SOURCE_KINDS)
    has_workbook = "ye_workbook" in input_kinds
    has_review_source = bool(input_kinds & REVIEW_SOURCE_KINDS)

    if args.ls_path:
        ls_path = Path(args.ls_path)
        if not ls_path.exists():
            blockers.append("The provided target .ls path does not exist yet.")
            return "ls_target_missing", blockers, notes

    if blockers:
        if has_workbook and not has_update_source:
            blockers.append("Export the approved workbook to CSV before using ls-updater.")
            return "export_csv_needed", blockers, notes
        return "blocked", blockers, notes

    if has_workbook and not has_update_source:
        blockers.append("Export the approved workbook to CSV before using ls-updater.")
        notes.append("Workbook input is review material only until it is exported to a CSV with limit columns.")
        return "export_csv_needed", blockers, notes

    if not has_update_source:
        if has_review_source:
            notes.append("The provided inputs look like review artifacts, not direct update sources.")
            return "review_source_only", blockers, notes
        return "unsupported_input", ["The provided inputs are not recognized as SPL, SPAT, or review artifacts."], notes

    if args.approval_status != "approved":
        blockers.append("Do not run ls-updater until the SPL or SPAT limits are explicitly approved for TP implementation.")
        return "review_before_update", blockers, notes

    if not args.source_tp:
        return "source_tp_needed", blockers, notes
    if args.target_handling == "unknown":
        return "target_handling_needed", blockers, notes
    if not args.ls_path:
        return "ls_target_needed", blockers, notes
    if not args.env:
        return "env_confirmation_needed", blockers, notes

    primary_input = next((item for item in detected_inputs if item["kind"] in UPDATE_SOURCE_KINDS), None)
    scope_screening = primary_input.get("scope_screening") if primary_input else {}
    if scope_screening and scope_screening.get("requires_scope_review"):
        blockers.append(
            "The CSV contains test classes that should be excluded or reviewed separately before a generic bulk SPL update."
        )
        notes.extend(scope_screening.get("recommended_actions", [])[:2])
        return "scope_review_needed", blockers, notes

    notes.append("A direct ls-updater path is available, but post-update .ls structure audits still remain mandatory.")
    return "ready_for_ls_updater", blockers, notes


def build_follow_up(missing_anchors: list[str], scope_screening: dict[str, Any] | None = None) -> list[str]:
    question_map = {
        "inputs": "Which approved SPL, SPAT, or Yield Explorer source file should I use?",
        "approval_status": "Are these limits already approved for TP implementation, or should I keep this as review-only first?",
        "source_tp": "Which source TP folder or revision should I use?",
        "target_handling": "Do you want a copied revision or in-place work?",
        "ls_path": "Which target .ls file should I update after the revision is confirmed?",
        "env": "Which environment scope should I apply: FTC, FTR, FTH, EWC, EWR, EWH, or ALL?",
    }
    follow_up = [question_map[item] for item in missing_anchors if item in question_map]
    if scope_screening and scope_screening.get("requires_scope_review"):
        follow_up.append(
            "Should I filter the CSV or prepare a review list first for the test classes that should stay out of the generic bulk SPL path?"
        )
    elif scope_screening and scope_screening.get("flag_counts", {}).get("continuity_tests"):
        follow_up.append(
            "For the continuity-like rows, should I split continuity open from continuity short before any implementation planning?"
        )
    return follow_up[:5]


def build_intake_checklist(
    args: argparse.Namespace,
    missing_anchors: list[str],
    primary_input: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    scope_screening = primary_input.get("scope_screening") if primary_input else {}
    flag_counts = scope_screening.get("flag_counts", {}) if scope_screening else {}
    bulk_scope_flags = {key: flag_counts.get(key, 0) for key in HARD_SCOPE_REVIEW_KEYS if flag_counts.get(key, 0)}
    continuity_flags = {
        key: flag_counts.get(key, 0)
        for key in ("continuity_tests", "continuity_open_tests", "continuity_short_tests")
        if flag_counts.get(key, 0)
    }
    cpk_yield_flags = {
        key: flag_counts.get(key, 0)
        for key in ("continuity_end_tests", "low_cpk_with_observed_fails", "yield_loss_above_target")
        if flag_counts.get(key, 0)
    }

    checklist = [
        {
            "id": "approval_and_scope",
            "status": "ok" if args.approval_status == "approved" and not missing_anchors else "review",
            "message": "Confirm approval, target TP, target .ls, and environment scope before any TP update.",
        },
        {
            "id": "bulk_scope_screen",
            "status": "warn" if bulk_scope_flags else "ok",
            "message": "Filter or separately review matching, delta, kelvin, continuity, NS/nA/UV, code-read, temperature, and unbin tests before any bulk SPL update.",
            "flag_counts": bulk_scope_flags,
        },
        {
            "id": "continuity_split",
            "status": "warn" if continuity_flags else "ok",
            "message": "Treat continuity open and continuity short separately: continuity open may tighten after review, continuity short usually keeps the current limit.",
            "flag_counts": continuity_flags,
        },
        {
            "id": "cpk_yield_review",
            "status": "warn" if cpk_yield_flags else "ok",
            "message": "Hold continuity end rows, low-Cpk rows with observed fails, and rows above about 0.00004% per-test yield loss for manual review.",
            "flag_counts": cpk_yield_flags,
        },
    ]
    return checklist


def build_ls_updater_command(args: argparse.Namespace, csv_path: str) -> str:
    return (
        f'python .claude/skills/ls-updater/ls_updater.py --csv "{csv_path}" '
        f'--ls "{to_display_path(args.ls_path)}" --env {args.env} --silent --in-place --log --report-json'
    )


def build_recommended_command(args: argparse.Namespace, detected_inputs: list[dict[str, Any]], stage: str) -> str:
    if stage != "ready_for_ls_updater":
        return ""
    primary = next((item for item in detected_inputs if item["kind"] in UPDATE_SOURCE_KINDS), None)
    if primary is None:
        return ""
    return build_ls_updater_command(args, primary["path"])


def main() -> int:
    args = parse_args()
    input_paths = split_inputs(args.input)
    detected_inputs = [classify_input(path) for path in input_paths]
    missing_anchors = determine_missing_anchors(args, detected_inputs)
    workflow_stage, blockers, notes = determine_stage(args, detected_inputs)
    likely_mode = infer_mode(args.mode, args.approval_status, detected_inputs)
    primary_input = next((item for item in detected_inputs if item["kind"] in UPDATE_SOURCE_KINDS), None)
    if primary_input is None and detected_inputs:
        primary_input = detected_inputs[0]
    scope_screening = primary_input.get("scope_screening") if primary_input else {}
    recommended_command = build_recommended_command(args, detected_inputs, workflow_stage)
    can_build_screened_command = (
        args.approval_status == "approved"
        and bool(args.source_tp)
        and args.target_handling != "unknown"
        and bool(args.ls_path)
        and bool(args.env)
    )
    screened_outputs = {}
    if args.bulk_output or args.review_output:
        screened_outputs = build_screened_outputs(
            primary_input,
            args.bulk_output,
            args.review_output,
            can_build_screened_command,
            args,
        )
        if screened_outputs.get("status") == "skipped":
            notes.append(screened_outputs["reason"])
        elif screened_outputs.get("bulk_path"):
            notes.append(
                "A conservative screened bulk CSV was generated by excluding all flagged review rows from the raw SPL export."
            )

    payload = {
        "status": "ok",
        "likely_mode": likely_mode,
        "workflow_stage": workflow_stage,
        "ready_for_update": workflow_stage == "ready_for_ls_updater",
        "approval_status": args.approval_status,
        "source_tp": args.source_tp,
        "target_handling": args.target_handling,
        "ls_path": to_display_path(args.ls_path) if args.ls_path else "",
        "env": args.env,
        "detected_inputs": detected_inputs,
        "primary_input": primary_input,
        "missing_anchors": missing_anchors,
        "blockers": blockers,
        "recommended_follow_up": build_follow_up(missing_anchors, scope_screening),
        "recommended_command": recommended_command,
        "screened_outputs": screened_outputs,
        "recommended_knowledge": KNOWLEDGE_PATHS,
        "intake_checklist": build_intake_checklist(args, missing_anchors, primary_input),
        "notes": notes,
    }

    if args.report_json:
        print(json.dumps(payload, separators=(",", ":")))
    else:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())