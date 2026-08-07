---
type: operational_pattern
status: verified
verifier: direct helper validation plus FC and FH rerun evidence
date: 2026-04-27
source: ".claude/artifacts/current_task/uae7-fc-fh-spl-tighten-only-rule-20260424.md; .claude/artifacts/current_task/uae7_release_limit_audit.py; .claude/artifacts/current_task/uae7_fc0012_ftc_release_audit_20260424.json; .claude/artifacts/current_task/uae7_fh0010_fth_release_audit_20260424.json; .claude/artifacts/current_task/uae7_spl_real_ls_visual_review_20260427.md; .claude/artifacts/current_task/uae7_spl_real_ls_rule_snapshot_20260427.md; .claude/artifacts/current_task/uae7_goodpop_before_after_histograms_20260427.md; .claude/artifacts/current_task/uae7_spl_csv_vs_release_goodpop_note_20260427.html; tester-toolkit-t2k/ls-updater/ls_updater.py; .claude/skills/ls-updater/ls_updater.py"
source_artifacts_files: 8
---

# SPL LS Updater Operational Rules

Use this note when applying approved SPL limits into an `.ls` file, reviewing `ls-updater` output, or deciding which updater path is safe for a given LS format.

This note captures verified updater behavior from the UAE7 FC `0012` and FH `0010` SPL rerun work. It is operational guidance for limit-application behavior, not a replacement for `spl_workflow_and_methodology.md`.

## 1. Tighten-Only Contract

When SPL is being applied in tighten-only mode:

- lower limits must round upward toward a tighter lower bound
- upper limits must round downward toward a tighter upper bound
- if a proposed or rounded value would relax the existing LS limit, keep the original LS value instead

Interpretation rule:

- `LL` must never move to a looser value after formatting or rounding
- `UL` must never move to a looser value after formatting or rounding

This clamp is the final guard. Even if the incoming SPL number, scaling, or rounding step suggests a relax direction, the emitted LS value must stay at the original limit.

## 2. Precision And Formatting Rule

For the default `none` precision mode:

- follow the displayed decimal precision already present in the target LS row
- preserve the displayed width, including trailing zeros
- do not emit source-style long decimals when the LS row uses a shorter displayed width

Why this matters:

- numeric equivalence alone is not enough for TP review
- mismatched decimal width creates noisy diffs and can make a valid tighten look like an uncontrolled formatting change

## 3. Minimum Validation Set

When changing or reviewing updater behavior, validate at least these cases:

1. a normal tighten case for `LL` and `UL`
2. a relax-guard case where the proposed value must clamp back to the original LS value
3. a trailing-zero case where the formatted output must preserve the original LS display width
4. a zero-result or zero-crossing case where the tightened output reaches `0` and still keeps the target LS formatting contract instead of escaping into long-decimal or inconsistent zero text

Treat any failure in decimal-width preservation or relax guarding as a real regression, even if the underlying floating-point number is close.

When the updater is following the target LS display width, add a post-update decimal-width audit against the exact no-SPL baseline:

- compare display width against the original baseline, not only numeric equivalence
- treat `baseline NA -> current numeric` as a non-actionable width exception because there was no original numeric width to preserve
- enumerate any remaining decimal-width mismatches explicitly before sign-off instead of assuming they are harmless

For UAE7-style SPL landings, the release audit should also distinguish these result classes instead of collapsing everything into one mismatch count:

- `relaxations`
	- must stay `0`; any positive count is a release blocker for tighten-only work
- `decimal_width_mismatches_on_changed_values`
	- actionable formatting regressions on changed numeric values; review individually before sign-off
- `decimal_width_mismatches_same_value`
	- formatting-only drift where the numeric value did not change; still audit, but treat separately from value changes
- `baseline_non_numeric_to_numeric`
	- expected only when the baseline had no numeric width to preserve, such as `NA -> numeric`; do not count these as decimal-width regressions by default
- `numeric_to_non_numeric`
	- high-risk backward movement from numeric to non-numeric; treat as a real defect unless the approved scope explicitly says otherwise
- `unit_mismatches`
	- must stay `0` for same-base update work; any positive count means the release audit and the updater disagree about engineering-unit preservation
- `current_numeric_positions_with_trailing_space`
	- formatting noise worth tracking because it can create misleading diffs and should be cleaned if the emitted helper or updater path starts widening it
	- keep this separate from decimal-width regressions; trailing-space noise is reviewable formatting residue, not proof that the numeric width contract failed

Also check shared test coverage directly:

- `missing_in_current` and `extra_in_current` must stay empty for structure-preserving limit-only release landings
- duplicate test IDs in the audit input are not expected; treat them as an audit-surface anomaly that should be resolved before release confidence is claimed

## 4. Full-Input Provenance Rule For Screened Bulk Reruns

If an operational rerun uses a screened bulk CSV instead of the full reference SPL CSV:

- report the rerun counts as screened-subset counts only
- reconcile the subset back to the full reference CSV with the paired workflow report and bulk or review CSV outputs
- keep held-back rows visible through `review_reason_counts` or equivalent workflow evidence; do not imply the updater processed the whole reference population

## 5. Baseline Selection Rule For SPL Reruns

For SPL reruns or regenerated compare evidence:

- rerun from the preserved no-SPL baseline when one exists
- do not reuse an already modified TP tree as the new source of truth for a second SPL pass
- compare each edited LS against its exact no-SPL counterpart for that same variant

This keeps the diff limited to approved SPL tightening instead of mixing in prior edits.

## 6. Updater Path Selection For UAE7-Style LS Files

The current updater paths are not equivalent for UAE7 LS parsing.

- `.claude/skills/ls-updater/ls_updater.py` is the verified working path for UAE7 `T... { ... }` environment-block rows
- `tester-toolkit-t2k/ls-updater/ls_updater.py` can share logic changes, but it is not yet operational for UAE7 application unless its parser is extended to recognize that row structure

Current verified limitation:

- JSON-safe reporting fixes alone do not make the external updater usable for UAE7 LS application
- parser support is the real blocker

## 7. Released-Limit Interpretation Rule

When the question is about landed SPL behavior rather than about the candidate CSV itself:

- use the actual before-SPL and after-SPL `.ls` files as the only limit authority
- treat the reference SPL CSV as statistical context or training context, not as the final release-side authority
- if the real after-SPL `.ls` diverges materially from the reference CSV after limits, do not keep using the older CSV-only SPL pack as the main release interpretation surface

For later-population checks such as GOODPOP:

- treat summed row-level projected fail percentages as release-screening signals across changed tests, not as literal single-pass yield numbers
- read target-window improvement and fallout increase together; more rows inside the `3.5-4.0` Cpk band does not by itself prove the release is safe
- keep the question-specific surfaces separate when they answer different things:
	- real `.ls` plus reference-statistics view for what actually landed
	- GOODPOP view for what the landed limits may do on a later population
	- after-limit mismatch review for where the real after-SPL `.ls` no longer matches the reference CSV SPL columns

Verified repo example:

- the April 27 UAE7 review showed that the real after-SPL `.ls` limits diverged from the reference CSV after limits on `931` rows overall
- that made the real `.ls` view the authoritative release-interpretation surface while the GOODPOP report stayed a later-population screening surface
- the same review also confirmed that the aggregate fail totals from row-level projections should not be read as literal one-pass yield

## 8. When To Load This Note

Load this note before planning when the task involves any of these:

- applying approved SPL CSV output into an LS file
- explaining why an updater output appears numerically right but formatting-wrong
- reviewing whether an updater result relaxed a limit by mistake
- deciding whether the external toolkit updater or the local TP-AgentKit updater should be used
- rerunning SPL from preserved `_WITHOUT_SPL` or other no-change baselines

Use this note together with:

- `spl_workflow_and_methodology.md` for SPL intent, approval, and review context
- `spl_csv_schema.md` for CSV field semantics and which columns drive LS updates
- `.claude/skills/limit-population-screening/SKILL.md` when the landed before/after `.ls` pair needs population screening or action-table comparison after release
- `constraints.md` for protected-area and revision-safety rules

## 9. What Not To Generalize

- Do not assume every LS family uses the UAE7 row structure.
- Do not assume every SPL task is tighten-only unless the approved scope says so.
- Do not treat local tool availability, such as Beyond Compare CLI presence, as durable workflow knowledge unless that environment dependency becomes a repeated repo-wide constraint.