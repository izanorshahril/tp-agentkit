---
type: operational_pattern
status: verified
verifier: repo-local helper validation plus new callable skill promotion
date: 2026-04-24
source: ".claude/artifacts/current_task/tp-agentkit-spl-readonly-compare-rework-20260423.md; .claude/artifacts/current_task/tp-agentkit-artifact-retention-20260423.md; .claude/artifacts/spl_readonly_compare.py; .claude/skills/spl-readonly-compare/spl_readonly_compare.py"
---

# SPL Read-Only Compare

Use this note when reviewing an SPL CSV against a target `.ls` file before any TP edit.

This note defines the stable bucket semantics and interpretation rules for the repo-local read-only compare workflow. It is the durable companion to the callable `spl-readonly-compare` skill.

## 1. Replace The Old Missing Bucket

Do not treat every not-directly-updatable row as one generic `missing` bucket.

Future read-only review should separate at least these states:

- active and comparable in the target env cell
- active but non-comparable
- commented in `Main.ls`
- target env is `NA`
- absent from `Main.ls`

These states correspond to different follow-up actions. Merging them into one bucket hides whether the problem is scope, TP structure, env coverage, or compareability.

## 2. LS Target Env Cell Is The Unit Authority

For UAE7-style `.ls` rows with multiple inline env cells:

- use the selected target env cell itself as the LS unit source
- do not infer the compare unit from a sibling env on the same row
- normalize `%` and `pct` as the same engineering unit token before deciding there is a unit mismatch

This is the rule that eliminated the false FC base-unit mismatch conclusion from the earlier compare pass.

## 3. Partial Target-Env NA Is Non-Comparable, Not Unit Mismatch

If the target env cell is active but one side of the limit pair is `NA`, classify the row as active but non-comparable.

Do not report those rows as `base_unit_mismatch` just because the compare cannot complete.

Practical interpretation:

- `FTC(NA)` or `FTH(NA)` belongs in `target_env_na`
- `FTC(1.0V, NA)` or the equivalent one-sided form belongs in `non_comparable`
- a true unit mismatch means the base engineering unit differs after normalization, not merely that the target cell is incomplete

## 4. Scope Screening Belongs In The Read-Only Report

Embed the shared SPL scope screen directly in the compare output.

Reason:

- pre-update review should show likely non-bulk classes at the same time it shows direct compare buckets
- this keeps read-only review aligned with `spl-limit-workflow` instead of forcing a separate manual judgment path

The compare report should therefore carry both bucket counts and the `scope_screening` summary.

## 5. What This Compare Is For

Use the read-only compare to answer questions such as:

- which rows are already active and directly comparable in the target env
- which rows are held back because they are commented, absent, target-env-NA, or structurally partial
- whether a supposed unit problem is real or only a bucket-classification mistake

Do not treat this compare as a substitute for:

- SPL approval
- scope approval for bulk implementation
- the later `ls-updater` audit after a real edit

## 6. Recommended Pairing

Use this note together with:

- `spl_workflow_and_methodology.md` for SPL intent and approval context
- `spl_ls_updater_operational_rules.md` for the actual update-path guardrails
- the callable `.claude/skills/spl-readonly-compare/` skill when a machine-readable compare report is needed