---
name: verification-before-completion
description: Use before claiming a TP task is complete, fixed, validated, safe, or ready; require fresh evidence for each positive claim and state any remaining validation gap directly.
metadata:
  status: beta
  language: markdown
---

# Verification Before Completion

Behavior-only skill. No executable script.

Use this skill before any message that implies success for TP work: complete, fixed, validated, clean, structure-preserving, safe to release, or ready for handoff.

## Purpose

- block unsupported completion or release claims
- separate verified facts from assumptions, pending checks, or tool reports
- force explicit disclosure when simulator, parser, launch, or lot evidence is missing
- keep TP handoffs honest when schedule pressure encourages soft wording

## Use When

- about to say a TP edit is complete, fixed, validated, or release-ready
- summarizing `edit`, `review-only`, or `analysis-only` conclusions with confidence language
- reduced-validation or no-simulator situations still need a clear status statement
- a helper script, compare tool, or subagent reported success and you need to verify independently
- writing a release-readiness note, walkthrough conclusion, or review closeout

## Do Not Use When

- still gathering intake anchors or drafting the plan
- still waiting for user approval before TP edits
- the next correct step is to gather more evidence rather than report status
- the user asked for open-ended brainstorming rather than a status judgment

## Core Rule

No positive completion claim without fresh task-specific evidence.

If the strongest available evidence is still partial, say exactly what remains unverified and how that reduces release confidence.

## Apply Per Claim

1. name the exact claim
2. name the exact evidence that would prove it
3. inspect that evidence fresh
4. report the result in TP terms
5. if any gap remains, state it immediately after the claim

## TP Evidence Map

- `limits updated correctly` -> compare touched values against the chosen source of truth and the correct same-variant baseline
- `structure preserved` -> confirm no unintended add, delete, reorder, tuple shift, or occurrence-count drift on touched test IDs
- `file integrity preserved` -> inspect surrounding unchanged rows and the footer or tail; run parser or tool validation when available
- `revision ready` -> confirm the correct target revision was edited, `JOB_REV` matches it where applicable, and required history or notes were updated
- `review clean` -> confirm the compare or diff was reviewed against the requested scope and no unresolved high-severity findings remain
- `safe to release` -> list the strongest available evidence explicitly; if simulator, launch, or lot validation is missing, mark release confidence as conditional
- `script succeeded` -> inspect changed files and produced outputs, not only exit code or generated summary text

## Partial-Validation Rule

Do not collapse `not disproven` into `verified`.

When simulator, parser, launch, or lot evidence is missing, state:

- what was verified
- what was not verified
- the most likely remaining failure mode
- whether explicit user acceptance is still required before release or closeout

## Red Flags

- `should be fine`
- `looks good`
- `validated` without naming the checks
- trusting a script or subagent report without opening the changed artifact
- calling a task done because one sampled row looks correct
- treating missing simulator or parser access as irrelevant

## Reporting Pattern

- `verified: <claim>. evidence: <checks actually performed>.`
- `unverified: <gap>. impact: <what confidence is still missing>.`
- `next check: <most useful remaining validation>.`

## TP-AgentKit Fit

- use after the `grill-me` pass and after execution-time validation
- do not let this skill replace required approval gates or revision-copy rules
- if evidence is weak, report the weak status clearly instead of trying to sound complete