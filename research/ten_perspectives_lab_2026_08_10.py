#!/usr/bin/env python3
"""Ten-Perspectives Lab experiment battery (research-only, Level A).

Executes the feasible, not-yet-run experiments from the 2026-08-10
"10-Perspective Independent Brainstorming & Red-Team" report. Experiments
already covered by `research/strategic_lab_2026_08_10.py` (R1-R5, E1/E2,
X1/X3/X6, G2/G4, P1/P2/P7, S1) are not duplicated; user-facing, LLM-facing
and intraday-data experiments remain BLOCKED and are listed in the report.

Same hard rules as the strategic lab battery: frozen fields only, no new
parameter search, robust statistics, date-block bootstrap CIs, diagnostic
statuses. Nothing here is a promotion or production decision.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from research.strategic_lab_2026_08_10 import (
    DEFAULT_AUDIT,
    DEFAULT_CACHE,
    DEFAULT_CSV,
    block_bootstrap_ci,
    compute_path_metrics,
    dist_summary,
    load_bars,
    load_export,
    load_flagged_symbols,
)

DEFAULT_OUT = Path("data/backtest_out/ten_perspectives_lab_2026-08-10.json")
COST_PCT = 0.55
SEED = 20260810
PRE_ENTRY_FEATURES = [
    "gap_pct",
    "rvol",
    "atr_pct_real",
    "dist_52w_high",
    "past_5d_pct",
    "finpilot_score",
    "squeeze_factor",
    "lottery_factor",
    "overnight_gap_factor",
    "sentiment",
]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _spearman(x: pd.Series, y: pd.Series) -> float | None:
    sub = pd.concat([x, y], axis=1).dropna()
    if len(sub) < 100:
        return None
    rho = spearmanr(sub.iloc[:, 0], sub.iloc[:, 1]).statistic
    return round(float(rho), 4)


def _benchmark_returns(df: pd.DataFrame, cache_dir: Path, symbol: str) -> pd.Series:
    """Date-aligned benchmark 5d close-to-close return per row."""
    bars = load_bars(cache_dir, symbol)
    if not bars:
        return pd.Series(np.nan, index=df.index)
    dates = [str(b["date"]) for b in bars]
    closes = np.array([b["close"] for b in bars], dtype=float)
    out = {}
    for idx, scan_date in df["scan_date"].items():
        entry = None
        for i, d in enumerate(dates):
            if d >= scan_date:
                entry = i
                break
        if entry is None or entry + 5 >= len(closes) or closes[entry] <= 0:
            out[idx] = np.nan
        else:
            out[idx] = float((closes[entry + 5] / closes[entry] - 1.0) * 100.0)
    return pd.Series(out)


def _kmeans(frame: np.ndarray, k: int, seed: int = SEED, iters: int = 25) -> np.ndarray:
    """Small dependency-free Lloyd's k-means with k-means++ init."""
    rng = np.random.default_rng(seed)
    n = len(frame)
    centers = [frame[rng.integers(n)]]
    for _ in range(k - 1):
        d2 = np.min(((frame[:, None, :] - np.array(centers)[None]) ** 2).sum(-1), axis=1)
        probs = d2 / d2.sum() if d2.sum() > 0 else np.full(n, 1 / n)
        centers.append(frame[rng.choice(n, p=probs)])
    centers = np.array(centers)
    labels = np.zeros(n, dtype=int)
    for _ in range(iters):
        dist = ((frame[:, None, :] - centers[None]) ** 2).sum(-1)
        new_labels = dist.argmin(axis=1)
        if (new_labels == labels).all():
            break
        labels = new_labels
        for c in range(k):
            members = frame[labels == c]
            if len(members):
                centers[c] = members.mean(axis=0)
    return labels


# ---------------------------------------------------------------------------
# Experiments
# ---------------------------------------------------------------------------


def exp_adverse_movement_target(df: pd.DataFrame) -> dict:
    """Q: does the score predict adverse movement (MAE <= -1 ATR)?"""
    sub = df.dropna(subset=["mae_5d_pct", "atr", "cache_close", "finpilot_score"]).copy()
    sub["atr_pct"] = sub["atr"] / sub["cache_close"] * 100.0
    sub["adverse"] = (sub["mae_5d_pct"] <= -sub["atr_pct"]).astype(float)
    if len(sub) < 1000:
        return {"status": "INSUFFICIENT_DATA", "n": int(len(sub))}
    base_rate = float(sub["adverse"].mean())
    rho = _spearman(sub["finpilot_score"], sub["adverse"])
    elig = sub[sub["entry_ok"]]
    return {
        "status": "COMPLETED",
        "n": int(len(sub)),
        "base_rate_adverse": round(base_rate, 4),
        "eligible_rate_adverse": round(float(elig["adverse"].mean()), 4),
        "spearman_score_vs_adverse": rho,
        "interpretation": (
            "higher score is associated with MORE adverse movement"
            if rho is not None and rho > 0.02
            else "higher score is associated with less adverse movement"
            if rho is not None and rho < -0.02
            else "score carries no meaningful adverse-movement information"
        ),
    }


def exp_failure_prediction(df: pd.DataFrame) -> dict:
    """Q: can pre-entry features predict failure (fwd_5d < -cost)?"""
    sub = df.dropna(subset=["fwd_5d_pct"]).copy()
    sub["failed"] = (sub["fwd_5d_pct"] < -COST_PCT).astype(float)
    table = {}
    for feat in PRE_ENTRY_FEATURES:
        rho = _spearman(sub[feat], sub["failed"])
        if rho is not None:
            table[feat] = rho
    ranked = dict(sorted(table.items(), key=lambda kv: -abs(kv[1])))
    return {
        "status": "COMPLETED",
        "n": int(len(sub)),
        "base_failure_rate": round(float(sub["failed"].mean()), 4),
        "spearman_with_failure": ranked,
        "best_feature": next(iter(ranked), None),
        "interpretation": "ranked univariate association with failure; |rho| < 0.05 is noise-level",
    }


def exp_score_semantics(df: pd.DataFrame) -> dict:
    """Q: what does the score encode, and which features carry forward info?"""
    sub = df.dropna(subset=["finpilot_score", "fwd_5d_pct"])
    semantics, forward = {}, {}
    for feat in PRE_ENTRY_FEATURES:
        if feat == "finpilot_score":
            continue
        rho_score = _spearman(sub["finpilot_score"], sub[feat])
        rho_fwd = _spearman(sub[feat], sub["fwd_5d_pct"])
        if rho_score is not None:
            semantics[feat] = rho_score
        if rho_fwd is not None:
            forward[feat] = rho_fwd
    return {
        "status": "COMPLETED",
        "n": int(len(sub)),
        "score_encodes": dict(sorted(semantics.items(), key=lambda kv: -abs(kv[1]))),
        "feature_forward_info": dict(sorted(forward.items(), key=lambda kv: -abs(kv[1]))),
        "note": "catalyst_factor is constant zero in this export and carries no information",
    }


def exp_null_feature_injection(df: pd.DataFrame) -> dict:
    """Q: how large are spurious feature-outcome correlations at this sample size?"""
    sub = df.dropna(subset=["fwd_5d_pct"])
    y = sub["fwd_5d_pct"].to_numpy()
    rng = np.random.default_rng(SEED)
    null_rhos = []
    for _ in range(20):
        null_feat = rng.normal(0, 1, len(sub))
        null_rhos.append(abs(spearmanr(null_feat, y).statistic))
    real = {f: abs(_spearman(sub[f], sub["fwd_5d_pct"]) or 0.0) for f in PRE_ENTRY_FEATURES}
    null_p95 = float(np.quantile(null_rhos, 0.95))
    return {
        "status": "COMPLETED",
        "n": int(len(sub)),
        "null_abs_spearman_p95": round(null_p95, 4),
        "real_abs_spearman": {k: round(v, 4) for k, v in real.items()},
        "features_above_null_p95": [k for k, v in real.items() if v > null_p95],
        "interpretation": (
            "features exceeding the null p95 carry detectable (not necessarily useful) signal"
        ),
    }


def exp_benchmark_relative(df: pd.DataFrame, cache_dir: Path) -> dict:
    """Q: do eligible candidates beat SPY/IWM over the same window?"""
    sub = df.dropna(subset=["fwd_5d_pct"]).copy()
    spy = _benchmark_returns(sub, cache_dir, "SPY")
    iwm = _benchmark_returns(sub, cache_dir, "IWM")
    sub["rel_spy"] = sub["fwd_5d_pct"] - spy
    sub["rel_iwm"] = sub["fwd_5d_pct"] - iwm
    elig = sub[sub["entry_ok"]]
    out = {"status": "COMPLETED"}
    for col in ("rel_spy", "rel_iwm"):
        out[col] = {
            "eligible": {
                **dist_summary(elig[col]),
                "block_ci": block_bootstrap_ci(elig.dropna(subset=[col]), col),
            },
            "all_rows": dist_summary(sub[col]),
        }
    out["interpretation"] = (
        "eligible cohort beats benchmarks on median"
        if (out["rel_spy"]["eligible"]["median"] or 0) > 0
        else "eligible cohort does NOT beat benchmarks on median (simple subtraction, not beta-neutral)"
    )
    return out


def exp_first_passage(df: pd.DataFrame) -> dict:
    """Q: within 5d, does the favorable or adverse excursion come first?"""
    sub = df.dropna(subset=["time_to_mfe_5d", "time_to_mae_5d"]).copy()
    sub["mfe_first"] = (sub["time_to_mfe_5d"] < sub["time_to_mae_5d"]).astype(float)
    elig = sub[sub["entry_ok"]]
    rej = sub[~sub["entry_ok"]]
    if len(elig) < 100:
        return {"status": "INSUFFICIENT_DATA"}
    return {
        "status": "COMPLETED",
        "note": "daily bars cannot resolve intraday ordering; same-day hits count as adverse-first",
        "eligible_p_mfe_first": round(float(elig["mfe_first"].mean()), 4),
        "rejected_p_mfe_first": round(float(rej["mfe_first"].mean()), 4),
        "eligible_median_time_to_mfe": round(float(elig["time_to_mfe_5d"].median()), 3),
        "eligible_median_time_to_mae": round(float(elig["time_to_mae_5d"].median()), 3),
    }


def exp_calibration_reliability(df: pd.DataFrame) -> dict:
    """Q: is a score-mapped probability calibrated out-of-sample vs base rate?"""
    sub = df.dropna(subset=["finpilot_score", "fwd_5d_pct"]).copy()
    dates = sorted(sub["scan_date"].unique())
    split = dates[int(len(dates) * 0.7)]
    train, test = sub[sub["scan_date"] <= split], sub[sub["scan_date"] > split]
    if len(train) < 2000 or len(test) < 500:
        return {"status": "INSUFFICIENT_DATA"}
    results = {}
    for threshold, name in ((0.0, "positive"), (COST_PCT, "beats_cost")):
        train = train.copy()
        train["y"] = (train["fwd_5d_pct"] > threshold).astype(float)
        test_y = (test["fwd_5d_pct"] > threshold).astype(float)
        train["band"] = pd.qcut(train["finpilot_score"], 10, labels=False, duplicates="drop")
        band_prob = train.groupby("band")["y"].mean()
        edges = train.groupby("band")["finpilot_score"].max()
        test_band = np.searchsorted(
            edges.to_numpy(), test["finpilot_score"].to_numpy(), side="right"
        )
        test_band = np.clip(test_band, 0, len(band_prob) - 1)
        mapped = band_prob.to_numpy()[test_band]
        base = float(train["y"].mean())
        brier_model = float(np.mean((mapped - test_y.to_numpy()) ** 2))
        brier_base = float(np.mean((base - test_y.to_numpy()) ** 2))
        reliability = [
            {
                "band": int(b),
                "predicted": round(float(band_prob.loc[b]), 4),
                "observed": round(float(test_y.to_numpy()[test_band == b].mean()), 4)
                if (test_band == b).any()
                else None,
                "n": int((test_band == b).sum()),
            }
            for b in band_prob.index
        ]
        results[name] = {
            "brier_model": round(brier_model, 6),
            "brier_base_rate": round(brier_base, 6),
            "brier_skill_vs_base": round(1 - brier_model / brier_base, 6)
            if brier_base > 0
            else None,
            "reliability": reliability,
        }
    return {"status": "COMPLETED", "train_dates": f"{dates[0]}..{split}", "events": results}


def exp_correlation_cluster_selection(df: pd.DataFrame) -> dict:
    """Q: does one-candidate-per-correlation-cluster beat all-eligible?"""
    sub = df[df["entry_ok"]].dropna(subset=["fwd_5d_pct"])
    daily_all, daily_cluster = [], []
    for date, group in sub.groupby("scan_date"):
        rets = group["fwd_5d_pct"].to_numpy()
        if len(rets) < 2:
            continue
        daily_all.append(float(rets.mean() - COST_PCT))
        g = group.sort_values("finpilot_score", ascending=False)
        clusters: list[list[int]] = []
        series = list(g["past20_ret"])
        for i, s in enumerate(series):
            placed = False
            if isinstance(s, list):
                si = np.array(s, dtype=float)
                for cluster in clusters:
                    rep = np.array(series[cluster[0]], dtype=float)
                    if len(si) == 20 and len(rep) == 20:
                        corr = np.corrcoef(si, rep)[0, 1]
                        if np.isfinite(corr) and abs(corr) > 0.5:
                            cluster.append(i)
                            placed = True
                            break
            if not placed:
                clusters.append([i])
        chosen = [c[0] for c in clusters]  # highest score per cluster
        daily_cluster.append(float(g["fwd_5d_pct"].iloc[chosen].mean() - COST_PCT))
    if len(daily_all) < 20:
        return {"status": "INSUFFICIENT_DATA", "n_dates": len(daily_all)}
    diff = np.array(daily_cluster) - np.array(daily_all)
    return {
        "status": "COMPLETED",
        "n_dates": len(daily_all),
        "all_eligible_daily": dist_summary(pd.Series(daily_all)),
        "cluster_selected_daily": dist_summary(pd.Series(daily_cluster)),
        "cluster_minus_all": {
            **dist_summary(diff),
            "share_positive": round(float((diff > 0).mean()), 4),
        },
    }


def exp_sizing_comparison(df: pd.DataFrame) -> dict:
    """Q: equal vs ATR-parity vs score-weighted sizing of the eligible portfolio."""
    sub = df[df["entry_ok"]].dropna(subset=["fwd_5d_pct", "atr", "cache_close"]).copy()
    sub["atr_pct"] = (sub["atr"] / sub["cache_close"] * 100.0).clip(lower=0.1)
    daily = {"equal": [], "atr_parity": [], "score_weighted": []}
    for date, group in sub.groupby("scan_date"):
        r = group["fwd_5d_pct"].to_numpy() - COST_PCT
        if len(r) == 0:
            continue
        daily["equal"].append(float(r.mean()))
        w_atr = (1.0 / group["atr_pct"]).to_numpy()
        daily["atr_parity"].append(float(np.average(r, weights=w_atr)))
        w_score = group["finpilot_score"].clip(lower=1.0).fillna(1.0).to_numpy()
        daily["score_weighted"].append(float(np.average(r, weights=w_score)))
    out = {"status": "COMPLETED", "schemes": {}}
    for name, series in daily.items():
        arr = np.array(series)
        equity = np.cumprod(1 + arr / 100.0)
        peak = np.maximum.accumulate(equity)
        dd = (equity / peak - 1.0) * 100.0
        out["schemes"][name] = {
            **dist_summary(arr),
            "max_drawdown_pct": round(float(dd.min()), 4),
            "daily_sharpe": round(float(arr.mean() / arr.std()), 4) if arr.std() > 0 else None,
        }
    return out


def exp_tail_metrics(df: pd.DataFrame) -> dict:
    """Q: tail risk (CVaR5) of eligible vs rejected 5d outcomes."""
    sub = df.dropna(subset=["fwd_5d_pct"])
    out = {"status": "COMPLETED"}
    for name, group in (("eligible", sub[sub["entry_ok"]]), ("rejected", sub[~sub["entry_ok"]])):
        arr = np.sort(group["fwd_5d_pct"].to_numpy())
        k = max(1, int(len(arr) * 0.05))
        out[name] = {
            "cvar5_pct": round(float(arr[:k].mean()), 4),
            "p05_pct": round(float(arr[k - 1]), 4),
            "n": int(len(arr)),
        }
    return out


def exp_rvol_conditioning(df: pd.DataFrame) -> dict:
    """Q: does relative volume condition eligible outcomes?"""
    sub = df[df["entry_ok"]].dropna(subset=["rvol", "fwd_5d_pct"]).copy()
    if len(sub) < 200:
        return {"status": "INSUFFICIENT_DATA", "n": int(len(sub))}
    sub["rvol_t"] = pd.qcut(sub["rvol"], 3, labels=["low", "mid", "high"])
    return {
        "status": "COMPLETED",
        "cells": {
            str(k): dist_summary(g["fwd_5d_pct"]) for k, g in sub.groupby("rvol_t", observed=True)
        },
    }


def exp_gap_conditioning(df: pd.DataFrame) -> dict:
    """Q: gap taxonomy lite — outcomes by overnight gap bucket (no event labels)."""
    sub = df.dropna(subset=["gap_pct", "fwd_5d_pct"]).copy()
    bins = [-np.inf, -3, -1, 1, 3, np.inf]
    labels = ["gap_down_3+", "gap_down_1_3", "flat", "gap_up_1_3", "gap_up_3+"]
    sub["gap_bucket"] = pd.cut(sub["gap_pct"], bins=bins, labels=labels)
    out = {"status": "COMPLETED", "all_rows": {}, "eligible": {}}
    for name, frame in (("all_rows", sub), ("eligible", sub[sub["entry_ok"]])):
        out[name] = {
            str(k): dist_summary(g["fwd_5d_pct"])
            for k, g in frame.groupby("gap_bucket", observed=True)
        }
    return out


def exp_unsupervised_regimes(df: pd.DataFrame) -> dict:
    """Q: do data-driven regimes separate outcomes better than vol_regime?"""
    feats = ["atr_pct_real", "rvol", "gap_pct", "past_5d_pct"]
    sub = df.dropna(subset=feats + ["fwd_5d_pct"]).copy()
    if len(sub) < 2000:
        return {"status": "INSUFFICIENT_DATA", "n": int(len(sub))}
    X = sub[feats].to_numpy()
    X = (X - X.mean(0)) / (X.std(0) + 1e-9)
    labels = _kmeans(X, 4)
    sub["cluster"] = labels
    cells = {f"cluster_{c}": dist_summary(g["fwd_5d_pct"]) for c, g in sub.groupby("cluster")}
    medians = [v["median"] for v in cells.values() if v["median"] is not None]
    spread = round(float(max(medians) - min(medians)), 4) if medians else None
    return {
        "status": "COMPLETED",
        "n": int(len(sub)),
        "cells": cells,
        "median_spread_across_clusters": spread,
        "interpretation": "wider median spread = regimes separate outcomes; compare with G2 vol_regime cells",
    }


EXPERIMENTS = {
    "Q1_adverse_movement_target": exp_adverse_movement_target,
    "Q2_failure_prediction": exp_failure_prediction,
    "Q3_score_semantics": exp_score_semantics,
    "Q4_null_feature_injection": exp_null_feature_injection,
    "Q5_benchmark_relative": exp_benchmark_relative,
    "Q6_first_passage_survival": exp_first_passage,
    "F1_calibration_reliability": exp_calibration_reliability,
    "P1_correlation_cluster_selection": exp_correlation_cluster_selection,
    "P2_sizing_comparison": exp_sizing_comparison,
    "P3_tail_metrics": exp_tail_metrics,
    "M1_rvol_conditioning": exp_rvol_conditioning,
    "M2_gap_conditioning": exp_gap_conditioning,
    "A1_unsupervised_regimes": exp_unsupervised_regimes,
}

NEEDS_CACHE = {"Q5_benchmark_relative"}


def run_battery(
    csv_path: Path = DEFAULT_CSV,
    cache_dir: Path = DEFAULT_CACHE,
    audit_path: Path = DEFAULT_AUDIT,
    out_path: Path = DEFAULT_OUT,
) -> dict:
    started = datetime.now(UTC).isoformat()
    df = load_export(csv_path)
    flagged = load_flagged_symbols(audit_path)
    df.attrs["flagged"] = flagged
    enriched = compute_path_metrics(df, cache_dir)

    results = {}
    for name, fn in EXPERIMENTS.items():
        try:
            if name in NEEDS_CACHE:
                results[name] = fn(enriched, cache_dir)
            else:
                results[name] = fn(enriched)
        except Exception as exc:  # research battery: record, don't crash
            results[name] = {"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}

    artifact = {
        "study": "ten_perspectives_lab_2026-08-10",
        "started_utc": started,
        "finished_utc": datetime.now(UTC).isoformat(),
        "input_csv": str(csv_path),
        "rows_after_dedup": int(len(df)),
        "rows_with_cache_metrics": int(enriched["cache_close"].notna().sum()),
        "cost_assumption_pct": COST_PCT,
        "seed": SEED,
        "scope": "research-only diagnostic; no production, promotion, OOS, shadow or broker decision",
        "results": results,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return artifact


def main() -> None:
    artifact = run_battery()
    statuses = defaultdict(int)
    for name, res in artifact["results"].items():
        statuses[res.get("status", "ERROR")] += 1
        print(f"{name}: {res.get('status')}")
    print(f"\nTotal: {dict(statuses)}")
    print(f"Artifact: {DEFAULT_OUT}")


if __name__ == "__main__":
    main()
