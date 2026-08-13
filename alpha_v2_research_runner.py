#!/usr/bin/env python3
"""Alpha V2-only research battery.

Rebuilds the documented Alpha V2 score from point-in-time artifact fields and
runs the same threshold, canonical symbol-day, cost, combination and temporal
split checks as the generic phase runner. This is research-only.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import UTC, datetime
from itertools import combinations

from phase1_7_research_runner import (
    COSTS,
    MIN_N,
    dedup,
    forward_metrics,
    monthly_metrics,
    number,
)

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(ROOT, "data", "backtest_out", "enriched_signals_v3.csv")
DEFAULT_OUT = os.path.join(ROOT, "data", "backtest_out", "alpha_v2")


def alpha_v2_score(row):
    short = row["short"] if row["short"] is not None else 0.0
    atr = row["atr"] or 0.0
    gap = row["gap"] or 0.0
    rvol = row["rvol"] if row["rvol"] is not None else 1.0
    dist52 = row["dist52"] or 0.0
    short_n = min(short / 20.0, 1.0)
    atr_n = min(atr / 6.0, 1.0)
    gap_n = min(max(gap, 0.0) / 5.0, 1.0)
    rvol_n = min(max(rvol - 1.0, 0.0) / 2.0, 1.0)
    extension_n = min(max(dist52 - 0.9, 0.0) / 0.1, 1.0)
    return round(4 * short_n + 3 * atr_n + 3 * gap_n + 2 * rvol_n - 1.5 * extension_n, 6)


def load_rows(path):
    rows = []
    with open(path, encoding="utf-8", newline="") as handle:
        for index, raw in enumerate(csv.DictReader(handle)):
            target = number(raw.get("resolved_pct_t5"))
            if target is None:
                continue
            signal_date = raw.get("signal_date") or raw.get("scan_date") or raw.get("scan_ts") or ""
            row = {
                "id": f"{raw.get('symbol')}_{signal_date}_{index}",
                "symbol": (raw.get("symbol") or "").strip(),
                "scan_ts": signal_date.strip(),
                "scan_date": signal_date[:10],
                "price": number(raw.get("entry")),
                "short": number(raw.get("short_pit"))
                if raw.get("short_pit") not in (None, "")
                else number(raw.get("short_pct")),
                "atr": number(raw.get("atr_pct")),
                "gap": number(raw.get("gap_pct")),
                "rvol": number(raw.get("rvol")),
                "dist52": number(raw.get("dist_52w_high")),
                "ret5": target,
                "target": target >= 5.0,
                "legacy_score": number(raw.get("score")),
                "regime": str(raw.get("regime") or "").lower() in {"true", "1", "bull"},
                "direction": str(raw.get("direction") or "").lower() in {"true", "1", "up"},
            }
            row["alpha_v2_score"] = alpha_v2_score(row)
            row["alpha_v2_score_pct"] = round(
                max(0.0, min(100.0, row["alpha_v2_score"] / 12.0 * 100.0)), 4
            )
            rows.append(row)
    return rows


def quality(rows):
    return {
        "rows": len(rows),
        "symbols": len({r["symbol"] for r in rows}),
        "dates": len({r["scan_date"] for r in rows}),
        "symbol_day_rows": len(dedup(rows)),
        "duplicate_rows": len(rows) - len(dedup(rows)),
        "missing": {
            field: sum(r[field] is None for r in rows)
            for field in ("price", "short", "atr", "gap", "rvol", "dist52")
        },
        "atr_caps": {
            str(cap): sum(r["atr"] is not None and r["atr"] <= cap for r in rows)
            for cap in (50, 100, 200)
        },
        "corporate_action_status": "not determinable from source artifact",
        "spread_dollar_adv_status": "not available in source artifact",
    }


def predicates():
    return {
        "V2_score_top20": lambda r: r["alpha_v2_score_pct"] >= r.get("score20_cut", 0),
        "V2_score_top10": lambda r: r["alpha_v2_score_pct"] >= r.get("score10_cut", 0),
        "short>=15": lambda r: r["short"] is not None and r["short"] >= 15,
        "ATR>=3": lambda r: r["atr"] is not None and r["atr"] >= 3,
        "ATR>=6": lambda r: r["atr"] is not None and r["atr"] >= 6,
        "gap>=3": lambda r: r["gap"] is not None and r["gap"] >= 3,
        "RVOL>=2": lambda r: r["rvol"] is not None and r["rvol"] >= 2,
        "not_extended": lambda r: r["dist52"] is None or r["dist52"] < 0.9,
        "direction_up": lambda r: r["direction"],
    }


def family(name):
    if name.startswith("short"):
        return "short"
    if name.startswith("ATR"):
        return "volatility"
    if name.startswith("gap"):
        return "gap"
    if name.startswith("RVOL"):
        return "volume"
    if name.startswith("direction"):
        return "trend"
    if name.startswith("V2"):
        return "score"
    return "context"


def combinations_for(pred):
    names = list(pred)
    output = []
    for size in (2, 3, 4, 5):
        for selected in combinations(names, size):
            families = [family(name) for name in selected]
            if any(
                families.count(item) > 1
                for item in {"short", "volatility", "gap", "volume", "trend", "score"}
            ):
                continue
            label = " AND ".join(selected)
            output.append(
                (
                    label,
                    selected,
                    lambda row, selected=selected: all(pred[name](row) for name in selected),
                )
            )
    return output


def prepare_score_cuts(rows):
    values = sorted(r["alpha_v2_score_pct"] for r in rows)
    cut20 = values[max(0, int(len(values) * 0.80) - 1)] if values else 0
    cut10 = values[max(0, int(len(values) * 0.90) - 1)] if values else 0
    for row in rows:
        row["score20_cut"] = cut20
        row["score10_cut"] = cut10
    return cut20, cut10


def run(rows):
    pred = predicates()
    canonical = dedup(rows)
    dates = sorted({r["scan_date"] for r in canonical if r["scan_date"]})
    cut1 = dates[max(0, int(len(dates) * 0.50) - 1)] if dates else None
    cut2 = dates[max(0, int(len(dates) * 0.75) - 1)] if dates else None
    discovery_base = [r for r in canonical if cut1 and r["scan_date"] <= cut1]
    cut20, cut10 = prepare_score_cuts(discovery_base)
    for row in rows:
        row["score20_cut"] = cut20
        row["score10_cut"] = cut10
    thresholds = {}
    for name, fn in pred.items():
        thresholds[name] = {
            "symbol_day": {
                label: {
                    "overall": forward_metrics(canonical, fn, cost),
                    "monthly": monthly_metrics(canonical, fn, cost),
                }
                for label, cost in COSTS.items()
            }
        }
    combos = []
    for label, selected, fn in combinations_for(pred):
        discovery = [r for r in canonical if cut1 and r["scan_date"] <= cut1]
        validation = [r for r in canonical if cut1 and cut2 and cut1 < r["scan_date"] <= cut2]
        oos = [r for r in canonical if cut2 and r["scan_date"] > cut2]
        d = forward_metrics(discovery, fn, COSTS["baseline"])
        if d["n"] < MIN_N:
            continue
        combos.append(
            {
                "label": label,
                "families": [family(name) for name in selected],
                "discovery": d,
                "validation": forward_metrics(validation, fn, COSTS["baseline"]),
                "locked_oos": forward_metrics(oos, fn, COSTS["baseline"]),
            }
        )
    combos.sort(key=lambda item: (item["discovery"]["mean_return_pct"] or -999), reverse=True)
    return {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "profile": "alpha_v2_offline_score_v1",
        "source_contract": {
            "source": "enriched_signals_v3.csv",
            "formula": "4*short_n + 3*atr_n + 3*gap_n + 2*rvol_n - 1.5*extension_n",
            "short_source": "short_pit fallback short_pct",
            "score_normalization": "alpha_v2_score / 12 * 100 for ranking tests",
            "research_only": True,
        },
        "quality": quality(rows),
        "alpha_v2_score_cuts_pct": {"top20": cut20, "top10": cut10},
        "thresholds": thresholds,
        "split": {
            "discovery_end": cut1,
            "validation_end": cut2,
            "locked_oos_start_exclusive": cut2,
        },
        "constrained_combinations": combos,
        "candidate_count": len(combos),
    }


def write_barrier_input(rows, path):
    fields = [
        "symbol",
        "scan_ts",
        "scan_date",
        "price",
        "atr_pct_real",
        "entry_ok",
        "direction",
        "gap_pct",
        "rvol",
        "squeeze_factor",
        "composite_score",
        "dist_52w_high",
        "regime",
    ]
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "symbol": row["symbol"],
                    "scan_ts": row["scan_ts"],
                    "scan_date": row["scan_date"],
                    "price": row["price"],
                    "atr_pct_real": row["atr"],
                    "entry_ok": False,
                    "direction": row["direction"],
                    "gap_pct": row["gap"],
                    "rvol": row["rvol"],
                    "squeeze_factor": 0.0,
                    "composite_score": row["alpha_v2_score_pct"],
                    "dist_52w_high": row["dist52"],
                    "regime": row["regime"],
                }
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()
    rows = load_rows(args.csv)
    result = run(rows)
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "alpha_v2_results.json"), "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    write_barrier_input(rows, os.path.join(args.out, "alpha_v2_barrier_input.csv"))
    with open(
        os.path.join(args.out, "constrained_combinations.csv"), "w", encoding="utf-8", newline=""
    ) as handle:
        fields = [
            "label",
            "families",
            "discovery_n",
            "discovery_mean",
            "validation_n",
            "validation_mean",
            "oos_n",
            "oos_mean",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in result["constrained_combinations"]:
            writer.writerow(
                {
                    "label": item["label"],
                    "families": ",".join(item["families"]),
                    "discovery_n": item["discovery"]["n"],
                    "discovery_mean": item["discovery"]["mean_return_pct"],
                    "validation_n": item["validation"]["n"],
                    "validation_mean": item["validation"]["mean_return_pct"],
                    "oos_n": item["locked_oos"]["n"],
                    "oos_mean": item["locked_oos"]["mean_return_pct"],
                }
            )
    print(f"OK -> {args.out}\\alpha_v2_results.json")
    print(f"rows={len(rows)} canonical={len(dedup(rows))} candidates={result['candidate_count']}")
    print("score_cuts_pct", result["alpha_v2_score_cuts_pct"])
    for name in ("V2_score_top20", "V2_score_top10", "short>=15", "ATR>=6", "gap>=3", "RVOL>=2"):
        print(name, result["thresholds"][name]["symbol_day"]["baseline"]["overall"])


if __name__ == "__main__":
    main()
