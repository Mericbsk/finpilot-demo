"""Read-only forensic audit of scanner timing evidence.

This script consumes the append-only timing log and never starts a scan,
changes configuration, or writes to runtime data.  It produces the audit
report and CSV evidence files requested by the 2026-09-21 master prompt.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "data" / "distribution" / "scan_timing.jsonl"
REPORTS = ROOT / "reports"
TODAY = "2026-09-21"


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=100, method="inclusive")[int(fraction * 100) - 1]


def fmt(value: float | None) -> str:
    return "UNKNOWN" if value is None else f"{value:.2f}"


def load_rows() -> list[dict]:
    return [
        json.loads(line) for line in LOG.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    rows = load_rows()
    full_batch = [row for row in rows if row.get("universe") == 200]
    recent = [row for row in full_batch if row.get("date") == TODAY]
    stage_events = sum(bool(row.get("stage_timing")) for row in rows)
    totals = [float(row["total_s"]) for row in full_batch if row.get("total_s") is not None]
    fallback = [float(row.get("yf_fallback") or 0) for row in full_batch]

    stage_rows = []
    for stage, duration_values, source, kind in (
        (
            "evaluation.window",
            [float(row.get("eval_s") or 0) for row in full_batch],
            "LOGGED",
            "UNKNOWN",
        ),
        (
            "enrichment.window",
            [float(row.get("enrich_s") or 0) for row in full_batch],
            "LOGGED",
            "UNKNOWN",
        ),
    ):
        median = statistics.median(duration_values) if duration_values else None
        p95 = percentile(duration_values, 0.95)
        total_median = statistics.median(totals) if totals else None
        share = (median / total_median * 100) if median is not None and total_median else None
        stage_rows.append(
            {
                "stage": stage,
                "source": source,
                "median_s": fmt(median),
                "p95_s": fmt(p95),
                "share_percent": fmt(share),
                "bottleneck_type": kind,
                "per_symbol": "UNKNOWN",
                "theoretical_max_gain_percent": fmt(share),
                "measurement_scope": "200-symbol logged batches; not full universe",
            }
        )
    for stage, reason in (
        ("prefetch.alpaca", "stage_timing disabled in all log records"),
        ("prefetch.repair", "stage_timing disabled in all log records"),
        ("prefetch.bulk_yfinance", "stage_timing disabled in all log records"),
        ("prefetch.resample_4h", "stage_timing disabled in all log records"),
        ("prefetch.symbol_yfinance", "stage_timing disabled in all log records"),
        ("fetch.request", "stage_timing disabled in all log records"),
        ("fetch.parse", "stage_timing disabled in all log records"),
        ("retry.attempt", "stage_timing disabled in all log records"),
        ("retry.backoff", "stage_timing disabled in all log records"),
        ("rate_limit.wait", "stage_timing disabled in all log records"),
        ("indicator.compute", "stage_timing disabled in all log records"),
        ("evaluation.symbol", "stage_timing disabled in all log records"),
        ("persist.shortlist", "called after _t_scoring_done; no timer exists"),
        ("persist.shadow_ledger", "called after _t_scoring_done; no timer exists"),
        ("persist.watchlist", "called after _t_scoring_done; no timer exists"),
        ("persist.distribution_export", "called after _t_scoring_done; no timer exists"),
    ):
        stage_rows.append(
            {
                "stage": stage,
                "source": "UNKNOWN",
                "median_s": "UNKNOWN",
                "p95_s": "UNKNOWN",
                "share_percent": "UNKNOWN",
                "bottleneck_type": "UNKNOWN",
                "per_symbol": "UNKNOWN",
                "theoretical_max_gain_percent": "UNKNOWN",
                "measurement_scope": reason,
            }
        )

    variance_rows = []
    for index, row in enumerate(rows, start=1):
        variance_rows.append(
            {
                "run_index": index,
                "date": row.get("date", "UNKNOWN"),
                "timestamp": row.get("ts", "UNKNOWN"),
                "universe": row.get("universe", "UNKNOWN"),
                "symbols": row.get("symbols", "UNKNOWN"),
                "cache_state": "UNKNOWN",
                "market_session": "UNKNOWN",
                "total_s": row.get("total_s", "UNKNOWN"),
                "eval_s": row.get("eval_s", "UNKNOWN"),
                "enrich_s": row.get("enrich_s", "UNKNOWN"),
                "yf_fallback": row.get("yf_fallback", "UNKNOWN"),
                "stage_timing_present": bool(row.get("stage_timing")),
                "source": "LOGGED",
            }
        )

    gap_rows = [
        {
            "stage": row["stage"],
            "status": row["source"],
            "reason": row["measurement_scope"],
            "how_to_measure": "Enable FINPILOT_SCAN_STAGE_TIMING for an approved controlled run; add outer wall-clock timers for persistence.",
        }
        for row in stage_rows
        if row["source"] == "UNKNOWN"
    ]

    write_csv(REPORTS / "scan_stage_breakdown_2026-09-21.csv", list(stage_rows[0]), stage_rows)
    write_csv(
        REPORTS / "scan_variance_analysis_2026-09-21.csv", list(variance_rows[0]), variance_rows
    )
    write_csv(REPORTS / "scan_instrumentation_gaps_2026-09-21.csv", list(gap_rows[0]), gap_rows)

    fallback_pairs = [
        (x, y)
        for x, y in zip(fallback, totals, strict=False)
        if math.isfinite(x) and math.isfinite(y)
    ]
    if len(fallback_pairs) > 1:
        x_mean = statistics.mean(x for x, _ in fallback_pairs)
        y_mean = statistics.mean(y for _, y in fallback_pairs)
        covariance = sum((x - x_mean) * (y - y_mean) for x, y in fallback_pairs)
        denominator = math.sqrt(
            sum((x - x_mean) ** 2 for x, _ in fallback_pairs)
            * sum((y - y_mean) ** 2 for _, y in fallback_pairs)
        )
        fallback_corr = covariance / denominator if denominator else None
    else:
        fallback_corr = None

    report = f"""# Scan Performance Audit — 2026-09-21

## 1. Executive Summary

**PRIMARY STATUS = NOT MEASURED.** The requested full-universe stage breakdown cannot be established from the available evidence. The timing log contains {len(rows)} records, including {len(full_batch)} logged 200-symbol batches and {len(recent)} records dated {TODAY}; none contains stage events. The reported `total_s` is measured only through `_t_scoring_done`, before four persistence calls. No production code, flag, cache, database, scheduler, scan, queue, or publication was changed or run by this audit.

The strongest logged fact is that 200-symbol batch duration varies from {fmt(min(totals) if totals else None)}s to {fmt(max(totals) if totals else None)}s, with median {fmt(statistics.median(totals) if totals else None)}s and p95 {fmt(percentile(totals, 0.95))}s. This is **LOGGED**, not a new measurement. The source of the variance is **UNKNOWN** because fallback count, cache state, provider wait, retry backoff, and stage timing are not jointly observed.

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

`scanner/performance.py` is opt-in. Existing log coverage is {stage_events}/{len(rows)} records with non-empty `stage_timing` (**LOGGED**). The flag was not changed. `api/routers/scan.py` records `total_s` immediately before `_persist_shortlist`, `_persist_shadow_ledger`, `_auto_add_watchlist`, and `_persist_distribution_export`; their wall-clock duration is outside the current window (**CODE-VERIFIED**, duration **UNKNOWN**).

## 4. Measurement Window

`total_s` is a logged score/evaluation window, not proven end-to-end scan wall-clock time. The missing persistence duration cannot be assigned a percentage from current evidence. Full-universe duration is also **UNKNOWN**: the log contains 200-symbol batches, not a single 1812/1900-symbol end-to-end run.

## 5. Stage Breakdown and Amdahl Ceiling

The CSV companion contains logged evaluation/enrichment windows and UNKNOWN rows for every uninstrumented stage. For the 200-symbol logged population, the median evaluation window is {fmt(statistics.median([float(r.get('eval_s') or 0) for r in full_batch]) if full_batch else None)}s and the median enrichment window is {fmt(statistics.median([float(r.get('enrich_s') or 0) for r in full_batch]) if full_batch else None)}s (**LOGGED**). Their percentage of the **measured window** is derived from medians; it is not a percentage of true end-to-end scan time. Amdahl ceilings for unknown stages are UNKNOWN.

## 6. Bottleneck Type

Network wait, CPU, disk I/O, lock/serialization, and provider rate-limit wait are **UNKNOWN** at stage level. `enrich_s` is near zero in the logged records, but this does not measure individual indicator CPU time or provider wait. No optimization conclusion follows.

## 7. Variance Analysis

The companion variance CSV preserves each logged run. Cache state and market session are recorded as UNKNOWN because the source log does not contain them. For 200-symbol runs, `yf_fallback` and `total_s` are both logged; their Pearson correlation is {fmt(fallback_corr)} (**DERIVED** from {len(fallback_pairs)} logged pairs), but this is not causal evidence and does not separate cache, network, rate-limit, or retry effects.

## 8. Serialization Analysis

`rate_limit.wait` and `retry.backoff` totals are **UNKNOWN**. Worker parallelism, GIL effects, and batch gaps are **UNKNOWN**. No parallelism recommendation is authorized by this audit.

## 9. Scale Model

The requested model remains uninstantiated:

`total_s ≈ fixed_cost + symbols × per_symbol_cost + fallback_symbols × fallback_extra_cost`

The terms are **UNKNOWN** for a full-universe run. Extrapolation from 200-symbol batches is intentionally omitted because fallback/cache/session state is not controlled and no full-run total is measured.

## 10. Decision Tree Result

**Status F: measurement incomplete.** The audit cannot select A–E because stage timing and end-to-end coverage are missing. No single bottleneck claim is made.

## 11. What We Measured

- **LOGGED:** {len(rows)} JSONL timing records; {len(full_batch)} with `universe=200`.
- **LOGGED:** 200-symbol total window median {fmt(statistics.median(totals) if totals else None)}s, p95 {fmt(percentile(totals, 0.95))}s, min {fmt(min(totals) if totals else None)}s, max {fmt(max(totals) if totals else None)}s.
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
- Generated: {datetime.now(UTC).isoformat()}
- Output files: `reports/scan_stage_breakdown_2026-09-21.csv`, `reports/scan_variance_analysis_2026-09-21.csv`, `reports/scan_instrumentation_gaps_2026-09-21.csv`
"""
    (REPORTS / "scan_performance_audit_2026-09-21.md").write_text(report, encoding="utf-8")
    print(report.split("## 2.", 1)[0].rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
