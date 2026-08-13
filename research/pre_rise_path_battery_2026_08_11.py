"""Leakage-controlled exploratory search for pre-rise price-path features."""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

HORIZONS = ("c2c_1d", "c2c_5d")
COST_PCT = 0.55
FILE_PATTERN = re.compile(r"^(?P<symbol>[^_]+)_(?P<start>\d{4}-\d{2}-\d{2})_")
PATH_FEATURES = (
    "path_first_return_pct",
    "path_range_expansion_ratio",
    "path_close_location",
    "path_reversal_pct",
    "path_trend_consistency",
    "relative_strength_5d_spy",
    "relative_strength_5d_iwm",
    "relative_strength_5d_sector",
)


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if pd.notna(result) else None


def _load_intraday(path: Path, scan_ts: str) -> list[dict[str, float | str]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    cutoff = pd.Timestamp(scan_ts).tz_localize("UTC")
    bars = []
    for item in raw if isinstance(raw, list) else []:
        values = item.get("value") if isinstance(item, dict) else item
        if not isinstance(values, list) or len(values) < 5:
            continue
        try:
            timestamp = pd.Timestamp(values[0])
            timestamp = (
                timestamp.tz_localize("UTC")
                if timestamp.tzinfo is None
                else timestamp.tz_convert("UTC")
            )
        except (TypeError, ValueError):
            continue
        if timestamp > cutoff:
            continue
        numbers = [_number(value) for value in values[1:5]]
        if any(value is None for value in numbers):
            continue
        bars.append(
            {
                "timestamp": timestamp.isoformat(),
                "open": numbers[0],
                "high": numbers[1],
                "low": numbers[2],
                "close": numbers[3],
            }
        )
    return sorted(bars, key=lambda bar: str(bar["timestamp"]))


def compute_path_features(bars: list[dict[str, float | str]]) -> dict[str, float] | None:
    if len(bars) < 4:
        return None
    midpoint = max(2, len(bars) // 2)
    first = bars[:midpoint]
    second = bars[midpoint:]
    start = float(first[0]["open"])
    last = float(bars[-1]["close"])
    if start <= 0:
        return None
    first_range = (
        (max(float(bar["high"]) for bar in first) - min(float(bar["low"]) for bar in first))
        / start
        * 100.0
    )
    second_range = (
        (max(float(bar["high"]) for bar in second) - min(float(bar["low"]) for bar in second))
        / start
        * 100.0
    )
    total_range = max(float(bar["high"]) for bar in bars) - min(float(bar["low"]) for bar in bars)
    gains = [float(bar["close"]) / start - 1.0 for bar in bars]
    return {
        "path_first_return_pct": (float(first[-1]["close"]) / start - 1.0) * 100.0,
        "path_range_expansion_ratio": second_range / first_range if first_range > 0 else 0.0,
        "path_close_location": (last - min(float(bar["low"]) for bar in bars)) / total_range
        if total_range > 0
        else 0.5,
        "path_reversal_pct": (max(gains) - gains[-1]) * 100.0,
        "path_trend_consistency": sum(
            current >= previous for previous, current in zip(gains, gains[1:], strict=False)
        )
        / max(1, len(gains) - 1),
    }


def _load_daily(cache_dir: Path, symbol: str) -> list[dict[str, Any]]:
    try:
        raw = json.loads((cache_dir / f"{symbol}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return sorted(
        [
            bar
            for bar in raw
            if isinstance(bar, dict) and bar.get("date") and _number(bar.get("close"))
        ],
        key=lambda bar: str(bar["date"]),
    )


def _relative_strength(
    cache_dir: Path, symbol: str, scan_date: str, benchmark: str
) -> float | None:
    bars = _load_daily(cache_dir, symbol)
    benchmark_bars = _load_daily(cache_dir, benchmark)

    def prior_return(series: list[dict[str, Any]]) -> float | None:
        eligible = [bar for bar in series if str(bar["date"]) < scan_date]
        if len(eligible) < 6:
            return None
        start = _number(eligible[-6].get("close"))
        end = _number(eligible[-1].get("close"))
        return (end / start - 1.0) * 100.0 if start and end and start > 0 else None

    stock = prior_return(bars)
    market = prior_return(benchmark_bars)
    return stock - market if stock is not None and market is not None else None


def _load_sector_etfs(path: Path) -> dict[str, str]:
    try:
        table = pd.read_csv(path)
    except (OSError, ValueError):
        return {}
    if not {"symbol", "etf"} <= set(table.columns):
        return {}
    return dict(zip(table["symbol"].astype(str), table["etf"].astype(str), strict=False))


def load_rows(
    csv_path: Path, intraday_dir: Path, daily_dir: Path, root: Path
) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = pd.read_csv(csv_path, low_memory=False)
    for column in (*HORIZONS, "atr_pct_real", "rvol", "gap_pct", "price"):
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.drop_duplicates(subset=["symbol", "scan_date"], keep="first").copy()
    files = {}
    sector_etfs = _load_sector_etfs(root / "data" / "backtest_out" / "sector_map_full.csv")
    for path in intraday_dir.glob("*.json"):
        match = FILE_PATTERN.match(path.name)
        if match:
            files[(match.group("symbol"), match.group("start"))] = path
    records = []
    for row in frame.to_dict("records"):
        path = files.get((str(row["symbol"]), str(row["scan_date"])))
        if path is None:
            continue
        features = compute_path_features(_load_intraday(path, str(row["scan_ts"])))
        if features is None:
            continue
        row.update(features)
        row["relative_strength_5d_spy"] = _relative_strength(
            daily_dir, str(row["symbol"]), str(row["scan_date"]), "SPY"
        )
        row["relative_strength_5d_iwm"] = _relative_strength(
            daily_dir, str(row["symbol"]), str(row["scan_date"]), "IWM"
        )
        sector_etf = sector_etfs.get(str(row["symbol"]))
        row["relative_strength_5d_sector"] = (
            _relative_strength(daily_dir, str(row["symbol"]), str(row["scan_date"]), sector_etf)
            if sector_etf
            else None
        )
        records.append(row)
    result = pd.DataFrame(records)
    return result, {
        "source_rows": int(len(frame)),
        "intraday_files": len(files),
        "resolved_rows": int(len(result)),
        "resolved_symbols": int(result["symbol"].nunique()) if not result.empty else 0,
        "resolved_dates": int(result["scan_date"].nunique()) if not result.empty else 0,
        "pre_scan_cutoff": "bars timestamp <= scan_ts; scan_ts interpreted as UTC",
        "volume_available": False,
        "sector_coverage": float(result["relative_strength_5d_sector"].notna().mean())
        if not result.empty
        else 0.0,
        "event_attribution_ready": False,
        "root": str(root),
    }


def _summary(subset: pd.DataFrame, horizon: str) -> dict[str, float | int | None]:
    if subset.empty:
        return {
            "n": 0,
            "median_pct": None,
            "positive_rate": None,
            "cost_adjusted_median_pct": None,
            "bad_rate": None,
        }
    outcomes = subset[horizon].dropna()
    return {
        "n": int(len(outcomes)),
        "median_pct": float(outcomes.median()) if not outcomes.empty else None,
        "positive_rate": float((outcomes > 0).mean()) if not outcomes.empty else None,
        "cost_adjusted_median_pct": float((outcomes - COST_PCT).median())
        if not outcomes.empty
        else None,
        "bad_rate": float((outcomes < -COST_PCT).mean()) if not outcomes.empty else None,
    }


def temporal_feature_tests(frame: pd.DataFrame, horizon: str) -> dict[str, Any]:
    usable = frame.dropna(subset=[horizon, "scan_date"]).sort_values("scan_date")
    dates = sorted(usable["scan_date"].unique())
    split = max(1, int(len(dates) * 0.70))
    train = usable[usable["scan_date"].isin(dates[:split])]
    validation = usable[usable["scan_date"].isin(dates[split:])]
    output = {}
    for feature in PATH_FEATURES:
        if feature not in usable:
            continue
        train_feature = train.dropna(subset=[feature])
        validation_feature = validation.dropna(subset=[feature])
        if train_feature.empty or validation_feature.empty:
            continue
        threshold = float(train_feature[feature].quantile(0.90))
        selected_train = train_feature[train_feature[feature] >= threshold]
        selected_validation = validation_feature[validation_feature[feature] >= threshold]
        output[feature] = {
            "threshold_train": threshold,
            "train_selected": _summary(selected_train, horizon),
            "train_baseline": _summary(train_feature, horizon),
            "validation_selected": _summary(selected_validation, horizon),
            "validation_baseline": _summary(validation_feature, horizon),
            "validation_lift_pct": float(
                selected_validation[horizon].median() - validation_feature[horizon].median()
            )
            if not selected_validation.empty
            else None,
        }
    return {
        "train_dates": len(dates[:split]),
        "validation_dates": len(dates[split:]),
        "features": output,
    }


def matched_controls(frame: pd.DataFrame, horizon: str) -> dict[str, Any]:
    usable = frame.dropna(subset=[horizon, "scan_date"]).copy()
    results = {}
    for feature in PATH_FEATURES:
        sub = usable.dropna(subset=[feature]).copy()
        if sub.empty:
            continue
        threshold = sub[feature].quantile(0.90)
        selected = sub[sub[feature] >= threshold]
        controls = sub[sub[feature] < threshold]
        pairs = []
        for _, row in selected.iterrows():
            pool = controls[controls["scan_date"] == row["scan_date"]]
            if pool.empty:
                continue
            candidate = pool.iloc[(pool[feature] - row[feature]).abs().argmin()]
            pairs.append(float(row[horizon] - candidate[horizon]))
        results[feature] = {
            "pairs": len(pairs),
            "median_difference_pct": float(pd.Series(pairs).median()) if pairs else None,
            "positive_difference_rate": float(sum(value > 0 for value in pairs) / len(pairs))
            if pairs
            else None,
            "interpretation": "same-date nearest-feature control; exploratory, not randomized",
        }
    return results


def build_report(frame: pd.DataFrame, inventory: dict[str, Any], source: Path) -> dict[str, Any]:
    return {
        "study": "pre_rise_path_battery_2026_08_11",
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "exploratory_research_only",
        "production_change": False,
        "source": str(source),
        "inventory": inventory,
        "features": list(PATH_FEATURES),
        "horizons": {
            horizon: {
                "temporal": temporal_feature_tests(frame, horizon),
                "matched_controls": matched_controls(frame, horizon),
            }
            for horizon in HORIZONS
        },
        "data_gates": {
            "intraday_volume": "BLOCKED_NO_VOLUME",
            "event_attribution": "BLOCKED_NO_TIMESTAMPED_HEADLINES",
            "sector_relative_strength": "EXPLORATORY_LOW_COVERAGE_UNVERIFIED",
            "locked_oos": "NOT_OPENED",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument(
        "--out", type=Path, default=Path("data/backtest_out/pre_rise_path_battery_2026-08-11.json")
    )
    args = parser.parse_args()
    frame, inventory = load_rows(
        args.csv,
        args.root / "data" / "intraday_cache",
        args.root / "data" / "price_cache",
        args.root,
    )
    result = build_report(frame, inventory, args.csv)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "study": result["study"],
                "resolved_rows": inventory["resolved_rows"],
                "resolved_dates": inventory["resolved_dates"],
            }
        )
    )


if __name__ == "__main__":
    main()
