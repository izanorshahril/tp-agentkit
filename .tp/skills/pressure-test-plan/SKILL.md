---
name: pressure-test-plan
description: Pressure-test a TP plan against authority, target safety, dependency integrity, validation, rollback, and release risk. Use before medium-risk or high-risk changes, destructive actions, ambiguous evidence, or decisions that may ship with reduced validation.
---

# Pressure-test the plan

Attack the plan's weakest branch after recoverable facts have been inspected.

## Risk triggers

- release, lot-disposition, destructive, or in-place work
- conflicting CSV, workbook, specification, source, log, or user direction
- variant or baseline ambiguity
- apparently narrow limit or flow work that can hide structure drift
- missing parser, simulator, tester, or production evidence
- multiple plausible implementations with different rollback or validation cost

## Interrogate

Require the draft plan to name:

- exact target and source authority
- recoverable baseline and restore path
- intended delta and protected invariants
- active variant and dependency edges
- deterministic checks and stop condition
- remaining validation gap and who accepts it

Inspect files before questioning the user. When a real choice remains, ask one discriminating question at a time, state the weak assumption, and give the recommended answer. Stop once the answer no longer changes execution or release confidence.

For a material mutation, present the hardened plan and obtain explicit approval immediately before execution unless the current request already authorizes that exact target and delta.

## Complete when

No unresolved branch can change the target, authority, implementation, validation depth, rollback, or release confidence. A merely plausible plan is still incomplete.
