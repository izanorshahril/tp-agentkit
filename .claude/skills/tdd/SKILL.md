---
name: tdd
description: Use when building or fixing TP-AgentKit Python tooling with a red-green-refactor loop focused on public behavior, CLI boundaries, and artifact outputs rather than implementation details.
metadata:
  status: beta
  language: markdown
---

# TDD

Behavior-only skill. No executable script.

Use this skill when a TP-AgentKit code change should be driven by behavior-first tests instead of incidental implementation structure.

## Purpose

- keep tests anchored to public behavior, command output, and generated artifacts
- drive Python skill work in small vertical slices
- reduce brittle test coupling to helper internals
- fit new code into the repo's existing `test_skill.py` and shared-support pattern

## Use When

- adding or fixing a Python skill, wrapper, parser, or report generator
- changing JSON or markdown output shape that should be verified from the boundary
- tightening regression coverage on an already-callable skill
- implementing a change where the failure mode is easier to express as behavior than as internal mechanics

## Do Not Use When

- the work is a behavior-only markdown skill with no executable behavior to drive
- the task is only prose or documentation cleanup
- the public boundary is still too unclear to test responsibly; use `design-an-interface` first if needed

## Workflow

### 1. Identify the public boundary

Choose the boundary the test should exercise, such as:

- CLI invocation
- compact JSON output
- generated file contents
- helper-module contract that is stable enough to be public within the repo

If the boundary is fuzzy, sharpen it before writing tests.

### 2. Plan one behavior at a time

List the behaviors that matter, then start with the smallest useful tracer bullet.

Avoid writing every imagined test before any implementation exists.

### 3. Run the red-green-refactor loop

- RED: write one failing test in `test_skill.py`
- GREEN: write the minimum code to satisfy it
- REFACTOR: clean up only after the test passes

Repeat one behavior at a time.

### 4. Prefer the local test harness

Use the existing repo helpers when they fit:

- `.claude/skills/_test_support.py`
- `SkillTestCase`
- `run_python_cli`
- `parse_compact_json_output`
- `.claude/skills/run_skill_tests.py`

For behavior-only skills, write a contract test rather than pretending there is runtime behavior.

### 5. Keep tests on observable outcomes

Prefer assertions on:

- exit behavior
- JSON fields
- emitted files
- preserved structure
- user-visible report content

Avoid testing private helper steps unless that helper is intentionally the stable public boundary.

### 6. Close out honestly

After the tests pass, use `verification-before-completion` so the final claim names what was actually verified.

## Anti-Patterns

- writing all tests first, then all code
- asserting private implementation steps when public behavior is available
- over-mocking the filesystem or subprocess layer before trying a real small fixture
- adding speculative functionality while making the current test pass
- using TDD vocabulary while skipping the real failing-test step

## Output Pattern

1. boundary under test
2. first tracer bullet behavior
3. next behaviors in order
4. validation command
5. remaining untested risk