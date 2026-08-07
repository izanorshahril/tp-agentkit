---
name: limit-population-screening
description: "Compare before/after .ls limits against population stats, emit keep-or-revert follow-up tables, and compare screening results across populations. Use when post-landing SPL review needs release-side screening from real .ls files rather than CSV-only evidence."
metadata:
  status: beta
  language: python
---

# Limit Population Screening

Use `limit_population_screening.py` to score changed `.ls` limits against one population stats CSV, derive row-level follow-up actions, and compare action tables across populations.

It also supports replaying one saved multi-step bundle from a config JSON when the repo wants a maintained rerun path for a retained artifact family.

## Purpose

- keep post-landing release screening anchored on the real before/after `.ls` files
- turn changed-limit rows into a repeatable verifier summary plus keep, revert, or manual-review actions
- compare two populations, such as GOODPOP versus ALLPOP, without treating either as literal release yield

## Use When

Use this skill when:

- approved SPL limits have already landed and the maintainer needs release-side screening from the actual `.ls`
- a changed-limit bundle needs a row-level keep or revert or manual-review table
- two screened populations need a diff view to show where action calls change

## Do Not Use When

- the task is still SPL or SPAT intake classification; use `spl-limit-workflow`
- the task is read-only CSV-versus-`.ls` comparison without population stats; use `spl-readonly-compare`
- the task is an actual `.ls` update; use `ls-updater`
- the request needs literal yield claims instead of projected screening output

## Tool Entry Point

- Script: `.claude/skills/limit-population-screening/limit_population_screening.py`
- Preferred runner: `python`
- Working directory: workspace root

## Standard Commands

### Verify changed limits against one population

```powershell
python .claude/skills/limit-population-screening/limit_population_screening.py verify --cases-json .claude/artifacts/current_task/limit_cases.json --stats-csv references/stats/<stats-file>.csv --dataset-label goodpop --output-json .claude/artifacts/current_task/limit_verify_goodpop.json --output-md .claude/artifacts/current_task/limit_verify_goodpop.md --report-json
```

### Build a follow-up action table

```powershell
python .claude/skills/limit-population-screening/limit_population_screening.py followup --verify-json .claude/artifacts/current_task/limit_verify_goodpop.json --membership-json .claude/artifacts/current_task/limit_membership.json --output-json .claude/artifacts/current_task/limit_followup_goodpop.json --output-md .claude/artifacts/current_task/limit_followup_goodpop.md --output-csv .claude/artifacts/current_task/limit_action_table_goodpop.csv --report-json
```

### Compare two populations

```powershell
python .claude/skills/limit-population-screening/limit_population_screening.py compare-populations --left-action-csv .claude/artifacts/current_task/limit_action_table_goodpop.csv --right-action-csv .claude/artifacts/current_task/limit_action_table_allpop.csv --left-label goodpop --right-label allpop --output-json .claude/artifacts/current_task/limit_population_compare.json --output-md .claude/artifacts/current_task/limit_population_compare.md --output-csv .claude/artifacts/current_task/limit_population_compare.csv --report-json
```

### Replay one saved bundle

```powershell
python .claude/skills/limit-population-screening/limit_population_screening.py replay-bundle --replay-json .claude/artifacts/current_task/example_replay.json --report-json
```

## Required Inputs

### `verify`

- `--cases-json`: JSON file with either `{"cases": [...]}` or a single case object
- each case needs `label`, `program`, `field`, `baseline_ls`, and `current_ls`
- `--stats-csv`: population statistics CSV with program, test number, unit, mean, and sigma columns

### `followup`

- `--verify-json`: output from the `verify` subcommand
- `--membership-json`: JSON map from case label to `bulk_csv` and optional `review_csv`

### `compare-populations`

- two action-table CSVs with matching `family` plus `test_id` keys

### `replay-bundle`

- one replay config JSON that points at the retained `cases_json`, `membership_json`, dataset runs, and comparison runs
- use this when the repo wants a maintained rerun path for a dated retained bundle without keeping the orchestration only in a shell wrapper

## Output Contract

### `verify`

- per-case changed-row summaries and row-level projections
- aggregate changed-row totals and projected incremental fallout summary
- optional markdown report and JSON artifact

### `followup`

- action-table CSV with `keep_candidate`, `revert_candidate`, and `manual_review_*` rows
- per-case scenario summaries and top offender tables
- optional markdown report and JSON artifact

### `compare-populations`

- diff CSV for matched action-table rows
- action-pair counts and change counts between the two populations
- optional markdown report and JSON artifact

### `replay-bundle`

- runs the listed verify, followup, and compare steps in one maintained call
- writes the configured artifacts to disk
- optional compact JSON summary of the bundle replay

## Limits And Failure Modes

- projected fail percentages are screening signals across changed rows, not literal one-pass yield
- the skill expects before and after `.ls` files to be the limit authority; it does not infer release truth from the source CSV alone
- duplicate test IDs remain lower-confidence because the parser follows the last matching occurrence in the `.ls`
- mismatched action-table keys between populations are treated as a hard error instead of guessed alignment
- unsupported stats headers or unreadable CSV files fail explicitly
- replay-bundle is only as reusable as the replay config; keep bundle-specific paths in the config, not hard-coded in the skill

## Agent Guidance

- load `spl_ls_updater_operational_rules.md` before using this skill for release-side interpretation
- keep population screening separate from updater behavior, CSV-schema decisions, and `.ls` write operations
- prefer this skill only after the landed `.ls` pair is known
- keep GOODPOP, ALLPOP, and real `.ls` questions separate when they answer different release questions