# Pre-Rise Path Battery — 2026-08-11

## Classification

- Layer: Research / Engineering
- Level: A, research-only diagnostic
- Production change: none
- Status: exploratory; no scanner, score, ranking, entry/exit, portfolio, publication, or live behavior was changed.

## Scope and data gate

The battery searched for price-path behavior before the scan timestamp using the existing enriched export, intraday cache, and daily price cache. Intraday bars were included only when their timestamp was at or before `scan_ts`, interpreted as UTC. No future intraday bar was used.

| Measure | Result |
|---|---:|
| Enriched export rows | 100,496 |
| Unique export symbol-date pairs | 48,760 |
| Intraday cache files | 880 |
| Filename-level symbol-date matches | 247 |
| Resolved rows after strict timestamp/path checks | 237 |
| Resolved symbols / dates | 93 / 16 |
| Intraday volume available | No |
| Full-universe sector map coverage | Approximately 9% |
| Sector ETF coverage in resolved intraday subset | 100% |

Because only 16 dates and 237 rows survive the strict path gate, the result is low-powered and cannot establish generalizable predictive evidence. Volume acceleration, VWAP, intraday RVOL, and volume-spike features were not computed.

## Features

The battery computes first-window return, range expansion ratio, close location in the observed path, reversal from the best interim close, trend consistency, and five-day relative strength against SPY, IWM, and the mapped sector ETF. The sector mapping uses the existing `data/backtest_out/sector_map_full.csv`; the 100% figure above is only for the resolved intraday subset and must not be generalized to the full universe.

For each horizon, the 70/30 temporal split learns the upper-decile threshold on the first 11 dates and applies it to the last 5 dates. The report also includes same-date nearest-feature controls. Returns are shown before and after the existing 0.55% scenario cost; `bad_rate` means the fraction below -0.55%.

## Main validation observations

| Feature | 1-day validation lift | 5-day validation lift | 5-day selected cost-adjusted median |
|---|---:|---:|---:|
| Range expansion ratio | +3.63 pp | +3.43 pp | -1.38% |
| Close location | -0.13 pp | +9.29 pp | +4.49% |
| Reversal | -0.07 pp | -3.82 pp | -8.63% |
| Trend consistency | +4.74 pp | +4.65 pp | -0.16% |
| Relative strength vs SPY | -0.31 pp | +4.62 pp | -0.19% |
| Relative strength vs IWM | -2.23 pp | +0.72 pp | -4.09% |
| Relative strength vs sector ETF | -2.23 pp | +0.72 pp | -4.09% |

The 5-day close-location result is the strongest candidate in this small validation slice: selected median 5.04% versus baseline -4.26%, with a 66.7% selected positive rate versus 40.0% baseline. It is based on only 3 validation selections. Trend consistency and SPY relative strength also show positive median lifts, but their selected cost-adjusted medians remain slightly negative. The 1-day results are mixed, and reversal is consistently unfavorable in this sample.

The same-date nearest-feature controls do not provide a stable confirmation. For example, five-day median differences were +2.78 pp for SPY relative strength, +2.58 pp for trend consistency, and +1.93 pp for reversal, while close location was -0.88 pp. Pair counts ranged from 18 to 24 for most features, so these estimates remain sensitive to individual dates and observations.

## Interpretation and gates

These are descriptive associations from a low-coverage, outcome-linked exploratory sample. They are not causal evidence, not a validated predictive rule, and not sufficient for an OOS or production gate. The 5-day close-location result is a candidate hypothesis for a future, independently locked test; it is not an approved scanner feature.

Open blockers remain:

- Intraday volume is absent, so the proposed volume-acceleration perspective cannot be tested from this cache.
- News cache records are date/value data, not timestamped headlines or event records; event attribution remains blocked.
- Full-universe sector coverage remains approximately 9%, despite complete mapping within this small resolved subset.
- There is no immutable prior price-cache snapshot or complete point-in-time lineage for a confirmatory claim.
- Locked OOS was not opened. Human approval remains required for any confirmatory or production decision.

## Reproducibility

- Runner: `research/pre_rise_path_battery_2026_08_11.py`
- Artifact: `data/backtest_out/pre_rise_path_battery_2026-08-11.json`
- Focused tests: `tests/test_pre_rise_path_battery_2026_08_11.py`
- Cost scenario: 0.55 percentage points, used for exploratory reporting only.
