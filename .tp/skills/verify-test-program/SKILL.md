---
name: verify-test-program
description: Verify a test-program change or conclusion through fresh deterministic evidence and iterative repair. Use before claiming work is complete, correct, structure-preserving, safe, validated, or ready for handoff or release.
---

# Verify the program

No positive completion claim without fresh task-specific evidence.

## Verification loop

1. Translate each intended outcome and protected invariant into an observable check.
2. Run the cheapest decisive checks first: targeted searches, parser or round-trip, counts, structural diff, compile, simulator, tester, datalog, then production evidence where available.
3. Inspect changed files and outputs directly; an exit code or generated summary is not sufficient.
4. When a check fails, classify the failure, make the smallest correction, and restart every check whose evidence the correction invalidated.
5. Stop only when all criteria pass or the declared iteration, access, or risk limit is reached. Report a limit as incomplete evidence, not success.

## Evidence by change

- **Revision:** source unchanged, target complete, launch references consistent, metadata normalized, history traceable.
- **Limits:** approved values in correct units/scale/environment; counts stable; no add/delete/reorder/tuple/footer damage.
- **Flow:** active path reaches exactly the requested nodes; dependencies resolve; neighboring order, branches, and bins remain intended.
- **New test:** identity unique; definition, limit, implementation, datalog, bin, setup, and flow agree; original condition preserved when duplicated.
- **Setup:** state and cleanup hold across pass, fail, retry, abort, and site paths; hardware-dependent behavior uses appropriate evidence.
- **Analysis:** schema and joins reproducible; totals reconcile; source, reachability, runtime, and inference claims remain distinct.

Use a task-local script when a deterministic invariant would otherwise be checked manually more than once. Keep the script beside the task evidence until the work closes; promote it only when repeated future value clearly exceeds maintenance cost.

## Report

State:

```text
verified: <claim> — <fresh evidence>
unverified: <gap> — <effect on confidence>
next check: <most decisive remaining action>
```

## Complete when

Every intended outcome and protected invariant has fresh evidence, failures have been repaired and rechecked, and missing parser, simulator, tester, or production evidence is explicit beside the claim it limits.
