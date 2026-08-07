"""Run one frozen candidate through the P0-P3 research gates."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from research.experiment_registry import ExperimentRegistry, RegistryError
from research.full_universe_barrier_backtest import (
    dedup_rows,
    label_rows,
    load_rows,
    resolve_paths,
)
from research.negative_control import run as run_negative_controls
from research.score_replay import replay
from research.stability_concentration_capacity import run as run_stability


def _summary(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"status": "insufficient_data", "n": 0}
    ordered = sorted(values)
    capped = [max(-20.0, min(20.0, value)) for value in values]
    return {
        "status": "ok",
        "n": len(values),
        "mean_net_return_pct": round(sum(values) / len(values), 6),
        "median_net_return_pct": round(ordered[len(ordered) // 2], 6),
        "capped_20_mean_net_return_pct": round(sum(capped) / len(capped), 6),
        "positive_net_rate": round(sum(value > 0 for value in values) / len(values), 6),
    }


def _candidate_scorecard(csv_path: Path, cache_dir: Path) -> dict[str, Any]:
    raw = load_rows(str(csv_path))
    canonical = dedup_rows(raw)
    resolved, inventory = resolve_paths(canonical, str(cache_dir), horizon=5, max_entry_drift=0.5)
    cost_scenarios: dict[str, dict[str, Any]] = {}
    temporal: dict[str, list[float]] = defaultdict(list)
    for cost_name, cost_pct in (("low", 0.25), ("base", 0.55), ("high", 1.0)):
        values: list[float] = []
        for row, result in label_rows(resolved, tp_mult=2.0, sl_mult=1.0, horizon=5):
            if not row["entry_ok"]:
                continue
            net = result.ret_pct * 100.0 - cost_pct
            values.append(net)
            if cost_name == "base":
                temporal[row["scan_date"]].append(net)
        cost_scenarios[cost_name] = {"cost_pct": cost_pct, **_summary(values)}
    dates = sorted(temporal)
    split_one = dates[: max(1, len(dates) // 2)]
    split_two = dates[max(1, len(dates) // 2) :]
    train = [value for date in split_one for value in temporal[date]]
    validation = [value for date in split_two for value in temporal[date]]
    return {
        "candidate": "entry_ok",
        "methodology": {
            "target": "5-day daily-OHLC triple-barrier net return",
            "tp_mult": 2.0,
            "sl_mult": 1.0,
            "horizon": 5,
            "cost_scenarios_pct": {"low": 0.25, "base": 0.55, "high": 1.0},
            "canonical_key": ["symbol", "scan_date"],
            "mfe_is_not_pnl": True,
        },
        "inventory": {**inventory, "raw_rows": len(raw), "canonical_rows": len(canonical)},
        "cost_scenarios": cost_scenarios,
        "temporal": {
            "train_dates": [split_one[0], split_one[-1]] if split_one else [],
            "validation_dates": [split_two[0], split_two[-1]] if split_two else [],
            "train": _summary(train),
            "validation": _summary(validation),
        },
    }


def run(
    csv_path: Path,
    cache_dir: Path,
    *,
    output_path: Path,
    registry_path: Path = Path("data/research_experiments.db"),
    permutations: int = 1000,
) -> dict[str, Any]:
    input_hash = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    experiment_id = f"p0-p3-entry-ok-{input_hash[:12]}"
    registry = ExperimentRegistry(registry_path)
    try:
        registry.register(
            experiment_id=experiment_id,
            family_id="entry-ok-p0-p3-v1",
            hypothesis="entry_ok has a stable cost-adjusted daily path outcome",
            rationale="Run the existing production candidate without new parameter selection",
            planned_tests=[
                "score_replay",
                "negative_controls",
                "cost_scorecard",
                "temporal_outlier",
            ],
            planned_runs=permutations * 3,
        )
    except RegistryError:
        if registry.get(experiment_id) is None:
            raise
    p0 = replay(csv_path)
    p1 = run_negative_controls(
        csv_path,
        cache_dir,
        permutations=permutations,
        registry_path=registry_path,
    )
    p2 = _candidate_scorecard(csv_path, cache_dir)
    p3 = run_stability(csv_path, cache_dir)
    result = {
        "experiment_id": experiment_id,
        "status": "completed",
        "scope": "research_only",
        "p0_score_replay": p0,
        "p1_negative_controls": p1,
        "p2_standardized_validation": p2,
        "p3_robustness": p3,
        "blocked_gates": {
            "locked_oos": "not_opened",
            "execution": "unknown_insufficient_data",
            "capacity": "insufficient_data",
            "shadow": "not_eligible",
            "production": "not_opened",
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument("--cache", type=Path, default=Path("data/price_cache"))
    parser.add_argument("--registry", type=Path, default=Path("data/research_experiments.db"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/backtest_out/research_run_2026-08-07_entry_ok_p0_p3.json"),
    )
    parser.add_argument("--permutations", type=int, default=1000)
    args = parser.parse_args()
    result = run(
        args.csv,
        args.cache,
        output_path=args.out,
        registry_path=args.registry,
        permutations=args.permutations,
    )
    print(f"OK -> {args.out}; experiment_id={result['experiment_id']}")


if __name__ == "__main__":
    main()
