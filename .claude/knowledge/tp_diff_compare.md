---
type: operational_pattern
status: verified
verifier: retained-baseline and full-folder TP diff review
date: 2026-04-08
source: ".claude/skills/tp_diff_compare/SKILL.md; .claude/artifacts/archive/scr-simulator-parse-discovery.md; .claude/artifacts/archive/ur7s-0021-vs-0022-section-compare-20260403.md; .claude/artifacts/archive/ur7s-ur7t-special-tp-99-audit-20260331.md"
source_artifacts_files: 3
source_artifacts_note: "Extended with retained section-based family compare and import-scoped suffix-overlay audit patterns from UR7S/UR7T reviews"
---

# TP Diff Compare Pattern

Reusable pattern for comparing two test program folders recursively when the goal is to establish the real per-file delta across the whole TP.

This pattern is also packaged as a reusable skill at `.claude/skills/tp_diff_compare/`.

Use this pattern for revision-to-revision review, retained-baseline comparison, packaging checks, and any TP audit where a filtered engineering-only subset is too narrow.

## Extraction Scope

- Verified example baselines:
   - `testprogram/UR7T_0016` -> `testprogram/UR7T_0017`
   - `testprogram/UR7S_0021` -> `testprogram/UR7S_0022`
   - `testprogram/UR8K_2207` -> `testprogram/UR8K_2700`
   - historical working-copy compares from earlier SCR validation:
     `testprogram/UR7T_0016` -> `testprogram/UR7T_0016_SCRWIP`, `testprogram/UR7S_0021` -> `testprogram/UR7S_0021_SCRWIP` (those working-copy folders are not retained in the current workspace snapshot)
- Verified compare modes:
  - whole-TP recursive compare
  - optional focused filter using `.cpp`, `.ls`, `.tpl`, and `*History.txt`
- Verified example outcome:
  - detects intended feature deltas
  - exposes broader release changes outside the original request
  - supports narrowing after the whole-file delta set is known
- Later UR7S / UR7T and UR7E diff reviews also confirmed the stale-export rule: once live repairs happen after HTML export generation, the export remains useful for file-set coverage but not for exact final text fidelity.

---

## 1. Problem Shape

Use this pattern when:

- The user asks for a whole TP diff between two folders
- The TP folder contains important deltas outside `.cpp`, `.ls`, `.tpl`, and history files
- Git history is incomplete, ignored, or unavailable for the TP folder itself
- A retained baseline exists under `references/`, `testprogram/`, or another known path
- The first question is "what changed at all?" rather than "what changed in engineering files only?"

This pattern starts broad, then narrows only if needed.

---

## 2. Core Lessons Learned

1. Whole-folder file presence is the correct first pass when the user asks for the full TP delta.
   - This prevents missing important support-file additions that a focused engineering filter would hide.

2. Filtered compares still matter, but they belong after whole-TP inventory.
   - Once the full file delta is known, `.cpp`, `.ls`, `.tpl`, and history can be isolated for engineering review.

3. A retained `references/` snapshot or older `testprogram/` revision is sufficient as a baseline.
   - Record the exact folders used so later reviewers understand the comparison source.

4. Compare summaries are usually more useful than raw diff dumps for the first pass.
   - Whole-folder counts and changed-file lists establish scope before deep hunk review.

5. Unified text diffs should be optional.
   - Printing every hunk for every changed file is useful only after the user confirms which files matter.

6. Markdown report generation is useful when the compare result needs to be retained as an artifact.
   - The skill can write a reusable markdown report directly, instead of requiring a separate manual summary step.
   - A single report that includes both whole-folder compare and recommended engineering-filter compare is more useful than separate artifacts.
   - For engineering review, the report is stronger when the recommended-filter section includes actual file-content diffs, not only changed-file lists.
   - Detailed compare output should ignore unknown-extension or binary files and show only contextual hunks for text-comparable files.

7. History files remain part of the review even in whole-TP mode.
   - Release context often explains whether broader deltas belong to the same revision bundle.

8. The same skill should support both whole-TP and focused compare modes.
   - Whole compare is the default; filters are a narrowing tool, not a separate workflow.

9. External compare-tool HTML exports are useful as a final scope cross-check.
   - If the export contains base-folder metadata plus repeated `File:` sections, it can be parsed and compared against the live folder delta set.
   - If the export is a Beyond Compare directory-summary page, it can still provide the external delta inventory even though it lacks per-file text content.
   - If the export is a WinMerge folder summary page with linked child reports in a sibling `.files/` folder, the summary page itself is enough to establish the external delta inventory.
   - Treat this as an audit gate for delta coverage and path status, not as a replacement for the live source-to-source compare.
   - If live files are repaired after the export is generated, treat the export as a stale snapshot for text fidelity. Keep using it for expected-file-set coverage and path-status review only, and use the current live files for final load-risk conclusions.

10. Overlay review benefits from a two-baseline compare sequence.
   - Compare previous release -> current release first, then current release -> overlay working copy.
   - This prevents normal release delta from being misreported as overlay-only work.

11. Simulator-built working copies can create heavy build-noise deltas.
   - Expect `.dll`, `.pdb`, `.lib`, `.exp`, `.obj`, `.tlog`, `.ipch`, `.sdf`, and `.suo` differences when one side has been locally built.
   - Whole-folder compare should report them, but engineering review should then narrow to source/config files.

12. Source hash compare and whole-folder metadata compare answer different questions.
   - Hash-compare of `.cpp`, `.ls`, `.tpl`, `.cfg`, `.env`, `.soc`, `.ini`, and history files is the right test for meaningful implementation drift.
   - Metadata compare across the full folder tree is the right test for simulator-build residue and packaging-state differences.

13. Mixed-family TP diffs are easier to interpret when grouped by section.
   - Separate normal production, SCR or other special-production families, and engineering special families instead of flattening every changed path into one list.
   - This makes it obvious whether the delta is isolated to one family layer or changes the structural model across the TP.

14. Overlay closeout scope should come from active launch imports.
   - Read the target `.tpl` imports before treating sibling `.ls` or similarly named launch files as blocking review items.
   - If a file is not imported by the jobs under review, keep it out of blocking scope unless the user explicitly asks for a wider family audit.

---

## 3. Recommended Execution Order

1. Identify the current TP folder and the best baseline folder.
2. Run a whole-TP recursive compare first.
3. Review counts for:
   - changed files
   - only-in-baseline files
   - only-in-current files
4. Summarize changed files by category or file type.
5. If needed, rerun with filters for `.cpp`, `.ls`, `.tpl`, and `*History.txt`.
6. If needed, rerun with unified text diffs for specific changed files.
7. If needed, emit a markdown report artifact directly from the skill.
8. Produce a concise report artifact for reuse.

---

## 4. TP Diff Compare Checklist

- [ ] Baseline path is explicitly named
- [ ] Current TP path is explicitly named
- [ ] Whole-TP compare is run before narrowing
- [ ] File presence deltas are stated explicitly
- [ ] Changed files are grouped in a usable way
- [ ] History deltas are included in the review context
- [ ] Focused engineering review is treated as a follow-up mode, not the default
- [ ] Unified diffs are requested only when they add value

---

## 5. Reporting Format That Worked

For each TP family:

- state baseline and current folder
- state whether the compare was whole-TP or filtered
- for mixed-family TPs, group findings by section and paired family before file-by-file detail
- list changed files
- list files only in baseline/current
- summarize the important changed files in plain language
- conclude whether the TP contains only the expected feature delta or broader release changes

Useful section order:

1. comparison scope
2. reference baselines used
3. changed-file counts
4. per-file or per-category findings
5. overall conclusion

---

## 6. Interpretation Rules

- If the whole-TP compare finds support-file additions, report them even if they are not engineering files.
- If a later focused compare narrows the set, say clearly that it is a follow-up filter, not the full delta.
- If a history file mentions a larger CI bundle than the originally requested feature, treat the larger bundle as the true release delta.
- If a file exists only in the current TP and not in the baseline, call that out explicitly.
- If a file type is unchanged after a filtered rerun, report that explicitly rather than leaving status ambiguous.
- If an external HTML export predates live repairs, say so explicitly and treat it as stale for exact diff text even if its file inventory is still useful.
- If the TP is organized into production, SCR, and engineering sections, report findings by section so unchanged families are explicit.
- If the task targets a specific job subset, derive blocking scope from the active `.tpl` imports before escalating on sibling `.ls` or launch files.

---

## 7. Applicability Notes

- This pattern is generic for TP review work and is not limited to one product family.
- It is especially useful when `testprogram/` is ignored by source control and direct git diff against repo history is not enough.
- Use filters when the user wants engineering-only follow-up review, but start with the whole TP unless the user explicitly asks otherwise.

## 8. Skill Behavior

The reusable skill at `.claude/skills/tp_diff_compare/` supports:

- recursive whole-folder compare by relative path
- per-file content comparison using hashes
- reporting files only in baseline/current
- optional extension and glob filters
- optional unified diffs for changed text files
- optional markdown report output
- JSON output for agent consumption
- optional external HTML cross-check for multi-file TP diff exports with `Left base folder`, `Right base folder`, and repeated `File:` sections
- optional external HTML cross-check for WinMerge folder summary pages that link into a `.files/` child-report directory

In markdown-report mode, the skill can bundle both views into one artifact:

- whole-folder compare
- recommended engineering filter compare using `.cpp`, `.h`, `.pat`, `.ls`, `.tpl`, `.bdefs`, and `*History.txt`
- detailed per-file unified diffs for changed files in the recommended engineering-filter compare
- unknown-extension or binary files ignored from detailed compare output

## 9. Verified Example Outcome

Verified source compares:

- `testprogram/UR7T_0016` versus `testprogram/UR7T_0017`
- `testprogram/UR7S_0021` versus `testprogram/UR7S_0022`
- `testprogram/UR8K_2207` versus `testprogram/UR8K_2700`
- historical working-copy compares from earlier SCR validation: `testprogram/UR7T_0016` versus `testprogram/UR7T_0016_SCRWIP`, `testprogram/UR7S_0021` versus `testprogram/UR7S_0021_SCRWIP` (those folders are not retained in the current workspace snapshot)

What the compare proved:

- the TP can contain more than the originally discussed feature delta
- whole-TP compare is the right first pass when support files or added helpers may matter
- filtered engineering review still works well as a second pass
- concise file-by-file summary remains more useful than dumping every raw hunk immediately
- overlay compares stay clearer when release delta and overlay delta are separated
- simulator-built working copies can differ heavily at artifact level while still matching on source content
