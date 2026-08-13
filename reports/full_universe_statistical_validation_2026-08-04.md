# Full-Universe Statistical Research

- Experiment: `full-universe-statistical-20260804`
- Scope: research-only; no production rule or publication change
- Raw rows: `53746`
- Canonical rows: `27308`
- Path-resolved rows: `27125`
- Date range: `2025-09-11..2026-07-13`
- Label: `5-bar triple barrier, TP=5.0x ATR, SL=1.5x ATR`
- Net-cost verdict: `insufficient_data` because observed spread/impact are unavailable

## Gates

- Temporal split: `ok`
- FER: `insufficient_data`
- Locked holdout: `not_opened`; runner is read-only

## Requested Methods

- CPCV paths: `15`; PBO: `0.13333333333333333`
- White Reality Check p-value: `0.009950248756218905`
- Hansen SPA p-value: `0.009950248756218905`
- Program-wide FDR tests: `21`; discoveries: `['ATR>=4', 'all', 'composite>=34', 'composite>=40', 'composite>=47']`
- HAC/Newey-West: calculated per candidate in the JSON companion
- DSR: calculated per candidate in the JSON companion
- HMM Regime Full: `ok`

## Candidate Summary

| Candidate | n | Mean return % | Median return % | HAC p | DSR |
| --- | ---: | ---: | ---: | ---: | ---: |
| `all` | 27125 | 1.9655 | -0.2220 | 0.004185 | 0.859181 |
| `entry_ok` | 799 | 0.6478 | -0.8769 | 0.339694 | 0.999636 |
| `ATR>=4` | 12902 | 3.3965 | -0.4785 | 0.018259 | 0.783827 |
| `ATR>=6` | 6707 | 5.1428 | -1.2750 | 0.058777 | 0.629938 |
| `gap>3` | 1727 | 5.9524 | -3.1840 | 0.124794 | 0.366315 |
| `RVOL>=2` | 2258 | 13.0384 | -0.8562 | 0.095964 | 0.485057 |
| `composite>=34` | 9957 | 0.7235 | -0.4043 | 0.004652 | 1.000000 |
| `composite>=47` | 5845 | 0.7885 | -0.3721 | 0.011793 | 1.000000 |
| `composite>=40` | 8198 | 0.7849 | -0.3521 | 0.004979 | 1.000000 |
| `composite>=52` | 3695 | 0.6460 | -0.5000 | 0.059730 | 1.000000 |
| `squeeze>=0.5` | 1361 | 1.0797 | -0.5000 | 0.076288 | 0.996828 |
| `ATR6+confirmation` | 1981 | 14.1964 | -3.3898 | 0.114116 | 0.436080 |
| `ATR6+entry_ok` | 168 | 1.6841 | -1.6243 | 0.375383 | 0.000003 |
| `ATR6+RVOL2` | 685 | 41.2499 | -3.0494 | 0.104467 | 0.442568 |
| `ATR6+RVOL2+composite70` | 42 | 0.8159 | -6.4246 | 0.786158 | 0.000000 |
| `ATR6+RVOL2+gap3` | 200 | 50.5942 | -7.9391 | 0.111038 | 0.352340 |
| `ATR6+RVOL2+direction` | 299 | -0.1120 | -9.0380 | 0.930739 | 0.000000 |
| `ATR6+RVOL2+gap3+direction` | 114 | -2.4302 | -9.5127 | 0.102017 | 0.000000 |
| `ATR6+RVOL2+gap3+not_near_52w_high` | 168 | 59.3731 | -9.3152 | 0.114684 | 0.334342 |
| `ATR6+RVOL2+gap3+direction+composite58` | 48 | -1.3756 | -9.4269 | 0.543005 | 0.000000 |
| `ATR6+RVOL2+gap3+direction+not_near_52w_high+composite58` | 29 | -2.1262 | -9.5482 | 0.540694 | 0.000000 |

## Interpretation Boundary

These are full-universe research statistics on path-aware labels, not a production approval.
The candidate matrix uses zero return for an unselected row only in bootstrap reality checks;
the per-candidate HAC/DSR results use selected observations only.
Missing spread, impact, point-in-time event data, and the unopened locked holdout remain blocking conditions.
