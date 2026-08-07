---
type: reference
status: verified
verifier: repo-maintained static cross-check
date: 2026-04-06
source: "AGENTS.md; .claude/rules/00-bootstrap.mdc; .claude/rules/01-agentkit.mdc; .claude/rules/02-protocol.mdc; .claude/rules/workflows.md"
---

# Repository Constraints

Quick pre-edit reference for repository boundaries, protected areas, and non-negotiable workflow rules.

Use this together with `./_registry.md` and `../rules/workflows.md`, not as a replacement for them.

## When To Re-Check This File

- before planning any edit under `testprogram/`
- before changing shared or framework-managed files
- when deciding whether a request is safe to do in place

---

## Core Workflow Constraints

1. Ask first which revision to use, or whether a new revision copy should be created, before any TP copy or edit.
2. Default to the revision-copy workflow: keep the source folder unchanged and edit only the confirmed working copy.
3. Use in-place backup handling only when the user explicitly requests in-place or backup-based work.
4. Present a plan and wait for explicit approval before executing file modifications.
5. Do not conclude a TP folder is missing from one exact-path check; follow the discovery workflow in `../rules/workflows.md`.

---

## Protected Areas

| Area | Constraint | Why |
|------|------------|-----|
| `CommonLib/` | Never modify | Shared across programs |
| Original `testprogram/<program>_<rev>/` source folder | Do not modify in place by default | Preserves baseline and supports side-by-side diff |
| `.claude/rules/`, `.claude/skills/`, `.claude/knowledge/` | Treat as maintainer-controlled framework internals | Changes should be deliberate and human-reviewed |
| `*History.txt` | Append new entries only at the bottom | Preserves chronology and diff readability |

---

## File-Order And Reference Constraints

- Apply edits in this dependency order: `bdefs -> ls -> flow -> code`
- Define tests before flow references them
- Never reference undefined tests from flow or code
- Update history when `JOB_REV` changes
- Compare each edited variant against its own baseline, not against a different flow variant

---

## Limit-Sheet Constraints

- Verify scale token and engineering unit before changing LL/UL values
- Treat limit-only edits as structure-preserving unless the user explicitly requested added or removed tests
- Audit touched test-ID occurrence counts against the baseline
- Inspect neighboring unchanged blocks after patching repeated or similar regions
- Inspect the file tail and footer after manual edits
- Use compare output as a structure gate, not only a value gate

---

## Flow And Discovery Constraints

- For flow-level or subplan tests, read `MainTestPlan/*.stpl` first, then the referenced `SubTestPlans/*.tpl`
- Do not rely only on keyword search in `TestClassesProjectSpecific/` or `.cpp` files for subplan-owned tests
- If a requested TP folder is not found, search recursively under `testprogram/`, then check `.claude/artifacts/current_task/` and `references/` before declaring it missing

---

## Planning And Artifact Constraints

- Read `./_registry.md` first, then the matching knowledge file before drafting a plan
- Keep active task material under `.claude/artifacts/current_task/`
- Treat task-local notes in `.claude/artifacts/current_task/` as support context, not long-term source of truth above inspected source
- Do not silently discard task history; summarize or index before cleanup

---

## Practical Pre-Edit Checklist

- confirmed source folder and working target
- confirmed revision-copy vs in-place handling
- loaded matching knowledge before planning
- identified protected/shared areas that must stay untouched
- checked file dependency order for the intended change
- prepared required structure and history validation steps
