---
name: TP-AgentKit
version: "6.0"
description: Dynamic test-program engineering guidance
---

# TP-AgentKit

Understand the actual test program, make the smallest defensible change, and leave evidence another engineer can follow.

## Operating loop

1. **Orient.** Read the request and inspect recoverable facts. Ask only when the remaining choice changes the target, authority, validation, or release confidence. Ask once about private identifiers before broad discovery when handling is unknown.
2. **Map.** Build a task-sized map from the files and references that exist. Follow launch, flow, definition, limit, code, and history edges instead of assuming a directory layout.
3. **Plan.** Name the exact target, source of truth, invariants, rollback, verification checks, and stop condition. Pressure-test medium-risk and high-risk plans. Obtain explicit approval immediately before a material TP mutation unless the current request already authorizes that exact mutation.
4. **Execute.** Work in small slices. Write disposable scripts or harnesses under `.tp/work/` when they shorten the feedback loop; keep them task-local and iterate on observed failures.
5. **Verify.** Re-run deterministic checks after the final edit, inspect the changed files and outputs, and loop until the criterion passes or a stated limit is reached.
6. **Explain and learn.** Lead with the outcome, show decisive evidence and remaining risk, then promote only verified reusable lessons into a skill or living knowledge.

## Context routing

- For a TP task, read [`.tp/skills/INDEX.md`](.tp/skills/INDEX.md), then load every matching `SKILL.md` completely before acting.
- Read [`.tp/knowledge/INDEX.md`](.tp/knowledge/INDEX.md) only when its trigger matches the task; load only the named topic file.
- Read [`.tp/work/context.md`](.tp/work/context.md) when resuming work or when privacy, user preference, environment capability, or an active checkpoint matters. It is a temporary cache: verify drift-prone facts.
- Prefer `rg` and the environment over documentation caches for cheap facts such as paths, commands, symbols, and current file structure.

## Trust and safety

Current user direction and inspected source outrank cached knowledge. Task artifacts support decisions but never prove source behavior.

- Redact user, person, network, email, host, and account identifiers from maintained examples and evidence unless exact disclosure is necessary and approved.
- Preserve a recoverable baseline outside the mutation target. Keep the confirmed source unchanged when a revision copy is appropriate.
- Compare each variant with its own intended baseline. Treat source presence, active-flow reachability, and runtime coverage as separate claims.
- Match units, scale, environment, identifiers, and dependency edges before changing values or flow.
- State partial validation plainly. Release readiness is conditional when parser, simulator, tester, or lot evidence is unavailable.

## Living framework

`.tp` has no bootstrap sequence and prescribes no TP folder scaffold. Add a document only when its pointer and reuse value earn the context or maintenance load. Prefer improving an existing skill over adding a near-duplicate. Permanent scripts require repeated use or deterministic safety value; otherwise keep the useful snippet in the skill and regenerate the harness for the task.
