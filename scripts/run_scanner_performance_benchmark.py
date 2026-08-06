"""Controlled 30-symbol scanner performance benchmark.

Runs one process-cold and one warm-cache scan with identical symbols, captures
opt-in scanner stage timing, resource counters, and compares decision snapshots.
This is research instrumentation only; it does not publish or overwrite scan
artifacts.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
import tracemalloc
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

DEFAULT_SYMBOLS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "AMD",
    "NFLX",
    "AVGO",
    "JPM",
    "BAC",
    "XOM",
    "PFE",
    "KO",
    "INTC",
    "CSCO",
    "ABNB",
    "SOFI",
    "PLTR",
    "MCD",
    "WMT",
    "COST",
    "ORCL",
    "ADBE",
    "QCOM",
    "TXN",
    "C",
    "GS",
    "DIS",
]


def _rss_bytes() -> int | None:
    try:
        import psutil

        return int(psutil.Process().memory_info().rss)
    except Exception:
        return None


def _clear_process_cache() -> str:
    try:
        from scanner import data_fetcher

        data_fetcher._memory_cache.clear()
        return "data_fetcher._memory_cache cleared"
    except Exception as exc:
        return f"process cache clear unavailable: {type(exc).__name__}"


def _run_once(symbols: list[str], label: str) -> dict[str, Any]:
    from scanner import evaluate_symbols_parallel
    from scanner.data_fetcher import (
        alpaca_miss_by_tf,
        reset_yf_fetch_count,
        yf_fetch_count,
    )
    from scanner.performance import snapshot as stage_snapshot
    from scripts.golden_scan import snapshot_from_results

    reset_yf_fetch_count()
    gc.collect()
    tracemalloc.start()
    rss_before = _rss_bytes()
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    results = evaluate_symbols_parallel(symbols=symbols, kelly_fraction=0.5)
    wall_s = time.perf_counter() - wall_started
    cpu_s = time.process_time() - cpu_started
    _, peak_alloc = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    rss_after = _rss_bytes()
    snapshot = snapshot_from_results(results)
    return {
        "label": label,
        "symbols_requested": len(symbols),
        "results": len(results),
        "wall_s": round(wall_s, 6),
        "cpu_process_s": round(cpu_s, 6),
        "cpu_wall_ratio": round(cpu_s / wall_s, 6) if wall_s else None,
        "peak_tracemalloc_bytes": peak_alloc,
        "rss_before_bytes": rss_before,
        "rss_after_bytes": rss_after,
        "rss_delta_bytes": (rss_after - rss_before)
        if rss_before is not None and rss_after is not None
        else None,
        "yf_fallback": yf_fetch_count(),
        "alpaca_miss": alpaca_miss_by_tf(),
        "stage_timing": stage_snapshot(),
        "decision_snapshot": snapshot,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run controlled scanner performance benchmark")
    parser.add_argument("--output", default="reports/scanner_performance_benchmark_2026-08-04.json")
    parser.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    args = parser.parse_args(argv[1:])

    symbols = [symbol.strip().upper() for symbol in args.symbols.split(",") if symbol.strip()]
    if len(symbols) != 30:
        raise SystemExit(f"Expected exactly 30 symbols, got {len(symbols)}")
    os.environ["FINPILOT_SCAN_STAGE_TIMING"] = "1"

    cold_cache_note = _clear_process_cache()
    cold = _run_once(symbols, "process_cold")
    warm = _run_once(symbols, "warm")

    from scripts.golden_scan import diff_snapshots

    diffs = diff_snapshots(cold["decision_snapshot"], warm["decision_snapshot"])
    payload = {
        "benchmark": "phase1-30-symbol-cold-warm-20260804",
        "created_at": datetime.now(tz=UTC).isoformat(),
        "symbols": symbols,
        "cache_note": cold_cache_note,
        "cache_scope": "process-cold; external cache state not forcibly cleared",
        "stage_timing_enabled": True,
        "cold": cold,
        "warm": warm,
        "golden_equal": not diffs,
        "golden_diffs": diffs,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(output),
                "cold_wall_s": cold["wall_s"],
                "warm_wall_s": warm["wall_s"],
                "cold_cpu_s": cold["cpu_process_s"],
                "warm_cpu_s": warm["cpu_process_s"],
                "cold_fallback": cold["yf_fallback"],
                "warm_fallback": warm["yf_fallback"],
                "golden_equal": not diffs,
                "cold_stage_events": len(cold["stage_timing"]),
                "warm_stage_events": len(warm["stage_timing"]),
            },
            ensure_ascii=False,
        )
    )
    return 0 if not diffs else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
