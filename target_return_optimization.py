#!/usr/bin/env python3
"""Target-return sweep on the point-in-time full-universe export.

The current enriched export contains 1-day and 5-day close-to-close returns,
but not forward OHLC paths. Peak-touch, time-to-hit, and path MAE/MFE are
therefore reported as unavailable rather than inferred.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import median, pstdev

TARGETS = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 10.0)
HORIZONS = (1, 5)
DEFAULT_COST_PCT = 0.30  # 10 bps commission + 5 bps slippage per side.
OOS_START = "2026-01-01"


def number(value: str | None) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def flag(value: str | None) -> bool | None:
    if value is None or value == "":
        return None
    return str(value).strip().lower() in {"1", "true", "yes", "up", "trend"}


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = []
        for row in csv.DictReader(handle):
            rows.append(
                {
                    **row,
                    "score_num": number(row.get("score")),
                    "composite_num": number(row.get("composite_score")),
                    "finpilot_num": number(row.get("finpilot_score")),
                    "ret_1d": number(row.get("resolved_pct_1d")),
                    "ret_5d": number(row.get("resolved_pct_t5")),
                    "regime_flag": flag(row.get("regime")),
                    "atr_num": number(row.get("atr_pct_real")) or number(row.get("atr_pct")),
                    "rvol_num": number(row.get("rvol")),
                }
            )
    return rows


def dedup_symbol_day(rows: list[dict]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    out = []
    for row in rows:
        key = (str(row.get("symbol", "")), str(row.get("scan_date", "")))
        if key not in seen:
            seen.add(key)
            out.append(row)
    return out


def profit_factor(returns: list[float]) -> float | None:
    gains = sum(value for value in returns if value > 0)
    losses = -sum(value for value in returns if value < 0)
    return round(gains / losses, 4) if losses else (None if not gains else math.inf)


def metrics(rows: list[dict], horizon: int, target: float, cost_pct: float) -> dict:
    key = f"ret_{horizon}d"
    returns = [float(row[key]) for row in rows if row[key] is not None]
    # Close-only target proxy: when the close reaches the target, assume an
    # exit at the target; otherwise the position exits at the horizon close.
    # This is not an intraday fill model and is labelled accordingly below.
    gross_hits = [value >= target for value in returns]
    net_hits = [value >= target + cost_pct for value in returns]
    exit_returns = [target if value >= target else value for value in returns]
    net = [value - cost_pct for value in exit_returns]
    n = len(returns)
    if not n:
        return {"n": 0, "coverage": 0.0}
    return {
        "n": n,
        "coverage": round(n / len(rows), 4) if rows else 0.0,
        "hit_rate": round(sum(gross_hits) / n, 4),
        "cost_adjusted_hit_rate": round(sum(net_hits) / n, 4),
        "false_positive_rate": round(1 - sum(gross_hits) / n, 4),
        "miss_rate": round(1 - sum(gross_hits) / n, 4),
        "mean_forward_return": round(sum(returns) / n, 4),
        "median_forward_return": round(median(returns), 4),
        "mean_exit_return_net": round(sum(net) / n, 4),
        "median_exit_return_net": round(median(net), 4),
        "expectancy_net": round(sum(net) / n, 4),
        "profit_factor_net": profit_factor(net),
        "time_to_hit": f"{horizon}d close observation only",
        "mae": "unavailable: no forward lows",
        "mfe": "unavailable: no forward highs",
        "gross_hits": sum(gross_hits),
        "net_hits": sum(net_hits),
    }


def stability(rows: list[dict], horizon: int, target: float) -> dict:
    key = f"ret_{horizon}d"
    monthly: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        value = row[key]
        if value is not None and row.get("scan_date"):
            monthly[str(row["scan_date"])[:7]].append(float(value) >= target)
    rates = [sum(values) / len(values) for values in monthly.values() if values]
    return {
        "months": len(rates),
        "positive_month_share": round(sum(rate > 0.5 for rate in rates) / len(rates), 4)
        if rates
        else None,
        "monthly_hit_rate_std": round(pstdev(rates), 4) if len(rates) > 1 else None,
    }


def run_group(rows: list[dict], label: str, cost_pct: float) -> list[dict]:
    output = []
    for horizon in HORIZONS:
        for target in TARGETS:
            output.append(
                {
                    "group": label,
                    "horizon_days": horizon,
                    "target_pct": target,
                    **metrics(rows, horizon, target, cost_pct),
                    "oos_stability": stability(
                        [r for r in rows if str(r.get("scan_date", "")) >= OOS_START],
                        horizon,
                        target,
                    ),
                }
            )
    return output


def make_groups(rows: list[dict]) -> dict[str, list[dict]]:
    groups = {"all": rows, "dedup_symbol_day": dedup_symbol_day(rows)}
    groups["trend"] = [r for r in rows if r["regime_flag"] is True]
    groups["range"] = [r for r in rows if r["regime_flag"] is False]
    groups["high_vol_atr6"] = [r for r in rows if (r["atr_num"] or 0) >= 6]
    groups["low_vol_atr4"] = [r for r in rows if r["atr_num"] is not None and r["atr_num"] < 4]
    composite = sorted(r["composite_num"] for r in rows if r["composite_num"] is not None)
    if composite:
        q25, q50, q75 = (
            composite[int(len(composite) * fraction)] for fraction in (0.25, 0.50, 0.75)
        )
        groups["composite_q1"] = [
            r for r in rows if r["composite_num"] is not None and r["composite_num"] <= q25
        ]
        groups["composite_q2"] = [
            r for r in rows if r["composite_num"] is not None and q25 < r["composite_num"] <= q50
        ]
        groups["composite_q3"] = [
            r for r in rows if r["composite_num"] is not None and q50 < r["composite_num"] <= q75
        ]
        groups["composite_q4"] = [
            r for r in rows if r["composite_num"] is not None and r["composite_num"] > q75
        ]
    # The export's ``score`` is a legacy zero placeholder; composite_score is
    # the usable score field for this dataset.
    for tier in ("A", "B", "C"):
        groups[f"conviction_{tier}"] = [
            r for r in rows if str(r.get("conviction_tier", "")).upper() == tier
        ]
    return groups


def write_markdown(path: Path, rows: list[dict], results: list[dict], cost_pct: float) -> None:
    def best(group: str, horizon: int, field: str) -> dict | None:
        candidates = [
            r
            for r in results
            if r["group"] == group and r["horizon_days"] == horizon and r.get(field) is not None
        ]
        return max(candidates, key=lambda r: r[field]) if candidates else None

    lines = [
        "# FinPilot Target Return Optimization",
        "",
        f"- Source rows: {len(rows):,}",
        f"- Scan range: {min(r['scan_date'] for r in rows)} to {max(r['scan_date'] for r in rows)}",
        "- Target definition: gross close-to-close return >= target after the signal entry.",
        "- Expectancy proxy: target-hit rows exit at target; misses exit at the horizon close; cost is then deducted.",
        "- Available horizons: 1 and 5 trading days only.",
        f"- Cost model: {cost_pct:.2f}% round trip, applied to expectancy and net-hit rate.",
        "- Duplicate rule: primary all-row view; symbol+scan-day dedup shown separately.",
        "- Not available in this export: intraday peak touch, exact time-to-hit, forward high/low MAE/MFE.",
        "",
        "## Executive summary",
        "",
    ]
    for horizon in HORIZONS:
        hit = best("all", horizon, "hit_rate")
        exp = best("all", horizon, "expectancy_net")
        if hit and exp:
            lines.append(
                f"- {horizon}d: highest gross hit rate is `{hit['target_pct']}%` "
                f"({hit['hit_rate']:.1%}, n={hit['n']:,}); highest net expectancy is "
                f"`{exp['target_pct']}%` ({exp['expectancy_net']:.2f}%)."
            )
    lines += [
        "- Bu sonuçlar peak-touch değildir; `%5` için mevcut güvenilir sonuç yalnızca 1/5 günlük kapanış getirisi tanımındadır.",
        "",
        "## Target sweep: all rows",
        "",
        "| Horizon | Target | N | Hit | Net hit | Mean | Median | Net expectancy | PF | OOS std |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        if r["group"] != "all":
            continue
        pf = "n/a" if r.get("profit_factor_net") is None else str(r["profit_factor_net"])
        std = r["oos_stability"].get("monthly_hit_rate_std")
        lines.append(
            f"| {r['horizon_days']} | {r['target_pct']:.1f}% | {r['n']:,} | {r.get('hit_rate', 0):.1%} | "
            f"{r.get('cost_adjusted_hit_rate', 0):.1%} | {r.get('mean_forward_return', 0):.2f}% | "
            f"{r.get('median_forward_return', 0):.2f}% | {r.get('expectancy_net', 0):.2f}% | {pf} | {std if std is not None else 'n/a'} |"
        )
    lines += ["", "## Group conclusions", ""]
    for group in make_groups(rows):
        five = best(group, 5, "expectancy_net")
        if five:
            lines.append(
                f"- `{group}`: 5d net-expectancy leader `{five['target_pct']}%` "
                f"({five['expectancy_net']:.2f}%, n={five['n']:,})."
            )
    lines += [
        "",
        "## Required-data gaps",
        "",
        "- Peak-touch and exact time-to-hit require forward daily highs/lows or intraday bars per signal.",
        "- MAE/MFE require the same forward OHLC path; the legacy `resolved_pct_*` fields cannot reconstruct them.",
        "- The legacy `score` field is a zero placeholder; composite-score quantiles are included because `composite_score` is populated.",
        "- Conviction A/B/C buckets are included, but only 214 rows carry a conviction tier, so they require cautious interpretation.",
        "- Earnings, market-cap, float and liquidity buckets are not consistently present in this export and are not asserted here.",
        "- A robust production target should be selected only after the missing path labels are generated and walk-forward validated.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument(
        "--out", type=Path, default=Path("data/backtest_out/target_return_optimization.json")
    )
    parser.add_argument("--cost-pct", type=float, default=DEFAULT_COST_PCT)
    args = parser.parse_args()
    rows = load_rows(args.csv)
    groups = make_groups(rows)
    results = [
        item for label, group in groups.items() for item in run_group(group, label, args.cost_pct)
    ]
    payload = {
        "generated_at": date.today().isoformat(),
        "source": str(args.csv),
        "methodology": {
            "target_definition": "close-to-close forward return >= target_pct",
            "horizons_available": list(HORIZONS),
            "targets_pct": list(TARGETS),
            "cost_round_trip_pct": args.cost_pct,
            "oos_start": OOS_START,
            "peak_touch": "unavailable",
            "time_to_hit": "unavailable",
            "mae_mfe": "unavailable",
        },
        "results": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = args.out.with_suffix(".md")
    write_markdown(md, rows, results, args.cost_pct)
    print(f"rows={len(rows)} groups={len(groups)} results={len(results)}")
    print(f"json={args.out}")
    print(f"report={md}")


if __name__ == "__main__":
    main()
