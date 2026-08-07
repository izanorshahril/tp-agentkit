---
type: improvement_report
status: new
date: 2026-03-30
use_case: "T2000 runtime-stop investigation where the framework wrapper message hides the real TP flow-item failure"
---

# Improvement Report: SystemController RTE Stack Mapper

## User Need Captured

- A production stop issue arrived as a generic runtime error at the flow/start-item level.
- The real useful evidence was deeper in `SystemController_Error.log`.
- The investigation required manually extracting repeated low-level stack frames and correlating them back to local TP source files.
- The user then needed a concise expert handoff that separated wrapper message from real failing path.

## Toolkit Gaps Found

1. `system_controller_log_analyzer` summarizes log structure, but it does not currently highlight repeated low-level runtime stacks as the main root-cause candidate.
2. There is no helper that maps stack source paths or function names back to workspace files and local line ranges.
3. There is no standard output format for "wrapper message vs actual low-level failure path".
4. There is no reusable compact handoff generator for expert escalation once the stack is narrowed.

## Proposed Improvement

Extend the current SystemController workflow or add a focused skill that:

1. extracts repeated low-level exception signatures
2. groups incidents by exception text, flow item, DUT/site, and stack frames
3. identifies likely wrapper messages versus underlying failure path
4. searches the workspace for the corresponding TP source files and functions
5. emits a short markdown handoff summary for expert review

## Minimum Feature Set

1. Parse repeated exception blocks from `SystemController_Error.log`.
2. Separate framework wrapper messages from low-level `ATF-UE:UsrErr` or similar exceptions.
3. Report the most repeated failing flow item and DUT/site if present.
4. Map stack function names and source filenames to workspace paths.
5. Produce a concise debug-target summary with source references.

## Guardrails

1. Do not claim the wrapper message is the root cause if deeper repeated stack data exists.
2. Do not overstate certainty if the referenced source file is not present locally.
3. Keep stop-causing RTE conclusions separate from reject or STDF fallout unless explicitly correlated.

## Why This Should Be an Improvement Report, Not a Skill Yet

- The repo already has a narrow `system_controller_log_analyzer`; this proposal is best treated as a focused expansion target.
- The desired behavior is clear now, but the exact output contract should be reviewed before implementing another reusable skill surface.
