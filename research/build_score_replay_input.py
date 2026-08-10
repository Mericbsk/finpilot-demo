"""Build a strict, auditable historical score-replay input.

Historical suggestion exports contain the production score components for a
small subset of the canonical universe. Multiple intraday observations can
exist for one symbol-day, so this builder selects the latest timestamp
deterministically and records conflict counts instead of silently merging
values.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

REQUIRED_TELEMETRY = {
    "alignment_ratio",
    "filter_score",
    "momentum_ratio",
    "price_momentum",
    "recommendation_score",
    "trend_strength",
    "volume_spike",
}


def _timestamp(row: dict[str, str]) -> datetime:
    value = row.get("timestamp", "") or row.get("scan_ts", "")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def build(suggestions_dir: Path, canonical_path: Path, output_path: Path) -> dict[str, Any]:
    canonical: dict[tuple[str, str], list[dict[str, str]]] = {}
    with canonical_path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            canonical.setdefault((row["symbol"], row["scan_date"]), []).append(row)

    by_key: dict[tuple[str, str], list[dict[str, str]]] = {}
    source_files = sorted(suggestions_dir.glob("suggestions_*.csv"))
    for source in source_files:
        with source.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                key = (row.get("symbol", ""), row.get("timestamp", "")[:10])
                if key in canonical:
                    by_key.setdefault(key, []).append(row)

    selected: list[dict[str, str]] = []
    conflict_keys = 0
    for key, rows in sorted(by_key.items()):
        rows.sort(key=_timestamp)
        if any(len({row.get(field, "") for row in rows}) > 1 for field in REQUIRED_TELEMETRY):
            conflict_keys += 1
        chosen = dict(rows[-1])
        nearest = min(
            canonical[key],
            key=lambda candidate: abs((_timestamp(chosen) - _timestamp(candidate)).total_seconds()),
        )
        chosen["vol_regime"] = nearest.get("vol_regime", "")
        selected.append(chosen)

    if selected:
        fields = list(dict.fromkeys(field for row in selected for field in row))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(selected)

    return {
        "status": "ok" if selected else "insufficient_data",
        "source_files": len(source_files),
        "source_rows": sum(len(rows) for rows in by_key.values()),
        "selected_rows": len(selected),
        "unique_symbol_days": len(by_key),
        "duplicate_symbol_days": sum(len(rows) > 1 for rows in by_key.values()),
        "conflict_symbol_days": conflict_keys,
        "canonical_path": str(canonical_path),
        "output_path": str(output_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suggestions", type=Path, default=Path("data/suggestions"))
    parser.add_argument(
        "--canonical", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument(
        "--out", type=Path, default=Path("data/backtest_out/score_replay_input_2026-08-07.csv")
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/backtest_out/score_replay_input_2026-08-07.json"),
    )
    args = parser.parse_args()
    result = build(args.suggestions, args.canonical, args.out)
    args.manifest.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
