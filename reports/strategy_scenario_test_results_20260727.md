# FinPilot Strategy Expansion and Scenario Test Results

- Date: 2026-07-27
- Layer: `03-research`
- Decision level: Level A for isolated research execution; any product, scanner, risk, sizing, or live-execution change remains Level B/C.
- Status: exploratory research only; no product-rule or live-execution change applied.

## Scope and controls

The test plan in [strategy_scenario_test_plan_20260727.md](strategy_scenario_test_plan_20260727.md) was executed against the available repository artifacts. The primary forward label is `resolved_pct_t5 >= 5%`, a close-to-close proxy. It is not an intraday peak-touch label and cannot establish time-to-hit, MAE, MFE, or stop/target path outcomes without forward OHLC or intraday data.

Controls used where supported:

- Canonical symbol-day observations use the earliest `scan_ts`; a latest-scan sensitivity remains available.
- Discovery/validation/locked-OOS boundaries are preserved by the existing runners.
- Costs are reported as percentage-point assumptions; the target sweep uses the repository baseline round-trip cost of `0.55%`.
- Results are interpreted with sample size, median return, temporal stability, and data availability.
- No missing spread, impact, earnings timestamp, or OHLC path was fabricated.

## Test inventory

| ID | Test | Dataset / runner | Result | Verdict |
|---|---|---|---|---|
| DQ-1 | Canonical symbol-day deduplication | `full_universe_enriched.csv`, `full_universe_robustness.py` | 53,859 raw rows; 27,386 canonical symbol-days; earliest timestamp policy | Completed; methodology control |
| DQ-2 | Threshold and rejection inventory | `threshold_false_negative_audit.py` | 20,811 T+5-positive rows; 20,067 rejected by `entry_ok` | Negative diagnostic for current gate coverage |
| T-1 | Target and horizon sweep | `target_return_optimization.py` | 1d net expectancy negative for every target; 5d positive from 1.5% onward | Close-to-close exploratory evidence only |
| T-2/T-3 | Factor and constrained combinations | `full_universe_robustness.py` | ATR6 and ATR6+entry confirmation lift, but discovery-dependent | Candidate for further validation, not a rule |
| B-1 | Stored barrier/schema audit | `scripts/barrier_audit.py` and `data/finpilot.db` | All four schemas failed edge gates | `NO EDGE` |
| B-2/B-3 | Exit and outlier sensitivity | Existing `barrier_atr50`, `barrier_atr200`, and prior reports | Prior artifacts show expectancy is materially reduced by outlier caps | Negative robustness warning |
| A-1 | Formula/score comparison | `score_formula_comparison.py` | V2 locked-OOS positive but small; legacy results vary by formula | Candidate for further validation |
| R-1 | Regime segmentation | `score_lab_3_regime.py` | Runner blocked by incorrect relative CSV path | Blocked |
| C-1 | Liquidity, spread, and cost stress | `v2_data_quality_cost_runner.py` | ADV available; spread and short freshness missing; execution withheld | `insufficient_data` |
| OOS-1/OOS-2 | Rolling validation and locked test | `v2_walk_forward_runner.py` | Three windows; mixed locked-test expectancy and shrinking samples | Candidate for further validation |
| E-1 | Earnings/news segmentation | Available exports | Required point-in-time timestamps not present consistently | `insufficient_data` |

## Results

### DQ-1: canonical robustness

The full-universe robustness run used the close-to-close target and 400 cluster-bootstrap repetitions.

- Raw rows: `53,859`
- Canonical symbol-day rows: `27,386`
- Deduplication policy: earliest `scan_ts`
- Primary proxy base rate: approximately `39.5%`
- Best canonical rule in the tested recommendation set: `ATR6_entry_ok`
- Selected n: `168`
- Hit rate: `66.67%`
- Base rate: `39.53%`
- Lift: `1.686`
- Delta: `+27.14 pp`
- Wilson 95% interval: `[59.24%, 73.35%]`
- Mean T+5 return: `14.023%`
- Median T+5 return: `8.542%`

This is a discovery result. It does not prove execution profitability, because the label is close-to-close and the selection was inspected across many candidate rules.

### DQ-2: false-negative / coverage diagnostic

The favorable-mover proxy contains `20,811` positive rows. Of these, `20,067` are rejected by `entry_ok`, or approximately `96.4%`. Other rejection inventories were:

- Regime proxy: `10,465` positive rows, `19.43%` of all rows.
- Direction proxy: `9,980`, `18.53%`.
- Raw score below 3: `19,813`, `36.79%`.
- Liquidity rejection: `11,863`, `22.03%`.
- ATR below 6 rejection: `7,049`, `13.09%`.
- Gap below 3 rejection: `1,663`, `3.09%`.
- RVOL below 2 rejection: `1,816`, `3.37%`.

This is a coverage diagnostic, not evidence that the gate should be relaxed. Any gate change would be a Level B product decision and would require point-in-time validation and risk review.

### T-1: target and horizon sweep

Source: `53,859` full-universe rows, with `0.55%` round-trip cost assumption.

| Horizon | Target with highest reported net expectancy | Net expectancy | Median return | Gross hit rate | Sample |
|---|---:|---:|---:|---:|---:|
| 1 trading day | 10.0% | -0.54% | 0.04% | 3.4% | 53,859 |
| 5 trading days | 10.0% | +3.38% | 3.45% | 18.8% | 53,859 |

At 5 days, the target sweep reports positive net expectancy from the `1.5%` target onward, with the broad all-row view leading to `3.38%` at 10%. This cannot be treated as a target recommendation: the result uses a proxy construction that assigns target-hit rows to the target and misses to horizon close, and it is not path-aware. The highest mean is also sensitive to the presence of large movers.

### T-2/T-3: factors and combinations

The canonical robustness run found the following discovery patterns:

- `ATR>=6`: n `12,248`, hit `59.6%`, lift `1.542`.
- `ATR6_plus_confirmation`: n `3,684`, hit `60.6%`, lift `1.568`.
- `ATR6_entry_ok`: n `385` in the prior all-row view and n `168` after canonicalization; canonical hit `66.67%`, lift `1.686`.
- `ATR4_entry_confirmation`: n `302`, hit `48.0%`, lift `1.243` in the prior robustness output.

The stronger small cohort should be treated as hypothesis generation. It is not an approved scanner rule and has not passed an independent, adequately powered locked-OOS test.

### B-1: barrier/schema audit

The SQLite audit evaluated four score schemas using stored barrier and T+5 outcomes. Every schema failed the configured edge gates:

- `new_100`: n `311`, win rate `34.1%`, expectancy `+0.381%`, decile lift `1.276`, permutation p `0.11`.
- `old_filter`: n `3,713`, win rate `29.5%`, expectancy `+0.471%`, decile lift `1.003`, permutation p `0.255`.
- `old_raw`: n `135`, win rate `51.9%`, expectancy `+0.165%`, decile lift `0.214`, permutation p `0.949`.
- `all_combined`: n `4,159`, win rate `30.6%`, expectancy `+0.455%`, decile lift `1.275`, permutation p `0.746`.

Verdict: `NO EDGE`. Small positive expectancy values do not overcome the failed lift/significance gates.

### B-2/B-3: exit and outlier sensitivity

Existing repository artifacts and the prior factor-ablation report show that uncapped expectancy is materially driven by extreme observations. For the documented ATR6+RVOL2 barrier cohort:

- Uncapped expectancy: `8.82%`, PF `2.84`.
- 100% cap: `2.02%`, PF `1.43`.
- 200% cap: `1.99%`, PF `1.42`.
- 50% cap: `1.36%`, PF `1.29`.

The median in that prior cohort was negative while MFE was large, which reinforces the need for forward OHLC path data before making any stop, target, or execution conclusion. No exit profile was changed.

### A-1: formula and score comparison

The comparison used separate legacy and V2 artifacts and explicitly warns that their universes are not identical.

Selected locked-OOS V2 results:

- `v2_documented`: n `78`, precision `51.28%`, mean return `7.91%`, median `5.76%`, PF `2.76`.
- `v2_selective`: n `66`, precision `51.52%`, mean return `9.13%`, median `5.83%`, PF `3.05`.
- `v2_confirmation`: n `79`, precision `49.37%`, mean return `6.47%`, median `4.32%`, PF `2.16`.
- `v2_volatility_first`: n `86`, precision `46.51%`, mean return `4.66%`, median `3.47%`, PF `1.73`.

These are positive but low-count locked-OOS observations. They remain `candidate for further validation`, not a product recommendation. Some legacy formulas have no locked-OOS selections, demonstrating that discovery success does not guarantee temporal transfer.

### C-1: liquidity and cost stress

The V2 data-quality runner produced:

- Canonical rows: `4,680`
- Locked-OOS selected rows: `92`
- Dollar ADV available: `4,680`
- Observed spread available: `0`
- Short-interest freshness available: `0`
- Baseline cost stress: `insufficient_data`, eligible n `0`
- Spread stress: `insufficient_data`, eligible n `0`
- Impact stress: `insufficient_data`, eligible n `0`

The runner correctly withheld execution replay because spread was not observed for selected rows. ADV availability alone is not sufficient to claim realistic execution cost.

### OOS-1/OOS-2: rolling walk-forward

The V2 rolling runner generated three ordered signal-date windows. Locked-test net expectancy for the main candidates was:

- `score_top10`: `-2.4676%`, `+7.6555%`, `+2.2592%`; execution n `142`, `54`, `16`.
- `score_top10_rvol2`: `-3.5586%`, `+3.9992%`, `+10.8877%`; execution n `53`, `16`, `6`.
- `score_top10_atr4_rvol2`: `-3.2972%`, `+4.9075%`, `+14.2787%`; execution n `45`, `14`, `5`.
- `score_top10_not_extended`: `-1.6088%`, `+9.3947%`, `-4.1545%`; execution n `97`, `46`, `12`.
- `score_top10_regime`: `-2.6337%`, `+13.5422%`, `+11.9708%`; execution n `71`, `22`, `6`.

The first locked window is negative for all listed candidates, and later windows have very small execution counts. The correct verdict is mixed temporal stability with insufficient power for a rule decision.

### R-1 and E-1: blocked data-dependent tests

The configured regime and signal-quality scripts were not counted as completed because their default path resolves to `research/data/backtest_out/enriched_signals_v2.csv`, which does not exist. The exit lab has the same path issue. These are runner/path defects, not negative strategy results.

Earnings/news segmentation was also not completed because consistent point-in-time earnings/news timestamps are not present in the available export. No event timestamps were inferred.

## Evaluation against quality gates

| Gate | Assessment |
|---|---|
| Adequate sample size | Mixed; broad tests are large, but strongest candidate cohorts and later OOS windows are small |
| Median consistent with mean | Not established; prior outlier-cap evidence shows material mean sensitivity |
| Positive after cost | Broad 5d proxy is positive, but realistic spread/impact execution cost is unavailable |
| Temporal stability | Not established; rolling windows are mixed and later samples shrink sharply |
| Cluster/bootstrap robustness | Canonical ATR6_entry_ok interval is positive, but multiple-testing and discovery selection remain |
| Path-aware execution validity | Not available from current export/cache |
| Independent locked OOS | Partial only; V2 locked-OOS is low-count and not sufficient for a product rule |

## Conclusions and next actions

1. The current evidence supports research hypotheses around ATR and confirmation filters, not a new scanner rule.
2. The stored barrier audit is negative across all tested score schemas.
3. The target sweep demonstrates that horizon and target conclusions change materially between 1d and 5d, but the label is close-to-close and the target construction is not a substitute for path-aware execution.
4. The strongest remaining blocker is data quality: forward OHLC/intraday paths, observed spreads, and point-in-time event timestamps.
5. The next research increment should repair runner input-path configuration and rerun R-1, signal-quality, and exit sensitivity tests against an explicitly selected artifact. That repair is tooling-only and must not alter product rules.
6. Before any Level B product proposal, rerun the candidate filters on a shared point-in-time universe with a locked date range, outlier caps, observed spread/ADV costs, cluster confidence intervals, and a minimum OOS sample policy.

## Phase 0-3 execution update (2026-07-28)

The implementation phase added a reproducible input manifest at
`data/backtest_out/research_start_20260727/phase0_input_manifest.json` and
executed path-aware tests against the available daily OHLC cache. The manifest
records input hashes, schemas, row counts, missingness, and duplicate keys.

### Path-aware execution replay

Command family: `research/p0_execution_replay.py`, 5-day horizon, 5 bps
slippage and 5 bps commission per side, $1,000 notional, 0.50% entry-drift
limit.

- Legacy quality profile: n `901`, net expectancy `+2.0968%`, PF `1.7778`,
	TP/SL/time rates `34.41% / 35.85% / 29.74%`.
- V2 confirmation profile: n `62`, net expectancy `-0.0046%`, PF `0.9993`,
	TP/SL/time rates `11.29% / 50.00% / 38.71%`.
- The legacy aggregate reports max drawdown `-589.16%`; this indicates that
	the simple aggregate is not a portfolio-safe performance measure and must
	not be read as deployable portfolio P&L.
- Rejections included discovery/validation exclusion, score thresholds,
	missing features, and insufficient forward bars. These are retained rather
	than silently dropped.

### V2 precision execution

The V2 runner produced 4,680 canonical rows over 1,216 symbols and 53 dates.
The main locked-OOS candidate summaries were:

- `score_top10`: n `62`, expectancy `-0.0046%`, PF `0.9993`.
- `score_top10_rvol2`: n `22`, expectancy `+4.5980%`, PF `1.9345`.
- `score_top10_atr4_rvol2`: n `19`, expectancy `+5.8916%`, PF `2.1636`.
- `score_top10_not_extended`: n `42`, expectancy `-0.1158%`, PF `0.9821`.
- `score_top10_first_signal`: n `10`, expectancy `-5.5456%`, PF `0.3487`.

The positive RVOL/ATR subsets are low-count hypotheses. They are not
validated strategy rules, especially because 11-13 selected rows in these
subsets were rejected for insufficient forward bars.

### Same-selection exit sensitivity

Using the identical V2 confirmation top-10 selection (`selected_n=600`), the
two exit profiles produced:

- `TP5/SL1`: locked-OOS n `62`, expectancy `+2.0501%`, PF `1.4284`.
- `TP5/SL1.5`: locked-OOS n `62`, expectancy `-0.0046%`, PF `0.9993`.
- Paired common executions: `568`; same outcome: `496`; `TP5/SL1` better:
	`227`; `TP5/SL1.5` better: `57`; mean paired delta `+0.7096` percentage
	points.

This is an exit-policy research signal only. It does not authorize changing
the production exit profile. A follow-up must include outlier caps,
period-by-period confidence intervals, portfolio-level drawdown, and a fully
locked OOS sample policy before any Level B proposal.

### Current phase artifacts

- Input manifest: `data/backtest_out/research_start_20260727/phase0_input_manifest.json`
- Path-aware smoke: `data/backtest_out/research_start_20260727/phase2_path_smoke/`
- P0 execution replay: `data/backtest_out/research_start_20260727/phase3_p0_execution/`
- V2 precision execution: `data/backtest_out/research_start_20260727/phase3_v2_precision/`
- Same-selection exit sensitivity: `data/backtest_out/research_start_20260727/phase3_exit_same_selection/`

## Governance status

## Complete sequential execution update (2026-07-28)

The council test sequence was executed in order against the locked research
inputs. This section supersedes neither the production rules nor the earlier
evidence; it records the additional runs and their limitations.

| Phase | Command / artifact | Scope and result | Label / cost | Verdict |
|---|---|---|---|---|
| P0 | `scripts/research_input_manifest.py` | Five input artifacts hashed; CSV schemas, missingness, duplicate keys, and date ranges recorded | Close-to-close warning retained; no fabricated values | Completed; methodology control |
| P1 | `pytest` focused suite | `62 passed`, one existing `datetime.utcnow()` deprecation warning | Contract/unit tests; no trading cost | Completed |
| P2 | `full_universe_robustness.py`, earliest/latest, 400 bootstrap | 53,859 raw rows; 27,386 symbol-days; earliest and latest produced the same displayed recommended-rule counts; ATR6 and confirmation lifts remain discovery findings | `resolved_pct_t5 >= 5%`, close-to-close; cluster bootstrap | Candidate for further validation, not a rule |
| P2 | `threshold_false_negative_audit.py` | 20,811 positive proxy rows; 20,067 rejected by `entry_ok`; 19,813 below raw score 3 | Close-to-close; no execution cost | Negative coverage diagnostic; no gate change |
| P2 | `signal_quality_lab.py` | V3 n=6,410; top 10% precision 58.7% for >=5%; top 2% 61.2%; top-5/day 57.8% | Close-to-close; proxy only | Candidate for further validation |
| P2 | `score_formula_comparison.py` | V2 locked-OOS formula results positive but low-count; legacy and V2 universes kept separate | Close-to-close; 0.55 pp cost assumption | Candidate for further validation |
| P3 | `full_universe_barrier_backtest.py` | 53,746 rows; 27,308 dedup rows; 549 viable path-aware configurations; apparent leaders concentrate in ATR6+RVOL2 and 5-10 day horizons | Daily OHLC high/low/close; 0.55% round-trip cost | Candidate for further validation; multiple-testing and outlier risk |
| P3 | `p0_execution_replay.py` and V2 precision runner | Legacy quality n=901, +2.0968%, PF 1.7778; V2 main n=62, -0.0046%, PF 0.9993; ATR4+RVOL2 n=19, +5.8916%, PF 2.1636 | Path-aware OHLC; 5 bps slippage + 5 bps commission each side; $1,000 notional | Main V2: `NO EDGE`; small subsets: candidate for further validation |
| P3 | Same-selection exit sensitivity | Locked-OOS TP5/SL1 n=62, +2.0501%, PF 1.4284; TP5/SL1.5 n=62, -0.0046%, PF 0.9993; paired mean delta +0.7096 pp | Same path-aware OHLC and costs | Candidate for further validation; no production exit change |
| P4 | `portfolio_target_backtest.py` | 43,031 resolved rows; 36 finite-slot configurations; top-N, overlap, sizing, regime, and exit-policy screens generated | Daily OHLC; 0.55% round-trip; 100,000 capital; 20 slots | Research screen only; not deployable P&L |
| P5 | `score_lab_2_exits.py` and barrier grid | Close proxy says tighter/selective gates lift precision; path-aware grid shows large apparent gains in selected high-volatility cohorts | Close proxy plus daily OHLC; costs recorded per runner | Candidate for further validation; outlier/cap/OOS gate remains |
| P6 | `score_calibration.py` and `score_lab_3_regime.py` | Score bands are broadly monotonic: 0-20 = 17.0% vs 50-65 = 58.9% >=5% hit; Tier A 73.1% matches 73% assumption, Tier B/C each 4 pp below assumptions; 2026 OOS lifts fall versus 2025 IS | Close-to-close; no spread/impact data | Calibration monitor passed; recalibration is Level B pending |
| P6 | `v2_walk_forward_runner.py` | Runner completed but generated empty test folds for the requested window configuration | Path-aware OHLC; 5 bps + 5 bps | `insufficient_data` / blocked for this configuration |
| P6 | Earnings/news segmentation | Required consistent point-in-time timestamps were not present | No values inferred | `insufficient_data` |

### Understandable interpretation

1. The entry diagnostics are useful for ranking hypotheses, but the strongest
	close-to-close combinations do not automatically survive path-aware
	execution. This is visible in the contrast between large proxy lifts and
	the V2 main execution expectancy of approximately zero.
2. The strongest small path-aware subsets are not yet reliable strategy
	candidates: their execution counts are 19-22 and several selected rows
	lack the required forward bars.
3. The TP5/SL1 result is a paired exit signal, not an approved exit change.
	It must pass capped-outlier, period-by-period, portfolio, and independent
	OOS tests before a Level B proposal could be drafted.
4. Spread and impact remain unavailable. ADV availability does not substitute
	for observed spread or broker fill evidence, so realistic net execution
	profitability remains `insufficient_data`.
5. The walk-forward command is operationally valid but the selected date
	windows contain no usable test folds. This is a data-window limitation, not
	evidence of either edge or no edge.

### Rule preservation

Throughout this sequence, the currently used rules remained unchanged:

- `legacy_quality`: TP 2.0 ATR / SL 1.0 ATR / horizon 5.
- `v2`: TP 5.0 ATR / SL 1.0 ATR / horizon 5.
- `v2_atr4_rvol2`: TP 5.0 ATR / SL 1.0 ATR / horizon 5.

No scanner gate, score weight, entry/exit rule, sizing, risk limit, portfolio
capacity, paper gateway, live gateway, or scheduler behavior was changed. The
four relative-path corrections made during this run affect research script
input resolution only.

### Phase artifacts

- Manifest: `data/backtest_out/research_start_20260727/phase0_input_manifest_20260728.json`
- Entry earliest/latest: `data/backtest_out/research_start_20260727/phase2_entry_earliest/`, `phase2_entry_latest/`
- False-negative and ranking logs: `data/backtest_out/research_start_20260727/phase2_*`
- Barrier grid: `data/backtest_out/research_start_20260727/phase3_barrier_grid/`
- Execution and exit: `data/backtest_out/research_start_20260727/phase3_*`
- Portfolio: `data/backtest_out/research_start_20260727/phase4_portfolio_target_backtest.json`
- Calibration/regime/OOS logs: `data/backtest_out/research_start_20260727/phase6_*`

## Governance status

No scanner, score, target, stop, sizing, portfolio, or live-execution rule was changed. No Level B or Level C decision is presented as approved. The research outputs are stored under `data/backtest_out/research_start_20260727/`; the plan and this report are under `reports/`.
