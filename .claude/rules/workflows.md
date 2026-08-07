# Rules & Workflows

## Scope
Applies to all ATE test program modifications within this repository.

For repo-maintenance work on `.claude/`, docs, tasks, or artifacts, use the maintainer focus-separation rule below before writing durable notes.

---

## Maintainer Focus Separation

When the work is on TP-AgentKit itself rather than on `testprogram/`, separate the maintained surfaces into two lanes before adding or updating skills, knowledge, or artifacts.

1. `TP-AgentKit`
    - TP workflow behavior, repo rules, local reusable skills, artifact policy, and framework-maintenance notes
2. `external tooling`
    - VS Code, Copilot, Python, model, GitHub, network, or workspace-tooling behavior around this repo

Rules:

- use `.claude/knowledge/focus_boundaries.md` when the lane is not obvious
- keep `.claude/skills/<name>/` flat; do not create nested focus folders under `.claude/skills/`
- keep `.claude/artifacts/current_task/` flat for rolling outputs and wrapper paths
- show the separation through registry or index grouping, subject-first artifact names, and summary text instead of by moving folders

---

## Privacy Intake Gate

On the first TP-AgentKit chat for a task, ask once whether private identifiers should be excluded or redacted before broad discovery, quoted previews, or maintained artifact writing.

Ask about categories such as usernames, person names, IP addresses, email addresses, hostnames, account handles, or other environment-specific identifiers.

Rules:

- ask before broad repo exploration, diff previews, or artifact generation unless the user already supplied privacy handling
- if the user says there are no special exclusions, proceed and do not keep re-asking
- if the user names categories to exclude, honor that across prompts, previews, summaries, diffs, and maintained artifacts where practical
- if exact identifiers are technically necessary, explain why and ask before including them

---

## Opening Intake Checklist

For the first TP-AgentKit chat on a task, establish the task anchors before planning or broad discovery.

Collect or provide these items:
1. privacy handling: whether usernames, person names, IP addresses, emails, hostnames, or similar identifiers should be excluded or redacted
2. mode: review-only, analysis-only, or edit
3. source folder or program and current revision
4. target handling: use the current revision or create a copied new revision
5. source-of-truth inputs: CSV, workbook, diff HTML, logs, screenshots, or issue list
6. scope: limits, flow, code, bins, history, minimal change, or broader hardening
7. environment or active flow when relevant

Guidance:
- ask the privacy question once on the first turn unless the user already answered it
- ask only for the remaining missing anchors after privacy handling is clear
- do not start with broad repo exploration when the source folder and scope are still ambiguous
- if the user already gave the anchors, move straight to planning
- when the user says there are no special exclusions, do not keep re-asking
- prefer a short intake checklist over a long exploratory first response

---

## Decision-Relevant Questioning Rule

After privacy handling and the basic task anchors are known, use this default questioning rule across TP-AgentKit.

- inspect `testprogram/`, `references/`, and current-task artifacts first when they can answer the next question safely
- ask the user only when an unresolved user-direction branch still changes execution, validation scope, or release confidence
- ask one discriminating question at a time and include the recommended answer or likely best direction
- keep low-risk and single-source tasks direct; do not keep interrogating when the next safe step is already clear
- preserve silent or automation-oriented workflows when explicit inputs already remove the ambiguity

---

## Default Grill Pass For Risky Tasks

After the task anchors are known and a draft plan exists, escalate the default questioning rule into a short user-facing `grill-me` pass by default for medium-risk and high-risk work.

Use this default grill pass when any of these are true:

- the task is release-facing, urgent, or likely to affect lot disposition
- the task is described as `just limits`, `minimal`, or otherwise low-risk without evidence yet
- source of truth may conflict across CSV, workbook, diff export, screenshots, logs, or the current TP
- variant or baseline matching is non-trivial across FT, QA, EWS, cold, ambient, or hot flows
- the change may ship without simulator validation or with reduced validation confidence
- the requested edit touches multiple dependency layers or could hide structure changes inside a nominally simple request
- in-place editing pressure exists, or revision handling is likely to be contested
- the investigation has multiple plausible branches and the next discriminating question matters

Execution rules:

1. inspect recoverable facts first, then ask the user one discriminating question at a time for the branches that still matter
2. include the recommended answer or likely best direction with each question
3. inspect `testprogram/`, `references/`, and current-task artifacts before asking the user for recoverable facts
4. bias the questions toward source-of-truth choice, revision safety, structure integrity, validation depth, variant correctness, and rollback confidence
5. do not treat silent self-challenge as a complete grill pass when unresolved user-direction choices remain
6. stop once the plan is robust enough that the remaining uncertainty no longer changes execution or release confidence

Mode-specific use:

- `review-only`: the grill pass can start as soon as source and scope are clear
- `analysis-only`: use the grill pass when branch resolution matters more than broad explanation
- `edit`: grill the draft plan before presenting it for approval; do not let the grill pass replace approval

For low-risk tasks with one clear source of truth and obvious validation, keep the grill pass brief or skip it and move straight to direct execution or review.

---

## Revision Folder Workflow (Preferred)

For revision updates, do not modify the original test program folder in place.

Use this workflow:
1. Ask the user first which revision to use, or whether a new revision copy should be created.
2. Start from the confirmed source folder (for example `testprogram/UR78FA008BE01_0134`).
3. Create a copied revision folder with the requested rev suffix (for example `..._0134` -> `..._0998`) when the user wants a new revision.
4. Apply all edits only in the new copied folder.
5. Keep the source folder unchanged for side-by-side comparison (for example with WinMerge).
6. Add short inline comments in `.ls` when limits change to show previous limits.

Required uprev metadata sweep:
- After creating or selecting the target revision folder, scan `MainTestPlan/*.tpl` for `JOB_REV` and normalize it to the target revision string.
- Recheck that no stale prior-revision `JOB_REV` value remains anywhere in the target `.tpl` set.
- If the `JOB_REV` correction happens after the main functional edit set, record that metadata correction in the current revision history.

Only use in-place backup files when explicitly requested by the user.

---

## Test Program Discovery

`testprogram/` may be gitignored or not yet created for the requested revision. **Do NOT use a single exact-path check** to conclude absence.

Use this discovery flow:
1. **User path first**: If user gives `testprogram/<program>`, try it directly.
2. **Recursive key-file discovery**: Search under `testprogram/` for `*.ls` and `*.tpl`, then match by program token (e.g. `UQ29FC004B01`).
3. **Keyword confirmation**: Search discovered files for expected test IDs/names to confirm the right program family.
4. **Planned-but-not-created fallback**: If not found, check `.claude/artifacts/current_task/` and `references/` for target folder names (for example, copy plans like `..._0113 -> ..._0117`).
5. **Then escalate**: Only after Steps 1-4 fail, report the folder as missing and ask whether to create/copy it.

If the user mentions a program path (e.g. `testprogram/UR8BFC008BA01_0121`) and it is not present, do not stop at "not found"; complete the fallback flow before concluding.

### Finding flow-level or subplan tests (e.g. relative tests)

Flow-level tests (relative/ESM, named subplans) are **not** defined by test class names under `TestClassesProjectSpecific/`. They live in **SubTestPlans** and are referenced from **MainTestPlan**.

When the user asks about "relative tests", a named subplan (e.g. "Relative", "leakage", "stress"), or which tests belong to a given flow:

1. **Read `MainTestPlan/*.stpl`** (e.g. `UQ29FC004B01.stpl`) and look for `SubTestPlans/` references (e.g. `Final ../SubTestPlans/Relative/RelativeMain.tpl`).
2. **Open the referenced SubTestPlan** (e.g. `SubTestPlans/Relative/RelativeMain.tpl`) to see test instances, test IDs, and flow.
3. Do **not** rely only on searching for the word "relative" (or the subplan name) in `.cpp` or under `TestClassesProjectSpecific/`—it often will not appear there.

**Why this matters:** In the first round of "what are the relative tests in testprogram/<program>?", the agent searched only for "relative"/"REL" in source and found nothing. The relative tests are defined in `SubTestPlans/Relative/RelativeMain.tpl` and referenced in `MainTestPlan/UQ29FC004B01.stpl`; discovering them requires following the .stpl → SubTestPlans path.

---

## Environment Inference From Program Name

When a task says "COLD", "AMB/ROOM", or "HOT" and the program folder name encodes the environment, infer the target environment set from the token.

**Known tokens (example: `UR8BFC008BA01_0121`):**
- `FC` -> FT Cold: **FTC only**
- `FA` -> FT Ambient: **FTR only**
- `FH` -> FT Hot: **FTH only**
- `QC` -> FT QA Cold: **FTC only**
- `EC` -> EWS Cold: **EWC only**

**Rules:**
- If the folder name is generic or ambiguous (no env token), ask for clarification.
- If the user explicitly says "EWS", "FT", or "ALL", follow that instead of inference.
- Extend the token map only when confirmed by the user for that program family.

---

## SPL / Yield Explorer Routing

When a request mentions SPL, SPAT, PAT, Yield Explorer, or uses `references/SPL/*.csv` inputs:

1. start with `.claude/knowledge/spl_workflow_and_methodology.md` for the workflow meaning and approval cautions
2. use `.claude/knowledge/spl_csv_schema.md` for real CSV field semantics and export-family differences
3. use `.claude/knowledge/spl_reference_families.md` when the first clue is the filename and you need a quick family or variant-guard read
4. use `.claude/skills/spl-limit-workflow/` before planning TP edits when approval state, target `.ls`, or environment anchors are still incomplete
5. treat exported CSVs as candidate inputs until the user confirms they are approved for TP implementation
6. cross-check the CSV `TestProgram` field instead of trusting filename tokens alone; repo examples include generic `FT` filenames whose `TestProgram` values are actually `FH`
7. treat `Fail%`, `%Fail`, and `Good Fail%` as equivalent review hints, and do not assume every SPL export contains a fail-rate column
8. when you need retained machine-readable compare outputs, start from `.claude/artifacts/INDEX.md` so you pick the preferred SPL snapshot instead of an older predecessor

---

## Flow-Variant Baseline Rule

Do not assume QA variants and their corresponding main-flow variants share the same exact test coverage or the same exact limits.

Examples:
- FH vs QA FH
- FC vs QA FC
- FA vs QA FA

Rules:
- Compare each edited variant against its own baseline file or launch package.
- Do not treat QA-versus-main differences as defects by default.
- A difference is only a defect when it conflicts with the intended baseline for that specific variant or with explicit user direction.
- When coverage differs between variants, audit only the tests that are expected to exist in that variant.

---

## Sibling-Variant Fast Path

When the user asks for the **same change pattern** on a sibling variant after one variant has already been analyzed in the same chat or in a recent local artifact, do not restart from full broad discovery by default.

Examples:
- FA REL work completed, then user asks for the same REL treatment on FC
- FC limit-only change completed, then user asks for the same change on FH
- main-flow variant audited, then user asks for the corresponding QA variant with the same source-of-truth package

Use this fast path only when all of these are true:
1. the user clearly indicates the new task is meant to mirror or largely follow the prior variant
2. the source-of-truth input is unchanged or explicitly carried forward
3. the program family matches closely enough that prior findings are likely reusable
4. revision handling and edit mode are still clear

Fast-path execution rules:
1. Start from the prior variant's verified risk map, active-flow map, and kept/disabled-block decisions.
2. Read the new variant's active launch path and main flow first, then compare only the expected delta points before widening scope.
3. Re-open source only for blocks that are variant-sensitive, still active in the new flow, or plausibly environment-dependent.
4. Do not repeat full broad archaeology of every previously classified helper or test function unless the new variant's flow structure, test names, or source usage materially differ.
5. If the new variant diverges in a way that changes release confidence, drop out of the fast path and resume the normal deeper workflow.

Recommended first-pass checklist for sibling variants:
- confirm active `tplConfigFile.cfg` target
- compare `MainFlow` / active `.tpl` against the previously analyzed sibling
- check whether previously disabled blocks are already commented or absent
- inspect only the still-live risky blocks before proposing edits
- preserve any previously validated keep decisions unless the new variant contradicts them

Why this matters:
- repeat family work should reuse proven findings instead of paying the full discovery cost again
- this reduces token growth, repeated file reads, and avoidable approval overhead without weakening safety

---

## Context Checkpointing For Long TP Work

When a TP task becomes multi-turn, multi-variant, or read-heavy enough that the agent has already established a strong risk map, create or update a compact local checkpoint before continuing broad follow-on work.

Use a checkpoint when any of these are true:
- a second sibling variant is about to be analyzed in the same chat
- the first variant required substantial source archaeology across flow and code layers
- the agent already has a stable list of risky blocks, safe keep decisions, and validation gaps
- the conversation is at risk of repeating earlier discoveries verbatim

Checkpoint content should be compact and reusable:
- active launch path
- key risky blocks and why they are risky
- key kept blocks and why they were retained
- variant-specific caveats
- validation gaps that still matter on the next variant

Checkpoint placement rules:
1. Prefer repository memory for short durable facts that will help on the next sibling variant.
2. Prefer `.claude/artifacts/current_task/` for task-local summaries when the working set is larger than a few bullets.
3. Reuse the checkpoint on the next variant before doing new broad discovery.
4. Update the checkpoint only when a new variant changes the previously trusted map.

Do not let checkpointing replace fresh validation of the new target flow. The goal is to avoid repeated archaeology, not to skip variant-specific confirmation.

---

## Documentation Standards

| Rule | Description |
|------|-------------|
| **Mermaid for Diagrams** | Always use Mermaid syntax for flowcharts and diagrams in markdown. Never use ASCII art. |
| **Markdown Format** | All documentation in `.md` files with proper headings |
| **YAML Frontmatter** | Knowledge files must include status verification in frontmatter |
| **Compact Artifact Prose** | For agent-generated `.claude/artifacts/` prose, prefer the `compact-reporting` skill. Drop back to full clarity for approvals, safety warnings, release gates, and scale or unit risk notes. |

### Artifact Retention

Use these retention rules for `.claude/artifacts/` to keep task history recoverable without turning the folder into a dump:

1. **`current_task/` is the active working set**
    - Keep the main incident/task artifact here while the activity is ongoing.
    - Keep lightweight task notes such as `TASK.md` or other short-lived support files here when needed.
    - Add lightweight navigation files such as `INDEX.md` when multiple artifacts accumulate.
    - Keep only these classes of material here: active work, rolling outputs, and open follow-through.
    - Treat `current_task/INDEX.md` as a curated resume surface, not a full file inventory.

2. **Promote reusable lessons out of task artifacts**
    - If a finding is reusable across future tasks, move or summarize it into `.claude/knowledge/` or a reusable skill.
    - During repo-maintenance closeout, review touched `.claude/artifacts/current_task/` TP-support notes as promotion candidates instead of blanket-excluding task artifacts.
    - Keep raw `testprogram/` and `references/` files out of durable harvesting; promote the summarized lesson from the artifact note instead.
    - Leave the task artifact focused on the specific incident or delivery history.

3. **Prefer one primary artifact per active effort**
    - Name it clearly, e.g. `<program>-<topic>-<yyyymmdd>.md`.
    - If supporting artifacts exist, reference them from the primary artifact or from `current_task/INDEX.md`.

4. **`archive/` is for completed historical artifacts**
    - Move completed, no-longer-active artifacts here when `current_task/` starts to accumulate unrelated work.
    - Keep an `archive/INDEX.md` so harvested knowledge can still point back to the original task records.
    - Promote an artifact when it is completed, superseded, or needed only for historical reference.
    - After promotion, remove it from `current_task/INDEX.md` unless it still belongs to an open or rolling category.

5. **Do not silently discard task history**
    - If cleanup is needed, summarize or index older artifacts first so recovery after undo/interruption remains practical.

6. **Use artifact compaction selectively**
    - `local-artifact-compress` is for completed prose-heavy artifacts, not for `testprogram/`, safety-critical instructions, or approval-gate wording.
    - Start with `conservative`; use `aggressive` only when the artifact is low-risk and readability can trade a little for stronger compaction.
    - Keep the original backup when using in-place mode and skip compaction when the expected win is trivial.

### `current_task/INDEX.md` Shape

Prefer this order:

1. **Active Now**
    - current repo-maintenance work or the primary incident still being changed

2. **Rolling Outputs**
    - rolling helper files such as latest harvest, latest JSON, or latest closeout summaries

3. **Open Follow-Through**
    - unresolved TP work, pending feedback items, or in-flight skill work that still matters on resume

Do not keep a long flat list of completed dated notes in `current_task/INDEX.md` once they stop being active, rolling, or open.

---

## Universal Constraint Table

| Area | Rule | Rationale |
|------|------|-----------|
| **Order** | bdefs → ls → flow → code | Prevents undefined references |
| **Revision Safety** | Copy folder to new rev and edit only the copy | Preserves baseline and supports WinMerge diff |
| **Limits** | Define tests before flow | Flow needs test definitions |
| **Code** | Never reference undefined tests | Prevents runtime errors |
| **History** | Update when JOB_REV changes | Traceability |
| **History Placement** | Append new entries at end of `*History.txt` only | Preserves chronological order and diff readability |
| **CommonLib** | Never modify | Shared across programs |

---

## Platform-Specific Workflows

### Advantest T2000 (OTPL)

**File Dependencies:**
```
UQ29FC004C02.cfg
    └── imports → MainTestPlanFlow.tpl
                      └── imports → *.stpl (sub test plans)
                      └── imports → Main.ls (limits)
                      └── imports → Main.bdefs (bins)
```

**Add New Test Workflow:**
1. Check `Main.bdefs` for sbin→hbin mapping
2. Add entry to `Main.ls` with test#, name, limits, sbin
3. Add test call in appropriate `.stpl` file
4. Implement test logic in TestClasses (if needed)
5. Update history file

**Limit Sheet Format (Main.ls):**
```
Test#     Test_Name                  LL        UL      Unit    Sbin
500000    REL_1501_VBAT_LEAK_13V    -6.000    6.000   sigma   19
```

**Bin Definition Format (Main.bdefs):**
```
softbin 19 -> hardbin 2 : "Relative Test Fail"
```

### OTPL Guardrails (Relative / Flow Integration)

When adding or updating relative tests in OTPL, run these checks before handing back:

1. **Limit tuple order must match program convention**
    - Some UQ29 programs encode limits as `UL,LL` in `Main.ls` tuples (`FTCT(...)`, `FTAT(...)`, `FTHT(...)`, `WSAT(...)`).
    - Do not assume `LL,UL` from comments/examples.
    - Validate with simulator error text if present (`Lower limit exceeds upper limit`).

2. **Do not re-import `Main.spec` in subplans unless required**
    - If top-level already imports `Main.spec`, importing it again in a subplan can trigger `UserVars _UserVars is redefined`.
    - Prefer inheriting `Main.spec` from top-level plan.

3. **Result action tokens must be legal OTPL actions**
    - Inside `Result { ... }`, use only supported actions (`Property`, `IncrementCounters`, `SetBin`, `SetBins`, `AppendBins`, `Return`, `Reject`, `GoTo`).
    - Avoid `NextAction` in explicit `Result` blocks if parser rejects it.

4. **Test class import must exist in parser search path**
    - If `Import <Custom>.ph` is missing in target TP, use an available class already used by the TP (for example `STM_Judge_Test.ph`) when functionally equivalent.
    - Verify referenced class supports used params/macros (for example `CalcAndJudgeParam`).

5. **`tplConfigFile.cfg` is entry-point only; flow order lives in `MainTestPlanFlow.tpl`**
    - Trace: `tplConfigFile.cfg` -> main `.tpl/.stpl` -> `MainTestPlanFlow.tpl` -> concrete flow (`L9906_SHORT_Flow`, etc.).
    - Apply flow edits at the concrete flow definition, not in cfg.

6. **FlowDefs does not auto-select by device type**
    - Multiple `MainFlow` entries register launchable flows.
    - Active flow is selected by run context/launcher, not automatically by listing order alone.

7. **Patch-scope safety for flow edits**
    - When inserting a new subflow into one flow (for example `L9906_SHORT_Flow`), recheck that similarly named blocks (`L9906_Flow`, `L9907_Flow`) were not unintentionally edited.


### Advantest T2000 (RDK)

**File Dependencies:**
```
tplConfigFile.cfg
    └── MainTestPlan/*.tpl
    └── MainTestPlan/*.ls
    └── TestFunctions/*.cpp
```

**Add New Test Workflow:**
1. Define test in Main.ls
2. Add test call in .tpl flow
3. Implement in TestFunctions/
4. Register in test framework

### Limit-Sheet Guardrails (All T2000 `.ls` edits)

When changing only LL/UL values in an existing `.ls`, treat structure preservation as a separate mandatory validation step.

Before editing any numeric limit, also treat scale and unit compatibility as mandatory.

0. **Verify scale token and unit before changing LL/UL**
    - Confirm the target `.ls` row or `LimitDef(...)` uses the expected scale token and engineering unit for that test.
    - Do not assume the CSV/reference numeric text can be pasted directly without checking whether the `.ls` stores the value as `u`, `m`, `n`, `NONE`, or another program-specific scale form.
    - If the source reference unit and target `.ls` unit do not match, stop and resolve the mismatch before editing.
    - When macros are used, verify both the `PrecScale` field and the `Unit` field, not only the LL/UL numbers.

1. **Default assumption: limit edits must not add or remove tests**
    - If the task is only to tighten/relax LSL or USL, the expected structural delta is zero added rows and zero removed rows.
    - Any added or removed test line must be treated as a defect unless the user explicitly requested a new/deleted test.

2. **Audit touched test-ID occurrence counts against the baseline**
    - For every edited test ID, compare the number of occurrences in the source `.ls` and edited `.ls`.
    - If baseline has one occurrence, edited file must still have one occurrence.
    - If baseline has repeated occurrences by design, update all intended occurrences and confirm the count is unchanged.

3. **Check neighboring blocks, not only the target value**
    - After each patch batch, inspect surrounding unchanged rows above and below the edited lines.
    - This is required because a value fix can still accidentally drop an adjacent line or duplicate a target line elsewhere.

4. **Inspect file tail and footer region explicitly**
    - Always read the last section of the edited `.ls` after manual patching.
    - Stray pasted lines often land near `JOB_REV`, EEPROM `LimitDef`s, or the file footer and can be missed by target-only searches.

5. **Use compare output as a structure gate, not only a value gate**
    - In Beyond Compare or equivalent diffs, review for unexpected insertions/deletions in addition to expected LL/UL deltas.
    - Do not mark the `.ls` correct just because the intended value appears somewhere in the diff.

### Advantest V93000 (SmarTest)

**File Structure:**
```
testflow/
    └── *.tf (test flows)
testmethod/
    └── *.cpp (test methods)
setup/
    └── *.txt (limits, pins)
```

### Teradyne Flex (IG-XL)

**File Structure:**
```
*.igxl (project)
*.vb (test modules)
*.txt (limits)
```

---

## Validation Checklist

Before telling the user that a task is complete, fixed, validated, clean, or ready to release, use the `verification-before-completion` skill. Tie each positive claim to the exact evidence you inspected. If simulator, parser, launch, or lot evidence is missing, state that gap directly instead of implying full validation.

### Before Marking Complete

**Limit Sheet:**
- [ ] All new test numbers are unique
- [ ] Test names follow naming convention
- [ ] Limits are logically valid (LL < UL)
- [ ] Softbins are assigned
- [ ] Units are correct
- [ ] Scale token or macro `PrecScale` is correct for every touched limit
- [ ] Source reference unit matches target `.ls` unit for every touched limit
- [ ] For limit-only edits, baseline and edited `.ls` have no unintended added/removed test rows
- [ ] Touched test IDs have the same occurrence count as baseline unless duplication/removal was explicitly requested
- [ ] File tail/footer checked for stray appended or deleted lines

**Bin Definitions:**
- [ ] All new softbins are mapped to hardbins
- [ ] Descriptions are meaningful

**Flow:**
- [ ] Test calls reference defined tests
- [ ] Tests are in correct flow position
- [ ] Control logic is valid

**Code:**
- [ ] Handles edge cases (divide by zero, etc.)
- [ ] Follows naming conventions
- [ ] Has proper datalogging

**Documentation:**
- [ ] History file updated
- [ ] JOB_REV updated if significant changes
- [ ] Walkthrough log complete
- [ ] Completion or release claim names the exact validations run and any remaining validation gaps

---

## Error Recovery

### If Compilation Fails
1. Check syntax against platform reference
2. Verify all imports exist
3. Review walkthrough for recent changes
4. Rollback if necessary from backup

### If Runtime Error
1. Check test number mappings
2. Verify variable definitions
3. Check for divide-by-zero cases
4. Review ESM initialization

---

## Human Escalation Triggers

Stop and request human input for:
- [ ] Conflicting requirements
- [ ] Missing critical information
- [ ] Changes to shared infrastructure
- [ ] Destructive operations
- [ ] First-time task with no examples

