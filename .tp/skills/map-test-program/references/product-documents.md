# Product documentation set

Create a small linked documentation set that helps the next engineer navigate the product and test program without turning derived Markdown into a second specification.

## Name and place it

Use the confirmed product identifier as a filesystem-safe prefix. For product `AB12`, default to:

- `AB12_TP.md`: current test-program navigation hub
- `AB12_PRODUCT.md`: test-relevant product facts derived from supplied datasheet or product documentation
- `AB12_PCMS.md`: normalized trace for supplied PCMS records or documents

Keep the product prefix on companions so a shared workspace cannot silently mix products. Honor an established repository naming convention or an explicit user name instead. If product identity is unknown, continue with `.tp/work/` task notes until it is proven. If several variants share one active program lineage, use one family hub with a variant matrix; split hubs when launch, authority, or revision ownership diverges.

Place the set in an existing user-approved documentation location. If none exists, use the mapped program root without adding a folder scaffold. When no safe durable location is writable, retain the task map and ask before promotion.

## Treat the files by role

- The TP hub is a navigational synthesis. It does not replace program source, launch configuration, limits, or runtime evidence.
- A companion is a source-specific, test-relevant summary. It does not replace the raw document.
- Preserve every raw supporting document unchanged. Record its path, displayed identifier or revision, date, applicable scope, and a checksum when practical.
- Link a fact to the file, page or section, symbol, revision, or runtime record that supports it. Mark unsupported interpretations as `inferred` or `unknown`.
- Link revision history to a focused diff or changed files and symbols. Summarize the effect instead of copying a full diff into Markdown.

Use document state `draft`, `verified`, or `stale`. Use claim basis `inspected-source`, `runtime`, `user-stated`, `inferred`, or `unknown`; avoid numeric confidence scores.

## Build `<PRODUCT>_TP.md`

Start with machine-readable identity and freshness:

```yaml
---
kind: test-program-map
product: AB12
status: draft
last_verified: YYYY-MM-DD
---
```

Then record only evidenced, test-relevant context:

1. **Scope and identity:** product or family, program name and revision, documentation scope, active baseline, and known exclusions.
2. **Product and process matrix:** variant or option, package, silicon process or stepping, test stage such as probe or final test, temperature or grade, and the applicable launch or flow. Keep silicon process and test stage separate.
3. **Execution environment:** tester platform and model, tester software release, site count, handler or prober, loadboard or probe card, instruments, and other configuration that changes behavior. Unknown fields stay unknown.
4. **Active program graph:** launch -> top plan -> subplan or flow -> definition/limits/bins -> implementation -> datalog or runtime evidence. Name the owning file and key symbol at every useful edge.
5. **Authority register:** TP source, product document, PCMS or specification, runtime evidence, revision/date, applicable variants, and companion link.
6. **Change trace:** change identifier -> requirement source -> source and target TP revisions -> affected files/symbols -> focused diff -> verification evidence.
7. **Evidence gaps:** unresolved facts, why they matter, and the check that would resolve each one.

## Build `<PRODUCT>_PRODUCT.md`

Create or refresh this companion when supplied product or IC documentation materially informs the TP. Capture:

- raw source identity, revision/date, path, and applicable product scope;
- family, variants, options, package, silicon process or stepping, grades, and operating conditions that affect test behavior;
- a test-relevance table mapping each product fact to TP limits, setup, flow, binning, or coverage consumers;
- page or section provenance and claim basis for each derived fact;
- conflicts between the product source and current TP, without silently choosing one.

Summarize the test-relevant subset; leave general datasheet content in the raw source.

## Build `<PRODUCT>_PCMS.md`

Create or refresh this companion when a supplied PCMS record or document is used to understand or change the program. Preserve the source's own meaning of `PCMS`; do not expand or reinterpret the acronym without evidence. For each change, trace:

| Field | Record |
|---|---|
| Change identity | ID, source revision/date, approval or status |
| Applicability | product, variant, package, silicon process/stepping, test stage |
| Requirement | prior behavior, requested behavior, units and conditions |
| TP mapping | source/target TP revision and affected flow, limit, setup, bin, file, or symbol |
| Implementation evidence | focused diff or revision-history reference |
| Verification | parser, compile, simulator, tester, datalog, or lot evidence and result |
| Open trace | unresolved mapping or missing authority |

One companion may register several PCMS source revisions. Create a separate companion only when product scope or change authority is genuinely independent.

## Refresh and complete

Before relying on an existing set, compare its registered source revision or checksum, TP revision, launch path, and last-verified date with current evidence. Mark the document `stale` as soon as a material mismatch is observed, then refresh affected claims and links.

The set is complete for the inspected scope when the TP hub identifies the active product/variant/platform path, every material supporting document has an unchanged raw source and a traceable companion, every implemented change connects requirement -> revision/diff -> verification, and unknowns remain explicit.
