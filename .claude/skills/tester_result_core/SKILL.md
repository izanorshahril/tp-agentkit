---
name: tester_result_core
description: Read and normalize standard tester result sources such as STDF-derived CSV and structured tester datalog TXT into reusable result tables for higher-level analysis.
metadata:
  status: beta
  language: python
---

# Tester Result Core

Use `tester_result_core.py` as the shared ingestion and normalization layer for standard tester result sources.

This is a reusable core library, not a full end-user analyzer by itself. Other analyzers should import it rather than re-implement CSV or tester-datalog parsing logic.

## Purpose

- load STDF-derived CSV in the currently supported export shape
- load generic CSV and XLSX result tables
- load structured tester datalog TXT that can be normalized into repeated result rows
- provide shared ID extraction and column-resolution helpers

## Tool Entry Point

- Script/module: `.claude/skills/tester_result_core/tester_result_core.py`
- Preferred use: import from another analyzer script
- Working directory: workspace root

## When To Use

Use this core when:

- a skill needs to read Galaxy STDF-derived CSV
- a skill needs to read structured tester datalog TXT into reusable rows
- a skill needs common test-ID lookup or column-resolution helpers
- a new analyzer should share the same result-table parsing path as existing tools

Do not use this core when:

- the input is an unstructured log such as SystemController key-value logs
- the task is product-specific math or judgment logic rather than shared result parsing
- the input is raw binary STDF; this core currently targets derived tabular sources

## Exposed Helpers

- `parse_active_ids()`
- `normalize_cell()`
- `parse_float()`
- `parse_measurement_value()`
- `load_csv_blocks()`
- `load_stdf_result_table()`
- `load_result_table()`
- `load_table_csv()`
- `load_table_xlsx()`
- `load_tester_datalog_txt()`
- `resolve_column_index()`
- `ResultTable`

## ResultTable API

`ResultTable` is the first normalized table object in the shared core.

Current methods:

- `column_for_test_id()`
- `column_index()`
- `column_name()`
- `iter_rows()`
- `iter_rows_with_values()`

## Notes

- This Phase 1 core intentionally focuses on shared readers and helpers only.
- Phase 2 adds a normalized `ResultTable` object so analyzers can consume a stable table API rather than loose tuples.
- Phase 3 now adds `.claude/skills/tester_result_analyzer/` as the first generic analyzer built on top of this core.
- Higher-level analyzers should keep their own domain math, summaries, and presets.
- Current supported STDF-derived CSV shape is the `Parameter` / `Tests#` block already used by the relative ESM validator.
- XLSX loading requires `openpyxl`; install it in the local Python environment when XLSX support is needed.

