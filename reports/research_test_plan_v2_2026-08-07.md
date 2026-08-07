# FinPilot Research Operating Plan v2

Date: 2026-08-07
Status: Planned research protocol; no experiment in this document has been
executed by this plan.
Authority layer: Research
Decision level: Level A for the plan and isolated audits; Level B/C for any
product rule, risk, portfolio, shadow, broker or production action.
Baseline: [Evidence Matrix v1](evidence_matrix_v1_2026-08-07.md)

## 1. Objective

The purpose of the next research cycle is not to find the highest historical
return. It is to determine whether a registered hypothesis can survive a
reproducible sequence of evidence gates:

```text
Hypothesis
  -> Discovery
  -> Standardized validation
  -> Statistical integrity and robustness
  -> One-time locked OOS
  -> Execution feasibility
  -> Capacity
  -> Shadow
  -> Human promotion decision
  -> Production
```

A candidate may stop at any gate. Rejection is a valid research outcome.
Production is not the success criterion; auditable elimination and correctly
classified uncertainty are.

## 2. Non-negotiable controls

These controls apply to every experiment, including negative results:

- Record dataset hash or immutable artifact id, date range, row count, schema,
  duplicate policy and canonical symbol-day rule.
- Declare whether the target is close-to-close, daily-OHLC path-aware or
  execution-observed. Favorable movement/MFE fields cannot be reported as
  realized P&L.
- Declare entry timestamp, entry-price rule, exit rule, horizon, cost version,
  currency, short-side policy and corporate-action treatment.
- Register the hypothesis and parameter family before running selection.
- Keep discovery, validation and locked OOS data roles separate.
- Never tune a candidate after observing its locked OOS result.
- Treat `PASS`, `FAIL`, `UNKNOWN`, `INSUFFICIENT_DATA` and `NOT_OPENED` as
  distinct states. `UNKNOWN` and `INSUFFICIENT_DATA` cannot satisfy a mandatory
  gate.
- Do not zero-fill missing spread, sector, PIT or execution fields.
- Do not change production behavior, send broker orders or make a public
  performance claim from a research result.

## 3. Candidate and evidence contracts

### 3.1 Hypothesis record

Every candidate must have a write-once pre-registration record containing:

| Field | Requirement |
| --- | --- |
| `hypothesis_id` | Stable identifier; never reused |
| `family_id` | Shared test family for multiple-testing accounting |
| `mechanism_status` | `supported` or `exploratory` |
| `mechanism` | Expected inefficiency, failure condition and why it may persist at FinPilot's scale |
| `entry` | Exact signal, timestamp and price rule |
| `ranking` | Ranking rule, if any |
| `timing` | Delay and execution assumptions |
| `exit` | Exact TP/SL/time/signal rule |
| `universe` | Symbols, filters, dates and PIT policy |
| `parameters` | Frozen values and units |
| `planned_tests` | Declared tests before discovery selection |
| `selection_rule` | How a candidate can be selected without choosing after the fact |
| `oos_reserved` | Boolean plus immutable holdout id |
| `status` | `registered`, `discovery`, `validation`, `rejected`, `oos_ready`, `oos_opened`, `shadow_eligible` |

Exploratory mechanism status is allowed in Discovery, but requires stronger
validation evidence before it can reach OOS. A mechanism record must answer:

> Why does this edge exist, why might it persist at FinPilot's scale, and why
> should it survive spread, slippage, delay and capacity costs?

### 3.2 Evidence record

Every run must emit:

- `experiment_id`, `hypothesis_id`, `family_id`, code version and input hash;
- label/cost/execution model versions;
- sample count, independent date count and independent symbol count;
- mean, geometric mean, median, P25, P75, P90, P95;
- TP, SL, time and first-touch rates;
- MAE, MFE, maximum loss, turnover and drawdown;
- uncapped and capped/winsorized views;
- cost-low, cost-base and cost-high scenarios;
- temporal, regime and cross-sectional results with minimum-sample status;
- missingness, reason codes and any excluded rows;
- gate status and decision rationale.

## 4. Research order and planned experiments

The order below is dependency-aware. A later phase must not be used to avoid an
earlier failed or unopened gate.

### Phase P0 — Evidence and harness integrity

**Goal:** Prove that the research pipeline measures the declared object before
using it to judge a candidate.

| ID | Experiment / test | Method | Minimum PASS condition | Output / stop condition |
| --- | --- | --- | --- | --- |
| P0-1 | Live/research score equivalence | Replay the same timestamped inputs through production evaluation and research bridge; compare every component and final field row by row. | Exact or explicitly explained equivalence for all mandatory fields; no unexplained 16.0/16.5 ceiling drift. | Equivalence report. Stop all score/ranking experiments if unresolved drift remains. |
| P0-2 | Canonical identity audit | Validate `(symbol, scan_date)` uniqueness, scan timestamp, entry drift, duplicate policy and path availability. | Zero silent duplicate policy changes; all exclusions have reason codes. | Canonical baseline manifest. |
| P0-3 | Label contract audit | Unit and fixture tests for close-only, daily-OHLC barrier and execution-observed targets; verify stop-first tie handling and time exit. | Each target is labelled with the correct semantic type; no MFE field is named or consumed as P&L. | Label contract report and focused tests. |
| P0-4 | Leakage and timestamp audit | Shift features and labels across time; test future feature rejection and as-of joins. | Future information is rejected; shifted controls behave as nulls. | PIT/leakage report. |
| P0-5 | Research budget registry | Register test family, planned count, actual count, discarded runs, reruns and selection rule before discovery. | Every candidate result can be traced to its full family count. | Write-once registry; no promotion if registry is incomplete. |

**P0 decision:** If P0-1 through P0-4 do not pass, the result is a harness or
data-contract investigation, not strategy evidence.

### Phase P1 — Negative-control preflight

**Goal:** Establish that the pipeline does not manufacture edge from null inputs.

This phase has two separate uses and they must not be conflated:

1. **Pipeline preflight:** Does the complete research motor call matched random
   inputs null?
2. **Candidate significance:** Does a registered candidate exceed its matched
   null distribution after selection and multiple-testing accounting?

| ID | Null family | Method | Required design | PASS / FAIL |
| --- | --- | --- | --- | --- |
| P1-1 | Label permutation | Shuffle outcomes while preserving signal rows, dates, symbols and holding periods. | At least 1,000 reproducible permutations per declared family or a pre-registered alternative. | Pipeline summary remains null-like; candidate statistic is not claimed from this test alone. |
| P1-2 | Signal permutation | Replace signal membership with matched random selections preserving daily count, symbol universe and holding-period distribution. | Same cost, portfolio slots, ranking and turnover treatment as the real candidate. | No systematic positive median/cost-adjusted edge above null distribution. |
| P1-3 | Time-shift control | Shift signal features to earlier/later dates under a declared offset. | Preserve data availability and avoid introducing artificial missingness. | Shifted controls do not reproduce the candidate result. |
| P1-4 | Harness invariant tests | Run deterministic fixtures and known-negative synthetic data. | Stable output hashes and expected null labels. | Any failure blocks all candidate interpretation. |

Candidate-level significance must report the candidate percentile against the
matched null distribution, not merely a single permutation p-value. Null
results are controls, not proof that a positive candidate is causal.

### Phase P2 — Standardized candidate validation

**Goal:** Compare a small, pre-registered candidate set under one scorecard.

The initial candidate set should be limited to previously observed hypotheses,
not a new broad sweep:

- current `entry_ok` baseline;
- score-2 research profile;
- one ATR/RVOL candidate;
- one existing ranking candidate;
- one explicitly defined timing or exit candidate.

No new threshold family should be added until this battery is complete.

Each candidate receives the same:

- daily-OHLC triple-barrier outcome;
- declared horizons;
- cost-low/base/high scenarios;
- median and capped-return analysis;
- portfolio and single-trade views;
- monthly and temporal summaries;
- sample and missingness gates.

**Suggested minimum evidence gates:**

- at least 500 resolved observations for broad candidate validation;
- at least 50 independent scan dates;
- at least 30 independent symbols;
- no mandatory field with unresolved lineage;
- median, capped and cost-high results reported together;
- no reliance on `resolved_pct_t5` as execution P&L.

These are proposed research thresholds, not production policy. If a candidate
falls below them, status is `INSUFFICIENT_DATA`, not an inferred pass or fail.

### Phase P3 — Robustness and statistical integrity

**Goal:** Test whether a validated result survives reasonable changes in time,
market state, cross-section and outlier treatment.

| ID | Test | Method | Required gate |
| --- | --- | --- | --- |
| P3-1 | Temporal robustness | Train, validation, reserved OOS and walk-forward windows. | Positive direction and cost-adjusted behavior in every mandatory window; minimum independent dates per window. |
| P3-2 | Regime robustness | Market trend and volatility regimes first; add sector only after PIT mapping. | No single regime may carry the entire result; small cells are `INSUFFICIENT_DATA`. |
| P3-3 | Outlier robustness | Capped/winsorized returns, leave-one-period-out and leave-one-symbol-cluster-out. | Candidate does not depend on a small number of extreme observations or one month. |
| P3-4 | Cross-sectional robustness | Actual pairwise candidate correlation, sector and market-cap mapping with PIT dates. | Coverage and minimum cell sizes pass; proxy ETF groups are not accepted as candidate correlation. |
| P3-5 | Multiple testing | FDR, HAC, CPCV/PBO, White Reality Check and SPA using registry family counts. | Result survives the declared family correction and is not selected solely by raw mean. |
| P3-6 | Veto quality | Compare rejected rows with matched accepted controls using cost-adjusted path outcomes. | Veto must reduce avoidable loss without unacceptable positive-opportunity rejection; no new veto rule from descriptive evidence alone. |

A candidate fails robustness if the median is negative and the positive mean is
removed by reasonable caps, if one month/regime dominates the result, or if a
mandatory segment is unavailable without a declared reason.

### Phase P4 — Locked OOS

**Goal:** Obtain one final, non-iterative result on data not used for discovery
or candidate selection.

Requirements before opening:

- human approval recorded;
- candidate and parameters frozen;
- registry write-once record complete;
- all preprocessing and cost versions frozen;
- null family and evaluation scorecard frozen;
- no exploratory candidate list added after lock;
- OOS access audit enabled.

The OOS result is opened once per candidate family. After opening:

- no threshold adjustment;
- no exit replacement;
- no candidate relabelling;
- no repeated OOS rerun for optimization.

Possible outcomes are `PASS`, `FAIL` or `INSUFFICIENT_DATA`. `NOT_OPENED` is
the current status and is not a negative performance result.

### Phase P5 — Execution feasibility

**Goal:** Measure whether the statistical result survives realistic timing and
fills.

| ID | Test | Data requirement | Output |
| --- | --- | --- | --- |
| P5-1 | Entry-delay curve | Timestamped signal, bid/ask or reliable quote, next-bar and intraday prices. | Net return at signal, +1m, +5m, +15m, +30m; execution decay curve. |
| P5-2 | Spread/slippage replay | Dated spread, fill or quote data; no fixed-cost substitution when observed data is absent. | Spread, slippage, fill probability and cost distribution. |
| P5-3 | Path-ordering replay | Intraday OHLC or quote/trade path. | Same-bar ordering, stop/target fill and gap treatment. |
| P5-4 | Turnover and holding analysis | Portfolio event ledger. | Turnover, time in market, concurrent positions and financing/borrow assumptions. |

The current `0%` observed spread-source rate means P5 is presently
`UNKNOWN`/`INSUFFICIENT_DATA`, not a failed strategy result.

### Phase P6 — Capacity

**Goal:** Determine the capital range in which the candidate remains economically
implementable.

Capacity is deliberately later than execution feasibility. The first ladder is
USD-based and bounded to the current FinPilot scale:

```text
$1k -> $5k -> $10k -> $25k -> $50k -> $100k
```

Extend beyond `$100k` only if observed execution data justifies it.

For every capital level report:

- participation rate;
- ADV and spread;
- fill probability;
- slippage and impact;
- position cap rejects;
- turnover and concentration;
- mark-to-market portfolio equity;
- worst drawdown and liquidity stress.

A current liquidity snapshot must not be joined retroactively to historical
outcomes as if it were historical execution evidence.

### Phase P7 — Shadow

**Goal:** Compare frozen research expectations with live observation without
sending broker orders.

Shadow is eligible only after P0-P6 mandatory gates pass and human approval is
recorded. The shadow ledger must capture:

- signal timestamp and frozen candidate id;
- expected entry and exit;
- hypothetical fill and delay;
- observed quote/spread;
- realized mark-to-market path;
- missing-data and reject reason;
- comparison against the locked research expectation.

Shadow must not be used to tune the candidate. A shadow result that triggers a
parameter change starts a new candidate family and cannot reuse the same OOS
claim.

### Phase P8 — Production decision

Production is a human decision, not an automatic result of a score.
Promotion requires, at minimum:

- no failed mandatory gate;
- no unresolved mandatory `UNKNOWN` or `INSUFFICIENT_DATA`;
- one-time locked OOS result recorded;
- execution and capacity evidence observed;
- shadow protocol completed;
- risk, compliance and product approval recorded;
- rollback and monitoring plan available.

This plan does not authorize production, paper orders, live orders, risk changes
or scanner changes.

## 5. Gate decision rules

### Mandatory gates

A candidate cannot advance when any mandatory gate is:

- `FAIL`;
- `NOT_OPENED`;
- `UNKNOWN`;
- `INSUFFICIENT_DATA` without an approved scope exception.

A scope exception must record:

- exact missing field or sample limitation;
- affected candidate and family;
- why the gate is not decision-critical for that specific phase;
- expiry date;
- approving human;
- next evidence required.

Repeated scope exceptions are not a substitute for collecting the missing data.

### Failure classes

| Failure class | Meaning | Required response |
| --- | --- | --- |
| `HARNESS_FAIL` | Pipeline, label, timestamp or equivalence error. | Stop interpretation; repair and rerun the same test. |
| `DATA_FAIL` | Required data missing, stale or not PIT. | Mark `INSUFFICIENT_DATA`; collect/repair data. |
| `NULL_FAIL` | Null control reproduces apparent edge. | Freeze candidate interpretation; audit leakage and selection. |
| `ROBUSTNESS_FAIL` | Result depends on outliers, period or segment. | Reject candidate for this protocol. |
| `ECONOMIC_FAIL` | Cost-adjusted result does not survive declared scenarios. | Reject promotion; do not reduce cost assumption silently. |
| `EXECUTION_FAIL` | Delay, spread, fill or path eliminates result. | Reject execution eligibility or redesign as a new hypothesis. |
| `CAPACITY_FAIL` | Capital level causes unacceptable impact, concentration or fill loss. | Record maximum viable tested range; no extrapolation. |
| `OOS_FAIL` | Frozen candidate fails locked holdout. | Retire candidate family; do not tune against OOS. |

## 6. Deferred execution plan

Because the current evidence matrix shows that the private research system is
not production-grade and launch-critical work has priority, the following work
is deferred rather than silently started:

### Launch sonrası P0/P1

1. Build the write-once registry and research-budget accounting.
2. Implement negative-control preflight with at least 1,000 matched
   permutations per pre-registered family, subject to resource limits declared
   before execution.
3. Complete score equivalence, canonical identity and label contract audits.
4. Produce one candidate-family scorecard without adding new strategy ideas.

### Later gates

1. Repair PIT sector, spread, fill and intraday path telemetry.
2. Obtain human approval and open the locked OOS once.
3. Run execution decay and bounded capacity tests.
4. Run observation-only shadow only after eligibility gates pass.

No planned item above changes production by itself.

## 7. Current baseline decision

Based on the [Evidence Matrix v1](evidence_matrix_v1_2026-08-07.md):

- the current `entry_ok` behavior remains unchanged;
- score-2, ATR/RVOL, composite top-N and new TP/SL profiles remain research
  hypotheses;
- no No-Trade/veto rule is approved;
- no Alpaca or paper order is authorized by this plan;
- the next useful deliverable after launch is the P0/P1 integrity spine, not a
  broader parameter sweep.

This document is a planned protocol, not evidence that any listed gate has
passed.
