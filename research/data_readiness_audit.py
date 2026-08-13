"""Research-only audit for the data gates preceding confirmatory runs."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REQUIRED_EXECUTION_FIELDS = {"spread", "slippage", "impact", "fill_price"}
PIT_FIELDS = {"symbol", "effective_from", "effective_to", "listed_at", "delisted_at"}


def _json_records(path: Path) -> list[Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return value if isinstance(value, list) else [value]


def _record_fields(record: Any) -> set[str]:
    return set(record) if isinstance(record, dict) else set()


def inspect_price_cache(cache_dir: Path) -> dict[str, Any]:
    files = sorted(cache_dir.glob("*.json")) if cache_dir.exists() else []
    total_bytes = sum(path.stat().st_size for path in files)
    return {
        "files": len(files),
        "bytes": total_bytes,
        "available": bool(files),
        "immutable_snapshot": False,
        "note": "A current cache is not an immutable prior snapshot.",
    }


def inspect_intraday_cache(cache_dir: Path) -> dict[str, Any]:
    files = sorted(cache_dir.glob("*.json")) if cache_dir.exists() else []
    record_count = 0
    usable_files = 0
    for path in files:
        records = _json_records(path)
        if records and all(
            (isinstance(item, list) and len(item) >= 5)
            or (
                isinstance(item, dict)
                and isinstance(item.get("value"), list)
                and len(item["value"]) >= 5
            )
            for item in records
        ):
            usable_files += 1
            record_count += len(records)
    return {
        "files": len(files),
        "usable_bar_files": usable_files,
        "records": record_count,
        "available": usable_files > 0,
        "execution_fields": sorted(REQUIRED_EXECUTION_FIELDS),
        "note": "Bars exist, but execution observations are a separate required dataset.",
    }


def inspect_json_tree(data_dir: Path, field_names: set[str]) -> dict[str, Any]:
    files = sorted(data_dir.rglob("*.json")) if data_dir.exists() else []
    observed: set[str] = set()
    for path in files:
        for record in _json_records(path)[:100]:
            observed.update(_record_fields(record))
    return {
        "files": len(files),
        "observed_fields": sorted(observed & field_names),
        "required_fields": sorted(field_names),
        "available": field_names <= observed,
    }


def inspect_execution_data(data_dir: Path) -> dict[str, Any]:
    files = sorted(data_dir.rglob("*.json")) if data_dir.exists() else []
    complete_records = 0
    observed: set[str] = set()
    for path in files:
        for record in _json_records(path)[:100]:
            fields = _record_fields(record)
            observed.update(fields & REQUIRED_EXECUTION_FIELDS)
            if fields >= REQUIRED_EXECUTION_FIELDS:
                complete_records += 1
    return {
        "files": len(files),
        "observed_fields": sorted(observed & REQUIRED_EXECUTION_FIELDS),
        "required_fields": sorted(REQUIRED_EXECUTION_FIELDS),
        "complete_records": complete_records,
        "available": complete_records > 0,
    }


def build_audit(root: Path) -> dict[str, Any]:
    data_dir = root / "data"
    price = inspect_price_cache(data_dir / "price_cache")
    intraday = inspect_intraday_cache(data_dir / "intraday_cache")
    pit = inspect_json_tree(data_dir, PIT_FIELDS)
    execution = inspect_execution_data(data_dir)
    gates = {
        "P1_data_reliability": "BLOCKED",
        "P2_label_execution": "AVAILABLE_FOR_BAR_DIAGNOSTICS"
        if intraday["available"] and execution["available"]
        else "BLOCKED",
        "H1_H2_H3_confirmatory": "HOLD",
        "locked_oos": "NOT_OPENED",
    }
    blockers = [
        "PIT listing/delisting universe and ticker lineage are unavailable."
        if not pit["available"]
        else None,
        "Corporate-action classification and immutable prior cache comparison are unavailable.",
        "Observed spread, slippage, impact and fill-price fields are unavailable."
        if not execution["available"]
        else None,
        "Locked OOS requires human approval after all prerequisite gates pass.",
    ]
    return {
        "audit_id": "finpilot-data-readiness-2026-08-11",
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "research_only",
        "production_change": False,
        "inputs": {
            "price_cache": price,
            "intraday_cache": intraday,
            "pit_universe": pit,
            "execution_data": execution,
        },
        "gates": gates,
        "blockers": [item for item in blockers if item],
    }


def snapshot_manifest(cache_dir: Path, output: Path) -> dict[str, Any]:
    files = sorted(cache_dir.glob("*.json"))
    entries = []
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append({"name": path.name, "bytes": path.stat().st_size, "sha256": digest})
    result = {
        "snapshot_id": "price-cache-2026-08-11-current",
        "created_at": datetime.now(UTC).isoformat(),
        "kind": "hash_manifest",
        "restatement_comparison_ready": False,
        "files": entries,
        "note": "A hash manifest records provenance but cannot compare bar values without the preserved files.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--out", type=Path, default=Path("data/backtest_out/data_readiness_audit_2026-08-11.json")
    )
    parser.add_argument("--snapshot-manifest", type=Path)
    args = parser.parse_args()
    result = build_audit(args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if args.snapshot_manifest:
        snapshot_manifest(args.root / "data" / "price_cache", args.snapshot_manifest)
    print(json.dumps(result["gates"], sort_keys=True))


if __name__ == "__main__":
    main()
