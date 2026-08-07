---
type: methodology
status: verified
verifier: artifact promotion passes on 2026-04-24 and 2026-04-27
date: 2026-04-27
source: ".claude/artifacts/current_task/tp-agentkit-artifact-harvest-promotion-20260424.md; .claude/artifacts/current_task/tp-agentkit-artifact-promotion-audit-20260427.md; .claude/artifacts/current_task/tp-agentkit-artifact-to-knowledge-skill-diagnosis-20260427.md; .claude/artifacts/current_task/tp-agentkit-artifact-promotion-template-20260427.md"
---

# Artifact Family Promotion

Use this note when converting one `.claude/artifacts/` family into durable knowledge, existing-skill reinforcement, or a new-skill decision.

## Core Rule

- treat each artifact family as one answered question, not as one folder dump
- keep one canonical human-review surface per question when a richer self-contained report already exists
- keep only the machine-readable outputs that the retained review surface or later automation still depends on
- treat wrapper dashboards, duplicate summaries, and one-off generators as derivative unless they define the real reusable operating boundary

## Family Review Method

For each family, answer these in order:

1. what exact question does this family answer
2. which file is the canonical retained human-review surface
3. which structured outputs still matter after that retained surface exists
4. which files are only wrapper, convenience, or reproducibility layers
5. what reusable lesson survives after filenames, dates, and release context are removed

If the family answers more than one question, keep separate retained surfaces only when those questions are materially different.

Verified repo example:

- real `.ls` release interpretation, later-population GOODPOP screening, and CSV-vs-real-limit mismatch isolation are separate questions and can justify separate retained surfaces

## Promotion Decision

### Promote To Knowledge When

- the family leaves a stable interpretation rule, routing rule, retention rule, or validation guard
- the lesson remains true after the dated evidence is removed
- the lesson prevents a repeated future misread or workflow mistake

### Reinforce An Existing Skill When

- the family exercises a workflow that already has a maintained skill boundary
- the reusable value is better expressed as stronger examples, limits, or validation inside that skill

### Justify A New Skill When

- the family reveals repeated user intent, not just one release slice
- the workflow has stable inputs, stable outputs, and repeatable validation
- the executable boundary is schema-based or workflow-based rather than device-name-based or date-based

### Keep Evidence-Only When

- filenames, dates, or one release context are part of the meaning
- the script mainly exists to generate one report family
- the output is useful for traceability but not as a repeated operating method

## Privacy Gate

Before promotion:

- check for user-home paths, usernames, emails, or non-workspace locations
- sanitize maintainer-authored non-workspace paths before the content moves into durable knowledge or rolling outputs
- prefer promoting the extracted lesson, not the raw evidence payload

## Minimal Family Template

Use this compact structure when reviewing a family:

- family scope
- canonical retained human-review surface
- retained machine-readable support outputs
- derivative or evidence-only outputs
- knowledge candidate
- existing-skill mapping
- new-skill qualification check
- privacy and path check
- final decision

## Short Decision Test

- artifacts are raw experience
- knowledge is the durable lesson extracted from repeated experience
- a skill is the durable lesson plus a stable executable workflow