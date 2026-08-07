---
type: improvement_report
status: new
date: 2026-03-18
use_case: "Mixed production hang plus reject incident triage with decoded STDF, handler logs, and TP correlation"
---

# Improvement Report: STDF-First Mixed Incident Triage Skill

## User Need Captured

- A production incident arrived as both tester hang or restart behavior and many rejects in the same lot window.
- The useful evidence was spread across decoded STDF, handler logs, OT support logs, and TP source.
- The user explicitly wanted a disciplined workflow: STDF first, then log correlation, then TP correlation.
- The investigation was long enough that durable artifact retention and later knowledge promotion were necessary.

## Toolkit Gaps Found

1. There is no current skill that handles mixed STDF plus handler-log incident triage end to end.
2. `system_controller_log_analyzer` is scoped to `SystemController_Error.log`, so it cannot cover the main evidence path for this class of issue.
3. There is no broader callable ATE incident-log skill in the active framework surface.
4. There is no reusable helper for stitching multiple decoded STDF `T` and `C` files into one chronological lot summary.
5. There is no reusable helper for interpreting abort-style `999/0` PRRs or mapping abnormal `PRR.num_test` values through generated flow metadata.

## Proposed Improvement

Add a real skill for production incident triage rather than another placeholder.

Recommended direction:

- either implement a new skill such as `stdf_first_incident_triage`
- or add a broader incident-triage skill only after its scope is defined clearly enough to avoid another placeholder

## Minimum Feature Set

1. Accept multiple decoded STDF text files and order them by timestamp and `cmod_cod`.
2. Confirm lot, job, and revision identity across all segments.
3. Emit per-segment summaries for part count, dominant soft bins, dominant failing tests, and per-site skew.
4. Detect abort-style PRR clusters such as `soft_bin 999` or invalid-record signatures and report whether they are terminal-only or distributed.
5. Correlate STDF segment boundaries with handler and OT log timestamps for runtime error, reject action, pause, reload, and writer reconnect events.
6. Optionally map abnormal `PRR.num_test` values through `*.Auto.staset` when available.
7. Produce artifact-ready markdown output with chronology tables and cautious conclusions.

## Guardrails

1. Do not claim DUT root cause from controller noise alone when STDF chronology contradicts it.
2. Do not classify `999/0` style records as normal fail bins without checking placement and support logs.
3. Do not assume `PRR.num_test` is a direct `Main.ls` test number for abnormal flush records.
4. Keep runtime-instability conclusions separate from stable reject conclusions.

## Why This Should Not Become Another Placeholder

- The repo already has one planned-only log skill.
- This use case needs concrete parsing behavior, expected outputs, and tested report structure.
- Until that exists, the durable asset should stay in knowledge, with this report serving as the implementation target.