from __future__ import annotations

import os
import sys

from ls_updater_cli import (
    Colors,
    color_text,
    format_path_with_colors,
    is_quit_selection,
    print_c,
)


def discover_files(root_dir, extension, skip_dirs=None):
    skip_dirs = skip_dirs or {"output", ".git", ".venv", "__pycache__"}
    matches = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [directory for directory in dirnames if directory not in skip_dirs]
        for name in filenames:
            if name.lower().endswith(extension):
                matches.append(os.path.join(dirpath, name))
    return matches


def select_file_from_list(files, label, root_dir, allow_multiple=False):
    if not files:
        sys.exit(f"Error: No {label} files found.")
    if len(files) == 1:
        path = files[0]
        rel = os.path.relpath(path, root_dir)
        name = os.path.basename(rel)
        dirpart = os.path.dirname(rel)
        dir_display = f"{dirpart}{os.sep}" if dirpart and dirpart != "." else ""
        if label == "CSV":
            print("")
        print_c(
            f"Detected {label} File: {color_text(name, Colors.OKGREEN)} ({color_text(dir_display, Colors.GRAY)})",
            Colors.OKBLUE,
        )
        return files if allow_multiple else files[0]

    print_c(f"\n--- Select {label} File ---", Colors.HEADER)
    for idx, path in enumerate(files, start=1):
        rel_path = os.path.relpath(path, root_dir)
        filename = os.path.basename(rel_path)
        rel_dir = os.path.dirname(rel_path)
        rel_dir_display = f"({rel_dir}{os.sep})" if rel_dir and rel_dir != "." else ""
        print(f"{idx}. {color_text(filename, Colors.OKGREEN)} {color_text(rel_dir_display, Colors.GRAY)}")

    while True:
        if allow_multiple:
            hint = color_text("add comma for multi selection", Colors.GRAY)
            range_display = color_text("1", Colors.WARNING) + "-" + color_text(str(len(files)), Colors.WARNING)
            all_display = "[" + color_text("A", Colors.WARNING) + "]ll"
            quit_display = "[" + color_text("Q", Colors.WARNING) + "]uit"
            selection = input(
                f"Select file(s) ({range_display}, {hint}, {all_display}, {quit_display}): "
            ).strip()
        else:
            quit_display = "[" + color_text("Q", Colors.WARNING) + "]uit"
            selection = input(f"Select file (1-{len(files)}, {quit_display}): ").strip()

        if is_quit_selection(selection):
            sys.exit("User quit.")
        if not selection:
            print_c("Selection required. Try again.", Colors.WARNING)
            continue
        if allow_multiple and selection.lower() in ["a", "all"]:
            return files
        if allow_multiple and "," in selection:
            parts = [part.strip() for part in selection.split(",") if part.strip()]
            if not parts:
                print_c("Invalid selection. Try again.", Colors.WARNING)
                continue
            indices = []
            invalid = False
            for part in parts:
                if not part.isdigit():
                    invalid = True
                    break
                index = int(part)
                if index < 1 or index > len(files):
                    invalid = True
                    break
                indices.append(index - 1)
            if invalid:
                print_c("Invalid selection. Try again.", Colors.WARNING)
                continue
            unique_indices = sorted(set(indices))
            return [files[index] for index in unique_indices]
        if not selection.isdigit():
            print_c("Invalid selection. Try again.", Colors.WARNING)
            continue
        index = int(selection)
        if index < 1 or index > len(files):
            print_c("Selection out of range. Try again.", Colors.WARNING)
            continue
        return files[index - 1]


def print_selected_files(label, paths, root_dir):
    print_c(f"\nSelected {label}:", Colors.OKBLUE)
    for path in paths:
        rel_path = os.path.relpath(path, root_dir)
        print(f"- {format_path_with_colors(rel_path, Colors.OKGREEN, Colors.GRAY)}")


def prompt_missing_files(csv_count, ls_count):
    print_c("\nNo CSV or LS files found.", Colors.WARNING)
    print(f"CSV files found: {csv_count}")
    print(f"LS files found: {ls_count}")
    options_line = (
        "Select Option ("
        + "[" + color_text("R", Colors.WARNING) + "]etry, "
        + "[" + color_text("Q", Colors.WARNING) + "]uit, "
        + color_text("[Enter] to Retry", Colors.GRAY)
        + "): "
    )
    while True:
        selection = input(options_line).strip().lower()
        if selection in ["", "r", "retry"]:
            return "retry"
        if selection in ["q", "quit", "e", "exit"]:
            sys.exit("User quit.")
        print_c("Invalid selection. Try again.", Colors.WARNING)


def resolve_paths(args, preview_csv_info):
    def split_paths(values):
        if not values:
            return []
        if isinstance(values, str):
            raw_items = [values]
        else:
            raw_items = values
        paths = []
        for item in raw_items:
            for part in str(item).split(","):
                part = part.strip()
                if part:
                    paths.append(part)
        return paths

    csv_paths_arg = split_paths(args.csv)
    ls_paths_arg = split_paths(args.ls)
    if csv_paths_arg and ls_paths_arg:
        return (
            [os.path.abspath(path) for path in csv_paths_arg],
            [os.path.abspath(path) for path in ls_paths_arg],
            False,
        )

    root = os.getcwd()
    csv_candidates = discover_files(root, ".csv")
    ls_candidates = discover_files(root, ".ls")

    if not args.silent and (len(csv_candidates) == 0 or len(ls_candidates) == 0):
        choice = prompt_missing_files(len(csv_candidates), len(ls_candidates))
        if choice == "retry":
            return [], [], True

    if args.silent:
        if len(csv_candidates) != 1 or len(ls_candidates) != 1:
            details = ["Error: Ambiguous or missing files in workspace."]
            details.append(f"CSV files found: {len(csv_candidates)}")
            details.append(f"LS files found: {len(ls_candidates)}")
            details.append("Provide --csv and --ls to select explicit files.")
            sys.exit("\n".join(details))
        return [os.path.abspath(csv_candidates[0])], [os.path.abspath(ls_candidates[0])], False

    selected_csv = select_file_from_list(csv_candidates, "CSV", root, allow_multiple=True)
    selected_csvs = selected_csv if isinstance(selected_csv, list) else [selected_csv]
    for csv_path in selected_csvs:
        preview_csv_info(csv_path, args, display=False)
    selected_ls = select_file_from_list(ls_candidates, "LS", root, allow_multiple=True)
    selected_lss = selected_ls if isinstance(selected_ls, list) else [selected_ls]
    return [os.path.abspath(path) for path in selected_csvs], [os.path.abspath(path) for path in selected_lss], False


__all__ = [
    "discover_files",
    "print_selected_files",
    "prompt_missing_files",
    "resolve_paths",
    "select_file_from_list",
]