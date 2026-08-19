# TP-AgentKit Working Knowledge

This file keeps only reusable facts. Task-specific observations belong in the context saved for that task.

## Source and discovery

- Treat the workspace layout as unknown. Find actual files, entry points, imports, variants, and source-of-truth inputs before naming a workflow.
- Follow the program's own dependency direction. Definitions must exist before flow references them; flow must be understood before implementation code is changed.
- A filename, export label, or environment token is a clue, not proof. Confirm variant and environment from file content and active flow.
- Compare a changed variant with its own baseline. Similar names do not guarantee equal coverage or limits.

## Edit safety

- For edit work, identify the target and obtain approval before mutation. Prefer a copied revision when the source is a release or baseline.
- Preserve structure for narrow changes. A limit-only request should not add, remove, reorder, or duplicate rows.
- Before changing a numeric limit, confirm tuple meaning, scale token, engineering unit, and source unit.
- After a narrow change, inspect neighboring rows, touched-ID occurrence counts, and the file tail or footer.
- Do not claim completion from a tool exit code alone. Inspect outputs and state what parser, simulator, launch, or production evidence is still missing.

## Context memory

- Stable facts: verified workspace conventions, confirmed terminology, recurring variant mappings, and durable safety decisions.
- Task facts: current source, target, inputs, scope, active flow, decisions, changed paths, evidence, risks, and next action.
- Save facts with evidence references and confidence. Prefer a small delta or content hash over copied source or transcript text.
- Treat user answers as decisions, observed files as facts, and agent inferences as provisional until confirmed.
- A resume point must be actionable: name the next check or decision, not merely the last message.

## Dynamic workflows

- Build a task graph from observed work. Use deterministic checks for structure and evidence; use model reasoning where the path is genuinely variable.
- Fan out independent discovery or review only when the task size or risk justifies it, then reconcile results before mutation.
- Allow cycles for missing information, failed validation, retries, and user approval. Do not force every task into a linear template.
- Add a reusable capability only after a pattern repeats and its boundary is clear. Do not add a script to encode a one-off program difference.
