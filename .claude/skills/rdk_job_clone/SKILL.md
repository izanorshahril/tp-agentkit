---
name: rdk_job_clone
description: "Clone an RDK launch-package file set from one job token to another and rewrite internal references consistently."
metadata:
  status: beta
  language: python
---

# SKILL: RDK Job Clone

## Purpose

Use `rdk_job_clone.py` to clone an RDK launch-package file set from one job token to another and rewrite internal jobname/file references consistently.

This skill is intended for naming-equivalent launch-package creation where one job family is missing but is confirmed to be functionally equivalent to an existing one.

## Tool Entry Point

- Script: `.claude/skills/rdk_job_clone/rdk_job_clone.py`
- Preferred runner: `python`
- Working directory: workspace root

## When To Use

Use this skill when:
- a TP is missing a `.tpl/.cfg/.env/.soc/.ini` launch package for a naming-equivalent job
- the user confirms the source and target job packages should be functionally the same except for naming
- you need a fast, consistent clone with reference replacement

Do not use this skill when:
- the target package requires behavior changes beyond renaming
- source and target job families are not confirmed equivalent
- the task requires editing code or limit behavior, not just cloning launch files

## What It Does

- Clones the source job file set under `MainTestPlan/`:
  - `.tpl`
  - `.cfg`
  - `.env`
  - `.soc`
- Clones the root `.ini`
- Replaces the source job token with the target job token inside all cloned files
- Supports dry-run preview or in-place write mode
- Optionally emits JSON for agent consumption

## Standard Commands

### Dry-run preview

```powershell
python .claude/skills/rdk_job_clone/rdk_job_clone.py \
  --root testprogram/URX8_0001 \
  --source-job URX8QH008BB01 \
  --target-job URX8QH008BA01
```

### Apply the clone

```powershell
python .claude/skills/rdk_job_clone/rdk_job_clone.py \
  --root testprogram/URX8_0001 \
  --source-job URX8QH008BB01 \
  --target-job URX8QH008BA01 \
  --write
```

## Inputs

- TP root folder
- source job token
- target job token
- optional `--write`
- optional `--report-json`

## Outputs

- Dry-run list of files that would be created
- Or written cloned files with rewritten internal references
- Optional one-line JSON summary

## Notes

- This skill assumes the source and target file set are plain text files.
- It is intentionally narrow: clone and rename only, no behavior changes.
- For the motivating example and general pattern, see `.claude/knowledge/tp_revision_patterns.md`.