from __future__ import annotations

import re

from ls_updater_parse import clean_token, parse_float, scale_token_to_exp
from ls_updater_audit import split_unit_prefix


def normalize_include_flag(value):
    if value is None:
        return True
    text = str(value).strip().lower()
    if text in ["false", "0", "no", "n", "disable", "disabled"]:
        return False
    return True


def normalize_expression_behavior(value):
    if value is None:
        return False
    text = str(value).strip().lower()
    return text == "include"


def extract_tid_from_expression(expression):
    match = re.search(r"P_(\d+)\s*:", expression)
    if match:
        return match.group(1)
    return ""


def build_csv_record(tid, ll, ul, scale, unit, csv_format):
    if not tid or not ll or not ul:
        return None
    base_ll = parse_float(ll)
    base_ul = parse_float(ul)
    if base_ll is None or base_ul is None:
        return None
    exp = scale_token_to_exp(scale)
    if exp == 0:
        unit_prefix, _ = split_unit_prefix(unit)
        inferred_exp = scale_token_to_exp(unit_prefix)
        if inferred_exp != 0:
            exp = inferred_exp
    base_ll = base_ll * (10 ** exp)
    base_ul = base_ul * (10 ** exp)
    scaled_unit = clean_token(unit)
    return {
        "tid": tid,
        "ll": ll,
        "ul": ul,
        "base_ll": base_ll,
        "base_ul": base_ul,
        "scale": scale,
        "unit": unit,
        "scaled_unit": scaled_unit,
        "format": csv_format,
    }


def parse_csv_row(row, csv_format, mapping):
    if csv_format == "spat":
        tid = str(row.get(mapping["tid"], "")).strip()
        ll = str(row.get(mapping["ll"], "")).strip()
        ul = str(row.get(mapping["ul"], "")).strip()
        scale = str(row.get(mapping["scale"], "")).strip()
        unit = str(row.get(mapping["unit"], "")).strip()
        include_val = row.get(mapping.get("include"))
        if not normalize_include_flag(include_val):
            return None, "csv ignored", tid
        if not ll or not ul:
            return None, "csv no value", tid
        return build_csv_record(tid, ll, ul, scale, unit, csv_format), None, tid

    if csv_format == "spl":
        tid = str(row.get(mapping["tid"], "")).strip()
        ll = str(row.get(mapping["ll"], "")).strip()
        ul = str(row.get(mapping["ul"], "")).strip()
        scale = str(row.get(mapping["scale"], "")).strip()
        unit = str(row.get(mapping["unit"], "")).strip()
        if not ll or not ul:
            return None, "csv no value", tid
        return build_csv_record(tid, ll, ul, scale, unit, csv_format), None, tid

    if csv_format == "O+":
        expr = str(row.get(mapping["expr"], "")).strip()
        tid = extract_tid_from_expression(expr)
        ll = str(row.get(mapping["ll"], "")).strip()
        ul = str(row.get(mapping["ul"], "")).strip()
        behavior = row.get(mapping.get("behavior"))
        if not normalize_expression_behavior(behavior):
            return None, "csv ignored", tid
        if not ll or not ul:
            return None, "csv no value", tid
        return build_csv_record(tid, ll, ul, "", "", csv_format), None, tid

    return None, "csv unknown", ""


__all__ = [
    "build_csv_record",
    "extract_tid_from_expression",
    "normalize_expression_behavior",
    "normalize_include_flag",
    "parse_csv_row",
]