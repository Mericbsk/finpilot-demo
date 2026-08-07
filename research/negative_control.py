"""Matched-null preflight for the registered ``entry_ok`` candidate.

The runner preserves the canonical symbol-day universe and per-day signal
counts. It is research-only: it produces null distributions and never selects
or promotes a candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any

from research.experiment_registry import ExperimentRegistry, RegistryError
from research.full_universe_barrier_backtest import (
    dedup_rows,
    label_rows,
    load_rows,
    resolve_paths,
)


def _input_hash(
    path: Path, *, horizon: int, tp_mult: float, sl_mult: float, cost_pct: float
) -> str:
    payload = (
        path.read_bytes()
        + json.dumps(
            {"horizon": horizon, "tp_mult": tp_mult, "sl_mult": sl_mult, "cost_pct": cost_pct},
            sort_keys=True,
        ).encode()
    )
    return hashlib.sha256(payload).hexdigest()


def _summary(values: list[float], *, candidate_mean: float | None = None) -> dict[str, Any]:
    if not values:
        return {"status": "insufficient_data", "n": 0}
    ordered = sorted(values)
    percentile = None
    if candidate_mean is not None:
        percentile = round(sum(value <= candidate_mean for value in values) / len(values), 6)
    return {
        "status": "ok",
        "n": len(values),
        "mean_pct": round(sum(values) / len(values), 6),
        "median_pct": round(median(values), 6),
        "p05_pct": round(ordered[max(0, int(len(values) * 0.05) - 1)], 6),
        "p95_pct": round(ordered[min(len(values) - 1, int(len(values) * 0.95))], 6),
        "candidate_percentile": percentile,
    }


def _daily_groups(rows: list[dict[str, Any]]) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        groups[row["scan_date"]].append(index)
    return dict(groups)


def _permuted_signal_returns(
    rows: list[dict[str, Any]],
    returns: list[float],
    candidate_indices: set[int],
    *,
    seed: int,
    mode: str,
) -> float:
    randomizer = random.Random(seed)
    groups = _daily_groups(rows)
    selected: list[int] = []
    dates = sorted(groups)
    if mode == "time_shift":
        shifted_counts = {date: len(candidate_indices.intersection(groups[date])) for date in dates}
        for date, count in shifted_counts.items():
            target_date = dates[dates.index(date) - 1] if dates.index(date) > 0 else None
            if target_date is not None:
                pool = groups[target_date]
                selected.extend(randomizer.sample(pool, min(count, len(pool))))
    else:
        for date in dates:
            pool = groups[date]
            count = len(candidate_indices.intersection(pool))
            selected.extend(randomizer.sample(pool, min(count, len(pool))))
    if mode == "label_permutation":
        shuffled = list(returns)
        randomizer.shuffle(shuffled)
        return sum(shuffled[index] for index in selected) / len(selected) if selected else 0.0
    return sum(returns[index] for index in selected) / len(selected) if selected else 0.0


def run(
    csv_path: Path,
    cache_dir: Path,
    *,
    permutations: int = 1000,
    seed: int = 20260807,
    horizon: int = 5,
    tp_mult: float = 1.5,
    sl_mult: float = 0.75,
    cost_pct: float = 0.55,
    registry_path: Path = Path("data/research_experiments.db"),
) -> dict[str, Any]:
    if permutations < 1000:
        raise ValueError("P1 requires at least 1000 reproducible permutations")
    raw_rows = load_rows(str(csv_path))
    canonical_rows = dedup_rows(raw_rows)
    resolved, inventory = resolve_paths(canonical_rows, str(cache_dir), horizon, 0.5)
    labeled = label_rows(resolved, tp_mult, sl_mult, horizon)
    rows = []
    returns = []
    for row, label in labeled:
        rows.append(row)
        returns.append(round(label.ret_pct * 100 - cost_pct, 8))
    candidate_indices = {index for index, row in enumerate(rows) if row["entry_ok"]}
    candidate_values = [returns[index] for index in sorted(candidate_indices)]
    candidate_mean = sum(candidate_values) / len(candidate_values) if candidate_values else None
    input_hash = _input_hash(
        csv_path, horizon=horizon, tp_mult=tp_mult, sl_mult=sl_mult, cost_pct=cost_pct
    )
    registry = ExperimentRegistry(registry_path)
    experiment_id = f"p1-negative-entry-ok-{input_hash[:12]}"
    try:
        registry.register(
            experiment_id=experiment_id,
            family_id="p1-entry-ok-null-v1",
            hypothesis="entry_ok path outcomes exceed matched null controls",
            rationale="Preflight the existing candidate without adding parameters",
            planned_tests=["label_permutation", "signal_permutation", "time_shift"],
            planned_runs=permutations * 3,
        )
    except RegistryError:
        if registry.get(experiment_id) is None:
            raise
    distributions: dict[str, list[float]] = {}
    for family_offset, mode in enumerate(("label_permutation", "signal_permutation", "time_shift")):
        values: list[float] = []
        for index in range(permutations):
            permutation_seed = seed + family_offset * permutations + index
            value = _permuted_signal_returns(
                rows,
                returns,
                candidate_indices,
                seed=permutation_seed,
                mode=mode,
            )
            values.append(value)
            try:
                registry.record_run(
                    experiment_id=experiment_id,
                    run_id=f"{experiment_id}-{mode}-{index:04d}",
                    run_index=family_offset * permutations + index,
                    seed=permutation_seed,
                    input_hash=input_hash,
                    status="completed",
                    result={"family": mode, "value_pct": value},
                )
            except RegistryError:
                # Re-running the same immutable experiment must not overwrite a run.
                pass
        distributions[mode] = values
    return {
        "experiment_id": experiment_id,
        "status": "completed" if rows and candidate_indices else "insufficient_data",
        "methodology": {
            "candidate": "entry_ok",
            "canonical_key": ["symbol", "scan_date"],
            "horizon": horizon,
            "tp_mult": tp_mult,
            "sl_mult": sl_mult,
            "cost_pct": cost_pct,
            "permutations_per_family": permutations,
            "seed": seed,
            "input_sha256": input_hash,
        },
        "inventory": {
            **inventory,
            "raw_rows": len(raw_rows),
            "canonical_rows": len(canonical_rows),
            "resolved_rows": len(rows),
        },
        "candidate": {"n": len(candidate_values), "mean_net_return_pct": candidate_mean},
        "null_families": {
            mode: _summary(values, candidate_mean=candidate_mean)
            for mode, values in distributions.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument("--cache", type=Path, default=Path("data/price_cache"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/backtest_out/research_run_2026-08-07_negative_controls.json"),
    )
    parser.add_argument("--registry", type=Path, default=Path("data/research_experiments.db"))
    parser.add_argument("--permutations", type=int, default=1000)
    args = parser.parse_args()
    result = run(args.csv, args.cache, permutations=args.permutations, registry_path=args.registry)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"OK -> {args.out}")


if __name__ == "__main__":
    main()
