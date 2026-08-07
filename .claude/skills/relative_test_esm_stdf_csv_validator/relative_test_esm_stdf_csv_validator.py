from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CORE_DIR = Path(__file__).resolve().parents[1] / "tester_result_core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from tester_result_core import (  # noqa: E402
    ResultTable,
    load_result_table,
    load_stdf_result_table,
    parse_active_ids,
    parse_float,
)


@dataclass
class PairResult:
    name: str
    test_id: int
    judge_id: int
    samples: int
    max_abs_error: float
    worst_site: str
    worst_part: str
    actual: float
    computed: float


@dataclass
class LoopPairResult:
    name: str
    test_id: int
    judge_id: int
    loops: int
    compared_rows: int
    correct_rows: int
    incorrect_rows: int
    skipped_rows: int
    max_abs_delta: float
    worst_loop: int
    actual: float
    computed: float
    verdict: str


def sample_stdev(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean_value = sum(values) / len(values)
    variance = sum((value - mean_value) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def load_loop_table(csv_path: Path | None, xlsx_path: Path | None, txt_path: Path | None, sheet_name: str | None, id_row: int) -> ResultTable:
    if csv_path:
        return load_result_table(csv_path, "csv", id_row=id_row)
    elif xlsx_path:
        return load_result_table(xlsx_path, "xlsx", id_row=id_row, sheet_name=sheet_name)
    elif txt_path:
        return load_result_table(txt_path, "tester_txt", id_row=id_row)
    else:
        raise ValueError("Provide --loop-csv, --loop-xlsx, or --loop-txt for bulk loop validation.")


def validate_loop_pairs(
    table: ResultTable,
    test_ids: list[int],
    judge_ids: list[int],
    delta_threshold: float,
) -> tuple[dict[str, object], list[LoopPairResult]]:
    if len(test_ids) != len(judge_ids):
        raise ValueError("Length mismatch between test IDs and judge IDs")

    results: list[LoopPairResult] = []
    matched_pairs = 0

    for test_id, judge_id in zip(test_ids, judge_ids):
        try:
            test_idx = table.column_for_test_id(test_id)
            judge_idx = table.column_for_test_id(judge_id)
        except ValueError:
            continue

        matched_pairs += 1
        raw_history: list[float] = []
        included_history: list[float] = []
        prev_gate_mean: float | None = None
        prev_gate_sigma: float | None = 0.0
        max_abs_delta = -1.0
        worst_loop = 0
        worst_actual = 0.0
        worst_computed = 0.0
        correct_rows = 0
        incorrect_rows = 0
        skipped_rows = 0
        compared_rows = 0
        loops = 0

        for row_number, row in enumerate(table.iter_rows(), start=1):
            source_text = row[test_idx].strip() if len(row) > test_idx else ""
            judge_text = row[judge_idx].strip() if len(row) > judge_idx else ""
            source_value = parse_float(source_text) if source_text else None
            judge_value = parse_float(judge_text) if judge_text else None

            if source_value is None:
                continue

            loops += 1
            raw_history.append(source_value)

            if len(raw_history) == 1:
                included_history.append(source_value)
                prev_gate_mean = source_value
                prev_gate_sigma = 0.0
                skipped_rows += 1
                continue

            rolling_mean = average(raw_history)
            recent_sigma = sample_stdev(raw_history[-2:])
            gate_condition = False
            if rolling_mean is not None and recent_sigma is not None and recent_sigma != 0.0:
                gate_condition = abs((rolling_mean - source_value) / recent_sigma) < 6.0

            if gate_condition:
                gate_mean = rolling_mean
                gate_sigma = sample_stdev(raw_history)
            else:
                gate_mean = prev_gate_mean
                gate_sigma = prev_gate_sigma

            if gate_mean is None or gate_sigma in (None, 0.0):
                skipped_rows += 1
                prev_gate_mean = gate_mean
                prev_gate_sigma = gate_sigma
                continue

            gate_deviation = (source_value - gate_mean) / gate_sigma
            if abs(gate_deviation) < 6.0:
                included_history.append(source_value)

            included_mean = average(included_history)
            included_sigma = sample_stdev(included_history)
            if judge_value is None or included_mean is None or included_sigma in (None, 0.0):
                skipped_rows += 1
                prev_gate_mean = gate_mean
                prev_gate_sigma = gate_sigma
                continue

            computed = (source_value - included_mean) / included_sigma
            delta = judge_value - computed
            compared_rows += 1
            if abs(delta) > delta_threshold:
                incorrect_rows += 1
            else:
                correct_rows += 1

            abs_delta = abs(delta)
            if abs_delta > max_abs_delta:
                max_abs_delta = abs_delta
                worst_loop = row_number
                worst_actual = judge_value
                worst_computed = computed

            prev_gate_mean = gate_mean
            prev_gate_sigma = gate_sigma

        if incorrect_rows > 0:
            verdict = "INCORRECT"
        elif compared_rows > 0:
            verdict = "CORRECT"
        else:
            verdict = "NO_DATA"

        results.append(
            LoopPairResult(
                name=str(judge_id),
                test_id=test_id,
                judge_id=judge_id,
                loops=loops,
                compared_rows=compared_rows,
                correct_rows=correct_rows,
                incorrect_rows=incorrect_rows,
                skipped_rows=skipped_rows,
                max_abs_delta=max_abs_delta,
                worst_loop=worst_loop,
                actual=worst_actual,
                computed=worst_computed,
                verdict=verdict,
            )
        )

    global_max = max((result.max_abs_delta for result in results if result.max_abs_delta >= 0.0), default=float("nan"))
    summary = {
        "matched_pairs": matched_pairs,
        "global_max_abs_delta": global_max,
    }
    return summary, sorted(results, key=lambda item: item.max_abs_delta, reverse=True)


def relative_value(sample: float, state: dict[str, float]) -> tuple[float, float, float]:
    count = int(state["count"])
    if count == 0:
        return 0.0, sample, 0.0

    n = float(count)
    mean_new = ((1.0 - (1.0 / (n + 1.0))) * state["mean_old"]) + ((1.0 / (n + 1.0)) * sample)
    esm_var_a = ((n - 1.0) / n) * (state["sigma_old"] ** 2)
    esm_var_b = ((sample - state["mean_old"]) ** 2) / (n + 1.0)
    if esm_var_b == 0.0:
        esm_var_b = 1e-14
    sigma_new = math.sqrt(esm_var_a + esm_var_b)
    rel = (sample - mean_new) / sigma_new
    if not math.isfinite(rel):
        rel = 999.0
    return rel, mean_new, sigma_new


def validate_env(csv_path: Path, list_path: Path, test_symbol: str, judge_symbol: str) -> tuple[dict[str, object], list[PairResult]]:
    test_ids = parse_active_ids(list_path, test_symbol)
    judge_ids = parse_active_ids(list_path, judge_symbol)
    if len(test_ids) != len(judge_ids):
        raise ValueError(f"Length mismatch for {csv_path.name}")

    table = load_stdf_result_table(csv_path)
    site_idx = table.column_index("SITE")

    pair_results: list[PairResult] = []
    matched_pairs = 0

    for test_id, judge_id in zip(test_ids, judge_ids):
        try:
            test_idx = table.column_for_test_id(test_id)
            judge_idx = table.column_for_test_id(judge_id)
        except ValueError:
            continue

        matched_pairs += 1
        states: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0.0, "mean_old": 0.0, "sigma_old": 0.0})
        max_abs_error = -1.0
        worst_site = ""
        worst_part = ""
        worst_actual = 0.0
        worst_computed = 0.0
        samples = 0

        for row in table.iter_rows_with_values(test_idx, judge_idx):
            raw_test = row[test_idx].strip()
            raw_judge = row[judge_idx].strip()

            site = row[site_idx].strip()
            sample = float(raw_test)
            actual = float(raw_judge)
            state = states[site]
            computed, mean_new, sigma_new = relative_value(sample, state)

            error = abs(computed - actual)
            samples += 1
            if error > max_abs_error:
                max_abs_error = error
                worst_site = site
                worst_part = row[0].strip()
                worst_actual = actual
                worst_computed = computed

            state["count"] += 1.0
            if -15.0 < computed < 15.0:
                state["mean_old"] = mean_new
                state["sigma_old"] = sigma_new

        pair_results.append(
            PairResult(
                name=table.column_name(judge_idx),
                test_id=test_id,
                judge_id=judge_id,
                samples=samples,
                max_abs_error=max_abs_error,
                worst_site=worst_site,
                worst_part=worst_part,
                actual=worst_actual,
                computed=worst_computed,
            )
        )

    global_max = max((result.max_abs_error for result in pair_results), default=float("nan"))
    summary = {
        "csv": str(csv_path),
        "matched_pairs": matched_pairs,
        "global_max_abs_error": global_max,
    }
    return summary, sorted(pair_results, key=lambda item: item.max_abs_error, reverse=True)


def print_summary(title: str, summary: dict[str, object], results: list[PairResult], top: int) -> None:
    print(f"=== {title} ===")
    print(f"CSV={summary['csv']}")
    print(f"MatchedPairs={summary['matched_pairs']}")
    print(f"GlobalMaxAbsError={summary['global_max_abs_error']:.12f}")
    print("TopWorst:")
    for result in results[:top]:
        print(
            " | ".join(
                [
                    f"Err={result.max_abs_error:.12f}",
                    f"JudgeName={result.name}",
                    f"TestID={result.test_id}",
                    f"JudgeID={result.judge_id}",
                    f"Samples={result.samples}",
                    f"Site={result.worst_site}",
                    f"Part={result.worst_part}",
                    f"Actual={result.actual:.12f}",
                    f"Computed={result.computed:.12f}",
                ]
            )
        )


def print_first_visible_by_site(csv_path: Path, pairs: list[tuple[str, str]]) -> None:
    table = load_stdf_result_table(csv_path)
    site_idx = table.column_index("SITE")
    print("--- First Visible Per-Site Spot Checks ---")
    for test_id, judge_id in pairs:
        test_idx = table.column_for_test_id(int(test_id))
        judge_idx = table.column_for_test_id(int(judge_id))
        seen: dict[str, tuple[str, float, float]] = {}
        for row in table.iter_rows_with_values(test_idx, judge_idx):
            raw_test = row[test_idx].strip()
            raw_judge = row[judge_idx].strip()
            site = row[site_idx].strip()
            if site not in seen:
                seen[site] = (row[0].strip(), float(raw_test), float(raw_judge))
            if len(seen) == 4:
                break
        print(f"{test_id} {table.column_name(test_idx)} => {judge_id} {table.column_name(judge_idx)} {seen}")


def print_loop_summary(title: str, summary: dict[str, object], results: list[LoopPairResult], top: int) -> None:
    print(f"=== {title} LOOP VALIDATION ===")
    print(f"MatchedPairs={summary['matched_pairs']}")
    print(f"GlobalMaxAbsDelta={summary['global_max_abs_delta']:.12f}")
    print("TopWorst:")
    for result in results[:top]:
        max_delta = result.max_abs_delta if result.max_abs_delta >= 0.0 else float("nan")
        print(
            " | ".join(
                [
                    f"Verdict={result.verdict}",
                    f"MaxDelta={max_delta:.12f}",
                    f"TestID={result.test_id}",
                    f"JudgeID={result.judge_id}",
                    f"Loops={result.loops}",
                    f"Compared={result.compared_rows}",
                    f"Correct={result.correct_rows}",
                    f"Incorrect={result.incorrect_rows}",
                    f"Skipped={result.skipped_rows}",
                    f"WorstLoop={result.worst_loop}",
                    f"Actual={result.actual:.12f}",
                    f"Computed={result.computed:.12f}",
                ]
            )
        )


def parse_spot_checks(values: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for value in values:
        if ":" not in value:
            raise ValueError(f"Invalid --spot-check value: {value}")
        test_id, judge_id = value.split(":", 1)
        pairs.append((test_id.strip(), judge_id.strip()))
    return pairs


def preset_config(name: str) -> tuple[Path, Path, str, str, str, list[tuple[str, str]]]:
    presets = {
        "ur84-cold": (
            ROOT / "references" / "stdf" / "muat2kap_1_ur84fc004bg01_99611ag0rn_va542bdx_p_t_t9u-test-cold_20260331-010753_20260331-071150.std.gextb.std.gextb.csv",
            ROOT / "testprogram" / "UR84_0334" / "TestFunctions" / "SampleTestFunc" / "Relative_TestID_JudgeID_Cold_List.h",
            "RelativeTestIDList_Cold",
            "RelativeJudgeIDList_Cold",
            "UR84 COLD",
            [("70106", "99970106"), ("704020", "999704020"), ("70032", "99970032")],
        ),
        "ur84-hot": (
            ROOT / "references" / "stdf" / "muat2kl_1_ur84fh004bg01_99611a1vrm_va542bds_p_t_t9u-test-hot_20260331-015617_20260331-075856.std.gextb.std.gextb.csv",
            ROOT / "testprogram" / "UR84_0334" / "TestFunctions" / "SampleTestFunc" / "Relative_TestID_JudgeID_Hot_List.h",
            "RelativeTestIDList_Hot",
            "RelativeJudgeIDList_Hot",
            "UR84 HOT",
            [("70106", "99970106"), ("704020", "999704020"), ("70032", "99970032")],
        ),
    }
    return presets[name]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate ESM relative-test values from STDF CSV exports or bulk 25x loop datasets.")
    parser.add_argument("--csv", type=Path, help="Path to STDF-extracted CSV")
    parser.add_argument("--list", dest="list_path", type=Path, help="Header/list file containing test/judge arrays")
    parser.add_argument("--test-symbol", help="Name of the source test array symbol")
    parser.add_argument("--judge-symbol", help="Name of the judge array symbol")
    parser.add_argument("--title", default="VALIDATION", help="Summary title")
    parser.add_argument("--spot-check", action="append", default=[], help="Spot-check pair in testID:judgeID form")
    parser.add_argument("--preset", choices=["ur84-cold", "ur84-hot"], help="Use a known reference configuration")
    parser.add_argument("--top", type=int, default=10, help="Number of worst pairs to print")
    parser.add_argument("--report-json", action="store_true", help="Print one-line JSON summary")
    parser.add_argument("--loop-csv", type=Path, help="Path to a wide CSV containing 25x same-unit loop data for many test/judge pairs")
    parser.add_argument("--loop-xlsx", type=Path, help="Path to a wide XLSX containing 25x same-unit loop data for many test/judge pairs")
    parser.add_argument("--loop-txt", type=Path, help="Path to a tester datalog TXT containing repeated sample blocks with main-test and relative-test values")
    parser.add_argument("--sheet", help="Worksheet name for --loop-xlsx")
    parser.add_argument("--loop-id-row", type=int, default=1, help="1-based row number containing test/judge IDs in loop CSV/XLSX inputs")
    parser.add_argument("--delta-threshold", type=float, default=0.002, help="Absolute delta threshold used for CORRECT versus INCORRECT in loop validation")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    loop_mode = bool(args.loop_csv or args.loop_xlsx or args.loop_txt)

    if args.preset:
        csv_path, list_path, test_symbol, judge_symbol, title, spot_checks = preset_config(args.preset)
    else:
        if not all([args.csv, args.list_path, args.test_symbol, args.judge_symbol]):
            if not (loop_mode and all([args.list_path, args.test_symbol, args.judge_symbol])):
                raise SystemExit("Provide --preset or STDF inputs (--csv, --list, --test-symbol, --judge-symbol), or loop inputs (--loop-csv/--loop-xlsx/--loop-txt plus --list, --test-symbol, --judge-symbol).")
        csv_path = args.csv
        list_path = args.list_path
        test_symbol = args.test_symbol
        judge_symbol = args.judge_symbol
        title = args.title
        spot_checks = parse_spot_checks(args.spot_check)

    if loop_mode:
        test_ids = parse_active_ids(list_path, test_symbol)
        judge_ids = parse_active_ids(list_path, judge_symbol)
        table = load_loop_table(args.loop_csv, args.loop_xlsx, args.loop_txt, args.sheet, args.loop_id_row)
        summary, results = validate_loop_pairs(table, test_ids, judge_ids, args.delta_threshold)

        if args.report_json:
            payload = {
                "summary": summary,
                "top": [asdict(item) for item in results[: args.top]],
            }
            print(json.dumps(payload, separators=(",", ":")))
            return

        print_loop_summary(title, summary, results, args.top)
        return

    summary, results = validate_env(csv_path, list_path, test_symbol, judge_symbol)

    if args.report_json:
        payload = {
            "summary": summary,
            "top": [asdict(item) for item in results[: args.top]],
        }
        print(json.dumps(payload, separators=(",", ":")))
        return

    print_summary(title, summary, results, args.top)
    if spot_checks:
        print_first_visible_by_site(csv_path, spot_checks)


if __name__ == "__main__":
    main()