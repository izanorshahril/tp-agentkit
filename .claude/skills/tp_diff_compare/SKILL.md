---
name: tp_diff_compare
description: "Compare two TP folders recursively and optionally cross-check the live delta set against a Beyond Compare-style multi-file HTML export or a WinMerge folder summary HTML export."
metadata:
  status: beta
  language: python
---

# SKILL: TP Diff Compare

## Purpose

Use `tp_diff_compare.py` to compare two test program folders recursively and report per-file differences across the whole TP.

It can also cross-check the live folder delta against either:
- a Beyond Compare multi-file HTML export with repeated `File:` sections
- a Beyond Compare directory-summary HTML with `Left base folder`, `Right base folder`, and a directory compare table
- a WinMerge folder summary HTML that links to a sibling `.files/` directory of per-file reports

This skill is intended for full TP audits, revision-to-revision review, retained-baseline comparison, and packaging checks where the user needs whole-folder visibility instead of a filtered engineering-only subset.

## Tool Entry Point

- Script: `.claude/skills/tp_diff_compare/tp_diff_compare.py`
- Preferred runner: `python`
- Working directory: workspace root

## When To Use

Use this skill when:
- the user asks for a whole TP diff between two folders
- the user needs file-by-file presence and content deltas across the entire TP
- the baseline is retained under `references/`, `testprogram/`, or another known path
- git history is incomplete, ignored, or unavailable for the TP folder itself
- the user provides a Beyond Compare-style TP HTML export and wants it checked against the live TP delta scope
- the user provides a WinMerge folder summary HTML and wants it checked against the live TP delta scope

Do not use this skill when:
- the task is a raw git review of repository-tracked source only
- the user wants semantic conclusions without first establishing the file-level delta set

Overlay-specific note:
- when auditing a special-TP overlay, first compare previous release -> current release, then compare current release -> overlay copy
- when one side has been simulator or IDE build residue, expect `.dll`, `.pdb`, `.lib`, `.exp`, `.obj`, `.tlog`, `.ipch`, `.sdf`, and `.suo` noise in whole-folder mode

## Default Compare Scope

Default behavior:
- walk both folders recursively
- compare all files by relative path
- report files only in baseline/current
- report changed files across the whole TP
- support optional unified text diffs for changed text files
- support optional markdown summary report output

Markdown report mode:
- writes one markdown file
- includes the whole-folder compare
- includes a second compare using the recommended engineering filters:
  - `.cpp`
  - `.h`
  - `.pat`
  - `.ls`
  - `.tpl`
  - `.bdefs`
  - `*History.txt`
- includes detailed per-file content diffs for changed files in the recommended engineering-filter section
- ignores unknown-extension or non-text/binary files in the detailed compare section
- trims large detailed diffs to contextual hunks instead of dumping the entire file diff

Optional narrowing:
- `--filter-ext` to restrict to selected extensions
- `--filter-glob` to restrict to selected filename globs

Overlay review follow-up filter set:
- `.cpp`
- `.ls`
- `.tpl`
- `.cfg`
- `.env`
- `.soc`
- `.ini`
- `*History.txt`

## Standard Commands

### Whole TP compare

```powershell
python .claude/skills/tp_diff_compare/tp_diff_compare.py \
  --baseline testprogram/UR8K_2207 \
  --current testprogram/UR8K_2700
```

### JSON output for agent consumption

```powershell
python .claude/skills/tp_diff_compare/tp_diff_compare.py \
  --baseline testprogram/UR8K_2207 \
  --current testprogram/UR8K_2700 \
  --report-json
```

### Show unified diffs for changed text files

```powershell
python .claude/skills/tp_diff_compare/tp_diff_compare.py \
  --baseline testprogram/UR8K_2207 \
  --current testprogram/UR8K_2700 \
  --show-diff
```

### Cross-check with an exported HTML folder diff

```powershell
python .claude/skills/tp_diff_compare/tp_diff_compare.py \
  --baseline testprogram/UR7S_0021 \
  --current testprogram/UR7S_0022 \
  --compare-html "references/Beyond Compare/UR7S_NewTP_Rev0022_Diff.html"
```

### Cross-check with a WinMerge folder summary report

```powershell
python .claude/skills/tp_diff_compare/tp_diff_compare.py \
  --baseline testprogram/UR7S_0021 \
  --current testprogram/UR7S_0022 \
  --compare-html references/WinMerge/UR7S_NewTP_0022_Diff.html
```

### Write a markdown report artifact

```powershell
python .claude/skills/tp_diff_compare/tp_diff_compare.py \
  --baseline testprogram/UR8K_2207 \
  --current testprogram/UR8K_2700 \
  --report-markdown .claude/artifacts/current_task/tp_diff_report.md
```

### Narrow to selected file types when needed

```powershell
python .claude/skills/tp_diff_compare/tp_diff_compare.py \
  --baseline testprogram/UR7T_0016 \
  --current testprogram/UR7T_0017 \
  --filter-ext .cpp \
  --filter-ext .ls \
  --filter-ext .tpl \
  --filter-glob *History.txt
```

## Inputs

- baseline TP folder
- current TP folder
- optional extension filters
- optional filename-glob filters
- optional unified-diff output request
- optional markdown report output path
- optional external HTML diff export for scope cross-check
- optional WinMerge folder summary HTML for scope cross-check

## Outputs

- Human-readable summary of:
  - compare scope
  - files only in baseline/current
  - changed files
  - changed counts by type
  - optional external HTML scope cross-check status
  - optional unified text diffs for changed files
- Optional markdown report file
- Optional one-line JSON summary

## Notes

- This skill is the general TP diff entry point.
- Use whole-TP output first, then narrow follow-up review to the files that matter.
- Markdown report mode combines the whole-folder compare and the recommended engineering-filter compare into one artifact.
- The recommended-filter section can include actual unified text diffs for the changed files so the markdown captures file-content changes, not just filenames.
- Unknown-extension or binary files are skipped from detailed compare output.
- For overlay audits, a second narrowed compare that includes `.cfg`, `.env`, `.soc`, and `.ini` is often more useful than the default engineering filter.
- For a previously validated retained-baseline review pattern, including focused `.cpp`, `.ls`, `.tpl`, and history-only review, see `.claude/knowledge/tp_diff_compare.md`.
- External HTML cross-check mode is intended as a scope gate. It checks base-folder metadata, delta-path coverage, and per-path status (`changed`, `only_current`, `only_baseline`) against the live folder compare.
- Supported external HTML inputs are Beyond Compare-style multi-file reports and WinMerge folder summary pages.