---
name: improve-codebase-architecture
description: Use when auditing TP-AgentKit for architectural friction, shallow modules, duplicated parsing or output logic, or testing pain and you want local refactor candidates instead of GitHub issue RFCs.
metadata:
  status: beta
  language: markdown
---

# Improve Codebase Architecture

Behavior-only skill. No executable script.

Use this skill for repo-maintenance audits that look for deep-module opportunities and cleaner public boundaries.

## Purpose

- find places where TP-AgentKit is harder to understand or test than it needs to be
- deepen shallow wrappers and split overloaded maintenance surfaces more deliberately
- reduce duplicated normalization, reporting, and file-walking logic across Python skills
- turn architecture observations into local follow-through artifacts instead of GitHub issue churn

## Use When

- understanding one repo concept requires bouncing across too many files
- a helper layer is almost as complex as the code it wraps
- similar parsing, normalization, or reporting logic appears in multiple skill folders
- tests are brittle because the public boundary is weak or unclear
- a repo-maintenance thread needs stronger refactor candidates before implementation starts

## Do Not Use When

- the task is a single contained bug fix with an obvious change path
- the main need is TP execution risk interrogation; use `grill-me` instead
- the problem is evidence strength before closeout; use `verification-before-completion` instead
- the area under discussion is too small to justify an architectural pass

## Workflow

### 1. Load local constraints first

Inspect:

- `.claude/knowledge/_registry.md`
- `.claude/knowledge/constraints.md`
- the relevant skill folders, helpers, tasks, or knowledge files already involved
- any active current-task artifact that explains why the area is under review

### 2. Explore for real friction

Do not force a rigid checklist.
Navigate the code the way a maintainer or agent would and capture where friction appears.

Good signals:

- repeated file hopping to understand one concept
- duplicated CLI or JSON-shape logic
- helper modules that expose too much of their internals
- tests that have to know private structure to stay useful
- support code that is co-owned by multiple skill folders but has no clear home

### 3. Present candidate deepening opportunities

For each candidate, show:

- cluster: modules or files involved
- friction: why the current shape is hard to follow or test
- boundary to deepen: what public surface could become smaller or clearer
- test impact: what could move from seam-testing to boundary-testing
- likely risk: low, medium, or high change surface

Do not jump straight to implementation.

### 4. Choose one candidate

Recommend the strongest candidate if one clearly dominates.
If needed, use `design-an-interface` next to compare multiple replacement boundaries before coding.

### 5. Write local follow-through output

Record the result in a local artifact, not a GitHub issue.

Preferred targets:

- `.claude/artifacts/current_task/<topic>-<date>.md` for active maintenance work
- `.claude/knowledge/improvements/` only after the recommendation becomes durable and reusable beyond one task

### 6. Hand off the next action cleanly

If the selected candidate should be implemented, route it into:

- `design-an-interface` for boundary comparison
- `write-a-skill` when the change creates or reshapes a real skill surface
- `prd-to-plan` when the refactor needs phased execution

## Evaluation Heuristics

- smaller public surface, deeper hidden implementation
- clearer ownership of shared helper logic
- fewer duplicate parse or report paths
- more stable boundary tests
- less reliance on task artifacts as de facto architecture docs

## Anti-Patterns

- proposing refactors because a file is long without identifying real friction
- defaulting to GitHub issue output for local maintenance work
- confusing naming cleanup with meaningful module deepening
- splitting code into more files when the real need is a better boundary

## Output Pattern

1. current friction summary
2. ranked candidate list
3. recommended candidate
4. why this is the best leverage point now
5. next implementation surface