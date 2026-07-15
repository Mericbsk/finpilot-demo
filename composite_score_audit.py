#!/usr/bin/env python3
"""Research-only composite score and ranking audit.

Measures score/rank separation in the existing full-universe artifact. It does
not change production scoring and does not claim that a favorable move is a
tradeable, cost-adjusted edge.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from collections import defaultdict
from datetime import UTC, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(ROOT, "data", "backtest_out", "full_universe_enriched.csv")
DEFAULT_BARRIER = os.path.join(ROOT, "data", "backtest_out", "full_universe_barrier_grid.csv")
DEFAULT_OUT = os.path.join(ROOT, "data", "backtest_out", "composite_score_audit.json")


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
            rows.append(
                {
                    "id": f"{raw.get('symbol')}_{raw.get('scan_ts')}_{index}",
                    "symbol": (raw.get("symbol") or "").strip(),
                    "date": (raw.get("scan_date") or "").strip(),
                    "score": number(raw.get("score")),
                    "composite": number(raw.get("composite_score")),
                    "finpilot": number(raw.get("finpilot_score")),
                    "entry_ok": boolean(raw.get("entry_ok")),
                    "regime": boolean(raw.get("regime")),
                    "direction": boolean(raw.get("direction")),
                    "tier": (raw.get("tier") or "").strip(),
                    "conviction": (raw.get("conviction_tier") or "").strip(),
                    "squeeze": number(raw.get("squeeze_factor")),
                    "sentiment": number(raw.get("sentiment")),
                    "gap": number(raw.get("gap_pct")),
                    "rvol": number(raw.get("rvol")),
                    "atr": number(raw.get("atr_pct_real")),
                    "ret_1d": number(raw.get("resolved_pct_1d")),
                    "ret_5d": number(raw.get("resolved_pct_t5")),
                }
            )
    return rows


def percent(value):
    return round(value * 100.0, 3) if value is not None else None


def mean(values):
    return sum(values) / len(values) if values else None


def median(values):
    ordered = sorted(values)
    return ordered[len(ordered) // 2] if ordered else None


def metrics(rows):
    labelled = [row for row in rows if row["ret_5d"] is not None]
    if not labelled:
        return {"n": 0, "hit_rate_5pct": None, "mean_ret5_pct": None, "median_ret5_pct": None}
    returns = [row["ret_5d"] for row in labelled]
    return {
        "n": len(labelled),
        "hit_rate_5pct": percent(sum(value >= 5.0 for value in returns) / len(returns)),
        "mean_ret5_pct": round(mean(returns), 4),
        "median_ret5_pct": round(median(returns), 4),
    }


def quantile_buckets(rows, field, bucket_count=10):
    eligible = [row for row in rows if row[field] is not None and row["ret_5d"] is not None]
    ordered = sorted(eligible, key=lambda row: row[field])
    if not ordered:
        return {"field": field, "base": metrics([]), "buckets": []}
    base = metrics(ordered)
    buckets = []
    for bucket in range(bucket_count):
        lo = bucket * len(ordered) // bucket_count
        hi = (bucket + 1) * len(ordered) // bucket_count
        selected = ordered[lo:hi]
        result = metrics(selected)
        result.update(
            {
                "bucket": bucket + 1,
                "min_value": selected[0][field] if selected else None,
                "max_value": selected[-1][field] if selected else None,
                "lift_vs_base": round(result["hit_rate_5pct"] / base["hit_rate_5pct"], 3)
                if result.get("hit_rate_5pct") is not None and base.get("hit_rate_5pct")
                else None,
            }
        )
        buckets.append(result)
    hit_rates = [
        bucket["hit_rate_5pct"] for bucket in buckets if bucket["hit_rate_5pct"] is not None
    ]
    monotonic_pairs = sum(
        right >= left for left, right in zip(hit_rates, hit_rates[1:], strict=False)
    )
    return {
        "field": field,
        "base": base,
        "buckets": buckets,
        "monotonic_adjacent_pairs": monotonic_pairs,
        "adjacent_pairs": max(len(hit_rates) - 1, 0),
        "monotonicity_ratio": round(monotonic_pairs / (len(hit_rates) - 1), 3)
        if len(hit_rates) > 1
        else None,
    }


def threshold_sweep(rows, field, thresholds):
    output = []
    for threshold in thresholds:
        selected = [row for row in rows if row[field] is not None and row[field] >= threshold]
        result = metrics(selected)
        result.update(
            {
                "field": field,
                "threshold": threshold,
                "coverage_pct": percent(len(selected) / len(rows)) if rows else None,
            }
        )
        output.append(result)
    return output


def tier_metrics(rows, field, order):
    output = []
    for value in order:
        selected = [row for row in rows if row[field] == value]
        result = metrics(selected)
        result.update(
            {
                "field": field,
                "value": value,
                "coverage_pct": percent(len(selected) / len(rows)) if rows else None,
            }
        )
        output.append(result)
    return output


def pearson(rows, left, right):
    pairs = [
        (row[left], row[right]) for row in rows if row[left] is not None and row[right] is not None
    ]
    if len(pairs) < 3:
        return {"n": len(pairs), "correlation": None}
    left_mean = mean([pair[0] for pair in pairs])
    right_mean = mean([pair[1] for pair in pairs])
    numerator = sum((a - left_mean) * (b - right_mean) for a, b in pairs)
    denominator = math.sqrt(
        sum((a - left_mean) ** 2 for a, _ in pairs) * sum((b - right_mean) ** 2 for _, b in pairs)
    )
    return {
        "n": len(pairs),
        "correlation": round(numerator / denominator, 4) if denominator else None,
    }


def monthly_top_overlap(rows, field, fraction=0.10):
    months = defaultdict(list)
    for row in rows:
        if row[field] is not None and row["symbol"] and row["date"]:
            months[row["date"][:7]].append(row)
    top_sets = {}
    for month, values in months.items():
        values = sorted(values, key=lambda row: row[field], reverse=True)
        count = max(1, int(len(values) * fraction))
        top_sets[month] = {row["symbol"] for row in values[:count]}
    overlaps = []
    ordered_months = sorted(top_sets)
    for previous, current in zip(ordered_months, ordered_months[1:], strict=False):
        left, right = top_sets[previous], top_sets[current]
        union = left | right
        overlaps.append(
            {
                "from": previous,
                "to": current,
                "jaccard_pct": percent(len(left & right) / len(union)) if union else None,
                "n_from": len(left),
                "n_to": len(right),
            }
        )
    return {
        "field": field,
        "months": len(top_sets),
        "mean_consecutive_jaccard_pct": round(mean([item["jaccard_pct"] for item in overlaps]), 3)
        if overlaps
        else None,
        "pairs": overlaps,
    }


def load_barrier_summary(path):
    if not os.path.exists(path):
        return {"available": False, "reason": "barrier grid not found"}
    wanted = []
    with open(path, encoding="utf-8", newline="") as handle:
        for raw in csv.DictReader(handle):
            if (
                raw.get("label")
                in {"all", "entry_ok", "ATR>=4", "ATR>=6", "ATR6+RVOL2", "ATR6+entry_ok"}
                and raw.get("config") == "tp=1.5xATR sl=0.75xATR h=3d"
            ):
                wanted.append(
                    {
                        key: number(raw.get(key))
                        if key not in {"config", "label"}
                        else raw.get(key)
                        for key in (
                            "config",
                            "label",
                            "n",
                            "tp_rate",
                            "sl_rate",
                            "time_rate",
                            "win_rate",
                            "expectancy_pct",
                            "median_return_pct",
                            "profit_factor",
                            "avg_mfe_pct",
                            "avg_mae_pct",
                            "avg_bars",
                        )
                    }
                )
    return {"available": True, "config": "tp=1.5xATR sl=0.75xATR h=3d", "rows": wanted}


def build_report(rows, barrier_path):
    fields = ["score", "composite", "finpilot", "atr", "gap", "rvol", "squeeze", "sentiment"]
    all_metrics = metrics(rows)
    high_score = [row for row in rows if row["composite"] is not None and row["composite"] > 58]
    low_score = [row for row in rows if row["composite"] is not None and row["composite"] <= 58]
    return {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "methodology": {
            "input_csv": "data/backtest_out/full_universe_enriched.csv",
            "target": "resolved_pct_t5 >= 5% and resolved_pct_t5 return",
            "ranking_metric": "composite_score descending; equal-score rows retain artifact order",
            "research_only": True,
            "cost_adjusted": False,
        },
        "score_taxonomy": {
            "raw_score": {
                "range": "0-3",
                "meaning": "RSI, volume, rising-positive MACD confirmation",
                "entry_effect": "hard gate requires exactly 3",
            },
            "composite_score": {
                "range": "0-100",
                "meaning": "additive recommendation strength normalized by fixed 16.5 ceiling",
                "entry_effect": "computed after entry gate; not eligibility",
            },
            "finpilot_score": {
                "range": "0-100",
                "meaning": "scanner composite pass-through while DRL weight is 0",
                "entry_effect": "no independent gate in current configuration",
            },
            "conviction": {
                "meaning": "A/B/C label and observed probability",
                "entry_effect": "alert/summary ordering when enabled; does not change composite",
            },
            "exit_score": {
                "status": "not implemented as a production decision surface",
                "current_exit": "ATR stop/TP or time exit",
            },
        },
        "inventory": {
            "rows": len(rows),
            "symbols": len({row["symbol"] for row in rows if row["symbol"]}),
            "dates": len({row["date"] for row in rows if row["date"]}),
            "labelled": all_metrics["n"],
            "base": all_metrics,
            "missing_fields": {field: sum(row[field] is None for row in rows) for field in fields},
        },
        "component_weights": {
            "regime": 2.0,
            "direction": 2.0,
            "raw_score": 0.5,
            "filter_score": 1.5,
            "alignment_ratio": 2.0,
            "momentum_ratio": {"low_vol": 2.5, "normal": 2.0, "high_vol": 1.5},
            "volume_spike": 0.5,
            "price_momentum": 0.5,
            "trend_strength": 0.5,
            "sentiment_range": "-0.5 to +0.5",
            "squeeze_optional": 1.5,
            "catalyst_optional": "-1.5 to +1.5",
            "lottery_optional_penalty": -2.0,
            "overnight_optional_penalty": -1.0,
            "normalization_ceiling": 16.5,
        },
        "score_distribution": {
            "composite_deciles": quantile_buckets(rows, "composite"),
            "raw_score_buckets": tier_metrics(rows, "score", [0.0, 1.0, 2.0, 3.0]),
            "composite_gt_58": metrics(high_score),
            "composite_le_58": metrics(low_score),
        },
        "rank_performance": {
            "deciles": {
                field: quantile_buckets(rows, field)
                for field in ["composite", "score", "finpilot", "atr", "gap", "rvol"]
            },
            "thresholds": {
                "composite": threshold_sweep(rows, "composite", [20, 30, 40, 50, 58, 60, 70, 80]),
                "score": threshold_sweep(rows, "score", [1, 2, 3]),
                "finpilot": threshold_sweep(rows, "finpilot", [20, 40, 50, 60, 70, 80]),
            },
            "tiers": {
                "conviction": tier_metrics(rows, "conviction", ["A", "B", "C", ""]),
                "entry_ok": [
                    {
                        **metrics([row for row in rows if row["entry_ok"] is value]),
                        "field": "entry_ok",
                        "value": value,
                    }
                    for value in [True, False]
                ],
            },
            "top_rank_stability": monthly_top_overlap(rows, "composite"),
        },
        "redundancy": {
            "correlations": {
                f"{left}__{right}": pearson(rows, left, right)
                for left, right in [
                    ("composite", "score"),
                    ("composite", "finpilot"),
                    ("composite", "atr"),
                    ("composite", "gap"),
                    ("composite", "rvol"),
                    ("gap", "rvol"),
                    ("atr", "rvol"),
                ]
            },
            "static_groups": [
                {
                    "group": "trend",
                    "components": ["regime", "direction", "trend_strength", "EMA gap"],
                    "risk": "same trend state rewarded in multiple layers",
                },
                {
                    "group": "momentum",
                    "components": [
                        "raw MACD",
                        "price_momentum",
                        "momentum_ratio",
                        "alignment",
                        "confluence",
                    ],
                    "risk": "same price movement counted across horizons",
                },
                {
                    "group": "volume",
                    "components": ["raw volume x1.2", "volume_spike", "RVOL"],
                    "risk": "volume event can receive repeated credit",
                },
                {
                    "group": "event sentiment",
                    "components": ["catalyst", "sentiment", "squeeze"],
                    "risk": "news/event family may be double counted when enabled",
                },
            ],
        },
        "entry_exit_audit": {
            "entry_score": "raw score is a hard eligibility confirmation; composite is calculated later and ranks/sizes rather than admits",
            "exit_score": "no production exit score field or update loop found",
            "strategy_selection": "momentum_score >=70 Sniper; <50 Defansif; 50-69 Normal",
            "exit_logic": "ATR/Yang-Zhang-derived stop and TP levels, forward barrier TP/SL/time exit in research",
            "score_decay": "not implemented",
            "freshness": "timestamp exists, but no score-aging rule is applied",
        },
        "barrier_backtest": load_barrier_summary(barrier_path),
        "findings": [
            "Composite ranking is not proven monotonic until its decile table shows stable adjacent increases; the audit reports the monotonicity ratio explicitly.",
            "A high composite score is not an entry decision: entry_ok is upstream and raw score/regime/direction/liquidity dominate eligibility.",
            "FinPilot score currently adds no independent information because the DRL weight is zero.",
            "Conviction probability and composite score are different ranking languages; alert paths can prioritize conviction before composite.",
            "No exit score means entry ranking and exit management are asymmetric; exit quality cannot be attributed to a score without a new logged decision surface.",
        ],
        "limitations": [
            "Full-universe CSV lacks component-level filter_score, alignment, momentum_ratio, MFE, MAE and hold-time fields.",
            "Barrier grid is ATR-scaled research output and is not a composite-score backtest unless score predicates are explicitly replayed through the barrier engine.",
            "No transaction costs, spread, slippage or clustered confidence intervals are calculated here.",
            "Threshold and decile sweeps are exploratory and exposed to multiple-testing bias.",
        ],
        "recommendations": {
            "p0": [
                "Add score_component_breakdown and reject_reason telemetry to every emitted row",
                "Create a canonical score/ranking contract",
                "Replay score and entry decisions point-in-time",
            ],
            "p1": [
                "Replace duplicated trend/volume/momentum credits with orthogonal groups",
                "Backtest score deciles and top-N under locked OOS and symbol-day clustering",
                "Keep exit logic separate until an exit score has independent evidence",
            ],
            "p2": [
                "Test quantile/adaptive rank cutoffs by regime",
                "Add score freshness/decay only with trade-lifecycle evidence",
                "Add explicit score-vs-MFE/MAE and hold-time logging",
            ],
            "p3": [
                "Consider a learned ranker only after the additive baseline has a clean replay contract",
                "Retire unused score vocabularies and reporting-only fields",
            ],
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--barrier", default=DEFAULT_BARRIER)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()
    rows = load_rows(args.csv)
    report = build_report(rows, args.barrier)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=True)
    composite = report["rank_performance"]["deciles"]["composite"]
    print(f"OK -> {args.out}")
    print(
        f"rows={len(rows)} symbols={report['inventory']['symbols']} dates={report['inventory']['dates']}"
    )
    print(f"composite_monotonicity={composite.get('monotonicity_ratio')}")
    for item in report["rank_performance"]["thresholds"]["composite"]:
        print(
            f"composite>={item['threshold']:>3} n={item['n']:>6} coverage={item['coverage_pct']}% hit={item['hit_rate_5pct']}%"
        )


if __name__ == "__main__":
    main()
