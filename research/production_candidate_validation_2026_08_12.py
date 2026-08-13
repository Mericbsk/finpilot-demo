"""Research-only validation of the four nearest production candidates.

The runner deliberately stops at diagnostics. It does not change scanner,
score, risk, publication, broker, paper or live behavior.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from research.decision_context_battery_2026_08_12 import _numeric_frame

REQUIRED = ("scan_date", "entry_ok", "atr_pct_real", "gap_pct", "rvol", "c2c_5d")


def _summary(values: list[float] | np.ndarray) -> dict[str, Any]:
    array = np.asarray(values, dtype=float)
    array = array[np.isfinite(array)]
    if not len(array):
        return {
            "n_dates": 0,
            "median_daily_pct": None,
            "mean_daily_pct": None,
            "max_drawdown_pct": None,
            "daily_sharpe": None,
            "cvar5_pct": None,
        }
    equity = np.cumprod(1.0 + array / 100.0)
    drawdown = equity / np.maximum.accumulate(equity) - 1.0
    tail_count = max(1, int(len(array) * 0.05))
    return {
        "n_dates": int(len(array)),
        "median_daily_pct": float(np.median(array)),
        "mean_daily_pct": float(np.mean(array)),
        "max_drawdown_pct": float(np.min(drawdown) * 100.0),
        "daily_sharpe": float(np.mean(array) / np.std(array)) if np.std(array) else None,
        "cvar5_pct": float(np.sort(array)[:tail_count].mean()),
    }


def _weighted_daily(group: pd.DataFrame, weights: np.ndarray | None) -> float | None:
    values = group["c2c_5d"].to_numpy(dtype=float)
    mask = np.isfinite(values) & np.isfinite(group["atr_pct_real"].to_numpy(dtype=float))
    if not mask.any():
        return None
    if weights is None:
        return float(values[mask].mean())
    return float(np.average(values[mask], weights=weights[mask]))


def _portfolio_schemes(
    frame: pd.DataFrame, seed: int = 20260812, random_runs: int = 100
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    groups = {
        "eligible": frame[frame["entry_ok"]],
        "rejected": frame[~frame["entry_ok"]],
    }
    daily: dict[str, dict[str, list[float]]] = {
        name: {"equal": [], "atr_parity": []} for name in groups
    }
    random_daily: dict[str, list[list[float]]] = {"equal": [], "atr_parity": []}
    for _, universe in frame.groupby("scan_date", sort=True):
        eligible_count = int(universe["entry_ok"].sum())
        dated_groups = {
            "eligible": universe[universe["entry_ok"]],
            "rejected": universe[~universe["entry_ok"]],
        }
        for name, group in dated_groups.items():
            if group.empty:
                continue
            weights = 1.0 / group["atr_pct_real"].clip(lower=0.1).to_numpy(dtype=float)
            equal_value = _weighted_daily(group, None)
            parity_value = _weighted_daily(group, weights)
            if equal_value is not None:
                daily[name]["equal"].append(equal_value)
            if parity_value is not None:
                daily[name]["atr_parity"].append(parity_value)
        if eligible_count > 0 and len(universe) >= eligible_count:
            random_daily["equal"].append([])
            random_daily["atr_parity"].append([])
            for run in range(random_runs):
                sample = universe.iloc[
                    rng.choice(len(universe), size=eligible_count, replace=False)
                ]
                weights = 1.0 / sample["atr_pct_real"].clip(lower=0.1).to_numpy(dtype=float)
                equal_value = _weighted_daily(sample, None)
                parity_value = _weighted_daily(sample, weights)
                if equal_value is not None:
                    random_daily["equal"][-1].append(equal_value)
                if parity_value is not None:
                    random_daily["atr_parity"][-1].append(parity_value)

    random_summary: dict[str, Any] = {}
    for scheme, blocks in random_daily.items():
        random_summary[scheme] = {
            "runs": random_runs,
            "date_median_of_run_medians_pct": float(
                np.median([np.median(block) for block in blocks if block])
            ),
            "run_summaries": [_summary([np.mean(block) for block in blocks if block])],
        }
    return {
        "groups": {
            name: {scheme: _summary(values) for scheme, values in schemes.items()}
            for name, schemes in daily.items()
        },
        "random_equal_size_as_eligible": random_summary,
        "interpretation": "Risk-construction diagnostic; daily overlapping outcomes are not executable portfolio P&L.",
    }


def _abstention(frame: pd.DataFrame) -> dict[str, Any]:
    dates = sorted(frame["scan_date"].unique())
    first = max(1, int(len(dates) * 0.50))
    calibration_end = max(first + 1, int(len(dates) * 0.70))
    train = frame[frame["scan_date"].isin(dates[:first])].copy()
    calibration = frame[frame["scan_date"].isin(dates[first:calibration_end])].copy()
    validation = frame[frame["scan_date"].isin(dates[calibration_end:])].copy()
    context_features = ("gap_pct", "rvol", "atr_pct_real")
    train_values = train.loc[:, context_features].apply(pd.to_numeric, errors="coerce")
    calibration_values = calibration.loc[:, context_features].apply(pd.to_numeric, errors="coerce")
    validation_values = validation.loc[:, context_features].apply(pd.to_numeric, errors="coerce")
    medians = train_values.median()
    spreads = (train_values.quantile(0.75) - train_values.quantile(0.25)).replace(0, 1.0)
    train_matrix = ((train_values.fillna(medians) - medians) / spreads).to_numpy(dtype=float)
    calibration_matrix = ((calibration_values.fillna(medians) - medians) / spreads).to_numpy(
        dtype=float
    )
    validation_matrix = ((validation_values.fillna(medians) - medians) / spreads).to_numpy(
        dtype=float
    )
    reference = train.loc[:, "c2c_5d"].to_numpy(dtype=float)

    def features(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        dispersion = []
        positive_rate = []
        for row in matrix:
            distances = np.sqrt(((train_matrix - row) ** 2).mean(axis=1))
            nearest = np.argpartition(distances, min(25, len(reference)) - 1)[
                : min(25, len(reference))
            ]
            values = reference[nearest]
            dispersion.append(np.percentile(values, 75) - np.percentile(values, 25))
            positive_rate.append((values > 0).mean())
        return np.asarray(dispersion), np.asarray(positive_rate)

    calibration_dispersion, calibration_positive = features(calibration_matrix)
    validation_dispersion, validation_positive = features(validation_matrix)
    calibration_evidence = (
        1.0 / (1.0 + calibration_dispersion) * (np.abs(calibration_positive - 0.5) * 2 + 0.5)
    )
    cutoff = float(np.quantile(calibration_evidence, 0.25))
    validation_evidence = (
        1.0 / (1.0 + validation_dispersion) * (np.abs(validation_positive - 0.5) * 2 + 0.5)
    )
    abstain = validation_evidence < cutoff
    active = validation.loc[~abstain, "c2c_5d"]
    silent = validation.loc[abstain, "c2c_5d"]
    return {
        "dates": {
            "train": len(dates[:first]),
            "calibration": len(dates[first:calibration_end]),
            "validation": len(dates[calibration_end:]),
        },
        "rows": {
            "train": len(train),
            "calibration": len(calibration),
            "validation": len(validation),
        },
        "calibration_cutoff": cutoff,
        "validation_abstain_rate": float(abstain.mean()) if len(abstain) else None,
        "validation_active_median_5d_pct": float(active.median()) if len(active) else None,
        "validation_abstain_median_5d_pct": float(silent.median()) if len(silent) else None,
        "interpretation": "Cutoff learned on calibration dates and evaluated once on later validation dates; still exploratory, not locked OOS.",
    }


def _context(frame: pd.DataFrame) -> dict[str, Any]:
    dates = sorted(frame["scan_date"].unique())
    split = max(1, int(len(dates) * 0.70))
    train = frame[frame["scan_date"].isin(dates[:split])]
    validation = frame[frame["scan_date"].isin(dates[split:])]
    result: dict[str, Any] = {"validation_dates": len(dates[split:]), "features": {}}
    for name in ("gap_pct", "rvol"):
        train_values = train[name].dropna()
        low = float(train_values.quantile(0.10))
        high = float(train_values.quantile(0.90))
        low_group = validation[validation[name] <= low]["c2c_5d"]
        high_group = validation[validation[name] >= high]["c2c_5d"]
        result["features"][name] = {
            "train_q10": low,
            "train_q90": high,
            "low_n": int(len(low_group)),
            "high_n": int(len(high_group)),
            "low_median_5d_pct": float(low_group.median()) if len(low_group) else None,
            "high_median_5d_pct": float(high_group.median()) if len(high_group) else None,
        }
    return result


def run(csv_path: Path, random_runs: int = 100) -> dict[str, Any]:
    raw = pd.read_csv(csv_path, low_memory=False)
    missing = sorted(set(REQUIRED).difference(raw.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    frame = raw.copy()
    frame["scan_date"] = pd.to_datetime(frame["scan_date"], errors="coerce").dt.date
    frame = frame.dropna(subset=["scan_date"]).drop_duplicates(["symbol", "scan_date"], keep="last")
    numeric = _numeric_frame(frame, ("atr_pct_real", "gap_pct", "rvol", "c2c_5d"))
    frame.loc[:, numeric.columns] = numeric
    frame["entry_ok"] = frame["entry_ok"].astype(str).str.lower().isin(("true", "1", "yes"))
    frame = frame.dropna(subset=["c2c_5d", "atr_pct_real", "gap_pct", "rvol"]).sort_values(
        ["scan_date", "symbol"]
    )
    return {
        "status": "exploratory",
        "scope": "research_only",
        "production_change": False,
        "source_csv": str(csv_path),
        "rows": {"raw": len(raw), "canonical": len(frame)},
        "atr_parity": _portfolio_schemes(frame, random_runs=random_runs),
        "abstention_independent_split": _abstention(frame),
        "gap_rvol_context": _context(frame),
        "data_quality": {
            "source": "data_readiness_audit_2026-08-12.json",
            "production_veto": False,
        },
        "locked_oos": "not_opened",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument("--random-runs", type=int, default=100)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/backtest_out/production_candidate_validation_2026-08-12.json"),
    )
    args = parser.parse_args()
    result = run(args.csv, random_runs=args.random_runs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                "rows": result["rows"],
                "atr_parity": result["atr_parity"]["groups"],
                "abstention": result["abstention_independent_split"],
                "gap_rvol": result["gap_rvol_context"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
