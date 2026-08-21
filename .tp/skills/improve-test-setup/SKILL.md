---
name: improve-test-setup
description: Improve test setup, instrumentation, calibration, sequencing, timing, multisite behavior, state restoration, or teardown without silently changing measured coverage. Use when reliability, clarity, repeatability, or runtime behavior depends on preconditions around a test.
---

# Improve test setup

Model setup as a state transition around the measurement:

```text
entry state -> configure -> settle/calibrate -> stimulate -> measure -> judge -> restore
```

## Setup loop

1. Trace the active caller and the real hardware, software, variable, relay, supply, timing, and site state at entry and exit.
2. Name the invariant to improve: correctness, repeatability, isolation, recovery, runtime, readability, or resource use. Preserve measured coverage unless the request changes it.
3. Identify shared state and failure paths. A passing path that restores state while an exception, reject, or site-mask path leaks it is incomplete.
4. Make one tracer change at the cleanest seam. Prefer an existing setup abstraction when it actually owns the behavior; avoid broad helpers that hide test-specific requirements.
5. Instrument or log only enough to distinguish the hypotheses, then remove noisy task-only diagnostics after the behavior is proven.
6. Exercise normal, fail, retry, abort, and multisite paths when they can change state. Verify teardown after each relevant path.

For timing or amplitude reductions, reason about the physical purpose and tester constraints; zero is not automatically safer. For calibration, distinguish tester-resource calibration from DUT programming or functional behavior before removing or moving it.

## Evidence ladder

Use the strongest available feedback: focused unit or harness check -> parser/compile -> simulator -> bench/tester -> representative datalog or lot. Offline structure checks cannot prove analog settling, instrument behavior, or production repeatability.

## Complete when

The improved invariant is observable, entry and exit state are defined, every relevant failure and site path restores required state, coverage changes are explicit, and hardware-dependent confidence is either demonstrated or marked conditional.
