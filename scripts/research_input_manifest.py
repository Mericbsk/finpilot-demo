"""Create a reproducible manifest for research input artifacts.

This tool is intentionally read-only. It records file hashes and lightweight
CSV quality statistics so research outputs can be traced to exact inputs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_INPUTS = (
    Path("data/backtest_out/full_universe_enriched.csv"),
    Path("data/backtest_out/enriched_signals_v2.csv"),
    Path("data/backtest_out/enriched_signals_v3.csv"),
    Path("data/finpilot.db"),
    Path("data/price_cache"),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _first_field(fieldnames: list[str], candidates: tuple[str, ...]) -> str | None:
    return next((name for name in candidates if name in fieldnames), None)


def _date_range(rows: list[dict[str, str]], field: str | None) -> dict[str, str | None]:
    values = sorted({row.get(field, "")[:10] for row in rows}) if field else []
    values = [value for value in values if value]
    return {"min": values[0] if values else None, "max": values[-1] if values else None}


def csv_summary(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    missing = {field: sum(row.get(field) in (None, "") for row in rows) for field in fieldnames}
    symbol_field = _first_field(fieldnames, ("symbol", "ticker", "sym"))
    date_field = _first_field(fieldnames, ("scan_date", "signal_date", "date"))
    timestamp_field = _first_field(fieldnames, ("scan_ts", "signal_ts", "timestamp"))
    duplicate_counts = Counter(
        (row.get(symbol_field, ""), row.get(date_field, "")[:10])
        for row in rows
        if symbol_field and date_field and row.get(symbol_field) and row.get(date_field)
    )
    duplicate_keys = sum(count > 1 for count in duplicate_counts.values())
    duplicate_rows = sum(count - 1 for count in duplicate_counts.values() if count > 1)
    return {
        "kind": "csv",
        "rows": len(rows),
        "columns": fieldnames,
        "missingness": {
            field: {"count": count, "rate": round(count / len(rows), 6) if rows else 0.0}
            for field, count in missing.items()
        },
        "keys": {
            "symbol_field": symbol_field,
            "date_field": date_field,
            "timestamp_field": timestamp_field,
            "unique_symbol_days": len(duplicate_counts),
            "duplicate_symbol_day_keys": duplicate_keys,
            "duplicate_rows": duplicate_rows,
        },
        "date_range": _date_range(rows, date_field),
    }


def artifact_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "status": "missing"}
    if path.is_file():
        summary: dict[str, Any] = {
            "path": str(path),
            "status": "available",
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        if path.suffix.lower() == ".csv":
            summary["quality"] = csv_summary(path)
        else:
            summary["quality"] = {"kind": "binary_or_database", "inspection": "hash_only"}
        return summary

    files = sorted(item for item in path.rglob("*") if item.is_file())
    return {
        "path": str(path),
        "status": "available",
        "kind": "directory",
        "file_count": len(files),
        "bytes": sum(item.stat().st_size for item in files),
        "files": [
            {
                "path": str(item),
                "bytes": item.stat().st_size,
                "sha256": sha256_file(item),
            }
            for item in files
        ],
    }


def build_manifest(paths: tuple[Path, ...]) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "research_only": True,
        "label_warning": "resolved_pct_* fields are close-to-close proxies, not path-aware P&L",
        "inputs": [artifact_summary(path) for path in paths],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()

    paths = tuple(args.root / path for path in DEFAULT_INPUTS)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(build_manifest(paths), indent=2), encoding="utf-8")
    print(f"manifest={args.out}")
    print(f"inputs={len(paths)}")


if __name__ == "__main__":
    main()
