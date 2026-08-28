---
name: extract-reference-documents
description: Extract technical PDFs into source-backed Markdown or compact review guides when parser choice, table or reading-order loss, layout-sensitive claims, or document provenance affects the result.
---

# Extract reference documents

Treat extraction as a representation decision, not a format conversion.
The PDF or other supplied document remains the authority; Markdown and structured records are navigation views.

## Set the boundary

1. Name each source, its role, the retained output, the intended consumer, and the claims the output must support.
Preserve the original source unchanged and record its path, page count, checksum, revision, and applicable scope.
Complete when every output has one named source and one declared authority.

2. Choose one retained extraction standard for the task.
Keep parser comparisons and intermediate diagnostics task-local unless they answer a documented decision.
Record the parser configuration that affects reading order, OCR, images, links, tables, headers, footers, workers, or model use.
Complete when the active parser and its material settings are explicit.

3. Classify the source pages before interpreting them.
Use native text extraction for searchable text and simple tables when it meets the retrieval goal.
Use table or layout-aware extraction when cell association changes the claim.
Use source-only treatment for schematics, drawings, wiring, relay states, and other geometry-dependent pages when the representation loses spatial relationships.
Complete when each page family has a representation policy and an escalation path for unresolved layout.

## Preserve meaning

- Keep one independent derived output per source when page provenance or refresh ownership differs.
- Preserve source-page markers or a page mapping when a reviewer must return to a location.
- Normalize identifiers only with authority from the source or a deterministic, page-local match.
- Keep the original text around a normalized value when the transformation could change interpretation.
- Record `inferred` or `unknown` for interpretations that extraction alone cannot prove.
- Put curated, test-relevant facts in a compact guide with page or section provenance and a clear omission list.
- Use a metadata-only representation for repetitive waveform, binary, or extraction-furniture content when the source path, identity, references, and checksum remain searchable.
- Replace omitted bodies with a literal pointer to the actual source file or PDF page.

## Handle layout risk

A text layer can preserve labels while losing the geometry that binds labels together.
Treat a plausible reading order as evidence for search, not proof of topology, pin association, relay state, site identity, or complete table-row meaning.
For those claims, return to the PDF image or an image-aware/OCR review and attach the result to a source page and checksum.
After source identity and page evidence are established, use [`create-document-diagrams`](../create-document-diagrams/SKILL.md) for a derived technical-document figure; keep extraction policy here and diagram construction there.

A curated guide may retain document identity, revision history, section maps, program names, limits, package facts, and other independently verifiable values.
It earns a claim only when its source location and basis are recorded.

## Validate the artifact

Run fresh checks after generation or curation:

1. Parse the output and inspect representative pages or records directly.
2. Compare the recorded source checksum and page count with the current source.
3. Check required anchors, normalized identifiers, and omission markers.
4. Confirm every retained link points to an existing source or explicitly names an external authority.
5. Scan the active documentation set for retired names, duplicate parser variants, and stale output paths, excluding rollback archives and task-local diagnostics.
6. Revert the derived output to the known baseline when a cleanup removes source meaning, then narrow the transformation and rerun the checks.

## Complete when

Each retained claim has a source and representation basis, each omitted body has an exact source pointer, source identity and provenance checks pass, layout-dependent gaps are explicit, and retired or duplicate active artifacts have no remaining references.
