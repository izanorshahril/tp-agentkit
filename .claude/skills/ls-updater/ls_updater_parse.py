from __future__ import annotations

import re
import sys
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, InvalidOperation
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))

from _io_support import read_csv_preview as _io_read_csv_preview, read_csv_dict_rows as _io_read_csv_dict_rows


TAB_WIDTH = 4
EPS = 1e-12

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
    "3": -3,
    "6": -6,
    "9": -9,
    "12": -12,
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


def set_runtime_options(precision_override, int_lock_mode, int_lock_threshold) -> None:
    global PRECISION_OVERRIDE, INT_LOCK_MODE, INT_LOCK_THRESHOLD
    PRECISION_OVERRIDE = precision_override
    INT_LOCK_MODE = int_lock_mode
    INT_LOCK_THRESHOLD = int_lock_threshold


def scale_token_to_exp(token):
    if token is None:
        return 0
    key = token.strip().strip("\"").strip("'")
    return SCALE_TO_EXP.get(key, 0)


def scale_token_to_prefix(token):
    if token is None:
        return ""
    key = token.strip().strip("\"").strip("'")
    return SCALE_TO_PREFIX.get(key, "")


def clean_token(token):
    if token is None:
        return ""
    return token.strip().strip("\"").strip("'")


def parse_float(value):
    try:
        return float(value)
    except Exception:
        return None


def is_na_token(value_str):
    if value_str is None:
        return False
    text = str(value_str).strip().lower()
    return text in ["na", "nobin", "nan", "inf", "-inf"]


def split_numeric_suffix(value_str):
    if value_str is None:
        return None, ""
    text = str(value_str).strip()
    match = re.match(r"^([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)", text)
    if not match:
        return None, ""
    num_str = match.group(1)
    suffix = text[match.end():]
    return num_str, suffix


def is_number(value):
    num_str, _ = split_numeric_suffix(value)
    return parse_float(num_str) is not None


def format_decimal(value):
    if value is None:
        return ""
    text = f"{value:.12g}"
    if "e" in text or "E" in text:
        text = f"{value:.12f}".rstrip("0").rstrip(".")
    if text == "-0":
        text = "0"
    return text


def values_equivalent(old_value_str, new_value_str, scale_token):
    if old_value_str == new_value_str:
        return True
    if old_value_str is None or new_value_str is None:
        return False
    if is_na_token(old_value_str) or is_na_token(new_value_str):
        return False
    old_base = parse_value_to_base(old_value_str, scale_token)
    new_base = parse_value_to_base(new_value_str, scale_token)
    if old_base is None or new_base is None:
        return False
    return abs(old_base - new_base) <= EPS


def parse_value_to_base(value_str, ls_scale_token):
    if value_str is None:
        return None
    if is_na_token(value_str):
        return None
    raw_num, _ = split_numeric_suffix(value_str)
    if raw_num is None:
        return None
    raw = raw_num.strip()
    if "e" in raw.lower():
        return parse_float(raw)
    exp = scale_token_to_exp(ls_scale_token)
    val = parse_float(raw)
    if val is None:
        return None
    return val * (10 ** exp)


def format_value_from_base(base_value, old_value_str, ls_scale_token):
    if base_value is None:
        return old_value_str
    if is_na_token(old_value_str):
        exp = scale_token_to_exp(ls_scale_token)
        scaled = base_value / (10 ** exp)
        return format_decimal(scaled)
    old_num, suffix = split_numeric_suffix(old_value_str)
    if old_num is None:
        return old_value_str
    old = old_num.strip()
    if "e" in old.lower():
        parts = re.split(r"[eE]", old)
        if len(parts) == 2 and parts[1]:
            exp_str = parts[1]
            try:
                exp = int(exp_str)
                scaled = base_value / (10 ** exp)
                return f"{format_decimal(scaled)}e{exp_str}{suffix}"
            except Exception:
                pass
    exp = scale_token_to_exp(ls_scale_token)
    scaled = base_value / (10 ** exp)
    return f"{format_decimal(scaled)}{suffix}"


def get_decimal_places(num_str):
    if "." not in num_str:
        return 0
    return len(num_str.split(".", 1)[1])


def is_integer_like(value_str):
    num_str, _ = split_numeric_suffix(value_str)
    if num_str is None:
        return False
    if "e" in num_str or "E" in num_str:
        mantissa_str, exp_str = re.split(r"[eE]", num_str, maxsplit=1)
        if "." in mantissa_str:
            return False
        try:
            exp = int(exp_str)
        except Exception:
            return False
        return exp >= 0
    if "." in num_str:
        return False
    return True


def get_value_precision(value_str):
    num_str, _ = split_numeric_suffix(value_str)
    if num_str is None:
        return 0
    if "e" in num_str or "E" in num_str:
        mantissa_str = re.split(r"[eE]", num_str, maxsplit=1)[0]
        return get_decimal_places(mantissa_str)
    return get_decimal_places(num_str)


def get_effective_precision(old_value_str, csv_value_str, selected_precision, allow_int_lock=True):
    if selected_precision is None:
        return None
    if should_int_lock(old_value_str, allow_int_lock):
        return 0
    old_precision = get_value_precision(old_value_str)
    csv_precision = get_value_precision(csv_value_str) if csv_value_str is not None else None
    if selected_precision == "source":
        if csv_precision is None:
            return old_precision
        return max(old_precision, csv_precision)
    if selected_precision == "dynamic":
        target_precision = old_precision + 1
        if csv_precision is not None and csv_precision < target_precision:
            return csv_precision
        return target_precision
    if old_precision > selected_precision:
        if csv_precision is not None and csv_precision >= old_precision:
            return old_precision
        return selected_precision
    return max(selected_precision, old_precision)


def format_decimal_from_decimal(value):
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text == "-0":
        text = "0"
    return text


def format_decimal_with_precision(value, precision):
    if precision == 0:
        text = format(value, ".0f")
    else:
        text = format(value, f".{precision}f")
    if Decimal(text) == 0:
        return text.lstrip("-")
    return text


def parse_integer_like_value(value_str):
    num_str, _ = split_numeric_suffix(value_str)
    if num_str is None:
        return None
    try:
        value = Decimal(num_str)
    except InvalidOperation:
        return None
    if value != value.to_integral_value():
        return None
    try:
        return int(value)
    except (OverflowError, ValueError):
        return None


def parse_decimal_value(value_str):
    num_str, _ = split_numeric_suffix(value_str)
    if num_str is None:
        return None
    try:
        return Decimal(num_str)
    except InvalidOperation:
        return None


def clamp_tightened_limit(new_value_str, old_value_str, limit_kind):
    new_value = parse_decimal_value(new_value_str)
    old_value = parse_decimal_value(old_value_str)
    if new_value is None or old_value is None:
        return new_value_str
    if limit_kind == "ll" and new_value < old_value:
        return old_value_str
    if limit_kind == "ul" and new_value > old_value:
        return old_value_str
    return new_value_str


def should_int_lock(value_str, allow_int_lock=True):
    if not is_integer_like(value_str):
        return False
    if INT_LOCK_MODE == "disable":
        return False
    if INT_LOCK_MODE == "any_unit":
        return True
    if INT_LOCK_MODE == "threshold":
        threshold = INT_LOCK_THRESHOLD
        if threshold is None:
            return False
        int_val = parse_integer_like_value(value_str)
        if int_val is None:
            return False
        return int_val >= threshold
    return allow_int_lock


def apply_precision_override(value_str, precision, mode):
    if precision is None:
        return value_str
    num_str, suffix = split_numeric_suffix(value_str)
    if num_str is None:
        return value_str

    sep = "e" if "e" in num_str else ("E" if "E" in num_str else None)
    if sep:
        mantissa_str, exp_str = num_str.split(sep, 1)
        mantissa_precision = get_decimal_places(mantissa_str)
        if mantissa_precision == precision:
            return value_str
        try:
            mantissa = Decimal(mantissa_str)
        except InvalidOperation:
            return value_str
        adjusted = mantissa
        if mantissa_precision > precision:
            rounding = ROUND_FLOOR if mode == "floor" else ROUND_CEILING
            quant = Decimal("1").scaleb(-precision)
            adjusted = mantissa.quantize(quant, rounding=rounding)
        mantissa_text = format_decimal_with_precision(adjusted, precision)
        return f"{mantissa_text}{sep}{exp_str}{suffix}"

    current_precision = get_decimal_places(num_str)
    if current_precision == precision:
        return value_str
    try:
        value = Decimal(num_str)
    except InvalidOperation:
        return value_str
    adjusted = value
    if current_precision > precision:
        rounding = ROUND_FLOOR if mode == "floor" else ROUND_CEILING
        quant = Decimal("1").scaleb(-precision)
        adjusted = value.quantize(quant, rounding=rounding)
    adjusted_text = format_decimal_with_precision(adjusted, precision)
    return f"{adjusted_text}{suffix}"


def apply_precision_override_to_limits(new_ll, new_ul, old_ll, old_ul, unit_token, csv_ll=None, csv_ul=None):
    selected_precision = PRECISION_OVERRIDE
    unit_text = clean_token(unit_token)
    unit_empty = unit_text == ""
    if selected_precision is None:
        ll_precision = 0 if should_int_lock(old_ll, allow_int_lock=unit_empty) else get_value_precision(old_ll)
        ul_precision = 0 if should_int_lock(old_ul, allow_int_lock=unit_empty) else get_value_precision(old_ul)
    else:
        ll_precision = get_effective_precision(old_ll, csv_ll, selected_precision, allow_int_lock=unit_empty)
        ul_precision = get_effective_precision(old_ul, csv_ul, selected_precision, allow_int_lock=unit_empty)
    new_ll = apply_precision_override(new_ll, ll_precision, "ceil")
    new_ul = apply_precision_override(new_ul, ul_precision, "floor")
    new_ll = clamp_tightened_limit(new_ll, old_ll, "ll")
    new_ul = clamp_tightened_limit(new_ul, old_ul, "ul")
    return new_ll, new_ul


def build_change_parts(old_ll, new_ll, old_ul, new_ul, label_style):
    parts = []
    if old_ll != new_ll:
        parts.append(f"LL {old_ll}->{new_ll}")
    if old_ul != new_ul:
        parts.append(f"UL {old_ul}->{new_ul}")
    return parts


def split_macro_args(arg_str):
    args = []
    current = ""
    in_quotes = False
    quote_char = ""
    for ch in arg_str:
        if ch in ('\"', "'"):
            if in_quotes and ch == quote_char:
                in_quotes = False
            elif not in_quotes:
                in_quotes = True
                quote_char = ch
        if ch == ',' and not in_quotes:
            args.append(current)
            current = ""
        else:
            current += ch
    args.append(current)
    return args


def extract_bracket_limits(token):
    bracket_regex = re.compile(r"\[(\s*)([^,]+?)(\s*),(\s*)([^,]+?)(\s*),")
    match = bracket_regex.search(token)
    if not match:
        return None, None
    return match.group(2).strip(), match.group(5).strip()


def replace_arg_value(token, new_val):
    match = re.match(r"^(\s*)(.*?)(\s*)$", token, re.DOTALL)
    if not match:
        return new_val
    return f"{match.group(1)}{new_val}{match.group(3)}"


def replace_arg_value_with_padding(token, new_val):
    match = re.match(r"^(\s*)(.*?)(\s*)$", token, re.DOTALL)
    if not match:
        return new_val
    orig_pre = match.group(1)
    orig_val = match.group(2)
    orig_post = match.group(3)
    new_post = adjust_padding_for_slot(orig_pre, orig_val, orig_post, new_val)
    return f"{orig_pre}{new_val}{new_post}"


def get_visual_length(s):
    length = 0
    for char in s:
        if char == "\t":
            length += (TAB_WIDTH - (length % TAB_WIDTH))
        else:
            length += 1
    return length


def adjust_padding_for_slot(orig_pre, orig_val, orig_post, new_val):
    old_slot_visual_width = get_visual_length(orig_pre) + len(orig_val) + get_visual_length(orig_post)
    new_content_visual_width = get_visual_length(orig_pre) + len(new_val)
    needed_spaces = old_slot_visual_width - new_content_visual_width
    if needed_spaces < 1:
        return " " if (orig_post.strip() == "" and len(orig_post) > 0) or len(orig_post) > 0 else ""
    return " " * needed_spaces


def split_top_level_commas(line):
    parts = []
    current = ""
    in_quotes = False
    quote_char = ""
    bracket_depth = 0
    for ch in line:
        if ch in ('\"', "'"):
            if in_quotes and ch == quote_char:
                in_quotes = False
            elif not in_quotes:
                in_quotes = True
                quote_char = ch
        if ch == "[" and not in_quotes:
            bracket_depth += 1
        elif ch == "]" and not in_quotes and bracket_depth > 0:
            bracket_depth -= 1
        if ch == "," and not in_quotes and bracket_depth == 0:
            parts.append(current)
            current = ""
        else:
            current += ch
    parts.append(current)
    return parts


def parse_limit_table_envs(line):
    match = re.search(r"LimitTable\s*\[(.*?)\]", line)
    if not match:
        return None
    content = match.group(1)
    if "${" in content:
        return None
    envs = [env.strip() for env in content.split(",") if env.strip()]
    return envs if envs else None


def build_macro_indices(macros, env_value):
    macro_indices = {}
    for macro_name, arg_list in macros.items():
        indices = []
        if env_value == "ALL":
            for index, arg in enumerate(arg_list):
                if "_LL" in arg or "min" in arg.lower() or "Llimit" in arg:
                    if index + 1 < len(arg_list):
                        indices.append((index, index + 1))
        else:
            ll_idx = -1
            ul_idx = -1
            for index, arg in enumerate(arg_list):
                if env_value in arg and ("LL" in arg or "min" in arg.lower()):
                    ll_idx = index
                if env_value in arg and ("UL" in arg or "max" in arg.lower()):
                    ul_idx = index
            if ll_idx != -1 and ul_idx != -1:
                indices.append((ll_idx, ul_idx))
        if indices:
            macro_indices[macro_name] = indices
    return macro_indices


def detect_csv_format(headers):
    header_set = {header.strip().lower() for header in headers}
    if "expression" in header_set and "static high limit" in header_set and "static low limit" in header_set:
        return CSV_FORMAT_OPLUS
    if "scaled_lspl" in header_set or "scaled_uspl" in header_set:
        return CSV_FORMAT_SPL
    if "newlsl" in header_set or "newusl" in header_set:
        return CSV_FORMAT_SPAT
    return None


def read_csv_preview(filename):
    return _io_read_csv_preview(filename)


def read_csv_dict_rows(filename):
    return _io_read_csv_dict_rows(filename)


def combine_scaled_unit(scale_token, unit_token):
    unit = clean_token(unit_token)
    if unit == "":
        return ""
    prefix = scale_token_to_prefix(scale_token)
    if prefix and unit.startswith(prefix):
        return unit
    if prefix and unit:
        return f"{prefix}{unit}"
    return unit


__all__ = [
    "CSV_FORMAT_OPLUS",
    "CSV_FORMAT_SPL",
    "CSV_FORMAT_SPAT",
    "EPS",
    "adjust_padding_for_slot",
    "apply_precision_override",
    "apply_precision_override_to_limits",
    "build_change_parts",
    "build_macro_indices",
    "clean_token",
    "combine_scaled_unit",
    "detect_csv_format",
    "extract_bracket_limits",
    "format_decimal",
    "format_decimal_from_decimal",
    "format_value_from_base",
    "get_decimal_places",
    "get_effective_precision",
    "get_value_precision",
    "get_visual_length",
    "is_integer_like",
    "is_na_token",
    "is_number",
    "parse_float",
    "parse_integer_like_value",
    "parse_limit_table_envs",
    "parse_value_to_base",
    "read_csv_preview",
    "read_csv_dict_rows",
    "replace_arg_value",
    "replace_arg_value_with_padding",
    "scale_token_to_exp",
    "scale_token_to_prefix",
    "set_runtime_options",
    "should_int_lock",
    "split_macro_args",
    "split_numeric_suffix",
    "split_top_level_commas",
    "values_equivalent",
]