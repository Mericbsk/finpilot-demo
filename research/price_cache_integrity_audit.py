#!/usr/bin/env python3
"""Research-only audit for daily price-cache discontinuities."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import median


def _finite(value: object) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) and parsed > 0 else None


def load_bars(path: Path) -> list[dict]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return []
    bars = [
        item
        for item in raw
        if isinstance(item, dict) and item.get("date") and _finite(item.get("close"))
    ]
    return sorted(bars, key=lambda item: str(item["date"]))


def audit_symbol(path: Path, jump_threshold_pct: float, price_field: str = "close") -> dict:
    bars = load_bars(path)
    jumps = []
    for previous, current in zip(bars, bars[1:], strict=False):
        previous_close = _finite(previous.get(price_field))
        current_close = _finite(current.get(price_field))
        if previous_close is None or current_close is None:
            continue
        change_pct = (current_close / previous_close - 1.0) * 100.0
        if abs(change_pct) >= jump_threshold_pct:
            jumps.append(
                {
                    "from_date": previous["date"],
                    "to_date": current["date"],
                    "from_close": previous_close,
                    "to_close": current_close,
                    "change_pct": round(change_pct, 6),
                }
            )
    return {
        "symbol": path.stem,
        "price_field": price_field,
        "bars": len(bars),
        "date_start": bars[0]["date"] if bars else None,
        "date_end": bars[-1]["date"] if bars else None,
        "large_jump_count": len(jumps),
        "largest_abs_jump_pct": round(
            max((abs(item["change_pct"]) for item in jumps), default=0.0), 6
        ),
        "jumps": sorted(jumps, key=lambda item: abs(item["change_pct"]), reverse=True)[:10],
    }


def run(cache_dir: Path, jump_threshold_pct: float = 50.0, price_field: str = "close") -> dict:
    symbols = [
        audit_symbol(path, jump_threshold_pct, price_field)
        for path in sorted(cache_dir.glob("*.json"))
    ]
    flagged = [item for item in symbols if item["large_jump_count"]]
    all_jumps = [item["largest_abs_jump_pct"] for item in flagged if item["largest_abs_jump_pct"]]
    return {
        "status": "diagnostic_only",
        "cache": str(cache_dir),
        "jump_threshold_pct": jump_threshold_pct,
        "price_field": price_field,
        "symbols_scanned": len(symbols),
        "symbols_with_large_jumps": len(flagged),
        "largest_abs_jump_median_pct": round(median(all_jumps), 6) if all_jumps else None,
        "flagged_symbols": sorted(
            flagged, key=lambda item: item["largest_abs_jump_pct"], reverse=True
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=Path("data/price_cache"))
    parser.add_argument("--threshold-pct", type=float, default=50.0)
    parser.add_argument("--field", default="close", choices=("close", "adjusted_close"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/backtest_out/price_cache_integrity_audit_2026-08-07.json"),
    )
    args = parser.parse_args()
    result = run(args.cache, args.threshold_pct, args.field)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"OK -> {args.out}")
    print(
        json.dumps(
            {key: value for key, value in result.items() if key != "flagged_symbols"},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
