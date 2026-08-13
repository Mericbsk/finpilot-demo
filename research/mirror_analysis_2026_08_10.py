#!/usr/bin/env python3
"""Mirror-thesis deep analysis (research-only, Level A).

The 2026-08-10 batteries produced five findings consistent with one claim:

    "The score is not a predictor; it is a mirror of what already happened."

This battery decomposes that claim into a causal chain and tests each link
separately, then tries to break the thesis with alternative explanations.

Chain under test:
  L1  score encodes extension (dist_52w_high, past returns)        [Q3]
  L2  extension predicts short-horizon reversal (mirror -> fade)   [M2]
  L3  therefore high score -> worse forward return (sign flip)     [R1/R2]
  L4  the effect is mechanical (score ~= past), not informational  [R1/R4]

Alternative explanations to attack:
  A1  it's just data artifacts (flagged symbols drive it)
  A2  it's just a few bad days (regime concentration)
  A3  it's the selection layer, not the score (entry_ok vs score)
  A4  it's horizon-specific (only 5d; other horizons differ)
  A5  it's a size/liquidity proxy (score ~ illiquid movers)

Every test reports a status; nothing here is a production decision.
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
    compute_path_metrics,
    dist_summary,
    load_export,
    load_flagged_symbols,
)

DEFAULT_OUT = Path("data/backtest_out/mirror_analysis_2026-08-10.json")
SEED = 20260810


def _sp(x: pd.Series, y: pd.Series) -> float | None:
    sub = pd.concat([x, y], axis=1).dropna()
    if len(sub) < 100:
        return None
    return round(float(spearmanr(sub.iloc[:, 0], sub.iloc[:, 1]).statistic), 4)


def _partial_spearman(x: pd.Series, y: pd.Series, controls: list[pd.Series]) -> float | None:
    """Spearman of x and y after rank-residualizing both on the controls."""
    cols = pd.concat([x, y] + controls, axis=1).dropna()
    if len(cols) < 200:
        return None
    xr = cols.iloc[:, 0].rank()
    yr = cols.iloc[:, 1].rank()
    Z = cols.iloc[:, 2:].rank().to_numpy()
    Z = np.column_stack([np.ones(len(Z)), Z])
    bx = np.linalg.lstsq(Z, xr.to_numpy(), rcond=None)[0]
    by = np.linalg.lstsq(Z, yr.to_numpy(), rcond=None)[0]
    rx = xr.to_numpy() - Z @ bx
    ry = yr.to_numpy() - Z @ by
    return round(float(spearmanr(rx, ry).statistic), 4)


# ---------------------------------------------------------------------------
# L1: what the score encodes (extension vs everything else)
# ---------------------------------------------------------------------------


def exp_l1_encoding(df: pd.DataFrame) -> dict:
    sub = df.dropna(subset=["finpilot_score"])
    features = [
        "dist_52w_high",
        "past_5d_pct",
        "gap_pct",
        "rvol",
        "atr_pct_real",
        "squeeze_factor",
        "lottery_factor",
        "overnight_gap_factor",
    ]
    enc = {f: _sp(sub["finpilot_score"], sub[f]) for f in features}
    enc = {k: v for k, v in enc.items() if v is not None}
    # How much of the score is just dist_52w_high + past_5d?
    sub2 = sub.dropna(subset=["dist_52w_high", "past_5d_pct"])
    if len(sub2) > 500:
        Z = sub2[["dist_52w_high", "past_5d_pct"]].rank().to_numpy()
        Z = np.column_stack([np.ones(len(Z)), Z])
        y = sub2["finpilot_score"].rank().to_numpy()
        beta = np.linalg.lstsq(Z, y, rcond=None)[0]
        resid = y - Z @ beta
        r2 = 1 - float(resid.var() / y.var())
    else:
        r2 = None
    return {
        "status": "COMPLETED",
        "n": int(len(sub)),
        "encodes": dict(sorted(enc.items(), key=lambda kv: -abs(kv[1]))),
        "rank_r2_from_extension_alone": round(r2, 4) if r2 is not None else None,
        "interpretation": (
            "extension (52w-high distance + past 5d) explains most of the score's rank"
            if r2 is not None and r2 > 0.5
            else "extension alone does not dominate the score's rank"
        ),
    }


# ---------------------------------------------------------------------------
# L2: extension -> reversal (the mirror's mechanical consequence)
# ---------------------------------------------------------------------------


def exp_l2_extension_reversal(df: pd.DataFrame) -> dict:
    sub = df.dropna(subset=["dist_52w_high", "fwd_5d_pct"]).copy()
    if len(sub) < 2000:
        return {"status": "INSUFFICIENT_DATA"}
    sub["ext_q"] = pd.qcut(
        sub["dist_52w_high"], 5, labels=["q1_near_high", "q2", "q3", "q4", "q5_far"]
    )
    cells = {str(k): dist_summary(g["fwd_5d_pct"]) for k, g in sub.groupby("ext_q", observed=True)}
    rho = _sp(sub["dist_52w_high"], sub["fwd_5d_pct"])
    # Same for past_5d
    sub2 = df.dropna(subset=["past_5d_pct", "fwd_5d_pct"]).copy()
    sub2["past_q"] = pd.qcut(
        sub2["past_5d_pct"], 5, labels=["q1_fell", "q2", "q3", "q4", "q5_ripped"]
    )
    cells2 = {
        str(k): dist_summary(g["fwd_5d_pct"]) for k, g in sub2.groupby("past_q", observed=True)
    }
    rho2 = _sp(sub2["past_5d_pct"], sub2["fwd_5d_pct"])
    return {
        "status": "COMPLETED",
        "dist_52w_high": {"quintiles": cells, "spearman_vs_fwd": rho},
        "past_5d": {"quintiles": cells2, "spearman_vs_fwd": rho2},
        "interpretation": (
            "extension is associated with forward underperformance (reversal)"
            if (rho is not None and rho < -0.02) or (rho2 is not None and rho2 < -0.02)
            else "no clean extension->reversal gradient at 5d"
        ),
    }


# ---------------------------------------------------------------------------
# L3: does the score add anything beyond extension? (the key falsification)
# ---------------------------------------------------------------------------


def exp_l3_score_beyond_extension(df: pd.DataFrame) -> dict:
    sub = df.dropna(subset=["finpilot_score", "fwd_5d_pct", "dist_52w_high", "past_5d_pct"])
    if len(sub) < 1000:
        return {"status": "INSUFFICIENT_DATA"}
    raw = _sp(sub["finpilot_score"], sub["fwd_5d_pct"])
    partial = _partial_spearman(
        sub["finpilot_score"],
        sub["fwd_5d_pct"],
        [sub["dist_52w_high"], sub["past_5d_pct"]],
    )
    return {
        "status": "COMPLETED",
        "n": int(len(sub)),
        "spearman_score_raw": raw,
        "spearman_score_given_extension": partial,
        "interpretation": (
            "the score adds NOTHING beyond extension once extension is controlled"
            if partial is not None and abs(partial) < 0.02
            else "the score carries extension-independent information"
        ),
    }


# ---------------------------------------------------------------------------
# L4: is it the score or the selection layer?
# ---------------------------------------------------------------------------


def exp_l4_score_vs_selection(df: pd.DataFrame) -> dict:
    sub = df.dropna(subset=["finpilot_score", "fwd_5d_pct"])
    if len(sub) < 1000:
        return {"status": "INSUFFICIENT_DATA"}
    # Within the score's top quintile only, does entry_ok still matter?
    sub = sub.copy()
    sub["score_q"] = pd.qcut(sub["finpilot_score"], 5, labels=False, duplicates="drop")
    top = sub[sub["score_q"] == sub["score_q"].max()]
    elig = top[top["entry_ok"]]["fwd_5d_pct"]
    nonelig = top[~top["entry_ok"]]["fwd_5d_pct"]
    # And across the whole set: score quintile x entry_ok
    grid = {}
    for q, g in sub.groupby("score_q"):
        grid[f"q{int(q)}"] = {
            "eligible": dist_summary(g[g["entry_ok"]]["fwd_5d_pct"]),
            "not_eligible": dist_summary(g[~g["entry_ok"]]["fwd_5d_pct"]),
        }
    return {
        "status": "COMPLETED",
        "top_quintile": {
            "eligible": dist_summary(elig),
            "not_eligible": dist_summary(nonelig),
        },
        "grid": grid,
        "interpretation": (
            "within the top score quintile, eligibility still separates outcomes"
            if (dist_summary(elig)["median"] or 0) - (dist_summary(nonelig)["median"] or 0) > 0.2
            else "within a score band, eligibility adds little — the score band itself drives the outcome"
        ),
    }


# ---------------------------------------------------------------------------
# A1: is it just the flagged (data-artifact) symbols?
# ---------------------------------------------------------------------------


def exp_a1_artifact_robustness(df: pd.DataFrame) -> dict:
    flagged = df.attrs.get("flagged", set())
    clean = df[~df["symbol"].isin(flagged)]
    dirty = df[df["symbol"].isin(flagged)]
    out = {"status": "COMPLETED", "flagged_n_symbols": len(flagged)}
    for name, frame in (("clean", clean), ("dirty", dirty)):
        sub = frame.dropna(subset=["finpilot_score", "fwd_5d_pct", "past_5d_pct"])
        if len(sub) < 200:
            out[name] = {"status": "INSUFFICIENT_DATA", "n": int(len(sub))}
            continue
        out[name] = {
            "n": int(len(sub)),
            "spearman_score_vs_past": _sp(sub["finpilot_score"], sub["past_5d_pct"]),
            "spearman_score_vs_fwd": _sp(sub["finpilot_score"], sub["fwd_5d_pct"]),
        }
    out["interpretation"] = (
        "mirror pattern holds on clean symbols too -> not a data artifact"
        if isinstance(out.get("clean"), dict)
        and (out["clean"].get("spearman_score_vs_past") or 0)
        > abs(out["clean"].get("spearman_score_vs_fwd") or 0)
        else "mirror pattern weakens on clean symbols -> artifact contribution possible"
    )
    return out


# ---------------------------------------------------------------------------
# A2: is it a few bad days? (day-level distribution of the score->fwd link)
# ---------------------------------------------------------------------------


def exp_a2_day_concentration(df: pd.DataFrame) -> dict:
    sub = df.dropna(subset=["finpilot_score", "fwd_5d_pct"])
    per_day = []
    for date, g in sub.groupby("scan_date"):
        if len(g) < 50:
            continue
        rho = _sp(g["finpilot_score"], g["fwd_5d_pct"])
        if rho is not None:
            per_day.append(rho)
    if len(per_day) < 20:
        return {"status": "INSUFFICIENT_DATA", "n_days": len(per_day)}
    arr = np.array(per_day)
    return {
        "status": "COMPLETED",
        "n_days": int(len(arr)),
        "daily_score_fwd_spearman": dist_summary(arr),
        "share_days_negative": round(float((arr < 0).mean()), 4),
        "interpretation": (
            "the score->forward link is near zero/negative on MOST days, not driven by a few"
            if (arr < 0.05).mean() > 0.6
            else "the score->forward link varies a lot by day (regime concentration possible)"
        ),
    }


# ---------------------------------------------------------------------------
# A4: horizon dependence of the mirror
# ---------------------------------------------------------------------------


def exp_a4_horizon_dependence(df: pd.DataFrame) -> dict:
    sub = df.dropna(subset=["finpilot_score"])
    out = {"status": "COMPLETED", "by_horizon": {}}
    for h in (1, 2, 3, 5, 10):
        col = f"fwd_{h}d_pct"
        s = sub.dropna(subset=[col])
        if len(s) < 500:
            out["by_horizon"][str(h)] = {"status": "INSUFFICIENT_DATA"}
            continue
        out["by_horizon"][str(h)] = {
            "n": int(len(s)),
            "spearman_score_vs_fwd": _sp(s["finpilot_score"], s[col]),
            "spearman_past5d_vs_fwd": _sp(s["past_5d_pct"], s[col]) if "past_5d_pct" in s else None,
        }
    return out


# ---------------------------------------------------------------------------
# A5: is the score just a liquidity/size proxy?
# ---------------------------------------------------------------------------


def exp_a5_liquidity_proxy(df: pd.DataFrame) -> dict:
    sub = df.dropna(subset=["finpilot_score", "rvol", "atr_pct_real"])
    out = {
        "status": "COMPLETED",
        "spearman_score_vs_rvol": _sp(sub["finpilot_score"], sub["rvol"]),
        "spearman_score_vs_atr_pct": _sp(sub["finpilot_score"], sub["atr_pct_real"]),
    }
    # Does the score->fwd link survive controlling for rvol + atr (vol/liquidity)?
    sub2 = df.dropna(subset=["finpilot_score", "fwd_5d_pct", "rvol", "atr_pct_real"])
    out["spearman_score_given_vol_liquidity"] = _partial_spearman(
        sub2["finpilot_score"], sub2["fwd_5d_pct"], [sub2["rvol"], sub2["atr_pct_real"]]
    )
    out["interpretation"] = (
        "the mirror is not explained away by volume/volatility proxies"
        if out["spearman_score_given_vol_liquidity"] is not None
        and abs(out["spearman_score_given_vol_liquidity"]) < 0.05
        else "volume/volatility partially explains the score's (non-)information"
    )
    return out


# ---------------------------------------------------------------------------
# Synthesis: what SHOULD the score be if it is a mirror?
# ---------------------------------------------------------------------------


def exp_synthesis_mirror_vs_forward(df: pd.DataFrame) -> dict:
    """Directly compare: score-as-mirror vs a trivial forward-looking baseline.

    Baseline: negative of extension (fade the mirror). If the mirror thesis is
    right, -extension should beat +score on forward return.
    """
    sub = df.dropna(subset=["finpilot_score", "dist_52w_high", "fwd_5d_pct"]).copy()
    if len(sub) < 1000:
        return {"status": "INSUFFICIENT_DATA"}
    sub["fade"] = -sub["dist_52w_high"]
    rho_score = _sp(sub["finpilot_score"], sub["fwd_5d_pct"])
    rho_fade = _sp(sub["fade"], sub["fwd_5d_pct"])
    # Top-decile comparison
    sub["score_dec"] = pd.qcut(sub["finpilot_score"], 10, labels=False, duplicates="drop")
    sub["fade_dec"] = pd.qcut(sub["fade"], 10, labels=False, duplicates="drop")
    top_score = sub[sub["score_dec"] == sub["score_dec"].max()]["fwd_5d_pct"]
    top_fade = sub[sub["fade_dec"] == sub["fade_dec"].max()]["fwd_5d_pct"]
    return {
        "status": "COMPLETED",
        "n": int(len(sub)),
        "spearman_score": rho_score,
        "spearman_fade_the_mirror": rho_fade,
        "top_decile_score": dist_summary(top_score),
        "top_decile_fade": dist_summary(top_fade),
        "interpretation": (
            "fading the mirror beats following it -> the score's sign is inverted"
            if (rho_fade or 0) > (rho_score or 0)
            else "following the score beats fading it"
        ),
    }


EXPERIMENTS = {
    "L1_score_encoding": exp_l1_encoding,
    "L2_extension_reversal": exp_l2_extension_reversal,
    "L3_score_beyond_extension": exp_l3_score_beyond_extension,
    "L4_score_vs_selection": exp_l4_score_vs_selection,
    "A1_artifact_robustness": exp_a1_artifact_robustness,
    "A2_day_concentration": exp_a2_day_concentration,
    "A4_horizon_dependence": exp_a4_horizon_dependence,
    "A5_liquidity_proxy": exp_a5_liquidity_proxy,
    "SYNTH_mirror_vs_forward": exp_synthesis_mirror_vs_forward,
}


def run_battery(
    csv_path: Path = DEFAULT_CSV,
    cache_dir: Path = DEFAULT_CACHE,
    audit_path: Path = DEFAULT_AUDIT,
    out_path: Path = DEFAULT_OUT,
) -> dict:
    started = datetime.now(UTC).isoformat()
    df = load_export(csv_path)
    df.attrs["flagged"] = load_flagged_symbols(audit_path)
    enriched = compute_path_metrics(df, cache_dir)

    results = {}
    for name, fn in EXPERIMENTS.items():
        try:
            results[name] = fn(enriched)
        except Exception as exc:
            results[name] = {"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}

    artifact = {
        "study": "mirror_analysis_2026-08-10",
        "started_utc": started,
        "finished_utc": datetime.now(UTC).isoformat(),
        "input_csv": str(csv_path),
        "rows_after_dedup": int(len(df)),
        "seed": SEED,
        "scope": "research-only diagnostic; no production decision",
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
