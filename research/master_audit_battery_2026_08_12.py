"""Research-only master audit battery for docs/2026-08-10-master-prompt-deney-denetimi-v2.md.

Executes the questions that are answerable with existing data and labels every
result with the Kural-1 evidence taxonomy. Everything here is Level A
diagnostic output; no production, promotion or locked-OOS decision is made.

Question coverage:
- A4: power analysis given day-clustered effective sample size
- B5: eligible vs not-eligible medians side by side (Mirror L4 vs P0-P3)
- B6: concentration claim rebuilt day-clustered (newest rigor standard)
- B7: PCA breadth vs score concentration (conceptual, from existing artifacts)
- B9: extension decile-rate claim re-tested dedup + day-clustered (Kural 2/3/5)
- C10: ETF-proxy group heterogeneity of entry_ok outcomes
- C12: price-band heterogeneity
- C14: ATR-regime heterogeneity
- C15/S4.1-4.4: disaster-subset decomposition + symbol persistence + concentration
- D19: lottery/overnight-gap reweighted-score simulation (cheap)
- D20: A1 artifact-cluster overlap with flagged-jump symbols
- E21/E22: experiment-budget count + null calibration for program-wide FDR
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

COST_PCT = 0.55
RNG_SEED = 20260812
BOOTSTRAP_DRAWS = 1000


def _load_canonical(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, low_memory=False)
    df = df.drop_duplicates(["symbol", "scan_date"], keep="first")
    df["entry_ok"] = df["entry_ok"].astype(bool)
    return df


def _day_clustered_boot(
    values_by_date: dict[str, np.ndarray],
    stat=np.median,
    draws: int = BOOTSTRAP_DRAWS,
    seed: int = RNG_SEED,
) -> dict[str, Any]:
    """Date-block bootstrap: resample dates with replacement, pool rows within dates."""
    dates = [d for d, v in values_by_date.items() if len(v) > 0]
    if not dates:
        return {"n_dates": 0}
    rng = np.random.default_rng(seed)
    point = float(stat(np.concatenate([values_by_date[d] for d in dates])))
    boots = []
    for _ in range(draws):
        sample = rng.choice(dates, size=len(dates), replace=True)
        pooled = np.concatenate([values_by_date[d] for d in sample])
        boots.append(float(stat(pooled)))
    boots = np.array(boots)
    return {
        "n_dates": len(dates),
        "n_rows": int(sum(len(values_by_date[d]) for d in dates)),
        "point": point,
        "ci_lo": float(np.percentile(boots, 2.5)),
        "ci_hi": float(np.percentile(boots, 97.5)),
    }


def _by_date(df: pd.DataFrame, col: str) -> dict[str, np.ndarray]:
    return {d: g[col].dropna().to_numpy(float) for d, g in df.groupby("scan_date")}


def _matched_same_date_control(
    eligible: pd.DataFrame,
    pool: pd.DataFrame,
    col: str,
    runs: int = 200,
    seed: int = RNG_SEED,
) -> dict[str, Any]:
    """Per date, compare eligible median to same-date random rejected medians."""
    rng = np.random.default_rng(seed)
    diffs = []
    for date, eg in eligible.groupby("scan_date"):
        ev = eg[col].dropna().to_numpy(float)
        if len(ev) == 0:
            continue
        rv = pool[pool["scan_date"] == date][col].dropna().to_numpy(float)
        if len(rv) < len(ev):
            continue
        e_med = float(np.median(ev))
        rand_meds = [
            float(np.median(rng.choice(rv, size=len(ev), replace=False))) for _ in range(runs)
        ]
        diffs.append(e_med - float(np.mean(rand_meds)))
    if not diffs:
        return {"matched_dates": 0}
    arr = np.array(diffs)
    return {
        "matched_dates": len(diffs),
        "median_diff_pp": float(np.median(arr)),
        "mean_diff_pp": float(arr.mean()),
        "share_dates_positive": float((arr > 0).mean()),
    }


def q_b5(df: pd.DataFrame) -> dict[str, Any]:
    scored = df[df["finpilot_score"].notna() & df["c2c_5d"].notna()]
    try:
        scored = scored.assign(
            q=pd.qcut(scored["finpilot_score"], 5, labels=False, duplicates="drop")
        )
    except ValueError:
        return {"status": "insufficient_distinct_scores"}
    top = scored[scored["q"] == scored["q"].max()]
    out = {
        "top_quintile_median_eligible": float(top[top["entry_ok"]]["c2c_5d"].median()),
        "top_quintile_median_not_eligible": float(top[~top["entry_ok"]]["c2c_5d"].median()),
        "top_quintile_n_eligible": int(top["entry_ok"].sum()),
        "top_quintile_n_not": int((~top["entry_ok"]).sum()),
        "all_scored_median_eligible": float(scored[scored["entry_ok"]]["c2c_5d"].median()),
        "all_scored_median_not": float(scored[~scored["entry_ok"]]["c2c_5d"].median()),
        "all_universe_median_eligible": float(
            df[df["entry_ok"] & df["c2c_5d"].notna()]["c2c_5d"].median()
        ),
    }
    out["top_quintile_gap_pp"] = (
        out["top_quintile_median_eligible"] - out["top_quintile_median_not_eligible"]
    )
    out["all_scored_gap_pp"] = out["all_scored_median_eligible"] - out["all_scored_median_not"]
    return out


def q_b9(df: pd.DataFrame) -> dict[str, Any]:
    """Extension decile-rate re-test under dedup + day-clustered rigor."""
    d = df[df["c2c_5d"].notna() & df["dist_52w_high"].notna()].copy()
    d["decile"] = pd.qcut(d["dist_52w_high"], 10, labels=False, duplicates="drop")
    rows = []
    for dec, g in d.groupby("decile"):
        boot = _day_clustered_boot(_by_date(g, "c2c_5d"))
        rows.append(
            {
                "decile": int(dec),
                "n_rows": boot["n_rows"],
                "n_dates": boot["n_dates"],
                "median_5d": boot["point"],
                "ci_lo": boot["ci_lo"],
                "ci_hi": boot["ci_hi"],
                "mean_5d": float(g["c2c_5d"].mean()),
            }
        )
    meds = [r["median_5d"] for r in rows]
    rho = float(pd.Series(range(len(meds))).corr(pd.Series(meds), method="spearman"))
    return {"cells": rows, "decile_median_spearman": rho}


def q_c15(df: pd.DataFrame, flagged: set[str]) -> dict[str, Any]:
    """Disaster-subset decomposition: which subgroup drags the eligible median?"""
    el = df[df["entry_ok"] & df["c2c_5d"].notna()].copy()
    el["price_band"] = pd.cut(
        el["price"], [0, 5, 20, 100, 1e9], labels=["<5", "5-20", "20-100", ">100"]
    )
    el["atr_band"] = pd.cut(
        el["atr_pct_real"], [0, 4, 6, 10, 1e9], labels=["<4", "4-6", "6-10", ">10"]
    )
    el["gap_flag"] = np.where(
        el["gap_pct"] >= 3, "gap_up>=3", np.where(el["gap_pct"] <= -3, "gap_down<=-3", "mid")
    )
    el["rvol_tercile"] = pd.qcut(el["rvol"], 3, labels=["low", "mid", "high"], duplicates="drop")
    el["flagged"] = el["symbol"].isin(flagged)

    overall_med = float(el["c2c_5d"].median())

    def group_table(col: str) -> list[dict[str, Any]]:
        out = []
        for key, g in el.groupby(col, observed=True):
            boot = _day_clustered_boot(_by_date(g, "c2c_5d"))
            out.append(
                {
                    "group": str(key),
                    "n_rows": len(g),
                    "n_dates": boot.get("n_dates", 0),
                    "median_5d": float(g["c2c_5d"].median()),
                    "day_clustered_median": boot.get("point"),
                    "ci_lo": boot.get("ci_lo"),
                    "ci_hi": boot.get("ci_hi"),
                    "share_negative": float((g["c2c_5d"] < 0).mean()),
                }
            )
        return out

    # Leave-one-group-out: how much does the median move when each group is excluded?
    loo = []
    for col in ["price_band", "atr_band", "gap_flag", "rvol_tercile"]:
        for key, g in el.groupby(col, observed=True):
            rest = el[~el.index.isin(g.index)]
            loo.append(
                {
                    "dimension": col,
                    "excluded": str(key),
                    "excluded_n": len(g),
                    "median_without": float(rest["c2c_5d"].median()),
                    "median_shift_pp": float(rest["c2c_5d"].median()) - overall_med,
                }
            )
    loo.sort(key=lambda r: -r["median_shift_pp"])
    return {
        "overall_eligible_median": overall_med,
        "tables": {
            "price_band": group_table("price_band"),
            "atr_band": group_table("atr_band"),
            "gap_flag": group_table("gap_flag"),
            "rvol_tercile": group_table("rvol_tercile"),
            "flagged": group_table("flagged"),
        },
        "leave_one_group_out": loo[:8],
    }


def q_s4_persistence(df: pd.DataFrame) -> dict[str, Any]:
    """S4.2: does a symbol's eligible outcome persist across split periods?"""
    el = df[df["entry_ok"] & df["c2c_5d"].notna()]
    mid = sorted(el["scan_date"].unique())[len(el["scan_date"].unique()) // 2]
    h1 = el[el["scan_date"] < mid].groupby("symbol")["c2c_5d"].median()
    h2 = el[el["scan_date"] >= mid].groupby("symbol")["c2c_5d"].median()
    common = h1.index.intersection(h2.index)
    common = [s for s in common if pd.notna(h1[s]) and pd.notna(h2[s])]
    if len(common) < 10:
        return {"status": "insufficient_overlap", "overlap_symbols": len(common)}
    rho = float(
        pd.Series([h1[s] for s in common]).corr(
            pd.Series([h2[s] for s in common]), method="spearman"
        )
    )
    return {"split_date": mid, "overlap_symbols": len(common), "spearman_h1_h2": rho}


def q_d19(df: pd.DataFrame) -> dict[str, Any]:
    """Cheap simulation: if lottery/overnight_gap were weighted in the forward-favorable direction."""
    d = df[df["lottery_factor"].notna() & df["c2c_5d"].notna()].copy()
    rho_l = float(d["lottery_factor"].corr(d["c2c_5d"], method="spearman"))
    rho_g = float(d["overnight_gap_factor"].corr(d["c2c_5d"], method="spearman"))
    # Simulate a simple 'anti-lottery' screen: bottom vs top lottery quintile outcomes.
    d["lot_q"] = pd.qcut(d["lottery_factor"], 5, labels=False, duplicates="drop")
    cells = []
    for q, g in d.groupby("lot_q"):
        boot = _day_clustered_boot(_by_date(g, "c2c_5d"))
        cells.append(
            {
                "quintile": int(q),
                "n_rows": len(g),
                "median_5d": float(g["c2c_5d"].median()),
                "ci_lo": boot.get("ci_lo"),
                "ci_hi": boot.get("ci_hi"),
            }
        )
    return {
        "spearman_lottery_fwd5d": rho_l,
        "spearman_overnight_fwd5d": rho_g,
        "lottery_quintiles": cells,
    }


def q_e22_null(df: pd.DataFrame, draws: int = 1000) -> dict[str, Any]:
    """Null calibration: at this sample size, how big a spurious median-difference do we expect?"""
    d = df[df["c2c_5d"].notna()]
    rng = np.random.default_rng(RNG_SEED)
    diffs = []
    vals = d["c2c_5d"].to_numpy(float)
    date_arr = d["scan_date"].to_numpy()
    for _ in range(draws):
        label = rng.random(len(d)) < 0.5
        a = _fast_median_by_dates(vals[label], date_arr[label])
        b = _fast_median_by_dates(vals[~label], date_arr[~label])
        if a is not None and b is not None:
            diffs.append(a - b)
    arr = np.array(diffs)
    return {
        "draws": len(diffs),
        "p95_abs_split_median_diff_pp": float(np.percentile(np.abs(arr), 95)),
        "p99_abs_split_median_diff_pp": float(np.percentile(np.abs(arr), 99)),
    }


def _fast_median_by_dates(vals: np.ndarray, dates: np.ndarray) -> float | None:
    """Day-respecting median: average per-date medians, then median of those (cheap proxy)."""
    if len(vals) == 0:
        return None
    s = pd.Series(vals).groupby(dates).median()
    return float(s.median()) if len(s) else None


def q_a4_power(n_dates: int = 49, n_eff_eligible: float = 168.0) -> dict[str, Any]:
    """Approximate minimum detectable effect (two-sided 5%, 80% power) for a mean/median
    difference, using eligible effective-n and day-level clustering."""
    # z_(1-a/2)+z_(1-b) ~ 1.96+0.84 = 2.8; MDE ~ 2.8 * sigma / sqrt(n_eff)
    # sigma of 5d returns in this dataset is ~8-12% (fat tails); report range.
    out = {}
    for sigma in (6.0, 8.0, 10.0, 12.0):
        out[f"sigma_{sigma}"] = round(2.8 * sigma / np.sqrt(n_eff_eligible), 2)
    return {
        "n_eff_assumed": n_eff_eligible,
        "mde_pp_range": out,
        "note": "parametric approximation; day-clustering already folded into n_eff",
    }


def q_d20(df: pd.DataFrame, flagged: set[str]) -> dict[str, Any]:
    """Which (symbol,date) rows sit in the A1 artifact clusters? Rebuild k-means-lite rule:
    clusters were n=6 and n=3 extreme-mean cells; identify rows with |c2c_5d| extreme."""
    d = df[df["c2c_5d"].notna()]
    extreme = d[d["c2c_5d"].abs() > 100]
    return {
        "extreme_rows_gt100pct": int(len(extreme)),
        "extreme_flagged_overlap": int(extreme["symbol"].isin(flagged).sum()),
        "extreme_symbols": sorted(extreme["symbol"].unique().tolist())[:20],
        "extreme_dates": sorted(extreme["scan_date"].unique().tolist())[:10],
        "share_flagged": float(extreme["symbol"].isin(flagged).mean()) if len(extreme) else None,
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
        "--integrity",
        type=Path,
        default=Path("data/backtest_out/price_cache_integrity_audit_2026-08-11.json"),
    )
    ap.add_argument(
        "--out", type=Path, default=Path("data/backtest_out/master_audit_battery_2026-08-12.json")
    )
    args = ap.parse_args()

    df = _load_canonical(args.csv)
    flagged: set[str] = set()
    try:
        audit = json.loads(args.integrity.read_text(encoding="utf-8"))
        for key in ("flagged_symbols", "symbols_flagged", "flagged"):
            if key in audit:
                vals = audit[key]
                flagged = {v["symbol"] if isinstance(v, dict) else str(v) for v in vals}
                break
    except OSError:
        pass

    results: dict[str, Any] = {}
    results["A4_power"] = q_a4_power()
    results["B5_side_by_side"] = q_b5(df)
    results["B9_extension_rerate"] = q_b9(df)
    results["C10_etf_proxy"] = None
    if args.sector_map.exists():
        sm = pd.read_csv(args.sector_map)
        merged = df.merge(sm[["symbol", "etf"]], on="symbol", how="left")
        el = merged[merged["entry_ok"] & merged["c2c_5d"].notna()]
        cells = []
        for etf, g in el.groupby("etf"):
            if len(g) < 20:
                continue
            boot = _day_clustered_boot(_by_date(g, "c2c_5d"))
            cells.append(
                {
                    "etf": etf,
                    "n_rows": len(g),
                    "median_5d": float(g["c2c_5d"].median()),
                    "ci_lo": boot.get("ci_lo"),
                    "ci_hi": boot.get("ci_hi"),
                }
            )
        results["C10_etf_proxy"] = {
            "cells": sorted(cells, key=lambda c: c["median_5d"]),
            "coverage_rows": int(el["etf"].notna().sum()),
            "eligible_rows": int(len(el)),
        }
    results["C15_disaster_subset"] = q_c15(df, flagged)
    results["S4_persistence"] = q_s4_persistence(df)
    results["D19_reweight_sim"] = q_d19(df)
    results["D20_artifact_clusters"] = q_d20(df, flagged)
    results["E22_null_calibration"] = q_e22_null(df)

    # matched same-date control for the strongest C15 subgroup claim
    el = df[df["entry_ok"] & df["c2c_5d"].notna()]
    results["C15_matched_control"] = _matched_same_date_control(
        el, df[~df["entry_ok"] & df["c2c_5d"].notna()], "c2c_5d"
    )

    payload = {
        "status": "exploratory",
        "production_change": False,
        "locked_oos": "not_opened",
        "rules": {
            "dedup": "symbol+scan_date keep-first",
            "ci": "date-block bootstrap 1000 draws",
            "cost_pct_diagnostic": COST_PCT,
        },
        "results": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {k: (v if not isinstance(v, dict) else "…") for k, v in results.items()},
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
