---
name: user_intake_router
description: Predict likely mode, intent, and minimal follow-up questions from sparse TP-AgentKit user prompts, including SPL, SPAT, and Yield Explorer limit requests.
metadata:
  status: beta
  language: python
  source: local
---

# User Intake Router

Use `user_intake_router.py` to classify a short or sparse TP-AgentKit prompt into a likely mode, likely intent, detected source and input paths, and the smallest useful follow-up questions.

This skill is a lightweight prompt-intake aid. It does not replace TP safety rules or approval gates.

## Purpose

- turn keyword-led first prompts into a normalized task shape
- infer likely mode and likely intent from short user wording
- recognize SPL, SPAT, PAT, and Yield Explorer starters early enough to ask about approval state and implementation scope
- surface a short privacy-handling question when the first prompt does not already say whether usernames, person names, IP addresses, emails, or similar identifiers should be excluded or redacted
- identify which anchors are still missing before safe execution
- support repo-maintenance work on prompt understanding and first-turn UX

## When To Use

Use this skill when:
- a first user prompt is sparse or keyword-led
- you want to predict the likely task class before asking follow-up questions
- you want a compact machine-readable intake summary for maintenance or benchmarking

Do not use this skill when:
- TP edit safety already requires the full revision and approval workflow
- the user already supplied a complete structured intake
- you need live access to Copilot reasoning or assistant text

## Tool Entry Point

- Script: `.claude/skills/user_intake_router/user_intake_router.py`
- Preferred runner: `python`
- Working directory: workspace root

## Standard Commands

### Analyze one sparse prompt

```powershell
python .claude/skills/user_intake_router/user_intake_router.py --prompt "limits csv testprogram/UR7E_0114 references/<limits-file>.csv"
```

### Machine-readable compact JSON

```powershell
python .claude/skills/user_intake_router/user_intake_router.py --prompt "review diff testprogram/UR7E_0113 testprogram/UR7E_0114" --report-json
```

### Prompt from a file

```powershell
python .claude/skills/user_intake_router/user_intake_router.py --prompt-file <path-to-prompt.txt> --report-json
```

## Returned JSON Shape

The compact JSON report includes these main sections:

- `status`
- `starter_style`
- `likely_mode`
- `intent_name`
- `confidence`
- `matched_keywords`
- `detected_paths`
- `privacy`
- `signals`
- `missing_anchors`
- `recommended_follow_up`
- `normalized_starter`

## Limits

- this is a heuristic router, not a guaranteed intent classifier
- it helps reduce follow-up questions, but TP edit safety rules still override convenience
- it predicts likely intent from the first user prompt only; it does not read the whole conversation history

## Agent Guidance

- if `privacy.prompt_before_use` is true, ask the short privacy question before broader discovery or maintained artifact writing
- do not treat the privacy prompt as a replacement for task-anchor questions; ask it once, then continue with the remaining missing anchors
- use the output to ask only the missing anchors that matter
- prefer this for low-context first turns and maintenance analysis, not for replacing normal planning
- treat `recommended_follow_up` as the minimal next questions, not as a mandatory long checklist