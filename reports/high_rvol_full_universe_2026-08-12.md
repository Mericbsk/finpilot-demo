# High-RVOL Full-Universe Test

## Protocol

This is a Level A research-only audit across the complete canonical
`(symbol, scan_date)` universe in `data/backtest_out/full_universe_enriched.csv`.
It used `43,279` outcome rows, approximately `1,970` symbols and `81` scan
dates. The first 10 dates were reserved as warm-up; each later date learned
the RVOL q90 threshold only from prior dates. No same-date outcome was used to
set the threshold. The outcome is overlapping `c2c_5d` and the dollar path is
only a diagnostic scenario with a `0.55%` cost assumption.

## Cohort results

| Cohort | Dates | Rows | Median date mean | Median row median | Positive date share | `$10k` scenario final |
|---|---:|---:|---:|---:|---:|---:|
| All rows | 71 | 41,705 | `+2.297%` | `+0.208%` | `70.4%` | `$206` |
| Eligible | 50 | 1,337 | `-0.829%` | `-0.265%` | `44.0%` | `$6,468` |
| High-RVOL all | 63 | 3,751 | `+1.601%` | `0.000%` | `63.5%` | `$73,020,271` |
| High-RVOL eligible | 36 | 238 | `-0.509%` | `-0.868%` | `50.0%` | `$9,160` |
| High-RVOL rejected | 63 | 3,513 | `+1.365%` | `0.000%` | `63.5%` | `$106,482,959` |
| Rejected | 71 | 40,368 | `+2.297%` | `+0.205%` | `74.6%` | `$231` |

The dollar figures are intentionally shown because they expose the failure:
the all-universe and rejected figures are economically nonsensical and are
driven by extreme overlapping outcomes. High-RVOL eligible does not exceed
the initial `$10,000` even before stricter data and execution gates.

The median row-level outcome for high-RVOL all and high-RVOL rejected is
`0.000%`, while their mean date returns are `+25.156%` and `+26.651%`.
That mean/median gap is direct evidence of tail domination. The full universe
contains 69 high-RVOL outcomes above `+50%` and 44 below `-50%`; high-RVOL
rejected contains 65 above `+50%` and 43 below `-50%`.

## Interpretation

Testing the whole universe did not rescue High RVOL. It made the problem more
visible:

1. The apparent result is concentrated in rejected rows, not in the product's
   eligible candidate layer.
2. High-RVOL all and high-RVOL rejected have almost identical date-level
   behavior, so RVOL is acting as a marker for the same contaminated/extreme
   outcome population rather than a validated selector.
3. The eligible high-RVOL cohort has negative median date and row outcomes and
   ends below `$10,000` in the same diagnostic scenario.
4. The compounding path is not executable because five-day windows overlap;
   observed fills, spread, ADV, turnover, capacity, immutable prior prices and
   corporate-action provenance are unavailable.

## Decision

High RVOL is rejected as a positive selector across the full universe. Its
only defensible product role is a context/data-quality warning: unusually high
activity should trigger greater skepticism about evidence quality and price
integrity. It must not be shown as an expected-return estimate or used to
promote rejected rows.

No scanner, score, ranking, entry/exit, risk, portfolio, publication, broker,
paper/live or locked-OOS behavior changed.

## Traceability

- Runner: `research/high_rvol_full_universe_2026_08_12.py`
- Artifact: `data/backtest_out/high_rvol_full_universe_2026-08-12.json`
- Source: `data/backtest_out/full_universe_enriched.csv`
- Test: `tests/test_high_rvol_full_universe_2026_08_12.py`
- Status: exploratory; production change `false`; locked OOS `not_opened`
