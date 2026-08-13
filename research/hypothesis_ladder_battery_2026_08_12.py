"""Research-only artifact-ladder completion for YH-1/YH-2/YH-3 discovery signals.

These are NOT confirmatory runs: they complete the master-audit artifact ladder
(row split -> day-clustered SE -> dedup/multi-block -> matched-random control)
on the SAME discovery data. Per the pre-registration rule, surviving signals
remain DISCOVERY SIGNALs until re-run on new data; failing signals are killed.

- YH-1: XLF-ETF eligible advantage (matched same-date non-XLF eligible +
  max-over-8-groups permutation null for multiple testing).
- YH-2: low-lottery advantage (partial Spearman controlling dist_52w_high,
  atr_pct_real, rvol; Q1-Q5 date-blocked diff; matched null; eligible subset).
- YH-3: ATR>10 exclusion (paired date-blocked diff, random-exclusion null,
  simple daily-median drawdown proxy).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from research.master_audit_battery_2026_08_12 import (
    COST_PCT,
    RNG_SEED,
    _load_canonical,
)

PERM_DRAWS = 1000


def _paired_date_median_diff(
    a: pd.DataFrame, b: pd.DataFrame, col: str, seed: int
) -> dict[str, Any]:
    """Per-date median(A)-median(B) on dates where both exist; date-block bootstrap CI."""
    am = a.groupby("scan_date")[col].median()
    bm = b.groupby("scan_date")[col].median()
    common = am.index.intersection(bm.index)
    if len(common) < 5:
        return {"status": "insufficient_paired_dates", "paired_dates": int(len(common))}
    diffs = (am[common] - bm[common]).to_numpy(float)
    rng = np.random.default_rng(seed)
    boots = [
        float(np.mean(rng.choice(diffs, size=len(diffs), replace=True))) for _ in range(PERM_DRAWS)
    ]
    return {
        "paired_dates": int(len(common)),
        "median_diff_pp": float(np.median(diffs)),
        "mean_diff_pp": float(diffs.mean()),
        "ci_lo": float(np.percentile(boots, 2.5)),
        "ci_hi": float(np.percentile(boots, 97.5)),
        "share_dates_positive": float((diffs > 0).mean()),
    }


def yh1_xlf(df: pd.DataFrame, sector_map: Path) -> dict[str, Any]:
    sm = pd.read_csv(sector_map)
    d = df.merge(sm[["symbol", "etf"]], on="symbol", how="left")
    el = d[d["entry_ok"] & d["c2c_5d"].notna() & d["etf"].notna()].copy()
    xlf = el[el["etf"] == "XLF"]
    rest = el[el["etf"] != "XLF"]
    paired = _paired_date_median_diff(xlf, rest, "c2c_5d", RNG_SEED)

    # Multiple-testing null: shuffle ETF labels within date; record max group advantage.
    observed_adv = float(xlf["c2c_5d"].median() - rest["c2c_5d"].median())
    rng = np.random.default_rng(RNG_SEED + 1)
    null_max = []
    groups = sorted(el["etf"].unique())
    for _ in range(PERM_DRAWS):
        shuffled = el.copy()
        shuffled["etf"] = shuffled.groupby("scan_date")["etf"].transform(
            lambda s: rng.permutation(s.to_numpy())
        )
        best = -np.inf
        for gname in groups:
            g = shuffled[shuffled["etf"] == gname]
            o = shuffled[shuffled["etf"] != gname]
            if len(g) >= 20:
                best = max(best, float(g["c2c_5d"].median() - o["c2c_5d"].median()))
        if np.isfinite(best):
            null_max.append(best)
    null_arr = np.array(null_max)
    p_perm = float((null_arr >= observed_adv).mean()) if len(null_arr) else None
    return {
        "xlf_rows": int(len(xlf)),
        "rest_rows": int(len(rest)),
        "xlf_median": float(xlf["c2c_5d"].median()),
        "rest_median": float(rest["c2c_5d"].median()),
        "observed_advantage_pp": observed_adv,
        "paired_date_test": paired,
        "max_of_8_null_p95_pp": float(np.percentile(null_arr, 95)) if len(null_arr) else None,
        "permutation_p": p_perm,
    }


def _partial_spearman(x: pd.Series, y: pd.Series, controls: pd.DataFrame) -> float:
    xr = x.rank().to_numpy(float)
    yr = y.rank().to_numpy(float)
    cz = controls.rank().to_numpy(float)
    cz = np.column_stack([np.ones(len(cz)), cz])
    bx, *_ = np.linalg.lstsq(cz, xr, rcond=None)
    by, *_ = np.linalg.lstsq(cz, yr, rcond=None)
    rx = xr - cz @ bx
    ry = yr - cz @ by
    return float(np.corrcoef(rx, ry)[0, 1])


def yh2_lottery(df: pd.DataFrame) -> dict[str, Any]:
    d = df[df["lottery_factor"].notna() & df["c2c_5d"].notna()].copy()
    d["lot_q"] = pd.qcut(d["lottery_factor"], 5, labels=False, duplicates="drop")
    q1 = d[d["lot_q"] == 0]
    q5 = d[d["lot_q"] == 4]
    paired = _paired_date_median_diff(q1, q5, "c2c_5d", RNG_SEED + 2)

    ctrl_cols = ["dist_52w_high", "atr_pct_real", "rvol"]
    d_partial = d.dropna(subset=ctrl_cols)
    ctrl = d_partial[ctrl_cols]
    raw_rho = float(d["lottery_factor"].corr(d["c2c_5d"], method="spearman"))
    partial_rho = _partial_spearman(d_partial["lottery_factor"], d_partial["c2c_5d"], ctrl)

    # Matched null: within-date shuffled quintile labels, Q1-Q5 median diff distribution.
    rng = np.random.default_rng(RNG_SEED + 3)
    obs_diff = float(q1["c2c_5d"].median() - q5["c2c_5d"].median())
    nulls = []
    for _ in range(PERM_DRAWS):
        sh = d.copy()
        sh["lot_q"] = sh.groupby("scan_date")["lot_q"].transform(
            lambda s: rng.permutation(s.to_numpy())
        )
        a = sh[sh["lot_q"] == 0]["c2c_5d"].median()
        b = sh[sh["lot_q"] == 4]["c2c_5d"].median()
        if pd.notna(a) and pd.notna(b):
            nulls.append(float(a - b))
    null_arr = np.array(nulls)

    # Eligible subset replication (product surface), with small-n caveat.
    el = d[d["entry_ok"]]
    el_cells = {}
    if len(el) >= 30 and el["lottery_factor"].notna().sum() >= 30:
        elq = el.dropna(subset=["lottery_factor"])
        elq = elq.assign(lot_q=pd.qcut(elq["lottery_factor"], 5, labels=False, duplicates="drop"))
        el_cells = {
            f"q{int(q)}": {"n": int(len(g)), "median": float(g["c2c_5d"].median())}
            for q, g in elq.groupby("lot_q")
        }
    return {
        "n_rows": int(len(d)),
        "raw_spearman": raw_rho,
        "partial_spearman_controlled": partial_rho,
        "q1_minus_q5_pp": obs_diff,
        "paired_date_test": paired,
        "null_p95_abs_pp": float(np.percentile(np.abs(null_arr), 95)) if len(null_arr) else None,
        "permutation_p": float((null_arr >= obs_diff).mean()) if len(null_arr) else None,
        "eligible_subset_cells": el_cells,
    }


def yh3_atr10(df: pd.DataFrame) -> dict[str, Any]:
    el = df[df["entry_ok"] & df["c2c_5d"].notna()].copy()
    hi = el[el["atr_pct_real"] > 10]
    lo = el[el["atr_pct_real"] <= 10]
    paired = _paired_date_median_diff(hi, lo, "c2c_5d", RNG_SEED + 4)

    overall_med = float(el["c2c_5d"].median())
    med_without = float(lo["c2c_5d"].median())
    observed_shift = med_without - overall_med

    # Random-exclusion null: shift from excluding a random same-size subset.
    rng = np.random.default_rng(RNG_SEED + 5)
    nulls = []
    idx = np.arange(len(el))
    vals = el["c2c_5d"].to_numpy(float)
    for _ in range(PERM_DRAWS):
        drop = rng.choice(idx, size=len(hi), replace=False)
        keep = np.delete(vals, drop)
        nulls.append(float(np.median(keep) - overall_med))
    null_arr = np.array(nulls)

    # Simple daily-median portfolio drawdown proxy, with vs without the band.
    def _maxdd(frame: pd.DataFrame) -> float | None:
        daily = frame.groupby("scan_date")["c2c_5d"].median().sort_index()
        if len(daily) < 5:
            return None
        equity = (1 + daily / 100).cumprod()
        peak = equity.cummax()
        return float(((equity / peak) - 1).min() * 100)

    return {
        "hi_rows": int(len(hi)),
        "lo_rows": int(len(lo)),
        "hi_median": float(hi["c2c_5d"].median()),
        "lo_median": float(lo["c2c_5d"].median()),
        "paired_date_test": paired,
        "median_shift_pp_without_band": observed_shift,
        "random_exclusion_null_p95_pp": float(np.percentile(null_arr, 95)),
        "shift_percentile_vs_null": float((null_arr >= observed_shift).mean()),
        "maxdd_with_band_pct": _maxdd(el),
        "maxdd_without_band_pct": _maxdd(lo),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    ap.add_argument(
        "--sector-map", type=Path, default=Path("data/backtest_out/sector_map_full.csv")
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("data/backtest_out/hypothesis_ladder_battery_2026-08-12.json"),
    )
    args = ap.parse_args()

    df = _load_canonical(args.csv)
    results = {
        "YH1_xlf": yh1_xlf(df, args.sector_map),
        "YH2_lottery": yh2_lottery(df),
        "YH3_atr10": yh3_atr10(df),
    }
    payload = {
        "status": "exploratory_ladder_completion",
        "production_change": False,
        "locked_oos": "not_opened",
        "note": "Same-data ladder completion; survivors remain DISCOVERY SIGNAL, not EVIDENCE.",
        "rules": {"cost_pct_diagnostic": COST_PCT, "perm_draws": PERM_DRAWS},
        "results": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
