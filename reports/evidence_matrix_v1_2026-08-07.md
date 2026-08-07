# FinPilot Evidence Matrix v1

Date: 2026-08-07
Status: Research-only diagnostic artifact
Authority layer: Research
Decision level: Level A for evidence inventory; any rule, risk, broker or
production change remains Level B/C.
Scope: Existing FinPilot research evidence through 2026-08-06. This document
freezes the current evidence state; it does not run a new strategy search.

## Purpose

This matrix answers one question:

> Which evidence gates has FinPilot actually passed, which gates failed, and
> which gates have not been opened or cannot yet be measured?

The matrix is not a strategy score, alpha score, confidence score or promotion
recommendation. `unknown`, `insufficient_data` and `not_opened` are explicit
states. They do not count as passes.

## Status vocabulary

| Status | Meaning | Promotion effect |
| --- | --- | --- |
| `PASS` | The defined gate is supported by the available evidence and its minimum conditions are met. | May proceed to the next gate, subject to all other gates. |
| `FAIL` | The evidence contradicts the gate or its minimum condition is not met. | Candidate stops for the current protocol. |
| `UNKNOWN` | The question is relevant but the available artifact cannot answer it. | Cannot support a promotion claim. |
| `INSUFFICIENT_DATA` | The measurement exists, but sample, coverage or lineage is below the declared minimum. | Cannot be treated as a pass. |
| `NOT_OPENED` | The gate is intentionally locked or awaiting approval. | No conclusion about strategy quality may be drawn. |
| `PARTIAL` | A bounded sub-test passed, but the complete gate contract is incomplete. | Diagnostic only; not a promotion pass. |

## Gate matrix

| Gate | Status | What is established | What is missing or failed | Evidence locator |
| --- | --- | --- | --- | --- |
| Hypothesis identity and reproducibility | `PARTIAL` | Evidence identity, feature timestamps, label version and cost metadata have research contracts. | Full row-level live/research score equivalence is still open; the 16.0/16.5 score-ceiling discrepancy remains unresolved. | `reports/research_program_execution_2026-08-06.md`; `research/evidence_ledger.py`; `research/score_bridge.py` |
| Discovery | `PASS` | Entry, score, ATR, RVOL, gap, composite, multi-timeframe and exit hypotheses have been registered and tested as research candidates. | Discovery success is not a strategy claim; broad search creates multiple-testing and selection exposure. | `reports/entry_quality_experiment_2026-08-06.md`; `reports/research_program_execution_2026-08-06.md` |
| Negative-control preflight | `NOT_OPENED` | No repository result currently establishes that the complete pipeline rejects matched random or permuted signals. | Label permutation, signal permutation and time-shift null distributions are not yet a mandatory preflight. | No completed negative-control artifact; deferred work recorded in `docs/governance/decision-log.md` |
| Standardized validation | `PARTIAL` | Canonical symbol-day deduplication, daily OHLC barrier labels, cost scenarios and common summary fields exist. | The broadest results remain sensitive to exit, horizon, selection and data lineage; no candidate is validated for promotion. | `research/full_universe_barrier_backtest.py`; `reports/fixed_target_full_universe_2026-08-05.md` |
| Realized path outcome | `PARTIAL` | Daily OHLC triple-barrier results use TP/SL/time ordering and stop-first same-bar handling. | Daily bars do not prove intraday fill ordering, spread, slippage or actual execution. Favorable movement fields remain non-P&L metrics. | `scanner/labeling.py`; `reports/entry_quality_experiment_2026-08-06.md` |
| Economic / cost-adjusted validation | `FAIL` | Fixed cost scenarios were applied; the $10,000 portfolio changed from positive to negative as assumed cost rose from 0.55% to 1.00%. | Observed spread and impact are unavailable; fixed cost is an assumption, not a measured execution model. | `docs/governance/decision-log.md` entry dated 2026-08-06; `reports/stability_concentration_capacity_2026-08-06.md` |
| Distribution and outlier robustness | `FAIL` | Expanded grid leaders had negative medians, high stop rates and negative capped means despite very high raw means. | No candidate has demonstrated median-positive, cap-stable economics across the declared periods. | `docs/governance/decision-log.md` entry “Genişletilmiş giriş/çıkış gridinde outlier duyarlılığı”; `data/backtest_out/entry_exit_sweep_2026-08-06/` |
| Statistical integrity | `PARTIAL` | FDR, HAC, CPCV/PBO, White Reality Check and Hansen SPA are present in research protocols. | Research budget/family accounting and negative-control null distributions are not yet wired as a single mandatory gate; several broad candidate families remain non-significant or selection-exposed. | `reports/fixed_target_full_universe_2026-08-05.md`; `reports/strategy_scenario_test_results_20260727.md` |
| Temporal robustness | `PARTIAL` | Train and validation diagnostics exist. Train median was -2.0039% and validation median -1.0500% in the 2026-08-06 stability run. | Locked OOS was not scored; prior rolling windows were mixed and later execution counts were small. | `reports/stability_concentration_capacity_2026-08-06.md`; `reports/strategy_scenario_test_results_20260727.md` |
| Market/regime robustness | `UNKNOWN` | Regime and monthly diagnostics indicate material variation. | A complete, adequately powered market/regime transfer gate has not been passed. | `reports/entry_quality_experiment_2026-08-06.md`; `reports/stability_concentration_capacity_2026-08-06.md` |
| Cross-sectional robustness | `INSUFFICIENT_DATA` | A sector and ETF-proxy diagnostic exists. | Historical sector coverage was approximately 8.31%; ETF groups are not pairwise candidate correlation; no decision-grade full-universe sector or correlation result exists. | `reports/stability_concentration_capacity_2026-08-06.md` |
| Rejection / veto quality | `FAIL` | Rejected observations were evaluated counterfactually. | Of 26,863 rejected observations, 11,225 had positive counterfactual net outcomes, a 41.79% false-rejection rate; this does not support a production No-Trade rule. | `reports/stability_concentration_capacity_2026-08-06.md`; `data/backtest_out/stability_concentration_capacity_2026-08-06.json` |
| Locked OOS | `NOT_OPENED` | Locked partitions and metadata exist. | The primary locked holdout remains unopened; no candidate has a one-time final result on the reserved full-universe holdout. | `reports/fixed_target_full_universe_2026-08-05.md`; `data/backtest_out/locked_holdout_opened.json` |
| Execution feasibility | `UNKNOWN` | Entry drift and data-quality warnings are measured in parts of the research path. | Observed spread rate is 0%; intraday forward OHLCV is missing; fill delay, slippage and execution decay cannot be measured honestly. | `reports/stability_concentration_capacity_2026-08-06.md`; `reports/strategy_scenario_test_results_20260727.md` |
| Capacity | `INSUFFICIENT_DATA` | A current liquidity snapshot reports dollar ADV and a position-notional/ADV diagnostic. | Snapshot was not joined to historical outcomes; observed spread is absent; historical capacity and impact are not validated. | `reports/stability_concentration_capacity_2026-08-06.md` |
| Shadow | `NOT_OPENED` | Observation-only shadow tracking has been discussed as a boundary. | No completed candidate has passed the required OOS, economics and execution gates for a controlled shadow protocol. | `docs/governance/decision-log.md` dated 2026-08-06; `reports/research_program_execution_2026-08-06.md` |
| Production promotion | `NOT_OPENED` | Production behavior has intentionally remained unchanged. | No validated, robust, cost-positive, executable and shadow-approved candidate exists; no Alpaca order was sent. | `docs/governance/decision-log.md` dated 2026-08-06 |

## Current evidence conclusion

The current research program has passed the ability to produce and audit
hypotheses. It has not established a production-grade, tradeable edge.
In particular:

- the fixed-target run produced zero gross-plus-period-stable configurations
  and zero cost-positive configurations under its declared gates;
- the expanded entry/exit grid produced outlier-sensitive leaders rather than
  robust candidates;
- the $10,000 portfolio result was close to break-even and cost-sensitive;
- the locked OOS, observed execution cost, intraday path and decision-grade
  capacity gates remain unopened or incomplete;
- the current rejection surface cannot be promoted to a production No-Trade
  engine based on its measured counterfactual false-rejection rate.

These are evidence-status conclusions, not claims that no future edge can
exist.

## Deferred minimum research spine

The following work is intentionally deferred until after the launch-critical
work. It is not part of this matrix and must not be inferred as completed:

1. write-once experiment registry with hypothesis-family and research-budget
   accounting;
2. negative-control preflight with matched null distributions, separated from
   candidate-level permutation significance;
3. one end-to-end candidate run through the complete gate chain;
4. observed spread, fill, slippage and execution-delay telemetry;
5. human-approved one-time locked-OOS opening.

When this work starts, `INSUFFICIENT_DATA` must include a reason code and the
missingness threshold that caused it. Repeated insufficient-data states cannot
be used to bypass a mandatory gate.

## Governance boundary

This artifact is Level A research inventory only. It does not:

- change `scanner/` entry, score, exit or risk behavior;
- add a No-Trade or veto rule;
- alter portfolio sizing;
- open the locked OOS;
- send Alpaca or paper orders;
- create a production or public profitability claim.

Any future research doctrine, registry contract, product rule, risk rule,
execution behavior or broker action must be handled under the applicable
Level B/C approval process.
