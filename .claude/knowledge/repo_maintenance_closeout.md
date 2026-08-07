---
type: methodology
status: partial
verifier: repo-maintenance workflow integration validated against the local closeout task
date: 2026-04-27
source: ".claude/tasks.json; .claude/artifacts/current_task/tp-agentkit-repo-maintenance-closeout-latest.md; .claude/artifacts/current_task/tp-agentkit-harvest-promotion-privacy-audit-20260421.md; .claude/artifacts/current_task/tp-agentkit-toolkit-harvest-and-closeout-audit-20260427.md; .claude/artifacts/current_task/tp-agentkit-artifact-promotion-audit-20260427.md; .claude/artifacts/INDEX.md; .claude/artifacts/current_task/INDEX.md"
source_note: "The earlier dated closeout-flow note from 2026-04-14 is not retained under the current workspace path set."
---

# Repo Maintenance Closeout

Use this note when the work is on TP-AgentKit itself rather than on `testprogram/` payloads.

## Goal

Close out repo-maintenance sessions with one repeatable refresh path that preserves session-learning signals, surfaces reusable TP-support artifact lessons for promotion, and avoids touching TP folders.

## Standard Refresh Step

Run the `Repo Maintenance Closeout Refresh` command listed in `.claude/tasks.json`.

That task is the maintained wrapper for:

- `.claude/skills/copilot_session_log_harvester/refresh_repo_maintenance_outputs.py`

Use the wrapper directly when you need to pass options such as `--max-sessions`, `--log-root`, or `--harvest-only` without editing the task preset.

Expected outputs:

- `.claude/artifacts/current_task/tp-agentkit-copilot-session-harvest-latest.md`
- `.claude/artifacts/current_task/tp-agentkit-copilot-session-harvest-latest.json`
- `.claude/artifacts/current_task/tp-agentkit-repo-maintenance-closeout-latest.md`

These are rolling helper files. They are not the archival record for a major delivery.

The same wrapper also supports a harvest-only path for refreshing just the rolling markdown and JSON outputs while skipping the closeout helper note.

## What To Review After The Refresh

1. `trend_alerts` first for threshold-crossing movement in watched startup metrics
2. `trend_vs_previous` and the rolling trend sections for broader movement in starter style and first-turn startup signals
3. `knowledge_candidates` in the latest JSON for durable knowledge promotion
4. `artifact_promotion_candidates` for touched `.claude/artifacts/current_task/` TP notes that may deserve promotion into knowledge, rules, or skills
	- use `artifact_family_promotion.md` when one retained family needs an explicit canonical review-surface and promotion decision
5. `automation_candidates` for new tasks, wrappers, or skill opportunities
6. `current_task/INDEX.md` if the session created or renamed active dated artifacts
7. the artifact indexes when helper outputs, retained support files, or archive moves are part of the closeout:
	- `.claude/artifacts/INDEX.md` for artifact-root helper and preferred machine-readable outputs
	- `.claude/artifacts/current_task/INDEX.md` for active notes and rolling outputs
	- `.claude/artifacts/archive/INDEX.md` for completed historical notes and grouped archive sets
8. whether any completed current-task notes should be archived in a separate explicit closeout pass


## What This Refresh Does Not Do

- it does not archive or delete artifacts automatically
- it does not modify `testprogram/`
- it does not decide which findings are durable policy versus one-task noise
- it does not create a dated closeout note unless a maintainer decides the session needs one

## Alert Tuning

Default trend-alert tuning lives in `.claude/skills/copilot_session_log_harvester/alert_profile.json`.

Use that profile when you want to persistently change:

- which startup metrics are watched
- the default percentage-point threshold
- the minimum previous-session floor required before alerts emit

Use CLI overrides only for one-off sensitivity changes during an exploratory run.

## Promotion Rule

Promote findings that are reusable and either cross-session or repeatedly reinforced by touched TP-support artifacts.

Keep task-local observations in artifacts when they are still:

- tied to one delivery or commit package
- specific to one TP or one customer incident
- too provisional to become framework guidance

For TP-change work:

- keep raw `testprogram/` and `references/` files out of durable knowledge candidates
- review touched `.claude/artifacts/current_task/` TP notes as promotion inputs instead of blanket-excluding them
- promote the reusable lesson from the artifact, not the raw TP payload itself

When promotion candidates include non-workspace file paths or environment-specific evidence:

- sanitize maintainer-authored non-workspace paths to `<user>` form before promoting or refreshing rolling outputs
- prioritize tracked and maintainer-authored surfaces first; untracked local artifacts still matter for local privacy, but they do not carry the same repo-sharing risk

When closeout includes generated analysis bundles under `.claude/artifacts/current_task/`:

- choose one canonical retained human-review surface per analysis family when a richer self-contained report already exists
- keep the machine-readable inputs or outputs that the retained report still depends on
- treat thin wrapper HTML, dashboard PNG layers, and one-off generator scripts as derivative convenience outputs once every caller is rewired to the canonical report
- keep multiple retained surfaces only when they answer different questions, for example real `.ls` release interpretation, later-population GOODPOP screening, and mismatch isolation
- record the retained entry point in the dated closeout note and refresh the artifact indexes when the expected review surface changes

## When To Write A Dated Closeout Artifact

Write a dated artifact in `current_task/` when the session materially changes TP-AgentKit behavior, workflow, validation, or packaging expectations.

Do not create a new dated closeout note for every routine refresh run.