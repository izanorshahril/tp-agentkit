from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))

from _io_support import display_path, iter_scan_files


DEFAULT_EXTENSIONS = (".json", ".md", ".mdc", ".txt")
ROOT_FILENAMES = ("AGENTS.md", "README.md", "USER_WORKFLOW.md")
PATH_PREFIXES = (".claude/", "references/", "testprogram/")
PATH_START_TOKENS = tuple(sorted((*PATH_PREFIXES, *ROOT_FILENAMES), key=len, reverse=True))
PATH_START_PATTERN = re.compile("|".join(re.escape(token) for token in PATH_START_TOKENS))
HISTORICAL_MARKERS = (
    "historical input",
    "historical",
    "not retained",
    "not present in current workspace",
    "not present in the current workspace",
    "not present in this workspace",
    "workspace snapshot",
)
SEGMENT_PATTERNS = (
    re.compile(r"\]\(([^)\n]+)\)"),
    re.compile(r"`([^`]+)`"),
    re.compile(r'"([^"\n]+)"'),
    re.compile(r"'([^'\n]+)'"),
)
TRAILING_MARKERS = (" (", " --", " |", " ->", ", ")
OUTPUT_FLAGS = (
    "--output",
    "--json-output",
    "--markdown-output",
    "--closeout-output",
    "--report-markdown",
    "-o",
)
OUTPUT_FLAG_PATTERN = re.compile(
    r"(?:^|\s)(?P<flag>"
    + "|".join(re.escape(flag) for flag in sorted(OUTPUT_FLAGS, key=len, reverse=True))
    + r")\s+(?P<value>\"[^\"\n]+\"|'[^'\n]+'|`[^`\n]+`|\S+)"
)
OUTPUT_LINE_MARKERS = (
    "example artifact path:",
    "output folder:",
    "rebuilt folder:",
    "captured output:",
)
EXAMPLE_CONTEXT_MARKERS = (
    "for example",
    "e.g.",
    "good short starts",
    "analyze one sparse prompt",
    "machine-readable compact json",
    "prompt from a file",
    "example:",
)
GENERATED_CURRENT_TASK_BASENAMES = {"TASK.md", "plan.md", "walkthrough.md", "eval_report.md"}
PLACEHOLDER_BASENAMES = {
    "list.h",
    "prompt.txt",
    "sample.csv",
    "sample.txt",
    "sample.md",
    "loop_capture.csv",
    "loop_capture.xlsx",
}


@dataclass(frozen=True)
class Finding:
    source_file: str
    line: int
    path: str
    classification: str
    exists: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit docs and text artifacts for workspace-looking path literals."
    )
    parser.add_argument(
        "targets",
        nargs="*",
        default=["."],
        help="Files or directories to scan. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--workspace-root",
        default=".",
        help="Workspace root used to resolve relative path literals. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--extension",
        action="append",
        dest="extensions",
        help="Additional file extension to scan. Repeatable.",
    )
    parser.add_argument(
        "--report-json",
        action="store_true",
        help="Emit a compact JSON summary on stdout.",
    )
    return parser.parse_args()


def normalize_separators(text: str) -> str:
    return re.sub(r"[\\/]+", "/", text)


def normalize_candidate(raw: str) -> str | None:
    text = normalize_separators(raw.strip())
    text = html.unescape(text)
    start_positions: list[tuple[int, str]] = []

    for prefix in PATH_PREFIXES:
        index = text.find(prefix)
        if index >= 0:
            start_positions.append((index, prefix))
    for filename in ROOT_FILENAMES:
        index = text.find(filename)
        if index >= 0:
            start_positions.append((index, filename))

    if not start_positions:
        return None

    start, _ = min(start_positions, key=lambda item: item[0])
    candidate = text[start:]

    for marker in TRAILING_MARKERS:
        if marker in candidate:
            candidate = candidate.split(marker, 1)[0]

    candidate = re.sub(r"(?:\s+(?:and|with))+$", "", candidate.rstrip())

    if "#" in candidate:
        candidate = candidate.split("#", 1)[0]

    candidate = candidate.lstrip("`\"'(")
    candidate = candidate.rstrip("`\"'.,;:?)]}")
    candidate = normalize_separators(candidate)
    if not candidate:
        return None
    if candidate in ROOT_FILENAMES or candidate.startswith(PATH_PREFIXES):
        return candidate
    return None


def find_output_candidates(line: str) -> set[str]:
    output_candidates: set[str] = set()
    for match in OUTPUT_FLAG_PATTERN.finditer(line):
        candidate = normalize_candidate(match.group("value"))
        if candidate is not None:
            output_candidates.add(candidate)
    return output_candidates


def split_segment_candidates(segment: str) -> list[str]:
    text = normalize_separators(segment.strip())
    text = html.unescape(text)
    matches = list(PATH_START_PATTERN.finditer(text))
    if not matches:
        return [text]

    pieces: list[str] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        pieces.append(text[match.start():end].strip())
    return pieces


def path_family(path: str) -> str:
    if path in ROOT_FILENAMES:
        return path
    return path.split("/", 1)[0]


def historical_context_applies(path: str, context_lines: list[str]) -> bool:
    if any(marker in context_lines[-1].lower() for marker in HISTORICAL_MARKERS):
        return True

    current_family = path_family(path)
    marker_seen = False
    families_since_marker: list[str] = []

    for context_line in context_lines[:-1]:
        lower_line = context_line.lower()
        if any(marker in lower_line for marker in HISTORICAL_MARKERS):
            marker_seen = True
            families_since_marker = []
            continue
        if not marker_seen:
            continue
        for candidate in extract_candidates_from_line(context_line):
            families_since_marker.append(path_family(candidate))

    if not marker_seen:
        return False
    if not families_since_marker:
        return True
    return all(family == current_family for family in families_since_marker)


def extract_candidates_from_line(line: str) -> list[str]:
    raw_segments: list[str] = []
    masked_line = list(line)
    for pattern in SEGMENT_PATTERNS:
        for match in pattern.finditer(line):
            raw_segments.append(match.group(1))
            start, end = match.span()
            for index in range(start, end):
                masked_line[index] = " "
    raw_segments.extend("".join(masked_line).split())

    candidates: list[str] = []
    seen: set[str] = set()
    for segment in raw_segments:
        decoded_segment = html.unescape(segment)
        for part in decoded_segment.split(";"):
            for candidate_part in split_segment_candidates(part):
                candidate = normalize_candidate(candidate_part)
                if candidate is None or candidate in seen:
                    continue
                seen.add(candidate)
                candidates.append(candidate)
    return candidates


def example_context_applies(path: str, context_lines: list[str]) -> bool:
    current_family = path_family(path)
    if current_family not in {".claude", "references", "testprogram", *ROOT_FILENAMES}:
        return False
    lower_context = "\n".join(item.lower() for item in context_lines)
    return any(marker in lower_context for marker in EXAMPLE_CONTEXT_MARKERS)


def classify_candidate(
    path: str,
    line: str,
    context_lines: list[str],
    workspace_root: Path,
    output_candidates: set[str],
    source_path: Path,
) -> tuple[str, bool]:
    lower_line = line.lower()
    source_path_str = normalize_separators(str(source_path))
    is_archive_source = source_path_str.startswith(".claude/artifacts/archive/") or "/.claude/artifacts/archive/" in source_path_str
    basename = Path(path).name
    if "<" in path or ">" in path or "*" in path:
        return "placeholder", False
    if basename in PLACEHOLDER_BASENAMES:
        return "placeholder", False
    if path.startswith(".claude/artifacts/current_task/") and basename in GENERATED_CURRENT_TASK_BASENAMES:
        return "output_path", False
    if path in output_candidates:
        return "output_path", False
    if path.startswith("references/_tmp"):
        return "output_path", False
    if any(marker in lower_line for marker in OUTPUT_LINE_MARKERS) and (
        path.startswith(".claude/artifacts/current_task/") or path.startswith("references/_tmp")
    ):
        return "output_path", False
    if source_path_str.endswith("/SKILL.md") and path.startswith(".claude/artifacts/current_task/"):
        return "placeholder", False
    if example_context_applies(path, context_lines):
        return "placeholder", False
    if historical_context_applies(path, context_lines):
        return "historical", False

    exists = (workspace_root / Path(path)).exists()
    if is_archive_source and not exists:
        return "historical", False

    if exists:
        return "existing", True
    return "missing", False
def audit_files(files: list[Path], workspace_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for file_path in files:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        source_file = display_path(file_path, workspace_root)
        lines = text.splitlines()
        for line_number, line in enumerate(lines, start=1):
            output_candidates = find_output_candidates(line)
            context_lines = lines[max(0, line_number - 3):line_number]
            for candidate in extract_candidates_from_line(line):
                classification, exists = classify_candidate(
                    candidate,
                    line,
                    context_lines,
                    workspace_root,
                    output_candidates,
                    file_path,
                )
                findings.append(
                    Finding(
                        source_file=source_file,
                        line=line_number,
                        path=candidate,
                        classification=classification,
                        exists=exists,
                    )
                )
    return findings


def build_payload(files: list[Path], findings: list[Finding], workspace_root: Path) -> dict[str, object]:
    counts = Counter(finding.classification for finding in findings)
    summary_counts = {
        "existing": counts.get("existing", 0),
        "historical": counts.get("historical", 0),
        "missing": counts.get("missing", 0),
        "output_path": counts.get("output_path", 0),
        "placeholder": counts.get("placeholder", 0),
    }
    unresolved = [
        asdict(finding)
        for finding in findings
        if finding.classification == "missing"
    ]
    return {
        "status": "success",
        "workspace_root": workspace_root.resolve().as_posix(),
        "scanned_files": len(files),
        "candidates": len(findings),
        "counts": summary_counts,
        "unresolved_count": len(unresolved),
        "unresolved": unresolved,
    }


def print_human_summary(payload: dict[str, object]) -> None:
    counts = payload["counts"]
    assert isinstance(counts, dict)
    print(f"Scanned files: {payload['scanned_files']}")
    print(f"Candidates: {payload['candidates']}")
    print(
        "Counts: "
        f"existing={counts['existing']} "
        f"missing={counts['missing']} "
        f"historical={counts['historical']} "
        f"placeholder={counts['placeholder']} "
        f"output_path={counts['output_path']}"
    )
    unresolved = payload["unresolved"]
    assert isinstance(unresolved, list)
    if not unresolved:
        print("Unresolved missing paths: none")
        return
    print("Unresolved missing paths:")
    for item in unresolved:
        assert isinstance(item, dict)
        print(f"- {item['source_file']}:{item['line']} -> {item['path']}")


def main() -> int:
    args = parse_args()
    raw_extensions = {str(ext) for ext in (*(args.extensions or []), *DEFAULT_EXTENSIONS)}
    extensions = tuple(sorted(ext if ext.startswith(".") else f".{ext}" for ext in raw_extensions))
    workspace_root = Path(args.workspace_root).resolve()
    files = iter_scan_files(args.targets, tuple(ext.lower() for ext in extensions))
    findings = audit_files(files, workspace_root)
    payload = build_payload(files, findings, workspace_root)

    if args.report_json:
        print(json.dumps(payload, ensure_ascii=True, separators=(",", ":")))
    else:
        print_human_summary(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())