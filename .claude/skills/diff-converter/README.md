# HTML Diff Converter

Convert WinMerge-generated HTML compare reports, WinMerge folder summary reports with companion `.files/` child reports, and compatible Beyond Compare-style folder HTML reports into:
- unified patch files (`.patch`)
- human-readable text diffs (`.txt`)
- reconstructed left/right source files from the full-context diff rows

Script: `html_diff_converter.py`

Compatibility wrapper:
- `winmerge_html_diff.py` remains available and forwards to `html_diff_converter.py`

## What This Solves

Diff HTML exports are easy to view in a browser but hard to automate. This tool converts those reports into machine-usable outputs and can rebuild both original sides of the comparison.

## Requirements

- Python 3.9+
- `uv` (recommended in this workspace)

## Quick Start

Run from the folder where the HTML files and script are located.

### Batch: generate patches + rebuild both sides

```powershell
uv run python .\html_diff_converter.py . --format patch --out-dir .\winmerge_export --rebuild-sides --rebuild-dir .\winmerge_rebuilt
```

### Single file: patch + rebuild

```powershell
uv run python .\html_diff_converter.py .\absolute_tpl.html --format patch --output .\winmerge_export\absolute_tpl.patch --rebuild-sides --rebuild-dir .\winmerge_rebuilt
```

### Beyond Compare-style folder HTML: per-file export + rebuild

```powershell
uv run python .\html_diff_converter.py .\UR7S_NewTP_Rev0022_TP_Diff.html --format patch --out-dir .\bc_export --rebuild-sides --rebuild-dir .\bc_rebuilt
```

### WinMerge folder summary HTML: follow linked per-file reports

```powershell
uv run python .\html_diff_converter.py .\references\WinMerge\UR7S_NewTP_0022_Diff.html --format patch --out-dir .\wm_export --rebuild-sides --rebuild-dir .\wm_rebuilt
```

### Text report only (all HTML files)

```powershell
uv run python .\html_diff_converter.py . --format text --out-dir .\winmerge_export
```

## CLI Options

```text
positional:
  source                HTML file path OR folder of HTML files

options:
  --format {text,patch,both}
                        Output type (default: both)
  --output PATH         Single-file output path (stdout if omitted)
  --out-dir PATH        Batch output folder or multi-file HTML export folder
  --rebuild-sides       Rebuild full left/right files from table rows
  --rebuild-dir PATH    Rebuild folder (default: <source>/winmerge_rebuilt)
```

## Output Layout

### Patch/text exports

- Batch mode writes to `winmerge_export/` by default:
  - `<name>.patch`
  - `<name>.txt`

- A single multi-file HTML export writes one artifact per `File:` section.
- Output paths are grouped under `<report-stem>/` when the HTML contains multiple file sections.

### Rebuilt files

- Rebuilt files go to `winmerge_rebuilt/` by default for classic single-file reports.
- Multi-file HTML exports rebuild into `<html-stem>_rebuilt/` by default.
- Paths are inferred from WinMerge header titles or from base-folder metadata plus `File:` section paths.
- Example:
  - `winmerge_rebuilt\UAF3FH108CCG01_0008\SubTestPlans\ABS\ABSMain.tpl`
  - `winmerge_rebuilt\UAF3FH108CCG01_0009\SubTestPlans\ABS\ABSMain.tpl`

## Notes

- This tool supports the standard single-compare WinMerge HTML format, WinMerge folder summary pages that link into a sibling `.files/` directory, and compatible multi-file folder-report HTML that includes `Left base folder`, `Right base folder`, and repeated `File:` sections.
- Beyond Compare directory-summary pages (`table class="dc"`) are inventory-only and do not contain per-file text rows, so this tool will reject them.
- If a report has no differences, patch output contains `# No differences found.`
- Rebuilt files reflect line content represented in the HTML report rows.

## Automation Example

```powershell
uv run python .\html_diff_converter.py . --format patch --out-dir .\winmerge_export --rebuild-sides --rebuild-dir .\winmerge_rebuilt
Get-ChildItem .\winmerge_export\*.patch
Get-ChildItem .\winmerge_rebuilt -Recurse
```
