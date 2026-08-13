# High RVOL 1-10 Day Horizon Battery

## Method

The full-universe canonical export does not contain raw OHLC bars or forward
returns for days 2-10. This research-only battery therefore reconstructs a
proxy by compounding the same symbol's daily `c2c_1d` observations over the
common scan-date sequence. Rows with missing symbol-date observations are
excluded. This is not a raw OHLC validation and is not executable P&L.

Selection remains prior-date expanding q90 RVOL with a 10-date warm-up. Costs
are the existing diagnostic `0.55%` per horizon observation. The clipped value
clips the reconstructed row return to `[-50%, +50%]` before subtracting cost.

## Results

Values below are row means; medians and clipped net means are included because
the raw means are heavily distorted by extreme observations.

| Day | All mean / median / clipped net | Eligible mean / median / clipped net | Rejected mean / median / clipped net |
|---:|---:|---:|---:|
| 1 | `+3.69 / 0.00 / -0.51%` | `+0.38 / +0.02 / -0.17%` | `+3.90 / 0.00 / -0.53%` |
| 2 | `+394.35 / +0.13 / -0.18%` | `-1.28 / -1.74 / -1.89%` | `+418.23 / +0.21 / -0.07%` |
| 3 | `+350.93 / +0.34 / +0.36%` | `-2.86 / -2.04 / -3.41%` | `+372.95 / +0.45 / +0.59%` |
| 4 | `+504.59 / -0.51 / -0.49%` | `-4.91 / -4.90 / -5.46%` | `+550.50 / -0.28 / -0.04%` |
| 5 | `+822.25 / -0.73 / -0.42%` | `-8.39 / -6.99 / -8.94%` | `+892.53 / -0.24 / +0.30%` |
| 6 | `+8.84 / -1.53 / -1.60%` | `-9.26 / -6.77 / -9.81%` | `+10.65 / -1.02 / -0.78%` |
| 7 | `+2.87 / -0.82 / -1.13%` | `-10.09 / -8.61 / -10.64%` | `+4.06 / -0.24 / -0.26%` |
| 8 | `+4.63 / +1.05 / +1.05%` | `-9.49 / -7.42 / -10.04%` | `+5.67 / +1.82 / +1.87%` |
| 9 | `+2.42 / +1.16 / +0.10%` | `-6.55 / -0.26 / -7.10%` | `+2.98 / +1.21 / +0.54%` |
| 10 | `+0.32 / -0.55 / -0.23%` | `-6.24 / -9.58 / -6.79%` | `+0.54 / -0.22 / -0.01%` |

The raw 2-5 day means are not interpretable as evidence: their medians remain
near zero while the clipped means collapse. The eligible cohort is negative
from day 2 onward on both median and clipped net mean. Rejected has a weak
clipped proxy maximum around day 8, but only `44%` of dates are positive there,
and it has not passed raw-OHLC, data-quality or independent OOS checks.

## Exit implication

No horizon currently satisfies a production exit rule. A defensible research
rule would require a horizon whose cost-adjusted median, clipped mean, positive
date share and matched-control lift remain positive across independent time
blocks. This battery does not establish that condition.

The next exit study must use raw OHLC and test, at each horizon, ATR-based stop,
time stop, maximum adverse excursion and transaction cost. Until then, fixed
claims such as “exit on day 5” or “hold for 8 days” are unsupported.

Artifact: `data/backtest_out/high_rvol_horizon_battery_2026-08-12.json`.
