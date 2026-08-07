---
name: design-an-interface
description: Use when designing a new TP-AgentKit skill, helper module, CLI, or machine-output contract and you want multiple interface shapes compared before implementation.
metadata:
  status: beta
  language: markdown
---

# Design An Interface

Behavior-only skill. No executable script.

Use this skill before implementing a new maintainer-facing surface so the first interface choice is not the only one considered.

## Purpose

- compare multiple interface shapes before adding a new skill, helper module, or JSON or markdown output contract
- prefer deep modules with small stable interfaces and hidden complexity
- reduce accidental CLI sprawl, output churn, and shallow helper layers

## Use When

- designing a new `.claude/skills/<skill>/` surface
- shaping a Python CLI, wrapper script, or helper module
- designing JSON output or markdown artifact structure for a maintained tool
- deciding what belongs inside a skill versus in knowledge, rules, or tasks

## Do Not Use When

- the task is already obvious and only needs a small local fix
- the main need is TP risk interrogation; use `grill-me` instead
- the problem is whether evidence is strong enough to call the task complete; use `verification-before-completion` instead
- the decision is only naming or prose tightening with no interface change

## Workflow

### 1. Define the problem and callers

Inspect who will use the surface: agent, maintainer, task runner, or downstream tool.
Capture the common case, edge cases, and what should stay hidden.

### 2. Load local constraints first

Inspect neighboring skills, registry expectations, task presets, and any knowledge or workflow file that already constrains the shape.
Bias toward the current Python and markdown stack, closed-environment operation, and local artifact outputs.

### 3. Generate three genuinely different designs

At minimum, compare:

- the smallest possible interface
- the most flexible interface
- the common-case-optimized interface

Each design should include:

- interface signature or command shape
- short usage example
- what complexity stays internal
- expected validation path
- trade-offs and likely misuse modes

### 4. Compare in TP-AgentKit terms

Judge each design on:

- interface size and clarity
- output stability for artifacts or automation
- testability from the public boundary
- maintenance burden
- fit with `.claude/skills/`, `.claude/knowledge/`, `.claude/tasks.json`, and current-task artifacts
- how hard it is to misuse under schedule pressure

### 5. Recommend one design or a hybrid

Be opinionated.
If one design wins for the repo's actual maintenance pattern, say so.
If the best answer is a hybrid, name which parts should survive.

### 6. Hand off cleanly

If implementation should proceed, route it through `write-a-skill` for new skills or through the normal code-change workflow for existing tools.
If the design meaningfully changes maintainer workflow, record the decision in a brief dated current-task artifact.

## Evaluation Heuristics

- small public surface, deep implementation
- deterministic output shape over clever flexibility
- stable names and fields over one-off convenience
- clear failure modes and obvious validation path
- no GitHub-first assumption when local artifacts are the real workflow

## Anti-Patterns

- copying an external CLI or JSON schema without checking repo fit
- adding flags for rare cases before the common case is clean
- designing around current file layout instead of durable behavior
- spreading one concept across skill, knowledge, rule, and artifact surfaces without a clear owner
- using a GitHub issue as the default output when a local artifact or registry update is the better fit

## Output Pattern

When presenting the comparison, use this order:

1. problem statement
2. design A
3. design B
4. design C
5. trade-off comparison
6. recommendation
7. next implementation surface