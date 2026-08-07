---
type: operational_pattern
status: verified
verifier: STDF-derived CSV coverage audit plus TP source and main-flow reachability review
date: 2026-04-03
source: ".claude/artifacts/archive/uae7-coverage-audit-20260401.md; .claude/artifacts/archive/uae7-rpc12-audit-20260401.md; .claude/artifacts/archive/uae7-hot-rtrp-plan-and-rpc-root-cause-20260401.md"
source_artifacts_files: 3
source_artifacts_note: "Promoted as a generic OTPL troubleshooting method; product-specific conclusions remain in archive"
---

# OTPL Source vs Runtime Coverage Triage

Reusable pattern for cases where a test appears to exist in OTPL source, but does not appear in STDF-derived CSV or other execution output.

This pattern is for deciding whether a test is:

- fully implemented and executed
- defined in source but not reachable at runtime
- absent from source entirely

It is especially useful for multi-environment audits where one environment shows full coverage and another does not.

## 1. Problem Shape

Use this pattern when:

- the user asks whether certain test IDs are covered in EWS or FT output
- STDF-derived CSV exists and exposes numeric test IDs or test columns
- the TP source contains matching test IDs in `Main.ls`, subplans, or result blocks
- output and source disagree, creating ambiguity about whether the test is really missing

Typical failure mode:

- a test is present in source and assumed to be active
- the CSV does not show it
- the wrong conclusion is made that the export is incomplete or the audit is wrong

---

## 2. Core Lesson

Do not treat "defined in source" as equivalent to "covered in execution output".

For every target test set, classify each ID into three separate states:

1. **Defined in source**
   - present in `Main.ls`
   - and/or referenced by ID or symbol in the relevant subplan/result blocks

2. **Reachable in executed flow**
   - the launched main flow actually routes into the subflow or subplan that contains the test

3. **Visible in runtime output**
   - the test appears in STDF-derived CSV or equivalent execution evidence

Only after all three are checked should a test be called covered, hidden, or missing.

---

## 3. Recommended Execution Order

1. Define the exact target test IDs.
2. Check STDF-derived CSV for the target IDs.
3. Check source presence in `Main.ls` and the relevant subplan(s).
4. If source and CSV disagree, inspect the launched main flow.
5. Confirm whether the relevant subflow is actually reachable in the target environment branch.
6. Summarize each target ID as one of:
   - present in source and present in CSV
   - present in source but not reachable in flow
   - present in source and reachable, but still not visible in CSV
   - absent from source

---

## 4. Flow-Reachability Rule

If a test exists in `Main.ls` or in a subplan but does not appear in runtime output, inspect the top-level main flow before concluding the audit is wrong.

The key question is not only "does the subplan exist?" but also:

- does the launched environment branch enter that subflow?
- is that branch the one actually used by the runtime job?

This prevents a common OTPL mistake:

- seeing valid result blocks in a subplan
- assuming they must run
- missing the fact that the main flow bypasses the entire subflow for one environment

---

## 5. Classification Labels That Worked

Use plain labels like these in reports:

- **source and CSV aligned**
- **source present, CSV absent**
- **source absent**
- **flow-bypassed**
- **supporting-only comparator**

These labels make it easier to separate implementation status from runtime behavior.

---

## 6. Comparator Selection Rule

In multi-environment coverage audits, choose a primary comparator and keep any secondary comparator clearly marked as supporting-only.

Good pattern:

- primary comparator: the environment expected to represent the intended released behavior
- supporting comparator: an environment used only as a negative control or shape check

Why this matters:

- not every environment should be expected to show the same test set
- ambient or QA branches may intentionally omit tests that hot or cold production branches contain

---

## 7. Reporting Format That Worked

For each environment or flow, report:

1. focus IDs present in CSV
2. focus IDs present in source
3. any source-present but CSV-absent IDs
4. any source-absent IDs
5. any flow reachability reason that explains the gap

Best compact summary form:

- environment summary by `x/y` covered
- per-test matrix across source and CSV states
- short conclusion on which environment aligns with the intended comparator

---

## 8. Minimum Checklist

- [ ] exact target test IDs are named
- [ ] CSV evidence is checked
- [ ] `Main.ls` presence is checked
- [ ] relevant subplan/result blocks are checked
- [ ] top-level flow reachability is checked when source and CSV disagree
- [ ] comparator environments are explicitly labeled primary or supporting-only
- [ ] final conclusion distinguishes source absence from runtime bypass

---

## 9. Applicability Notes

- This is most useful for OTPL jobs with explicit `Main.ls`, `MainTestPlanFlow.tpl`, `.stpl`, and subplan structures.
- The method still generalizes beyond OTPL whenever a test can be defined in source but gated away by the launched flow.
- This pattern complements `tp_diff_compare.md` rather than replacing it.
  - use this file for execution-coverage reasoning
  - use `tp_diff_compare.md` for whole-folder structural comparison

---

## 10. Durable Takeaway

When output and source disagree, the missing step is often flow reachability, not file comparison.

That distinction turns an ambiguous "why is this missing?" question into a defensible engineering result:

- implemented and executed
- implemented but bypassed
- or not implemented
