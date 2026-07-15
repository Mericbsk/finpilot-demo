#!/usr/bin/env python3
"""Research-only legacy/V2 score formula comparison on their source artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from collections import defaultdict
from datetime import UTC, datetime
from statistics import mean, median

ROOT = os.path.dirname(os.path.abspath(__file__))
LEGACY_CSV = os.path.join(ROOT, "data", "backtest_out", "full_universe_enriched.csv")
V2_CSV = os.path.join(ROOT, "data", "backtest_out", "enriched_signals_v3.csv")
DEFAULT_OUT = os.path.join(ROOT, "data", "backtest_out", "score_formula_comparison")
COSTS = {"none": 0.0, "low": 0.30, "baseline": 0.55, "stress": 1.00}
MIN_N = 30


def number(value):
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def flag(value):
    return str(value).strip().lower() in {"true", "1", "yes", "bull", "up"}


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def normalized(value, scale, default=0.0):
    return clamp((value if value is not None else default) / scale)


def canonical(rows):
    chosen = {}
    for row in rows:
        key = (row["symbol"], row["date"])
        old = chosen.get(key)
        if old is None or (row["timestamp"], row["id"]) < (old["timestamp"], old["id"]):
            chosen[key] = row
    return list(chosen.values())


def load_legacy(path):
    rows = []
    with open(path, encoding="utf-8", newline="") as handle:
        for index, raw in enumerate(csv.DictReader(handle)):
            ret5 = number(raw.get("resolved_pct_t5"))
            if ret5 is None:
                continue
            rows.append(
                {
                    "id": f"legacy_{raw.get('symbol')}_{raw.get('scan_ts')}_{index}",
                    "source": "legacy",
                    "symbol": (raw.get("symbol") or "").strip(),
                    "timestamp": (raw.get("scan_ts") or "").strip(),
                    "date": (raw.get("scan_date") or "").strip(),
                    "price": number(raw.get("price")),
                    "legacy_composite": number(raw.get("composite_score")),
                    "score": number(raw.get("score")),
                    "regime": flag(raw.get("regime")),
                    "direction": flag(raw.get("direction")),
                    "entry_ok": flag(raw.get("entry_ok")),
                    "liquidity_ok": flag(raw.get("liquidity_ok")),
                    "atr": number(raw.get("atr_pct_real")),
                    "gap": number(raw.get("gap_pct")),
                    "rvol": number(raw.get("rvol")),
                    "squeeze": number(raw.get("squeeze_factor")),
                    "sentiment": number(raw.get("sentiment")),
                    "lottery": number(raw.get("lottery_factor")),
                    "overnight": number(raw.get("overnight_gap_factor")),
                    "dist52": number(raw.get("dist_52w_high")),
                    "ret5": ret5,
                    "target": ret5 >= 5.0,
                }
            )
    return rows


def load_v2(path):
    rows = []
    with open(path, encoding="utf-8", newline="") as handle:
        for index, raw in enumerate(csv.DictReader(handle)):
            ret5 = number(raw.get("resolved_pct_t5"))
            if ret5 is None:
                continue
            rows.append(
                {
                    "id": f"v2_{raw.get('symbol')}_{raw.get('signal_date')}_{index}",
                    "source": "v2",
                    "symbol": (raw.get("symbol") or "").strip(),
                    "timestamp": (raw.get("signal_date") or "").strip(),
                    "date": (raw.get("signal_date") or "")[:10],
                    "price": number(raw.get("entry")),
                    "legacy_composite": None,
                    "score": number(raw.get("score")),
                    "regime": flag(raw.get("regime")),
                    "regime_raw": (raw.get("regime") or "").strip(),
                    "direction": flag(raw.get("direction")),
                    "entry_ok": False,
                    "liquidity_ok": True,
                    "atr": number(raw.get("atr_pct")),
                    "gap": number(raw.get("gap_pct")),
                    "rvol": number(raw.get("rvol")),
                    "squeeze": 0.0,
                    "sentiment": None,
                    "lottery": 0.0,
                    "overnight": 0.0,
                    "dist52": number(raw.get("dist_52w_high")),
                    "short": number(raw.get("short_pit"))
                    if raw.get("short_pit") not in (None, "")
                    else number(raw.get("short_pct")),
                    "ret5": ret5,
                    "target": ret5 >= 5.0,
                }
            )
    return rows


def legacy_formula_scores(row):
    regime = 1.0 if row["regime"] else 0.0
    direction = 1.0 if row["direction"] else 0.0
    raw_score = normalized(row["score"], 3.0)
    atr = normalized(row["atr"], 6.0)
    rvol = normalized((row["rvol"] - 1.0) if row["rvol"] is not None else None, 2.0)
    gap = normalized(max(row["gap"] or 0.0, 0.0), 5.0)
    squeeze = clamp(row["squeeze"] or 0.0)
    sentiment = clamp(((row["sentiment"] or 0.0) + 1.0) / 2.0)
    lottery = clamp(row["lottery"] or 0.0)
    overnight = clamp(row["overnight"] or 0.0)
    base = 2.0 * regime + 2.0 * direction + 1.5 * raw_score
    return {
        "legacy_existing": row["legacy_composite"],
        "legacy_base": round(base / 5.5 * 100.0, 6),
        "legacy_confirmation": round(
            (base + 1.5 * atr + 1.0 * rvol + 1.0 * gap + 1.0 * squeeze) / 10.0 * 100.0, 6
        ),
        "legacy_precision": round(
            (
                base
                + 1.0 * atr
                + 1.0 * rvol
                + 1.0 * squeeze
                + 0.5 * sentiment
                - 1.5 * lottery
                - 1.0 * overnight
            )
            / 10.0
            * 100.0,
            6,
        ),
        "legacy_quality": round(
            (base + 1.5 * atr + 1.5 * rvol + 0.5 * squeeze - 1.5 * lottery - 1.0 * overnight)
            / 10.0
            * 100.0,
            6,
        ),
    }


def v2_formula_scores(row):
    short_n = normalized(row.get("short"), 20.0)
    atr_n = normalized(row["atr"], 6.0)
    gap_n = normalized(max(row["gap"] or 0.0, 0.0), 5.0)
    rvol_n = normalized((row["rvol"] - 1.0) if row["rvol"] is not None else None, 2.0)
    extension_n = normalized(max((row["dist52"] or 0.0) - 0.9, 0.0), 0.1)
    return {
        "v2_documented": round(
            (4.0 * short_n + 3.0 * atr_n + 3.0 * gap_n + 2.0 * rvol_n - 1.5 * extension_n)
            / 12.0
            * 100.0,
            6,
        ),
        "v2_volatility_first": round(
            (2.0 * short_n + 4.0 * atr_n + 2.0 * gap_n + 2.0 * rvol_n - 1.5 * extension_n)
            / 11.5
            * 100.0,
            6,
        ),
        "v2_selective": round(
            (4.0 * short_n + 4.0 * atr_n + 1.5 * gap_n + 1.5 * rvol_n - 2.0 * extension_n)
            / 13.0
            * 100.0,
            6,
        ),
        "v2_confirmation": round(
            (3.0 * short_n + 3.0 * atr_n + 2.0 * gap_n + 2.0 * rvol_n - 2.0 * extension_n)
            / 12.0
            * 100.0,
            6,
        ),
    }


def add_scores(rows):
    for row in rows:
        row.update(
            legacy_formula_scores(row) if row["source"] == "legacy" else v2_formula_scores(row)
        )
    return rows


def metrics(selected, universe, cost):
    returns = [
        row["ret5"] - cost
        for row in sorted(selected, key=lambda r: (r["date"], r["timestamp"], r["id"]))
    ]
    hits = sum(row["target"] for row in selected)
    wins = [value for value in returns if value > 0]
    losses = [-value for value in returns if value < 0]
    dates = {row["date"] for row in universe}
    base_hits = sum(row["target"] for row in universe)
    hit_rate = hits / len(selected) if selected else None
    return {
        "n": len(selected),
        "symbols": len({row["symbol"] for row in selected}),
        "daily_signal_count": round(len(selected) / len(dates), 4) if dates else None,
        "coverage_pct": round(len(selected) / len(universe) * 100.0, 4) if universe else None,
        "precision_pct": round(hit_rate * 100.0, 4) if hit_rate is not None else None,
        "false_positive_pct": round((1.0 - hit_rate) * 100.0, 4) if hit_rate is not None else None,
        "recall_pct": round(hits / base_hits * 100.0, 4) if base_hits else None,
        "mean_return_pct": round(mean(returns), 4) if returns else None,
        "median_return_pct": round(median(returns), 4) if returns else None,
        "profit_factor_gross": round(sum(wins) / sum(losses), 4) if losses else None,
        "cost_pct": cost,
    }


def split_rows(rows):
    cut1 = "2026-04-17"
    cut2 = "2026-05-21"
    return {
        "discovery": [row for row in rows if row["date"] <= cut1],
        "validation": [row for row in rows if cut1 < row["date"] <= cut2],
        "locked_oos": [row for row in rows if row["date"] > cut2],
    }, {"discovery_end": cut1, "validation_end": cut2, "locked_oos_start_exclusive": cut2}


def percentile_cut(rows, field, fraction):
    values = sorted(row[field] for row in rows if row.get(field) is not None)
    if not values:
        return None
    index = min(len(values) - 1, max(0, math.ceil(len(values) * (1.0 - fraction)) - 1))
    return values[index]


def ranked_selected(rows, field, fraction):
    groups = defaultdict(list)
    for row in rows:
        groups[row["date"]].append(row)
    selected = []
    for group in groups.values():
        ranked = sorted(
            group,
            key=lambda row: (
                row.get(field) is not None,
                row.get(field) or -999999.0,
                row["symbol"],
            ),
            reverse=True,
        )
        selected.extend(ranked[: max(1, math.ceil(len(ranked) * fraction))])
    return selected


def rule_selected(rows, field, cut):
    if cut is None:
        return []
    return [row for row in rows if row.get(field) is not None and row[field] >= cut]


def run_source(rows):
    rows = add_scores(canonical(rows))
    groups, split_info = split_rows(rows)
    prefix = "legacy_" if rows[0]["source"] == "legacy" else "v2_"
    formula_names = [key for key in rows[0] if key.startswith(prefix)]
    result = {
        "source": rows[0]["source"],
        "rows": len(rows),
        "symbols": len({r["symbol"] for r in rows}),
        "dates": len({r["date"] for r in rows}),
        "split": split_info,
        "formulas": {},
    }
    for formula in formula_names:
        discovery = groups["discovery"]
        cut10 = percentile_cut(discovery, formula, 0.10)
        cut20 = percentile_cut(discovery, formula, 0.20)
        formula_result = {
            "discovery_cuts": {"top10": cut10, "top20": cut20},
            "overall": {},
            "top_percentile": {},
            "temporal": {},
        }
        for fraction, label in ((0.10, "top10"), (0.20, "top20")):
            selected = ranked_selected(rows, formula, fraction)
            formula_result["top_percentile"][label] = {
                name: metrics(selected, rows, cost) for name, cost in COSTS.items()
            }
        for name, group in groups.items():
            formula_result["temporal"][name] = {}
            for _fraction, label in ((0.10, "top10"), (0.20, "top20")):
                selected = rule_selected(group, formula, formula_result["discovery_cuts"][label])
                formula_result["temporal"][name][label] = {
                    cost_name: metrics(selected, group, cost) for cost_name, cost in COSTS.items()
                }
        result["formulas"][formula] = formula_result
    gates = {
        "legacy_entry_atr4_rvol12": lambda r: r["source"] == "legacy"
        and r["entry_ok"]
        and r["liquidity_ok"]
        and r["regime"]
        and r["direction"]
        and (r["atr"] or -1) >= 4
        and (r["rvol"] or -1) >= 1.2,
        "legacy_entry_atr6_rvol2": lambda r: r["source"] == "legacy"
        and r["entry_ok"]
        and (r["atr"] or -1) >= 6
        and (r["rvol"] or -1) >= 2,
        "v2_short15_atr6_not_extended": lambda r: r["source"] == "v2"
        and (r.get("short") or -1) >= 15
        and (r["atr"] or -1) >= 6
        and (r["dist52"] or 0) < 0.9,
        "v2_atr6_rvol2": lambda r: r["source"] == "v2"
        and (r["atr"] or -1) >= 6
        and (r["rvol"] or -1) >= 2,
    }
    result["gates"] = {}
    for label, predicate in gates.items():
        selected = [row for row in rows if predicate(row)]
        if selected:
            result["gates"][label] = {
                name: metrics(selected, rows, cost) for name, cost in COSTS.items()
            }
    return result


def write_summary(report, path):
    output = []
    for source, source_result in report["sources"].items():
        for formula, formula_result in source_result["formulas"].items():
            for selection in ("top10", "top20"):
                item = formula_result["top_percentile"][selection]["baseline"]
                output.append(
                    {
                        "source": source,
                        "type": "formula_percentile",
                        "name": formula,
                        "selection": selection,
                        **item,
                    }
                )
        for name, costs in source_result["gates"].items():
            output.append(
                {
                    "source": source,
                    "type": "gate",
                    "name": name,
                    "selection": "all",
                    **costs["baseline"],
                }
            )
    fields = [
        "source",
        "type",
        "name",
        "selection",
        "n",
        "symbols",
        "daily_signal_count",
        "coverage_pct",
        "precision_pct",
        "false_positive_pct",
        "recall_pct",
        "mean_return_pct",
        "median_return_pct",
        "profit_factor_gross",
        "cost_pct",
    ]
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-csv", default=LEGACY_CSV)
    parser.add_argument("--v2-csv", default=V2_CSV)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()
    legacy = run_source(load_legacy(args.legacy_csv))
    v2 = run_source(load_v2(args.v2_csv))
    report = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "methodology": {
            "research_only": True,
            "target": "resolved_pct_t5 >= 5%",
            "canonicalization": "earliest timestamp per symbol-day within each source artifact",
            "formula_cut_selection": "top10/top20 cut learned in discovery and replayed unchanged in validation/locked OOS",
            "costs_pct_points": COSTS,
            "comparability_warning": "legacy and V2 source artifacts are not the same universe; use same-artifact results for ranking and rerun both on a shared point-in-time universe before production choice",
        },
        "sources": {"legacy": legacy, "v2": v2},
        "limitations": [
            "Formula variants use fields persisted in the artifacts; unavailable production components are not fabricated.",
            "Forward target is favorable movement, not path-dependent execution P&L.",
            "Formula selection is research-only and subject to multiple testing until independent locked OOS is completed.",
            "Current production V2 flag does not change the legacy composite score path; this report tests the documented offline V2 formula separately.",
        ],
    }
    os.makedirs(args.out, exist_ok=True)
    json_path = os.path.join(args.out, "score_formula_comparison.json")
    csv_path = os.path.join(args.out, "score_formula_summary.csv")
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=True)
    write_summary(report, csv_path)
    print(f"OK -> {json_path}")
    print(f"OK -> {csv_path}")
    for source, data in report["sources"].items():
        print(source, "rows", data["rows"], "dates", data["dates"])
        for formula, item in data["formulas"].items():
            baseline = item["top_percentile"]["top10"]["baseline"]
            oos = item["temporal"]["locked_oos"]["top10"]["baseline"]
            print(formula, "top10", baseline, "locked_oos", oos)


if __name__ == "__main__":
    main()
