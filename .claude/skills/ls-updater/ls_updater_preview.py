from __future__ import annotations

import sys

from ls_updater_cli import Colors, color_text, format_path_with_colors, print_c
from ls_updater_env import env_name_to_code


CSV_PREVIEW_CACHE = {}
CSV_PREVIEWED = set()
CSV_PREVIEW_FORMAT_DISPLAYED = set()
CSV_PREVIEW_FORMAT_OVERRIDES = {}


def clear_preview_state():
    CSV_PREVIEW_CACHE.clear()
    CSV_PREVIEWED.clear()
    CSV_PREVIEW_FORMAT_DISPLAYED.clear()
    CSV_PREVIEW_FORMAT_OVERRIDES.clear()


def get_cached_preview(filename):
    return CSV_PREVIEW_CACHE.get(filename)


def is_previewed(filename):
    return filename in CSV_PREVIEWED


def log_csv_detection(csv_format, mapping, args, get_column_label_map):
    label_map = get_column_label_map()
    print_c("\n--- CSV Format ---", Colors.HEADER)
    print(f"Detected: {color_text(csv_format.upper(), Colors.WARNING)}")
    print_c("\n--- Detected Columns ---", Colors.OKBLUE)
    for key, column_name in mapping.items():
        if column_name:
            print(f"{label_map.get(key, key)}: {color_text(column_name, Colors.OKGREEN)}")


def preview_csv_info(
    csv_path,
    args,
    read_csv_preview,
    resolve_csv_columns,
    get_column_label_map,
    force_prompt=False,
    display=True,
):
    headers, first_row = read_csv_preview(csv_path)
    if not headers:
        sys.exit("Error: Failed to read CSV headers.")
    csv_format, mapping = resolve_csv_columns(headers, first_row, args, force_prompt=force_prompt)
    if not force_prompt and csv_format in CSV_PREVIEW_FORMAT_OVERRIDES:
        mapping = CSV_PREVIEW_FORMAT_OVERRIDES[csv_format]
    CSV_PREVIEW_CACHE[csv_path] = (csv_format, mapping)
    CSV_PREVIEWED.add(csv_path)
    if display and not args.silent:
        if csv_format not in CSV_PREVIEW_FORMAT_DISPLAYED:
            CSV_PREVIEW_FORMAT_DISPLAYED.add(csv_format)
            log_csv_detection(csv_format, mapping, args, get_column_label_map)
    if force_prompt:
        CSV_PREVIEW_FORMAT_OVERRIDES[csv_format] = mapping
    return csv_format


def get_columns_for_format(csv_format, mapping):
    order_map = {
        "spat": ["tid", "ll", "ul", "scale", "unit", "include"],
        "spl": ["tid", "ll", "ul", "scale", "unit", "testprogram"],
        "O+": ["expr", "ll", "ul", "behavior"],
    }
    columns = []
    for key in order_map.get(csv_format, []):
        value = mapping.get(key)
        if value:
            columns.append(value)
    return columns


def get_format_mapping_for_display(csv_format):
    if csv_format in CSV_PREVIEW_FORMAT_OVERRIDES:
        return CSV_PREVIEW_FORMAT_OVERRIDES[csv_format]
    for _, (fmt, mapping) in CSV_PREVIEW_CACHE.items():
        if fmt == csv_format:
            return mapping
    return {}


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


def print_confirm_banner(
    csv_paths,
    ls_paths,
    csv_envs,
    format_precision_override,
    int_lock_mode,
    int_lock_threshold,
):
    print_c("\n--------------------------", Colors.OKBLUE)
    print_c("CHECK & CONFIRM SELECTIONS", Colors.OKBLUE)
    print_c("--------------------------", Colors.OKBLUE)

    csv_by_env = {}
    for csv_path in csv_paths:
        info = csv_envs.get(csv_path, {})
        env_code = env_name_to_code(info.get("env"))
        if env_code:
            csv_by_env[env_code] = csv_path
    if csv_by_env:
        for env_code, csv_path in csv_by_env.items():
            csv_display = format_path_with_colors(csv_path, Colors.OKBLUE, Colors.GRAY)
            print(f"{env_code} CSV: {csv_display}")
    else:
        for csv_path in csv_paths:
            csv_display = format_path_with_colors(csv_path, Colors.OKBLUE, Colors.GRAY)
            print(f"CSV: {csv_display}")

    for ls_path in ls_paths:
        ls_display = format_path_with_colors(ls_path, Colors.OKBLUE, Colors.GRAY)
        print(f"LS: {ls_display}")

    formats = []
    for csv_path in csv_paths:
        cached = CSV_PREVIEW_CACHE.get(csv_path)
        if cached:
            formats.append(cached[0])
    for csv_format in sorted(set(formats)):
        mapping = get_format_mapping_for_display(csv_format)
        columns = get_columns_for_format(csv_format, mapping)
        columns_text = ", ".join(columns) if columns else "None"
        format_display = color_text(csv_format.upper(), Colors.OKBLUE)
        columns_display = color_text(f"Columns: {columns_text}", Colors.GRAY)
        print(f"Detected CSV Format: {format_display} {columns_display}")

    detected_envs = []
    for csv_path in csv_paths:
        info = csv_envs.get(csv_path, {})
        env_code = env_name_to_code(info.get("env"))
        if env_code and info.get("source"):
            detected_envs.append(env_code)
    if detected_envs:
        env_display = color_text(", ".join(sorted(set(detected_envs))), Colors.OKBLUE)
        print(f"Detected Temperature: {env_display}")

    try:
        precision_display = format_precision_override()
    except Exception:
        precision_display = "none"
    print(f"Precision override: {color_text(precision_display, Colors.OKBLUE)}")

    int_display = _int_lock_display(int_lock_mode, int_lock_threshold)
    print(f"Integer lock: {color_text(int_display, Colors.OKBLUE)}")


__all__ = [
    "clear_preview_state",
    "get_cached_preview",
    "get_columns_for_format",
    "get_format_mapping_for_display",
    "is_previewed",
    "log_csv_detection",
    "preview_csv_info",
    "print_confirm_banner",
]