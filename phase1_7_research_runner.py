#!/usr/bin/env python3
"""Phased research runner for score, data-quality, combinations, costs and OOS.

This is research-only. It never changes scanner behavior and never pretends that
missing point-in-time inputs can be reconstructed from the enriched CSV.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import defaultdict
from datetime import UTC, datetime
from itertools import combinations
from statistics import median

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(ROOT, "data", "backtest_out", "full_universe_enriched.csv")
DEFAULT_OUT = os.path.join(ROOT, "data", "backtest_out", "phase1_7")
# Returns in the enriched artifact are percentage points, so costs are also
# represented in percentage points: 0.55 means a 0.55% round-trip cost.
COSTS = {"none": 0.0, "low": 0.3, "baseline": 0.55, "stress": 1.0}
MIN_N = 50


def number(value):
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def boolean(value):
    return str(value).strip().lower() in {"true", "1", "yes"}


def load_rows(path):
    rows = []
    with open(path, encoding="utf-8", newline="") as handle:
        for index, raw in enumerate(csv.DictReader(handle)):
            target = number(raw.get("resolved_pct_t5"))
            if target is None:
                continue
            rows.append(
                {
                    "id": f"{raw.get('symbol')}_{raw.get('scan_ts')}_{index}",
                    "symbol": (raw.get("symbol") or "").strip(),
                    "scan_ts": (raw.get("scan_ts") or "").strip(),
                    "scan_date": (raw.get("scan_date") or "").strip(),
                    "price": number(raw.get("price")),
                    "score": number(raw.get("score")),
                    "composite": number(raw.get("composite_score")),
                    "finpilot": number(raw.get("finpilot_score")),
                    "regime": boolean(raw.get("regime")),
                    "direction": boolean(raw.get("direction")),
                    "entry_ok": boolean(raw.get("entry_ok")),
                    "liquidity_ok": boolean(raw.get("liquidity_ok")),
                    "vol_regime": number(raw.get("vol_regime")),
                    "atr_pct": number(raw.get("atr_pct_real")),
                    "gap": number(raw.get("gap_pct")),
                    "rvol": number(raw.get("rvol")),
                    "dist52": number(raw.get("dist_52w_high")),
                    "ret5": target,
                    "target": target >= 5.0,
                }
            )
    return rows


def dedup(rows):
    seen = {}
    for row in rows:
        key = (row["symbol"], row["scan_date"])
        old = seen.get(key)
        if old is None or (row["scan_ts"], row["id"]) < (old["scan_ts"], old["id"]):
            seen[key] = row
    return list(seen.values())


def pct(value):
    return round(value * 100, 4) if value is not None else None


def mean(values):
    return sum(values) / len(values) if values else None


def max_drawdown(returns):
    equity = 1.0
    peak = 1.0
    worst = 0.0
    for value in returns:
        equity *= 1.0 + value / 100.0
        peak = max(peak, equity)
        worst = min(worst, (equity / peak - 1.0) * 100.0)
    return round(worst, 4)


def forward_metrics(rows, predicate=lambda row: True, cost=0.0):
    selected = [row for row in rows if predicate(row)]
    ordered = sorted(selected, key=lambda row: (row["scan_date"], row["scan_ts"], row["id"]))
    returns = [row["ret5"] - cost for row in ordered]
    wins = [value for value in returns if value > 0]
    losses = [-value for value in returns if value < 0]
    gross_loss = sum(losses)
    return {
        "n": len(selected),
        "coverage_pct": pct(len(selected) / len(rows)) if rows else None,
        "favorable_recall_pct": pct(
            sum(row["target"] for row in selected) / sum(row["target"] for row in rows)
        )
        if rows and any(row["target"] for row in rows)
        else None,
        "hit_rate_pct": pct(sum(row["target"] for row in selected) / len(selected))
        if selected
        else None,
        "mean_return_pct": round(mean(returns), 4) if returns else None,
        "median_return_pct": round(median(returns), 4) if returns else None,
        "profit_factor": round(sum(wins) / gross_loss, 4) if gross_loss else None,
        "max_drawdown_pct": max_drawdown(sorted(returns)) if returns else None,
        "months": len({row["scan_date"][:7] for row in selected if row["scan_date"]}),
        "daily_signal_count": round(
            len(selected) / len({row["scan_date"] for row in rows if row["scan_date"]}), 3
        )
        if rows
        else None,
        "cost_pct": cost,
    }


def monthly_metrics(rows, predicate, cost):
    groups = defaultdict(list)
    for row in rows:
        groups[row["scan_date"][:7]].append(row)
    output = []
    for month, group in sorted(groups.items()):
        selected = [row for row in group if predicate(row)]
        if selected:
            result = forward_metrics(group, predicate, cost)
            result["month"] = month
            output.append(result)
    positive = [
        item["mean_return_pct"] > 0 for item in output if item["mean_return_pct"] is not None
    ]
    return {
        "months": output,
        "months_positive": sum(positive),
        "months_tested": len(positive),
        "positive_month_ratio_pct": pct(sum(positive) / len(positive)) if positive else None,
    }


def predicates():
    return {
        "ATR>=4": lambda r: r["atr_pct"] is not None and r["atr_pct"] >= 4,
        "ATR>=6": lambda r: r["atr_pct"] is not None and r["atr_pct"] >= 6,
        "RVOL>=2": lambda r: r["rvol"] is not None and r["rvol"] >= 2,
        "gap>3": lambda r: r["gap"] is not None and r["gap"] > 3,
        "direction_up": lambda r: r["direction"],
        "regime_bull": lambda r: r["regime"],
        "raw_score>=3": lambda r: r["score"] is not None and r["score"] >= 3,
        "composite>=58": lambda r: r["composite"] is not None and r["composite"] >= 58,
        "composite>=70": lambda r: r["composite"] is not None and r["composite"] >= 70,
        "entry_ok": lambda r: r["entry_ok"],
        "not_near_52w_high": lambda r: r["dist52"] is None or r["dist52"] < 0.9,
    }


def family_for(name):
    if name.startswith("ATR"):
        return "volatility"
    if name.startswith("RVOL"):
        return "volume"
    if name.startswith("gap"):
        return "gap_event"
    if name in {"direction_up", "regime_bull"}:
        return "trend"
    if name.startswith("raw_score"):
        return "momentum"
    if name.startswith("composite"):
        return "composite"
    return "context"


def constrained_combinations(pred):
    names = list(pred)
    output = []
    for size in (2, 3, 4, 5, 6):
        for selected in combinations(names, size):
            families = [family_for(name) for name in selected]
            if any(
                families.count(family) > 1
                for family in {
                    "volatility",
                    "volume",
                    "gap_event",
                    "trend",
                    "momentum",
                    "composite",
                }
            ):
                continue
            if families.count("context") > 2:
                continue
            label = " AND ".join(selected)
            output.append(
                (label, lambda row, selected=selected: all(pred[name](row) for name in selected))
            )
    return output


def replay_contract(rows):
    required = {
        "scan_ts": "timestamp available",
        "symbol": "symbol available",
        "price": "entry price available",
        "score": "raw score available",
        "composite": "composite score available",
        "finpilot": "FinPilot score may be missing",
        "regime": "regime flag available",
        "direction": "direction flag available",
        "entry_ok": "entry decision available",
    }
    missing = {
        field: sum(row[field] is None or row[field] == "" for row in rows) for field in required
    }
    snapshot_match = sum(
        bool(row["scan_ts"]) and row["composite"] is not None and row["entry_ok"] is not None
        for row in rows
    )
    finpilot_equal = sum(
        row["finpilot"] is not None
        and row["composite"] is not None
        and abs(row["finpilot"] - row["composite"]) < 1e-9
        for row in rows
    )
    return {
        "status": "partial_replay_only",
        "available_contract": required,
        "missing_or_unavailable": {
            "timeframe_ohlcv_snapshots": "not present in enriched CSV",
            "feature_timestamps_and_age": "not present per feature",
            "spread_dollar_adv_estimated_impact": "not present",
            "canonical_reject_reason": "not present",
            "component_inputs_filter_score_alignment_momentum": "not present as raw fields",
        },
        "missing_counts": missing,
        "rows_with_same_snapshot_timestamp_and_entry_composite": snapshot_match,
        "finpilot_equals_composite_rows": finpilot_equal,
        "finpilot_equal_ratio_pct": pct(finpilot_equal / len(rows)) if rows else None,
        "explanation": "Full production replay is blocked until point-in-time timeframe inputs and component telemetry are persisted.",
    }


def quality_report(rows):
    atr_caps = {}
    for cap in (None, 50, 100, 200):
        kept = [
            row
            for row in rows
            if row["atr_pct"] is not None and (cap is None or row["atr_pct"] <= cap)
        ]
        atr_caps["none" if cap is None else str(cap)] = {
            "rows_kept": len(kept),
            "rows_excluded": len(rows) - len(kept),
            "excluded_pct": pct((len(rows) - len(kept)) / len(rows)) if rows else None,
        }
    suspicious = [
        row
        for row in rows
        if row["price"] is not None
        and row["price"] < 1
        or row["atr_pct"] is not None
        and row["atr_pct"] > 200
    ]
    return {
        "rows": len(rows),
        "symbols": len({row["symbol"] for row in rows}),
        "dates": len({row["scan_date"] for row in rows}),
        "symbol_day_rows": len(dedup(rows)),
        "duplicate_rows": len(rows) - len(dedup(rows)),
        "missing": {
            field: sum(row[field] is None for row in rows)
            for field in ("price", "score", "composite", "finpilot", "atr_pct", "gap", "rvol")
        },
        "atr_cap_scenarios": atr_caps,
        "suspicious_price_or_atr_rows": len(suspicious),
        "corporate_action_status": "not determinable from CSV; OHLC adjustment and split metadata absent",
        "dollar_adv_spread_status": "not available in CSV",
    }


def component_contract(rows):
    return {
        "status": "partial_component_breakdown",
        "available_rows_by_component": {
            "regime_contribution": sum(row["regime"] is not None for row in rows),
            "direction_contribution": sum(row["direction"] is not None for row in rows),
            "raw_score_contribution": sum(row["score"] is not None for row in rows),
        },
        "unavailable_components": {
            "filter_score": "volume_spike, price_momentum and trend_strength are not persisted",
            "alignment_ratio": "1h/4h/1d component values are not persisted",
            "momentum_ratio": "six momentum checks are not persisted",
            "optional_factors": "raw optional inputs are incomplete or missing",
        },
        "reconstructable_formula_prefix": "2*regime + 2*direction + 0.5*raw_score",
    }


def cap_sensitivity(rows, predicate):
    result = {}
    for cap in (None, 50, 100, 200):
        eligible = [
            row
            for row in rows
            if row["atr_pct"] is not None and (cap is None or row["atr_pct"] <= cap)
        ]
        result["none" if cap is None else str(cap)] = {
            "excluded_rows": len(rows) - len(eligible),
            "baseline_cost": forward_metrics(eligible, predicate, COSTS["baseline"]),
        }
    return result


def run(rows, out_dir):
    pred = predicates()
    canonical = dedup(rows)
    replay = replay_contract(rows)
    quality = quality_report(rows)
    thresholds = {}
    for name, predicate in pred.items():
        thresholds[name] = {
            "no_dedup": {
                label: {
                    "overall": forward_metrics(rows, predicate, cost),
                    "monthly": monthly_metrics(rows, predicate, cost),
                }
                for label, cost in COSTS.items()
            },
            "symbol_day": {
                label: {
                    "overall": forward_metrics(canonical, predicate, cost),
                    "monthly": monthly_metrics(canonical, predicate, cost),
                }
                for label, cost in COSTS.items()
            },
            "atr_cap_sensitivity": cap_sensitivity(canonical, predicate),
        }

    combos = []
    definitions = constrained_combinations(pred)
    dates = sorted({row["scan_date"] for row in canonical if row["scan_date"]})
    cut1 = dates[max(0, int(len(dates) * 0.50) - 1)] if dates else None
    cut2 = dates[max(0, int(len(dates) * 0.75) - 1)] if dates else None
    for label, predicate in definitions:
        discovery = [row for row in canonical if cut1 and row["scan_date"] <= cut1]
        validation = [row for row in canonical if cut1 and cut2 and cut1 < row["scan_date"] <= cut2]
        oos = [row for row in canonical if cut2 and row["scan_date"] > cut2]
        discovery_metric = forward_metrics(discovery, predicate, COSTS["baseline"])
        if discovery_metric["n"] < MIN_N:
            continue
        combos.append(
            {
                "label": label,
                "families": [family_for(name) for name in label.split(" AND ")],
                "discovery": discovery_metric,
                "validation": forward_metrics(validation, predicate, COSTS["baseline"]),
                "locked_oos": forward_metrics(oos, predicate, COSTS["baseline"]),
            }
        )
    combos.sort(
        key=lambda item: (
            item["discovery"]["mean_return_pct"] or -999,
            item["discovery"]["profit_factor"] or -999,
        ),
        reverse=True,
    )
    return {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "methodology": {
            "research_only": True,
            "primary_target": "resolved_pct_t5",
            "favorable_target": "resolved_pct_t5 >= 5%",
            "cost_scenarios": COSTS,
            "locked_split": {
                "discovery": "first 50% dates",
                "validation": "next 25% dates",
                "locked_oos": "last 25% dates",
            },
            "canonical_observation": "first scan timestamp per symbol-day",
            "combination_family_constraints": "one volatility, volume, gap/event, trend, momentum and composite factor; max two context factors",
        },
        "production_replay_contract": replay,
        "component_contract": component_contract(rows),
        "data_quality": quality,
        "single_factor_thresholds": thresholds,
        "constrained_combinations": combos,
        "candidate_count": len(combos),
        "top_discovery_candidates": combos[:20],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()
    rows = load_rows(args.csv)
    result = run(rows, args.out)
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "phase1_7_results.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    combo_path = os.path.join(args.out, "constrained_combinations.csv")
    with open(combo_path, "w", newline="", encoding="utf-8") as handle:
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
    print(f"OK -> {path}")
    print(f"OK -> {combo_path}")
    print(
        f"rows={len(rows)} canonical={len(dedup(rows))} constrained_candidates={len(result['constrained_combinations'])}"
    )
    print("replay_status=", result["production_replay_contract"]["status"])
    print("top_candidates:")
    for item in result["top_discovery_candidates"][:10]:
        print(item["label"], item["discovery"], "OOS", item["locked_oos"])


if __name__ == "__main__":
    main()
