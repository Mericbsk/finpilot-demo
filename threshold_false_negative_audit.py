#!/usr/bin/env python3
"""Research-only threshold and false-negative audit.

This audit uses the enriched full-universe artifact as an outcome-labelled
cross-section. It does not replay unavailable intraday features and does not
change live scanner behavior.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import UTC, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(ROOT, "data", "backtest_out", "full_universe_enriched.csv")
DEFAULT_OUT = os.path.join(ROOT, "data", "backtest_out", "threshold_false_negative_audit.json")


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
                    "scan_date": (raw.get("scan_date") or "").strip(),
                    "price": number(raw.get("price")),
                    "score": number(raw.get("score")),
                    "composite": number(raw.get("composite_score")),
                    "regime": boolean(raw.get("regime")),
                    "direction": boolean(raw.get("direction")),
                    "entry_ok": boolean(raw.get("entry_ok")),
                    "liquidity_ok": boolean(raw.get("liquidity_ok")),
                    "atr": number(raw.get("atr_pct_real")),
                    "gap": number(raw.get("gap_pct")),
                    "rvol": number(raw.get("rvol")),
                    "squeeze": number(raw.get("squeeze_factor")),
                    "target": number(raw.get("resolved_pct_t5")),
                }
            )
    return rows


def percent(value):
    return round(100.0 * value, 3) if value is not None else None


def metrics(rows):
    labelled = [row for row in rows if row["target"] is not None]
    if not labelled:
        return {"n": 0, "positive_n": 0, "hit_rate_5pct": None, "recall_of_all_positive_pct": None}
    positive_n = sum(row["target"] >= 5.0 for row in labelled)
    return {
        "n": len(labelled),
        "positive_n": positive_n,
        "hit_rate_5pct": percent(positive_n / len(labelled)),
        "recall_of_all_positive_pct": None,
    }


def add_recall(result, all_positive_n):
    if all_positive_n and result["positive_n"] is not None:
        result["recall_of_all_positive_pct"] = percent(result["positive_n"] / all_positive_n)
    return result


def threshold_sweep(rows, field, thresholds, predicate=lambda value, threshold: value >= threshold):
    all_positive_n = sum(row["target"] is not None and row["target"] >= 5.0 for row in rows)
    output = []
    for threshold in thresholds:
        selected = [
            row for row in rows if row[field] is not None and predicate(row[field], threshold)
        ]
        result = add_recall(metrics(selected), all_positive_n)
        result.update(
            {
                "field": field,
                "threshold": threshold,
                "coverage_pct": percent(len(selected) / len(rows)) if rows else None,
            }
        )
        output.append(result)
    return output


def cohort_report(rows, name, predicate, all_positive_n):
    selected = [row for row in rows if predicate(row)]
    result = add_recall(metrics(selected), all_positive_n)
    result.update(
        {"name": name, "coverage_pct": percent(len(selected) / len(rows)) if rows else None}
    )
    return result


def build_report(rows):
    all_positive_n = sum(row["target"] is not None and row["target"] >= 5.0 for row in rows)

    def positive(row):
        return row["target"] is not None and row["target"] >= 5.0

    positive_rows = [row for row in rows if positive(row)]
    rejected_positive = [row for row in positive_rows if not row["entry_ok"]]

    cohorts = [
        ("all_positive", positive),
        ("positive_rejected_by_entry_ok", lambda row: positive(row) and not row["entry_ok"]),
        ("positive_rejected_regime_proxy", lambda row: positive(row) and not row["regime"]),
        ("positive_rejected_direction_proxy", lambda row: positive(row) and not row["direction"]),
        (
            "positive_raw_score_below_3",
            lambda row: positive(row) and (row["score"] is None or row["score"] < 3),
        ),
        ("positive_rejected_liquidity", lambda row: positive(row) and not row["liquidity_ok"]),
        (
            "positive_atr6_rejected",
            lambda row: positive(row)
            and row["atr"] is not None
            and row["atr"] >= 6
            and not row["entry_ok"],
        ),
        (
            "positive_gap3_rejected",
            lambda row: positive(row)
            and row["gap"] is not None
            and row["gap"] >= 3
            and not row["entry_ok"],
        ),
        (
            "positive_rvol2_rejected",
            lambda row: positive(row)
            and row["rvol"] is not None
            and row["rvol"] >= 2
            and not row["entry_ok"],
        ),
        (
            "positive_atr6_gap3_or_rvol2_rejected",
            lambda row: positive(row)
            and row["atr"] is not None
            and row["atr"] >= 6
            and (
                (row["gap"] is not None and row["gap"] >= 3)
                or (row["rvol"] is not None and row["rvol"] >= 2)
            )
            and not row["entry_ok"],
        ),
    ]

    threshold_inventory = {
        "production_hard_gates": [
            {
                "name": "history",
                "values": {"15m_bars": 15, "1h_bars": 10, "4h_bars": 15, "1d_bars": 50},
                "status": "enforced in evaluate_symbol",
            },
            {
                "name": "regime",
                "rule": "daily close > EMA200, EMA50 fallback when history is short",
                "status": "enforced",
            },
            {"name": "direction", "rule": "daily close > EMA50", "status": "enforced"},
            {
                "name": "raw_score",
                "rule": "score >= 3 and entry_ok additionally requires score == 3",
                "status": "enforced; fixed",
            },
            {"name": "price", "value": 2.0, "status": "enforced"},
            {"name": "average_volume", "value": 300000, "status": "enforced; 10-day share volume"},
            {
                "name": "earnings_blackout",
                "values": {"days_before": 2, "days_after": 1},
                "status": "enforced when lookup succeeds",
            },
            {
                "name": "daily_drawdown",
                "value": 0.03,
                "status": "enforced before evaluation; fail-open on missing state",
            },
        ],
        "production_scoring_or_reporting": [
            {
                "name": "volume_spike",
                "value": 1.5,
                "status": "feature/composite; not entry_ok gate",
            },
            {
                "name": "momentum_z",
                "values": {
                    "base": 1.5,
                    "segment": {"high": 2.0, "mid": 1.6, "low": 1.4},
                    "dynamic_min": 1.1,
                    "dynamic_max": 3.0,
                },
                "status": "adaptive feature; not entry_ok gate",
            },
            {
                "name": "alignment",
                "value": 0.67,
                "status": "feature output; config min_alignment_ratio is not applied by entry_ok",
            },
            {
                "name": "momentum_confluence",
                "value": 0.5,
                "status": "feature output; not entry_ok gate",
            },
            {
                "name": "composite_high_score",
                "value": 58,
                "status": "position-size suppression band, not entry cutoff",
            },
        ],
        "optional_feature_thresholds": [
            {
                "name": "squeeze",
                "values": {"short_percent_float_pivot": 0.20, "float_pivot": 50000000},
                "status": "env-gated",
            },
            {
                "name": "conviction",
                "values": {
                    "short_strong_factor": 0.5,
                    "gap_strong_factor": 0.6,
                    "gap_present_factor": 0.2,
                    "rvol_present_factor": 0.25,
                    "atr_present_pct": 4.0,
                },
                "status": "env-gated label; does not change score",
            },
        ],
        "research_only": [
            {
                "name": "production_config_proxy",
                "rule": "ATR >= 4 OR gap >= 3 OR RVOL >= 2",
                "status": "backtest only",
            },
            {
                "name": "tier_A",
                "rule": "short >= 15 and gap >= 3",
                "status": "backtest proxy / conviction research",
            },
            {
                "name": "tier_B",
                "rule": "short >= 15 and ATR >= 4 OR at least 3 factors",
                "status": "backtest proxy / conviction research",
            },
            {
                "name": "tier_C",
                "rule": "at least 2 of short, ATR, gap >= 1, RVOL >= 1.5",
                "status": "backtest proxy / conviction research",
            },
        ],
    }

    return {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "methodology": {
            "input_csv": "data/backtest_out/full_universe_enriched.csv",
            "target": "resolved_pct_t5 >= 5%",
            "positive_cohort": "favorable movement, not cost-adjusted trade P&L",
            "false_negative_definition": "positive labelled row with entry_ok=False; gate attribution is proxy-based",
            "research_only": True,
        },
        "inventory": {
            "rows": len(rows),
            "positive_rows": all_positive_n,
            "positive_rate_pct": percent(all_positive_n / len(rows)) if rows else None,
            "rejected_positive_rows": len(rejected_positive),
            "rejected_positive_share_of_positive_pct": percent(
                len(rejected_positive) / all_positive_n
            )
            if all_positive_n
            else None,
            "symbols": len({row["symbol"] for row in rows if row["symbol"]}),
            "scan_dates": len({row["scan_date"] for row in rows if row["scan_date"]}),
        },
        "threshold_inventory": threshold_inventory,
        "threshold_sensitivity": {
            "price": threshold_sweep(rows, "price", [0.5, 1, 2, 3, 5, 10]),
            "score": threshold_sweep(rows, "score", [1, 2, 3, 4, 5]),
            "atr_pct": threshold_sweep(rows, "atr", [2, 4, 6, 10, 20, 50]),
            "gap_pct": threshold_sweep(rows, "gap", [1, 3, 5, 10]),
            "rvol": threshold_sweep(rows, "rvol", [1.2, 1.5, 2, 3, 5]),
            "squeeze": threshold_sweep(rows, "squeeze", [0.3, 0.5, 0.7]),
        },
        "false_negative_cohorts": [
            cohort_report(rows, name, predicate, all_positive_n) for name, predicate in cohorts
        ],
        "rejected_positive_intersections": [
            cohort_report(
                rows,
                "rejected_positive_atr6_and_rvol2",
                lambda row: positive(row)
                and not row["entry_ok"]
                and row["atr"] is not None
                and row["atr"] >= 6
                and row["rvol"] is not None
                and row["rvol"] >= 2,
                all_positive_n,
            ),
            cohort_report(
                rows,
                "rejected_positive_atr6_and_gap3",
                lambda row: positive(row)
                and not row["entry_ok"]
                and row["atr"] is not None
                and row["atr"] >= 6
                and row["gap"] is not None
                and row["gap"] >= 3,
                all_positive_n,
            ),
        ],
        "findings": [
            "A positive row rejected by entry_ok is a recall miss under the favorable-movement target, not proof that the live gate made a bad trade decision.",
            "Regime, direction, score, and liquidity are observable proxies for rejection; the CSV does not contain every intermediate live gate reason.",
            "ATR, gap, and RVOL are research proxies in this artifact and must not be promoted to production gates without point-in-time, cost-adjusted, out-of-sample validation.",
            "A threshold can improve hit rate while destroying usable coverage; threshold decisions require both precision and recall, plus execution outcomes.",
        ],
        "limitations": [
            "The artifact may not be a byte-for-byte production replay and may contain repeated symbol-day observations.",
            "No spread, slippage, borrow, halt, fill, or corporate-action quality field is used here.",
            "The target is a five-day favorable move and can overstate tradeable edge.",
            "Threshold sweeps are exploratory and exposed to multiple-testing bias; use a locked OOS period for calibration.",
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
    print(
        f"rows={report['inventory']['rows']} positive={report['inventory']['positive_rows']} rejected_positive={report['inventory']['rejected_positive_rows']}"
    )
    for item in report["false_negative_cohorts"]:
        print(
            f"{item['name']:42s} n={item['n']:>6} positive={item['positive_n']:>6} coverage={item['coverage_pct']}%"
        )


if __name__ == "__main__":
    main()
