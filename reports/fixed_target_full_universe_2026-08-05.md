# Fixed-Target Full-Universe Research

- Experiment: `fixed-target-full-universe-2026-08-05`
- Scope: research-only; no production rule change
- Configurations: `3120`
- Targets: `[3.0, 5.0, 7.000000000000001, 10.0]%`
- Fixed stops: `[2.0, 3.0, 5.0]%`; ATR stops: `[1.0, 1.5, 2.0]x ATR`
- Horizons: `[1, 3, 5, 10, 20]` bars
- Data: `53746` raw, `27308` canonical, `24731` path-resolved
- Date range: `2025-09-11..2026-06-30`
- Month coverage: `{'2025-09': 1678, '2025-10': 332, '2025-11': 6, '2025-12': 6, '2026-04': 1137, '2026-05': 11204, '2026-06': 10368}`
- Split coverage: `{'train_rows': 2022, 'validation_rows': 0, 'locked_oos_rows_unopened': 22709}`
- Observed transaction costs: `insufficient_data`; cost values below are scenarios, not observations

## Gates

- FDR discoveries: `994`
- CPCV/PBO: `0.4` across `15` paths
- White Reality Check p: `0.2837162837162837`
- Hansen SPA p: `0.29270729270729273`
- Gross + train/validation stable: `0`
- Cost-positive: `0`
- Locked holdout: `not_opened`; not opened by runner

## Highest-Median Configurations

| Configuration | n | Mean % | Median % | Train median % | Validation median % | HAC p | DSR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ATR>=7|tp=10.00%|atr_stop=1.5|h=20` | 4270 | 0.519 | 10.000 | 10.000 | nan | 0.235989 | 0.000000 |
| `ATR>=5|tp=10.00%|atr_stop=2|h=20` | 8280 | 1.247 | 10.000 | 10.000 | nan | 0.000032 | 1.000000 |
| `ATR>=6|tp=10.00%|atr_stop=2|h=20` | 5979 | 0.800 | 10.000 | 10.000 | nan | 0.036643 | 1.000000 |
| `ATR>=7|tp=10.00%|atr_stop=2|h=20` | 4270 | 0.511 | 10.000 | 10.000 | nan | 0.298422 | 0.000000 |
| `ATR>=6+composite>=34|tp=10.00%|atr_stop=2|h=20` | 2154 | 0.434 | 10.000 | nan | nan | 0.535277 | 0.000000 |
| `ATR>=6+composite>=40|tp=10.00%|atr_stop=2|h=20` | 1748 | 0.632 | 10.000 | nan | nan | 0.387932 | 0.000000 |
| `ATR>=6+composite>=47|tp=10.00%|atr_stop=2|h=20` | 1204 | 1.145 | 10.000 | nan | nan | 0.126791 | 0.004067 |
| `ATR>=6+RVOL>=1.5|tp=10.00%|atr_stop=2|h=20` | 1156 | 0.951 | 10.000 | 10.000 | nan | 0.063078 | 0.000000 |
| `ATR>=6+RVOL>=2|tp=10.00%|atr_stop=2|h=20` | 646 | 1.047 | 10.000 | 10.000 | nan | 0.015905 | 0.000000 |
| `ATR>=6+gap>2|tp=10.00%|atr_stop=2|h=20` | 1333 | 0.366 | 10.000 | 10.000 | nan | 0.573019 | 0.000000 |
| `ATR>=7|tp=10.00%|atr_stop=1.5|h=10` | 4270 | 0.652 | 10.000 | 10.000 | nan | 0.110400 | 0.707246 |
| `ATR>=6+RVOL>=2|tp=10.00%|atr_stop=1.5|h=10` | 646 | 0.920 | 10.000 | 10.000 | nan | 0.020784 | 0.000000 |
| `ATR>=6+gap>2|tp=10.00%|atr_stop=1.5|h=10` | 1333 | 0.753 | 10.000 | 10.000 | nan | 0.175349 | 0.000000 |
| `ATR>=5|tp=10.00%|atr_stop=1.5|h=20` | 8280 | 1.140 | 10.000 | 10.000 | nan | 0.000050 | 1.000000 |
| `ATR>=6|tp=10.00%|atr_stop=1.5|h=20` | 5979 | 0.775 | 10.000 | 10.000 | nan | 0.026656 | 1.000000 |
| `ATR>=6+composite>=34|tp=10.00%|atr_stop=1.5|h=20` | 2154 | 0.456 | 10.000 | nan | nan | 0.459045 | 0.000000 |
| `ATR>=6+composite>=40|tp=10.00%|atr_stop=1.5|h=20` | 1748 | 0.613 | 10.000 | nan | nan | 0.345158 | 0.000000 |
| `ATR>=6+composite>=47|tp=10.00%|atr_stop=1.5|h=20` | 1204 | 1.012 | 10.000 | nan | nan | 0.142111 | 0.001907 |
| `ATR>=6+RVOL>=1.5|tp=10.00%|atr_stop=1.5|h=20` | 1156 | 0.915 | 10.000 | 10.000 | nan | 0.063557 | 0.000000 |
| `ATR>=6+RVOL>=2|tp=10.00%|atr_stop=1.5|h=20` | 646 | 0.722 | 10.000 | 10.000 | nan | 0.101368 | 0.000000 |
| `ATR>=6+gap>2|tp=10.00%|atr_stop=1.5|h=20` | 1333 | 0.760 | 10.000 | 10.000 | nan | 0.184670 | 0.000000 |
| `ATR>=6+gap>3|tp=10.00%|atr_stop=1.5|h=20` | 904 | 0.002 | 10.000 | 10.000 | nan | 0.997555 | 0.000000 |
| `ATR>=5|tp=10.00%|atr_stop=2|h=10` | 8280 | 1.448 | 10.000 | 10.000 | nan | 0.000000 | 1.000000 |
| `ATR>=6|tp=10.00%|atr_stop=2|h=10` | 5979 | 1.147 | 10.000 | 10.000 | nan | 0.000630 | 1.000000 |
| `ATR>=7|tp=10.00%|atr_stop=2|h=10` | 4270 | 0.936 | 10.000 | 10.000 | nan | 0.025504 | 1.000000 |

## Final Interpretation

- Gross and period-stable configurations: `[]`
- Configurations positive after declared cost scenarios: `[]`
- A locked holdout result is not claimed because the one-time holdout was not opened.
- Missing observed spread, slippage, impact, and point-in-time execution fields remain blocking conditions.
