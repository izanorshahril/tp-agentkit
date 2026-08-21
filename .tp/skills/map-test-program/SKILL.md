---
name: map-test-program
description: Map an unfamiliar test program's active launch, flows, dependencies, variants, evidence, and durable product context. Use before modifying or explaining a TP when owning paths or runtime reachability are unproven, or when tester-platform, product, datasheet, or change-document traceability should persist.
---

# Map the program

Build a **task map**, not a repository dump. Read `.tp/knowledge/test-programs.md` when the file family looks like an ATE program covered there.

## Map

1. Start from the user-named program and evidence. Use `rg --files` and targeted searches; expand only when a missing edge blocks the task.
2. Identify platform and launch clues from content, extensions, configuration, and referenced paths. Treat familiar names as hints until a file proves the edge.
3. Trace the active path: launch -> top plan -> subplan or flow -> test/limit/bin definition -> implementation -> datalog or runtime evidence.
4. Separate source presence, active reachability, and observed runtime coverage.
5. Record only the relevant nodes, key symbols or identifiers, owning files, variant, source of truth, and unresolved decisions.
6. When the map has reuse value or supporting documents materially inform it, read [product-documents.md](references/product-documents.md) and create or refresh the product documentation set. Keep a quick answer or one-off investigation in the task map.

Use a compact work note when the map must survive a long task:

```markdown
# Task map
- Target and variant:
- Active launch:
- Authority:
- Edges: file/symbol -> consumer
- Invariants:
- Evidence available:
- Unknowns that change execution:
```

Store it under `.tp/work/` and refresh it when source evidence contradicts the cache.

## Durable context

Use `<PRODUCT>_TP.md` as the product-scoped navigation hub. Link source-specific companions such as `<PRODUCT>_PRODUCT.md` and `<PRODUCT>_PCMS.md` when datasheets or change documents are provided. These files preserve provenance and traceability; the inspected TP, raw supporting documents, and runtime evidence remain the authorities for their own claims.

## Boundaries

- Avoid loading entire large files when headers, references, symbols, and local neighborhoods answer the question.
- Follow generated or copied names back to active callers before treating them as authoritative.
- Do not declare a program, flow, or test absent until recursive key-file discovery and reference following both fail.
- Use a temporary task map until the product identity and durable documentation location are proven; do not invent either.

## Complete when

Every proposed edit or conclusion is connected to its active consumer, the correct variant and authority are named, and every remaining unknown is either non-decision-relevant or surfaced to the user. When durable documents were warranted, their source register, cross-links, freshness state, and change trace are complete at the inspected scope.
