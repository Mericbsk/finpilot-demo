"""RESEARCH-X — Loser / Failure Phenotype Audit. READ-ONLY, DESCRIPTIVE.

Date: 2026-09-21. Meriç-framed reverse-angle research. NO new score, NO model, NO
threshold optimization, NO feature mining to "explain" — Phase 1 phenotype discovery ONLY.

Goal: characterize the anatomy of FinPilot's failures — which conditions produce
high-score stocks that FALL (and big-fall), and which low-score stocks RISE.

Cohorts (score split at median within scan_date; outcome by c2c_5d):
  HIGH_SCORE -> BIG_LOSER  (c2c_5d <= -10%)
  HIGH_SCORE -> NORMAL_LOSER (-10% < c2c_5d < 0)
  HIGH_SCORE -> WINNER (c2c_5d > 0)
  LOW_SCORE  -> BIG_WINNER (c2c_5d >= +10%)
  LOW_SCORE  -> NORMAL_WINNER (0 < c2c_5d < 10%)
  LOW_SCORE  -> LOSER (c2c_5d < 0)
Plus UNCONDITIONAL baseline.

For each cohort: distribution of available features (gap_pct, atr_pct_real, rvol,
  dist_52w_high, lottery_factor, squeeze_factor, overnight_gap_factor, vol_regime,
  regime, direction, composite_score, score, price). Report median/IQR per cohort.
Clustering: do failures cluster by scan_date? by vol_regime? by regime?
Pre-registered: descriptive only; any pattern -> HYPOTHESIS (not conclusion).
No production/change. Negative/empty findings reported honestly.
Output: reports/research_x_failure_phenotype_2026-09-21.md + JSON.
"""

from __future__ import annotations

import json

import pandas as pd

DATA = "data/backtest_out/full_universe_enriched_eod_only.csv"
OUT_JSON = "data/backtest_out/research_x_failure_phenotype_2026-09-21.json"
FEATURES = [
    "gap_pct",
    "atr_pct_real",
    "rvol",
    "dist_52w_high",
    "lottery_factor",
    "squeeze_factor",
    "overnight_gap_factor",
    "vol_regime",
    "composite_score",
    "score",
    "price",
]


def cohort_label(score_high: bool, r: float) -> str:
    if score_high:
        if r <= -10:
            return "HS_BIG_LOSER"
        if r < 0:
            return "HS_NORMAL_LOSER"
        return "HS_WINNER"
    else:
        if r >= 10:
            return "LS_BIG_WINNER"
        if r > 0:
            return "LS_NORMAL_WINNER"
        return "LS_LOSER"


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    df["scan_date"] = pd.to_datetime(df["scan_date"])
    df = df.sort_values(["scan_date", "symbol"]).drop_duplicates(
        subset=["symbol", "scan_date"], keep="first"
    )
    df = df.dropna(subset=["composite_score", "c2c_1d", "c2c_5d"]).copy()
    # score split: median within each scan_date (point-in-time safe)
    df["score_median"] = df.groupby("scan_date")["composite_score"].transform("median")
    df["high_score"] = df["composite_score"] >= df["score_median"]
    df["cohort"] = [
        cohort_label(h, r) for h, r in zip(df["high_score"], df["c2c_5d"], strict=False)
    ]

    res = {"n": len(df), "cohort_counts": df["cohort"].value_counts().to_dict()}

    # Per-cohort feature distributions (median + IQR)
    cohort_feat = {}
    for coh, g in df.groupby("cohort"):
        fd = {}
        for f in FEATURES:
            if f in g.columns and g[f].notna().sum() >= 30:
                v = pd.to_numeric(g[f], errors="coerce").dropna()
                if len(v) >= 30:
                    fd[f] = {
                        "median": round(float(v.median()), 4),
                        "iqr": round(float(v.quantile(0.75) - v.quantile(0.25)), 4),
                        "n": len(v),
                    }
        cohort_feat[coh] = fd
    res["cohort_features"] = cohort_feat

    # Baseline (unconditional) for reference
    base = {}
    for f in FEATURES:
        v = pd.to_numeric(df[f], errors="coerce").dropna()
        if len(v) >= 30:
            base[f] = {
                "median": round(float(v.median()), 4),
                "iqr": round(float(v.quantile(0.75) - v.quantile(0.25)), 4),
            }
    res["baseline_features"] = base

    # Clustering: do failures cluster by scan_date / vol_regime / regime?
    big_loser = df[df["c2c_5d"] <= -10]
    res["big_loser_n"] = len(big_loser)
    res["big_loser_rate_overall"] = round(float((df["c2c_5d"] <= -10).mean()), 4)
    # by scan_date concentration: share of big losers in top-3 worst dates
    by_date = big_loser.groupby("scan_date").size().sort_values(ascending=False)
    res["big_loser_top3_dates_share"] = round(
        float(by_date.head(3).sum() / max(1, len(big_loser))), 4
    )
    # by vol_regime
    if "vol_regime" in df.columns:
        vr = df.dropna(subset=["vol_regime"])
        res["bigloser_by_volregime"] = {
            str(int(k)): round(float((vr[vr["vol_regime"] == k]["c2c_5d"] <= -10).mean()), 4)
            for k in sorted(vr["vol_regime"].unique())
        }
    # by regime bool
    res["bigloser_by_regime"] = {
        str(k): round(float((df[df["regime"] == k]["c2c_5d"] <= -10).mean()), 4)
        for k in [True, False]
    }
    # inverted check: high_score big-loser rate vs low_score big-loser rate
    res["bigloser_rate_high_score"] = round(
        float((df[df["high_score"]]["c2c_5d"] <= -10).mean()), 4
    )
    res["bigloser_rate_low_score"] = round(
        float((df[~df["high_score"]]["c2c_5d"] <= -10).mean()), 4
    )
    res["bigwinner_rate_low_score"] = round(
        float((df[~df["high_score"]]["c2c_5d"] >= 10).mean()), 4
    )
    res["bigwinner_rate_high_score"] = round(
        float((df[df["high_score"]]["c2c_5d"] >= 10).mean()), 4
    )

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, default=str)
    print(json.dumps(res, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
