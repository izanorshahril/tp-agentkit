# Skill Router

This index is the routing cache for the nonstandard `.tp` skill location. Match the task against every row, then read each matching skill completely. Skills combine when their triggers overlap.

| Skill | Load when |
|---|---|
| [`map-test-program`](map-test-program/SKILL.md) | the program is unfamiliar, its active launch or dependencies are unclear, a task-sized map is needed, or tester-platform, product, datasheet, or change-document context should persist |
| [`pressure-test-plan`](pressure-test-plan/SKILL.md) | a medium-risk or high-risk change, ambiguous authority, destructive action, or reduced-validation release decision needs hard questions before execution |
| [`backup-work`](backup-work/SKILL.md) | work will edit in place, replace or remove files, create a revision, or otherwise needs a tested rollback baseline |
| [`update-revision`](update-revision/SKILL.md) | a TP revision, launch package, job token, revision macro, or history record must be copied or updated |
| [`update-limits`](update-limits/SKILL.md) | limits must be reviewed or changed from CSV, workbook, specification, population, or direct user values |
| [`update-spec`](update-spec/SKILL.md) | an approved specification change must be interpreted, traced, or implemented without losing units, conditions, or provenance |
| [`change-test-flow`](change-test-flow/SKILL.md) | tests or subplans must be added, removed, moved, gated, binned, or made reachable in an active flow |
| [`add-test`](add-test/SKILL.md) | a new or companion test needs identifiers, limits, implementation, datalogging, bins, and active-flow integration |
| [`improve-test-setup`](improve-test-setup/SKILL.md) | setup, instrumentation, calibration, timing, site behavior, state restoration, or teardown must be improved |
| [`analyze-test-evidence`](analyze-test-evidence/SKILL.md) | CSV, STDF-derived data, datalog, runtime log, diff, or source must be correlated to explain behavior or failures |
| [`verify-test-program`](verify-test-program/SKILL.md) | a TP change or conclusion is about to be called complete, correct, safe, validated, or ready |
| [`show-work`](show-work/SKILL.md) | an engineer needs a concise decision trail, change summary, verification evidence, rollback, or next action |
| [`learn-from-work`](learn-from-work/SKILL.md) | completed work revealed a verified reusable method, invariant, failure mode, user preference, or environment constraint |

Descriptions here are intentionally the only always-routed cache. Keep each row discriminating and update it with the skill frontmatter when a trigger changes.
