"""Baseline Ranking Health & Component Decomposition — PRE-REGISTERED.

Date: 2026-09-09 · Master Validation Prompt v1.0
Level A · READ-ONLY · NO OPTIMIZATION.

PRIMARY QUESTION: Is FinPilot's baseline ranking (composite_score) demonstrably
better than random at ranking forward returns (c2c_1d)?

PRE-REGISTERED decisions (fixed BEFORE results):
  - Dataset: data/backtest_out/full_universe_enriched_eod_only.csv
  - Cleaning: existing methodology — sort by (scan_date, symbol), drop duplicate
    symbol/date keep="first", drop rows with null composite_score. NO new filters.
  - Primary target: c2c_1d. Secondary: c2c_5d (reported SEPARATELY).
  - Ranking score = composite_score (0-100). finpilot_score ~ equal (DRL off).
  - Baseline components available as columns: score(0-3 raw), regime, direction,
    vol_regime, atr_pct_real, rvol, squeeze_factor, lottery_factor,
    overnight_gap_factor, dist_52w_high, gap_pct, price, tier_score.
    NOT AVAILABLE as columns (limitation, NOT fabricated): alignment_ratio,
    momentum_ratio, filter_score, volume_spike, price_momentum, trend_strength.
  - Random seed: 20260909 (fixed). Random replications: 300 (per scan-date,
    matched universe & sample size).
  - Top-N: 5/10/20/50/100.
  - Monotonicity: quintiles Q1-Q5.
  - Walk-forward windows: reuse prior (W2 2026-04-22->05-22, W3 05-13->06-12,
    W4 06-03->07-03); W1 excluded (degenerate in prior run).
  - Component ablation: leave-one-out on RECONSTRUCTIBLE components only, weights
    NOT re-fitted (contributions simply removed where the exact production weight
    is known: score*0.5, regime*2, direction*2). Continuous inputs unavailable ->
    their ablation is UNVALIDATED, reported as limitation.
  - Multiple testing: reported; p<0.05 alone is NOT validation.
  - Permutation test: within-scan-date rank shuffle, 300 permutations.
  - NO production/code/flag/weight/data changes. No overwrites.
Outputs: reports/baseline_ranking_health_2026-09-09.md + 5 CSVs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SEED = 20260909
REPS = 300
TOPNS = [5, 10, 20, 50, 100]
WINDOWS = {
    "W2": ("2026-04-22", "2026-05-22"),
    "W3": ("2026-05-13", "2026-06-12"),
    "W4": ("2026-06-03", "2026-07-03"),
}
DATA = "data/backtest_out/full_universe_enriched_eod_only.csv"


# Reconstructible baseline component contributions (production weights, OFF flags excluded)
def comp_contributions(d: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=d.index)
    out["score_contrib"] = d["score"].astype(float) * 0.5
    out["regime_contrib"] = d["regime"].astype(float) * 2.0
    out["direction_contrib"] = d["direction"].astype(float) * 2.0
    return out


# Available per-row baseline INPUT columns treated as "components" for direct tests
COMPONENT_COLS = {
    "score": "score",
    "regime": "regime",
    "direction": "direction",
    "vol_regime": "vol_regime",
    "atr_pct_real": "atr_pct_real",
    "rvol": "rvol",
    "squeeze_factor": "squeeze_factor",
    "lottery_factor": "lottery_factor",
    "overnight_gap_factor": "overnight_gap_factor",
    "dist_52w_high": "dist_52w_high",
    "gap_pct": "gap_pct",
    "tier_score": "tier_score",
}


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA, low_memory=False)
    df["scan_date"] = pd.to_datetime(df["scan_date"])
    df = df.sort_values(["scan_date", "symbol"]).drop_duplicates(
        subset=["symbol", "scan_date"], keep="first"
    )
    df = df.dropna(subset=["composite_score"]).copy()
    return df


def integrity(df: pd.DataFrame) -> dict:
    d0 = pd.read_csv(DATA, low_memory=False)
    return {
        "raw_rows": len(d0),
        "dedup_rows": int(df.shape[0] + df["composite_score"].isna().sum()),
        "final_rows": len(df),
        "unique_symbols": int(df["symbol"].nunique()),
        "unique_dates": int(df["scan_date"].nunique()),
        "date_min": str(df["scan_date"].min().date()),
        "date_max": str(df["scan_date"].max().date()),
        "dup_symbol_date": int(df.duplicated(subset=["symbol", "scan_date"]).sum()),
        "missing_score": int(df["composite_score"].isna().sum()),
        "missing_c2c_1d": int(df["c2c_1d"].isna().sum()),
        "missing_c2c_5d": int(df["c2c_5d"].isna().sum()),
        "c2c_1d_outliers_>|50%|": int((df["c2c_1d"].abs() > 50).sum()),
    }


def spearman(a, b):
    a = pd.Series(a)
    b = pd.Series(b)
    m = a.notna() & b.notna()
    if m.sum() < 10:
        return np.nan
    return a[m].rank().corr(b[m].rank())


def quintile_table(d: pd.DataFrame, col: str, target: str) -> pd.DataFrame:
    x = d[col].astype(float)
    y = d[target].astype(float)
    m = x.notna() & y.notna()
    x, y = x[m], y[m]
    if len(x) < 50 or x.nunique() < 5:
        return pd.DataFrame()
    try:
        q = pd.qcut(x, 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"], duplicates="drop")
    except ValueError:
        return pd.DataFrame()
    g = pd.DataFrame({"q": q, "y": y}).groupby("q", observed=True)["y"]
    return pd.DataFrame(
        {
            "n": g.size(),
            "mean": g.mean(),
            "median": g.median(),
            "hit": g.apply(lambda s: (s > 0).mean()),
        }
    )


def topn_stats(d: pd.DataFrame, score_col: str, target: str, n: int) -> dict:
    # rank within each scan_date, take top-n per date
    def per_date(g):
        gg = g.nlargest(min(n, len(g)), score_col)
        y = gg[target]
        return pd.Series(
            {"mean": y.mean(), "median": y.median(), "hit": (y > 0).mean(), "n": len(gg)}
        )

    res = d.groupby("scan_date").apply(per_date)
    return {
        "top_n": n,
        "mean_return": res["mean"].mean(),
        "median_return": res["median"].mean(),
        "hit_rate": res["hit"].mean(),
        "dates": len(res),
    }


def random_baseline(d: pd.DataFrame, target: str, n: int) -> np.ndarray:
    rng = np.random.default_rng(SEED)
    dates = d["scan_date"].unique()
    out = []
    for _ in range(REPS):
        rets = []
        for dt in dates:
            g = d[d["scan_date"] == dt]
            if len(g) == 0:
                continue
            k = min(n, len(g))
            samp = g[target].iloc[rng.choice(len(g), size=k, replace=False)]
            rets.append(samp.mean())
        out.append(np.nanmean(rets))
    return np.array(out)


def monotonicity(qt: pd.DataFrame) -> str:
    if qt.empty:
        return "INSUFFICIENT DATA"
    means = qt["mean"].values
    if len(means) < 3:
        return "INSUFFICIENT DATA"
    diffs = np.diff(means)
    if np.all(diffs > 0):
        return "POSITIVE MONOTONIC"
    if np.all(diffs < 0):
        return "NEGATIVE MONOTONIC"
    if np.all(np.abs(means - means.mean()) < 1e-9):
        return "FLAT"
    return "NON-MONOTONIC"


def winsorize(s: pd.Series, lo=0.01, hi=0.99) -> pd.Series:
    a, b = s.quantile(lo), s.quantile(hi)
    return s.clip(a, b)


def random_baseline_robust(d: pd.DataFrame, target: str, n: int):
    """Random control on winsorized mean + median (robust to penny-stock outliers)."""
    rng = np.random.default_rng(SEED)
    dates = d["scan_date"].unique()
    wm, md = [], []
    for _ in range(REPS):
        mrets, dre = [], []
        for dt in dates:
            g = d[d["scan_date"] == dt]
            if len(g) == 0:
                continue
            k = min(n, len(g))
            samp = g[target].iloc[rng.choice(len(g), size=k, replace=False)]
            mrets.append(samp.mean())
            dre.append(samp.median())
        wm.append(np.nanmean(mrets))
        md.append(np.nanmean(dre))
    return np.array(wm), np.array(md)


def main() -> None:
    df = load()
    print("integrity:", integrity(df))

    target = "c2c_1d"
    dd = df.dropna(subset=[target]).copy()

    # 6/7. Baseline reconstruction note + contributions
    contrib = comp_contributions(dd)

    # 8. contribution distribution
    dist_rows = []
    for c in contrib.columns:
        s = contrib[c]
        dist_rows.append(
            {
                "component": c,
                "mean": s.mean(),
                "median": s.median(),
                "std": s.std(),
                "min": s.min(),
                "max": s.max(),
                "pct_pos": (s > 0).mean(),
                "pct_zero": (s == 0).mean(),
                "pct_neg": (s < 0).mean(),
            }
        )
    pd.DataFrame(dist_rows).to_csv(
        "reports/baseline_component_contributions_2026-09-09.csv", index=False
    )

    # 9/10. direct predictiveness + monotonicity
    pred_rows = []
    for name, col in COMPONENT_COLS.items():
        if col not in dd.columns:
            continue
        x = pd.to_numeric(dd[col], errors="coerce")
        y = dd[target]
        qt = quintile_table(dd, col, target)
        pred_rows.append(
            {
                "component": name,
                "pearson": x.corr(y),
                "spearman": spearman(x, y),
                "monotonicity": monotonicity(qt),
                "q1_mean": qt["mean"].iloc[0] if not qt.empty else np.nan,
                "q5_mean": qt["mean"].iloc[-1] if not qt.empty else np.nan,
                "q5_minus_q1": (qt["mean"].iloc[-1] - qt["mean"].iloc[0])
                if not qt.empty
                else np.nan,
            }
        )
    # also composite itself
    qt_comp = quintile_table(dd, "composite_score", target)
    pred_rows.append(
        {
            "component": "composite_score",
            "pearson": dd["composite_score"].corr(dd[target]),
            "spearman": spearman(dd["composite_score"], dd[target]),
            "monotonicity": monotonicity(qt_comp),
            "q1_mean": qt_comp["mean"].iloc[0],
            "q5_mean": qt_comp["mean"].iloc[-1],
            "q5_minus_q1": qt_comp["mean"].iloc[-1] - qt_comp["mean"].iloc[0],
        }
    )
    pd.DataFrame(pred_rows).to_csv(
        "reports/baseline_component_predictiveness_2026-09-09.csv", index=False
    )

    # 11/12. buckets + top-N for composite
    topn_rows = [topn_stats(dd, "composite_score", target, n) for n in TOPNS]
    qt_comp.to_csv("reports/baseline_score_buckets_2026-09-09.csv")

    # 13/14. random replications (raw + robust winsorized)
    rc_rows = []
    dd["_w"] = winsorize(dd[target])
    for n in TOPNS:
        base = topn_stats(dd, "composite_score", target, n)["mean_return"]
        base_w = topn_stats(dd.assign(c2c_1d=dd["_w"]), "composite_score", target, n)["mean_return"]
        base_med = topn_stats(dd, "composite_score", target, n)["median_return"]
        rnd = random_baseline(dd, target, n)
        rw, rm = random_baseline_robust(dd, target, n)
        pct = (rnd < base).mean()
        rc_rows.append(
            {
                "top_n": n,
                "baseline_mean": base,
                "random_mean": rnd.mean(),
                "random_std": rnd.std(),
                "baseline_percentile": pct,
                "baseline_minus_random": base - rnd.mean(),
                "baseline_winsorized": base_w,
                "random_winsorized_mean": rw.mean(),
                "baseline_minus_random_wins": base_w - rw.mean(),
                "baseline_median": base_med,
                "random_median_mean": rm.mean(),
                "baseline_minus_random_median": base_med - rm.mean(),
            }
        )
    pd.DataFrame(rc_rows).to_csv("reports/baseline_random_control_2026-09-09.csv", index=False)

    # 15. permutation test (within-date shuffle of ranks) for top-20
    rng = np.random.default_rng(SEED + 1)
    dates = dd["scan_date"].unique()
    real = topn_stats(dd, "composite_score", target, 20)["mean_return"]
    perm = []
    arr = dd[["scan_date", "composite_score", target]].dropna()
    for _ in range(REPS):
        rets = []
        for dt in dates:
            g = arr[arr["scan_date"] == dt]
            if len(g) < 5:
                continue
            sh = g[target].iloc[rng.permutation(len(g))].values
            order = np.argsort(-g["composite_score"].values)
            k = min(20, len(g))
            rets.append(sh[order[:k]].mean())
        perm.append(np.nanmean(rets))
    perm = np.array(perm)
    pval = (perm >= real).mean()

    # 16/17. walk-forward baseline health
    wf_rows = []
    for wname, (a, b) in WINDOWS.items():
        w = dd[(dd["scan_date"] >= a) & (dd["scan_date"] <= b)].copy()
        if len(w) < 100:
            wf_rows.append({"window": wname, "oos_n": len(w), "status": "insufficient"})
            continue
        cut = w["scan_date"].quantile(0.7)
        oos = w[w["scan_date"] > cut]
        if len(oos) < 20:
            wf_rows.append({"window": wname, "oos_n": len(oos), "status": "insufficient"})
            continue
        base20 = topn_stats(oos, "composite_score", target, 20)["mean_return"]
        rnd = random_baseline(oos, target, 20)
        wf_rows.append(
            {
                "window": wname,
                "oos_n": len(oos),
                "spearman": spearman(oos["composite_score"], oos[target]),
                "top20_mean": base20,
                "top20_hit": topn_stats(oos, "composite_score", target, 20)["hit_rate"],
                "random20_mean": rnd.mean(),
                "baseline_minus_random": base20 - rnd.mean(),
                "baseline_percentile": (rnd < base20).mean(),
                "status": "ok",
            }
        )
    pd.DataFrame(wf_rows).to_csv("reports/baseline_walk_forward_2026-09-09.csv", index=False)

    # 19/21. leave-one-out ablation (reconstructible only)
    ab_rows = []
    for drop in ["score_contrib", "regime_contrib", "direction_contrib"]:
        adj = dd["composite_score"] - contrib[drop] * (100.0 / 16.5)
        tmp = dd.copy()
        tmp["_adj"] = adj
        ab_rows.append(
            {
                "removed": drop,
                "spearman": spearman(tmp["_adj"], tmp[target]),
                "top20_mean": topn_stats(tmp, "_adj", target, 20)["mean_return"],
                "top20_hit": topn_stats(tmp, "_adj", target, 20)["hit_rate"],
            }
        )
    ab_rows.insert(
        0,
        {
            "removed": "NONE_full_baseline",
            "spearman": spearman(dd["composite_score"], dd[target]),
            "top20_mean": topn_stats(dd, "composite_score", target, 20)["mean_return"],
            "top20_hit": topn_stats(dd, "composite_score", target, 20)["hit_rate"],
        },
    )
    pd.DataFrame(ab_rows).to_csv("reports/baseline_component_ablation_2026-09-09.csv", index=False)

    # 28. correlation / redundancy among available components
    numc = [c for c in COMPONENT_COLS.values() if c in dd.columns]
    corr = dd[numc + ["composite_score"]].corr()

    # 29/30. score compression / ties
    comp = dd["composite_score"]
    compression = {
        "nunique": int(comp.nunique()),
        "rows": len(comp),
        "pct_ties": float(comp.duplicated().mean()),
        "range": [float(comp.min()), float(comp.max())],
    }

    # save a compact json-ish summary
    import json

    summ = {
        "integrity": integrity(df),
        "permutation_top20": {
            "real": real,
            "perm_mean": perm.mean(),
            "p_value": pval,
            "percentile": (perm < real).mean(),
        },
        "compression": compression,
        "topn": topn_rows,
        "random_control": rc_rows,
        "walk_forward": wf_rows,
    }
    with open(
        "data/backtest_out/baseline_ranking_health_2026-09-09.json", "w", encoding="utf-8"
    ) as f:
        json.dump(summ, f, indent=2, default=str)
    corr.to_csv("reports/baseline_component_correlation_2026-09-09.csv")

    print("\n=== TOP-N (c2c_1d) ===")
    [print(r) for r in topn_rows]
    print("\n=== RANDOM CONTROL ===")
    [print(r) for r in rc_rows]
    print(
        f"\n=== PERMUTATION top20: real={real:.4f} perm={perm.mean():.4f} "
        f"p={pval:.3f} pct={(perm < real).mean():.3f}"
    )
    print("\n=== WALK-FORWARD ===")
    [print(r) for r in wf_rows]
    print("\n=== COMPRESSION ===", compression)
    print("\n=== PREDICTIVENESS ===")
    for r in pred_rows:
        print(r)
    print("\n=== ABLATION ===")
    [print(r) for r in ab_rows]


if __name__ == "__main__":
    main()
