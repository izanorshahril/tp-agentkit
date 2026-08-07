---
type: operational_pattern
status: partial
verifier: repeated SystemController stack correlation plus TP source inspection plus STDF interruption chronology
date: 2026-03-30
source: ".claude/artifacts/archive/urx8-production-log-analysis-20260318.md"
source_artifacts_files: 1
source_artifacts_note: "Promoted from the URX8 runtime-stop investigation after narrowing the low-level T2000 RTE path"
---

# T2000 RTE Stack Narrowing

Reusable pattern for production incidents where T2000 reports a generic flow/start-item runtime error, but the real stop-causing failure is deeper in the SystemController stack and TP test-function code.

---

## 1. Problem Shape

Use this pattern when:

- production testing stops on runtime error and interrupts STDF generation
- top-level logs report a generic failed flow or start item
- the same lot resumes only after stop or reload
- TP text for the named start item looks structurally valid, so the wrapper message is suspicious

---

## 2. Core Lessons Learned

1. Treat the first runtime message as a wrapper until the deeper stack is checked.
   - In the URX8 case, the repeated `Flow_Main_ft` / `JOB_REV` message was not the true low-level cause.

2. Prefer the deepest repeated SystemController exception over the broadest framework wording.
   - The most useful lines were the repeated low-level `ATF-UE:UsrErr` exception and the C++ call stack below it.

3. Correlate the low-level stack back to workspace TP source immediately.
   - Once the stack names the failing test function and source lines, inspect the exact helper and caller path in the local TP copy.

4. Separate runtime-stop cause from reject or yield fallout.
   - If the runtime error stops T2000 and fragments STDF, treat yield patterns as secondary until the stop-causing exception is narrowed.

5. Repetition matters more than a single noisy incident line.
   - If the same exception, DUT, and call stack recur across multiple stop windows, treat that repeated signature as the main narrowing axis.

---

## 3. URX8 Case Pattern

The reusable shape extracted from URX8 was:

- framework wrapper message: failed flow execution at a generic start item
- repeated low-level failure: `rdk::ArrayDUT::operator() endIdx(5500) < startIdx(7974) at DUT2`
- repeated failing flow item: `T_4_IDDQ_ATPG_Stress`
- repeated code path:
  - `Get_STRESS_info`
  - `ENERGY_STRESS`
  - `T_4_IDDQ_ATPG_Stress`

This pattern was sufficient to move the investigation away from start-item text or user-var wiring and into the test-function implementation.

---

## 4. Code-Level Smells To Check First

When the repeated low-level exception points into TP code, prioritize these checks:

1. Fixed window assumptions versus actual capture length.
   - Example: waveform generation or intended processing length differs from the configured capture length.

2. Unchecked array slicing or indexing.
   - Example: `array(start, end)` or `array[idx]` is called without validating `start`, `end`, and array size.

3. Threshold-search return values used directly as slice boundaries.
   - Example: `findFirstRisingIndex(...)` or similar APIs can return values that are legal for the captured array but illegal for the assumed processing window.

4. DUT-specific waveform or edge-detection behavior.
   - One DUT can be enough to throw the RTE and stop the lot even if most other DUTs are still behaving normally.

---

## 5. Recommended Narrowing Workflow

1. Collect the repeated low-level exception text from `SystemController_Error.log`.
2. Group incidents by identical exception signature, DUT, and call stack.
3. Identify the repeated failing flow item.
4. Read the referenced TP source and confirm whether the named helper and caller path exist locally.
5. Look first for array-window, capture-length, or threshold-index assumptions near the cited lines.
6. State the result in two layers:
   - framework wrapper message
   - actual low-level failing path

---

## 6. Minimum Deliverables For Similar Cases

- repeated low-level exception signature
- repeated DUT or site reference if present
- mapped TP source path and functions
- one short explanation of why the wrapper message is not the root cause
- one concrete debug focus list for the expert owner

---

## 7. Limits Of This Pattern

Related proposal: `./improvements/systemcontroller_rte_stack_mapper_20260330.md` captures the tooling follow-up for mapping repeated low-level runtime errors back to TP source. Treat this file as the reusable analysis pattern and the improvement report as the proposed automation path.

- This pattern narrows root cause; it does not prove the final code fix by itself.
- It depends on the SystemController log carrying a useful low-level stack.
- It should be combined with TP source inspection before claiming the stop-causing mechanism.
