---
type: operational_pattern
status: partial
verifier: decoded STDF chronology plus handler/OT log correlation plus TP source inspection
date: 2026-04-12
source: ".claude/artifacts/archive/urx8-production-log-analysis-20260318.md; .claude/artifacts/archive/tp-agentkit-5s-audit-20260318.md; .claude/artifacts/current_task/urx8-ba-zero-yield-csv-investigation-20260409.md"
source_artifacts_files: 3
source_artifacts_note: "Promoted from the URX8 mixed runtime-stop plus reject incident investigation and later extended with good-run versus bad-run export limit-header comparison"
---

# STDF-First Mixed Incident Triage

Reusable pattern for production incidents that present as both tester hang or restart behavior and many rejects in the same lot window.

## Extraction Scope

- Source case: `URX8FH008BB01` on lot `99612BGQ01`
- Evidence set: decoded STDF text, handler logs, OT/T2000 support logs, and production TP source
- Incident shape: repeated pre-`04:11` runtime stops followed by a later runtime-stable but reject-heavy continuation
- Later URX8 BA investigation extended this pattern with good-run versus bad-run export limit-header comparison to separate deployed-limit drift from DUT-signature drift.

---

## 1. Problem Shape

Use this pattern when:

- the user reports both hang or restart behavior and elevated rejects in one production window
- decoded STDF exists, especially as multiple `T` and `C` segments for the same lot
- handler or cell-controller logs show runtime errors, reconnects, or forced stop and reload cycles
- the same TP text appears structurally valid, so the question is runtime state versus static TP content

---

## 2. Core Lessons Learned

1. Anchor on decoded STDF first.
   - STDF gives the cleanest chronological record of what the lot actually produced. Use it before arguing from controller logs.

2. Treat `T` then `C` files as one lot unless identity changes.
   - Confirm `lot_id`, `job_nam`, and `job_rev` across all files. If they match, rebuild one chronological incident instead of analyzing each file as a separate run.

3. Split the incident into two layers early.
   - Separate runtime-stop behavior from persistent reject behavior. A lot can recover from restart instability while still carrying the same site-linked reject families.

4. Do not over-read abnormal `999/0` PRRs as normal fail bins.
   - In the URX8 case, `soft_bin = 999`, `hard_bin = 0`, `part_flg = 0x1c`, invalid coordinates, and `test_t = 0` clustered at segment ends and aligned with stop windows. That pattern is best treated as abort residue, not a normal DUT fail mechanism.

5. `PRR.num_test` in abnormal records may be an internal sequence slot.
   - When abort-style PRRs are present, map `PRR.num_test` through generated flow metadata such as `*.Auto.staset` before assuming it is a direct `Main.ls` test number.

6. TP inspection is still required even when STDF leads the workflow.
   - Use TP source to rule out missing definitions and to identify runtime dependencies. In the URX8 case, `JOB_REV` was fully wired in TP text, which shifted the root-cause theory toward framework-managed runtime state.

7. Handler logs usually carry the sharpest crash signature.
   - Supporting OT or T2000 logs may explain restart or writer disruption, but the handler log often identifies the failing flow and start item most directly.

---

## 3. Recommended Execution Order

1. Inventory all decoded STDF files for the incident window.
2. Confirm lot and job identity across the full set.
3. Rebuild the lot chronology in actual timestamp order using `cmod_cod` and file windows.
4. Summarize each segment by PRR count, dominant soft bins, dominant failing tests, and per-site skew.
5. Isolate abnormal PRR signatures such as `999/0` and check where they appear within each file.
6. Correlate segment boundaries with handler runtime errors, reject actions, pauses, reloads, and writer reconnects.
7. Inspect TP flow text and supporting code for the failing start item or dependency named in the runtime logs.
8. If abnormal `PRR.num_test` values appear, map them through generated flow metadata before drawing conclusions.
9. State the final result as separate conclusions for runtime instability and real production fallout.

---

## 4. Interpretation Patterns That Worked

### Segment Boundary Pattern

If the first few STDF files end immediately after handler runtime faults and the final file ends on a clean pause, interpret the early files as interrupted segments rather than arbitrary export splits.

### Abort-Residue Pattern

If abnormal PRRs:

- cluster only at the end of a segment
- cover the active sites seen just before stop time
- carry invalid timing or coordinate fields
- and the log path shows aborted-test conversion

then classify them as stop-time flush residue first.

### Stable-Reject Pattern

If a later continuation no longer shows abort residue but still shows strong site-linked non-pass families, treat that as a separate persistent reject problem. Do not let the earlier runtime crash explain away later yield loss.

### Runtime-State Versus Static-Content Pattern

If TP inspection confirms:

- the failing flow item exists
- the limit entry exists
- sibling jobs use the same structure
- and checked STDF runs show normal values when the item executes

then the remaining theory should move toward framework or runtime state, not missing TP text.

---

## 5. Minimum Deliverables For Similar Future Incidents

- one chronology table across all STDF segments
- one runtime-alignment table against handler timestamps
- one separation of abort residue versus real fail families
- one per-site outlier summary for the stable phase
- one TP correlation summary that states what was ruled out and what remains plausible

---

## 6. Good-Run Versus Bad-Run Export Limit-Header Compare

Use this extension when a known-good export and a failing export both exist for the same product family and the question is whether the reject delta comes from a different loaded tester limit state, a different DUT signature, or both.

### Working Rule

1. Compare exported `LowL` and `HighL` values for the same failing tests between the good run and the bad run.
2. Separate tests whose active limits changed from tests whose active limits stayed the same.
3. For tests with unchanged active limits, compare the measured-value ranges or stable signatures between the two runs.
4. Use static TP compare as a companion check, not as the only source of truth for what the tester actually loaded.

### Why This Matters

- It cleanly separates deployed-limit drift from true DUT-population or signature drift.
- It prevents over-attributing a yield excursion to TP text when the loaded tester limit state was different.
- It also prevents the opposite mistake: assuming everything is a limit issue when the active limits are identical but the measured signatures changed.

### Verified URX8 Outcome Shape

- In the URX8 BA case, `20062 / ABS_XOUT_pos_typ` differed at the export-header level between the good run and the bad run, proving a different loaded active limit state.
- The `801xx` ChipID/NVM block kept the same numeric export limits across both runs, so the remaining difference had to be explained by DUT signature rather than a changed limit table.

---

## 7. Limits Of This Pattern

- This pattern improves triage quality, not root-cause certainty by itself.
- It does not replace lower-level framework exception data when those logs are available.
- `999/0` interpretation should still be validated against the actual STDF conversion path if the support logs exist.
- The sequence-slot mapping lesson is strongest when generated metadata such as `*.Auto.staset` is present.

---

## 8. Skill-Promotion Guidance

Related proposal: `./improvements/stdf_first_mixed_incident_triage_skill_20260318.md` captures the pending executable-skill promotion idea. Treat this file as the durable methodology and the improvement report as the tooling proposal.

This workflow is reusable, but in this repo it is not yet a clean executable skill because:

- `system_controller_log_analyzer` is intentionally narrow to `SystemController` logs
- there is no broader callable ATE incident-log skill yet
- mixed incident triage requires coordinated STDF parsing, log correlation, and optional TP sequence mapping

Current best promotion path:

- keep the methodology in knowledge now
- implement a dedicated incident-triage skill only when the parser interface and expected outputs are stable enough to avoid another placeholder module
