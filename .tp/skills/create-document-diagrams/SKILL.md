---
name: create-document-diagrams
description: Create or rebuild source-backed diagrams in technical documentation when a figure, state machine, topology, or other layout-sensitive content must be represented in Mermaid or a fixed-layout artifact.
---

# Create document diagrams

Keep diagram work in the documentation and retrieval branch.
The controlled source remains authoritative; the diagram is a derived view for navigation and explanation.

## Set the boundary

1. Name the authoritative source, page or figure, output file, intended reader, and claims the diagram must support.
Preserve the source unchanged and record the source path, revision or date, checksum when available, and figure or page anchor.
Complete when the diagram has one named authority and every intended claim has a source location.

2. Classify the figure's information loss before choosing a renderer.
Treat labels and simple sequence as text-retrievable when the reading order preserves their meaning.
Inspect the rendered source page when topology, wire geometry, pin association, port direction, relay state, relative placement, or arrow routing carries meaning.
Complete when the geometry-dependent claims have been visually checked or explicitly marked unresolved.

3. Choose the representation from the required precision.
Use Mermaid for a semantic flow, state transition, or relationship view when approximate layout is acceptable.
Use a hand-authored SVG or another fixed-layout artifact when coordinates, ports, crossings, or PDF geometry must be preserved.
Keep the source page as the reference when neither representation can preserve the claim.
Complete when the renderer choice and its deliberate loss or preservation are recorded.

## Build the diagram

- Extract the semantic inventory before writing syntax: nodes, directed edges, labels, edge conditions, special edge colors, annotations, and start or terminal states.
- Use stable, readable node identifiers and preserve source labels verbatim unless a normalization is justified and recorded.
- Keep a figure status or explanatory note outside the Mermaid block when the source presents behavior conceptually rather than as literal implementation.
- Keep layout-only constructs semantically separate from real transitions so a future reader cannot mistake a spacer or hidden link for behavior.

For Mermaid, use the graph's ranks deliberately:

- Set `flowchart TB` or `flowchart LR` to match the reading direction.
- Declare the primary path as an explicit chain where a vertical or horizontal spine matters.
- Use subgraphs to group related nodes, but account for Mermaid's limitation that external node links can override a subgraph's local direction.
- Use invisible links (`~~~`) only to bias ordering or spacing, and label them as layout-only in nearby source comments when their purpose is not obvious.
- Use extra link dashes to request additional rank distance; they do not provide pixel coordinates.
- Tune `nodeSpacing`, `rankSpacing`, and `curve` only when the target renderer supports the configuration.
- Try `layout: elk` for a complex graph when the target Mermaid version supports it; verify the result because renderer availability and output can vary.
- Treat `linkStyle` indexes as order-dependent. Add all real and layout-only edges first, then calculate and verify the indexes. Use edge IDs only when the target renderer supports them.

## Validate the rendered view

Run checks against the actual documentation renderer or a pinned local renderer when available:

1. Parse or render the diagram and confirm there is no syntax error or blank output.
2. Compare the rendered result with the source figure for every node, edge, condition, arrow direction, color distinction, and annotation.
3. Check that layout-only links, subgraph borders, labels, and line crossings do not imply behavior absent from the source.
4. Verify source-page or figure provenance and confirm the output link points to an existing source.
5. Record the remaining precision gap when Mermaid produces an approximate layout or the source image was not available for visual review.

## Complete when

The diagram has a named authoritative source, a deliberate renderer choice, preserved semantic content, validated syntax and rendering, checked provenance, and an explicit statement of any geometry or implementation detail it does not prove.
