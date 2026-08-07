---
type: reference
status: verified
verifier: repo-maintained static cross-check
date: 2026-04-21
source: "AGENTS.md; .claude/rules/01-agentkit.mdc; .claude/rules/02-protocol.mdc; .claude/rules/workflows.md; .claude/skills/_registry.md; .claude/knowledge/_registry.md; .claude/artifacts/current_task/INDEX.md"
---

# Focus Boundaries

Use this file when a maintainer task touches `.claude/`, docs, tasks, or repo-maintenance artifacts and you need to decide whether the main focus is `TP-AgentKit` or `external tooling`.

## Two Focus Lanes

| Lane | Primary subject | Typical examples |
|------|-----------------|------------------|
| `TP-AgentKit` | TP workflows, repo rules, local skill behavior, current-task artifact policy, and repo-specific maintenance | revision handling, skill authoring, doc-path audit policy, closeout flow, reusable TP analysis skills |
| `external tooling` | VS Code, Copilot, Python environment or packages, model behavior, GitHub or network issues, and editor or workspace tooling around this repo | Copilot session harvesting, token benchmarking, Python install notes, DNS or auth diagnostics |

## Classification Rule

- classify by the main subject of the note, not by which repo it lives in
- if the repo disappeared and the lesson would still make sense as a VS Code, Python, Copilot, model, GitHub, or network note, classify it as `external tooling`
- if the change mainly updates TP-AgentKit behavior, routing, guardrails, docs, or reusable local skills, classify it as `TP-AgentKit`
- when a task mixes both, classify by the main question the user asked and cross-link the other lane instead of collapsing them together

## Surface Rules

### Skills

- keep every maintained skill folder directly under `.claude/skills/<name>/`
- do not create nested focus folders under `.claude/skills/`; registry lookup, tests, and wrapper paths assume the flat layout
- separate focus in `.claude/skills/_registry.md` using the focus tables there

### Knowledge

- keep verified top-level knowledge flat unless a durable namespace already exists for another reason, such as `improvements/`
- separate focus in `.claude/knowledge/_registry.md` and `.claude/knowledge/INDEX.md`
- make the opening summary explicit about whether the file is TP-AgentKit guidance or external-tooling guidance

### Artifacts

- keep `.claude/artifacts/current_task/` flat because rolling outputs and helper scripts write to fixed paths there
- separate focus through `current_task/INDEX.md`, subject-first artifact names, and summary text
- prefer `tp-agentkit-<topic>-<date>.md` for repo or framework notes whose main subject is TP-AgentKit itself
- prefer tool-first or platform-first names such as `copilot-<topic>-<date>.md`, `vscode-<topic>-<date>.md`, `python-<topic>-<date>.md`, `github-<topic>-<date>.md`, or `workspace-<topic>-<date>.md` for external-tooling notes
- when `archive/INDEX.md` mixes maintainer notes with completed TP delivery history, keep the `TP-AgentKit` and `external tooling` split for maintainer notes and add a separate TP-support or program-history section instead of forcing TP records into the maintainer lanes
- keep established rolling-output filenames when wrapper code, tasks, tests, or docs already depend on the exact path; classify them in the index instead of renaming them casually
- do not rename older artifacts just to force taxonomy; classify them correctly in the index instead

## Quick Placement Examples

| Item | Preferred focus | Why |
|------|------------------|-----|
| `grill-me` workflow guidance | `TP-AgentKit` | it changes local TP planning and approval behavior |
| repo closeout rules | `TP-AgentKit` | they change this repo's maintained operating procedure |
| Copilot session harvest outputs | `external tooling` | the main subject is Copilot session behavior around the repo |
| Python package bootstrap note | `external tooling` | the main subject is environment setup, not TP logic |
| GitHub DNS or auth diagnosis | `external tooling` | the issue lives in network or credential tooling, not TP-AgentKit behavior |

## Anti-Patterns

- do not create nested focus folders such as `skills/tp-agentkit/...` or `skills/external/...`
- do not split rolling artifacts into nested focus folders unless the wrapper scripts are updated first
- do not classify only by filename prefix; several historical `tp-agentkit-*` artifacts are really external-tooling notes by subject