---
name: show-work
description: Present TP decisions, changes, verification, rollback, and remaining risk in a concise engineer-readable trail. Use for plans, reviews, handoffs, completion reports, or complex tasks whose reasoning must be recoverable later.
---

# Show the work

Lead with the decision or outcome. Write for an engineer deciding what to approve, inspect, run, or release.

## Default report

```markdown
Outcome: <one sentence>

Changed:
- <file or behavior and why>

Evidence:
- <check -> result>

Remaining:
- <gap, risk, owner, or none>

Rollback / next action: <one concrete step>
```

Use exact paths, identifiers, counts, units, variants, and commands only when they help verification. Link to retained files instead of repeating their contents. Explain abbreviations on first use when the reader may not share them.

## Decision trail

For a task with several consequential branches, keep a compact table under `.tp/work/`:

```text
time<TAB>decision<TAB>evidence<TAB>alternative rejected<TAB>effect
```

Record decisions, not narration. Omit routine tool calls, copied output, and speculation. Keep safety warnings, approval boundaries, scale/unit risk, and validation gaps in full clarity even when the rest is compressed.

## Complete when

The first screen tells the engineer the outcome, strongest evidence, remaining risk, and next action; a later agent can recover consequential decisions without replaying the whole session.
