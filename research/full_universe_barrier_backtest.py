#!/usr/bin/env python3
"""Execution-style full-universe barrier backtest.

Uses the already-enriched scanner rows and cached daily OHLC bars to measure
path-dependent outcomes: take-profit first, stop-loss first, or time exit.
This is research output only; it does not change live scanner behavior.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import defaultdict
from datetime import UTC, datetime

from scanner.labeling import triple_barrier_label

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(ROOT, "data", "backtest_out", "full_universe_enriched.csv")
DEFAULT_CACHE = os.path.join(ROOT, "data", "price_cache")
DEFAULT_OUT = os.path.join(ROOT, "data", "backtest_out")
MIN_N = 50


def _f(value):
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def _b(value):
    return str(value).strip().lower() in {"true", "1", "yes"}


def load_rows(path):
    rows = []
    with open(path, encoding="utf-8", newline="") as handle:
        for index, data in enumerate(csv.DictReader(handle)):
            entry = _f(data.get("price"))
            atr = _f(data.get("atr_pct_real"))
            if not entry or entry <= 0 or not atr or atr <= 0:
                continue
            rows.append(
                {
                    "id": f"{data.get('symbol')}_{data.get('scan_ts')}_{index}",
                    "symbol": (data.get("symbol") or "").strip(),
                    "scan_date": (data.get("scan_date") or "").strip(),
                    "entry": entry,
                    "atr_pct": atr,
                    "entry_ok": _b(data.get("entry_ok")),
                    "direction": _b(data.get("direction")),
                    "gap": _f(data.get("gap_pct")),
                    "rvol": _f(data.get("rvol")),
                    "squeeze": _f(data.get("squeeze_factor")),
                    "composite": _f(data.get("composite_score")),
                    "dist52": _f(data.get("dist_52w_high")),
                    "regime": (data.get("regime") or "").strip(),
                }
            )
    return rows


def load_bars(cache_dir, symbol):
    path = os.path.join(cache_dir, f"{symbol}.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as handle:
            bars = json.load(handle)
    except (OSError, ValueError, TypeError):
        return []
    return sorted(
        [
            bar
            for bar in bars
            if bar.get("date") and bar.get("high") and bar.get("low") and bar.get("close")
        ],
        key=lambda bar: bar["date"],
    )


def forward_path(bars, scan_date, horizon):
    dates = {bar["date"]: index for index, bar in enumerate(bars)}
    index = dates.get(scan_date)
    if index is None:
        index = next((i for i, bar in enumerate(bars) if bar["date"] >= scan_date), None)
    if index is None:
        return []
    return bars[index + 1 : index + 1 + horizon]


def predicates():
    return {
        "all": lambda row: True,
        "entry_ok": lambda row: row["entry_ok"],
        "ATR>=4": lambda row: row["atr_pct"] >= 4,
        "ATR>=6": lambda row: row["atr_pct"] >= 6,
        "gap>3": lambda row: row["gap"] is not None and row["gap"] > 3,
        "RVOL>=2": lambda row: row["rvol"] is not None and row["rvol"] >= 2,
        "composite>=34": lambda row: row["composite"] is not None and row["composite"] >= 34,
        "composite>=47": lambda row: row["composite"] is not None and row["composite"] >= 47,
        "composite>=40": lambda row: row["composite"] is not None and row["composite"] >= 40,
        "composite>=52": lambda row: row["composite"] is not None and row["composite"] >= 52,
        "squeeze>=0.5": lambda row: row["squeeze"] is not None and row["squeeze"] >= 0.5,
        "ATR6+confirmation": lambda row: row["atr_pct"] >= 6
        and (
            (row["gap"] is not None and row["gap"] > 3)
            or (row["rvol"] is not None and row["rvol"] >= 2)
            or (row["squeeze"] is not None and row["squeeze"] >= 0.5)
        ),
        "ATR6+entry_ok": lambda row: row["atr_pct"] >= 6 and row["entry_ok"],
        "ATR6+RVOL2": lambda row: row["atr_pct"] >= 6
        and row["rvol"] is not None
        and row["rvol"] >= 2,
        "ATR6+RVOL2+composite70": lambda row: row["atr_pct"] >= 6
        and row["rvol"] is not None
        and row["rvol"] >= 2
        and row["composite"] is not None
        and row["composite"] >= 70,
        "ATR6+RVOL2+gap3": lambda row: row["atr_pct"] >= 6
        and row["rvol"] is not None
        and row["rvol"] >= 2
        and row["gap"] is not None
        and row["gap"] > 3,
        "ATR6+RVOL2+direction": lambda row: row["atr_pct"] >= 6
        and row["rvol"] is not None
        and row["rvol"] >= 2
        and row["direction"],
        "ATR6+RVOL2+gap3+direction": lambda row: row["atr_pct"] >= 6
        and row["rvol"] is not None
        and row["rvol"] >= 2
        and row["gap"] is not None
        and row["gap"] > 3
        and row["direction"],
        "ATR6+RVOL2+gap3+not_near_52w_high": lambda row: row["atr_pct"] >= 6
        and row["rvol"] is not None
        and row["rvol"] >= 2
        and row["gap"] is not None
        and row["gap"] > 3
        and (row["dist52"] is None or row["dist52"] < 0.9),
        "ATR6+RVOL2+gap3+direction+composite58": lambda row: row["atr_pct"] >= 6
        and row["rvol"] is not None
        and row["rvol"] >= 2
        and row["gap"] is not None
        and row["gap"] > 3
        and row["direction"]
        and row["composite"] is not None
        and row["composite"] >= 58,
        "ATR6+RVOL2+gap3+direction+not_near_52w_high+composite58": lambda row: row["atr_pct"] >= 6
        and row["rvol"] is not None
        and row["rvol"] >= 2
        and row["gap"] is not None
        and row["gap"] > 3
        and row["direction"]
        and (row["dist52"] is None or row["dist52"] < 0.9)
        and row["composite"] is not None
        and row["composite"] >= 58,
    }


def resolve_paths(rows, cache_dir, horizon, max_entry_drift):
    bars_by_symbol = {}
    resolved = []
    missing = 0
    short = 0
    rejected_drift = 0
    max_observed_drift = 0.0
    for row in rows:
        if row["symbol"] not in bars_by_symbol:
            bars_by_symbol[row["symbol"]] = load_bars(cache_dir, row["symbol"])
        bars = bars_by_symbol[row["symbol"]]
        path = forward_path(bars, row["scan_date"], horizon)
        if not path:
            missing += 1
            continue
        scan_bar = next((bar for bar in bars if bar["date"] >= row["scan_date"]), None)
        reference_close = _f(scan_bar.get("close")) if scan_bar else None
        drift = abs(row["entry"] / reference_close - 1.0) if reference_close else None
        if drift is not None:
            max_observed_drift = max(max_observed_drift, drift)
            if drift > max_entry_drift:
                rejected_drift += 1
                continue
        if len(path) < horizon:
            short += 1
            continue
        enriched = dict(row)
        enriched["forward"] = path
        resolved.append(enriched)
    return resolved, {
        "missing_paths": missing,
        "short_paths": short,
        "rejected_entry_drift": rejected_drift,
        "max_observed_entry_drift": round(max_observed_drift, 4),
        "symbols_with_cache": len(bars_by_symbol),
    }


def label_rows(rows, tp_mult, sl_mult, horizon):
    output = []
    for row in rows:
        atr_fraction = row["atr_pct"] / 100.0
        label = triple_barrier_label(
            [bar["close"] for bar in row["forward"]],
            entry_price=row["entry"],
            tp_pct=max(tp_mult * atr_fraction, 0.01),
            sl_pct=max(sl_mult * atr_fraction, 0.005),
            max_horizon=horizon,
            forward_highs=[bar["high"] for bar in row["forward"]],
            forward_lows=[bar["low"] for bar in row["forward"]],
        )
        output.append((row, label))
    return output


def summarize(labeled, label, predicate):
    selected = [result for row, result in labeled if predicate(row)]
    if not selected:
        return {"label": label, "n": 0}
    tp = sum(item.label == "tp" for item in selected)
    sl = sum(item.label == "sl" for item in selected)
    tm = sum(item.label == "time" for item in selected)
    returns = [item.ret_pct * 100 for item in selected]
    mfe = [item.mfe_pct * 100 for item in selected]
    mae = [item.mae_pct * 100 for item in selected]
    wins = [value for value in returns if value > 0]
    losses = [value for value in returns if value < 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    return {
        "label": label,
        "n": len(selected),
        "tp_rate": round(tp / len(selected), 4),
        "sl_rate": round(sl / len(selected), 4),
        "time_rate": round(tm / len(selected), 4),
        "win_rate": round(sum(value > 0 for value in returns) / len(selected), 4),
        "expectancy_pct": round(sum(returns) / len(returns), 4),
        "median_return_pct": round(sorted(returns)[len(returns) // 2], 4),
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss else None,
        "avg_mfe_pct": round(sum(mfe) / len(mfe), 4),
        "avg_mae_pct": round(sum(mae) / len(mae), 4),
        "avg_bars": round(sum(item.bars_to_hit for item in selected) / len(selected), 3),
    }


def dedup_rows(rows):
    seen = {}
    for row in rows:
        seen.setdefault((row["symbol"], row["scan_date"]), row)
    return list(seen.values())


def period_summary(labeled, predicate):
    periods = defaultdict(list)
    for row, label in labeled:
        periods[row["scan_date"][:7]].append((row, label))
    output = []
    for month, values in sorted(periods.items()):
        if len(values) >= MIN_N:
            output.append(summarize(values, month, predicate))
    return output


def run_grid(rows, cache_dir, horizons, tp_mults, sl_mults, max_entry_drift):
    predicates_map = predicates()
    grid = []
    period = {}
    dedup = {}
    inventory = {}
    for horizon in horizons:
        resolved, stats = resolve_paths(rows, cache_dir, horizon, max_entry_drift)
        inventory[str(horizon)] = {"resolved": len(resolved), **stats}
        resolved_dedup, _ = resolve_paths(dedup_rows(rows), cache_dir, horizon, max_entry_drift)
        for tp_mult in tp_mults:
            for sl_mult in sl_mults:
                labeled = label_rows(resolved, tp_mult, sl_mult, horizon)
                labeled_dedup = label_rows(resolved_dedup, tp_mult, sl_mult, horizon)
                config = f"tp={tp_mult}xATR sl={sl_mult}xATR h={horizon}d"
                for name, predicate in predicates_map.items():
                    result = summarize(labeled, name, predicate)
                    result.update(
                        {
                            "config": config,
                            "tp_mult": tp_mult,
                            "sl_mult": sl_mult,
                            "horizon": horizon,
                        }
                    )
                    grid.append(result)
                    if name in {
                        "all",
                        "ATR>=4",
                        "ATR>=6",
                        "ATR6+confirmation",
                        "ATR6+entry_ok",
                        "ATR6+RVOL2",
                        "ATR6+RVOL2+gap3",
                        "ATR6+RVOL2+direction",
                        "ATR6+RVOL2+gap3+direction",
                        "ATR6+RVOL2+gap3+not_near_52w_high",
                        "ATR6+RVOL2+gap3+direction+composite58",
                        "ATR6+RVOL2+gap3+direction+not_near_52w_high+" "composite58",
                    }:
                        period[f"{config}|{name}"] = period_summary(labeled, predicate)
                        dedup[f"{config}|{name}"] = summarize(labeled_dedup, name, predicate)
    return grid, period, dedup, inventory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--cache", default=DEFAULT_CACHE)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--horizons", default="3,5")
    parser.add_argument("--tp", default="1.5,2,3")
    parser.add_argument("--sl", default="0.75,1,1.5")
    parser.add_argument(
        "--max-entry-drift",
        type=float,
        default=0.5,
        help="Ayni gun bar kapanisindan izin verilen mutlak entry sapmasi (0.5 = %%50).",
    )
    parser.add_argument(
        "--max-atr-pct",
        type=float,
        default=None,
        help="ATR yuzdesi bu degeri asan satirlari barrier analizinden cikarir.",
    )
    parser.add_argument("--start-date", default=None, help="Scan date lower bound, inclusive.")
    parser.add_argument("--end-date", default=None, help="Scan date upper bound, inclusive.")
    parser.add_argument(
        "--round-trip-cost-pct",
        type=float,
        default=0.55,
        help="Research cost in percentage points, subtracted from barrier expectancy.",
    )
    args = parser.parse_args()

    rows = load_rows(args.csv)
    original_rows = len(rows)
    if args.start_date is not None:
        rows = [row for row in rows if row["scan_date"] >= args.start_date]
    if args.end_date is not None:
        rows = [row for row in rows if row["scan_date"] <= args.end_date]
    if args.max_atr_pct is not None:
        rows = [
            row for row in rows if row["atr_pct"] is not None and row["atr_pct"] <= args.max_atr_pct
        ]
    horizons = [int(value) for value in args.horizons.split(",") if value.strip()]
    tp_mults = [float(value) for value in args.tp.split(",") if value.strip()]
    sl_mults = [float(value) for value in args.sl.split(",") if value.strip()]
    grid, periods, dedup, inventory = run_grid(
        rows, args.cache, horizons, tp_mults, sl_mults, args.max_entry_drift
    )
    viable = [item for item in grid if item["n"] >= MIN_N]
    ranked = sorted(
        viable,
        key=lambda item: (item.get("expectancy_pct", -999), item.get("profit_factor") or -999),
        reverse=True,
    )
    for item in grid:
        expectancy = item.get("expectancy_pct")
        item["round_trip_cost_pct"] = args.round_trip_cost_pct
        item["cost_adjusted_expectancy_pct"] = (
            round(expectancy - args.round_trip_cost_pct, 4) if expectancy is not None else None
        )
    output = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "methodology": {
            "input_rows": len(rows),
            "dedup_rows": len(dedup_rows(rows)),
            "barrier": "ATR-scaled TP/SL, stop-first same-bar tie, time exit at last close",
            "entry": "CSV scan-date price; forward path starts next available daily bar",
            "horizons": horizons,
            "tp_multipliers": tp_mults,
            "sl_multipliers": sl_mults,
            "max_entry_drift": args.max_entry_drift,
            "max_atr_pct": args.max_atr_pct,
            "atr_filtered_rows": original_rows - len(rows),
            "start_date": args.start_date,
            "end_date": args.end_date,
            "round_trip_cost_pct": args.round_trip_cost_pct,
        },
        "inventory": inventory,
        "top_configs": ranked[:50],
        "all_results": grid,
        "period_results": periods,
        "dedup_results": dedup,
    }
    os.makedirs(args.out, exist_ok=True)
    json_path = os.path.join(args.out, "full_universe_barrier_results.json")
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2, default=str)
    csv_path = os.path.join(args.out, "full_universe_barrier_grid.csv")
    fields = [
        "config",
        "label",
        "n",
        "tp_rate",
        "sl_rate",
        "time_rate",
        "win_rate",
        "expectancy_pct",
        "round_trip_cost_pct",
        "cost_adjusted_expectancy_pct",
        "median_return_pct",
        "profit_factor",
        "avg_mfe_pct",
        "avg_mae_pct",
        "avg_bars",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: item.get(field) for field in fields} for item in grid)

    print(f"OK -> {json_path}")
    print(f"OK -> {csv_path}")
    print(f"rows={len(rows)} dedup={len(dedup_rows(rows))} viable_results={len(viable)}")
    print("\n=== TOP BARRIER CONFIGURATIONS ===")
    for item in ranked[:20]:
        print(
            f"  {item['config']:25s} {item['label']:24s} n={item['n']:>6} tp={item['tp_rate'] * 100:>5.1f}% sl={item['sl_rate'] * 100:>5.1f}% exp={item['expectancy_pct']:>7.3f}% PF={item['profit_factor']}"
        )


if __name__ == "__main__":
    main()
