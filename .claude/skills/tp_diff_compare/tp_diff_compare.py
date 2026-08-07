from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DIFF_CONVERTER_DIR = Path(__file__).resolve().parents[1] / "diff-converter"
SKILLS_ROOT = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))
if str(DIFF_CONVERTER_DIR) not in sys.path:
    sys.path.insert(0, str(DIFF_CONVERTER_DIR))

from _io_support import iter_files  # noqa: E402
from html_diff_converter import parse_html_report_index  # noqa: E402


TEXT_EXTENSIONS = {
    ".bat",
    ".bdefs",
    ".cfg",
    ".cpp",
    ".csv",
    ".env",
    ".h",
    ".ini",
    ".log",
    ".ls",
    ".md",
    ".pat",
    ".ph",
    ".pin",
    ".pln",
    ".soc",
    ".spec",
    ".stpl",
    ".tf",
    ".tim",
    ".tpl",
    ".txt",
    ".xml",
}

NOISY_EXTENSIONS = {
    ".cache",
    ".dll",
    ".exp",
    ".idb",
    ".ilk",
    ".intellisense",
    ".ipch",
    ".lastbuildstate",
    ".lib",
    ".log",
    ".obj",
    ".pdb",
    ".res",
    ".sdf",
    ".suo",
    ".tlog",
}

RECOMMENDED_FILTER_EXTENSIONS = {".cpp", ".h", ".pat", ".ls", ".tpl", ".bdefs"}
RECOMMENDED_FILTER_GLOBS = {"*History.txt"}


@dataclass
class DiffEntry:
    path: str
    kind: str


def normalize_rel(path: Path) -> str:
    return path.as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_fs_path(value: str) -> str:
    return value.strip().replace("/", "\\").rstrip("\\").lower()


def build_html_cross_check(result: dict[str, Any], html_report: dict[str, Any], baseline: Path, current: Path) -> dict[str, Any]:
    live_status_by_path: dict[str, str] = {}
    for entry in result["changed"]:
        live_status_by_path[entry["path"]] = "changed"
    for rel_path in result["only_baseline"]:
        live_status_by_path[rel_path] = "only_baseline"
    for rel_path in result["only_current"]:
        live_status_by_path[rel_path] = "only_current"

    html_status_by_path = {section["path"]: section["status"] for section in html_report["sections"]}
    live_paths = set(live_status_by_path)
    html_paths = set(html_status_by_path)
    shared_paths = sorted(live_paths & html_paths)
    status_mismatches = sorted(
        path for path in shared_paths if live_status_by_path[path] != html_status_by_path[path]
    )

    html_left_base = html_report.get("left_base")
    html_right_base = html_report.get("right_base")
    baseline_path = normalize_fs_path(str(baseline.resolve()))
    current_path = normalize_fs_path(str(current.resolve()))

    return {
        "report_path": html_report["report_path"],
        "title": html_report["title"],
        "mode": html_report.get("mode"),
        "left_base": html_left_base,
        "right_base": html_right_base,
        "baseline_matches": normalize_fs_path(html_left_base) == baseline_path if html_left_base else None,
        "current_matches": normalize_fs_path(html_right_base) == current_path if html_right_base else None,
        "html_counts": html_report["counts"],
        "matching_paths": len(shared_paths),
        "missing_from_html": sorted(live_paths - html_paths),
        "html_only": sorted(html_paths - live_paths),
        "status_mismatches": [
            {
                "path": path,
                "live_status": live_status_by_path[path],
                "html_status": html_status_by_path[path],
            }
            for path in status_mismatches
        ],
    }


def html_cross_check_failures(html_cross_check: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    if html_cross_check["baseline_matches"] is False:
        failures.append("HTML left base folder does not match the requested baseline folder")
    if html_cross_check["current_matches"] is False:
        failures.append("HTML right base folder does not match the requested current folder")
    if html_cross_check["missing_from_html"]:
        failures.append(f"live delta has {len(html_cross_check['missing_from_html'])} path(s) missing from the HTML export")
    if html_cross_check["html_only"]:
        failures.append(f"HTML export has {len(html_cross_check['html_only'])} path(s) not present in the live delta")
    if html_cross_check["status_mismatches"]:
        failures.append(f"HTML export has {len(html_cross_check['status_mismatches'])} path(s) with status mismatches")

    return failures


def file_kind(rel_path: str) -> str:
    rel = Path(rel_path)
    return rel.suffix.lower() or rel.name


def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    with path.open("rb") as handle:
        sample = handle.read(4096)
    return b"\x00" not in sample


def decode_text(path: Path) -> list[str]:
    data = path.read_text(encoding="utf-8", errors="replace")
    return data.splitlines(keepends=True)


def matches_filters(path: Path, filter_exts: set[str], filter_globs: set[str]) -> bool:
    if not filter_exts and not filter_globs:
        return True
    if filter_exts and path.suffix.lower() in filter_exts:
        return True
    return any(path.match(pattern) or path.name == pattern for pattern in filter_globs)


def collect_files(root: Path, filter_exts: set[str], filter_globs: set[str]) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for candidate in iter_files(root):
        rel = candidate.relative_to(root)
        if matches_filters(rel, filter_exts, filter_globs):
            files[normalize_rel(rel)] = candidate
    return files


def is_generated_noise(rel_path: str) -> bool:
    normalized = rel_path.replace("\\", "/")
    ext = file_kind(rel_path)
    if ext in NOISY_EXTENSIONS:
        return True
    noisy_markers = (
        "ipch/",
        "/Debug/",
        "/x64/Debug/",
        "/bin/Debug/",
        "/lib/Debug/",
    )
    return any(marker in normalized for marker in noisy_markers) and ext not in {".cpp", ".h", ".inl"}


def bullet_list(items: list[str]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- `{item}`" for item in items]


def is_known_text_extension(rel_path: str) -> bool:
    return file_kind(rel_path) in TEXT_EXTENSIONS


def is_comparable_text_pair(baseline_root: Path, current_root: Path, rel_path: str) -> bool:
    baseline_file = baseline_root / rel_path
    current_file = current_root / rel_path
    if not baseline_file.exists() or not current_file.exists():
        return False
    if not is_known_text_extension(rel_path):
        return False
    return is_text_file(baseline_file) and is_text_file(current_file)


def trim_unified_diff(diff_text: str, max_hunks: int = 4, max_lines: int = 120) -> str:
    lines = diff_text.splitlines()
    if len(lines) <= max_lines:
        return diff_text

    if len(lines) <= 2:
        return diff_text

    header = lines[:2]
    body = lines[2:]
    hunk_blocks: list[list[str]] = []
    current_block: list[str] = []

    for line in body:
        if line.startswith("@@"):
            if current_block:
                hunk_blocks.append(current_block)
            current_block = [line]
        elif current_block:
            current_block.append(line)

    if current_block:
        hunk_blocks.append(current_block)

    trimmed: list[str] = header[:]
    line_count = len(header)
    shown_hunks = 0

    for block in hunk_blocks:
        if shown_hunks >= max_hunks or line_count >= max_lines:
            break

        remaining_capacity = max_lines - line_count
        if remaining_capacity <= 0:
            break

        if len(block) > remaining_capacity:
            trimmed.extend(block[:remaining_capacity])
            line_count += remaining_capacity
            shown_hunks += 1
            break

        trimmed.extend(block)
        line_count += len(block)
        shown_hunks += 1

    omitted_hunks = max(0, len(hunk_blocks) - shown_hunks)
    if line_count >= max_lines or omitted_hunks > 0:
        trimmed.append(f"... diff truncated: showing {shown_hunks} hunk(s), additional content omitted ...")

    return "\n".join(trimmed) + "\n"


def trimmed_diff_text(baseline_root: Path, current_root: Path, rel_path: str, context_lines: int = 3) -> str:
    diff_text = unified_diff_text(baseline_root, current_root, rel_path, context_lines)
    if not diff_text.strip():
        return "(no textual diff to display)\n"
    return trim_unified_diff(diff_text)


def render_detailed_file_compare(baseline: Path, current: Path, result: dict[str, Any], title: str) -> list[str]:
    lines: list[str] = []
    lines.append(f"## {title}")
    lines.append("")

    changed_entries = result["changed"]
    comparable_changed_entries = [entry for entry in changed_entries if is_comparable_text_pair(baseline, current, entry["path"])]
    skipped_changed_entries = [entry["path"] for entry in changed_entries if not is_comparable_text_pair(baseline, current, entry["path"])]
    comparable_only_baseline = [rel_path for rel_path in result["only_baseline"] if is_known_text_extension(rel_path)]
    comparable_only_current = [rel_path for rel_path in result["only_current"] if is_known_text_extension(rel_path)]
    skipped_only_baseline = [rel_path for rel_path in result["only_baseline"] if not is_known_text_extension(rel_path)]
    skipped_only_current = [rel_path for rel_path in result["only_current"] if not is_known_text_extension(rel_path)]

    if comparable_changed_entries:
        lines.append("### Changed File Content")
        lines.append("")
        lines.append("Contextual unified diffs are shown only for known text-comparable files. Large diffs are trimmed to the first few hunks.")
        lines.append("")
        for entry in comparable_changed_entries:
            rel_path = entry["path"]
            lines.append(f"#### `{rel_path}`")
            lines.append("")
            lines.append("```diff")
            lines.append(trimmed_diff_text(baseline, current, rel_path).rstrip("\n"))
            lines.append("```")
            lines.append("")
    else:
        lines.append("### Changed File Content")
        lines.append("")
        lines.append("No text-comparable changed files in this compare scope.")
        lines.append("")

    if comparable_only_baseline:
        lines.append("### Only-In-Baseline Files")
        lines.append("")
        for rel_path in comparable_only_baseline:
            lines.append(f"- `{rel_path}`")
        lines.append("")

    if comparable_only_current:
        lines.append("### Only-In-Current Files")
        lines.append("")
        for rel_path in comparable_only_current:
            lines.append(f"- `{rel_path}`")
        lines.append("")

    skipped_paths = skipped_changed_entries + skipped_only_baseline + skipped_only_current
    if skipped_paths:
        lines.append("### Ignored Non-Comparable Files")
        lines.append("")
        lines.append("These files were skipped from detailed compare because they are unknown-extension or not treated as text-comparable.")
        lines.append("")
        for rel_path in skipped_paths:
            lines.append(f"- `{rel_path}`")
        lines.append("")

    return lines


def render_compare_section(result: dict[str, Any], title: str) -> list[str]:
    counts = result["counts"]
    filters = result["filters"]
    changed_paths = [entry["path"] for entry in result["changed"]]
    changed_noise = [path for path in changed_paths if is_generated_noise(path)]
    changed_meaningful = [path for path in changed_paths if not is_generated_noise(path)]
    only_baseline_noise = [path for path in result["only_baseline"] if is_generated_noise(path)]
    only_current_noise = [path for path in result["only_current"] if is_generated_noise(path)]
    only_baseline_meaningful = [path for path in result["only_baseline"] if not is_generated_noise(path)]
    only_current_meaningful = [path for path in result["only_current"] if not is_generated_noise(path)]

    main_plan_changed = [path for path in changed_meaningful if path.startswith("MainTestPlan/")]
    source_changed = [
        path
        for path in changed_meaningful
        if path.startswith("TestFunctions/") and file_kind(path) in {".cpp", ".h", ".inl", ".vcxproj", ".filters"}
    ]
    history_changed = [path for path in changed_meaningful if Path(path).name.endswith("History.txt") or Path(path).name.endswith("History.txt.bak")]
    offline_added = [path for path in only_current_meaningful if path.startswith("OfflineData/")]
    support_added = [path for path in only_current_meaningful if path not in offline_added]

    changed_noise_by_type = Counter(file_kind(path) for path in changed_noise)
    only_baseline_noise_by_type = Counter(file_kind(path) for path in only_baseline_noise)
    only_current_noise_by_type = Counter(file_kind(path) for path in only_current_noise)

    lines: list[str] = []
    lines.append(f"## {title}")
    lines.append("")
    if filters["extensions"] or filters["globs"]:
        lines.append("### Filters")
        lines.append("")
        lines.append(f"- Filter extensions: `{', '.join(filters['extensions']) if filters['extensions'] else '<all>'}`")
        lines.append(f"- Filter globs: `{', '.join(filters['globs']) if filters['globs'] else '<all>'}`")
        lines.append("")
    lines.append("### Summary Counts")
    lines.append("")
    lines.append(f"- Baseline files: {counts['baseline_files']}")
    lines.append(f"- Current files: {counts['current_files']}")
    lines.append(f"- Shared files: {counts['shared_files']}")
    lines.append(f"- Changed files: {counts['changed_files']}")
    lines.append(f"- Only in baseline: {counts['only_baseline_files']}")
    lines.append(f"- Only in current: {counts['only_current_files']}")
    lines.append("")
    lines.append("### Meaningful TP Deltas")
    lines.append("")
    lines.append("#### Main Plan, Limits, and Bins")
    lines.append("")
    lines.extend(bullet_list(main_plan_changed))
    lines.append("")
    lines.append("#### Source and Framework Files")
    lines.append("")
    lines.extend(bullet_list(source_changed + [path for path in support_added if path.startswith("TestFunctions/")]))
    lines.append("")
    lines.append("#### History and Release Trace")
    lines.append("")
    lines.extend(bullet_list(history_changed))
    lines.append("")
    lines.append("#### Added Offline or Support Material In Current")
    lines.append("")
    lines.extend(bullet_list(offline_added + [path for path in support_added if not path.startswith("TestFunctions/")]))
    lines.append("")
    lines.append("### Changed File Types")
    lines.append("")
    for key, value in sorted(result["changed_by_type"].items()):
        lines.append(f"- `{key}`: {value}")
    lines.append("")
    lines.append("### Generated / Environment Noise")
    lines.append("")
    if changed_noise:
        lines.append("High-noise changed file types:")
        lines.append("")
        for key, value in sorted(changed_noise_by_type.items()):
            lines.append(f"- `{key}` changed: {value}")
        lines.append("")
        if only_baseline_noise_by_type:
            lines.append("Baseline-only noise by type:")
            lines.append("")
            for key, value in sorted(only_baseline_noise_by_type.items()):
                lines.append(f"- `{key}`: {value}")
            lines.append("")
        if only_current_noise_by_type:
            lines.append("Current-only noise by type:")
            lines.append("")
            for key, value in sorted(only_current_noise_by_type.items()):
                lines.append(f"- `{key}`: {value}")
            lines.append("")
    else:
        lines.append("No significant generated-noise patterns were detected.")
        lines.append("")
    lines.append("### Only-In-Baseline Meaningful Files")
    lines.append("")
    lines.extend(bullet_list(only_baseline_meaningful))
    lines.append("")
    lines.append("### Only-In-Current Meaningful Files")
    lines.append("")
    lines.extend(bullet_list(only_current_meaningful))
    lines.append("")
    return lines


def render_markdown_report(result: dict[str, Any]) -> str:
    baseline = Path(result["baseline"])
    current = Path(result["current"])
    recommended_result = compare_folders(baseline, current, RECOMMENDED_FILTER_EXTENSIONS, RECOMMENDED_FILTER_GLOBS)

    lines: list[str] = []
    lines.append(f"# {baseline.name} vs {current.name} TP Diff")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append(f"- Baseline: `{baseline.as_posix()}`")
    lines.append(f"- Current: `{current.as_posix()}`")
    lines.append("- Primary compare mode: whole-TP recursive compare")
    lines.append("- Tool: `.claude/skills/tp_diff_compare/tp_diff_compare.py`")
    lines.append("")
    lines.append("## Main Finding")
    lines.append("")
    lines.append(
        "This report contains both the whole-folder compare and the recommended engineering-filter compare, so one markdown file can support "
        "package-level folder audit and implementation-focused review together."
    )
    lines.append("")
    lines.extend(render_compare_section(result, "Whole-Folder Compare"))
    lines.append("## Recommended Engineering Filter Compare")
    lines.append("")
    lines.append("Recommended filter set:")
    lines.append("")
    lines.append("- `.cpp`")
    lines.append("- `.h`")
    lines.append("- `.pat`")
    lines.append("- `.ls`")
    lines.append("- `.tpl`")
    lines.append("- `.bdefs`")
    lines.append("- `*History.txt`")
    lines.append("")
    lines.extend(render_compare_section(recommended_result, "Recommended Filter Results"))
    lines.extend(render_detailed_file_compare(baseline, current, recommended_result, "Recommended Filter Detailed File Compare"))
    html_cross_check = result.get("html_cross_check")
    if html_cross_check:
        lines.append("## External HTML Cross-Check")
        lines.append("")
        lines.append(f"- Report: `{html_cross_check['report_path']}`")
        lines.append(f"- Title: `{html_cross_check['title']}`")
        lines.append(f"- Mode: `{html_cross_check['mode'] or '<unknown>'}`")
        lines.append(f"- HTML left base matches baseline: `{html_cross_check['baseline_matches']}`")
        lines.append(f"- HTML right base matches current: `{html_cross_check['current_matches']}`")
        lines.append(f"- Matching delta paths: {html_cross_check['matching_paths']}")
        lines.append(f"- Missing from HTML: {len(html_cross_check['missing_from_html'])}")
        lines.append(f"- HTML-only paths: {len(html_cross_check['html_only'])}")
        lines.append(f"- Status mismatches: {len(html_cross_check['status_mismatches'])}")
        lines.append("")
        if html_cross_check["missing_from_html"]:
            lines.append("### Live Delta Missing From HTML")
            lines.append("")
            lines.extend(bullet_list(html_cross_check["missing_from_html"]))
            lines.append("")
        if html_cross_check["html_only"]:
            lines.append("### HTML-Only Delta Paths")
            lines.append("")
            lines.extend(bullet_list(html_cross_check["html_only"]))
            lines.append("")
        if html_cross_check["status_mismatches"]:
            lines.append("### Status Mismatches")
            lines.append("")
            for mismatch in html_cross_check["status_mismatches"]:
                lines.append(
                    f"- `{mismatch['path']}`: live `{mismatch['live_status']}` vs HTML `{mismatch['html_status']}`"
                )
            lines.append("")
    lines.append("## Conclusion")
    lines.append("")
    lines.append(
        "Use the whole-folder section for completeness review and the recommended-filter section for engineering change review. "
        "If needed, rerun the skill with custom filters or unified diffs for a narrower follow-up."
    )
    lines.append("")
    return "\n".join(lines)


def write_markdown_report(report_path: Path, content: str) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8")


def compare_folders(baseline: Path, current: Path, filter_exts: set[str], filter_globs: set[str]) -> dict[str, Any]:
    baseline_files = collect_files(baseline, filter_exts, filter_globs)
    current_files = collect_files(current, filter_exts, filter_globs)

    baseline_set = set(baseline_files)
    current_set = set(current_files)

    only_baseline = sorted(baseline_set - current_set)
    only_current = sorted(current_set - baseline_set)
    shared = sorted(baseline_set & current_set)

    changed: list[DiffEntry] = []
    unchanged_by_type: Counter[str] = Counter()

    for rel in shared:
        base_file = baseline_files[rel]
        curr_file = current_files[rel]
        kind = file_kind(rel)
        if sha256_file(base_file) != sha256_file(curr_file):
            changed.append(DiffEntry(path=rel, kind=kind))
        else:
            unchanged_by_type[kind] += 1

    changed_by_type: Counter[str] = Counter(entry.kind for entry in changed)
    only_baseline_by_type: Counter[str] = Counter(file_kind(path) for path in only_baseline)
    only_current_by_type: Counter[str] = Counter(file_kind(path) for path in only_current)

    return {
        "baseline": str(baseline),
        "current": str(current),
        "filters": {
            "extensions": sorted(filter_exts),
            "globs": sorted(filter_globs),
        },
        "counts": {
            "baseline_files": len(baseline_files),
            "current_files": len(current_files),
            "shared_files": len(shared),
            "changed_files": len(changed),
            "only_baseline_files": len(only_baseline),
            "only_current_files": len(only_current),
        },
        "changed": [asdict(entry) for entry in changed],
        "only_baseline": only_baseline,
        "only_current": only_current,
        "changed_by_type": dict(changed_by_type),
        "only_baseline_by_type": dict(only_baseline_by_type),
        "only_current_by_type": dict(only_current_by_type),
        "unchanged_by_type": dict(unchanged_by_type),
    }


def unified_diff_text(baseline_root: Path, current_root: Path, rel_path: str, context_lines: int) -> str:
    baseline_file = baseline_root / rel_path
    current_file = current_root / rel_path
    if not is_text_file(baseline_file) or not is_text_file(current_file):
        return f"--- {rel_path}\n+++ {rel_path}\n(binary or non-text diff omitted)\n"
    baseline_lines = decode_text(baseline_file)
    current_lines = decode_text(current_file)
    diff_lines = difflib.unified_diff(
        baseline_lines,
        current_lines,
        fromfile=f"baseline/{rel_path}",
        tofile=f"current/{rel_path}",
        n=context_lines,
    )
    return "".join(diff_lines)


def print_human(result: dict[str, Any], baseline: Path, current: Path, show_diff: bool, context_lines: int) -> None:
    counts = result["counts"]
    filters = result["filters"]
    print("=== TP Diff Compare ===")
    print(f"Baseline={result['baseline']}")
    print(f"Current={result['current']}")
    print(f"FilterExt={','.join(filters['extensions']) if filters['extensions'] else '<all>'}")
    print(f"FilterGlob={','.join(filters['globs']) if filters['globs'] else '<all>'}")
    print(
        "Counts="
        f"baseline:{counts['baseline_files']} "
        f"current:{counts['current_files']} "
        f"shared:{counts['shared_files']} "
        f"changed:{counts['changed_files']} "
        f"only_baseline:{counts['only_baseline_files']} "
        f"only_current:{counts['only_current_files']}"
    )

    print("ChangedByType=")
    for key, value in sorted(result["changed_by_type"].items()):
        print(f"  {key}: {value}")

    print("ChangedFiles=")
    for entry in result["changed"]:
        print(f"  [{entry['kind']}] {entry['path']}")

    print("OnlyInBaseline=")
    for path in result["only_baseline"]:
        print(f"  {path}")

    print("OnlyInCurrent=")
    for path in result["only_current"]:
        print(f"  {path}")

    print("UnchangedByType=")
    for key, value in sorted(result["unchanged_by_type"].items()):
        print(f"  {key}: {value}")

    html_cross_check = result.get("html_cross_check")
    if html_cross_check:
        print("ExternalHtmlCrossCheck=")
        print(f"  Report={html_cross_check['report_path']}")
        print(f"  Title={html_cross_check['title']}")
        print(f"  Mode={html_cross_check['mode'] or '<unknown>'}")
        print(f"  HtmlLeftBase={html_cross_check['left_base'] or '<missing>'}")
        print(f"  HtmlRightBase={html_cross_check['right_base'] or '<missing>'}")
        print(f"  BaselineMatches={html_cross_check['baseline_matches']}")
        print(f"  CurrentMatches={html_cross_check['current_matches']}")
        print(f"  MatchingPaths={html_cross_check['matching_paths']}")
        print("  MissingFromHtml=")
        for rel_path in html_cross_check["missing_from_html"]:
            print(f"    {rel_path}")
        print("  HtmlOnly=")
        for rel_path in html_cross_check["html_only"]:
            print(f"    {rel_path}")
        print("  StatusMismatches=")
        for mismatch in html_cross_check["status_mismatches"]:
            print(
                f"    {mismatch['path']}: live={mismatch['live_status']} html={mismatch['html_status']}"
            )

    if show_diff:
        print("UnifiedDiffs=")
        for entry in result["changed"]:
            print(f"--- DIFF {entry['path']} ---")
            print(unified_diff_text(baseline, current, entry["path"], context_lines), end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Recursive compare for two TP folders with optional per-file unified text diffs.")
    parser.add_argument("--baseline", required=True, type=Path, help="Baseline folder")
    parser.add_argument("--current", required=True, type=Path, help="Current TP folder")
    parser.add_argument("--compare-html", type=Path, help="External HTML diff report to cross-check against the live folder delta set")
    parser.add_argument("--filter-ext", action="append", default=[], help="Restrict compare to an extension, e.g. .cpp")
    parser.add_argument("--filter-glob", action="append", default=[], help="Restrict compare to a filename glob, e.g. *History.txt")
    parser.add_argument("--show-diff", action="store_true", help="Print unified diffs for changed text files")
    parser.add_argument("--context-lines", type=int, default=3, help="Unified diff context lines")
    parser.add_argument("--report-json", action="store_true", help="Print one-line JSON summary")
    parser.add_argument("--report-markdown", type=Path, help="Write a markdown summary report to the given path")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    filter_exts = {value.lower() for value in args.filter_ext}
    filter_globs = set(args.filter_glob)

    result = compare_folders(args.baseline, args.current, filter_exts, filter_globs)
    html_failures: list[str] = []
    if args.compare_html:
        if not args.compare_html.exists():
            raise SystemExit(f"compare-html report not found: {args.compare_html}")
        try:
            html_report = parse_html_report_index(args.compare_html)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        result["html_cross_check"] = build_html_cross_check(result, html_report, args.baseline, args.current)
        html_failures = html_cross_check_failures(result["html_cross_check"])
    if args.report_markdown:
        write_markdown_report(args.report_markdown, render_markdown_report(result))
    if args.report_json:
        print(json.dumps(result, separators=(",", ":")))
    else:
        print_human(result, args.baseline, args.current, args.show_diff, args.context_lines)

    if html_failures:
        raise SystemExit("HTML cross-check failed: " + "; ".join(html_failures))


if __name__ == "__main__":
    main()