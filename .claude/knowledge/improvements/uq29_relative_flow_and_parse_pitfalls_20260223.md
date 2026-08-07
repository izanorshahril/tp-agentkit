---
type: improvement_report
status: integrated
date: 2026-02-23
use_case: "UQ29FC004B01_0117 relative tests (OTPL simulator parse/load/flow issues)"
---

# Improvement Report: UQ29 Relative Test Integration Pitfalls

## User Feedback Captured

- Simulator load failed with limit inversion on `T500000` (`Lower limit exceeds upper limit`).
- Parse failed with `UserVars _UserVars is redefined`.
- Parse failed at `RelativeMain.tpl` Result action syntax.
- Parse failed because `UQ29_CalcAndJudge_Test.ph` was not found.
- Relative flow was added to wrong branches (FT + EWS) while target requested FT-only and specifically `L9906_SHORT_Flow`.
- Confusion on why `L9907_SHORT_Flow` is not auto-used even though listed in `FlowDefs`.

## Root Causes Found

1. **Limit ordering mismatch**
- In this TP, `Main.ls` tuples are interpreted in `UL,LL` order for runtime limits.
- Relative tests were initially entered as `-10,10` (LL,UL style), causing inversion at load.

2. **Duplicate spec import scope**
- `Import Main.spec;` in `SubTestPlans/Relative/RelativeMain.tpl` duplicated top-level spec scope and redefined anonymous `UserVars` (`_UserVars`).

3. **Illegal Result action token in this parser context**
- `NextAction` in explicit `Result { ... }` block caused parse error in Relative flow; parser expected only core actions.

4. **Missing custom `.ph` in target package**
- `UQ29_CalcAndJudge_Test.ph` did not exist in the delivered TP include paths, though DLL/header artifacts existed.

5. **Flow edit scope drift**
- Initial patch targeted wrong similarly structured blocks (`L9906_Flow`/`L9907_Flow`) before correction.

6. **Flow selection misunderstanding**
- `FlowDefs` lists launchable `MainFlow`s; runtime launcher/context chooses which flow to run.
- Listing both short flows does not auto-switch by `ENV_DEVICE_TYPE`.

## Fixes Applied In Session

- Corrected relative limits `T500000-T500042` in `Main.ls` to match TP order (`10,-10` in tuple form).
- Removed duplicate `Main.spec` import from `RelativeMain.tpl`.
- Replaced invalid Result actions in `RelativeMain.tpl` with valid `Return`/binning actions.
- Switched relative judge import/class to available `STM_Judge_Test.ph`/`STM_Judge_Test`.
- Added `Relative_flw` into `L9906_SHORT_Flow` flow tail.
- Removed `Relative_flw` from EWS branches in normal flows where requested.
- Explained and documented flow resolution path: cfg -> main tpl/stpl -> `MainTestPlanFlow.tpl` -> selected `MainFlow`.

## Preventive Rules To Integrate

1. Add mandatory pre-check for tuple order convention (`UL,LL` vs `LL,UL`) before editing `.ls` limits.
2. Add relative subplan rule: do not import `Main.spec` if top-level already imports it.
3. Add parser-safe Result action checklist for OTPL flow edits.
4. Add import-existence check for `.ph` files before writing new subplan imports.
5. Add patch-scope verification step after flow edits to ensure only intended flow blocks changed.
6. Add explicit note that `FlowDefs` is registration, not automatic device-based flow routing.

## Validation Checklist For Similar Future Tasks

- [ ] Simulator loads without limit inversion errors.
- [ ] No `_UserVars` redefinition parse errors.
- [ ] Relative subplan parses with legal Result actions.
- [ ] All imported `.ph` files resolve in include search path.
- [ ] `Relative_flw` appears only in requested flow(s) and env branches.
- [ ] Final flow path from cfg to selected `MainFlow` is stated in handoff.
