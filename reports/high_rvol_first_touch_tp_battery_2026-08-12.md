# High-RVOL First-Touch TP Battery

Date: 2026-08-12
Status: research-only; no production promotion
Authority layer: Research / Engineering
Decision level: Level A for the isolated diagnostic; any exit-rule change remains Level B/C.

## Protocol

Runner: `research/high_rvol_raw_ohlc_exit_battery_2026_08_12.py`
Input: `data/backtest_out/full_universe_enriched.csv` and local `data/price_cache`
Selection: prior-date expanding q90 RVOL
Entry: scan-date raw-bar close
Coverage: 4,163 selected rows; 3,445 complete paths through T+10
Cost: diagnostic 0.55% round trip; observed spread, slippage and impact are unavailable.

The battery added first-touch fixed-percentage targets of 0.5%, 1%, 1.5%, 2%, 3%, 5%, 7% and 10%, plus ATR targets of 0.5x, 1x, 1.5x, 2x and 3x. Every target was crossed with 1x, 1.5x and 2x ATR stops and 1, 5 and 10 day horizons. The first event wins: stop, target, then time exit. When daily OHLC shows both stop and target on the same bar, stop wins. Gap handling is conservative for stops; a target gap uses the next open.

## Results

The following rows use the 1.5x ATR stop and are cost-adjusted. Means are reported with medians because the raw cache contains large jump flags and the mean is materially outlier-sensitive.

### Fixed-percentage targets

| Cohort | Horizon | Target | Target hit | Stop exit | Time exit | Mean net % | Median net % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| All (n=3,445) | 1d | 0.5% | 72.4% | 10.4% | 17.2% | -0.608 | -0.050 |
| All (n=3,445) | 1d | 2% | 50.3% | 10.4% | 39.3% | -0.465 | 1.450 |
| All (n=3,445) | 5d | 1.5% | 73.1% | 18.9% | 8.0% | 4.654 | 0.950 |
| All (n=3,445) | 5d | 5% | 48.3% | 27.0% | 24.7% | 56.343 | 2.520 |
| Eligible (n=233) | 1d | 0.5% | 69.5% | 19.3% | 11.2% | -1.387 | -0.050 |
| Eligible (n=233) | 1d | 2% | 48.1% | 19.3% | 32.6% | -1.236 | 0.367 |
| Eligible (n=233) | 5d | 1.5% | 67.0% | 27.9% | 5.2% | -1.308 | 0.950 |
| Eligible (n=233) | 5d | 5% | 42.1% | 40.3% | 17.6% | -1.400 | -0.630 |
| Eligible (n=233) | 10d | 3% | 60.1% | 36.1% | 3.9% | -1.146 | 2.450 |
| Eligible (n=233) | 10d | 10% | 27.0% | 56.7% | 16.3% | -1.640 | -4.396 |

The all-cohort 5d and 10d means are not promotion evidence: the 5% target mean is 56.343% at 5d and 60.157% at 10d while the corresponding medians are 2.520% and 4.450%. This mean/median separation is consistent with the existing cache-integrity warning and requires outlier and corporate-action remediation before economic interpretation.

### ATR targets

For the eligible cohort at 5d, the 1.5x ATR stop results were:

| ATR target | Target hit | Stop exit | Time exit | Mean net % | Median net % |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.5x | 62.2% | 31.8% | 6.0% | -1.324 | 1.020 |
| 1x | 48.5% | 39.1% | 12.4% | -1.440 | 0.027 |
| 1.5x | 34.3% | 43.8% | 21.9% | -1.659 | -3.309 |
| 2x | 20.6% | 48.1% | 31.3% | -2.170 | -3.820 |
| 3x | 12.9% | 48.9% | 38.2% | -1.910 | -4.333 |

## Interpretation

No fixed or ATR profit target is validated. The eligible cohort remains negative on cost-adjusted mean across the displayed 1d, 5d and 10d fixed-target examples and across the 5d ATR-target grid. Positive medians at some low or medium targets do not overcome the small eligible sample, the cache jump warnings, absent observed execution costs and lack of an independent locked OOS.

This battery is a comparison artifact, not a production exit recommendation. It does not support a day-1, day-5 or day-10 exit rule, nor a production TP/SL change. Locked OOS remains unopened.

## Validation

- Focused tests: `2 passed` in `tests/test_high_rvol_raw_ohlc_exit_battery_2026_08_12.py`.
- Artifact checks: 3,445 complete paths; eligible 5d row count 233; `locked_oos` is `not_opened`.
- Production scanner, score, ranking, entry/exit, risk, portfolio, publication, broker and paper/live behavior were unchanged.
