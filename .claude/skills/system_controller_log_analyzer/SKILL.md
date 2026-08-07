---
name: system_controller_log_analyzer
description: Parse SystemController log files into JSON summaries, Pareto counts, trends, and optional CSV export.
metadata:
  status: beta
  language: python
  source: tester-toolkit-t2k/under-dev/error-log-analyzer
---

# System Controller Log Analyzer

Use `log_analyzer_agent.py` to parse and analyze unstructured SystemController log files such as `.log`, `.txt`, and `.bak`.

This skill is intentionally narrow. It covers SystemController-style logs only.

## Purpose

- Parse messy SystemController logs into structured records.
- Produce machine-readable JSON summaries for agent consumption.
- Compute top error-code and routine Pareto summaries.
- Export parsed records to CSV when requested.

## Tool Entry Point

- Script: `.claude/skills/system_controller_log_analyzer/log_analyzer_agent.py`
- Preferred runner: `python`
- Working directory: workspace root

## When To Use

Use this skill when:
- the user asks to analyze a SystemController log
- the input file is `.log`, `.txt`, or `.bak` with key-value entries such as `Time`, `Status`, `Routine`, `ErrorCode`, and `Message`
- the user wants top errors, failure trends, or CSV export from such logs

Do not use this skill when:
- the user needs a generic ATE datalog parser
- the input is STDF, OTPL datalog, or another tester-native result format
- the log format is unrelated to SystemController key-value records

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | file path | Yes | Path to the SystemController log file |
| `output_csv` | file path | No | Optional CSV export path |

## Outputs

- JSON report with parsing health, time span, Pareto counts, and daily trend
- Optional CSV file of parsed records

## Standard Commands

### JSON summary only

```powershell
python .claude/skills/system_controller_log_analyzer/log_analyzer_agent.py references/log/SystemController_Error.log --report-json
```

### JSON summary with CSV export

```powershell
python .claude/skills/system_controller_log_analyzer/log_analyzer_agent.py references/log/SystemController_Error.log -o references/log/SystemController_Analysis.csv --report-json
```

Preferred compact-JSON stdout flag: `--report-json` (`--json` remains accepted as a compatibility alias).

## Returned JSON Shape

The tool returns a JSON object with these top-level sections:

- `status`
- `parsing_health`
- `context`
- `summary`
- `pareto`
- `trend`

## Agent Guidance

- Check `parsing_health.parse_confidence` first.
- If confidence is low, warn that the log format may not match the parser.
- Use `pareto.top_10_error_codes` and `pareto.top_10_routines` for first-pass root-cause direction.
- Treat this as a SystemController log parser, not as evidence that generic ATE log parsing is covered.