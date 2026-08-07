---
name: TP-AgentKit
version: "5.0"
description: "Autonomous Test Program Development Framework"
---

# TP-AgentKit

> Maintainer and agent quick reference. User onboarding lives only in `README.md`.

---

## Open First

| Need | Primary home | Use when |
|------|--------------|----------|
| User quickstart and prompt starters | `README.md` | onboarding or first-turn user guidance |
| Active workflow and edit policy | `.claude/rules/workflows.md` | any TP task or repo-maintenance workflow decision |
| Risk-task pressure-test guidance | `.claude/skills/grill-me/SKILL.md` | after a draft plan exists for medium-risk or high-risk TP work |
| Completion evidence gate | `.claude/skills/verification-before-completion/SKILL.md` | before saying a TP task is complete, validated, or ready to release |
| Knowledge selector | `.claude/knowledge/_registry.md` | before planning or broad discovery |
| Focus boundary selector | `.claude/knowledge/focus_boundaries.md` | maintainer work that may be about TP-AgentKit itself or about surrounding tooling such as VS Code, Copilot, Python, or GitHub |
| Constraints and protected areas | `.claude/knowledge/constraints.md` | before edits, cleanup, or risky moves |
| Skill catalog | `.claude/skills/_registry.md` | to find callable or behavior-only skills |
| Command presets | `.claude/tasks.json` | to run maintained repo commands |
| Repo-maintenance closeout | `.claude/knowledge/repo_maintenance_closeout.md` | after work on docs, rules, skills, knowledge, tasks, or artifacts |
| Active task resume surface | `.claude/artifacts/current_task/INDEX.md` | to resume or update the current working set; start at the top `Resume Now` section |

Questioning route:

- use `.claude/rules/workflows.md` for the repo-wide rule: inspect recoverable facts first, ask the user only when the remaining branch still changes execution, validation scope, or release confidence
- use `.claude/skills/grill-me/SKILL.md` when that questioning needs to become an explicit pressure-test for medium-risk or high-risk work

This file routes maintainers to the owning surface. It is not the source of truth for workflow policy, reusable knowledge, skill behavior, or task history.

### IDE Support

TP-AgentKit standardizes on `.claude/`.
Cursor and VS Code both support `.claude` natively, with no extra IDE-specific configuration.

### Path Conventions

To reduce repetition in internal docs under `.claude/`, use relative paths when possible.

- In `.claude/skills/*.md`: prefer `./` for skill-local paths
- Use absolute-style `.claude/...` paths in top-level docs (`AGENTS.md`, `README.md`) for readability

Execution guidance is now carried by `.claude/rules/`, `.claude/skills/`, and `.claude/knowledge/` directly. Tracked agent-definition files are no longer part of the maintained framework surface.

## Maintainer Sequence

- classify maintainer work as `TP-AgentKit` or `external tooling` first; use `.claude/knowledge/focus_boundaries.md` when the boundary is unclear
- read `.claude/knowledge/_registry.md` first
- load the matching rule or knowledge file before planning
- when resuming maintainer work, open the top of `.claude/artifacts/current_task/INDEX.md` before scanning older follow-through notes
- when the user asks for the same change on a sibling TP variant, reuse the prior variant's verified findings first and widen discovery only where the new flow differs
- for medium-risk or high-risk tasks, run a short `grill-me` pass after the draft plan and before approval or execution
- create a compact reusable checkpoint before broad follow-on variant work when the first pass already established a strong risk map
- before any completion, validation, or release claim, run `verification-before-completion`
- inspect the codebase or TP only after the right guidance is loaded
- keep user-facing instruction in `README.md`, not here
- keep durable policy in rules or knowledge, not in task artifacts

## Extension Points

- new workflow or enforcement rule: `.claude/rules/`
- new durable cross-task guidance: `.claude/knowledge/` plus `_registry.md`
- new callable or behavior-local capability: `.claude/skills/<skill>/` with `SKILL.md`, implementation, `test_skill.py`, and registry entry
- new internal shared support module for multiple skills: `.claude/skills/_*.py`; keep it non-callable and move only repo-generic helper logic there
- new task-local note or handoff: `.claude/artifacts/current_task/`

Keep skill folders flat and use the registries and indexes to separate `TP-AgentKit` focus from `external tooling` focus.

Do not let artifacts become the long-term source of truth when the content really belongs in rules, knowledge, or a skill.

## Repo-Maintenance Closeout

Use `.claude/knowledge/repo_maintenance_closeout.md` for the maintained closeout path and `.claude/tasks.json` for the command presets that run it.

---

*Keep user onboarding in `README.md`. Keep maintainer routing in `AGENTS.md`. Keep real policy, knowledge, skill behavior, tasks, and task history under `.claude/`.*
