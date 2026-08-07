from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Dict, Optional, TypedDict, cast


class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    GRAY = "\033[90m"
    ENDC = "\033[0m"


class EnvInfo(TypedDict, total=False):
    code: Optional[str]
    env: Optional[str]
    fallback: Optional[str]
    source: Optional[str]


def get_env_info(store: Dict[str, EnvInfo], path: str) -> EnvInfo:
    info = store.get(path)
    if info is None:
        info = {}
        store[path] = cast(EnvInfo, info)
    return cast(EnvInfo, info)


def print_c(msg, color=Colors.ENDC):
    print(f"{color}{msg}{Colors.ENDC}")


def color_text(msg, color):
    return f"{color}{msg}{Colors.ENDC}"


def format_path_with_colors(path, name_color, path_color=Colors.GRAY):
    rel_path = to_rel_path(path)
    dir_part = os.path.dirname(rel_path)
    file_part = os.path.basename(rel_path)
    if dir_part:
        dir_part = dir_part + os.sep
        return f"{color_text(dir_part, path_color)}{color_text(file_part, name_color)}"
    return color_text(file_part, name_color)


def is_quit_selection(selection):
    return selection.strip().lower() in ["q", "quit", "exit"]


def parse_arguments():
    parser = argparse.ArgumentParser(description="T2K Limit Updater")
    def parse_precision_override(value):
        text = str(value).strip().lower()
        if text in {"1", "2", "3"}:
            return int(text)
        if text in {"dynamic", "source"}:
            return text
        raise argparse.ArgumentTypeError("Precision must be one of: 1, 2, 3, dynamic, source")

    parser.add_argument(
        "--csv",
        action="append",
        help="Input CSV file (repeatable or comma-separated)",
    )
    parser.add_argument(
        "--ls",
        action="append",
        help="Target .ls file (repeatable or comma-separated)",
    )
    parser.add_argument("--env", help="Temperature (FTC, ALL, etc)")
    parser.add_argument(
        "--precision",
        type=parse_precision_override,
        help="Precision override for LL/UL rounding (1-3, dynamic, source)",
    )
    parser.add_argument("--silent", action="store_true", help="No output unless error")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Backup and overwrite the original .ls in its folder",
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Write a log file (default: no log)",
    )
    parser.add_argument(
        "--log-path",
        help="Explicit log file path (implies --log)",
    )
    parser.add_argument(
        "--report-json",
        action="store_true",
        help="Emit a one-line JSON status report to stdout",
    )
    return parser.parse_args()


def log_print(msg, args):
    if not args.silent:
        print(msg)


def debug_print(msg, args):
    if args.verbose and not args.silent:
        print(msg)


def to_rel_path(path, base_dir=None):
    if not path:
        return ""
    base_dir = base_dir or os.getcwd()
    try:
        rel_path = os.path.relpath(path, base_dir)
    except Exception:
        return path
    return rel_path


def should_show_progress(args, total_tests=None, progress_min_tests=50):
    base_check = (not args.silent) and (not args.report_json) and sys.stdout.isatty()
    if not base_check:
        return False
    if total_tests is not None and total_tests < progress_min_tests:
        return False
    return True


def render_progress(current, total, prefix, color):
    if total <= 0:
        return
    width = 30
    ratio = min(max(current / total, 0.0), 1.0)
    filled = int(width * ratio)
    bar = "#" * filled + "-" * (width - filled)
    percent = int(ratio * 100)
    label = f"{prefix} " if prefix else ""
    sys.stdout.write(
        f"\r{color}{label}[{bar}] {percent:3d}% ({current}/{total}){Colors.ENDC}"
    )
    sys.stdout.flush()


def finish_progress(enabled, total, prefix, start_time, end_time=None, emit=True):
    elapsed_sec = 0.0
    if enabled:
        end_time = end_time or time.perf_counter()
        elapsed_ms = int((end_time - start_time) * 1000)
        elapsed_sec = elapsed_ms / 1000 if elapsed_ms > 0 else 0.001
        sys.stdout.write("\r" + " " * 120 + "\r")
        if emit:
            sys.stdout.write(
                f"{Colors.GRAY}Completed {total} tests in {elapsed_sec:.2f} sec{Colors.ENDC}\n"
            )
        sys.stdout.flush()
    return elapsed_sec


__all__ = [
    "Colors",
    "EnvInfo",
    "color_text",
    "debug_print",
    "finish_progress",
    "format_path_with_colors",
    "get_env_info",
    "is_quit_selection",
    "log_print",
    "parse_arguments",
    "print_c",
    "render_progress",
    "should_show_progress",
    "to_rel_path",
]