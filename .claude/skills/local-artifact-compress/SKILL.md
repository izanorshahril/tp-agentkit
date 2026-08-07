---
name: local-artifact-compress
description: "Use when compacting markdown or text artifacts inside the closed environment without any network calls or external model dependency."
metadata:
  status: beta
  language: python
---

# Local Artifact Compress

Use `local_artifact_compress.py` to compact natural-language markdown or text files locally.

This skill is meant for closed-environment token reduction. It does not call any remote service.

## Purpose

- reduce future prompt-input cost from long artifact files
- keep the operation local and deterministic
- preserve structure that must not change during compaction

## Tool Entry Point

- Script: `.claude/skills/local-artifact-compress/local_artifact_compress.py`
- Preferred runner: `python`
- Working directory: workspace root

## When To Use

Use this skill when:

- a `.md`, `.txt`, `.markdown`, or `.rst` artifact is long and mostly prose
- the file lives under `.claude/artifacts/` or another approved documentation area
- the team wants a local-only alternative to model-driven compression

Do not use this skill when:

- the file is code, config, JSON, CSV, HTML, or another non-prose format
- the target is under `testprogram/`
- the file is safety-critical and should stay fully explicit
- the file already has a `.original.md` or `.original.txt` backup beside it and the user has not reviewed that state

## What It Preserves

- frontmatter
- markdown headings
- fenced code blocks
- inline code spans
- markdown links and bare URLs
- file paths
- markdown tables
- blockquotes

## What It Compresses

- paragraph prose
- bullet item prose
- numbered item prose
- filler phrases and repeated soft wording

Two local modes are available:

- `conservative`: safe reduction first; if there is no clear win, the original is kept
- `aggressive`: drops more filler and some articles for stronger size reduction on completed low-risk artifacts

## Outputs

- compressed text written to `--output`, or
- in-place overwrite with a sibling backup when `--in-place` is used
- optional one-line JSON summary for automation

## Standard Commands

### Write to a new output file

```powershell
python .claude/skills/local-artifact-compress/local_artifact_compress.py \
  .claude/artifacts/current_task/repo-learning-summary.md \
  --output .claude/artifacts/current_task/repo-learning-summary.compact.md \
  --report-json
```

### Write with aggressive mode

```powershell
python .claude/skills/local-artifact-compress/local_artifact_compress.py \
  .claude/artifacts/current_task/repo-learning-summary.md \
  --output .claude/artifacts/current_task/repo-learning-summary.compact.aggressive.md \
  --mode aggressive \
  --report-json
```

### Compact in place with backup

```powershell
python .claude/skills/local-artifact-compress/local_artifact_compress.py \
  .claude/artifacts/current_task/repo-learning-summary.md \
  --in-place \
  --report-json
```

## Validation Behavior

- validates preserved headings, code blocks, URLs, and file paths before writing unless `--no-validate` is passed
- refuses in-place overwrite when the expected backup file already exists
- does not write outside the chosen file path and its explicit backup path
- if the conservative rewrite is not smaller than the original, keeps the original content and reports that no savings were found
- preferred compact-JSON stdout flag: `--report-json` (`--json` remains accepted as a compatibility alias)

## Notes

- no external dependencies
- no network access required
- no hidden prompt injection or user-home config changes
- best first targets are large, completed, prose-heavy task artifacts rather than active safety-critical protocol files
- diff-heavy compare artifacts may validate cleanly but produce only small size reductions
- use `aggressive` only on completed low-risk artifacts where readability can trade a little for stronger compaction