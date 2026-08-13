"""Exploratory anatomy of strong one-day and five-day price moves.

This module profiles winners using only fields known at scan time. It is
descriptive, not causal, and cannot promote a production rule or open OOS.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

HORIZONS = ("c2c_1d", "c2c_5d")
HORIZON_DAYS = {"c2c_1d": 1, "c2c_5d": 5}
FEATURES = (
    "gap_pct",
    "rvol",
    "atr_pct_real",
    "sentiment",
    "overnight_gap_factor",
    "score",
    "entry_ok",
    "catalyst_factor",
)


def load_export(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, low_memory=False)
    for column in (*HORIZONS, *FEATURES):
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def _profile(frame: pd.DataFrame, horizon: str, quantile: float) -> dict[str, Any]:
    usable = frame.dropna(subset=[horizon]).copy()
    threshold = float(usable[horizon].quantile(quantile))
    winners = usable[usable[horizon] >= threshold]
    features: dict[str, Any] = {}
    for column in FEATURES:
        if column not in usable:
            continue
        correlation = usable[[horizon, column]].corr(method="spearman").iloc[0, 1]
        features[column] = {
            "all_median": float(usable[column].median()),
            "winner_median": float(winners[column].median()),
            "winner_missing_rate": float(winners[column].isna().mean()),
            "spearman_with_outcome": None if pd.isna(correlation) else float(correlation),
        }
    return {
        "horizon": horizon,
        "rows": int(len(usable)),
        "winner_rows": int(len(winners)),
        "winner_quantile": quantile,
        "winner_threshold_pct": threshold,
        "winner_median_pct": float(winners[horizon].median()),
        "features": features,
        "interpretation": "descriptive winner profile; not causal or promotion evidence",
    }


def _load_bars(cache_dir: Path, symbol: str) -> list[dict[str, Any]]:
    try:
        raw = json.loads((cache_dir / f"{symbol}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return sorted(
        [bar for bar in raw if isinstance(bar, dict) and bar.get("date") and bar.get("close")],
        key=lambda bar: str(bar["date"]),
    )


def _forward_return(cache_dir: Path, symbol: str, scan_date: str, horizon: int) -> float | None:
    bars = _load_bars(cache_dir, symbol)
    index = next((i for i, bar in enumerate(bars) if str(bar["date"]) >= scan_date), None)
    if index is None or index + horizon >= len(bars):
        return None
    start = float(bars[index]["close"])
    end = float(bars[index + horizon]["close"])
    return (end / start - 1.0) * 100.0 if start > 0 else None


def _same_date_controls(frame: pd.DataFrame, horizon: str) -> dict[str, Any]:
    usable = frame.dropna(subset=[horizon]).copy()
    threshold = usable[horizon].quantile(0.90)
    usable["winner"] = usable[horizon] >= threshold
    daily = []
    for scan_date, group in usable.groupby("scan_date"):
        winners = group[group["winner"]]
        controls = group[~group["winner"]]
        if winners.empty or controls.empty:
            continue
        daily.append(
            {
                "scan_date": str(scan_date),
                "winner_n": int(len(winners)),
                "control_n": int(len(controls)),
                "winner_median_pct": float(winners[horizon].median()),
                "control_median_pct": float(controls[horizon].median()),
                "difference_pct": float(winners[horizon].median() - controls[horizon].median()),
            }
        )
    differences = [row["difference_pct"] for row in daily]
    return {
        "days": len(daily),
        "median_daily_difference_pct": float(pd.Series(differences).median())
        if differences
        else None,
        "positive_difference_days": float(
            sum(value > 0 for value in differences) / len(differences)
        )
        if differences
        else None,
        "interpretation": "same-date descriptive control comparison; not a randomized control",
    }


def _temporal_predictive_check(frame: pd.DataFrame, horizon: str) -> dict[str, Any]:
    usable = frame.dropna(subset=[horizon, "scan_date"]).sort_values("scan_date").copy()
    dates = sorted(usable["scan_date"].unique())
    split = max(1, int(len(dates) * 0.70))
    periods = {"train": dates[:split], "validation": dates[split:]}
    result: dict[str, Any] = {}
    for name, period_dates in periods.items():
        subset = usable[usable["scan_date"].isin(period_dates)]
        correlations = {}
        for feature in FEATURES:
            if feature not in subset or subset[feature].nunique(dropna=True) < 2:
                continue
            value = subset[[feature, horizon]].corr(method="spearman").iloc[0, 1]
            correlations[feature] = None if pd.isna(value) else float(value)
        result[name] = {"dates": len(period_dates), "rows": len(subset), "spearman": correlations}
    return result


def _feature_selection_test(frame: pd.DataFrame, horizon: str) -> dict[str, Any]:
    usable = frame.dropna(subset=[horizon, "scan_date"]).sort_values("scan_date").copy()
    dates = sorted(usable["scan_date"].unique())
    split = max(1, int(len(dates) * 0.70))
    train = usable[usable["scan_date"].isin(dates[:split])]
    validation = usable[usable["scan_date"].isin(dates[split:])]
    result: dict[str, Any] = {}
    for feature in ("rvol", "atr_pct_real", "gap_pct", "score"):
        if feature not in usable:
            continue
        train_feature = train.dropna(subset=[feature])
        validation_feature = validation.dropna(subset=[feature])
        if train_feature.empty or validation_feature.empty:
            continue
        threshold = float(train_feature[feature].quantile(0.90))
        result[feature] = {"train_threshold": threshold}
        for name, subset in (("train", train_feature), ("validation", validation_feature)):
            selected = subset[subset[feature] >= threshold]
            baseline = subset[horizon]
            result[feature][name] = {
                "selected_n": int(len(selected)),
                "selected_rate": float(len(selected) / len(subset)),
                "selected_median_pct": float(selected[horizon].median())
                if not selected.empty
                else None,
                "baseline_median_pct": float(baseline.median()),
                "median_lift_pct": float(selected[horizon].median() - baseline.median())
                if not selected.empty
                else None,
                "selected_positive_rate": float((selected[horizon] > 0).mean())
                if not selected.empty
                else None,
                "baseline_positive_rate": float((baseline > 0).mean()),
            }
    return result


def _sector_summary(frame: pd.DataFrame, root: Path, horizon: str) -> dict[str, Any]:
    path = root / "data" / "sector_cache.json"
    try:
        sectors = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        sectors = {}
    usable = frame.dropna(subset=[horizon]).copy()
    usable["sector"] = usable["symbol"].map(sectors).fillna("Unknown")
    usable["winner"] = usable[horizon] >= usable[horizon].quantile(0.90)
    table = usable.groupby("sector", observed=True).agg(
        rows=(horizon, "size"), winners=("winner", "sum")
    )
    table["winner_rate"] = table["winners"] / table["rows"]
    return {
        "coverage": float((usable["sector"] != "Unknown").mean()),
        "groups": {
            str(index): {key: float(value) for key, value in row.items()}
            for index, row in table.sort_values("winner_rate", ascending=False).head(20).iterrows()
        },
    }


def _benchmark_summary(frame: pd.DataFrame, root: Path, horizon: str) -> dict[str, Any]:
    cache_dir = root / "data" / "price_cache"
    usable = frame.dropna(subset=[horizon]).copy()
    results = {}
    for benchmark in ("SPY", "IWM"):
        bars = _load_bars(cache_dir, benchmark)
        closes = {str(bar["date"]): float(bar["close"]) for bar in bars}
        dates = list(closes)
        returns = usable["scan_date"].map(
            lambda scan_date: (
                (closes[dates[index + HORIZON_DAYS[horizon]]] / closes[dates[index]] - 1.0) * 100.0
                if (
                    index := next(
                        (i for i, date in enumerate(dates) if date >= str(scan_date)), None
                    )
                )
                is not None
                and index + HORIZON_DAYS[horizon] < len(dates)
                and closes[dates[index]] > 0
                else None
            )
        )
        excess = usable[horizon] - returns
        winner_excess = excess[usable[horizon] >= usable[horizon].quantile(0.90)].dropna()
        all_excess = excess.dropna()
        results[benchmark] = {
            "coverage": float(returns.notna().mean()),
            "winner_excess_median_pct": float(winner_excess.median())
            if not winner_excess.empty
            else None,
            "all_excess_median_pct": float(all_excess.median()) if not all_excess.empty else None,
        }
    return results


def _quintile_rates(frame: pd.DataFrame, horizon: str) -> dict[str, dict[str, float]]:
    usable = frame.dropna(subset=[horizon]).copy()
    usable["winner"] = usable[horizon] >= usable[horizon].quantile(0.90)
    result: dict[str, dict[str, float]] = {}
    for column in ("rvol", "atr_pct_real", "gap_pct", "score"):
        if column not in usable or usable[column].nunique(dropna=True) < 2:
            continue
        bucket = pd.qcut(usable[column], 5, duplicates="drop")
        rates = usable.groupby(bucket, observed=True)["winner"].mean()
        result[column] = {str(index): float(value) for index, value in rates.items()}
    return result


def attribution_data_inventory(root: Path) -> dict[str, Any]:
    data = root / "data"
    news_files = (
        sorted((data / "news_cache").glob("*.json")) if (data / "news_cache").exists() else []
    )
    news_records = 0
    timestamped_event_records = 0
    for path in news_files:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        records = value if isinstance(value, list) else [value]
        news_records += len(records)
        timestamped_event_records += sum(
            isinstance(record, dict) and {"timestamp", "headline"} <= set(record)
            for record in records
        )
    return {
        "sector_fields": False,
        "benchmark_fields": False,
        "event_timestamp_headline_records": timestamped_event_records,
        "news_cache_files": len(news_files),
        "news_cache_records": news_records,
        "event_attribution_ready": timestamped_event_records > 0,
        "note": "Sentiment/date cache is not timestamped headline or event attribution data.",
    }


def build_report(frame: pd.DataFrame, *, source: Path, root: Path) -> dict[str, Any]:
    return {
        "study": "winner_anatomy_2026_08_11",
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "exploratory_research_only",
        "production_change": False,
        "source": str(source),
        "source_date_min": str(frame["scan_date"].min()),
        "source_date_max": str(frame["scan_date"].max()),
        "rows": int(len(frame)),
        "symbols": int(frame["symbol"].nunique()),
        "dates": int(frame["scan_date"].nunique()),
        "profiles": {horizon: _profile(frame, horizon, 0.90) for horizon in HORIZONS},
        "same_date_controls": {
            horizon: _same_date_controls(frame, horizon) for horizon in HORIZONS
        },
        "temporal_predictive_check": {
            horizon: _temporal_predictive_check(frame, horizon) for horizon in HORIZONS
        },
        "pre_scan_feature_selection": {
            horizon: _feature_selection_test(frame, horizon) for horizon in HORIZONS
        },
        "sector_summary": {horizon: _sector_summary(frame, root, horizon) for horizon in HORIZONS},
        "benchmark_summary": {
            horizon: _benchmark_summary(frame, root, horizon) for horizon in HORIZONS
        },
        "quintile_winner_rates": {horizon: _quintile_rates(frame, horizon) for horizon in HORIZONS},
        "attribution_inventory": attribution_data_inventory(root),
        "conclusion": (
            "High-RVOL and high-ATR characteristics are exploratory commonality candidates; "
            "event cause, market/sector decomposition and predictive value remain untested."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--out", type=Path, default=Path("data/backtest_out/winner_anatomy_2026-08-11.json")
    )
    args = parser.parse_args()
    result = build_report(load_export(args.csv), source=args.csv, root=args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        json.dumps({"study": result["study"], "rows": result["rows"], "symbols": result["symbols"]})
    )


if __name__ == "__main__":
    main()
