---
name: diff-converter
description: "Convert WinMerge and Beyond Compare HTML diff reports into patches, text reports, and reconstructed file trees."
metadata:
	status: beta
	language: python
---

# SKILL: HTML Diff Converter

## Purpose

Use `html_diff_converter.py` to transform WinMerge HTML reports, WinMerge folder summary reports with linked child comparisons, and compatible Beyond Compare-style folder HTML reports into automation-ready artifacts:
- unified patches for code review or apply workflows
- text diff reports for quick inspection
- reconstructed left/right source files for downstream tooling

## Tool Entry Point

- Script: `html_diff_converter.py`
- Compatibility wrapper: `winmerge_html_diff.py`
- Preferred runner: `uv run python`
- Working directory: folder containing script and WinMerge HTML files

## When To Use

Use this skill when:
- input is WinMerge `*.html` compare report(s)
- input is a WinMerge folder summary HTML plus its companion `.files/` directory of linked per-file reports
- input is a Beyond Compare-style multi-file TP HTML export with `Left base folder`, `Right base folder`, and repeated `File:` sections
- user asks for patch generation from diff HTML
- user needs original left/right files rebuilt from diff HTML context
- user wants batch conversion for CI or scripted processing

Do not use this skill when:
- input is already raw source files and native diff tools are available
- HTML does not contain either the standard WinMerge single-compare table structure or the compatible multi-file folder-report structure above
- input is a Beyond Compare directory-summary page without per-file text rows; use `tp_diff_compare` for scope validation instead

## Standard Commands

### Batch patch + rebuild (default automation path)

```powershell
uv run python .\html_diff_converter.py . --format patch --out-dir .\winmerge_export --rebuild-sides --rebuild-dir .\winmerge_rebuilt
```

### Batch text only

```powershell
uv run python .\html_diff_converter.py . --format text --out-dir .\winmerge_export
```

### Single-file patch + rebuild

```powershell
uv run python .\html_diff_converter.py .\absolute_tpl.html --format patch --output .\winmerge_export\absolute_tpl.patch --rebuild-sides --rebuild-dir .\winmerge_rebuilt
```

### Beyond Compare-style folder HTML: split into per-file patches

```powershell
uv run python .\html_diff_converter.py .\UR7S_NewTP_Rev0022_TP_Diff.html --format patch --out-dir .\bc_export --rebuild-sides --rebuild-dir .\bc_rebuilt
```

### WinMerge folder summary HTML: split linked per-file reports

```powershell
uv run python .\html_diff_converter.py .\references\WinMerge\UR7S_NewTP_0022_Diff.html --format patch --out-dir .\wm_export --rebuild-sides --rebuild-dir .\wm_rebuilt
```

## Agent Workflow

1. Detect scope:
- If user passes one HTML file, run single-file mode.
- If user mentions "all" or folder processing, run batch mode on `.` or specified folder.

2. Choose outputs:
- Default to `--format patch` for tooling interoperability.
- Add `--rebuild-sides` when user requests source reconstruction.
- Use `--format both` only when user explicitly wants human text report and patch together.

3. Validate results:
- Check process success message.
- Confirm patch files exist in output folder.
- If rebuilding, verify expected left/right file paths exist and are non-empty.

4. Report back:
- Provide executed command(s).
- Provide output directories and key generated files.
- Mention any limitations encountered.

## Expected Inputs and Outputs

Input:
- WinMerge HTML file(s) with compare-table title headers.
- WinMerge folder summary HTML with linked per-file `.html` reports in a sibling `.files/` folder.
- Compatible multi-file folder-report HTML with `Left base folder`, `Right base folder`, and repeated `File:` sections.

Output:
- Patch files: `*.patch`
- Text reports: `*.txt` (when requested)
- Rebuilt source trees: under rebuild directory (when requested)
- For a single multi-file HTML export, one patch/text file per `File:` section under the chosen output directory
- For a WinMerge summary HTML, one patch/text file per linked child report under the chosen output directory

## Error Handling

If source path does not exist:
- Fail early and report missing path.

If no HTML files found in folder:
- Report and stop.

If HTML format differs from supported structures:
- Report partial/failed parse risk.
- Fall back to patch-only generation if possible, else stop and request sample file.

## Constraints and Notes

- Rebuilt paths are inferred from title paths or base-folder plus `File:` section paths, with invalid filename characters sanitized.
- Reconstructed output reflects the HTML row content exactly (including any normalized spaces represented by WinMerge HTML).
- Preserve generated artifacts; do not delete unless user asks.
