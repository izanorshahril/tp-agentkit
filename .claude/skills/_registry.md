# Skills Registry

This directory contains maintained skills that agents can use. Each skill is a self-contained folder with a `SKILL.md` definition and, for callable skills, an implementation script.

Keep skill folders flat under `.claude/skills/<name>/`. Focus separation lives in this registry, not in nested folders.

## Status Levels

| Status | Meaning | Can Use? |
|--------|---------|-------------|
| **stable** | Fully implemented and tested | Yes |
| **beta** | Implemented but may have issues | Yes, with caution |
| **planned** | NOT IMPLEMENTED - placeholder only | **NO - Do not invoke** |

## Promotion To Stable

Use these gates before changing a Python skill from **beta** to **stable**.

1. `--help` startup smoke passes.
2. At least one functional smoke case exists for the main success path.
3. No active editor diagnostics remain in the shipped files.
4. `SKILL.md` documents at least one important failure mode, limit, or misuse case.

If a skill does not meet all four gates, keep it as **beta** even if it is already useful.

## Focus Lanes

| Focus | Meaning | Typical examples |
|------|---------|------------------|
| `TP-AgentKit` | The skill changes TP workflow, local repo behavior, or reusable capability maintained inside this repo | revision helpers, analyzers, audits, reporting, skill-authoring guidance |
| `external tooling` | The main subject is VS Code, Copilot, Python, or model or token behavior around the repo | Copilot session harvesting, token-efficiency measurement |

## TP-AgentKit Focus Skills

| Skill | Folder | Description | Status |
|-------|--------|-------------|--------|
| Diff Converter | [diff-converter/](diff-converter/) | Convert external patch or diff material into workspace-friendly compare artifacts | **beta** |
| Doc Path Audit | [doc-path-audit/](doc-path-audit/) | Audit docs and text artifacts for missing workspace-looking path literals while classifying placeholders, outputs, and historical notes separately | **beta** |
| T2K Cfg-To-Ini Generator | [t2k_cfg_to_ini_generator/](t2k_cfg_to_ini_generator/) | Generate T2K `.ini` launch files from `.cfg` with auto RDK or OTPL detection | **beta** |
| LS Updater | [ls-updater/](ls-updater/) | Update `.ls` limit sheets from structured input while preserving TP formatting | **beta** |
| System Controller Log Analyzer | [system_controller_log_analyzer/](system_controller_log_analyzer/) | Parse SystemController `.log`, `.txt`, or `.bak` files into JSON summaries, Pareto counts, and optional CSV export | **beta** |
| Tester Result Core | [tester_result_core/](tester_result_core/) | Shared ingestion and normalization helpers for STDF-derived CSV and structured tester datalog TXT | **beta** |
| Tester Result Analyzer | [tester_result_analyzer/](tester_result_analyzer/) | Generic analyzer for standard tester result sources with summary, site-skew, and test-coverage modes | **beta** |
| Pin-Key Checker | [pin_key_checker/](pin_key_checker/) | Detect `StorePinMeasurement` PinName-vs-MeasValue naming mismatches in OTPL `.tpl` files | **beta** |
| Relative Test ESM STDF CSV Validator | [relative_test_esm_stdf_csv_validator/](relative_test_esm_stdf_csv_validator/) | Replay ESM relative-test outputs against STDF CSV exports using TP source/judge ID mappings | **beta** |
| TP Diff Compare | [tp_diff_compare/](tp_diff_compare/) | Compare two TP folders recursively and report whole-folder per-file deltas with optional filters and unified diffs | **beta** |
| SCR Special TP Audit | [scr_special_tp_audit/](scr_special_tp_audit/) | Audit an RDK SCR overlay folder for expected SCR launch files, SCR_MODE declarations, and runtime gating markers | **beta** |
| RDK Job Clone | [rdk_job_clone/](rdk_job_clone/) | Clone an RDK launch-package file set from one job token to another and rewrite internal references consistently | **beta** |
| SPL Limit Workflow | [spl-limit-workflow/](spl-limit-workflow/) | Classify SPL, SPAT, and Yield Explorer limit inputs into the safest next TP limit-update step before invoking `ls-updater` | **beta** |
| SPL Read-Only Compare | [spl-readonly-compare/](spl-readonly-compare/) | Compare an SPL CSV against a target `.ls` file without editing it and classify rows into active, commented, target-env-NA, absent, and non-comparable review buckets | **beta** |
| Limit Population Screening | [limit-population-screening/](limit-population-screening/) | Compare before/after `.ls` limits against population stats, build keep-or-revert follow-up tables, and compare action tables across populations | **beta** |
| User Intake Router | [user_intake_router/](user_intake_router/) | Predict likely mode, intent, and minimal follow-up questions from sparse TP-AgentKit first prompts | **beta** |
| Grill Me | [grill-me/](grill-me/) | User-facing pressure-test for medium-risk and high-risk TP plans, review scope, release decisions, and ambiguous STDF CSV schema analysis one question at a time after task anchors are known | **beta** |
| Verification Before Completion | [verification-before-completion/](verification-before-completion/) | Require fresh TP-specific evidence before claiming a task is complete, fixed, validated, or release-ready | **beta** |
| Compact Reporting | [compact-reporting/](compact-reporting/) | Behavior-only low-token writing skill for plans, walkthroughs, diff notes, and handoff artifacts | **beta** |
| Design an Interface | [design-an-interface/](design-an-interface/) | Compare multiple interface shapes for new skills, helper modules, and machine-output contracts before implementation | **beta** |
| Improve Codebase Architecture | [improve-codebase-architecture/](improve-codebase-architecture/) | Audit TP-AgentKit for deep-module opportunities, duplicated helper logic, and clearer local refactor candidates | **beta** |
| Local Artifact Compress | [local-artifact-compress/](local-artifact-compress/) | Closed-environment markdown and text compactor with conservative validation and optional in-place backup workflow | **beta** |
| PRD To Plan | [prd-to-plan/](prd-to-plan/) | Turn a maintainer brief into tracer-bullet phases and a dated local plan artifact instead of a GitHub issue | **beta** |
| TDD | [tdd/](tdd/) | Apply red-green-refactor to TP-AgentKit Python tooling using boundary-focused tests and the local skill harness | **beta** |
| Ubiquitous Language | [ubiquitous-language/](ubiquitous-language/) | Standardize TP-AgentKit domain terminology into local knowledge or artifacts and flag ambiguous wording | **beta** |
| Write a Skill | [write-a-skill/](write-a-skill/) | Standardize TP-AgentKit skill authoring, validation, and surface selection for new or harvested skills | **beta** |

## External Tooling Focus Skills

| Skill | Folder | Description | Status |
|-------|--------|-------------|--------|
| Copilot Session Log Harvester | [copilot_session_log_harvester/](copilot_session_log_harvester/) | Harvest GitHub Copilot debug session logs into cross-session summaries, token/tool stats, and reusable maintenance signals | **beta** |
| Token Efficiency Benchmark | [token-efficiency-benchmark/](token-efficiency-benchmark/) | Measure character and proxy-token savings from maintained compaction and compact machine-output paths, plus local runtime-sanity signals for the proof and harvest paths | **beta** |

> **WARNING**: Check `status` in each SKILL.md before use.

## Adding New Skills

To add a new skill:

1. Classify the skill as `TP-AgentKit` or `external tooling` first; use `.claude/knowledge/focus_boundaries.md` if the boundary is unclear
2. Create a new flat folder in this directory (e.g., `my_skill/`)
2. Add these files:
   - `SKILL.md` - Skill definition (required)
    - `test_skill.py` - Skill-local regression entrypoint
    - Implementation script (`.py`, `.bat`, `.ps1`, etc.) when the skill is callable
3. Update the status to `stable` or `beta` when implemented
4. Add an entry to the correct focus table in this registry

## Skill Folder Structure

```
./
└── skill_name/
    ├── SKILL.md          # Skill definition (required)
    ├── test_skill.py     # Skill-local regression tests
    └── script.py         # Implementation for callable skills only
```

## How Skills Are Invoked

1. Agent identifies need for a skill based on task
2. Agent reads `./<skill_name>/SKILL.md` for interface or behavioral guidance
3. If the skill is callable, the agent executes it with appropriate parameters
4. If the skill is behavior-only, the agent applies the guidance directly
5. Agent processes the output or resulting workflow guidance
6. Agent records the skill use in walkthrough when relevant


