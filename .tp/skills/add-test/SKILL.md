---
name: add-test
description: Add a new or companion test across identifiers, limits, implementation, datalogging, bins, and active flow. Use when creating coverage from scratch or duplicating an existing test for another condition, setup, product option, or environment.
---

# Add a test

Use the closest active analogue as a map, not as blind copy material. Preserve each program and variant's own conventions.

## Contract first

Before editing, define:

- unique test identity and human-readable name
- measured quantity, engineering unit, scale, limits, and environments
- setup and stimulus condition
- implementation entry point, inputs, outputs, site scope, and cleanup
- datalog behavior and failure semantics
- bin or branch behavior
- active insertion point and variants

## Build a tracer slice

1. Trace an analogous active test end to end and note every owning surface.
2. Add the minimum coherent definition, limit, implementation/datalog, and flow edges required by the actual platform. Do not create a surface the analogue does not need.
3. Keep the original test active when adding a companion condition. Use a unique identifier and make the condition split explicit in names and variables.
4. Separate changed stimulus or setup from measurement parameters; change both only when the requirement says both change.
5. Search all active variants for the old and new identifiers, then classify missing occurrences as intended or defective.
6. Exercise the smallest available feedback loop: parser, compile, simulator, focused harness, or representative datalog replay.

Task-local audit shape:

```markdown
| Surface | Analogue | New test | Active variant | Evidence |
|---|---|---|---|---|
| definition/limit | | | | |
| implementation/datalog | | | | |
| flow/bin | | | | |
| setup/cleanup | | | | |
```

## Complete when

The new identity is unique, every active reference resolves, units and conditions agree across surfaces, the original and neighboring tests retain intended behavior, and execution is proven by the strongest available parser, simulator, tester, or datalog evidence with any gap stated.
