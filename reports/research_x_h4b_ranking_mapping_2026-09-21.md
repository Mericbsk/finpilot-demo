# RESEARCH-X/H4B - Production Ranking Mapping Reconstruction

**Date:** 2026-09-21
**Level:** A - read-only forensic research
**Runner:** `research/research_x_h4b_ranking_mapping_2026_09_21.py`
**Artifact:** `data/backtest_out/research_x_h4b_ranking_mapping_2026-09-21.json`

## 1. Executive Result
H4B verdict: `MAPPING_DEPENDS_ON_ADDITIONAL_INPUTS`.
The implemented score-source branch is identifiable, but exact historical ranking and final public order are not replayable from the canonical CSV.
Official production ranking resolution remains `DEFINITION_REQUIRED`; this is separate from H4A structural compression and does not establish predictive or economic failure.

## 2. Research Question
Reconstruct the path `raw features -> composite_score -> ? -> ranking_score -> production ordering` without changing the score formula.
The audit separates score-source selection, candidate eligibility, publication ordering, and final tie behavior.

## 3. Governance and Scope
Research / Level A / READ_ONLY.
No score inversion, refit, threshold tuning, ranking mutation, scanner mutation, configuration mutation, database write, deployment, or locked-OOS opening was permitted.
H2 remains `CLOSED / NOT_SUPPORTED`; H4A remains structural and does not authorize a production score change.

## 4. Dataset and Provenance
Input: `data/backtest_out/full_universe_enriched_eod_only.csv`
SHA-256: `87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad`
Raw rows: `79935`; deduplicated EOD rows: `43551`; composite non-null rows: `40014`.
Composite date range: `['2026-05-06', '2026-08-05']`; unique dates: `57`.
Deduplication: one row per symbol/scan_date, retaining earliest lexical scan_ts; stable first row on exact ties.

## 5. Production Path Under Audit
`scanner/evaluate.py` builds the score input, computes composite strength, computes legacy quality, selects ranking_score by environment flag, and emits the fields.
`distribution/jobs.py` passes scan export rows to `distribution.snapshot_builder.build_snapshot`.
`scanner/scan_summary.py` separately builds the summary/alert candidate pool with its own rank helper.
`distribution/prepublish_gate.py` requires ranking fields in the export contract; it does not define a ranking resolution metric.

## 6. Raw Features to Composite Score
The evaluated score input contains regime, direction, raw score, filter score, alignment ratio, momentum ratio, binary filter components, volatility regime, sentiment, and optional feature factors.
The composite path is `compute_recommendation_score` followed by `compute_recommendation_strength`.
This is the composite construction path only; it is not the default ranking source when the legacy override flag is disabled.

## 7. Composite Score Storage
`composite_score` is the rounded 0-100 strength value: `clip(raw_recommendation_score / 16.5 * 100, 0, 100)` followed by `int(round(strength))`.
The historical export contains `90` unique composite values across `40014` observations.
The raw recommendation score and component breakdown are not persisted in the canonical historical CSV.

## 8. Ranking Score Definition
Current code: `ranking_score = composite_score when FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=1; otherwise ranking_score = legacy_quality_score`.
The runner's effective branch is `legacy_quality_score`; this describes the runner/repository default, not an unverified live process state.
`legacy_quality_score` is a separate 0-100 nominal score rounded to three decimals and uses regime, direction, raw score, ATR, RVOL, squeeze, lottery, and overnight inputs.

## 9. Configuration and Flag Provenance
Flag: `FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING`.
Source-code default: `0`; repository `.env` value: `0`; runner process value: `None`.
The score engine reads `os.environ` directly; a `.env` value is provenance only unless the caller loads it.
This runner did not inspect or mutate a live production process.

## 10. Mapping Relationship
The ranking path is not a single transform from composite_score. It is a conditional source switch between composite_score and an independently computed legacy_quality_score.
Code-level source mapping: `True` given a known flag; historical exact replay: `False`.
Therefore structural compression of composite_score must not be presented as official production ranking resolution.

## 11. Additional Inputs
The default legacy branch requires additional inputs beyond the persisted composite score.
- regime
- direction
- raw score
- daily ATR percentage
- raw RVOL / alpha RVOL transformation
- squeeze_factor
- lottery_factor
- overnight_gap_factor
- FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING process value
Historical `atr_pct_real` and `rvol` permit a descriptive back-computation, but missing per-row feature timestamps, evaluator provenance, and persisted ranking_score prevent exact production replay.

## 12. Ranking Method Provenance
`ranking_method` is emitted as `legacy_quality` unconditionally in `evaluate.py`.
That label is consistent with the default legacy branch but would be stale if the composite override flag were enabled.
Status: `CONSISTENT_FOR_DEFAULT_BRANCH_ONLY`.

## 13. Candidate Eligibility
Public snapshot candidates require a grade/conviction label, selection eligibility when present, execution feasibility when present, and no position-cap rejection.
The summary candidate pool has a separate fallback eligibility rule and does not use exactly the same candidate filter as the public snapshot.
Snapshot cap: `50`; summary pool default: `25`.

## 14. Public Snapshot Ordering
`distribution/snapshot_builder._sort_key` orders public candidates by:
- grade ascending: A, B, C, then unknown
- execution_confidence ascending: Tier 2, Tier 1, Tier 0
- conviction_prob descending
- selected score descending: ranking_score or legacy_quality_score or composite_score or score
The score is therefore the fourth precedence level, not the sole publication ordering field.

## 15. Summary and Alert Ordering
`scanner/scan_summary._rank` orders its candidate pool separately by conviction tier, execution confidence, conviction probability, and ranking score/composite fallback.
- conviction_tier ascending: A, B, C, then empty
- execution_confidence ascending: Tier 2, Tier 1, Tier 0
- conviction_prob descending
- ranking_score descending; composite_score is the default only when the key is absent
When `ranking_score` is absent, the mapping expression uses `composite_score`; a present zero or null value is coerced to zero rather than replaced by composite_score.
This path can diverge from the snapshot builder because its tier mapping and score fallback are not identical.

## 16. Tie-Breakers and Stability
No explicit symbol, timestamp, row id, or deterministic final tie-breaker is present in either inspected sort key.
- Python stable sort preserves input order for equal keys
Equal-key ordering depends on input sequence. The historical CSV row order is not sufficient evidence of the production scan result insertion order.
The Python `or` fallback also treats a zero ranking score as falsy and may select the next score field.

## 17. Historical Ranking Coverage
Persisted historical ranking fields:
- ranking_score: False
- legacy_quality_score: False
- ranking_method: False
A legacy-quality historical proxy is calculable for `39986` of `40014` composite rows; it is not a persisted ranking_score.
Historical exact ranking order: NOT RECONSTRUCTABLE.

## 18. Reconstructed Score Diagnostics
Historical legacy-quality proxy unique values: `27050`; range: `-5.122` to `85.0`.
Comparable proxy/composite rows: `39986`; descriptive Pearson: `0.887466`; descriptive Spearman: `0.884258`.
These are proxy diagnostics only. They do not prove a historical production ranking value, monotonicity, predictive quality, or economic value.

## 19. Resolution Definition
Composite unique values: `90`.
Historical ranking unique values: `NOT AVAILABLE` because ranking_score is not persisted.
Historical proxy unique values: `27050`; this is not the official production metric.
Official production ranking resolution: `DEFINITION_REQUIRED` because the scoped evidence does not choose between score values, complete sort-key tuples, and final displayed ranks.

## 20. Evidence vs Interpretation
**EVIDENCE**
- current code computes composite_score, legacy_quality_score, and ranking_score separately
- the default code branch selects legacy_quality_score when the override flag is not 1
- public snapshot ordering is a multi-key tuple
- historical EOD export lacks persisted ranking fields
**INTERPRETATION**
- composite_score is not the default production ranking field under the observed repository default
- compression findings for composite_score cannot be relabeled as official ranking resolution
**NOT PROVEN**
- the exact historical production ranking order
- that ranking_score is a monotone transform of composite_score
- that score precision or tie concentration caused predictive/economic failure
- that any score, ranking, or publication change would improve outcomes

## 21. Limitations and Not Proven
The canonical EOD export lacks ranking_score, legacy_quality_score, ranking_method, complete evaluator feature provenance, and original production input ordering.
The proxy uses available historical columns and the current legacy formula; it is not a point-in-time replay of the live evaluator.
Mapping reconstruction does not test a new score and does not authorize changing any production rule.

## 22. Production Impact and Next Question
Production impact: `NONE`. All mutation flags are false.
H4B closes the code-level source question only partially: the ranking field and sort precedence are visible, while exact historical final order and official resolution remain unresolved.
Next question: define the official production ranking resolution metric and, only after that, decide whether an H4C information-loss audit is warranted. Compression is not ranking failure, and mapping ambiguity is not predictive/economic failure.
Guardrail: no score formula, ranking source, scanner, configuration, database, scheduler, publication behavior, or user-facing surface was changed.

## Source Evidence Index

| Surface | Path | SHA-256 | Relevant symbols/lines |
|---|---|---|---|
| score_engine | `scanner/score_engine.py` | `9455d5205eb476261373700a71252062b44f85f209ebb1d693fc677151ba4a3f` | compute_legacy_quality_score:193-222, compute_recommendation_score:99-190, compute_recommendation_strength:378-397, legacy_composite_ranking_enabled:238-240 |
| evaluate | `scanner/evaluate.py` | `a126de0f25ae61771dc167584dd881e259b65c59103a03420121a93bdb03b4be` | evaluate_symbol:355-883 |
| snapshot_builder | `distribution/snapshot_builder.py` | `47b92eaa8115b500b13f4023f0cc27afbc60a206610f5f86a2cb8268ca292552` | _sort_key:99-116, _grade_of:86-96, _public_candidate:123-131, build_snapshot:397-565 |
| scan_summary | `scanner/scan_summary.py` | `512e528c04ff23636a1a030a4c8520a1138f94e28058894b088c1003b6e2c18a` | _rank:29-36, build_candidate_pool:39-50, summarize_full_scan:259-298 |
| distribution_jobs | `distribution/jobs.py` | `52df5978371a04242a63b449978dff85841c98c2969ede98b27a8f07dd0cb7aa` | n/a |
| prepublish_gate | `distribution/prepublish_gate.py` | `13f27e65e834e108a263cd028f6f0a1156abd18d74671ae54bbc7a76addb4960` | n/a |
