"""Prepare and benchmark a replayable scanner scaling dataset.

The prepare phase fetches raw OHLCV once and writes Parquet files. The run
phase never calls a provider: it computes indicators and evaluates against the
same replay data for 30, 100 and 500 symbols.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

TIMEFRAMES = ("15m", "1h", "1d")
SCALES = (30, 100, 500)


def _symbols_from_csv(path: Path, limit: int) -> list[str]:
    frame = pd.read_csv(path, usecols=["symbol"])
    symbols = frame["symbol"].astype(str).str.upper().drop_duplicates().tolist()
    return symbols[:limit]


def _prepare_local_daily(dataset: Path, symbols: list[str], cache_dir: Path) -> dict[str, Any]:
    dataset.mkdir(parents=True, exist_ok=True)
    parts = []
    used_symbols = []
    for symbol in symbols:
        path = cache_dir / f"{symbol}.json"
        if not path.exists():
            continue
        rows = json.loads(path.read_text(encoding="utf-8"))
        frame = pd.DataFrame(rows)
        if frame.empty or not {"date", "open", "high", "low", "close", "volume"}.issubset(frame):
            continue
        frame = frame.rename(
            columns={
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
            }
        )
        frame["date"] = pd.to_datetime(frame["date"])
        frame = frame.set_index("date")[["Open", "High", "Low", "Close", "Volume"]]
        frame.insert(0, "symbol", symbol)
        parts.append(frame.reset_index())
        used_symbols.append(symbol)
    if len(used_symbols) < len(symbols):
        raise SystemExit(
            f"Local daily cache only covers {len(used_symbols)}/{len(symbols)} symbols"
        )
    output = dataset / "ohlcv_1d.parquet"
    pd.concat(parts, ignore_index=True).to_parquet(output, index=False)
    manifest = {
        "created_at": datetime.now(tz=UTC).isoformat(),
        "symbols": used_symbols,
        "timeframes": ["1d"],
        "files": {"1d": str(output)},
        "source": str(cache_dir),
        "replay_scope": "daily-only local cache; not a full multi-timeframe scanner replay",
    }
    (dataset / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def _rss_bytes() -> int | None:
    try:
        import psutil

        return int(psutil.Process().memory_info().rss)
    except Exception:
        return None


def prepare(dataset: Path, symbols: list[str]) -> dict[str, Any]:
    from scanner.data_fetcher import prefetch_symbols_multi_timeframe
    from scanner.performance import reset, snapshot, timer

    dataset.mkdir(parents=True, exist_ok=True)
    os.environ["FINPILOT_SCAN_STAGE_TIMING"] = "1"
    reset()
    started = time.perf_counter()
    with timer("replay.prepare", count=len(symbols), path="provider"):
        data = prefetch_symbols_multi_timeframe(
            symbols,
            with_indicators=False,
            max_workers=10,
        )
    files: dict[str, str] = {}
    for timeframe in (*TIMEFRAMES, "4h"):
        parts = []
        for symbol in symbols:
            frame = data.get(symbol, {}).get(timeframe)
            if frame is None or frame.empty:
                continue
            current = frame.reset_index()
            current.insert(0, "symbol", symbol)
            parts.append(current)
        if parts:
            output = dataset / f"ohlcv_{timeframe}.parquet"
            pd.concat(parts, ignore_index=True).to_parquet(output, index=False)
            files[timeframe] = str(output)
    manifest = {
        "created_at": datetime.now(tz=UTC).isoformat(),
        "symbols": symbols,
        "timeframes": list(TIMEFRAMES) + ["4h"],
        "files": files,
        "prepare_wall_s": round(time.perf_counter() - started, 6),
        "stage_timing": snapshot(),
    }
    (dataset / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def _load_replay(dataset: Path, symbols: list[str]) -> dict[str, dict[str, pd.DataFrame]]:
    result = {symbol: {} for symbol in symbols}
    for timeframe in (*TIMEFRAMES, "4h"):
        path = dataset / f"ohlcv_{timeframe}.parquet"
        if not path.exists():
            continue
        frame = pd.read_parquet(path, filters=[("symbol", "in", symbols)])
        for symbol, group in frame.groupby("symbol", sort=False):
            index_column = "index" if "index" in group.columns else "date"
            current = group.drop(columns=["symbol"]).set_index(index_column)
            current.index = pd.to_datetime(current.index)
            result[str(symbol)][timeframe] = current
    return result


def run_scale(dataset: Path, symbols: list[str], scale: int) -> dict[str, Any]:
    from scanner.evaluate import evaluate_symbol
    from scanner.indicators import add_indicators
    from scanner.performance import reset, snapshot, timer
    from scripts.golden_scan import snapshot_from_results

    selected = symbols[:scale]
    replay = _load_replay(dataset, selected)
    reset()
    gc.collect()
    tracemalloc.start()
    rss_before = _rss_bytes()
    wall_started = time.perf_counter()
    cpu_started = time.process_time()

    def evaluate_one(symbol: str) -> dict[str, Any]:
        frames = replay.get(symbol, {})
        prepared: dict[str, pd.DataFrame] = {}
        for timeframe in TIMEFRAMES:
            frame = frames.get(timeframe, pd.DataFrame())
            prepared[timeframe] = add_indicators(frame) if not frame.empty else frame
        if "4h" in frames and not frames["4h"].empty:
            prepared["4h"] = add_indicators(frames["4h"])
        with timer("evaluation.symbol", count=1, path="replay"):
            return evaluate_symbol(symbol, 0.5, prefetched_data=prepared)

    results: list[dict[str, Any]] = []
    workers = min(32, max(4, scale))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(evaluate_one, symbol): symbol for symbol in selected}
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    wall_s = time.perf_counter() - wall_started
    cpu_s = time.process_time() - cpu_started
    _, peak_alloc = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    rss_after = _rss_bytes()
    return {
        "scale": scale,
        "symbols_requested": scale,
        "results": len(results),
        "wall_s": round(wall_s, 6),
        "cpu_process_s": round(cpu_s, 6),
        "cpu_wall_ratio": round(cpu_s / wall_s, 6) if wall_s else None,
        "peak_tracemalloc_bytes": peak_alloc,
        "rss_delta_bytes": rss_after - rss_before
        if rss_before is not None and rss_after is not None
        else None,
        "stage_timing": snapshot(),
        "decision_snapshot": snapshot_from_results(results),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Replay scanner scaling benchmark")
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--dataset", default="data/scanner_replay_2026-08-04")
    parser.add_argument("--symbols-file", default="data/backtest_out/full_universe_raw.csv")
    parser.add_argument("--local-daily-cache", default="data/price_cache")
    parser.add_argument("--daily-only", action="store_true")
    parser.add_argument("--output", default="reports/scanner_replay_scaling_2026-08-04.json")
    args = parser.parse_args(argv[1:])

    dataset = Path(args.dataset)
    symbols = _symbols_from_csv(Path(args.symbols_file), 500)
    if len(symbols) < 500:
        raise SystemExit(f"Need 500 symbols, found {len(symbols)}")
    os.environ["FINPILOT_SCAN_STAGE_TIMING"] = "1"

    manifest = None
    if args.prepare or not (dataset / "manifest.json").exists():
        manifest = (
            _prepare_local_daily(dataset, symbols, Path(args.local_daily_cache))
            if args.daily_only
            else prepare(dataset, symbols)
        )
    elif args.daily_only:
        manifest = json.loads((dataset / "manifest.json").read_text(encoding="utf-8"))
    results = [run_scale(dataset, symbols, scale) for scale in SCALES]
    payload = {
        "benchmark": "replay-scaling-30-100-500-20260804",
        "created_at": datetime.now(tz=UTC).isoformat(),
        "dataset": str(dataset),
        "symbols_source": args.symbols_file,
        "symbols": symbols,
        "network_in_run_phase": False,
        "prepare": manifest,
        "scales": results,
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
                "dataset": str(dataset),
                "network_in_run_phase": False,
                "scales": [
                    {
                        "scale": item["scale"],
                        "wall_s": item["wall_s"],
                        "cpu_s": item["cpu_process_s"],
                    }
                    for item in results
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
