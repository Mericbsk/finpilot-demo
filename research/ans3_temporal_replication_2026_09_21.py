"""ANS-3 — Temporal Replication of ANS-1. PRE-REGISTERED, READ-ONLY.

Date: 2026-09-21. Question: does ANS-1's result (attention elimination improves median
c2c_5d) REPLICATE across time, with the SAME procedure and UNCHANGED thresholds?

CONSTRAINT (honest): research EOD data spans 2026-05-06→07-31 (c2c_5d, 54 days). There is
NO truly-future data. So "temporal replication" here = split the SAME research set into
two NON-OVERLAPPING chronological halves and test whether the effect holds in BOTH
independently. This is a stability/replication check, NOT a true future-OOS test —
stated explicitly. (A true future-window replication needs new data after 2026-07-31.)

PRE-REGISTERED (fixed before running; thresholds UNCHANGED from ANS-1):
  Attention flag: |gap_pct|>=3% OR atr_pct_real>=6% (UNCHANGED). Target c2c_5d.
  Split: chronological 50/50 by unique scan_date (EARLY = first half, LATE = second half).
    Chosen by date order only, NOT by looking at results.
  Same metrics: median improvement (kept - removed), big-loser rate diff, hit diff.
  Same controls per half: matched-random (same count, 300 reps), null-shuffle (300),
    block-bootstrap (block=5, B=2000) 95% CI of median diff.
  Success (per half): median improvement > 0 AND CI excludes 0 AND beats null-shuffle (p<0.05).
  Replication verdict: SUPPORTED only if BOTH halves pass. If only one -> PARTIAL.
    If neither -> NOT REPLICATED. No threshold tuning. Negative result valid.
Output: reports/ans3_temporal_replication_2026-09-21.md + JSON.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

SEED = 20260918  # same seed family as ANS-1 for comparability
REPS = 300
BOOT_B = 2000
BLOCK = 5
DATA = "data/backtest_out/full_universe_enriched_eod_only.csv"
OUT_JSON = "data/backtest_out/ans3_temporal_replication_2026-09-21.json"


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA, low_memory=False)
    df["scan_date"] = pd.to_datetime(df["scan_date"])
    df = df.sort_values(["scan_date", "symbol"]).drop_duplicates(
        subset=["symbol", "scan_date"], keep="first"
    )
    df = df.dropna(subset=["composite_score", "c2c_1d"]).copy()
    df["abs_gap"] = df["gap_pct"].abs()
    df["attention"] = ((df["abs_gap"] >= 3) | (df["atr_pct_real"] >= 6)).astype(int)
    return df.dropna(subset=["c2c_5d"]).copy()


def median_diff(d):
    att = d[d["attention"] == 1]["c2c_5d"]
    nor = d[d["attention"] == 0]["c2c_5d"]
    if len(att) == 0 or len(nor) == 0:
        return None
    return float(nor.median() - att.median())


def matched_random(d):
    rng = np.random.default_rng(SEED)
    out = []
    dates = d["scan_date"].unique()
    for _ in range(REPS):
        kp = []
        for dt in dates:
            g = d[d["scan_date"] == dt]
            n_att = int(g["attention"].sum())
            if len(g) == 0:
                continue
            keep = rng.choice(len(g), size=max(1, len(g) - n_att), replace=False)
            kp.append(g["c2c_5d"].iloc[keep])
        out.append(float(pd.concat(kp).median()))
    return np.array(out)


def null_shuffle(d):
    rng = np.random.default_rng(SEED + 1)
    out = []
    for _ in range(REPS):
        dd = d.copy()
        dd["attention"] = dd.groupby("scan_date")["attention"].transform(
            lambda s: s.iloc[rng.permutation(len(s))].values
        )
        v = median_diff(dd)
        if v is not None:
            out.append(v)
    return np.array(out)


def block_bootstrap(d):
    rng = np.random.default_rng(SEED + 2)
    dates = np.array(sorted(d["scan_date"].unique()))
    n = len(dates)
    nb = int(np.ceil(n / BLOCK))
    out = []
    by = {t: g["c2c_5d"].values for t, g in d.groupby("scan_date")}
    at = {t: g["attention"].values for t, g in d.groupby("scan_date")}
    for _ in range(BOOT_B):
        starts = rng.integers(0, max(1, n - BLOCK + 1), size=nb)
        diffs = []
        for s in starts:
            blk = dates[s : s + BLOCK]
            rets = np.concatenate([by[t] for t in blk])
            aa = np.concatenate([at[t] for t in blk])
            a = rets[aa == 1]
            nn = rets[aa == 0]
            if len(a) and len(nn):
                diffs.append(np.median(nn) - np.median(a))
        if diffs:
            out.append(float(np.mean(diffs)))
    return np.array(out)


def eval_period(d, name):
    att = d[d["attention"] == 1]["c2c_5d"]
    nor = d[d["attention"] == 0]["c2c_5d"]
    md = median_diff(d)
    r = {
        "period": name,
        "n": len(d),
        "n_att": len(att),
        "att_rate": round(float(d["attention"].mean()), 3),
        "att_median": round(float(att.median()), 4),
        "nor_median": round(float(nor.median()), 4),
        "median_improvement_pp": round(md, 4) if md is not None else None,
        "att_bigloser": round(float((att < -10).mean()), 4),
        "nor_bigloser": round(float((nor < -10).mean()), 4),
    }
    if md is None or len(d) < 200:
        r["status"] = "insufficient"
        return r
    mr = matched_random(d)
    ns = null_shuffle(d)
    bb = block_bootstrap(d)
    lo, hi = np.percentile(bb, [2.5, 97.5])
    r["matched_random"] = {
        "kept_median_mean": round(float(mr.mean()), 4),
        "real_percentile": round(float((mr < nor.median()).mean()), 3),
    }
    r["null_shuffle"] = {"p_value": round(float((ns >= md).mean()), 4)}
    r["block_bootstrap"] = {
        "ci_95": [round(float(lo), 4), round(float(hi), 4)],
        "ci_excludes_zero": bool(lo > 0 or hi < 0),
    }
    r["pass"] = bool(md > 0 and (lo > 0 or hi < 0) and r["null_shuffle"]["p_value"] < 0.05)
    r["status"] = "ok"
    return r


def main() -> int:
    d = load()
    dates = np.array(sorted(d["scan_date"].unique()))
    mid = len(dates) // 2
    cut = dates[mid]
    early = d[d["scan_date"] < cut]
    late = d[d["scan_date"] >= cut]

    res = {
        "seed": SEED,
        "split": "chronological 50/50 by unique scan_date (date order, not results)",
        "cut_date": str(pd.Timestamp(cut).date()),
        "early_range": [str(early["scan_date"].min().date()), str(early["scan_date"].max().date())],
        "late_range": [str(late["scan_date"].min().date()), str(late["scan_date"].max().date())],
    }
    res["full"] = eval_period(d, "full")
    res["early"] = eval_period(early, "early")
    res["late"] = eval_period(late, "late")

    early_result, late_result = res["early"], res["late"]
    if early_result.get("status") != "ok" or late_result.get("status") != "ok":
        verdict = "INSUFFICIENT_DATA"
    elif early_result["pass"] and late_result["pass"]:
        verdict = "REPLICATED"
    elif early_result["pass"] or late_result["pass"]:
        verdict = "PARTIAL"
    else:
        verdict = "NOT_REPLICATED"
    res["verdict"] = verdict

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, default=str)
    print(json.dumps(res, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
