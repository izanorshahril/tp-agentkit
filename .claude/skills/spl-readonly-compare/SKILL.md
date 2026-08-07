---
name: spl-readonly-compare
description: "Use when reviewing an SPL CSV against a target .ls file without editing it, especially to split rows into active, commented, target-env-NA, absent, and non-comparable buckets before implementation."
metadata:
  status: beta
  language: python
---

# SPL Read-Only Compare

Use `spl_readonly_compare.py` to compare an SPL CSV against a target `.ls` file without modifying the TP.

This skill exists for pre-implementation review, scope triage, and review-bucket generation. It is not an updater.

## Purpose

- compare approved or candidate SPL CSV rows against a target `.ls` file in read-only mode
- split the old coarse `missing` concept into reviewable buckets that match real TP follow-up work
- surface active changed rows, active unchanged rows, commented rows, target-env-NA rows, absent rows, and active non-comparable rows
- embed the shared SPL scope screen so pre-update review and bulk-safety triage stay aligned

## Use When

Use this skill when:

- you need a read-only SPL versus `.ls` review before any TP edit
- the user asks why rows are `missing`, `not found`, `NA`, or otherwise not update-ready
- you want a machine-readable review report for `FTC`, `FTH`, or another target env cell in a UAE7-style `.ls`
- you need to separate `commented_in_ls`, `target_env_na`, `absent_from_main`, and `non_comparable` rows instead of treating them as one bucket

## Do Not Use When

- the task is already at the `ls-updater` execution step
- the user only needs SPL intake classification; use `spl-limit-workflow` first in that case
- the request is a whole-TP diff or a generic compare unrelated to SPL CSV rows

## Tool Entry Point

- Script: `.claude/skills/spl-readonly-compare/spl_readonly_compare.py`
- Preferred runner: `python`
- Working directory: workspace root

## Standard Commands

### Compare one SPL CSV against a target LS env cell

```powershell
python .claude/skills/spl-readonly-compare/spl_readonly_compare.py --csv references/SPL/SPL.UAE7_FC_SPL_17April26.csv --ls testprogram/UAE7FC016CA01_0012/MainTestPlan/Main.ls --env FTC --report-json
```

### Persist a reusable review report under artifacts

```powershell
python .claude/skills/spl-readonly-compare/spl_readonly_compare.py --csv references/SPL/SPL.UAE7_FC_SPL_17April26.csv --ls testprogram/UAE7FC016CA01_0012/MainTestPlan/Main.ls --env FTC --case-name "UAE7 FC FTC review" --output .claude/artifacts/spl_diff_fc_ftc_review.json --report-json
```

## Output Contract

The report includes these main fields:

- `status`
- `case`
- `env`
- `csv` and `ls`
- `csv_rows` and `rows_with_limits`
- `matched_rows`
- `changed_rows` and `unchanged_rows`
- `non_comparable_rows`
- `commented_in_ls`
- `target_env_na_rows`
- `absent_from_main_rows`
- `base_unit_mismatch_rows`, `partial_na_rows`, and `non_numeric_rows`
- `scope_screening`
- compact example arrays for each important bucket

If `--output` is provided, the report is also written to disk as pretty JSON and the payload includes `output`.

## Bucket Semantics

- `active_in_ls`: target env cell exists on an active row and is eligible for direct compare
- `commented_in_ls`: row exists but is commented out in `Main.ls`
- `target_env_na`: target env exists but the cell is `NA`
- `absent_from_main`: no matching `T...` row exists in `Main.ls`
- `non_comparable_rows`: target env exists but compare is blocked, for example by partial `NA`, non-numeric text, or true base-unit mismatch

## Limits And Failure Modes

- this skill is read-only and does not update the TP
- it currently expects an SPL-style CSV shape, not workbook input
- the compare is keyed by `TestNumber`; duplicate TIDs in the CSV are reported as ambiguous rather than merged silently
- a row can be active yet still non-comparable when one limit side is `NA` or non-numeric in the target env cell
- `matching_tests = 0` inside `scope_screening` does not prove the source CSV had no match-like names; it only describes the screened compare subset

## Agent Guidance

- use `spl_workflow_and_methodology.md` for SPL intent and approval context before planning edits
- use this skill before `ls-updater` when the user needs an explanation of what is directly update-ready versus held for review
- if the report shows `commented_in_ls`, `target_env_na`, `absent_from_main`, or `non_comparable_rows`, keep those rows out of the generic bulk update path until the user or engineering owner resolves them
- if the task later moves from review to implementation, pair this skill with `spl-limit-workflow` and then `ls-updater`