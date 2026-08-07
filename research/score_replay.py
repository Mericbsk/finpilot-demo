"""Research-only row-level replay of production score accounting."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from research.score_bridge import build_score_bridge

REQUIRED_FIELDS = {
    "regime",
    "direction",
    "score",
    "filter_score",
    "alignment_ratio",
    "momentum_ratio",
    "vol_regime",
    "volume_spike",
    "price_momentum",
    "trend_strength",
    "recommendation_score",
}


def _bool(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _float(value: object) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def _row(data: dict[str, str]) -> dict[str, Any]:
    booleans = {"regime", "direction", "volume_spike", "price_momentum", "trend_strength"}
    numeric = REQUIRED_FIELDS - booleans - {"recommendation_score"}
    result: dict[str, Any] = {}
    for key in booleans:
        result[key] = _bool(data.get(key))
    for key in numeric | {"recommendation_score"}:
        result[key] = _float(data.get(key))
    return result


def replay(path: Path, *, tolerance: float = 1e-6) -> dict[str, Any]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing_fields = sorted(REQUIRED_FIELDS - fields)
        rows = list(reader)
    input_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if missing_fields:
        return {
            "status": "insufficient_data",
            "reason": "required score component fields are absent",
            "missing_fields": missing_fields,
            "rows": len(rows),
            "input_sha256": input_hash,
        }
    mismatches: list[dict[str, Any]] = []
    invalid_rows = 0
    for index, data in enumerate(rows):
        values = _row(data)
        if any(
            values[key] is None
            for key in REQUIRED_FIELDS
            if key
            not in {"regime", "direction", "volume_spike", "price_momentum", "trend_strength"}
        ):
            invalid_rows += 1
            continue
        bridge = build_score_bridge(values, research_score=values["recommendation_score"])
        delta = abs(float(bridge["score_delta"] or 0.0))
        if delta > tolerance:
            mismatches.append(
                {
                    "row": index,
                    "symbol": data.get("symbol"),
                    "scan_ts": data.get("timestamp") or data.get("scan_ts"),
                    "live_score": bridge["live_score"],
                    "research_score": values["recommendation_score"],
                    "score_delta": bridge["score_delta"],
                }
            )
    compared = len(rows) - invalid_rows
    status = (
        "pass"
        if compared and invalid_rows == 0 and not mismatches
        else "insufficient_data"
        if invalid_rows
        else "fail"
    )
    return {
        "status": status,
        "rows": len(rows),
        "compared": compared,
        "invalid_rows": invalid_rows,
        "mismatch_count": len(mismatches),
        "tolerance": tolerance,
        "input_sha256": input_hash,
        "mismatches": mismatches[:25],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    result = replay(args.csv)
    payload = json.dumps(result, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        print(f"OK -> {args.out}")
    else:
        print(payload)


if __name__ == "__main__":
    main()
