---
type: methodology
status: partial
verifier: session-harvest evidence from local Copilot debug logs
date: 2026-04-14
source: ".claude/artifacts/current_task/tp-agentkit-copilot-session-harvest-latest.md; .claude/artifacts/current_task/tp-agentkit-copilot-session-harvest-latest.json"
source_note: "The original dated 2026-04-14 harvest note is not retained under the current workspace path set."
sessions_scanned: 10
---

# Copilot Session Harvest Patterns

Use this file when improving TP-AgentKit from repeated local Copilot sessions instead of from a single task artifact.

## What To Promote

Promote a pattern into durable repo knowledge when all three conditions are true:

1. it appears across multiple sessions rather than one incident
2. it points to a reusable repo-maintenance surface rather than one TP folder
3. it changes how future planning, search, editing, or validation should be done

Keep the finding in `.claude/artifacts/current_task/` when it is still task-local, approval-local, or tied to one TP release.

For TP-change work, be more aggressive about reviewing touched current-task artifacts. If a TP-support note captures a reusable structure, validation, or workflow lesson, promote that lesson even when the raw TP files remain excluded from durable harvesting.

## What The April 14 Harvest Showed

The first cross-session harvest highlighted these reusable surfaces most often:

- `README.md`
- `AGENTS.md`
- `.claude/rules/workflows.md`
- `.claude/knowledge/_registry.md`
- `.claude/tasks.json`
- `.claude/skills/compact-reporting/SKILL.md`
- `.claude/skills/tp_diff_compare/SKILL.md`

Treat these as high-value maintenance surfaces when the goal is lower token use, clearer onboarding, or less repeated repo discovery.

The user-workflow and prompt-template content was later folded into `README.md`, so treat older split-doc signals as part of the `README.md` onboarding surface now.

## Promotion Filters

When harvesting Copilot debug logs into reusable knowledge, exclude these by default:

- `testprogram/`
- `references/`
- path-like directory names without a concrete file leaf

Those raw source or evidence surfaces still matter for active work, but they create noisy long-tail results when the goal is durable framework knowledge.

Do not blanket-exclude `.claude/artifacts/current_task/` from review. Instead:

- keep rolling `*-latest.*` helper outputs and `INDEX.md` out of promotion candidates
- review touched TP-support artifacts under `current_task/` as promotion inputs
- summarize the reusable lesson into knowledge, a rule, or a skill rather than treating the artifact itself as the long-term source of truth

## Repeated Workflow Signals

The first harvest showed these repeated tool chains:

- `read_file -> grep_search`
- `file_search -> grep_search`
- `apply_patch -> get_errors`
- `list_dir -> read_file`

Translate them into working defaults:

1. search before deep reading when the target surface is still ambiguous
2. convert repeated maintenance commands into tasks or skills when they recur across sessions
3. validate immediately after edits instead of leaving diagnostics to the end

## Practical Repo-Maintenance Rules

### Planning

- start from `.claude/knowledge/_registry.md` before drafting workflow or repo-maintenance changes
- prefer promoting repeated lessons into `.claude/knowledge/` over keeping them only in one task artifact

### Artifact Discipline

- keep active execution history in `.claude/artifacts/current_task/`
- move only the reusable part of a lesson into `.claude/knowledge/`
- do not treat current-task artifacts as the long-term source of truth when the lesson has already stabilized

### Skill And Task Surfacing

- add or refine a skill when a repeated pattern needs structured parsing or domain-specific validation
- add a task when the command is stable and users benefit from a low-friction rerun path

## Limits

- session frequency is evidence, not policy by itself
- safety rules for TP edits still come from `.claude/rules/workflows.md` and `constraints.md`
- the harvester summarizes existing local logs only; it does not auto-capture future sessions

## Recommended Next Uses

- use the harvester after a cluster of repo-maintenance sessions
- review `knowledge_candidates` first for promotion targets
- review `artifact_promotion_candidates` next when TP-change or TP-review notes were part of the working set
- review `automation_candidates` next for task or skill opportunities
- keep TP-specific findings in task artifacts unless they clearly generalize across programs