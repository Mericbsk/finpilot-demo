"""Research-only High RVOL raw-OHLC horizon and exit battery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from research.budget_return_battery_2026_08_12 import DEFAULT_COST_PCT

FIXED_TARGETS_PCT = (0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 7.0, 10.0)
ATR_TARGETS = (0.5, 1.0, 1.5, 2.0, 3.0)
ATR_STOPS = (1.0, 1.5, 2.0)


def _bars(cache: Path, symbol: str) -> list[dict[str, Any]]:
    path = cache / f"{symbol}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return sorted(
        [
            b
            for b in data
            if all(b.get(k) is not None for k in ("date", "open", "high", "low", "close"))
        ],
        key=lambda b: b["date"],
    )


def _atr_pct(bars: list[dict[str, Any]], index: int, period: int = 14) -> float | None:
    if index < 1:
        return None
    true_ranges = []
    for i in range(max(1, index - period), index):
        current = bars[i]
        previous = bars[i - 1]["close"]
        true_ranges.append(
            max(
                current["high"] - current["low"],
                abs(current["high"] - previous),
                abs(current["low"] - previous),
            )
        )
    return (
        (sum(true_ranges) / len(true_ranges)) / bars[index]["close"] * 100
        if true_ranges and bars[index]["close"]
        else None
    )


def _path(row: pd.Series, cache: Path, max_horizon: int) -> dict[str, Any] | None:
    bars = _bars(cache, str(row["symbol"]))
    index_by_date = {bar["date"]: i for i, bar in enumerate(bars)}
    index = index_by_date.get(str(row["scan_date"]))
    if index is None:
        return None
    entry = float(bars[index]["close"])
    atr_pct = _atr_pct(bars, index)
    if not atr_pct or atr_pct <= 0:
        return None
    future = bars[index + 1 : index + 1 + max_horizon]
    if len(future) < max_horizon:
        return None
    closes = np.array([float(bar["close"]) for bar in future])
    highs = np.array([float(bar["high"]) for bar in future])
    lows = np.array([float(bar["low"]) for bar in future])
    return {
        "symbol": row["symbol"],
        "scan_date": row["scan_date"],
        "entry_ok": bool(row["entry_ok"]),
        "entry": entry,
        "atr_pct": atr_pct,
        "close_returns": ((closes / entry) - 1) * 100,
        "mfe": ((np.maximum.accumulate(highs) / entry) - 1) * 100,
        "mae": ((np.minimum.accumulate(lows) / entry) - 1) * 100,
        "highs": highs,
        "lows": lows,
        "opens": np.array([float(bar["open"]) for bar in future]),
    }


def _summary(values: list[float], cost_pct: float) -> dict[str, Any]:
    series = pd.Series(values, dtype=float)
    net = series - cost_pct
    return {
        "rows": int(len(series)),
        "mean_pct": float(series.mean()) if len(series) else None,
        "median_pct": float(series.median()) if len(series) else None,
        "p10_pct": float(series.quantile(0.10)) if len(series) else None,
        "p90_pct": float(series.quantile(0.90)) if len(series) else None,
        "mean_net_pct": float(net.mean()) if len(series) else None,
        "median_net_pct": float(net.median()) if len(series) else None,
        "clipped_mean_net_pct": float(series.clip(-50, 50).sub(cost_pct).mean())
        if len(series)
        else None,
    }


def _first_touch_exit(
    item: dict[str, Any],
    horizon: int,
    target_pct: float,
    stop_multiple: float,
) -> tuple[float, str]:
    entry = float(item["entry"])
    target = entry * (1 + target_pct / 100)
    stop = entry * (1 - stop_multiple * float(item["atr_pct"]) / 100)
    highs = item["highs"][:horizon]
    lows = item["lows"][:horizon]
    opens = item["opens"][:horizon]
    for index, (high, low) in enumerate(zip(highs, lows, strict=True)):
        stop_hit = float(low) <= stop
        target_hit = float(high) >= target
        if stop_hit:
            fill = min(float(opens[index]), stop)
            return (fill / entry - 1) * 100, "stop"
        if target_hit:
            fill = max(float(opens[index]), target)
            return (fill / entry - 1) * 100, "target"
    return float(item["close_returns"][horizon - 1]), "time"


def _target_grid(
    paths: list[dict[str, Any]],
    horizon: int,
    targets: tuple[float, ...],
    *,
    atr_targets: bool,
) -> dict[str, Any]:
    grid = {}
    for target in targets:
        target_results = {}
        for stop_multiple in ATR_STOPS:
            returns = []
            events = {"target": 0, "stop": 0, "time": 0}
            for item in paths:
                target_pct = target * float(item["atr_pct"]) if atr_targets else target
                value, event = _first_touch_exit(item, horizon, target_pct, stop_multiple)
                returns.append(value)
                events[event] += 1
            target_results[str(stop_multiple)] = {
                "stop_multiple": stop_multiple,
                "target_mode": "atr" if atr_targets else "fixed_pct",
                "target_value": target,
                "target_hit_share": events["target"] / len(paths) if paths else None,
                "stop_hit_share": events["stop"] / len(paths) if paths else None,
                "time_exit_share": events["time"] / len(paths) if paths else None,
                "time_or_stop_or_target": _summary(returns, DEFAULT_COST_PCT),
            }
        grid[str(target)] = target_results
    return grid


def _matched_control(
    paths: list[dict[str, Any]], all_paths: list[dict[str, Any]], horizon: int, runs: int = 100
) -> dict[str, Any]:
    selected_by_date = {}
    universe_by_date = {}
    for item in paths:
        selected_by_date.setdefault(item["scan_date"], []).append(item)
    for item in all_paths:
        universe_by_date.setdefault(item["scan_date"], []).append(item)
    rng = np.random.default_rng(20260812 + horizon)
    selected_means = []
    random_means = []
    for date, selected in selected_by_date.items():
        universe = universe_by_date.get(date, [])
        selected_symbols = {item["symbol"] for item in selected}
        universe = [item for item in universe if item["symbol"] not in selected_symbols]
        if len(universe) < len(selected):
            continue
        selected_means.append(
            float(np.mean([item["close_returns"][horizon - 1] for item in selected]))
        )
        for _ in range(runs):
            sample = rng.choice(len(universe), size=len(selected), replace=False)
            random_means.append(
                float(np.mean([universe[i]["close_returns"][horizon - 1] for i in sample]))
            )
    selected_mean = float(np.mean(selected_means)) if selected_means else None
    random_mean = float(np.mean(random_means)) if random_means else None
    return {
        "runs": runs,
        "matched_dates": len(selected_means),
        "selected_mean_pct": selected_mean,
        "random_control_mean_pct": random_mean,
        "lift_vs_random_pct_points": selected_mean - random_mean
        if selected_mean is not None and random_mean is not None
        else None,
    }


def run(
    csv_path: Path,
    cache_dir: Path,
    min_history_dates: int = 10,
    max_horizon: int = 10,
    random_runs: int = 100,
) -> dict[str, Any]:
    frame = pd.read_csv(csv_path, low_memory=False)
    required = {"symbol", "scan_date", "entry_ok", "rvol"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    frame["scan_date"] = pd.to_datetime(frame["scan_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    frame["rvol"] = pd.to_numeric(frame["rvol"], errors="coerce")
    frame["entry_ok"] = frame["entry_ok"].astype(str).str.lower().isin(("true", "1", "yes"))
    frame = frame.dropna(subset=["scan_date", "rvol"]).drop_duplicates(
        ["symbol", "scan_date"], keep="last"
    )
    dates = sorted(frame["scan_date"].unique())
    selected_rows = []
    for index, date in enumerate(dates):
        if index < min_history_dates:
            continue
        threshold = frame[frame["scan_date"].isin(dates[:index])]["rvol"].quantile(0.90)
        selected_rows.append(frame[(frame["scan_date"] == date) & (frame["rvol"] >= threshold)])
    selected = pd.concat(selected_rows, ignore_index=True) if selected_rows else frame.iloc[:0]
    all_rows = frame[frame["scan_date"].isin(selected["scan_date"])]
    selected_paths = [_path(row, cache_dir, max_horizon) for _, row in selected.iterrows()]
    all_paths = [_path(row, cache_dir, max_horizon) for _, row in all_rows.iterrows()]
    selected_paths = [item for item in selected_paths if item]
    all_paths = [item for item in all_paths if item]
    cohorts = {
        "high_rvol_all": selected_paths,
        "high_rvol_eligible": [item for item in selected_paths if item["entry_ok"]],
        "high_rvol_rejected": [item for item in selected_paths if not item["entry_ok"]],
    }
    summaries = {}
    controls = {}
    for name, paths in cohorts.items():
        horizons = {}
        stop_grid = {}
        for horizon in range(1, max_horizon + 1):
            returns = [float(item["close_returns"][horizon - 1]) for item in paths]
            horizons[str(horizon)] = _summary(returns, DEFAULT_COST_PCT)
            stop_grid[str(horizon)] = {}
            for multiple in ATR_STOPS:
                stop_returns = []
                hit = 0
                for item in paths:
                    stop = item["entry"] * (1 - multiple * item["atr_pct"] / 100)
                    lows = item["lows"][:horizon]
                    hit_indices = np.flatnonzero(lows <= stop)
                    if len(hit_indices):
                        hit += 1
                        i = int(hit_indices[0])
                        fill = min(float(item["opens"][i]), stop)
                        stop_returns.append((fill / item["entry"] - 1) * 100)
                    else:
                        stop_returns.append(float(item["close_returns"][horizon - 1]))
                stop_grid[str(horizon)][str(multiple)] = {
                    "stop_hit_share": hit / len(paths) if paths else None,
                    "time_or_stop": _summary(stop_returns, DEFAULT_COST_PCT),
                }
        summaries[name] = {
            "rows": len(paths),
            "horizon_close_to_close": horizons,
            "atr_stop_grid": stop_grid,
            "fixed_target_grid": {
                str(horizon): _target_grid(paths, horizon, FIXED_TARGETS_PCT, atr_targets=False)
                for horizon in range(1, max_horizon + 1)
            },
            "atr_target_grid": {
                str(horizon): _target_grid(paths, horizon, ATR_TARGETS, atr_targets=True)
                for horizon in range(1, max_horizon + 1)
            },
        }
        controls[name] = {
            str(horizon): _matched_control(paths, all_paths, horizon, random_runs)
            for horizon in range(1, max_horizon + 1)
        }
    return {
        "status": "exploratory",
        "production_change": False,
        "locked_oos": "not_opened",
        "protocol": {
            "selection": "prior-date expanding q90 RVOL",
            "bars": "local data/price_cache daily OHLCV",
            "entry": "cached scan-date close",
            "cost": f"diagnostic {DEFAULT_COST_PCT}% per round trip; observed spread/slippage unavailable",
            "stop": "long-side first low touch; fill=min(next open, stop), conservative gap handling",
            "target": "first-touch target/stop/time exit; same-bar stop wins; target fill=max(next open, target)",
            "fixed_targets_pct": list(FIXED_TARGETS_PCT),
            "atr_targets": list(ATR_TARGETS),
            "atr_stops": list(ATR_STOPS),
        },
        "coverage": {
            "selected_rows": len(selected),
            "paths_with_full_horizon": len(selected_paths),
            "control_universe_paths": len(all_paths),
        },
        "cohort_summary": summaries,
        "same_date_random_control": controls,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument("--cache", type=Path, default=Path("data/price_cache"))
    parser.add_argument("--min-history-dates", type=int, default=10)
    parser.add_argument("--max-horizon", type=int, default=10)
    parser.add_argument("--random-runs", type=int, default=100)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/backtest_out/high_rvol_raw_ohlc_exit_battery_2026-08-12.json"),
    )
    args = parser.parse_args()
    result = run(args.csv, args.cache, args.min_history_dates, args.max_horizon, args.random_runs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result["coverage"], indent=2))
    print(json.dumps(result["cohort_summary"], indent=2, default=str))


if __name__ == "__main__":
    main()
