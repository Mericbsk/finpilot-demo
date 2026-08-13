# FinPilot Scanner Performance Research

Status: Level B research proposal and baseline evidence; no scanner behavior changed.
Date: 2026-08-04
Scope: scanner pipeline from data acquisition through evaluation and API persistence.

## Executive Summary

The scanner must be treated as a data-processing pipeline, not as one CPU-bound
function. The first available evidence points to variable external-data fallback
cost as a major contributor to the current slowdown, especially incomplete
Alpaca/IEX intraday history followed by yfinance repair. This is a measured
correlation, not yet a causal proof.

The existing API timing record measures only `eval_s`, `enrich_s`, and `total_s`.
It does not yet expose per-timeframe request latency, repair latency, indicator
CPU time, evaluation CPU time, memory allocation, or disk wait. Therefore a
credible theoretical minimum cannot be stated yet.

## Current Pipeline

The current production path is:

1. API `/scan` receives a symbol batch.
2. `evaluate_symbols_parallel()` removes known delisted symbols.
3. `prefetch_symbols_multi_timeframe()` attempts Alpaca bulk data.
4. Incomplete Alpaca/IEX symbol/timeframe results are repaired with bulk
   `yf.download()` and, if still insufficient, per-symbol multi-timeframe
   yfinance requests.
5. `4h` data is derived from `1h` data by resampling.
6. `add_indicators()` computes indicators for each timeframe.
7. `evaluate_symbol()` applies the existing filters, score, risk, feature and
   contract calculations to prefetched data.
8. API enrichment and persistence run after evaluation.

The scanner already uses bulk requests where possible, a thread pool for the
fallback path, and a cache. These are existing facts, not new recommendations.

## Evidence Available On 2026-08-04

Source: `data/distribution/scan_timing.jsonl`, produced by the existing timing
telemetry. The data is runtime evidence from FinPilot scans, not a synthetic
benchmark.

| Date | Batches | Symbols | Sum `eval_s` | Wall span | yfinance fallback | Alpaca misses |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2026-08-02 | 16 | 3,200 | 3,207.0 s | 3,309.2 s | 609 (19.0%) | 15m=589, 1h=494, 1d=5 |
| 2026-08-03 | 12 | 2,400 | 3,519.1 s | 2,600.9 s | 810 (33.8%) | 15m=487, 1h=397, 1d=4 |
| 2026-08-04 | 9 | 1,800 | 2,968.4 s | 2,841.7 s | 705 (39.2%) | 15m=360, 1h=273, 1d=3 |

The timing report includes an additional 12-symbol and 30-symbol run on
2026-08-03. Those are not mixed into the comparable 200-symbol batch table.

### What this supports

- Runtime is highly variable at the same nominal batch size.
- Intraday Alpaca misses are concentrated in `15m` and `1h`, not `1d`.
- The slowest observed 200-symbol batch in the available tail was 534.36 s
  with 144 yfinance fallback symbols and Alpaca misses of 15m=77, 1h=55,
  1d=3.
- A 200-symbol batch with 15 yfinance fallbacks completed in 134.79 s in the
  same available period.
- The data is consistent with fallback and upstream latency being important,
  but it does not isolate their causal contribution. Batch ordering, cache
  state, rate limiting, remote service conditions, symbol composition and
  retries are confounders.

### What this does not support

- It does not prove that yfinance fallback is the only or dominant cause.
- It does not prove that indicator calculation is cheap for every workload.
- It does not justify changing the composite score, filters, thresholds,
  timeframes, or signal eligibility.
- It does not provide a theoretical minimum runtime.

## Initial Bottleneck Ranking

This is a measurement priority order, not a final optimization ranking.

| Priority | Suspected area | Classification | Evidence | Confidence |
| --- | --- | --- | --- | --- |
| 1 | Alpaca/IEX intraday coverage misses and repair path | Network / I/O | 15m and 1h miss counts track the fallback path; batch times vary widely | Medium |
| 2 | Remote request latency, rate limits and retries | Network-bound | Existing fetcher has rate limiting and multiple fallback paths; request timing is not recorded | Medium-low |
| 3 | Per-symbol indicator and DataFrame allocation work | CPU / memory | `add_indicators()` copies frames and computes multiple pandas series per timeframe; no stage timing yet | Low |
| 4 | Evaluation and feature/risk calculations | CPU / Python | `evaluate_symbol()` performs many Python-level calls after prefetch; no per-stage timing yet | Low |
| 5 | API persistence/enrichment | I/O | Existing API records this as `enrich_s`; observed values are near zero in the available tail | Low for current runs |

## Measurement Plan

### Phase 0: Reproducible baseline

Run the same symbol list, batch size, timeframe configuration, cache state and
credentials in a controlled environment. Record:

- wall time and monotonic stage time;
- CPU time and CPU utilization;
- RSS peak and allocation peak;
- request count, request latency, retries, rate-limit waits and response bytes;
- cache hit/miss/expiry status;
- symbols and rows returned per timeframe;
- result count, unavailable count and contract fields;
- machine, Python, pandas, yfinance and provider versions.

Do not use a live publication or overwrite a full-scan artifact for a benchmark.
Use a separate partial output location and keep runtime output out of Git.

### Phase 1: Stage instrumentation

Add observation-only timing around these boundaries:

- universe preparation;
- Alpaca bulk request per timeframe;
- Alpaca result repair per timeframe;
- bulk yfinance request and parsing per timeframe;
- per-symbol yfinance fallback;
- `4h` resampling;
- indicator calculation per timeframe;
- parallel evaluation;
- API enrichment;
- persistence and logging.

Each record must include a run id, batch id, symbol count, timeframe, path
(`alpaca`, `bulk_yfinance`, `symbol_yfinance`, `cache`), elapsed time, outcome,
and row count. Instrumentation must not alter scanner output or scoring.

### Phase 2: Profiler matrix

Use the least invasive tool that answers the question:

- `cProfile`: whole-run Python call profile;
- `py-spy`: low-overhead wall-clock sampling during a representative run;
- `line_profiler`: only confirmed CPU hot functions;
- `tracemalloc`: allocation and peak-memory comparison;
- `psutil` or platform counters: CPU, RSS and I/O context;
- Scalene or memory-profiler only if the preceding evidence leaves a memory
  question unresolved.

The profiling environment and exact command must be recorded with each result.
Do not install optional profilers into production requirements for this phase.

### Phase 3: Scaling and concurrency matrix

Use fixed replayable input data before comparing concurrency. Measure 100, 500,
1,000, 3,000 and 10,000 symbols where data is available. Compare sequential,
threaded and process-based evaluation only after separating network fetch from
local evaluation. `asyncio`, Ray, Dask, Joblib, CUDA and distributed execution
are hypotheses to test, not default recommendations.

## Lower Bound and Throughput Model

For a controlled run, the practical lower bound is at least the maximum of
mandatory serialized stages and the critical-path network latency:

$$
T_{min} \geq \max(T_{serialized}, T_{critical\ network}, T_{required\ compute})
$$

For the current system, those terms are not measured separately, so the bound
is currently **unknown**. The 134.79-second 200-symbol batch is a historical
observed runtime, not a lower bound. A throughput estimate must be reported
with workload, cache state, provider path and confidence interval.

## FinPilot-Specific Experiments

These experiments are deferred until a correctness-preserving replay baseline
exists:

1. Coarse liquidity/price/volume filtering before expensive indicators. Compare
   selected-symbol recall and all scanner contract fields against the baseline.
2. Two-stage and three-stage scans. Measure candidate reduction, wall time and
   signal-quality metrics on the same historical input.
3. Indicator reuse and cache reuse. Confirm that reused values correspond to the
   same data cutoff and do not change output fields.
4. Incremental EMA, RSI, ATR, MACD, Bollinger and composite calculations. First
   prove numerical equivalence within an explicitly chosen tolerance; then
   benchmark.
5. Parallelism by workload class. Network fetch, pandas evaluation and any
   numerical kernels must be benchmarked separately.
6. CPU, GPU and local-AI hardware. Only indicator kernels with measured CPU
   saturation and sufficient batch arithmetic intensity should be candidates
   for GPU or native acceleration. AI hardware is not expected to accelerate
   ordinary HTTP, database, pandas or broker I/O without a separate workload.

Any experiment that changes product filters, composite scoring, eligibility,
risk, entry/exit or publication behavior is a Level B/C product or risk decision
and must remain unapproved until reviewed.

## Industry Comparison Boundary

QuantConnect/Lean, Zipline, Freqtrade, Backtrader and vectorbt can provide
architectural comparison later. Their published or repository behavior must be
labeled as third-party evidence and must not be presented as FinPilot benchmark
results. A fair comparison requires identical data, indicators, universe,
lookback, output contract and hardware assumptions.

## Next Implementation Slice

The first observation-only instrumentation slice is now implemented behind
`FINPILOT_SCAN_STAGE_TIMING=1`:

1. `scanner/performance.py` provides a thread-safe in-memory timing collector;
2. prefetch records Alpaca, Alpaca repair, bulk yfinance, per-symbol yfinance,
   bulk request, and derived `4h` stages;
3. evaluation records per-symbol prefetched evaluation stages;
4. API timing payloads and append-only timing records carry `stage_timing`;
5. collector tests cover disabled, enabled, and error outcomes.

The following evidence steps remain open:

1. expose indicator and parsing durations separately where the first run shows
   they matter;
2. run one 30-symbol warm-cache and one cold-cache benchmark with the flag on;
3. add request retry, rate-limit wait, CPU, RSS and allocation measurements;
4. compare output snapshots with `scripts/golden_scan.py`.

No optimization should be merged before this evidence exists. The first likely
low-risk target, if the measurements confirm it, is reducing avoidable fallback
work or improving provider coverage while preserving the existing data-quality
and scanner↔distribution contract.

## Controlled 30-Symbol Benchmark

Run artifact: `reports/scanner_performance_benchmark_2026-08-04.json`.
Command: `python scripts/run_scanner_performance_benchmark.py --output reports/scanner_performance_benchmark_2026-08-04.json`.
Environment: Python 3.12.3 on Windows, `FINPILOT_SCAN_STAGE_TIMING=1`, fixed
30-symbol list, one process. The cold label means process-cold: the fetcher's
process-local memory cache was cleared before the first run. Redis and
Streamlit/framework caches were not forcibly cleared, so this is not evidence
of a fully cold external-cache state.

| Run | Wall | Process CPU | CPU / wall | Peak tracemalloc | RSS delta | yfinance fallback | Golden equality |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| process-cold | 32.835 s | 34.703 s | 1.057 | 8.20 MB | 38.66 MB | 0 | yes |
| warm | 38.730 s | 35.141 s | 0.907 | 6.79 MB | 11.65 MB | 0 | yes |

The warm run was 5.895 s slower than the process-cold run. This counterintuitive
result means the pair cannot be treated as a cache-speedup experiment: provider
latency, concurrent request scheduling and framework cache behavior remain
confounders. Both runs produced 36 stage events and zero decision-snapshot
differences, so the comparison is correctness-safe for this workload.

### Stage Evidence And Classification

| Stage | Process-cold total | Warm total | Interpretation |
| --- | ---: | ---: | --- |
| `fetch.request` (3 bulk requests) | 19.183 s | 19.707 s | Network/I/O candidate; measured request wall time |
| `prefetch.bulk_yfinance` | 25.951 s | 29.757 s | Network/I/O plus fetch orchestration; dominant serialized fetch stage |
| `prefetch.resample_4h` | 2.150 s | 4.832 s | Local pandas/resampling candidate; not separately CPU-profiled |
| `evaluation.symbol` (30 symbols, summed) | 87.788 s | 35.358 s | Parallel local work; sum exceeds wall time and is not a critical-path duration |

Initial classification for this run: network/I/O is the strongest measured
bottleneck candidate because bulk yfinance/request stages occupy most of the
fetch critical path. CPU saturation is not proven: process CPU is close to wall
time, but stage CPU time is not separated from network waits. Memory pressure is
not proven: RSS grows more in the process-cold run, while peak Python allocation
is small relative to RSS and no sustained pressure measurement exists.
Algorithmic bottlenecks are not proven by this sample. The per-symbol
evaluation events show local work, but a 30-symbol run has no scaling slope and
indicator/parsing stages are not yet independently timed. A fixed-input scaling
matrix and indicator-level instrumentation are required before estimating a
theoretical minimum runtime.

This benchmark is evidence only, not an optimization decision. No scanner
scoring, filter, eligibility, risk, entry/exit or publication behavior changed.

## Replay Separation And Scaling Matrix

The first attempt to prepare a 500-symbol multi-timeframe replay from the live
fetch path was stopped by the existing per-symbol fallback: yfinance returned
rate-limit errors and `prefetch_symbols_multi_timeframe()` reached its 180 s
timeout with 139 of 500 futures unfinished. This is direct evidence that the
current fallback/rate-limit path is not a reliable bulk replay preparation
mechanism at this scale. No second provider flood was attempted.

The repository already contains daily OHLCV JSON files in `data/price_cache`.
Those files were converted to a fixed, local Parquet replay dataset covering
500 symbols. The run phase made no provider calls and used the same raw daily
frames for indicator computation and evaluation. Because the local cache is
daily-only, this is a **local daily indicator/evaluation scaling test**, not a
full multi-timeframe scanner benchmark and not a quality result.

Run artifact: `reports/scanner_replay_daily_scaling_2026-08-04.json`.
Dataset manifest: `data/scanner_replay_daily_2026-08-04/manifest.json`.

| Scale | Results | Wall | Process CPU | CPU/wall | RSS delta | Peak tracemalloc |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 30 | 30 | 1.225 s | 1.281 s | 1.046 | 1.05 MB | 1.87 MB |
| 100 | 100 | 4.929 s | 4.859 s | 0.986 | 2.10 MB | 3.20 MB |
| 500 | 500 | 25.502 s | 26.047 s | 1.021 | 6.19 MB | 5.07 MB |

Stage totals are summed across parallel workers and therefore are not wall
clock critical-path durations:

| Scale | Indicator total / mean | Evaluation total / mean |
| ---: | ---: | ---: |
| 30 | 9.018 s / 300.61 ms | 1.025 s / 34.17 ms |
| 100 | 69.655 s / 696.55 ms | 4.496 s / 44.96 ms |
| 500 | 670.393 s / 1,340.79 ms | 58.432 s / 116.86 ms |

This replay isolates local work from network and supports an initial
algorithmic/CPU finding: indicator computation is much larger than evaluation
in summed local work, and its per-symbol cost increases with this dataset
scale. The increase may reflect DataFrame size, allocation pressure and
parallel contention; it does not by itself prove a specific indicator or
algorithm is faulty. Memory pressure is still not proven because RSS and
allocation peaks were measured only at process level.

The next safe measurement is a full multi-timeframe replay built from a
provider snapshot captured outside the rate-limited fallback path, with raw
frames and response metadata preserved. Only after that replay confirms the
same indicator slope and golden output equality should indicator reuse,
incremental calculation or concurrency changes be proposed.
