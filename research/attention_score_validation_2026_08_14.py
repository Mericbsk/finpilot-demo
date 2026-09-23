"""Attention Score validation — matched-control + month-by-month stability.

Produces the numbers cited in the migration plan. Every number is traceable
to this script and its output artifact.

Usage: python -m research.attention_score_validation_2026_08_14
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(20260814)
BOOTSTRAP_DRAWS = 1000
MATCHED_RUNS = 100


def load_data() -> pd.DataFrame:
    df = pd.read_csv("data/backtest_out/full_universe_enriched.csv", low_memory=False)
    df = df.drop_duplicates(["symbol", "scan_date"], keep="first")
    df = df[(df["price"] >= 1.0) & (df["c2c_5d"].notna()) & (df["c2c_5d"].abs() <= 100)]
    return df


def attention_score(row: pd.Series) -> int:
    """Export-field-based attention score (validated against export data)."""
    score = 0
    if abs(row.get("gap_pct", 0) or 0) >= 3:
        score += 25
    if (row.get("atr_pct_real") or 0) >= 6:
        score += 25
    if (row.get("rvol") or 0) >= 2.0:
        score += 15
    if (row.get("dist_52w_high") or 1.0) < 0.3:
        score += 15
    if (row.get("lottery_factor") or 0) >= 0.6:
        score += 10
    if (row.get("squeeze_factor") or 0) >= 0.5:
        score += 10
    return score


def matched_control(df: pd.DataFrame, att: pd.DataFrame) -> dict:
    """Same-date random control: |5d| median of attention vs random."""
    diffs = []
    for date in att["scan_date"].unique():
        s = att[att["scan_date"] == date]
        u = df[(df["scan_date"] == date) & (~df.index.isin(s.index))]
        if len(u) < len(s) or len(s) == 0:
            continue
        s_abs_med = s["c2c_5d"].abs().median()
        for _ in range(MATCHED_RUNS):
            rand = u.sample(n=min(len(s), len(u)), replace=False, random_state=RNG)
            diffs.append(s_abs_med - rand["c2c_5d"].abs().median())
    arr = np.array(diffs)
    return {
        "median_diff_pp": float(np.median(arr)),
        "p_value": float((arr <= 0).mean()),
        "share_positive": float((arr > 0).mean()),
        "n_comparisons": len(diffs),
    }


def monthly_stability(df: pd.DataFrame) -> list[dict]:
    """Month-by-month |5d| lift of attention >= 25 vs < 25."""
    df = df.copy()
    df["month"] = df["scan_date"].str[:7]
    results = []
    for m in sorted(df["month"].unique()):
        cell = df[df["month"] == m]
        att_m = cell[cell["attention_score"] >= 25]
        norm_m = cell[cell["attention_score"] < 25]
        if len(att_m) < 20 or len(norm_m) < 20:
            continue
        att_med = att_m["c2c_5d"].abs().median()
        norm_med = norm_m["c2c_5d"].abs().median()
        lift = att_med / norm_med if norm_med > 0 else None
        results.append(
            {
                "month": m,
                "attention_n": len(att_m),
                "attention_abs5d_median": round(float(att_med), 4),
                "normal_abs5d_median": round(float(norm_med), 4),
                "lift": round(float(lift), 4) if lift else None,
            }
        )
    return results


def main() -> None:
    df = load_data()
    df["attention_score"] = df.apply(attention_score, axis=1)
    att = df[df["attention_score"] >= 25]

    # Matched control
    mc = matched_control(df, att)

    # Monthly stability
    monthly = monthly_stability(df)

    # Precision and coverage
    movers = df[df["c2c_5d"].abs() >= 5]
    att_movers = att[att["c2c_5d"].abs() >= 5]
    precision = len(att_movers) / len(att) if len(att) else 0
    coverage = len(att_movers) / len(movers) if len(movers) else 0
    base_rate = len(movers) / len(df) if len(df) else 0
    lift = precision / base_rate if base_rate > 0 else 0

    # Day-clustered bootstrap CI for |5d| median of attention group
    by_date = defaultdict(list)
    for _, r in att.iterrows():
        by_date[r["scan_date"]].append(r["c2c_5d"])
    dates = list(by_date.keys())
    boots = []
    for _ in range(BOOTSTRAP_DRAWS):
        sample = RNG.choice(dates, size=len(dates), replace=True)
        pooled = np.concatenate([by_date[d] for d in sample])
        boots.append(float(np.median(np.abs(pooled))))
    boots = np.array(boots)

    result = {
        "status": "exploratory",
        "production_change": False,
        "locked_oos": "not_opened",
        "data": "full_universe_enriched.csv, dedup, price>=$1, |c2c_5d|<=100%",
        "n_total": len(df),
        "n_attention": len(att),
        "attention_threshold": 25,
        "matched_control": mc,
        "monthly_stability": monthly,
        "precision": round(precision, 4),
        "coverage": round(coverage, 4),
        "base_rate": round(base_rate, 4),
        "lift": round(lift, 4),
        "day_clustered_ci": {
            "point": float(np.median(att["c2c_5d"].abs())),
            "ci_lo": float(np.percentile(boots, 2.5)),
            "ci_hi": float(np.percentile(boots, 97.5)),
            "n_dates": len(dates),
        },
        "tier_distribution": {
            tier: len(df[df["attention_score"].between(*rng)])
            for tier, rng in [("normal", (0, 24)), ("watch", (25, 49)), ("high", (50, 100))]
        },
    }

    out = Path("data/backtest_out/attention_score_validation_2026-08-14.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    print(
        json.dumps(
            {k: v for k, v in result.items() if k != "monthly_stability"}, indent=2, default=str
        )
    )
    print("\nMonthly stability:")
    for m in monthly:
        print(f"  {m['month']}: lift={m['lift']}x (att n={m['attention_n']})")


if __name__ == "__main__":
    main()
