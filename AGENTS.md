---
name: TP-AgentKit
version: "6.0"
description: "Context-first test program engineering guidance"
---

# TP-AgentKit Maintainer Guide

This file contains the technical repository contract. Read `.tp/directive.md`
before working in the repository. The root [README.md](README.md) is the only
user-facing onboarding document.

## Control surface

- `.tp/directive.md` is the only always-on operating contract.
- `.tp/context.schema.json` defines the optional machine-readable context shape.
- `.tp/capabilities.json` provides runtime selection hints, not fixed workflows.
- `.tp/knowledge.md` contains compact reusable TP safety knowledge.
- `.tp/state/` and `.tp/session/` are optional generated runtime locations and are
	ignored by Git.

`.tp` is intentionally non-standard and local to this repository. Do not add a
compatibility directory, fixed payload layout, task preset, or script runner.

## Operating model

Before substantive work begins, the agent confirms the intake with the user. The
confirmation covers the intended outcome, scope, available supporting documents,
privacy constraints, missing-evidence risks, and the first validation boundary.
The user may insist on proceeding without supporting documents; that decision is
recorded as an evidence gap and does not block the task.

After confirmation, the agent treats the workspace as unknown until it has
inspected the real files, entry points, variants, dependencies, and
source-of-truth inputs. It then builds a runtime task graph around the current
evidence:

1. Inspect the workspace and request.
2. Ask only decision-relevant questions.
3. Decide the smallest capability set and execution path.
4. State the target, source of truth, scope, and approval boundary before edits.
5. Act, validate at the narrowest useful boundary, and repeat when needed.
6. Finish with evidence, changed paths, validation gaps, risks, and the next
	 action.

Capabilities are selected and composed at runtime. Do not turn a one-off program
difference into a repository script or a universal workflow template.

## Intake and artifact handling

Suggest supporting material according to the task rather than requesting a full
document package. Relevant examples are:

- an older TP or release baseline for comparison
- product or test specifications and official reference documentation
- instructions received by email or other approved internal channels
- schematics, datasheets, configuration notes, and flow documentation
- CSV or workbook exports, tester logs, and known-good result sets

The agent should open and inspect artifacts in their existing formats when local
support exists. When a format is unsupported, it should use an existing local
tool or write a focused reader or script so the user is not asked to perform a
manual conversion. Any generated intermediate or output artifact must be
identified, kept separate from the source, and validated at the appropriate
boundary.

Tool installation requires the user's consent. Before proposing it, inspect the
available environment and approved alternatives. Follow corporate proxy,
firewall, package-source, administrator, licensing, and data-privacy rules; do
not bypass controls or send artifacts to external services without explicit
authorization.

## Context contract

Persist context only when it benefits the current task or a later handoff. Save
stable, evidence-backed facts and task deltas rather than empty plans, indexes,
walkthroughs, copied transcripts, or large tool output. A useful checkpoint can
recover the intent, facts, decisions, changed paths, outputs, validation,
open risks, and next action. Never persist secrets or private identifiers unless
the user explicitly requires it.

## Safety invariants

- For edits, obtain approval after the target and plan are understood. Repository
	maintenance may use the user's explicit approval of the maintenance scope.
- Prefer a copied revision when the source is a baseline or release artifact,
	unless the user explicitly chooses in-place work.
- Follow dependency order discovered in the program. Never invent tests, imports,
	limits, bins, or flow references.
- For limit changes, verify scale, unit, tuple meaning, structure preservation,
	occurrence counts, neighboring rows, and the file tail.
- Compare each variant with its own baseline; names alone do not prove
	equivalence.
- Report unverified parser, simulator, launch, or production evidence directly.

## Documentation boundary

Keep common-user onboarding, capabilities, use cases, and task-start guidance in
the root [README.md](README.md). Keep implementation mechanics, `.tp` contract
details, safety invariants, and maintainer constraints here. Do not create a
second README inside `.tp`.
