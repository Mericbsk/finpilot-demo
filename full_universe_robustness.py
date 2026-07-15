#!/usr/bin/env python3
"""Full-universe robustness and combination battery.

Reads the enriched full-universe CSV and evaluates:
- configurable two- through six-factor combinations on the primary forward target;
- the proposed volatility-first rules;
- no-dedup versus one-observation-per-symbol-day;
- monthly and half-period stability;
- cluster bootstrap intervals using symbol-day clusters.

This is an analysis layer only. It does not change scanner or live scoring behavior.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
from collections import defaultdict
from datetime import UTC, datetime
from itertools import combinations

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(ROOT, "data", "backtest_out", "full_universe_enriched.csv")
DEFAULT_OUT = os.path.join(ROOT, "data", "backtest_out")
PRIMARY = "Y_5pct_5d"
DEFAULT_BOOTSTRAPS = 400
MIN_N = 50


def _f(value):
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def _b(value):
    return str(value).strip().lower() in {"true", "1", "yes"}


def load_rows(path):
    rows = []
    with open(path, encoding="utf-8", newline="") as handle:
        for index, data in enumerate(csv.DictReader(handle)):
            target = _f(data.get("resolved_pct_t5"))
            if target is None:
                continue
            rows.append(
                {
                    "id": f"{data.get('symbol')}_{data.get('scan_ts')}_{index}",
                    "symbol": (data.get("symbol") or "").strip(),
                    "scan_date": (data.get("scan_date") or "").strip(),
                    "entry_ok": _b(data.get("entry_ok")),
                    "direction": _b(data.get("direction")),
                    "target": target >= 5.0,
                    "ret5": target,
                    "atr": _f(data.get("atr_pct_real")),
                    "gap": _f(data.get("gap_pct")),
                    "rvol": _f(data.get("rvol")),
                    "squeeze": _f(data.get("squeeze_factor")),
                    "composite": _f(data.get("composite_score")),
                    "score": _f(data.get("score")),
                    "dist52": _f(data.get("dist_52w_high")),
                    "regime": (data.get("regime") or "").strip(),
                }
            )
    return rows


def dedup_symbol_day(rows):
    seen = {}
    for row in rows:
        seen.setdefault((row["symbol"], row["scan_date"]), row)
    return list(seen.values())


def wilson(successes, total, z=1.96):
    if not total:
        return None
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return [round(max(0.0, centre - margin), 4), round(min(1.0, centre + margin), 4)]


def p_value(successes, total, control_successes, control_total):
    if not total or not control_total:
        return None
    p1 = successes / total
    p2 = control_successes / control_total
    pooled = (successes + control_successes) / (total + control_total)
    se = math.sqrt(pooled * (1 - pooled) * (1 / total + 1 / control_total))
    if not se:
        return 1.0
    z = abs((p1 - p2) / se)
    return 2 * (1 - 0.5 * (1 + math.erf(z / math.sqrt(2))))


def metric(rows, label, predicate, universe=None):
    universe = rows if universe is None else universe
    selected = [row for row in rows if predicate(row)]
    control = [row for row in universe if not predicate(row)]
    successes = sum(row["target"] for row in selected)
    base_successes = sum(row["target"] for row in universe)
    control_successes = sum(row["target"] for row in control)
    n = len(selected)
    base_n = len(universe)
    hit = successes / n if n else None
    base = base_successes / base_n if base_n else None
    return {
        "label": label,
        "n": n,
        "hit_rate": round(hit, 4) if hit is not None else None,
        "base_rate": round(base, 4) if base is not None else None,
        "lift": round(hit / base, 3) if hit is not None and base else None,
        "delta_pp": round((hit - base) * 100, 2) if hit is not None and base is not None else None,
        "ci95": wilson(successes, n),
        "control_n": len(control),
        "control_hit_rate": round(control_successes / len(control), 4) if control else None,
        "p": p_value(successes, n, control_successes, len(control)),
        "mean_ret5": round(float(np.mean([row["ret5"] for row in selected])), 3)
        if selected
        else None,
        "median_ret5": round(float(np.median([row["ret5"] for row in selected])), 3)
        if selected
        else None,
    }


def factor_predicates():
    return {
        "ATR>=4": lambda row: row["atr"] is not None and row["atr"] >= 4,
        "ATR>=6": lambda row: row["atr"] is not None and row["atr"] >= 6,
        "gap>3": lambda row: row["gap"] is not None and row["gap"] > 3,
        "gap>5": lambda row: row["gap"] is not None and row["gap"] > 5,
        "RVOL>=2": lambda row: row["rvol"] is not None and row["rvol"] >= 2,
        "squeeze>=0.5": lambda row: row["squeeze"] is not None and row["squeeze"] >= 0.5,
        "squeeze>=0.7": lambda row: row["squeeze"] is not None and row["squeeze"] >= 0.7,
        "entry_ok": lambda row: row["entry_ok"],
        "direction_up": lambda row: row["direction"],
        "composite>=70": lambda row: row["composite"] is not None and row["composite"] >= 70,
        "composite>=80": lambda row: row["composite"] is not None and row["composite"] >= 80,
        "not_near_52w_high": lambda row: row["dist52"] is None or row["dist52"] < 0.9,
    }


def combination_definitions(sizes=(2, 3)):
    predicates = factor_predicates()
    definitions = []
    names = list(predicates)
    for size in sizes:
        if size < 2 or size > len(names):
            raise ValueError(f"Combination size must be between 2 and {len(names)}: {size}")
        for selected_names in combinations(names, size):
            label = " AND ".join(selected_names)

            def combined(row, selected_names=selected_names):
                return all(predicates[name](row) for name in selected_names)

            definitions.append((label, combined))
    return definitions


def combination_results(rows, sizes=(2, 3)):
    results = []
    for label, predicate in combination_definitions(sizes):
        result = metric(rows, label, predicate)
        if result["n"] >= MIN_N:
            results.append(result)
    return sorted(results, key=lambda item: (item["lift"] or -999, item["n"]), reverse=True)


def recommended_rules(rows):
    predicates = factor_predicates()
    rules = {
        "volatility_first_ATR4": predicates["ATR>=4"],
        "volatility_first_ATR6": predicates["ATR>=6"],
        "ATR4_plus_confirmation": lambda row: predicates["ATR>=4"](row)
        and (
            predicates["gap>3"](row)
            or predicates["squeeze>=0.5"](row)
            or predicates["RVOL>=2"](row)
        ),
        "ATR6_plus_confirmation": lambda row: predicates["ATR>=6"](row)
        and (
            predicates["gap>3"](row)
            or predicates["squeeze>=0.5"](row)
            or predicates["RVOL>=2"](row)
        ),
        "ATR4_gap3_squeeze05": lambda row: predicates["ATR>=4"](row)
        and predicates["gap>3"](row)
        and predicates["squeeze>=0.5"](row),
        "ATR6_gap3_or_squeeze05": lambda row: predicates["ATR>=6"](row)
        and (predicates["gap>3"](row) or predicates["squeeze>=0.5"](row)),
        "ATR4_entry_ok": lambda row: predicates["ATR>=4"](row) and predicates["entry_ok"](row),
        "ATR6_entry_ok": lambda row: predicates["ATR>=6"](row) and predicates["entry_ok"](row),
        "ATR4_direction": lambda row: predicates["ATR>=4"](row) and predicates["direction_up"](row),
        "ATR6_direction": lambda row: predicates["ATR>=6"](row) and predicates["direction_up"](row),
        "ATR4_entry_confirmation": lambda row: predicates["ATR>=4"](row)
        and predicates["entry_ok"](row)
        and (
            predicates["gap>3"](row)
            or predicates["squeeze>=0.5"](row)
            or predicates["RVOL>=2"](row)
        ),
    }
    return [metric(rows, label, predicate) for label, predicate in rules.items()]


def period_stability(rows, predicate):
    periods = defaultdict(list)
    for row in rows:
        month = row["scan_date"][:7] if row["scan_date"] else "unknown"
        periods[month].append(row)
    ordered = sorted(periods.items())
    half = max(1, len(ordered) // 2)
    groups = {
        "first_half": [row for _, group in ordered[:half] for row in group],
        "second_half": [row for _, group in ordered[half:] for row in group],
    }
    out = {name: metric(group, name, predicate) for name, group in groups.items() if group}
    out["monthly"] = [
        metric(group, month, predicate) for month, group in ordered if len(group) >= MIN_N
    ]
    valid = [item for item in out["monthly"] if item["lift"] is not None]
    out["monthly_summary"] = {
        "months_tested": len(valid),
        "months_lift_gt_1": sum(item["lift"] > 1 for item in valid),
        "median_monthly_lift": round(float(np.median([item["lift"] for item in valid])), 3)
        if valid
        else None,
    }
    return out


def cluster_bootstrap(rows, predicate, repeats, seed):
    clusters = defaultdict(list)
    for row in rows:
        clusters[(row["symbol"], row["scan_date"])].append(row)
    cluster_values = []
    for group in clusters.values():
        selected = [row for row in group if predicate(row)]
        universe_hits = sum(row["target"] for row in group)
        selected_hits = sum(row["target"] for row in selected)
        cluster_values.append((len(selected), selected_hits, len(group), universe_hits))
    if not cluster_values:
        return None
    rng = random.Random(seed)
    lifts = []
    deltas = []
    for _ in range(repeats):
        sample = [cluster_values[rng.randrange(len(cluster_values))] for _ in cluster_values]
        selected_n = sum(item[0] for item in sample)
        selected_hits = sum(item[1] for item in sample)
        universe_n = sum(item[2] for item in sample)
        universe_hits = sum(item[3] for item in sample)
        if selected_n and universe_n and universe_hits:
            selected_rate = selected_hits / selected_n
            base_rate = universe_hits / universe_n
            lifts.append(selected_rate / base_rate)
            deltas.append((selected_rate - base_rate) * 100)
    if not lifts:
        return None
    return {
        "clusters": len(cluster_values),
        "repeats": repeats,
        "lift_median": round(float(np.median(lifts)), 3),
        "lift_ci95": [
            round(float(np.percentile(lifts, 2.5)), 3),
            round(float(np.percentile(lifts, 97.5)), 3),
        ],
        "delta_pp_median": round(float(np.median(deltas)), 2),
        "delta_pp_ci95": [
            round(float(np.percentile(deltas, 2.5)), 2),
            round(float(np.percentile(deltas, 97.5)), 2),
        ],
    }


def stability_for_rules(rows, rules, bootstrap_repeats, seed):
    predicates = factor_predicates()
    out = {}
    selected = {
        "entry_ok": predicates["entry_ok"],
        "direction_up": predicates["direction_up"],
        "ATR>=4": predicates["ATR>=4"],
        "ATR>=6": predicates["ATR>=6"],
        "gap>3": predicates["gap>3"],
        "squeeze>=0.5": predicates["squeeze>=0.5"],
    }
    for rule in rules:
        selected[rule["label"]] = (
            next(
                predicate
                for label, predicate in [
                    ("volatility_first_ATR4", predicates["ATR>=4"]),
                    ("volatility_first_ATR6", predicates["ATR>=6"]),
                    (
                        "ATR4_plus_confirmation",
                        lambda row: predicates["ATR>=4"](row)
                        and (
                            predicates["gap>3"](row)
                            or predicates["squeeze>=0.5"](row)
                            or predicates["RVOL>=2"](row)
                        ),
                    ),
                    (
                        "ATR6_plus_confirmation",
                        lambda row: predicates["ATR>=6"](row)
                        and (
                            predicates["gap>3"](row)
                            or predicates["squeeze>=0.5"](row)
                            or predicates["RVOL>=2"](row)
                        ),
                    ),
                    (
                        "ATR4_gap3_squeeze05",
                        lambda row: predicates["ATR>=4"](row)
                        and predicates["gap>3"](row)
                        and predicates["squeeze>=0.5"](row),
                    ),
                    (
                        "ATR6_gap3_or_squeeze05",
                        lambda row: predicates["ATR>=6"](row)
                        and (predicates["gap>3"](row) or predicates["squeeze>=0.5"](row)),
                    ),
                    (
                        "ATR4_entry_ok",
                        lambda row: predicates["ATR>=4"](row) and predicates["entry_ok"](row),
                    ),
                    (
                        "ATR6_entry_ok",
                        lambda row: predicates["ATR>=6"](row) and predicates["entry_ok"](row),
                    ),
                    (
                        "ATR4_direction",
                        lambda row: predicates["ATR>=4"](row) and predicates["direction_up"](row),
                    ),
                    (
                        "ATR6_direction",
                        lambda row: predicates["ATR>=6"](row) and predicates["direction_up"](row),
                    ),
                    (
                        "ATR4_entry_confirmation",
                        lambda row: predicates["ATR>=4"](row)
                        and predicates["entry_ok"](row)
                        and (
                            predicates["gap>3"](row)
                            or predicates["squeeze>=0.5"](row)
                            or predicates["RVOL>=2"](row)
                        ),
                    ),
                ]
                if label == rule["label"]
            )
            if rule["label"]
            in {
                "volatility_first_ATR4",
                "volatility_first_ATR6",
                "ATR4_plus_confirmation",
                "ATR6_plus_confirmation",
                "ATR4_gap3_squeeze05",
                "ATR6_gap3_or_squeeze05",
                "ATR4_entry_ok",
                "ATR6_entry_ok",
                "ATR4_direction",
                "ATR6_direction",
                "ATR4_entry_confirmation",
            }
            else None
        )
    for label, predicate in selected.items():
        out[label] = {
            "overall": metric(rows, label, predicate),
            "periods": period_stability(rows, predicate),
            "cluster_bootstrap": cluster_bootstrap(rows, predicate, bootstrap_repeats, seed),
        }
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--bootstrap", type=int, default=DEFAULT_BOOTSTRAPS)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--combination-sizes",
        default="2,3",
        help="Comma-separated AND combination sizes to evaluate, e.g. 2,3,4,5,6.",
    )
    args = parser.parse_args()
    if not os.path.exists(args.csv):
        raise SystemExit(f"Bulunamadi: {args.csv}")

    rows = load_rows(args.csv)
    deduped = dedup_symbol_day(rows)
    sizes = tuple(
        sorted({int(value) for value in args.combination_sizes.split(",") if value.strip()})
    )
    combinations_all = combination_results(rows, sizes)
    combination_predicates = dict(combination_definitions(sizes))
    rules = recommended_rules(rows)
    stability = stability_for_rules(rows, rules, args.bootstrap, args.seed)

    dedup_stability = stability_for_rules(deduped, rules, args.bootstrap, args.seed)
    top_combo_stability = {}
    for item in combinations_all[:10]:
        predicate = combination_predicates[item["label"]]
        top_combo_stability[item["label"]] = {
            "no_dedup": {
                "overall": item,
                "periods": period_stability(rows, predicate),
                "cluster_bootstrap": cluster_bootstrap(rows, predicate, args.bootstrap, args.seed),
            },
            "symbol_day": {
                "overall": metric(deduped, item["label"], predicate),
                "periods": period_stability(deduped, predicate),
                "cluster_bootstrap": cluster_bootstrap(
                    deduped, predicate, args.bootstrap, args.seed
                ),
            },
        }

    out = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "primary_target": PRIMARY,
        "methodology": {
            "primary_rows_no_dedup": len(rows),
            "symbol_day_rows": len(deduped),
            "bootstrap": "symbol-day cluster resampling",
            "bootstrap_repeats": args.bootstrap,
            "seed": args.seed,
            "combination_sizes": list(sizes),
            "target": "T+1..T+5 maximum high >= entry * 1.05",
        },
        "top_combinations_no_dedup": combinations_all[:100],
        "top_combination_stability": top_combo_stability,
        "recommended_rules_no_dedup": rules,
        "stability_no_dedup": stability,
        "recommended_rules_symbol_day": [item["overall"] for item in dedup_stability.values()],
        "stability_symbol_day": dedup_stability,
    }
    os.makedirs(args.out, exist_ok=True)
    output_path = os.path.join(args.out, "full_universe_robustness_results.json")
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=2, default=str)

    combo_path = os.path.join(args.out, "full_universe_combinations.csv")
    with open(combo_path, "w", newline="", encoding="utf-8") as handle:
        fields = [
            "label",
            "n",
            "hit_rate",
            "base_rate",
            "lift",
            "delta_pp",
            "ci95",
            "p",
            "mean_ret5",
            "median_ret5",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: item.get(field) for field in fields} for item in combinations_all)

    print(f"OK -> {output_path}")
    print(f"OK -> {combo_path}")
    print(
        f"rows={len(rows)} no-dedup, symbol-day={len(deduped)}, combinations={len(combinations_all)}"
    )
    print("\n=== TOP COMBINATIONS ===")
    for item in combinations_all[:15]:
        print(
            f"  {item['label']:55s} n={item['n']:>6} hit={item['hit_rate'] * 100:>5.1f}% lift={item['lift']}"
        )
    print("\n=== RECOMMENDED RULES ===")
    for item in rules:
        boot = stability[item["label"]]["cluster_bootstrap"]
        ci = boot["lift_ci95"] if boot else None
        print(
            f"  {item['label']:32s} n={item['n']:>6} hit={item['hit_rate'] * 100:>5.1f}% lift={item['lift']} cluster_ci={ci}"
        )


if __name__ == "__main__":
    main()
