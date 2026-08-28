---
name: prepare-rag-dataset
description: Prepare a test-program source set for semantic reference or knowledge-base ingestion.
disable-model-invocation: true
---

# Prepare a reference dataset

Use this skill only for an explicitly requested unification, cleanup, pruning, or packaging task whose destination is semantic reference or a knowledge base rather than an ATE execution package.

## Boundary

1. Name the source variants, target dataset, protected originals, authority, and intended knowledge-base consumer.
2. Create and inspect a recoverable baseline before any in-place removal or bulk rewrite. Keep the restore path outside the mutation target.
3. State the retention goal separately from build reproducibility. A semantic dataset may omit compiler, generated-file, custom-build, resource, library, simulator, and tool metadata, but that deliberate loss must be reported.

## Representation policy

Choose one canonical retained representation that the actual knowledge-base consumer can ingest reliably.
Give each output a stable name and role, and keep parser comparisons, probes, and superseded formats outside the active reference set.

Use full text or bounded chunks for launch, flow, limit, variable, and behavior-bearing source.
Use metadata-only records for repetitive pattern bodies, compiled or binary assets, and extraction furniture when their names, references, source paths, and checksums remain searchable.
Retain named timing constants, profiles, maps, and other semantics that explain how a retained pattern or test is configured.
Use source-only treatment for diagrams and other representations whose meaning depends on geometry.
Replace every omitted body with a literal pointer to the actual source file or page.

Keep one searchable text field per embedding document.
Add metadata only when it supports filtering, joins, provenance, or a decision that the consumer cannot recover from the source path and record identity.
Prefer derivable state over duplicate flags and remove duplicate text fields when the consumer has one clear content field.
Select delimited formats only when they round-trip multiline source and the consumer accepts them; otherwise retain the supported structured or plain-text representation and remove the unsupported format from active scripts and documentation together.

## Map before pruning

Run both dependency passes before deleting files:

- **TP load pass:** resolve launch/configuration, templates, imports, environments, flow includes, patterns, and runtime DLL declarations.
- **C++ project pass:** resolve every source, header, project link, resource, custom-build input, and other project item listed by retained `vcxproj` files. Treat a project-listed source or header as part of the program model even when direct call-site search finds no consumer.

Classify each candidate as:

- runtime-required
- behavior-bearing and needed for program comprehension
- build-only or tooling metadata
- unproven

Delete only after the candidate's classification and authority are recorded. Prefer the smallest semantic dataset that preserves runtime understanding and behavior-bearing TP/C++ code. Keep `vcxproj` files when they are the clearest inventory of the C++ program, even when build-only project items are removed from them.

## Prune in dependency order

1. Remove or change active callers before deleting a retired runtime payload, and recheck the load path immediately.
2. Remove stale project items before deleting their build-only files, and recheck every remaining project input.
3. Preserve required runtime declarations and code-facing headers even when their role is indirect or template-driven.
4. If an audit exposes an over-aggressive deletion, restore the exact baseline or canonical local copy, rerun both dependency passes, and continue only after the boundary is sound.

## Verify the dataset

Use fresh deterministic checks:

- every retained launch/configuration target resolves;
- every retained TP import, environment, flow include, pattern, and runtime DLL declaration resolves;
- every retained `vcxproj` input and project link resolves;
- exact filenames, paths, project attributes, and tokens for deleted artifacts have no active references;
- metadata-only records contain an omission marker and an exact source pointer;
- compacted text preserves the ordered sequence of non-empty source lines byte-for-byte;
- edited project and TP files parse or pass editor diagnostics;
- the final report separates verified semantic coverage from unverified native build, simulator, tester, or production evidence.

For deletion scans, use exact-token or reference-type-aware matching. Broad substring searches are discovery aids, not proof of a dangling reference.

## Complete when

The target dataset has a documented boundary and recoverable baseline, both dependency passes are complete, every retained runtime and behavior-bearing dependency resolves, deleted artifacts have no exact active references, and any reduction in buildability is explicit beside the semantic result.
