---
type: operational_pattern
status: verified
verifier: ATE datalog verification
date: 2026-03-14
source: "Verified duplicate-test implementation in testprogram/UR7T_0016 and testprogram/UR7S_0021"
source_artifacts_files: 3
source_artifacts_note: "Original task-local TASK/plan/walkthrough artifacts were not retained under stable repo paths; editor validation and ATE datalog verification passed"
---

# Duplicate Test Pattern

Reusable pattern for duplicating an existing test into a companion condition, setup, or variant while keeping the original test active and adding a new test number beside it.

This lesson is written as a general duplicate-test category. The UR7T and UR7S SATBCK 27V to 33V split is the verified example that produced the pattern, not the only intended use case.

## Extraction Scope

- Verified example programs: `UR7T_0016`, `UR7S_0021`
- Verified example change: baseline main test `351008` stayed active for `14V` while CI companion tests `9351008` and `99351008` were added for `27V` and `33V`
- Verified example domain: setup-specific SATBCK high-voltage measurement split in `T_POWER_UP_FUNCTIONAL`
- Historical ATE verification log filenames from the verified example:
   - `UR7TQH208BA801_REV16_STDF_20260313114031_SiteC1.txt`
   - `UR7SQH208CA801_REV21_STDF_20260313145933_SiteC1.txt`
- These raw log files are not retained under `references/` in the current workspace snapshot.

---

## 1. Problem Shape

Use this pattern when:

- An existing test must stay active for its current condition
- A new companion test number must be added for a second condition, setup, product option, voltage, timing corner, or environment
- Datalogging and limits must remain aligned across all active TP files
- The task may touch limits, code, flow, and history, but not every platform requires all four

Generic file groups to inspect:

- limit definitions
- flow or test-plan registration
- test implementation code
- history or revision log

For Advantest T2000 RDK specifically, this usually maps to:

- `TestFunctions/*.cpp`
- `MainTestPlan/*.ls`
- `MainTestPlan/*.tpl` when flow registration is needed
- `TestProgramHistory.txt`

---

## 2. Core Lessons Learned

1. Inspect the existing implementation before editing anything.
   - One TP may already contain the companion code path, so only limit or flow alignment is needed.

2. Preserve each TP or product's own behavior unless the user explicitly asks to normalize it.
   - Limits, names, bins, and variable conventions can legitimately differ across related programs.

3. Update every active variant file, not only the obvious primary file.
   - Missing duplicate-test entries often remain in alternate limit sheets, subplans, or environment-specific variants.

4. Make the split explicit in naming.
   - Rename the original label so it clearly identifies the original condition, and name the new label so it clearly identifies the companion condition.

5. Correct misleading identifiers while duplicating the path.
   - If a variable name, label, or comment no longer matches the real setup, fix it during the same change so the duplicate path is understandable.

6. Separate force/setup parameters from measurement parameters.
   - Do not change a measurement argument just because the forced condition changed unless there is a real measurement requirement behind it.

7. Do not assume flow edits are always required.
   - If the existing implementation is already invoked and only its outputs are expanding, flow changes may be unnecessary.

8. History handling should follow workflow rules first, then explicit user intent.
   - Default workflow may say append a new revision entry, but if the user explicitly requires same-revision tracking, record the change under that revision block.

9. Preserve a comparison baseline even if temporary backups are later cleaned up.
   - Backup creation before edits is still mandatory, but a retained reference copy under `references/` can support later audit after cleanup.

10. Extract the lesson at the category level, then keep the completed task as an example.
   - The pattern should explain how to duplicate tests generally, while the verified SATBCK case remains only the proof source.

---

## 3. Recommended Execution Order

1. Confirm the target duplicate-test behavior and which condition stays on the original test number.
2. Present plan and wait for approval per protocol.
3. Create the required backup or revision copy.
4. Inspect current limits, flow, code, and history to determine what already exists.
5. Add or align the duplicate test definition in every active file family that needs it.
6. Update revision history in the format required by workflow and user instruction.
7. Validate with diagnostics, targeted searches, and, when available, real datalog evidence.
8. Record a retained comparison baseline if temporary backup folders are later removed.

---

## 4. Duplicate-Test Checklist

- [ ] Original test remains active for its original condition
- [ ] New companion test number is unique
- [ ] Limits or setup metadata are duplicated from the correct source entry
- [ ] All active variant files define or reference the new companion test where required
- [ ] Original and new names make the condition split explicit
- [ ] Variable names and datalog labels match the real setup
- [ ] Flow changes are added only where registration is actually missing
- [ ] History reflects the final change in the required format
- [ ] No shared infrastructure such as `CommonLib/` is modified unless explicitly approved
- [ ] A stable before/after comparison source is retained for audit

---

## 5. Validation Queries That Worked

Useful checks for similar tasks:

- Search for both old and new test numbers across the TP
- Search for the old and new condition labels in limits and code
- Read every active variant of the touched limit or flow files
- Run diagnostics on touched code, limit, and history files
- Compare the final TP against a retained baseline under `references/` if temporary backups were removed
- Review real datalogs when available to confirm the original and companion tests both execute and pass as intended

---

## 6. Applicability Notes

- This pattern is intended to be reused across similar duplicate-test tasks, not only SATBCK or these two TP folders.
- The verified extraction source is an Advantest T2000 RDK case, so platform-specific file names should be adapted when applying the pattern to OTPL, SmarTest, Flex, or other TP structures.
- Keep the category generic, but preserve the example evidence so future users can see one real verified implementation behind the guidance.

## 7. Verified Example Evidence

Verified source case: SATBCK high-voltage coverage expansion in `UR7T_0016` and `UR7S_0021`.

- `351008` remains the baseline SATBCK high test at `14V`
- CI `C254265735` adds `9351008` for `27V`
- CI `C254265735` adds `99351008` for `33V`

- UR7T ATE datalog shows:
   - `351008` baseline `14V` PASS at `7.9568V`
   - `9351008` `_27V` PASS at `7.9500V`
   - `99351008` `_33V` PASS at `7.9552V`
   - limits `7.6800V` to `8.3200V`
- UR7S ATE datalog shows:
   - `351008` baseline `14V` PASS at `7.8940V` on DUT 1 and `7.9434V` on DUT 5
   - `9351008` `_27V` PASS at `7.9219V` and `7.9381V`
   - `99351008` `_33V` PASS at `7.9291V` and `7.9489V`
   - limits `7.6800V` to `8.2200V`

Result: the duplicate-test pattern is verified on real ATE through this concrete example and can be reused as a general lesson category.