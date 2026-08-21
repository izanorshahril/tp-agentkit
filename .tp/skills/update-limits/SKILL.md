---
name: update-limits
description: Review or change test limits with scale, unit, environment, variant, structure, and provenance controls. Use when limits come from CSV, workbook, specification, population analysis, comparison output, or direct approved values.
---

# Update limits

Treat every imported value as a candidate until its authority, target variant, test identity, unit, scale, and environment are proven.

## Limit loop

1. Identify the winning source and approval state. When inputs disagree, stop at a proposal until the user resolves authority.
2. Inspect the real input schema. Separate limit fields from statistics, comments, metadata, and aliases; do not infer meaning from position or filename alone.
3. Join source rows to target definitions using the strongest available keys: program/variant, test number, parameter or name, unit, and environment.
4. Normalize values only for comparison. Preserve the target program's valid syntax, precision, scale token, special values, and comments when writing.
5. Produce a dry-run table with old value, proposed value, unit, scale, environment, target occurrences, and reason. Classify unmatched, ambiguous, inactive, not-applicable, and non-comparable rows separately.
6. Apply only approved rows. Inspect adjacent repeated blocks and the file tail after patching.
7. Compare before and after for value and structure; re-count every touched identifier and prove excluded rows stayed unchanged.

For T2000 `LimitDef` work, read `.tp/knowledge/test-programs.md` and first confirm the target uses the documented environment-pair order. A `COLD` request can mean different active FT or EWS pairs; derive the intended set from the confirmed program and user direction.

## Task harness

For bulk data, write a temporary parser under `.tp/work/` that emits machine-readable proposed rows and errors before it writes anything. Keep the phases separable:

```text
parse source -> parse target -> join/classify -> render proposal
                                      |
                               explicit approval
                                      v
                                  apply -> reparse -> compare
```

Fail closed on duplicate keys, unknown units, non-finite values, inverted limits, unexpected occurrence counts, or a target row shape the harness cannot round-trip.

## Complete when

Every requested and excluded row is accounted for; all applied values match the approved source in engineering units and intended environments; and fresh comparison proves no unintended add, delete, reorder, tuple shift, identifier drift, or footer damage.
