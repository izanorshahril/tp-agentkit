---
type: operational_pattern
status: partial
verifier: repo-maintained
date: 2026-04-12
source: ".claude/artifacts/archive/ur7s-ur7t-scr-workflow-plan.md; .claude/artifacts/archive/urx8-qh-ba01-promotion.md; .claude/artifacts/archive/ur7s-job-family-study-20260403.md; .claude/artifacts/archive/ur7s-scr-tightening-update-20260403.md; .claude/artifacts/archive/ur7s-ur7t-special-tp-99-audit-20260331.md; .claude/artifacts/archive/ur7s-ur7t-ton-ilim-700us-plan-20260407.md; .claude/artifacts/archive/urx8-history-20260414/urx8-session-closeout-20260412.md"
source_artifacts_files: 7
source_artifacts_note: "Extended with verified AGR/AMK paired-family interpretation, list-driven unchanged-set audit, active-import overlay-scope guidance, and the official-release versus unconfirmed-branch split from the URX8 closeout"
---

# TP Revision Patterns

Reusable patterns for creating and preparing new test program revisions. These complement the Revision Folder Workflow in `../rules/workflows.md`.

For reusable duplicate-test guidance, including a verified example where one setup was split into explicit 27V and 33V companion tests, also see `./duplicate_test_pattern.md`.
For reusable whole-TP and filtered retained-baseline compare workflow, also see `./tp_diff_compare.md`.

## Extraction Scope

- Historical UQ29 relative-test planning informed this pattern, but the original standalone plan file is not retained in the repo.
- Later UR7S `0022` / UR7T `0017` hot-limit rollout closeout informed the revision-metadata sweep pattern below.
- Later UR7S family-study and section-compare reviews informed the paired AGR/AMK family interpretation pattern below.
- Later UR7S SCR tightening and UR7S/UR7T suffix-99 audit passes informed the unchanged-set audit and active-import overlay-scope guidance below.
- Later URX8 release closeout review informed the official-release versus unconfirmed-branch split pattern below.
- Artifacts processed:
   - `.claude/artifacts/archive/ur7s-ur7t-scr-workflow-plan.md`
   - `.claude/artifacts/archive/urx8-qh-ba01-promotion.md`
   - `.claude/artifacts/archive/ur7s-job-family-study-20260403.md`
   - `.claude/artifacts/archive/ur7s-scr-tightening-update-20260403.md`
   - `.claude/artifacts/archive/ur7s-ur7t-special-tp-99-audit-20260331.md`
   - `.claude/artifacts/archive/ur7s-ur7t-ton-ilim-700us-plan-20260407.md`
   - `.claude/artifacts/archive/urx8-history-20260414/urx8-session-closeout-20260412.md`

---

## 1. Lean Cleanup After Revision Copy

When a TP folder supports multiple product variants (e.g. B01, C01, C02) but the new revision targets **only one variant**, strip unneeded variant files immediately after copying.

### When to Apply

- After copying `<program>_<old_rev>` to `<program>_<new_rev>`.
- When the task explicitly targets a single variant (e.g. "B01 only").
- Before any other edits, so the working tree is clean.

### Keep Rules

| Keep if base name starts with | Examples |
|-------------------------------|----------|
| Target variant prefix | `UQ29FC004B01.tpl`, `UQ29FC004B01.stpl`, `UQ29FC004B01.env`, `UQ29FC004B01.soc` |
| `Main` | `Main.ls`, `Main.bdefs`, `Main.pin`, `Main.menv`, `Main.spec`, `Main.lvl`, `Main.tim`, `MainTestPlan.tpl`, `MaintestPlanFlow.tpl`, `MacroDef.txt` |

### Remove Rules

Remove files matching these extensions that do **not** satisfy any Keep rule above:

- `.stpl`
- `.env`
- `.soc`
- `.tpl`

Also remove legacy cleanup artifacts: `*.bak`, `*copy*`, `*_orig`, files ending with `_`.

### Verification After Cleanup

- Confirm `tplConfigFile.cfg` still references only the kept variant's files (no edit needed if cfg already pointed to the target variant).
- Confirm all `Main*` shared assets are intact.

---

## 2. Relative Test Integration Checklist (OTPL)

End-to-end ordered steps for adding ESM relative tests to an Advantest T2000 OTPL test program. Execute in this order; do not proceed to execution until the full checklist is approved.

For ESM theory and platform code templates, see `./relative_test_esm.md`.
For OTPL guardrails (limit order, import safety, etc.), see `../rules/workflows.md` § OTPL Guardrails.

### Steps

1. **Copy folder** -- `<program>_<old_rev>` → `<program>_<new_rev>`. Verify key files exist in the new folder.

2. **Lean cleanup** (if single-variant) -- Apply § 1 above. Re-verify cfg still resolves.

3. **Bin definitions** -- In `MainTestPlan/Main.bdefs`, add a LeafBin for the relative-test soft bin (e.g. Sbin 31 → Hbin 2, "Relative Test Fail"). Must happen before limit sheet references this bin.

4. **Limit sheet** -- In `MainTestPlan/Main.ls`, add relative test entries (e.g. T500000–T500042). Use the correct limit tuple order for the TP (check UL/LL convention; see OTPL Guardrails #1). Assign the soft bin from step 3.

5. **Flow insertion** -- In `MainTestPlan/MaintestPlanFlow.tpl`, insert the relative sub-flow call (e.g. `${ DFlow( REL, Relative_flw, lastFlow )}`) in the target flow(s) only. Place it **after** all functional tests (e.g. after jvt_Flow). Verify patch scope -- ensure only intended flow blocks were modified (OTPL Guardrails #7).

6. **Relative SubTestPlan** -- Create `SubTestPlans/Relative/RelativeMain.tpl` with `UserVarTransfer` + `Relative_Judge` (Esm function, BranchStatus matching the soft bin). Add `Final ../SubTestPlans/Relative/RelativeMain.tpl;` to `MainTestPlan/<variant>.stpl` after the last existing sub-plan. Do not re-import `Main.spec` (OTPL Guardrails #2). Use a `.ph` class that exists in the TP's search path (OTPL Guardrails #4).

7. **Revision metadata** -- Set `JOB_REV` to the new revision string in `MainTestPlan/<variant>.tpl`. Append a revision block to the history file (at the bottom per workflow rules).

8. **Verification** -- Confirm:
   - Main.ls has the expected number of relative test entries.
   - Main.bdefs has the relative soft bin.
   - Flow order: functional tests → REL::Relative_flw → lastFlow.
   - JOB_REV and history reflect the new revision.
   - No edits in the original (source) folder.
   - Simulator loads without limit-inversion or parse errors (if simulator is available).

### Gate

Do not execute changes until this checklist is read and user approves ("approved" / "proceed").

---

## 3. Applicability Notes

- **Lean cleanup** is generic; adapt the variant prefix and extension list to the target program family.
- **Relative test checklist** is OTPL-specific. For RDK, Flex, or other platforms, adapt the file names and flow mechanisms per `../rules/workflows.md` § Platform-Specific Workflows and `./relative_test_esm.md` § Tester Platform Templates.

---

## 4. RDK Special-TP Overlay Pattern

For the fuller SCR-specific overlay, runtime-flag, validation, and scope-rollback guidance extracted from the same family of work, prefer `./scr_special_tp_pattern.md`. This section keeps only the generic overlay shape that also applies outside SCR.

Use this pattern when a user wants a special launch-package overlay on top of an existing released RDK TP, while keeping the released revision folder unchanged during implementation.

### When to Apply

- The released TP revision number must stay unchanged during development.
- Only a subset of launch jobs needs the special behavior.
- The overlay must stay isolated from the base job files.

### Working Shape That Reused Well

1. Copy the released folder to a working folder such as `<program>_SCRWIP`.
2. Keep the source folder untouched for comparison.
3. Create dedicated overlay launch packages per required job family.
4. Keep copied support files exact where no behavior change is needed.
5. Retarget only the launch files that must point to overlay-specific assets.

### File-Split Pattern

For each overlay job:

- `.env` and `.soc`: usually exact copies of the source counterpart
- `.tpl`: edited to change `TestPlan`, `SocketDef`, and imported limit sheet
- `.cfg`: edited to retarget `tplFile`, `envFile`, and `socFile`
- `.ini`: edited to retarget the launch-file references
- `.ls`: dedicated copied-and-edited limit sheet so overlay limits stay isolated

### Active-Import Scope Gate

Before treating sibling `.ls` or launch files as blocking review items, derive the live scope from the target jobs' `.tpl` imports.

1. Start from the launch packages the user actually wants to ship or review.
2. Read their `.tpl` imports and record which `.ls` files are active for those jobs.
3. Treat non-imported sibling `.ls` files as out-of-scope unless the user explicitly requests a wider family sweep.
4. If the active jobs span paired FH/QH or AGR/AMK families, audit that active set first, then widen deliberately if needed.

### Normalized Overlay Audit Set

For suffix-overlay or special-package audits, normalize the review to these file types before deciding whether the overlay stayed isolated:

- `.ls`
- `.tpl`
- `.cfg`
- `.env`
- `.soc`
- `.ini`
- `*History.txt`

Expected isolated-overlay deltas are usually limited to:

- job-token or package-name renames
- launch-file reference redirects
- standard-limit imports switching to special-limit imports

Unchanged `.env`, `.soc`, overlay `.ls`, or history files are acceptable in this normalized audit when the request is only to redirect launch paths or confirm an already-updated special limit sheet.

### Review Rule

When auditing the overlay, compare against two baselines when possible:

1. previous released revision -> current released revision
2. current released revision -> working overlay copy

This separates normal release delta from overlay-only delta.

---

## 5. Naming-Equivalent Job Clone Pattern

Use this pattern when one material or naming family is missing a launch package, but the user confirms it is functionally equivalent to an existing package from a sibling naming family.

### Verified Example Shape

- Existing family: `BB01/BB02`
- Missing family: `BA01`
- Missing package type: QH job set

### Working Rule

1. Copy the full existing job file set into a temporary working copy first.
2. Clone the matching `.tpl`, `.cfg`, `.env`, `.soc`, and root `.ini` files.
3. Rename internal jobname and file references consistently.
4. Verify no old family token remains inside the cloned set.
5. Promote only the verified cloned set into the official TP folder.

### Why This Matters

- It avoids unnecessary code changes when the difference is only naming coverage.
- It preserves the original package as the known-good reference.
- It keeps the clone review narrow and deterministic.

---

## 6. In-Place Limit Rollout Repair And Audit Pattern

Use this pattern when the user explicitly approves working in place on an already-created revision and the change touches large `.ls` files with repeated or near-duplicate regions.

### When to Apply

- The target revision is already the active working release.
- Multiple `.ls` files need the same limit rollout.
- At least one target file contains repeated test-number regions or duplicated structural blocks.
- A quick patch or repair may accidentally drop adjacent unchanged rows.

### Failure Mode This Guards Against

A narrowly targeted repair can fix the intended limit values while still deleting nearby unchanged content in the same repeated region. In the verified UR7S case, a Ton_ilim repair left the requested limit values correct but dropped the adjacent `# GATE STRESS` block and tests `1004000`, `1004001`, `1004002`, `1004003`, and `1004010` from `Main.ls` and `Main_qth.ls`.

### Safe Repair Sequence

1. Re-read the baseline and current files around the edited region instead of trusting the last patch.
2. If the wrong repeated block was touched, restore the affected local section from the clean baseline first.
3. Re-apply the intended rollout only at the verified target region.
4. Re-check the same change across every sibling `.ls` file that should stay aligned.

### Minimum Verification After Repair

Run these checks for every touched `.ls` file between baseline and current revision, and do not treat a matching value alone as sufficient proof.

0. **Scale and unit audit**
   - Confirm each touched direct row or `${LimitDef(...)}` keeps the correct scale token or `PrecScale` field.
   - Confirm the engineering unit in the target `.ls` matches the intended source reference.
   - If the reference list uses a different unit presentation than the TP file, convert intentionally; do not paste numeric text blindly.

1. **Presence audit**
   - Parse test IDs from direct rows and `${LimitDef(...)}` entries.
   - Confirm no test ID present in baseline is absent from the matching current file.

2. **Occurrence-count audit**
   - Compare per-file occurrence counts for every parsed test ID.
   - This catches repeated-ID cases where one copy survives but another copy was accidentally dropped.

3. **Neighbor-block audit**
   - Read unchanged rows immediately above and below the edited target region.
   - This catches repairs that preserve the intended value but damage nearby unchanged tests or comments.

4. **Tail and footer audit**
   - Always inspect the final section of the edited `.ls`, including `JOB_REV`, EEPROM `LimitDef`s, and trailing lines.
   - This catches stray appended test rows that do not belong near the footer.

5. **Variant-specific baseline audit**
   - Compare each edited flow variant only against its own baseline.
   - Do not force equality across main-flow and QA variants such as FH versus QA FH, FC versus QA FC, or FA versus QA FA.
   - Coverage and limits may intentionally differ between those variants.

6. **Intentionally unchanged-set audit**
   - If the source list includes explicit `No Cut`, keep-as-is, or otherwise excluded rows, record that unchanged ID set before editing.
   - Re-check those IDs after scripted substitution to confirm they stayed unchanged in every intended sibling `.ls` file.
   - Treat this as mandatory when a rollout is driven by an external limit list and nearby IDs share the same repeated region or family.

### Pre-Simulator Sanity Gate

If the user supplies a Beyond Compare HTML export, use it as a final scope cross-check:

1. confirm the baseline/current folders in the export match the live folders
2. confirm the expected edited `.ls` and history files appear in the export
3. confirm expected launch-package additions appear and no unexpected engineering files show up
4. treat clean editor diagnostics as a syntax gate, not as proof of runtime success

### Why This Matters

- It catches silent content loss that a value-only spot check can miss.
- It catches wrong-scale or wrong-unit edits that can look numerically plausible while still being incorrect in TP representation.
- It avoids false defects when QA and main-flow variants intentionally use different coverage or limits.
- In urgent TP releases, non-`.cpp` edits such as `.ls`, `.tpl`, `.cfg`, `.env`, and `.soc` may be packaged and sent forward without a full offline simulator cycle, so these audits may be the last practical safety gate before release.
- It gives a defensible final audit trail before simulator load.
- It is safer than assuming a successful patch on one repeated block implies the rest of the file stayed intact.

---

## 7. Folder-Wide `JOB_REV` Normalization After Up-Rev Audit

Use this pattern when an up-rev, package clone, or follow-up diff review reveals stale prior-revision `JOB_REV` macros inside `MainTestPlan/*.tpl`.

### When to Apply

- The working folder revision has already been established and the main functional edits are complete.
- A diff review or launch-package audit finds at least one `.tpl` still declaring the previous revision string.
- The stale `JOB_REV` looks like a copy-forward issue rather than an intentional one-off exception.

### Failure Mode This Guards Against

A narrow review can first expose the stale revision macro in only one package family, but the real defect may be systemic across the whole `.tpl` set. In the verified UR7S `0022` and UR7T `0017` closeout, the first visible stale values appeared in specific launch-package files, but the safe correction was folder-wide normalization across all target `.tpl` files.

### Safe Normalization Sequence

1. Identify the expected revision string from the target folder name and current release intent.
2. Scan the full `MainTestPlan/*.tpl` set for the prior revision macro, not only the file that first exposed the issue.
3. If the stale value is systemic, normalize the entire `.tpl` set in one pass.
4. Re-check that no old `JOB_REV` string remains under the target `MainTestPlan/` tree.
5. Append a traceability note to the current revision history if the metadata correction happens after the main functional edit set.

### Verification After Normalization

- Confirm every target `.tpl` reports the current folder revision string.
- Confirm no residual prior-revision `JOB_REV` values remain in sibling `.tpl` files.
- Confirm the history file records the metadata correction in the current revision block rather than silently absorbing it.
- Treat filename-versus-`TestPlan` naming oddities as separate review items unless the current change actually introduced them.

### Why This Matters

- Revision metadata drift can survive even when limits, flow, and launch-file references are otherwise correct.
- Fixing only the first exposed file leaves inconsistent traceability across the same revision bundle.
- A folder-wide sweep is safer and easier to defend than assuming the stale macro is isolated.

---

## 8. Paired AGR/AMK Job Family Interpretation Pattern

Use this pattern when a TP family carries paired job sets such as `01/801`, `99/899`, or `SCR01/SCR801`, and the question is whether the pair represents a real functional split or only a launch-package naming split.

### When to Apply

- The TP has sibling launch packages that differ mainly by suffix or job token.
- The family is expected to represent an `AGR` versus `AMK` split.
- Reviewers need to decide whether different filenames imply different behavior.

### Working Rule

1. Compare `.ini`, `.tpl`, and `.cfg` first for job-token and launch-path renames.
2. Check `.env` for the primary family selector, especially `Wafer_Fab = "AGR"` versus `"AMK"`.
3. Treat identical `.soc` files across the pair as normal unless the task explicitly expects socket-level divergence.
4. Compare imported `.ls` content, not only `.ls` filenames. Paired SCR or engineering limit sheets may intentionally keep separate names while remaining text-identical.
5. Group the review by TP section: normal production, SCR or other special-production family, and engineering special family.

### Why This Matters

- It prevents false defects when the real split is carried by `.env` instead of `.soc` or `.ls` content.
- It avoids assuming different dedicated `.ls` filenames mean different active limits.
- It keeps mixed-family revision reviews readable when only one section changed.

---

## 9. Official Release Versus Unconfirmed Branch Split

Use this pattern when the same nominal TP revision exists in two live folders: one is the PE-verified or otherwise approved release candidate, and the other is an exploratory, debug, or unconfirmed working branch.

### When to Apply

- A user clarifies that one folder is the official release source of truth and another similarly named folder is not.
- Prior analysis or edits may already exist against the exploratory branch.
- Packaging, compare, release-note, or change-management work must continue without mixing those branches.

### Working Rule

1. Record the official release folder explicitly.
2. Record the unconfirmed or exploratory branch explicitly.
3. Treat the official folder as the only source of truth for release packaging, release notes, and forward compare work.
4. Do not back-merge conclusions or edits from the exploratory branch into the official folder unless a new explicit review cycle approves that move.
5. When handing off the work, state exactly which folder is official, which folder is exploratory, and whether any official TP files were edited after the split was clarified.

### Why This Matters

- It prevents packaging or shipping the wrong folder when two nearly identical revision names coexist.
- It keeps later diff and release-note conclusions interpretable.
- It preserves traceability when exploratory same-revision work must be retained for reference without becoming the release baseline.
