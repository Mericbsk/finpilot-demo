#!/usr/bin/env python3
"""Audit point-in-time liquidity and feature freshness for V2 replay rows."""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter
from datetime import UTC, datetime

from p0_execution_replay import DISCOVERY_END, VALIDATION_END, load_bars, percentile_cut
from score_formula_comparison import add_scores, canonical, load_v2, number

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(ROOT, "data", "backtest_out", "enriched_signals_v3.csv")
DEFAULT_CACHE = os.path.join(ROOT, "data", "price_cache")
DEFAULT_OUT = os.path.join(ROOT, "data", "backtest_out", "v2_data_quality_cost")


def raw_rows(path: str) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def field_value(row: dict, names: tuple[str, ...]):
    for name in names:
        if row.get(name) not in (None, ""):
            return row[name]
    return None


def cache_adv(row: dict, cache_dir: str) -> float | None:
    bars = load_bars(cache_dir, row["symbol"])
    prior = [bar for bar in bars if bar["date"] < row["date"] and bar.get("volume") is not None]
    values = [
        float(bar["close"]) * float(bar["volume"])
        for bar in prior[-20:]
        if float(bar["close"]) > 0 and float(bar["volume"]) >= 0
    ]
    return sum(values) / len(values) if len(values) >= 5 else None


def spread_value(row: dict) -> float | None:
    direct = number(field_value(row, ("spread_bps",)))
    if direct is not None and direct >= 0:
        return direct
    bid = number(field_value(row, ("bid", "bid_price")))
    ask = number(field_value(row, ("ask", "ask_price")))
    if bid is not None and ask is not None and ask >= bid and (ask + bid) > 0:
        return (ask - bid) / ((ask + bid) / 2.0) * 10_000.0
    return None


def freshness_days(row: dict) -> float | None:
    value = field_value(row, ("short_interest_timestamp", "short_pit_timestamp", "short_as_of"))
    if not value:
        return None
    try:
        observed = datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
        signal = datetime.fromisoformat(row["date"]).date()
        return max(0.0, (signal - observed).days)
    except ValueError:
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--cache", default=DEFAULT_CACHE)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    source = raw_rows(args.csv)
    rows = add_scores(canonical(load_v2(args.csv)))
    raw_by_key = {}
    for raw in source:
        key = ((raw.get("symbol") or "").strip(), (raw.get("signal_date") or "")[:10])
        raw_by_key.setdefault(key, raw)
    for row in rows:
        raw = raw_by_key.get((row["symbol"], row["date"]), {})
        row["dollar_adv"] = cache_adv(row, args.cache)
        row["spread_bps"] = spread_value(raw)
        row["short_freshness_days"] = freshness_days(raw)

    discovery = [row for row in rows if row["date"] <= DISCOVERY_END]
    cut = percentile_cut(discovery, "v2_confirmation", 0.10)
    selected_oos = [
        row
        for row in rows
        if row["date"] > VALIDATION_END and cut is not None and row["v2_confirmation"] >= cut
    ]
    quality = {
        "canonical_rows": len(rows),
        "selected_locked_oos": len(selected_oos),
        "score_cut": cut,
        "dollar_adv_available": sum(row["dollar_adv"] is not None for row in rows),
        "spread_available": sum(row["spread_bps"] is not None for row in rows),
        "short_freshness_available": sum(row["short_freshness_days"] is not None for row in rows),
        "required_fields": {
            "spread_bps": "missing"
            if not any(row["spread_bps"] is not None for row in rows)
            else "available",
            "dollar_adv": "available_from_price_cache"
            if any(row["dollar_adv"] is not None for row in rows)
            else "missing",
            "short_interest_timestamp": "missing"
            if not any(row["short_freshness_days"] is not None for row in rows)
            else "available",
        },
    }
    freshness = Counter(
        "missing"
        if row["short_freshness_days"] is None
        else "<=7d"
        if row["short_freshness_days"] <= 7
        else "8-30d"
        if row["short_freshness_days"] <= 30
        else ">30d"
        for row in selected_oos
    )
    costs = {}
    for label, spread_bps, impact_bps in (
        ("baseline", 5.0, 0.0),
        ("spread_stress", 10.0, 0.0),
        ("impact_stress", 10.0, 10.0),
    ):
        eligible = [
            row
            for row in selected_oos
            if row["spread_bps"] is not None and row["dollar_adv"] is not None
        ]
        costs[label] = {
            "status": "measured" if eligible else "insufficient_data",
            "eligible_n": len(eligible),
            "spread_bps_assumption": spread_bps,
            "impact_bps_assumption": impact_bps,
            "note": "Execution replay is intentionally withheld until observed spread and ADV are available for the selected rows."
            if not eligible
            else "Eligible rows require observed spread and point-in-time ADV.",
        }
    result = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "methodology": {
            "research_only": True,
            "adv": "mean Close*Volume over prior 20 cached bars, strictly before signal date",
            "short_freshness": "signal date minus historical short-interest timestamp",
            "oos": {"validation_end": VALIDATION_END},
        },
        "quality": quality,
        "short_freshness_locked_oos": dict(freshness),
        "cost_stress": costs,
    }
    os.makedirs(args.out, exist_ok=True)
    with open(
        os.path.join(args.out, "v2_data_quality_cost_results.json"), "w", encoding="utf-8"
    ) as handle:
        json.dump(result, handle, indent=2)
    print(f"OK -> {args.out}\\v2_data_quality_cost_results.json")
    print("quality", quality)
    print("short_freshness_locked_oos", dict(freshness))
    print("cost_stress", costs)


if __name__ == "__main__":
    main()
