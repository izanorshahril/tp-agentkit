---
name: grill-me
description: Use when a medium-risk or high-risk TP plan, review scope, release decision, investigation path, or STDF CSV analysis needs a user-facing pressure-test or interactive schema questioning after the task anchors are known.
metadata:
  status: beta
  language: markdown
---

# Grill Me

Behavior-only skill. No executable script.

Switch into hard-questioning mode to pressure-test a TP task with the user once the basic intake anchors are known.

## Purpose

- expose weak assumptions before execution
- force branch-by-branch clarity instead of accepting shallow first answers
- surface missing validation, compare, and rollback thinking early
- reduce avoidable late rework on risky TP and release tasks

## Use When

- a plan looks plausible but not yet robust
- a review-only task needs sharper challenge instead of a soft summary
- a release or urgent limit-only change needs explicit validation pressure
- an investigation has multiple branches and the next discriminating question matters
- an STDF CSV analysis request depends on header, row, or column meaning that the workspace cannot prove safely
- the user explicitly asks to be grilled or wants a harder challenge process

## Default TP-AgentKit Triggers

Activate by default after a draft plan for medium-risk and high-risk tasks such as:

- release-facing or urgent requests
- `just limits`, `minimal`, or `safe` requests that still lack proof
- tasks with conflicting or layered source-of-truth inputs
- FT, QA, EWS, or environment-variant comparisons where the baseline is easy to get wrong
- STDF CSV analysis where column roles such as `USL`, `LSL`, `HighL`, `LowL`, `Unit`, `Tests#`, or family-specific aliases are unclear from inspected evidence
- tasks likely to ship with reduced simulator or parser validation
- requests that look narrow in wording but can still hide structure edits or variant drift

## Do Not Use When

- the task is still missing the basic intake anchors from the repo workflow
- revision handling is still unresolved for TP edit work
- the next safe step is obvious and additional interrogation would only stall progress
- the user needs a direct safety warning, approval gate, or irreversible-action explanation

## Activation Boundary

- keep normal TP-AgentKit intake discipline first
- after anchors are known, use this skill to harden the shared plan, review, or release decision
- for medium-risk and high-risk tasks, prefer this as the default second-phase pass after the draft plan
- in `analysis-only` and `review-only`, this can activate as soon as source and scope are clear
- in STDF CSV analysis, this can activate before interpretation when schema meaning is ambiguous and the next safe step is a user-facing clarification
- in `edit`, use this before plan approval, not instead of plan approval

## User-Facing Default

- the default form of this skill is explicit questioning in chat, not a silent internal self-critique
- inspect recoverable facts from the repo first, then ask the user the next discriminating question that still changes execution or release confidence
- if all risky branches are resolved from inspected evidence, say so directly and move on; do not pretend a user-facing grill pass happened when no question remains
- do not treat internal self-grilling as a complete grill pass when unresolved user-direction choices still exist
- use internal self-checking only to sharpen the next question or eliminate branches the workspace already answers

## Questioning Rules

- ask the user one question at a time unless the repo can answer it directly
- with each question, state the recommended answer or likely best direction
- make the weak assumption explicit: what is unproven and why it matters
- follow the decision tree until the weak branch is resolved; do not stop at the first acceptable answer
- if the codebase, `references/`, or task artifacts can answer the question, inspect them instead of asking the user
- favor discriminating questions that change the execution plan, validation scope, or release confidence
- challenge vague words like `minimal`, `safe`, `same as before`, `just limits`, or `should be fine`
- in STDF CSV analysis, ask before assigning meaning to an ambiguous header, row, or family-specific alias that the workspace cannot verify confidently
- for STDF CSV analysis, separate `where it is` from `what it means`; a column can be locatable from the file but still require user confirmation for semantics
- after the user confirms a recurring STDF schema meaning, preserve that lesson in durable repo knowledge instead of treating it as one-off chat context

## STDF CSV Questioning Pattern

Use this pattern when the user asks to analyze STDF-derived CSV data and the schema is not fully proven from the workspace:

1. inspect the file enough to name the exact unknown
2. ask one concrete schema question at a time
3. state why the assumption is unsafe
4. prefer questions like `Which row is the authority for USL/LSL?`, `Does this family use HighL/LowL instead of USL/LSL?`, or `Is this header metadata or a mapped test column?`
5. after the user answers, continue the analysis using the user-confirmed schema instead of re-deriving it from weak clues
6. if the answer is recurring and reusable, promote it into `.claude/knowledge/`

Example STDF prompts:

- `I can find candidate limit columns, but I cannot prove which row is authoritative for USL and LSL in this export. Recommended answer: tell me whether this family uses the \\`HighL\\` and \\`LowL\\` row, explicit \\`USL\\` and \\`LSL\\` headers, or another schema rule.`
- `I found \\`Tests#\\` and \\`Parameter\\`, but this alias block is ambiguous. Recommended answer: confirm whether these later columns are metadata fields or true mapped test columns for this family.`
- `I can locate the column, but I should not assume its meaning. Recommended answer: confirm what this header means in your STDF export before I use it in the analysis.`

## TP Pressure Points

Bias the questions toward these failure-prone areas when relevant:

- source-of-truth quality: which file actually wins if CSV, workbook, diff, and TP disagree?
- revision safety: current revision or copied target revision, and why?
- variant correctness: are FT, QA, EWS, cold, ambient, or hot variants being compared against the right baseline?
- structure integrity: what proves the change is structure-preserving and not only value-correct?
- validation depth: what exact compare, parser, simulator, or occurrence-count checks will prove the change?
- release confidence: what is the rollback path if the first test lot or simulator run disagrees?
- missing evidence: what key fact is assumed but not yet verified from the workspace?

## Failure-Mode Attack Map

- limits-only claims: ask the user what proves the delta is value-only and not a hidden add, delete, reorder, or tuple-order mistake
- release gating: ask the user what exact evidence justifies shipping if simulator, parser, or lot validation is absent or partial
- baseline drift: ask the user why the chosen compare target is the correct same-variant baseline instead of a sibling flow or earlier convenience file
- source conflicts: ask the user which artifact wins and what evidence shows the losing source is outdated, derived, or irrelevant
- revision pressure: ask the user why a copied revision is not being used and what rollback path exists if the edit is wrong
- validation gaps: ask the user which exact compare, occurrence-count, parser, simulator, or launch-path checks will catch the most likely failure mode
- STDF schema drift: ask the user which row or header family is authoritative before treating a guessed column as limits, units, test mapping, or metadata

## Stop Rules

- stop pressing on a branch once the answer is verified and no longer decision-relevant
- do not ask for data already recoverable from inspected files
- do not let aggressive questioning bypass approval, revision-copy, or protected-area rules
- when no user-facing question remains, summarize the resolved branches and switch back to direct execution mode

## Output Style

- direct, compact, and unsentimental
- user-facing when uncertainty remains; do not hide the challenge inside private reasoning
- no filler praise or softening language
- clear about why the current answer is weak, acceptable, or sufficient
- escalate intensity on risky branches; stay short on already-verified ones

## Example Openers

- `You called this limits-only. What exact compare proves there is no hidden structure edit? Recommended answer: a compare that shows only intended limit tuple changes plus occurrence-count checks on touched test IDs.`
- `Why are we choosing an in-place edit instead of a copied revision? Recommended answer: we usually should not; default to a copied revision unless the user explicitly requested otherwise.`
- `What evidence says this QA or environment variant is allowed to differ from its own baseline? Recommended answer: compare against the same variant's own baseline, not a sibling flow.`
- `If simulator validation is missing, what evidence is strong enough to release anyway? Recommended answer: only a tighter structure audit, same-variant compare, occurrence-count check, and explicit user acceptance of the remaining risk.`
- `I can locate candidate USL and LSL fields, but I should not guess which row is authoritative. Recommended answer: tell me which header or row this STDF family uses for the real limits before I analyze against the wrong columns.`