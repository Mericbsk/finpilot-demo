#!/usr/bin/env python3
"""P0 point-in-time replay and execution-P&L comparison for legacy vs V2."""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter
from datetime import UTC, datetime

from scanner.labeling import triple_barrier_label
from score_formula_comparison import (
    add_scores,
    canonical,
    load_legacy,
    load_v2,
)

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CACHE = os.path.join(ROOT, "data", "price_cache")
DEFAULT_OUT = os.path.join(ROOT, "data", "backtest_out", "p0_execution_replay")
DISCOVERY_END = "2026-04-17"
VALIDATION_END = "2026-05-21"


def load_bars(cache_dir: str, symbol: str) -> list[dict]:
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


def forward_path(bars: list[dict], scan_date: str, horizon: int) -> list[dict]:
    index = next((i for i, bar in enumerate(bars) if bar["date"] >= scan_date), None)
    return [] if index is None else bars[index + 1 : index + 1 + horizon]


def percentile_cut(rows: list[dict], field: str, fraction: float) -> float | None:
    values = sorted(row[field] for row in rows if row.get(field) is not None)
    if not values:
        return None
    index = min(len(values) - 1, max(0, int(len(values) * (1.0 - fraction))))
    return values[index]


def reject_reasons(row: dict, formula: str, cut: float | None) -> list[str]:
    reasons: list[str] = []
    required = ("atr", "gap", "rvol")
    if formula.startswith("v2_"):
        required = ("short", "atr", "gap", "rvol")
    for field in required:
        if row.get(field) is None:
            reasons.append(f"missing_{field}")
    if row.get("price") is None or row["price"] <= 0:
        reasons.append("invalid_entry_price")
    if row.get("date", "") <= DISCOVERY_END:
        reasons.append("discovery_or_training_period")
    elif row.get("date", "") <= VALIDATION_END:
        reasons.append("validation_period")
    if cut is None or row.get(formula) is None:
        reasons.append("score_unavailable")
    elif row[formula] < cut:
        reasons.append("score_threshold")
    return reasons


def execution_result(
    row: dict,
    cache_dir: str,
    horizon: int,
    tp_mult: float,
    sl_mult: float,
    slippage_bps: float,
    commission_bps: float,
    notional: float,
    max_entry_drift: float,
) -> tuple[dict | None, str | None]:
    bars = load_bars(cache_dir, row["symbol"])
    if not bars:
        return None, "missing_price_cache"
    path = forward_path(bars, row["date"], horizon)
    if len(path) < horizon:
        return None, "insufficient_forward_bars"
    scan_bar = next((bar for bar in bars if bar["date"] >= row["date"]), None)
    reference_close = float(scan_bar["close"]) if scan_bar else None
    drift = abs(row["price"] / reference_close - 1.0) if reference_close else None
    if drift is not None and drift > max_entry_drift:
        return None, "entry_drift_limit"

    raw = triple_barrier_label(
        [float(bar["close"]) for bar in path],
        entry_price=float(row["price"]),
        tp_pct=max(float(row["atr"]) / 100.0 * tp_mult, 0.0001),
        sl_pct=max(float(row["atr"]) / 100.0 * sl_mult, 0.0001),
        max_horizon=horizon,
        forward_highs=[float(bar["high"]) for bar in path],
        forward_lows=[float(bar["low"]) for bar in path],
    )
    entry_factor = 1.0 + (slippage_bps + commission_bps) / 10_000.0
    exit_factor = 1.0 - (slippage_bps + commission_bps) / 10_000.0
    adjusted_entry = raw.entry_price * entry_factor
    adjusted_exit = raw.exit_price * exit_factor
    qty = notional / adjusted_entry
    pnl = (adjusted_exit - adjusted_entry) * qty
    net_return_pct = pnl / notional * 100.0
    return {
        "symbol": row["symbol"],
        "date": row["date"],
        "entry_price": round(adjusted_entry, 6),
        "exit_price": round(adjusted_exit, 6),
        "barrier": raw.label,
        "bars_to_exit": raw.bars_to_hit,
        "gross_return_pct": round(raw.ret_pct * 100.0, 4),
        "net_return_pct": round(net_return_pct, 4),
        "pnl": round(pnl, 4),
        "mfe_pct": round(raw.mfe_pct * 100.0, 4),
        "mae_pct": round(raw.mae_pct * 100.0, 4),
        "entry_drift_pct": round((drift or 0.0) * 100.0, 4),
    }, None


def summarize(trades: list[dict], rejected: Counter) -> dict:
    returns = [trade["net_return_pct"] for trade in trades]
    wins = [value for value in returns if value > 0]
    losses = [-value for value in returns if value < 0]
    return {
        "n": len(trades),
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
        "max_drawdown_pct": round(max_drawdown(returns), 4),
        "rejected": sum(rejected.values()),
        "reject_reason_counts": dict(rejected),
    }


def max_drawdown(returns: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for value in returns:
        equity += value
        peak = max(peak, equity)
        drawdown = min(drawdown, equity - peak)
    return drawdown


def run_source(
    rows: list[dict],
    source: str,
    formula: str,
    cache_dir: str,
    horizon: int,
    tp_mult: float,
    sl_mult: float,
    slippage_bps: float,
    commission_bps: float,
    notional: float,
    max_entry_drift: float,
) -> dict:
    rows = add_scores(canonical(rows))
    discovery = [row for row in rows if row["date"] <= DISCOVERY_END]
    cut = percentile_cut(discovery, formula, 0.10)
    trades: list[dict] = []
    rejected = Counter()
    replay_rows = []
    for row in rows:
        reasons = reject_reasons(row, formula, cut)
        if not reasons:
            execution, reason = execution_result(
                row,
                cache_dir,
                horizon,
                tp_mult,
                sl_mult,
                slippage_bps,
                commission_bps,
                notional,
                max_entry_drift,
            )
            if reason:
                reasons.append(reason)
            elif execution:
                trades.append(
                    {"source": source, "formula": formula, "score": row[formula], **execution}
                )
        for reason in reasons:
            rejected[reason] += 1
        replay_rows.append(
            {
                "source": source,
                "formula": formula,
                "symbol": row["symbol"],
                "date": row["date"],
                "score": row.get(formula),
                "selected": not reasons,
                "reject_reason": json.dumps(reasons),
            }
        )
    return {
        "source": source,
        "formula": formula,
        "discovery_score_cut_top10": cut,
        "split": {
            "discovery_end": DISCOVERY_END,
            "validation_end": VALIDATION_END,
            "locked_oos_start_exclusive": VALIDATION_END,
        },
        "execution": {
            "horizon": horizon,
            "tp_atr": tp_mult,
            "sl_atr": sl_mult,
            "slippage_bps_each_side": slippage_bps,
            "commission_bps_each_side": commission_bps,
            "notional": notional,
            "max_entry_drift": max_entry_drift,
        },
        "coverage": {
            "replayed_symbol_days": len(replay_rows),
            "replayed_dates": len({row["date"] for row in replay_rows}),
            "selected_trades": sum(row["selected"] for row in replay_rows),
            "selected_dates": len({row["date"] for row in replay_rows if row["selected"]}),
            "discovery_symbol_days": sum(row["date"] <= DISCOVERY_END for row in replay_rows),
            "validation_symbol_days": sum(
                DISCOVERY_END < row["date"] <= VALIDATION_END for row in replay_rows
            ),
            "locked_oos_symbol_days": sum(row["date"] > VALIDATION_END for row in replay_rows),
        },
        "summary": summarize(trades, rejected),
        "trades": trades,
        "replay": replay_rows,
    }


def common_symbol_days(
    legacy_rows: list[dict], v2_rows: list[dict]
) -> tuple[list[dict], list[dict], dict]:
    """Restrict both artifacts to the same canonical symbol-day keys."""
    legacy = canonical(legacy_rows)
    v2 = canonical(v2_rows)
    common = {(row["symbol"], row["date"]) for row in legacy} & {
        (row["symbol"], row["date"]) for row in v2
    }
    return (
        [row for row in legacy if (row["symbol"], row["date"]) in common],
        [row for row in v2 if (row["symbol"], row["date"]) in common],
        {
            "legacy_canonical_rows": len(legacy),
            "v2_canonical_rows": len(v2),
            "common_symbol_day_rows": len(common),
            "common_symbols": len({key[0] for key in common}),
            "common_dates": len({key[1] for key in common}),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--legacy-csv",
        default=os.path.join(ROOT, "data", "backtest_out", "full_universe_enriched.csv"),
    )
    parser.add_argument(
        "--v2-csv", default=os.path.join(ROOT, "data", "backtest_out", "enriched_signals_v3.csv")
    )
    parser.add_argument("--cache", default=DEFAULT_CACHE)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--universe", choices=("common", "all"), default="common")
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--legacy-tp-atr", type=float, default=2.0)
    parser.add_argument("--legacy-sl-atr", type=float, default=1.0)
    parser.add_argument("--v2-tp-atr", type=float, default=5.0)
    parser.add_argument("--v2-sl-atr", type=float, default=1.5)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    parser.add_argument("--commission-bps", type=float, default=5.0)
    parser.add_argument("--notional", type=float, default=1000.0)
    parser.add_argument("--max-entry-drift", type=float, default=0.50)
    args = parser.parse_args()

    legacy_input = load_legacy(args.legacy_csv)
    v2_input = load_v2(args.v2_csv)
    if args.universe == "common":
        legacy_rows, v2_rows, universe = common_symbol_days(legacy_input, v2_input)
    else:
        legacy_rows = canonical(legacy_input)
        v2_rows = canonical(v2_input)
        universe = {
            "mode": "all",
            "legacy_canonical_rows": len(legacy_rows),
            "v2_canonical_rows": len(v2_rows),
            "common_symbol_day_rows": len(
                {(row["symbol"], row["date"]) for row in legacy_rows}
                & {(row["symbol"], row["date"]) for row in v2_rows}
            ),
            "common_symbols": None,
            "common_dates": None,
        }
    configurations = [
        ("legacy", legacy_rows, "legacy_quality", args.legacy_tp_atr, args.legacy_sl_atr),
        ("v2", v2_rows, "v2_confirmation", args.v2_tp_atr, args.v2_sl_atr),
    ]
    results = []
    for source, rows, formula, tp_mult, sl_mult in configurations:
        results.append(
            run_source(
                rows,
                source,
                formula,
                args.cache,
                args.horizon,
                tp_mult,
                sl_mult,
                args.slippage_bps,
                args.commission_bps,
                args.notional,
                args.max_entry_drift,
            )
        )
    output = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "methodology": {
            "research_only": True,
            "point_in_time": True,
            "selection": "top10 cut learned only from discovery",
            "target": "execution P&L after TP/SL, slippage and commission",
            "universe_alignment": "same canonical (symbol, date) intersection for legacy and V2"
            if args.universe == "common"
            else "all canonical (symbol, date) rows per source; source universes are not identical",
            "universe_mode": args.universe,
            "common_universe": universe,
            "exit_profiles": {
                "legacy": {"tp_atr": args.legacy_tp_atr, "sl_atr": args.legacy_sl_atr},
                "v2": {"tp_atr": args.v2_tp_atr, "sl_atr": args.v2_sl_atr},
            },
        },
        "results": results,
    }
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "p0_execution_results.json"), "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)
    fields = [
        "source",
        "formula",
        "symbol",
        "date",
        "score",
        "entry_price",
        "exit_price",
        "barrier",
        "bars_to_exit",
        "gross_return_pct",
        "net_return_pct",
        "pnl",
        "mfe_pct",
        "mae_pct",
        "entry_drift_pct",
    ]
    with open(
        os.path.join(args.out, "execution_trades.csv"), "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerows(result["trades"])
    with open(
        os.path.join(args.out, "point_in_time_replay.csv"), "w", encoding="utf-8", newline=""
    ) as handle:
        fields = ["source", "formula", "symbol", "date", "score", "selected", "reject_reason"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerows(result["replay"])
    print(f"OK -> {args.out}\\p0_execution_results.json")
    for result in results:
        print(result["source"], result["formula"], result["summary"])


if __name__ == "__main__":
    main()
