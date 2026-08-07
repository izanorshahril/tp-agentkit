from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path


COMPRESSIBLE_EXTENSIONS = {".md", ".txt", ".markdown", ".rst"}
CONFIG_EXTENSIONS = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env"}
SKIP_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".xml", ".css", ".scss",
    ".sql", ".csv", ".xls", ".xlsx", ".zip", ".7z", ".bat", ".ps1", ".sh",
    ".cpp", ".c", ".h", ".hpp", ".java", ".go", ".rs",
}

URL_REGEX = re.compile(r"https?://[^\s)]+")
MARKDOWN_LINK_REGEX = re.compile(r"\[[^\]]+\]\([^\)]+\)")
INLINE_CODE_REGEX = re.compile(r"`[^`\n]+`")
PATH_REGEX = re.compile(r"(?:\./|\.\./|/|[A-Za-z]:\\)[\w\-/\\\.]+|[\w\-.]+[/\\][\w\-/\\\.]+")
FENCE_OPEN_REGEX = re.compile(r"^(\s{0,3})(`{3,}|~{3,})(.*)$")
HEADING_REGEX = re.compile(r"^(#{1,6})\s+")
CHECKBOX_REGEX = re.compile(r"^(\s*[-*+]\s+\[[ xX]\]\s+)(.*)$")
BULLET_REGEX = re.compile(r"^(\s*[-*+]\s+)(.*)$")
NUMBERED_REGEX = re.compile(r"^(\s*\d+[.)]\s+)(.*)$")
HTML_LINE_REGEX = re.compile(r"^\s*<[^>]+>")
TABLE_SEPARATOR_REGEX = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")

CODE_LINE_PATTERNS = [
    re.compile(r"^\s*(import |from .+ import |require\(|const |let |var )"),
    re.compile(r"^\s*(def |class |function |async function |export )"),
    re.compile(r"^\s*@\w+"),
    re.compile(r"^\s*[\}\]\);]+\s*$"),
    re.compile(r'^\s*"[^"]+"\s*:\s*'),
]

START_REPLACEMENTS = [
    (re.compile(r"^please\s+", re.IGNORECASE), ""),
    (re.compile(r"^you should\s+", re.IGNORECASE), ""),
    (re.compile(r"^you may want to\s+", re.IGNORECASE), ""),
    (re.compile(r"^you may\s+", re.IGNORECASE), ""),
    (re.compile(r"^you can\s+", re.IGNORECASE), ""),
    (re.compile(r"^remember to\s+", re.IGNORECASE), ""),
    (re.compile(r"^make sure to\s+", re.IGNORECASE), "ensure "),
    (re.compile(r"^it is recommended to\s+", re.IGNORECASE), ""),
    (re.compile(r"^it may be helpful to\s+", re.IGNORECASE), ""),
]

PHRASE_REPLACEMENTS = [
    (re.compile(r"\bin order to\b", re.IGNORECASE), "to"),
    (re.compile(r"\bplease note that\b", re.IGNORECASE), ""),
    (re.compile(r"\bit is important to note that\b", re.IGNORECASE), ""),
    (re.compile(r"\bit is worth noting that\b", re.IGNORECASE), ""),
    (re.compile(r"\bdue to the fact that\b", re.IGNORECASE), "because"),
    (re.compile(r"\bthe reason is because\b", re.IGNORECASE), "because"),
    (re.compile(r"\bfor example\b", re.IGNORECASE), "e.g."),
    (re.compile(r"\bfor instance\b", re.IGNORECASE), "e.g."),
    (re.compile(r"\bin the event that\b", re.IGNORECASE), "if"),
    (re.compile(r"\bat this point in time\b", re.IGNORECASE), "now"),
    (re.compile(r"\ba large number of\b", re.IGNORECASE), "many"),
    (re.compile(r"\ba small number of\b", re.IGNORECASE), "few"),
    (re.compile(r"\bwith regard to\b", re.IGNORECASE), "for"),
    (re.compile(r"\butilize\b", re.IGNORECASE), "use"),
    (re.compile(r"\bmake sure to\b", re.IGNORECASE), "ensure"),
]

FILLER_PATTERNS = [
    re.compile(r"\bjust\b", re.IGNORECASE),
    re.compile(r"\breally\b", re.IGNORECASE),
    re.compile(r"\bbasically\b", re.IGNORECASE),
    re.compile(r"\bactually\b", re.IGNORECASE),
    re.compile(r"\bsimply\b", re.IGNORECASE),
    re.compile(r"\bessentially\b", re.IGNORECASE),
    re.compile(r"\bgenerally\b", re.IGNORECASE),
]

AGGRESSIVE_PHRASE_REPLACEMENTS = [
    (re.compile(r"\bapproximately\b", re.IGNORECASE), "about"),
    (re.compile(r"\badditional\b", re.IGNORECASE), "extra"),
    (re.compile(r"\binformation\b", re.IGNORECASE), "info"),
    (re.compile(r"\bconfiguration\b", re.IGNORECASE), "config"),
    (re.compile(r"\breference\b", re.IGNORECASE), "ref"),
    (re.compile(r"\breferences\b", re.IGNORECASE), "refs"),
    (re.compile(r"\brequirement\b", re.IGNORECASE), "req"),
    (re.compile(r"\brequirements\b", re.IGNORECASE), "reqs"),
]

ARTICLE_PATTERNS = [
    re.compile(r"\bthe\b", re.IGNORECASE),
    re.compile(r"\ba\b", re.IGNORECASE),
    re.compile(r"\ban\b", re.IGNORECASE),
]


@dataclass
class ValidationResult:
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.is_valid = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


def detect_newline(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def is_code_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return any(pattern.match(line) for pattern in CODE_LINE_PATTERNS)


def looks_like_yaml(lines: list[str]) -> bool:
    indicators = 0
    non_empty = 0
    for line in lines[:30]:
        stripped = line.strip()
        if not stripped:
            continue
        non_empty += 1
        if stripped == "---":
            indicators += 1
        elif re.match(r"^\w[\w\s-]*:\s", stripped):
            indicators += 1
        elif stripped.startswith("- ") and ":" in stripped:
            indicators += 1
    return non_empty > 0 and indicators / non_empty > 0.6


def detect_file_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in COMPRESSIBLE_EXTENSIONS:
        return "natural_language"
    if suffix in CONFIG_EXTENSIONS:
        return "config"
    if suffix in SKIP_EXTENSIONS:
        return "code"
    if suffix:
        return "unknown"

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return "unknown"

    lines = text.splitlines()
    if looks_like_yaml(lines):
        return "config"

    non_empty = [line for line in lines[:50] if line.strip()]
    if non_empty:
        code_like = sum(1 for line in non_empty if is_code_line(line))
        if code_like / len(non_empty) > 0.4:
            return "code"

    return "natural_language"


def should_compress(path: Path) -> bool:
    if not path.is_file():
        return False
    name = path.name.lower()
    if name.endswith(".original.md") or name.endswith(".original.txt"):
        return False
    return detect_file_type(path) == "natural_language"


def backup_path_for(path: Path) -> Path:
    if path.suffix.lower() == ".md":
        return path.with_name(path.stem + ".original.md")
    if path.suffix.lower() == ".txt":
        return path.with_name(path.stem + ".original.txt")
    if path.suffix:
        return path.with_name(path.stem + ".original" + path.suffix)
    return path.with_name(path.name + ".original.md")


def is_table_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if TABLE_SEPARATOR_REGEX.match(line):
        return True
    return stripped.count("|") >= 2


def protect_fragments(text: str) -> tuple[str, list[str]]:
    protected: list[str] = []
    patterns = [MARKDOWN_LINK_REGEX, INLINE_CODE_REGEX, URL_REGEX, PATH_REGEX]

    def make_replacer():
        def replacer(match: re.Match[str]) -> str:
            token = f"%%PROTECTED{len(protected)}%%"
            protected.append(match.group(0))
            return token
        return replacer

    updated = text
    for pattern in patterns:
        updated = pattern.sub(make_replacer(), updated)
    return updated, protected


def restore_fragments(text: str, protected: list[str]) -> str:
    restored = text
    for index, original in enumerate(protected):
        restored = restored.replace(f"%%PROTECTED{index}%%", original)
    return restored


def compress_inline_text(text: str, mode: str = "conservative") -> str:
    if not text.strip():
        return text

    protected_text, protected = protect_fragments(text)
    compact = protected_text.strip()

    for pattern, replacement in START_REPLACEMENTS:
        compact = pattern.sub(replacement, compact)
    for pattern, replacement in PHRASE_REPLACEMENTS:
        compact = pattern.sub(replacement, compact)
    for pattern in FILLER_PATTERNS:
        compact = pattern.sub("", compact)

    if mode == "aggressive":
        for pattern, replacement in AGGRESSIVE_PHRASE_REPLACEMENTS:
            compact = pattern.sub(replacement, compact)
        compact = re.sub(r"\band\b", "&", compact, flags=re.IGNORECASE)
        for pattern in ARTICLE_PATTERNS:
            compact = pattern.sub(" ", compact)

    compact = re.sub(r"\s{2,}", " ", compact)
    compact = re.sub(r"\s+([,.;:!?])", r"\1", compact)
    compact = compact.strip(" ")

    if compact and text.lstrip()[:1].isupper() and compact[:1].islower():
        compact = compact[0].upper() + compact[1:]

    restored = restore_fragments(compact, protected)
    restored = re.sub(r"\s{2,}", " ", restored)
    restored = re.sub(r"\s+([,.;:!?])", r"\1", restored)
    return restored.strip()


def wrap_paragraph(text: str, width: int = 100) -> list[str]:
    if not text:
        return []
    return textwrap.wrap(
        text,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    ) or [text]


def compress_markdown(text: str, mode: str = "conservative") -> str:
    newline = detect_newline(text)
    ends_with_newline = text.endswith(("\n", "\r\n"))
    lines = text.splitlines()

    output: list[str] = []
    paragraph_buffer: list[str] = []

    frontmatter_end = -1
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                frontmatter_end = index
                break

    cursor = 0
    if frontmatter_end >= 0:
        output.extend(lines[: frontmatter_end + 1])
        cursor = frontmatter_end + 1

    in_code_block = False
    fence_char = ""
    fence_len = 0

    def flush_paragraph() -> None:
        if not paragraph_buffer:
            return
        paragraph = " ".join(segment.strip() for segment in paragraph_buffer if segment.strip())
        paragraph_buffer.clear()
        compact = compress_inline_text(paragraph, mode=mode)
        output.extend(wrap_paragraph(compact))

    for line in lines[cursor:]:
        fence_match = FENCE_OPEN_REGEX.match(line)
        if in_code_block:
            output.append(line)
            if (
                fence_match
                and fence_match.group(2)[0] == fence_char
                and len(fence_match.group(2)) >= fence_len
                and not fence_match.group(3).strip()
            ):
                in_code_block = False
            continue

        if fence_match:
            flush_paragraph()
            output.append(line)
            in_code_block = True
            fence_char = fence_match.group(2)[0]
            fence_len = len(fence_match.group(2))
            continue

        if not line.strip():
            flush_paragraph()
            output.append("")
            continue

        if HEADING_REGEX.match(line) or is_table_line(line) or line.lstrip().startswith(">") or HTML_LINE_REGEX.match(line):
            flush_paragraph()
            output.append(line)
            continue

        checkbox_match = CHECKBOX_REGEX.match(line)
        if checkbox_match:
            flush_paragraph()
            output.append(checkbox_match.group(1) + compress_inline_text(checkbox_match.group(2), mode=mode))
            continue

        bullet_match = BULLET_REGEX.match(line)
        if bullet_match:
            flush_paragraph()
            output.append(bullet_match.group(1) + compress_inline_text(bullet_match.group(2), mode=mode))
            continue

        numbered_match = NUMBERED_REGEX.match(line)
        if numbered_match:
            flush_paragraph()
            output.append(numbered_match.group(1) + compress_inline_text(numbered_match.group(2), mode=mode))
            continue

        paragraph_buffer.append(line)

    flush_paragraph()

    compressed = newline.join(output)
    if ends_with_newline:
        compressed += newline
    return compressed


def extract_headings(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if HEADING_REGEX.match(line)]


def extract_code_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    lines = text.splitlines()
    current: list[str] = []
    in_block = False
    fence_char = ""
    fence_len = 0

    for line in lines:
        match = FENCE_OPEN_REGEX.match(line)
        if not in_block:
            if not match:
                continue
            in_block = True
            fence_char = match.group(2)[0]
            fence_len = len(match.group(2))
            current = [line]
            continue

        current.append(line)
        if (
            match
            and match.group(2)[0] == fence_char
            and len(match.group(2)) >= fence_len
            and not match.group(3).strip()
        ):
            blocks.append("\n".join(current))
            current = []
            in_block = False

    return blocks


def extract_urls(text: str) -> set[str]:
    return set(URL_REGEX.findall(text))


def extract_paths(text: str) -> set[str]:
    return set(PATH_REGEX.findall(text))


def validate_output(original: str, compressed: str) -> ValidationResult:
    result = ValidationResult()

    if extract_headings(original) != extract_headings(compressed):
        result.add_error("Heading set changed")

    if extract_code_blocks(original) != extract_code_blocks(compressed):
        result.add_error("Code blocks changed")

    original_urls = extract_urls(original)
    compressed_urls = extract_urls(compressed)
    if original_urls != compressed_urls:
        result.add_error(
            f"URL mismatch: lost={sorted(original_urls - compressed_urls)}, added={sorted(compressed_urls - original_urls)}"
        )

    original_paths = extract_paths(original)
    compressed_paths = extract_paths(compressed)
    if original_paths != compressed_paths:
        result.add_warning(
            f"Path mismatch: lost={sorted(original_paths - compressed_paths)}, added={sorted(compressed_paths - original_paths)}"
        )

    return result


def build_summary(input_path: Path, output_path: Path | None, original: str, compressed: str, result: ValidationResult) -> dict[str, object]:
    original_chars = len(original)
    compressed_chars = len(compressed)
    saved_chars = original_chars - compressed_chars
    saved_pct = 0.0 if original_chars == 0 else round(saved_chars / original_chars * 100, 2)
    return {
        "input": str(input_path),
        "output": str(output_path) if output_path else None,
        "original_chars": original_chars,
        "compressed_chars": compressed_chars,
        "saved_chars": saved_chars,
        "saved_pct": saved_pct,
        "valid": result.is_valid,
        "warnings": result.warnings,
        "errors": result.errors,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compact markdown or text artifacts locally without network access.")
    parser.add_argument("input", type=Path, help="Input markdown or text file")
    parser.add_argument("--output", type=Path, help="Write compacted text to a new file")
    parser.add_argument("--in-place", action="store_true", help="Overwrite the input file after writing a sibling backup")
    parser.add_argument(
        "--report-json",
        "--json",
        dest="report_json",
        action="store_true",
        help="Print one-line JSON summary. --json is kept as a compatibility alias.",
    )
    parser.add_argument("--no-validate", action="store_true", help="Skip structure validation before writing")
    parser.add_argument("--mode", choices=["conservative", "aggressive"], default="conservative", help="Compression mode")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    input_path = args.input.resolve()

    if not input_path.exists() or not input_path.is_file():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        return 1

    if input_path.parts and any(part.lower() == "testprogram" for part in input_path.parts):
        print("ERROR: refusing to compact files under testprogram/", file=sys.stderr)
        return 1

    if args.in_place and args.output:
        print("ERROR: use either --output or --in-place, not both", file=sys.stderr)
        return 1

    if args.report_json and not (args.output or args.in_place):
        print("ERROR: --report-json/--json requires --output or --in-place", file=sys.stderr)
        return 1

    if not should_compress(input_path):
        print(f"ERROR: unsupported or non-prose input: {input_path}", file=sys.stderr)
        return 1

    original = input_path.read_text(encoding="utf-8", errors="ignore")
    compressed = compress_markdown(original, mode=args.mode)

    if len(compressed) >= len(original):
        compressed = original

    validation = ValidationResult()

    if not args.no_validate:
        validation = validate_output(original, compressed)
        if not validation.is_valid:
            for error in validation.errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 2

    if compressed == original:
        validation.add_warning("No conservative savings detected; kept original content")

    output_path: Path | None = None
    if args.in_place:
        backup_path = backup_path_for(input_path)
        if backup_path.exists():
            print(f"ERROR: backup already exists: {backup_path}", file=sys.stderr)
            return 1
        backup_path.write_text(original, encoding="utf-8")
        input_path.write_text(compressed, encoding="utf-8")
        output_path = input_path
    elif args.output:
        output_path = args.output.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(compressed, encoding="utf-8")
    else:
        sys.stdout.write(compressed)
        return 0

    summary = build_summary(input_path, output_path, original, compressed, validation)
    summary["mode"] = args.mode
    if args.report_json:
        print(json.dumps(summary, ensure_ascii=True, separators=(",", ":")))
    else:
        print(f"Input:  {input_path}")
        print(f"Output: {output_path}")
        print(f"Mode:   {args.mode}")
        print(f"Saved:  {summary['saved_chars']} chars ({summary['saved_pct']}%)")
        if validation.warnings:
            print("Warnings:")
            for warning in validation.warnings:
                print(f"  - {warning}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())