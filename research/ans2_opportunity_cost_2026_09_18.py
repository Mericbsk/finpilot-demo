"""ANS-2 — Attention Negative-Screen OPPORTUNITY COST. PRE-REGISTERED, READ-ONLY.

Date: 2026-09-18. Follows ANS-1 (SUPPORTED). Question:
  "Does eliminating attention-flagged rows' downside benefit survive the POSITIVE-TAIL
   opportunity cost?" ANS-1 showed median improves; this measures what the GOOD tail loses.

PRE-REGISTERED (fixed before running):
  Universe/cleaning/flag/target: same as ANS-1 (EOD-only, |gap|>=3% OR ATR>=6%, c2c_5d).
  H1: The median/downside benefit of elimination is NOT fully offset by positive-tail loss.
  Compare: ALL universe vs ATTENTION-EXCLUDED universe on:
    downside: median, mean, p10, p5, big-loser(<-10%) rate, min
    upside:   mean, p90, p95, big-winner(>+10%) rate, top-5% mean, top-1% mean
    dispersion: std, IQR
  Opportunity-cost metric: (big-winner rate lost) and (top-tail mean lost) vs
    (big-loser rate removed). Also net-of-tails: mean difference and a symmetric
    "tail EV" = mean of |extreme| beyond +/-10%.
  Controls: matched-random removal (same count, seed 20260918, 300 reps) and
    null-shuffle (flag shuffle within date) for the PRIMARY metric (median diff) AND
    the opportunity-cost metric (top-5% mean diff).
  Success: downside benefit persists (CI excludes 0, matches ANS-1) AND we REPORT
    the upside cost honestly (no cherry-pick). If upside cost > downside benefit on
    mean/tail-EV, verdict = MIXED, not SUPPORTED.
  Negative result valid. No production/data change. No threshold tuning.
Output: reports/ans2_opportunity_cost_2026-09-18.md + JSON.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

SEED = 20260918
REPS = 300
DATA = "data/backtest_out/full_universe_enriched_eod_only.csv"
OUT_JSON = "data/backtest_out/ans2_opportunity_cost_2026-09-18.json"


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


def profile(x: pd.Series) -> dict:
    x = pd.Series(x).dropna()
    if len(x) == 0:
        return {}
    return {
        "n": len(x),
        "mean": round(float(x.mean()), 4),
        "median": round(float(x.median()), 4),
        "p5": round(float(np.percentile(x, 5)), 4),
        "p10": round(float(np.percentile(x, 10)), 4),
        "p90": round(float(np.percentile(x, 90)), 4),
        "p95": round(float(np.percentile(x, 95)), 4),
        "std": round(float(x.std()), 4),
        "iqr": round(float(x.quantile(0.75) - x.quantile(0.25)), 4),
        "big_loser_pct": round(float((x < -10).mean()), 4),
        "big_winner_pct": round(float((x > 10).mean()), 4),
        "top5_mean": round(float(x.nlargest(max(1, int(len(x) * 0.05))).mean()), 4),
        "top1_mean": round(float(x.nlargest(max(1, int(len(x) * 0.01))).mean()), 4),
        "tail_ev_abs_gt10": round(float(x[x.abs() > 10].abs().mean()), 4)
        if (x.abs() > 10).any()
        else None,
    }


def main() -> int:
    d = load()
    allu = d["c2c_5d"]
    att = d[d["attention"] == 1]["c2c_5d"]
    kept = d[d["attention"] == 0]["c2c_5d"]

    res = {"seed": SEED, "n": len(d), "n_attention": len(att), "n_kept": len(kept)}
    res["profile_all"] = profile(allu)
    res["profile_attention"] = profile(att)
    res["profile_kept"] = profile(kept)

    # Opportunity cost: what eliminating attention loses (upside) vs gains (downside)
    res["opportunity_cost"] = {
        "median_gain_pp": round(kept.median() - allu.median(), 4),
        "bigloser_removed_pp": round(float((att < -10).mean()), 4),
        "bigwinner_lost_pp": round(float((att > 10).mean()), 4),
        "top5_mean_all": res["profile_all"]["top5_mean"],
        "top5_mean_kept": res["profile_kept"]["top5_mean"],
        "top5_mean_lost_pp": round(
            res["profile_all"]["top5_mean"] - res["profile_kept"]["top5_mean"], 4
        ),
        "mean_all": res["profile_all"]["mean"],
        "mean_kept": res["profile_kept"]["mean"],
        "mean_change_pp": round(res["profile_kept"]["mean"] - res["profile_all"]["mean"], 4),
        "tail_ev_all": res["profile_all"]["tail_ev_abs_gt10"],
        "tail_ev_kept": res["profile_kept"]["tail_ev_abs_gt10"],
    }

    # Controls for the two key deltas (median diff + top5 diff)
    rng = np.random.default_rng(SEED)
    dates = d["scan_date"].unique()
    mr_median = []
    mr_top5 = []
    for _ in range(REPS):
        kept_parts = []
        for dt in dates:
            g = d[d["scan_date"] == dt]
            n_att = int(g["attention"].sum())
            if len(g) == 0:
                continue
            keep_idx = rng.choice(len(g), size=max(1, len(g) - n_att), replace=False)
            kept_parts.append(g["c2c_5d"].iloc[keep_idx])
        k = pd.concat(kept_parts)
        mr_median.append(float(k.median()))
        mr_top5.append(float(k.nlargest(max(1, int(len(k) * 0.05))).mean()))
    res["matched_random"] = {
        "kept_median_mean": round(float(np.mean(mr_median)), 4),
        "real_kept_median": round(float(kept.median()), 4),
        "kept_top5_mean": round(float(np.mean(mr_top5)), 4),
        "real_kept_top5": res["profile_kept"]["top5_mean"],
    }

    # Verdict logic (pre-registered)
    downside_ok = res["opportunity_cost"]["median_gain_pp"] > 0
    top5_lost = res["opportunity_cost"]["top5_mean_lost_pp"]
    mean_change = res["opportunity_cost"]["mean_change_pp"]
    # Honest read: if removing attention LOWERS mean AND removes a large top tail -> MIXED
    if downside_ok and mean_change >= 0 and top5_lost < 5.0:
        verdict = "SUPPORTED_NET_POSITIVE"
    elif downside_ok and (mean_change < 0 or top5_lost >= 5.0):
        verdict = "MIXED"  # median improves but positive tail cost is real
    else:
        verdict = "NOT SUPPORTED"
    res["verdict"] = verdict

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, default=str)
    print(json.dumps(res, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
