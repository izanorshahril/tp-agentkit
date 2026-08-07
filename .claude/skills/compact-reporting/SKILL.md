---
name: compact-reporting
description: "Use when writing agent-generated plans, walkthroughs, diff notes, handoff artifacts, and PR drafts with low-token, high-signal wording inside TP-AgentKit."
metadata:
  status: beta
  language: markdown
---

# Compact Reporting

Behavior-only skill. No executable script. Apply these writing rules when the task needs a concise artifact, summary, review note, or handoff record.

## Purpose

- cut token-heavy narration from agent-generated artifacts
- keep technical identifiers, file paths, revision names, test IDs, and decisions exact
- stay clear enough for semiconductor workflow review and future handoff

## Use When

- writing `.claude/artifacts/current_task/*.md` summaries
- writing plan updates, walkthrough notes, compare summaries, or release handoff notes
- drafting commit summaries or PR bodies for repo-maintenance work
- presenting review findings where one-line issue statements are enough

## Do Not Use When

- asking for approval on TP edits or revision-copy handling
- explaining destructive or irreversible actions
- warning about release risk, scale or unit mismatch, or structure-audit findings
- writing anything where short phrasing could hide scope, uncertainty, or a safety gate

## Rules

- lead with decision, finding, or action; keep setup text short
- prefer short paragraphs or flat bullets over long narrative blocks
- remove filler, pleasantries, hedging, and repeated restatement
- preserve exact file paths, commands, test IDs, lot names, softbins, revision numbers, and dates
- quantify only when the number is known from inspected evidence
- if a point needs a caveat, state the caveat directly instead of surrounding it with soft wording
- keep the artifact readable; this is compact, not cryptic

## Artifact Patterns

### Plan Summary

- task objective
- exact files or surfaces in scope
- main execution steps
- validations or audits required
- open questions only if they materially block execution

### Review Findings

Use one finding per bullet.

- `risk: <problem>. <impact>. <fix or check>.`
- `bug: <problem>. <impact>. <fix>.`
- `note: <important context>.`

### Handoff Note

- current state
- exact source of truth
- remaining risk or follow-up
- next command, file, or artifact to open first

## Auto-Clarity Override

Drop compact mode temporarily for:

- safety warnings
- approval gates
- release decisions
- multi-step procedures where order matters
- anything the reader could reasonably misinterpret if shortened further

Resume compact mode after the high-risk explanation is complete.