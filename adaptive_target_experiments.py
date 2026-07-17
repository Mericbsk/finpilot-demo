#!/usr/bin/env python3
"""Compare fixed and adaptive target policies on FinPilot scan outcomes.

The source export has forward close returns for 1d and 5d, not per-signal
forward OHLC paths. Results are therefore a close-only policy screen. The
existing triple-barrier report remains the path-aware risk check.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import median, pstdev

HORIZONS = (1, 5)
COST_PCT = 0.30
FIXED_TARGETS = (2.0, 3.0, 5.0)


def num(value: str | None) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def boolean(value: str | None) -> bool | None:
    if value in (None, ""):
        return None
    return str(value).strip().lower() in {"1", "true", "yes", "trend", "up"}


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [
            {
                **row,
                "ret_1d": num(row.get("resolved_pct_1d")),
                "ret_5d": num(row.get("resolved_pct_t5")),
                "atr": num(row.get("atr_pct_real")) or num(row.get("atr_pct")),
                "composite": num(row.get("composite_score")),
                "regime": boolean(row.get("regime")),
                "rvol": num(row.get("rvol")),
                "gap": num(row.get("gap_pct")),
                "squeeze": num(row.get("squeeze_factor")),
                "catalyst": num(row.get("catalyst_factor")),
            }
            for row in csv.DictReader(handle)
        ]


def quantile_cutoffs(rows: list[dict]) -> tuple[float, float, float] | None:
    values = sorted(r["composite"] for r in rows if r["composite"] is not None)
    if not values:
        return None
    return tuple(values[int(len(values) * p)] for p in (0.25, 0.50, 0.75))


def policy_targets(rows: list[dict], policy: str) -> list[float | None]:
    cuts = quantile_cutoffs(rows)
    targets: list[float | None] = []
    for row in rows:
        atr = row["atr"]
        composite = row["composite"]
        if policy.startswith("fixed_"):
            targets.append(float(policy.removeprefix("fixed_")))
        elif policy == "atr_adaptive":
            targets.append(None if atr is None else (2.0 if atr < 4 else 3.0 if atr < 6 else 5.0))
        elif policy == "regime_adaptive":
            targets.append(None if row["regime"] is None else (5.0 if row["regime"] else 2.0))
        elif policy == "composite_adaptive":
            if composite is None or cuts is None:
                targets.append(None)
            else:
                q25, q50, q75 = cuts
                targets.append(
                    2.0
                    if composite <= q25
                    else 3.0
                    if composite <= q50
                    else 4.0
                    if composite <= q75
                    else 5.0
                )
        elif policy == "atr_composite_adaptive":
            if atr is None or composite is None or cuts is None:
                targets.append(None)
            else:
                q25, q50, q75 = cuts
                high_score = composite > q75
                targets.append(2.0 if atr < 4 else 3.0 if atr < 6 else (7.0 if high_score else 5.0))
        elif policy == "selective_atr_adaptive":
            targets.append(
                None if atr is None or atr < 2 else (2.0 if atr < 4 else 3.0 if atr < 6 else 5.0)
            )
        else:
            raise ValueError(f"unknown policy: {policy}")
    return targets


def profit_factor(returns: list[float]) -> float | None:
    gains = sum(x for x in returns if x > 0)
    losses = -sum(x for x in returns if x < 0)
    return round(gains / losses, 4) if losses else None


def evaluate(rows: list[dict], targets: list[float | None], horizon: int) -> dict:
    key = f"ret_{horizon}d"
    observations = [
        (row[key], target)
        for row, target in zip(rows, targets, strict=False)
        if row[key] is not None and target is not None
    ]
    if not observations:
        return {"n": 0}
    gross = [target if value >= target else value for value, target in observations]
    net = [value - COST_PCT for value in gross]
    hits = [value >= target for value, target in observations]
    return {
        "n": len(observations),
        "coverage": round(len(observations) / len(rows), 4),
        "hit_rate": round(sum(hits) / len(hits), 4),
        "mean_assigned_target": round(
            sum(target for _, target in observations) / len(observations), 4
        ),
        "mean_exit_net_pct": round(sum(net) / len(net), 4),
        "median_exit_net_pct": round(median(net), 4),
        "profit_factor": profit_factor(net),
        "target_counts": {
            str(t): sum(1 for _, assigned in observations if assigned == t)
            for t in sorted({t for _, t in observations})
        },
    }


def monthly_stability(rows: list[dict], targets: list[float | None], horizon: int) -> dict:
    key = f"ret_{horizon}d"
    monthly: dict[str, list[bool]] = defaultdict(list)
    for row, target in zip(rows, targets, strict=False):
        if row[key] is not None and target is not None:
            monthly[str(row.get("scan_date", ""))[:7]].append(row[key] >= target)
    rates = [sum(values) / len(values) for values in monthly.values() if values]
    return {
        "months": len(rates),
        "positive_month_share": round(sum(rate > 0.5 for rate in rates) / len(rates), 4)
        if rates
        else None,
        "monthly_hit_rate_std": round(pstdev(rates), 4) if len(rates) > 1 else None,
    }


def run(rows: list[dict]) -> dict:
    policies = [
        "fixed_2.0",
        "fixed_3.0",
        "fixed_5.0",
        "atr_adaptive",
        "regime_adaptive",
        "composite_adaptive",
        "atr_composite_adaptive",
        "selective_atr_adaptive",
    ]
    result = []
    for policy in policies:
        targets = policy_targets(rows, policy)
        for horizon in HORIZONS:
            item = {"policy": policy, "horizon_days": horizon, **evaluate(rows, targets, horizon)}
            item["stability"] = monthly_stability(rows, targets, horizon)
            result.append(item)
    return {
        "methodology": {
            "target_type": "close-only adaptive target policy",
            "cost_round_trip_pct": COST_PCT,
            "horizons": list(HORIZONS),
            "path_metrics": "unavailable in source CSV; use triple-barrier report for path-aware risk",
        },
        "results": result,
    }


def write_report(path: Path, payload: dict, rows: list[dict]) -> None:
    lines = [
        "# FinPilot Adaptive Target Experiments",
        "",
        f"- Source rows: {len(rows):,}",
        "- Target policy comparison uses identical observations and a 0.30% round-trip cost proxy.",
        "- This is close-only; no peak-touch, time-to-hit, MAE or MFE is inferred.",
        "",
        "| Policy | Horizon | N | Coverage | Hit rate | Mean assigned target | Net exit expectancy | PF | OOS std |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in payload["results"]:
        stability = r.get("stability", {})
        lines.append(
            f"| {r['policy']} | {r['horizon_days']}d | {r.get('n', 0):,} | {r.get('coverage', 0):.1%} | "
            f"{r.get('hit_rate', 0):.1%} | {r.get('mean_assigned_target', 0):.2f}% | "
            f"{r.get('mean_exit_net_pct', 0):.2f}% | {r.get('profit_factor', 'n/a')} | "
            f"{stability.get('monthly_hit_rate_std', 'n/a')} |"
        )
    lines += [
        "",
        "## Policy definitions",
        "",
        "- `fixed_2.0`, `fixed_3.0`, `fixed_5.0`: control groups.",
        "- `atr_adaptive`: ATR <4 -> 2%; 4-6 -> 3%; >=6 -> 5%.",
        "- `regime_adaptive`: trend -> 5%; range -> 2%.",
        "- `composite_adaptive`: composite quartiles -> 2%, 3%, 4%, 5%.",
        "- `atr_composite_adaptive`: ATR policy with 7% only for high-ATR/high-composite signals.",
        "- `selective_atr_adaptive`: abstains when ATR <2%, then follows ATR policy.",
        "",
        "The target-specific exit is a close-only proxy: hits are capped at the assigned target; misses exit at the horizon close.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument(
        "--out", type=Path, default=Path("data/backtest_out/adaptive_target_experiments.json")
    )
    args = parser.parse_args()
    rows = load(args.csv)
    payload = {"source": str(args.csv), **run(rows)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report = args.out.with_suffix(".md")
    write_report(report, payload, rows)
    print(f"rows={len(rows)} policies=8 results={len(payload['results'])}")
    print(f"json={args.out}")
    print(f"report={report}")


if __name__ == "__main__":
    main()
