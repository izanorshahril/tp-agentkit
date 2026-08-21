---
name: change-test-flow
description: Add, remove, move, gate, bin, or restore tests and subplans in an active test flow while preserving dependencies and variant intent. Use when execution order or reachability must change without accidental coverage or binning drift.
---

# Change test flow

Prove the active launch path before editing a flow-looking file. A dormant or sibling plan is not an execution target.

## Flow loop

1. Map the selected launch through top plan, imports, subplans, branches, and final binning. Name the exact active variant.
2. Define the intended reachability delta: which node becomes reachable or unreachable, under which condition, at which order, and with what bin or branch effect.
3. Capture surrounding invariants: predecessor and successor, setup state, branch labels, soft/hard bins, variables, cleanup, and tests expected to remain unchanged.
4. For an addition, prove every referenced test, limit, bin, variable, implementation, and setup exists before activating the edge.
5. For a removal, disconnect the active edge first. Retain definitions and implementation unless deletion is explicitly requested and all callers are proven absent.
6. Patch the narrowest owning surface. Re-read the changed neighborhood and every import or reference boundary it crosses.
7. Parse or simulate when available; otherwise use structural searches and an active-path walk, then state the runtime gap.

Useful task-local queries:

```powershell
rg -n --fixed-strings '<test-or-subplan>' '<program>'
rg -n 'import|include|SubTestPlan|Branch|Bin|Flow' '<active-plan-area>'
```

Search results are candidates; classify each as definition, active caller, inactive caller, comment, generated output, or evidence.

## Complete when

The intended node has exactly the requested reachability and order in every in-scope active variant, all dependencies resolve, protected neighboring flow and bin behavior is unchanged, and runtime validation is either passed or explicitly missing.
