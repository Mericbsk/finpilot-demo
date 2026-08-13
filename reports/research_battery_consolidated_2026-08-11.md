# Consolidated Research Battery Report

Date: 2026-08-11
Status: research-only evidence; no production promotion
Authority layer: Research / Engineering
Decision level: Level A for isolated diagnostics; any scanner, publication, risk or live-rule change remains Level B/C.

## Scope

This report consolidates the feasible diagnostics requested for the current research phase. Production scanner behavior, ranking, entry/exit logic, portfolio execution, publication and live trading were not changed.

The confirmatory H1 gap reversal, H2 rvol inversion and H3 ATR-parity hypotheses were not run. Their pre-registration gates remain closed because the current dataset has unresolved price-cache discontinuities, incomplete point-in-time provenance and execution-data limitations.

## Existing Research Batteries

- Strategic Lab: `data/backtest_out/strategic_lab_2026-08-10.json`; 17 experiments completed and 1 partial.
- Ten Perspectives Lab: `data/backtest_out/ten_perspectives_lab_2026-08-10.json`; 13 experiments completed.
- Mirror Analysis: `data/backtest_out/mirror_analysis_2026-08-10.json`; 9 experiments completed.
- Focused validation: 27 tests passed across the three battery test modules and close-to-close export tests.

These are diagnostic results, not production validation. Their conclusions remain bounded by the data-integrity and point-in-time gates below.

## Additional Diagnostics

### Price-cache integrity

Command:

```text
python -m research.price_cache_integrity_audit --cache data/price_cache --threshold-pct 50 --field close --out data/backtest_out/price_cache_integrity_audit_2026-08-11.json
```

Artifact: `data/backtest_out/price_cache_integrity_audit_2026-08-11.json`.

Result: 2,047 symbols scanned; 485 symbols contain at least one absolute close-to-close jump of 50% or more. The median largest absolute jump among flagged symbols is 173.57513%. The largest example is FFAI, with a reported 1,542,757.142857% jump from 0.0007 to 10.8.

Interpretation: this is a diagnostic flag, not proof that every jump is an error. It is sufficient to keep confirmatory runs closed until splits, corporate actions, ticker changes and cache/provider behavior are explained.

### Matched-null preflight

Command:

```text
python -m research.negative_control --csv data/backtest_out/full_universe_enriched.csv --cache data/price_cache --permutations 1000 --out data/backtest_out/negative_controls_2026-08-11.json
```

Artifact: `data/backtest_out/negative_controls_2026-08-11.json`.

Result: the candidate `entry_ok` cohort has 1,095 rows and mean net return of -1.5663109374246575%. Its percentile is 0.0 in both label-permutation and signal-permutation null families, and 0.004 in the time-shift family. Each family contains 1,000 permutations.

Interpretation: the candidate does not separate positively from the matched null distributions in this run. It is a discovery/diagnostic result, not evidence for a production rule.

### Feature lineage

The lineage contract identifies the following fields as forward-looking and prohibited as features: `resolved_pct_t5`, `resolved_pct_1d`, `c2c_1d`, `c2c_5d` and `mae_t5`. The current enriched export contains all of these fields, so validating the complete export column list as a feature set correctly returns `ok: false` due to leakage fields. This confirms that outcome columns must remain separated from any future feature matrix.

### Daily signal half-life

Input: `data/backtest_out/full_universe_enriched.csv`.

Result: 2,438 eligible rows. Day-1 median close-to-close return is 0.0311%, with a 50.21% positive rate. Day-5 median close-to-close return is -0.6711%, with a 44.71% positive rate. The median day-1 share of the day-5 move is 0.2395.

Interpretation: the daily approximation does not show a positive persistent edge. Intraday half-life remains blocked because intraday bars, spread and impact data are not available in this research slice.

### Restatement detector

Status: BLOCKED. No immutable prior price-cache snapshot was available for a valid same-symbol, same-date comparison. The distribution snapshots are publication snapshots, not bar-cache snapshots, and were not substituted as if they were equivalent.

### Experiment registry

Registry: `data/research_experiments.db`.

Result: 3 registered experiments and 6,000 completed runs. The `p1-entry-ok-null-v1` family accounts for 2 experiments and 6,000 runs. This run count is recorded for multiple-testing and selection-bias visibility; it does not promote any candidate.

## Gate Summary

| Area | Status | Reason |
| --- | --- | --- |
| Diagnostic batteries | COMPLETED | 39 experiments across Strategic, Ten Perspectives and Mirror outputs; focused tests passed. |
| Price-cache integrity | HOLD | 485 of 2,047 symbols have large-jump flags requiring explanation. |
| Matched-null control | FAILED FOR CANDIDATE | `entry_ok` is below the null distributions in the recorded families. |
| Feature leakage preflight | COMPLETED WITH BLOCK | Forward outcome fields are present in the export and must not enter features. |
| Daily half-life | COMPLETED | No positive persistent edge demonstrated; intraday gate remains open. |
| Restatement comparison | BLOCKED | No immutable prior bar-cache snapshot. |
| H1/H2/H3 confirmatory runs | HOLD | Required integrity, provenance and execution gates are not open. |
| Production scanner/publication/live behavior | NOT CHANGED | No Level B/C approval or production edit performed. |

## Conclusion

The feasible research battery has been run, but it does not validate a regular weekly 5–10% gain expectation, a production score, or a production entry/exit rule. The strongest current evidence is negative or incomplete: the matched-null candidate underperforms its null controls, the price cache has substantial discontinuity flags, and the daily half-life check does not show a positive persistent edge.

Next admissible research work is data remediation and measurement: explain flagged price jumps, obtain immutable cache snapshots and point-in-time publication metadata, and add intraday spread/impact observations. No confirmatory hypothesis or production behavior should be promoted before those gates are independently rerun.
