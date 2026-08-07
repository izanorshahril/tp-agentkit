from __future__ import annotations

import sys

from ls_updater_cli import Colors, color_text, print_c, to_rel_path
from ls_updater_env import env_name_to_code


def prompt_confirm_action():
    options_line = (
        "Select Option ("
        + "[" + color_text("P", Colors.WARNING) + "]roceed, "
        + "[" + color_text("S", Colors.WARNING) + "]tart over, "
        + "[" + color_text("C", Colors.WARNING) + "]olumn override, "
        + "[" + color_text("T", Colors.WARNING) + "]emperature override, "
        + "[" + color_text("Q", Colors.WARNING) + "]uit, "
        + color_text("[Enter] to Proceed", Colors.GRAY)
        + "): "
    )
    while True:
        selection = input(options_line).strip().lower()
        if selection == "":
            return "proceed"
        if selection in ["p", "proceed"]:
            return "proceed"
        if selection in ["s", "start", "restart"]:
            return "restart"
        if selection in ["c", "column", "columns", "override", "override columns"]:
            return "override_columns"
        if selection in ["t", "env", "environment", "temp", "temperature"]:
            return "override_env"
        if selection in ["q", "quit", "exit"]:
            return "quit"
        print_c("Invalid selection. Try again.", Colors.WARNING)


def prompt_output_conflict(path):
    sys.stdout.write("\r" + " " * 120 + "\r")
    sys.stdout.flush()
    print("\n" + color_text("Output already exists:", Colors.FAIL))
    print(f"{to_rel_path(path)}")
    options_line = (
        "Select Option ("
        + "[" + color_text("O", Colors.WARNING) + "]verwrite, "
        + "[" + color_text("R", Colors.WARNING) + "]etry, "
        + "[" + color_text("S", Colors.WARNING) + "]tart over, "
        + "[" + color_text("Q", Colors.WARNING) + "]uit "
        + color_text("[Enter] to Retry", Colors.GRAY)
        + "): "
    )
    while True:
        selection = input(options_line).strip().lower()
        if selection in ["", "y", "yes", "ok"]:
            return "retry"
        if selection in ["o", "overwrite"]:
            return "overwrite"
        if selection in ["r", "retry"]:
            return "retry"
        if selection in ["s", "start", "restart"]:
            return "restart"
        if selection in ["q", "quit", "e", "exit"]:
            return "quit"
        print_c("Invalid selection. Try again.", Colors.WARNING)


def prompt_env_conflict(csv_env, ls_env, csv_path, ls_path, env_options=None):
    print_c("\nTemperature conflict detected:", Colors.WARNING)
    csv_code = env_name_to_code(csv_env)
    ls_code = env_name_to_code(ls_env)
    csv_env_display = color_text(csv_code or "?", Colors.FAIL)
    ls_env_display = color_text(ls_code or "?", Colors.FAIL)
    csv_path_display = color_text(to_rel_path(csv_path), Colors.GRAY)
    ls_path_display = color_text(to_rel_path(ls_path), Colors.GRAY)
    print(f"CSV: {csv_env_display} {csv_path_display}")
    print(f"LS:  {ls_env_display} {ls_path_display}")
    options_line = (
        "Select Option ("
        + "[" + color_text("C", Colors.WARNING) + "]SV temperature, "
        + "[" + color_text("L", Colors.WARNING) + "]S temperature, "
        + "[" + color_text("O", Colors.WARNING) + "]verride, "
        + "[" + color_text("Q", Colors.WARNING) + "]uit, "
        + color_text(f"[Enter] to {ls_env_display}", Colors.GRAY)
        + "): "
    )
    while True:
        selection = input(options_line).strip().lower()
        if selection in [""]:
            return "ls"
        if selection in ["c", "csv"]:
            return "csv"
        if selection in ["l", "ls"]:
            return "ls"
        if selection in ["o", "override"]:
            return "override"
        if selection in ["q", "quit", "e", "exit"]:
            sys.exit("User quit.")
        print_c("Invalid selection. Try again.", Colors.WARNING)


def prompt_env_override(csv_path):
    options_line = (
        "Select Option: "
        + color_text("[", Colors.ENDC)
        + color_text("K", Colors.WARNING)
        + color_text("]", Colors.ENDC)
        + color_text("eep", Colors.WARNING)
        + color_text(", ", Colors.ENDC)
        + color_text("[", Colors.ENDC)
        + color_text("O", Colors.WARNING)
        + color_text("]", Colors.ENDC)
        + color_text("verride", Colors.WARNING)
        + color_text(", ", Colors.ENDC)
        + color_text("[", Colors.ENDC)
        + color_text("Q", Colors.WARNING)
        + color_text("]", Colors.ENDC)
        + color_text("uit", Colors.WARNING)
    )
    while True:
        selection = input(options_line).strip().lower()
        if selection in ["", "y", "yes", "ok"]:
            return "keep"
        if selection in ["k", "keep"]:
            return "keep"
        if selection in ["o", "override"]:
            return "override"
        if selection in ["q", "quit", "e", "exit"]:
            return "quit"
        print_c("Invalid selection. Try again.", Colors.WARNING)


def prompt_q_env_fallback(csv_env, fallback_env):
    print_c("\nQ temperature not found in LS files.", Colors.WARNING)
    print(f"CSV temperature: {csv_env}")
    if fallback_env:
        prompt = f"Use fallback {fallback_env}? (Y/N): "
    else:
        prompt = "No fallback available. Skip these jobs? (Y/N, both will exit): "
    while True:
        selection = input(prompt).strip().lower()
        if selection in ["y", "yes"]:
            if fallback_env:
                return True
            sys.exit("User chose to skip (no Q-temp fallback available).")
        if selection in ["n", "no"]:
            if fallback_env:
                return False
            sys.exit("User chose to skip (no Q-temp fallback available).")
        print_c("Invalid selection. Try again.", Colors.WARNING)


def prompt_pre_execution():
    options_line = (
        "Select Option: "
        + color_text("[", Colors.ENDC)
        + color_text("P", Colors.WARNING)
        + color_text("]", Colors.ENDC)
        + color_text("roceed", Colors.WARNING)
        + color_text(", ", Colors.ENDC)
        + color_text("[", Colors.ENDC)
        + color_text("S", Colors.WARNING)
        + color_text("]", Colors.ENDC)
        + color_text("tart over", Colors.WARNING)
        + color_text(", ", Colors.ENDC)
        + color_text("[", Colors.ENDC)
        + color_text("O", Colors.WARNING)
        + color_text("]", Colors.ENDC)
        + color_text("verride temperature", Colors.WARNING)
        + color_text(", ", Colors.ENDC)
        + color_text("[", Colors.ENDC)
        + color_text("Q", Colors.WARNING)
        + color_text("]", Colors.ENDC)
        + color_text("uit", Colors.WARNING)
    )
    while True:
        selection = input(options_line).strip().lower()
        if selection in ["", "y", "yes", "ok"]:
            return "proceed"
        if selection in ["p", "proceed", "y", "yes"]:
            return "proceed"
        if selection in ["s", "start", "restart"]:
            return "restart"
        if selection in ["o", "override"]:
            return "override"
        if selection in ["q", "quit", "e", "exit"]:
            return "quit"
        print_c("Invalid selection. Try again.", Colors.WARNING)


def prompt_csv_preview_action(csv_path):
    options_line = (
        "Select Option: "
        + color_text("[", Colors.ENDC)
        + color_text("P", Colors.WARNING)
        + color_text("]", Colors.ENDC)
        + color_text("roceed", Colors.WARNING)
        + color_text(", ", Colors.ENDC)
        + color_text("[", Colors.ENDC)
        + color_text("S", Colors.WARNING)
        + color_text("]", Colors.ENDC)
        + color_text("tart over", Colors.WARNING)
        + color_text(", ", Colors.ENDC)
        + color_text("[", Colors.ENDC)
        + color_text("O", Colors.WARNING)
        + color_text("]", Colors.ENDC)
        + color_text("verride columns", Colors.WARNING)
        + color_text(", ", Colors.ENDC)
        + color_text("[", Colors.ENDC)
        + color_text("Q", Colors.WARNING)
        + color_text("]", Colors.ENDC)
        + color_text("uit", Colors.WARNING)
    )
    print(options_line)
    while True:
        selection = input("").strip().lower()
        if selection in ["", "y", "yes", "ok"]:
            return "proceed"
        if selection in ["p", "proceed"]:
            return "proceed"
        if selection in ["s", "start", "restart"]:
            return "restart"
        if selection in ["o", "override"]:
            return "override"
        if selection in ["q", "quit", "e", "exit"]:
            return "quit"
        print_c("Invalid selection. Try again.", Colors.WARNING)


__all__ = [
    "prompt_confirm_action",
    "prompt_csv_preview_action",
    "prompt_env_conflict",
    "prompt_env_override",
    "prompt_output_conflict",
    "prompt_pre_execution",
    "prompt_q_env_fallback",
]