from __future__ import annotations

import json
import os
import re


def _json_safe(value):
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=lambda item: str(item))]
    return value


def normalize_scaled_unit(unit_value):
    if not unit_value:
        return ""
    text = unit_value.strip().lower()
    if text == "%":
        text = "pct"
    text = re.sub(r"ohms", "ohm", text)
    return text


def split_unit_prefix(unit_value):
    text = normalize_scaled_unit(unit_value)
    if not text:
        return "", ""
    if text == "pct":
        return "", text
    prefixes = ["p", "n", "u", "m", "k", "g"]
    for prefix in prefixes:
        if text.startswith(prefix) and len(text) > 1 and text[1:].isalpha():
            return prefix, text[1:]
    return "", text


def is_unit_mismatch(csv_scaled_unit, ls_scaled_unit):
    if not csv_scaled_unit or not ls_scaled_unit:
        return False
    _, csv_base = split_unit_prefix(csv_scaled_unit)
    _, ls_base = split_unit_prefix(ls_scaled_unit)
    return csv_base != ls_base


def is_scale_mismatch(csv_scaled_unit, ls_scaled_unit):
    if not csv_scaled_unit or not ls_scaled_unit:
        return False
    csv_norm = normalize_scaled_unit(csv_scaled_unit)
    ls_norm = normalize_scaled_unit(ls_scaled_unit)
    if csv_norm == ls_norm:
        return False
    _, csv_base = split_unit_prefix(csv_scaled_unit)
    _, ls_base = split_unit_prefix(ls_scaled_unit)
    return csv_base == ls_base


def record_scale_mismatch(mismatch_log, tid, csv_scaled_unit, ls_scaled_unit):
    if not csv_scaled_unit or not ls_scaled_unit:
        return
    if is_scale_mismatch(csv_scaled_unit, ls_scaled_unit):
        mismatch_log.add(f"Scale mismatch {tid}: CSV={csv_scaled_unit} LS={ls_scaled_unit}")


def record_unit_mismatch(mismatch_log, tid, csv_scaled_unit, ls_scaled_unit):
    if not csv_scaled_unit or not ls_scaled_unit:
        return
    if is_unit_mismatch(csv_scaled_unit, ls_scaled_unit):
        mismatch_log.add(f"Unit mismatch {tid}: CSV={csv_scaled_unit} LS={ls_scaled_unit}")


def make_unique_path(directory, filename):
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(directory, filename)
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{base}_{counter}{ext}")
        counter += 1
    return candidate


def should_write_log(args):
    if args.log or args.log_path:
        return True
    if args.silent or args.report_json:
        return False
    return True


def emit_report(args, payload):
    if args.report_json:
        print(json.dumps(_json_safe(payload), ensure_ascii=True, separators=(",", ":")))


__all__ = [
    "emit_report",
    "is_scale_mismatch",
    "is_unit_mismatch",
    "make_unique_path",
    "normalize_scaled_unit",
    "record_scale_mismatch",
    "record_unit_mismatch",
    "should_write_log",
    "split_unit_prefix",
]