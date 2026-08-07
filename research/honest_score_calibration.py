"""Research-only calibration check on resolved triple-barrier outcomes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from research.full_universe_barrier_backtest import dedup_rows, label_rows, load_rows, resolve_paths

BANDS = ((0, 20), (20, 35), (35, 50), (50, 65), (65, 80), (80, 101))


def _band(score: float | None) -> str | None:
    if score is None:
        return None
    for lower, upper in BANDS:
        if lower <= score < upper:
            return f"{lower}-{min(upper, 100)}"
    return None


def _bucket_fit(rows: list[dict[str, object]]) -> dict[str, float]:
    probabilities: dict[str, float] = {}
    for band in {row["band"] for row in rows if row.get("band") is not None}:
        values = [float(row["target"]) for row in rows if row.get("band") == band]
        if values:
            probabilities[str(band)] = sum(values) / len(values)
    return probabilities


def _evaluate(
    rows: list[dict[str, object]], probabilities: dict[str, float], minimum_band_n: int = 30
) -> dict[str, object]:
    scored = [row for row in rows if row.get("band") in probabilities]
    if not scored:
        return {"status": "insufficient_data", "n": 0}
    brier = sum((float(row["target"]) - probabilities[row["band"]]) ** 2 for row in scored) / len(
        scored
    )
    bands = {
        band: {
            "n": sum(row["band"] == band for row in scored),
            "observed_rate": round(
                sum(float(row["target"]) for row in scored if row["band"] == band)
                / sum(row["band"] == band for row in scored),
                6,
            ),
            "fit_probability": round(probabilities[band], 6),
            "status": "ok"
            if sum(row["band"] == band for row in scored) >= minimum_band_n
            else "insufficient_data",
        }
        for band in probabilities
    }
    return {
        "status": "ok",
        "n": len(scored),
        "brier": round(brier, 6),
        "bands": bands,
    }


def run(csv_path: Path, cache_path: Path, cost_pct: float, split_date: str) -> dict[str, object]:
    raw_rows = load_rows(str(csv_path))
    rows, inventory = resolve_paths(
        dedup_rows(raw_rows), str(cache_path), horizon=5, max_entry_drift=0.5
    )
    labeled = label_rows(rows, tp_mult=2.0, sl_mult=1.0, horizon=5)
    observations: list[dict[str, object]] = []
    for row, result in labeled:
        score = row.get("composite")
        if score is None:
            continue
        net_return = result.ret_pct * 100.0 - cost_pct
        observations.append(
            {
                "event": f"{row['symbol']}:{row['scan_date']}",
                "scan_date": row["scan_date"],
                "band": _band(float(score)),
                "target": 1.0 if net_return > 0 else 0.0,
                "net_return_pct": round(net_return, 6),
            }
        )
    train = [row for row in observations if row["scan_date"] < split_date]
    test = [row for row in observations if row["scan_date"] >= split_date]
    probabilities = _bucket_fit(train)
    return {
        "methodology": {
            "target": "5-day triple-barrier net return > 0",
            "tp_mult": 2.0,
            "sl_mult": 1.0,
            "cost_pct": cost_pct,
            "score_source": "full_universe_enriched.composite",
            "calibration_split_date": split_date,
            "minimum_band_n": 30,
        },
        "inventory": inventory,
        "observations": len(observations),
        "train": _evaluate(train, probabilities),
        "test": _evaluate(test, probabilities),
        "status": "insufficient_data" if not test else "research_only",
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
        default=Path("data/backtest_out/honest_score_calibration_2026-08-06.json"),
    )
    parser.add_argument("--cost-pct", type=float, default=0.55)
    parser.add_argument("--split-date", default="2026-06-15")
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(run(args.csv, args.cache, args.cost_pct, args.split_date), indent=2),
        encoding="utf-8",
    )
    print(f"OK -> {args.out}")


if __name__ == "__main__":
    main()
