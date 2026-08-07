# Research Program Execution Report

Date: 2026-08-06
Status: research-only evidence; no production promotion
Authority layer: Research / Engineering
Decision level: Level A for isolated research artifacts; any live rule change remains Level B/C.

## Scope

This run applied the first evidence, score-contract, calibration, barrier and portfolio slices of the research roadmap. Scanner scoring, entry/exit behavior, risk limits, publication and Telegram output were not changed.

## Contracts Added

- `research/evidence_ledger.py`: canonical evidence event identity, feature timestamp validation, label/cost version metadata and unresolved/insufficient-data states.
- `research/score_bridge.py`: live score, optional research score, component accounting and filter overlap telemetry.
- `research/honest_score_calibration.py`: 5-day triple-barrier net-cost calibration using temporal train/test bands.
- Focused tests cover event identity, PIT timestamp rejection, outcome maturity, score accounting and thin calibration bands.

## Executed Experiments

### Barrier sensitivity

Command:

```text
python -m research.full_universe_barrier_backtest --horizons 3,5,10,20 --tp 1,1.5,2,3,4,5 --sl 0.5,0.75,1,1.5,2 --round-trip-cost-pct 0.55 --out data/backtest_out/entry_exit_sweep_2026-08-06
```

Inputs and outputs:

- Input: `data/backtest_out/full_universe_enriched.csv`
- Cache: `data/price_cache/`
- Rows: 53,746; canonical deduplicated rows: 27,308
- Output: `data/backtest_out/entry_exit_sweep_2026-08-06/full_universe_barrier_results.json`
- Grid: `data/backtest_out/entry_exit_sweep_2026-08-06/full_universe_barrier_grid.csv`

Interpretation:

- The sweep generated 2,520 viable result rows and many positive cost-adjusted expectancy values.
- The strongest values concentrate in selective predicates and 5x ATR / 10-20 day horizons.
- This is not promotion evidence. The result is exposed to selection, horizon and tail-return effects, and the grid itself does not establish locked-OOS stability.
- The existing script had a repository-root path defect when invoked as a module; this was corrected without changing the barrier methodology.

### Portfolio simulation

Command:

```text
python portfolio_target_backtest.py --csv data/backtest_out/full_universe_enriched.csv --cache data/price_cache --out data/backtest_out/portfolio_experiment_2026-08-06
```

Artifact: `data/backtest_out/portfolio_experiment_2026-08-06`.

- Input rows: 53,746
- Resolved rows: 53,115
- Short paths: 50
- Entry-drift rejects: 581
- Symbols: 1,929
- Configurations: 36

The best final-equity configuration in this run was composite top-10, 20 maximum positions, ATR-risk sizing and wide-volatility exit: final equity `$100,515.21`, CAGR `0.0062`, realized daily Sharpe `0.2323`, max drawdown `-4.06%`, 245 trades and win rate `40.82%`.

This is approximately flat, not profitability evidence. Other configurations were negative, including the earlier composite top-5 fixed-ATR examples. The portfolio result therefore blocks any inference that selective barrier expectancy automatically becomes a robust portfolio edge.

### Honest score calibration

Command:

```text
python -m research.honest_score_calibration --csv data/backtest_out/full_universe_enriched.csv --cache data/price_cache --out data/backtest_out/honest_score_calibration_2026-08-06.json --cost-pct 0.55 --split-date 2026-06-15
```

Artifact: `data/backtest_out/honest_score_calibration_2026-08-06.json`.

Method:

- Target: 5-day triple-barrier net return greater than zero.
- TP: 2x ATR; SL: 1x ATR.
- Round-trip cost: 0.55 percentage points.
- Score source: `full_universe_enriched.composite`.
- Temporal split: train before 2026-06-15, test on/after 2026-06-15.
- Total resolved observations: 23,345.
- Train: 12,403; test: 10,942.

Results:

- Train Brier: `0.236069`.
- Test Brier: `0.248426`.
- Score bands are not monotonic in observed net-win rate.
- Test `80-100` band has only `n=12` and is marked `insufficient_data` by the minimum-band gate.

Conclusion: the composite score is not currently demonstrated to be a calibrated probability or monotonic quality scale under this honest target. No production score or public wording should be changed from this result alone.

## Current Gates

- Evidence identity/PIT: foundational contract added and focused tests pass.
- Live/research score equivalence: bridge exists, but a full row-level equivalence report is still required.
- Score ceiling: the live component maximum observed in the bridge fixture is `16.0`, while `MAX_RECO_SCORE` and its comments state `16.5`; this remains an unresolved score-contract discrepancy and was not changed.
- Calibration: research-only; OOS degradation and thin bands prevent promotion.
- Portfolio robustness: not passed; best observed configuration is approximately flat and configuration-sensitive.
- Locked holdout: not opened.
- Production/public promotion: not requested and not performed.

## Next Ordered Work

1. Build a row-level live/research score equivalence report and resolve the documented 16.0/16.5 ceiling discrepancy through the product decision process.
2. Add temporal split and minimum-sample gates to the interaction/regime experiment runner.
3. Run pairwise interactions with pre-registered hypotheses, FDR and HAC controls.
4. Run separate market, sector, volatility and liquidity regime conditioning in shadow mode.
5. Extend portfolio analysis with concentration, correlation, sector and turnover constraints.
6. Only after those gates, evaluate dynamic profile selection and research-agent orchestration.

No result in this report is a production recommendation or an alpha claim.
