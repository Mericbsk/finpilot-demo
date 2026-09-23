"""Experiment #1 — Market Regime x Attention Tier x Forward Direction matrix.

Level: A (research-only; no production change; locked OOS NOT_OPENED)
Date: 2026-09-03

PRE-REGISTRATION (written before results were inspected)
---------------------------------------------------------
Primary question: does market regime add DIRECTIONAL information on top of
the attention map (which captures move size only)?

Split: chronological by scan_date — discovery = first 70% of distinct dates
(<= 2026-06-26), OOS = remainder. A hypothesis is "supported" only if the
effect sign replicates in OOS and the same-date matched-control
share_positive >= 0.90 for the main signed-return contrast.

H1 (Regime x Tier x Threshold matrix):
    Day regime = universe median gap_pct of that scan_date with FIXED
    thresholds: strong-up >= +0.2%, strong-down <= -0.2%, else neutral
    (no look-ahead; thresholds fixed before inspection).
    Tier = Normal (<25) / Watch (25-49) / High (>=50) from the weighted
    6-flag attention score.
    Outcome bands on c2c_5d: >=+5, [+3,+5), [0,+3), (-3,0), (-5,-3], <-5.
    Hypothesis: within a tier, band distributions shift monotonically with
    regime (strong-up tilts positive, strong-down tilts negative). Tested by
    per-cell positive-rate and median, plus matched control on signed 5d
    return for High-tier cells.

H2 (event-type proxy): catalyst_factor in the canonical CSV is constant 0
    (data gap — real event labels unavailable). Proxy: gap direction.
    gap-up (gap_pct >= +3) vs gap-down (gap_pct <= -3) x tier.
    Hypothesis: gap-up tilts forward returns positive vs gap-down.

H3 (opening-range fade, exploratory — tiny cache, no OOS split possible):
    On gap days (|gap| >= 3%), fade rule: at ~30min mark take the OPPOSITE
    of the first-30min direction, exit at close. Prior battery found only
    39.7% continuation. Hypothesis: fade rule win rate > 50%.
    Limitations stated upfront: 15-min bars, no volume, no spread/cost data,
    ~1-2 weeks only => "tradeable" verdict cannot be made; directional only.

H4 (intraday path, exploratory): at cumulative marks 30/60/120/195 min,
    correlation between move-so-far and rest-of-day move (same day).
    Hypothesis: later marks carry more information (correlation with
    rest-of-day becomes less negative / sign stabilizes).

Usage: python -m research.direction_threshold_matrix_2026_09_03
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(20260903)
MATCHED_RUNS = 100
CSV = Path("data/backtest_out/full_universe_enriched.csv")
INTRADAY = Path("data/intraday_cache")
OUT = Path("data/backtest_out/direction_threshold_matrix_2026-09-03.json")
SPLIT_Q = 0.70
REGIME_UP = 0.2
REGIME_DOWN = -0.2
BANDS = [(-np.inf, -5), (-5, -3), (-3, 0), (0, 3), (3, 5), (5, np.inf)]
BAND_LABELS = ["<-5%", "-5..-3%", "-3..0%", "0..+3%", "+3..+5%", ">=+5%"]


def attention_score(df: pd.DataFrame) -> pd.Series:
    return (
        (df["gap_pct"].abs() >= 3).astype(int) * 25
        + (df["atr_pct_real"] >= 6).astype(int) * 25
        + (df["rvol"] >= 2.0).astype(int) * 15
        + (df["dist_52w_high"] < 0.3).astype(int) * 15
        + (df["lottery_factor"] >= 0.6).astype(int) * 10
        + (df["squeeze_factor"] >= 0.5).astype(int) * 10
    )


def load() -> pd.DataFrame:
    df = pd.read_csv(CSV, low_memory=False)
    df = df.drop_duplicates(["symbol", "scan_date"], keep="first")
    df = df[(df["price"] >= 1) & df["c2c_5d"].notna() & (df["c2c_5d"].abs() <= 100)].copy()
    df["att"] = attention_score(df)
    df["tier"] = pd.cut(df["att"], [-1, 24, 49, 10_000], labels=["Normal", "Watch", "High"])
    day_med = df.groupby("scan_date")["gap_pct"].median()
    regime = day_med.apply(
        lambda v: "strong_up"
        if v >= REGIME_UP
        else ("strong_down" if v <= REGIME_DOWN else "neutral")
    )
    df["mkt_regime"] = df["scan_date"].map(regime)
    return df


def band_shares(x: pd.Series) -> dict:
    out = {}
    for (lo, hi), lbl in zip(BANDS, BAND_LABELS, strict=False):
        out[lbl] = round(float(((x >= lo) & (x < hi)).mean()) * 100, 1) if len(x) else 0.0
    return out


def matched_signed(df: pd.DataFrame, mask: pd.Series) -> dict:
    diffs = []
    for date in df.loc[mask, "scan_date"].unique():
        s = df[(df["scan_date"] == date) & mask]
        u = df[(df["scan_date"] == date) & ~mask]
        if len(s) == 0 or len(u) < len(s):
            continue
        s_med = s["c2c_5d"].median()
        for _ in range(MATCHED_RUNS):
            diffs.append(
                s_med - u.sample(n=len(s), replace=False, random_state=RNG)["c2c_5d"].median()
            )
    arr = np.array(diffs) if diffs else np.array([0.0])
    return {
        "median_diff_pp": round(float(np.median(arr)), 3),
        "share_positive": round(float((arr > 0).mean()), 3),
        "n_comparisons": int(len(diffs)),
    }


def h1_matrix(df: pd.DataFrame) -> dict:
    matrix = {}
    for reg in ["strong_up", "neutral", "strong_down"]:
        matrix[reg] = {}
        for tier in ["Normal", "Watch", "High"]:
            x = df[(df["mkt_regime"] == reg) & (df["tier"] == tier)]["c2c_5d"]
            cell = {"n": int(len(x))}
            if len(x) >= 30:
                cell.update(
                    {
                        "median_5d": round(float(x.median()), 3),
                        "positive_rate": round(float((x > 0).mean()) * 100, 1),
                        "bands_pct": band_shares(x),
                    }
                )
            matrix[reg][tier] = cell
    # matched control: High tier per regime (signed)
    mc = {}
    for reg in ["strong_up", "neutral", "strong_down"]:
        mask = (df["mkt_regime"] == reg) & (df["tier"] == "High")
        if mask.sum() >= 30:
            mc[reg] = matched_signed(df, mask)
    return {"matrix": matrix, "matched_control_high_tier": mc}


def h2_event_proxy(df: pd.DataFrame) -> dict:
    out = {}
    for lbl, m in [("gap_up", df["gap_pct"] >= 3), ("gap_down", df["gap_pct"] <= -3)]:
        sub = {}
        for tier in ["Normal", "Watch", "High"]:
            x = df[m & (df["tier"] == tier)]["c2c_5d"]
            if len(x) >= 30:
                sub[tier] = {
                    "n": int(len(x)),
                    "median_5d": round(float(x.median()), 3),
                    "positive_rate": round(float((x > 0).mean()) * 100, 1),
                    "bands_pct": band_shares(x),
                }
            else:
                sub[tier] = {"n": int(len(x))}
        out[lbl] = sub
    out["gap_up_matched"] = matched_signed(df, df["gap_pct"] >= 3)
    out["gap_down_matched"] = matched_signed(df, df["gap_pct"] <= -3)
    return out


def _iter_gap_days():
    for f in sorted(INTRADAY.glob("*.json")):
        try:
            bars = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(bars, list) or len(bars) < 10:
            continue
        by_day: dict[str, list] = defaultdict(list)
        for b in bars:
            try:
                by_day[str(b[0])[:10]].append(b)
            except (IndexError, TypeError):
                continue
        days = sorted(by_day)
        for i, day in enumerate(days):
            if i == 0:
                continue
            today, prev = by_day[day], by_day[days[i - 1]]
            try:
                day_open, prev_close, day_close = (
                    float(today[0][1]),
                    float(prev[-1][4]),
                    float(today[-1][4]),
                )
            except (IndexError, TypeError, ValueError):
                continue
            if prev_close <= 0:
                continue
            gap = (day_open - prev_close) / prev_close * 100
            if abs(gap) < 3 or len(today) < 6:
                continue
            yield day, today, day_open, day_close, gap


def h3_fade() -> dict:
    rets, wins = [], 0
    for _, today, day_open, day_close, _gap in _iter_gap_days():
        mark30 = float(today[min(1, len(today) - 1)][4])
        first_dir = np.sign(mark30 - day_open)
        if first_dir == 0:
            continue
        fade_ret = (day_close - mark30) / mark30 * 100 * (-first_dir)
        rets.append(fade_ret)
        wins += fade_ret > 0
    if not rets:
        return {"status": "skipped"}
    r = pd.Series(rets)
    return {
        "n": int(len(r)),
        "win_rate": round(wins / len(r), 4),
        "mean_pct": round(float(r.mean()), 3),
        "median_pct": round(float(r.median()), 3),
        "note": "gross of spread/costs/slippage; 15-min bars; tiny sample — NOT a tradeable verdict",
    }


def h4_path() -> dict:
    marks = [1, 3, 7, 12]  # ~30/60/120/195 min at 15-min bars
    buckets: dict[int, list[tuple[float, float]]] = {m: [] for m in marks}
    for _, today, day_open, day_close, _ in _iter_gap_days():
        for m in marks:
            if len(today) <= m:
                continue
            px = float(today[m][4])
            so_far = (px - day_open) / day_open * 100
            rest = (day_close - px) / px * 100
            buckets[m].append((so_far, rest))
    out = {}
    for m, pairs in buckets.items():
        if len(pairs) < 30:
            continue
        a = pd.DataFrame(pairs, columns=["so_far", "rest"])
        out[f"~{m * 15 + 15}min"] = {
            "n": int(len(a)),
            "corr_so_far_vs_rest": round(float(a["so_far"].corr(a["rest"])), 3),
            "same_sign_rate": round(float((np.sign(a["so_far"]) == np.sign(a["rest"])).mean()), 3),
        }
    return out


def main() -> None:
    df = load()
    dates = sorted(df["scan_date"].unique())
    cut = dates[int(len(dates) * SPLIT_Q)]
    disc, oos = df[df["scan_date"] <= cut].copy(), df[df["scan_date"] > cut].copy()
    day_counts = df.groupby("mkt_regime")["scan_date"].nunique().to_dict()

    result = {
        "status": "exploratory",
        "production_change": False,
        "locked_oos": "not_opened",
        "split": {"cut_date": cut, "discovery_n": len(disc), "oos_n": len(oos)},
        "regime_day_counts_total": day_counts,
        "discovery": {"h1": h1_matrix(disc), "h2": h2_event_proxy(disc)},
        "oos": {"h1": h1_matrix(oos), "h2": h2_event_proxy(oos)},
        "h3_opening_range_fade": h3_fade(),
        "h4_intraday_path": h4_path(),
        "catalyst_factor_note": "catalyst_factor is constant 0.0 in canonical CSV (48,188 non-null, all zero) — real event labels unavailable; H2 uses gap-direction proxy only",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
