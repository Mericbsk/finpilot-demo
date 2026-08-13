"""Research-only decomposition of the full-universe High RVOL result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from research.budget_return_battery_2026_08_12 import DEFAULT_COST_PCT

COHORTS = ("high_rvol_all", "high_rvol_eligible", "high_rvol_rejected")


def _mean_by_date(frame: pd.DataFrame, value: str, clip: float | None = None) -> pd.Series:
    values = frame[value].clip(-clip, clip) if clip is not None else frame[value]
    return values.groupby(frame["scan_date"]).mean().sort_index()


def _summary(values: pd.Series, cost_pct: float) -> dict[str, Any]:
    net = values - cost_pct
    return {
        "dates": int(len(values)),
        "median_date_mean_pct": float(values.median()) if len(values) else None,
        "mean_date_mean_pct": float(values.mean()) if len(values) else None,
        "positive_date_share": float((values > 0).mean()) if len(values) else None,
        "median_net_pct": float(net.median()) if len(net) else None,
        "mean_net_pct": float(net.mean()) if len(net) else None,
        "top_four_share_of_raw_sum_pct": float(100 * values.nlargest(4).sum() / values.sum())
        if values.sum()
        else None,
        "every_fifth_date_mean_net_pct": float(net.iloc[::5].mean()) if len(net) else None,
    }


def _random_control(
    frame: pd.DataFrame,
    selected: pd.DataFrame,
    cohort: str,
    seed: int = 20260812,
    runs: int = 100,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    selected_groups = selected.groupby("scan_date")
    control_returns: list[float] = []
    selected_returns: list[float] = []
    for date, group in selected_groups:
        universe = frame[frame["scan_date"] == date]
        if cohort == "high_rvol_eligible":
            universe = universe[universe["entry_ok"]]
        elif cohort == "high_rvol_rejected":
            universe = universe[~universe["entry_ok"]]
        universe = universe[~universe["symbol"].isin(group["symbol"])]
        if len(universe) < len(group):
            continue
        selected_returns.append(float(group["c2c_1d"].mean()))
        for _ in range(runs):
            sample = universe.iloc[rng.choice(len(universe), size=len(group), replace=False)]
            control_returns.append(float(sample["c2c_1d"].mean()))
    selected_mean = float(np.mean(selected_returns)) if selected_returns else None
    control_mean = float(np.mean(control_returns)) if control_returns else None
    return {
        "runs": runs,
        "matched_dates": len(selected_returns),
        "selected_mean_date_1d_pct": selected_mean,
        "random_control_mean_1d_pct": control_mean,
        "lift_vs_random_1d_pct": selected_mean - control_mean
        if selected_mean is not None and control_mean is not None
        else None,
    }


def run(csv_path: Path, min_history_dates: int = 10, random_runs: int = 100) -> dict[str, Any]:
    raw = pd.read_csv(csv_path, low_memory=False)
    required = {"symbol", "scan_date", "entry_ok", "rvol", "c2c_1d", "c2c_5d"}
    missing = sorted(required.difference(raw.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    frame = raw.copy()
    frame["scan_date"] = pd.to_datetime(frame["scan_date"], errors="coerce").dt.date
    frame = frame.dropna(subset=["scan_date"]).drop_duplicates(["symbol", "scan_date"], keep="last")
    for column in ("rvol", "c2c_1d", "c2c_5d"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["entry_ok"] = frame["entry_ok"].astype(str).str.lower().isin(("true", "1", "yes"))
    frame = frame.dropna(subset=["rvol", "c2c_1d", "c2c_5d"]).sort_values(["scan_date", "symbol"])
    dates = sorted(frame["scan_date"].unique())
    selected_rows: list[pd.DataFrame] = []
    thresholds: list[dict[str, Any]] = []
    for index, date in enumerate(dates):
        if index < min_history_dates:
            continue
        history = frame[frame["scan_date"].isin(dates[:index])]
        current = frame[frame["scan_date"] == date].copy()
        threshold = float(history["rvol"].quantile(0.90))
        current["high_rvol"] = current["rvol"] >= threshold
        selected_rows.append(current[current["high_rvol"]].assign(rvol_q90_prior=threshold))
        thresholds.append(
            {
                "scan_date": date,
                "rvol_q90_prior": threshold,
                "high_rvol_n": int(current["high_rvol"].sum()),
            }
        )
    selected = (
        pd.concat(selected_rows, ignore_index=True) if selected_rows else frame.iloc[0:0].copy()
    )
    selected["cohort"] = np.select(
        [selected["entry_ok"], ~selected["entry_ok"]],
        ["high_rvol_eligible", "high_rvol_rejected"],
        default="high_rvol_all",
    )
    selected_all = selected.copy()
    selected_groups = {
        "high_rvol_all": selected_all,
        "high_rvol_eligible": selected_all[selected_all["entry_ok"]],
        "high_rvol_rejected": selected_all[~selected_all["entry_ok"]],
    }
    summaries: dict[str, Any] = {}
    controls: dict[str, Any] = {}
    for name, group in selected_groups.items():
        five_day = _mean_by_date(group, "c2c_5d")
        one_day = _mean_by_date(group, "c2c_1d")
        clipped_five_day = _mean_by_date(group, "c2c_5d", clip=50)
        summaries[name] = {
            "rows": int(len(group)),
            "five_day": _summary(five_day, DEFAULT_COST_PCT),
            "five_day_clip_50": _summary(_mean_by_date(group, "c2c_5d", clip=50), DEFAULT_COST_PCT),
            "one_day_non_overlapping": _summary(one_day, DEFAULT_COST_PCT),
            "cost_sensitivity": {
                str(cost): {
                    "one_day_mean_net_pct": float((one_day - cost).mean())
                    if len(one_day)
                    else None,
                    "five_day_clip_50_mean_net_pct": float((clipped_five_day - cost).mean())
                    if len(clipped_five_day)
                    else None,
                }
                for cost in (0.0, 0.55, 1.0, 2.0)
            },
            "row_median_5d_pct": float(group["c2c_5d"].median()) if len(group) else None,
            "row_p99_5d_pct": float(group["c2c_5d"].quantile(0.99)) if len(group) else None,
            "rows_above_50_pct": int((group["c2c_5d"] > 50).sum()),
            "rows_below_minus_50_pct": int((group["c2c_5d"] < -50).sum()),
        }
        controls[name] = _random_control(frame, group, name, runs=random_runs)
    return {
        "status": "exploratory",
        "production_change": False,
        "locked_oos": "not_opened",
        "source_csv": str(csv_path),
        "protocol": {
            "threshold": "prior-date expanding q90 RVOL",
            "one_day_control": "c2c_1d is non-overlapping by date",
            "five_day_warning": "c2c_5d windows overlap",
            "clip": "row clipping is applied before date aggregation",
            "cost_pct": DEFAULT_COST_PCT,
        },
        "rows": {"raw": len(raw), "canonical": len(frame), "selected_high_rvol": len(selected)},
        "dates": {
            "total": len(dates),
            "evaluated": max(0, len(dates) - min_history_dates),
            "warmup": min_history_dates,
        },
        "thresholds": thresholds,
        "cohort_summary": summaries,
        "same_date_random_control": controls,
        "decision": "Do not promote High RVOL as return selector until clipped, one-day, matched-control and price-provenance checks are positive.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument("--min-history-dates", type=int, default=10)
    parser.add_argument("--random-runs", type=int, default=100)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/backtest_out/high_rvol_opportunity_battery_2026-08-12.json"),
    )
    args = parser.parse_args()
    result = run(args.csv, args.min_history_dates, args.random_runs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result["cohort_summary"], indent=2, default=str))


if __name__ == "__main__":
    main()
