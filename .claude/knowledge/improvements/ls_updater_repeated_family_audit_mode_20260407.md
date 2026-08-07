---
type: improvement_report
status: new
date: 2026-04-07
use_case: "Repeated-family T2K .ls rollout or manual repair where occurrence-count and structure audits should run without applying CSV updates"
---

# Improvement Report: LS Updater Repeated-Family Audit Mode

## User Need Captured

- Some T2K `.ls` changes are not driven directly from a CSV import.
- The risky cases are repeated or near-duplicate limit families where a manual rollout or repair can preserve the intended value while still damaging adjacent structure.
- The user still needs a disciplined, reusable safety gate before release, especially for urgent non-`.cpp` TP deliveries that may ship without offline simulator validation.
- The desired behavior is audit-only: validate structure and repeated-family integrity without rewriting values.

## Toolkit Gaps Found

1. The current `ls-updater` workflow already documents the required audits, but it does not expose them as a reusable audit-only mode for already-edited files.
2. There is no helper that compares touched test-ID occurrence counts between a retained baseline and an edited `.ls` when the edit did not come from a CSV update pass.
3. There is no helper that validates repeated-family value shape, such as "exactly one hot-side `700.0e-6` and the remaining environment values unchanged," across a list of target test IDs.
4. There is no reusable conditional-parity check for sibling `.ls` variants using `$if/$else/$endif` counts as a structural integrity signal.
5. Footer and tail inspection remain manual even though stray appended rows near `JOB_REV` or EEPROM blocks are a recurring failure mode.

## Proposed Improvement

Extend the existing `ls-updater` workflow with an audit-only repeated-family mode instead of creating a separate skill.

Recommended direction:

- either add an `--audit-only` path to the current tool
- or add a sibling helper under the same skill that focuses only on baseline-versus-edited structure checks

## Minimum Feature Set

1. Accept baseline and edited `.ls` paths directly, without requiring a CSV input.
2. Parse direct rows and `${LimitDef(...)}` entries to compare touched test-ID presence and per-file occurrence counts.
3. Support an explicit target-ID list or target-name family so the audit can focus on the intended repeated family.
4. Optionally validate expected value shape for repeated families, not just value presence.
5. Report `$if/$else/$endif` count parity for sibling variant comparisons when requested.
6. Flag suspicious tail or footer additions after the last expected limit region.
7. Emit concise markdown or JSON output suitable for artifact retention.

## Guardrails

1. Do not claim a file is safe based on target-value presence alone if occurrence counts or nearby structure differ.
2. Do not force equality across QA and main-flow variants unless the user explicitly says they should match.
3. Do not treat this audit as a simulator replacement; it is a structure-integrity gate for limit-only and related non-`.cpp` edits.
4. Keep scale-token and engineering-unit checks visible in the audit output when a value-shape rule is used.

## Why This Should Be An Improvement Report, Not A New Skill Yet

- The repo already has a natural home for this behavior in `ls-updater`.
- The reusable need is tooling convenience and output standardization, not a separate discovery surface.
- The desired checks are clear now, but the exact CLI and output contract should be reviewed before expanding the current skill implementation.