#!/usr/bin/env python3
"""Research-only signal timing and forward drift study."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import median

DEFAULT_CSV = Path("data/backtest_out/full_universe_enriched.csv")
DEFAULT_CACHE = Path("data/price_cache")
DEFAULT_OUT = Path("data/backtest_out/timing_drift_study_2026-08-07.json")
DEFAULT_BENCHMARKS = ("SPY", "IWM")


def _float(value: object) -> float | None:
    try:
        parsed = float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None
    return parsed if parsed is not None and math.isfinite(parsed) else None


def load_bars(cache_dir: Path, symbol: str) -> list[dict[str, float | str]]:
    path = cache_dir / f"{symbol}.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return []
    bars = []
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, dict) or not item.get("date"):
            continue
        values = {key: _float(item.get(key)) for key in ("open", "high", "low", "close", "volume")}
        if values["open"] is None or values["close"] is None:
            continue
        bars.append({"date": str(item["date"]), **values})
    return sorted(bars, key=lambda item: str(item["date"]))


def _bar_index(bars: list[dict], date: str) -> int | None:
    for index, bar in enumerate(bars):
        if bar["date"] >= date:
            return index
    return None


def _indexed_bars(bars: list[dict]) -> tuple[list[dict], dict[str, int]]:
    ordered = sorted(bars, key=lambda item: str(item["date"]))
    return ordered, {str(bar["date"]): index for index, bar in enumerate(ordered)}


def load_signal_rows(csv_path: Path) -> list[dict]:
    rows = []
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        for index, raw in enumerate(csv.DictReader(handle)):
            symbol = str(raw.get("symbol") or "").strip()
            scan_date = str(raw.get("scan_date") or "").strip()
            price = _float(raw.get("price"))
            if not symbol or not scan_date or price is None or price <= 0:
                continue
            rows.append(
                {
                    "row_id": f"{symbol}_{raw.get('scan_ts')}_{index}",
                    "symbol": symbol,
                    "scan_date": scan_date,
                    "scan_ts": str(raw.get("scan_ts") or ""),
                    "recorded_price": price,
                    "direction": str(raw.get("direction") or "").strip().lower()
                    in {"1", "true", "yes"},
                    "entry_ok": str(raw.get("entry_ok") or "").strip().lower()
                    in {"1", "true", "yes"},
                    "composite_score": _float(raw.get("composite_score")),
                    "finpilot_score": _float(raw.get("finpilot_score")),
                    "atr_pct": _float(raw.get("atr_pct_real")),
                    "gap_pct": _float(raw.get("gap_pct")),
                    "rvol": _float(raw.get("rvol")),
                }
            )
    return rows


def deduplicate_symbol_day(rows: list[dict]) -> list[dict]:
    selected: dict[tuple[str, str], dict] = {}
    for row in rows:
        key = (row["symbol"], row["scan_date"])
        current = selected.get(key)
        if current is None or row["scan_ts"] < current["scan_ts"]:
            selected[key] = row
    return sorted(
        selected.values(), key=lambda row: (row["scan_date"], row["symbol"], row["scan_ts"])
    )


def _return_pct(entry: float, exit_price: float) -> float:
    return ((exit_price / entry) - 1.0) * 100.0


def _summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {
            "n": 0,
            "mean_pct": None,
            "median_pct": None,
            "trimmed_mean_pct": None,
            "positive_rate": None,
        }
    ordered = sorted(values)
    trim = max(1, int(len(ordered) * 0.10)) if len(ordered) >= 10 else 0
    trimmed = ordered[trim : len(ordered) - trim] if trim else ordered
    return {
        "n": len(values),
        "mean_pct": round(sum(values) / len(values), 6),
        "median_pct": round(median(values), 6),
        "trimmed_mean_pct": round(sum(trimmed) / len(trimmed), 6),
        "positive_rate": round(sum(value > 0 for value in values) / len(values), 6),
        "min_pct": round(min(values), 6),
        "max_pct": round(max(values), 6),
    }


def _tail_contribution(values: list[float], fraction: float = 0.05) -> float | None:
    if not values:
        return None
    top_n = max(1, int(len(values) * fraction))
    total = sum(values)
    return round(sum(sorted(values, reverse=True)[:top_n]) / total, 6) if total else None


def build_observations(
    rows: list[dict], cache_dir: Path, horizons: list[int], benchmark_symbols: tuple[str, ...]
):
    cache: dict[str, tuple[list[dict], dict[str, int]]] = {}
    benchmark_bars = {
        symbol: _indexed_bars(load_bars(cache_dir, symbol)) for symbol in benchmark_symbols
    }
    observations = []
    inventory = defaultdict(int)
    max_horizon = max(horizons)
    for row in rows:
        symbol_data = cache.get(row["symbol"])
        if symbol_data is None:
            symbol_data = _indexed_bars(load_bars(cache_dir, row["symbol"]))
            cache[row["symbol"]] = symbol_data
        bars, date_index = symbol_data
        index = date_index.get(row["scan_date"])
        if index is None:
            index = next((i for i, bar in enumerate(bars) if bar["date"] >= row["scan_date"]), None)
        if index is None:
            inventory["missing_symbol_path"] += 1
            continue
        signal_bar = bars[index]
        forward = bars[index + 1 : index + 2 + max_horizon]
        if len(forward) < max_horizon + 1:
            inventory["short_forward_path"] += 1
            continue
        observation = {
            **row,
            "cache_signal_date": signal_bar["date"],
            "cache_signal_close": signal_bar["close"],
            "entry_drift_pct": round(
                (row["recorded_price"] / signal_bar["close"] - 1.0) * 100.0, 6
            ),
            "next_open": forward[0]["open"],
            "next_close": forward[0]["close"],
            "benchmark_returns": {},
            "returns": {},
        }
        for horizon in horizons:
            exit_bar = forward[horizon - 1]
            observation["returns"][str(horizon)] = {
                "signal_close": _return_pct(signal_bar["close"], exit_bar["close"]),
                "next_open": _return_pct(forward[0]["open"], exit_bar["close"]),
                "next_close": _return_pct(forward[0]["close"], forward[horizon]["close"]),
            }
            for benchmark_symbol, (
                bars_for_benchmark,
                benchmark_date_index,
            ) in benchmark_bars.items():
                benchmark_index = benchmark_date_index.get(row["scan_date"])
                if benchmark_index is None:
                    benchmark_index = next(
                        (
                            i
                            for i, bar in enumerate(bars_for_benchmark)
                            if bar["date"] >= row["scan_date"]
                        ),
                        None,
                    )
                if benchmark_index is None or benchmark_index + horizon >= len(bars_for_benchmark):
                    continue
                benchmark_forward = bars_for_benchmark[
                    benchmark_index + 1 : benchmark_index + 2 + horizon
                ]
                if len(benchmark_forward) < horizon + 1:
                    continue
                starts = {
                    "signal_close": bars_for_benchmark[benchmark_index]["close"],
                    "next_open": benchmark_forward[0]["open"],
                    "next_close": benchmark_forward[0]["close"],
                }
                ends = {
                    "signal_close": benchmark_forward[horizon - 1]["close"],
                    "next_open": benchmark_forward[horizon - 1]["close"],
                    "next_close": benchmark_forward[horizon]["close"],
                }
                for entry_name in starts:
                    observation["benchmark_returns"].setdefault(str(horizon), {}).setdefault(
                        benchmark_symbol, {}
                    )[entry_name] = (ends[entry_name] / starts[entry_name] - 1.0) * 100.0
        observations.append(observation)
        inventory["resolved"] += 1
    inventory["loaded_symbols"] = len(cache)
    inventory["benchmark_symbols_available"] = sum(bool(bars) for bars in benchmark_bars.values())
    return observations, dict(inventory)


def summarize_observations(
    observations: list[dict], horizons: list[int], benchmark_symbols: tuple[str, ...]
) -> dict:
    result = {}
    for horizon in horizons:
        horizon_result = {}
        for entry_name in ("signal_close", "next_open", "next_close"):
            values = [item["returns"][str(horizon)][entry_name] for item in observations]
            summary = _summary(values)
            summary["top_5_pct_contribution"] = _tail_contribution(values)
            horizon_result[entry_name] = summary
            for benchmark_symbol in benchmark_symbols:
                excess = [
                    item["returns"][str(horizon)][entry_name]
                    - item["benchmark_returns"][str(horizon)][benchmark_symbol][entry_name]
                    for item in observations
                    if entry_name
                    in item["benchmark_returns"].get(str(horizon), {}).get(benchmark_symbol, {})
                ]
                horizon_result[f"{entry_name}_minus_{benchmark_symbol}"] = _summary(excess)
        result[str(horizon)] = horizon_result
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--horizons", default="1,2,3,5,10")
    parser.add_argument("--benchmark", default=",".join(DEFAULT_BENCHMARKS))
    args = parser.parse_args()
    horizons = [int(value) for value in args.horizons.split(",") if value.strip()]
    benchmark_symbols = tuple(
        value.strip().upper() for value in args.benchmark.split(",") if value.strip()
    )
    raw_rows = load_signal_rows(args.csv)
    rows = deduplicate_symbol_day(raw_rows)
    observations, inventory = build_observations(rows, args.cache, horizons, benchmark_symbols)
    abs_drifts = sorted(abs(item["entry_drift_pct"]) for item in observations)
    output = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "status": "diagnostic_only",
        "methodology": {
            "input": str(args.csv),
            "cache": str(args.cache),
            "entry_points": ["signal_close", "next_open", "next_close"],
            "horizons_days": horizons,
            "directional_return": False,
            "direction_field": "diagnostic bullish gate only; not interpreted as long/short orientation",
            "deduplication": "earliest scan_ts per symbol-day",
            "benchmark_adjustment": "same-date close-to-close benchmark return; not beta-neutral",
            "intraday_data_used": False,
        },
        "data_contract": {
            "raw_rows": len(raw_rows),
            "deduplicated_rows": len(rows),
            **inventory,
            "entry_drift_abs_median_pct": round(median(abs_drifts), 6) if abs_drifts else None,
            "entry_drift_abs_p95_pct": round(
                abs_drifts[min(len(abs_drifts) - 1, int(len(abs_drifts) * 0.95))], 6
            )
            if abs_drifts
            else None,
        },
        "summary": summarize_observations(observations, horizons, benchmark_symbols),
        "diagnostic_tags": {
            "entry_ok_n": sum(item["entry_ok"] for item in observations),
            "direction_true_n": sum(item["direction"] for item in observations),
            "non_entry_ok_n": sum(not item["entry_ok"] for item in observations),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"OK -> {args.out}")
    print(f"raw={len(raw_rows)} dedup={len(rows)} resolved={len(observations)}")
    print(json.dumps(inventory, sort_keys=True))


if __name__ == "__main__":
    main()
