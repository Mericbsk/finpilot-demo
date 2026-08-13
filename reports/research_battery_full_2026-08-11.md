# FinPilot Full Research Battery Report

Date: 2026-08-11
Status: research-only evidence; no production promotion
Authority layer: Research / Engineering
Decision level: Level A for isolated diagnostics; scanner, publication, risk and live-rule changes remain Level B/C.

## Scope and Data Identity

All runs in this report are diagnostics on the current export. No production scanner, score, ranking, entry/exit, portfolio, execution, publication or live behavior was changed. The current fixed-target artifact identifies the input as `data/backtest_out/full_universe_enriched.csv`, SHA-256 `e3b183552c7c38755528d133327a0c0601fe0cfff49ba58b9e360d17716ed3d3`, with 100,440 raw rows, 48,727 canonical rows and 26,372 path-resolved rows over 2025-09-11..2026-07-09. Some auxiliary diagnostics resolve a different deduplicated/resolved count because their loaders and horizon requirements differ; those counts are reported separately and must not be merged.

The locked OOS was not opened. The current export has unresolved cache discontinuities, incomplete point-in-time provenance and missing observed spread/slippage/impact fields. Therefore, no result below is promotion evidence.

## Completed Artifacts

- Strategic Lab: `data/backtest_out/strategic_lab_2026-08-10.json` — 17 completed, 1 partial.
- Ten Perspectives Lab: `data/backtest_out/ten_perspectives_lab_2026-08-10.json` — 13 completed; two constant-input correlation warnings.
- Mirror Analysis: `data/backtest_out/mirror_analysis_2026-08-10.json` — 9 completed.
- Fixed-target full-universe protocol: `data/backtest_out/fixed_target_full_universe_2026-08-11.json` and `.md` — 3,120 configurations.
- Decision quality: `data/backtest_out/decision_quality_experiments_2026-08-11.json` — completed.
- Stability/concentration/capacity: `data/backtest_out/stability_concentration_capacity_2026-08-11.json` — completed.
- Honest score calibration: `data/backtest_out/honest_score_calibration_2026-08-11.json` — completed.
- Timing/drift: `data/backtest_out/timing_drift_study_2026-08-11.json` — completed, diagnostic-only.
- Price-cache integrity: `data/backtest_out/price_cache_integrity_audit_2026-08-11.json` — diagnostic-only.
- Matched null: `data/backtest_out/negative_controls_2026-08-11.json` — 1,000 permutations per family.

Focused validation: 27 tests passed across Strategic, Ten Perspectives, Mirror and close-to-close export tests.

## Entry, TP/SL and Exit Findings

The fixed-target protocol tested TP values of 3%, 5%, 7% and 10%, fixed stops of 2%, 3% and 5%, ATR stops of 1, 1.5 and 2 times ATR, and horizons of 1, 3, 5, 10 and 20 bars. It tested 3,120 configurations after temporal splitting and multiple-testing accounting.

Direct all-candidate fixed-stop results under the declared 55 bps round-trip scenario show no robust positive median. The best mean-net configuration for each target/stop pair was still selected over the grid, not independently validated:

| Fixed stop | Target | Best horizon | n | Gross mean % | Net mean at 55 bps % | Net median at 55 bps % |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2% | 3% | 5 | 26,372 | 0.023 | -0.527 | -2.550 |
| 2% | 5% | 20 | 26,372 | 0.297 | -0.253 | -2.550 |
| 2% | 7% | 20 | 26,372 | 0.466 | -0.084 | -2.550 |
| 2% | 10% | 20 | 26,372 | 0.687 | 0.137 | -2.550 |
| 3% | 3% | 20 | 26,372 | 0.010 | -0.540 | -0.348 |
| 3% | 5% | 20 | 26,372 | 0.318 | -0.232 | -3.550 |
| 3% | 7% | 20 | 26,372 | 0.514 | -0.036 | -3.550 |
| 3% | 10% | 20 | 26,372 | 0.772 | 0.222 | -3.550 |
| 5% | 3% | 20 | 26,372 | 0.106 | -0.444 | 2.450 |
| 5% | 5% | 20 | 26,372 | 0.462 | -0.088 | 4.450 |
| 5% | 7% | 20 | 26,372 | 0.689 | 0.139 | -1.155 |
| 5% | 10% | 20 | 26,372 | 0.989 | 0.439 | -5.550 |

These are capped barrier outcomes and therefore target-cap/time-exit artifacts are plausible, especially where the median equals the target or stop-adjusted value. The fixed-target global gates were: FDR discoveries 1,012 of 3,120; CPCV/PBO 0.6; White Reality Check p=0.7413; Hansen SPA p=0.7761; locked holdout not opened. This does not validate any TP/SL rule.

The long ATR barrier grid was stopped after the broader fixed-target protocol completed; no ATR-grid artifact is claimed as completed.

## Entry Selection and Score

Decision-quality diagnostics used a 5-day triple-barrier target with a 55 bps scenario cost. The eligible cohort contained 305 rows and had mean net return -1.4361%, median -3.3977% and positive rate 30.16%. The full comparison cohort had mean -0.1755%, median -1.8605% and positive rate 39.75%. This descriptive counterfactual does not support `entry_ok` as a profitable selector.

Honest score calibration used 39,297 observations, trained before 2026-06-15 and evaluated after that date. Train Brier score was 0.240359 and test Brier score 0.236560. Test observed rates were generally below the fitted training probabilities in the populated 0–80 score bands; the 80–100 test band had only 20 observations and was marked insufficient data. Calibration is not a production probability guarantee.

Feature lineage correctly rejects forward outcome fields in the enriched export: `resolved_pct_t5`, `resolved_pct_1d`, `c2c_1d`, `c2c_5d` and `mae_t5`. They must remain labels/outcomes, never features.

## Timing, Stability and Null Controls

Timing/drift resolved 36,336 rows from 48,760 deduplicated rows, with 12,424 short forward paths. For one-day signal-close returns, the raw mean was 6.8838% but the median was 0%, trimmed mean -0.0290%, and the top five percent contributed 108.0% of the total. At next-open, the mean was 0.1130% and trimmed mean -0.0014%; benchmark-adjusted trimmed means were negative. This is strong evidence of outlier sensitivity, not a stable daily edge.

The daily half-life diagnostic found 2,438 eligible rows: day-1 median 0.0311% and positive rate 50.21%; day-5 median -0.6711% and positive rate 44.71%. Intraday half-life remains blocked because intraday bars and execution-cost observations are unavailable.

The matched-null run completed 1,000 permutations per null family. The recorded `entry_ok` candidate did not separate positively from the matched null distributions. The experiment registry reports 3 experiments and 6,000 completed runs, with the null family accounting for 6,000 runs; this is selection-bias exposure, not confirmation.

## Integrity and Governance Gates

| Gate | Status | Evidence |
| --- | --- | --- |
| Diagnostic batteries | COMPLETED | 39 named experiments plus focused tests; Strategic includes one partial experiment. |
| Fixed TP/SL matrix | COMPLETED | 3,120 configurations; global reality-check p-values non-significant. |
| Price-cache integrity | HOLD | 485 of 2,047 symbols have at least one close jump of 50% or more; median largest flagged jump 173.57513%. |
| Matched-null control | FAILED FOR CANDIDATE | Candidate did not outperform recorded null families. |
| Feature leakage preflight | COMPLETED WITH BLOCK | Forward outcome columns present and prohibited as features. |
| Restatement comparison | BLOCKED | No immutable prior bar-cache snapshot exists. |
| Observed execution costs | INSUFFICIENT DATA | Spread, slippage and impact fields are missing; declared costs are scenarios only. |
| Locked OOS | NOT OPENED | Opening requires human approval. |
| H1/H2/H3 confirmatory runs | HOLD | Integrity, provenance and execution gates are not open. |
| Production behavior | NOT CHANGED | No production edits or promotion occurred. |

## Final Decision

The feasible research battery is complete for the current data slice, with the stated partial and blocked items. It does not validate regular weekly total gains of 5–10%, a production score interpretation, an `entry_ok` edge, or any TP/SL/exit rule. The apparent positive means at some high targets are dominated by target caps, time horizons and outliers, while medians, null controls, reality checks and data-integrity gates remain unfavorable or incomplete.

Next admissible work is data remediation and measurement: explain price-cache jumps, obtain immutable point-in-time snapshots and publication metadata, and collect observed spread/slippage/impact plus intraday bars. Confirmatory H1/H2/H3 runs and production changes remain HOLD.
