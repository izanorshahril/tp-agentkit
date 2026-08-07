from __future__ import annotations

import os

from ls_updater_audit import make_unique_path, should_write_log
from ls_updater_cli import Colors, color_text, format_path_with_colors, log_print
from ls_updater_env import env_name_to_code


def _int_lock_display(int_lock_mode, int_lock_threshold):
    if int_lock_mode == "unit_only" or not int_lock_mode:
        return "Only integer with no unit"
    if int_lock_mode == "any_unit":
        return "Any integer"
    if int_lock_mode == "threshold":
        if int_lock_threshold is not None:
            return f"Any integer above threshold (> {int_lock_threshold})"
        return "Any integer above threshold"
    if int_lock_mode == "disable":
        return "none"
    return str(int_lock_mode)


def _summary_labels(include_test_not_found: bool) -> dict[str, str]:
    labels = {
        "no change": "New Limit in CSV same as in LS",
        "unit mismatch": "Unit mismatch",
        "non-numeric LL/UL": "Non-numeric LL/UL",
        "missing LL/UL fields": "Missing LL/UL fields",
        "no LL/UL brackets": "No LL/UL brackets",
        "commented out": "Commented out",
        "no LL/UL update": "No LL/UL update",
        "csv no value": "Test in CSV has no value",
        "csv ignored": "Test ignored per IncludeInSimulation / Expression Behaviour status",
    }
    if include_test_not_found:
        labels["test not found in LS"] = "Test not found in LS"
    return labels


def _render_single_run_summary(
    args,
    result,
    format_not_updated_count,
    format_precision_override,
    int_lock_mode,
    int_lock_threshold,
):
    env_code = result.get("env_code") or env_name_to_code(result.get("env")) or ""
    log_print(color_text(env_code, Colors.OKBLUE), args)
    log_print("---", args)
    updated = result.get("updated", 0)
    not_updated = result.get("not_updated", 0)
    updated_color = Colors.OKGREEN if updated > 0 else Colors.GRAY
    log_print(f"Total Updated Tests: {color_text(str(updated), updated_color)}", args)
    log_print(
        f"Total Test Not Updated: {format_not_updated_count(not_updated)}",
        args,
    )
    summary_labels = _summary_labels(include_test_not_found=True)
    reason_counts = result.get("reason_counts") or {}
    for key in [
        "no change",
        "test not found in LS",
        "unit mismatch",
        "non-numeric LL/UL",
        "missing LL/UL fields",
        "no LL/UL brackets",
        "commented out",
        "no LL/UL update",
        "csv no value",
        "csv ignored",
    ]:
        count = reason_counts.get(key, 0)
        if count:
            log_print(
                f"- {summary_labels[key]}: {color_text(str(count), Colors.WARNING)}",
                args,
            )
    log_print("-" * 36, args)
    precision_display = format_precision_override()
    log_print(color_text(f"Precision override: {precision_display}", Colors.GRAY), args)
    int_display = _int_lock_display(int_lock_mode, int_lock_threshold)
    log_print(color_text(f"Integer lock: {int_display}", Colors.GRAY), args)
    log_print("=" * 36, args)

    csv_display = format_path_with_colors(result["csv"], Colors.OKBLUE, Colors.GRAY)
    ls_input_display = format_path_with_colors(result.get("ls_input") or result["ls"], Colors.OKBLUE, Colors.GRAY)
    ls_backup_display = format_path_with_colors(result.get("backup"), Colors.ENDC, Colors.GRAY)
    ls_output_display = format_path_with_colors(result.get("output"), Colors.OKGREEN, Colors.GRAY)
    log_display = format_path_with_colors(result.get("log"), Colors.WARNING, Colors.GRAY)
    log_print(f"CSV: {csv_display}", args)
    log_print(f"LS Input: {ls_input_display}", args)
    log_print(f"LS Backup: {ls_backup_display}", args)
    log_print(f"LS Output: {ls_output_display}", args)
    if result.get("log"):
        log_print(f"Log: {log_display}", args)


def _render_multi_run_summary(args, results, format_precision_override, int_lock_mode, int_lock_threshold):
    overall_updated = sum(result.get("updated", 0) for result in results)
    overall_reason_counts = {}
    commented_sets = []
    updated_any: set[str] = set()

    for result in results:
        reason_counts = result.get("reason_counts") or {}
        all_tids = set(result.get("all_tids") or [])
        updated_tids = set(result.get("updated_tids") or [])
        updated_any |= updated_tids
        not_updated_tids = all_tids - updated_tids
        seen_tids = set(result.get("seen_tids") or [])
        csv_missing_value_tids = set(result.get("csv_missing_value_tids") or [])
        unupdated_reasons = result.get("unupdated_reasons") or {}

        for key, count in reason_counts.items():
            if key == "test not found in LS":
                continue
            overall_reason_counts[key] = overall_reason_counts.get(key, 0) + count

        commented_here = set()
        for tid in not_updated_tids:
            reasons = set(unupdated_reasons.get(tid, set()))
            if tid in csv_missing_value_tids:
                reasons.add("csv no value")
            elif tid not in seen_tids:
                reasons.add("test not found in LS")
            if "commented out" in reasons:
                commented_here.add(tid)

        result["_commented_tids"] = commented_here
        commented_sets.append(commented_here)

    commented_any = set().union(*commented_sets) if commented_sets else set()
    commented_only = commented_any - updated_any

    unique_ls_inputs = []
    seen_ls_inputs = set()
    for result in results:
        ls_input = result.get("ls_input")
        if ls_input and ls_input not in seen_ls_inputs:
            seen_ls_inputs.add(ls_input)
            unique_ls_inputs.append(ls_input)
    show_ls_name = len(unique_ls_inputs) > 1

    log_print("=" * 36, args)
    log_print(color_text("OVERALL", Colors.OKBLUE), args)
    log_print("-------", args)
    overall_color = Colors.OKGREEN if overall_updated > 0 else Colors.GRAY
    log_print(f"Total Updated Tests: {color_text(str(overall_updated), overall_color)}", args)
    summary_labels = _summary_labels(include_test_not_found=False)
    for key in [
        "no change",
        "unit mismatch",
        "non-numeric LL/UL",
        "missing LL/UL fields",
        "no LL/UL brackets",
        "commented out",
        "no LL/UL update",
        "csv no value",
        "csv ignored",
    ]:
        if key == "commented out":
            count = len(commented_only)
        else:
            count = overall_reason_counts.get(key, 0)
        if count:
            log_print(
                f"- {summary_labels[key]}: {color_text(str(count), Colors.WARNING)}",
                args,
            )

    log_print("-" * 36, args)

    for result in results:
        env_code = result.get("env_code") or env_name_to_code(result.get("env")) or ""
        if show_ls_name:
            ls_input_name = os.path.basename(result.get("ls_input") or "")
            env_label = (
                color_text(env_code, Colors.OKBLUE)
                + color_text(" : ", Colors.OKBLUE)
                + color_text(ls_input_name, Colors.GRAY)
            )
            log_print(env_label, args)
        else:
            log_print(color_text(env_code, Colors.OKBLUE), args)
        log_print("---", args)
        updated = result.get("updated", 0)
        updated_color = Colors.OKGREEN if updated > 0 else Colors.GRAY
        log_print(f"Total Updated Tests: {color_text(str(updated), updated_color)}", args)
        reason_counts = result.get("reason_counts") or {}
        commented_here = set(result.get("_commented_tids") or [])
        commented_only_here = commented_here & commented_only
        for key in [
            "no change",
            "unit mismatch",
            "non-numeric LL/UL",
            "missing LL/UL fields",
            "no LL/UL brackets",
            "commented out",
            "no LL/UL update",
            "csv no value",
            "csv ignored",
        ]:
            if key == "commented out":
                count = len(commented_only_here)
            else:
                count = reason_counts.get(key, 0)
            if count:
                log_print(
                    f"- {summary_labels[key]}: {color_text(str(count), Colors.WARNING)}",
                    args,
                )
        log_print("-" * 36, args)

    precision_display = format_precision_override()
    log_print(color_text(f"Precision override: {precision_display}", Colors.GRAY), args)
    int_display = _int_lock_display(int_lock_mode, int_lock_threshold)
    log_print(color_text(f"Integer lock: {int_display}", Colors.GRAY), args)
    log_print(color_text("=" * 36, Colors.OKGREEN), args)

    csv_by_env = {}
    for result in results:
        env_code = result.get("env_code") or env_name_to_code(result.get("env")) or ""
        csv_path = result.get("csv")
        if env_code and csv_path:
            csv_by_env[env_code] = csv_path

    if csv_by_env:
        for env_code, csv_path in csv_by_env.items():
            csv_display = format_path_with_colors(csv_path, Colors.OKBLUE, Colors.GRAY)
            log_print(f"CSV {env_code}: {csv_display}", args)
    else:
        unique_csv = []
        seen_csv = set()
        for result in results:
            csv_path = result.get("csv")
            if csv_path and csv_path not in seen_csv:
                seen_csv.add(csv_path)
                unique_csv.append(csv_path)
        for csv_path in unique_csv:
            csv_display = format_path_with_colors(csv_path, Colors.OKBLUE, Colors.GRAY)
            log_print(f"CSV: {csv_display}", args)

    unique_ls_output = []
    seen_ls_output = set()
    unique_ls_backup = []
    seen_ls_backup = set()
    for result in results:
        out_path = result.get("output")
        if out_path and out_path not in seen_ls_output:
            seen_ls_output.add(out_path)
            unique_ls_output.append(out_path)
        bak_path = result.get("backup")
        if bak_path and bak_path not in seen_ls_backup:
            seen_ls_backup.add(bak_path)
            unique_ls_backup.append(bak_path)

    for ls_path in unique_ls_inputs:
        ls_display = format_path_with_colors(ls_path, Colors.OKBLUE, Colors.GRAY)
        log_print(f"LS Input: {ls_display}", args)
    for out_path in unique_ls_output:
        out_display = format_path_with_colors(out_path, Colors.OKGREEN, Colors.GRAY)
        log_print(f"LS Output: {out_display}", args)
    for bak_path in unique_ls_backup:
        bak_display = format_path_with_colors(bak_path, Colors.ENDC, Colors.GRAY)
        log_print(f"LS Backup: {bak_display}", args)


def render_update_summary(
    args,
    results,
    combine_completion,
    format_not_updated_count,
    format_precision_override,
    int_lock_mode,
    int_lock_threshold,
):
    if args.silent or not results:
        return

    multi_run = len(results) > 1
    log_print(color_text("=" * 36, Colors.OKGREEN), args)
    log_print(color_text("########## UPDATE SUMMARY ##########", Colors.OKGREEN), args)
    log_print(color_text("=" * 36, Colors.OKGREEN), args)
    if combine_completion:
        total_elapsed = sum(result.get("elapsed_sec", 0.0) for result in results)
        targets = [result.get("total_targets", 0) for result in results]
        if targets and all(target == targets[0] for target in targets):
            total_targets = targets[0]
        else:
            total_targets = sum(targets)
        log_print(
            color_text(
                f"Completed {total_targets} tests in {total_elapsed:.2f} sec",
                Colors.GRAY,
            ),
            args,
        )
    elif multi_run:
        for result in results:
            log_print(
                color_text(
                    f"Completed {result.get('total_targets', 0)} tests in "
                    f"{result.get('elapsed_sec', 0.0):.2f} sec",
                    Colors.GRAY,
                ),
                args,
            )
    else:
        result = results[0]
        log_print(
            color_text(
                f"Completed {result.get('total_targets', 0)} tests in "
                f"{result.get('elapsed_sec', 0.0):.2f} sec",
                Colors.GRAY,
            ),
            args,
        )

    if multi_run:
        _render_multi_run_summary(args, results, format_precision_override, int_lock_mode, int_lock_threshold)
    else:
        _render_single_run_summary(
            args,
            results[0],
            format_not_updated_count,
            format_precision_override,
            int_lock_mode,
            int_lock_threshold,
        )


def write_combined_log(args, results, timestamp):
    if len(results) <= 1 or not should_write_log(args):
        return None

    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    combined_log_path = make_unique_path(output_dir, f"ls_update_{timestamp}.log")
    with open(combined_log_path, "w", encoding="utf-8") as file_handle:
        for idx, result in enumerate(results, start=1):
            file_handle.write(f"Run {idx}\n")
            file_handle.write(result.get("log_text", ""))
            if idx < len(results):
                file_handle.write("\n")
    if not args.silent:
        log_display = format_path_with_colors(combined_log_path, Colors.WARNING, Colors.GRAY)
        log_print(f"Log: {log_display}", args)
    return combined_log_path


__all__ = ["render_update_summary", "write_combined_log"]