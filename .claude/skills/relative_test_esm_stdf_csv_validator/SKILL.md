---
name: relative_test_esm_stdf_csv_validator
description: "Replay ESM relative-test behavior against STDF CSV exports and compare computed judge values to exported outputs."
metadata:
  status: beta
  language: python
---

# SKILL: Relative Test ESM STDF CSV Validator

## Purpose

Use `relative_test_esm_stdf_csv_validator.py` to replay an ESM relative-test implementation against STDF-extracted CSV data and compare computed judge values against exported `RelTest_*` results.

The same script can also bulk-validate 25x same-unit loop data across many source/judge pairs, reproducing the Excel workbook logic without manually pasting one pair at a time.

This skill is intended for proving whether a CSV export matches the active TP algorithm, not for changing TP code.

## Tool Entry Point

- Script: `.claude/skills/relative_test_esm_stdf_csv_validator/relative_test_esm_stdf_csv_validator.py`
- Preferred runner: `python`
- Working directory: workspace root

## When To Use

Use this skill when:
- a TP implements ESM relative testing in source code
- STDF-extracted CSVs contain both source-test measurements and relative judge outputs
- the user asks whether exported relative results are mathematically correct
- you need to compare self-inclusive updated-stat behavior versus historical-only expectations
- you have one wide 25x loop dataset and want to check many source/judge pairs in one run instead of manually pasting them into Excel

Do not use this skill when:
- the CSV does not contain usable `Tests#` mappings
- source/judge ID arrays are unknown
- only about 25 repeated loop results from the same unit are available and no STDF-style CSV replay data exists; use the workbook-based fallback described in `.claude/knowledge/relative_test_esm.md` or a local equivalent workbook capture
- the task is to modify TP code rather than validate data

## What It Does

- Parses active test ID and judge ID arrays from a TP header file
- Reads the STDF CSV from the `Parameter` row onward
- Maps columns by `Tests#`
- Replays the self-inclusive updated-stat algorithm per site and per pair
- Applies the same fallback and history-gate behavior used by the implementation
- Reports worst mismatches by pair, site, and part
- Optionally prints first-visible per-site spot checks
- In loop mode, reads one wide CSV/XLSX where columns are source/judge IDs and rows are repeated same-unit loop samples
- In loop mode, can also read tester datalog TXT files that contain repeated sample blocks and both main-test and `RelTest_*` lines
- Reproduces the workbook-style `D:M` logic in bulk, including inclusion, cumulative stats, deviation delta, and `CORRECT`/`INCORRECT` verdicts
- Treats the first loop as initialization history and starts meaningful relative-test comparison from the second run, matching the workbook example behavior

## Standard Commands

### Explicit validation

```powershell
python .claude/skills/relative_test_esm_stdf_csv_validator/relative_test_esm_stdf_csv_validator.py \
  --csv references/sample.csv \
  --list <path-to-Relative_TestID_JudgeID_Hot_List.h> \
  --test-symbol RelativeTestIDList_Hot \
  --judge-symbol RelativeJudgeIDList_Hot \
  --title HOT \
  --spot-check 70106:99970106 \
  --spot-check 704020:999704020
```

### Preset validation when a UR84 reference package is available

```powershell
python .claude/skills/relative_test_esm_stdf_csv_validator/relative_test_esm_stdf_csv_validator.py --preset ur84-hot
python .claude/skills/relative_test_esm_stdf_csv_validator/relative_test_esm_stdf_csv_validator.py --preset ur84-cold
```

These presets expect a local UR84 reference package, which is not retained in the current workspace snapshot.

### JSON summary for agent consumption

```powershell
python .claude/skills/relative_test_esm_stdf_csv_validator/relative_test_esm_stdf_csv_validator.py \
  --csv references/sample.csv \
  --list references/list.h \
  --test-symbol RelativeTestIDList \
  --judge-symbol RelativeJudgeIDList \
  --report-json
```

### Bulk 25x loop validation from one wide CSV

```powershell
python .claude/skills/relative_test_esm_stdf_csv_validator/relative_test_esm_stdf_csv_validator.py \
  --loop-csv references/loop_capture.csv \
  --list references/list.h \
  --test-symbol RelativeTestIDList \
  --judge-symbol RelativeJudgeIDList \
  --title LOOP \
  --top 20
```

### Bulk 25x loop validation from XLSX

```powershell
python .claude/skills/relative_test_esm_stdf_csv_validator/relative_test_esm_stdf_csv_validator.py \
  --loop-xlsx references/loop_capture.xlsx \
  --sheet LoopData \
  --list references/list.h \
  --test-symbol RelativeTestIDList \
  --judge-symbol RelativeJudgeIDList \
  --loop-id-row 1
```

### Bulk 25x loop validation directly from tester datalog TXT

```powershell
python .claude/skills/relative_test_esm_stdf_csv_validator/relative_test_esm_stdf_csv_validator.py \
  --loop-txt <path-to-25x-datalog.txt> \
  --list references/list.h \
  --test-symbol RelativeTestIDList_Hot \
  --judge-symbol RelativeJudgeIDList_Hot \
  --title HOT_TXT
```

## Inputs

- CSV path
- header/list file path containing source and judge arrays
- source test array symbol name
- judge array symbol name
- optional spot-check pairs in `testID:judgeID` form

Loop mode input expectations:

- one wide CSV or XLSX for the same unit's repeated loop data
- one column per source test and one column per relative judge test
- column IDs should match the numeric test/judge IDs, or contain them uniquely
- one row per loop sample
- the ID row defaults to the first row and can be changed with `--loop-id-row`
- the first loop is treated as initialization/history seed rather than a normal compared relative-test sample

TXT loop mode expectations:

- one tester datalog TXT containing repeated `***** Test Plan [...] Start ...` sample blocks
- each block should contain both the source test line and the matching `RelTest_*` line for the pair being checked
- values are parsed from the tester output text, so the same test should keep a consistent unit across the loop capture

## Outputs

- Human-readable mismatch summary
- Optional spot-check output by site
- Optional one-line JSON summary with matched pair count and max error
- In loop mode: per-pair verdict, correct/incorrect row counts, max deviation delta, and worst loop row

## Notes

- Current replay logic matches the self-inclusive updated-stat algorithm with fallback `999` and history gate `|z| < 15`.
- If the target TP uses a different algorithm, update the replay logic before trusting the results.
- Shared result-table readers are now factored into `.claude/skills/tester_result_core/tester_result_core.py`, including the normalized `ResultTable` API; this skill remains the domain-specific relative-test consumer of that core.
- This skill complements, but does not replace, the 25x same-unit workbook check described in `.claude/knowledge/relative_test_esm.md`; the original workbook used during earlier validation is not retained in the current workspace.
- CSV mode is stdlib-only. XLSX loop mode requires `openpyxl`, which should be installed in the local Python environment when needed.
- TXT loop mode can parse UR84-style datalog files directly, but a successful parse does not guarantee the capture starts at a clean relative-history boundary; if results look systematically shifted, review reset/start conditions before calling the TP math wrong.
- if the datalog prints a placeholder first relative value such as `0.000`, treat that first loop as initialization; the meaningful comparison still starts from the second run.
