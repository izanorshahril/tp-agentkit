---
name: scr_special_tp_audit
description: "Audit an RDK SCR special-TP overlay against a baseline folder for expected launch, gating, and marker files."
metadata:
  status: beta
  language: python
---

# SKILL: SCR Special TP Audit

## Purpose

Use `scr_special_tp_audit.py` to audit an Advantest T2000 RDK SCR special-TP overlay against a baseline folder and confirm that the expected structural markers are present.

This skill is intended for review and validation of SCR-style overlay packages, not for editing TP content.

## Tool Entry Point

- Script: `.claude/skills/scr_special_tp_audit/scr_special_tp_audit.py`
- Preferred runner: `python`
- Working directory: workspace root

## When To Use

Use this skill when:
- a TP has dedicated `*SCR*` launch packages layered on top of a baseline RDK TP
- the user wants to confirm the overlay structure before promotion or handoff
- the task includes runtime-gated limits controlled through `SCR_MODE`
- you need to verify that offline-simulator-compatible gating was implemented

Do not use this skill when:
- the task is to edit the TP rather than audit it
- the TP does not use dedicated `*SCR*` launch files
- there is no meaningful baseline folder to compare against

## What It Does

- Scans the current folder for `*SCR*` launch assets under `MainTestPlan/` and at the TP root
- Compares baseline and current file presence for SCR overlay files
- Checks `TestFunctions/Utils.cpp` for both:
  - `SysCUserVars.SCR_MODE`
  - `SysCUserVarsDummy.SCR_MODE`
- Checks SCR `.tpl` files for `String SCR_MODE = "1";`
- Checks `TestProgramHistory.txt` for SCR-related text
- Emits a concise human-readable summary
- Optionally emits one-line JSON for agent consumption

## Standard Commands

### Audit a working SCR overlay against its baseline

```powershell
python .claude/skills/scr_special_tp_audit/scr_special_tp_audit.py \
  --baseline <baseline-tp-folder> \
  --current <current-scr-tp-folder>
```

### Audit with JSON summary

```powershell
python .claude/skills/scr_special_tp_audit/scr_special_tp_audit.py \
  --baseline <baseline-tp-folder> \
  --current <current-scr-tp-folder> \
  --report-json
```

## Inputs

- baseline TP folder
- current TP folder
- optional `--report-json`

## Outputs

- Human-readable summary of:
  - SCR files only in current
  - whether `Utils.cpp` contains live and dummy namespace gating
  - whether SCR `.tpl` files carry `String SCR_MODE = "1";`
  - whether history contains SCR text
- Optional one-line JSON summary

## Notes

- This skill is specific to the RDK SCR-overlay pattern captured in `.claude/knowledge/scr_special_tp_pattern.md`.
- It is a structural audit, not a simulator runner and not a datalog parser.
- Treat a successful audit as implementation evidence, not as a substitute for online real-device validation.