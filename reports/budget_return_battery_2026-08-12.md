# $10,000 Budget Return Battery

## Scope and interpretation

This is a Level A, research-only budget translation of the row-level
experiments. It starts with `$10,000`, uses a `0.55%` round-trip cost scenario,
learns q10/q20/q80/q90 thresholds on the first 70% of dates, and evaluates the
last 30% chronologically from `data/backtest_out/full_universe_enriched.csv`.
The outcome is `c2c_5d` and the calculation compounds one date-level portfolio
return after another.

The outcome windows overlap. There are no observed fills, spreads, ADV,
turnover, capacity, cash lock-up or position-level daily marks. Therefore the
final dollar values below are **diagnostic scenario values**, not a claim that
`$10,000` could have been traded into those amounts.

## Equal-weight results

| Strategy | Selected rows / dates | Final value | P/L | Return | Max DD |
|---|---:|---:|---:|---:|---:|
| High RVOL | 496 / 14 | `$147,297` | `$137,297` | `+1,372.97%` | `-15.29%` |
| Low gap | 1,170 / 15 | `$33,771` | `$23,771` | `+237.71%` | `-28.59%` |
| Low score | 3,275 / 15 | `$30,012` | `$20,012` | `+200.12%` | `-0.05%` |
| Rejected | 11,353 / 15 | `$15,203` | `$5,203` | `+52.03%` | `-98.98%` |
| All rows | 11,530 / 15 | `$14,718` | `$4,718` | `+47.18%` | `-1.50%` |
| Low RVOL | 1,880 / 15 | `$12,988` | `$2,988` | `+29.88%` | `-9.40%` |
| High gap | 1,117 / 15 | `$9,091` | `-$909` | `-9.09%` | `-22.05%` |
| `entry_ok` | 177 / 13 | `$5,556` | `-$4,444` | `-44.44%` | `-40.54%` |

The high-RVOL, low-gap and low-score figures are dominated by a small number
of validation dates and overlapping outcomes. They must not be interpreted as
validated alpha.

## ATR-parity results

| Strategy | Final value | P/L | Return | Max DD |
|---|---:|---:|---:|---:|
| High RVOL | `$20,822` | `$10,822` | `+108.22%` | `-7.73%` |
| Low score | `$16,707` | `$6,707` | `+67.07%` | `-0.85%` |
| Low gap | `$14,854` | `$4,854` | `+48.54%` | `-25.26%` |
| Rejected | `$11,360` | `$1,360` | `+13.60%` | `-2.71%` |
| All rows | `$11,148` | `$1,148` | `+11.48%` | `-2.82%` |
| Low RVOL | `$9,890` | `-$110` | `-1.10%` | `-6.49%` |
| High gap | `$9,413` | `-$587` | `-5.87%` | `-15.58%` |
| High score | `$9,320` | `-$680` | `-6.80%` | `-12.82%` |
| `entry_ok` | `$6,294` | `-$3,706` | `-37.06%` | `-34.30%` |

ATR-parity reduces some concentration-driven drawdowns, but it does not turn
the `entry_ok` selection layer into a profitable strategy. The same protocol
also produced contradictory behavior across cohorts, so no automatic sizing
rule is promoted.

## Combinations

| Combination | Equal-weight final | ATR-parity final | Selected dates |
|---|---:|---:|---:|
| `entry_ok + high_RVOL` | `$8,314` | `$8,372` | 10 |
| `entry_ok + high_score + low_gap` | `$7,544` | `$7,666` | 3 |
| `entry_ok + low_gap` | `$5,705` | `$5,844` | 6 |
| `entry_ok + low_RVOL` | `$5,619` | `$5,986` | 6 |
| `entry_ok + low_gap + low_RVOL` | `$6,267` | `$6,267` | 2 |

None of these combinations beats the initial `$10,000` after the base cost
scenario. The two- and three-date combinations are especially unusable as
evidence.

## What was not converted to dollars

The intraday pre-rise battery and the daily pre-rise matched-control battery
were not given fabricated equity curves. Their artifacts preserve summary
medians/lifts, but not the date-level selected return path required for a
defensible compounded budget simulation. The intraday study also covers only
237 rows and 16 dates. A separate rerun would need to persist row-level
selection paths first.

Data-quality and abstention are not directional return strategies. They are
gates/context layers; their prior validation results remain in their dated
artifacts and are not silently converted into dollar P&L here.

## Decision

The budget exercise does not validate a profitable production strategy. The
most important result is negative: `entry_ok`, high-score selection and their
combinations lose capital in this scenario. High-RVOL and low-gap nominal
results are exploratory outlier-sensitive diagnostics, not product promises.
The product candidates remain data-quality visibility, evidence/abstention
context, and ATR-parity risk comparison, subject to independent locked OOS,
reliable price provenance and observed execution data.

## Traceability

- Runner: `research/budget_return_battery_2026_08_12.py`
- Artifact: `data/backtest_out/budget_return_battery_2026-08-12.json`
- Test: `tests/test_budget_return_battery_2026_08_12.py`
- Source: `data/backtest_out/full_universe_enriched.csv`
- Cost sensitivity checked at `0.00%`, `0.55%` and `1.00%`
- Production change: `false`; locked OOS: `not_opened`
