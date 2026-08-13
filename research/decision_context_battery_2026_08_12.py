"""Research-only event, state and similar-case context battery.

This module deliberately does not produce a trading rule.  It evaluates
whether descriptive market states and nearest historical cases provide more
useful forward context than a constant base-rate estimate on a chronological
validation split.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

FEATURES = ("gap_pct", "rvol", "atr_pct_real", "dist_52w_high", "finpilot_score")
OUTCOMES = ("c2c_1d", "c2c_5d")


def _numeric_frame(frame: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    result = frame.loc[:, columns].apply(pd.to_numeric, errors="coerce")
    return result.replace([np.inf, -np.inf], np.nan)


def _quantile_thresholds(train: pd.DataFrame) -> dict[str, dict[str, float]]:
    values = _numeric_frame(train, FEATURES)
    thresholds: dict[str, dict[str, float]] = {}
    for feature in FEATURES:
        series = values[feature].dropna()
        thresholds[feature] = {
            "q10": float(series.quantile(0.10)),
            "q25": float(series.quantile(0.25)),
            "q75": float(series.quantile(0.75)),
            "q90": float(series.quantile(0.90)),
        }
    return thresholds


def classify_states(frame: pd.DataFrame, thresholds: dict[str, dict[str, float]]) -> pd.Series:
    values = _numeric_frame(frame, FEATURES)
    states = pd.Series("ordinary", index=frame.index, dtype="object")
    gap = values["gap_pct"]
    atr = values["atr_pct_real"]
    rvol = values["rvol"]
    extension = values["dist_52w_high"]

    states.loc[gap <= thresholds["gap_pct"]["q10"]] = "gap_down"
    states.loc[gap >= thresholds["gap_pct"]["q90"]] = "gap_up"
    ordinary = states == "ordinary"
    states.loc[
        ordinary & (atr >= thresholds["atr_pct_real"]["q90"]) & (rvol >= thresholds["rvol"]["q75"])
    ] = "high_activity"
    states.loc[
        ordinary
        & (extension >= thresholds["dist_52w_high"]["q90"])
        & (gap >= thresholds["gap_pct"]["q75"])
    ] = "extended_up"
    return states


def _state_summary(frame: pd.DataFrame, states: pd.Series) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for state, group in frame.assign(_state=states).groupby("_state", sort=True):
        result[str(state)] = {
            "n": int(len(group)),
            "dates": int(group["scan_date"].nunique()),
            "c2c_1d_median_pct": float(group["c2c_1d"].median()),
            "c2c_5d_median_pct": float(group["c2c_5d"].median()),
            "c2c_5d_positive_rate": float((group["c2c_5d"] > 0).mean()),
            "c2c_5d_material_move_rate": float((group["c2c_5d"].abs() >= 3).mean()),
        }
    return result


def _standardize(
    train: pd.DataFrame, values: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    train_values = _numeric_frame(train, FEATURES)
    value_values = _numeric_frame(values, FEATURES)
    medians = train_values.median()
    spreads = (train_values.quantile(0.75) - train_values.quantile(0.25)).replace(0, 1.0)
    train_matrix = ((train_values.fillna(medians) - medians) / spreads).to_numpy(dtype=float)
    value_matrix = ((value_values.fillna(medians) - medians) / spreads).to_numpy(dtype=float)
    return train_matrix, value_matrix, list(FEATURES)


def similar_case_predictions(
    train: pd.DataFrame, validation: pd.DataFrame, k: int = 25
) -> pd.DataFrame:
    train_matrix, validation_matrix, _ = _standardize(train, validation)
    train_outcomes = train.loc[:, OUTCOMES].to_numpy(dtype=float)
    rows: list[dict[str, float]] = []
    neighbour_count = min(k, len(train))
    for row in validation_matrix:
        distances = np.sqrt(((train_matrix - row) ** 2).mean(axis=1))
        nearest = np.argpartition(distances, neighbour_count - 1)[:neighbour_count]
        outcomes = train_outcomes[nearest]
        rows.append(
            {
                "similar_case_median_1d": float(np.median(outcomes[:, 0])),
                "similar_case_median_5d": float(np.median(outcomes[:, 1])),
                "similar_case_dispersion_5d": float(
                    np.percentile(outcomes[:, 1], 75) - np.percentile(outcomes[:, 1], 25)
                ),
                "similar_case_positive_rate_5d": float((outcomes[:, 1] > 0).mean()),
            }
        )
    return pd.DataFrame(rows, index=validation.index)


def _mae(actual: pd.Series, prediction: pd.Series) -> float:
    return float(np.abs(actual.to_numpy(dtype=float) - prediction.to_numpy(dtype=float)).mean())


def _date_block_median(frame: pd.DataFrame, column: str) -> float:
    daily = frame.groupby("scan_date")[column].median()
    return float(daily.median()) if len(daily) else float("nan")


def run_battery(csv_path: Path, k: int = 25) -> dict[str, Any]:
    raw = pd.read_csv(csv_path, low_memory=False)
    required = {"scan_date", *FEATURES, *OUTCOMES}
    missing = sorted(required.difference(raw.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    frame = raw.copy()
    frame["scan_date"] = pd.to_datetime(frame["scan_date"], errors="coerce").dt.date
    frame = frame.dropna(subset=["scan_date"]).drop_duplicates(["symbol", "scan_date"], keep="last")
    numeric = _numeric_frame(frame, (*FEATURES, *OUTCOMES))
    frame.loc[:, numeric.columns] = numeric
    frame = (
        frame.dropna(subset=list(OUTCOMES))
        .sort_values(["scan_date", "symbol"])
        .reset_index(drop=True)
    )
    dates = sorted(frame["scan_date"].unique())
    split = max(1, int(len(dates) * 0.70))
    train_dates = set(dates[:split])
    train = frame[frame["scan_date"].isin(train_dates)].copy()
    validation = frame[~frame["scan_date"].isin(train_dates)].copy()
    thresholds = _quantile_thresholds(train)
    train_states = classify_states(train, thresholds)
    validation_states = classify_states(validation, thresholds)
    state_frame = pd.concat(
        [train.assign(_state=train_states), validation.assign(_state=validation_states)]
    )

    predictions = similar_case_predictions(train, validation, k=k)
    validation = validation.join(predictions)
    base_1d = float(train["c2c_1d"].median())
    base_5d = float(train["c2c_5d"].median())
    validation["base_median_1d"] = base_1d
    validation["base_median_5d"] = base_5d
    validation["similar_case_abs_error_1d"] = (
        validation["c2c_1d"] - validation["similar_case_median_1d"]
    ).abs()
    validation["base_abs_error_1d"] = (validation["c2c_1d"] - base_1d).abs()
    validation["similar_case_abs_error_5d"] = (
        validation["c2c_5d"] - validation["similar_case_median_5d"]
    ).abs()
    validation["base_abs_error_5d"] = (validation["c2c_5d"] - base_5d).abs()
    validation["evidence_score"] = (
        1.0
        / (1.0 + validation["similar_case_dispersion_5d"].clip(lower=0))
        * validation["similar_case_positive_rate_5d"].sub(0.5).abs().mul(2).add(0.5)
    )
    validation["abstain"] = validation["evidence_score"] < validation["evidence_score"].quantile(
        0.25
    )

    state_validation = _state_summary(validation, validation_states)
    state_train = _state_summary(train, train_states)
    active = validation[~validation["abstain"]]
    return {
        "status": "exploratory",
        "scope": "research_only",
        "production_change": False,
        "source_csv": str(csv_path),
        "rows": {
            "raw": int(len(raw)),
            "canonical": int(len(frame)),
            "train": int(len(train)),
            "validation": int(len(validation)),
        },
        "dates": {
            "total": int(len(dates)),
            "train": int(len(train_dates)),
            "validation": int(len(dates) - len(train_dates)),
        },
        "protocol": {
            "primary_question": "Do descriptive states and similar historical cases improve validation context versus a train-only base rate?",
            "features": list(FEATURES),
            "outcomes": list(OUTCOMES),
            "nearest_neighbours": k,
            "thresholds_train_only": thresholds,
            "benchmark_context": "unavailable",
            "execution_cost": "scenario not observed; no tradeability claim",
            "locked_oos": "not_opened",
        },
        "state_summary": {"train": state_train, "validation": state_validation},
        "similar_case_validation": {
            "base_mae_1d_pct": _mae(validation["c2c_1d"], validation["base_median_1d"]),
            "similar_case_mae_1d_pct": _mae(
                validation["c2c_1d"], validation["similar_case_median_1d"]
            ),
            "base_mae_5d_pct": _mae(validation["c2c_5d"], validation["base_median_5d"]),
            "similar_case_mae_5d_pct": _mae(
                validation["c2c_5d"], validation["similar_case_median_5d"]
            ),
            "date_block_median_error_5d_base_pct": _date_block_median(
                validation.assign(error=validation["base_abs_error_5d"]), "error"
            ),
            "date_block_median_error_5d_similar_pct": _date_block_median(
                validation.assign(error=validation["similar_case_abs_error_5d"]), "error"
            ),
        },
        "abstention_validation": {
            "abstain_rate": float(validation["abstain"].mean()),
            "active_rows": int(len(active)),
            "active_5d_median_pct": float(active["c2c_5d"].median()) if len(active) else None,
            "abstained_5d_median_pct": float(validation[validation["abstain"]]["c2c_5d"].median())
            if validation["abstain"].any()
            else None,
            "interpretation": "descriptive selection diagnostic, not a trading rule",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument("--k", type=int, default=25)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/backtest_out/decision_context_battery_2026-08-12.json"),
    )
    args = parser.parse_args()
    result = run_battery(args.csv, k=args.k)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                "rows": result["rows"],
                "similar_case_validation": result["similar_case_validation"],
                "abstention_validation": result["abstention_validation"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
