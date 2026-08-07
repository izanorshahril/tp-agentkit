#!/usr/bin/env python3
"""
T2K Limit Sheet (LS) Updater - CSV to LS limit updater tool

DESIGN PRINCIPLES:
- Portable stdlib-only Python tool: entry point plus local helper modules for cross-platform use (Windows 11, Linux)
- Suitable for both interactive (human) and non-interactive (automation) use
- Consistent, friendly CLI UX with clear prompts and safe defaults

ARCHITECTURE:
1. Parse CLI arguments (--csv, --ls, --env, --precision, --silent, etc.)
2. Detect environments from CSV and LS files
3. Interactive prompts for configuration (env, precision, int-lock, columns)
4. Execute per-job run_update() for each CSV/LS pair
5. Output summary and optional logs

CONVENTIONS:
- Global state: PRECISION_OVERRIDE, INT_LOCK_MODE, INT_LOCK_THRESHOLD
    (CSV preview/cache state now lives in ls_updater_preview.py)
- Tolerance constant: EPS = 1e-12 for floating-point comparisons
- Colorized output: ANSI codes via Colors class (future: --no-color flag support)
- Temperature codes: FC/FH/FA (FTC/FTH/FTR), QC/QH/QA (QAC/QAH/QAR), EC/EH/EA/ER (EWC/EWH/EWA/EWR)

For maintainers:
- This skill now keeps the main update flow in `ls_updater.py` and small helper layers in sibling modules
- Core logic is in run_update() which processes a single CSV/LS pair
- Prompt helpers may call sys.exit() directly (CLI-first design)
"""

import csv
import re
import shutil
import os
import datetime
import time
import sys
from typing import Dict, Optional
from decimal import Decimal, ROUND_FLOOR, ROUND_CEILING, InvalidOperation

from ls_updater_audit import (
    emit_report,
    is_scale_mismatch,
    is_unit_mismatch,
    make_unique_path,
    normalize_scaled_unit,
    record_scale_mismatch,
    record_unit_mismatch,
    should_write_log,
    split_unit_prefix,
)
from ls_updater_apply import (
    extract_env_block_tid as _applied_extract_env_block_tid,
    get_ls_scaled_unit_from_env_block as _applied_get_ls_scaled_unit_from_env_block,
    get_ls_scaled_unit_from_macro as _applied_get_ls_scaled_unit_from_macro,
    get_ls_scaled_unit_from_table as _applied_get_ls_scaled_unit_from_table,
    update_bracket_token as _applied_update_bracket_token,
    update_env_block_line as _applied_update_env_block_line,
    update_macro_line as _applied_update_macro_line,
    update_table_line as _applied_update_table_line,
)
from ls_updater_cli import (
    Colors,
    EnvInfo,
    color_text,
    debug_print,
    finish_progress,
    format_path_with_colors,
    get_env_info,
    is_quit_selection,
    log_print,
    parse_arguments,
    print_c,
    render_progress,
    should_show_progress,
    to_rel_path,
)
from ls_updater_csv import (
    build_csv_record as _csv_build_csv_record,
    extract_tid_from_expression as _csv_extract_tid_from_expression,
    normalize_expression_behavior as _csv_normalize_expression_behavior,
    normalize_include_flag as _csv_normalize_include_flag,
    parse_csv_row as _csv_parse_csv_row,
)
from ls_updater_env import (
    collect_env_options_from_ls as _env_collect_env_options_from_ls,
    detect_env_codes_in_text as _env_detect_env_codes_in_text,
    detect_env_from_csv as _env_detect_env_from_csv,
    detect_env_from_ls as _env_detect_env_from_ls,
    detect_env_names_in_text as _env_detect_env_names_in_text,
    detect_envs_from_content as _env_detect_envs_from_content,
    env_name_to_code as _env_env_name_to_code,
    map_env_code_to_names as _env_map_env_code_to_names,
    normalize_env_option as _env_normalize_env_option,
    prompt_env_choice as _env_prompt_env_choice,
    prompt_env_code_conflict as _env_prompt_env_code_conflict,
    prompt_env_from_list as _env_prompt_env_from_list,
    prompt_env_name_conflict as _env_prompt_env_name_conflict,
)
from ls_updater_paths import (
    discover_files as _paths_discover_files,
    print_selected_files as _paths_print_selected_files,
    prompt_missing_files as _paths_prompt_missing_files,
    resolve_paths as _paths_resolve_paths,
    select_file_from_list as _paths_select_file_from_list,
)
from ls_updater_prompts import (
    prompt_confirm_action as _prompts_prompt_confirm_action,
    prompt_csv_preview_action as _prompts_prompt_csv_preview_action,
    prompt_env_conflict as _prompts_prompt_env_conflict,
    prompt_env_override as _prompts_prompt_env_override,
    prompt_output_conflict as _prompts_prompt_output_conflict,
    prompt_pre_execution as _prompts_prompt_pre_execution,
    prompt_q_env_fallback as _prompts_prompt_q_env_fallback,
)
from ls_updater_preview import (
    clear_preview_state as _preview_clear_preview_state,
    get_cached_preview as _preview_get_cached_preview,
    get_columns_for_format as _preview_get_columns_for_format,
    get_format_mapping_for_display as _preview_get_format_mapping_for_display,
    is_previewed as _preview_is_previewed,
    log_csv_detection as _preview_log_csv_detection,
    preview_csv_info as _preview_preview_csv_info,
    print_confirm_banner as _preview_print_confirm_banner,
)
from ls_updater_summary import render_update_summary, write_combined_log
from ls_updater_session import prepare_run_context
from ls_updater_parse import (
    build_macro_indices as _parsed_build_macro_indices,
    clean_token as _parsed_clean_token,
    combine_scaled_unit as _parsed_combine_scaled_unit,
    detect_csv_format as _parsed_detect_csv_format,
    extract_bracket_limits as _parsed_extract_bracket_limits,
    format_decimal as _parsed_format_decimal,
    format_decimal_from_decimal as _parsed_format_decimal_from_decimal,
    format_value_from_base as _parsed_format_value_from_base,
    get_decimal_places as _parsed_get_decimal_places,
    get_effective_precision as _parsed_get_effective_precision,
    get_value_precision as _parsed_get_value_precision,
    get_visual_length as _parsed_get_visual_length,
    is_integer_like as _parsed_is_integer_like,
    is_na_token as _parsed_is_na_token,
    is_number as _parsed_is_number,
    parse_float as _parsed_parse_float,
    parse_integer_like_value as _parsed_parse_integer_like_value,
    parse_limit_table_envs as _parsed_parse_limit_table_envs,
    parse_value_to_base as _parsed_parse_value_to_base,
    read_csv_preview as _parsed_read_csv_preview,
    read_csv_dict_rows as _parsed_read_csv_dict_rows,
    replace_arg_value as _parsed_replace_arg_value,
    replace_arg_value_with_padding as _parsed_replace_arg_value_with_padding,
    scale_token_to_exp as _parsed_scale_token_to_exp,
    scale_token_to_prefix as _parsed_scale_token_to_prefix,
    set_runtime_options,
    should_int_lock as _parsed_should_int_lock,
    split_macro_args as _parsed_split_macro_args,
    split_numeric_suffix as _parsed_split_numeric_suffix,
    split_top_level_commas as _parsed_split_top_level_commas,
    values_equivalent as _parsed_values_equivalent,
    apply_precision_override as _parsed_apply_precision_override,
    apply_precision_override_to_limits as _parsed_apply_precision_override_to_limits,
    build_change_parts as _parsed_build_change_parts,
)

# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
TAB_WIDTH = 4

# Floating-point comparison tolerance for limit value equivalence checks
EPS = 1e-12

# Progress bar display threshold: only show progress for jobs with more tests than this
# Avoids visual flicker on very small update operations
PROGRESS_MIN_TESTS = 50

# Regex patterns for parsing LS macro syntax and environment blocks
REGEX_DEFINE = re.compile(r"\$define\s+(\w+)\((.*?)\)", re.IGNORECASE)
# Allow optional whitespace between the closing ')' and '}' so that lines like
# `${LimitDef_FTH (12345, ... ) }` are still detected as macro calls.
REGEX_MACRO_CALL = re.compile(r"\$\{\s*(\w+)\s*\((.*?)\)\s*\}")
REGEX_LIMIT_TABLE = re.compile(r"LimitTable\s*\[(.*?)\]")
REGEX_TABLE_TID = re.compile(r"^\s*(\d+)\s*,")
REGEX_ENV_IF = re.compile(r"\$if\s*\(\s*ENV_VALUE\s*==\s*\"([A-Za-z0-9_]+)\"\s*\)")
REGEX_ENV_ENDIF = re.compile(r"\$endif")

# Scale token to exponent mapping
# Letter codes: standard SI prefixes (p=pico, n=nano, u=micro, m=milli, k/K=kilo, M=mega, G=giga)
# Numeric codes: vendor-specific shorthand ("3"=-3, "6"=-6, "9"=-9, "12"=-12)
SCALE_TO_EXP = {
    "p": -12,
    "n": -9,
    "u": -6,
    "m": -3,
    "k": 3,
    "K": 3,
    "g": 9,
    "M": 6,
    "G": 9,
    "P": -12,
    "N": -9,
    "U": -6,
    "3": -3,  # Vendor code for milli (10^-3)
    "6": -6,  # Vendor code for micro (10^-6)
    "9": -9,  # Vendor code for nano (10^-9)
    "12": -12,  # Vendor code for pico (10^-12)
    "0": 0,
    "1": 0,
    "NONE": 0,
    "None": 0,
    "": 0,
}

SCALE_TO_PREFIX = {
    "p": "p",
    "n": "n",
    "u": "u",
    "m": "m",
    "k": "k",
    "K": "k",
    "g": "G",
    "M": "M",
    "G": "G",
    "P": "p",
    "N": "n",
    "U": "u",
    "3": "m",
    "6": "u",
    "9": "n",
    "12": "p",
    "0": "",
    "1": "",
    "NONE": "",
    "None": "",
    "": "",
}

CSV_FORMAT_SPAT = "spat"
CSV_FORMAT_SPL = "spl"
CSV_FORMAT_OPLUS = "O+"

PRECISION_OVERRIDE = None
INT_LOCK_MODE = "disable"
INT_LOCK_THRESHOLD = None

ENV_CODE_MAP = {
    "FC": ("FTC", None),
    "FH": ("FTH", None),
    "FA": ("FTR", "FTA"),
    "QC": ("QAC", "FTC"),
    "QH": ("QAH", "FTH"),
    "QA": ("QAR", "FTR"),
    "EC": ("EWC", None),
    "EH": ("EWH", None),
    "EA": ("EWA", None),
    "ER": ("EWR", None),
}
ENV_NAME_LIST = [
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
]

ENV_NAME_TO_CODE = {
    "FTC": "FC",
    "FTH": "FH",
    "FTR": "FA",
    "FTA": "FA",
    "QAC": "QC",
    "QAH": "QH",
    "QAR": "QA",
    "EWC": "EC",
    "EWH": "EH",
    "EWA": "EA",
    "EWR": "ER",
}


def sync_parse_runtime() -> None:
    set_runtime_options(PRECISION_OVERRIDE, INT_LOCK_MODE, INT_LOCK_THRESHOLD)


def get_env_choice(content, env_value, args):
    macros = {}
    for match in REGEX_DEFINE.finditer(content):
        macros[match.group(1)] = [a.strip() for a in match.group(2).split(",")]

    if args.env is None and not args.silent:
        if not env_value:
            env_value = prompt_env_choice(content)
    elif not env_value:
        env_value = "ALL"

    macro_indices_by_name = build_macro_indices(macros, env_value)
    return macro_indices_by_name, env_value, False


# Delegate pure parsing and value-format helpers to the extracted parse layer.
scale_token_to_exp = _parsed_scale_token_to_exp
scale_token_to_prefix = _parsed_scale_token_to_prefix
clean_token = _parsed_clean_token
parse_float = _parsed_parse_float
is_na_token = _parsed_is_na_token
split_numeric_suffix = _parsed_split_numeric_suffix
is_number = _parsed_is_number
format_decimal = _parsed_format_decimal
values_equivalent = _parsed_values_equivalent
parse_value_to_base = _parsed_parse_value_to_base
format_value_from_base = _parsed_format_value_from_base
get_decimal_places = _parsed_get_decimal_places
is_integer_like = _parsed_is_integer_like
get_value_precision = _parsed_get_value_precision
get_effective_precision = _parsed_get_effective_precision
format_decimal_from_decimal = _parsed_format_decimal_from_decimal
parse_integer_like_value = _parsed_parse_integer_like_value
should_int_lock = _parsed_should_int_lock
apply_precision_override = _parsed_apply_precision_override
apply_precision_override_to_limits = _parsed_apply_precision_override_to_limits
build_change_parts = _parsed_build_change_parts
split_macro_args = _parsed_split_macro_args
extract_bracket_limits = _parsed_extract_bracket_limits
replace_arg_value = _parsed_replace_arg_value
replace_arg_value_with_padding = _parsed_replace_arg_value_with_padding
get_visual_length = _parsed_get_visual_length
split_top_level_commas = _parsed_split_top_level_commas
parse_limit_table_envs = _parsed_parse_limit_table_envs
build_macro_indices = _parsed_build_macro_indices
detect_csv_format = _parsed_detect_csv_format
read_csv_preview = _parsed_read_csv_preview
read_csv_dict_rows = _parsed_read_csv_dict_rows
combine_scaled_unit = _parsed_combine_scaled_unit


def detect_envs_from_content(content):
    return _env_detect_envs_from_content(content)


def prompt_env_choice(content):
    return _env_prompt_env_choice(content)


def normalize_include_flag(value):
    return _csv_normalize_include_flag(value)


def normalize_expression_behavior(value):
    return _csv_normalize_expression_behavior(value)


def detect_env_codes_in_text(text):
    return _env_detect_env_codes_in_text(text)


def detect_env_names_in_text(text):
    return _env_detect_env_names_in_text(text)


def map_env_code_to_names(code):
    return _env_map_env_code_to_names(code)


def env_name_to_code(env_name):
    return _env_env_name_to_code(env_name)


def format_not_updated_count(count):
    if count == 0:
        return color_text(str(count), Colors.GRAY)
    return color_text(str(count), Colors.FAIL)


def prompt_env_code_conflict(label, options):
    return _env_prompt_env_code_conflict(label, options)


def prompt_env_name_conflict(label, options):
    return _env_prompt_env_name_conflict(label, options)


def prompt_env_from_list(
    label,
    options,
    highlight_label=False,
    show_label=True,
    include_all=False,
    override_label=True,
):
    return _env_prompt_env_from_list(
        label,
        options,
        highlight_label=highlight_label,
        show_label=show_label,
        include_all=include_all,
        override_label=override_label,
    )


def detect_env_from_csv(csv_path) -> EnvInfo:
    return _env_detect_env_from_csv(csv_path)


def log_csv_detection(csv_format, mapping, args):
    return _preview_log_csv_detection(csv_format, mapping, args, get_column_label_map)


def preview_csv_info(csv_path, args, force_prompt=False, display=True):
    return _preview_preview_csv_info(
        csv_path,
        args,
        read_csv_preview,
        resolve_csv_columns,
        get_column_label_map,
        force_prompt=force_prompt,
        display=display,
    )


def normalize_env_option(env_value):
    return _env_normalize_env_option(env_value)


def collect_env_options_from_ls(ls_paths):
    return _env_collect_env_options_from_ls(ls_paths)


def detect_env_from_ls(ls_path) -> EnvInfo:
    return _env_detect_env_from_ls(ls_path)


def find_header(headers, candidates, allow_contains=True):
    for cand in candidates:
        for h in headers:
            if cand.lower() == h.lower():
                return h
        if allow_contains:
            for h in headers:
                if cand.lower() in h.lower():
                    return h
    return None


def get_csv_format_prompt_options():
    return [
        {
            "format": CSV_FORMAT_SPAT,
            "label": "SPAT",
            "columns": "TestNumber/TestID, NewLSL, NewUSL, Scale, Unit, IncludeInSimulation (Optional)",
        },
        {
            "format": CSV_FORMAT_SPL,
            "label": "SPL",
            "columns": "TestNumber/TestID, Scaled_LSPL, Scaled_USPL, Scale, ScaledUnit, TestProgram (Optional)",
        },
        {
            "format": CSV_FORMAT_OPLUS,
            "label": "O+",
            "columns": "Expression, Static Low Limit, Static High Limit, Expression Behavior (Optional)",
            "remark": " # Expected No Scaling",
        },
    ]


def choose_csv_format_interactive():
    print_c("\n--- Select CSV Format ---", Colors.HEADER)
    options = get_csv_format_prompt_options()
    for idx, option in enumerate(options, start=1):
        columns_text = color_text(option["columns"], Colors.GRAY)
        line = f"{idx}. {option['label']}: {columns_text}"
        if option.get("remark"):
            line += color_text(option["remark"], Colors.GRAY)
        print(line)
    while True:
        selection = input(f"Select format (1-{len(options)}) [default=1, Q=quit]: ").strip()
        if is_quit_selection(selection):
            sys.exit("User quit.")
        selection = selection or "1"
        if not selection.isdigit():
            print_c("Invalid selection. Try again.", Colors.WARNING)
            continue
        index = int(selection)
        if index < 1 or index > len(options):
            print_c("Selection out of range. Try again.", Colors.WARNING)
            continue
        return options[index - 1]["format"]


def prompt_unknown_csv_format():
    print_c("\nNo matching CSV format detected.", Colors.WARNING)
    print_c("\n--- Select CSV Format ---", Colors.HEADER)
    options = get_csv_format_prompt_options()
    for idx, option in enumerate(options, start=1):
        columns_text = color_text(option["columns"], Colors.GRAY)
        line = f"{idx}. {option['label']}: {columns_text}"
        if option.get("remark"):
            line += color_text(option["remark"], Colors.GRAY)
        print(line)
    while True:
        selection = input("Select format [1-3, [R]etry detection, [Q]uit]: ").strip().lower()
        if selection in ["r", "retry"]:
            return "retry"
        if selection in ["q", "quit", "exit"]:
            sys.exit("User quit.")
        if not selection.isdigit():
            print_c("Invalid selection. Try again.", Colors.WARNING)
            continue
        index = int(selection)
        if index < 1 or index > len(options):
            print_c("Selection out of range. Try again.", Colors.WARNING)
            continue
        return options[index - 1]["format"]


def print_column_map_header(headers, first_row):
    print_c("\n--- CSV Column Mapping ---", Colors.HEADER)
    for idx, h in enumerate(headers):
        sample = first_row[idx] if idx < len(first_row) else ""
        sample_display = color_text(f" | Sample: {sample[:20]}", Colors.GRAY)
        print(f"{idx}. {h:<24}{sample_display}")


def prompt_column_map(headers, default_value, title, optional=False):
    label = f"{title} (optional)" if optional else title
    default_index = None
    if default_value in headers:
        default_index = headers.index(default_value)
    if default_index is not None:
        default_display = color_text(f"{default_index}. {default_value}", Colors.GRAY)
    else:
        default_display = color_text("none", Colors.GRAY)
    prompt = f"Input column# for {label} ({default_display}, [Q]uit): "
    while True:
        selection = input(prompt).strip()
        if is_quit_selection(selection):
            sys.exit("User quit.")
        if selection == "":
            if default_index is not None:
                return headers[default_index]
            if optional:
                return None
            print_c("Selection required. Try again.", Colors.WARNING)
            continue
        if not selection.isdigit():
            print_c("Invalid selection. Try again.", Colors.WARNING)
            continue
        index = int(selection)
        if index < 0 or index >= len(headers):
            print_c("Selection out of range. Try again.", Colors.WARNING)
            continue
        return headers[index]


def resolve_csv_columns(headers, first_row, args, force_prompt=False):
    label_map = get_column_label_map()
    csv_format = detect_csv_format(headers)
    if not csv_format:
        if args.silent:
            sys.exit("Error: Unknown CSV format.")
        while not csv_format:
            selection = prompt_unknown_csv_format()
            if selection == "retry":
                csv_format = detect_csv_format(headers)
            else:
                csv_format = selection

    if csv_format == CSV_FORMAT_SPAT:
        mapping = {
            "tid": find_header(headers, ["TestNumber", "Test No", "TestID", "TestName"]),
            "ll": find_header(headers, ["NewLSL", "suggestedLSL", "New LSL", "LSL", "Lower Limit"]),
            "ul": find_header(headers, ["NewUSL", "suggestedUSL", "New USL", "USL", "Upper Limit"]),
            "scale": find_header(headers, ["Scale", "ScaledUnit", "UnitMultiplier"]),
            "unit": find_header(headers, ["ParameterUnit", "Unit", "Units"]),
            "include": find_header(headers, ["IncludeInSimulation"]),
        }
    elif csv_format == CSV_FORMAT_SPL:
        unit = find_header(headers, ["ScaledUnit"], allow_contains=False)
        if not unit:
            unit = find_header(headers, ["Unit"], allow_contains=False)
        mapping = {
            "tid": find_header(headers, ["TestNumber", "Test No", "TestID", "TestName"]),
            "ll": find_header(headers, ["Scaled_LSPL", "LSPL", "Lower Limit"]),
            "ul": find_header(headers, ["Scaled_USPL", "USPL", "Upper Limit"]),
            "scale": find_header(headers, ["Scale", "UnitMultiplier"], allow_contains=False),
            "unit": unit,
            "testprogram": find_header(headers, ["TestProgram"], allow_contains=False),
        }
    else:
        mapping = {
            "expr": find_header(headers, ["Expression"]),
            "ll": find_header(headers, ["Static Low Limit"]),
            "ul": find_header(headers, ["Static High Limit"]),
            "behavior": find_header(headers, ["Expression Behavior"]),
        }

    required_keys = {
        CSV_FORMAT_SPAT: ["tid", "ll", "ul", "scale", "unit"],
        CSV_FORMAT_SPL: ["tid", "ll", "ul", "scale", "unit"],
        CSV_FORMAT_OPLUS: ["expr", "ll", "ul"],
    }[csv_format]

    optional_keys = {
        CSV_FORMAT_SPAT: ["include"],
        CSV_FORMAT_SPL: ["testprogram"],
        CSV_FORMAT_OPLUS: ["behavior"],
    }[csv_format]

    missing = [key for key in required_keys if not mapping.get(key)]
    if missing:
        if args.silent:
            sys.exit(f"Error: Missing required columns: {', '.join(missing)}")
        print_c("\nDetected columns are incomplete. Please map missing fields.", Colors.WARNING)
        print_column_map_header(headers, first_row)
        for key in missing:
            title = label_map.get(key, key)
            mapping[key] = prompt_column_map(headers, mapping.get(key), title, optional=False)

    if force_prompt and not args.silent:
        #print_c("\n--- Manual Column Mapping ---", Colors.HEADER)
        print_column_map_header(headers, first_row)
        for key in required_keys + optional_keys:
            title = label_map.get(key, key)
            mapping[key] = prompt_column_map(
                headers,
                mapping.get(key),
                title,
                optional=(key in optional_keys),
            )

    return csv_format, mapping


def get_column_label_map():
    return {
        "tid": "Test Number",
        "ll": "Lower Limit",
        "ul": "Upper Limit",
        "scale": "Scale",
        "unit": "Unit",
        "include": "Include In Simulation",
        "testprogram": "Test Program",
        "expr": "Expression",
        "behavior": "Expression Behavior",
    }


def parse_csv_data(filename, args):
    cached = _preview_get_cached_preview(filename)
    if cached:
        csv_format, mapping = cached
    else:
        headers, first_row = read_csv_preview(filename)
        if not headers:
            sys.exit("Error: Failed to read CSV headers.")
        csv_format, mapping = resolve_csv_columns(headers, first_row, args)
    if not args.silent and not _preview_is_previewed(filename):
        log_csv_detection(csv_format, mapping, args)

    data = {}
    all_tids = set()
    missing_value_tids = set()
    try:
        for row in read_csv_dict_rows(filename):
            parsed, reason, tid = parse_csv_row(row, csv_format, mapping)
            if tid:
                all_tids.add(tid)
            if reason == "csv no value" and tid:
                missing_value_tids.add(tid)
            if not parsed:
                continue
            data[tid] = parsed
        return data, csv_format, all_tids, missing_value_tids
    except OSError:
        sys.exit("Error: Failed to read CSV.")


def parse_csv_row(row, csv_format, mapping):
    return _csv_parse_csv_row(row, csv_format, mapping)


def extract_tid_from_expression(expression):
    return _csv_extract_tid_from_expression(expression)


def build_csv_record(tid, ll, ul, scale, unit, csv_format):
    return _csv_build_csv_record(tid, ll, ul, scale, unit, csv_format)


def discover_files(root_dir, extension, skip_dirs=None):
    return _paths_discover_files(root_dir, extension, skip_dirs)


def select_file_from_list(files, label, root_dir, allow_multiple=False):
    return _paths_select_file_from_list(files, label, root_dir, allow_multiple)


def print_selected_files(label, paths, root_dir):
    return _paths_print_selected_files(label, paths, root_dir)


def resolve_paths(args):
    return _paths_resolve_paths(args, preview_csv_info)


def get_columns_for_format(csv_format, mapping):
    return _preview_get_columns_for_format(csv_format, mapping)


def get_format_mapping_for_display(csv_format):
    return _preview_get_format_mapping_for_display(csv_format)


def print_confirm_banner(csv_paths, ls_paths, csv_envs):
    return _preview_print_confirm_banner(
        csv_paths,
        ls_paths,
        csv_envs,
        format_precision_override,
        INT_LOCK_MODE,
        INT_LOCK_THRESHOLD,
    )


def prompt_missing_files(csv_count, ls_count):
    return _paths_prompt_missing_files(csv_count, ls_count)


def prompt_int_lock_mode():
    global INT_LOCK_MODE
    global INT_LOCK_THRESHOLD
    print_c("\n--- Lock Integer in LS ---", Colors.HEADER)
    print(f"1. {color_text('Only integer with no unit', Colors.ENDC)}")
    print(f"2. {color_text('Any integer', Colors.ENDC)} {color_text('integer will remain integer if CSV is decimal', Colors.GRAY)}")
    print(f"3. Any integer above threshold {color_text('e.g., integer > 100 only', Colors.GRAY)}")
    print(f"4. {color_text('none', Colors.ENDC)} {color_text('default, integer will become decimal if CSV is decimal', Colors.GRAY)}")
    while True:
        range_display = color_text('1', Colors.WARNING) + '-' + color_text('4', Colors.WARNING)
        quit_display = '[' + color_text('Q', Colors.WARNING) + ']uit'
        enter_display = color_text('[Enter] for default', Colors.GRAY)
        selection = input(f"Select option ({range_display}, {quit_display}, {enter_display}): ").strip()
        if is_quit_selection(selection):
            sys.exit("User quit.")
        if selection == "":
            INT_LOCK_MODE = "disable"
            INT_LOCK_THRESHOLD = None
            return
        if not selection.isdigit():
            print_c("Invalid selection. Try again.", Colors.WARNING)
            continue
        idx = int(selection)
        if idx == 1:
            INT_LOCK_MODE = "unit_only"
            INT_LOCK_THRESHOLD = None
            return
        if idx == 2:
            INT_LOCK_MODE = "any_unit"
            INT_LOCK_THRESHOLD = None
            return
        if idx == 3:
            while True:
                thresh = input("Enter integer threshold (e.g. 100): ").strip()
                if thresh.isdigit():
                    INT_LOCK_MODE = "threshold"
                    INT_LOCK_THRESHOLD = int(thresh)
                    return
                print_c("Invalid threshold. Enter a positive integer.", Colors.WARNING)
        if idx == 4:
            INT_LOCK_MODE = "disable"
            INT_LOCK_THRESHOLD = None
            return
        print_c("Invalid selection. Try again.", Colors.WARNING)


def prompt_precision_override():
    global PRECISION_OVERRIDE
    print_c("\n--- Precision Override ---", Colors.HEADER)
    print("1. 0.1")
    print("2. 0.01")
    print("3. 0.001")
    print(f"4. dynamic {color_text('+1 decimal from LS', Colors.GRAY)}")
    print(f"5. source {color_text('follow CSV when finer than LS', Colors.GRAY)}")
    print(f"6. none {color_text('default, follow original LS decimals', Colors.GRAY)}")
    if PRECISION_OVERRIDE is None:
        default_choice = "6"
    elif PRECISION_OVERRIDE == "dynamic":
        default_choice = "4"
    elif PRECISION_OVERRIDE == "source":
        default_choice = "5"
    else:
        default_choice = str(PRECISION_OVERRIDE)
    while True:
        range_display = color_text('1', Colors.WARNING) + '-' + color_text('6', Colors.WARNING)
        quit_display = '[' + color_text('Q', Colors.WARNING) + ']'
        enter_display = color_text('[Enter] for default', Colors.GRAY)
        selection = input(f"Select option ({range_display}, {quit_display}uit, {enter_display}): ").strip()
        if is_quit_selection(selection):
            sys.exit("User quit.")
        if selection == "":
            # apply default
            if default_choice == "6":
                PRECISION_OVERRIDE = None
            elif default_choice == "4":
                PRECISION_OVERRIDE = "dynamic"
            elif default_choice == "5":
                PRECISION_OVERRIDE = "source"
            else:
                try:
                    PRECISION_OVERRIDE = int(default_choice)
                except Exception:
                    PRECISION_OVERRIDE = None
            return
        if not selection.isdigit():
            print_c("Invalid selection. Try again.", Colors.WARNING)
            continue
        idx = int(selection)
        if idx in (1, 2, 3):
            PRECISION_OVERRIDE = idx
            return
        if idx == 4:
            PRECISION_OVERRIDE = "dynamic"
            return
        if idx == 5:
            PRECISION_OVERRIDE = "source"
            return
        if idx == 6:
            PRECISION_OVERRIDE = None
            return
        print_c("Invalid selection. Try again.", Colors.WARNING)


def prompt_confirm_action():
    return _prompts_prompt_confirm_action()


# Delegate line-application helpers to the extracted apply layer.
update_bracket_token = _applied_update_bracket_token
extract_env_block_tid = _applied_extract_env_block_tid
get_ls_scaled_unit_from_env_block = _applied_get_ls_scaled_unit_from_env_block
update_table_line = _applied_update_table_line
get_ls_scaled_unit_from_macro = _applied_get_ls_scaled_unit_from_macro
get_ls_scaled_unit_from_table = _applied_get_ls_scaled_unit_from_table
update_env_block_line = _applied_update_env_block_line
update_macro_line = _applied_update_macro_line


def prompt_output_conflict(path):
    return _prompts_prompt_output_conflict(path)


def prompt_env_conflict(csv_env, ls_env, csv_path, ls_path, env_options=None):
    return _prompts_prompt_env_conflict(csv_env, ls_env, csv_path, ls_path, env_options)


def prompt_env_override(csv_path):
    return _prompts_prompt_env_override(csv_path)


def prompt_q_env_fallback(csv_env, fallback_env):
    return _prompts_prompt_q_env_fallback(csv_env, fallback_env)


def prompt_pre_execution():
    return _prompts_prompt_pre_execution()


def prompt_csv_preview_action(csv_path):
    return _prompts_prompt_csv_preview_action(csv_path)


def build_log_text(
    csv_path,
    ls_input_path,
    old_backup,
    new_output,
    csv_format,
    env_filter,
    total_updated_tests,
    total_not_updated_tests,
    reason_counts,
    all_tids,
    updated_tids,
    unit_mismatch_details,
    scale_mismatch_details,
    unupdated_reasons,
    csv_missing_value_tids,
    seen_tids,
    updated_changes,
):
    lines = []
    csv_rel = to_rel_path(csv_path)
    ls_input_rel = to_rel_path(ls_input_path)
    backup_rel = to_rel_path(old_backup)
    output_rel = to_rel_path(new_output)
    lines.append(f"T2K Limit Updater Log - {TIMESTAMP}")
    lines.append(f"CSV: {csv_rel}")
    lines.append(f"LS Input: {ls_input_rel}")
    lines.append(f"LS Backup: {backup_rel}")
    lines.append(f"LS Output: {output_rel}")
    lines.append(f"CSV Format: {csv_format}")
    # include precision override and integer-lock settings in the log
    try:
        precision_display = format_precision_override()
    except Exception:
        precision_display = "none"
    lines.append(f"Precision override: {precision_display}")
    int_mode = INT_LOCK_MODE if 'INT_LOCK_MODE' in globals() else None
    int_thresh = INT_LOCK_THRESHOLD if 'INT_LOCK_THRESHOLD' in globals() else None
    if int_mode == "unit_only" or not int_mode:
        int_display = "Only integer with no unit"
    elif int_mode == "any_unit":
        int_display = "Any integer"
    elif int_mode == "threshold":
        int_display = f"Any integer above threshold (> {int_thresh})" if int_thresh is not None else "Any integer above threshold"
    elif int_mode == "disable":
        int_display = "none"
    else:
        int_display = str(int_mode)
    lines.append(f"Integer lock: {int_display}")
    lines.append(f"Temperature: {env_name_to_code(env_filter)}")
    lines.append(f"Total Updated Tests: {total_updated_tests}")
    lines.append(f"Total Test Not Updated: {total_not_updated_tests}")
    rename_reason = {
        "no change": "New Limit in CSV same as in LS",
        "test not found in LS": "Test not found in LS",
        "unit mismatch": "Unit mismatch",
        "non-numeric LL/UL": "Non-numeric LL/UL",
        "missing LL/UL fields": "Missing LL/UL fields",
        "no LL/UL brackets": "No LL/UL brackets",
        "commented out": "Commented out",
        "no LL/UL update": "No LL/UL update",
        "csv no value": "Test in CSV has no value",
        "csv ignored": "Test ignored per IncludeInSimulation / Expression Behaviour status",
    }
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
            lines.append(f"- {rename_reason[key]}: {count}")
    lines.append("")
    lines.append("CSV Audit")
    lines.append("-" * 40)
    for tid in sorted(all_tids, key=lambda x: int(x) if x.isdigit() else x):
        parts = []
        is_updated = tid in updated_tids
        if is_updated:
            parts.append("updated")
            change_detail = updated_changes.get(tid)
            if change_detail:
                parts.append(change_detail)
        else:
            parts.append("not updated")
        if tid in unit_mismatch_details:
            parts.append(f"unit mismatch ({unit_mismatch_details[tid]})")
        if tid in scale_mismatch_details and tid in updated_tids:
            parts.append(f"scale mismatch ({scale_mismatch_details[tid]})")
        reasons = set(unupdated_reasons.get(tid, set()))
        if tid in csv_missing_value_tids:
            reasons.add("csv no value")
        elif tid not in seen_tids:
            reasons.add("test not found in LS")
        if not reasons and not is_updated:
            reasons.add("no change")
        reason_labels = {
            "no change": "new limit in CSV same as in LS",
            "test not found in LS": "test not found in LS",
            "unit mismatch": "unit mismatch",
            "non-numeric LL/UL": "non-numeric LL/UL",
            "missing LL/UL fields": "missing LL/UL fields",
            "no LL/UL brackets": "no LL/UL brackets",
            "commented out": "commented out",
            "no LL/UL update": "no LL/UL update",
            "csv no value": "test in CSV has no value",
            "csv ignored": "test ignored per IncludeInSimulation / Expression Behaviour status",
        }
        # If this test was successfully updated in an active LS macro/table,
        # ignore any "commented out" or similar passive reasons that only
        # reflect other copies of the test being commented in the LS.
        for reason in sorted(reasons):
            if is_updated and reason in ["no change", "commented out"]:
                continue
            parts.append(reason_labels.get(reason, reason))
        lines.append(f"{tid}: {'; '.join(parts)}")
    return "\n".join(lines) + "\n"


def run_update(
    csv_path,
    ls_path,
    args,
    env_override=None,
    reuse_output=False,
    emit_log=True,
    emit_summary=True,
    emit_progress_summary=True,
    ls_input_path=None,
    backup_path=None,
):
    """
    Core processing function: updates one LS file using limits from one CSV file.
    
    Parses CSV data, processes LS content line-by-line to find and update limit values,
    applies precision/int-lock overrides, and generates output/backup/log files.
    
    Args:
        csv_path: Path to input CSV with new limit values
        ls_path: Path to LS file to update (may be a working copy from prior job)
        args: CLI arguments object
        env_override: Temperature environment to filter (overrides args.env)
        reuse_output: True if ls_path is already a working copy from previous job
        emit_log: Write log file if True
        emit_summary: Print summary to console if True
        emit_progress_summary: Show progress stats during processing if True
        ls_input_path: Original LS path (for display/logging when ls_path is working copy)
        backup_path: Pre-existing backup path (for multi-job runs)
    
    Returns:
        Dict with status, paths, counts, reason details, and elapsed time
    """
    sync_parse_runtime()
    if env_override:
        env_filter = env_override.upper()
    else:
        env_filter = args.env.upper() if args.env else None
    limits, csv_format, csv_all_tids, csv_missing_value_tids = parse_csv_data(csv_path, args)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output")
    if not args.in_place:
        os.makedirs(output_dir, exist_ok=True)

    if not args.silent and emit_summary:
        csv_display = format_path_with_colors(csv_path, Colors.OKBLUE, Colors.GRAY)
        ls_display = format_path_with_colors(ls_input_path or ls_path, Colors.OKBLUE, Colors.GRAY)
        log_print(f"CSV: {csv_display}", args)
        log_print(f"LS Input: {ls_display}", args)
    debug_print(f"CSV format detected: {csv_format}", args)

    with open(ls_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    macro_indices_by_name, env_name, _ = get_env_choice("".join(lines), env_filter, args)
    env_filter = env_name
    if not args.silent and emit_summary:
        env_display = color_text(env_name_to_code(env_filter), Colors.WARNING)
        log_print(f"Temperature: {env_display}", args)
    current_table_envs = None
    active_env_guard = None
    audit_entries = []
    scale_mismatch_details = {}
    unit_mismatch_details = {}
    update_count = 0
    seen_tids = set()
    updated_tids = set()
    unupdated_reasons = {}
    updated_changes = {}

    all_tids_set = set(csv_all_tids)
    total_targets = len(all_tids_set)
    show_progress = should_show_progress(args, total_targets) and total_targets > 0
    processed_tids = set(csv_missing_value_tids) & all_tids_set
    progress_count = len(processed_tids)
    update_every = max(1, total_targets // 200)
    start_time = None

    def mark_progress(tid):
        nonlocal progress_count
        if not show_progress or tid in processed_tids or tid not in all_tids_set:
            return
        processed_tids.add(tid)
        progress_count += 1
        if progress_count % update_every == 0 or progress_count == total_targets:
            render_progress(progress_count, total_targets, "", Colors.OKGREEN)

    if show_progress:
        start_time = time.perf_counter()
        render_progress(progress_count, total_targets, "", Colors.OKGREEN)

    for tid in csv_missing_value_tids:
        unupdated_reasons.setdefault(tid, set()).add("csv no value")

    new_lines = []
    for line in lines:
        if line.lstrip().startswith("#"):
            stripped = line.lstrip("#").lstrip()
            macro_match = REGEX_MACRO_CALL.search(stripped)
            if macro_match:
                raw_args = split_macro_args(macro_match.group(2))
                args_list = [x.strip() for x in raw_args]
                if args_list:
                    tid = args_list[0].replace("\"", "").strip()
                    if tid in limits:
                        mark_progress(tid)
                        seen_tids.add(tid)
                        unupdated_reasons.setdefault(tid, set()).add("commented out")
            else:
                tid = extract_env_block_tid(stripped)
                if not tid:
                    tid_match = REGEX_TABLE_TID.match(stripped)
                    if tid_match:
                        tid = tid_match.group(1)
                if tid:
                    if tid in limits:
                        mark_progress(tid)
                        seen_tids.add(tid)
                        unupdated_reasons.setdefault(tid, set()).add("commented out")
            new_lines.append(line)
            continue

        env_if_match = REGEX_ENV_IF.search(line)
        if env_if_match:
            active_env_guard = env_if_match.group(1).upper()
        elif REGEX_ENV_ENDIF.search(line):
            active_env_guard = None

        # NOTE: Toggle this guard if you want to ignore conditional ENV blocks.
        if active_env_guard and env_filter and env_filter != "ALL" and active_env_guard != env_filter:
            new_lines.append(line)
            continue

        table_envs = parse_limit_table_envs(line)
        if table_envs is not None:
            current_table_envs = table_envs

        modified = False
        updated_line = line

        macro_match = REGEX_MACRO_CALL.search(line)
        comment_fragments = []
        if macro_match:
            tid = None
            raw_args = split_macro_args(macro_match.group(2))
            args_list = [x.strip() for x in raw_args]
            if args_list:
                tid = args_list[0].replace("\"", "").strip()
                if tid in limits:
                    mark_progress(tid)
                    seen_tids.add(tid)
                    ls_scaled_unit = get_ls_scaled_unit_from_macro(args_list)
                    csv_scaled_unit = limits[tid]["scaled_unit"]
                    if is_unit_mismatch(csv_scaled_unit, ls_scaled_unit):
                        unit_mismatch_details[tid] = f"CSV={csv_scaled_unit} LS={ls_scaled_unit}"
                        unupdated_reasons.setdefault(tid, set()).add("unit mismatch")
                        new_lines.append(line)
                        continue
                    if is_scale_mismatch(csv_scaled_unit, ls_scaled_unit):
                        scale_mismatch_details[tid] = f"CSV={csv_scaled_unit} LS={ls_scaled_unit}"
            updated_line, modified, comment_fragments, reason = update_macro_line(
                line,
                limits,
                env_name,
                macro_indices_by_name,
                audit_entries,
            )
            if tid and tid in limits:
                if modified:
                    updated_tids.add(tid)
                    if comment_fragments:
                        updated_changes[tid] = "; ".join(comment_fragments)
                elif reason:
                    if reason == "env mismatch" and env_filter != "ALL":
                        pass
                    else:
                        unupdated_reasons.setdefault(tid, set()).add(reason)
        else:
            tid = extract_env_block_tid(line)
            if tid:
                if tid in limits:
                    mark_progress(tid)
                    seen_tids.add(tid)
                    ls_scaled_unit = get_ls_scaled_unit_from_env_block(line, env_filter)
                    csv_scaled_unit = limits[tid]["scaled_unit"]
                    if is_unit_mismatch(csv_scaled_unit, ls_scaled_unit):
                        unit_mismatch_details[tid] = f"CSV={csv_scaled_unit} LS={ls_scaled_unit}"
                        unupdated_reasons.setdefault(tid, set()).add("unit mismatch")
                        new_lines.append(line)
                        continue
                    if is_scale_mismatch(csv_scaled_unit, ls_scaled_unit):
                        scale_mismatch_details[tid] = f"CSV={csv_scaled_unit} LS={ls_scaled_unit}"
                updated_line, modified, comment_fragments, reason = update_env_block_line(
                    line,
                    limits,
                    env_filter,
                    audit_entries,
                )
                if tid in limits:
                    if modified:
                        updated_tids.add(tid)
                        if comment_fragments:
                            updated_changes[tid] = "; ".join(comment_fragments)
                    elif reason:
                        if reason == "env mismatch" and env_filter != "ALL":
                            pass
                        else:
                            unupdated_reasons.setdefault(tid, set()).add(reason)
            else:
                parts = split_top_level_commas(line)
                tid_match = REGEX_TABLE_TID.match(line)
                if tid_match:
                    tid = tid_match.group(1)
                    if tid in limits:
                        mark_progress(tid)
                        seen_tids.add(tid)
                        ls_scaled_unit = get_ls_scaled_unit_from_table(parts)
                        csv_scaled_unit = limits[tid]["scaled_unit"]
                        if is_unit_mismatch(csv_scaled_unit, ls_scaled_unit):
                            unit_mismatch_details[tid] = f"CSV={csv_scaled_unit} LS={ls_scaled_unit}"
                            unupdated_reasons.setdefault(tid, set()).add("unit mismatch")
                            new_lines.append(line)
                            continue
                        if is_scale_mismatch(csv_scaled_unit, ls_scaled_unit):
                            scale_mismatch_details[tid] = f"CSV={csv_scaled_unit} LS={ls_scaled_unit}"
                updated_line, modified, comment_fragments, reason = update_table_line(
                    line,
                    limits,
                    env_filter,
                    current_table_envs,
                    audit_entries,
                )
                if tid_match:
                    tid = tid_match.group(1)
                    if tid in limits:
                        if modified:
                            updated_tids.add(tid)
                            if comment_fragments:
                                updated_changes[tid] = "; ".join(comment_fragments)
                        elif reason:
                            if reason == "env mismatch" and env_filter != "ALL":
                                pass
                            else:
                                unupdated_reasons.setdefault(tid, set()).add(reason)

        if modified:
            update_count += 1
            updated_line = updated_line.rstrip("\n")
            if comment_fragments:
                comment_text = "; ".join(comment_fragments)
                if "#" in updated_line:
                    head, existing = updated_line.split("#", 1)
                    existing = existing.strip()
                    suffix = f"{existing}; {comment_text}" if existing else comment_text
                    updated_line = f"{head.rstrip()} # {suffix}"
                else:
                    updated_line += " # " + comment_text
            updated_line += "\n"
        new_lines.append(updated_line)

    progress_end_time = time.perf_counter() if show_progress else None

    old_name = os.path.basename(ls_path)
    if args.in_place:
        output_dir = os.path.dirname(ls_path)
    if reuse_output and backup_path:
        old_backup = backup_path
    else:
        old_backup = make_unique_path(output_dir, f"{old_name}.{TIMESTAMP}-old.bak")
    new_output = os.path.join(output_dir, old_name)
    temp_output: Optional[str] = None
    if args.in_place:
        temp_output = make_unique_path(output_dir, f"{old_name}.{TIMESTAMP}.tmp")
    elif os.path.exists(new_output):
        if reuse_output:
            pass
        elif args.silent:
            sys.exit(f"Error: Output file already exists: {new_output}")
        else:
            while os.path.exists(new_output):
                choice = prompt_output_conflict(new_output)
                if choice == "overwrite":
                    break
                if choice == "restart":
                    sys.exit("User requested restart.")
                if choice == "quit":
                    sys.exit("User quit.")
                # retry: loop to re-check after user action

    elapsed_sec = finish_progress(
        show_progress,
        total_targets,
        "",
        start_time,
        progress_end_time,
        emit=emit_progress_summary,
    )

    log_path = None
    if emit_log and should_write_log(args):
        if args.log_path:
            log_path = os.path.abspath(args.log_path)
        else:
            log_dir = output_dir if args.in_place else output_dir
            log_path = make_unique_path(log_dir, f"ls_update_{TIMESTAMP}.log")

    if not (reuse_output and backup_path):
        shutil.copy2(ls_path, old_backup)
    if args.in_place:
        assert temp_output is not None
        with open(temp_output, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        shutil.move(temp_output, ls_path)
        new_output = ls_path
    else:
        with open(new_output, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    all_tids = set(csv_all_tids)
    not_updated = all_tids - updated_tids
    total_updated_tests = len(updated_tids)
    total_not_updated_tests = len(not_updated)
    reason_counts = {}
    for tid in not_updated:
        reasons = set(unupdated_reasons.get(tid, set()))
        if tid in csv_missing_value_tids:
            reasons.add("csv no value")
        elif tid not in seen_tids:
            reasons.add("test not found in LS")
        if not reasons:
            reasons.add("no change")
        for reason in reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    log_text = build_log_text(
        csv_path,
        ls_input_path or ls_path,
        old_backup,
        new_output,
        csv_format,
        env_filter,
        total_updated_tests,
        total_not_updated_tests,
        reason_counts,
        all_tids,
        updated_tids,
        unit_mismatch_details,
        scale_mismatch_details,
        unupdated_reasons,
        csv_missing_value_tids,
        seen_tids,
        updated_changes,
    )
    if log_path:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(log_text)

    if not args.silent and emit_summary:
        updated_count = len(updated_tids)
        count_color = Colors.OKGREEN if updated_count > 0 else Colors.GRAY
        count_display = color_text(str(updated_count), count_color)
        log_print(f"Total Updated Tests: {count_display}", args)
        total_not_updated = total_not_updated_tests
        if total_not_updated is not None:
            log_print(
                f"Total Test Not Updated: {format_not_updated_count(total_not_updated)}",
                args,
            )
        reason_labels = {
            "no change": "New Limit in CSV same as in LS",
            "test not found in LS": "Test not found in LS",
            "unit mismatch": "Unit mismatch",
            "non-numeric LL/UL": "Non-numeric LL/UL",
            "missing LL/UL fields": "Missing LL/UL fields",
            "no LL/UL brackets": "No LL/UL brackets",
            "commented out": "Commented out",
            "no LL/UL update": "No LL/UL update",
            "csv no value": "Test in CSV has no value",
            "csv ignored": "Test ignored per IncludeInSimulation / Expression Behaviour status",
        }
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
                    f"- {reason_labels[key]}: {color_text(str(count), Colors.WARNING)}",
                    args,
                )
        backup_display = format_path_with_colors(old_backup, Colors.ENDC, Colors.GRAY)
        output_display = format_path_with_colors(new_output, Colors.WARNING, Colors.GRAY)
        log_print(f"LS Backup: {backup_display}", args)
        output_display = format_path_with_colors(new_output, Colors.OKGREEN, Colors.GRAY)
        log_print(f"LS Output: {output_display}", args)
        if log_path:
            log_display = format_path_with_colors(log_path, Colors.WARNING, Colors.GRAY)
            log_print(f"Log: {log_display}", args)

    return {
        "status": "ok",
        "csv": csv_path,
        "ls": ls_path,
        "ls_input": ls_input_path or ls_path,
        "output": new_output,
        "backup": old_backup,
        "log": log_path,
        "updated": total_updated_tests,
        "not_updated": total_not_updated_tests,
        "env": env_filter,
        "env_code": env_name_to_code(env_filter),
        "csv_format": csv_format,
        "reason_counts": reason_counts,
        "all_tids": all_tids,
        "updated_tids": updated_tids,
        "unit_mismatch_details": unit_mismatch_details,
        "scale_mismatch_details": scale_mismatch_details,
        "unupdated_reasons": unupdated_reasons,
        "csv_missing_value_tids": csv_missing_value_tids,
        "seen_tids": seen_tids,
        "log_text": log_text,
        "elapsed_sec": elapsed_sec,
        "total_targets": total_targets,
    }


def format_precision_override():
    precision = PRECISION_OVERRIDE
    if precision is None:
        return "none"
    if precision == "dynamic":
        return "dynamic"
    if precision == "source":
        return "source"
    return "0." + "0" * (precision - 1) + "1"


def main(args):
    """
    Main entry point for the LS updater CLI.
    
    Flow:
    1. Resolve input CSV and LS file paths (interactive or from args)
    2. Detect environments from filenames and content
    3. Prompt for configuration (precision, int-lock mode, column mapping)
    4. Execute run_update() for each CSV/LS job pair
    5. Display summary and write logs if requested
    
    Args:
        args: Parsed command-line arguments from argparse
    """
    global PRECISION_OVERRIDE
    if args.precision is not None:
        PRECISION_OVERRIDE = args.precision
    sync_parse_runtime()
    if not args.silent:
        print_c("######################################", Colors.OKBLUE)
        print_c("###| T2K Limit Sheet (LS) Updater |###", Colors.OKBLUE)
        print_c("###|   a CSV to LS update tool    |###", Colors.OKBLUE)
        print_c("######################################", Colors.OKBLUE)

    context = prepare_run_context(
        args,
        resolve_paths,
        detect_env_from_csv,
        detect_env_from_ls,
        collect_env_options_from_ls,
        normalize_env_option,
        get_env_info,
        prompt_env_from_list,
        prompt_env_conflict,
        prompt_confirm_action,
        prompt_precision_override,
        prompt_int_lock_mode,
        print_confirm_banner,
        preview_csv_info,
        sync_parse_runtime,
        _preview_clear_preview_state,
    )
    csv_paths = context["csv_paths"]
    ls_paths = context["ls_paths"]
    csv_envs = context["csv_envs"]
    ls_envs = context["ls_envs"]
    env_options = context["env_options"]
    decision_cache = context["decision_cache"]
    any_q_ls = context["any_q_ls"]
    jobs = context["jobs"]

    results = []
    q_fallback_cache = {}
    working_ls_map = {}
    backup_map = {}
    multi_run = len(jobs) > 1
    multi_ls = len(ls_paths) > 1
    multi_csv = len(csv_paths) > 1
    combine_completion = multi_ls and not multi_csv
    for csv_path, ls_path in jobs:
        working_ls = working_ls_map.get(ls_path, ls_path)
        reuse_output = ls_path in working_ls_map
        backup_path = backup_map.get(ls_path)
        csv_info = csv_envs.get(csv_path, {})
        ls_info = ls_envs.get(ls_path, {})
        csv_env = csv_info.get("env")
        csv_fallback = csv_info.get("fallback")
        ls_env = ls_info.get("env")

        if args.silent and not args.env:
            if not csv_env:
                sys.exit(
                    f"Error: Unable to detect CSV temperature for {os.path.basename(csv_path)}. "
                    "Provide --env to override."
                )
            if csv_env and ls_env and csv_env != ls_env:
                sys.exit(
                    f"Error: Temperature mismatch CSV={csv_env} LS={ls_env}. "
                    "Provide --env to override."
                )
            if csv_env and csv_env.startswith("Q") and not any_q_ls:
                sys.exit(
                    f"Error: Q temperature {csv_env} not found in LS files. "
                    "Provide --env to override."
                )

        env_override = None

        # Determine env_override for this job: prioritize CLI --env, then handle Q-temp special case,
        # then resolve CSV/LS conflicts using cached decisions or prompts
        if args.env:
            env_override = args.env
        elif csv_env and csv_env.startswith("Q"):
            # Q-temperature special case: requires exact LS match or fallback to FT equivalent
            if any_q_ls:
                if ls_env != csv_env:
                    if not args.silent:
                        log_print(
                            f"Skipping {os.path.basename(csv_path)} for {os.path.basename(ls_path)} "
                            f"(Q temperature {csv_env} does not match LS temperature {ls_env}).",
                            args,
                        )
                    continue
                env_override = csv_env
            else:
                ok = q_fallback_cache.get(csv_env)
                if ok is None:
                    ok = prompt_q_env_fallback(csv_env, csv_fallback)
                    q_fallback_cache[csv_env] = ok
                if not ok:
                    sys.exit("User quit.")
                env_override = csv_fallback
        else:
            if csv_env and ls_env and csv_env != ls_env:
                cache_key = (csv_env, ls_env)
                choice = decision_cache.get(cache_key)
                if not choice:
                    choice_result = prompt_env_conflict(csv_env, ls_env, csv_path, ls_path, env_options)
                    if choice_result == "override":
                        # User wants to select a different environment
                        override_env = prompt_env_from_list(
                            "Override temperature",
                            env_options,
                            show_label=True,
                            include_all=False,
                            override_label=False,
                        )
                        choice = ("override", override_env)
                    else:
                        choice = choice_result
                    decision_cache[cache_key] = choice
                # Handle choice which can be "csv", "ls", or ("override", env_name)
                if isinstance(choice, tuple) and choice[0] == "override":
                    env_override = choice[1]
                elif choice == "csv":
                    env_override = csv_env
                else:
                    env_override = ls_env
            else:
                env_override = csv_env or ls_env

        result = run_update(
            csv_path,
            working_ls,
            args,
            env_override=env_override,
            reuse_output=reuse_output,
            emit_log=not multi_run,
            emit_summary=False,
            emit_progress_summary=False,
            ls_input_path=ls_path,
            backup_path=backup_path,
        )
        working_ls_map[ls_path] = result.get("output", working_ls)
        if not backup_path:
            backup_map[ls_path] = result.get("backup")
        results.append(result)

    render_update_summary(
        args,
        results,
        combine_completion,
        format_not_updated_count,
        format_precision_override,
        INT_LOCK_MODE,
        INT_LOCK_THRESHOLD,
    )

    combined_log_path = write_combined_log(args, results, TIMESTAMP)

    if len(results) == 1:
        return results[0]
    return {
        "status": "ok",
        "runs": results,
        "log": combined_log_path,
    }


if __name__ == "__main__":
    try:
        args = parse_arguments()
    except SystemExit:
        raise
    try:
        result = main(args)
        emit_report(args, result)
    except SystemExit as exc:
        message = exc.code if isinstance(exc.code, str) else "Exited"
        emit_report(args, {"status": "error", "message": message})
        if isinstance(exc.code, int):
            sys.exit(exc.code)
        sys.exit(1)
    except Exception as exc:
        emit_report(args, {"status": "error", "message": str(exc)})
        sys.stderr.write(f"Error: {exc}\n")
        sys.exit(1)
