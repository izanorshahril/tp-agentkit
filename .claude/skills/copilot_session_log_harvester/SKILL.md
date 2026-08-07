---
name: copilot_session_log_harvester
description: Harvest GitHub Copilot debug session logs into compact cross-session summaries for TP-AgentKit maintenance.
metadata:
  status: beta
  language: python
  source: local
---

# Copilot Session Log Harvester

Use `copilot_session_log_harvester.py` to parse VS Code GitHub Copilot debug-log sessions and turn them into compact summaries that are useful for TP-AgentKit repo maintenance.

This skill is for harvesting past session evidence into reusable maintenance signals. It is not a raw conversation replay tool.

## Purpose

- scan multiple Copilot session folders under a `debug-logs/` root
- summarize user-request previews, tool usage, file-touch patterns, and token totals
- summarize starter styles, likely intent patterns, and first-turn intake signals from the first user prompt
- audit transcript-level workflow guardrail proxies such as approval-before-TP-edit, risky-edit grill evidence, user-facing grill-question gaps on unresolved risky edits, and explicit verified versus unverified closeout wording
- identify repeated knowledge surfaces and repeated tool chains worth converting into repo knowledge or skills
- surface touched current-task TP artifacts as promotion candidates when they were used during TP edit or TP review work
- generate compact JSON and markdown outputs for current-task review

## Privacy And Scope Rules

- This harvester intentionally ignores model reasoning fields.
- It focuses on observable session data such as user messages, tool calls, edited files, and token counts.
- Emitted non-workspace paths sanitize user-home segments to avoid leaking local usernames into maintained artifacts.
- It should be used on local debug logs that already exist on disk.
- It cannot recover deleted sessions or automatically hook future sessions by itself.

## Tool Entry Point

- Parser: `.claude/skills/copilot_session_log_harvester/copilot_session_log_harvester.py`
- Maintained wrapper: `.claude/skills/copilot_session_log_harvester/refresh_repo_maintenance_outputs.py`
- Preferred runner: `python`
- Working directory: workspace root

## When To Use

Use this skill when:
- you want to review how TP-AgentKit has been used across multiple Copilot sessions
- you want evidence for which docs, rules, or skills are touched repeatedly
- you want to find repeated tool chains that suggest a missing skill or automation surface
- you want a compact maintenance artifact instead of manually reading many session logs

Do not use this skill when:
- you need a live session hook or automatic background ingestion of future sessions
- you want model chain-of-thought or internal reasoning fields
- the available input is not a Copilot `debug-logs/` session tree

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `log_root` | path | No | Path to a Copilot `debug-logs/` folder, a single session folder, or a `main.jsonl` file; if omitted, the script auto-detects the best local debug-log root for the current workspace |
| `workspace_root` | path | No | Workspace root used to normalize touched file paths; defaults to this repo root |
| `max_sessions` | integer | No | Optional cap on how many newest sessions to include |
| `preview_chars` | integer | No | Max characters for stored user-message previews |
| `json_output` | path | No | Optional path to write the JSON report |
| `markdown_output` | path | No | Optional path to write the markdown report |
| `compare_json` | path | No | Optional prior JSON report used as the baseline for trend reporting |
| `alert_profile` | path | No | Optional JSON alert profile that defines watched metrics and default alert thresholds |
| `alert_threshold_pct_points` | float | No | Percentage-point movement required before a watched trend metric is emitted as an alert |
| `alert_min_previous_sessions` | integer | No | Minimum previous `sessions_scanned` value required before trend alerts are considered reliable enough to emit |
| `closeout_output` | path | No | Optional path to write a rolling repo-maintenance closeout summary driven by the latest harvest |

## Outputs

- compact JSON report with session counts, token totals, top tools, top files, and harvest candidates
- intake-pattern summary and first-turn signal counts that help measure prompt-understanding and low-friction startup
- workflow-guardrail summary that flags likely protocol misses in past sessions using transcript proxies
- workflow-guardrail summary includes a stricter grill-me proxy that flags risky TP-edit sessions where grill evidence exists but unresolved intake anchors were not surfaced as a user-facing question before the first TP edit
- trend comparison and alerting can now watch selected workflow-guardrail rates in addition to starter styles and first-turn signals
- recent-window workflow-guardrail summaries for the latest `10` and `20` sessions when the rolling sample is larger, so live discipline and historical burden stay distinct
- optional before-vs-previous trend summary when a prior JSON baseline is available
- threshold-based trend alerts for meaningful movement in watched startup metrics
- artifact-promotion candidate list for `.claude/artifacts/current_task/` notes touched during TP work, so reusable TP lessons are not suppressed just because they still live in task artifacts
- markdown report suitable for `.claude/artifacts/current_task/`
- optional rolling closeout summary that points maintainers to the next knowledge-promotion, automation-review, and protocol-watch actions

## Standard Commands

### Refresh rolling repo-maintenance outputs through the maintained wrapper

```powershell
python .claude/skills/copilot_session_log_harvester/refresh_repo_maintenance_outputs.py
```

### Refresh only the rolling markdown and JSON harvest outputs

```powershell
python .claude/skills/copilot_session_log_harvester/refresh_repo_maintenance_outputs.py --harvest-only
```

### Auto-detect current workspace debug logs

```powershell
python .claude/skills/copilot_session_log_harvester/copilot_session_log_harvester.py --report-json
```

### Compact JSON to stdout

```powershell
python .claude/skills/copilot_session_log_harvester/copilot_session_log_harvester.py "C:\Users\<user>\AppData\Roaming\Code - Insiders\User\workspaceStorage\<workspace-id>\GitHub.copilot-chat\debug-logs" --report-json
```

### Harvest from one session path and scan sibling sessions

```powershell
python .claude/skills/copilot_session_log_harvester/copilot_session_log_harvester.py "C:\Users\<user>\AppData\Roaming\Code - Insiders\User\workspaceStorage\<workspace-id>\GitHub.copilot-chat\debug-logs\<session-id>" --report-json
```

### Write markdown and JSON artifacts

```powershell
python .claude/skills/copilot_session_log_harvester/copilot_session_log_harvester.py "C:\Users\<user>\AppData\Roaming\Code - Insiders\User\workspaceStorage\<workspace-id>\GitHub.copilot-chat\debug-logs" --markdown-output .claude/artifacts/current_task/tp-agentkit-copilot-session-harvest-20260414.md --json-output .claude/artifacts/current_task/tp-agentkit-copilot-session-harvest-20260414.json
```

### Refresh rolling repo-maintenance closeout outputs

```powershell
python .claude/skills/copilot_session_log_harvester/copilot_session_log_harvester.py --markdown-output .claude/artifacts/current_task/tp-agentkit-copilot-session-harvest-latest.md --json-output .claude/artifacts/current_task/tp-agentkit-copilot-session-harvest-latest.json --closeout-output .claude/artifacts/current_task/tp-agentkit-repo-maintenance-closeout-latest.md
```

When `--json-output` already exists, that previous JSON file is reused automatically as the baseline for trend reporting before it is overwritten.

Default alert tuning lives in `.claude/skills/copilot_session_log_harvester/alert_profile.json`. Use `--alert-profile` when you want a different watched-metric set or different default thresholds without editing the shipped profile.

## Returned JSON Shape

The tool returns a JSON object with these main sections:

- `status`
- `log_root`
- `workspace_root`
- `sessions_scanned`
- `totals`
- `top_models`
- `top_tools`
- `intake_patterns`
- `first_turn_signals`
- `workflow_guardrails`
- `workflow_guardrails.recent_windows` when the report includes more than the default recent-window sizes
- `trend_vs_previous`
- `trend_alerts`
- `top_tool_bigrams`
- `top_read_files`
- `top_edited_files`
- `top_user_requests`
- `knowledge_candidates`
- `artifact_promotion_candidates`
- `automation_candidates`
- `sessions`

## Agent Guidance

- Use this as a maintenance harvester, not as a conversation browser.
- Treat `knowledge_candidates` as promotion candidates into `.claude/knowledge/` or workflow docs.
- Treat `artifact_promotion_candidates` as current-task artifact notes that should be reviewed for reusable TP lessons, then promoted into durable knowledge, rules, or skills.
- Treat `automation_candidates` as possible future skill surfaces.
- Treat `first_turn_signals` as heuristics for prompt-start efficiency, not as proof that no follow-up was required.
- Treat `workflow_guardrails` as transcript proxies that surface sessions worth review, not as perfect proof that the protocol was or was not followed.
- Treat the user-facing grill-question gap as a narrow proxy: it only fires when risky TP-edit context, grill evidence, unresolved first-prompt anchors, and lack of user-facing questioning all appear together before the first TP edit.
- Treat workflow-guardrail trend alerts as review aids for movement in observed protocol rates, not as automatic judgments of a single session.
- Treat `trend_vs_previous` as a rolling baseline comparison, not as a statistically complete long-term trend model.
- Treat `trend_alerts` as review aids for notable movement, not as automatic policy decisions.
- Prefer the maintained wrapper when refreshing the rolling `latest` artifacts so output paths stay centralized in one place.
- Keep watched metrics and default thresholds in the alert profile when the desired behavior is persistent, and use CLI overrides only for one-off sensitivity changes.
- Prefer the no-argument form first; pass `log_root` explicitly only when auto-detection is ambiguous or the logs live outside the normal local VS Code workspaceStorage tree.
- Use `closeout_output` when you want a stable helper note for repo-maintenance closeout without creating another dated artifact.
- If the user wants ongoing harvesting of future sessions, explain that this script can be rerun, but it does not install an automatic hook by itself.