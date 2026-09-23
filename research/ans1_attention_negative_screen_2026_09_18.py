"""ANS-1 — Attention-as-Negative-Screen. PRE-REGISTERED, READ-ONLY.

Date: 2026-09-18. Hypothesis source: EXTERNAL literature (Barber et al. 2022 JF
Robinhood; Bali et al. 2011 JFE MAX/lottery) — NOT derived from our data, so this
is a confirmatory test, not a mined discovery. Internal cross-check
(direction_evidence_crosscheck_2026_09_18.md) confirmed the sign is present
descriptively; this test applies OOS discipline.

PRE-REGISTERED (fixed before running):
  Universe: data/backtest_out/full_universe_enriched_eod_only.csv; cleaning = existing
    (sort scan_date/symbol, drop dup keep first, drop null composite_score, drop null c2c_5d).
  Attention flag: |gap_pct|>=3% OR atr_pct_real>=6%  (Big Gap OR Volatility Spike).
  Target: c2c_5d (5-day close-to-close). Primary horizon = 5d.
  H1: Removing attention-flagged rows IMPROVES median c2c_5d of the remaining universe.
  Primary metric: median(kept) - median(removed) in percentage points.
  Secondary: big-loser (<-10%) rate difference; hit-rate difference.
  Controls (both required):
    (a) matched-random: remove SAME COUNT of random rows per scan_date; seed=20260918, 300 reps.
    (b) null-shuffle: shuffle attention flag within scan_date; 300 reps.
  Uncertainty: block-bootstrap over scan_date (block=5 consecutive days), B=2000,
    95% CI of the median difference.
  Success threshold: median improvement > 0 AND 95% CI excludes 0 AND beats
    matched-random AND beats null-shuffle.
  Kill criterion: if ANY of those fails -> NOT SUPPORTED. No post-hoc threshold
    loosening. No subgroup mining. No threshold tuning.
  Negative result is valid. Read-only. No production/data change.
Output: reports/ans1_attention_negative_screen_2026-09-18.md + JSON artifact.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

SEED = 20260918
REPS = 300
BOOT_B = 2000
BLOCK = 5
DATA = "data/backtest_out/full_universe_enriched_eod_only.csv"
OUT_JSON = "data/backtest_out/ans1_attention_negative_screen_2026-09-18.json"


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA, low_memory=False)
    df["scan_date"] = pd.to_datetime(df["scan_date"])
    df = df.sort_values(["scan_date", "symbol"]).drop_duplicates(
        subset=["symbol", "scan_date"], keep="first"
    )
    df = df.dropna(subset=["composite_score", "c2c_1d"]).copy()
    df["abs_gap"] = df["gap_pct"].abs()
    df["attention"] = ((df["abs_gap"] >= 3) | (df["atr_pct_real"] >= 6)).astype(int)
    return df


def median_diff(d: pd.DataFrame) -> float:
    att = d[d["attention"] == 1]["c2c_5d"]
    nor = d[d["attention"] == 0]["c2c_5d"]
    return float(nor.median() - att.median())


def matched_random(d: pd.DataFrame) -> np.ndarray:
    """Remove the same COUNT of random rows per scan_date; measure median of rest."""
    rng = np.random.default_rng(SEED)
    out = []
    dates = d["scan_date"].unique()
    for _ in range(REPS):
        kept_parts = []
        for dt in dates:
            g = d[d["scan_date"] == dt]
            n_att = int(g["attention"].sum())
            if len(g) == 0 or n_att == 0:
                kept_parts.append(g["c2c_5d"])
                continue
            keep_idx = rng.choice(len(g), size=max(1, len(g) - n_att), replace=False)
            kept_parts.append(g["c2c_5d"].iloc[keep_idx])
        kept = pd.concat(kept_parts)
        out.append(float(kept.median()))
    return np.array(out)


def null_shuffle(d: pd.DataFrame) -> np.ndarray:
    """Shuffle attention flag within each scan_date; measure median diff."""
    rng = np.random.default_rng(SEED + 1)
    out = []
    for _ in range(REPS):
        dd = d.copy()
        dd["attention"] = dd.groupby("scan_date")["attention"].transform(
            lambda s: s.iloc[rng.permutation(len(s))].values
        )
        out.append(median_diff(dd))
    return np.array(out)


def block_bootstrap(d: pd.DataFrame) -> np.ndarray:
    """Block-bootstrap over consecutive scan_dates (block=5), resample, median diff."""
    rng = np.random.default_rng(SEED + 2)
    dates = np.array(sorted(d["scan_date"].unique()))
    n = len(dates)
    nblocks = int(np.ceil(n / BLOCK))
    out = []
    by_date = {dt: g["c2c_5d"].values for dt, g in d.groupby("scan_date")}
    att_by_date = {dt: g["attention"].values for dt, g in d.groupby("scan_date")}
    for _ in range(BOOT_B):
        starts = rng.integers(0, n - BLOCK + 1, size=nblocks)
        diffs = []
        for s in starts:
            blk = dates[s : s + BLOCK]
            rets = np.concatenate([by_date[t] for t in blk])
            att = np.concatenate([att_by_date[t] for t in blk])
            a = rets[att == 1]
            nn = rets[att == 0]
            if len(a) and len(nn):
                diffs.append(np.median(nn) - np.median(a))
        if diffs:
            out.append(float(np.mean(diffs)))
    return np.array(out)


def main() -> int:
    df = load()
    d = df.dropna(subset=["c2c_5d"]).copy()

    att = d[d["attention"] == 1]["c2c_5d"]
    nor = d[d["attention"] == 0]["c2c_5d"]
    res = {
        "seed": SEED,
        "reps": REPS,
        "boot_B": BOOT_B,
        "block": BLOCK,
        "n": len(d),
        "n_attention": int((d["attention"] == 1).sum()),
        "attention_rate": round(float(d["attention"].mean()), 3),
        "attention_median": round(float(att.median()), 4),
        "normal_median": round(float(nor.median()), 4),
        "median_improvement_pp": round(float(nor.median() - att.median()), 4),
        "attention_bigloser_rate": round(float((att < -10).mean()), 4),
        "normal_bigloser_rate": round(float((nor < -10).mean()), 4),
        "bigloser_reduction_pp": round(float((att < -10).mean() - (nor < -10).mean()), 4),
        "attention_hit": round(float((att > 0).mean()), 3),
        "normal_hit": round(float((nor > 0).mean()), 3),
    }

    # (a) matched-random: median of randomly-kept (same count removed)
    mr = matched_random(d)
    res["matched_random"] = {
        "kept_median_mean": round(float(mr.mean()), 4),
        "kept_median_std": round(float(mr.std()), 4),
        "real_kept_median": round(float(nor.median()), 4),
        "real_percentile_vs_matched": round(float((mr < nor.median()).mean()), 3),
    }

    # (b) null-shuffle of attention flag
    ns = null_shuffle(d)
    res["null_shuffle"] = {
        "diff_mean": round(float(ns.mean()), 4),
        "diff_std": round(float(ns.std()), 4),
        "real_diff": res["median_improvement_pp"],
        "real_percentile_vs_null": round(float((ns < res["median_improvement_pp"]).mean()), 3),
        "p_value": round(float((ns >= res["median_improvement_pp"]).mean()), 4),
    }

    # (c) block-bootstrap CI of median difference
    bb = block_bootstrap(d)
    lo, hi = np.percentile(bb, [2.5, 97.5])
    res["block_bootstrap"] = {
        "median_diff_mean": round(float(bb.mean()), 4),
        "ci_95": [round(float(lo), 4), round(float(hi), 4)],
        "ci_excludes_zero": bool(lo > 0 or hi < 0),
    }

    # verdict
    ok = (
        res["median_improvement_pp"] > 0
        and res["block_bootstrap"]["ci_excludes_zero"]
        and res["matched_random"]["real_percentile_vs_matched"] > 0.5
        and res["null_shuffle"]["p_value"] < 0.05
    )
    res["verdict"] = "SUPPORTED" if ok else "NOT SUPPORTED"

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, default=str)
    print(json.dumps(res, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
