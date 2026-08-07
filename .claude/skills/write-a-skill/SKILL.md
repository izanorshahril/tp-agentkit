---
name: write-a-skill
description: Use when creating, harvesting, or refactoring a TP-AgentKit skill so the result fits the local `.claude/skills` conventions, registry, tests, and workflow boundaries.
metadata:
  status: beta
  language: markdown
---

# Write A Skill

Behavior-only skill. No executable script.

Use this skill to shape a TP-AgentKit skill before touching files.

## Purpose

- keep new skills aligned with the local `.claude/skills/` contract
- choose the right surface: skill, knowledge, rule, task, or current-task artifact
- keep harvested external capabilities from arriving as style islands
- require a small local validation path before a new skill is treated as real

## Use When

- adding a new callable or behavior-only skill under `.claude/skills/`
- adapting a skill from another repo into TP-AgentKit
- splitting an overgrown skill into helper files or support modules
- deciding whether a repeated workflow deserves a real skill instead of another artifact note

## Do Not Use When

- the content belongs in `.claude/knowledge/` as durable cross-task guidance
- the content is a workflow or enforcement rule that belongs in `.claude/rules/`
- the content is a one-off task handoff that belongs in `.claude/artifacts/current_task/`
- the work is only a small fix inside an existing well-shaped skill

## Required Inputs

Before drafting the skill, inspect:

- `.claude/skills/_registry.md`
- one comparable local skill folder
- `AGENTS.md` extension-point guidance
- any matching rule or knowledge file that already governs the task
- `.claude/skills/_test_support.py` and `.claude/skills/run_skill_tests.py` if the skill will ship Python code

## Workflow

### 1. Classify the surface

Decide if the work should become:

- a callable skill with deterministic script output
- a behavior-only skill with markdown guidance only
- knowledge, a rule, a task, or an artifact instead of a skill

Questions to resolve:

- Is there a repeated agent capability here?
- Does the behavior need executable code, or only bounded instructions?
- Would a maintainer expect to discover this from the skill registry?

### 2. Define the trigger description

- first sentence: what the skill does
- second sentence: `Use when ...`
- be specific about file types, task shapes, or repo surfaces
- avoid vague descriptions like `helps with docs`

### 3. Choose the file set

Minimum shipped surface:

- `SKILL.md`
- `test_skill.py`

Add an executable script only when the operation is deterministic and worth reusing.
Add helper files only when the main skill would otherwise become hard to scan or mix unrelated domains.

### 4. Draft the local contract

For most TP-AgentKit skills, include the sections that fit the skill type:

- Purpose
- Use When
- Do Not Use When
- Tool Entry Point and standard commands for callable skills
- Rules, workflow, or output pattern for behavior-only skills
- limits, failure modes, or misuse cases
- agent guidance when the output needs careful interpretation

### 5. Wire into TP-AgentKit surfaces

- add or update the row in `.claude/skills/_registry.md`
- if the skill changes workflow behavior, update the matching rule or knowledge file instead of hiding the rule in the skill alone
- if the change materially affects repo maintenance, add a brief dated note under `.claude/artifacts/current_task/`
- keep user onboarding in `README.md` only when end users need to know the behavior changed

### 6. Validate before claiming the skill is ready

For Python skills, use the promotion gates already defined in `.claude/skills/_registry.md`:

- `--help` startup smoke passes
- at least one main success-path smoke case exists
- no active editor diagnostics remain
- `SKILL.md` documents an important failure mode, limit, or misuse case

For any skill type:

- run `python .claude/skills/run_skill_tests.py <skill-name>` or the skill-local `test_skill.py`
- keep the validation claim narrow if only contract tests ran
- behavior-only skills still need a contract test that proves the markdown surface is intentional

## TP-AgentKit Conventions

- prefer relative paths inside skill-local docs when possible
- keep durable policy out of task artifacts
- prefer local artifact output over GitHub issue creation
- use `.claude/skills/_test_support.py` for shared Python test helpers when helpful
- do not leave planned-only placeholders in the active catalog
- if a skill wraps a repetitive repo-maintenance command, keep the canonical command shape in one script and reference it from tasks

## Anti-Patterns

- copying an external skill verbatim without adapting workflow boundaries
- encoding GitHub-only output paths when TP-AgentKit uses local artifacts
- burying failure modes or limits
- treating `README.md` or a task note as the source of truth for a skill
- adding a script when a behavior-only skill would be clearer and cheaper to maintain

## Minimal Review Checklist

- [ ] description states what it does and when to use it
- [ ] correct surface chosen: skill vs knowledge vs rule vs artifact
- [ ] registry row added or updated
- [ ] `test_skill.py` exists and matches the shipped contract
- [ ] failure mode, limit, or misuse case documented
- [ ] validation run or explicitly pending