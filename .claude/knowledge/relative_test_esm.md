---
type: reference_doc
source: "Historical ESM methodology PDF (Rev 14), OCR/manual conversion; original PDF is not retained in this workspace"
conversion_method: AI assistant, OCR, manual_cleanup
status: partial_verification # Options: raw, partial, verified
verification_history:
  - section: "example code for T2000‑RDK,T2000-OTPL & Flex"
    verifier: "local_review"
    date: 2026-01-22
  - section: "practical T2000-RDK implementation and validation notes"
    verifier: "maintainer_review"
    date: 2026-03-15
---

## Discovery (T2000 OTPL)

In an OTPL test program, **where relative tests live** is flow-level, not in test class source:

- **MainTestPlan** `*.stpl` lists sub-plans, e.g. `Final ../SubTestPlans/Relative/RelativeMain.tpl;  # REL`.
- **SubTestPlans/Relative/RelativeMain.tpl** (or equivalent) defines the test plan name (e.g. `TestPlan REL;`), the relative test instance(s) (e.g. `Relative_Judge` using `UQ29_CalcAndJudge_Test`), and test ID ranges (e.g. T500000–T500042).

When asked "what are the relative tests in testprogram/&lt;program&gt;?", read `MainTestPlan/*.stpl` and then `SubTestPlans/Relative/*.tpl`; do not rely only on searching for "relative" or "REL" in `.cpp` or under `TestClassesProjectSpecific/`.

---

# Relative Test Using Extreme Studentized Deviation (ESD) Methodology  
APG Product Engineering – STMicroelectronics Muar  

---

## 1. Objective

- To explore the best possible algorithm to detect outliers as a replacement for the present relative test methodology.
- To develop an alternative method that is:
  - Statistically sound.
  - Able to outperform the present Relative Test in detecting maverick units/outliers.
  - Maintaining minimal over-rejection.

---

## 2. Weaknesses of the Present Relative Test Method

The current relative test approach has several limitations:

- **Assumption of stability over time**
  - Assumes uniformity of the lot over time.
  - Assumes uniformity of judgment across engineers.

- **Subjective engineering judgment**
  - What one engineer considers an outlier may not be considered so by another.
  - Limits often depend on engineering judgment rather than statistical rules.

- **High engineering overhead**
  - Requires continuous engineering effort and time.
  - PE needs to review limits over a long period or large lot runs.

- **Inflexible formulation**
  - The denominator is fixed as:
    $$
    \text{USL} - \text{LSL}
    $$
  - If the spec window is too wide or too loose, detection becomes weak.
  - If the spec window is narrow, it may over-penalize natural variation.

---

## 3. First Relative Test Method (Current Method)

### 3.1 Definition

The original Relative Test is defined as:

$$
\text{Relative Test (\%)} = 
\frac{\text{DUT reading} - \overline{X}_{10}}
{\text{USL} - \text{LSL}} \times 100
$$

where:

- $\overline{X}_{10}$ = mean of the **10 previously tested Bin1 units** for that test.
- USL = Upper Specification Limit.  
- LSL = Lower Specification Limit.

### 3.2 When It Starts

- Relative Test starts **at the 11th unit**, provided that all previously tested 10 units **pass**.
- Only **Bin1 (good)** units are used to calculate the mean for comparison.

### 3.3 Illustration

For a given test (say Test #Y), and a sequence of units:

- Units 1–10: Bin1, used to compute $\overline{X}_{10}$.
- Unit 11 (or 12, 13, 14, …):  
  For unit $k$:

$$
\text{Relative Test} =
\frac{\text{Unit}_k \text{ reading at Test #Y} - \overline{X}_{10}}
{\text{USL} - \text{LSL}} \times 100\%
$$

This relative percentage is then compared to a fixed engineering-defined limit (e.g. ±5%, ±10%, etc.).

**Key limitations of this method:**

- Only the **first 10** units contribute to the reference mean.
- The denominator is fixed to $(\text{USL} - \text{LSL})$, independent of actual lot distribution.
- Does not adapt to changes in process mean or variation as the lot progresses.

---

## 4. Second Relative Test Method: Fixed-Window ESD (30-Sample)

### 4.1 Definition (ESD-Based Relative Test)

This method uses the **Extreme Studentized Deviation (ESD)** concept:

$$
\text{Relative Test (ESD)} =
\frac{\text{DUT reading} - \overline{X}_{30}}
{S_{30}}
$$

where:

- $\overline{X}_{30}$ = mean of the **30 previously tested Bin1 units**.
- $S_{30}$ = standard deviation of the **30 previously tested Bin1 units**.

### 4.2 Choice of 30 Samples

- A sample size of **30** is chosen to:
  - Provide a reasonably good estimate of standard deviation.
  - Be statistically sound while still practical in production.

### 4.3 Reject Criteria

- A part is rejected if:

$$
\left|\frac{\text{DUT reading} - \overline{X}_{30}}{S_{30}}\right| > 6
$$

- This **6σ** rule is in line with JEDEC Standard:
  - JESD‑62A, *“Outlier Identification and Management System for Electronic Components”*.

### 4.4 Advantages

- Uses **moving mean** and **moving standard deviation** (over last 30 good parts).
- Reacts quickly to **lot-to-lot shifts** in data distribution.
- Allows natural variance between different lots while maintaining a stable rule of 6σ.

### 4.5 Disadvantages

- **Potential over-rejection scenario**:
  - If the **previous 30 good parts** have very low variance (very tight cluster), and
  - The current DUT slightly deviates from them (still normal within the overall lot distribution),
  - It may be flagged as outlier because the local window looks too tight.

---

## 5. Pseudo Dynamic ESD (ESM) – Latest Relative Test Method

Also known as:

- **Pseudo Dynamic Extreme Studentized Deviation**
- **Pseudo DynPat test**
- **ESM relative test** (with re‑introduction by Calogero Casa)

### 5.1 Definition

Instead of using a fixed window (e.g., last 30 units), this method uses **all previously and presently tested Bin1 units** up to the current unit $n$:

$$
\text{Relative Test (ESM)} =
\frac{X_n - \overline{X}_n}
{S_n}
$$

where:

- $X_n$ = measurement of **unit $n$**.
- $\overline{X}_n$ = mean of **all Bin1 units from unit 1 to $n$**.
- $S_n$ = standard deviation of **all Bin1 units from unit 1 to $n$**.

> Comparison can start as early as the **2nd unit**.

### 5.2 Reject Criteria

- A part is rejected if:

$$
\left|\frac{X_n - \overline{X}_n}{S_n}\right| > 6
$$

- Default recommendation: **6 standard deviations** (JEDEC-aligned).  
- User may tighten or loosen this limit as needed, but 6σ is the recommended value.

### 5.3 Incremental Update Formulas

The method is designed to be easily implemented iteratively without re-summing all past data.

For $n \ge 2$:

- **Mean update:**

$$
\overline{X}_n =
\left(1 - \frac{1}{n}\right)\overline{X}_{n-1}
+ \frac{1}{n} X_n
$$

- **Variance / standard deviation update (conceptual form):**

A commonly used incremental form (aligned with the slide intent) is:

$$
S_n^2 =
\frac{n-2}{n-1} S_{n-1}^2
+ \frac{1}{n} (X_n - \overline{X}_{n-1})^2
$$

and then:

$$
S_n = \sqrt{S_n^2}
$$

> The key idea: **$ \overline{X}_n $ and $ S_n $ can be derived from $ \overline{X}_{n-1} $ and $ S_{n-1} $**, avoiding full recomputation.

### 5.4 Deviation on Unit n (Formal Definition)

For $n \ge 2$, the **standardized deviation** (z-value) of unit $n$ is:

$$
D_n =
\frac{X_n - \overline{X}_n}{S_n}
$$

Reject unit $n$ if:

$$
|D_n| \ge 6
$$

### 5.5 Advantages

- **Early comparison:**
  - Outlier detection is possible starting from the **2nd unit**.
- **Least over-rejection** among all tested methods:
  - Every new measure updates the global statistics; tails of a wide distribution are less likely to be falsely rejected.
- **Efficient implementation:**
  - Incremental formulas make it easy to implement in code on any tester:
    - Keep track of $\overline{X}_{n-1}$ and $S_{n-1}$.
    - Update to $\overline{X}_n$ and $S_n$ upon each new good unit.
- **Adapts continuously:**
  - As the lot progresses, statistics reflect the accumulated distribution, improving robustness and minimizing false positives.

---

## 6. Where to Insert the Relative Test in the Flow

Relative test should be placed **after the entire test sequence for that test step**, and only for units that have passed all prior screening.

Example product with 5 tests:

1. Test 1  
2. Test 2  *(we want to introduce relative test here)*  
3. Test 3  
4. Test 4  
5. Test 5  

### Wrong Implementation

- Perform Relative Test for Test 2 **immediately after Test 2**:

```text
Test 1
Test 2
Test 2 Relative Test    ← WRONG
Test 3
Test 4
Test 5
```

Reason: Relative test would also be applied to parts that may later fail Test 3–5.

### Correct Implementation

- Perform Relative Test for Test 2 **after all tests are completed and passed**:

```text
Test 1
Test 2
Test 3
Test 4
Test 5
Test 2 Relative Test    ← CORRECT
```

**Key rule:**

- **Apply relative test only to parts that are “good”** according to all existing (pre‑relative-test) criteria.

---

## 7. Comparison of Outlier Detection Methods

### 7.1 vs Pat Outlier (Post-Processing Method)

Empirical comparison (as presented):

- **Pat Outlier (post-processing, as used in EWS):**  
  - 4 outliers rejected.
- **Bosch Relative Test method @ 6σ (1st method equivalent):**  
  - No outliers rejected in the given example.
- **ESD method @ 6σ (2nd method):**  
  - 3 outliers rejected.
- **Pseudo DynPat (ESM) method @ 6σ (latest method):**
  - 6 outliers rejected.
  - 2 additional over-rejects observed.

**Observation:**

- Only with the **Pseudo DynPat / ESM method**:
  - All outliers above 6σ were detectable.
  - At the cost of a small number of over-rejects (trade‑off).

### 7.2 Original Data vs Pseudo DynPat Outliers

- Pseudo DynPat (ESM) relative test data most closely approximates the **original data behavior**, especially for outliers.
- Indicates the method provides the most faithful representation of actual distribution tails.

---

## 8. Detailed Comparison of Relative Test Methods

| Aspect | 1st Method: Conventional Relative Test | 2nd Method: 30‑Sample ESD | Latest Method: ESM / Pseudo DynPat |
|--------|----------------------------------------|----------------------------|-------------------------------------|
| Formula | $\displaystyle \frac{X - \overline{X}}{\text{USL} - \text{LSL}}$ | $\displaystyle \frac{X - \overline{X}}{\sigma}$ using last 30 samples | $\displaystyle \frac{X - \overline{X}}{\sigma}$ using all prior samples (dynamic) |
| Limit dependency | Limits depend on **large historical lot data**. Requires time to establish. | Limits can be set **immediately** (e.g., 6σ). No need for long historical data. | Same as 2nd: can be set right away; no extensive history needed. |
| Start of comparison | Starts at **11th unit** onward (after first 10 Bin1 units). | Starts at unit **31+** (once 30 samples exist). | Start effectively from **2nd unit** onward. |
| Limit setting | Typically ±5%, ±10%, etc. **Subjective**, engineer‑defined. | **Always 6σ** (or configurable multiple); independent of personal judgment. | Same: limit expressed in σ; default 6σ; independent of personal judgment. |
| Sample size for statistics | Mean based on only **10 samples**, increasing risk of over‑rejection or poor estimation. | Uses **30 samples** for mean and standard deviation; more statistically sound. | Uses **all prior good data** for mean and σ; each new part refines the estimate. |
| Risk of rejecting non‑outliers | Higher, especially if distribution is wide; tails may be falsely accused. | Lower; denominator is σ, so outlier detection is sharper and tails of wide distributions are tolerated. | **Lowest**; continuously updated σ reflects true distribution, further reducing false rejects. |
| Dependency on spec limits | Strong: formula depends on $(\text{USL} - \text{LSL})$. Loose or wide specs weaken detection power. | None: formula independent of spec limits, based only on sample σ. | Same independence from spec limits; uses actual data distribution. |

> Note: If the test distribution is **wide (large σ)**:
> - Tails are less likely to be rejected (reducing over‑rejection).
>
> If the distribution is **narrow (small σ)**:
> - Test becomes more sensitive to any measurement outside the cluster (better outlier detection).

---

## 9. Conclusion

- The **Extreme Studentized Deviation (ESD)-based relative test** is more accurate in detecting outliers than the current (1st) relative test.
- Among the ESD-based approaches, the **latest method (Pseudo Dynamic / ESM)**:
  - Starts comparison from the **2nd unit**.
  - Continuously updates mean and σ as the lot progresses.
  - Makes the risk of under-rejection (over-acceptance of outliers) **very low**.  
- Unless the **very first unit** is itself an outlier (a highly remote scenario), the method is robust against both:
  - Under‑rejection (missed outliers).
  - Over‑rejection (false outliers).

---

## 10. Pre‑Requisites for Implementation

### 10.1 Distribution Requirements

- All relative test / outlier detection methodologies assumed here require the test measurement distribution to be **Gaussian (normal)**.
- Using these methods on **non‑Gaussian** populations (e.g., long‑tailed distributions) can cause:
  - Over-rejection.
  - Over-acceptance.

### 10.2 Distribution Transformation

If the native population is not Gaussian, prior transformation is required:

- Possible transformations:
  - **Box–Cox Transformation**
  - **Logarithmic Transformation**
  - **Johnson Transformation**
- This normalizing transformation is already considered in the **SPL limit setting** process.

### 10.3 Scope of Application

- Implement relative tests only for **selected critical tests**, not all available tests.
- Think like a **“sniper”** rather than a **“soldier with a machine gun”**:
  - Target a few high-impact parameters.
  - Avoid unnecessary complexity and data noise.

---

## 11. Generic Implementation Pattern (Algorithm)

Although the slides include tester-specific code (ETS800, Flex, A565, LTX, QT200, Hatina Strip test, T2000, J750), they all follow a **common pattern** for the ESM method:

### 11.1 Global Variables (Per Site / Per Test)

- Counters:
  - `good_counter` or `site_pass_no_counter` – number of parts that passed all tests so far.
- Running statistics:
  - $\overline{X}$ – running mean.
  - $S$ – running standard deviation (or variance).
- Optional:
  - Arrays/buffers to hold measurements used specifically for relative test logging.

### 11.2 Initialization (First Good Unit)

1. When the **first good unit** for that test is encountered:
   - Set:
     $$
     \overline{X}_1 = X_1
     $$
   - Initialize $S_1$ (e.g., to a very small positive value) to avoid division by zero later.
   - Set `good_counter = 1`.

### 11.3 For Each Subsequent Good Unit (n ≥ 2)

Given new measurement $X_n$:

1. **Compute updated mean**:

   $$
   \overline{X}_n =
   \left(1 - \frac{1}{n}\right)\overline{X}_{n-1}
   + \frac{1}{n} X_n
   $$

2. **Update variance/standard deviation** (conceptual):

   $$
   S_n^2 =
   \frac{n-2}{n-1} S_{n-1}^2
   + \frac{1}{n}(X_n - \overline{X}_{n-1})^2
   $$
   $$
   S_n = \sqrt{S_n^2}
   $$

   - If $S_n = 0$, assign a small default value to avoid divide-by-zero.

3. **Compute relative deviation**:

   $$
   D_n = \frac{X_n - \overline{X}_n}{S_n}
   $$

4. **Apply reject rule**:

   - If $|D_n| > L$ (typically $L = 6$), **reject** as outlier.
   - Else, **accept**:
     - Increment `good_counter`.
     - Save $\overline{X}_n$ and $S_n$ for the next iteration.

5. **Datalog**:
   - Log:
     - Raw measurement $X_n$.
     - Relative deviation $D_n$.
     - Pass/fail status against the relative test limit.

> The exact coding syntax and framework differ by platform (ETS800, Flex, A565, LTX, QT200, T2000, J750, etc.), but the statistical logic is common.

---

## 12. Tester‑Specific Implementation Notes (High Level)

### 12.1 ETS800

- **Global definition**
  - Define global variables for mean, sigma, counters.
- **Flow**
  1. Initialize mean & sigma for first unit.
  2. Calculate subsequent mean and sigma using incremental formulas.
  3. Special handling if 2nd unit has same reading as previous mean (avoid zero variance).
  4. Compute deviation (delta from mean over sigma).
  5. Compare against limit and datalog result.
  6. If unit passes:
     - Increment `site_pass_no_counter`.
     - Store old mean and sigma for next unit.

### 12.2 Flex

- **Steps**
  1. Initialize mean & sigma for first unit (e.g., in the setup or initialization section).
  2. Calculate subsequent mean and sigma.
  3. Add guard to avoid divide-by-zero when sigma is zero.
  4. Compute deviation (delta / sigma).
  5. Compare/datalog.
  6. Store mean & sigma for next iteration; increment pass counter.
  7. Define structures/variables in `OnProgramStarted`.

### 12.3 A565

- **Global definition**
- **Implementation**
  1. Declare and set **Relative test limit** (±6σ).
  2. Add relative test code inside `main()`.
  3. Initialize mean & sigma for first unit.
  4. Calculate subsequent mean and sigma.
  5. Guard logic for divide-by-zero.
  6. Compute deviation (delta / sigma).
  7. Compare / Datalog.
  8. Store old mean & sigma; increment `good_counter` if unit passes.

### 12.4 LTX

- **Global**
  1. Global definition of:
     - Test arrays.
     - Relative counters.
     - Number of pins per package.
  2. Code in `Prog_rev` procedure to initialize relative counters at lot start/reset.
- **Flow**
  3. Store test value into `rel_para` array (ensure `num_relative` dimension is sufficient).
  4. In relative test procedure:
     - Declare local variables (L1…LX, TT, etc.).
     - Declare matching in/out arrays in `float_test`.
  5. Perform relative test per site:
     - Initialize stats on first run.
     - Compute mean, stdev, and relative data.
     - If stdev is 0, assign default to avoid hang.
  6. Store previous mean & sigma; increment `good_counter` if unit passes.
     - Use relative limit (e.g., ±10σ), with logic matching the chosen threshold.
  7. Integration:
     - Either create a dedicated test block for relative test, or
     - Add the relative test method inside an existing test block (e.g., after JVT or End_Continuity).

### 12.5 QT200

- **Steps**
  1. Variable declaration.
  2. Store desired tests in an array:
     - `indx = 1` for first test, `indx++` for subsequent tests.
  3. Relative test calculation and datalogging.
  4. After reltest datalogging, store data **only if reltest passes**.

### 12.6 Hatina Strip Test

- **Steps**
  1. Variable declaration.
  2. Store tests in an array:
     - `testindx = 0` for first test, increment for subsequent tests.
  3. Initialize mean & sigma for first unit.
  4. Calculate subsequent mean and sigma.
  5. Handle 2nd unit with same reading as previous mean.
  6. Compute deviation (delta / sigma).
  7. Datalog relative test result.
  8. Store previous mean & sigma; increment `site_pass_no_counter` if unit passes.

### 12.7 T2000‑RDK

- **Steps**
  1. Initialize mean & sigma for first unit.
  2. Calculate subsequent mean & sigma.
  3. Compute deviation (delta / sigma).
  4. Compare & Datalog.
  5. Store old mean & sigma for next unit; increment `site_pass_no_counter` on pass.

### 12.8 T2000‑OTPL

- **Integration**
  1. Retrieve measured value from UV.
  2. Call ESM function from test class; datalog the final value.
  3. ESM function implemented in `.cpp` (often already available in existing test program).
     - Access via macros defined in `MacroDef`.
- **Calculation in `.cpp`**
  1. Initialize mean & sigma for first unit.
  2. Calculate subsequent mean and sigma.
  3. Compute deviation (delta / sigma).
  4. Compare & Datalog.
  5. Store previous mean & sigma; increment `site_pass_no_counter` on pass.

### 12.8A Practical T2000-RDK Implementation Lessons

The high-level RDK steps above are correct, but real implementations often add details that affect both behavior and validation.

#### State Management

- Keep ESM state **per site** and **per monitored parameter**.
- If a package supports multiple temperature or environment lists, keep the source test list and judge list selection explicit.
- Do not assume initialization in unrelated global setup functions clears ESM state.

#### Formula Verification Rule

- Always trust the **active code path** over comments or older commented alternatives.
- Some RDK implementations compute the z-value using **updated mean and updated sigma**.
- Others may intend a purely historical-stat comparison. Do not assume one variant from documentation alone.

#### Self-Inclusive Updated-Stat Algorithm vs Historical-Only Core Algorithm

Two similar but materially different execution models appear in real ESM implementations:

- **Historical-only core algorithm**

  $$
  z_n^{hist} = \frac{X_n - \bar{X}_{n-1}}{S_{n-1}}
  $$

  - Compare the current value only against previously accepted history.
  - If the part fails the relative limit, do not fold it into the stored statistics.
  - This is the cleaner textbook model for strict outlier screening.

- **Self-inclusive updated-stat algorithm**

  $$
  \bar{X}_n = \left(1 - \frac{1}{n}\right)\bar{X}_{n-1} + \frac{1}{n}X_n
  $$

  $$
  S_n = \sqrt{\frac{n-2}{n-1}S_{n-1}^2 + \frac{1}{n}(X_n - \bar{X}_{n-1})^2}
  $$

  $$
  z_n^{upd} = \frac{X_n - \bar{X}_n}{S_n}
  $$

  - Update mean and sigma first, then compute the relative value from the updated statistics.
  - This usually produces a more conservative score because the current sample partially pulls the mean toward itself and can widen sigma.
  - Production code may still add fallback handling such as `999` and persistence gates such as `±15`.

Practical interpretation:

- Both variants can work if the tester flow, judge limits, datalog, and replay logic all follow the same executed formula.
- When validating STDF CSV data, match the implementation actually running in the TP, not the cleaner theoretical variant.
- If comments claim historical-only behavior but replay matches the updated-stat path, document the implementation as a **self-inclusive updated-stat algorithm** rather than calling it mathematically wrong.

##### Self-Inclusive Updated-Stat Algorithm Details

Execution order per new sample:

1. Read the current measurement $X_n$.
2. Use the stored prior state $\bar{X}_{n-1}$, $S_{n-1}$, and count $n-1$.
3. Compute updated mean $\bar{X}_n$.
4. Compute updated sigma $S_n$.
5. Compute the relative result from the updated state:

  $$
  z_n^{upd} = \frac{X_n - \bar{X}_n}{S_n}
  $$

6. Apply fallback handling if the result is non-finite.
7. Apply judge limits to the computed relative result.
8. Persist updated history only if the implementation's storage rule allows it.

Behavioral characteristics:

- The current sample participates in the statistics that are used to judge itself.
- The relative result is usually smaller in magnitude than the historical-only form because the current sample pulls the mean toward itself and can increase sigma.
- This makes the method more self-damped and often more tolerant of marginal excursions.
- It is still a valid outlier-screening method as long as its limits, datalog interpretation, and replay model are matched to the executed formula.

Typical implementation add-ons:

- first-sample initialization with no comparison
- sigma-zero guard or epsilon substitution
- non-finite fallback values such as `999`
- history persistence gates such as `|z| < 15`
- reset logic tied to lot, mode, or retest context

What this algorithm is good at:

- production robustness when raw sigma can collapse early
- smooth behavior across accumulating lot history
- easier match to existing production code that already updates running stats before judgment

What to watch carefully:

- comments may still describe historical-only intent even when active code is self-inclusive
- replay or audit code must use the updated-stat execution order exactly
- reset ambiguity can make early visible CSV rows look inconsistent with clean-start replay
- limit behavior can differ noticeably from historical-only screening for small sample counts

#### Guard and Fallback Logic

- Review divide-by-zero protection explicitly.
- If the implementation sanitizes non-finite values to a fallback such as `999`, reproduce that exact behavior during analysis.
- If the implementation updates stored history only when the relative result remains inside a gate such as `±15`, preserve that gate in any replay or audit.

#### Single-Function Algorithm Toggle Pattern

When a TP team wants to compare the self-inclusive updated-stat algorithm and the historical-only core algorithm without maintaining two separate production functions, use a single compile-time toggle inside the live ESM function.

Recommended pattern:

```cpp
#define RELATIVE_ESM_USE_SELF_INCLUSIVE 1

...

#if RELATIVE_ESM_USE_SELF_INCLUSIVE
  // self-inclusive updated-stat branch
#else
  // historical-only core branch
#endif
```

Why this pattern is useful:

- only one live function symbol is exposed to the test flow
- shared steps stay outside the branch and are less likely to drift
- the algorithm choice is changed in one obvious place
- users do not need to rename functions or uncomment large blocks to compare behavior

What should stay shared outside the toggle when possible:

- latest-result fetch
- first-device initialization structure
- fallback sanitization such as `999`
- judge calls
- persistence gate handling such as `|z| < 15`
- temporary-value cleanup

Implementation caution:

- document which branch is the current production default
- keep the branch names algorithm-based, not platform-based
- if the historical-only branch is added later into an existing self-inclusive implementation, revalidate replay alignment and judge behavior before promoting it as default

#### Reset Behavior

- ESM reset must be explicit and auditable.
- If a reset helper exists, confirm where it is actually called in flow.
- If reset is keyed only to lot ID, mode code, or retest code, same-context transitions can preserve history unexpectedly.
- When a datalog or CSV starts with nonzero relative values on the first visible sample for a site, treat missing reset context as a first-class explanation.

#### Flow Placement

- Keep ESM after the main screening sequence for that flow step.
- Update stored history only for parts that are still considered valid for relative accumulation according to the implementation.

#### Validation Strategy

- When exported STDF CSVs are available, replay the TP algorithm against the CSV instead of relying only on visual spot checks.
- Use the `Tests#` row to map source test IDs and judge IDs to columns.
- Replay the algorithm in file order, per site, with the exact formula, fallback logic, and history gating used by the TP.
- Treat early large mismatches as either:
  - formula mismatch
  - list mismatch
  - reset/history carryover
  rather than assuming the CSV is wrong.

#### 25x Same-Unit Workbook Integrity Check

When broad production-style sample history is not available, but a user can collect about 25 consecutive loop results from the same unit, use the workbook-based integrity check before concluding that the TP ESM math is correct.

Use this fallback when:

- accuracy still matters, but only same-unit loop data is available
- the team can capture about 25 repeated results for one source test and its relative judge output
- the goal is to verify that TP code and workbook math agree, not to prove final production robustness across many units

Known reference inputs:

- historical workbook filename: `references/ESM_RELATIVE_TEST_DATA_INTEGRITY_CHECK.xlsx`
- current workspace note: the workbook is not retained locally; use this section as the method description and supply a local workbook copy if you need the old worksheet flow

Worksheet roles inside the workbook:

- `Relative Test Validation Exampl` is the worked reference sheet that already contains example `Test 1` and `Relative Test 1` loop data
- `Relative Test Validation File` uses the same calculation area and formula pattern, but is the template-style sheet to populate with captured loop data

First-run interpretation in the workbook:

- the first source-test loop is initialization only
- the integrity check takes the meaningful relative-test value starting on the second run
- in the worked example, column `B` starts at loop 1 while column `C` becomes meaningful from loop 2 onward
- therefore validation should not treat the first loop's relative output as a normal compared sample

What the workbook checks:

- source measurement column (`Test 1`)
- TP-produced relative result column (`Relative Test 1`)
- sample-inclusion decision (`Test 1 to be included`)
- cumulative mean and sigma
- recomputed deviation and pass/fail status
- delta between workbook-computed deviation and TP output
- final verdict in `Test Code correct?`

Representative workbook logic:

- include a sample only when the workbook's deviation gate passes
- recompute cumulative average and sigma from the included series
- recompute the relative deviation from that running state
- compare TP output versus workbook output using a small delta tolerance

Representative formulas from the workbook:

```excel
D3 = IF($C3<>"",IF(ABS(G3)<6,B3,""),"")
E3 = IF($C3<>"",IF(AND(C3<>"",ABS(AVERAGE($B$2:B3)-B3)/STDEV(B2:B3)<6),AVERAGE($B$2:B3),E2),"")
F3 = IF($C3<>"",IF(AND($C3<>"",(ABS(AVERAGE($B2:$B3)-$B3)/STDEV($B2:$B3))<6),STDEV($B$2:$B3),F2),"")
G3 = IF($C3<>"",(B3-E3)/F3,"")
K3 = IF($C3<>"",($B3-$I3)/$J3,"")
L3 = IF($C3<>"",C3-K3,"")
M3 = IF($C3<>"",IF(ABS(L3)>0.002,"INCORRECT","CORRECT"),"")
```

Interpretation:

- if the 25x loop rows stay `CORRECT` and the deviation delta stays within the workbook tolerance, the TP implementation matches the workbook formula for that same-unit dataset
- if the workbook shows `INCORRECT`, inspect formula order, inclusion gate, sigma handling, fallback behavior, and any mismatch between the TP's active algorithm and the workbook's intended algorithm
- this workbook check is a fallback integrity method, not a replacement for ordered STDF/CSV replay across real production history
- remember that the first loop is the history seed; comparison effectively starts from the second run

Automation note:

- when many relative-test pairs must be checked, do not scale this by manually pasting 200 columns into Excel
- instead, use `.claude/skills/relative_test_esm_stdf_csv_validator/relative_test_esm_stdf_csv_validator.py` in bulk loop mode with one wide CSV/XLSX containing all source and judge columns
- UR84-style tester datalog TXT files can also be used directly when they contain repeated sample blocks plus both the source test and `RelTest_*` lines
- the bulk loop mode reproduces the worksheet-style `D:M` logic across all mapped pairs and reports which pairs stay `CORRECT` or become `INCORRECT`
- direct TXT parsing only proves that the capture is readable; if the resulting deltas are consistently off, verify that the log starts at the intended clean loop boundary and not mid-history

#### STDF CSV Replay Validation Pattern

When a user asks whether exported `RelTest_*` judge values are mathematically correct, use a direct replay of the active TP algorithm against STDF-extracted CSV data.

##### Problem Shape

Use this validation approach when:

- a T2000 RDK TP implements ESM or relative testing in code
- STDF-extracted CSVs contain per-part measurement data
- the user wants proof that exported judge values follow the active TP formula
- it is unclear whether mismatch comes from formula drift, list mapping, missing state, or CSV interpretation

Typical required inputs:

- the active TP implementation file
- the testID to judgeID mapping headers
- at least one STDF CSV containing both source test columns and exported `RelTest_*` columns

##### Replay Procedure

1. Read the active ESM implementation.
2. Extract the active testID and judgeID arrays from the TP headers.
3. Load the CSV from the `Parameter` row onward.
4. Use the `Tests#` row to find the column index for each source test and each judge ID.
5. Iterate `PID-*` rows in file order.
6. Maintain mean, sigma, and count independently for each site and each pair.
7. Recompute the expected relative value exactly as the code does.
8. Compare recomputed value versus exported CSV value.
9. Sort pairs by worst absolute error.
10. Spot-check the first visible sample per site for representative pairs.

##### Replay Rules That Matter

- Replay the active code path, not comments or historical variants.
- Map by `Tests#`, not by column name alone.
- Keep independent running state per site.
- Copy first-sample, fallback, and history-gating rules exactly.
- If a reset helper exists, review where it is actually called before deciding the CSV is wrong.

##### Interpretation Rules

- If errors are near CSV rounding scale across the full set, the export aligns with TP math.
- If large errors appear immediately on first visible site samples and those first visible relative values are already nonzero, the export probably starts mid-history.
- If one environment mismatches while another matches, inspect reset-path behavior before blaming formula drift.
- If a reset helper exists but no visible flow call is found, treat history carryover as a live hypothesis.

##### Common Failure Modes

- mapping by human-readable column name instead of `Tests#`
- mixing sites into one running state
- replaying a commented or older formula instead of the active code path
- ignoring `999` or other fallback behavior
- ignoring update gates such as `±15`
- assuming the CSV begins at a true reset boundary

##### Validation Checklist

- [ ] Active implementation file is identified
- [ ] Source and judge ID arrays are extracted from TP headers
- [ ] CSV `Tests#` row is used for mapping
- [ ] Replay is site-aware
- [ ] First-sample behavior matches TP code
- [ ] Non-finite fallback behavior is reproduced
- [ ] History update gate is reproduced
- [ ] Worst mismatches are summarized by pair, site, and part
- [ ] First visible samples are inspected before declaring a CSV invalid
- [ ] Reset path is reviewed in source when mismatch persists

##### Reusable Implementation Note

The concrete helper produced during analysis is:

- `.claude/skills/relative_test_esm_stdf_csv_validator/relative_test_esm_stdf_csv_validator.py`

Reuse it as a starting point, but recheck the following for each TP family:

- symbol names of the test and judge ID arrays
- exact first-sample rule
- exact sigma update math
- fallback and gating thresholds
- reset trigger conditions

### 12.9 J750

- **Relative Test Module**

  1. **Constants declaration**:
     - Saved variables for statistics.
     - Test number offset.
     - Number of pins tested per device/package.

  2. **`Init_RelTests` (Executed during `OnProgramValidation`)**:
     - Initialize relative test parameters and variables.
     - `NumOfPartsToSkip_RT`:
       - Relative test executed only after a certain number of parts (e.g., 100) to ensure stable statistics.
     - Create test arrays for:
       - Tests with multiple pins.
       - Tests with a single pin.
     - Define test number offsets and pin counts per package.

  3. **`StartIntercept_RT` (Called in `StartOfBody`)**:
     - Begin capturing measured values.
     - Save data per site.

  4. **`ReadIntercept_RT` (Called in `EndOfBody`)**:
     - Read back measured values.
     - On first measurement:
       - Initialize arrays with measured values, pin names, and channels.
     - For each subsequent measurement:
       - Save measured values and channels in arrays for future parts.
     - Stop capturing when done.

  5. **`ProcessAndDatalog_RT`**:
     - Called at the end of flow to:
       - Process relative test statistics.
       - Datalog relative test results.
       - Update statistics only if the part is otherwise good.

---

Below is a **complete, reusable core implementation** of the Pseudo Dynamic ESD (ESM) relative test, plus **template code for each tester platform**.  

## 1. Core Algorithm (ESM / Pseudo Dynamic ESD)

This section is a **generic reference template** for ESM coding.

- It is intentionally kept as the cleaner historical-only core algorithm.
- It is **not** a claim that every production implementation uses this exact execution order.
- Some production implementations use a different but internally consistent computation model, such as the **self-inclusive updated-stat algorithm** described earlier in this note.
- Keep the template as a reusable reference unless the target program explicitly requires a different executed formula.

We maintain **running statistics** per (site, test parameter):

- Sample count $n$
- Mean $\overline{X}_n$
- Variance via Welford’s method (accumulator $M_2$)

For each **new candidate good unit** (i.e., after all functional tests pass):

1. If $n$ is too small (e.g., $n < 2$ or your chosen warmup count), **do not apply** relative test yet:
   - Accept the unit.
   - Update statistics with its measurement.

2. Otherwise:
   - Compute sample standard deviation:
     $$
     \sigma = \sqrt{\frac{M_2}{n-1}}
     $$
   - If $\sigma$ is $0$ (or extremely small), skip relative decision (or use epsilon) to avoid divide by zero.
   - Compute standardized deviation (z‑score):
     $$
     z = \frac{X_\text{current} - \overline{X}_n}{\sigma}
     $$
   - If $\lvert z \rvert > L$ (e.g. $L = 6$), **reject** as outlier (do not update stats).
   - Else:
     - Accept the unit.
     - Update mean and $M_2$ (and thereby $\sigma$) with the new value.

This effectively compares each unit to the global statistics of **all previously accepted units**.

---

## 5. Tester Platform Templates

### 5.1 ETS800 (by Ong Chien Hoon) --- !!! UNVERIFIED !!! ---

Algorithm label: historical-only core algorithm.

```c
/* Global definitions (e.g., in a shared header or global section) */
#define MAX_SITES   8
#define MAX_RT_TEST 32

typedef struct {
    RelativeTestState state;
    int initialized;
} RtPerTest;

RtPerTest rt_table[MAX_SITES][MAX_RT_TEST];

/* Called at program start or new lot */
void RelTest_GlobalInit(void) {
    for (int site = 0; site < MAX_SITES; ++site) {
        for (int t = 0; t < MAX_RT_TEST; ++t) {
            rt_init(&rt_table[site][t].state);
            rt_table[site][t].initialized = 1;
        }
    }
}

/*
 * Called after full test flow for a device, for the
 * specific test index rt_idx and site index site_id.
 *
 * `value` is the DUT reading for the selected parameter.
 * `dev_is_good` is true only if ALL previous tests passed.
 */
void RelTest_Execute(int site_id, int rt_idx,
                     double value, int dev_is_good)
{
    if (!dev_is_good) {
        /* Do not include failing parts in relative stats */
        return;
    }

    RtPerTest *rt = &rt_table[site_id][rt_idx];

    double z;
    int pass_rel = rt_check(&rt->state, value,
                            6.0,  /* limit_sigma */
                            2,    /* min_samples_before_test */
                            &z);

    /* Datalog: pseudo calls, replace with ETS800 apis */
    ETS800_LogDouble("RT_Z", z, site_id);
    ETS800_LogBool("RT_PASS", pass_rel, site_id);

    if (!pass_rel) {
        /* Mark as relative-test fail / bin as outlier */
        ETS800_SetFailFlag(site_id, "REL_TEST_FAIL");
    }
}
```

Hook `RelTest_Execute` **after the last test** for this device, only for good devices.

---

### 5.2 Flex (by Teck Kiong Foo)

Algorithm label: self-inclusive updated-stat algorithm.

```vb
Public Function TO1_RelativeTest() As Long
On Error GoTo errHandler
    Dim index As Integer
    Dim No_of_test As Integer
    Dim SiteNum As Variant
    Dim calc_rel As New SiteBoolean
    ' Public RelativeBin1Counter(0) As New SiteDouble        'Must declare as global variable
    ' Public mean(100) As New SiteDouble                     'Must declare as global variable
    ' Public mean_old(100) As New SiteDouble                 'Must declare as global variable
    ' Public sigma(100) As New SiteDouble                    'Must declare as global variable
    ' Public sigma_old(100) As New SiteDouble                'Must declare as global variable
    ' Public aaa(100) As New SiteDouble                      'Must declare as global variable
    ' Public bbb(100) As New SiteDouble                      'Must declare as global variable
    ' Public relative_delta(100) As New SiteDouble           'Must declare as global variable
    ' Public Store1(100) As New SiteDouble                   'Must declare as global variable <- parameters to be evaluated in ESM

    No_of_test = 51                                          'Need to declare how many tests are evaluated in ESM
    '########################################################
    For Each SiteNum In TheExec.Sites.Active
        index = 0

        For index = 0 To No_of_test
            If (RelativeBin1Counter(SiteNum) = 0) Then
                ' initialize mean & sigma for first good unit
                mean(index)(SiteNum) = Store1(index)(SiteNum)
                sigma(index)(SiteNum) = 0
            Else
                ' calculate subsequent mean & sigma
                mean(index)(SiteNum) = ((1 - (1 / (RelativeBin1Counter(SiteNum) + 1))) * mean_old(index)(SiteNum)) _
                                      + ((1 / (RelativeBin1Counter(SiteNum) + 1)) * Store1(index)(SiteNum))
                aaa(index)(SiteNum) = ((RelativeBin1Counter(SiteNum) - 1) / RelativeBin1Counter(SiteNum)) * (sigma_old(index) ^ 2)
                bbb(index)(SiteNum) = ((Store1(index)(SiteNum) - mean_old(index)(SiteNum)) ^ 2) / (RelativeBin1Counter(SiteNum) + 1)
                sigma(index)(SiteNum) = (aaa(index)(SiteNum) + bbb(index)(SiteNum)) ^ (0.5)
            End If
        Next index

        For index = 0 To No_of_test      ''' to cater for divide by 0 error
            If (sigma(index)(SiteNum) = 0) Then
                relative_delta(index)(SiteNum) = 0 ' Needed to avoid divide by zero error
            Else
                ' calculate deviation (delta / sigma)
                relative_delta(index)(SiteNum) = (Store1(index)(SiteNum) - mean(index)(SiteNum)) / sigma(index)(SiteNum)
            End If
        Next index
    Next SiteNum

    For index = 0 To No_of_test ' compare datalog
        Call TheExec.Flow.TestLimit(resultval:=relative_delta(index), forceresults:=tlForceFlow)  'TK-Datalogging
    Next index

    For Each SiteNum In TheExec.Sites.Active
        RelativeBin1Counter(SiteNum) = RelativeBin1Counter(SiteNum) + 1 '<- only be executed if all relative tests are passed
        index = 0
        For index = 0 To No_of_test
            If (relative_delta(index)(SiteNum) < 6) Then
                ' store mean & sigma for next unit
                sigma_old(index)(SiteNum) = sigma(index)(SiteNum)
                mean_old(index)(SiteNum) = mean(index)(SiteNum)
            End If
        Next index
        relative_delta(0)(SiteNum) = 0
    Next SiteNum

    '########################################################

    Exit Function
errHandler:
    If AbortTest Then Exit Function Else Resume Next
End Function
```

Define in OnProgramStarted:
```vb
'======================== OnProgramStarted ========================
Function OnProgramStarted() As Long
    If (TheExec.Datalog.setup.LotSetup.DeviceNumber = 1) Then   'TK- Only run once at first device
        RelativeBin1Counter(0) = 0    'Site0
        RelativeBin1Counter(1) = 0    'Site1
        RelativeBin1Counter(2) = 0    'Site2
        RelativeBin1Counter(3) = 0    'Site3
    End If

    Exit Function
errHandler:
    HandleExecIPError "OnProgramStarted"
End Function
```
---

### 5.3 A565 (by Eng Hui Law)

Algorithm label: historical-only core algorithm.

Assume a C‑like program with main() and per‑test code.

```c
/* Global definition */
RelativeTestState rt_state_testY[MAX_SITES];

/* On lot start */
void Init_RelativeTest(void) {
    for (int s = 0; s < num_sites; ++s) {
        rt_init(&rt_state_testY[s]);
    }
}

/* In main test flow, after Test Y & all other tests passed */
void Do_TestY_Relative(int site, double value_testY, int dev_is_good) {
    if (!dev_is_good) return;

    double z;
    int pass_rel = rt_check(&rt_state_testY[site],
                            value_testY,
                            6.0,
                            2,
                            &z);

    A565_DatalogDouble("TestY_RT_Z", z, site);
    A565_DatalogBool("TestY_RT_PASS", pass_rel, site);

    if (!pass_rel) {
        A565_Fail(site, "REL_TEST_FAIL");
    }
}
```

---

### 5.4 LTX (by Glennpili Delacruz) --- !!! UNVERIFIED !!! ---

Algorithm label: historical-only core algorithm.

Here you likely have arrays per test and per pin; below is generic logic per parameter per site.

```c
#define MAX_LTX_SITES 8
#define MAX_REL_PARA  32

RelativeTestState ltx_rt_state[MAX_LTX_SITES][MAX_REL_PARA];

/* Initialization, e.g. in Prog_rev or on new lot */
void LTX_Init_Relative(void) {
    for (int site = 0; site < MAX_LTX_SITES; ++site) {
        for (int p = 0; p < MAX_REL_PARA; ++p) {
            rt_init(&ltx_rt_state[site][p]);
        }
    }
}

/* Relative test procedure, called per site/parameter */
void LTX_Do_Relative(int site, int para_idx,
                     double value, int dev_is_good,
                     double limit_sigma)
{
    if (!dev_is_good) return;

    RelativeTestState *s = &ltx_rt_state[site][para_idx];
    double z;
    int pass_rel = rt_check(s, value,
                            limit_sigma, /* e.g., 6.0 or 10.0 */
                            2,
                            &z);

    /* Avoid divide-by-zero already handled in rt_check */

    LTX_Datalog("Rel_Z", z, site, para_idx);
    LTX_Datalog("Rel_Pass", pass_rel, site, para_idx);

    if (!pass_rel) {
        LTX_FailDevice(site, para_idx, "REL_TEST_FAIL");
    }
}
```

Can integrate this:
- Either as a dedicated test block for relative test, or
- As additional method inside existing block (e.g., after JVT / End_Continuity).

---

### 5.5 QT200 (by Nurul Jannah Mahmood) --- !!! UNVERIFIED !!! ---

Algorithm label: historical-only core algorithm.

Basic array‑based approach.

```c
#define MAX_QT_SITES  8
#define MAX_QT_TESTS  32

RelativeTestState qt_rt_state[MAX_QT_SITES][MAX_QT_TESTS];

/* Called once per lot or on start */
void QT_Init_Relative(void) {
    for (int s = 0; s < num_sites; ++s) {
        for (int t = 0; t < MAX_QT_TESTS; ++t) {
            rt_init(&qt_rt_state[s][t]);
        }
    }
}

/* For each "indexed" test that we want to include in relative test */
void QT_Do_Relative(int site, int test_index,
                    double value, int dev_is_good)
{
    if (!dev_is_good) return;

    double z;
    RelativeTestState *st = &qt_rt_state[site][test_index];

    int pass_rel = rt_check(st, value,
                            6.0,
                            2,
                            &z);

    QT_DatalogDouble(site, test_index, "Rel_Z", z);
    QT_DatalogBool(site, test_index, "Rel_Pass", pass_rel);

    if (!pass_rel) {
        QT_FailDevice(site, test_index, "REL_TEST_FAIL");
    }
}
```

---

### 5.6 Hatina Strip Test (by William Lim CW) --- !!! UNVERIFIED !!! ---

Algorithm label: historical-only core algorithm.

Very similar to QT200; the main difference is indexing.

```c
#define MAX_STRIP_SITES  8
#define MAX_STRIP_TESTS  64

RelativeTestState strip_rt_state[MAX_STRIP_SITES][MAX_STRIP_TESTS];

/* Initialization */
void Strip_Init_Relative(void) {
    for (int s = 0; s < num_sites; ++s) {
        for (int t = 0; t < MAX_STRIP_TESTS; ++t) {
            rt_init(&strip_rt_state[s][t]);
        }
    }
}

/* Called after parameter is measured and device is good */
void Strip_RelativeTest(int site, int test_index,
                        double value, int dev_is_good)
{
    if (!dev_is_good) return;

    RelativeTestState *st = &strip_rt_state[site][test_index];
    double z;
    int pass_rel = rt_check(st, value,
                            6.0,
                            2,
                            &z);

    Strip_Datalog("Rel_Z", z, site, test_index);
    Strip_Datalog("Rel_Pass", pass_rel, site, test_index);

    if (!pass_rel) {
        Strip_MarkOutlier(site, test_index);
    }
}
```

---

### 5.7 T2000‑RDK (by Tan Yunde)

Algorithm label: self-inclusive updated-stat algorithm.

```c++
TESTFUNCTION
void Relative_ESM(const OASIS::OFCString & /*parameter_string*/,AT::RsltAllDUTCtnr & result)
{
    dlgout << "<Relative_ESM>" << endl;

    int    index;
    double dbRelativeBin1Count   = 0;
    double dbRelativeBin1CountP1 = 0;
    double dbMeanOld             = 0;
    double dbMeasurementNow      = 0;
    double dbPart1MeanOld        = 0;
    double dbPart1MeanNow        = 0;
    double dbSigmaOld            = 0;
    double dbSigmaNow            = 0;
    double dbDelta_now           = 0;

    DUT_LOOP(ACTIVE)
    {
        for (index = 0; index < 146; ++index)
        {
            // 1) Initialize mean & sigma for first unit
            if (RelativeBin1Counter[GET_DUT()] == 0)
            {
                mean[GET_DUT()][index]           = Store1[GET_DUT()][index];
                sigma[GET_DUT()][index]          = 0.0;
                relative_delta[GET_DUT()][index] = 0.0;
            }
            else
            {
                // 2) Calculate subsequent mean and sigma
                dbRelativeBin1Count   = RelativeBin1Counter[GET_DUT()];
                dbRelativeBin1CountP1 = dbRelativeBin1Count + 1.0;

                dbMeanOld        = mean_old[GET_DUT()][index];
                dbMeasurementNow = Store1[GET_DUT()][index];

                dbPart1MeanOld = ((1 - (1 / dbRelativeBin1Count)) * dbMeanOld);
                dbPart1MeanNow = ((1  / dbRelativeBin1CountP1) * dbMeasurementNow);
                mean[GET_DUT()][index] = dbPart1MeanOld + dbPart1MeanNow;

                // --- sigma update (incremental) ---
                // reconstruct M2_old from sigma_old and n
                dbRelativeBin1CountN1 = RelativeBin1Counter[GET_DUT()] - 1;
                dbSigmaOld = sigma_old[GET_DUT()][index];
                aaa[GET_DUT()][index] = (dbRelativeBin1CountN1 / dbRelativeBin1Count) * (dbSigmaOld * dbSigmaOld);
                bbb[GET_DUT()][index] = ((dbMeasurementNow - dbMeanOld) * (dbMeasurementNow - dbMeanOld)) / dbRelativeBin1CountP1;

                if (bbb[GET_DUT()][index] == 0) bbb[GET_DUT()][index] = 1.0e-15;
                sigma[GET_DUT()][index] = sqrt((aaa[GET_DUT()][index] + bbb[GET_DUT()][index]));
                dbSigmaNow = sigma[GET_DUT()][index];

                // 3) Calculate deviation/delta from mean over sigma
                dbDelta_now = Store1[GET_DUT()][index] - mean[GET_DUT()][index];
                relative_delta[GET_DUT()][index] = (dbDelta_now / dbSigmaNow);
            }
        }
    }

    // 4) Compare / Datalog results
    result |= rdk::JUDGE(2200648, relative_delta.getElement(4));
    REJECT_FAIL_DUT_AND_RETURN_IF_NO_ACTIVE(result);

    // 5) Store old mean & old sigma for next unit iteration.
    //    Increment RelativeBin1Counter (site_pass_no counter) if unit passes.
    DUT_LOOP(ACTIVE)
    {
        RelativeBin1Counter[GET_DUT()] = RelativeBin1Counter[GET_DUT()] + 1;

        for (index = 0; index < 146; ++index)
        {
            if (relative_delta[GET_DUT()][index] < 6)
            {
                sigma_old[GET_DUT()][index] = sigma[GET_DUT()][index];
                mean_old [GET_DUT()][index] = mean [GET_DUT()][index];
            }
            // reset delta for next device
            relative_delta[GET_DUT()][index] = 0;
        }
    }
}
```

---

### 5.8 T2000‑OTPL (by Tan Yunde)

Algorithm label: self-inclusive updated-stat algorithm.

```lua
# ESM function (in .cpp) is already built in some device XXX_CalcAndJudge_Test specific test class.
# Just need to retrieve/copy from existing TP which has ESM function.
Test UAx9_Miscellaneous_Test Relative_Misc
{
    ${[ UserVarsToMeasVal(Leak_Drivers_UV.OUT12_IQHL_DIFF , OUT12_IQHL_DIFF ) ]} # Retrieve value measured from UV
    ${[ UserVarsToMeasVal(Leak_Drivers_UV.OUT14_IQHL_DIFF , OUT14_IQHL_DIFF ) ]}
    ${[ UserVarsToMeasVal(Leak_Drivers_UV.OUTHS_IQHL_DIFF , OUTHS_IQHL_DIFF ) ]}
    ${[ UserVarsToMeasVal(Leak_Drivers_UV.OUT6_IQHL_DIFF  , OUT6_IQHL_DIFF  ) ]}
}

Test UAx9_CalcAndJudge_Test Relative_Judge
{
    FailStopMode  = FailStop;

    #                       TestID  Func  Value             Description           HLimit  LLimit  Unit   Scale BranchStatus
    ${[ CalcJudgeIMV      ( 110000, COPY, Alarm                                                                   ) ]}
    ${[ CalcJudgeIMV_Unit ( 112720, Esm,  OUT12_IQHL_DIFF , "Iqlh012_DIFF_Sigma ", 6.000, -6.000, sigma, NONE, 57 ) ]}
    ${[ CalcJudgeIMV_Unit ( 112721, Esm,  OUT14_IQHL_DIFF , "Iqlh014_DIFF_Sigma ", 6.000, -6.000, sigma, NONE, 57 ) ]}
    ${[ CalcJudgeIMV_Unit ( 112722, Esm,  OUTHS_IQHL_DIFF , "Iqlh0HS_DIFF_Sigma ", 6.000, -6.000, sigma, NONE, 57 ) ]}
    ${[ CalcJudgeIMV_Unit ( 112723, Esm,  OUT6_IQHL_DIFF  , "Iqlh06_DIFF_Sigma  ", 6.000, -6.000, sigma, NONE, 57 ) ]}
}
# definition declared in MacroDef
$define CalcJudgeIMV_Unit(TestId, Func, MVall, Desc, UnitStr, Scale, BranchNo) {
    CalcAndJudgeParam { TestID   = TestId, CalcFunc = "Func", MeasValue= {"MVall"}, TestDesc = Desc,
                        LLimit   = "_LimitSets._$+TestId$+_LL", ULimit   = "_LimitSets._$+TestId$+_UL", UnitScale= VFS_$+Scale, BranchStatus = BranchNo }
}
```

```cpp
// Calculation in .cpp
ValDUT Judge_Test::Esm( void )
{
    if (getMeasValueCount() != 1)
        TC_ERROR_JTParamCntWrong("Esm", "1", OFCString::toString(getMeasValueCount()));

    ValDUT relative_delta_all = 0.0;
    ValDUT currentMeas = getMeasValue();
    EsmInfo_t& currentEsmInfo = m_EsmInfo[m_currentEsmIndex];

    for(ItrDUTs dutitr(DUT_ACTIVE); !dutitr.isDone(); dutitr++) //loop over DUTs
    {
        double     store1        = currentMeas[*dutitr];
        ValPerDUT& bin1cnt       = currentEsmInfo.m_passCount[*dutitr];
        double     bin1cntDbl    = bin1cnt.getAsDouble();
        ValPerDUT& mean_old      = currentEsmInfo.m_previousMean[*dutitr];
        ValPerDUT& sigma_old     = currentEsmInfo.m_previousSigma[*dutitr];
        ValPerDUT& mean          = currentEsmInfo.m_updatedMean[*dutitr];
        ValPerDUT& sigma         = currentEsmInfo.m_updatedSigma[*dutitr];
        ValPerDUT& relative_delta= relative_delta_all[*dutitr];

        if(currentEsmInfo.m_passCount[*dutitr].getAsInt() == 0)
        {
            // initialize mean & sigma for first unit
            mean  = store1;
            sigma = 0.0;
        }
        else
        {
            // calculate subsequent mean and sigma
            mean = ((1.0 - (1.0 / (bin1cntDbl + 1.0)))) * mean_old
                 + ((1.0 / (bin1cntDbl + 1.0)) * store1);
            double aaa = ((bin1cntDbl - 1.0) / bin1cntDbl) * pow(sigma_old, 2.0);
            double bbb = (pow(store1 - mean_old, 2.0)) / (bin1cntDbl + 1.0);
            sigma = pow(aaa + bbb, 0.5);
        }

        // calculate deviation/delta from mean over sigma
        if(sigma == 0.0)
            relative_delta = 0.0;
        else
            relative_delta = (store1 - mean) / sigma;

        if(isDumpDebugInfo())
        {
            dlgout << "###### Information for Esm calculation for DUT " << dutitr.getName() << " #######" << endl;
            dlgout << "   Current measurement = " << store1 << endl;
            dlgout << "   Mean                = " << mean << endl;
            dlgout << "   Sigma               = " << sigma << endl;
            dlgout << "   Relative delta      = " << relative_delta << endl;
        }
    }

    return(relative_delta_all);
}

ValDUT
Judge_Test::calculateRslt (OASIS::OFCString CalcFunc, bool &calculationDone)
{
    calculationDone = true;
    ValDUT result;
    unsigned int measValueCount = getMeasValueCount();

    if( !CalcFunc.icompare("copy") )
    {
        if (measValueCount != 1)
        {
            TC_ERROR_JTParamCntWrong("copy", OFCString::toString(1), OFCString::toString(measValueCount));
        }

        result = getMeasValue(0);
    }
    // compare result from datalog
    else if(!CalcFunc.icompare("Esm")) { result = Esm(); }
    else
    {
        calculationDone = false;
        result = -999.9;
    }

    return result;
}

void
Judge_Test::postCalculate()
{
    if(m_calcAndJudgeParam[m_paramSet].CalcFunc != "Esm")
        return;

    EsmInfo_t& currentEsmInfo = m_EsmInfo[m_currentEsmIndex];
    for(ItrDUTs dutitr(m_rsltJudge.getPassedDUTs()); !dutitr.isDone(); dutitr++) //loop over DUTs
    {
        ValPerDUT& bin1cnt   = currentEsmInfo.m_passCount[*dutitr];
        ValPerDUT& mean_old  = currentEsmInfo.m_previousMean[*dutitr];
        ValPerDUT& sigma_old = currentEsmInfo.m_previousSigma[*dutitr];
        ValPerDUT& mean      = currentEsmInfo.m_updatedMean[*dutitr];
        ValPerDUT& sigma     = currentEsmInfo.m_updatedSigma[*dutitr];

        bin1cnt   = bin1cnt + 1; // increment pass counter
        // store old mean & old sigma for next unit iteration
        sigma_old = sigma;
        mean_old  = mean;
    }

    // Increment index for next Esm
    m_currentEsmIndex++;
}
```

---

### 5.9 J750 (by Giovanni Marsoni, IG‑XL‑style VB) --- !!! UNVERIFIED !!! ---

Algorithm label: historical-only core algorithm.

IG‑XL uses a VB‑like language. Below is **VB‑style pseudo‑code** we can adapt inside the Relative Test module.

```vb
' Global variables (module level)
Private Type RelativeTestState
    n    As Long
    mean As Double
    M2   As Double
End Type

Private RtState() As RelativeTestState   ' dimension per test/pin/site
Private Const RT_LIMIT_SIGMA As Double = 6#
Private Const RT_MIN_SAMPLES  As Long   = 2
Private Const RT_EPS          As Double = 1E-12

Public Sub Init_RelTests()
    Dim site As Long, t As Long
    ReDim RtState(NumSites - 1, NumRelTests - 1)
    For site = 0 To NumSites - 1
        For t = 0 To NumRelTests - 1
            Call RT_InitState(RtState(site, t))
        Next t
    Next site
End Sub

Private Sub RT_InitState(ByRef s As RelativeTestState)
    s.n = 0
    s.mean = 0#
    s.M2 = 0#
End Sub

Private Function RT_Sigma(ByRef s As RelativeTestState) As Double
    If s.n < 2 Then
        RT_Sigma = 0#
        Exit Function
    End If
    Dim variance As Double
    variance = s.M2 / CDbl(s.n - 1)
    If variance <= 0# Then
        RT_Sigma = 0#
    Else
        RT_Sigma = Sqr(variance)
    End If
End Function

Private Sub RT_UpdateStats(ByRef s As RelativeTestState, ByVal x As Double)
    s.n = s.n + 1
    Dim delta As Double, delta2 As Double
    delta = x - s.mean
    s.mean = s.mean + delta / CDbl(s.n)
    delta2 = x - s.mean
    s.M2 = s.M2 + delta * delta2
End Sub

' Returns: pass_fail (True/False) and zscore
Private Function RT_Check(ByRef s As RelativeTestState, _
                          ByVal x As Double, _
                          ByVal limit_sigma As Double, _
                          ByVal min_samples As Long, _
                          ByRef zscore As Double) As Boolean

    Dim sigma As Double
    zscore = 0#
    Dim passed As Boolean
    passed = True

    If s.n >= min_samples Then
        sigma = RT_Sigma(s)
        If sigma > RT_EPS Then
            zscore = (x - s.mean) / sigma
            If Abs(zscore) > limit_sigma Then
                passed = False
            End If
        End If
    End If

    If passed Then
        Call RT_UpdateStats(s, x)
    End If

    RT_Check = passed
End Function
```

Then in **interpose functions**:

```vb
' Called in StartOfBody to start capturing values
Public Function StartIntercept_RT() As Long
    ' existing logic to enable capturing
End Function

' Called in EndOfBody to read captured values
Public Function ReadIntercept_RT() As Long
    ' existing logic to store measured data by site/pin/test
End Function

' Called after the flow to process & datalog relative test per part/site
Public Function ProcessAndDatalog_RT() As Long
    Dim site As Long, testIdx As Long
    Dim x As Double, z As Double
    Dim goodPart As Boolean, passRel As Boolean

    For site = 0 To NumSites - 1

        goodPart = IsPartGood(site) ' existing good-part check
        If Not goodPart Then GoTo NextSite

        For testIdx = 0 To NumRelTests - 1
            x = GetMeasureForRelTest(site, testIdx) ' function to fetch measurement

            passRel = RT_Check(RtState(site, testIdx), _
                               x, RT_LIMIT_SIGMA, RT_MIN_SAMPLES, z)

            ' Datalog
            Call RL_Datalog_Z(site, testIdx, z)
            Call RL_Datalog_Pass(site, testIdx, passRel)

            If Not passRel Then
                Call MarkPartAsRelFail(site)
            End If
        Next testIdx

NextSite:
    Next site

    ProcessAndDatalog_RT = 0
End Function
```

You’ll need to map:

- `IsPartGood`,  
- `GetMeasureForRelTest`,  
- `RL_Datalog_Z`, `RL_Datalog_Pass`,  
- `MarkPartAsRelFail`  

to your actual IG‑XL functions.

---