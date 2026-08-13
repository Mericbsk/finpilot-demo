# Winner Anatomy / Move Attribution — 2026-08-11

## Status

- Layer: Research / Engineering
- Level: A — research-only exploratory work
- Scope: `data/backtest_out/full_universe_enriched.csv`
- Production change: none
- Confirmatory/OOS status: not opened

## Protocol

The study profiles the top 10% of observations for `c2c_1d` and `c2c_5d`.
Feature summaries use fields available in the enriched export and report
all-cohort medians, winner-cohort medians, missingness and Spearman
association. These are descriptive associations only. Outcome columns are not
used as features.

## Results

| Horizon | Rows | Winner rows | Top-tail threshold | Winner median |
|---|---:|---:|---:|---:|
| `c2c_1d` | 100,496 | 10,050 | 4.47% | 6.92% |
| `c2c_5d` | 87,690 | 8,769 | 9.53% | 14.66% |

The strongest commonality candidate is movement intensity, not the existing
score or entry decision itself:

| Horizon | RVOL all / winners | ATR all / winners |
|---|---:|---:|
| `c2c_1d` | 0.85 / 0.90 | 4.44% / 6.68% |
| `c2c_5d` | 0.85 / 0.92 | 4.45% / 6.33% |

This supports a new exploratory perspective: large moves may be associated
with unusually active and volatile names at scan time. It does not show that
RVOL or ATR causes the move, improves future selection, survives costs, or is
stable out of sample.

## Attribution data gate

The inventory found 1,216 news-cache files and 385,635 records, but zero
records containing both a timestamp and headline. Sector fields, benchmark
fields and observed event labels are also absent from the enriched export.
Therefore market/sector/event/idiosyncratic return decomposition is blocked.
The available sentiment/date cache must not be described as causal news
attribution.

## Added controls and temporal check

The expanded run added date-aligned benchmark excess returns, the available
sector map, a same-date top-tail comparison, and a chronological 70/30
stability split.

| Horizon | Same-date median difference | Sector coverage | SPY winner excess median | IWM winner excess median |
|---|---:|---:|---:|---:|
| `c2c_1d` | 7.01% | 9.23% | 6.73% | 6.78% |
| `c2c_5d` | 14.67% | 9.15% | 13.98% | 14.14% |

For the same test applied to the entire available universe, the median excess
returns are:

| Horizon | SPY all-universe median excess | IWM all-universe median excess |
|---|---:|---:|
| `c2c_1d` | -0.03% | -0.01% |
| `c2c_5d` | -0.12% | +0.10% |

This is the key comparison. The full universe is approximately flat versus
the benchmarks, while the top-tail cohort is strongly positive by construction
because it is defined using the realized outcome. The winner excess numbers
therefore describe the realized separation of winners from the universe; they
are not a deployable signal and cannot be used as evidence that the scanner
would have selected those names in advance.

The benchmark comparison confirms that top-tail winners outperformed the
market over the same realized window. This is a property of the selected
winner cohort, not evidence that the pre-scan features predicted those
outcomes. The sector result is not decision-ready because coverage is only
about 9%.

The temporal feature check does not support a simple stable rule:

- RVOL versus `c2c_1d`: Spearman `0.040` in train and `0.033` in validation.
- ATR versus `c2c_1d`: `-0.038` in train and `-0.152` in validation.
- RVOL versus `c2c_5d`: `0.009` in train and `0.108` in validation.
- ATR versus `c2c_5d`: `-0.002` in train and `-0.241` in validation.

These low and unstable associations mean that the winner profile should not
yet become a predictive filter. The next useful data task is to raise
point-in-time sector coverage and add timestamped event data, followed by a
pre-registered matched-control predictive test.

## Pre-scan selection test

Each feature's upper-decile threshold was learned on the first 70% of dates
and applied unchanged to the last 30%. Lift is selected-cohort median outcome
minus the validation baseline median.

| Horizon | Feature | Train lift | Validation lift | Validation positive rate | Baseline positive rate |
|---|---|---:|---:|---:|---:|
| `c2c_1d` | RVOL | -0.07% | -0.35% | 43.6% | 46.7% |
| `c2c_1d` | ATR | -0.97% | -1.24% | 40.1% | 46.7% |
| `c2c_1d` | Gap | +0.07% | +0.10% | 48.7% | 46.7% |
| `c2c_1d` | Score | +0.01% | -0.01% | 46.9% | 46.7% |
| `c2c_5d` | RVOL | -0.54% | +0.56% | 51.7% | 46.6% |
| `c2c_5d` | ATR | -1.93% | -4.17% | 35.2% | 46.5% |
| `c2c_5d` | Gap | -0.37% | -1.99% | 37.6% | 46.5% |
| `c2c_5d` | Score | -0.13% | +0.22% | 48.0% | 46.5% |

The current answer is negative for a simple upper-tail filter: high ATR is
unfavorable in validation, RVOL is inconsistent across horizons, and gap and
score do not show stable lift. The positive `c2c_5d` RVOL result is small and
exploratory; it requires matched controls, costs, multiple-testing correction
and a fresh locked validation before it can be considered a candidate.

## Ordered next work

1. Add a point-in-time event schema with symbol, event timestamp, source,
   headline and event type; preserve ingestion provenance.
2. Add point-in-time sector and benchmark returns for market/sector residual
   decomposition.
3. Re-run the same frozen cohorts with same-date matched controls and a
   temporal validation split before proposing any predictive test.
4. Only after data and execution gates pass, prepare a separately approved
   confirmatory or product-rule proposal.

## Evidence

- Machine-readable artifact: `data/backtest_out/winner_anatomy_2026-08-11.json`
- Runner: `research/winner_anatomy_2026_08_11.py`
- Focused test: `tests/test_winner_anatomy_2026_08_11.py`
