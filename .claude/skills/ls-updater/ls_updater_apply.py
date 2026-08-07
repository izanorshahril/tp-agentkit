from __future__ import annotations

import re

from ls_updater_audit import split_unit_prefix
from ls_updater_parse import (
    EPS,
    adjust_padding_for_slot,
    apply_precision_override_to_limits,
    build_change_parts,
    combine_scaled_unit,
    extract_bracket_limits,
    format_value_from_base,
    is_na_token,
    is_number,
    parse_value_to_base,
    replace_arg_value_with_padding,
    split_numeric_suffix,
    split_macro_args,
    split_top_level_commas,
    values_equivalent,
)


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


def extract_env_block_tid(line):
    match = REGEX_ENV_BLOCK_TID.match(line)
    if not match:
        return ""
    return match.group(1)


def _parse_env_cell_body(body_text):
    return re.match(
        r"(?P<pre_ul>\s*)(?P<ul>[^,]+?)(?P<post_ul>\s*),(?P<pre_ll>\s*)(?P<ll>.+?)(?P<post_ll>\s*)$",
        body_text,
    )


def _extract_embedded_scaled_unit(*value_tokens):
    for value_token in value_tokens:
        _, suffix = split_numeric_suffix(value_token)
        unit_text = suffix.strip().strip('"').strip("'")
        if unit_text:
            return unit_text
    return ""


def _embedded_scale_token(unit_text):
    prefix, _ = split_unit_prefix(unit_text)
    return prefix


def get_ls_scaled_unit_from_env_block(line, env_filter):
    target_env = (env_filter or "").upper()
    for match in REGEX_ENV_CELL.finditer(line):
        env_name = match.group(1).upper()
        if env_name not in KNOWN_ENV_NAMES:
            continue
        if target_env and target_env != "ALL" and env_name != target_env:
            continue
        body_match = _parse_env_cell_body(match.group(2))
        if body_match is None:
            continue
        return _extract_embedded_scaled_unit(body_match.group("ul"), body_match.group("ll"))
    return ""


def update_bracket_token(
    token,
    base_ll,
    base_ul,
    ls_scale_token,
    unit_token,
    audit_entries,
    tid,
    env_tag,
    csv_ll,
    csv_ul,
):
    bracket_regex = re.compile(r"(\[)(\s*)([^,]+?)(\s*),(\s*)([^,]+?)(\s*),(.*?)(\])")
    match = bracket_regex.search(token)
    if not match:
        return token, False, ""

    old_ll = match.group(3).strip()
    old_ul = match.group(6).strip()
    old_ll_na = is_na_token(old_ll)
    old_ul_na = is_na_token(old_ul)
    if (not old_ll_na and not is_number(old_ll)) or (not old_ul_na and not is_number(old_ul)):
        return token, False, ""

    old_base_ll = parse_value_to_base(old_ll, ls_scale_token)
    old_base_ul = parse_value_to_base(old_ul, ls_scale_token)
    if (old_base_ll is None and not old_ll_na) or (old_base_ul is None and not old_ul_na):
        return token, False, ""

    if not old_ll_na and not old_ul_na:
        if abs(old_base_ll - base_ll) <= EPS and abs(old_base_ul - base_ul) <= EPS:
            return token, False, ""

    new_ll = format_value_from_base(base_ll, old_ll, ls_scale_token)
    new_ul = format_value_from_base(base_ul, old_ul, ls_scale_token)
    new_ll, new_ul = apply_precision_override_to_limits(
        new_ll,
        new_ul,
        old_ll,
        old_ul,
        unit_token,
        csv_ll=csv_ll,
        csv_ul=csv_ul,
    )

    if values_equivalent(old_ll, new_ll, ls_scale_token):
        new_ll = old_ll
    if values_equivalent(old_ul, new_ul, ls_scale_token):
        new_ul = old_ul

    new_space_post_ll = adjust_padding_for_slot(match.group(2), match.group(3), match.group(4), new_ll)
    new_space_post_ul = adjust_padding_for_slot(match.group(5), match.group(6), match.group(7), new_ul)

    updated = (
        f"{match.group(1)}{match.group(2)}{new_ll}{new_space_post_ll},"
        f"{match.group(5)}{new_ul}{new_space_post_ul},{match.group(8)}{match.group(9)}"
    )
    change_parts = build_change_parts(old_ll, new_ll, old_ul, new_ul, "comment")
    if not change_parts:
        return token, False, ""
    audit_entries.append(f"Table {env_tag} {tid}: {'; '.join(change_parts)}")
    comment = f"{env_tag}: {'; '.join(change_parts)}"
    return "".join(updated), True, comment


def update_table_line(line, limit_entry, env_filter, table_envs, audit_entries):
    match = REGEX_TABLE_TID.match(line)
    if not match:
        return line, False, [], "not a table line"

    tid = match.group(1)
    if tid not in limit_entry:
        return line, False, [], "tid not in csv"

    parts = split_top_level_commas(line)
    if len(parts) < 5:
        return line, False, [], "missing LL/UL fields"

    scale_token = parts[2]
    unit_token = parts[3]
    base_ll = limit_entry[tid]["base_ll"]
    base_ul = limit_entry[tid]["base_ul"]

    bracket_spans = list(re.finditer(r"\[[^\]]*\]", line))
    if not bracket_spans:
        return line, False, [], "no LL/UL brackets"

    target_indices = list(range(len(bracket_spans)))
    if len(bracket_spans) == 1:
        target_indices = [0]
    elif env_filter != "ALL" and table_envs:
        if env_filter in table_envs:
            target_indices = [table_envs.index(env_filter)]
        else:
            return line, False, [], "env mismatch"

    updated_line = ""
    last_end = 0
    modified = False
    saw_non_numeric = False
    saw_no_change = False
    comment_fragments = []
    for idx, span in enumerate(bracket_spans):
        updated_line += line[last_end:span.start()]
        token = line[span.start():span.end()]
        if idx in target_indices:
            if len(bracket_spans) == 1 and (table_envs and len(table_envs) > 1):
                env_tag = "ALL"
            else:
                if table_envs and idx < len(table_envs):
                    env_tag = table_envs[idx]
                else:
                    env_tag = env_filter if env_filter else "ENV"
            old_ll, old_ul = extract_bracket_limits(token)
            if old_ll is not None and old_ul is not None:
                old_ll_na = is_na_token(old_ll)
                old_ul_na = is_na_token(old_ul)
                old_base_ll = parse_value_to_base(old_ll, scale_token)
                old_base_ul = parse_value_to_base(old_ul, scale_token)
                if (old_base_ll is None and not old_ll_na) or (old_base_ul is None and not old_ul_na):
                    saw_non_numeric = True
                elif not old_ll_na and not old_ul_na:
                    if abs(old_base_ll - base_ll) <= EPS and abs(old_base_ul - base_ul) <= EPS:
                        saw_no_change = True
            csv_ll = limit_entry[tid].get("ll")
            csv_ul = limit_entry[tid].get("ul")
            updated_token, changed, comment = update_bracket_token(
                token,
                base_ll,
                base_ul,
                scale_token,
                unit_token,
                audit_entries,
                tid,
                env_tag,
                csv_ll,
                csv_ul,
            )
            updated_line += updated_token
            modified = modified or changed
            if changed and comment:
                comment_fragments.append(comment)
        else:
            updated_line += token
        last_end = span.end()
    updated_line += line[last_end:]

    if modified:
        return updated_line, True, comment_fragments, None
    if saw_non_numeric:
        return updated_line, False, comment_fragments, "non-numeric LL/UL"
    if saw_no_change:
        return updated_line, False, comment_fragments, "no change"
    return updated_line, False, comment_fragments, "no LL/UL update"


def get_ls_scaled_unit_from_macro(args_list):
    if len(args_list) < 4:
        return ""
    return combine_scaled_unit(args_list[2], args_list[3])


def get_ls_scaled_unit_from_table(parts):
    if len(parts) < 4:
        return ""
    return combine_scaled_unit(parts[2], parts[3])


def update_env_block_line(line, limit_entry, env_filter, audit_entries):
    tid = extract_env_block_tid(line)
    if not tid:
        return line, False, [], "not an env block line"
    if tid not in limit_entry:
        return line, False, [], "tid not in csv"

    base_ll = limit_entry[tid]["base_ll"]
    base_ul = limit_entry[tid]["base_ul"]
    csv_ll = limit_entry[tid].get("ll")
    csv_ul = limit_entry[tid].get("ul")
    target_env = (env_filter or "").upper()

    updated_line = ""
    last_end = 0
    modified = False
    saw_non_numeric = False
    saw_no_change = False
    saw_missing_fields = False
    saw_target_env = False
    comment_fragments = []

    for match in REGEX_ENV_CELL.finditer(line):
        env_name = match.group(1).upper()
        if env_name not in KNOWN_ENV_NAMES:
            continue

        updated_line += line[last_end:match.start()]
        cell_text = line[match.start():match.end()]
        last_end = match.end()

        if target_env and target_env != "ALL" and env_name != target_env:
            updated_line += cell_text
            continue

        saw_target_env = True
        body_match = _parse_env_cell_body(match.group(2))
        if body_match is None:
            saw_missing_fields = True
            updated_line += cell_text
            continue

        old_ul = body_match.group("ul").strip()
        old_ll = body_match.group("ll").strip()
        ls_scaled_unit = _extract_embedded_scaled_unit(old_ul, old_ll)
        ls_scale_token = _embedded_scale_token(ls_scaled_unit)

        old_ll_na = is_na_token(old_ll)
        old_ul_na = is_na_token(old_ul)
        old_base_ll = parse_value_to_base(old_ll, ls_scale_token)
        old_base_ul = parse_value_to_base(old_ul, ls_scale_token)
        if (old_base_ll is None and not old_ll_na) or (old_base_ul is None and not old_ul_na):
            saw_non_numeric = True
            updated_line += cell_text
            continue
        if not old_ll_na and not old_ul_na:
            if abs(old_base_ll - base_ll) <= EPS and abs(old_base_ul - base_ul) <= EPS:
                saw_no_change = True

        new_ll = format_value_from_base(base_ll, old_ll, ls_scale_token)
        new_ul = format_value_from_base(base_ul, old_ul, ls_scale_token)
        new_ll, new_ul = apply_precision_override_to_limits(
            new_ll,
            new_ul,
            old_ll,
            old_ul,
            ls_scaled_unit,
            csv_ll=csv_ll,
            csv_ul=csv_ul,
        )

        if values_equivalent(old_ll, new_ll, ls_scale_token):
            new_ll = old_ll
        if values_equivalent(old_ul, new_ul, ls_scale_token):
            new_ul = old_ul

        changed = new_ll != old_ll or new_ul != old_ul
        if not changed:
            updated_line += cell_text
            continue

        new_post_ul = adjust_padding_for_slot(
            body_match.group("pre_ul"),
            body_match.group("ul"),
            body_match.group("post_ul"),
            new_ul,
        )
        new_post_ll = adjust_padding_for_slot(
            body_match.group("pre_ll"),
            body_match.group("ll"),
            body_match.group("post_ll"),
            new_ll,
        )
        updated_line += (
            f"{env_name}("
            f"{body_match.group('pre_ul')}{new_ul}{new_post_ul},"
            f"{body_match.group('pre_ll')}{new_ll}{new_post_ll})"
        )

        change_log = build_change_parts(old_ll, new_ll, old_ul, new_ul, "log")
        change_comment = build_change_parts(old_ll, new_ll, old_ul, new_ul, "comment")
        if change_log:
            audit_entries.append(f"EnvBlock {env_name} {tid}: {'; '.join(change_log)}")
            comment_fragments.append(f"{env_name}: {'; '.join(change_comment)}")
        modified = True

    updated_line += line[last_end:]

    if not saw_target_env:
        return line, False, [], "env mismatch"
    if modified:
        return updated_line, True, comment_fragments, None
    if saw_non_numeric:
        return updated_line, False, comment_fragments, "non-numeric LL/UL"
    if saw_missing_fields:
        return updated_line, False, comment_fragments, "missing LL/UL fields"
    if saw_no_change:
        return updated_line, False, comment_fragments, "no change"
    return updated_line, False, comment_fragments, "no LL/UL update"


def update_macro_line(line, limit_entry, env_filter, macro_indices_by_name, audit_entries):
    match = REGEX_MACRO_CALL.search(line)
    if not match:
        return line, False, [], "not a macro line"

    macro_name = match.group(1)
    raw_args = split_macro_args(match.group(2))
    args_list = [arg.strip() for arg in raw_args]
    if not args_list:
        return line, False, [], "missing args"

    tid = args_list[0].replace("\"", "").strip()
    if tid not in limit_entry:
        return line, False, [], "tid not in csv"

    base_ll = limit_entry[tid]["base_ll"]
    base_ul = limit_entry[tid]["base_ul"]
    csv_ll = limit_entry[tid].get("ll")
    csv_ul = limit_entry[tid].get("ul")
    scale_token = args_list[2] if len(args_list) > 2 else ""

    modified = False
    old_vals_log = []
    comment_fragments = []

    macro_indices = macro_indices_by_name.get(macro_name, []) if macro_indices_by_name else []
    if macro_indices:
        saw_non_numeric = False
        saw_no_change = False
        for l_idx, u_idx in macro_indices:
            if u_idx >= len(args_list):
                continue
            old_ll = args_list[l_idx]
            old_ul = args_list[u_idx]
            old_ll_na = is_na_token(old_ll)
            old_ul_na = is_na_token(old_ul)
            old_base_ll = parse_value_to_base(old_ll, scale_token)
            old_base_ul = parse_value_to_base(old_ul, scale_token)
            if (old_base_ll is None and not old_ll_na) or (old_base_ul is None and not old_ul_na):
                saw_non_numeric = True
                continue
            if not old_ll_na and not old_ul_na:
                if abs(old_base_ll - base_ll) <= EPS and abs(old_base_ul - base_ul) <= EPS:
                    saw_no_change = True
                    continue
            new_ll = format_value_from_base(base_ll, old_ll, scale_token)
            new_ul = format_value_from_base(base_ul, old_ul, scale_token)
            unit_token = args_list[3] if len(args_list) > 3 else ""
            new_ll, new_ul = apply_precision_override_to_limits(
                new_ll,
                new_ul,
                old_ll,
                old_ul,
                unit_token,
                csv_ll=csv_ll,
                csv_ul=csv_ul,
            )
            if values_equivalent(old_ll, new_ll, scale_token):
                new_ll = old_ll
            if values_equivalent(old_ul, new_ul, scale_token):
                new_ul = old_ul
            raw_args[l_idx] = replace_arg_value_with_padding(raw_args[l_idx], new_ll)
            raw_args[u_idx] = replace_arg_value_with_padding(raw_args[u_idx], new_ul)
            args_list[l_idx] = new_ll
            args_list[u_idx] = new_ul
            change_log = build_change_parts(old_ll, new_ll, old_ul, new_ul, "log")
            change_comment = build_change_parts(old_ll, new_ll, old_ul, new_ul, "comment")
            if not change_log:
                continue
            old_vals_log.append("; ".join(change_log))
            env_tag = env_filter if env_filter else "ENV"
            comment_fragments.append(f"{env_tag}: {'; '.join(change_comment)}")
            modified = True
        if not modified:
            if saw_non_numeric:
                return line, False, [], "non-numeric LL/UL"
            if saw_no_change:
                return line, False, [], "no change"
            return line, False, [], "no LL/UL update"
    elif macro_name.startswith("LimitDef_") or macro_name.startswith("UnBinLimitDef_"):
        macro_env = macro_name.split("_", 1)[1].upper()
        if env_filter != "ALL" and macro_env != env_filter:
            return line, False, [], "env mismatch"
        if len(args_list) >= 2:
            l_idx = len(args_list) - 2
            u_idx = len(args_list) - 1
            old_ll = args_list[l_idx]
            old_ul = args_list[u_idx]
            old_ll_na = is_na_token(old_ll)
            old_ul_na = is_na_token(old_ul)
            old_base_ll = parse_value_to_base(old_ll, scale_token)
            old_base_ul = parse_value_to_base(old_ul, scale_token)
            if (old_base_ll is None and not old_ll_na) or (old_base_ul is None and not old_ul_na):
                return line, False, [], "non-numeric LL/UL"
            if not old_ll_na and not old_ul_na:
                if abs(old_base_ll - base_ll) <= EPS and abs(old_base_ul - base_ul) <= EPS:
                    return line, False, [], "no change"
            new_ll = format_value_from_base(base_ll, old_ll, scale_token)
            new_ul = format_value_from_base(base_ul, old_ul, scale_token)
            unit_token = args_list[3] if len(args_list) > 3 else ""
            new_ll, new_ul = apply_precision_override_to_limits(
                new_ll,
                new_ul,
                old_ll,
                old_ul,
                unit_token,
                csv_ll=csv_ll,
                csv_ul=csv_ul,
            )
            if values_equivalent(old_ll, new_ll, scale_token):
                new_ll = old_ll
            if values_equivalent(old_ul, new_ul, scale_token):
                new_ul = old_ul
            raw_args[l_idx] = replace_arg_value_with_padding(raw_args[l_idx], new_ll)
            raw_args[u_idx] = replace_arg_value_with_padding(raw_args[u_idx], new_ul)
            args_list[l_idx] = new_ll
            args_list[u_idx] = new_ul
            change_log = build_change_parts(old_ll, new_ll, old_ul, new_ul, "log")
            change_comment = build_change_parts(old_ll, new_ll, old_ul, new_ul, "comment")
            if not change_log:
                return line, False, [], "no change"
            old_vals_log.append("; ".join(change_log))
            comment_fragments.append(f"{macro_env}: {'; '.join(change_comment)}")
            modified = True
    elif macro_name.startswith("LimitDef") or macro_name.startswith("UnBinLimitDef"):
        if len(args_list) >= 2:
            l_idx = len(args_list) - 2
            u_idx = len(args_list) - 1
            old_ll = args_list[l_idx]
            old_ul = args_list[u_idx]
            old_ll_na = is_na_token(old_ll)
            old_ul_na = is_na_token(old_ul)
            old_base_ll = parse_value_to_base(old_ll, scale_token)
            old_base_ul = parse_value_to_base(old_ul, scale_token)
            if (old_base_ll is None and not old_ll_na) or (old_base_ul is None and not old_ul_na):
                return line, False, [], "non-numeric LL/UL"
            if not old_ll_na and not old_ul_na:
                if abs(old_base_ll - base_ll) <= EPS and abs(old_base_ul - base_ul) <= EPS:
                    return line, False, [], "no change"
            new_ll = format_value_from_base(base_ll, old_ll, scale_token)
            new_ul = format_value_from_base(base_ul, old_ul, scale_token)
            unit_token = args_list[3] if len(args_list) > 3 else ""
            new_ll, new_ul = apply_precision_override_to_limits(
                new_ll,
                new_ul,
                old_ll,
                old_ul,
                unit_token,
                csv_ll=csv_ll,
                csv_ul=csv_ul,
            )
            if values_equivalent(old_ll, new_ll, scale_token):
                new_ll = old_ll
            if values_equivalent(old_ul, new_ul, scale_token):
                new_ul = old_ul
            raw_args[l_idx] = replace_arg_value_with_padding(raw_args[l_idx], new_ll)
            raw_args[u_idx] = replace_arg_value_with_padding(raw_args[u_idx], new_ul)
            args_list[l_idx] = new_ll
            args_list[u_idx] = new_ul
            change_log = build_change_parts(old_ll, new_ll, old_ul, new_ul, "log")
            change_comment = build_change_parts(old_ll, new_ll, old_ul, new_ul, "comment")
            if not change_log:
                return line, False, [], "no change"
            old_vals_log.append("; ".join(change_log))
            env_tag = env_filter if env_filter else "ENV"
            comment_fragments.append(f"{env_tag}: {'; '.join(change_comment)}")
            modified = True
    else:
        return line, False, [], "no LL/UL update"

    if modified:
        new_args_str = ",".join(raw_args)
        line = line[:match.start(2)] + new_args_str + line[match.end(2):]
        audit_entries.append(f"Macro {tid}: {'; '.join(old_vals_log)}")

    return line, modified, comment_fragments, None if modified else "no change"


__all__ = [
    "extract_env_block_tid",
    "get_ls_scaled_unit_from_env_block",
    "get_ls_scaled_unit_from_macro",
    "get_ls_scaled_unit_from_table",
    "update_bracket_token",
    "update_env_block_line",
    "update_macro_line",
    "update_table_line",
]