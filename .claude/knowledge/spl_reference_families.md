---
type: reference
status: partial
verifier: repo reference CSV cross-check
date: 2026-04-23
source: "references/SPL/SPL.UAE7_FC_SPL_17April26.csv; references/SPL/SPL.UAE7_FH_SPL_16April26.csv; references/SPL/SPL.SPL_UR7B_FT.20251030_170637.csv; references/SPL/SPL.SPL_UR7E_FT_300K_12Nov25.20251112_102355_Update.csv; references/SPL/SPL.UR6E_FT_SPL_300K.20251028_105041.csv; references/SPL/SPL_UBE6_FT_Rev_0014_<reviewer>_Final.csv"
---

# SPL Reference Families

Quick grouping for the SPL CSV families currently retained under `references/SPL/`.

Use this note when a new SPL request starts from a filename and you want the fastest safe read on:

- which header family it most likely belongs to
- whether the fail-rate field is present and how it is labeled
- whether the filename can be trusted as the target-variant hint

This note complements `spl_csv_schema.md`.

- `spl_csv_schema.md` explains column semantics and update-source rules
- this note groups the actual repo examples into recognizable families for faster intake and safer variant matching

## 1. Verified Files

- `references/SPL/SPL.UAE7_FC_SPL_17April26.csv`
- `references/SPL/SPL.UAE7_FH_SPL_16April26.csv`
- `references/SPL/SPL.SPL_UR7B_FT.20251030_170637.csv`
- `references/SPL/SPL.SPL_UR7E_FT_300K_12Nov25.20251112_102355_Update.csv`
- `references/SPL/SPL.UR6E_FT_SPL_300K.20251028_105041.csv`
- `references/SPL/SPL_UBE6_FT_Rev_0014_<reviewer>_Final.csv`

## 2. Header Families

| Family | Files | Distinguishing columns | Fail-rate field | Intake note |
|------|------|------|------|------|
| standard_core_fail_percent | `SPL.UAE7_FC_SPL_17April26.csv` | standard SPL core header only | `Fail%` | direct YE-style export with an explicit fail-rate field |
| standard_core_percent_fail | `SPL.UAE7_FH_SPL_16April26.csv`; `SPL.SPL_UR7E_FT_300K_12Nov25.20251112_102355_Update.csv`; `SPL.UR6E_FT_SPL_300K.20251028_105041.csv` | standard SPL core header only | `%Fail` | same core family as UAE7 FC, but with the alternate fail-rate label |
| standard_core_no_fail_field | `SPL.SPL_UR7B_FT.20251030_170637.csv` | standard SPL core header only | absent | do not assume missing fail-rate means the file is not an SPL export |
| extended_manual_review | `SPL_UBE6_FT_Rev_0014_<reviewer>_Final.csv` | leading `Seq` plus `suggested LSL`, `suggested USL`, `LSLCheck`, `USLCheck`, `Final_Cpk`, `New Cpk`, `Comments/CpkCheck`, `Status` | `Good Fail%` | extended review-oriented export; use the SPL core columns for TP updates and treat the extra review columns as context |

## 3. Variant Guard Families

### 3.1 Filename and `TestProgram` mostly agree

These examples carry filename tokens that already align with the embedded variant:

| File | `TestProgram` example | Guard level | Note |
|------|------|------|------|
| `SPL.UAE7_FC_SPL_17April26.csv` | `UAE7FC016CA01` | medium | filename already says `FC`, but still cross-check `TestProgram` before edits |
| `SPL.UAE7_FH_SPL_16April26.csv` | `UAE7FH016CA01` | medium | filename already says `FH`, but the CSV field is still the stronger source |

### 3.2 Filename is broad, noisy, or potentially misleading

These examples show why the CSV `TestProgram` field should be the main variant guard:

| File | Broad filename cue | `TestProgram` example | Guard level | Note |
|------|------|------|------|------|
| `SPL.SPL_UR7B_FT.20251030_170637.csv` | `FT` | `UR7BFH008BA01` | high | filename is not precise enough to infer `FH` safely |
| `SPL.SPL_UR7E_FT_300K_12Nov25.20251112_102355_Update.csv` | `FT` | `UR7EFH012CA01` | high | filename says `FT`, but the CSV points to an `FH` family |
| `SPL.UR6E_FT_SPL_300K.20251028_105041.csv` | `FT` | `UR6EFH004BB01` | high | same broad-token pattern; use the CSV field instead of the filename |
| `SPL_UBE6_FT_Rev_0014_<reviewer>_Final.csv` | `FT` plus rev wording | `UBE6FH108AA101` | high | filename carries workflow context, not a reliable final variant code |

## 4. Safe Intake Rules From The Families

- identify the header family first so you know whether missing fail-rate data is normal, alternate-labeled, or part of an extended review export
- use `Scaled_LSPL` and `Scaled_USPL` as the default update source across all verified families unless the user explicitly asks for a different source pair
- treat extended review columns such as `suggested LSL`, `Final_Cpk`, `New Cpk`, and `Status` as review context, not the primary replacement source
- prefer the CSV `TestProgram` field over the filename whenever the filename is generic, broad, or revision-oriented
- keep the schema logic tolerant of `Fail%`, `%Fail`, `Good Fail%`, or no fail-rate field at all

## 5. Relationship To Existing SPL Notes

- `spl_workflow_and_methodology.md`
  - explains why SPL exists and when approval or review gates matter
- `spl_csv_schema.md`
  - explains the field semantics and update-source columns
- `spl-limit-workflow`
  - should use this family grouping when classifying new repo SPL references and when warning that filename tokens may be weaker than `TestProgram`