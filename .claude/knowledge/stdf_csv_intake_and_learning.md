---
type: reference
status: partial
verifier: user-directed workflow plus repo sample cross-check
date: 2026-04-24
source: "user direction in chat; .claude/skills/grill-me/SKILL.md; .claude/artifacts/current_task/stdf-cross-device-layout-summary.md"
supplemental_source: "repo memory from prior STDF schema work, refreshed on 2026-04-24"
---

# STDF CSV Intake And Learning

Use this note when a user asks for STDF CSV analysis and the file structure is only partly known.

This note is about intake discipline and schema learning, not only about the currently verified STDF layout examples.

## Core Rule

- When STDF CSV structure is ambiguous, do not silently assign meaning to a header, row, or alias from weak clues.
- Use `grill-me` as the interactive questioning mode for these cases.
- Ask the user one schema question at a time when the workspace cannot safely prove the meaning.
- Separate location from meaning: it can be valid to locate a column while still requiring user confirmation of what that column means.

## What To Ask The User

Ask interactively when any of these are unclear from inspected evidence:

- which row is authoritative for limits such as `USL`, `LSL`, `HighL`, or `LowL`
- whether a header is metadata or a mapped test column
- whether a family-specific alias is equivalent to a known wafer, coordinate, unit, or limit field
- whether the STDF export family follows an existing known pattern or a device-specific variant
- whether a repeated or duplicated header name refers to the same semantic field or only shares text

Recommended pattern:

1. inspect the file enough to identify the exact unknown
2. ask one direct question
3. say why the assumption is unsafe
4. continue only after the user confirms the meaning or the repo proves it

## What Not To Ask

- do not ask the user for facts already recoverable from the file itself
- do not ask broad open-ended questions when the real uncertainty is one column, one row, or one alias block
- do not convert a schema question into a guess just because a similar family looked close enough

## Knowledge Promotion Rule

- If the user confirms a recurring STDF schema meaning that is likely reusable across tasks in this repo, promote that answer into durable knowledge.
- Prefer updating this note or another STDF-focused knowledge note over leaving the lesson only in task artifacts or transient chat context.
- Keep the promoted knowledge explicit about scope, for example family-specific rather than universal, when the answer may not generalize.

## User-Confirmed CmodeCode Mapping

The user confirmed this meaning for `CmodeCode` values used in the STDF CSV files in this repo:

- `T`: first test
- `C`: continue test if `T` was interrupted
- `R`: retest all 100%
- `F`: retest the rejects from `T` and `C`
- `G`: golden or finalized yield result from `T/C/R+F`

Use this mapping when interpreting the top-level `CmodeCode` field in STDF CSV exports unless a specific file family or tester flow proves a different meaning.

## Current Verified Wafer And X/Y Pattern

For the current STDF CSV families sampled in this repo:

- `WAFER_ID`, `DIE_X`, and `DIE_Y` behave as metadata or location columns, not mapped test-result columns.
- These columns have blank aligned entries in the `Tests#` row.
- Some families also carry later-position aliases for the same kind of location data.

Verified alias examples from the current sample set:

- UR7S family: `WaferNumber_NVM`, `X_coord`, `Y_coord`
- suae7ca5 family: `wasfer_ID`, `XCoord`, `YCoord`, `dieX`, `dieY`
- broader sample aliases: `ChipID_Wafer`, `ChipID_X`, `ChipID_Y`

Interpretation rule:

- a wafer or coordinate field can contain real per-part values in the data rows while still not being a mapped test column
- use the aligned `Tests#` row to distinguish metadata or location fields from true mapped test-result columns
- if a new family uses unclear wafer or coordinate aliases, ask the user before assigning meaning

## Current Alias Families

The current sampled files support a stronger reusable rule than a flat alias list.

Treat these as semantic families for metadata or location fields, not as proof that every matching header is a mapped test column.

Verified wafer-style aliases:

- `WAFER_ID`
- `WaferNumber_NVM`
- `wasfer_ID`
- `WfID_bef`
- `WFid_trimming`
- `WFID_MM_default`
- `WFID_MM_BC`
- `WFID_MM1`
- `WFID_MM2`
- `WFID_delta_1` to `WFID_delta_4`
- `ChipID_Wafer`

Verified X-coordinate-style aliases:

- `DIE_X`
- `X_coord`
- `XCoord`
- `dieX`
- `DieX_bef5_0`
- `dieX_MM_default`
- `dieX__MM_BC`
- `dieX__MM1`
- `dieX__MM2`
- `dieX_delta_1` to `dieX_delta_4`
- `ChipID_X`
- `X_offset`
- `ChipID_OX`

Verified Y-coordinate-style aliases:

- `DIE_Y`
- `Y_coord`
- `YCoord`
- `dieY`
- `DieY_bef5_0`
- `dieY_MM_default`
- `dieY__MM_BC`
- `dieY__MM1`
- `dieY__MM2`
- `dieY_delta_1` to `dieY_delta_4`
- `ChipID_Y`
- `Y_offset`
- `ChipID_OY`

Interpretation rule:

- use these groups as schema hints only
- still confirm metadata-versus-test meaning from the aligned `Tests#` row and column position
- if a new header looks similar but is not proven by the file, fall back to question-first intake instead of auto-classifying it from the alias family name alone

## Current Verified Baseline

- The current repo sample set still supports the `Parameter` plus aligned `Tests#` mapping rule documented in `.claude/artifacts/current_task/stdf-cross-device-layout-summary.md`.
- That baseline does not remove the need to ask the user when a new STDF family introduces unclear limit rows, aliases, or header semantics.

## Cross-Device Family Baseline

Across the current sampled families in this repo, the first mapped test column is the first nonblank `Tests#` entry immediately after `WAFER_ID`.

Verified family baselines:

- UR7S: first mapped header after `WAFER_ID` is `JOB_REV`, aligned to test `190`
- URX8: first mapped header after `WAFER_ID` is `JOB_REV`, aligned to test `90`
- UAE7FC, UAE7FH, and UAE7QC: first mapped header after `WAFER_ID` is `Dib_FT`, aligned to test `6`
- suae7ca5 or UAE7E: first mapped header after `WAFER_ID` is `Dib_EWS`, aligned to test `8`

This is a current family baseline, not a universal STDF rule. If a new file breaks it, fall back to the question-first intake rule instead of forcing the old pattern.

## Duplicate Header Safety Rule

Some STDF CSV files in this repo repeat header names within the same `Parameter` row.

Implication:

- do not parse by header-name uniqueness alone
- use column index plus the aligned `Tests#` value to identify the real mapped test column

Verified duplicate-header examples from the current sample set:

- UAE7FH repeats `OPEN_VCC3`, `OPEN_VADC`, `SHORT_VCC3`, and `SHORT_VADC`
- UR7S repeats `TM_WD_DIS` and `9913729_Spi_thermal_CK`
- UAE7FC and UAE7QC repeat `I_monkl30bs_off` and the `Ion_SENSE_LSL_2` or `Ion_SENSE_LSR_2` block

## Row-Value Interpretation Guard

When reading a CSV or STDF-derived row value, check the first column name before assigning meaning to later cells.

Why this matters:

- the same raw row can mix labels, units, limits, and values
- guessing from position alone can misread a unit or a test number as a wafer or limit value

Current verified guardrails from prior repo work:

- `LSB` is a unit, not a numeric limit
- `25` can be an upper-limit value and `1` can be a lower-limit value in the same mapped set; do not assume those numbers are metadata without checking the row authority first
- `80100` seen next to UR7S `WaferNumber_NVM` output is a test number, not proof of a wafer value

Operational rule:

- identify the authoritative row first
- then map each cell by that row's meaning rather than by a number pattern or nearby alias name