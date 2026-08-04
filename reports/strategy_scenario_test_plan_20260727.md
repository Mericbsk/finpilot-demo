# FinPilot Strategy Expansion and Scenario Test Plan

Date: 2026-07-27
Layer: 03-research
Escalation: Level A for research execution; Level B/C for any product, risk, sizing, stop-loss, leverage, or live-rule change
Status: research-only; no production rule change

## Objective

Test alternatives around the existing FinPilot strategy without changing the scanner, product rules, or execution gateway. Treat `resolved_pct_t5 >= 5%` as a close-to-close research proxy only. Do not interpret it as intraday peak-touch or tradeable P&L.

## Test matrix

| ID | Test | Data / runner | Status | Decision gate |
|---|---|---|---|---|
| DQ-1 | Symbol-day canonicalization | `full_universe_robustness.py` | runnable | earliest/ latest policy recorded |
| DQ-2 | Duplicate and missingness inventory | full-universe CSV | runnable | report coverage and duplicate count |
| T-1 | T+3/T+5/T+10 horizon and target sweep | existing target-return / outcome artifacts | partial | no peak-touch claim without OHLC |
| T-2 | ATR, RVOL, gap, entry and composite thresholds | `full_universe_robustness.py`, threshold audit | runnable | minimum n, coverage, recall, stability |
| T-3 | Constrained 2/3-factor combinations | `full_universe_robustness.py` | runnable | reject redundant and small-n findings |
| B-1 | Triple-barrier baseline by schema | `scripts/barrier_audit.py`, existing barrier artifacts | runnable with stored DB/artifacts | TP/SL/time, median, PF, permutation |
| B-2 | ATR TP/SL and fixed target sensitivity | `research/score_lab_2_exits.py`, stored barrier runs | runnable / proxy-limited | no stop conclusion without path OHLC |
| B-3 | Outlier caps | existing `barrier_atr50/200` artifacts | runnable from stored results | edge must survive caps |
| A-1 | Score component ablation | `research/score_lab_1_weights.py`, `scripts/component_ablation.py` | runnable / source-dependent | discovery only; no weight promotion |
| R-1 | Trend/range and volatility regime | `research/score_lab_3_regime.py` | runnable | segment stability and minimum n |
| C-1 | Point-in-time liquidity/spread/cost stress | `research/v2_data_quality_cost_runner.py` | blocked | price cache is empty; no fabricated ADV/spread |
| OOS-1 | Temporal discovery/validation/locked-OOS | existing p0/v2 runners and canonical output | partial | locked OOS cannot tune parameters |
| OOS-2 | Walk-forward calibration | `research/walkforward.py` | runnable if KPI signals exist | insufficient data is a valid result |
| E-1 | Earnings/news segmentation | existing fields / data availability | partial | requires point-in-time timestamps |

## Common controls

Every quantitative result must include dataset, date range, row count, duplicate policy, cost assumption, and whether the label is close-to-close or path-aware. Results with small cohorts, redundant filters, uncapped ATR outliers, or discovery-only selection are hypotheses, not strategy decisions.

## Execution order

1. Data quality and canonical baseline.
2. Threshold and constrained combination battery.
3. Barrier, exit, and outlier sensitivity.
4. Score ablation and regime segmentation.
5. Liquidity/cost and temporal OOS gates.
6. Consolidated evaluation and Level B/C escalation notes.

## Stop conditions

- Do not edit `/01-product/*`.
- Do not change scanner weights, entry/exit behavior, position sizing, leverage, or live execution.
- Do not claim success from a single hit-rate, mean expectancy, or small cohort.
- If required data is missing, report `insufficient_data`; do not zero-fill or infer it.
