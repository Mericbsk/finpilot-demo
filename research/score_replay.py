"""Research-only row-level replay of production score accounting."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from contextlib import contextmanager
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
FIELD_ALIASES = {"recommendation_score": "score_component_total"}
FLAG_ENV_NAMES = {
    "squeeze_factor": "FINPILOT_ENABLE_SQUEEZE_FACTOR",
    "edgar_catalyst": "FINPILOT_ENABLE_EDGAR_CATALYST",
    "lottery_fade": "FINPILOT_ENABLE_LOTTERY_FADE",
    "overnight_gap": "FINPILOT_ENABLE_OVERNIGHT_GAP",
}


@contextmanager
def _score_flags(flags: dict[str, Any] | None):
    if not isinstance(flags, dict):
        yield
        return
    previous = {name: os.environ.get(name) for name in FLAG_ENV_NAMES.values()}
    try:
        for key, env_name in FLAG_ENV_NAMES.items():
            if key in flags:
                os.environ[env_name] = "1" if bool(flags[key]) else "0"
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


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
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("results", payload) if isinstance(payload, dict) else payload
        rows = [dict(row) for row in rows]
        fields = set(rows[0]) if rows else set()
    else:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            rows = list(reader)
    for row in rows:
        nested_input = row.get("score_input")
        if isinstance(nested_input, dict):
            for key, value in nested_input.items():
                row.setdefault(key, value)
    if rows:
        fields.update(key for row in rows for key in row)
    missing_fields = sorted(
        field
        for field in REQUIRED_FIELDS
        if field not in fields and FIELD_ALIASES.get(field) not in fields
    )
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
    persisted_breakdown_mismatches: list[dict[str, Any]] = []
    invalid_rows = 0
    for index, data in enumerate(rows):
        if "recommendation_score" not in data and "score_component_total" in data:
            data["recommendation_score"] = data["score_component_total"]
        persisted = data.get("score_component_breakdown")
        if isinstance(persisted, dict) and data.get("score_component_total") is not None:
            try:
                persisted_delta = abs(
                    float(persisted.get("total")) - float(data["score_component_total"])
                )
                if persisted_delta > tolerance:
                    persisted_breakdown_mismatches.append(
                        {
                            "row": index,
                            "symbol": data.get("symbol"),
                            "persisted_total": data.get("score_component_total"),
                            "breakdown_total": persisted.get("total"),
                            "delta": persisted_delta,
                        }
                    )
            except (TypeError, ValueError):
                persisted_breakdown_mismatches.append(
                    {
                        "row": index,
                        "symbol": data.get("symbol"),
                        "reason": "invalid persisted total",
                    }
                )
        values = _row(data)
        if any(
            values[key] is None
            for key in REQUIRED_FIELDS
            if key
            not in {"regime", "direction", "volume_spike", "price_momentum", "trend_strength"}
        ):
            invalid_rows += 1
            continue
        with _score_flags(data.get("score_feature_flags")):
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
        "persisted_breakdown_compared": sum(
            isinstance(row.get("score_component_breakdown"), dict) for row in rows
        ),
        "persisted_breakdown_mismatch_count": len(persisted_breakdown_mismatches),
        "tolerance": tolerance,
        "input_sha256": input_hash,
        "mismatches": mismatches[:25],
        "persisted_breakdown_mismatches": persisted_breakdown_mismatches[:25],
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
