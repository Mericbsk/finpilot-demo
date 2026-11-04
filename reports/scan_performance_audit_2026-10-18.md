# Scan Performance Audit - 2026-10-18

**PRIMARY STATUS = NOT MEASURED.** The requested full-universe, end-to-end stage allocation cannot be stated from these records. This is an offline audit: no live scan, provider request, API request, flag change, `.env` read/write, production change, publication, commit, or push was performed.

## 1. Executive Summary

- **DERIVED from LOGGED JSONL:** 820 JSON objects parsed; 0 JSON parse errors and 0 non-object JSON lines; SHA-256 snapshot `008c66b0a4849310fed31612b9a09a04caf23edb1700a34b6f54c9f9109a16b9`.
- **DERIVED from LOGGED rows:** 593 records have `universe=200`; 416 have `total_s`; maximum logged `universe` is 200. A 200-symbol request is not the full universe.
- **DERIVED from LOGGED `total_s`:** median 321.38 s; p95 534.99 s; range 37.45-590.13 s, n=416.
- **DERIVED from LOGGED stage events:** only 12 of 820 records have nonempty `stage_timing`; the comparable Sep 22 stage cohort is 5 runs after excluding its documented first cold run.
- **DERIVED, Sep 22 200-symbol cohort only:** `prefetch.repair` median 305.025 s; median paired run share 86.45% (range 78.55-90.61%). Not a full-universe result.
- **DERIVED from LOGGED persistence fields:** `persist_s` is available for 130 completed 200-symbol rows; median 0.30 s, p95 1.02 s.
- The 81.6% historical repair-share label conflicts with raw-row statistics; this report exposes both definitions and does not edit the historical documents.
- **No full-universe bottleneck, share, or Amdahl ceiling is asserted.**

## 2. Feasibility Gate

| Capability | Status | Consequence |
|---|---|---|
| Python runtime | Available; used for offline parsing and artifact generation | Offline analysis is reproducible; no scanner ran. |
| `time.perf_counter` | Present in scanner/API code | Historical timers exist; no new scanner timing was taken. |
| `cProfile` | Available in the selected Python runtime; not run | CPU profile remains absent. |
| `psutil` | Installed in the selected Python runtime; not used | No process CPU/RAM sample was collected. |
| Workspace disk write | Available; analyzer wrote only the new dated artifacts; a separate Level A receipt was appended to the decision log | Runtime data and application state were not written. |
| Local API | Not tested | No API request was issued. |
| External provider network | Not tested | No provider request or credential use occurred. |
| Live `FINPILOT_SCAN_STAGE_TIMING` state | UNKNOWN; not inspected or changed | Historical event rows show prior opt-in runs only. |

## 3. Instrumentation Status

**DERIVED from LOGGED rows:** `stage_timing` is nonempty in 12/820 records (1.46%), 12/593 `universe=200` records (2.02%), and 12/416 completed 200-symbol records (2.88%). The timed population separates into 6 Sep 21 rows with `alpaca_total_failure=true` and 6 Sep 22 API-campaign rows; the first Sep 22 run is excluded from the five-run comparison per the decision log.

**DERIVED from LOGGED fields:** `persist_s` is present on 130/416 completed 200-symbol rows. It is a combined persistence timer, not an operation-level breakdown. The current live flag value is not known from this audit.

## 4. Measurement Window

**CODE-VERIFIED:** in `api/routers/scan.py`, `total_s` is captured from `_t_start` to `_t_scoring_done`, after scanner evaluation and `_enrich_results`. It ends before the four persistence calls. `persist_s` separately times `_persist_shortlist`, `_persist_shadow_ledger`, `_auto_add_watchlist`, and `_persist_distribution_export`. The timing-log append and analytics increment occur after `persist_s`; request queueing before `_t_start` and response completion are also outside these fields. Therefore neither `total_s` nor `total_s + persist_s` is a proven end-to-end request duration.

## 5. Stage Breakdown and Amdahl Ceiling

The table statistics are **DERIVED from LOGGED** timer values. p50/p95 are calculated over per-run values using `statistics.quantiles(method="inclusive")`; run shares are paired per-run ratios, not ratios of unrelated medians. Event-level sums for parallel or nested timers are not treated as wall-clock shares.

| Sample | Stage/window | n | p50 seconds | p95 seconds | p50 run share | p95 run share | Amdahl ceiling |
|---|---|---:|---:|---:|---:|---:|---:|
| All completed 200-symbol requests | evaluation.window (eval_s) | 416 | 321.375 | 534.980 | 100.00 | 100.00 | 100.00 |
| All completed 200-symbol requests | enrichment.window (enrich_s) | 416 | 0.000 | 0.020 | 0.00 | 0.01 | 0.00 |
| Completed 200-symbol requests with persist_s | persistence.window (persist_s) | 130 | 0.300 | 1.024 | 0.10 | 0.32 | 0.10 |
| 2026-09-22 API stage cohort; first cold run excluded | prefetch.alpaca | 5 | 34.302230 | 46.395972 | 11.31 | 17.47 | 11.31 |
| 2026-09-22 API stage cohort; first cold run excluded | prefetch.repair | 5 | 305.025259 | 332.145814 | 86.45 | 90.27 | 86.45 |
| 2026-09-22 API stage cohort; first cold run excluded | prefetch.alpaca + prefetch.repair (sequential timers) | 5 | 332.009 | 369.690 | 98.00 | 98.96 | 98.00 |
| 2026-09-21 Alpaca-total-failure cohort (not comparable) | prefetch.bulk_yfinance | 6 | 59.345296 | 66.302226 | 82.34 | 85.73 | 82.34 |

For the valid Sep 22 sample (JSONL source lines 336-340), the raw `prefetch.repair` values have mean 274.648 s and median 305.025 s. The total median is 336.640 s. Therefore:

- **DERIVED:** median of paired `repair_s / total_s` ratios = 86.45% (run range 78.55-90.61%); this is the sample-specific Amdahl ceiling for that measured 200-symbol window.
- **DERIVED:** ratio of medians = `median(repair_s) / median(total_s)` = 90.61%.
- **DERIVED:** `mean(repair_s) / median(total_s)` = 81.59%; this reproduces the historical 81.6% value, but it is not a ratio of medians.

The `prefetch.alpaca` and `prefetch.repair` timers are sequential top-level blocks in `scanner/data_fetcher.py`. `evaluation.symbol`, `indicator.compute`, `fetch.request`, `fetch.parse`, `rate_limit.wait`, and retry timers are inner or parallel events. Their per-run event sums are retained in the stage CSV, but their end-to-end shares and Amdahl ceilings are UNKNOWN. Six Sep 21 stage rows (316;317;318;319;320;321) belong to the separate Alpaca-total-failure regime and are not merged into the Sep 22 cohort.

## 6. Bottleneck Type

**UNKNOWN for the full universe.** The five-run Sep 22 `prefetch.repair` wall timer includes repair/provider/fallback work; the event data does not split network wait from client parsing or other processing. `rate_limit.wait` is explicitly timed in the sample, but summing concurrent event durations does not establish its wall-clock contribution. No CPU, disk-I/O, memory-pressure, or lock-wait profile was collected. No optimization conclusion follows from stage names alone.

## 7. Variance Analysis

**DERIVED from LOGGED completed 200-symbol rows (n=416):** `total_s` median 321.38 s, p95 534.99 s, minimum 37.45 s, maximum 590.13 s; p95/median=1.665 and max/min=15.758. `yf_fallback` median 60.00 and p95 162.50; Pearson r(total_s, yf_fallback)=0.478 over n=416 paired rows (**DERIVED, observational; not causal**).

**LOGGED Sep 22 sample:** the five selected runs span total_s 180.67-376.86 s and `yf_fallback` 81-198. Cache state for these runs is UNKNOWN except the first run's cold label in the decision log; the remaining runs are not assumed warm. Market session is UNKNOWN. The variance CSV preserves each 200-symbol row and its source line.

**Snapshot note:** The source was observed growing from 817 to 820 non-empty records during this audit; the three appended tail records have universe=8 and no total_s, so they do not change the completed 200-symbol population.

## 8. Serialization Analysis

**LOGGED:** the five selected Sep 22 rows contain timed `rate_limit.wait` and `retry.attempt` events. The `retry.backoff` timer is present in code but has zero events in this cohort; no backoff duration is inferred for other runs. **UNKNOWN:** full-universe rate-limit/backoff totals, worker saturation, GIL contribution, lock contention, and batch-gap time. No parallelism change is recommended.

## 9. Scale Model

`total_s ≈ fixed_cost + symbols × per_symbol_cost + fallback_symbols × fallback_extra_cost`

All terms are **UNKNOWN** for the full universe. The largest `universe` value in this timing-log snapshot is 200; all stage-instrumented runs use a 200-symbol request. No extrapolation or `ESTIMATED` value is supplied.

## 10. Instrumentation Gaps

See `reports/scan_instrumentation_gaps_2026-10-18.csv` for the full gap register. Principal gaps: full-universe end-to-end wall time, persistence sub-operation timing, physical resource split, controlled cache/session metadata, per-timeframe outer repair timing, batch-chain identifiers, and validated scale behavior. The master prompt's `prefetch.symbol_yfinance` label is not merged with the distinct current-code timer `prefetch.symbol_repair`.

## 11. Decision Tree Result

**Status F: measurement incomplete.** Partial 200-symbol stage timings exist, but no full-universe end-to-end stage allocation exists. The master prompt's success sentence cannot be populated without extrapolation; no full-universe bottleneck or percentage is claimed.

## 12. Bottlenecks by Impact

1. **Full-universe bottleneck:** UNKNOWN; ranking and ceiling are UNKNOWN.
2. **Sep 22 200-symbol sample only:** `prefetch.repair` has a derived median paired share of 86.45%; its sample-specific ceiling is not transferable to the full universe or another cache/provider regime.
3. **Persistence in the paired logged windows only:** median `persist_s` is 0.300 s; median `persist_s/(total_s+persist_s)` is 0.096% (p95 0.319%). This excludes outer request/logging overhead and is not a full-request ceiling.

## 13. What We Measured

- **LOGGED:** source `data/distribution/scan_timing.jsonl`, SHA-256 `008c66b0a4849310fed31612b9a09a04caf23edb1700a34b6f54c9f9109a16b9`, 1896605 bytes, 820 nonempty lines; 820 JSON objects, 0 JSON parse errors, and 0 non-object JSON lines.
- **DERIVED:** 593 `universe=200` rows, 416 with `total_s`, max recorded universe 200.
- **DERIVED from LOGGED:** completed 200-symbol `total_s` and `yf_fallback` distributions; `persist_s` distribution on 130 rows; stage-event distributions in separately classified cohorts.
- **LOGGED, Sep 22:** selected source lines 336,337,338,339,340; first cold run excluded as documented.
- **MEASURED in this audit:** no live scanner performance value. The only new runtime action was offline parsing and artifact generation.

## 14. What We Could Not Measure

Full-universe wall-clock duration and stage shares; end-to-end request duration; cold-versus-hot delta; market-session effect; provider-only network time; CPU/GIL and disk-I/O contributions; lock/serialization totals; complete retry/backoff behavior; full-run persistence split; and linear/nonlinear scaling. Missing quantities remain UNKNOWN, not estimated.

## 15. What the Measurement Contradicts

- The Oct 17 decision-log receipt records 411 completed 200-symbol batches; this source snapshot contains 416. The five-row difference is not reconciled here; this report uses the pinned current snapshot and does not rewrite that receipt.
- The Sep 21 audit report's zero-stage-event claim was accurate for its dated snapshot, but is stale for the current JSONL, which contains 12 stage-timed records. Likewise, `persist_s` is now present in 130 completed 200-symbol rows, though it remains incomplete for end-to-end timing.
- **CORE-005 metric conflict:** the Sep 22 decision log computes 274.648 s as the sum of five repair values divided by five (the mean); the Sep 23 note labels 274.648 s a median and calls 81.59% a ratio of medians. Raw rows instead give median repair 305.025 s, median total 336.640 s, ratio-of-medians 90.61%, and median paired run share 86.45%. Historical documents are left untouched; these definitions remain visibly distinguished.
- **FAZ 1:** the Sep 21 stage rows are not a valid production baseline because Alpaca completely failed; the Sep 22 five-run cohort is 200-symbol stage evidence only and does not complete the full-universe measurement.
- **CORE-005 phase-status conflict:** the Sep 21 acceleration plan labels FAZ 2R pending, while the Sep 22 decision-log entry says FAZ 2R.3 closed. This audit does not choose between them. The Oct 17 receipt says the FAZ 3 live A/B was not run and FAZ 4 had not started.
- The Sep 21 timed rows have `alpaca_total_failure=true` and are not evidence for the production Alpaca path. They remain separate from the Sep 22 API cohort.

## 16. Single Next Step

After an operator-approved measurement window is available, run one same-path full-universe campaign with at least five repeated runs, an explicitly recorded cache/session state, `FINPILOT_SCAN_STAGE_TIMING` enabled by the operator, and an outer wall timer spanning the complete batch chain through persistence and response. This audit did not enable the flag or run that campaign.

## 17. Proposed Governance Action

**None applied.** This Level A offline audit changes no scanner behavior, provider selection, signal, flag, cache, database, scheduler, API, or publication state. The two historical documentation conflicts above are reported but not edited; no performance optimization is proposed without a full-universe measurement.

## Reproducibility

- Source: `data/distribution/scan_timing.jsonl`
- Source SHA-256: `008c66b0a4849310fed31612b9a09a04caf23edb1700a34b6f54c9f9109a16b9`
- Source file modified UTC: `2026-10-18T12:57:45.078654+00:00`
- Analyzer: `research/scan_performance_audit_2026_10_18.py`
- Generated UTC: `2026-10-18T13:09:58.928752+00:00`
- Percentile method: `statistics.quantiles(..., method="inclusive")`
- Output CSVs: `reports/scan_stage_breakdown_2026-10-18.csv`, `reports/scan_variance_analysis_2026-10-18.csv`, `reports/scan_instrumentation_gaps_2026-10-18.csv`
- Stage cohort source lines: Sep 21 316,317,318,319,320,321; Sep 22 selected 336,337,338,339,340.
