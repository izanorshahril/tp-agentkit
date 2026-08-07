# Knowledge Registry

Use this file as the first stop before planning changes in this repository.

## Focus Routing

| Focus | Use when | First file |
|------|----------|------------|
| `TP-AgentKit` | the main subject is TP workflow, repo behavior, local skills, or current-task artifact policy | read the matching TP-AgentKit file below |
| `external tooling` | the main subject is VS Code, Copilot, Python, model, GitHub, network, or surrounding tooling behavior | start with `focus_boundaries.md`, then load the matching external file |

If the boundary is unclear, read `focus_boundaries.md` first.

## TP-AgentKit Focus

### Workflow Knowledge

| File | Use When | Notes |
|------|----------|-------|
| `artifact_family_promotion.md` | Reviewing one `.claude/artifacts/` family for retained review surface, evidence-only layers, and knowledge or skill promotion | Use during repo-maintenance harvest or closeout when one artifact family needs an explicit promotion call |
| `tp_reliability_workflow.md` | REL / reliability / return TP adaptation | Covers active-flow-first scoping, ATE-vs-DUT calibration distinction, EEPROM rewrite removal, REL history separation, and optional stress hardening |
| `tp_revision_patterns.md` | Revision copy / suffix / folder strategy | Use for standard revision-copy workflow |
| `repo_maintenance_closeout.md` | Closing out TP-AgentKit repo-maintenance work | Use when the work is on `.claude`, docs, tasks, skills, or artifacts rather than on `testprogram/` |
| `user_intake_keyword_map.md` | Sparse, keyword-led, or low-context first user prompts | Map likely intent, likely mode, and the smallest useful follow-up instead of forcing a full intake immediately |
| `tp_diff_compare.md` | Comparing source TP against reference TP | Good for minimal-delta reviews |
| `scr_special_tp_pattern.md` | SCR special TP preparation | Separate from REL workflow |
| `relative_test_esm.md` | Relative / ESM flow understanding | Do not mix with REL unless user asks |
| `continuous_improvement.md` | Deciding whether a lesson should become durable workflow or knowledge | Repo-level learning loop for TP-AgentKit itself |

### Reference Knowledge

| File | Use When | Notes |
|------|----------|-------|
| `limit_env_mapping.md` | Environment token inference | Use for FC/FA/FH/QC/EC mapping |
| `spl_workflow_and_methodology.md` | SPL / SPAT / PAT / Yield Explorer limit-review tasks | Use before planning SPL intake, exported-limit review, or TP implementation from YE outputs |
| `spl_ls_updater_operational_rules.md` | SPL LS updater semantics and tool-path choice | Use when applying approved SPL values into `.ls`, reviewing tighten-only behavior, or choosing between the local and external updater copies |
| `spl_readonly_compare.md` | SPL CSV versus `.ls` review before edits | Use when a read-only compare needs stable bucket semantics for active, commented, target-env-NA, absent, and non-comparable rows |
| `spl_csv_schema.md` | Real YE SPL CSV field semantics | Use when deciding which SPL CSV columns should drive TP implementation, why two exports differ structurally, or when the filename and `TestProgram` imply different variants |
| `spl_reference_families.md` | Quick family grouping for retained SPL reference CSVs | Use when a new SPL request starts from a filename and you need the fastest safe read on header family, fail-field pattern, or filename-versus-`TestProgram` guard strength |
| `constraints.md` | Repository constraints and protected areas | Re-check before edits |
| `duplicate_test_pattern.md` | Duplicate-test handling | Use when adding or comparing repeated tests |
| `otpl_source_vs_runtime_coverage_triage.md` | CSV or output mismatch against OTPL source | Separates source presence, flow reachability, and runtime coverage |
| `stdf_csv_intake_and_learning.md` | STDF CSV analysis where header, row, or alias meaning is ambiguous | Ask the user one schema question at a time, prefer file-proof over guesses, and promote recurring answers into durable knowledge |
| `stdf_first_mixed_incident_triage.md` | Mixed reject and stop incidents | Use when runtime interruption and fallout are interleaved |
| `t2k_rte_stack_narrowing.md` | SystemController or runtime stack narrowing | Use from wrapper error down to TP source |

## External Tooling Focus

| File | Use When | Notes |
|------|----------|-------|
| `focus_boundaries.md` | The task mixes repo-maintenance and external-tooling subjects | Primary classifier for the two-lane split |
| `platform.md` | Host OS, shell, framework, and file-type awareness | External environment reference before terminal or tool use |
| `copilot_session_harvest_patterns.md` | Repo-maintenance learning is being harvested from Copilot session logs | Use after multi-session Copilot work to decide what should move into knowledge, tasks, or skills |
| `toolkit_harvested_modules.md` | Comparing sibling toolkits or deciding whether to absorb external modules | Cross-toolkit maintenance reference |

## Planning Rule

Before drafting a plan:

1. classify the focus as `TP-AgentKit` or `external tooling`
2. read `focus_boundaries.md` first if the lane is unclear
3. read the matching knowledge file here
4. then inspect the codebase and active flow

Do not plan REL work from generic assumptions when `tp_reliability_workflow.md` already applies.