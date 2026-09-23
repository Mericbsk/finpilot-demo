"""Walk-Forward + Matched-Control + Rank-Displacement scoring validation.

Master Prompt v1.0 (2026-09-08). READ-ONLY. NO weight optimization.
Continuation of meta-validation + scoring ablation.

Dataset: data/backtest_out/full_universe_enriched_eod_only.csv (EOD-only).
Target: c2c_1d (1D forward return). No random split — chronological only.

PRE-REGISTERED walk-forward windows (fixed before results):
  The dataset spans 2025-09-11 -> 2026-08-05 (82 distinct scan dates).
  Dense period: 2026-04 onward (median 191 rows/date). We use 4 sequential
  windows over the dense period; each window = first 70% of its dates as
  development, last 30% as OOS. Window date boundaries are computed from the
  date array at fixed quantiles — chosen before any model is evaluated.

  W1: 2026-04-01 -> 2026-05-01
  W2: 2026-04-22 -> 2026-05-22
  W3: 2026-05-13 -> 2026-06-12
  W4: 2026-06-03 -> 2026-07-03
  (boundaries approximate; exact cut computed as 70th percentile of dates in window)

Models: baseline / +squeeze / +lottery / +overnight / +catalyst / full.
Catalyst factor = 0.0 everywhere (cache empty) => reported UNVALIDATED (data gap).

Usage: python -m research.walk_forward_scoring_validation_2026_09_08
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

CSV = Path("data/backtest_out/full_universe_enriched_eod_only.csv")
OUTDIR = Path("data/backtest_out")
REPORT = Path("reports/walk_forward_scoring_validation_2026-09-08.md")
RES_CSV = Path("reports/walk_forward_scoring_results_2026-09-08.csv")
DISP_CSV = Path("reports/rank_displacement_results_2026-09-08.csv")
MC_CSV = Path("reports/matched_control_results_2026-09-08.csv")
LB_CSV = Path("reports/component_validation_leaderboard_2026-09-08.csv")

RNG = np.random.default_rng(20260908)
W = {"squeeze": 1.5, "lottery": 2.0, "overnight": 1.0, "catalyst": 1.5}
VOLW = {0: 2.5, 1: 2.0, 2: 1.5}
COMPS = ["squeeze", "lottery", "overnight", "catalyst"]
MODELS = ["baseline", *COMPS, "full"]
TOPNS = (10, 20, 50)
DISPLACEMENT_BINS = [(-np.inf, -20), (-20, -5), (-5, 5), (5, 20), (20, np.inf)]
DISPLACEMENT_LABELS = ["strong_down", "mod_down", "neutral", "mod_up", "strong_up"]


def load() -> pd.DataFrame:
    df = pd.read_csv(CSV, low_memory=False)
    df = df.drop_duplicates(["symbol", "scan_date"], keep="first")
    df = df[(df["price"] >= 1) & df["c2c_1d"].notna() & (df["c2c_1d"].abs() <= 50)].copy()
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


def base_score(r: pd.Series) -> float:
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


def add_comp(base: float, r: pd.Series, c: str) -> float:
    if c == "squeeze":
        return base + max(0.0, min(1.0, float(r.get("squeeze_factor", 0) or 0))) * W[c]
    if c == "lottery":
        return base - max(0.0, min(1.0, float(r.get("lottery_factor", 0) or 0))) * W[c]
    if c == "overnight":
        return base - max(0.0, min(1.0, float(r.get("overnight_gap_factor", 0) or 0))) * W[c]
    if c == "catalyst":
        return base + max(-1.0, min(1.0, float(r.get("catalyst_factor", 0) or 0))) * W[c]
    return base


def build_scores(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["score_baseline"] = d.apply(base_score, axis=1)
    for c in COMPS:
        d[f"score_{c}"] = d.apply(lambda r, c=c: add_comp(r["score_baseline"], r, c), axis=1)
    d["score_full"] = d["score_baseline"]
    for c in COMPS:
        d["score_full"] = d.apply(lambda r, c=c: add_comp(r["score_full"], r, c), axis=1)
    return d


def eval_model(d: pd.DataFrame, col: str) -> dict:
    dd = d.dropna(subset=[col, "c2c_1d"])
    if len(dd) < 30:
        return {"n": len(dd), "error": "insufficient"}
    out = {
        "n": int(len(dd)),
        "spearman": round(float(dd[col].corr(dd["c2c_1d"], method="spearman")), 4),
    }
    for n in TOPNS:
        top = dd.nlargest(min(n, len(dd)), col)
        out[f"top{n}_mean"] = round(float(top["c2c_1d"].mean()), 3)
        out[f"top{n}_hit"] = round(float((top["c2c_1d"] > 0).mean()), 3)
    return out


def displacement_analysis(d: pd.DataFrame, comp: str) -> pd.DataFrame:
    """Rank displacement: baseline rank vs component rank, bucketed by delta."""
    dd = d.dropna(subset=["score_baseline", f"score_{comp}", "c2c_1d"]).copy()
    if len(dd) < 50:
        return pd.DataFrame()
    dd["rank_base"] = dd["score_baseline"].rank(ascending=False)
    dd["rank_comp"] = dd[f"score_{comp}"].rank(ascending=False)
    dd["rank_delta"] = dd["rank_base"] - dd["rank_comp"]  # + = moved UP (better rank)
    dd["bucket"] = pd.cut(
        dd["rank_delta"],
        bins=[b[0] for b in DISPLACEMENT_BINS] + [np.inf],
        labels=DISPLACEMENT_LABELS,
        right=False,
    )
    g = dd.groupby("bucket", observed=True)["c2c_1d"].agg(["count", "mean", "median"]).round(3)
    g["hit"] = dd.groupby("bucket", observed=True)["c2c_1d"].apply(
        lambda x: round(float((x > 0).mean()), 3)
    )
    g = g.reset_index()
    g["component"] = comp
    return g


def matched_control(d: pd.DataFrame, comp: str, n_runs: int = 50) -> dict:
    """Treated = strong displaced (|rank_delta|>=20); control = same-day similar baseline rank."""
    dd = d.dropna(subset=["score_baseline", f"score_{comp}", "c2c_1d"]).copy()
    if len(dd) < 100:
        return {"error": "insufficient", "n": len(dd)}
    dd["rank_base"] = dd["score_baseline"].rank(ascending=False)
    dd["rank_comp"] = dd[f"score_{comp}"].rank(ascending=False)
    dd["rank_delta"] = dd["rank_base"] - dd["rank_comp"]
    treated = dd[dd["rank_delta"].abs() >= 20]
    if len(treated) < 20:
        return {"error": "few treated", "n": len(treated)}
    diffs = []
    for date in treated["scan_date"].unique():
        t = treated[treated["scan_date"] == date]
        pool = dd[(dd["scan_date"] == date) & (dd["rank_delta"].abs() < 5)]
        if len(pool) < len(t) or len(t) == 0:
            continue
        for _ in range(n_runs):
            ctrl = pool.sample(n=min(len(t), len(pool)), replace=False, random_state=RNG)
            diffs.append(float(t["c2c_1d"].mean() - ctrl["c2c_1d"].mean()))
    if not diffs:
        return {"error": "no matched dates"}
    arr = np.array(diffs)
    return {
        "treated_n": int(len(treated)),
        "median_diff": round(float(np.median(arr)), 4),
        "share_positive": round(float((arr > 0).mean()), 3),
        "comparisons": len(diffs),
    }


def random_control(d: pd.DataFrame, comp: str, n_runs: int = 100) -> dict:
    dd = d.dropna(subset=[f"score_{comp}", "c2c_1d"])
    if len(dd) < 50:
        return {"error": "insufficient"}
    top = dd.nlargest(min(20, len(dd)), f"score_{comp}")
    diffs = []
    for date in top["scan_date"].unique():
        pool = dd[dd["scan_date"] == date]
        t = top[top["scan_date"] == date]
        if len(pool) <= len(t):
            continue
        for _ in range(n_runs):
            r = pool.sample(n=len(t), replace=False, random_state=RNG)
            diffs.append(float(t["c2c_1d"].mean() - r["c2c_1d"].mean()))
    if not diffs:
        return {"error": "no dates"}
    arr = np.array(diffs)
    return {
        "median_diff": round(float(np.median(arr)), 4),
        "share_positive": round(float((arr > 0).mean()), 3),
        "comparisons": len(diffs),
    }


def main() -> None:
    df = load()
    # Pre-registered windows over dense period (2026-04 onward)
    dense = sorted(d for d in df["scan_date"].unique() if str(d) >= "2026-04-01")
    windows = []
    wdefs = [
        ("W1", "2026-04-01", "2026-05-01"),
        ("W2", "2026-04-22", "2026-05-22"),
        ("W3", "2026-05-13", "2026-06-12"),
        ("W4", "2026-06-03", "2026-07-03"),
    ]
    for name, lo, hi in wdefs:
        wdates = sorted(d for d in dense if lo <= str(d) <= hi)
        if len(wdates) < 4:
            continue
        cut = wdates[int(len(wdates) * 0.7)]
        windows.append((name, lo, hi, cut))

    all_results = {
        "windows": {},
        "windows_defined": [
            {"name": n, "range": f"{lo}..{hi}", "cut": c} for n, lo, hi, c in windows
        ],
    }

    disp_all = []
    mc_all = []
    for name, lo, hi, cut in windows:
        wd = df[(df["scan_date"] >= lo) & (df["scan_date"] <= hi)].copy()
        wd = build_scores(wd)
        dev = wd[wd["scan_date"] <= cut]
        oos = wd[wd["scan_date"] > cut]
        wres = {"dev_n": len(dev), "oos_n": len(oos), "cut": cut, "models": {}}
        for m in MODELS:
            col = "score_baseline" if m == "baseline" else f"score_{m}"
            wres["models"][m] = {"dev": eval_model(dev, col), "oos": eval_model(oos, col)}
        all_results["windows"][name] = wres
        # displacement + matched/random control on OOS
        for c in COMPS:
            da = displacement_analysis(oos, c)
            if len(da):
                da["window"] = name
                disp_all.append(da)
            mc = matched_control(oos, c)
            mc.update({"component": c, "window": name})
            mc_all.append(mc)

    # random control per model on each OOS window
    rand_all = []
    for name, lo, hi, cut in windows:
        wd = df[(df["scan_date"] >= lo) & (df["scan_date"] <= hi)].copy()
        wd = build_scores(wd)
        oos = wd[wd["scan_date"] > cut]
        for m in MODELS:
            rc = random_control(oos, m)
            rc.update({"model": m, "window": name})
            rand_all.append(rc)

    all_results["random_control"] = rand_all
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "walk_forward_scoring_2026-09-08.json").write_text(
        json.dumps(all_results, indent=2, default=str), encoding="utf-8"
    )

    # CSVs
    rows = []
    for wname, wres in all_results["windows"].items():
        for m, v in wres["models"].items():
            for split in ("dev", "oos"):
                rows.append({"window": wname, "model": m, "split": split, **v[split]})
    pd.DataFrame(rows).to_csv(RES_CSV, index=False)
    if disp_all:
        pd.concat(disp_all).to_csv(DISP_CSV, index=False)
    pd.DataFrame(mc_all).to_csv(MC_CSV, index=False)

    # leaderboard: per component, OOS win/same/worse vs baseline across windows
    lb_rows = []
    for c in COMPS + ["full"]:
        better = same = worse = 0
        deltas = []
        for _wname, wres in all_results["windows"].items():
            b = wres["models"]["baseline"]["oos"].get("top20_mean")
            t = wres["models"][c]["oos"].get("top20_mean")
            if b is None or t is None:
                continue
            d = t - b
            deltas.append(d)
            if d > 0.2:
                better += 1
            elif d < -0.2:
                worse += 1
            else:
                same += 1
        lb_rows.append(
            {
                "model": c,
                "oos_better": better,
                "oos_same": same,
                "oos_worse": worse,
                "mean_delta": round(float(np.mean(deltas)), 3) if deltas else None,
                "median_delta": round(float(np.median(deltas)), 3) if deltas else None,
            }
        )
    pd.DataFrame(lb_rows).to_csv(LB_CSV, index=False)

    print(
        json.dumps(
            {"windows": len(all_results["windows"]), "leaderboard": lb_rows}, indent=2, default=str
        )
    )
    print("\nRandom control (OOS top-20 vs random):")
    for r in rand_all[:6]:
        print(" ", r)


if __name__ == "__main__":
    main()
