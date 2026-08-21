---
name: analyze-test-evidence
description: Correlate test-program source with CSV, STDF-derived data, datalogs, runtime logs, diffs, or screenshots to explain behavior and failures. Use when evidence schema, active coverage, populations, aliases, or source-to-runtime relationships must be established before a conclusion or change.
---

# Analyze test evidence

Keep raw evidence unchanged. Record its origin, time or revision, program/variant, filters, and any transformation used to reach a conclusion.

## Evidence loop

1. Profile shape before meaning: encoding, delimiter, headers, duplicate columns, metadata rows, site/unit keys, missing values, and row counts.
2. Separate **where a field is** from **what it means**. Ask the user when semantics cannot be proven from the file, source, or authoritative documentation.
3. Establish populations and joins explicitly. Avoid mixing runs, sites, variants, good/bad populations, or pre/post-limit data without a keyed reason.
4. Correlate source presence, active-flow reachability, and runtime coverage as separate layers.
5. Form a falsifiable hypothesis, write the smallest task-local parser or query under `.tp/work/`, and make it fail loudly on schema drift or ambiguous joins.
6. Reconcile totals: every row, unit, test, error, or mismatch belongs to a named bucket. Sample rows illustrate; they do not prove completeness.
7. Preserve machine-readable intermediate output only while it supports review or resumption. Promote the method, not the raw private evidence.

Minimum provenance header for a task harness output:

```text
input=<path or redacted label>
variant=<value>
filters=<explicit rules>
join_keys=<ordered keys>
rows_in=<count>
rows_accounted=<count by bucket>
generated=<timestamp>
```

## Complete when

Schema meaning is proven or user-confirmed, populations and joins are reproducible, totals reconcile, alternative explanations were tested, and every conclusion states whether it is supported by source, reachability, runtime evidence, or an inference across them.
