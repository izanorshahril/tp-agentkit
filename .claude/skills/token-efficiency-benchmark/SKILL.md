---
name: token-efficiency-benchmark
description: "Use when measuring TP-AgentKit token and character savings from local compaction or compact machine-output changes, with optional local runtime-sanity evidence."
metadata:
  status: beta
  language: python
---

# Token Efficiency Benchmark

Use `token_efficiency_benchmark.py` to measure local token-efficiency impact from TP-AgentKit maintenance changes and to keep a small wall-clock sanity check on the maintained benchmark and harvest-generation paths.

## Purpose

- quantify character and proxy-token savings from compact artifact output
- measure compact JSON formatting wins without changing payload meaning
- keep a lightweight local wall-clock sanity signal for the maintained proof-refresh and harvest-generation paths
- generate a reproducible markdown report for repo-maintenance evidence

## Tool Entry Point

- Script: `.claude/skills/token-efficiency-benchmark/token_efficiency_benchmark.py`
- Preferred runner: `python`
- Working directory: workspace root

## When To Use

Use this skill when:

- validating a claim that a repo-maintenance change reduced prompt-input cost
- comparing compact versus baseline machine-output formatting
- refreshing a token-efficiency proof artifact after changing compaction or report formatting behavior

Do not use this skill when:

- working on `testprogram/` content
- you need an exact model tokenizer measurement rather than a local proxy
- the goal is code correctness rather than report-size efficiency

## What It Measures

- artifact compaction savings on representative current-task markdown files
- compact JSON output savings for selected maintained skills
- local wall-clock elapsed time for the benchmark self-refresh path and the temp-output session-harvest generation path
- character counts exactly
- token counts through the optional `tiktoken` `o200k_base` encoder when installed

## Output

- markdown report written to the path given by `--output-markdown`
- stdout report when `--output-markdown` is omitted
- runtime-sanity section included by default unless `--skip-runtime-sanity` is passed

## Standard Command

```powershell
python .claude/skills/token-efficiency-benchmark/token_efficiency_benchmark.py \
  --output-markdown .claude/artifacts/current_task/tp-agentkit-token-efficiency-proof-latest.md
```

## Validation Behavior

- runs the real local compactor against representative repo artifacts when present
- exercises compact JSON output paths through maintained skill entrypoints
- runs a local wall-clock sanity check for the benchmark self-refresh path and a temp-output Copilot session harvest path
- tolerates missing optional benchmark source artifacts by skipping those cases instead of failing the whole run
- tolerates missing local Copilot debug logs by marking the harvest runtime row as `skipped` instead of failing the whole report

## Dependency Surface

- token columns use `tiktoken` when it is installed in the local Python environment
- without `tiktoken`, token columns fall back to `n/a` while character metrics still run

## Limits

- token counts are a proxy, not an exact GPT-5.4 tokenizer guarantee
- runtime readings are local wall-clock only and are not a substitute for profiler-grade CPU or memory measurements
- results depend on the current repository artifact set and may shift as active artifacts change
- if `tiktoken` is not installed, token columns fall back to `n/a` while character metrics still run