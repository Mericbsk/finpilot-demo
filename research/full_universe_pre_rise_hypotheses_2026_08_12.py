"""Full-universe exploratory test of pre-rise feature hypotheses.

Intraday path features are not available for the full universe. This study
therefore uses daily pre-scan proxies and labels them separately from the
intraday study.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

HORIZONS = ("c2c_1d", "c2c_5d")
COST_PCT = 0.55
FEATURES = (
    "daily_close_location",
    "daily_trend_consistency_5d",
    "daily_range_expansion_ratio",
    "daily_relative_strength_5d_spy",
    "daily_relative_strength_5d_iwm",
    "daily_relative_strength_5d_sector",
)
COMBINATION = "daily_close_location>=q70 AND daily_trend_consistency_5d>=q70 AND daily_relative_strength_5d_spy>=q70 AND daily_range_expansion_ratio<=q80"
COMBINATION_FEATURES = (
    "daily_close_location",
    "daily_trend_consistency_5d",
    "daily_relative_strength_5d_spy",
    "daily_range_expansion_ratio",
)
INFERENCE_ITERATIONS = 2000


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if pd.notna(number) else None


def load_daily_cache(cache_dir: Path) -> dict[str, list[dict[str, Any]]]:
    result = {}
    for path in cache_dir.glob("*.json"):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        bars = [
            bar
            for bar in raw
            if isinstance(bar, dict)
            and bar.get("date")
            and all(
                _number(bar.get(field)) is not None for field in ("open", "high", "low", "close")
            )
        ]
        result[path.stem] = sorted(bars, key=lambda bar: str(bar["date"]))
    return result


def _prior_bars(bars: list[dict[str, Any]], scan_date: str) -> list[dict[str, Any]]:
    return [bar for bar in bars if str(bar["date"]) < scan_date]


def _prior_return(bars: list[dict[str, Any]], scan_date: str) -> float | None:
    eligible = _prior_bars(bars, scan_date)
    if len(eligible) < 6:
        return None
    start = _number(eligible[-6]["close"])
    end = _number(eligible[-1]["close"])
    return (end / start - 1.0) * 100.0 if start and end and start > 0 else None


def daily_path_features(
    bars: list[dict[str, Any]],
    scan_date: str,
    spy_bars: list[dict[str, Any]],
    iwm_bars: list[dict[str, Any]],
    sector_bars: list[dict[str, Any]] | None = None,
    stock_return: float | None = None,
    spy_return: float | None = None,
    iwm_return: float | None = None,
    sector_return: float | None = None,
) -> dict[str, float] | None:
    eligible = _prior_bars(bars, scan_date)
    if len(eligible) < 11:
        return None
    latest = eligible[-1]
    latest_high = float(latest["high"])
    latest_low = float(latest["low"])
    latest_close = float(latest["close"])
    latest_range = latest_high - latest_low
    recent = eligible[-5:]
    previous = eligible[-10:-5]
    recent_ranges = [float(bar["high"]) - float(bar["low"]) for bar in recent]
    previous_ranges = [float(bar["high"]) - float(bar["low"]) for bar in previous]
    previous_mean_range = sum(previous_ranges) / len(previous_ranges)
    closes = [float(bar["close"]) for bar in eligible[-6:]]
    stock_return = _prior_return(bars, scan_date) if stock_return is None else stock_return
    spy_return = _prior_return(spy_bars, scan_date) if spy_return is None else spy_return
    iwm_return = _prior_return(iwm_bars, scan_date) if iwm_return is None else iwm_return
    sector_return = (
        _prior_return(sector_bars, scan_date)
        if sector_bars and sector_return is None
        else sector_return
    )
    return {
        "daily_close_location": (latest_close - latest_low) / latest_range
        if latest_range > 0
        else 0.5,
        "daily_trend_consistency_5d": sum(
            current >= previous for previous, current in zip(closes, closes[1:], strict=False)
        )
        / 5.0,
        "daily_range_expansion_ratio": (sum(recent_ranges) / len(recent_ranges))
        / previous_mean_range
        if previous_mean_range > 0
        else 0.0,
        "daily_relative_strength_5d_spy": stock_return - spy_return
        if stock_return is not None and spy_return is not None
        else None,
        "daily_relative_strength_5d_iwm": stock_return - iwm_return
        if stock_return is not None and iwm_return is not None
        else None,
        "daily_relative_strength_5d_sector": stock_return - sector_return
        if stock_return is not None and sector_return is not None
        else None,
    }


def load_sector_map(path: Path) -> dict[str, str]:
    try:
        table = pd.read_csv(path)
    except (OSError, ValueError):
        return {}
    if not {"symbol", "etf"} <= set(table.columns):
        return {}
    return dict(zip(table["symbol"].astype(str), table["etf"].astype(str), strict=False))


def build_feature_frame(
    source: Path, cache_dir: Path, sector_map_path: Path
) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = pd.read_csv(source, low_memory=False)
    for column in HORIZONS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    daily = load_daily_cache(cache_dir)
    sector_map = load_sector_map(sector_map_path)
    spy_bars = daily.get("SPY", [])
    iwm_bars = daily.get("IWM", [])
    feature_cache: dict[tuple[str, str], dict[str, float] | None] = {}
    return_cache: dict[tuple[str, str], float | None] = {}

    def cached_return(symbol: str, scan_date: str) -> float | None:
        key = (symbol, scan_date)
        if key not in return_cache:
            return_cache[key] = _prior_return(daily.get(symbol, []), scan_date)
        return return_cache[key]

    rows = []
    for row in frame.to_dict("records"):
        key = (str(row["symbol"]), str(row["scan_date"]))
        if key not in feature_cache:
            sector_bars = daily.get(sector_map.get(key[0], ""))
            feature_cache[key] = daily_path_features(
                daily.get(key[0], []),
                key[1],
                spy_bars,
                iwm_bars,
                sector_bars,
                cached_return(key[0], key[1]),
                cached_return("SPY", key[1]),
                cached_return("IWM", key[1]),
                cached_return(sector_map.get(key[0], ""), key[1]) if sector_bars else None,
            )
        features = feature_cache[key]
        if features is None:
            continue
        row.update(features)
        rows.append(row)
    result = pd.DataFrame(rows)
    inventory = {
        "source_rows": int(len(frame)),
        "source_symbols": int(frame["symbol"].nunique()),
        "source_dates": int(frame["scan_date"].nunique()),
        "daily_cache_symbols": len(daily),
        "resolved_rows": int(len(result)),
        "resolved_symbols": int(result["symbol"].nunique()),
        "resolved_dates": int(result["scan_date"].nunique()),
        "sector_feature_coverage": float(
            result["daily_relative_strength_5d_sector"].notna().mean()
        ),
        "intraday_feature_coverage": "not applicable; daily proxy study",
        "pre_scan_rule": "all daily bars have date < scan_date",
        "volume_available": "daily export rvol exists; intraday volume unavailable",
    }
    return result, inventory


def _summary(subset: pd.DataFrame, horizon: str) -> dict[str, float | int | None]:
    outcomes = subset[horizon].dropna()
    return {
        "n": int(len(outcomes)),
        "median_pct": float(outcomes.median()) if not outcomes.empty else None,
        "mean_pct": float(outcomes.mean()) if not outcomes.empty else None,
        "positive_rate": float((outcomes > 0).mean()) if not outcomes.empty else None,
        "cost_adjusted_median_pct": float((outcomes - COST_PCT).median())
        if not outcomes.empty
        else None,
        "bad_rate_below_cost": float((outcomes < -COST_PCT).mean()) if not outcomes.empty else None,
    }


def _split(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list[str], list[str]]:
    dates = sorted(frame["scan_date"].dropna().unique())
    split = max(1, int(len(dates) * 0.70))
    return (
        frame[frame["scan_date"].isin(dates[:split])],
        frame[frame["scan_date"].isin(dates[split:])],
        dates[:split],
        dates[split:],
    )


def feature_selection(frame: pd.DataFrame, horizon: str) -> dict[str, Any]:
    train, validation, train_dates, validation_dates = _split(
        frame.dropna(subset=[horizon, "scan_date"])
    )
    result: dict[str, Any] = {
        "train_dates": len(train_dates),
        "validation_dates": len(validation_dates),
        "features": {},
        "combination": {},
    }
    for feature in FEATURES:
        if feature not in frame:
            continue
        train_feature = train.dropna(subset=[feature])
        validation_feature = validation.dropna(subset=[feature])
        if train_feature.empty or validation_feature.empty:
            continue
        threshold = float(train_feature[feature].quantile(0.90))
        selected_train = train_feature[train_feature[feature] >= threshold]
        selected_validation = validation_feature[validation_feature[feature] >= threshold]
        result["features"][feature] = {
            "train_threshold_q90": threshold,
            "train_selected": _summary(selected_train, horizon),
            "train_baseline": _summary(train_feature, horizon),
            "validation_selected": _summary(selected_validation, horizon),
            "validation_baseline": _summary(validation_feature, horizon),
            "validation_median_lift_pct": float(
                selected_validation[horizon].median() - validation_feature[horizon].median()
            )
            if not selected_validation.empty
            else None,
        }
    combo = _combination_selection(train, validation, horizon)
    result["combination"] = combo
    return result


def _combination_mask(frame: pd.DataFrame, thresholds: dict[str, float]) -> pd.Series:
    return (
        (frame["daily_close_location"] >= thresholds["daily_close_location"])
        & (frame["daily_trend_consistency_5d"] >= thresholds["daily_trend_consistency_5d"])
        & (frame["daily_relative_strength_5d_spy"] >= thresholds["daily_relative_strength_5d_spy"])
        & (frame["daily_range_expansion_ratio"] <= thresholds["daily_range_expansion_ratio"])
    )


def _combination_selection(
    train: pd.DataFrame, validation: pd.DataFrame, horizon: str
) -> dict[str, Any]:
    required = [
        "daily_close_location",
        "daily_trend_consistency_5d",
        "daily_relative_strength_5d_spy",
        "daily_range_expansion_ratio",
    ]
    train = train.dropna(subset=required)
    validation = validation.dropna(subset=required)
    if train.empty or validation.empty:
        return {"definition": COMBINATION, "status": "insufficient_data"}
    thresholds = {
        "daily_close_location": float(train["daily_close_location"].quantile(0.70)),
        "daily_trend_consistency_5d": float(train["daily_trend_consistency_5d"].quantile(0.70)),
        "daily_relative_strength_5d_spy": float(
            train["daily_relative_strength_5d_spy"].quantile(0.70)
        ),
        "daily_range_expansion_ratio": float(train["daily_range_expansion_ratio"].quantile(0.80)),
    }
    train_selected = train[_combination_mask(train, thresholds)]
    validation_selected = validation[_combination_mask(validation, thresholds)]
    return {
        "definition": COMBINATION,
        "thresholds_learned_on_train": thresholds,
        "train_selected": _summary(train_selected, horizon),
        "train_baseline": _summary(train, horizon),
        "validation_selected": _summary(validation_selected, horizon),
        "validation_baseline": _summary(validation, horizon),
        "validation_median_lift_pct": float(
            validation_selected[horizon].median() - validation[horizon].median()
        )
        if not validation_selected.empty
        else None,
    }


def _matched_differences(
    frame: pd.DataFrame,
    horizon: str,
    selected_mask: pd.Series,
    matching_features: list[str],
) -> tuple[pd.DataFrame, list[float]]:
    selected = frame[selected_mask]
    controls = frame[~selected_mask]
    if selected.empty or controls.empty:
        return selected, []
    scale = frame[matching_features].std().replace(0, 1)
    differences = []
    for date, selected_group in selected.groupby("scan_date", sort=False):
        control_group = controls[controls["scan_date"] == date]
        if control_group.empty:
            continue
        selected_values = selected_group[matching_features].to_numpy(dtype=float)
        control_values = control_group[matching_features].to_numpy(dtype=float)
        distances = (
            (selected_values[:, None, :] - control_values[None, :, :]) / scale.to_numpy(dtype=float)
        ) ** 2
        nearest = distances.sum(axis=2).argmin(axis=1)
        differences.extend(
            (
                selected_group[horizon].to_numpy(dtype=float)
                - control_group[horizon].to_numpy(dtype=float)[nearest]
            ).tolist()
        )
    return selected, differences


def _paired_inference(differences: list[float], seed: int) -> dict[str, Any]:
    values = np.asarray(differences, dtype=float)
    if values.size == 0:
        return {"status": "insufficient_data"}
    rng = np.random.default_rng(seed)
    bootstrap = np.median(
        rng.choice(values, size=(INFERENCE_ITERATIONS, values.size), replace=True), axis=1
    )
    null_medians = np.median(
        rng.choice(np.abs(values), size=(INFERENCE_ITERATIONS, values.size), replace=True)
        * rng.choice([-1.0, 1.0], size=(INFERENCE_ITERATIONS, values.size)),
        axis=1,
    )
    observed = float(np.median(values))
    return {
        "method": "paired median bootstrap and sign-permutation null",
        "iterations": INFERENCE_ITERATIONS,
        "seed": seed,
        "observed_median_difference_pct": observed,
        "bootstrap_median_ci_95_pct": [
            float(np.quantile(bootstrap, 0.025)),
            float(np.quantile(bootstrap, 0.975)),
        ],
        "null_median_ci_95_pct": [
            float(np.quantile(null_medians, 0.025)),
            float(np.quantile(null_medians, 0.975)),
        ],
        "two_sided_permutation_p_value": float((np.abs(null_medians) >= abs(observed)).sum() + 1)
        / (INFERENCE_ITERATIONS + 1),
        "interpretation": "paired differences are resampled; sign permutation tests a zero-median null; exploratory, not causal",
    }


def _combination_thresholds(frame: pd.DataFrame) -> dict[str, float]:
    return {
        "daily_close_location": frame["daily_close_location"].quantile(0.70),
        "daily_trend_consistency_5d": frame["daily_trend_consistency_5d"].quantile(0.70),
        "daily_relative_strength_5d_spy": frame["daily_relative_strength_5d_spy"].quantile(0.70),
        "daily_range_expansion_ratio": frame["daily_range_expansion_ratio"].quantile(0.80),
    }


def matched_controls(frame: pd.DataFrame, horizon: str) -> dict[str, Any]:
    required = [*COMBINATION_FEATURES, horizon, "scan_date"]
    usable = frame.dropna(subset=required).copy()
    if usable.empty:
        return {"status": "insufficient_data"}
    thresholds = _combination_thresholds(usable)
    selected, differences = _matched_differences(
        usable, horizon, _combination_mask(usable, thresholds), list(thresholds)
    )
    return {
        "selected_n": int(len(selected)),
        "pairs": len(differences),
        "median_difference_pct": float(pd.Series(differences).median()) if differences else None,
        "positive_difference_rate": float(
            sum(value > 0 for value in differences) / len(differences)
        )
        if differences
        else None,
        "interpretation": "same-date nearest standardized-feature control; exploratory, not randomized",
        "inference": _paired_inference(differences, seed=20260812),
    }


def single_feature_matched_controls(frame: pd.DataFrame, horizon: str) -> dict[str, Any]:
    results = {}
    usable_base = frame.dropna(subset=[*COMBINATION_FEATURES, horizon, "scan_date"]).copy()
    for feature in COMBINATION_FEATURES:
        usable = usable_base.dropna(subset=[feature]).copy()
        threshold = (
            usable[feature].quantile(0.80)
            if feature == "daily_range_expansion_ratio"
            else usable[feature].quantile(0.70)
        )
        selected_mask = (
            usable[feature] <= threshold
            if feature == "daily_range_expansion_ratio"
            else usable[feature] >= threshold
        )
        matching_features = [name for name in COMBINATION_FEATURES if name != feature]
        selected, differences = _matched_differences(
            usable, horizon, selected_mask, matching_features
        )
        results[feature] = {
            "selection_rule": f"{'<=' if feature == 'daily_range_expansion_ratio' else '>='} q{80 if feature == 'daily_range_expansion_ratio' else 70}",
            "threshold": float(threshold),
            "selected_n": int(len(selected)),
            "pairs": len(differences),
            "median_difference_pct": float(pd.Series(differences).median())
            if differences
            else None,
            "positive_difference_rate": float(
                sum(value > 0 for value in differences) / len(differences)
            )
            if differences
            else None,
            "matching_features": matching_features,
            "inference": _paired_inference(differences, seed=20260812 + len(results)),
            "interpretation": "single-feature selector; same-date nearest control matched on the other three features; exploratory, not randomized",
        }
    return results


def build_report(frame: pd.DataFrame, inventory: dict[str, Any], source: Path) -> dict[str, Any]:
    return {
        "study": "full_universe_pre_rise_hypotheses_2026_08_12",
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "exploratory_research_only",
        "production_change": False,
        "source": str(source),
        "inventory": inventory,
        "hypotheses": {
            "H1": "Daily close-location proxy, trend consistency and market relative strength carry pre-rise information.",
            "H2": "The pre-registered combination adds information beyond any single proxy.",
            "H3": "ATR/RVOL are treated as context/risk features, not directional alpha features.",
        },
        "horizons": {
            horizon: {
                "feature_selection": feature_selection(frame, horizon),
                "combination_matched_controls": matched_controls(frame, horizon),
                "single_feature_matched_controls": single_feature_matched_controls(frame, horizon),
            }
            for horizon in HORIZONS
        },
        "gates": {
            "daily_proxy_is_intraday_equivalent": False,
            "intraday_volume": "BLOCKED_NO_INTRADAY_VOLUME",
            "event_attribution": "BLOCKED_NO_TIMESTAMPED_HEADLINES",
            "point_in_time_snapshot": "BLOCKED_NO_IMMUTABLE_PRIOR_CACHE",
            "locked_oos": "NOT_OPENED",
            "production_promotion": "NOT_ALLOWED",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--source", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/backtest_out/full_universe_pre_rise_hypotheses_2026-08-12.json"),
    )
    args = parser.parse_args()
    frame, inventory = build_feature_frame(
        args.source,
        args.root / "data" / "price_cache",
        args.root / "data" / "backtest_out" / "sector_map_full.csv",
    )
    report = build_report(frame, inventory, args.source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "study": report["study"],
                "resolved_rows": inventory["resolved_rows"],
                "resolved_dates": inventory["resolved_dates"],
            }
        )
    )


if __name__ == "__main__":
    main()
