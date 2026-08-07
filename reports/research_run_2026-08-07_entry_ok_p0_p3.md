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

Focused tests: `6 passed`.

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
