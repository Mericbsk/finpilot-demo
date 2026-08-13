# High RVOL Opportunity Battery

## Scope

This Level A research-only battery re-tested High RVOL across the full
canonical universe. For each evaluated date, q90 RVOL was learned from prior
dates only. The selected cohorts were High RVOL all, High RVOL eligible and
High RVOL rejected. The battery added three checks to the prior audit:

- non-overlapping `c2c_1d` date-level outcomes;
- `c2c_5d` outcomes clipped to `[-50%, +50%]` before date aggregation;
- 100 fixed-seed same-date, same-size random controls for each cohort.

The `c2c_5d` label still overlaps and is not executable portfolio P&L. Costs
are diagnostic scenarios, not observed fills.

## Results

| Cohort | Raw 5d mean | 5d mean after +/-50% clip | 1d mean | 1d median date | Random-control 1d lift |
|---|---:|---:|---:|---:|---:|
| High RVOL all | `+25.16%` | `-0.67%` | `+4.17%` | `0.004%` | `+3.16 pp` |
| High RVOL eligible | `+1.26%` | `+0.48%` | `+0.83%` | `+1.03%` | `+0.76 pp` |
| High RVOL rejected | `+26.65%` | `-0.58%` | `+4.49%` | `0.004%` | `+4.15 pp` |

The one-day values are arithmetic date means, not compounded capital. Their
top-four-date contribution is still extreme: `124.8%` for High RVOL all and
`124.0%` for High RVOL rejected. The every-fifth-date proxy is negative after
the `0.55%` cost assumption for all (`-0.18%`) and rejected (`-0.16%`).

For High RVOL eligible, the `0.55%` cost scenario gives a clipped five-day
mean net result of `-0.067%` and one-day mean net result of `+0.277%`. At a
`1.0%` cost assumption both become negative: `-0.517%` and `-0.173%`.

## Interpretation

The result has two distinct layers:

1. There is a potentially interesting short-horizon conditional association.
   High RVOL rejected exceeds the same-date random control by `+4.15 pp` on
   the one-day arithmetic mean, and eligible exceeds it by `+0.76 pp`.
2. The association is not yet a reliable five-day economic opportunity. The
   apparent five-day result disappears under clipping, the typical date is
   near zero, and a few dates account for more than the full raw sum.

The rejected cohort remains the most interesting research target, but it is not
a product candidate. It may be mixing genuine news/momentum with bad prices,
corporate actions, illiquidity and stale data. `entry_ok=False` is not a
single economic class.

## Queue decision

- **Gate 1, decomposition:** completed. High RVOL all is mostly rejected
  (`3,513` of `3,751` selected rows), so the two headline results are not
  independent confirmations.
- **Gate 2, non-overlap and matched controls:** completed. The one-day control
  lift is positive but date- and outlier-sensitive.
- **Gate 3, cost stress:** completed. Eligible is approximately flat at 55 bps
  after clipping and negative at 1% costs; rejected remains negative on the
  clipped five-day view.
- **Promotion decision:** High RVOL remains exploratory. No selector,
  expected-return promise or production change is approved.

## Next research opportunity

The next justified experiment is not another threshold sweep. It is a rejected
row taxonomy with independent price/corporate-action provenance and liquidity
inputs. Only after that should the positive one-day conditional association be
retested on a clean, non-overlapping, independently held-out sample.

Evidence artifact: `data/backtest_out/high_rvol_opportunity_battery_2026-08-12.json`.
