"""Research-only 1-10 day High RVOL horizon battery.

Horizons above one day are reconstructed by compounding each symbol's daily
``c2c_1d`` observations across the common scan-date sequence. This is a
proxy, not a replacement for raw OHLC forward returns.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from research.budget_return_battery_2026_08_12 import DEFAULT_COST_PCT


def _summary(values: pd.Series, cost_pct: float = DEFAULT_COST_PCT) -> dict[str, Any]:
    net = values - cost_pct
    return {
        "rows": int(len(values)),
        "dates": int(values.index.nunique()),
        "mean_pct": float(values.mean()) if len(values) else None,
        "median_pct": float(values.median()) if len(values) else None,
        "positive_date_share": float((values.groupby(level=0).mean() > 0).mean())
        if len(values)
        else None,
        "mean_net_pct": float(net.mean()) if len(net) else None,
        "median_net_pct": float(net.median()) if len(net) else None,
        "clipped_mean_net_pct": float(values.clip(-50, 50).sub(cost_pct).mean())
        if len(values)
        else None,
    }


def run(csv_path: Path, min_history_dates: int = 10, max_horizon: int = 10) -> dict[str, Any]:
    required = {"symbol", "scan_date", "entry_ok", "rvol", "c2c_1d"}
    frame = pd.read_csv(csv_path, low_memory=False)
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    frame["scan_date"] = pd.to_datetime(frame["scan_date"], errors="coerce").dt.date
    frame = frame.dropna(subset=["scan_date"]).drop_duplicates(["symbol", "scan_date"], keep="last")
    frame["rvol"] = pd.to_numeric(frame["rvol"], errors="coerce")
    frame["c2c_1d"] = pd.to_numeric(frame["c2c_1d"], errors="coerce")
    frame["entry_ok"] = frame["entry_ok"].astype(str).str.lower().isin(("true", "1", "yes"))
    frame = frame.dropna(subset=["rvol", "c2c_1d"])
    dates = sorted(frame["scan_date"].unique())
    date_index = {date: index for index, date in enumerate(dates)}
    lookup = frame.set_index(["symbol", "scan_date"])["c2c_1d"]
    selected: list[dict[str, Any]] = []
    for index, date in enumerate(dates):
        if index < min_history_dates:
            continue
        threshold = float(frame[frame["scan_date"].isin(dates[:index])]["rvol"].quantile(0.90))
        current = frame[(frame["scan_date"] == date) & (frame["rvol"] >= threshold)]
        for row in current.itertuples(index=False):
            selected.append({"symbol": row.symbol, "scan_date": date, "entry_ok": row.entry_ok})
    selected_frame = pd.DataFrame(selected)
    cohorts = {
        "high_rvol_all": selected_frame,
        "high_rvol_eligible": selected_frame[selected_frame["entry_ok"]],
        "high_rvol_rejected": selected_frame[~selected_frame["entry_ok"]],
    }
    output: dict[str, Any] = {}
    for cohort, group in cohorts.items():
        horizon_results: dict[str, Any] = {}
        for horizon in range(1, max_horizon + 1):
            returns: list[dict[str, Any]] = []
            for row in group.itertuples(index=False):
                start = date_index[row.scan_date]
                values = []
                complete = True
                for offset in range(horizon):
                    target_index = start + offset
                    if target_index >= len(dates):
                        complete = False
                        break
                    try:
                        values.append(float(lookup.loc[(row.symbol, dates[target_index])]))
                    except KeyError:
                        complete = False
                        break
                if complete:
                    returns.append(
                        {
                            "scan_date": row.scan_date,
                            "return_pct": (np.prod(1 + np.array(values) / 100) - 1) * 100,
                        }
                    )
            values = pd.DataFrame(returns)
            if len(values):
                series = values.set_index("scan_date")["return_pct"]
                horizon_results[str(horizon)] = _summary(series)
            else:
                horizon_results[str(horizon)] = _summary(pd.Series(dtype=float))
        output[cohort] = horizon_results
    return {
        "status": "exploratory",
        "production_change": False,
        "locked_oos": "not_opened",
        "protocol": {
            "selection": "prior-date expanding q90 RVOL",
            "horizon_proxy": "compound same-symbol c2c_1d over common scan-date sequence",
            "warning": "not raw OHLC; missing symbol-date observations are excluded",
            "cost_pct": DEFAULT_COST_PCT,
        },
        "dates": {"total": len(dates), "evaluated": max(0, len(dates) - min_history_dates)},
        "cohort_summary": output,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument("--min-history-dates", type=int, default=10)
    parser.add_argument("--max-horizon", type=int, default=10)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/backtest_out/high_rvol_horizon_battery_2026-08-12.json"),
    )
    args = parser.parse_args()
    result = run(args.csv, args.min_history_dates, args.max_horizon)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result["cohort_summary"], indent=2, default=str))


if __name__ == "__main__":
    main()
