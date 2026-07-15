#!/usr/bin/env python3
"""Compare V2 exits on the exact same point-in-time selected rows."""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter
from datetime import UTC, datetime

from p0_execution_replay import (
    DISCOVERY_END,
    VALIDATION_END,
    execution_result,
    load_v2,
    percentile_cut,
)
from score_formula_comparison import add_scores, canonical

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(ROOT, "data", "backtest_out", "enriched_signals_v3.csv")
DEFAULT_CACHE = os.path.join(ROOT, "data", "price_cache")
DEFAULT_OUT = os.path.join(ROOT, "data", "backtest_out", "v2_exit_same_selection")


def period(date: str) -> str:
    if date <= DISCOVERY_END:
        return "discovery"
    if date <= VALIDATION_END:
        return "validation"
    return "locked_oos"


def summarize(trades: list[dict], rejected: Counter, selected_n: int) -> dict:
    returns = [trade["net_return_pct"] for trade in trades]
    wins = [value for value in returns if value > 0]
    losses = [-value for value in returns if value < 0]
    return {
        "selected_n": selected_n,
        "execution_n": len(trades),
        "tp_rate": round(sum(t["barrier"] == "tp" for t in trades) / len(trades), 4)
        if trades
        else 0.0,
        "sl_rate": round(sum(t["barrier"] == "sl" for t in trades) / len(trades), 4)
        if trades
        else 0.0,
        "time_rate": round(sum(t["barrier"] == "time" for t in trades) / len(trades), 4)
        if trades
        else 0.0,
        "win_rate": round(sum(value > 0 for value in returns) / len(returns), 4)
        if returns
        else 0.0,
        "net_expectancy_pct": round(sum(returns) / len(returns), 4) if returns else 0.0,
        "net_total_pnl": round(sum(t["pnl"] for t in trades), 4),
        "profit_factor": round(sum(wins) / sum(losses), 4) if losses else None,
        "rejected": sum(rejected.values()),
        "reject_reasons": dict(rejected),
    }


def run_exit(
    rows: list[dict], cache_dir: str, args, tp_atr: float, sl_atr: float
) -> tuple[dict, list[dict]]:
    by_period: dict[str, list[dict]] = {"discovery": [], "validation": [], "locked_oos": []}
    for row in rows:
        by_period[period(row["date"])].append(row)
    summaries = {}
    all_trades = []
    for name, period_rows in by_period.items():
        trades = []
        rejected = Counter()
        for row in period_rows:
            execution, reason = execution_result(
                row,
                cache_dir,
                args.horizon,
                tp_atr,
                sl_atr,
                args.slippage_bps,
                args.commission_bps,
                args.notional,
                args.max_entry_drift,
            )
            if reason:
                rejected[reason] += 1
            elif execution:
                execution["period"] = name
                execution["tp_atr"] = tp_atr
                execution["sl_atr"] = sl_atr
                trades.append(execution)
        summaries[name] = summarize(trades, rejected, len(period_rows))
        all_trades.extend(trades)
    return summaries, all_trades


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--cache", default=DEFAULT_CACHE)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    parser.add_argument("--commission-bps", type=float, default=5.0)
    parser.add_argument("--notional", type=float, default=1000.0)
    parser.add_argument("--max-entry-drift", type=float, default=0.50)
    args = parser.parse_args()

    rows = add_scores(canonical(load_v2(args.csv)))
    discovery = [row for row in rows if row["date"] <= DISCOVERY_END]
    cut = percentile_cut(discovery, "v2_confirmation", 0.10)
    selected = [
        row
        for row in rows
        if cut is not None
        and row.get("v2_confirmation") is not None
        and row["v2_confirmation"] >= cut
    ]
    profiles = {"tp5_sl1": (5.0, 1.0), "tp5_sl1_5": (5.0, 1.5)}
    results = {}
    trade_sets = {}
    for name, (tp_atr, sl_atr) in profiles.items():
        results[name], trade_sets[name] = run_exit(selected, args.cache, args, tp_atr, sl_atr)

    paired = []
    by_key = {
        name: {(trade["symbol"], trade["date"]): trade for trade in trades}
        for name, trades in trade_sets.items()
    }
    common_keys = sorted(set(by_key["tp5_sl1"]) & set(by_key["tp5_sl1_5"]))
    for key in common_keys:
        first = by_key["tp5_sl1"][key]
        second = by_key["tp5_sl1_5"][key]
        paired.append(
            {
                "symbol": key[0],
                "date": key[1],
                "period": first["period"],
                "barrier_tp5_sl1": first["barrier"],
                "barrier_tp5_sl1_5": second["barrier"],
                "net_return_tp5_sl1": first["net_return_pct"],
                "net_return_tp5_sl1_5": second["net_return_pct"],
                "delta_1_vs_1_5_pct": round(first["net_return_pct"] - second["net_return_pct"], 4),
                "pnl_delta": round(first["pnl"] - second["pnl"], 4),
            }
        )

    output = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "methodology": {
            "research_only": True,
            "selection": "one fixed V2 confirmation top-10 discovery cut; identical selected rows for both exits",
            "selection_cut": cut,
            "selected_n": len(selected),
            "split": {
                "discovery_end": DISCOVERY_END,
                "validation_end": VALIDATION_END,
                "locked_oos_start_exclusive": VALIDATION_END,
            },
            "execution": {
                "horizon": args.horizon,
                "tp_atr_fixed": 5.0,
                "sl_profiles": [1.0, 1.5],
                "slippage_bps_each_side": args.slippage_bps,
                "commission_bps_each_side": args.commission_bps,
                "notional": args.notional,
                "max_entry_drift": args.max_entry_drift,
            },
            "universe": "V2 canonical source artifact",
        },
        "results": results,
        "paired_comparison": {
            "common_executed_n": len(paired),
            "same_outcome_n": sum(
                row["barrier_tp5_sl1"] == row["barrier_tp5_sl1_5"] for row in paired
            ),
            "tp5_sl1_better_n": sum(row["delta_1_vs_1_5_pct"] > 0 for row in paired),
            "tp5_sl1_5_better_n": sum(row["delta_1_vs_1_5_pct"] < 0 for row in paired),
            "mean_delta_pct": round(
                sum(row["delta_1_vs_1_5_pct"] for row in paired) / len(paired), 4
            )
            if paired
            else 0.0,
            "total_pnl_delta": round(sum(row["pnl_delta"] for row in paired), 4),
        },
    }
    os.makedirs(args.out, exist_ok=True)
    with open(
        os.path.join(args.out, "v2_exit_same_selection_results.json"), "w", encoding="utf-8"
    ) as handle:
        json.dump(output, handle, indent=2)
    with open(
        os.path.join(args.out, "paired_exit_comparison.csv"), "w", encoding="utf-8", newline=""
    ) as handle:
        fields = list(paired[0]) if paired else ["symbol", "date", "period"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(paired)
    print(f"OK -> {args.out}\\v2_exit_same_selection_results.json")
    print("selected_n", len(selected), "cut", cut)
    for name, data in results.items():
        print(name, data)
    print("paired", output["paired_comparison"])


if __name__ == "__main__":
    main()
