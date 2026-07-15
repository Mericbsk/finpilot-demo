#!/usr/bin/env python3
"""Rolling point-in-time execution test for the Alpha V2 candidate filters."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import UTC, datetime

from p0_execution_replay import execution_result, percentile_cut
from score_formula_comparison import add_scores, canonical, load_v2
from v2_precision_execution_runner import add_history, candidates

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(ROOT, "data", "backtest_out", "enriched_signals_v3.csv")
DEFAULT_CACHE = os.path.join(ROOT, "data", "price_cache")
DEFAULT_OUT = os.path.join(ROOT, "data", "backtest_out", "v2_walk_forward")


def evaluate(rows: list[dict], predicate, cache_dir: str, args) -> dict:
    selected = [row for row in rows if predicate(row)]
    trades = []
    rejected = Counter()
    for row in selected:
        execution, reason = execution_result(
            row,
            cache_dir,
            args.horizon,
            args.tp_atr,
            args.sl_atr,
            args.slippage_bps,
            args.commission_bps,
            args.notional,
            args.max_entry_drift,
        )
        if reason:
            rejected[reason] += 1
        elif execution:
            trades.append(execution)
    returns = [trade["net_return_pct"] for trade in trades]
    wins = [value for value in returns if value > 0]
    losses = [-value for value in returns if value < 0]
    return {
        "selected_n": len(selected),
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
        "net_total_pnl": round(sum(trade["pnl"] for trade in trades), 4),
        "profit_factor": round(sum(wins) / sum(losses), 4) if losses else None,
        "rejected": sum(rejected.values()),
        "reject_reasons": dict(rejected),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--cache", default=DEFAULT_CACHE)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--train-days", type=int, default=20)
    parser.add_argument("--validation-days", type=int, default=8)
    parser.add_argument("--test-days", type=int, default=8)
    parser.add_argument("--step-days", type=int, default=8)
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--tp-atr", type=float, default=5.0)
    parser.add_argument("--sl-atr", type=float, default=1.5)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    parser.add_argument("--commission-bps", type=float, default=5.0)
    parser.add_argument("--notional", type=float, default=1000.0)
    parser.add_argument("--max-entry-drift", type=float, default=0.50)
    args = parser.parse_args()

    rows = add_scores(canonical(load_v2(args.csv)))
    add_history(rows)
    dates = sorted({row["date"] for row in rows})
    output = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "methodology": {
            "research_only": True,
            "window_units": "ordered signal dates, not calendar months",
            "train_days": args.train_days,
            "validation_days": args.validation_days,
            "test_days": args.test_days,
            "step_days": args.step_days,
            "exit": {
                "horizon": args.horizon,
                "tp_atr": args.tp_atr,
                "sl_atr": args.sl_atr,
                "slippage_bps_each_side": args.slippage_bps,
                "commission_bps_each_side": args.commission_bps,
            },
            "selection": "V2 confirmation top-10 cut learned independently inside each discovery window",
        },
        "coverage": {
            "canonical_rows": len(rows),
            "dates": len(dates),
            "symbols": len({row["symbol"] for row in rows}),
        },
        "windows": [],
    }
    for start in range(
        0, len(dates) - args.train_days - args.validation_days - args.test_days + 1, args.step_days
    ):
        train_dates = dates[start : start + args.train_days]
        validation_dates = dates[
            start + args.train_days : start + args.train_days + args.validation_days
        ]
        test_dates = dates[
            start + args.train_days + args.validation_days : start
            + args.train_days
            + args.validation_days
            + args.test_days
        ]
        train = [row for row in rows if row["date"] in train_dates]
        validation = [row for row in rows if row["date"] in validation_dates]
        test = [row for row in rows if row["date"] in test_dates]
        cut = percentile_cut(train, "v2_confirmation", 0.10)
        window = {
            "window": len(output["windows"]) + 1,
            "train_start": train_dates[0],
            "train_end": train_dates[-1],
            "validation_start": validation_dates[0],
            "validation_end": validation_dates[-1],
            "test_start": test_dates[0],
            "test_end": test_dates[-1],
            "train_n": len(train),
            "validation_n": len(validation),
            "test_n": len(test),
            "score_cut": cut,
            "candidates": {},
        }
        for name, predicate in candidates(cut).items():
            window["candidates"][name] = {
                "validation": evaluate(validation, predicate, args.cache, args),
                "locked_test": evaluate(test, predicate, args.cache, args),
            }
        output["windows"].append(window)

    os.makedirs(args.out, exist_ok=True)
    with open(
        os.path.join(args.out, "v2_walk_forward_results.json"), "w", encoding="utf-8"
    ) as handle:
        json.dump(output, handle, indent=2)
    print(f"OK -> {args.out}\\v2_walk_forward_results.json")
    for name in candidates(None):
        tests = [window["candidates"][name]["locked_test"] for window in output["windows"]]
        valid = [window["candidates"][name]["validation"] for window in output["windows"]]
        print(
            name,
            "test_expectancy",
            [item["net_expectancy_pct"] for item in tests],
            "test_n",
            [item["execution_n"] for item in tests],
            "validation_expectancy",
            [item["net_expectancy_pct"] for item in valid],
        )


if __name__ == "__main__":
    main()
