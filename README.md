# TP-AgentKit

Context-first AI guidance for semiconductor test program engineering. Bring a
real task and its available evidence; TP-AgentKit discovers the workspace and
chooses the smallest workflow that fits.

## What it does

- **Discovers before deciding**: finds the actual program files, entry points,
	variants, and source-of-truth inputs instead of assuming a folder layout.
- **Follows evidence**: maps flows, limits, bins, configuration, code, exports,
	logs, and baselines to the question being asked.
- **Protects edits**: identifies the target and approval boundary before
	mutation, with copied revisions preferred for baselines and release material.
- **Preserves narrow changes**: keeps structure intact for focused updates and
	checks touched rows, neighboring content, occurrences, and file tails.
- **Validates at the right boundary**: runs the narrowest useful checks and
	states missing parser, simulator, launch, or production evidence clearly.
- **Adapts to the task**: composes discovery, comparison, planning, editing,
	validation, and independent review when the evidence calls for them.
- **Supports interruption and handoff**: retains the decisions and next action
	needed to continue a long or multi-variant task.

## Use it for

- Test program and flow analysis
- Limit, bin, configuration, and code reviews
- CSV, workbook, log, and baseline comparisons
- Release-facing change reviews
- Repository and test-program maintenance

## Start a task

Describe the outcome you need in ordinary language. Include any known paths,
inputs, scope, target variant, privacy constraints, or desired mode such as
analysis-only, review-only, or edit. The agent will inspect what is actually
present and ask only questions that affect execution, safety, or validation.

Edit work pauses for approval before files are changed. Analysis and review work
can proceed without a mutation approval.

There is no required test-program folder layout, revision naming scheme, or
local script runner. Technical operating details for maintainers are documented
in [AGENTS.md](AGENTS.md).

