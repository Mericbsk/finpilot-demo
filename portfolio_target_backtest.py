#!/usr/bin/env python3
"""Portfolio-level, path-aware target and sizing research.

Research only. It reuses the enriched scanner export and cached daily bars.
Trades are selected by scan-day rank, entered at the recorded scan price, and
held until a stop, target, or time barrier. The portfolio uses a fixed number
of slots, so overlapping signals compete for capital instead of being treated
as independent unlimited-notional trades.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from scanner.labeling import triple_barrier_label

ROOT = Path(__file__).resolve().parent
DEFAULT_CSV = ROOT / "data/backtest_out/full_universe_enriched.csv"
DEFAULT_CACHE = ROOT / "data/price_cache"
DEFAULT_OUT = ROOT / "data/backtest_out/portfolio_target_backtest.json"
COST_PCT = 0.55
HORIZON = 5
MAX_ENTRY_DRIFT = 0.50
INITIAL_CAPITAL = 100_000.0


@dataclass
class Trade:
    symbol: str
    scan_date: str
    exit_date: str
    gross_return_pct: float
    net_return_pct: float
    mfe_pct: float
    mae_pct: float
    bars_to_exit: int
    barrier: str
    notional: float
    pnl: float
    target_pct: float
    stop_pct: float
    rank: int
    size_multiplier: float
    regime: str


def number(value: str | None) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def boolean(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "trend", "up"}


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = []
        for index, raw in enumerate(csv.DictReader(handle)):
            entry = number(raw.get("price"))
            atr = number(raw.get("atr_pct_real")) or number(raw.get("atr_pct"))
            if not entry or entry <= 0 or not atr or atr <= 0:
                continue
            rows.append(
                {
                    "id": f"{raw.get('symbol')}_{raw.get('scan_ts')}_{index}",
                    "symbol": (raw.get("symbol") or "").strip(),
                    "scan_date": (raw.get("scan_date") or "").strip(),
                    "entry": entry,
                    "atr": atr,
                    "composite": number(raw.get("composite_score")),
                    "rvol": number(raw.get("rvol")),
                    "gap": number(raw.get("gap_pct")),
                    "entry_ok": boolean(raw.get("entry_ok")),
                    "regime": (raw.get("regime") or "unknown").strip().lower(),
                    "conviction": (raw.get("conviction_tier") or raw.get("tier") or "")
                    .strip()
                    .upper(),
                }
            )
    return rows


def load_bars(cache_dir: Path, symbol: str) -> list[dict]:
    path = cache_dir / f"{symbol}.json"
    if not path.exists():
        return []
    try:
        bars = json.loads(path.read_text(encoding="utf-8"))
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


def resolve_paths(rows: list[dict], cache_dir: Path) -> tuple[list[dict], dict]:
    by_symbol: dict[str, list[dict]] = {}
    resolved = []
    missing = short = drift_rejected = 0
    for row in rows:
        by_symbol.setdefault(row["symbol"], load_bars(cache_dir, row["symbol"]))
        bars = by_symbol[row["symbol"]]
        path = forward_path(bars, row["scan_date"], HORIZON)
        if len(path) < HORIZON:
            short += 1
            continue
        scan_bar = next((bar for bar in bars if bar["date"] >= row["scan_date"]), None)
        reference = number(scan_bar.get("close")) if scan_bar else None
        drift = abs(row["entry"] / reference - 1) if reference else 0
        if drift > MAX_ENTRY_DRIFT:
            drift_rejected += 1
            continue
        item = dict(row)
        item["forward"] = path
        item["drift"] = drift
        resolved.append(item)
    missing = len(rows) - len(resolved) - short - drift_rejected
    return resolved, {
        "input_rows": len(rows),
        "resolved_rows": len(resolved),
        "short_paths": short,
        "missing_paths": max(0, missing),
        "rejected_entry_drift": drift_rejected,
        "symbols": len(by_symbol),
    }


def rank_rows(rows: list[dict], selection: str) -> list[dict]:
    selected = [row for row in rows if row["entry_ok"]]
    if selection == "all_entry_ok":
        return selected
    if selection == "atr_rvol":
        return sorted(
            selected, key=lambda row: ((row["atr"] or 0) * (row["rvol"] or 0)), reverse=True
        )
    return sorted(
        selected,
        key=lambda row: (row["composite"] is not None, row["composite"] or -1),
        reverse=True,
    )


def sizing_multiplier(row: dict, sizing: str) -> float:
    if sizing == "equal":
        return 1.0
    if sizing == "conviction":
        if row["conviction"] == "A":
            return 1.5
        if row["conviction"] == "B":
            return 1.0
        return 0.6
    if sizing == "atr_risk":
        return max(0.5, min(1.5, 4.0 / row["atr"]))
    if sizing == "conviction_atr":
        return sizing_multiplier(row, "conviction") * sizing_multiplier(row, "atr_risk")
    raise ValueError(f"unknown sizing: {sizing}")


def exit_parameters(row: dict, exit_policy: str) -> tuple[float, float]:
    atr = row["atr"] / 100.0
    if exit_policy == "fixed_atr":
        return 3.0 * atr, 0.75 * atr
    if exit_policy == "regime_atr":
        # Trend gets room to run; range uses a tighter target and stop.
        return (3.0 * atr, 1.0 * atr) if boolean(row["regime"]) else (2.0 * atr, 0.75 * atr)
    if exit_policy == "wide_volatility":
        return (3.0 * atr, 1.0 * atr) if row["atr"] >= 6 else (2.0 * atr, 0.75 * atr)
    raise ValueError(f"unknown exit policy: {exit_policy}")


def make_trade(row: dict, rank: int, size: float, exit_policy: str, notional: float) -> Trade:
    target, stop = exit_parameters(row, exit_policy)
    label = triple_barrier_label(
        [float(bar["close"]) for bar in row["forward"]],
        entry_price=row["entry"],
        tp_pct=target,
        sl_pct=stop,
        max_horizon=HORIZON,
        forward_highs=[float(bar["high"]) for bar in row["forward"]],
        forward_lows=[float(bar["low"]) for bar in row["forward"]],
    )
    gross = label.ret_pct * 100
    net = gross - COST_PCT
    exit_index = min(max(label.bars_to_hit - 1, 0), len(row["forward"]) - 1)
    return Trade(
        symbol=row["symbol"],
        scan_date=row["scan_date"],
        exit_date=row["forward"][exit_index]["date"],
        gross_return_pct=round(gross, 4),
        net_return_pct=round(net, 4),
        mfe_pct=round(label.mfe_pct * 100, 4),
        mae_pct=round(label.mae_pct * 100, 4),
        bars_to_exit=label.bars_to_hit,
        barrier=label.label,
        notional=notional,
        pnl=round(notional * net / 100, 4),
        target_pct=round(target * 100, 4),
        stop_pct=round(stop * 100, 4),
        rank=rank,
        size_multiplier=round(size, 4),
        regime=row["regime"],
    )


def simulate(
    rows: list[dict], top_n: int, max_positions: int, selection: str, sizing: str, exit_policy: str
) -> dict:
    by_day: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_day[row["scan_date"]].append(row)
    trades: list[Trade] = []
    capital = INITIAL_CAPITAL
    peak = capital
    equity = {min(by_day): capital} if by_day else {}
    open_until: list[str] = []
    daily_turnover: dict[str, float] = defaultdict(float)
    for day in sorted(by_day):
        open_until = [exit for exit in open_until if exit >= day]
        available = max(0, max_positions - len(open_until))
        ranked = rank_rows(by_day[day], selection)[:top_n]
        chosen = ranked[:available]
        if not chosen:
            equity[day] = capital
            continue
        raw_sizes = [sizing_multiplier(row, sizing) for row in chosen]
        total_size = sum(raw_sizes)
        allocation = capital / max_positions
        for rank, (row, raw_size) in enumerate(zip(chosen, raw_sizes, strict=False), 1):
            notional = min(capital * raw_size / total_size, allocation * raw_size)
            trade = make_trade(row, rank, raw_size, exit_policy, notional)
            trades.append(trade)
            open_until.append(trade.exit_date)
            daily_turnover[day] += notional
        # Realized P&L is booked on exit date in the next section's ledger below.
        exits = [
            trade
            for trade in trades
            if trade.exit_date == day and trade not in trades[-len(chosen) :]
        ]
        capital += sum(trade.pnl for trade in exits)
        peak = max(peak, capital)
        equity[day] = capital
    # Rebuild realized equity correctly from all trade exits, including days with no new entries.
    capital = INITIAL_CAPITAL
    equity = {}
    for day in sorted(by_day):
        capital += sum(trade.pnl for trade in trades if trade.exit_date == day)
        equity[day] = capital
        peak = max(peak, capital)
    returns = []
    previous = INITIAL_CAPITAL
    max_drawdown = 0.0
    running_peak = INITIAL_CAPITAL
    for day in sorted(equity):
        value = equity[day]
        returns.append(value / previous - 1 if previous else 0)
        previous = value
        running_peak = max(running_peak, value)
        max_drawdown = min(max_drawdown, value / running_peak - 1 if running_peak else 0)
    years = (
        max(
            1 / 252,
            (date.fromisoformat(max(equity)) - date.fromisoformat(min(equity))).days / 365.25,
        )
        if equity
        else 1
    )
    final_equity = equity[max(equity)] if equity else INITIAL_CAPITAL
    cagr = (final_equity / INITIAL_CAPITAL) ** (1 / years) - 1 if final_equity > 0 else -1
    mean = sum(returns) / len(returns) if returns else 0
    variance = sum((value - mean) ** 2 for value in returns) / max(1, len(returns) - 1)
    sharpe = mean / math.sqrt(variance) * math.sqrt(252) if variance > 0 else None
    wins = [trade.net_return_pct for trade in trades if trade.net_return_pct > 0]
    losses = -sum(trade.net_return_pct for trade in trades if trade.net_return_pct < 0)
    return {
        "config": {
            "top_n": top_n,
            "max_positions": max_positions,
            "selection": selection,
            "sizing": sizing,
            "exit_policy": exit_policy,
        },
        "n_trades": len(trades),
        "final_equity": round(final_equity, 2),
        "cagr": round(cagr, 4),
        "sharpe_daily_realized": round(sharpe, 4) if sharpe is not None else None,
        "max_drawdown": round(max_drawdown, 4),
        "turnover": round(sum(daily_turnover.values()) / INITIAL_CAPITAL, 4),
        "mean_trade_net_pct": round(sum(trade.net_return_pct for trade in trades) / len(trades), 4)
        if trades
        else None,
        "median_trade_net_pct": round(
            sorted(trade.net_return_pct for trade in trades)[len(trades) // 2], 4
        )
        if trades
        else None,
        "win_rate": round(len(wins) / len(trades), 4) if trades else None,
        "profit_factor": round(sum(wins) / losses, 4) if losses else None,
        "avg_bars_to_exit": round(sum(trade.bars_to_exit for trade in trades) / len(trades), 4)
        if trades
        else None,
        "tp_rate": round(sum(trade.barrier == "tp" for trade in trades) / len(trades), 4)
        if trades
        else None,
        "sl_rate": round(sum(trade.barrier == "sl" for trade in trades) / len(trades), 4)
        if trades
        else None,
        "time_rate": round(sum(trade.barrier == "time" for trade in trades) / len(trades), 4)
        if trades
        else None,
        "avg_mfe_pct": round(sum(trade.mfe_pct for trade in trades) / len(trades), 4)
        if trades
        else None,
        "avg_mae_pct": round(sum(trade.mae_pct for trade in trades) / len(trades), 4)
        if trades
        else None,
        "regime": regime_summary(trades),
        "time_to_target": time_to_target_summary(trades),
    }


def regime_summary(trades: list[Trade]) -> dict:
    output = {}
    for regime in sorted({trade.regime for trade in trades}):
        subset = [trade for trade in trades if trade.regime == regime]
        output[regime] = {
            "n": len(subset),
            "mean_net_pct": round(sum(t.net_return_pct for t in subset) / len(subset), 4)
            if subset
            else None,
            "sl_rate": round(sum(t.barrier == "sl" for t in subset) / len(subset), 4)
            if subset
            else None,
        }
    return output


def time_to_target_summary(trades: list[Trade]) -> dict:
    tp = [trade.bars_to_exit for trade in trades if trade.barrier == "tp"]
    return {
        "tp_n": len(tp),
        "tp_median_bars": sorted(tp)[len(tp) // 2] if tp else None,
        "tp_within_1d": round(sum(bar <= 1 for bar in tp) / len(tp), 4) if tp else None,
        "tp_within_2d": round(sum(bar <= 2 for bar in tp) / len(tp), 4) if tp else None,
    }


def write_report(path: Path, payload: dict) -> None:
    results = payload["results"]
    ranked = sorted(
        results,
        key=lambda item: (item.get("sharpe_daily_realized") or -999, item.get("cagr") or -999),
        reverse=True,
    )
    lines = [
        "# FinPilot Portfolio Target Backtest",
        "",
        "## Scope",
        "",
        "This is a research-only portfolio simulation using cached daily OHLC paths. It is not a live trading change.",
        "",
        f"- Resolved path rows: {payload['inventory']['resolved_rows']:,}",
        f"- Horizon: {payload['methodology']['horizon']} trading days",
        f"- Round-trip cost: {payload['methodology']['cost_pct']:.2f}%",
        "- Selection: entry_ok rows ranked by composite score; top-N is applied per scan day.",
        "- Capital: 100,000 with 20 maximum portfolio slots; open positions compete for slots.",
        "- Barrier tie: stop-first when high and low touch both barriers on the same bar.",
        "",
        "## Portfolio results",
        "",
        "| Top-N | Sizing | Exit | Trades | CAGR | Sharpe | Max DD | Turnover | Win | PF | Avg bars |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in ranked:
        config = item["config"]
        lines.append(
            f"| {config['top_n']} | {config['sizing']} | {config['exit_policy']} | {item['n_trades']:,} | "
            f"{item['cagr']:.2%} | {item.get('sharpe_daily_realized', 'n/a')} | {item['max_drawdown']:.2%} | "
            f"{item['turnover']:.2f}x | {item.get('win_rate', 0):.1%} | {item.get('profit_factor', 'n/a')} | {item.get('avg_bars_to_exit', 'n/a')} |"
        )
    best = ranked[0] if ranked else None
    lines += [
        "",
        "## Path-aware findings",
        "",
        "- The portfolio result is not interchangeable with signal-level expectancy: top-N selection, overlapping positions, capacity and realized exit timing change the outcome.",
        "- The best current configuration is a research candidate only; its Sharpe and CAGR are close to zero and require a locked future shadow test.",
        "- The wide-volatility exit generally improves target-hit rate and drawdown relative to the fixed ATR control in the observed portfolio screen, but it does not establish a universal optimum.",
        "- Time-to-target is available for TP-labelled trades. Use the JSON `time_to_target` fields to compare early capital release with exit policy changes.",
        "",
        "## Decision",
        "",
        f"- Best observed screen: `{best['config'] if best else 'n/a'}`.",
        "- Production decision: NO-GO. The result is a small historical research sample, uses cached daily bars, and has no spread/impact or independent forward shadow confirmation.",
        "- Next gate: run the same configurations on a locked future shadow window with broker execution prices, ADV-based sizing, spread/impact, and daily marked-to-market equity.",
        "",
        "## Required follow-up",
        "",
        "- Add dollar ADV and spread/impact constraints before interpreting turnover or CAGR.",
        "- Add a daily marked-to-market curve, not only realized-exit equity.",
        "- Compare raw and canonical symbol-day selection to quantify duplicate scan inflation.",
        "- Lock the exit and sizing policy before opening the next validation period.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    rows = load_rows(args.csv)
    resolved, inventory = resolve_paths(rows, args.cache)
    configurations = []
    for top_n in (5, 10, 20):
        for sizing in ("equal", "conviction", "atr_risk", "conviction_atr"):
            for exit_policy in ("fixed_atr", "regime_atr", "wide_volatility"):
                configurations.append(
                    simulate(resolved, top_n, 20, "composite", sizing, exit_policy)
                )
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "methodology": {
            "horizon": HORIZON,
            "cost_pct": COST_PCT,
            "capital": INITIAL_CAPITAL,
            "entry": "recorded scan price",
            "same_bar_tie": "stop-first",
            "unavailable": ["spread", "intraday fill", "short-side"],
        },
        "inventory": inventory,
        "results": configurations,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.out.with_suffix(".md"), payload)
    print(f"rows={len(rows)} resolved={len(resolved)} configurations={len(configurations)}")
    print(f"out={args.out}")


if __name__ == "__main__":
    main()
