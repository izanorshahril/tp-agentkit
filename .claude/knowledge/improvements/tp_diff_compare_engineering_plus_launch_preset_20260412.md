---
type: improvement_report
status: new
date: 2026-04-12
use_case: "TP compare sessions where whole-folder output is too noisy but engineering-only filters are too narrow because launch-package files also matter"
---

# Improvement Report: TP Diff Compare Engineering-Plus-Launch Preset

## User Need Captured

- Some TP reviews need a middle ground between:
  - whole-folder compare, which is dominated by build or simulator residue
  - engineering-only compare, which can hide launch-package removals or redirects
- In the URX8 official `0001` versus `0002` review, the most useful filter set was:
  - `.cpp`
  - `.h`
  - `.ls`
  - `.tpl`
  - `.cfg`
  - `.env`
  - `.soc`
  - `.ini`
  - `*History.txt`
- This same middle-scope compare is likely to recur in release, packaging, and launch-package reduction reviews.

## Toolkit Gaps Found

1. `tp_diff_compare` already supports repeated `--filter-ext` and `--filter-glob`, but the useful middle-scope preset must currently be reconstructed manually each time.
2. The existing recommended engineering filter is too narrow when `.cfg`, `.env`, `.soc`, and `.ini` are part of the real review scope.
3. Whole-folder mode remains necessary as a first pass, but follow-up review becomes repetitive when the same launch-package filter set is typed repeatedly.
4. There is no named preset that signals the semantic intent: `engineering source plus launch-package surface`.

## Proposed Improvement

Extend `tp_diff_compare` with a named preset for engineering-plus-launch review.

Recommended direction:

- add a CLI option such as `--preset engineering-plus-launch`
- map it to:
  - `.cpp`
  - `.h`
  - `.ls`
  - `.tpl`
  - `.cfg`
  - `.env`
  - `.soc`
  - `.ini`
  - `*History.txt`
- allow explicit `--filter-ext` and `--filter-glob` to still override or extend the preset when needed

## Minimum Feature Set

1. Add a named preset for engineering-plus-launch review.
2. Keep whole-folder compare as the default first-pass behavior; the preset should be a narrowing tool, not the new default.
3. Print the resolved filter set clearly in both human and JSON output.
4. Keep markdown report mode compatible with the preset.
5. Keep external HTML cross-check mode compatible with the preset.

## Guardrails

1. Do not let the preset replace whole-folder compare when the user explicitly asked for the full TP delta.
2. Do not hide the active filter set; reviewers should always see what file classes were included.
3. Do not silently exclude history files from this preset; release context still matters.
4. Keep `.pat` outside this preset unless the user explicitly asks for it, because launch-package reviews usually do not need pattern churn.

## Why This Should Be An Improvement Report, Not A New Skill

- The correct home is the existing `tp_diff_compare` skill.
- The reusable need is a better preset and CLI surface, not a separate discovery surface.
- The current tool already has the core comparison engine and report behavior needed for this improvement.