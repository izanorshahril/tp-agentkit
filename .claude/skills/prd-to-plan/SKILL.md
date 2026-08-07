---
name: prd-to-plan
description: Use when a TP-AgentKit maintainer already has a feature brief, harvested proposal, or repo-maintenance objective and needs it broken into tracer-bullet phases as a dated local plan artifact.
metadata:
  status: beta
  language: markdown
---

# PRD To Plan

Behavior-only skill. No executable script.

Use this skill to turn a maintainer brief into a phased execution plan that fits TP-AgentKit's local artifact workflow.

## Purpose

- break larger maintenance or framework work into narrow, end-to-end phases
- keep durable decisions visible before implementation starts
- avoid horizontal planning that separates docs, code, tests, and validation into disconnected piles
- store plans where TP-AgentKit maintainers already resume work

## Use When

- a feature brief, proposal, or harvested improvement is already in the conversation or in a local file
- the work spans multiple skills, knowledge files, rules, scripts, or docs
- implementation needs explicit phase boundaries before coding starts
- the maintainer wants a reusable local plan artifact instead of an issue ticket

## Do Not Use When

- the task is small enough to execute directly without a multi-phase plan
- the user is asking for a normal TP edit plan governed by the existing approval workflow
- there is no source brief yet and the plan would just invent scope

## Inputs

Before drafting, confirm:

- the source brief, proposal, or request is in context
- the relevant local constraints and knowledge files are loaded
- the current architecture and affected repo surfaces are understood well enough to slice responsibly

## Workflow

### 1. Confirm the source brief

If the request, proposal, or feature brief is not already in context, get it first.
Do not start slicing against a vague memory of the task.

### 2. Inspect the repo surfaces involved

Look at the real affected layers, such as:

- skill docs and tests
- Python entrypoints and helpers
- knowledge and rules
- task presets
- current-task artifact expectations

### 3. Identify durable decisions

Before breaking work into phases, name the choices unlikely to change later, for example:

- which repo surfaces own the behavior
- whether the change is behavior-only or callable
- where artifact output belongs
- what validation path will prove the work
- whether user-facing docs need to change

### 4. Draft tracer-bullet phases

Each phase should be a thin vertical slice through the real repo layers it needs.

Good TP-AgentKit slices often cut through combinations like:

- skill doc + implementation + test
- knowledge note + workflow update + validation
- task wrapper + maintained command path + current-task note

Avoid horizontal slicing such as `update docs`, `write tests`, `then code everything`.

### 5. Review the granularity

For each phase, show:

- title
- what user or maintainer outcome becomes possible
- main repo surfaces touched
- validation or acceptance shape

Split phases further if they are not independently reviewable or verifiable.

### 6. Write the local plan artifact

Do not create `./plans/` or a GitHub issue for this repo.

Preferred output:

- `.claude/artifacts/current_task/<topic>-plan-<date>.md`

Promote durable lessons later into knowledge, not into a second competing plan location.

## Suggested Plan Shape

Use a structure like:

- source brief
- durable decisions
- phase 1
- phase 2
- phase 3
- validation gates
- open risks or questions

Each phase should describe end-to-end behavior, not just file edits.

## Anti-Patterns

- writing a plan before reading the actual brief
- horizontal slices that separate tests from behavior
- GitHub issue output as the default planning surface
- overfitting the plan to brittle file names or temporary code layout

## Output Pattern

1. source brief anchor
2. durable decisions
3. phased tracer bullets
4. validation gates
5. follow-through risks