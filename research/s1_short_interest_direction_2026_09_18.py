"""S1 — Short-Interest Change (ΔSI) direction test. PRE-REGISTERED, READ-ONLY.

Date: 2026-09-18. Candidate S1 from direction_signal_source_scouting_2026_09_18.md.

PRE-REGISTRATION (fixed before results):
  Universe: data/backtest_out/full_universe_enriched_eod_only.csv (EOD-only; existing
    cleaning: sort by scan_date/symbol, drop dup symbol/date keep first, drop null
    composite_score). Target: c2c_1d (1-day close-to-close, EOD).
  Signal: ΔSI = most recent bi-weekly short-interest change known AT OR BEFORE scan_date
    (as-of join, NO lookahead). Normalized two ways: (a) raw ΔSI shares, (b) ΔSI / prior SI
    (pct change). Both pre-registered; primary = pct change.
  Hypotheses (two-sided):
    H0: ΔSI carries no directional info on c2c_1d (Spearman ≈ 0, buckets flat).
    H1a (classic): SI increase → DOWN (negative relation).
    H1b (squeeze): EXTREME high SI + SI increase → UP (short squeeze).
  Primary metric: Spearman(ΔSI_pct, c2c_1d). Secondary: quintile mean/median/hit; monotonicity.
  Squeeze leg: top-decile SI level AND positive ΔSI → c2c_1d (vs rest).
  Random control: within-scan_date random selection, seed=20260918, 300 reps.
  Walk-forward: 3 pre-registered windows reused (W2 04-22→05-22, W3 05-13→06-12, W4 06-03→07-03).
    NOTE: research EOD data spans 2026-05-06→08-05; FINRA ends 2026-06-15 → only early
    windows have fresh SI; later windows use last-known SI (stale-data caveat reported).
  Multiple-testing: 5 candidates planned; this is 1/5 → note Bonferroni (alpha 0.05/5=0.01).
  Negative result = valid. No imputation. Missing SI → row excluded, counted.
Output: reports/s1_short_interest_direction_2026-09-18.md + data artifact JSON.
"""

from __future__ import annotations

import glob
import json
import os

import numpy as np
import pandas as pd

SEED = 20260918
REPS = 300
DATA = "data/backtest_out/full_universe_enriched_eod_only.csv"
FINRA = "data/finra_cache"
OUT_MD = "reports/s1_short_interest_direction_2026_09_18.md"
OUT_JSON = "data/backtest_out/s1_short_interest_direction_2026-09-18.json"
WINDOWS = {
    "W2": ("2026-04-22", "2026-05-22"),
    "W3": ("2026-05-13", "2026-06-12"),
    "W4": ("2026-06-03", "2026-07-03"),
}


def load_finra() -> dict[str, pd.DataFrame]:
    """symbol -> DataFrame[date, si] sorted by date."""
    out = {}
    for f in glob.glob(os.path.join(FINRA, "*.json")):
        sym = os.path.basename(f)[:-5]
        try:
            rows = json.load(open(f, encoding="utf-8"))
            if not rows:
                continue
            df = pd.DataFrame(rows, columns=["date", "si"])
            df["date"] = pd.to_datetime(df["date"])
            df = df.dropna().sort_values("date").reset_index(drop=True)
            if len(df) >= 2:
                out[sym] = df
        except Exception:
            continue
    return out


def build_dsi(finra: dict) -> pd.DataFrame:
    """Per-symbol as-of ΔSI series: for each consecutive pair, ΔSI known at later date."""
    recs = []
    for sym, df in finra.items():
        df = df.copy()
        df["si_prev"] = df["si"].shift(1)
        df["dsi"] = df["si"] - df["si_prev"]
        df["dsi_pct"] = np.where(df["si_prev"] > 0, df["dsi"] / df["si_prev"], np.nan)
        df["si_level"] = df["si"]
        dd = df.dropna(subset=["dsi_pct"])
        for _, r in dd.iterrows():
            recs.append(
                {
                    "symbol": sym,
                    "si_date": r["date"],
                    "dsi_pct": r["dsi_pct"],
                    "si_level": r["si_level"],
                }
            )
    return pd.DataFrame(recs)


def spearman(a, b):
    a, b = pd.Series(a), pd.Series(b)
    m = a.notna() & b.notna()
    return a[m].rank().corr(b[m].rank()) if m.sum() >= 30 else np.nan


def quintiles(d, col, target):
    x = pd.to_numeric(d[col], errors="coerce")
    y = d[target]
    m = x.notna() & y.notna()
    x, y = x[m], y[m]
    if len(x) < 100 or x.nunique() < 5:
        return None
    try:
        q = pd.qcut(x, 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"], duplicates="drop")
    except ValueError:
        return None
    g = pd.DataFrame({"q": q, "y": y}).groupby("q", observed=True)["y"]
    return {
        "n": g.size().tolist(),
        "mean": [round(v, 4) for v in g.mean()],
        "median": [round(v, 4) for v in g.median()],
        "hit": [round((s > 0).mean(), 3) for _, s in g],
    }


def main() -> int:
    eod = pd.read_csv(DATA, low_memory=False)
    eod["scan_date"] = pd.to_datetime(eod["scan_date"])
    eod = eod.sort_values(["scan_date", "symbol"]).drop_duplicates(
        subset=["symbol", "scan_date"], keep="first"
    )
    d = eod.dropna(subset=["composite_score", "c2c_1d"]).copy()

    finra = load_finra()
    dsi = build_dsi(finra)

    # As-of join: for each (symbol, scan_date), latest si_date <= scan_date
    dsi = dsi.sort_values("si_date")
    d = d.sort_values("scan_date")
    merged = pd.merge_asof(
        d.sort_values("scan_date"),
        dsi.sort_values("si_date"),
        left_on="scan_date",
        right_on="si_date",
        by="symbol",
        direction="backward",
    )
    merged["si_lag_days"] = (merged["scan_date"] - merged["si_date"]).dt.days
    n_total = len(merged)
    merged = merged.dropna(subset=["dsi_pct"]).copy()

    res = {
        "seed": SEED,
        "reps": REPS,
        "n_total_rows": n_total,
        "n_with_dsi": len(merged),
        "coverage_pct": round(len(merged) / n_total, 3),
        "symbols_with_si": int(merged["symbol"].nunique()),
        "si_lag_days_median": float(merged["si_lag_days"].median()),
    }

    # primary
    res["spearman_dsi_pct_c2c1d"] = float(spearman(merged["dsi_pct"], merged["c2c_1d"]))
    res["spearman_dsi_raw_c2c1d"] = float(
        spearman(merged["dsi_pct"] * merged["si_level"], merged["c2c_1d"])
    )
    res["pearson_dsi_pct_c2c1d"] = float(merged["dsi_pct"].corr(merged["c2c_1d"]))
    res["quintiles_dsi_pct"] = quintiles(merged, "dsi_pct", "c2c_1d")

    # squeeze leg: top-decile SI level AND positive ΔSI
    lvl_thresh = merged["si_level"].quantile(0.9)
    sq = merged[(merged["si_level"] >= lvl_thresh) & (merged["dsi_pct"] > 0)]
    rest = merged[~((merged["si_level"] >= lvl_thresh) & (merged["dsi_pct"] > 0))]
    res["squeeze_leg"] = {
        "n": len(sq),
        "mean_c2c1d": round(float(sq["c2c_1d"].mean()), 4) if len(sq) else None,
        "hit": round(float((sq["c2c_1d"] > 0).mean()), 3) if len(sq) else None,
        "rest_mean": round(float(rest["c2c_1d"].mean()), 4),
        "rest_n": len(rest),
    }

    # random control: top-ΔSI-quintile mean vs within-date random
    rng = np.random.default_rng(SEED)
    high = merged[merged["dsi_pct"] >= merged["dsi_pct"].quantile(0.8)]
    real_high = high["c2c_1d"].mean()
    dates = merged["scan_date"].unique()
    rnd = []
    for _ in range(REPS):
        rs = []
        for dt in dates:
            g = merged[merged["scan_date"] == dt]
            if len(g) == 0:
                continue
            k = max(1, int(len(g) * 0.2))
            rs.append(g["c2c_1d"].iloc[rng.choice(len(g), size=k, replace=False)].mean())
        rnd.append(np.nanmean(rs))
    rnd = np.array(rnd)
    res["random_control_top_dsi_quintile"] = {
        "real_mean": round(float(real_high), 4),
        "random_mean": round(float(rnd.mean()), 4),
        "random_std": round(float(rnd.std()), 4),
        "percentile": round(float((rnd < real_high).mean()), 3),
        "delta": round(float(real_high - rnd.mean()), 4),
    }

    # walk-forward
    wf = []
    for wname, (a, b) in WINDOWS.items():
        w = merged[(merged["scan_date"] >= a) & (merged["scan_date"] <= b)]
        if len(w) < 100:
            wf.append({"window": wname, "status": "insufficient", "n": len(w)})
            continue
        cut = w["scan_date"].quantile(0.7)
        oos = w[w["scan_date"] > cut]
        wf.append(
            {
                "window": wname,
                "n": len(w),
                "oos_n": len(oos),
                "spearman": (
                    float(spearman(oos["dsi_pct"], oos["c2c_1d"])) if len(oos) >= 30 else None
                ),
                "si_lag_median": float(oos["si_lag_days"].median()) if len(oos) else None,
                "status": "ok",
            }
        )
    res["walk_forward"] = wf

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, default=str)
    print(json.dumps(res, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
