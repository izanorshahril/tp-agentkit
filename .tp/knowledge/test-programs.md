---
status: verified
scope: cross-program principles with T2000-specific clues
updated: 2026-08-27
---

# Test-program model

## Map relationships, not folders

ATE programs vary. Treat file extensions and familiar directories as clues, then prove the active relationships from launch configuration and references.

Common T2000 clues:

- `.ini` or `.cfg`: launch selection and platform mode
- `.stpl`: top-level plan that may reference subplans
- `.tpl` or `.otpl`: plan, flow, variables, or job metadata
- `.ls`: limits
- `.bdefs`: bin definitions
- `.cpp`: implementation or test functions

A named flow-level test can live in a subplan rather than in the implementation file whose name seems likely. Follow the active plan into referenced subplans before concluding that a test is absent.

## Keep three claims separate

1. **Source presence:** a definition or implementation exists.
2. **Reachability:** the active launch and flow can invoke it.
3. **Runtime coverage:** observed output proves it ran.

Evidence for one claim does not prove the next.

## Derived reference views

Generated Markdown, JSON, and text exports are navigation views unless the source register explicitly grants them another role.
The actual TP source, controlled product documents, and runtime evidence remain authoritative for their own claims.
A compact view can omit repetitive or layout-dependent content while remaining useful when it preserves exact source paths, provenance, references, and explicit unknowns.
Presence of a derived record proves that the exporter saw a source or reference, not that the source is reachable in an active variant or ran at runtime.

## Variant and revision invariants

- Compare a changed variant with its own intended baseline. Sibling cold, ambient, hot, QA, and engineering flows may differ legitimately.
- Preserve the source when producing a new revision unless the user explicitly authorizes in-place work.
- Search the full active target for revision metadata. On T2000, a stale `JOB_REV` may exist in sibling `.tpl` files even when the first changed file is correct.
- Append to chronological history when the program maintains one; follow the actual local format.

## Limit invariants

For the observed T2000 `LimitDef` family, the environment pairs are:

```text
LimitDef(TestNo, Desc, PrecScale, Unit, Bin,
  FTC_LL, FTC_UL, FTR_LL, FTR_UL, FTH_LL, FTH_UL,
  EWC_LL, EWC_UL, EWR_LL, EWR_UL, EWH_LL, EWH_UL)
```

Confirm the target file uses this shape before relying on it. A temperature word does not automatically authorize every FT and EWS pair; map the requested flows and active variants explicitly. Verify scale and engineering unit before comparing numeric values.

## Dependency invariant

Before making a flow edge active, prove that every referenced test, limit, bin, variable, implementation, and required setup exists in that variant. When duplicating a test, keep the original condition active, use a unique identifier, make condition names explicit, and change flow only when reachability actually needs it.

## Two dependency surfaces

TP comprehension has two dependency surfaces that must be checked separately:

- The **load surface** is selected by launch/configuration and followed through templates, imports, environments, flows, patterns, and runtime DLL declarations.
- The **C++ surface** is declared by retained `vcxproj` files and followed through compiled sources, headers, project-to-project links, and code-facing resources or generated inputs.

Direct call-site search is insufficient for the C++ surface: a project-listed source or header can define part of the program even when no TP file or neighboring source names it directly. Conversely, a file can be present in a project and still be build-only metadata rather than behavior-bearing code; classify that distinction from the project item type and source/resource references.
