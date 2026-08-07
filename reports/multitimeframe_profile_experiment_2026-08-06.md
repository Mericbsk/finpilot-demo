# Multi-Timeframe Profile Experiment

Date: 2026-08-06
Status: research-only, no production rule change
Decision level: Level B if either profile is later proposed for live entry or ranking

## Question

Should multi-timeframe confirmation and early detection be represented as two
separate profiles instead of being compressed into one `entry_ok` decision?

- Confirmatory profile: full 1h/4h/daily alignment plus momentum confluence.
- Early profile: short-term momentum confluence while the higher-timeframe
  alignment is not yet complete.

The experiment does not alter `entry_ok`, ranking, risk, position sizing, or
execution.

## Data and method

Input artifact:

- `data/suggestions/*.csv`
- 63 CSV files
- 602 rows
- 124 symbols
- date range: 2025-09-12 through 2025-12-01
- fields available: `timeframe_aligned`, `alignment_ratio`,
  `momentum_confluence`, `momentum_ratio`, `entry_ok`, `score`, `regime`,
  `direction`, `price`, and price-unit `atr`

Canonical and path controls:

- earliest row per `(symbol, scan_date)`
- 265 canonical rows resolved to a 5-day forward path
- 51 rows rejected by the existing maximum entry-drift check
- no missing paths or short paths among the retained rows
- ATR percentage derived explicitly as `atr / price * 100`

Outcome model:

- forward horizon: 5 trading days
- take-profit: 2.0 x ATR
- stop-loss: 1.0 x ATR
- stop-first same-bar tie handling
- research round-trip cost: 0.55 percentage points
- cost-adjusted expectancy = gross expectancy - 0.55 percentage points

The artifact is an old suggestion export, not a production point-in-time
replay. Its short date range and selection history limit the strength of any
conclusion.

## Profile definitions

These are research cohort definitions, not live rules:

- `confirmatory`: `alignment_ratio >= 1.0`, `momentum_ratio >= 0.5`, and
  `momentum_confluence == True`.
- `early`: `alignment_ratio < 1.0`, `momentum_ratio >= 0.5`, and
  `momentum_confluence == True`.
- `insufficient_data`: momentum ratio below 0.5 or momentum confluence absent.

The pure classifier is in `research/multitimeframe_profiles.py`. It is not
imported by scanner evaluation and cannot change `entry_ok`.

## Canonical 5-day barrier results

| Profile | N | TP | SL | Gross expectancy % | Cost-adjusted expectancy % | PF | Median return % | Worst MAE % | Maximum loss % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| All suggestion rows | 265 | 39.25% | 60.00% | 0.151 | -0.399 | 1.328 | -0.500 | -27.573 | -5.633 |
| Confirmatory | 200 | 41.50% | 58.50% | 0.173 | -0.377 | 1.379 | -0.500 | -16.929 | -5.633 |
| Early | 24 | 29.17% | 70.83% | 0.235 | -0.315 | 1.451 | -0.500 | -27.573 | -2.807 |

The early cohort is too small for a reliable comparison. Its slightly higher
gross expectancy is not evidence of a superior strategy, especially because
its stop rate is higher and its worst MAE is materially worse than the
confirmatory cohort.

## Monthly stability

| Profile | 2025-09 | 2025-10 | 2025-11 | 2025-12 |
|---|---:|---:|---:|---:|
| Confirmatory gross expectancy % | 0.098 | 0.527 | -0.125 | 1.000 |
| Early gross expectancy % | 0.731 | -0.267 | -0.500 | 0.500 |

Both profiles change sign across months. The early result is especially
unstable because only 24 canonical observations are available.

## Interpretation

1. The architecture should preserve separate confirmatory and early profiles.
   They answer different questions and should not share one ranking, one risk
   interpretation, or one performance claim.
2. The current artifact does not show a statistically reliable winner.
3. Confirmatory alignment improves selectivity and has a higher TP rate in this
   sample, but cost-adjusted expectancy remains negative.
4. Early detection has a higher observed gross expectancy in this small sample,
   but a higher stop rate, worse worst-case MAE, and insufficient sample size.
5. No profile should be promoted to production from this run.

## Required next experiment

A production-quality comparison needs a new point-in-time export or replay
artifact with, per canonical symbol-day:

- individual 1h, 4h, and daily alignment flags;
- `alignment_ratio` and feature timestamps;
- 15m and 4h momentum flags plus `momentum_ratio`;
- raw RSI, volume, and MACD components;
- current gate state and reject reasons;
- canonical dedup identity;
- execution-feasible price, ATR, spread/impact and cost-model version;
- regime and volatility labels.

The next run should pre-register separate profiles and separate evaluation
policies:

- Confirmatory: full alignment, normal risk envelope, ranking only within the
  confirmatory cohort.
- Early: incomplete higher-timeframe alignment, stricter volatility/stop-risk
  controls, separate ranking, and no comparison against confirmatory signals
  as though they had identical risk.

Both profiles must be evaluated on discovery, validation, and locked-OOS time
splits with cluster-aware inference. Until that artifact exists, conclusions
about early-vs-confirmatory superiority are `insufficient_data`.

## Recent-month extension: July and August 2026

The first run used `data/suggestions/*.csv` because those files contained the
alignment and confluence fields together with a price-unit ATR. Recent scan
exports were then added from `data/distribution/scan_export_2026-*.json`.

Coverage:

- export dates represented: 2026-07-02 through 2026-08-05;
- 16,696 raw rows;
- 15,090 canonical symbol-days after deduplication;
- 10,415 canonical July rows and 4,675 canonical August rows;
- 1,697 five-day paths resolved, all from July;
- 8 rows rejected by entry drift in the resolved set;
- August has no mature five-day outcome path yet and is therefore not included
  in performance metrics.

The same profile definitions and barrier configuration were used:

- confirmatory: alignment `>= 1.0`, momentum ratio `>= 0.5`, confluence true;
- early: alignment `< 1.0`, momentum ratio `>= 0.5`, confluence true;
- 5-day horizon, 2x ATR TP, 1x ATR SL, 0.55 percentage-point cost.

### Mature July results

| Profile | N | TP | SL | Gross expectancy % | Cost-adjusted expectancy % | PF |
|---|---:|---:|---:|---:|---:|---:|
| Confirmatory | 129 | 30.23% | 68.99% | -0.171 | -0.721 | 0.660 |
| Early | 175 | 29.71% | 70.29% | -0.220 | -0.770 | 0.611 |

The table is limited to metrics produced and retained by the recent-month
profile run; no aggregate all-row MAE is inferred from the profile cohorts.

### July weekly stability

| Profile | Week 2 gross / cost % | Week 3 gross / cost % | Week 4+ gross / cost % |
|---|---:|---:|---:|
| Confirmatory | -0.047 / -0.597 | -0.187 / -0.737 | insufficient data |
| Early | -0.112 / -0.662 | -0.204 / -0.754 | -2.050 / -2.600 |

The recent mature period does not support a quality advantage for either
profile. The early cohort is not only smaller in the original artifact; in
the mature July export it also has a higher stop rate and worse expectancy.

### August status

August has 4,675 canonical observations in the exports, but zero resolved
five-day paths as of 2026-08-06. These rows remain an outcome queue, not a
performance result. They should be re-run after the five-trading-day maturity
window, with the same snapshot identity and no retrospective replacement of
the feature values.
