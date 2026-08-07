---
name: tester_result_analyzer
description: Analyze standard tester result sources such as STDF-derived CSV and structured tester datalog TXT using generic summary, site-skew, and test-coverage modes.
metadata:
  status: beta
  language: python
---

# Tester Result Analyzer

Use `tester_result_analyzer.py` as the first generic analyzer built on top of `tester_result_core.py`.

This skill is for reusable result-table analysis, not product-specific judgment math.

## Purpose

- summarize standardized tester result tables
- report site distribution and site skew
- report test-ID coverage from result tables that expose numeric test columns

## Tool Entry Point

- Script: `.claude/skills/tester_result_analyzer/tester_result_analyzer.py`
- Preferred runner: `python`
- Working directory: workspace root

## When To Use

Use this skill when:

- the input is STDF-derived CSV or structured tester datalog TXT
- you want a first-pass generic summary before deeper analysis
- you want to inspect site skew or test-column coverage without writing a one-off script

Do not use this skill when:

- you need product-specific validation math such as relative ESM replay
- the input is an unstructured controller log
- the source format cannot be normalized into a result table

## Supported Modes

- `summary`
- `site-skew`
- `test-coverage`

## Standard Commands

### Summary on STDF-derived CSV

```powershell
python .claude/skills/tester_result_analyzer/tester_result_analyzer.py \
  references/stdf/uae7fc016ca01_996085vnrr_t96-test-cold_g_1.std.gextb.std.gextb.csv \
  --kind stdf_csv \
  --mode summary \
  --report-json
```

### Site skew on STDF-derived CSV

```powershell
python .claude/skills/tester_result_analyzer/tester_result_analyzer.py \
  references/stdf/uae7fc016ca01_996085vnrr_t96-test-cold_g_1.std.gextb.std.gextb.csv \
  --kind stdf_csv \
  --mode site-skew \
  --report-json
```

### Test coverage on STDF-derived CSV

```powershell
python .claude/skills/tester_result_analyzer/tester_result_analyzer.py \
  references/stdf/uae7fc016ca01_996085vnrr_t96-test-cold_g_1.std.gextb.std.gextb.csv \
  --kind stdf_csv \
  --mode test-coverage \
  --top 20 \
  --report-json
```

## Inputs

- result file path
- `--kind`: `stdf_csv`, `csv`, `xlsx`, or `tester_txt`
- `--mode`: `summary`, `site-skew`, or `test-coverage`
- optional `--sheet` and `--id-row` for table-based sources
- optional `--test-id` for site-skew by specific test ID
- preferred compact-JSON stdout flag: `--report-json` (`--json` remains accepted as a compatibility alias)

## Outputs

- human-readable summary by default
- JSON object with mode-specific details when `--report-json` is used

## Notes

- this is the first generic consumer of `.claude/skills/tester_result_core/tester_result_core.py`
- `site-skew` requires a `SITE` column in the normalized table
- `test-coverage` is most useful when the normalized table has an ID row with numeric test IDs
- `xlsx` mode depends on `openpyxl`, which should be installed in the local Python environment when needed
