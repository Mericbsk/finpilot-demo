#!/usr/bin/env python3
"""Backfill adjusted-close metadata for flagged daily cache symbols."""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
from datetime import date
from pathlib import Path

import requests
from refresh_price_cache import gather_symbols

from research.price_cache_integrity_audit import load_bars
from research.price_cache_integrity_audit import run as audit_cache


def load_env(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("EODHD_API_KEY="):
            return line.split("=", 1)[1].strip().strip("\"'")
    return ""


def fetch_history(symbol: str, api_key: str, start: str, end: str) -> list[dict] | None:
    url = f"https://eodhd.com/api/eod/{symbol.replace('.', '-')}.US"
    try:
        response = requests.get(
            url,
            params={"api_token": api_key, "fmt": "json", "from": start, "to": end, "period": "d"},
            timeout=30,
        )
    except requests.RequestException:
        return None
    if response.status_code == 429:
        return None
    if response.status_code != 200:
        return []
    try:
        raw = response.json()
    except ValueError:
        return None
    return (
        [item for item in raw if isinstance(item, dict) and item.get("date")]
        if isinstance(raw, list)
        else []
    )


def merge_history(path: Path, history: list[dict]) -> int:
    existing = {item["date"]: item for item in load_bars(path)}
    changed = 0
    for item in history:
        current = existing.get(item["date"], {})
        merged = {
            **current,
            **{
                key: item.get(key)
                for key in ("open", "high", "low", "close", "adjusted_close", "volume")
                if key in item
            },
        }
        if merged != current:
            changed += 1
        existing[item["date"]] = merged
    output = [existing[key] for key in sorted(existing)]
    temporary = path.with_suffix(".backfill.tmp")
    temporary.write_text(json.dumps(output), encoding="utf-8")
    os.replace(temporary, path)
    return changed


def canonical_symbols(csv_path: Path | None, ledger_path: Path | None = None) -> set[str] | None:
    if ledger_path is not None:
        eligible, _ = gather_symbols(False, None)
        return {symbol for symbol, _ in eligible}
    if csv_path is None:
        return None
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return {row["symbol"] for row in csv.DictReader(handle) if row.get("symbol")}


def run(
    cache_dir: Path,
    env_path: Path,
    threshold_pct: float,
    sleep_seconds: float,
    csv_path: Path | None = None,
    ledger_path: Path | None = None,
) -> dict:
    api_key = load_env(env_path)
    if not api_key:
        raise RuntimeError("EODHD_API_KEY is missing from the environment file")
    audit = audit_cache(cache_dir, threshold_pct)
    requested_symbols = canonical_symbols(csv_path, ledger_path)
    flagged = [
        item
        for item in audit["flagged_symbols"]
        if requested_symbols is None or item["symbol"] in requested_symbols
    ]
    today = date.today().isoformat()
    completed = failed = skipped = changed = 0
    failures = []
    for item in flagged:
        symbol = item["symbol"]
        path = cache_dir / f"{symbol}.json"
        start = item["date_start"] or (today[:4] + "-01-01")
        history = None
        for attempt in range(3):
            history = fetch_history(symbol, api_key, start, today)
            if history is not None:
                break
            time.sleep(1.5 * (attempt + 1))
        if history is None:
            failed += 1
            failures.append(symbol)
        elif not history:
            skipped += 1
        else:
            changed += merge_history(path, history)
            completed += 1
        time.sleep(sleep_seconds)
    return {
        "status": "completed" if not failures else "partial",
        "threshold_pct": threshold_pct,
        "canonical_filter": str(ledger_path or csv_path) if (ledger_path or csv_path) else None,
        "flagged_before": len(flagged),
        "symbols_completed": completed,
        "symbols_failed": failed,
        "symbols_without_response": skipped,
        "bars_changed": changed,
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=Path("data/price_cache"))
    parser.add_argument("--env", type=Path, default=Path(".env"))
    parser.add_argument("--threshold-pct", type=float, default=50.0)
    parser.add_argument("--csv", type=Path, default=None)
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/backtest_out/adjusted_cache_backfill_2026-08-07.json"),
    )
    args = parser.parse_args()
    result = run(args.cache, args.env, args.threshold_pct, args.sleep, args.csv, args.ledger)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"OK -> {args.out}")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
