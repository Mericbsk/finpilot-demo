# Full-Universe Statistical Research

- Experiment: `full-universe-candidate-gates-20260804`
- Scope: research-only; no production rule or publication change
- Raw rows: `53746`
- Canonical rows: `27308`
- Path-resolved rows: `27125`
- Date range: `2025-09-11..2026-07-13`
- Label: `5-bar triple barrier, TP=5.0x ATR, SL=1.5x ATR`
- Net-cost verdict: `insufficient_data` because observed spread/impact are unavailable
- Cost scenarios tested (not observed): `[10.0, 25.0, 50.0, 100.0] bps`

## Gates

- Temporal split: `ok`
- FER: `insufficient_data`
- Locked holdout: `not_opened`; runner is read-only

## Requested Methods

- CPCV paths: `15`; PBO: `0.13333333333333333`
- White Reality Check p-value: `0.009950248756218905`
- Hansen SPA p-value: `0.014925373134328358`
- Program-wide FDR tests: `26`; discoveries: `['all', 'composite>=34', 'composite>=40', 'composite>=47']`
- HAC/Newey-West: calculated per candidate in the JSON companion
- DSR: calculated per candidate in the JSON companion
- HMM Regime Full: `ok`
- Pre-holdout gross candidates passing mean/median/FDR/HAC/DSR gates: `[]`

## Candidate Summary

| Candidate | n | Mean return % | Median return % | HAC p | DSR |
| --- | ---: | ---: | ---: | ---: | ---: |
| `all` | 27125 | 1.9655 | -0.2220 | 0.004185 | 0.839703 |
| `entry_ok` | 799 | 0.6478 | -0.8769 | 0.339694 | 0.979181 |
| `ATR>=3` | 17496 | 2.7677 | -0.2396 | 0.009288 | 0.802120 |
| `ATR>=4` | 12902 | 3.3965 | -0.4785 | 0.018259 | 0.752616 |
| `ATR>=5` | 9260 | 4.1792 | -0.8225 | 0.035510 | 0.672946 |
| `ATR>=6` | 6707 | 5.1428 | -1.2750 | 0.058777 | 0.579116 |
| `ATR>=7` | 4809 | 6.6830 | -1.6393 | 0.075911 | 0.512115 |
| `composite>=34` | 9957 | 0.7235 | -0.4043 | 0.004652 | 1.000000 |
| `composite>=40` | 8198 | 0.7849 | -0.3521 | 0.004979 | 1.000000 |
| `composite>=47` | 5845 | 0.7885 | -0.3721 | 0.011793 | 1.000000 |
| `composite>=52` | 3695 | 0.6460 | -0.5000 | 0.059730 | 1.000000 |
| `composite>=58` | 1691 | 0.1956 | -0.8554 | 0.630604 | 0.000000 |
| `ATR>=4+composite>=34` | 4244 | 0.9376 | -1.1145 | 0.090155 | 1.000000 |
| `ATR>=4+composite>=40` | 3450 | 1.1480 | -0.9812 | 0.062903 | 1.000000 |
| `ATR>=4+composite>=47` | 2405 | 1.2459 | -0.7035 | 0.075568 | 1.000000 |
| `ATR>=6+composite>=34` | 2208 | 0.9632 | -1.7931 | 0.281433 | 1.000000 |
| `ATR>=6+composite>=40` | 1771 | 1.3750 | -1.2346 | 0.174639 | 1.000000 |
| `ATR>=6+composite>=47` | 1213 | 1.8964 | -0.2244 | 0.096448 | 1.000000 |
| `ATR>=4+RVOL>=1.5` | 2442 | 12.5269 | -1.1601 | 0.084763 | 0.464000 |
| `ATR>=4+RVOL>=2` | 1286 | 22.5239 | -2.2445 | 0.099932 | 0.406051 |
| `ATR>=6+RVOL>=1.5` | 1235 | 23.4678 | -1.5974 | 0.097672 | 0.406565 |
| `ATR>=6+RVOL>=2` | 685 | 41.2499 | -3.0494 | 0.104467 | 0.379239 |
| `ATR>=4+gap>2` | 2268 | 5.7304 | -1.2444 | 0.055689 | 0.572083 |
| `ATR>=4+gap>3` | 1383 | 7.5459 | -3.7736 | 0.116472 | 0.313567 |
| `ATR>=6+gap>2` | 1441 | 7.9895 | -2.0642 | 0.085259 | 0.434482 |
| `ATR>=6+gap>3` | 975 | 10.2216 | -4.4776 | 0.128980 | 0.258181 |

## Interpretation Boundary

These are full-universe research statistics on path-aware labels, not a production approval.
The candidate matrix uses zero return for an unselected row only in bootstrap reality checks;
the per-candidate HAC/DSR results use selected observations only.
Missing spread, impact, point-in-time event data, and the unopened locked holdout remain blocking conditions.
