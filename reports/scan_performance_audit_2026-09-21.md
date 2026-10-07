# Scan Performance Audit — 2026-09-21

> **TARİHSEL SNAPSHOT (2026-09-23 notu).** Bu rapor yazıldığında aşama zamanlaması hiç açılmamıştı, bu yüzden "NOT MEASURED" statüsü **o tarih için doğruydu**. 2026-09-22'de stage timing açık 5 koşuluk kampanya yapıldı ve aşama kırılımı ölçüldü: `prefetch.repair` toplam sürenin medyanlar-oranıyla %81.6'sı, koşu-başına medyanla %86.5'i. Güncel durum için: `docs/2026-09-23-neden-yavas-ve-cozum-uzayi.md` ve `docs/governance/decision-log.md` (2026-09-22 girdileri). Bu rapor içeriği değiştirilmeden bırakıldı.

## 1. Executive Summary

**PRIMARY STATUS = NOT MEASURED.** The requested full-universe stage breakdown cannot be established from the available evidence. The timing log contains 315 records, including 279 logged 200-symbol batches and 5 records dated 2026-09-21; none contains stage events. The reported `total_s` is measured only through `_t_scoring_done`, before four persistence calls. No production code, flag, cache, database, scheduler, scan, queue, or publication was changed or run by this audit.

The strongest logged fact is that 200-symbol batch duration varies from 37.45s to 590.13s, with median 300.44s and p95 496.67s. This is **LOGGED**, not a new measurement. The source of the variance is **UNKNOWN** because fallback count, cache state, provider wait, retry backoff, and stage timing are not jointly observed.

## 2. Feasibility Gate

| Capability | Available | Consequence |
|---|---|---|
| Python / `perf_counter` | YES | A controlled measurement is technically possible, but was not run. |
| `cProfile` | YES | CPU profiling is technically possible, but no live profile was collected. |
| `psutil` / pandas | YES | Resource profiling is technically possible, but no live profile was collected. |
| Disk write | YES | Audit artifacts were written under `research/` and `reports/` only. |
| Local API | YES, GET/health path required | No scan endpoint was invoked. |
| External provider network | UNAUTHENTICATED check returned HTTP 401 | Live provider measurement is not established; no credentials were exposed or used. |
| Stage timing flag | **NO (`FINPILOT_SCAN_STAGE_TIMING=0`)** | Existing records have no stage events; stage-level claims remain UNKNOWN. |

## 3. Instrumentation Status

`scanner/performance.py` is opt-in. Existing log coverage is 0/315 records with non-empty `stage_timing` (**LOGGED**). The flag was not changed. `api/routers/scan.py` records `total_s` immediately before `_persist_shortlist`, `_persist_shadow_ledger`, `_auto_add_watchlist`, and `_persist_distribution_export`; their wall-clock duration is outside the current window (**CODE-VERIFIED**, duration **UNKNOWN**).

## 4. Measurement Window

`total_s` is a logged score/evaluation window, not proven end-to-end scan wall-clock time. The missing persistence duration cannot be assigned a percentage from current evidence. Full-universe duration is also **UNKNOWN**: the log contains 200-symbol batches, not a single 1812/1900-symbol end-to-end run.

## 5. Stage Breakdown and Amdahl Ceiling

The CSV companion contains logged evaluation/enrichment windows and UNKNOWN rows for every uninstrumented stage. For the 200-symbol logged population, the median evaluation window is 300.43s and the median enrichment window is 0.00s (**LOGGED**). Their percentage of the **measured window** is derived from medians; it is not a percentage of true end-to-end scan time. Amdahl ceilings for unknown stages are UNKNOWN.

## 6. Bottleneck Type

Network wait, CPU, disk I/O, lock/serialization, and provider rate-limit wait are **UNKNOWN** at stage level. `enrich_s` is near zero in the logged records, but this does not measure individual indicator CPU time or provider wait. No optimization conclusion follows.

## 7. Variance Analysis

The companion variance CSV preserves each logged run. Cache state and market session are recorded as UNKNOWN because the source log does not contain them. For 200-symbol runs, `yf_fallback` and `total_s` are both logged; their Pearson correlation is 0.50 (**DERIVED** from 279 logged pairs), but this is not causal evidence and does not separate cache, network, rate-limit, or retry effects.

## 8. Serialization Analysis

`rate_limit.wait` and `retry.backoff` totals are **UNKNOWN**. Worker parallelism, GIL effects, and batch gaps are **UNKNOWN**. No parallelism recommendation is authorized by this audit.

## 9. Scale Model

The requested model remains uninstantiated:

`total_s ≈ fixed_cost + symbols × per_symbol_cost + fallback_symbols × fallback_extra_cost`

The terms are **UNKNOWN** for a full-universe run. Extrapolation from 200-symbol batches is intentionally omitted because fallback/cache/session state is not controlled and no full-run total is measured.

## 10. Decision Tree Result

**Status F: measurement incomplete.** The audit cannot select A–E because stage timing and end-to-end coverage are missing. No single bottleneck claim is made.

## 11. What We Measured

- **LOGGED:** 315 JSONL timing records; 279 with `universe=200`.
- **LOGGED:** 200-symbol total window median 300.44s, p95 496.67s, min 37.45s, max 590.13s.
- **LOGGED:** all existing records have empty `stage_timing`.
- **DERIVED:** fallback/total correlation shown above; it is descriptive only.
- **CODE-VERIFIED:** persistence calls occur after `_t_scoring_done`.

## 12. What We Could Not Measure

Full-universe wall-clock duration; persistence phase; per-path network time; retry/backoff; rate-limit wait; disk I/O; CPU profile; cache state; market session; batch gaps; and controlled cold-vs-hot comparison.

## 13. What the Measurement Contradicts

The existing `total_s` values cannot be called complete scan duration without qualification. The log also does not support a causal claim that fallback count alone explains the 10× variance. Any prior statement stronger than these two points is not established by this evidence.

## 14. Single Next Step

Run one approved controlled measurement campaign with `FINPILOT_SCAN_STAGE_TIMING=1`, without changing production code or signal logic: at least five repeated runs per declared cache condition, with outer timers around the four persistence calls and resource/network metadata captured. Until that happens, **PRIMARY STATUS remains NOT MEASURED**.

## 15. Proposed Performance Action

**None applied.** Any flag enablement or additional outer timer is a proposed measurement action, not an optimization. It requires an explicit operational approval and must not change scanner outputs.

## Reproducibility

- Source: `data/distribution/scan_timing.jsonl`
- Script: `research/scan_performance_audit_2026_09_21.py`
- Generated: 2026-09-21T08:08:47.943754+00:00
- Output files: `reports/scan_stage_breakdown_2026-09-21.csv`, `reports/scan_variance_analysis_2026-09-21.csv`, `reports/scan_instrumentation_gaps_2026-09-21.csv`
