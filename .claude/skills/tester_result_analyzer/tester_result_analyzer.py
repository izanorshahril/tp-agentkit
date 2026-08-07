from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "tester_result_core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from tester_result_core import ResultTable, load_result_table, load_stdf_result_table  # noqa: E402


def load_table(path: Path, kind: str, id_row: int, sheet_name: str | None) -> ResultTable:
    if kind == "stdf_csv":
        return load_stdf_result_table(path)
    return load_result_table(path, kind, id_row=id_row, sheet_name=sheet_name)


def try_site_index(table: ResultTable) -> int | None:
    candidates = ["SITE", "Site", "site"]
    for candidate in candidates:
        try:
            return table.column_index(candidate)
        except ValueError:
            continue
    return None


def numeric_test_columns(table: ResultTable) -> list[tuple[int, int]]:
    if table.id_row is None:
        return []
    columns: list[tuple[int, int]] = []
    for index, cell in enumerate(table.id_row):
        text = cell.strip()
        if text.isdigit():
            columns.append((index, int(text)))
    return columns


def build_summary(table: ResultTable) -> dict[str, object]:
    site_index = try_site_index(table)
    site_counts = Counter()
    if site_index is not None:
        for row in table.iter_rows():
            if len(row) > site_index and row[site_index].strip():
                site_counts[row[site_index].strip()] += 1

    return {
        "mode": "summary",
        "source_format": table.source_format,
        "row_count": len(table.data_rows),
        "column_count": len(table.headers),
        "has_id_row": table.id_row is not None,
        "numeric_test_column_count": len(numeric_test_columns(table)),
        "site_counts": dict(site_counts),
    }


def build_site_skew(table: ResultTable, test_id: int | None) -> dict[str, object]:
    site_index = try_site_index(table)
    if site_index is None:
        raise ValueError("SITE column not found; site-skew mode requires a site column.")

    counts = Counter()
    if test_id is None:
        for row in table.iter_rows():
            if len(row) > site_index and row[site_index].strip():
                counts[row[site_index].strip()] += 1
    else:
        test_index = table.column_for_test_id(test_id)
        for row in table.iter_rows_with_values(test_index):
            if len(row) > site_index and row[site_index].strip():
                counts[row[site_index].strip()] += 1

    if not counts:
        max_site = None
        min_site = None
        spread = 0
    else:
        max_site = max(counts.items(), key=lambda item: item[1])
        min_site = min(counts.items(), key=lambda item: item[1])
        spread = max_site[1] - min_site[1]

    return {
        "mode": "site-skew",
        "source_format": table.source_format,
        "test_id": test_id,
        "site_counts": dict(counts),
        "max_site": max_site,
        "min_site": min_site,
        "spread": spread,
    }


def build_test_coverage(table: ResultTable, top: int) -> dict[str, object]:
    test_columns = numeric_test_columns(table)
    coverage_rows: list[dict[str, object]] = []

    for column_index, test_id in test_columns:
        nonempty = 0
        for row in table.iter_rows():
            if len(row) > column_index and row[column_index].strip():
                nonempty += 1
        coverage_rows.append({
            "test_id": test_id,
            "column_index": column_index,
            "nonempty_rows": nonempty,
            "column_name": table.column_name(column_index),
        })

    coverage_rows.sort(key=lambda item: item["nonempty_rows"], reverse=True)
    return {
        "mode": "test-coverage",
        "source_format": table.source_format,
        "test_id_column_count": len(test_columns),
        "top": coverage_rows[:top],
    }


def print_human(report: dict[str, object]) -> None:
    mode = report["mode"]
    print(f"=== TESTER RESULT ANALYZER: {mode.upper()} ===")
    print(json.dumps(report, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generic analyzer for standard tester result tables.")
    parser.add_argument("input_path", type=Path, help="Result source path")
    parser.add_argument("--kind", choices=["stdf_csv", "csv", "xlsx", "tester_txt"], required=True, help="Input result kind")
    parser.add_argument("--mode", choices=["summary", "site-skew", "test-coverage"], required=True, help="Analysis mode")
    parser.add_argument("--sheet", help="Worksheet name for xlsx")
    parser.add_argument("--id-row", type=int, default=1, help="1-based row containing IDs for csv/xlsx/tester_txt table modes")
    parser.add_argument("--test-id", type=int, help="Optional test ID for site-skew by specific test column")
    parser.add_argument("--top", type=int, default=20, help="Row limit for coverage output")
    parser.add_argument(
        "--report-json",
        "--json",
        dest="report_json",
        action="store_true",
        help="Print compact JSON only. --json is kept as a compatibility alias.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    table = load_table(args.input_path, args.kind, args.id_row, args.sheet)

    if args.mode == "summary":
        report = build_summary(table)
    elif args.mode == "site-skew":
        report = build_site_skew(table, args.test_id)
    else:
        report = build_test_coverage(table, args.top)

    if args.report_json:
        print(json.dumps(report, separators=(",", ":")))
        return

    print_human(report)


if __name__ == "__main__":
    main()
