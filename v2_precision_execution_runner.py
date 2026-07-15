#!/usr/bin/env python3
"""Point-in-time Alpha V2 precision and execution research battery."""

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
DEFAULT_OUT = os.path.join(ROOT, "data", "backtest_out", "v2_precision_execution")


def parse_rows(path: str) -> list[dict]:
    return add_scores(canonical(load_v2(path)))


def add_history(rows: list[dict]) -> None:
    counts: Counter[str] = Counter()
    for row in sorted(rows, key=lambda item: (item["date"], item["timestamp"], item["id"])):
        row["prior_symbol_signals"] = counts[row["symbol"]]
        counts[row["symbol"]] += 1


def v2_top10_cut(rows: list[dict]) -> float | None:
    return percentile_cut(
        [row for row in rows if row["date"] <= DISCOVERY_END], "v2_confirmation", 0.10
    )


def regime_active(row: dict) -> bool:
    value = str(row.get("regime_raw") or "").strip().lower()
    return value in {"true", "1", "bull", "trend"}


def candidates(cut: float | None) -> dict[str, object]:
    def top10(row: dict) -> bool:
        return (
            cut is not None
            and row.get("v2_confirmation") is not None
            and row["v2_confirmation"] >= cut
        )

    def value(row: dict, field: str, threshold: float) -> bool:
        return row.get(field) is not None and row[field] >= threshold

    def not_extended(row: dict) -> bool:
        return row.get("dist52") is None or row["dist52"] < 0.90

    return {
        "score_top10": top10,
        "score_top10_rvol2": lambda row: top10(row) and value(row, "rvol", 2.0),
        "score_top10_atr4_rvol2": lambda row: top10(row)
        and value(row, "atr", 4.0)
        and value(row, "rvol", 2.0),
        "score_top10_gap3_rvol2": lambda row: top10(row)
        and value(row, "gap", 3.0)
        and value(row, "rvol", 2.0),
        "score_top10_not_extended": lambda row: top10(row) and not_extended(row),
        "score_top10_continuation": lambda row: top10(row)
        and value(row, "gap", 3.0)
        and value(row, "rvol", 2.0)
        and not_extended(row),
        "score_top10_regime": lambda row: top10(row) and regime_active(row),
        "score_top10_continuation_regime": lambda row: top10(row)
        and value(row, "gap", 3.0)
        and value(row, "rvol", 2.0)
        and not_extended(row)
        and regime_active(row),
        "score_top10_first_signal": lambda row: top10(row)
        and row.get("prior_symbol_signals", 0) == 0,
        "score_top10_continuation_first": lambda row: top10(row)
        and value(row, "gap", 3.0)
        and value(row, "rvol", 2.0)
        and not_extended(row)
        and row.get("prior_symbol_signals", 0) == 0,
    }


def split_name(date: str) -> str:
    if date <= DISCOVERY_END:
        return "discovery"
    if date <= VALIDATION_END:
        return "validation"
    return "locked_oos"


def summarize(rows: list[dict], predicate, cache_dir: str, args) -> dict:
    selected = [row for row in rows if predicate(row)]
    split: dict[str, list[dict]] = {"discovery": [], "validation": [], "locked_oos": []}
    for row in selected:
        split[split_name(row["date"])].append(row)
    result = {
        "selected_symbol_days": len(selected),
        "selected_dates": len({row["date"] for row in selected}),
        "periods": {},
    }
    for name, period_rows in split.items():
        trades = []
        rejected = Counter()
        for row in period_rows:
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
        result["periods"][name] = {
            "selected_n": len(period_rows),
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
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--cache", default=DEFAULT_CACHE)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--tp-atr", type=float, default=5.0)
    parser.add_argument("--sl-atr", type=float, default=1.5)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    parser.add_argument("--commission-bps", type=float, default=5.0)
    parser.add_argument("--notional", type=float, default=1000.0)
    parser.add_argument("--max-entry-drift", type=float, default=0.50)
    args = parser.parse_args()
    rows = parse_rows(args.csv)
    add_history(rows)
    cut = v2_top10_cut(rows)
    result = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "methodology": {
            "research_only": True,
            "universe": "V2 canonical source artifact",
            "point_in_time": "score cut learned only from discovery; persistence uses prior rows only",
            "split": {
                "discovery_end": DISCOVERY_END,
                "validation_end": VALIDATION_END,
                "locked_oos_start_exclusive": VALIDATION_END,
            },
            "target": "net execution P&L after triple barrier, slippage and commission",
            "exit": {
                "horizon": args.horizon,
                "tp_atr": args.tp_atr,
                "sl_atr": args.sl_atr,
                "slippage_bps_each_side": args.slippage_bps,
                "commission_bps_each_side": args.commission_bps,
            },
        },
        "coverage": {
            "canonical_rows": len(rows),
            "symbols": len({row["symbol"] for row in rows}),
            "dates": len({row["date"] for row in rows}),
            "score_top10_cut": cut,
            "missing": {
                field: sum(row.get(field) is None for row in rows)
                for field in ("short", "atr", "gap", "rvol", "dist52")
            },
        },
        "candidates": {},
    }
    for name, predicate in candidates(cut).items():
        result["candidates"][name] = summarize(rows, predicate, args.cache, args)
    os.makedirs(args.out, exist_ok=True)
    with open(
        os.path.join(args.out, "v2_precision_execution_results.json"), "w", encoding="utf-8"
    ) as handle:
        json.dump(result, handle, indent=2)
    fields = [
        "candidate",
        "period",
        "selected_n",
        "execution_n",
        "tp_rate",
        "sl_rate",
        "time_rate",
        "win_rate",
        "net_expectancy_pct",
        "net_total_pnl",
        "profit_factor",
        "rejected",
        "reject_reasons",
    ]
    with open(
        os.path.join(args.out, "candidate_summary.csv"), "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for candidate, data in result["candidates"].items():
            for period, metrics in data["periods"].items():
                writer.writerow({"candidate": candidate, "period": period, **metrics})
    print(f"OK -> {args.out}\\v2_precision_execution_results.json")
    for name, data in result["candidates"].items():
        print(name, data["periods"]["locked_oos"])


if __name__ == "__main__":
    main()
