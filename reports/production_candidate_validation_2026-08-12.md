# Production-Near Candidate Validation

## Status

This is a Level A, research-only validation. The source is
`data/backtest_out/full_universe_enriched.csv`, covering `2025-09-11` to
`2026-08-05`. The run used `100,496` raw rows and `43,279` canonical rows
after `(symbol, scan_date)` deduplication and required-field filtering.
No scanner, score, ranking, entry/exit, risk, portfolio, publication, broker,
paper or live behavior changed. Locked OOS was not opened.

## Results

### 1. ATR-parity risk construction

The same date-local daily calculation was run for eligible, rejected and
fixed-seed random controls. Outcomes are overlapping `c2c_5d` percentages;
they are not observed executable portfolio P&L.

| Cohort / scheme | Dates | Median daily | Mean daily | Max drawdown | Daily Sharpe | CVaR5 |
|---|---:|---:|---:|---:|---:|---:|
| Eligible / equal | 54 | -0.602% | 0.437% | -65.260% | 0.060 | -13.916% |
| Eligible / ATR-parity | 54 | -0.313% | 0.756% | -51.701% | 0.116 | -13.916% |
| Rejected / equal | 81 | 2.260% | 5.900% | -98.983% | 0.155 | -36.833% |
| Rejected / ATR-parity | 81 | 0.628% | 3.289% | -99.309% | 0.091 | -37.594% |

For 100 same-date random controls sized to the eligible count, the median of
run medians was `0.365%` for equal-weight and `0.801%` for ATR-parity. The
random-control summary is in the JSON artifact. The eligible result is
consistent with ATR-parity reducing concentration and drawdown in this
diagnostic, but the rejected result does not show a general benefit. This is
a risk-construction candidate, not evidence that selection or score predicts
returns.

### 2. Calibration-frozen abstention

The prior battery selected the abstention quartile on validation itself. This
run separates 50% train dates, 20% calibration dates and 30% later validation
dates. The evidence cutoff is learned on calibration only and then frozen.

- Calibration cutoff: `0.04660`
- Later validation abstain rate: `21.62%`
- Active validation 5-day median: `-0.047%`
- Abstained validation 5-day median: `-3.185%`

The separation is a useful exploratory signal that low evidence states may be
more adverse, but this remains a temporal holdout proxy rather than an
independent external dataset. Cost, capacity, turnover and user-behavior
effects were not observed.

### 3. Gap and RVOL context

Thresholds were learned from the first 70% of dates and evaluated on the last
30%.

| Feature | Train q10 | Train q90 | Low-group median | High-group median |
|---|---:|---:|---:|---:|
| `gap_pct` | -1.867% | 1.767% | -1.566% (`n=2,136`) | -2.852% (`n=2,312`) |
| `rvol` | 0.456 | 1.733 | -1.857% (`n=3,304`) | 0.000% (`n=1,829`) |

These context differences are descriptive and do not establish a stable
entry, exit, veto or inversion rule. Earlier gap/RVOL experiments remain
exploratory for the same reason.

### 4. Data-quality candidate

The dated data-readiness audit was refreshed alongside this run. It reports:

- `P1_data_reliability`: `BLOCKED`
- `P2_label_execution`: `BLOCKED`
- `H1/H2/H3_confirmatory`: `HOLD`
- `locked_oos`: `NOT_OPENED`

The audit therefore supports keeping data-quality checks as a research
warning/veto candidate, but not silently filtering the export or changing
production behavior. Price-jump flags, immutable prior snapshots, PIT
lineage, corporate-action provenance and observed execution data remain open
gaps.

## Decision

No candidate becomes a production rule from this run. ATR-parity is the
strongest research candidate because its eligible-cohort drawdown improved in
the same diagnostic, but it still requires reliable prices, observed costs,
capacity/turnover validation, independent locked OOS and Level B human
approval. Abstention, data-quality and gap/RVOL context remain exploratory.

## Traceability

- Runner: `research/production_candidate_validation_2026_08_12.py`
- Artifact: `data/backtest_out/production_candidate_validation_2026-08-12.json`
- Data audit: `data/backtest_out/data_readiness_audit_2026-08-12.json`
- Focused test: `tests/test_production_candidate_validation_2026_08_12.py`
- Execution: `python -m research.production_candidate_validation_2026_08_12 --random-runs 100`
- Status: exploratory; production change `false`; locked OOS not opened
