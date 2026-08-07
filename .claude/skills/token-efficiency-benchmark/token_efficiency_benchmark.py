from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import textwrap
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

try:
    import tiktoken
except ImportError:  # pragma: no cover
    tiktoken = None


REPO_ROOT = Path(__file__).resolve().parents[3]
SKILLS_ROOT = REPO_ROOT / ".claude" / "skills"
ARTIFACTS_ROOT = REPO_ROOT / ".claude" / "artifacts" / "current_task"
TOKEN_ENCODING_NAME = "o200k_base"
TOKEN_ENCODER = tiktoken.get_encoding(TOKEN_ENCODING_NAME) if tiktoken is not None else None


class TextMetrics(TypedDict):
    chars: int
    tokens: int | None


class JsonBenchmarkCase(TypedDict):
    tool: str
    baseline_style: str
    compact_text: str
    baseline_text: str


class RuntimeBenchmarkResult(TypedDict):
    case: str
    status: str
    exit_code: int | str
    elapsed_ms: float
    notes: str


def run_cli(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )


def text_metrics(text: str) -> TextMetrics:
    token_count = None
    if TOKEN_ENCODER is not None:
        token_count = len(TOKEN_ENCODER.encode(text))
    return {
        "chars": len(text),
        "tokens": token_count,
    }


def pct_saved(original: int, optimized: int) -> float:
    if original <= 0:
        return 0.0
    return round(((original - optimized) / original) * 100, 2)


def build_json_baseline(payload: object, style: str, ensure_ascii: bool = False) -> str:
    if style == "default":
        return json.dumps(payload, ensure_ascii=ensure_ascii)
    if style == "indent2":
        return json.dumps(payload, indent=2, ensure_ascii=ensure_ascii)
    raise ValueError(f"Unsupported JSON baseline style: {style}")


def benchmark_artifact_compaction() -> list[dict[str, object]]:
    script = SKILLS_ROOT / "local-artifact-compress" / "local_artifact_compress.py"
    results: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        bundle_path = temp_root / "maintainer-workflow-bundle.md"
        bundle_parts = [
            REPO_ROOT / "AGENTS.md",
            REPO_ROOT / ".claude" / "rules" / "workflows.md",
            ARTIFACTS_ROOT / "tp-agentkit-efficiency-cleanup-plan-20260413.md",
        ]
        bundle_text = "\n\n".join(path.read_text(encoding="utf-8") for path in bundle_parts if path.exists())
        bundle_path.write_text(bundle_text, encoding="utf-8")
        cases = [
            {
                "label": "diff-heavy",
                "path": ARTIFACTS_ROOT / "URX8_2222_13Jan2026-vs-URX8_0001-20260409.md",
                "display_name": "URX8_2222_13Jan2026-vs-URX8_0001-20260409.md",
                "modes": ["conservative", "aggressive"],
            },
            {
                "label": "prose-heavy",
                "path": ARTIFACTS_ROOT / "tp-agentkit-introduction-full-slides-20260408.md",
                "display_name": "tp-agentkit-introduction-full-slides-20260408.md",
                "modes": ["conservative", "aggressive"],
            },
            {
                "label": "current-task-artifact",
                "path": ARTIFACTS_ROOT / "tp-agentkit-efficiency-cleanup-plan-20260413.md",
                "display_name": "tp-agentkit-efficiency-cleanup-plan-20260413.md",
                "modes": ["conservative", "aggressive"],
            },
            {
                "label": "workflow-bundle",
                "path": bundle_path,
                "display_name": "maintainer-workflow-bundle.md",
                "modes": ["conservative", "aggressive"],
            },
        ]
        for case in cases:
            source_path = case["path"]
            if not source_path.exists():
                continue
            original_text = source_path.read_text(encoding="utf-8")
            original_metrics = text_metrics(original_text)
            for mode in case["modes"]:
                output_path = temp_root / f"{source_path.stem}.{mode}.md"
                result = run_cli(
                    script,
                    str(source_path),
                    "--output",
                    str(output_path),
                    "--mode",
                    mode,
                    "--report-json",
                )
                if result.returncode != 0:
                    raise RuntimeError(
                        f"artifact compaction failed for {source_path.name} ({mode})\n"
                        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                    )
                summary = json.loads(result.stdout.strip())
                compressed_text = output_path.read_text(encoding="utf-8")
                compressed_metrics = text_metrics(compressed_text)
                results.append(
                    {
                        "file": case["display_name"],
                        "kind": case["label"],
                        "mode": mode,
                        "original_chars": original_metrics["chars"],
                        "optimized_chars": compressed_metrics["chars"],
                        "saved_chars": original_metrics["chars"] - compressed_metrics["chars"],
                        "saved_chars_pct": pct_saved(original_metrics["chars"], compressed_metrics["chars"]),
                        "original_tokens": original_metrics["tokens"],
                        "optimized_tokens": compressed_metrics["tokens"],
                        "saved_tokens": None
                        if original_metrics["tokens"] is None or compressed_metrics["tokens"] is None
                        else original_metrics["tokens"] - compressed_metrics["tokens"],
                        "saved_tokens_pct": None
                        if original_metrics["tokens"] is None or compressed_metrics["tokens"] is None
                        else pct_saved(original_metrics["tokens"], compressed_metrics["tokens"]),
                        "valid": summary["valid"],
                        "warnings": summary["warnings"],
                    }
                )
    return results


def benchmark_local_artifact_json(temp_root: Path) -> JsonBenchmarkCase:
    script = SKILLS_ROOT / "local-artifact-compress" / "local_artifact_compress.py"
    input_path = temp_root / "artifact.md"
    output_path = temp_root / "artifact.compact.md"
    input_path.write_text(
        "# Title\n\nPlease note that this is a very simple paragraph in order to demonstrate how the tool can reduce filler wording.\n",
        encoding="utf-8",
    )
    result = run_cli(script, str(input_path), "--output", str(output_path), "--report-json")
    if result.returncode != 0:
        raise RuntimeError(f"local artifact compress json benchmark failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    compact_text = result.stdout.strip()
    payload = json.loads(compact_text)
    baseline_text = build_json_baseline(payload, "default", ensure_ascii=True)
    return {
        "tool": "local_artifact_compress",
        "baseline_style": "json.dumps(..., ensure_ascii=True)",
        "compact_text": compact_text,
        "baseline_text": baseline_text,
    }


def benchmark_pin_key_checker_json(temp_root: Path) -> JsonBenchmarkCase:
    script = SKILLS_ROOT / "pin_key_checker" / "pin_key_checker.py"
    tp_dir = temp_root / "tp"
    tpl_path = tp_dir / "SubTestPlans" / "sample.tpl"
    tpl_path.parent.mkdir(parents=True, exist_ok=True)
    tpl_path.write_text(
        textwrap.dedent(
            """\
            StorePinMeasurement {
                PinName = \"VBAT__NA_MMXHB_PMU\"
                MeasValue = \"VBAT_main\"
            }
            """
        ),
        encoding="utf-8",
    )
    result = run_cli(script, str(tp_dir), "--report-json")
    if result.returncode != 0:
        raise RuntimeError(f"pin key checker json benchmark failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    compact_text = result.stdout.strip()
    payload = json.loads(compact_text)
    baseline_text = build_json_baseline(payload, "default")
    return {
        "tool": "pin_key_checker",
        "baseline_style": "json.dumps(summary)",
        "compact_text": compact_text,
        "baseline_text": baseline_text,
    }


def benchmark_system_controller_json(temp_root: Path) -> JsonBenchmarkCase:
    script = SKILLS_ROOT / "system_controller_log_analyzer" / "log_analyzer_agent.py"
    log_path = temp_root / "system.log"
    log_path.write_text(
        textwrap.dedent(
            """\
            Time: Mon Apr 01 10:00:00 2026
            Status: FAIL
            ErrorCode: E001
            Routine: SampleRoutine
            Message: First failure
            File: Sample.cpp
            Line: 10
            """
        ),
        encoding="utf-8",
    )
    result = run_cli(script, str(log_path), "--report-json")
    if result.returncode != 0:
        raise RuntimeError(f"system controller json benchmark failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    compact_text = result.stdout.strip()
    payload = json.loads(compact_text)
    baseline_text = build_json_baseline(payload, "indent2")
    return {
        "tool": "system_controller_log_analyzer",
        "baseline_style": "json.dumps(report, indent=2)",
        "compact_text": compact_text,
        "baseline_text": baseline_text,
    }


def benchmark_ls_updater_json(temp_root: Path) -> JsonBenchmarkCase:
    script = SKILLS_ROOT / "ls-updater" / "ls_updater.py"
    csv_path = temp_root / "limits.csv"
    ls_path = temp_root / "sample.ls"
    csv_path.write_text(
        "Expression,Static Low Limit,Static High Limit,Expression Behavior\n"
        "P_12345 : TEST,0.5,1.5,Include\n",
        encoding="utf-8",
    )
    ls_path.write_text("12345, TEST, 0, V, [0.1, 1.0, 1]\n", encoding="utf-8")
    result = run_cli(
        script,
        "--csv",
        str(csv_path),
        "--ls",
        str(ls_path),
        "--env",
        "FTC",
        "--silent",
        "--in-place",
        "--report-json",
    )
    if result.returncode != 0:
        raise RuntimeError(f"ls updater json benchmark failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    compact_text = result.stdout.strip()
    payload = json.loads(compact_text)
    baseline_text = build_json_baseline(payload, "default", ensure_ascii=True)
    return {
        "tool": "ls_updater",
        "baseline_style": "json.dumps(payload, ensure_ascii=True)",
        "compact_text": compact_text,
        "baseline_text": baseline_text,
    }


def benchmark_json_outputs() -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        cases: list[JsonBenchmarkCase] = [
            benchmark_local_artifact_json(temp_root),
            benchmark_pin_key_checker_json(temp_root),
            benchmark_system_controller_json(temp_root),
            benchmark_ls_updater_json(temp_root),
        ]
        for case in cases:
            compact_metrics = text_metrics(case["compact_text"])
            baseline_metrics = text_metrics(case["baseline_text"])
            results.append(
                {
                    "tool": case["tool"],
                    "baseline_style": case["baseline_style"],
                    "compact_chars": compact_metrics["chars"],
                    "baseline_chars": baseline_metrics["chars"],
                    "saved_chars": baseline_metrics["chars"] - compact_metrics["chars"],
                    "saved_chars_pct": pct_saved(baseline_metrics["chars"], compact_metrics["chars"]),
                    "compact_tokens": compact_metrics["tokens"],
                    "baseline_tokens": baseline_metrics["tokens"],
                    "saved_tokens": None
                    if baseline_metrics["tokens"] is None or compact_metrics["tokens"] is None
                    else baseline_metrics["tokens"] - compact_metrics["tokens"],
                    "saved_tokens_pct": None
                    if baseline_metrics["tokens"] is None or compact_metrics["tokens"] is None
                    else pct_saved(baseline_metrics["tokens"], compact_metrics["tokens"]),
                    "single_line": "\n" not in case["compact_text"] and "\r" not in case["compact_text"],
                }
            )
    return results


def summarize_process_failure(stdout: str, stderr: str, limit: int = 180) -> str:
    collapsed = " ".join((stderr or stdout).split())
    if not collapsed:
        return "No stderr or stdout captured."
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: max(0, limit - 3)].rstrip() + "..."


def is_missing_harvest_log_case(stdout: str, stderr: str) -> bool:
    combined = f"{stdout}\n{stderr}"
    return (
        "Could not auto-detect a Copilot debug log root" in combined
        or "No session folders with main.jsonl found under:" in combined
    )


def benchmark_runtime_command(
    case: str,
    command: list[str],
    *,
    expected_outputs: list[Path] | None = None,
    timeout: int = 180,
    allow_skip: bool = False,
    success_notes: str,
) -> RuntimeBenchmarkResult:
    started = time.perf_counter()
    try:
        result = subprocess.run(
            command,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        elapsed_ms = round((time.perf_counter() - started) * 1000.0, 2)
        return {
            "case": case,
            "status": "timeout",
            "exit_code": "timeout",
            "elapsed_ms": elapsed_ms,
            "notes": f"Timed out after {timeout} seconds.",
        }

    elapsed_ms = round((time.perf_counter() - started) * 1000.0, 2)
    if result.returncode != 0:
        skipped = allow_skip and is_missing_harvest_log_case(result.stdout, result.stderr)
        return {
            "case": case,
            "status": "skipped" if skipped else "failed",
            "exit_code": result.returncode,
            "elapsed_ms": elapsed_ms,
            "notes": summarize_process_failure(result.stdout, result.stderr),
        }

    if expected_outputs:
        missing_outputs = [str(path.name) for path in expected_outputs if not path.exists()]
        if missing_outputs:
            return {
                "case": case,
                "status": "failed",
                "exit_code": result.returncode,
                "elapsed_ms": elapsed_ms,
                "notes": "Expected outputs missing: " + ", ".join(missing_outputs),
            }

    return {
        "case": case,
        "status": "ok",
        "exit_code": result.returncode,
        "elapsed_ms": elapsed_ms,
        "notes": success_notes,
    }


def benchmark_runtime_sanity() -> list[RuntimeBenchmarkResult]:
    results: list[RuntimeBenchmarkResult] = []
    benchmark_script = Path(__file__).resolve()
    harvest_script = SKILLS_ROOT / "copilot_session_log_harvester" / "copilot_session_log_harvester.py"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        proof_path = temp_root / "token-efficiency-proof.md"
        harvest_markdown = temp_root / "copilot-session-harvest.md"
        harvest_json = temp_root / "copilot-session-harvest.json"

        results.append(
            benchmark_runtime_command(
                "token_efficiency_benchmark",
                [
                    sys.executable,
                    str(benchmark_script),
                    "--skip-runtime-sanity",
                    "--output-markdown",
                    str(proof_path),
                ],
                expected_outputs=[proof_path],
                success_notes="Self-run with --skip-runtime-sanity to avoid recursive timing.",
            )
        )
        results.append(
            benchmark_runtime_command(
                "copilot_session_harvest",
                [
                    sys.executable,
                    str(harvest_script),
                    "--workspace-root",
                    str(REPO_ROOT),
                    "--markdown-output",
                    str(harvest_markdown),
                    "--json-output",
                    str(harvest_json),
                ],
                expected_outputs=[harvest_markdown, harvest_json],
                allow_skip=True,
                success_notes="Public harvest CLI writing temp outputs so rolling latest artifacts stay unchanged.",
            )
        )
    return results


def render_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def format_optional(value: object) -> str:
    if value is None:
        return "n/a"
    return str(value)


def format_elapsed_ms(value: object) -> str:
    if not isinstance(value, (int, float)):
        return "n/a"
    return f"{value:.2f}"


def build_markdown(
    artifact_results: list[dict[str, object]],
    json_results: list[dict[str, object]],
    runtime_results: list[RuntimeBenchmarkResult],
) -> str:
    artifact_rows = []
    for item in artifact_results:
        artifact_rows.append(
            [
                item["file"],
                item["kind"],
                item["mode"],
                item["original_chars"],
                item["optimized_chars"],
                item["saved_chars"],
                f"{item['saved_chars_pct']}%",
                format_optional(item["original_tokens"]),
                format_optional(item["optimized_tokens"]),
                format_optional(item["saved_tokens"]),
                "n/a" if item["saved_tokens_pct"] is None else f"{item['saved_tokens_pct']}%",
            ]
        )

    json_rows = []
    for item in json_results:
        json_rows.append(
            [
                item["tool"],
                item["baseline_style"],
                item["baseline_chars"],
                item["compact_chars"],
                item["saved_chars"],
                f"{item['saved_chars_pct']}%",
                format_optional(item["baseline_tokens"]),
                format_optional(item["compact_tokens"]),
                format_optional(item["saved_tokens"]),
                "n/a" if item["saved_tokens_pct"] is None else f"{item['saved_tokens_pct']}%",
                str(item["single_line"]).lower(),
            ]
        )

    runtime_rows = []
    for item in runtime_results:
        runtime_rows.append(
            [
                item["case"],
                item["status"],
                item["exit_code"],
                format_elapsed_ms(item["elapsed_ms"]),
                item["notes"],
            ]
        )

    lines = [
        "# TP-AgentKit Token Efficiency Proof",
        "",
        f"Date: {datetime.now(timezone.utc).date().isoformat()}",
        "Script: `.claude/skills/token-efficiency-benchmark/token_efficiency_benchmark.py`",
        "",
        "## Method",
        "",
        "- Character counts are exact.",
        f"- Token counts use `tiktoken` `{TOKEN_ENCODING_NAME}` as a proxy tokenizer for modern OpenAI-family models.",
        "- JSON benchmarks compare the current compact output against the previous formatting style used by each tool path.",
        "- Artifact benchmarks run the actual local compactor against representative current-task files.",
        "",
        "## Artifact Compaction Results",
        "",
        render_table(
            [
                "File",
                "Kind",
                "Mode",
                "Original Chars",
                "Compressed Chars",
                "Saved Chars",
                "Saved %",
                "Original Tokens",
                "Compressed Tokens",
                "Saved Tokens",
                "Saved Token %",
            ],
            artifact_rows,
        ),
        "",
        "## Machine JSON Output Results",
        "",
        render_table(
            [
                "Tool",
                "Baseline",
                "Baseline Chars",
                "Compact Chars",
                "Saved Chars",
                "Saved %",
                "Baseline Tokens",
                "Compact Tokens",
                "Saved Tokens",
                "Saved Token %",
                "Single Line",
            ],
            json_rows,
        ),
        "",
        "## Interpretation",
        "",
        "- The local artifact compressor gives measurable savings on prose-heavy artifacts and little gain on diff-heavy artifacts.",
        "- Compact machine JSON saves tokens deterministically because whitespace is removed without changing payload meaning.",
        "- The smoke suite now enforces single-line compact output for the updated machine-output paths, so that gain is regression-protected.",
        "- Runtime sanity is local wall-clock only; it helps catch obvious slowdowns in the maintained benchmark and harvest-generation paths, but it is not a full profiler and does not include peak-memory capture.",
        "- This is evidence of token reduction, but it is still a proxy benchmark rather than an exact GPT-5.4 tokenizer measurement.",
    ]
    if runtime_rows:
        interpretation_index = lines.index("## Interpretation")
        runtime_section = [
            "## Runtime Sanity Results",
            "",
            render_table(
                [
                    "Case",
                    "Status",
                    "Exit Code",
                    "Elapsed Ms",
                    "Notes",
                ],
                runtime_rows,
            ),
            "",
        ]
        lines[interpretation_index:interpretation_index] = runtime_section
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark TP-AgentKit token-efficiency changes.")
    parser.add_argument("--output-markdown", type=Path, help="Write the markdown report to this file")
    parser.add_argument(
        "--skip-runtime-sanity",
        action="store_true",
        help="Skip local wall-clock runtime sanity checks and report only token and character savings.",
    )
    args = parser.parse_args()

    artifact_results = benchmark_artifact_compaction()
    json_results = benchmark_json_outputs()
    runtime_results = [] if args.skip_runtime_sanity else benchmark_runtime_sanity()
    markdown = build_markdown(artifact_results, json_results, runtime_results)

    if args.output_markdown:
        output_path = args.output_markdown.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    else:
        sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())