#!/usr/bin/env python3
"""Convert supported HTML diff reports to text summaries and unified patches."""

from __future__ import annotations

import argparse
from collections import Counter
import difflib
import html
import re
from dataclasses import asdict, dataclass
from itertools import zip_longest
from pathlib import Path
from typing import Any, Iterable


TR_RE = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
TD_RE = re.compile(r"<td\b[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL)
TD_WITH_ATTR_RE = re.compile(r"<td\b([^>]*)>(.*?)</td>", re.IGNORECASE | re.DOTALL)
TH_RE = re.compile(r"<th\b[^>]*class=\"title\"[^>]*>(.*?)</th>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>", re.DOTALL)
FILE_SECTION_RE = re.compile(r"(?:^|<br\s*/?>)\s*File:\s*(.*?)\s*&nbsp;", re.IGNORECASE | re.MULTILINE)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
HREF_RE = re.compile(r'href="([^"]+\.html)"', re.IGNORECASE)
WINMERGE_COMPARE_RE = re.compile(r"^Compare\s+(.*?)\s+with\s+(.*?)$", re.IGNORECASE)


@dataclass
class HtmlCompare:
    rel_path: str | None
    left_name: str
    right_name: str
    left_lines: list[str]
    right_lines: list[str]


@dataclass
class HtmlReportSection:
    path: str
    status: str
    changed_rows: int


def _clean_cell(cell_html: str) -> str:
    text = cell_html.replace("<wbr>", "").replace("<wbr/>", "").replace("<wbr />", "")
    text = re.sub(r"<img\b.*?align=\"middle\">", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = TAG_RE.sub("", text)
    text = html.unescape(text).replace("\xa0", " ")
    return text.rstrip("\r\n")


def _extract_labeled_value(content: str, label: str) -> str | None:
    match = re.search(rf"{re.escape(label)}\s*(.*?)<br\s*/?>", content, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    value = _clean_cell(match.group(1)).strip()
    return value or None


def _normalize_rel_path(value: str) -> str:
    return value.strip().replace("\\", "/")


def _build_full_name(base_folder: str | None, rel_path: str, fallback_root: str) -> str:
    native_rel = rel_path.replace("/", "\\")
    if base_folder:
        return f"{base_folder.rstrip('\\/')}\\{native_rel}"
    return f"{fallback_root}\\{native_rel}"


def _cell_has_line(cell_html: str) -> bool:
    return bool(_clean_cell(cell_html).strip()) or "<br" in cell_html.lower()


def _extract_winmerge_compare_paths(content: str) -> tuple[str | None, str | None]:
    title_match = TITLE_RE.search(content)
    if not title_match:
        return None, None

    title_text = _clean_cell(title_match.group(1)).strip()
    compare_match = WINMERGE_COMPARE_RE.match(title_text)
    if not compare_match:
        return None, None
    return compare_match.group(1).strip(), compare_match.group(2).strip()


def _extract_row_pair(row: str) -> tuple[str, str, bool, bool] | None:
    cells = TD_RE.findall(row)
    if len(cells) >= 5:
        return (
            _clean_cell(cells[1]),
            _clean_cell(cells[4]),
            _cell_has_line(cells[0]) or _cell_has_line(cells[1]),
            _cell_has_line(cells[3]) or _cell_has_line(cells[4]),
        )
    if len(cells) >= 4:
        return (
            _clean_cell(cells[1]),
            _clean_cell(cells[3]),
            _cell_has_line(cells[0]) or _cell_has_line(cells[1]),
            _cell_has_line(cells[2]) or _cell_has_line(cells[3]),
        )
    return None


def _normalize_folder_report_sides(
    left_lines: list[str],
    right_lines: list[str],
    left_present: bool,
    right_present: bool,
) -> tuple[list[str], list[str]]:
    if not left_present and right_present:
        left_lines = []
    if not right_present and left_present:
        right_lines = []

    return left_lines, right_lines


def _parse_single_compare(content: str, path: Path) -> list[HtmlCompare]:
    title_cells = [_clean_cell(m) for m in TH_RE.findall(content)]
    if len(title_cells) >= 4:
        left_name = title_cells[1]
        right_name = title_cells[3]
    else:
        left_name = f"{path.stem}_left"
        right_name = f"{path.stem}_right"

    left_lines: list[str] = []
    right_lines: list[str] = []

    for row in TR_RE.findall(content):
        pair = _extract_row_pair(row)
        if pair is None:
            continue
        left_text, right_text, _, _ = pair
        left_lines.append(left_text)
        right_lines.append(right_text)

    return [HtmlCompare(rel_path=None, left_name=left_name, right_name=right_name, left_lines=left_lines, right_lines=right_lines)]


def _parse_folder_report(content: str, path: Path) -> list[HtmlCompare]:
    left_base = _extract_labeled_value(content, "Left base folder:")
    right_base = _extract_labeled_value(content, "Right base folder:")
    sections: list[HtmlCompare] = []

    for match in FILE_SECTION_RE.finditer(content):
        rel_path = _normalize_rel_path(_clean_cell(match.group(1)))
        if not rel_path:
            continue

        next_match = FILE_SECTION_RE.search(content, match.end())
        section_html = content[match.end(): next_match.start() if next_match else len(content)]

        left_lines: list[str] = []
        right_lines: list[str] = []
        left_present = False
        right_present = False
        for row in TR_RE.findall(section_html):
            pair = _extract_row_pair(row)
            if pair is None:
                continue
            left_text, right_text, row_left_present, row_right_present = pair
            left_lines.append(left_text)
            right_lines.append(right_text)
            left_present = left_present or row_left_present
            right_present = right_present or row_right_present

        left_lines, right_lines = _normalize_folder_report_sides(
            left_lines,
            right_lines,
            left_present,
            right_present,
        )

        sections.append(
            HtmlCompare(
                rel_path=rel_path,
                left_name=_build_full_name(left_base, rel_path, f"{path.stem}_left"),
                right_name=_build_full_name(right_base, rel_path, f"{path.stem}_right"),
                left_lines=left_lines,
                right_lines=right_lines,
            )
        )

    return sections


def _is_beyond_compare_directory_summary(content: str) -> bool:
    return "left base folder:" in content.lower() and "right base folder:" in content.lower() and 'table class="dc"' in content.lower()


def _parse_winmerge_index(content: str, path: Path) -> list[HtmlCompare]:
    left_base, right_base = _extract_winmerge_compare_paths(content)
    if left_base is None or right_base is None or ".files/" not in content.lower():
        return []

    sections: list[HtmlCompare] = []
    for row in TR_RE.findall(content):
        cells = TD_RE.findall(row)
        if len(cells) < 3:
            continue

        href_match = HREF_RE.search(cells[0])
        if not href_match:
            continue

        child_path = path.parent / html.unescape(href_match.group(1))
        if not child_path.exists():
            raise ValueError(f"WinMerge linked report not found: {child_path}")

        filename = _clean_cell(cells[0]).strip()
        folder = _clean_cell(cells[1]).strip()
        rel_path = _normalize_rel_path(f"{folder}/{filename}" if folder else filename)

        child_compares = _parse_single_compare(child_path.read_text(encoding="utf-8", errors="replace"), child_path)
        if not child_compares:
            continue

        compare = child_compares[0]
        compare.rel_path = rel_path
        if compare.left_name == f"{child_path.stem}_left":
            compare.left_name = _build_full_name(left_base, rel_path, f"{path.stem}_left")
        if compare.right_name == f"{child_path.stem}_right":
            compare.right_name = _build_full_name(right_base, rel_path, f"{path.stem}_right")
        sections.append(compare)

    return sections


def parse_winmerge_html(path: Path) -> list[HtmlCompare]:
    content = path.read_text(encoding="utf-8", errors="replace")
    if FILE_SECTION_RE.search(content):
        sections = _parse_folder_report(content, path)
        if sections:
            return sections
    if _is_beyond_compare_directory_summary(content):
        raise ValueError(
            "Beyond Compare directory-summary HTML does not contain per-file text rows. Export a per-file report or use tp_diff_compare for scope validation."
        )
    sections = _parse_winmerge_index(content, path)
    if sections:
        return sections
    return _parse_single_compare(content, path)


def _count_changed_rows(left_lines: list[str], right_lines: list[str]) -> int:
    return sum(1 for left, right in zip_longest(left_lines, right_lines, fillvalue="") if left != right)


def _status_from_compare(compare: HtmlCompare) -> str:
    if compare.left_lines and compare.right_lines:
        return "changed"
    if compare.right_lines:
        return "only_current"
    return "only_baseline"


def _build_status_report(
    path: Path,
    title: str,
    left_base: str | None,
    right_base: str | None,
    mode: str | None,
    sections: list[HtmlReportSection],
) -> dict[str, Any]:
    status_counts = Counter(section.status for section in sections)
    return {
        "report_path": str(path),
        "title": title,
        "left_base": left_base,
        "right_base": right_base,
        "mode": mode,
        "counts": {
            "files": len(sections),
            "changed": status_counts.get("changed", 0),
            "only_baseline": status_counts.get("only_baseline", 0),
            "only_current": status_counts.get("only_current", 0),
        },
        "sections": [asdict(section) for section in sections],
    }


def _map_winmerge_status(status_text: str) -> str | None:
    normalized = status_text.strip().lower()
    if normalized.startswith("right only:"):
        return "only_current"
    if normalized.startswith("left only:"):
        return "only_baseline"
    if "different" in normalized:
        return "changed"
    return None


def _parse_beyond_compare_directory_summary_index(path: Path, content: str) -> dict[str, Any] | None:
    if not (
        "left base folder:" in content.lower()
        and "right base folder:" in content.lower()
        and 'table class="dc"' in content.lower()
    ):
        return None

    title_match = TITLE_RE.search(content)
    sections: list[HtmlReportSection] = []
    current_dir: str | None = None

    for row in TR_RE.findall(content):
        if "diritemheader" in row.lower():
            continue
        cells = TD_WITH_ATTR_RE.findall(row)
        if len(cells) < 7:
            continue

        left_name_html = cells[0][1]
        right_name_html = cells[4][1]
        left_name = _clean_cell(left_name_html)
        right_name = _clean_cell(right_name_html)

        is_directory_row = 'alt="<dir>"' in row.lower()
        has_tree_marker = "<img" in left_name_html.lower() or "<img" in right_name_html.lower()

        if is_directory_row:
            directory_name = right_name or left_name
            current_dir = _normalize_rel_path(directory_name) if directory_name else None
            continue

        if not left_name and not right_name:
            continue

        parent_dir = current_dir if has_tree_marker else None
        item_name = right_name or left_name
        rel_path = _normalize_rel_path(f"{parent_dir}/{item_name}" if parent_dir else item_name)
        if not rel_path:
            continue

        if left_name and right_name:
            status = "changed"
        elif right_name:
            status = "only_current"
        else:
            status = "only_baseline"

        sections.append(HtmlReportSection(path=rel_path, status=status, changed_rows=1 if status == "changed" else 0))

        if not has_tree_marker:
            current_dir = None

    if not sections:
        return None

    title = _clean_cell(title_match.group(1)) if title_match else path.stem
    return _build_status_report(
        path,
        title,
        _extract_labeled_value(content, "Left base folder:"),
        _extract_labeled_value(content, "Right base folder:"),
        _extract_labeled_value(content, "Mode:"),
        sections,
    )


def _parse_winmerge_index_status_report(path: Path, content: str) -> dict[str, Any] | None:
    left_base, right_base = _extract_winmerge_compare_paths(content)
    if left_base is None or right_base is None or ".files/" not in content.lower():
        return None

    title_match = TITLE_RE.search(content)
    sections: list[HtmlReportSection] = []

    for row in TR_RE.findall(content):
        cells = TD_WITH_ATTR_RE.findall(row)
        if len(cells) < 3:
            continue

        href_match = HREF_RE.search(cells[0][1])
        if not href_match:
            continue

        filename = _clean_cell(cells[0][1])
        folder = _clean_cell(cells[1][1])
        rel_path = _normalize_rel_path(f"{folder}/{filename}" if folder else filename)
        status = _map_winmerge_status(_clean_cell(cells[2][1]))
        if status is None or not rel_path:
            continue

        sections.append(HtmlReportSection(path=rel_path, status=status, changed_rows=1 if status == "changed" else 0))

    if not sections:
        return None

    title = _clean_cell(title_match.group(1)) if title_match else path.stem
    return _build_status_report(path, title, left_base, right_base, "WinMerge folder compare", sections)


def parse_html_report_index(path: Path) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8", errors="replace")

    directory_summary = _parse_beyond_compare_directory_summary_index(path, content)
    if directory_summary is not None:
        return directory_summary

    if FILE_SECTION_RE.search(content):
        title_match = TITLE_RE.search(content)
        compares = _parse_folder_report(content, path)
        sections = [
            HtmlReportSection(
                path=compare.rel_path,
                status=_status_from_compare(compare),
                changed_rows=_count_changed_rows(compare.left_lines, compare.right_lines),
            )
            for compare in compares
            if compare.rel_path is not None
        ]
        if sections:
            title = _clean_cell(title_match.group(1)) if title_match else path.stem
            return _build_status_report(
                path,
                title,
                _extract_labeled_value(content, "Left base folder:"),
                _extract_labeled_value(content, "Right base folder:"),
                _extract_labeled_value(content, "Mode:"),
                sections,
            )

    winmerge_index = _parse_winmerge_index_status_report(path, content)
    if winmerge_index is not None:
        return winmerge_index

    raise ValueError(
        "Unsupported HTML diff report for --compare-html: expected a Beyond Compare file-detail report, a Beyond Compare directory-summary report, or a WinMerge summary index report."
    )


def build_text_report(left_name: str, right_name: str, left_lines: list[str], right_lines: list[str]) -> str:
    lines: list[str] = []
    lines.append(f"Left : {left_name}")
    lines.append(f"Right: {right_name}")
    lines.append("")

    max_rows = max(len(left_lines), len(right_lines))
    changes = 0

    for idx in range(max_rows):
        left = left_lines[idx] if idx < len(left_lines) else ""
        right = right_lines[idx] if idx < len(right_lines) else ""
        if left == right:
            continue

        changes += 1
        row_num = idx + 1
        lines.append(f"@@ row {row_num} @@")
        if left:
            lines.append(f"- {left}")
        else:
            lines.append("- <empty>")
        if right:
            lines.append(f"+ {right}")
        else:
            lines.append("+ <empty>")
        lines.append("")

    if changes == 0:
        lines.append("No differences found.")
    else:
        lines.append(f"Total changed rows: {changes}")

    return "\n".join(lines)


def build_unified_patch(left_name: str, right_name: str, left_lines: list[str], right_lines: list[str]) -> str:
    patch_lines = list(
        difflib.unified_diff(
            left_lines,
            right_lines,
            fromfile=left_name,
            tofile=right_name,
            lineterm="",
        )
    )
    if not patch_lines:
        return "# No differences found."
    return "\n".join(patch_lines)


def _rel_output_path(compare: HtmlCompare, report_stem: str, multi_compare: bool) -> Path:
    if compare.rel_path:
        rel_parts = _sanitize_parts(_split_path_parts(compare.rel_path))
        rel_path = Path(*rel_parts) if rel_parts else Path(report_stem)
    else:
        rel_path = Path(report_stem)
    if multi_compare:
        return Path(report_stem) / rel_path
    return rel_path


def _render_compare_output(compare: HtmlCompare, fmt: str) -> tuple[str | None, str | None]:
    text_report = None
    patch = None
    if fmt in {"text", "both"}:
        text_report = build_text_report(compare.left_name, compare.right_name, compare.left_lines, compare.right_lines)
    if fmt in {"patch", "both"}:
        patch = build_unified_patch(compare.left_name, compare.right_name, compare.left_lines, compare.right_lines)
    return text_report, patch


def _write_compare_outputs(out_dir: Path, report_stem: str, compares: list[HtmlCompare], fmt: str) -> int:
    ensure_directory(out_dir)
    multi_compare = len(compares) > 1
    written = 0

    for compare in compares:
        rel_output = _rel_output_path(compare, report_stem, multi_compare)
        text_report, patch = _render_compare_output(compare, fmt)

        if text_report is not None:
            text_path = out_dir / Path(f"{rel_output.as_posix()}.txt")
            ensure_directory(text_path.parent)
            text_path.write_text(text_report + "\n", encoding="utf-8")
            written += 1
        if patch is not None:
            patch_path = out_dir / Path(f"{rel_output.as_posix()}.patch")
            ensure_directory(patch_path.parent)
            patch_path.write_text(patch + "\n", encoding="utf-8")
            written += 1

    return written


def _combine_compare_outputs(compares: list[HtmlCompare], fmt: str) -> str:
    if fmt == "patch":
        return "\n\n".join(
            patch for compare in compares for _, patch in [_render_compare_output(compare, fmt)] if patch is not None
        )

    combined_parts: list[str] = []
    for compare in compares:
        label = compare.rel_path if compare.rel_path else compare.left_name
        text_report, patch = _render_compare_output(compare, fmt)
        section_parts: list[str] = [f"=== {label} ==="]
        if text_report is not None:
            section_parts.append(text_report)
        if patch is not None:
            section_parts.append(patch)
        combined_parts.append("\n\n".join(section_parts))
    return "\n\n".join(combined_parts)


def _single_output_text(text_report: str | None, patch: str | None) -> str:
    parts: list[str] = []
    if text_report is not None:
        parts.append(text_report)
    if patch is not None:
        parts.append(patch)
    return "\n\n".join(parts)


def _rebuild_all_compares(rebuild_root: Path, report_stem: str, compares: list[HtmlCompare]) -> int:
    rebuilt = 0
    for index, compare in enumerate(compares, start=1):
        stem = compare.rel_path.replace("/", "_") if compare.rel_path else f"{report_stem}_{index:04d}"
        write_rebuilt_pair(
            rebuild_root,
            stem,
            compare.left_name,
            compare.right_name,
            compare.left_lines,
            compare.right_lines,
        )
        rebuilt += 1
    return rebuilt


def iter_input_files(source: Path) -> Iterable[Path]:
    if source.is_file():
        yield source
        return

    for path in sorted(source.glob("*.html")):
        if path.name.lower().endswith(".html"):
            yield path


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _split_path_parts(value: str) -> list[str]:
    value = value.strip().replace("/", "\\")
    # Remove optional Windows drive prefix for a stable relative output path.
    value = re.sub(r"^[A-Za-z]:\\", "", value)
    parts = [p for p in value.split("\\") if p]
    return parts


def _sanitize_parts(parts: list[str]) -> list[str]:
    cleaned: list[str] = []
    for part in parts:
        # Keep names filesystem-safe across platforms.
        safe = re.sub(r'[<>:"/\\|?*]', "_", part)
        cleaned.append(safe)
    return cleaned


def _derive_rebuild_relpaths(left_name: str, right_name: str, stem: str) -> tuple[Path, Path]:
    left_parts = _split_path_parts(left_name)
    right_parts = _split_path_parts(right_name)

    prefix_len = 0
    for left_part, right_part in zip(left_parts, right_parts):
        if left_part.lower() == right_part.lower():
            prefix_len += 1
        else:
            break

    left_tail = left_parts[prefix_len:]
    right_tail = right_parts[prefix_len:]

    if not left_tail:
        left_tail = [f"{stem}.left.rebuilt"]
    if not right_tail:
        right_tail = [f"{stem}.right.rebuilt"]

    return Path(*_sanitize_parts(left_tail)), Path(*_sanitize_parts(right_tail))


def write_rebuilt_pair(
    rebuild_root: Path,
    stem: str,
    left_name: str,
    right_name: str,
    left_lines: list[str],
    right_lines: list[str],
) -> tuple[Path, Path]:
    left_rel, right_rel = _derive_rebuild_relpaths(left_name, right_name, stem)
    left_out = rebuild_root / left_rel
    right_out = rebuild_root / right_rel

    ensure_directory(left_out.parent)
    ensure_directory(right_out.parent)

    left_out.write_text("\n".join(left_lines) + ("\n" if left_lines else ""), encoding="utf-8")
    right_out.write_text("\n".join(right_lines) + ("\n" if right_lines else ""), encoding="utf-8")
    return left_out, right_out


def process_single_file(source: Path, fmt: str) -> tuple[str | None, str | None]:
    compares = parse_winmerge_html(source)
    if len(compares) != 1:
        raise ValueError("process_single_file only supports single-compare HTML inputs")
    return _render_compare_output(compares[0], fmt)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert supported WinMerge and Beyond Compare HTML diff reports into text reports or unified patches."
    )
    parser.add_argument("source", type=Path, help="Path to an HTML file or a folder of HTML files")
    parser.add_argument(
        "--format",
        choices=["text", "patch", "both"],
        default="both",
        help="Output format to generate",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path for single-file mode. If omitted, print to stdout.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        help="Output directory for folder mode or multi-file HTML export mode. Defaults to <source>/winmerge_export or <html-stem>_export.",
    )
    parser.add_argument(
        "--rebuild-sides",
        action="store_true",
        help="Rebuild and write full left/right file contents from the WinMerge HTML rows.",
    )
    parser.add_argument(
        "--rebuild-dir",
        type=Path,
        help="Directory where rebuilt left/right files are written. Defaults to <source>/winmerge_rebuilt.",
    )

    args = parser.parse_args()
    source = args.source

    if not source.exists():
        raise SystemExit(f"Source not found: {source}")

    if source.is_file():
        try:
            compares = parse_winmerge_html(source)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        if len(compares) == 1:
            text_report, patch = _render_compare_output(compares[0], args.format)
            combined = _single_output_text(text_report, patch)
            if args.output:
                ensure_directory(args.output.parent)
                args.output.write_text(combined + "\n", encoding="utf-8")
            else:
                print(combined)

            if args.rebuild_sides:
                rebuild_root = args.rebuild_dir if args.rebuild_dir else source.parent / "winmerge_rebuilt"
                left_out, right_out = write_rebuilt_pair(
                    rebuild_root,
                    source.stem,
                    compares[0].left_name,
                    compares[0].right_name,
                    compares[0].left_lines,
                    compares[0].right_lines,
                )
                print(f"Rebuilt left : {left_out}")
                print(f"Rebuilt right: {right_out}")
            return 0

        if args.output:
            ensure_directory(args.output.parent)
            args.output.write_text(_combine_compare_outputs(compares, args.format) + "\n", encoding="utf-8")
            print(f"Wrote combined multi-file report to: {args.output}")
        else:
            out_dir = args.out_dir if args.out_dir else source.parent / f"{source.stem}_export"
            written = _write_compare_outputs(out_dir, source.stem, compares, args.format)
            print(f"Processed {len(compares)} compare section(s) from: {source}")
            print(f"Wrote {written} output file(s) into: {out_dir}")

        if args.rebuild_sides:
            rebuild_root = args.rebuild_dir if args.rebuild_dir else source.parent / f"{source.stem}_rebuilt"
            rebuilt_count = _rebuild_all_compares(rebuild_root, source.stem, compares)
            print(f"Rebuilt left/right files for {rebuilt_count} compare section(s) into: {rebuild_root}")
        return 0

    out_dir = args.out_dir if args.out_dir else source / "winmerge_export"
    ensure_directory(out_dir)
    rebuild_root = args.rebuild_dir if args.rebuild_dir else source / "winmerge_rebuilt"
    rebuilt_count = 0

    html_files = list(iter_input_files(source))
    if not html_files:
        raise SystemExit(f"No .html files found in: {source}")

    for html_file in html_files:
        try:
            compares = parse_winmerge_html(html_file)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        _write_compare_outputs(out_dir, html_file.stem, compares, args.format)

        if args.rebuild_sides:
            rebuilt_count += _rebuild_all_compares(rebuild_root, html_file.stem, compares)

    print(f"Processed {len(html_files)} file(s) into: {out_dir}")
    if args.rebuild_sides:
        print(f"Rebuilt left/right files for {rebuilt_count} report(s) into: {rebuild_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
