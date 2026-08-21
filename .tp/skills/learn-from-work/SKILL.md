---
name: learn-from-work
description: Promote verified lessons from completed TP work into a focused skill, living knowledge, or temporary context update. Use after a task reveals a reusable method, invariant, failure mode, user preference, or environment constraint that should improve later work.
---

# Learn from completed work

Promote the lesson, not the transcript or raw customer evidence.

## Promotion test

A candidate earns durable space when it is non-obvious, evidence-backed, likely to change a future decision, and scoped tightly enough to avoid misrouting unrelated work.

Classify it:

- **Skill:** reusable procedure, decision loop, verification method, or adaptable snippet.
- **Knowledge:** stable domain fact, relationship, invariant, schema meaning, or bounded failure pattern.
- **Temporary context:** current user preference, environment capability, constraint, active goal, checkpoint, or provisional observation.
- **Discard:** task narration, cheap-to-rediscover lookup, unsupported guess, private raw evidence, or one-off detail with no future decision value.

## Learn

1. Finish verification first and cite the evidence shape that supports the candidate.
2. Search existing `.tp/skills/` and `.tp/knowledge/` for the owning concept.
3. Improve that source of truth with the smallest patch. Create a new skill only when it has a distinct automatic trigger; create a new knowledge topic only when an existing topic cannot hold it coherently.
4. Update the relevant index pointer in the same patch. Keep trigger wording discriminating and body guidance positive, scoped, and completion-bound.
5. Redact private identifiers and turn device-specific examples into bounded examples rather than universal rules.
6. Re-read the changed document as a future agent and test at least one matching and one non-matching scenario. Broad policy, authorization, or safety changes require user approval.

Useful snippets belong in the skill when adaptation is expected. Promote executable code only after repeated use or deterministic safety value proves that regeneration is more expensive or less reliable.

## Close the task

Remove completed goal detail and disposable outputs from `.tp/work/` when they no longer support rollback, audit, or resumption. Keep the context cache short and mark drift-prone facts with an observation date.

## Complete when

Every promoted lesson has one authoritative home, a reliable pointer, bounded evidence and scope, no private identifiers, and a demonstrated reason to affect future behavior. If no candidate passes, record nothing durable.
