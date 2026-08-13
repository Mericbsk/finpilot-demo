"""Expanding, all-universe high-RVOL audit with prior-date thresholds only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from research.budget_return_battery_2026_08_12 import DEFAULT_COST_PCT, _money_summary, _parse_bool


def _date_returns(frame: pd.DataFrame, mask: pd.Series, atr_parity: bool) -> list[float]:
    values: list[float] = []
    for _, group in frame[mask].groupby("scan_date", sort=True):
        if atr_parity:
            weights = 1.0 / group["atr_pct_real"].clip(lower=0.1).to_numpy(dtype=float)
            values.append(float(np.average(group["c2c_5d"], weights=weights)))
        else:
            values.append(float(group["c2c_5d"].mean()))
    return values


def run(csv_path: Path, min_history_dates: int = 10) -> dict[str, Any]:
    raw = pd.read_csv(csv_path, low_memory=False)
    required = {"symbol", "scan_date", "entry_ok", "rvol", "atr_pct_real", "c2c_5d"}
    missing = sorted(required.difference(raw.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    frame = raw.copy()
    frame["scan_date"] = pd.to_datetime(frame["scan_date"], errors="coerce").dt.date
    frame = frame.dropna(subset=["scan_date"]).drop_duplicates(["symbol", "scan_date"], keep="last")
    numeric = ["rvol", "atr_pct_real", "c2c_5d"]
    frame.loc[:, numeric] = frame[numeric].apply(pd.to_numeric, errors="coerce")
    frame["entry_ok"] = _parse_bool(frame["entry_ok"])
    frame = frame.dropna(subset=numeric).sort_values(["scan_date", "symbol"]).reset_index(drop=True)
    dates = sorted(frame["scan_date"].unique())
    daily_rows: list[dict[str, Any]] = []
    for index, date in enumerate(dates):
        if index < min_history_dates:
            continue
        history = frame[frame["scan_date"].isin(dates[:index])]
        current = frame[frame["scan_date"] == date].copy()
        threshold = float(history["rvol"].quantile(0.90))
        current["high_rvol"] = current["rvol"] >= threshold
        for cohort, cohort_mask in (
            ("all_rows", pd.Series(True, index=current.index)),
            ("eligible", current["entry_ok"]),
            ("rejected", ~current["entry_ok"]),
            ("high_rvol_all", current["high_rvol"]),
            ("high_rvol_eligible", current["high_rvol"] & current["entry_ok"]),
            ("high_rvol_rejected", current["high_rvol"] & ~current["entry_ok"]),
        ):
            group = current[cohort_mask]
            if group.empty:
                continue
            daily_rows.append(
                {
                    "scan_date": date,
                    "cohort": cohort,
                    "rvol_q90_prior": threshold,
                    "n": int(len(group)),
                    "mean_5d_pct": float(group["c2c_5d"].mean()),
                    "median_5d_pct": float(group["c2c_5d"].median()),
                    "positive_rate": float((group["c2c_5d"] > 0).mean()),
                    "outcomes_above_50_pct": int((group["c2c_5d"] > 50).sum()),
                    "outcomes_below_minus_50_pct": int((group["c2c_5d"] < -50).sum()),
                }
            )
    daily = pd.DataFrame(daily_rows)
    summaries: dict[str, Any] = {}
    for cohort in sorted(daily["cohort"].unique()):
        subset = daily[daily["cohort"] == cohort].sort_values("scan_date")
        raw_returns = subset["mean_5d_pct"].tolist()
        summaries[cohort] = {
            "dates": int(len(subset)),
            "rows": int(subset["n"].sum()),
            "median_date_mean_5d_pct": float(subset["mean_5d_pct"].median()),
            "median_date_median_5d_pct": float(subset["median_5d_pct"].median()),
            "mean_date_mean_5d_pct": float(subset["mean_5d_pct"].mean()),
            "positive_date_share": float((subset["mean_5d_pct"] > 0).mean()),
            "equal_weight_10000": _money_summary(raw_returns, 10_000.0, DEFAULT_COST_PCT),
            "outcomes_above_50_pct": int(subset["outcomes_above_50_pct"].sum()),
            "outcomes_below_minus_50_pct": int(subset["outcomes_below_minus_50_pct"].sum()),
        }
    return {
        "status": "exploratory",
        "scope": "research_only",
        "production_change": False,
        "source_csv": str(csv_path),
        "rows": {
            "raw": len(raw),
            "canonical_outcome_rows": len(frame),
            "symbols": int(frame["symbol"].nunique()),
        },
        "dates": {
            "total": len(dates),
            "evaluated": max(0, len(dates) - min_history_dates),
            "history_warmup_dates": min_history_dates,
        },
        "protocol": {
            "threshold": "prior-date expanding q90 RVOL; no same-date outcome leakage",
            "outcome": "c2c_5d",
            "cost_pct": DEFAULT_COST_PCT,
            "overlap_warning": "5-day outcomes overlap; this is not an executable event portfolio",
            "price_integrity": "extreme jumps retained and counted; no silent filtering",
            "locked_oos": "not_opened",
        },
        "cohort_summary": summaries,
        "date_level": daily.to_dict(orient="records"),
        "interpretation": "All-universe expanding audit; high-RVOL is not a production selector unless results survive price provenance, non-overlap and execution validation.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument("--min-history-dates", type=int, default=10)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/backtest_out/high_rvol_full_universe_2026-08-12.json"),
    )
    args = parser.parse_args()
    result = run(args.csv, min_history_dates=args.min_history_dates)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result["cohort_summary"], indent=2, default=str))


if __name__ == "__main__":
    main()
