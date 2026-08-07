---
type: index
status: partial
verifier: repo-maintained
date: 2026-03-31
---

# Knowledge Index

Landing index for durable reusable knowledge under `.claude/knowledge/`.

Use this file first when deciding whether a lesson is already captured as reusable guidance, versus still being a proposal or a historical artifact.

## Focus Lanes

- `TP-AgentKit`
  - TP workflows, repo-maintenance behavior, local reusable skills, artifact policy, and framework rules
- `external tooling`
  - VS Code, Copilot, Python, model, GitHub, network, or sibling-tooling behavior around this repo
- `focus_boundaries.md`
  - use when the lane is unclear before filing a new note or artifact

## TP-AgentKit Durable Knowledge

- `artifact_family_promotion.md`
  - method for turning one artifact family into a canonical retained review surface plus evidence-only, knowledge, or skill promotion decisions

- `duplicate_test_pattern.md`
  - verified pattern for splitting one setup into explicit companion tests while preserving TP-specific limits

- `limit_env_mapping.md`
  - confirmed environment-token mapping for COLD, ROOM, HOT, and ALL requests

- `spl_workflow_and_methodology.md`
  - SPL training harvest covering purpose, Yield Explorer workflow, MADe plus Johnson Fit concepts, implementation cautions, and support escalation expectations

- `spl_ls_updater_operational_rules.md`
  - verified operational rules for tighten-only SPL LS updates, original-LS decimal formatting, baseline rerun choice, and the current UAE7 parser boundary between the local and external updater copies

- `spl_csv_schema.md`
  - real YE SPL CSV schema note covering `Scaled_LSPL` or `Scaled_USPL` usage, unit and scale columns, fail-field variation or absence, `Seq`-style review columns, and `TestProgram` versus filename variant checks

- `spl_reference_families.md`
  - quick grouping of the retained SPL CSV examples by header family, fail-field pattern, and filename-versus-`TestProgram` variant-guard strength

- `relative_test_esm.md`
  - ESM relative-test theory, validation paths, platform notes, and workbook fallback guidance

- `otpl_source_vs_runtime_coverage_triage.md`
  - OTPL method for separating source presence, flow reachability, and runtime-output coverage when CSV and source disagree

- `stdf_csv_intake_and_learning.md`
  - STDF CSV ask-first schema workflow that uses `grill-me` for ambiguous headers, rows, aliases, and recurring user-confirmed meanings

- `scr_special_tp_pattern.md`
  - RDK SCR-only overlay, runtime-flag, validation, and scope-rollback pattern

- `stdf_first_mixed_incident_triage.md`
  - mixed production incident method for separating runtime-stop behavior from real reject fallout, including good-versus-bad export limit-header compare to separate deployed-limit drift from DUT-signature drift

- `t2k_rte_stack_narrowing.md`
  - T2000 runtime-error narrowing method from wrapper message to low-level stack and TP source

- `tp_diff_compare.md`
  - whole-TP and filtered compare workflow for retained baseline review, including section-based reporting for mixed-family TPs, import-scoped overlay review, and stale-HTML snapshot handling after live repairs

- `tp_revision_patterns.md`
  - revision-copy preparation patterns, lean cleanup, OTPL relative-test integration checklist, naming-equivalent clone pattern, paired AGR/AMK family interpretation, repeated-region `.ls` rollout repair/audit guidance including unchanged-set checks, folder-wide `JOB_REV` normalization sweep after up-rev audit, and official-release versus unconfirmed-branch split guidance

- `constraints.md`
  - quick pre-edit boundaries for protected areas, revision safety, and safe-edit workflow rules

- `continuous_improvement.md`
  - framework-level learning loop, extraction triggers, and KB or rule update criteria

## External Tooling Knowledge

- `focus_boundaries.md`
  - classifier for TP-AgentKit-versus-tooling placement across skills, knowledge, and artifacts

- `platform.md`
  - quick host environment reference across supported shells, file types, and workspace assumptions

- `copilot_session_harvest_patterns.md`
  - Copilot-session harvest lessons, promotion boundaries, and repo-maintenance tuning signals

- `toolkit_harvested_modules.md`
  - inventory note for modules harvested from sibling toolkits; treat as maintenance-sensitive reference rather than stable TP pattern knowledge

## Process And Framework Meta

- `improvements/_registry.md`
  - status table for unintegrated or pending improvement reports; these are proposals, not durable verified knowledge

## Improvement Proposals

Improvement reports live under `improvements/` and are intentionally separate from durable knowledge.

- `improvements/stdf_first_mixed_incident_triage_skill_20260318.md`
  - proposal for promoting mixed incident triage into a callable skill

- `improvements/systemcontroller_rte_stack_mapper_20260330.md`
  - proposal for tooling that maps low-level SystemController runtime errors back to TP source

- `improvements/ls_updater_repeated_family_audit_mode_20260407.md`
  - proposal for extending the existing `ls-updater` workflow with an audit-only repeated-family structure-check mode

- `improvements/tp_diff_compare_engineering_plus_launch_preset_20260412.md`
  - proposal for adding an engineering-plus-launch preset to the existing TP diff compare skill

- `improvements/tester_result_analyzer_two_run_limit_header_compare_20260412.md`
  - proposal for adding a two-run limit-header compare mode to the tester result analyzer workflow

- `improvements/uq29_relative_flow_and_parse_pitfalls_20260223.md`
  - integrated report retained as historical improvement record

## Archive Relationship

If the lesson came from a finished one-off task, also check `.claude/artifacts/archive/INDEX.md` to see whether the durable knowledge was already extracted and where the historical source artifact lives.
