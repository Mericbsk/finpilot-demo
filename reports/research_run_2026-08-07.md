# Research Run 2026-08-07

Date: 2026-08-07
Protocol: [Research Operating Plan v2](research_test_plan_v2_2026-08-07.md)
Baseline: [Evidence Matrix v1](evidence_matrix_v1_2026-08-07.md)
Scope: Research-only execution; no production, broker, paper-order, locked-OOS
or shadow action was performed.

## Executive result

The executable P0/P3 slice was run in sequence. P0 contract and fixture tests
passed. Existing research-only decision-quality and stability/capacity analyses
were rerun into dated artifacts. The run did not turn any blocked gate into a
pass:

- P0 fixture/contract slice: `PASS`.
- P0 full row-level live/research score replay: `PARTIAL`, not opened by this
  run because the required common timestamped replay dataset is not registered.
- P1 negative-control permutation preflight: `NOT_OPENED`; no matched-null
  runner is present in the current research surface.
- P2 standardized candidate validation: `PARTIAL`; existing artifacts were
  reused/checked, but no new candidate family was selected or promoted.
- P3 temporal/rejection/liquidity diagnostics: `FAIL`/`INSUFFICIENT_DATA` in the
  same dimensions already recorded by Evidence Matrix v1.
- P4 locked OOS: `NOT_OPENED`.
- P5 execution: `UNKNOWN`/`INSUFFICIENT_DATA` because observed spread is absent.
- P6 capacity: `INSUFFICIENT_DATA`; current snapshot is not historical
  execution evidence.
- P7 shadow and P8 production decision: not eligible and not executed.

## Commands executed

### P0 focused integrity tests

```text
python -m pytest tests/test_p0_telemetry.py tests/test_score_contract.py tests/test_scanner_contract.py tests/test_evaluate.py tests/test_evidence_ledger.py tests/test_score_bridge.py tests/test_research_protocol.py -q
```

Result: `57 passed`, one pre-existing `datetime.utcnow()` deprecation warning.

### P0/P3 research contract tests

```text
python -m pytest tests/test_evidence_ledger.py tests/test_score_bridge.py tests/test_research_protocol.py tests/test_full_universe_robustness.py tests/test_decision_quality_experiments.py tests/test_stability_concentration_capacity.py tests/test_honest_score_calibration.py tests/test_research_input_manifest.py -q
```

Result: `23 passed`, one pre-existing `datetime.utcnow()` deprecation warning.

### Existing research-only analyses

```text
python -m research.decision_quality_experiments --out data/backtest_out/research_run_2026-08-07_decision_quality.json
python -m research.stability_concentration_capacity --out data/backtest_out/research_run_2026-08-07_stability.json
```

Both completed successfully. Streamlit emitted a no-runtime cache warning;
the commands still produced the requested artifacts.

## Observed evidence

### Decision quality

Artifact: `data/backtest_out/research_run_2026-08-07_decision_quality.json`

- `missing_paths=0`
- `short_paths=25`
- `rejected_entry_drift=158`
- `symbols_with_cache=1,929`
- Rejected-row counterfactual positive rates remained high:
  - missing entry eligibility: `41.7762%`
  - weak trend: `42.2245%`
  - high volatility: `40.3863%`
  - gap risk: `32.2581%`
  - near 52-week high: `40.7280%`
  - low relative volume: `42.2566%`

These are descriptive research results and do not authorize a No-Trade or
veto rule.

### Stability, rejection, concentration and liquidity

Artifact: `data/backtest_out/research_run_2026-08-07_stability.json`

- Canonical inventory: `27,125` resolved observations in the existing research
  path.
- Rejected observations: `26,863`.
- Counterfactual false-rejection rate: `41.7861%` (`11,225 / 26,863`).
- Liquidity snapshot: `n=1,561`, snapshot date `2026-08-06`.
- `liquidity_ok_rate=11.8514%`.
- Observed spread-source rate: `0%`.
- Snapshot was explicitly not joined to historical outcomes.

The output therefore preserves `INSUFFICIENT_DATA` for historical capacity and
`UNKNOWN`/`INSUFFICIENT_DATA` for observed execution costs.

## Gate interpretation

The run confirms that the integrity test surface is executable, but it does
not establish a tradeable production edge. The largest unexecuted research
item is P1 negative-control preflight. The next implementation task is a
write-once, matched-null runner with pre-registered family counts and
reproducible seeds. It must be completed before interpreting additional
candidate selection results.

The following actions remain explicitly blocked by protocol and governance:

- opening the locked OOS;
- tuning or selecting a candidate after holdout observation;
- using current liquidity as historical execution evidence;
- claiming realized P&L from favorable movement/MFE fields;
- sending Alpaca, paper or live orders;
- changing scanner, score, entry, exit, risk, portfolio or public behavior.

## Reproducibility

The two dated JSON artifacts are the direct outputs of the commands above.
The focused tests are deterministic repository tests. No new broad parameter
sweep was run.
