---
type: methodology
status: verified
verifier: aligned with README.md and recent session-harvest workflow tuning
date: 2026-04-14
source: "README.md; .claude/skills/user_intake_router/SKILL.md"
source_note: "The earlier principles-check task note from 2026-04-14 is not retained under a stable current_task path."
---

# User Intake Keyword Map

Use this file when the first user message is sparse, keyword-led, or only partially structured.

Goal: infer the likely task shape quickly, then ask only for the missing anchors that materially affect safe execution.

Prefer `.claude/skills/user_intake_router/user_intake_router.py` when you want executable routing from a real first-turn prompt. Keep this file as the maintained reasoning reference behind that routing behavior.

## Default Handling Rule

- prefer the smallest useful intake, not the full intake checklist, when the user intent is already mostly clear
- infer the likely mode from the user verb and artifact type first
- if the first prompt does not already say how to handle privacy, ask one short question about excluding or redacting private identifiers before broader discovery or artifact writing
- ask for source TP, target handling, or input file only when those details are still required for the next safe step
- do not turn a short workable request into a long checklist unless the task is genuinely ambiguous

## Privacy Handling Rule

- ask once, early, and keep it short
- preferred question: `Before I use TP-AgentKit on this, should I exclude or redact any private identifiers such as usernames, person names, IP addresses, emails, or hostnames?`
- treat an explicit field such as `Privacy handling: none` or `Privacy handling: exclude usernames and IP addresses` as sufficient
- do not keep repeating the question after the user answers it

## Quick Intent Map

| User words or pattern | Likely mode | Likely intent | Ask next only if missing |
|------|------|------|------|
| `limits`, `csv`, `lsl`, `usl`, `update limits` | `edit` | limit update from a source file | source TP, source-of-truth CSV, copied revision vs in-place |
| `spl`, `spat`, `pat`, `yield explorer`, `ye export` | `edit` or `review-only` | SPL or SPAT limit review or implementation | source TP, approved vs proposed status, source artifact, copied revision vs in-place |
| `relative`, `esm`, `subplan` with `add`, `update`, `fix` | `edit` | relative-test work | source TP, input notes or CSV, copied revision vs in-place |
| `relative`, `esm`, `subplan` with `check`, `review`, `explain` | `analysis-only` or `review-only` | trace or audit relative flow wiring | source TP, exact concern if unclear |
| `review diff`, `compare`, `delta`, `mismatch` | `review-only` | compare revisions or cross-check compare output | both source folders and diff HTML if available |
| `release`, `safe to release`, `release check`, `audit` | `review-only` | release-readiness audit | source TP, expected release target if relevant |
| `stdf`, `softbin`, `site skew`, `summary`, `result` | `analysis-only` | tester-result analysis | result file path, desired summary depth if important |
| `log`, `error`, `systemcontroller`, `failure` | `analysis-only` | log triage and root-cause guidance | log file path |
| `special tp`, `screen`, `urgent lot`, `overlay` | `edit` | special-TP preparation | source TP, driving request or issue note, copied revision target |
| `convert`, `migration`, `cfg to ini`, `clone job` | `edit` or `analysis-only` | framework conversion or cloning task | source artifact and desired output token or platform |

## Follow-Up Discipline

- if the first prompt does not state privacy handling, ask the short privacy question before wider repo exploration or maintained artifact writing
- when the user already supplied mode, do not re-ask it
- when the user already supplied a usable source path, do not ask for the full revision story up front unless edit safety requires it
- when the request is analysis-only or review-only, avoid edit-specific questions unless the user changes mode
- when the user intent clearly matches a known starter pattern, respond from that pattern instead of broad repo exploration

## Good Short Starts

- `limits csv testprogram/UR7E_0114 references/<limits-file>.csv`
- `implement SPL testprogram/UAE7FC016CA01_0012 references/<approved-spl-file>.csv`
- `review diff testprogram/UR7E_0113 testprogram/UR7E_0114`
- `analyze stdf references/stdf/<file>.csv`
- `check log references/log/<file>`
- `add relative tests testprogram/UR8K_2700`
- `special tp screen testprogram/<program_revision>`

## Limits

- this map improves first-turn prediction, but the file itself is guidance rather than an executable classifier
- TP edit safety rules still override convenience: revision handling, approval, and structure validation remain mandatory