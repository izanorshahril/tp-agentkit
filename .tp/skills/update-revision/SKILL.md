---
name: update-revision
description: Create or update a test-program revision while preserving the source and normalizing active launch metadata and history. Use for revision copies, job-token clones, revision macros, launch-package renames, or stale revision references.
---

# Update a revision

Map the program first when the launch family or revision surfaces are unclear. Load `backup-work` for the baseline.

## Revise

1. Confirm the source, target revision, naming convention, active variants, and whether the user authorized a copy or an in-place update.
2. Preserve the source by default. Copy only after proving the target does not collide with an existing revision.
3. Search the source for revision-bearing content: folder and file names, launch references, job tokens, `JOB_REV`-style macros, generated paths, and chronological history.
4. Rewrite by semantic role. Avoid blind replacement of every numeric or job-like token.
5. Follow renamed references through the active launch path and append history in the program's observed format.
6. Sweep the entire active target for stale old-revision values. On T2000, include all relevant `.tpl` siblings rather than only the first file that exposed `JOB_REV` drift.

Useful checks to adapt:

```powershell
rg -n --fixed-strings '<old-revision>' '<target>'
rg -n 'JOB_REV|REVISION|JOB[_-]?REV' '<target>'
rg -n --fixed-strings '<new-revision>' '<target>'
```

Compare source and target after the copy. The expected delta is the intended rename and metadata change plus explicitly requested functional work; unexplained deletes, size collapses, or content changes are failures.

## Complete when

The source is unchanged, the target launches through internally consistent references, all active revision metadata names the new revision, history is traceable when present, and no stale old token remains except documented intentional text.
