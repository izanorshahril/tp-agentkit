---
type: reference
status: partial
verifier: repo example CSV cross-check plus local workflow classification
date: 2026-04-23
source: "references/SPL/SPL.UAE7_FH_SPL_16April26.csv; references/SPL/SPL.UAE7_FC_SPL_17April26.csv; references/SPL/SPL.SPL_UR7B_FT.20251030_170637.csv; references/SPL/SPL.SPL_UR7E_FT_300K_12Nov25.20251112_102355_Update.csv; references/SPL/SPL.UR6E_FT_SPL_300K.20251028_105041.csv; references/SPL/SPL_UBE6_FT_Rev_0014_<reviewer>_Final.csv; .claude/skills/ls-updater/ls_updater.py; .claude/skills/spl-limit-workflow/spl_limit_workflow.py"
---

# SPL CSV Schema

Reference note for the actual Yield Explorer SPL CSV shape observed in this repo.

Use this note when a task involves `references/SPL/*.csv`, an approved YE SPL export, or any question about which SPL CSV columns should drive TP limit implementation.

This note is narrower than `spl_workflow_and_methodology.md`: it captures the practical file schema and field semantics seen in real example exports.

## 1. Example Files Verified

- `references/SPL/SPL.UAE7_FH_SPL_16April26.csv`
- `references/SPL/SPL.UAE7_FC_SPL_17April26.csv`
- `references/SPL/SPL.SPL_UR7B_FT.20251030_170637.csv`
- `references/SPL/SPL.SPL_UR7E_FT_300K_12Nov25.20251112_102355_Update.csv`
- `references/SPL/SPL.UR6E_FT_SPL_300K.20251028_105041.csv`
- `references/SPL/SPL_UBE6_FT_Rev_0014_<reviewer>_Final.csv`

All six files are recognized by the maintained workflow as `spl_csv` and by `ls-updater` as SPL-format CSV input.

## 2. Core Header Family Observed

Most verified examples share this main structure:

- `TestProgram`
- `TestNumber`
- `Parameter`
- `Scaled_LSL`
- `Scaled_USL`
- `Scaled_LSPL`
- `Scaled_USPL`
- `ScaledUnit`
- `LSL`
- `USL`
- `LSPL`
- `USPL`
- `ParameterUnit`
- `Comment`
- `PreferredUnit`
- `Scale`

They also include large statistical sections such as:

- part counts and fail counts
- calculated lower and upper limits
- median, average, standard deviation, minimum, maximum
- `Cpk` and `Cpkn` variants
- optional fail-rate field near the far right

The `SPL_UBE6_FT_Rev_0014_<reviewer>_Final.csv` variant extends the same core family with extra review columns such as:

- leading `Seq`
- `suggested LSL` and `suggested USL`
- `LSLCheck` and `USLCheck`
- `Final_Cpl`, `Final_Cph`, `Final_Cpk`
- `New Cpl`, `New Cph`, `New Cpk`
- `Comments/CpkCheck`
- `Status`

Treat those as review metadata, not the primary source columns for direct `.ls` replacement.

## 3. Columns That Matter Most For TP Updates

### 3.1 Default update source

For TP implementation, the default candidate update columns are:

- `Scaled_LSPL`
- `Scaled_USPL`

These are the statistically proposed SPL limits already expressed in the display unit used by the export.

### 3.2 Columns that are not the default update source

- `Scaled_LSL` and `Scaled_USL` represent the existing scaled lower and upper limits at export time, not the default new limits to apply.
- `LSL`, `USL`, `LSPL`, and `USPL` are the unscaled or base-unit companions and should not be used for direct `.ls` replacement when the scaled columns are present.

Plain rule: when the task is `implement approved SPL CSV into TP`, start from `Scaled_LSPL` and `Scaled_USPL` unless the user explicitly says to use the current spec limits instead.

## 4. Observed Real-World Quirks In The Example Files

### 4.1 Fail-rate field presence and spelling are not stable

The verified examples now show three patterns:

- `SPL.UAE7_FH_SPL_16April26.csv`, `SPL.SPL_UR7E_FT_300K_12Nov25.20251112_102355_Update.csv`, and `SPL.UR6E_FT_SPL_300K.20251028_105041.csv` use `%Fail`
- `SPL.UAE7_FC_SPL_17April26.csv` uses `Fail%`
- `SPL_UBE6_FT_Rev_0014_<reviewer>_Final.csv` uses `Good Fail%`
- `SPL.SPL_UR7B_FT.20251030_170637.csv` has no fail-rate column in the verified header

Do not key parser or workflow logic on one exact fail-rate header spelling, and do not assume every SPL export carries a fail-rate field at all.

### 4.2 Unit information is split across multiple columns

The examples use these unit-related fields together:

- `ScaledUnit`
- `ParameterUnit`
- `PreferredUnit`
- `Scale`

Observed pattern:

- `ScaledUnit` already carries the display prefix such as `V`, `uA`, or `nA`
- `ParameterUnit` may hold the base engineering unit, for example `A`
- `Scale` may hold a numeric exponent token such as `0`, `6`, or `9`
- `PreferredUnit` may mirror the same unit-preference token family

For TP-AgentKit, this means the scale and unit pair must still be audited even when the displayed `ScaledUnit` looks obvious.

Implementation rule:

- when the SPL CSV and the target `.ls` use the same base engineering unit but different display scales, follow the target `.ls` scale and unit selection
- convert the SPL numeric proposal into the target `.ls` display instead of forcing the CSV display unit into the TP
- only escalate to the user when the correct engineering-unit choice is still unclear from both the SPL CSV and the target `.ls`

### 4.3 Not every row is a normal analog-limit candidate

The example CSVs include rows such as:

- `DIB_FT`
- `DIB_REV`
- `DIB_SERIAL`

These rows can have blank unit fields and comments like `Modality=1 is insufficient` or `Modality=3 is insufficient`.

Treat those rows as review items, not automatic analog limit-update candidates.

### 4.4 Comment strings carry important review meaning

The `Comment` field is highly informative in the verified examples. Repeated patterns include:

- `Use Cpkn=4`
- `Reduced LSPL to reduce Yieldloss ...`
- `Increased USPL to reduce Yieldloss ...`
- `Reset LSPL = LSL`
- `Reset USPL = USL`
- `Modality=... is insufficient`

This field is not required for `ls-updater`, but it is useful for human review because it explains whether the statistical result tightened, relaxed, or reset one side of the limit.

### 4.5 TestProgram is a stronger variant guard than the filename

The `TestProgram` column is present in all verified examples and should be treated as the main cross-check against the target TP variant before updates are applied.

The newer reference set shows why this matters:

- `SPL.SPL_UR7B_FT.20251030_170637.csv` carries `TestProgram=UR7BFH008BA01`
- `SPL.SPL_UR7E_FT_300K_12Nov25.20251112_102355_Update.csv` carries `TestProgram=UR7EFH012CA01`
- `SPL.UR6E_FT_SPL_300K.20251028_105041.csv` carries `TestProgram=UR6EFH004BB01`

So a generic `FT` token in the filename is not sufficient proof of the exact final TP variant. Prefer the CSV `TestProgram` field over filename wording when choosing the target program family.

## 5. TP-AgentKit Guidance From These Examples

When working from YE SPL CSVs like these:

- confirm the target TP revision first
- confirm whether the CSV is approved or still under review
- cross-check `TestProgram` against the intended target variant
- do not trust filename tokens alone when they conflict with the CSV `TestProgram` value
- use `Scaled_LSPL` and `Scaled_USPL` as the default update pair
- treat the target `.ls` as the authority for the final displayed scale and unit when the base engineering unit matches
- keep `Scaled_LSL` and `Scaled_USL` as review context, not the default replacement values
- use `Comment` to understand one-sided resets or yield-loss-driven changes
- do not treat rows with blank units or `Modality ... insufficient` comments as normal analog update rows
- do not depend on the fail-rate field being present or spelled consistently across exports

## 6. Relationship To Existing Repo Surfaces

- `spl_workflow_and_methodology.md`
  - explains why SPL exists and how the methodology is used
- `spl_reference_families.md`
  - groups the retained repo SPL CSVs by header family and filename-versus-`TestProgram` variant guard strength
- `ls-updater`
  - already accepts the required SPL subset: `TestNumber`, `Scaled_LSPL`, `Scaled_USPL`, `Scale`, and `ScaledUnit`
- `spl-limit-workflow`
  - should surface this schema knowledge when classifying real YE SPL CSV inputs