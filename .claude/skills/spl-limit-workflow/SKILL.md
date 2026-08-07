---
name: spl-limit-workflow
description: "Classify SPL, SPAT, and Yield Explorer limit inputs into the safest TP-AgentKit next step. Use when reviewing or implementing approved YE limit exports into T2K .ls files without skipping TP safety anchors."
metadata:
  status: beta
  language: python
---

# SPL Limit Workflow

Use `spl_limit_workflow.py` to turn an SPL, SPAT, or Yield Explorer limit artifact into a narrow next-step decision.

This skill does not replace engineering approval or TP validation. It exists to keep SPL-driven limit work on the safe path before `ls-updater` is run.

## Purpose

- classify whether the provided input is an SPL CSV, SPAT CSV, workbook export, or review-only report
- keep unapproved limit material in review mode instead of jumping straight to TP edits
- require the missing anchors that matter before emitting a direct `ls-updater` command
- point maintainers at the matching TP-AgentKit knowledge notes for SPL work

## Use When

Use this skill when:

- a user says `implement SPL`, `SPAT limits`, `Yield Explorer`, or `YE export`
- you have an SPL or SPAT CSV and need to know whether the update is ready for `ls-updater`
- you have a workbook or report and need the next safe step before TP edits
- you want a machine-readable workflow summary for SPL limit-update intake

## Do Not Use When

- the task is already a confirmed `ls-updater` run with all anchors known
- the request is a generic TP diff, release audit, or non-limit TP change
- the user needs engineering judgment about whether the proposed SPL limits are correct for release

## Tool Entry Point

- Script: `.claude/skills/spl-limit-workflow/spl_limit_workflow.py`
- Preferred runner: `python`
- Working directory: workspace root

## Standard Commands

### Classify one approved SPL CSV

```powershell
python .claude/skills/spl-limit-workflow/spl_limit_workflow.py --input references/SPL/SPL.UAE7_FC_SPL_17April26.csv --source-tp testprogram/UAE7FC016CA01_0012 --ls testprogram/UAE7FC016CA01_0012/MainTestPlan/Main.ls --env FTC --approval-status approved --target-handling copied-revision --report-json
```

### Generate screened bulk and review CSVs

```powershell
python .claude/skills/spl-limit-workflow/spl_limit_workflow.py --input references/SPL/SPL.UAE7_FC_SPL_17April26.csv --source-tp testprogram/UAE7FC016CA01_0012 --ls testprogram/UAE7FC016CA01_0012/MainTestPlan/Main.ls --env FTC --approval-status approved --target-handling copied-revision --bulk-output .claude/artifacts/current_task/UAE7_FC_SPL_17April26.bulk.csv --review-output .claude/artifacts/current_task/UAE7_FC_SPL_17April26.review.csv --report-json
```

### Review a workbook export before TP edits

```powershell
python .claude/skills/spl-limit-workflow/spl_limit_workflow.py --input <path-to-approved-spl-export>.xlsx --report-json
```

## Output Contract

The compact JSON report includes these main sections:

- `status`
- `likely_mode`
- `workflow_stage`
- `ready_for_update`
- `detected_inputs`
- `primary_input`
- `schema_summary`
- `missing_anchors`
- `blockers`
- `recommended_follow_up`
- `recommended_command`
- `screened_outputs`
- `recommended_knowledge`
- `intake_checklist`
- `notes`

For recognized SPL CSV inputs, the primary input payload also carries `scope_screening` when row-level screening was possible.

When `--bulk-output` or `--review-output` is provided for an SPL CSV, `screened_outputs` includes:

- `bulk_path` and `review_path`
- `bulk_row_count` and `review_row_count`
- `bulk_ready_for_update`
- `screened_recommended_command`
- `review_reason_counts`

If the later updater rerun uses the emitted bulk CSV rather than the full reference CSV, keep or regenerate the matching full-input workflow report first. Bulk row counts are subset counts only and must not be reported as if they were the full reference CSV totals.

The screened export is now conservative in two ways:

- it excludes every row flagged by the SPL scope heuristics
- when target `.ls` and `--env` anchors are present, it also excludes rows that the target `.ls` cannot update cleanly, such as commented-out rows, rows absent from `Main.ls`, rows missing the target environment cell, or rows with structurally missing LL or UL fields in the target line

## Workflow Stages

- `ready_for_ls_updater`
  - a recognized SPL or SPAT CSV is present, the limits are approved, and the anchors needed for a safe `ls-updater` command are available
- `scope_review_needed`
  - the CSV is recognized and approved, but the row-level scope screen found test classes that should be excluded from a generic bulk SPL update or reviewed separately first
- `review_before_update`
  - a recognized update source exists, but approval is missing or not yet granted
- `export_csv_needed`
  - the source is a workbook export, so the next step is CSV export before `ls-updater`
- `ls_target_needed`, `env_confirmation_needed`, `source_tp_needed`, `target_handling_needed`
  - the update source is recognized, but one required anchor is still missing
- `review_source_only`
  - the inputs look like reports or review artifacts rather than direct update sources

## Limits And Failure Modes

- workbook or XLSX input is not applied directly; export the approved YE data to CSV first
- this skill does not edit the TP, does not call `ls-updater` for you, and does not imply approval
- real YE SPL CSVs may carry both `Scaled_LSL` or `Scaled_USL` and `Scaled_LSPL` or `Scaled_USPL`; the workflow treats the SPL pair as the default update source and the LSL or USL pair as context
- real SPL CSVs in this repo may also include a leading `Seq`, extra manual-review columns, and a fail-rate field that is absent or named `Fail%`, `%Fail`, or `Good Fail%`
- prefer the CSV `TestProgram` field over filename tokens when confirming the target variant; some repo examples use generic `FT` names while the `TestProgram` value is `FH`
- the row-level scope screen is intentionally lightweight and heuristic-based; it is a safety triage aid, not proof that every flagged row must be excluded forever
- the shared screen is tuned against real UAE7-style names such as `*_MATCH*`, `CONT_*_END`, `DELTA_*`, `KELVIN_*`, and temperature-logic rows
- the screened bulk export is still not a live TP write; it only materializes the safest known bulk subset and its paired review bucket
- a `ready_for_ls_updater` result still requires the normal `.ls` structure checks after the update
- unsupported or unreadable CSV files are reported, but the skill does not try to guess missing columns silently

## Agent Guidance

- use `spl_workflow_and_methodology.md` before planning SPL or SPAT work
- use `spl_reference_families.md` when the request starts from a filename and you need a quick read on header family or on whether the filename is weaker than `TestProgram`
- use this skill to keep the first move narrow: classify the artifact, approval state, and missing anchors before broader TP discovery
- if `scope_review_needed` is returned, prefer the maintained screened bulk or review split over hand-editing the raw CSV
- if a bulk rerun is later executed from a screened subset, keep the paired full-input workflow report and review CSV as provenance for the held-back rows
- only treat `recommended_command` as runnable after the target revision and `.ls` path are confirmed
- after any real `ls-updater` run, still audit occurrence counts, neighboring unchanged blocks, and the file tail or footer before sign-off