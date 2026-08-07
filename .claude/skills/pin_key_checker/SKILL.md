---
name: pin_key_checker
description: "Detect StorePinMeasurement blocks where PinName and MeasValue naming are semantically inconsistent."
metadata:
   status: beta
   language: python
---

# SKILL: OTPL Pin-Key Mismatch Checker

## Purpose

Use `pin_key_checker.py` to detect `StorePinMeasurement` blocks where the `PinName` and `MeasValue` key are semantically inconsistent — i.e. the pin root derived from `PinName` does not appear in the `MeasValue` string.

Example mismatch caught:
```
StorePinMeasurement {PinName = "IS2P__MMXHA_PMU", MeasValue = "REL_1518_IS1M_LEAK_13V"}
                              ^^^^                                     ^^^^
                              IS2P pin stored under IS1M key -- mismatch!
```

## Tool Entry Point

- Script: `.claude/skills/pin_key_checker/pin_key_checker.py`
- Preferred runner: `uv run python`
- Working directory: workspace root (pass `tp_dir` as relative path)

## When To Use

Use this skill when:
- Any `.tpl` file containing `StorePinMeasurement` has been created or edited
- Reviewing a test program that uses `StoreMode = Accumulate` with multiple `StorePinMeasurement` entries
- Performing a full Review Agent validation pass on an OTPL test program
- User asks to verify pin naming consistency in a test program

Do not use this skill when:
- No `.tpl` files exist or no `StorePinMeasurement` blocks are present
- The test program does not use `STM_DC_PMU_Test` or similar parametric measurement classes

## Standard Commands

### Check a test program (human-readable output)

```powershell
uv run python .claude/skills/pin_key_checker/pin_key_checker.py <path-to-testprogram-folder>
```

### Check with verbose file-by-file progress

```powershell
uv run python .claude/skills/pin_key_checker/pin_key_checker.py <path-to-testprogram-folder> --verbose
```

### JSON output (for agent consumption)

```powershell
uv run python .claude/skills/pin_key_checker/pin_key_checker.py <path-to-testprogram-folder> --format json
```

### One-line summary JSON (for quick pass/fail in agent reports)

```powershell
uv run python .claude/skills/pin_key_checker/pin_key_checker.py <path-to-testprogram-folder> --report-json
```

## Pin Root Extraction Logic

The script derives a short "pin root" from the full `PinName` by:
1. Stripping known PMU board suffixes (`__NA_MMXHA_PMU`, `__MMXHB_PMU`, `_PMU`, etc.)
2. Stripping leading `NA__` noise
3. For compound names (e.g. `OPA551_supply__CS_MMXHA_PMU`), taking the segment after the last `__`
4. Stripping trailing underscores

Examples:
| PinName                    | Derived Root |
|----------------------------|--------------|
| `VBAT__NA_MMXHB_PMU`       | `VBAT`       |
| `CBS1__NA_MMXHA_PMU`       | `CBS1`       |
| `IS2P__MMXHA_PMU`          | `IS2P`       |
| `NA__SI_MMXHA_PMU`         | `SI`         |
| `NA__PWMH1_MMXHB_PMU`      | `PWMH1`      |
| `OPA551_supply__CS_MMXHA_PMU` | `CS`      |

## Agent Workflow

1. **Trigger**: After any edit to `.tpl` files containing `StorePinMeasurement`, or as part of a full review pass.

2. **Run the checker**:
   ```powershell
   uv run python .claude/skills/pin_key_checker/pin_key_checker.py <tp_dir> --verbose
   ```

3. **Interpret results**:
   - Exit code `0`: No mismatches — pass.
   - Exit code `1`: Mismatches found — report each one with file, line, `PinName`, `MeasValue`, and derived root.
   - Exit code `2`: Directory not found — check the path argument.

4. **Fix mismatches**: For each reported mismatch, correct either:
   - The `MeasValue` key in the `StorePinMeasurement` block (in the source `.tpl`), **and** update the corresponding `CalcJudge1MV` entry in the relative test `.tpl` to use the corrected key.
   - Or the `PinName` if it was entered incorrectly.

5. **Re-run** after fixes to confirm exit code `0`.

6. **Report** in the eval/review output:
   - Command run
   - Exit code
   - Number of mismatches found (and list if any)

## Expected Inputs and Outputs

Input:
- Path to a test program directory containing `SubTestPlans/**/*.tpl` files

Output (text mode):
```
MISMATCHES FOUND: 3 issue(s) across 12 files checked.

Line    File                                               PinName                         MeasValue                       PinRoot
---...
42      SubTestPlans/leakage/leakageMain.tpl               IS2P__MMXHA_PMU                 REL_1518_IS1M_LEAK_13V          IS2P
```

Output (--report-json):
```json
{"total": 3, "mismatches": 3, "files_checked": 12}
```

## Error Handling

If directory not found:
- Script prints error to stderr and exits with code `2`.

If no `.tpl` files found:
- Script prints a warning and exits with code `0` (nothing to check).

If a `StorePinMeasurement` block is missing `PinName` or `MeasValue`:
- Block is silently skipped (incomplete blocks are not flagged as mismatches).

## Constraints and Notes

- The checker searches `SubTestPlans/` recursively. If that subdirectory does not exist, it falls back to searching the entire `tp_dir`.
- Pin root matching is case-insensitive.
- The script uses only Python stdlib — no `uv` or pip install required.
- False positives are possible for pins with very short roots (e.g. single-letter pins). Review flagged entries manually.
