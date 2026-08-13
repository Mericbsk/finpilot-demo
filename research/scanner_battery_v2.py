"""Research-only scanner battery v2.

This module measures the proposed follow-up questions without changing the
production scanner. It separates executable diagnostics from data-blocked
questions and records assumptions for every synthetic execution model.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from research.full_universe_barrier_backtest import load_bars

DEFAULT_CSV = Path("data/backtest_out/full_universe_enriched.csv")
DEFAULT_CACHE = Path("data/price_cache")
DEFAULT_OUT = Path("data/backtest_out/scanner_battery_v2_2026-08-11.json")
COSTS_BPS = (0, 5, 10, 15, 25, 40, 55, 75, 100, 150)
FEATURES = (
    "finpilot_score",
    "composite_score",
    "dist_52w_high",
    "gap_pct",
    "rvol",
    "atr_pct_real",
    "squeeze_factor",
    "lottery_factor",
    "overnight_gap_factor",
    "catalyst_factor",
)


def _float(value: object) -> float | None:
    try:
        if value in (None, ""):
            return None
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def _bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _mean(values: list[float]) -> float | None:
    return round(float(np.mean(values)), 6) if values else None


def _median(values: list[float]) -> float | None:
    return round(float(np.median(values)), 6) if values else None


def _spearman(left: list[float], right: list[float]) -> float | None:
    if len(left) < 3 or len(left) != len(right):
        return None
    a = np.asarray(left, dtype=float)
    b = np.asarray(right, dtype=float)
    if np.std(a) == 0 or np.std(b) == 0:
        return None
    ar = np.argsort(np.argsort(a)).astype(float)
    br = np.argsort(np.argsort(b)).astype(float)
    return round(float(np.corrcoef(ar, br)[0, 1]), 6)


def _summary(values: list[float], cost_bps: float = 0) -> dict[str, Any]:
    if not values:
        return {"status": "INSUFFICIENT_DATA", "n": 0}
    net = [value - cost_bps / 100.0 for value in values]
    wins = [value for value in net if value > 0]
    losses = [value for value in net if value < 0]
    abs_losses = [abs(value) for value in losses]
    top = sorted(net, reverse=True)
    total = sum(net)
    return {
        "status": "COMPLETED",
        "n": len(net),
        "mean_net_pct": _mean(net),
        "median_net_pct": _median(net),
        "trimmed_5pct_mean_net_pct": _mean(
            sorted(net)[max(0, len(net) // 20) : len(net) - max(0, len(net) // 20) or None]
        ),
        "positive_rate": round(len(wins) / len(net), 6),
        "avg_win_pct": _mean(wins),
        "avg_loss_pct": _mean(losses),
        "payoff_ratio": round(float(np.mean(wins) / np.mean(abs_losses)), 6)
        if wins and abs_losses
        else None,
        "profit_factor": round(float(sum(wins) / sum(abs_losses)), 6)
        if wins and abs_losses and sum(abs_losses)
        else None,
        "expectancy_pct": _mean(net),
        "top_1pct_contribution_pct": round(sum(top[: max(1, len(top) // 100)]) / total * 100, 6)
        if total
        else None,
        "top_5pct_contribution_pct": round(sum(top[: max(1, len(top) // 20)]) / total * 100, 6)
        if total
        else None,
        "max_loss_pct": round(float(min(net)), 6),
        "max_win_pct": round(float(max(net)), 6),
    }


def _read_export(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for raw in csv.DictReader(handle):
            row: dict[str, Any] = dict(raw)
            row["symbol"] = (raw.get("symbol") or "").strip()
            row["scan_date"] = (raw.get("scan_date") or "").strip()
            row["scan_ts"] = (raw.get("scan_ts") or "").strip()
            for field in FEATURES + (
                "price",
                "resolved_pct_t5",
                "resolved_pct_1d",
                "c2c_1d",
                "c2c_5d",
                "mae_t5",
                "atr",
                "score",
            ):
                row[field] = _float(raw.get(field))
            row["entry_ok"] = _bool(raw.get("entry_ok"))
            row["liquidity_ok"] = _bool(raw.get("liquidity_ok"))
            row["regime"] = (raw.get("regime") or "").strip()
            row["direction"] = _bool(raw.get("direction"))
            row["vol_regime"] = _float(raw.get("vol_regime"))
            if row["symbol"] and row["scan_date"] and row["price"] and row["atr_pct_real"]:
                rows.append(row)
    rows.sort(key=lambda item: (item["symbol"], item["scan_date"], item["scan_ts"]))
    seen: set[tuple[str, str]] = set()
    canonical = []
    for row in rows:
        key = (row["symbol"], row["scan_date"])
        if key not in seen:
            canonical.append(row)
            seen.add(key)
    return canonical


def _path_metrics(
    rows: list[dict[str, Any]], cache_dir: Path, max_horizon: int = 10
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cache: dict[str, list[dict[str, Any]]] = {}
    output: list[dict[str, Any]] = []
    inventory = Counter()
    for row in rows:
        if row["symbol"] not in cache:
            cache[row["symbol"]] = load_bars(str(cache_dir), row["symbol"])
        bars = cache[row["symbol"]]
        index = next((i for i, bar in enumerate(bars) if bar.get("date") >= row["scan_date"]), None)
        if index is None:
            inventory["missing_path"] += 1
            continue
        entry_bar = bars[index]
        future = bars[index + 1 : index + 1 + max_horizon]
        if len(future) < 1:
            inventory["short_path"] += 1
            continue
        item = dict(row)
        entry = row["price"]
        for horizon in (1, 2, 3, 5, 10):
            if len(future) >= horizon:
                item[f"fwd_{horizon}d_pct"] = (
                    float(future[horizon - 1]["close"]) / entry - 1.0
                ) * 100.0
                item[f"next_open_{horizon}d_pct"] = (
                    float(future[horizon - 1]["open"]) / entry - 1.0
                ) * 100.0
            else:
                item[f"fwd_{horizon}d_pct"] = None
                item[f"next_open_{horizon}d_pct"] = None
        item["entry_drift_pct"] = (
            abs(entry / float(entry_bar["close"]) - 1.0) * 100.0 if entry_bar.get("close") else None
        )
        item["next_day_pullback_025_atr"] = bool(
            future
            and future[0].get("low") is not None
            and future[0]["low"] <= entry * (1 - 0.25 * row["atr_pct_real"] / 100.0)
        )
        item["pullback_proxy_return_pct"] = (
            item["fwd_1d_pct"] + 0.25 * row["atr_pct_real"]
            if item["next_day_pullback_025_atr"] and item["fwd_1d_pct"] is not None
            else None
        )
        output.append(item)
    inventory["input_rows"] = len(rows)
    inventory["resolved_rows"] = len(output)
    inventory["symbols"] = len(cache)
    inventory["adjusted_close_values"] = sum(
        1
        for bars in cache.values()
        for bar in bars
        if _float(bar.get("adjusted_close")) is not None
    )
    inventory["raw_close_values"] = sum(
        1 for bars in cache.values() for bar in bars if _float(bar.get("close")) is not None
    )
    return output, dict(inventory)


def cost_sensitivity(rows: list[dict[str, Any]], outcome: str = "fwd_5d_pct") -> dict[str, Any]:
    result: dict[str, Any] = {"outcome": outcome, "costs_bps": list(COSTS_BPS), "groups": {}}
    for name, selected in (
        ("all", rows),
        ("eligible", [r for r in rows if r["entry_ok"]]),
        ("rejected", [r for r in rows if not r["entry_ok"]]),
    ):
        values = [r[outcome] for r in selected if r.get(outcome) is not None]
        result["groups"][name] = {str(bps): _summary(values, bps) for bps in COSTS_BPS}
        break_even = max(
            (
                bps
                for bps in COSTS_BPS
                if _summary(values, bps).get("median_net_pct") is not None
                and _summary(values, bps)["median_net_pct"] > 0
            ),
            default=None,
        )
        result["groups"][name]["break_even_median_cost_bps_grid"] = break_even
    return result


def payoff_tail(rows: list[dict[str, Any]], outcome: str = "fwd_5d_pct") -> dict[str, Any]:
    groups = {}
    for name, selected in (
        ("all", rows),
        ("eligible", [r for r in rows if r["entry_ok"]]),
        ("rejected", [r for r in rows if not r["entry_ok"]]),
    ):
        values = [r[outcome] for r in selected if r.get(outcome) is not None]
        groups[name] = {"all": _summary(values)}
        for fraction, label in ((0.01, "without_top_1pct"), (0.05, "without_top_5pct")):
            cutoff = max(1, int(len(values) * fraction))
            groups[name][label] = _summary(sorted(values)[:-cutoff] if len(values) > cutoff else [])
    return {"outcome": outcome, "groups": groups}


def feature_ablation(rows: list[dict[str, Any]], outcome: str = "fwd_5d_pct") -> dict[str, Any]:
    result = {}
    valid_outcomes = [r for r in rows if r.get(outcome) is not None]
    for feature in FEATURES:
        sub = [r for r in valid_outcomes if r.get(feature) is not None]
        if not sub:
            result[feature] = {"status": "INSUFFICIENT_DATA", "n": 0}
            continue
        values = [r[feature] for r in sub]
        order = np.argsort(values)
        top = [sub[i][outcome] for i in order[-max(1, len(order) // 5) :]]
        result[feature] = {
            "status": "COMPLETED",
            "n": len(sub),
            "spearman_vs_forward_pct": _spearman(values, [r[outcome] for r in sub]),
            "top_quintile": _summary(top),
        }
    return {"outcome": outcome, "features": result}


def signal_frequency(rows: list[dict[str, Any]], outcome: str = "fwd_5d_pct") -> dict[str, Any]:
    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get(outcome) is not None:
            by_date[row["scan_date"]].append(row)
    daily = []
    for date, values in sorted(by_date.items()):
        eligible = [r for r in values if r["entry_ok"]]
        daily.append(
            {
                "scan_date": date,
                "all_count": len(values),
                "eligible_count": len(eligible),
                "eligible_median_forward_pct": _median([r[outcome] for r in eligible]),
            }
        )
    paired = [
        (row["eligible_count"], row["eligible_median_forward_pct"])
        for row in daily
        if row["eligible_median_forward_pct"] is not None
    ]
    counts = [count for count, _ in paired]
    quality = [median_forward for _, median_forward in paired]
    return {
        "status": "COMPLETED" if daily else "INSUFFICIENT_DATA",
        "days": len(daily),
        "daily": daily,
        "eligible_count_summary": _summary([float(value) for value in counts])
        if counts
        else {"n": 0},
        "count_vs_daily_median_quality_spearman": _spearman(counts, quality) if quality else None,
    }


def matched_selection(rows: list[dict[str, Any]], outcome: str = "fwd_5d_pct") -> dict[str, Any]:
    eligible = [r for r in rows if r["entry_ok"] and r.get(outcome) is not None]
    rejected_by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not row["entry_ok"] and row.get(outcome) is not None:
            rejected_by_date[row["scan_date"]].append(row)
    pairs = []
    for row in eligible:
        pool = rejected_by_date.get(row["scan_date"], [])
        if not pool:
            continue
        candidates = [
            candidate
            for candidate in pool
            if all(
                candidate.get(field) is not None and row.get(field) is not None
                for field in ("composite_score", "atr_pct_real", "gap_pct", "rvol", "dist_52w_high")
            )
        ]
        if not candidates:
            continue
        scale = {
            "composite_score": 20.0,
            "atr_pct_real": 5.0,
            "gap_pct": 5.0,
            "rvol": 2.0,
            "dist_52w_high": 0.5,
        }
        match = min(
            candidates,
            key=lambda candidate: sum(
                abs(candidate[field] - row[field]) / scale[field] for field in scale
            ),
        )
        pairs.append(
            {
                "date": row["scan_date"],
                "eligible_pct": row[outcome],
                "matched_rejected_pct": match[outcome],
                "difference_pct": row[outcome] - match[outcome],
            }
        )
    differences = [pair["difference_pct"] for pair in pairs]
    return {
        "status": "COMPLETED" if pairs else "INSUFFICIENT_DATA",
        "pairs": len(pairs),
        "difference": _summary(differences),
    }


def veto_decomposition(rows: list[dict[str, Any]], outcome: str = "fwd_5d_pct") -> dict[str, Any]:
    predicates = {
        "high_volatility": lambda r: r.get("atr_pct_real") is not None and r["atr_pct_real"] >= 8,
        "gap_risk": lambda r: r.get("gap_pct") is not None and r["gap_pct"] >= 5,
        "near_52w_high": lambda r: r.get("dist_52w_high") is not None
        and r["dist_52w_high"] >= 0.95,
        "low_relative_volume": lambda r: r.get("rvol") is not None and r["rvol"] < 1,
        "weak_trend": lambda r: not _bool(r.get("regime")) or not bool(r.get("direction")),
    }
    result = {}
    for name, predicate in predicates.items():
        flagged = [r[outcome] for r in rows if r.get(outcome) is not None and predicate(r)]
        other = [r[outcome] for r in rows if r.get(outcome) is not None and not predicate(r)]
        result[name] = {"flagged": _summary(flagged), "not_flagged": _summary(other)}
    return {"status": "COMPLETED", "vetoes": result}


def regime_interaction(rows: list[dict[str, Any]], outcome: str = "fwd_5d_pct") -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get(outcome) is not None:
            regime = str(
                row.get("vol_regime")
                if row.get("vol_regime") is not None
                else row.get("regime") or "missing"
            )
            groups[regime].append(row)
    cells = {}
    for regime, values in groups.items():
        values = [r for r in values if r.get("finpilot_score") is not None]
        if len(values) < 30:
            cells[regime] = {"status": "INSUFFICIENT_DATA", "n": len(values)}
            continue
        values.sort(key=lambda r: r["finpilot_score"])
        cells[regime] = {
            "status": "COMPLETED",
            "n": len(values),
            "score_quintiles": [
                _summary([r[outcome] for r in values[i : i + max(1, len(values) // 5)]])
                for i in range(0, len(values), max(1, len(values) // 5))
            ][:5],
        }
    return {
        "status": "COMPLETED",
        "macro_regime_status": "BLOCKED_NO_VIX_OR_BENCHMARK_FIELDS",
        "cells": cells,
    }


def execution_stress(rows: list[dict[str, Any]], outcome: str = "fwd_5d_pct") -> dict[str, Any]:
    scenarios = {}
    for notional in (10_000, 50_000, 100_000):
        scenarios[str(notional)] = {}
        for bps in COSTS_BPS:
            values = [r[outcome] - bps / 100.0 for r in rows if r.get(outcome) is not None]
            scenarios[str(notional)][str(bps)] = _summary(values)
    return {
        "status": "SCENARIO_ONLY",
        "observed_spread_rate": 0.0,
        "observed_slippage_rate": 0.0,
        "observed_impact_rate": 0.0,
        "scenarios": scenarios,
        "note": "Flat bps scenarios are not observed fills. ADV-conditioned impact is BLOCKED because dollar_ADV is absent from the export.",
    }


def data_gap_audit(
    rows: list[dict[str, Any]], cache_dir: Path, artifacts_dir: Path
) -> dict[str, Any]:
    cache_files = list(cache_dir.glob("*.json"))
    adjusted = 0
    raw = 0
    for path in cache_files:
        try:
            bars = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            continue
        for bar in bars:
            raw += int(_float(bar.get("close")) is not None)
            adjusted += int(_float(bar.get("adjusted_close")) is not None)
    artifact_names = [path.name for path in artifacts_dir.glob("*.json")]
    return {
        "status": "COMPLETED_WITH_BLOCKS",
        "cache_symbols": len(cache_files),
        "adjusted_close_coverage": round(adjusted / raw, 6) if raw else 0.0,
        "survivorship": "BLOCKED_NO_POINT_IN_TIME_LISTING_DELISTING_UNIVERSE",
        "corporate_actions": "BLOCKED_NO_ACTION_FEED_OR_PROVIDER_EXPLANATION",
        "score_version": "BLOCKED_NO_SCORE_VERSION_OR_EPOCH_FIELD",
        "benchmark_beta_neutral": "BLOCKED_NO_BENCHMARK_FIELDS",
        "artifact_count_for_meta_audit": len(artifact_names),
    }


def run(csv_path: Path, cache_dir: Path, artifacts_dir: Path) -> dict[str, Any]:
    rows = _read_export(csv_path)
    resolved, inventory = _path_metrics(rows, cache_dir)
    full_5d = [row for row in resolved if row.get("fwd_5d_pct") is not None]
    clean_5pct = [
        row
        for row in full_5d
        if row.get("entry_drift_pct") is not None and row["entry_drift_pct"] <= 5.0
    ]
    clean_1pct = [
        row
        for row in full_5d
        if row.get("entry_drift_pct") is not None and row["entry_drift_pct"] <= 1.0
    ]

    def battery_set(values: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "rows": len(values),
            "cost_sensitivity": cost_sensitivity(values),
            "payoff_tail_decomposition": payoff_tail(values),
            "score_raw_feature_ablation": feature_ablation(values),
            "signal_frequency_quality": signal_frequency(values),
            "matched_eligible_rejected": matched_selection(values),
            "veto_component_decomposition": veto_decomposition(values),
            "regime_score_interaction": regime_interaction(values),
            "execution_cost_stress": execution_stress(values),
            "short_horizon_and_pullback": {
                "horizons": {
                    str(h): _summary(
                        [r[f"fwd_{h}d_pct"] for r in values if r.get(f"fwd_{h}d_pct") is not None]
                    )
                    for h in (1, 2, 3, 5, 10)
                },
                "next_open_proxy": _summary(
                    [r["next_open_1d_pct"] for r in values if r.get("next_open_1d_pct") is not None]
                ),
                "pullback_025_atr_proxy": _summary(
                    [
                        r["pullback_proxy_return_pct"]
                        for r in values
                        if r.get("pullback_proxy_return_pct") is not None
                    ]
                ),
                "status": "COMPLETED_WITH_DAILY_BAR_LIMITATION",
            },
        }

    result = {
        "study": "scanner_battery_v2",
        "status": "research_only",
        "data_snapshot_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "input_canonical_rows": len(rows),
        "inventory": inventory,
        "path_sets": {
            "any_forward_path": len(resolved),
            "full_5d_path": len(full_5d),
            "full_5d_entry_drift_le_5pct": len(clean_5pct),
            "full_5d_entry_drift_le_1pct": len(clean_1pct),
        },
        "experiments": {
            "all_path": battery_set(resolved),
            "full_5d_path": battery_set(full_5d),
            "clean_drift_le_5pct": battery_set(clean_5pct),
            "clean_drift_le_1pct": battery_set(clean_1pct),
            "data_gap_and_meta_audit": data_gap_audit(rows, cache_dir, artifacts_dir),
        },
        "blocked_questions": [
            "survivorship and delisted-inclusive universe",
            "corporate-action classification for flagged jumps",
            "historical score version/epoch replay",
            "VIX/SPY/sector beta-neutral regime interaction",
            "observed spread/slippage/impact and ADV-conditioned fill model",
            "intraday pullback ordering and execution",
        ],
        "production_change": False,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--artifacts", type=Path, default=DEFAULT_OUT.parent)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    result = run(args.csv, args.cache, args.artifacts)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "study": result["study"],
                "resolved_rows": result["inventory"]["resolved_rows"],
                "out": str(args.out),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
