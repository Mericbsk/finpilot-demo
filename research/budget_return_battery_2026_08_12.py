"""Research-only $10,000 return scenarios for tested candidate rules."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

STARTING_CAPITAL = 10_000.0
DEFAULT_COST_PCT = 0.55


def _money_summary(returns: list[float], capital: float, cost_pct: float) -> dict[str, Any]:
    values = np.asarray(returns, dtype=float)
    values = values[np.isfinite(values)]
    if not len(values):
        return {
            "n_dates": 0,
            "starting_capital_usd": capital,
            "final_capital_usd": None,
            "profit_loss_usd": None,
            "return_pct": None,
            "max_drawdown_pct": None,
            "median_daily_net_pct": None,
            "cvar5_daily_net_pct": None,
        }
    net = values - cost_pct
    equity = capital * np.cumprod(1.0 + net / 100.0)
    drawdown = equity / np.maximum.accumulate(equity) - 1.0
    tail_count = max(1, int(len(net) * 0.05))
    final = float(equity[-1])
    return {
        "n_dates": int(len(net)),
        "starting_capital_usd": capital,
        "final_capital_usd": final,
        "profit_loss_usd": final - capital,
        "return_pct": (final / capital - 1.0) * 100.0,
        "max_drawdown_pct": float(drawdown.min() * 100.0),
        "median_daily_net_pct": float(np.median(net)),
        "cvar5_daily_net_pct": float(np.sort(net)[:tail_count].mean()),
    }


def _parse_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(("true", "1", "yes"))


def _portfolio_returns(frame: pd.DataFrame, mask: pd.Series, atr_parity: bool) -> list[float]:
    values: list[float] = []
    selected = frame[mask]
    for _, group in selected.groupby("scan_date", sort=True):
        if group.empty:
            continue
        if atr_parity:
            weights = 1.0 / group["atr_pct_real"].clip(lower=0.1).to_numpy(dtype=float)
            values.append(float(np.average(group["c2c_5d"], weights=weights)))
        else:
            values.append(float(group["c2c_5d"].mean()))
    return values


def _strategy_masks(frame: pd.DataFrame, train: pd.DataFrame) -> dict[str, pd.Series]:
    gap_low = float(train["gap_pct"].quantile(0.10))
    gap_high = float(train["gap_pct"].quantile(0.90))
    rvol_low = float(train["rvol"].quantile(0.10))
    rvol_high = float(train["rvol"].quantile(0.90))
    score_high = float(train["finpilot_score"].quantile(0.80))
    score_low = float(train["finpilot_score"].quantile(0.20))
    eligible = frame["entry_ok"]
    low_gap = frame["gap_pct"] <= gap_low
    high_gap = frame["gap_pct"] >= gap_high
    low_rvol = frame["rvol"] <= rvol_low
    high_rvol = frame["rvol"] >= rvol_high
    high_score = frame["finpilot_score"] >= score_high
    low_score = frame["finpilot_score"] <= score_low
    return {
        "all_rows": pd.Series(True, index=frame.index),
        "entry_ok": eligible,
        "rejected": ~eligible,
        "low_gap": low_gap,
        "high_gap": high_gap,
        "low_rvol": low_rvol,
        "high_rvol": high_rvol,
        "high_score": high_score,
        "low_score": low_score,
        "entry_ok_low_gap": eligible & low_gap,
        "entry_ok_low_rvol": eligible & low_rvol,
        "entry_ok_high_rvol": eligible & high_rvol,
        "entry_ok_high_score_low_gap": eligible & high_score & low_gap,
        "entry_ok_low_score_low_gap": eligible & low_score & low_gap,
        "entry_ok_low_gap_low_rvol": eligible & low_gap & low_rvol,
    }


def run(
    csv_path: Path, capital: float = STARTING_CAPITAL, cost_pct: float = DEFAULT_COST_PCT
) -> dict[str, Any]:
    raw = pd.read_csv(csv_path, low_memory=False)
    required = {
        "symbol",
        "scan_date",
        "entry_ok",
        "gap_pct",
        "rvol",
        "atr_pct_real",
        "finpilot_score",
        "c2c_5d",
    }
    missing = sorted(required.difference(raw.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    frame = raw.copy()
    frame["scan_date"] = pd.to_datetime(frame["scan_date"], errors="coerce").dt.date
    frame = frame.dropna(subset=["scan_date"]).drop_duplicates(["symbol", "scan_date"], keep="last")
    numeric_columns = ["gap_pct", "rvol", "atr_pct_real", "finpilot_score", "c2c_5d"]
    frame.loc[:, numeric_columns] = frame[numeric_columns].apply(pd.to_numeric, errors="coerce")
    frame["entry_ok"] = _parse_bool(frame["entry_ok"])
    frame = (
        frame.dropna(subset=numeric_columns)
        .sort_values(["scan_date", "symbol"])
        .reset_index(drop=True)
    )
    dates = sorted(frame["scan_date"].unique())
    split = max(1, int(len(dates) * 0.70))
    train_dates = set(dates[:split])
    validation = frame[~frame["scan_date"].isin(train_dates)].copy()
    masks = _strategy_masks(validation, frame[frame["scan_date"].isin(train_dates)])
    results: dict[str, Any] = {}
    for name, mask in masks.items():
        equal_returns = _portfolio_returns(validation, mask, atr_parity=False)
        parity_returns = _portfolio_returns(validation, mask, atr_parity=True)
        results[name] = {
            "selected_rows": int(mask.sum()),
            "selected_dates": int(validation.loc[mask, "scan_date"].nunique()),
            "equal_weight": _money_summary(equal_returns, capital, cost_pct),
            "atr_parity": _money_summary(parity_returns, capital, cost_pct),
        }
    return {
        "status": "exploratory",
        "scope": "research_only",
        "production_change": False,
        "source_csv": str(csv_path),
        "rows": {"raw": len(raw), "canonical_outcome_rows": len(frame)},
        "dates": {
            "total": len(dates),
            "train": len(train_dates),
            "validation": len(dates) - len(train_dates),
        },
        "protocol": {
            "starting_capital_usd": capital,
            "round_trip_cost_pct": cost_pct,
            "outcome": "c2c_5d",
            "thresholds": "train-only q10/q20/q80/q90",
            "compounding": "daily scan-date portfolio return; overlapping 5-day outcomes",
            "execution": "not observed; no spread, fill, ADV, turnover or capacity claim",
            "locked_oos": "not_opened",
        },
        "strategies": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument("--capital", type=float, default=STARTING_CAPITAL)
    parser.add_argument("--cost-pct", type=float, default=DEFAULT_COST_PCT)
    parser.add_argument(
        "--out", type=Path, default=Path("data/backtest_out/budget_return_battery_2026-08-12.json")
    )
    args = parser.parse_args()
    result = run(args.csv, capital=args.capital, cost_pct=args.cost_pct)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    ranked = sorted(
        (
            (name, data["equal_weight"]["final_capital_usd"])
            for name, data in result["strategies"].items()
            if data["equal_weight"]["final_capital_usd"] is not None
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    print(
        json.dumps(
            {"capital": args.capital, "cost_pct": args.cost_pct, "top_equal_weight": ranked[:10]},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
