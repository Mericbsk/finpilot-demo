#!/usr/bin/env python3
"""Strategic Thinking Lab experiment battery (research-only, Level A).

Runs the feasible subset of the 2026-08-10 Strategic Thinking Lab experiments
against the canonical full-universe export and the daily price cache.

Hard rules for this battery:
- No new parameter search. All inputs are frozen fields from the canonical
  export plus deterministic forward-path metrics from the price cache.
- Robust statistics throughout (median, winsorized mean, positive rate) and
  a flagged-symbol-excluded robustness variant, because the cache integrity
  audit (2026-08-07) flagged 148 symbols with 50%+ single-day jumps.
- Date-block bootstrap for confidence intervals (rows within a scan_date are
  cross-sectionally correlated; naive row bootstrap understates uncertainty).
- Every experiment reports a status: COMPLETED, PARTIAL or INSUFFICIENT_DATA.
  Nothing here is a promotion, profitability or production decision.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from research.timing_drift_study import load_bars

DEFAULT_CSV = Path("data/backtest_out/full_universe_enriched.csv")
DEFAULT_CACHE = Path("data/price_cache")
DEFAULT_AUDIT = Path("data/backtest_out/price_cache_adjusted_integrity_audit_2026-08-07.json")
DEFAULT_OUT = Path("data/backtest_out/strategic_lab_2026-08-10.json")

COST_PCT = 0.55  # round-trip cost assumption, matching prior P2 protocol
HORIZONS = (1, 2, 3, 5, 10)
BOOTSTRAP_DRAWS = 1000
SEED = 20260810
WINSOR_LO, WINSOR_HI = 0.01, 0.99
ARTIFACT_RETURN_CAP_PCT = 100.0  # |return| above this is treated as data artifact


# ---------------------------------------------------------------------------
# Loading and enrichment
# ---------------------------------------------------------------------------


def load_export(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, low_memory=False)
    df["scan_date"] = df["scan_date"].astype(str)
    df["symbol"] = df["symbol"].astype(str).str.strip()
    df["entry_ok"] = df["entry_ok"].astype(str).str.lower().isin({"1", "true", "yes"})
    for col in (
        "price",
        "score",
        "composite_score",
        "finpilot_score",
        "atr",
        "resolved_pct_t5",
        "resolved_pct_1d",
        "gap_pct",
        "rvol",
        "atr_pct_real",
        "dist_52w_high",
        "vol_regime",
    ):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df[df["price"].notna() & (df["price"] > 0)]
    # Canonical dedup: earliest scan_ts per (symbol, scan_date)
    df = df.sort_values(["symbol", "scan_date", "scan_ts"])
    df = df.drop_duplicates(subset=["symbol", "scan_date"], keep="first")
    return df.reset_index(drop=True)


def load_flagged_symbols(audit_path: Path) -> set[str]:
    try:
        payload = json.loads(audit_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    return {str(item.get("symbol")) for item in payload.get("flagged_symbols", [])}


def compute_path_metrics(rows: pd.DataFrame, cache_dir: Path) -> pd.DataFrame:
    """Attach cache-derived per-row metrics in a single pass over symbols.

    Entry convention: the first cache bar with date >= scan_date is the entry
    bar. Forward day N return = close(entry+N) vs close(entry). MFE/MAE over
    horizon H use the high/low of bars entry+1 .. entry+H (forward window
    excludes the entry bar itself).
    """
    metrics: dict[int, dict[str, float | None]] = {}
    grouped = rows.groupby("symbol")
    for symbol, group in grouped:
        bars = load_bars(cache_dir, symbol)
        if not bars:
            continue
        dates = [str(b["date"]) for b in bars]
        date_index = {d: i for i, d in enumerate(dates)}
        closes = np.array([b["close"] for b in bars], dtype=float)
        opens = np.array([b["open"] for b in bars], dtype=float)
        highs = np.array(
            [b["high"] if b["high"] is not None else np.nan for b in bars], dtype=float
        )
        lows = np.array([b["low"] if b["low"] is not None else np.nan for b in bars], dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            daily_ret = closes[1:] / closes[:-1] - 1.0
        for row_idx, scan_date in zip(group.index, group["scan_date"], strict=False):
            entry_idx: int | None = None
            for i, d in enumerate(dates):
                if d >= scan_date:
                    entry_idx = i
                    break
            if entry_idx is None:
                continue
            entry_close = closes[entry_idx]
            if not math.isfinite(entry_close) or entry_close <= 0:
                continue
            out: dict[str, float | None] = {"cache_close": float(entry_close)}
            # Past 5-day return (backward-looking information)
            if entry_idx - 5 >= 0 and closes[entry_idx - 5] > 0:
                out["past_5d_pct"] = float((entry_close / closes[entry_idx - 5] - 1.0) * 100.0)
            else:
                out["past_5d_pct"] = None
            # Forward close-to-close returns per horizon
            for h in HORIZONS:
                j = entry_idx + h
                out[f"fwd_{h}d_pct"] = (
                    float((closes[j] / entry_close - 1.0) * 100.0)
                    if j < len(closes) and closes[j] > 0
                    else None
                )
            # Entry-delay variants: same exit bar (entry+5 close), different entry price
            exit5 = closes[entry_idx + 5] if entry_idx + 5 < len(closes) else None
            if exit5 is not None and exit5 > 0:
                out["delay_close5_pct"] = float((exit5 / entry_close - 1.0) * 100.0)
                if entry_idx + 1 < len(opens) and opens[entry_idx + 1] > 0:
                    out["delay_nextopen5_pct"] = float((exit5 / opens[entry_idx + 1] - 1.0) * 100.0)
                else:
                    out["delay_nextopen5_pct"] = None
                if entry_idx + 1 < len(closes) and closes[entry_idx + 1] > 0:
                    out["delay_nextclose5_pct"] = float(
                        (exit5 / closes[entry_idx + 1] - 1.0) * 100.0
                    )
                else:
                    out["delay_nextclose5_pct"] = None
            else:
                out["delay_close5_pct"] = None
                out["delay_nextopen5_pct"] = None
                out["delay_nextclose5_pct"] = None
            # MFE / MAE over 5d and 10d forward windows
            for h in (5, 10):
                end = min(entry_idx + h, len(closes) - 1)
                if end > entry_idx:
                    window_high = highs[entry_idx + 1 : end + 1]
                    window_low = lows[entry_idx + 1 : end + 1]
                    if np.isfinite(window_high).any():
                        mfe_idx = int(np.nanargmax(window_high))
                        out[f"mfe_{h}d_pct"] = float(
                            (window_high[mfe_idx] / entry_close - 1.0) * 100.0
                        )
                        out[f"time_to_mfe_{h}d"] = float(mfe_idx + 1)
                    else:
                        out[f"mfe_{h}d_pct"] = None
                        out[f"time_to_mfe_{h}d"] = None
                    if np.isfinite(window_low).any():
                        mae_idx = int(np.nanargmin(window_low))
                        out[f"mae_{h}d_pct"] = float(
                            (window_low[mae_idx] / entry_close - 1.0) * 100.0
                        )
                        out[f"time_to_mae_{h}d"] = float(mae_idx + 1)
                    else:
                        out[f"mae_{h}d_pct"] = None
                        out[f"time_to_mae_{h}d"] = None
                else:
                    out[f"mfe_{h}d_pct"] = None
                    out[f"mae_{h}d_pct"] = None
                    out[f"time_to_mfe_{h}d"] = None
                    out[f"time_to_mae_{h}d"] = None
            # Past 20-day daily return series (for candidate correlation)
            if entry_idx - 20 >= 0:
                series = daily_ret[entry_idx - 20 : entry_idx]
                out["past20_ret"] = series.tolist() if len(series) == 20 else None
            else:
                out["past20_ret"] = None
            metrics[row_idx] = out
    metrics_df = pd.DataFrame.from_dict(metrics, orient="index")
    enriched = rows.join(metrics_df) if not metrics_df.empty else rows.copy()
    if "cache_close" not in enriched.columns:
        enriched["cache_close"] = np.nan
    enriched["drift_pct"] = (enriched["price"] / enriched["cache_close"] - 1.0) * 100.0
    return enriched


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------


def winsorized_mean(
    values: np.ndarray, lo: float = WINSOR_LO, hi: float = WINSOR_HI
) -> float | None:
    clean = values[np.isfinite(values)]
    if clean.size == 0:
        return None
    qlo, qhi = np.quantile(clean, [lo, hi])
    capped = np.clip(clean, qlo, qhi)
    return float(capped.mean())


def dist_summary(values: pd.Series | np.ndarray) -> dict:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {"n": 0, "mean": None, "median": None, "winsor_mean": None, "positive_rate": None}
    return {
        "n": int(arr.size),
        "mean": round(float(arr.mean()), 6),
        "median": round(float(np.median(arr)), 6),
        "winsor_mean": round(winsorized_mean(arr), 6),
        "positive_rate": round(float((arr > 0).mean()), 6),
    }


def block_bootstrap_ci(
    df: pd.DataFrame,
    value_col: str,
    stat: str = "median",
    draws: int = BOOTSTRAP_DRAWS,
    seed: int = SEED,
) -> dict:
    """Date-block bootstrap CI for a per-row statistic.

    Resamples scan_dates with replacement and keeps all rows of each sampled
    date, preserving within-day cross-sectional correlation.
    """
    rng = np.random.default_rng(seed)
    sub = df[["scan_date", value_col]].dropna()
    if sub.empty:
        return {"stat": stat, "estimate": None, "ci_lo": None, "ci_hi": None, "n_dates": 0}
    dates = sub["scan_date"].unique()
    by_date = {d: sub.loc[sub["scan_date"] == d, value_col].to_numpy() for d in dates}

    def _stat(sample: np.ndarray) -> float:
        return float(np.median(sample)) if stat == "median" else float(winsorized_mean(sample))

    pooled = sub[value_col].to_numpy()
    estimate = _stat(pooled)
    boot = []
    for _ in range(draws):
        picked = rng.choice(dates, size=len(dates), replace=True)
        sample = np.concatenate([by_date[d] for d in picked])
        boot.append(_stat(sample))
    lo, hi = np.quantile(boot, [0.025, 0.975])
    return {
        "stat": stat,
        "estimate": round(estimate, 6),
        "ci_lo": round(float(lo), 6),
        "ci_hi": round(float(hi), 6),
        "n_dates": int(len(dates)),
    }


def effective_sample_size(df: pd.DataFrame, value_col: str) -> dict:
    """Ratio of naive row-bootstrap CI width to date-block CI width.

    A ratio well below 1 means naive independence assumptions understate
    uncertainty; n_eff ~= n_rows * ratio^2 is a rough guide.
    """
    sub = df[["scan_date", value_col]].dropna()
    if sub.empty:
        return {"ratio": None, "n_rows": 0, "n_eff_approx": None}
    rng = np.random.default_rng(SEED)
    values = sub[value_col].to_numpy()
    dates = sub["scan_date"].unique()
    by_date = {d: sub.loc[sub["scan_date"] == d, value_col].to_numpy() for d in dates}
    naive, block = [], []
    for _ in range(500):
        naive.append(float(np.median(rng.choice(values, size=len(values), replace=True))))
        picked = rng.choice(dates, size=len(dates), replace=True)
        block.append(float(np.median(np.concatenate([by_date[d] for d in picked]))))
    naive_w = float(np.quantile(naive, 0.975) - np.quantile(naive, 0.025))
    block_w = float(np.quantile(block, 0.975) - np.quantile(block, 0.025))
    ratio = (naive_w / block_w) if block_w > 0 else None
    n_rows = int(len(values))
    return {
        "ratio": round(ratio, 4) if ratio is not None else None,
        "n_rows": n_rows,
        "n_eff_approx": int(n_rows * ratio * ratio) if ratio else None,
    }


# ---------------------------------------------------------------------------
# Experiments
# ---------------------------------------------------------------------------


def exp_v0_label_validation(df: pd.DataFrame) -> dict:
    """V0: does resolved_pct_t5 match cache-derived 5d close-to-close?"""
    sub = df.dropna(subset=["resolved_pct_t5", "fwd_5d_pct"])
    if len(sub) < 100:
        return {"status": "INSUFFICIENT_DATA", "n": int(len(sub))}
    sample = sub.sample(n=min(2000, len(sub)), random_state=SEED)
    corr = float(np.corrcoef(sample["resolved_pct_t5"], sample["fwd_5d_pct"])[0, 1])
    mad = float(np.abs(sample["resolved_pct_t5"] - sample["fwd_5d_pct"]).median())
    return {
        "status": "COMPLETED",
        "n": int(len(sample)),
        "pearson_corr": round(corr, 4),
        "median_abs_diff_pct": round(mad, 4),
        "interpretation": (
            "resolved_pct_t5 matches cache close-to-close 5d return"
            if corr > 0.95
            else "resolved_pct_t5 diverges from cache close-to-close; treat label semantics as unverified"
        ),
    }


def exp_r1_backward_vs_forward(df: pd.DataFrame) -> dict:
    """R1: is the score backward-looking (past returns) or forward-looking?"""
    sub = df.dropna(subset=["finpilot_score", "past_5d_pct", "fwd_5d_pct"])
    sub = sub[~sub["symbol"].isin(df.attrs.get("flagged", set()))]
    if len(sub) < 500:
        return {"status": "INSUFFICIENT_DATA", "n": int(len(sub))}
    past = spearmanr(sub["finpilot_score"], sub["past_5d_pct"]).statistic
    fwd = spearmanr(sub["finpilot_score"], sub["fwd_5d_pct"]).statistic
    return {
        "status": "COMPLETED",
        "n": int(len(sub)),
        "spearman_score_vs_past_5d": round(float(past), 4),
        "spearman_score_vs_fwd_5d": round(float(fwd), 4),
        "interpretation": (
            "score carries more backward- than forward-looking information"
            if abs(past) > abs(fwd)
            else "score carries at least as much forward- as backward-looking information"
        ),
    }


def exp_r2_reverse_ranking(df: pd.DataFrame) -> dict:
    """R2: eligible vs rejected counterfactual with date-block bootstrap."""
    sub = df.dropna(subset=["fwd_5d_pct"])
    eligible = sub[sub["entry_ok"]]
    rejected = sub[~sub["entry_ok"]]
    if len(eligible) < 100 or len(rejected) < 1000:
        return {"status": "INSUFFICIENT_DATA"}
    elig_ci = block_bootstrap_ci(eligible, "fwd_5d_pct")
    rej_ci = block_bootstrap_ci(rejected, "fwd_5d_pct")
    return {
        "status": "COMPLETED",
        "eligible": {**dist_summary(eligible["fwd_5d_pct"]), "block_ci": elig_ci},
        "rejected": {**dist_summary(rejected["fwd_5d_pct"]), "block_ci": rej_ci},
        "eligible_minus_rejected_median": round(
            (elig_ci["estimate"] or 0) - (rej_ci["estimate"] or 0), 6
        ),
        "interpretation": (
            "eligible cohort outperforms rejected cohort"
            if (elig_ci["estimate"] or 0) > (rej_ci["estimate"] or 0)
            else "eligible cohort does NOT outperform rejected cohort (reverse-ranking signal replicates)"
        ),
    }


def exp_r3_decile_monotonicity(df: pd.DataFrame) -> dict:
    """R3: score deciles vs forward return; monotonicity test."""
    sub = df.dropna(subset=["finpilot_score", "fwd_5d_pct"]).copy()
    if len(sub) < 1000:
        return {"status": "INSUFFICIENT_DATA", "n": int(len(sub))}
    sub["decile"] = pd.qcut(sub["finpilot_score"], 10, labels=False, duplicates="drop")
    rows = []
    for decile, group in sub.groupby("decile"):
        s = dist_summary(group["fwd_5d_pct"])
        s["decile"] = int(decile)
        s["score_min"] = round(float(group["finpilot_score"].min()), 2)
        s["score_max"] = round(float(group["finpilot_score"].max()), 2)
        rows.append(s)
    medians = [r["median"] for r in rows]
    mono = spearmanr([r["decile"] for r in rows], medians).statistic if len(rows) >= 5 else None
    return {
        "status": "COMPLETED",
        "deciles": rows,
        "spearman_decile_vs_median": round(float(mono), 4) if mono is not None else None,
        "interpretation": (
            "score deciles are monotone in forward return"
            if mono is not None and mono > 0.8
            else "score deciles are NOT monotone in forward return"
        ),
    }


def exp_r4_rank_stability(df: pd.DataFrame) -> dict:
    """R4: day-over-day rank stability of the score per symbol."""
    sub = df.dropna(subset=["finpilot_score"]).copy()
    sub["rank"] = sub.groupby("scan_date")["finpilot_score"].rank(pct=True)
    sub = sub.sort_values(["symbol", "scan_date"])
    sub["next_rank"] = sub.groupby("symbol")["rank"].shift(-1)
    sub["next_date"] = sub.groupby("symbol")["scan_date"].shift(-1)
    pairs = sub.dropna(subset=["next_rank"])
    pairs = pairs[pairs["next_date"] > pairs["scan_date"]]
    if len(pairs) < 500:
        return {"status": "INSUFFICIENT_DATA", "n": int(len(pairs))}
    rho = spearmanr(pairs["rank"], pairs["next_rank"]).statistic
    return {
        "status": "COMPLETED",
        "n_pairs": int(len(pairs)),
        "spearman_rank_stability": round(float(rho), 4),
        "interpretation": (
            "ranks are highly sticky day-over-day (score mostly repeats yesterday)"
            if rho > 0.7
            else "ranks turn over meaningfully day-over-day"
        ),
    }


def exp_r5_signal_decay(df: pd.DataFrame) -> dict:
    """R5: forward return by horizon for eligible vs all rows."""
    out = {"status": "COMPLETED", "by_horizon": {}}
    for h in HORIZONS:
        col = f"fwd_{h}d_pct"
        sub = df.dropna(subset=[col])
        elig = sub[sub["entry_ok"]][col]
        out["by_horizon"][str(h)] = {
            "eligible": dist_summary(elig),
            "all_rows": dist_summary(sub[col]),
        }
    elig_medians = [out["by_horizon"][str(h)]["eligible"]["median"] for h in HORIZONS]
    out["interpretation"] = (
        "eligible median return decays with horizon"
        if all(m is not None for m in elig_medians) and elig_medians[0] > elig_medians[-1]
        else "no clean horizon decay pattern in eligible median"
    )
    return out


def exp_r10_cross_sectional(df: pd.DataFrame) -> dict:
    """R10: within-day percentile rank vs absolute score as predictor."""
    sub = df.dropna(subset=["finpilot_score", "fwd_5d_pct"]).copy()
    if len(sub) < 1000:
        return {"status": "INSUFFICIENT_DATA"}
    sub["pct_rank"] = sub.groupby("scan_date")["finpilot_score"].rank(pct=True)
    abs_rho = spearmanr(sub["finpilot_score"], sub["fwd_5d_pct"]).statistic
    rel_rho = spearmanr(sub["pct_rank"], sub["fwd_5d_pct"]).statistic
    return {
        "status": "COMPLETED",
        "n": int(len(sub)),
        "spearman_absolute_score": round(float(abs_rho), 4),
        "spearman_within_day_percentile": round(float(rel_rho), 4),
        "interpretation": (
            "within-day relative rank carries more forward information than absolute score"
            if abs(rel_rho) > abs(abs_rho)
            else "absolute score carries at least as much information as relative rank"
        ),
    }


def exp_e1_entry_delay(df: pd.DataFrame) -> dict:
    """E1 (daily approximation): entry at signal close vs next open vs next close."""
    cols = {
        "signal_close": "delay_close5_pct",
        "next_open": "delay_nextopen5_pct",
        "next_close": "delay_nextclose5_pct",
    }
    out = {"status": "COMPLETED", "variants": {}}
    for name, col in cols.items():
        sub = df.dropna(subset=[col])
        elig = sub[sub["entry_ok"]]
        out["variants"][name] = {
            "eligible": dist_summary(elig[col]),
            "all_rows": dist_summary(sub[col]),
        }
    elig_meds = {k: v["eligible"]["median"] for k, v in out["variants"].items()}
    if elig_meds["signal_close"] is not None and elig_meds["next_open"] is not None:
        out["delay_cost_median_pct"] = round(elig_meds["signal_close"] - elig_meds["next_open"], 6)
    out["interpretation"] = (
        "entry delay consumes a large share of any median edge"
        if out.get("delay_cost_median_pct") is not None and abs(out["delay_cost_median_pct"]) > 0.5
        else "entry-delay cost is small relative to median outcome"
    )
    return out


def exp_e2_drift_budget(df: pd.DataFrame) -> dict:
    """E2: exclude candidates whose recorded-price vs cache-close drift exceeds budget."""
    sub = df.dropna(subset=["drift_pct", "fwd_5d_pct"])
    elig = sub[sub["entry_ok"]]
    out = {"status": "COMPLETED", "budgets": {}}
    for budget in (1.0, 3.0, 5.0):
        kept = elig[elig["drift_pct"].abs() <= budget]
        out["budgets"][str(budget)] = {
            "kept_n": int(len(kept)),
            "kept_share": round(len(kept) / max(len(elig), 1), 4),
            "outcome": dist_summary(kept["fwd_5d_pct"]),
        }
    out["all_eligible"] = dist_summary(elig["fwd_5d_pct"])
    return out


def exp_x1_mae_mfe(df: pd.DataFrame) -> dict:
    """X1: MAE/MFE data layer — distributions for eligible vs rejected."""
    sub = df.dropna(subset=["mfe_5d_pct", "mae_5d_pct"])
    elig = sub[sub["entry_ok"]]
    rej = sub[~sub["entry_ok"]]
    if len(elig) < 100:
        return {"status": "INSUFFICIENT_DATA", "eligible_n": int(len(elig))}
    return {
        "status": "COMPLETED",
        "eligible": {
            "mfe_5d": dist_summary(elig["mfe_5d_pct"]),
            "mae_5d": dist_summary(elig["mae_5d_pct"]),
            "mfe_10d": dist_summary(elig["mfe_10d_pct"]),
            "mae_10d": dist_summary(elig["mae_10d_pct"]),
            "time_to_mfe_5d_median": round(float(elig["time_to_mfe_5d"].median()), 3),
            "time_to_mae_5d_median": round(float(elig["time_to_mae_5d"].median()), 3),
        },
        "rejected": {
            "mfe_5d": dist_summary(rej["mfe_5d_pct"]),
            "mae_5d": dist_summary(rej["mae_5d_pct"]),
        },
    }


def exp_x3_mfe_capture(df: pd.DataFrame) -> dict:
    """X3: how much of the 5d MFE does holding-to-horizon capture?"""
    sub = df.dropna(subset=["mfe_5d_pct", "fwd_5d_pct"])
    sub = sub[sub["mfe_5d_pct"] > 0]
    elig = sub[sub["entry_ok"]]
    if len(elig) < 100:
        return {"status": "INSUFFICIENT_DATA"}
    capture = elig["fwd_5d_pct"] / elig["mfe_5d_pct"]
    return {
        "status": "COMPLETED",
        "eligible_n": int(len(elig)),
        "capture_ratio": dist_summary(capture),
        "interpretation": (
            "holding to horizon captures less than half of the typical favorable excursion"
            if dist_summary(capture)["median"] is not None and dist_summary(capture)["median"] < 0.5
            else "holding to horizon captures most of the favorable excursion"
        ),
    }


def exp_x6_invalidation_exit(df: pd.DataFrame) -> dict:
    """X6-lite: hold-to-horizon vs exit at first daily close below entry - 1*ATR.

    Daily-bar approximation; intraday stop ordering cannot be resolved.
    """
    sub = df.dropna(subset=["fwd_5d_pct", "atr", "cache_close"])
    elig = sub[sub["entry_ok"]].copy()
    if len(elig) < 100:
        return {"status": "INSUFFICIENT_DATA"}
    # Proxy: candidates whose 5d MAE breached -1 ATR% would have been stopped;
    # approximate the stopped outcome as -1 ATR% (optimistic: assumes fill at level).
    elig["atr_pct"] = elig["atr"] / elig["cache_close"] * 100.0
    stopped = elig["mae_5d_pct"] <= -elig["atr_pct"]
    hold = elig["fwd_5d_pct"]
    exit_proxy = np.where(stopped, -elig["atr_pct"], elig["fwd_5d_pct"])
    return {
        "status": "PARTIAL",
        "note": "daily-bar proxy; assumes fill exactly at -1 ATR (optimistic, ignores gap-through)",
        "eligible_n": int(len(elig)),
        "stopped_share": round(float(stopped.mean()), 4),
        "hold_to_horizon": dist_summary(hold),
        "invalidation_exit_proxy": dist_summary(pd.Series(exit_proxy)),
    }


def exp_g2_regime_calibration(df: pd.DataFrame) -> dict:
    """G2: vol_regime x score tercile -> forward return."""
    sub = df.dropna(subset=["vol_regime", "finpilot_score", "fwd_5d_pct"]).copy()
    if len(sub) < 1000:
        return {"status": "INSUFFICIENT_DATA", "n": int(len(sub))}
    sub["tercile"] = pd.qcut(sub["finpilot_score"], 3, labels=["low", "mid", "high"])
    table = {}
    for (regime, tercile), group in sub.groupby(["vol_regime", "tercile"], observed=True):
        key = f"regime{int(regime)}_{tercile}"
        table[key] = dist_summary(group["fwd_5d_pct"])
    return {"status": "COMPLETED", "cells": table}


def exp_g4_regime_stratified(df: pd.DataFrame) -> dict:
    """G4: eligible performance stratified by vol_regime instead of time."""
    sub = df.dropna(subset=["vol_regime", "fwd_5d_pct"])
    elig = sub[sub["entry_ok"]]
    out = {"status": "COMPLETED", "by_regime": {}}
    for regime, group in elig.groupby("vol_regime"):
        out["by_regime"][str(int(regime))] = {
            **dist_summary(group["fwd_5d_pct"]),
            "block_ci": block_bootstrap_ci(group, "fwd_5d_pct"),
        }
    return out


def exp_p1_counterfactual_portfolio(df: pd.DataFrame) -> dict:
    """P1: per-date selected portfolio vs random rejected portfolios, net of cost."""
    sub = df.dropna(subset=["fwd_5d_pct"])
    rng = np.random.default_rng(SEED)
    diffs = []
    selected_rets = []
    for date, group in sub.groupby("scan_date"):
        sel = group[group["entry_ok"]]["fwd_5d_pct"].to_numpy()
        rej = group[~group["entry_ok"]]["fwd_5d_pct"].to_numpy()
        if len(sel) == 0 or len(rej) < len(sel):
            continue
        sel_net = float(np.mean(sel) - COST_PCT)
        selected_rets.append(sel_net)
        cf = [
            float(np.mean(rng.choice(rej, size=len(sel), replace=False)) - COST_PCT)
            for _ in range(200)
        ]
        diffs.append(sel_net - float(np.mean(cf)))
    if len(diffs) < 30:
        return {"status": "INSUFFICIENT_DATA", "n_dates": len(diffs)}
    arr = np.array(diffs)
    return {
        "status": "COMPLETED",
        "n_dates": int(len(diffs)),
        "selected_portfolio": dist_summary(pd.Series(selected_rets)),
        "selected_minus_counterfactual": {
            **dist_summary(arr),
            "share_positive": round(float((arr > 0).mean()), 4),
        },
        "interpretation": (
            "selection adds value over random same-date rejected portfolios"
            if np.median(arr) > 0
            else "selection does NOT beat random same-date rejected portfolios"
        ),
    }


def exp_p2_candidate_correlation(df: pd.DataFrame) -> dict:
    """P2: mean pairwise correlation of past-20d returns among same-day candidates."""
    sub = df[df["entry_ok"]].dropna(subset=["past20_ret"])
    per_date = []
    for date, group in sub.groupby("scan_date"):
        series = [np.array(s, dtype=float) for s in group["past20_ret"]]
        series = [s for s in series if len(s) == 20 and np.isfinite(s).all()]
        if len(series) < 2:
            continue
        mat = np.corrcoef(np.vstack(series))
        iu = np.triu_indices(len(series), k=1)
        per_date.append(float(np.nanmean(mat[iu])))
    if len(per_date) < 20:
        return {"status": "INSUFFICIENT_DATA", "n_dates": len(per_date)}
    return {
        "status": "COMPLETED",
        "n_dates": len(per_date),
        "mean_pairwise_correlation": dist_summary(pd.Series(per_date)),
        "interpretation": (
            "same-day candidates are highly correlated (redundant bets)"
            if np.median(per_date) > 0.5
            else "same-day candidates show moderate/low return correlation"
        ),
    }


def exp_p7_loss_clustering(df: pd.DataFrame) -> dict:
    """P7: do eligible losses cluster in time?"""
    sub = df[df["entry_ok"]].dropna(subset=["fwd_5d_pct"])
    daily = sub.groupby("scan_date")["fwd_5d_pct"].agg(["mean", "count", lambda s: (s < 0).mean()])
    daily.columns = ["mean_ret", "n", "loss_share"]
    daily = daily[daily["n"] >= 2]
    if len(daily) < 30:
        return {"status": "INSUFFICIENT_DATA", "n_dates": int(len(daily))}
    loss_days = (daily["loss_share"] > 0.6).mean()
    autocorr = float(daily["mean_ret"].autocorr(lag=1))
    return {
        "status": "COMPLETED",
        "n_dates": int(len(daily)),
        "share_of_days_with_majority_losses": round(float(loss_days), 4),
        "lag1_autocorr_daily_mean": round(autocorr, 4),
        "interpretation": (
            "eligible losses cluster in time (regime-like loss days)"
            if autocorr > 0.2
            else "no strong day-to-day loss clustering in eligible outcomes"
        ),
    }


def exp_s1_effective_sample(df: pd.DataFrame) -> dict:
    """S1: effective sample size under date-block correlation."""
    return {
        "status": "COMPLETED",
        "fwd_5d_all": effective_sample_size(df, "fwd_5d_pct"),
        "fwd_5d_eligible": effective_sample_size(df[df["entry_ok"]], "fwd_5d_pct"),
    }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

EXPERIMENTS = {
    "V0_label_validation": exp_v0_label_validation,
    "R1_backward_vs_forward": exp_r1_backward_vs_forward,
    "R2_reverse_ranking": exp_r2_reverse_ranking,
    "R3_decile_monotonicity": exp_r3_decile_monotonicity,
    "R4_rank_stability": exp_r4_rank_stability,
    "R5_signal_decay": exp_r5_signal_decay,
    "R10_cross_sectional_vs_absolute": exp_r10_cross_sectional,
    "E1_entry_delay": exp_e1_entry_delay,
    "E2_drift_budget": exp_e2_drift_budget,
    "X1_mae_mfe_layer": exp_x1_mae_mfe,
    "X3_mfe_capture": exp_x3_mfe_capture,
    "X6_invalidation_exit": exp_x6_invalidation_exit,
    "G2_regime_calibration": exp_g2_regime_calibration,
    "G4_regime_stratified": exp_g4_regime_stratified,
    "P1_counterfactual_portfolio": exp_p1_counterfactual_portfolio,
    "P2_candidate_correlation": exp_p2_candidate_correlation,
    "P7_loss_clustering": exp_p7_loss_clustering,
    "S1_effective_sample_size": exp_s1_effective_sample,
}


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
            results[name] = fn(enriched)
        except Exception as exc:  # research battery: record, don't crash
            results[name] = {"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}

    artifact = {
        "study": "strategic_lab_2026-08-10",
        "started_utc": started,
        "finished_utc": datetime.now(UTC).isoformat(),
        "input_csv": str(csv_path),
        "rows_after_dedup": int(len(df)),
        "rows_with_cache_metrics": int(enriched["cache_close"].notna().sum()),
        "flagged_symbols_excluded_in_robustness": len(flagged),
        "cost_assumption_pct": COST_PCT,
        "bootstrap_draws": BOOTSTRAP_DRAWS,
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
