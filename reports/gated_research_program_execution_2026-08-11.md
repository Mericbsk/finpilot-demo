# FinPilot Gated Research Program Execution

Date: 2026-08-11
Layer: Research / Engineering
Level: A - research-only orchestration
Status: Program registered and evaluated; downstream phases intentionally blocked.

## What was completed

The proposed program was operationalized as a machine-readable manifest:

- Manifest: `data/backtest_out/gated_research_program_2026-08-11.json`
- Runner: `research/gated_research_program_2026_08_11.py`
- Focused tests: `tests/test_gated_research_program_2026_08_11.py`
- Planned phases: 10
- Corrected planned test count: 220, not 200
- Priority list: 25 tests
- Production change: `false`

The runner records phase availability and refuses to imply that blocked or
unopened tests have produced evidence. It does not open locked OOS, alter
scanner logic, or promote research hypotheses.

## Gate result

| Phase | Tests | Status | Reason |
|---|---:|---|---|
| P0 Research protocol | 12 | COMPLETED | Current export exists and protocol/lineage/null controls are available. |
| P1 Data reliability | 30 | BLOCKED | No PIT listing/delisting universe, corporate-action feed or immutable prior cache snapshot. |
| P2 Label and execution | 26 | BLOCKED | No observed spread/slippage/impact, ADV-conditioned fill data or intraday bars. |
| P3 Baselines and target semantics | 20 | NOT_OPENED | P2 prerequisite is blocked. |
| P4 Score decomposition | 28 | NOT_OPENED | P3 prerequisite is not open. |
| P5 Entry setup families | 30 | NOT_OPENED | P4 prerequisite is not open. |
| P6 Entry eligibility decomposition | 18 | NOT_OPENED | P5 prerequisite is not open. |
| P7 Exit, holding and risk | 20 | NOT_OPENED | P6 prerequisite is not open. |
| P8 Portfolio, risk and capacity | 16 | NOT_OPENED | P7 prerequisite is not open. |
| P9 Robustness and locked validation | 20 | BLOCKED | Locked OOS cannot open before the data and execution gates pass. |

## Existing evidence reused

The gate evaluator points to existing current-snapshot research artifacts,
without treating them as confirmation of a production edge:

- `data/backtest_out/scanner_battery_v2_2026-08-11.json`
- `data/backtest_out/price_cache_integrity_audit_2026-08-11_e2e.json`
- `data/backtest_out/negative_controls_current_2026-08-11.json`
- `reports/scanner_research_end_to_end_2026-08-11.md`

Those artifacts already show that the current `entry_ok` selection is not
validated, realistic execution is unavailable, and weekly 5-10% or monthly
10% performance claims are unsupported. The gated program does not erase or
reinterpret those findings.

## Rules now enforced

1. The test budget is predeclared by phase and family.
2. A blocked prerequisite prevents later phases from opening.
3. Missing data is `BLOCKED` or `NOT_OPENED`, never a positive finding.
4. Locked OOS is explicitly `NOT_OPENED`.
5. Production boundary is explicitly `UNCHANGED`.
6. A future setup family must pass the data, execution, baseline and validation gates before it can become an OOS candidate.

## Decision

The research program is complete as an execution control system, not as a
claim that all 220 tests have run. The honest next action is to acquire and
version the missing PIT/corporate-action and execution datasets. Until then,
P1 and P2 remain blocked and no new alpha-family search should be opened.
Any data acquisition that changes production or any locked-OOS opening remains
subject to the appropriate human approval.

## Validation

```text
python -m research.gated_research_program_2026_08_11 --csv data/backtest_out/full_universe_enriched.csv --out data/backtest_out/gated_research_program_2026-08-11.json
python -m pytest -q tests/test_gated_research_program_2026_08_11.py
```

Result: 2/2 focused tests passed. Manifest output: P0 `COMPLETED`, P1/P2
`BLOCKED`, P3-P8 `NOT_OPENED`, P9 `BLOCKED`; locked OOS `NOT_OPENED`.
