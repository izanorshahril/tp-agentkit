---
name: doc-path-audit
description: Audit TP-AgentKit docs and text artifacts for workspace-looking path literals, classifying missing references versus placeholders, output paths, and historical notes.
metadata:
  status: beta
  language: python
---

# Doc Path Audit

Use `doc_path_audit.py` to scan markdown, text, JSON, or `.mdc` files for workspace-looking path literals such as `references/...`, `testprogram/...`, and `.claude/...`, then classify whether each path is live, missing, historical, placeholder-only, or likely command output.

This skill is for repo-maintenance and documentation-hygiene audits, not TP execution or release validation.

## Tool Entry Point

- Script: `./doc_path_audit.py`
- Preferred runner: `python`
- Working directory: workspace root

## When To Use

Use this skill when:

- maintained docs or archive notes may still point to removed workspace files
- a repo-maintenance pass needs a repeatable path-integrity scan instead of ad hoc grep work
- you want missing-path findings separated from placeholders, command-created outputs, or explicit historical notes

Do not use this skill when:

- the task is to validate TP runtime references inside tester source files
- the target surface is binary-only data or non-text payloads
- you need a full semantic doc linter; this tool is heuristic and path-focused

## Standard Commands

### Scan maintained docs with compact JSON output

```powershell
python .claude/skills/doc-path-audit/doc_path_audit.py README.md AGENTS.md .claude references --report-json
```

### Scan archive artifacts only

```powershell
python .claude/skills/doc-path-audit/doc_path_audit.py .claude/artifacts/archive --report-json
```

### Scan a temp or alternate workspace root

```powershell
python .claude/skills/doc-path-audit/doc_path_audit.py docs --workspace-root c:/Temp/sample-repo --report-json
```

## Inputs

- one or more files or directories to scan
- optional workspace root override for path resolution

## Outputs

- human-readable summary by default
- optional compact JSON summary with counts and unresolved findings

## Notes

- The tool focuses on workspace-looking relative paths such as `.claude/...`, `references/...`, `testprogram/...`, `README.md`, and `AGENTS.md`.
- Historical-only root-doc names such as `USER_WORKFLOW.md` are still detected when they appear in archive notes or older maintenance records.
- Explicit placeholders such as `<path-to-file>` and explicit historical notes such as `not retained in the current workspace` are classified separately from unresolved live breaks.
- Command-created outputs such as `--output ...` and `--json-output ...` are treated separately so a not-yet-created artifact does not look like a broken input.
- The extraction is heuristic. Backticked or quoted path literals are the most reliable; free-form prose can still need reviewer judgment.