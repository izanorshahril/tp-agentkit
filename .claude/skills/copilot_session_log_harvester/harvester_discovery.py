from __future__ import annotations

import os
from pathlib import Path

from harvester_session_parser import extract_tool_paths, is_workspace_relative_path, parse_json_arg, parse_json_line


KNOWN_VSCODE_PRODUCTS = ("Code - Insiders", "Code")


def resolve_debug_root(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_file() and path.name == "main.jsonl":
        return path.parent.parent
    if path.is_dir() and (path / "main.jsonl").exists():
        return path.parent
    return path


def discover_workspace_storage_roots() -> list[Path]:
    candidates: list[Path] = []
    seen: set[str] = set()

    appdata = os.environ.get("APPDATA")
    if appdata:
        roaming_root = Path(appdata)
        for product in KNOWN_VSCODE_PRODUCTS:
            candidates.append(roaming_root / product / "User" / "workspaceStorage")

    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        config_root = Path(xdg_config_home)
        for product in KNOWN_VSCODE_PRODUCTS:
            candidates.append(config_root / product / "User" / "workspaceStorage")
    else:
        config_root = Path.home() / ".config"
        for product in KNOWN_VSCODE_PRODUCTS:
            candidates.append(config_root / product / "User" / "workspaceStorage")

    existing_roots: list[Path] = []
    for candidate in candidates:
        resolved_key = str(candidate.resolve(strict=False)).casefold()
        if resolved_key in seen:
            continue
        seen.add(resolved_key)
        if candidate.exists():
            existing_roots.append(candidate)
    return existing_roots


def iter_detected_debug_roots() -> list[Path]:
    debug_roots: list[Path] = []
    for storage_root in discover_workspace_storage_roots():
        for workspace_dir in storage_root.iterdir():
            debug_root = workspace_dir / "GitHub.copilot-chat" / "debug-logs"
            if debug_root.is_dir():
                debug_roots.append(debug_root)
    return debug_roots


def score_debug_root(debug_root: Path, workspace_root: Path) -> tuple[int, float]:
    score = 0
    latest_activity_ms = 0.0
    latest_file_mtime_ms = 0.0
    session_logs = sorted(
        (path / "main.jsonl" for path in debug_root.iterdir() if path.is_dir() and (path / "main.jsonl").exists()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    for main_log in session_logs[:5]:
        latest_file_mtime_ms = max(latest_file_mtime_ms, main_log.stat().st_mtime * 1000.0)
        try:
            with main_log.open("r", encoding="utf-8", errors="ignore") as handle:
                for raw_line in handle:
                    try:
                        record = parse_json_line(raw_line)
                    except ValueError:
                        continue
                    timestamp = record.get("ts")
                    if isinstance(timestamp, int):
                        latest_activity_ms = max(latest_activity_ms, float(timestamp))
                    if not record or record.get("type") != "tool_call":
                        continue
                    tool_name = str(record.get("name") or "")
                    if not tool_name:
                        continue
                    attrs = record.get("attrs") or {}
                    parsed_args = parse_json_arg(attrs.get("args"))
                    read_paths, edited_paths = extract_tool_paths(tool_name, parsed_args, workspace_root)
                    for path in [*read_paths, *edited_paths]:
                        if is_workspace_relative_path(path):
                            score += 1
        except OSError:
            continue

    return score, latest_activity_ms or latest_file_mtime_ms


def auto_detect_debug_root(workspace_root: Path) -> Path:
    env_session_log = os.environ.get("VSCODE_TARGET_SESSION_LOG")
    if env_session_log:
        env_path = Path(env_session_log).expanduser()
        if env_path.exists():
            return resolve_debug_root(str(env_path))

    debug_roots = iter_detected_debug_roots()
    if not debug_roots:
        raise FileNotFoundError(
            "Could not auto-detect a Copilot debug log root. Pass log_root explicitly or ensure local VS Code Copilot debug logs exist."
        )

    if len(debug_roots) == 1:
        return debug_roots[0]

    scored_roots = [(score_debug_root(debug_root, workspace_root), debug_root) for debug_root in debug_roots]
    scored_roots.sort(
        key=lambda item: (item[0][0] > 0, item[0][1], item[0][0], str(item[1])),
        reverse=True,
    )
    return scored_roots[0][1]


def iter_session_dirs(debug_root: Path) -> list[Path]:
    if not debug_root.exists():
        raise FileNotFoundError(f"Debug log root not found: {debug_root}")

    session_dirs = [path for path in debug_root.iterdir() if path.is_dir() and (path / "main.jsonl").exists()]
    if not session_dirs:
        raise FileNotFoundError(f"No session folders with main.jsonl found under: {debug_root}")
    return sorted(session_dirs, key=lambda path: path.name)