---
name: ubiquitous-language
description: Use when TP-AgentKit conversation, docs, knowledge, or review notes use inconsistent TP terms and you need a canonical glossary or ambiguity map written into local knowledge or artifacts.
metadata:
  status: beta
  language: markdown
---

# Ubiquitous Language

Behavior-only skill. No executable script.

Use this skill to standardize TP-AgentKit domain wording before ambiguity leaks into prompts, reviews, skills, or knowledge notes.

## Purpose

- reduce terminology drift across TP work, maintainer notes, and reusable knowledge
- separate real domain terms from temporary wording or code-level names
- make follow-up prompts, reviews, and skill docs use the same language consistently
- capture ambiguity explicitly instead of letting synonyms spread silently

## Use When

- the same concept is described with different words across docs or conversations
- one word is overloaded across TP flow, revision handling, or release discussion
- a new skill, workflow note, or intake pattern needs stable domain terms
- a maintainer wants a reusable glossary for future threads or harvested knowledge

## Do Not Use When

- the issue is only code naming with no domain-language impact
- there are not enough repeated terms yet to justify a glossary pass
- the output would stay one-task-only and never be reused

## Workflow

### 1. Gather domain terms from real sources

Scan the current conversation and the inspected local surfaces that matter, such as:

- current-task artifacts
- knowledge files
- workflow notes
- skill docs
- user prompt starters

Focus on nouns, verbs, and relationship words that matter to TP work.

### 2. Identify language problems

Look for:

- synonyms for the same concept
- overloaded words used for different concepts
- vague shortcuts that hide important distinctions
- code or tool names being used where domain language would be clearer

### 3. Propose canonical terms

Be opinionated.
For each concept, choose one preferred term, define it tightly, and list aliases to avoid.

### 4. Choose the correct output home

Do not write a root-level `UBIQUITOUS_LANGUAGE.md` in this repo.

Preferred targets:

- durable, cross-task terminology: update or add a file under `.claude/knowledge/`
- task-local terminology work: write a dated note under `.claude/artifacts/current_task/`

If the glossary later proves durable, promote it from the artifact into knowledge.

### 5. Include the right structure

When the glossary is worth writing, include:

- grouped term tables when natural clusters exist
- aliases to avoid
- flagged ambiguities with clear recommendations
- key relationships between terms when they matter to TP reasoning
- a short example dialogue only if it helps clarify important boundaries

### 6. Re-run carefully

If invoked again, update the existing glossary or note rather than creating parallel competing files.

## TP-AgentKit Heuristics

- prefer domain terms over class, script, or file names unless those names carry real domain meaning
- keep definitions short and specific
- route durable wording into knowledge, not only into a task artifact
- use the result to sharpen `README.md`, knowledge notes, intake patterns, and skill wording when appropriate

## Anti-Patterns

- treating a root-level generic glossary as the source of truth
- including generic programming vocabulary with no TP meaning
- keeping two competing names for one concept because both feel familiar
- letting task-local shorthand become durable repo vocabulary without review

## Output Pattern

1. term groups
2. canonical term tables
3. relationships
4. flagged ambiguities
5. recommended next doc or skill surfaces to update