"""Scoring Ablation & Causal Validation — READ-ONLY, pre-registered.

Master Prompt v1.0 (2026-09-08). Level: A research-only. No production changes.

Question: do the four flag-gated components (squeeze, lottery, overnight, catalyst)
add predictive/ranking value over the baseline composite — or do they merely
perturb the score?

Dataset: data/backtest_out/full_universe_enriched_eod_only.csv (EOD-only labels,
the c2c_5d integrity fix). Chronological 70/30 split. Catalyst factor is 0.0
(cache empty) => reported as UNVALIDATED (data gap), not evaluated.

Pre-registration: split date, metrics, and decision rules fixed before results.

Usage: python -m research.scoring_ablation_runner_2026_09_08
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

CSV = Path("data/backtest_out/full_universe_enriched_eod_only.csv")
OUT_MD = Path("reports/scoring_ablation_audit_2026-09-08.md")
OUT_CSV = Path("reports/scoring_ablation_results_2026-09-08.csv")
OUT_LB = Path("reports/scoring_component_leaderboard_2026-09-08.csv")
SPLIT_Q = 0.70
RNG = np.random.default_rng(20260908)

W = {"squeeze": 1.5, "lottery": 2.0, "overnight": 1.0, "catalyst": 1.5}
VOLW = {0: 2.5, 1: 2.0, 2: 1.5}


def load() -> pd.DataFrame:
    df = pd.read_csv(CSV, low_memory=False)
    df = df.drop_duplicates(["symbol", "scan_date"], keep="first")
    df = df[(df["price"] >= 1) & df["c2c_5d"].notna() & (df["c2c_5d"].abs() <= 100)].copy()
    for c in [
        "squeeze_factor",
        "lottery_factor",
        "overnight_gap_factor",
        "score",
        "filter_score",
        "alignment_ratio",
        "momentum_ratio",
    ]:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def baseline_score(r: pd.Series) -> float:
    s = 0.0
    s += 2.0 if r.get("regime") else 0.0
    s += 2.0 if r.get("direction") else 0.0
    s += float(r.get("score", 0) or 0) * 0.5
    s += float(r.get("filter_score", 0) or 0) * 1.5
    s += float(r.get("alignment_ratio", 0) or 0) * 2.0
    vr = r.get("vol_regime")
    vr = int(vr) if vr is not None and not pd.isna(vr) else 1
    s += float(r.get("momentum_ratio", 0) or 0) * VOLW.get(vr, 2.0)
    s += 0.5 if r.get("volume_spike") else 0.0
    s += 0.5 if r.get("price_momentum") else 0.0
    s += 0.5 if r.get("trend_strength") else 0.0
    return s


def add_component(base: float, r: pd.Series, comp: str) -> float:
    if comp == "squeeze":
        return base + max(0.0, min(1.0, float(r.get("squeeze_factor", 0) or 0))) * W["squeeze"]
    if comp == "lottery":
        return base - max(0.0, min(1.0, float(r.get("lottery_factor", 0) or 0))) * W["lottery"]
    if comp == "overnight":
        return (
            base - max(0.0, min(1.0, float(r.get("overnight_gap_factor", 0) or 0))) * W["overnight"]
        )
    if comp == "catalyst":
        return base + max(-1.0, min(1.0, float(r.get("catalyst_factor", 0) or 0))) * W["catalyst"]
    return base


def eval_subset(df: pd.DataFrame, score_col: str) -> dict:
    """Top-N predictive metrics for a given score column."""
    out = {}
    d = df.dropna(subset=[score_col, "c2c_5d"])
    if len(d) < 50:
        return {"n": len(d), "error": "insufficient"}
    out["n"] = int(len(d))
    out["spearman"] = round(float(d[score_col].corr(d["c2c_5d"], method="spearman")), 4)
    for n in (10, 20, 50):
        top = d.nlargest(n, score_col)
        out[f"top{n}_mean_5d"] = round(float(top["c2c_5d"].mean()), 3)
        out[f"top{n}_hit"] = round(float((top["c2c_5d"] > 0).mean()), 3)
    return out


def regime_split(df: pd.DataFrame) -> dict:
    """Split by vol_regime (0=low,1=normal,2=high)."""
    out = {}
    for vr in (0, 1, 2):
        sub = df[df["vol_regime"] == vr]
        out[f"vol_regime_{vr}"] = sub
    return out


def main() -> None:
    df = load()
    dates = sorted(df["scan_date"].unique())
    cut = dates[int(len(dates) * SPLIT_Q)]
    dev = df[df["scan_date"] <= cut].copy()
    oos = df[df["scan_date"] > cut].copy()

    comps = ["squeeze", "lottery", "overnight", "catalyst"]
    models = ["baseline", *comps, "full"]

    results = {}
    for name, d in [("dev", dev), ("oos", oos)]:
        d = d.copy()
        d["score_baseline"] = d.apply(baseline_score, axis=1)
        for c in comps:
            d[f"score_{c}"] = d.apply(
                lambda r, c=c: add_component(r["score_baseline"], r, c), axis=1
            )
        d["score_full"] = d["score_baseline"]
        for c in comps:
            d["score_full"] = d.apply(lambda r, c=c: add_component(r["score_full"], r, c), axis=1)

        res = {"n": len(d), "models": {}}
        for m in models:
            res["models"][m] = eval_subset(d, f"score_{m}" if m != "baseline" else "score_baseline")
        results[name] = res

        # bucket analysis per component (dev only)
        if name == "dev":
            buckets = {}
            for c in comps:
                col = {
                    "squeeze": "squeeze_factor",
                    "lottery": "lottery_factor",
                    "overnight": "overnight_gap_factor",
                    "catalyst": "catalyst_factor",
                }[c]
                dd = d.dropna(subset=[col, "c2c_5d"])
                if dd[col].nunique() >= 5 and len(dd) >= 100:
                    dd = dd.assign(q=pd.qcut(dd[col], 5, labels=False, duplicates="drop"))
                    bk = dd.groupby("q")["c2c_5d"].agg(["mean", "median", "count"]).round(3)
                    buckets[c] = bk.to_dict("index")
                else:
                    buckets[c] = {"note": "insufficient variation"}
            results["dev_buckets"] = buckets

    # leaderboard rows
    lb_rows = []
    for m in models:
        dv = results["dev"]["models"].get(m, {})
        oo = results["oos"]["models"].get(m, {})
        lb_rows.append(
            {
                "model": m,
                "dev_n": dv.get("n"),
                "dev_spearman": dv.get("spearman"),
                "dev_top20_mean": dv.get("top20_mean_5d"),
                "dev_top20_hit": dv.get("top20_hit"),
                "oos_n": oo.get("n"),
                "oos_spearman": oo.get("spearman"),
                "oos_top20_mean": oo.get("top20_mean_5d"),
                "oos_top20_hit": oo.get("top20_hit"),
            }
        )
    lb = pd.DataFrame(lb_rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    lb.to_csv(OUT_LB, index=False)

    # detailed results csv
    detail = []
    for name in ("dev", "oos"):
        for m, v in results[name]["models"].items():
            detail.append({"split": name, "model": m, **v})
    pd.DataFrame(detail).to_csv(OUT_CSV, index=False)

    report = {
        "status": "exploratory",
        "production_change": False,
        "locked_oos": "not_opened",
        "dataset": str(CSV),
        "split_cut_date": cut,
        "dev_n": len(dev),
        "oos_n": len(oos),
        "catalyst_note": "catalyst_factor=0.0 for all rows (cache empty) — reported UNVALIDATED, not evaluated",
        "results": results,
        "leaderboard": lb_rows,
    }
    Path("data/backtest_out/scoring_ablation_2026-09-08.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    print(json.dumps({"leaderboard": lb_rows}, indent=2, default=str))
    print("\nDev buckets (quintile mean 5d return):")
    for c, b in results.get("dev_buckets", {}).items():
        print(f"  {c}: {b}")


if __name__ == "__main__":
    main()
