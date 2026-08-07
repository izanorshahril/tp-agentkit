---
type: operational_pattern
status: partial
verifier: simulator load plus offline datalog verification plus online sample limit-table verification
date: 2026-04-08
source: ".claude/artifacts/archive/ur7s-ur7t-scr-workflow-plan.md; .claude/artifacts/archive/scr-simulator-parse-discovery.md; .claude/artifacts/archive/ur7t-scr-revert-scope-change.md; .claude/artifacts/current_task/ur7s-scr01-sample-limit-check-20260408.md"
source_artifacts_files: 4
source_artifacts_note: "Built from the completed UR7S/UR7T SCR special-TP implementation, simulator parser debug, offline datalog validation, later UR7T scope rollback, and the 2026-04-08 UR7S FH online sample limit check"
---

# RDK SCR Special-TP Pattern

Reusable pattern for adding SCR-only launch packages and SCR-only limits to an Advantest T2000 RDK TP while keeping the base jobs unchanged.

## Extraction Scope

- Initial implementation families: `UR7T_0016_SCRWIP`, `UR7S_0021_SCRWIP`
- Final retained scope: UR7S only
- Final official folder state after user rename:
  - active: `testprogram/UR7S_0021`
   - historical retained baseline name from the verified example: `testprogram/UR7S_0021_old` (not present in the current workspace snapshot)
  - UR7T final non-SCR baseline: `testprogram/UR7T_0016`

---

## 1. Problem Shape

Use this pattern when:

- Only selected launch jobs need a tighter or alternative special TP behavior.
- The base revision folder must remain auditable during implementation.
- Some requested changes live in dedicated limit sheets, but at least one target may be judged in `.cpp` instead of `.ls`.
- Offline simulator behavior matters before tester-side deployment.

---

## 2. Core Lessons Learned

1. Isolate the overlay with dedicated launch packages.
   - Create dedicated `.tpl`, `.cfg`, `.env`, `.soc`, `.ini`, and `.ls` files for the special jobs rather than editing base launch files in place.

2. Treat `SysCUserVarsDummy` conservatively.
   - In this TP family, `UserVars SysCUserVarsDummy` accepted `String SCR_MODE = "1"` but rejected numeric-form `SCR_MODE` declarations during simulator parse.

3. Runtime gating may need both live and dummy user-var namespaces.
   - Offline simulator execution may expose only `SysCUserVarsDummy.*` even when production code normally reads `SysCUserVars.*`.

4. Not every limit lives in `.ls`.
   - If a requested test number is missing from the special limit sheets, trace the judgment path in `.cpp` before assuming the change was missed.

5. Keep overlay limits localized.
   - Dedicated copied `.ls` files with short inline previous-limit comments make the review safer than editing the base limit sheets.

6. Scope can narrow after implementation.
   - If the user later limits the need to one product family, revert the unnecessary family to baseline and remove the redundant working folder to avoid false future assumptions.

---

## 3. Recommended Execution Order

1. Copy the released TP folder to a working overlay folder.
2. Create dedicated special launch packages for each required job.
3. Copy source `.ls` files into dedicated special `.ls` files.
4. Apply limit-only changes in the dedicated special `.ls` files.
5. Trace code-judged targets in `TestFunctions/*.cpp` and gate them through a special-mode helper.
6. Validate simulator parsing first.
7. Validate offline datalog for every `.ls`-driven target that can be exercised offline.
8. Mark any remaining real-device-only items explicitly instead of over-claiming verification.

---

## 4. Implementation Shape That Worked

### Dedicated Job Sets

Special job families were created as dedicated launch packages instead of modifying the base jobs in place.

### Runtime Flag Pattern

Add the special runtime flag in the special `.tpl` files using the same declaration style already proven in `SysCUserVarsDummy`:

```tpl
String SCR_MODE = "1";
```

### C++ Gate Pattern

Use a helper that checks both namespaces:

```cpp
RscUserVar scrMode("SysCUserVars.SCR_MODE");
RscUserVar dummyScrMode("SysCUserVarsDummy.SCR_MODE");
```

If either returns string value `"1"`, apply the special limit.

---

## 5. Validation Pattern

### What Can Be Verified Offline

- parser acceptance of the launch files
- `.ls`-driven limit changes through offline datalog
- code-driven runtime-gated limits when the helper supports the simulator namespace path

### What May Still Need Online Verification

- tests that require a real device path and cannot be exercised meaningfully in offline simulator mode

### Online Limit-Deployment Validation

- If an Examinator-style workbook or export includes both active `HighL`/`LowL` rows and per-device results, use it to prove the tester actually loaded the intended SCR limits.
- Compare exported `HighL`/`LowL` values to the live special `.ls` file, not only to the failing test list. A fail list alone does not prove deployment of the new limits.
- Parse both explicit `.ls` rows and `${LimitDef(...)}` macro rows when comparing against the live TP. In the UR7S FH sample check, an explicit-only compare undercounted the SCR delta from `17` rows to the actual `42` changed rows.
- Normalize unit-display prefixes from the export before declaring a mismatch. `KOhm`-style display formatting can differ from `.ls` scale-plus-unit storage even when the numeric limits are identical.
- Treat `limits were deployed online` and `changed limits caused rejects` as separate conclusions. Both questions need to be answered explicitly during closeout.
- If `SCR01` and `SCR801` limit sheets are identical as live pairs, an FH sample from one can validate deployment for the other in that same family; it does not replace separate QH online evidence.
- Alarm-bin devices may not show a numeric out-of-limit row in the exported matrix. If root-cause detail is required, pull tester alarm or datalog traces in addition to the limit export.

### Verified Online Sample Outcome: UR7S FH

- Verified source: `references/SCR01_limit_tighten.xlsx`, embedded result sheet `muat2kdc_1_ur7sfh108scr801_0123`.
- Verified scope: FH hot only, `31` sample units total; no QH online sample was present in the same artifact.
- Observed bin split in the sample: `24` pass, `4` alarm, `2` deployment, `1` SYSBST.
- Live-pair parity was confirmed for both FH and QH: `SCR01` and `SCR801` limit sheets matched as pairs.
- Workbook `HighL`/`LowL` rows matched the live FH SCR limits on all `42` FH SCR-different tests.
- All `42` changed FH rows were exercised in the sample results, and none of those changed-limit rows produced a fail.
- The only numeric sample fails were on non-SCR changed tests: `7700608`, `7701507`, and `311000`.
- Practical conclusion from that sample: the online system was using the intended FH SCR limits, but the observed rejects were not caused by those SCR-specific limit changes.
- Tightening watchlist from that sample, if a later round is needed: `340001`, `7700412`, `1800324`, `7700708`, `320009`, `230001`, `9105128`.

### Verified Example Outcomes

Offline verification confirmed the special UR7S behavior for:

- `155088`
- `98108`
- `360018`
- `1555000`
- `4800202`
- `4800203`
- `4800223`

One implemented item remained explicitly online-only for final behavioral confirmation:

- `1498917`

### Example End-State Note

In the extracted UR7S task, the verified overlay later became the official active folder and the previous baseline was retained under an `_old` suffix. Treat that as one task-specific handoff choice, not as a default repository workflow rule.

---

## 6. Scope-Rollback Pattern

If one family no longer needs the special TP:

1. revert shared edited files to baseline behavior
2. delete dedicated special launch files for that family
3. confirm no live `*SCR*` files remain under that family's active folder
4. remove the redundant reverted working folder if the user wants the workspace cleaned up

This was the correct cleanup path when UR7T was removed from the final SCR scope.