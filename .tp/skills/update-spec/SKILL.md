---
name: update-spec
description: Interpret and implement an approved test-specification change with traceability from requirement to TP behavior. Use when a specification revision changes limits, conditions, coverage, names, bins, timing, setup, or acceptance criteria.
---

# Update a specification

A specification is an authority only within its stated revision, product, condition, and approval scope. Preserve that context through implementation.

## Trace

1. Identify the approved specification version and the exact changed clauses, tables, notes, units, conditions, and effective variants.
2. Separate normative requirements from examples, rationale, draft comments, statistics, and historical text.
3. Build a delta table before editing:

```markdown
| Spec item | Old -> new | Condition | TP owner | Intended change | Verification |
|---|---|---|---|---|---|
```

4. Map each item to the actual limit, definition, flow, implementation, setup, bin, datalog label, or documentation consumer. One requirement may fan out; one TP field may satisfy several requirements.
5. Surface ambiguity rather than silently choosing a tolerance direction, boundary inclusivity, rounding rule, unit conversion, or precedence.
6. Apply the smallest coherent delta, then verify both the specification mapping and the program's internal dependencies.

When the specification changes limits, load `update-limits`. When it changes reachability or implementation, load the matching flow, test, or setup skill as well.

## Boundaries

- Do not rewrite the source specification unless requested; retain its original provenance.
- Avoid translating a customer or product rule into a universal framework rule.
- A renamed label is not proof that runtime behavior changed, and changed code is not proof that the active flow reaches it.

## Complete when

Every in-scope normative delta maps to an implemented or explicitly deferred TP effect, every out-of-scope item is accounted for, and verification evidence covers the stated units, conditions, variants, and acceptance boundaries.
