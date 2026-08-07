from __future__ import annotations

import os
import re
import sys

from ls_updater_cli import Colors, EnvInfo, color_text, is_quit_selection, print_c
from ls_updater_parse import detect_csv_format, read_csv_preview


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

REGEX_LIMIT_TABLE = re.compile(r"LimitTable\s*\[(.*?)\]")


def detect_env_codes_in_text(text):
    if not text:
        return []
    matches = []
    seen = set()
    regex = re.compile(r"(FC|FH|FA|QC|QH|QA|EC|EH|EA|ER)", re.IGNORECASE)
    for match in regex.finditer(text):
        code = match.group(1).upper()
        if code not in seen:
            matches.append(code)
            seen.add(code)
    return matches


def detect_env_names_in_text(text):
    if not text:
        return []
    matches = []
    seen = set()
    regex = re.compile(r"(FTC|FTH|FTR|FTA|QAC|QAH|QAR|EWC|EWH|EWA|EWR)", re.IGNORECASE)
    for match in regex.finditer(text):
        name = match.group(1).upper()
        if name not in seen:
            matches.append(name)
            seen.add(name)
    return matches


def map_env_code_to_names(code):
    return ENV_CODE_MAP.get(code, (None, None))


def env_name_to_code(env_name):
    if not env_name:
        return ""
    return ENV_NAME_TO_CODE.get(env_name, env_name)


def prompt_env_code_conflict(label, options):
    print_c(f"\nMultiple temperature codes detected from {label}:", Colors.WARNING)
    for idx, code in enumerate(options, start=1):
        primary, fallback = map_env_code_to_names(code)
        suffix = f" -> {primary}" if primary else ""
        if fallback:
            suffix += f" (fallback {fallback})"
        print(f"{idx}. {code}{suffix}")
    while True:
        selection = input(f"Select temperature code (1-{len(options)}, Q=quit): ").strip()
        if is_quit_selection(selection):
            sys.exit("User quit.")
        if not selection.isdigit():
            print_c("Invalid selection. Try again.", Colors.WARNING)
            continue
        index = int(selection)
        if index < 1 or index > len(options):
            print_c("Selection out of range. Try again.", Colors.WARNING)
            continue
        return options[index - 1]


def prompt_env_name_conflict(label, options):
    print_c(f"\nMultiple temperature names detected from {label}:", Colors.WARNING)
    for idx, name in enumerate(options, start=1):
        print(f"{idx}. {name}")
    while True:
        selection = input(f"Select temperature (1-{len(options)}, Q=quit): ").strip()
        if is_quit_selection(selection):
            sys.exit("User quit.")
        if not selection.isdigit():
            print_c("Invalid selection. Try again.", Colors.WARNING)
            continue
        index = int(selection)
        if index < 1 or index > len(options):
            print_c("Selection out of range. Try again.", Colors.WARNING)
            continue
        return options[index - 1]


def prompt_env_from_list(
    label,
    options,
    highlight_label=False,
    show_label=True,
    include_all=False,
    override_label=True,
):
    title = "--- Override Temperature ---" if override_label else "--- Select Temperature ---"
    if show_label and label:
        label_color = Colors.OKBLUE if not highlight_label else Colors.WARNING
        display_label = color_text(label, label_color)
        print_c(f"\n{title}: {display_label}", Colors.HEADER)
    else:
        print_c(f"\n{title}:", Colors.HEADER)
    for idx, option in enumerate(options, start=1):
        code = option.get("code")
        name = option.get("name")
        if name and name != code:
            name_display = color_text(f"({name})", Colors.GRAY)
            print(f"{idx}. {code} {name_display}")
        else:
            print(f"{idx}. {code}")
    if include_all:
        print(f"{len(options) + 1}. ALL")
    while True:
        max_index = len(options) + (1 if include_all else 0)
        selection = input(f"Select temperature (1-{max_index}, [Q]uit): ").strip()
        if is_quit_selection(selection):
            sys.exit("User quit.")
        if not selection.isdigit():
            print_c("Invalid selection. Try again.", Colors.WARNING)
            continue
        index = int(selection)
        if index < 1 or index > max_index:
            print_c("Selection out of range. Try again.", Colors.WARNING)
            continue
        if include_all and index == max_index:
            return "ALL"
        selected = options[index - 1]
        return selected.get("name") or selected.get("code")


def detect_envs_from_content(content):
    envs = []
    seen = set()
    env_line_regex = re.compile(r"^\s*([A-Za-z0-9]+)\s*\{\s*Flow=", re.MULTILINE)
    for match in env_line_regex.finditer(content):
        env = match.group(1).upper()
        if env not in seen:
            envs.append(env)
            seen.add(env)
    for match in REGEX_LIMIT_TABLE.finditer(content):
        raw = match.group(1)
        if "${" in raw:
            continue
        for env in raw.split(","):
            env = env.strip()
            if env:
                env = env.upper()
                if env not in seen:
                    envs.append(env)
                    seen.add(env)
    macro_env_regex = re.compile(r"\$\{\s*(?:LimitDef|UnBinLimitDef)_([A-Za-z0-9]+)\s*\(")
    for match in macro_env_regex.finditer(content):
        env = match.group(1).upper()
        if env not in seen:
            envs.append(env)
            seen.add(env)
    return envs


def prompt_env_choice(content):
    envs = detect_envs_from_content(content)
    if not envs:
        return "ALL"
    print_c("\n--- Temperature Selection ---", Colors.HEADER)
    envs = [env for env in envs if env != "ALL" and env[:1] in ["F", "E", "Q"]]
    if not envs:
        return "ALL"
    options = envs + ["ALL"]
    for idx, env in enumerate(options, start=1):
        print(f"{idx}. {env}")
    while True:
        selection = input("Select Temperature (Name or Number) [Q=quit]: ").strip()
        if is_quit_selection(selection):
            sys.exit("User quit.")
        if not selection:
            print_c("Selection required. Try again.", Colors.WARNING)
            continue
        if selection.isdigit():
            index = int(selection)
            if 1 <= index <= len(options):
                return options[index - 1]
            print_c("Selection out of range. Try again.", Colors.WARNING)
            continue
        selection = selection.upper()
        if selection in options:
            return selection
        print_c("Invalid selection. Try again.", Colors.WARNING)


def detect_env_from_csv(csv_path) -> EnvInfo:
    headers, first_row = read_csv_preview(csv_path)
    csv_format = detect_csv_format(headers or []) if headers else None
    sources = []
    env_name_candidates = []
    if csv_format == "spl" and headers and first_row:
        header_map = {header.lower(): header for header in headers}
        key = header_map.get("testprogram")
        if key:
            idx = headers.index(key)
            value = first_row[idx] if idx < len(first_row) else ""
            codes = [
                code for code in detect_env_codes_in_text(value)
                if not (map_env_code_to_names(code)[0] or "").startswith("E")
            ]
            if codes:
                sources.append(("CSV TestProgram", codes, []))
    filename = os.path.basename(csv_path)
    codes_from_name = [
        code for code in detect_env_codes_in_text(filename)
        if not (map_env_code_to_names(code)[0] or "").startswith("E")
    ]
    if codes_from_name:
        sources.append(("CSV filename", codes_from_name, []))
    names_from_name = [name for name in detect_env_names_in_text(filename) if not name.startswith("E")]
    if names_from_name:
        env_name_candidates.extend(names_from_name)

    if headers and first_row:
        row_text = " ".join([str(value) for value in first_row if value is not None])
        codes_from_row = [
            code for code in detect_env_codes_in_text(row_text)
            if not (map_env_code_to_names(code)[0] or "").startswith("E")
        ]
        if codes_from_row:
            sources.append(("CSV row", codes_from_row, []))
        names_from_row = [name for name in detect_env_names_in_text(row_text) if not name.startswith("E")]
        if names_from_row:
            env_name_candidates.extend(names_from_row)

    for label, codes, _ in sources:
        dedup_codes = list(dict.fromkeys(codes))
        if len(dedup_codes) == 1:
            primary, fallback = map_env_code_to_names(dedup_codes[0])
            return {"code": dedup_codes[0], "env": primary, "fallback": fallback, "source": label}
        if len(dedup_codes) > 1:
            code = prompt_env_code_conflict(label, dedup_codes)
            primary, fallback = map_env_code_to_names(code)
            return {"code": code, "env": primary, "fallback": fallback, "source": label}

    if env_name_candidates:
        env = env_name_candidates[0]
        if len(env_name_candidates) > 1:
            env = prompt_env_name_conflict("CSV filename", env_name_candidates)
        return {"code": None, "env": env, "fallback": None, "source": "CSV filename"}

    return {"code": None, "env": None, "fallback": None, "source": None}


def normalize_env_option(env_value):
    if not env_value:
        return None
    env_upper = env_value.upper()
    if env_upper in ENV_CODE_MAP:
        primary, _ = ENV_CODE_MAP.get(env_upper, (None, None))
        name = primary or env_upper
        return {"code": env_upper, "name": name}
    if env_upper in ENV_NAME_TO_CODE:
        return {"code": ENV_NAME_TO_CODE[env_upper], "name": env_upper}
    return None


def collect_env_options_from_ls(ls_paths):
    options = []
    seen = set()
    for ls_path in ls_paths:
        try:
            with open(ls_path, "r", encoding="utf-8", errors="ignore") as file_handle:
                content = file_handle.read()
            for env_name in detect_envs_from_content(content):
                if env_name.upper() == "ALL":
                    continue
                normalized = normalize_env_option(env_name)
                if not normalized:
                    continue
                key = (normalized["code"], normalized["name"])
                if key in seen:
                    continue
                options.append(normalized)
                seen.add(key)
        except Exception:
            continue
    return options


def detect_env_from_ls(ls_path) -> EnvInfo:
    parts = os.path.normpath(ls_path).split(os.sep)
    candidates = []
    for idx, part in enumerate(parts):
        if part.lower() == "maintestplan" and idx > 0:
            parent = parts[idx - 1]
            codes = [
                code for code in detect_env_codes_in_text(parent)
                if not (map_env_code_to_names(code)[0] or "").startswith("E")
            ]
            candidates.extend(codes)
    filename = os.path.splitext(os.path.basename(ls_path))[0]
    candidates.extend([
        code for code in detect_env_codes_in_text(filename)
        if not (map_env_code_to_names(code)[0] or "").startswith("E")
    ])
    candidates = [candidate for candidate in candidates if candidate in ENV_CODE_MAP]
    candidates = list(dict.fromkeys(candidates))
    if not candidates:
        names = [name for name in detect_env_names_in_text(filename) if not name.startswith("E")]
        if names:
            env = names[0] if len(names) == 1 else prompt_env_name_conflict("LS filename", names)
            return {"code": None, "env": env, "fallback": None, "source": "LS filename"}
        return {"code": None, "env": None, "fallback": None, "source": None}
    if len(candidates) > 1:
        code = prompt_env_code_conflict("LS path", candidates)
    else:
        code = candidates[0]
    primary, fallback = map_env_code_to_names(code)
    return {"code": code, "env": primary, "fallback": fallback, "source": "LS path"}


__all__ = [
    "collect_env_options_from_ls",
    "detect_env_codes_in_text",
    "detect_env_from_csv",
    "detect_env_from_ls",
    "detect_env_names_in_text",
    "detect_envs_from_content",
    "env_name_to_code",
    "map_env_code_to_names",
    "normalize_env_option",
    "prompt_env_choice",
    "prompt_env_code_conflict",
    "prompt_env_from_list",
    "prompt_env_name_conflict",
]