"""Deep, research-only audit of the high-RVOL budget result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from research.budget_return_battery_2026_08_12 import (
    DEFAULT_COST_PCT,
    _money_summary,
    _parse_bool,
    _strategy_masks,
)


def _date_returns(
    frame: pd.DataFrame,
    mask: pd.Series,
    atr_parity: bool,
    clip: tuple[float, float] | None = None,
) -> pd.DataFrame:
    rows = []
    for date, group in frame[mask].groupby("scan_date", sort=True):
        values = group["c2c_5d"].to_numpy(dtype=float)
        if clip is not None:
            values = np.clip(values, clip[0], clip[1])
        if atr_parity:
            weights = 1.0 / group["atr_pct_real"].clip(lower=0.1).to_numpy(dtype=float)
            portfolio = float(np.average(values, weights=weights))
        else:
            portfolio = float(values.mean())
        rows.append(
            {
                "scan_date": date,
                "n": int(len(group)),
                "portfolio_raw_pct": portfolio,
                "portfolio_net_pct": portfolio - DEFAULT_COST_PCT,
                "row_max_pct": float(values.max()),
                "row_median_pct": float(np.median(values)),
                "row_p99_pct": float(np.percentile(values, 99)),
            }
        )
    result = pd.DataFrame(rows)
    if not result.empty:
        result["equity_factor"] = 1.0 + result["portfolio_net_pct"] / 100.0
    return result


def _scenario(date_frame: pd.DataFrame, dates: list[Any], atr_parity: bool) -> dict[str, Any]:
    subset = date_frame[date_frame["scan_date"].isin(dates)]
    returns = subset["portfolio_raw_pct"].tolist()
    return {
        "dates": len(dates),
        "date_list": [str(item) for item in dates],
        "summary_10000_usd": _money_summary(returns, 10_000.0, DEFAULT_COST_PCT),
        "atr_parity": atr_parity,
    }


def run(csv_path: Path) -> dict[str, Any]:
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
    numeric = ["gap_pct", "rvol", "atr_pct_real", "finpilot_score", "c2c_5d"]
    frame.loc[:, numeric] = frame[numeric].apply(pd.to_numeric, errors="coerce")
    frame["entry_ok"] = _parse_bool(frame["entry_ok"])
    frame = frame.dropna(subset=numeric).sort_values(["scan_date", "symbol"]).reset_index(drop=True)
    dates = sorted(frame["scan_date"].unique())
    split = max(1, int(len(dates) * 0.70))
    train = frame[frame["scan_date"].isin(set(dates[:split]))]
    validation = frame[~frame["scan_date"].isin(set(dates[:split]))]
    mask = _strategy_masks(validation, train)["high_rvol"]
    result: dict[str, Any] = {
        "status": "exploratory",
        "scope": "research_only",
        "production_change": False,
        "source_csv": str(csv_path),
        "protocol": {
            "starting_capital_usd": 10_000.0,
            "cost_pct": DEFAULT_COST_PCT,
            "validation_split": "chronological 70/30",
            "outcome": "c2c_5d",
            "overlap_warning": "c2c_5d windows overlap; non-overlap subsequences are reported as sensitivity only",
            "locked_oos": "not_opened",
        },
    }
    for name, parity in (("equal_weight", False), ("atr_parity", True)):
        dated = _date_returns(validation, mask, parity)
        if dated.empty:
            result[name] = {"status": "INSUFFICIENT_DATA"}
            continue
        ranked = dated.sort_values("portfolio_net_pct", ascending=False).reset_index(drop=True)
        all_dates = dated["scan_date"].tolist()
        worst_date = dated.sort_values("portfolio_net_pct").iloc[0]["scan_date"]
        top_dates = set(ranked.head(4)["scan_date"])
        without_top = dated[~dated["scan_date"].isin(top_dates)]
        alternating = all_dates[::5]
        result[name] = {
            "date_level": dated.to_dict(orient="records"),
            "top_contribution": ranked.head(5).to_dict(orient="records"),
            "top_four_dates_share_of_net_sum_pct": float(
                ranked.head(4)["portfolio_net_pct"].sum() / dated["portfolio_net_pct"].sum() * 100.0
            )
            if dated["portfolio_net_pct"].sum()
            else None,
            "without_top_four_dates": _scenario(
                without_top, without_top["scan_date"].tolist(), parity
            ),
            "without_worst_date": _scenario(
                dated[dated["scan_date"] != worst_date],
                dated.loc[dated["scan_date"] != worst_date, "scan_date"].tolist(),
                parity,
            ),
            "non_overlap_every_fifth_date": _scenario(dated, alternating, parity),
            "row_outlier_sensitivity": {
                "clip_minus_50_plus_50_pct": _money_summary(
                    _date_returns(validation, mask, parity, clip=(-50.0, 50.0))[
                        "portfolio_raw_pct"
                    ].tolist(),
                    10_000.0,
                    DEFAULT_COST_PCT,
                ),
                "clip_minus_20_plus_20_pct": _money_summary(
                    _date_returns(validation, mask, parity, clip=(-20.0, 20.0))[
                        "portfolio_raw_pct"
                    ].tolist(),
                    10_000.0,
                    DEFAULT_COST_PCT,
                ),
                "row_outcomes_above_50_pct": int((validation.loc[mask, "c2c_5d"] > 50.0).sum()),
                "row_outcomes_below_minus_50_pct": int(
                    (validation.loc[mask, "c2c_5d"] < -50.0).sum()
                ),
            },
        }
    result["interpretation"] = (
        "A high-RVOL budget result is not robust if it disappears after top-date, non-overlap or outlier sensitivity. No production rule is proposed."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument(
        "--out", type=Path, default=Path("data/backtest_out/high_rvol_deep_audit_2026-08-12.json")
    )
    args = parser.parse_args()
    result = run(args.csv)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                name: {key: value for key, value in block.items() if key != "date_level"}
                for name, block in result.items()
                if name in ("equal_weight", "atr_parity")
            },
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
