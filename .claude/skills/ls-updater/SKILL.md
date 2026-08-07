---
name: ls-updater
description: "Use when updating T2K .ls limit sheet files from CSV exports, especially for scale-aware LL/UL changes, in-place backups, and urgent-release limit-audit workflows."
metadata:
	status: beta
	language: python
---

# Skill: LS Updater (T2K Limit Sheet)

## Purpose
Update T2K .ls limit sheet files from a CSV export. Stays stdlib-only and runs on Windows 11 and Linux. The main entry point is `ls_updater.py`, with local helper modules for CLI and audit support. For AI/automation, run in-place to create a backup next to the .ls file and overwrite the original.

## Entry Point
- Script: ls_updater.py
- Main: main()
- Helper modules: `ls_updater_cli.py`, `ls_updater_audit.py`

## What It Does
- Detects CSV format (SPAT, SPL, or O+) from headers and maps required columns.
- Prompts for CSV/LS selection and environment when not in silent mode.
- **Temperature**: If CSV env is not detected and there is a single LS env, uses that LS env without prompting. On CSV/LS conflict, user can choose CSV, LS, or **Override** (pick another temperature from the list).
- **Column override**: At confirmation, user can choose "Column override" to re-run CSV column mapping and adjust which columns map to LL/UL, scale, unit, etc.; mappings are stored in CSV_PREVIEW_FORMAT_OVERRIDES.
- Parses limit table lines and macro calls in .ls files; converts scale tokens to base units (EPS tolerance) for comparison.
- Parses legacy comma-table rows, macro calls, and UAE7-style `Tnnn { FTC(...); FTH(...); }` environment-block rows.
- Updates LL/UL values in brackets or macro args, preserving spacing/alignment.
- Skips updates for unit mismatch, non-numeric values, missing limits, or env mismatch.
- Writes output .ls, backup .bak, and a detailed log.
- Supports scale-aware comparison, but callers must still verify the target TP's stored scale token/`PrecScale` and engineering unit before sign-off.

## Inputs
- CSV file (limit data)
- .ls file (target limit sheet)
- Environment filter (optional)

## Outputs
- In-place overwrite of the original .ls file
- Backup .bak in the same folder as the .ls
- Log file (default on for interactive runs; default off for automation)

## Key CLI Flags
- --csv <path>    : CSV input file (repeatable or comma-separated)
- --ls <path>     : LS input file (repeatable or comma-separated)
- --env <env>     : Environment filter (FTC, ALL, etc.); use when auto-detect fails or for non-interactive runs
- --precision <mode> : Precision override `1`, `2`, `3`, `dynamic`, or `source` for LL/UL rounding (optional)
- --silent        : No prompts, minimal output; use with --env when automation cannot interact
- --verbose       : Debug output
- --in-place      : Backup + overwrite original .ls in its folder
- --log           : Write a log file (default on for interactive; default off for automation)
- --log-path <p>  : Explicit log file path (implies --log)
- --report-json   : Emit one-line JSON status for automation

## CSV Formats
- SPAT: requires TestNumber/TestID, NewLSL, NewUSL, Scale, Unit
- SPL: requires TestNumber/TestID, Scaled_LSPL, Scaled_USPL, Scale, ScaledUnit
- O+: requires Expression, Static Low Limit, Static High Limit

Observed YE SPL exports in this repo also include `TestProgram`, `Scaled_LSL`, `Scaled_USL`, `LSL`, `USL`, `LSPL`, `USPL`, `Comment`, `PreferredUnit`, optional `Seq`, and a fail-rate field that may be absent or named `Fail%`, `%Fail`, or `Good Fail%`. Some reviewed exports also add manual-review columns such as `suggested LSL`, `suggested USL`, `LSLCheck`, `USLCheck`, `Final_Cpk`, `New Cpk`, `Comments/CpkCheck`, and `Status`. The updater only needs the recognized subset above for direct limit replacement.

## Behavior Notes
- Uses scale tokens (and EPS = 1e-12) to convert values to base units before comparison; engineers do not need to manually align scale.
- For same-base engineering units with different display scales, the updater follows the target `.ls` scale and unit selection; it converts the incoming CSV numeric value into the target LS representation instead of forcing the CSV display unit into the TP.
- Treat `unit mismatch` as a true base-engineering-unit mismatch, not merely a prefix or display-scale difference such as `nA` versus `uA`.
- Cross-check the CSV `TestProgram` field against the target TP variant before applying updates; some reference exports use generic filename tokens that do not precisely match the `TestProgram` value.
- On UAE7-style environment-block rows, `--env` targets the matching inline cell such as `FTC(...)` or `FTH(...)` and leaves the sibling environments unchanged.
- Adds inline comments on updated lines with LL/UL deltas.
- Tracks reasons for non-updates in the log (unit mismatch, no change, etc.).
- A successful value update is not a complete audit: after editing, also compare touched test-ID occurrence counts against baseline, inspect neighboring unchanged blocks, and inspect the `.ls` tail/footer for accidental added or removed lines.
- Do not assume sibling variants should match each other exactly; compare each edited `.ls` against its own variant baseline.
- In urgent release flows, `.ls`-only or other non-`.cpp` TP edits may be saved and packaged directly without offline simulator validation. In those cases, scale/unit checks plus structure-integrity audits are the mandatory release gate and must be treated as non-optional.
- Q-temperature: if CSV has Q env but LS has none, user is prompted to use fallback (e.g. FTC) or skip; when no fallback, prompt clarifies that both Y/N lead to exit.
- At confirmation, **Column override** re-invokes preview_csv_info(..., force_prompt=True) so user can adjust column mappings; **Temperature override** lets user re-pick env per CSV.
- In silent mode, provide `--env` if CSV/LS envs cannot be auto-detected or conflict.

## Example Usage
- python ls_updater.py --in-place --silent --csv input/file.csv --ls input/file.ls --env FTC --report-json
- python ls_updater.py --in-place --silent --csv input/file.csv --ls input/file.ls --log
