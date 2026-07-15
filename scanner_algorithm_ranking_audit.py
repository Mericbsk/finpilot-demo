#!/usr/bin/env python3
"""Hard audit of scanner filters and ranking using full-universe outcomes.

Research-only. This script does not change live scanner behavior and does not
reconstruct unavailable point-in-time features. It measures what is present in
the enriched full-universe artifact and labels missing evidence explicitly.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from datetime import UTC, datetime
from itertools import combinations

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(ROOT, "data", "backtest_out", "full_universe_enriched.csv")
DEFAULT_OUT = os.path.join(ROOT, "data", "backtest_out", "scanner_algorithm_ranking_audit.json")


def f(value):
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def b(value):
    return str(value).strip().lower() in {"true", "1", "yes"}


def load_rows(path):
    rows = []
    with open(path, encoding="utf-8", newline="") as handle:
        for index, raw in enumerate(csv.DictReader(handle)):
            target = f(raw.get("resolved_pct_t5"))
            rows.append(
                {
                    "id": f"{raw.get('symbol')}_{raw.get('scan_ts')}_{index}",
                    "symbol": (raw.get("symbol") or "").strip(),
                    "scan_date": (raw.get("scan_date") or "").strip(),
                    "price": f(raw.get("price")),
                    "score": f(raw.get("score")),
                    "composite": f(raw.get("composite_score")),
                    "entry_ok": b(raw.get("entry_ok")),
                    "liquidity_ok": b(raw.get("liquidity_ok")),
                    "regime": b(raw.get("regime")),
                    "direction": b(raw.get("direction")),
                    "squeeze": f(raw.get("squeeze_factor")),
                    "catalyst": f(raw.get("catalyst_factor")),
                    "sentiment": f(raw.get("sentiment")),
                    "gap": f(raw.get("gap_pct")),
                    "rvol": f(raw.get("rvol")),
                    "atr": f(raw.get("atr_pct_real")),
                    "dist52": f(raw.get("dist_52w_high")),
                    "target": target,
                }
            )
    return rows


def pct(value):
    return round(100.0 * value, 3) if value is not None else None


def mean(values):
    return sum(values) / len(values) if values else None


def median(values):
    values = sorted(values)
    if not values:
        return None
    return values[len(values) // 2]


def cohort_metrics(rows):
    targets = [row["target"] for row in rows if row["target"] is not None]
    if not targets:
        return {"n": 0}
    hits = [value >= 5.0 for value in targets]
    return {
        "n": len(targets),
        "hit_rate_5pct": pct(sum(hits) / len(hits)),
        "mean_t5_pct": round(mean(targets), 4),
        "median_t5_pct": round(median(targets), 4),
    }


def threshold_sensitivity(
    rows, field, thresholds, predicate=lambda value, threshold: value >= threshold
):
    output = []
    for threshold in thresholds:
        selected = [
            row for row in rows if row[field] is not None and predicate(row[field], threshold)
        ]
        result = cohort_metrics(selected)
        result.update(
            {
                "field": field,
                "threshold": threshold,
                "share_of_rows_pct": pct(len(selected) / len(rows)) if rows else None,
            }
        )
        output.append(result)
    return output


def gate_attrition(rows):
    names = [
        ("all", lambda row: True),
        ("regime", lambda row: row["regime"]),
        ("direction", lambda row: row["direction"]),
        ("raw_score_3", lambda row: row["score"] is not None and row["score"] >= 3),
        ("liquidity_ok", lambda row: row["liquidity_ok"]),
        ("entry_ok", lambda row: row["entry_ok"]),
    ]
    output = []
    active = rows
    previous = len(rows)
    for name, predicate in names:
        active = [row for row in active if predicate(row)]
        selected = active
        output.append(
            {
                "stage": name,
                "n": len(selected),
                "share_of_all_pct": pct(len(selected) / len(rows)) if rows else None,
                "incremental_retention_from_previous_pct": pct(len(selected) / previous)
                if previous
                else None,
                "cohort": cohort_metrics(selected),
            }
        )
        previous = len(selected)
    return output


def quantile_edges(values, buckets=10):
    values = sorted(values)
    if not values:
        return []
    edges = []
    for index in range(1, buckets):
        position = int((len(values) - 1) * index / buckets)
        edges.append(values[position])
    return edges


def decile_lift(rows, field):
    eligible = [row for row in rows if row[field] is not None and row["target"] is not None]
    if not eligible:
        return {"field": field, "buckets": []}
    edges = quantile_edges([row[field] for row in eligible])
    buckets = []
    for index in range(10):
        if index == 0:
            selected = [row for row in eligible if row[field] <= edges[0]]
        elif index == 9:
            selected = [row for row in eligible if row[field] > edges[-1]]
        else:
            selected = [row for row in eligible if edges[index - 1] < row[field] <= edges[index]]
        metrics = cohort_metrics(selected)
        metrics.update(
            {
                "bucket": index + 1,
                "min_value": min((row[field] for row in selected), default=None),
                "max_value": max((row[field] for row in selected), default=None),
            }
        )
        buckets.append(metrics)
    base = cohort_metrics(eligible)
    for bucket in buckets:
        bucket["lift_vs_base"] = (
            round(bucket["hit_rate_5pct"] / base["hit_rate_5pct"], 3)
            if bucket.get("hit_rate_5pct") is not None and base.get("hit_rate_5pct")
            else None
        )
    return {"field": field, "base": base, "buckets": buckets}


def pearson(rows, left, right):
    pairs = [
        (row[left], row[right]) for row in rows if row[left] is not None and row[right] is not None
    ]
    if len(pairs) < 3:
        return {"n": len(pairs), "correlation": None}
    x = [pair[0] for pair in pairs]
    y = [pair[1] for pair in pairs]
    mx, my = mean(x), mean(y)
    numerator = sum((a - mx) * (b - my) for a, b in pairs)
    denominator = math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
    return {
        "n": len(pairs),
        "correlation": round(numerator / denominator, 4) if denominator else None,
    }


def interaction(rows, name, predicate):
    selected = [row for row in rows if predicate(row)]
    complement = [row for row in rows if not predicate(row)]
    result = cohort_metrics(selected)
    result.update({"name": name, "complement": cohort_metrics(complement)})
    if result.get("hit_rate_5pct") is not None and result["complement"].get("hit_rate_5pct"):
        result["lift_vs_complement"] = round(
            result["hit_rate_5pct"] / result["complement"]["hit_rate_5pct"], 3
        )
    else:
        result["lift_vs_complement"] = None
    return result


def build_report(rows):
    numeric = ["score", "composite", "atr", "gap", "rvol", "squeeze", "sentiment", "dist52"]
    pairwise = [
        ("ATR6", lambda row: row["atr"] is not None and row["atr"] >= 6),
        ("RVOL2", lambda row: row["rvol"] is not None and row["rvol"] >= 2),
        (
            "ATR6_AND_RVOL2",
            lambda row: row["atr"] is not None
            and row["atr"] >= 6
            and row["rvol"] is not None
            and row["rvol"] >= 2,
        ),
        ("entry_ok", lambda row: row["entry_ok"]),
        (
            "ATR6_AND_ENTRY_OK",
            lambda row: row["atr"] is not None and row["atr"] >= 6 and row["entry_ok"],
        ),
    ]
    return {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "methodology": {
            "input_csv": "data/backtest_out/full_universe_enriched.csv",
            "target": "resolved_pct_t5 >= 5%",
            "research_only": True,
            "does_not_reconstruct_missing_point_in_time_features": True,
        },
        "inventory": {
            "rows": len(rows),
            "symbols": len({row["symbol"] for row in rows if row["symbol"]}),
            "scan_dates": len({row["scan_date"] for row in rows if row["scan_date"]}),
            "target_available": sum(row["target"] is not None for row in rows),
            "missing_fields": {field: sum(row[field] is None for row in rows) for field in numeric},
        },
        "gate_attrition": gate_attrition(rows),
        "threshold_sensitivity": {
            "score": threshold_sensitivity(rows, "score", [1, 2, 3, 5, 8, 10]),
            "composite": threshold_sensitivity(rows, "composite", [10, 20, 30, 40, 50, 60, 70, 80]),
            "atr": threshold_sensitivity(rows, "atr", [2, 4, 6, 10, 20, 50]),
            "gap": threshold_sensitivity(rows, "gap", [1, 3, 5, 10]),
            "rvol": threshold_sensitivity(rows, "rvol", [1.2, 2, 3, 5]),
        },
        "decile_lift": {
            field: decile_lift(rows, field)
            for field in ["score", "composite", "atr", "rvol", "gap"]
        },
        "redundancy": {
            "pairs": {
                f"{left}__{right}": pearson(rows, left, right)
                for left, right in combinations(numeric, 2)
            },
            "interpretation": "Correlation is a screening diagnostic, not proof of duplicate information or causality.",
        },
        "interactions": [interaction(rows, name, predicate) for name, predicate in pairwise],
        "static_findings": [
            "Production score is additive and uses fixed weights; no learned ranking model is present in this audit surface.",
            "Production evaluate_symbol hard-gates regime, direction, raw score and liquidity; alignment, momentum confluence and filter_score are emitted/used in composite but do not directly gate entry_ok.",
            "Regime x composite gate changes position sizing, not entry eligibility.",
            "Alert ranking is conviction_prob then composite_score when conviction tiers are enabled; otherwise all entry_ok rows pass through.",
            "Research-only ATR/RVOL rules are not live scanner criteria.",
        ],
        "limitations": [
            "Historical CSV fields are not a causal reconstruction of every live feature at every timestamp.",
            "The target is favorable movement, not cost-adjusted execution P&L.",
            "Correlation and threshold sweeps are exposed to multiple-testing and selection bias.",
            "Full-universe duplicate observations can be dependent; use symbol-day clustered inference for claims.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()
    rows = load_rows(args.csv)
    report = build_report(rows)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=True)
    print(f"OK -> {args.out}")
    print(f"rows={len(rows)} target_available={report['inventory']['target_available']}")
    for item in report["gate_attrition"]:
        print(
            f"{item['stage']:16s} n={item['n']:>6} share={item['share_of_all_pct']}% hit={item['cohort'].get('hit_rate_5pct')}%"
        )
    print("=== interactions ===")
    for item in report["interactions"]:
        print(
            f"{item['name']:20s} n={item['n']:>5} hit={item.get('hit_rate_5pct')}% lift={item.get('lift_vs_complement')}"
        )


if __name__ == "__main__":
    main()
