---
type: methodology
status: partial
verifier: external SPL training material cross-read
date: 2026-04-22
source: "calculation methodology (MADE +JF)_ sept2019.pdf; SPL BY YE_USERS GUIDELINE_REV4.pdf; SPL METHODOLOGY_sett2022.pdf; SPL recommendations_Sept'20-final.pptx; SPL SUPPORT incident management_v2.pptx; SPL_METHODOLOGY.pdf; WHY SPL_30 september 2019.pdf"
supplemental_source: "user-provided SPL implementation notes, 2026-04-23"
---

# SPL Workflow And Methodology

Reusable guidance for SPL-driven TP work in TP-AgentKit.

Use this note when the request involves SPL, SPAT, PAT, Yield Explorer limit review, exported SPL limit files, or requests to implement statistically generated limits into a TP.

This note captures the recurring lessons from the provided training set. It is source-backed methodology guidance, not blanket approval to push any generated limit into production without program-specific review.

## 1. What SPL Is For

SPL in the training material is a statistical limit-review and outlier-detection workflow used to support PAT or SPAT and production limit enforcement.

Recurring intent across the documents:

- set parametric test limits from robust statistical treatment of historical data
- handle non-normal distributions without assuming a simple Gaussian model
- remove abnormal parts and expose outliers
- detect process or distribution shift before it turns into fallout or customer return risk
- improve production reliability while making yield-loss impact explicit

High-signal source phrases repeated across the training set:

- `WHY SPL?`
- `SPL analysis flow`
- `Statistical Parametric Limits`
- `The goal of SPL is to enable the enforcement of the new limits in the production flow, improve reliability and prevent customer returns.`
- `To support Removal of parts with abnormal characteristics (Outliers) and detect Process shift`

## 2. Core Method Concepts

### 2.1 Robust preprocessing before limit calculation

The training repeatedly pairs `MADe` filtering with `Johnson Fit`.

- `MADe` filtering is used to clean abnormal points or strong outliers before the final fit.
- `Johnson Fit` is used because the real data population is often non-normal.
- The target limit is then taken from a percentile equivalent to the desired sigma level rather than from a naive normal assumption.

The strongest repeated headings were:

- `JOHNSON FIT + MADe filtering`
- `HOW MADe filtering works`
- `Johnson family distributions`
- `A problem and the solution: a simple model - the percentiles`

### 2.2 SPL is not only a number generator

The training treats SPL as a review workflow, not a blind limit export.

- review yield-loss impact after the suggested limit change
- review charts and fitted distributions
- look for outlier clusters or process-shift signals
- use capability indicators such as `Cpk` or related metrics when provided by the tool output

For TP-AgentKit this means an exported SPL limit file should be treated as candidate engineering output until the user confirms what was approved for TP implementation.

### 2.3 PAT and DPAT ordering matters

The recommendations material explicitly says the SPL node should run before DPAT and that DPAT should consume the previous step output so SPL rejects are not re-included.

## 3. User Workflow Repeated In The Training

The YE and recommendations documents repeat a common workflow shape:

1. Create a new SPL project in Yield Explorer.
2. Select the input dataset and scope.
3. Run the analysis interactively or by schedule.
4. Review calculated limits, charts, yield-loss impact, and outlier behavior.
5. Validate the chosen limits.
6. Generate the report and SPL limits file used by downstream PAT tooling.

The training also frames the overall process as `Data collection` followed by `Data Elaboration`.

For TP-AgentKit intake, this means an SPL request should be anchored to the real stage of the work:

- raw historical data review
- Yield Explorer project or screenshots
- SPL report only
- exported limits file or CSV
- already approved implementation delta waiting to be applied to the TP

## 4. Preconditions And Cautions

### 4.1 Data quality and representativeness

- enough representative data is required for a robust calculation
- the methodology slides reference six lots as the preferred population baseline for AEC-Q001-style work
- when six lots are not available yet, characterization lots can be a temporary fallback

Do not treat an early low-volume population as equivalent to a stable production distribution.

### 4.2 Scope discipline inside YE

The user guideline and recommendation slides contain several operational cautions:

- avoid overly specific recurring context like a fixed lot list when building reusable analysis flows
- `PASSING PARTS ONLY` is the default and changing it is described as not recommended unless there is a reason
- regex-based test-name filtering is described as not recommended for performance reasons
- local STDF input is expected to come from a local folder

### 4.3 Recommended analysis settings from training

The recommendations deck calls out these baseline settings:

- `MADE = 7`
- `JF = 7`

Treat these as training defaults, not universal mandatory values for every product or release.

### 4.4 User-provided implementation heuristics

These notes were added from later working guidance rather than the original training deck.

Treat them as planning and review heuristics for SPL implementation work, not as blanket rules that override product-specific approval.

- target `Cpk` for candidate SPL tightening is typically in the `3.5` to `4.0` range
- per-test yield-loss target is typically around `0.00002%` to `0.00004%`
- a practical reference point is `0.00002%` yield loss per individual test
- four decimal places are usually sufficient when discussing these tiny percentages; five decimal places may become stricter than intended
- a rough aggregate planning target is about `0.1%` total yield loss across roughly `3000` tests
- total test-count coverage can be considered during planning, but these notes do not require it as a hard prerequisite for choosing the percentage target
- tests with low `Cpk` and high failure count should usually keep the current limit instead of being tightened through SPL
- some tests are known poor candidates for SPL and should be excluded from the generic bulk-application path unless the user or engineering owner explicitly says otherwise

Default exclude-or-review-separately list from these working notes:

- matching tests
- delta tests
- kelvin tests
- continuity tests in the generic bulk path
- `NS`, `nA`, `UV`, code-read, temperature, and unbin tests

### 4.5 Special handling for continuity-style tests

The user-provided notes treat continuity-like tests as a separate review class rather than part of the generic bulk SPL path.

- continuity tests may still use SPL, but only with manual review to avoid limits that become artificially tight
- continuity open can support SPL tightening when the review confirms the behavior is meaningful
- continuity short should usually keep the existing limit
- continuity end tests should not be changed through the generic SPL flow
- do not tighten continuity-style tests that already show low `Cpk`
- keep open and short populations separated during review so the result is not distorted by mixed failure modes

### 4.6 Production-safety cautions for TP-AgentKit

When implementing SPL results into a TP:

- do not infer approval from the existence of an SPL export alone
- confirm whether the task is analysis-only, review-only, or edit work
- confirm which environments, variants, or products the approved limits apply to
- preserve file structure unless the request explicitly includes added or removed tests
- keep unchanged variants untouched when the approved scope is narrower than `ALL`

Pair this note with `limit_env_mapping.md` when the request specifies COLD, ROOM, HOT, or only one environment family.

## 5. TP-AgentKit Intake Anchors For SPL Tasks

When a user asks to `implement SPL` or references an SPL project, the highest-value anchors are:

- source TP revision and whether a copied target revision is required
- SPL source artifact: report, CSV, YE export, screenshots, or limits file
- whether the numbers are proposed or already approved
- exact implementation scope: LL only, UL only, full LL or UL pair, one environment, all environments, or a named test subset
- validation expectation: diff review, structure audit, simulator, YE re-export, or datalog confirmation
- whether the task is only limit replacement or also includes test add or remove decisions

Do not collapse `SPL request` into `replace every matching limit everywhere`.

## 6. Support And Escalation Expectations

The support deck makes two support lanes explicit:

- functional support should start with the divisional key user
- tool or execution incidents should be escalated with a minimum support packet

The repeated support packet items were:

- screenshot with the error message
- SPL project name
- YE server information
- username or equivalent tool identity

The formal escalation path in the training is a HELYX ticket under `Ye_Gen` and `Application Issue`.

For TP-AgentKit artifacts, keep the support-packet structure but avoid writing private local identifiers into durable notes unless the user explicitly asked for them.

## 7. Practical Reuse Inside TP-AgentKit

Load this note before planning when the user asks about:

- SPL or SPAT implementation into a TP
- PAT limit generation or review
- statistically generated limit files from Yield Explorer
- outlier-driven limit tightening or relaxation
- process-shift investigation tied to historical parametric data

Use this note together with:

- `spl_csv_schema.md` for the actual YE SPL CSV field shape and which columns should drive TP updates
- `constraints.md` for revision and protected-area rules before edits
- `limit_env_mapping.md` for environment-specific LL or UL handling
- `tp_revision_patterns.md` when the SPL work needs a new revision copy first

## 8. What This Note Does Not Assert

This training harvest does not by itself prove that a specific SPL output is correct for a specific product, test, or release.

It does not replace:

- product-specific engineering review
- environment-scope confirmation
- TP structure validation after implementation
- release-readiness evidence