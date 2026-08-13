# Entry Candidate P0-P3 Research Run

Date: 2026-08-07
Level: A
Layer: Research
Status: applied, research-only

## Scope

This run evaluates the frozen `entry_ok` candidate through the existing P0-P3 research gates. It does not change scanner behavior, score computation, entry/exit rules, risk, portfolio, publication, broker configuration, or production behavior.

No locked OOS was opened. No shadow run or order was started.

## Reproducibility

- Command: `python -m research.candidate_pipeline --permutations 1000`
- Canonical input: `data/backtest_out/full_universe_enriched.csv`
- Input SHA-256: `38b981b372571a01b727d6a51f3fd8b918a770f7a53e552ef55e1629c142e896`
- Raw rows: 53,859
- Candidate resolved observations: 799
- Daily price cache: `data/price_cache`
- Candidate: existing `entry_ok`; no new parameter search
- P2 target: 5-day daily-OHLC triple-barrier outcome
- P2 barrier: TP 2.0 ATR, SL 1.0 ATR, horizon 5
- P2 costs: 0.25%, 0.55%, and 1.00%
- P1: 1,000 permutations per family, seed base `20260807`
- Registry: `data/research_experiments.db`
- P0-P3 artifact: `data/backtest_out/research_run_2026-08-07_entry_ok_p0_p3.json`

The registry contains 3,000 immutable permutation run records with run indexes 0 through 2,999. The earlier write-once P1 experiment metadata was created with `planned_runs=1000`; because the record is immutable it was not edited. The implementation now registers future P1 experiments with `permutations * 3` planned runs.

## Results

### P0: score-equivalence replay

Status: `INSUFFICIENT_DATA`

The canonical dataset does not contain these required production score fields:

`alignment_ratio`, `filter_score`, `momentum_ratio`, `price_momentum`, `recommendation_score`, `trend_strength`, `volume_spike`.

The replay therefore did not infer or reconstruct score values. This gate is not a pass.

Follow-up telemetry recovery was attempted from 63 historical suggestion CSV
exports. The deterministic builder selected the latest intraday record for each
of 303 unique symbol-day keys from 602 rows, recorded 115 duplicate keys and 57
keys with conflicting intraday score values, and joined the nearest canonical
intraday record by timestamp. The seven non-volatility score fields were
present, but all 303 selected rows lacked a historical `vol_regime` value after
the timestamp-aligned join. Strict replay therefore remained
`INSUFFICIENT_DATA` (`compared=0`, `invalid_rows=303`); no default volatility
regime was invented. Artifacts: `research/build_score_replay_input.py`,
`data/backtest_out/score_replay_input_2026-08-07.csv`,
`data/backtest_out/score_replay_input_2026-08-07.json` and
`data/backtest_out/research_run_2026-08-07_score_replay_telemetry.json`.

The current JSON scan export was then replayed after adding support for its
`results` payload and `score_component_total` alias. It contains 1,801 rows;
1,570 rows have complete required component fields and persisted breakdowns,
while 231 rows are invalid because telemetry fields are missing. Persisted
breakdown accounting has four strict `0.001` total discrepancies (EMR, MGEE,
LOW and SYY), all consistent with one-decimal-in-the-third-place rounding
differences but retained as mismatches under the strict tolerance. Independent
bridge recomputation mismatched all 1,570 comparable rows because the export
does not preserve every feature-flag/input alias used to reconstruct squeeze,
catalyst, lottery and overnight score paths. Current replay artifact:
`data/backtest_out/research_run_2026-08-07_score_replay_current.json`.

The export-contract fix is now implemented for future evaluator rows, but has
not been applied retroactively to this immutable export. New rows persist
`recommendation_score`, the exact `score_input` mapping, and the
`score_feature_flags` snapshot used by the production score engine. Strict
replay consumes those nested fields and restores the recorded flags while
recomputing. This is a Level B scanner/export contract proposal and requires
human approval before it is treated as an approved production change.

### P1: matched-null controls

All three families completed with 1,000 permutations:

| Family | Null mean | Null median | P05 | P95 | Candidate percentile |
| --- | ---: | ---: | ---: | ---: | ---: |
| Label permutation | 0.030151% | -0.198878% | -0.568287% | 1.722515% | 0.020 |
| Signal permutation | 0.340015% | -0.499621% | -0.856117% | 5.755813% | 0.272 |
| Time shift | -0.514939% | -0.674665% | -1.012398% | -0.225876% | 0.564 |

Candidate mean net return under the P1 configuration was `-0.6387102336%` across 799 observations. The label-permutation percentile is low because the candidate result is below nearly all matched label-null outcomes; this is not evidence of a positive edge.

P1 status: completed as a diagnostic distribution run. It does not promote the candidate.

### P2: standardized cost and temporal validation

| Cost scenario | N | Mean net return | Median | Positive net rate |
| --- | ---: | ---: | ---: | ---: |
| Low, 0.25% | 799 | -0.142591% | -2.393951% | 40.3004% |
| Base, 0.55% | 799 | -0.442591% | -2.693951% | 39.1740% |
| High, 1.00% | 799 | -0.892591% | -3.143951% | 37.7972% |

Base-cost temporal split:

- Train dates: 2025-09-15 through 2026-05-13; N=574; mean `-0.171665%`; positive net rate `41.4634%`.
- Validation dates: 2026-05-14 through 2026-07-13; N=225; mean `-1.133753%`; positive net rate `33.3333%`.

P2 result: negative in all cost scenarios and worse in the later validation period. This is a research finding, not a production rule change.

### P3: robustness and capacity diagnostics

Existing robustness diagnostics were rerun as part of the pipeline:

- False-rejection rate: `41.7861%` (`11,225 / 26,863`).
- Liquidity source: snapshot only, N=1,561.
- Snapshot liquidity-ok rate: `11.8514%`.
- Observed spread-source rate: `0%`.
- Historical outcomes were not joined to the liquidity snapshot.

P3 capacity and execution evidence remain insufficient for a deployability decision.

## Gate summary

| Gate | Status | Reason |
| --- | --- | --- |
| P0 score replay | INSUFFICIENT_DATA | Required production score fields absent |
| P1 matched nulls | COMPLETED / diagnostic | 3,000 immutable runs recorded; no promotion decision |
| P2 standardized validation | FAIL | Negative mean at low/base/high costs; validation deterioration |
| P3 robustness | FAIL / INSUFFICIENT_DATA | False rejection persists; capacity and execution evidence incomplete |
| Locked OOS | NOT_OPENED | Governance and data prerequisites remain unmet |
| Execution | UNKNOWN / INSUFFICIENT_DATA | No observed spread/impact telemetry |
| Capacity | INSUFFICIENT_DATA | Snapshot is not historically joined to outcomes |
| Shadow | NOT_ELIGIBLE | Upstream evidence gates are not satisfied |
| Production | NOT_OPENED | No human production decision was requested or made |

## Decision boundary

This run is a Level A research-only implementation and diagnostic execution. It is not approval for a live rule, paper order, shadow deployment, broker action, risk change, portfolio change, or production release. The P0 score-equivalence contract and execution/capacity gates remain open.

## Validation

Focused telemetry and replay tests: `11 passed`. The research pipeline
regression subset also passed `4 tests`. The pre-existing
`datetime.utcnow()` deprecation warning in `scanner/data_fetcher.py` remains.

Validated modules:

- `research/experiment_registry.py`
- `research/negative_control.py`
- `research/score_replay.py`
- `research/candidate_pipeline.py`
- `tests/test_experiment_registry.py`
- `tests/test_negative_control.py`
- `tests/test_score_replay.py`
- `tests/test_candidate_pipeline.py`

Syntax compilation and `git diff --check` completed. The only observed test warning was the pre-existing `datetime.utcnow()` deprecation in `scanner/data_fetcher.py`.

## End-to-end conclusion

The research sequence is complete for the frozen `entry_ok` candidate. P1 is
fully recorded as a diagnostic null-distribution run, while P2 is negative at
all three cost assumptions and deteriorates in the later validation period.
P3 does not contain sufficient historical spread, impact, or capacity
evidence. P0 is not closed: the immutable historical export fails strict
independent score equivalence because telemetry and score-contract context are
missing.

No locked OOS, shadow run, paper order, live order, broker action, risk change,
product-rule change, publication promotion, or production release occurred.
The next evidence-producing action is a new export generated after Level B
approval of the telemetry contract, followed by a fresh P0 replay with a new
input hash and separately labelled P1-P3 rerun.
