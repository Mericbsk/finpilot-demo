#!/usr/bin/env python3
"""Whole-universe precision-first signal selectivity battery.

Research-only. Runs baseline, threshold sweeps, filter ablation, constrained
confirmation rules, per-day top-N, regime splits, temporal OOS and symbol-day
cluster bootstrap on the enriched full-universe artifact.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
from collections import Counter, defaultdict
from datetime import UTC, datetime
from itertools import combinations
from statistics import mean, median

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(ROOT, "data", "backtest_out", "full_universe_enriched.csv")
DEFAULT_OUT = os.path.join(ROOT, "data", "backtest_out", "precision_selectivity")
COSTS = {"none": 0.0, "low": 0.30, "baseline": 0.55, "stress": 1.00}
MIN_N = 50


def num(value):
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
            ret5 = num(raw.get("resolved_pct_t5"))
            if ret5 is None:
                continue
            rows.append(
                {
                    "id": f"{raw.get('symbol')}_{raw.get('scan_ts')}_{index}",
                    "symbol": (raw.get("symbol") or "").strip(),
                    "scan_ts": (raw.get("scan_ts") or "").strip(),
                    "date": (raw.get("scan_date") or "").strip(),
                    "price": num(raw.get("price")),
                    "score": num(raw.get("score")),
                    "composite": num(raw.get("composite_score")),
                    "entry_ok": boolean(raw.get("entry_ok")),
                    "liquidity_ok": boolean(raw.get("liquidity_ok")),
                    "regime": boolean(raw.get("regime")),
                    "direction": boolean(raw.get("direction")),
                    "squeeze": num(raw.get("squeeze_factor")),
                    "catalyst": num(raw.get("catalyst_factor")),
                    "lottery": num(raw.get("lottery_factor")),
                    "sentiment": num(raw.get("sentiment")),
                    "vol_regime": num(raw.get("vol_regime")),
                    "atr": num(raw.get("atr_pct_real")),
                    "gap": num(raw.get("gap_pct")),
                    "rvol": num(raw.get("rvol")),
                    "dist52": num(raw.get("dist_52w_high")),
                    "ret1": num(raw.get("resolved_pct_1d")),
                    "ret5": ret5,
                    "target": ret5 >= 5.0,
                }
            )
    return rows


def dedup(rows):
    chosen = {}
    for row in rows:
        key = (row["symbol"], row["date"])
        old = chosen.get(key)
        if old is None or (row["scan_ts"], row["id"]) < (old["scan_ts"], old["id"]):
            chosen[key] = row
    return list(chosen.values())


def pct(value):
    return round(value * 100.0, 4) if value is not None else None


def wilson(successes, total, z=1.96):
    if not total:
        return None
    p = successes / total
    den = 1.0 + z * z / total
    centre = (p + z * z / (2.0 * total)) / den
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total) / den
    return [
        round(max(0.0, centre - margin) * 100.0, 3),
        round(min(1.0, centre + margin) * 100.0, 3),
    ]


def drawdown(values):
    equity = 1.0
    peak = 1.0
    worst = 0.0
    for value in values:
        equity *= 1.0 + value / 100.0
        peak = max(peak, equity)
        worst = min(worst, equity / peak - 1.0)
    return round(worst * 100.0, 4)


def metrics(selected, universe, cost=0.0):
    ordered = sorted(selected, key=lambda row: (row["date"], row["scan_ts"], row["id"]))
    returns = [row["ret5"] - cost for row in ordered]
    wins = [value for value in returns if value > 0]
    losses = [-value for value in returns if value < 0]
    base_hits = sum(row["target"] for row in universe)
    hit_count = sum(row["target"] for row in selected)
    result = {
        "n": len(selected),
        "unique_symbols": len({row["symbol"] for row in selected}),
        "coverage_pct": pct(len(selected) / len(universe)) if universe else None,
        "daily_signal_count": round(len(selected) / len({row["date"] for row in universe}), 3)
        if universe
        else None,
        "hit_rate_pct": pct(hit_count / len(selected)) if selected else None,
        "precision_pct": pct(hit_count / len(selected)) if selected else None,
        "favorable_recall_pct": pct(hit_count / base_hits) if base_hits else None,
        "false_positive_rate_pct": pct((len(selected) - hit_count) / len(selected))
        if selected
        else None,
        "mean_return_pct": round(mean(returns), 4) if returns else None,
        "median_return_pct": round(median(returns), 4) if returns else None,
        "profit_factor": round(sum(wins) / sum(losses), 4) if losses else None,
        "max_drawdown_pct": drawdown(returns) if returns else None,
        "wilson_hit_ci95_pct": wilson(hit_count, len(selected)),
        "cost_pct": cost,
        "avg_mfe_pct": None,
        "avg_mae_pct": None,
        "hold_time_outcome": "not available in enriched CSV; use barrier artifact",
    }
    base = hit_count / len(universe) if universe else None
    result["lift_vs_universe"] = (
        round((result["hit_rate_pct"] / (base * 100.0)), 4)
        if base and result["hit_rate_pct"] is not None
        else None
    )
    return result


def monthly(selected, universe, cost):
    groups = defaultdict(list)
    universe_groups = defaultdict(list)
    for row in selected:
        groups[row["date"][:7]].append(row)
    for row in universe:
        universe_groups[row["date"][:7]].append(row)
    month_rows = []
    for month in sorted(universe_groups):
        if groups.get(month):
            item = metrics(groups[month], universe_groups[month], cost)
            item["month"] = month
            month_rows.append(item)
    positive = [
        item["mean_return_pct"] > 0 for item in month_rows if item["mean_return_pct"] is not None
    ]
    return {
        "months": month_rows,
        "months_tested": len(positive),
        "months_positive": sum(positive),
        "positive_month_ratio_pct": pct(sum(positive) / len(positive)) if positive else None,
        "median_monthly_hit_rate_pct": round(
            median([item["hit_rate_pct"] for item in month_rows]), 4
        )
        if month_rows
        else None,
    }


def cluster_bootstrap(rows, predicate, repeats=400, seed=42):
    clusters = defaultdict(list)
    for row in rows:
        clusters[(row["symbol"], row["date"])].append(row)
    values = []
    for group in clusters.values():
        selected = [row for row in group if predicate(row)]
        values.append(
            (
                len(selected),
                sum(row["target"] for row in selected),
                len(group),
                sum(row["target"] for row in group),
            )
        )
    if not values:
        return None
    rng = random.Random(seed)
    lifts, deltas = [], []
    for _ in range(repeats):
        sample = [values[rng.randrange(len(values))] for _ in values]
        selected_n = sum(item[0] for item in sample)
        selected_hits = sum(item[1] for item in sample)
        universe_n = sum(item[2] for item in sample)
        universe_hits = sum(item[3] for item in sample)
        if selected_n and universe_n and universe_hits:
            sr = selected_hits / selected_n
            br = universe_hits / universe_n
            lifts.append(sr / br)
            deltas.append((sr - br) * 100.0)
    if not lifts:
        return None
    lifts.sort()
    deltas.sort()

    def q(values, p):
        return round(values[min(len(values) - 1, int(len(values) * p))], 4)

    return {
        "clusters": len(values),
        "repeats": repeats,
        "lift_median": q(lifts, 0.5),
        "lift_ci95": [q(lifts, 0.025), q(lifts, 0.975)],
        "delta_pp_median": q(deltas, 0.5),
        "delta_pp_ci95": [q(deltas, 0.025), q(deltas, 0.975)],
    }


def predicates():
    return {
        "regime_bull": lambda r: r["regime"],
        "direction_up": lambda r: r["direction"],
        "raw_score_3": lambda r: r["score"] is not None and r["score"] >= 3,
        "liquidity_ok": lambda r: r["liquidity_ok"],
        "entry_ok": lambda r: r["entry_ok"],
        "ATR>=2": lambda r: r["atr"] is not None and r["atr"] >= 2,
        "ATR>=4": lambda r: r["atr"] is not None and r["atr"] >= 4,
        "ATR>=6": lambda r: r["atr"] is not None and r["atr"] >= 6,
        "RVOL>=1.2": lambda r: r["rvol"] is not None and r["rvol"] >= 1.2,
        "RVOL>=2": lambda r: r["rvol"] is not None and r["rvol"] >= 2,
        "RVOL>=3": lambda r: r["rvol"] is not None and r["rvol"] >= 3,
        "gap>=1": lambda r: r["gap"] is not None and r["gap"] >= 1,
        "gap>=3": lambda r: r["gap"] is not None and r["gap"] >= 3,
        "gap>=5": lambda r: r["gap"] is not None and r["gap"] >= 5,
        "squeeze>=0.5": lambda r: r["squeeze"] is not None and r["squeeze"] >= 0.5,
        "composite>=58": lambda r: r["composite"] is not None and r["composite"] >= 58,
        "composite>=70": lambda r: r["composite"] is not None and r["composite"] >= 70,
        "composite>=80": lambda r: r["composite"] is not None and r["composite"] >= 80,
        "not_extended": lambda r: r["dist52"] is None or r["dist52"] < 0.9,
        "precision_core": lambda r: r["entry_ok"]
        and r["liquidity_ok"]
        and r["regime"]
        and r["direction"],
        "strict_confirmation": lambda r: r["entry_ok"]
        and r["liquidity_ok"]
        and r["regime"]
        and r["direction"]
        and r["atr"] is not None
        and r["atr"] >= 4
        and r["rvol"] is not None
        and r["rvol"] >= 1.2,
    }


def family(name):
    if name.startswith("ATR"):
        return "volatility"
    if name.startswith("RVOL"):
        return "volume"
    if name.startswith("gap"):
        return "gap"
    if name in {"regime_bull", "direction_up"}:
        return "trend"
    if name.startswith("raw_score") or name.startswith("composite"):
        return "score"
    if name in {"entry_ok", "liquidity_ok", "precision_core"}:
        return "gate"
    return "context"


def constrained_combinations(pred):
    names = list(pred)
    allowed = [name for name in names if name not in {"precision_core", "strict_confirmation"}]
    output = []
    for size in (2, 3):
        for selected in combinations(allowed, size):
            families = [family(name) for name in selected]
            if any(
                families.count(item) > 1
                for item in {"volatility", "volume", "gap", "trend", "score"}
            ):
                continue
            if families.count("gate") > 2:
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


def top_n_by_day(rows, rank_key, n):
    groups = defaultdict(list)
    for row in rows:
        groups[row["date"]].append(row)
    selected = []
    for group in groups.values():
        ranked = sorted(
            group,
            key=lambda row: (
                row.get(rank_key) is not None,
                row.get(rank_key) or -999999,
                row["symbol"],
            ),
            reverse=True,
        )
        selected.extend(ranked[:n])
    return selected


def top_percentile_by_day(rows, rank_key, percentile):
    groups = defaultdict(list)
    for row in rows:
        groups[row["date"]].append(row)
    selected = []
    for group in groups.values():
        ranked = sorted(
            group,
            key=lambda row: (row.get(rank_key) is not None, row.get(rank_key) or -999999),
            reverse=True,
        )
        count = max(1, math.ceil(len(ranked) * percentile))
        selected.extend(ranked[:count])
    return selected


def ranking_key(row):
    if row["composite"] is not None:
        return row["composite"]
    return -999999


def inventory(rows):
    return {
        "rows": len(rows),
        "symbols": len({r["symbol"] for r in rows}),
        "dates": len({r["date"] for r in rows}),
        "daily_rows_mean": round(len(rows) / len({r["date"] for r in rows}), 3) if rows else None,
        "daily_rows_min": min(Counter(r["date"] for r in rows).values(), default=0),
        "daily_rows_max": max(Counter(r["date"] for r in rows).values(), default=0),
        "entry_ok_rows": sum(r["entry_ok"] for r in rows),
        "entry_ok_daily_mean": round(
            sum(r["entry_ok"] for r in rows) / len({r["date"] for r in rows}), 3
        )
        if rows
        else None,
        "duplicate_symbol_day_rows": len(rows) - len(dedup(rows)),
        "missing": {
            field: sum(r[field] is None for r in rows)
            for field in ("composite", "atr", "gap", "rvol", "dist52", "ret1", "ret5")
        },
    }


def evaluate_rule(rows, universe, label, predicate, bootstrap, seed):
    selected = [row for row in rows if predicate(row)]
    return {
        "label": label,
        "overall": {name: metrics(selected, universe, cost) for name, cost in COSTS.items()},
        "monthly_baseline": monthly(selected, universe, COSTS["baseline"]),
        "cluster_bootstrap": cluster_bootstrap(rows, predicate, bootstrap, seed)
        if bootstrap
        else None,
    }


def temporal(rows, predicate):
    dates = sorted({r["date"] for r in rows})
    cut1 = dates[max(0, int(len(dates) * 0.50) - 1)] if dates else None
    cut2 = dates[max(0, int(len(dates) * 0.75) - 1)] if dates else None
    groups = {
        "discovery": [r for r in rows if cut1 and r["date"] <= cut1],
        "validation": [r for r in rows if cut1 and cut2 and cut1 < r["date"] <= cut2],
        "locked_oos": [r for r in rows if cut2 and r["date"] > cut2],
    }
    return {
        "split": {
            "discovery_end": cut1,
            "validation_end": cut2,
            "locked_oos_start_exclusive": cut2,
        },
        "metrics": {
            name: metrics([row for row in group if predicate(row)], group, COSTS["baseline"])
            for name, group in groups.items()
        },
    }


def run(rows, bootstrap, seed):
    pred = predicates()
    canonical = dedup(rows)
    base = {
        "all_universe": lambda r: True,
        "entry_ok": pred["entry_ok"],
        "precision_core": pred["precision_core"],
        "strict_confirmation": pred["strict_confirmation"],
    }
    baseline = {
        label: evaluate_rule(canonical, canonical, label, fn, bootstrap, seed)
        for label, fn in base.items()
    }

    thresholds = {}
    for label, fn in pred.items():
        thresholds[label] = evaluate_rule(canonical, canonical, label, fn, bootstrap, seed)

    ablation = {}
    for name in ("regime", "direction", "raw_score", "liquidity", "entry"):
        mapping = {
            "regime": "regime_bull",
            "direction": "direction_up",
            "raw_score": "raw_score_3",
            "liquidity": "liquidity_ok",
            "entry": "entry_ok",
        }
        gate = mapping[name]
        kept = [r for r in canonical if pred[gate](r)]
        ablation[f"remove_{name}"] = {
            "gate_removed_from_entry_ok": name,
            "cohort": metrics(kept, canonical, COSTS["baseline"]),
            "note": "retrospective ablation cohort; not a causal live replay",
        }

    combos = []
    for label, selected, fn in constrained_combinations(pred):
        item = evaluate_rule(canonical, canonical, label, fn, 0, seed)
        if item["overall"]["baseline"]["n"] >= MIN_N:
            item["families"] = [family(name) for name in selected]
            combos.append(item)
    combos.sort(
        key=lambda item: (
            item["overall"]["baseline"]["precision_pct"] or -999,
            item["overall"]["baseline"]["mean_return_pct"] or -999,
        ),
        reverse=True,
    )
    combo_predicates = {label: fn for label, _, fn in constrained_combinations(pred)}
    for item in combos[:20]:
        item["cluster_bootstrap"] = (
            cluster_bootstrap(canonical, combo_predicates[item["label"]], bootstrap, seed)
            if bootstrap
            else None
        )

    top_n = {}
    for n in (20, 50, 100, 200):
        selected = top_n_by_day(canonical, "composite", n)
        top_n[f"composite_top_{n}_per_day"] = {
            name: metrics(selected, canonical, cost) for name, cost in COSTS.items()
        }
    for fraction in (0.01, 0.05, 0.10, 0.20):
        selected = top_percentile_by_day(canonical, "composite", fraction)
        top_n[f"composite_top_{int(fraction * 100)}pct_per_day"] = {
            name: metrics(selected, canonical, cost) for name, cost in COSTS.items()
        }

    regimes = {}
    for label, fn in {
        "bull": lambda r: r["regime"],
        "bear": lambda r: not r["regime"],
        "high_vol": lambda r: r["vol_regime"] == 2,
        "normal_vol": lambda r: r["vol_regime"] == 1,
        "low_vol": lambda r: r["vol_regime"] == 0,
    }.items():
        subgroup = [r for r in canonical if fn(r)]
        regimes[label] = {
            "n": len(subgroup),
            "baseline": metrics(subgroup, subgroup, COSTS["baseline"]),
            "top_50": metrics(top_n_by_day(subgroup, "composite", 50), subgroup, COSTS["baseline"]),
        }

    oos_rules = {}
    for label, fn in {
        "entry_ok": pred["entry_ok"],
        "precision_core": pred["precision_core"],
        "strict_confirmation": pred["strict_confirmation"],
        "composite>=70": pred["composite>=70"],
        "ATR>=6": pred["ATR>=6"],
        "RVOL>=2": pred["RVOL>=2"],
    }.items():
        oos_rules[label] = temporal(canonical, fn)

    return {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "methodology": {
            "input": "data/backtest_out/full_universe_enriched.csv",
            "research_only": True,
            "primary_target": "resolved_pct_t5 >= 5%",
            "forward_target_warning": "not execution P&L; use barrier artifacts for path-dependent MFE/MAE and hold outcome",
            "costs_pct_points": COSTS,
            "canonicalization": "earliest scan timestamp per symbol-day",
            "cluster_bootstrap": f"symbol-day resampling, {bootstrap} repeats, seed {seed}; zero means not run",
            "top_n": "per scan date, ranked by composite_score",
        },
        "inventory_raw": inventory(rows),
        "inventory_canonical": inventory(canonical),
        "baseline": baseline,
        "thresholds": thresholds,
        "filter_ablation": ablation,
        "constrained_combinations_top100": combos[:100],
        "constrained_combination_count": len(combos),
        "top_n_and_percentile": top_n,
        "regime_splits": regimes,
        "temporal_oos": oos_rules,
        "limitations": [
            "MFE/MAE, exact hold-time outcome, spread and market impact are not present in this CSV and are not invented here.",
            "Forward target metrics can be distorted by corporate actions or price-scale anomalies.",
            "Threshold/combinations are discovery research; only locked OOS outputs should influence decisions.",
            "A retrospective filter ablation is not a causal replay because the original scanner was not rerun for each condition.",
        ],
    }


def write_csv(report, path):
    rows = []

    def add(section, label, item):
        base = item.get("baseline") or item.get("overall", {}).get("baseline") or item
        if not isinstance(base, dict):
            return
        rows.append(
            {
                "section": section,
                "label": label,
                **{
                    key: base.get(key)
                    for key in (
                        "n",
                        "unique_symbols",
                        "daily_signal_count",
                        "precision_pct",
                        "favorable_recall_pct",
                        "false_positive_rate_pct",
                        "mean_return_pct",
                        "median_return_pct",
                        "profit_factor",
                        "max_drawdown_pct",
                        "lift_vs_universe",
                        "cost_pct",
                    )
                },
            }
        )

    for label, item in report["baseline"].items():
        add("baseline", label, item)
    for label, item in report["thresholds"].items():
        add("threshold", label, item)
    for label, item in report["top_n_and_percentile"].items():
        add("top_n", label, item)
    for label, item in report["regime_splits"].items():
        add("regime_top50", label, item["top_50"])
    with open(path, "w", encoding="utf-8", newline="") as handle:
        fields = [
            "section",
            "label",
            "n",
            "unique_symbols",
            "daily_signal_count",
            "precision_pct",
            "favorable_recall_pct",
            "false_positive_rate_pct",
            "mean_return_pct",
            "median_return_pct",
            "profit_factor",
            "max_drawdown_pct",
            "lift_vs_universe",
            "cost_pct",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--bootstrap", type=int, default=400)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    rows = load_rows(args.csv)
    report = run(rows, args.bootstrap, args.seed)
    os.makedirs(args.out, exist_ok=True)
    json_path = os.path.join(args.out, "precision_selectivity_results.json")
    csv_path = os.path.join(args.out, "precision_selectivity_summary.csv")
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=True)
    write_csv(report, csv_path)
    print(f"OK -> {json_path}")
    print(f"OK -> {csv_path}")
    print("raw", report["inventory_raw"])
    print("canonical", report["inventory_canonical"])
    for label, item in report["baseline"].items():
        print(label, item["overall"]["baseline"])
    print("combination_count", report["constrained_combination_count"])


if __name__ == "__main__":
    main()
