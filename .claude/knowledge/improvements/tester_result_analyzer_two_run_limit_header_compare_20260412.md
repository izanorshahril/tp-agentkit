---
type: improvement_report
status: new
date: 2026-04-12
use_case: "Known-good versus failing tester-result exports where the reviewer needs to separate deployed-limit drift from DUT-signature drift"
---

# Improvement Report: Tester Result Analyzer Two-Run Limit-Header Compare

## User Need Captured

- Some incident and yield investigations need two result sources compared directly:
  - one known-good run
  - one failing or suspect run
- In the URX8 BA case, the decisive question was not only which tests failed, but whether the tester had actually loaded different active limits for those tests.
- Comparing exported `LowL` and `HighL` values between the two runs proved that one fail family came from a changed loaded limit state, while another fail family kept the same numeric limits and therefore had to be explained by DUT signature.

## Toolkit Gaps Found

1. `tester_result_analyzer` supports `summary`, `site-skew`, and `test-coverage`, but it does not support direct comparison of two normalized result tables.
2. There is no generic mode that compares active limit headers (`LowL`, `HighL`) for the same tests across two runs.
3. There is no reusable output that separates:
   - tests with changed active limits
   - tests with unchanged active limits but changed fail signatures
4. Current workflows require ad hoc scripts or manual spreadsheet inspection to answer a recurring release and incident question.

## Proposed Improvement

Extend `tester_result_analyzer` with a two-run compare mode focused on active limit headers and high-level fail-signature differences.

Recommended direction:

- add a mode such as `compare-two-runs`
- accept two input files of the same supported kind
- compare shared tests by exported active limits and optionally by measured-value range summary

## Minimum Feature Set

1. Accept `--baseline` and `--current` result inputs, or equivalent paired input arguments.
2. Compare shared tests by exported `LowL` and `HighL` values when present.
3. Report three groups clearly:
   - changed active limits
   - unchanged active limits
   - tests present only in one run
4. Optionally summarize measured-value min/max or dominant fail direction for unchanged-limit tests.
5. Emit both human-readable and JSON output.

## Guardrails

1. Do not overstate causation from changed active limits alone; report that they explain loaded-limit drift, not necessarily all fallout.
2. Do not assume every source format exposes comparable limit-header fields; the mode should degrade gracefully when headers are missing.
3. Keep the mode generic and table-based; do not embed product-specific judge math.
4. Make it explicit when the comparison is header-only versus header-plus-measurement-summary.

## Why This Should Be An Improvement Report, Not A New Skill

- The result-table loading and normalization logic already belongs to `tester_result_core` and `tester_result_analyzer`.
- The reusable need is a higher-level compare mode on top of the existing analyzer, not a separate standalone skill.
- The correct design should be reviewed before expanding the analyzer CLI and JSON contract.