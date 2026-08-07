from __future__ import annotations

import csv
from pathlib import Path


DEFAULT_CSV_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")


def to_display_path(value: Path | str) -> str:
    return str(value).replace("\\", "/")


def iter_files(root: Path | str, pattern: str = "*", extensions: tuple[str, ...] | None = None) -> list[Path]:
    root_path = Path(root)
    ext_filter = {extension.lower() for extension in extensions} if extensions else None

    if root_path.is_file():
        if ext_filter and root_path.suffix.lower() not in ext_filter:
            return []
        if pattern != "*" and not root_path.match(pattern):
            return []
        return [root_path]
    if not root_path.exists():
        return []

    matches = [
        path for path in root_path.rglob(pattern)
        if path.is_file() and (not ext_filter or path.suffix.lower() in ext_filter)
    ]
    return sorted(matches)


def iter_scan_files(targets: list[str | Path], extensions: tuple[str, ...]) -> list[Path]:
    selected: set[Path] = set()
    ext_filter = tuple(extensions)
    for raw_target in targets:
        target = Path(raw_target)
        if target.is_file():
            if target.suffix.lower() in {extension.lower() for extension in ext_filter}:
                selected.add(target)
            continue
        selected.update(iter_files(target, extensions=ext_filter))
    return sorted(selected)


def display_path(path: Path | str, workspace_root: Path | str) -> str:
    resolved_path = Path(path).resolve()
    resolved_root = Path(workspace_root).resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError:
        return to_display_path(resolved_path)


def iter_relative_files(root: Path | str, pattern: str = "*", extensions: tuple[str, ...] | None = None) -> list[str]:
    root_path = Path(root)
    return [display_path(path, root_path) for path in iter_files(root_path, pattern=pattern, extensions=extensions)]


def read_csv_preview(path: Path | str, encodings: tuple[str, ...] = DEFAULT_CSV_ENCODINGS) -> tuple[list[str] | None, list[str] | None]:
    csv_path = Path(path)
    for encoding in encodings:
        try:
            with csv_path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.reader(handle)
                headers = next(reader)
                first_row = next(reader, [])
                return headers, first_row
        except UnicodeDecodeError:
            continue
        except (OSError, StopIteration):
            return None, None
    return None, None


def read_csv_dict_rows(path: Path | str, encodings: tuple[str, ...] = DEFAULT_CSV_ENCODINGS) -> list[dict[str, str]]:
    csv_path = Path(path)
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            with csv_path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                rows: list[dict[str, str]] = []
                for row in reader:
                    rows.append({str(key or ""): str(value or "") for key, value in row.items()})
                return rows
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
        except OSError as exc:
            last_error = exc
            continue
    if last_error is not None:
        raise last_error
    return []


__all__ = [
    "DEFAULT_CSV_ENCODINGS",
    "display_path",
    "iter_files",
    "iter_relative_files",
    "iter_scan_files",
    "read_csv_dict_rows",
    "read_csv_preview",
    "to_display_path",
]