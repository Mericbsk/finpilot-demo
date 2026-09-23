"""Direction-context battery — can attention-map direction be conditioned?

Level: A (research-only; no production change; locked OOS NOT_OPENED)
Date: 2026-09-03

PRE-REGISTRATION (written before any result was inspected)
----------------------------------------------------------
Question: attention picks stocks with big moves but no direction. Can context
(regime, sector clustering, opening range) condition the direction?

Split: chronological by scan_date — discovery = first 70% of distinct dates
(<= 2026-06-26), OOS = remainder (> 2026-06-26). Hypotheses are evaluated on
discovery first; a hypothesis is "supported" only if the effect sign
replicates in OOS and the same-date matched-control share_positive >= 0.90.

H1a (regime column): attention ∩ regime=True has higher median c2c_5d and
    positive rate than attention ∩ regime=False.
H1b (breadth regime): same contrast using day-level universe median gap_pct
    (fixed thresholds >= +0.2% up-day, <= -0.2% down-day; fixed => no look-ahead).
H2  (sector cluster): attention stocks in a sector-day cluster (>=3 attention
    stocks sharing the same mapped sector ETF) show (i) within-cluster same-
    direction share > 50% and (ii) different median c2c_5d vs isolated
    attention stocks (sector-day count 1-2).
H3  (opening range, exploratory): among cached intraday days with |gap| >= 3%
    at session start, first-30-minute direction matches rest-of-day direction
    in > 50% of cases. Cache is tiny (880 files, ~1-2 weeks) — hypothesis is
    directional only, no production implication.

Metrics: median c2c_5d, positive rate, |c2c_5d| median; same-date matched
control (100 deterministic draws) for H1/H2 main contrasts.

Usage: python -m research.direction_context_battery_2026_09_03
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
SECTOR_MAP = Path("data/backtest_out/sector_map_full.csv")
INTRADAY = Path("data/intraday_cache")
OUT = Path("data/backtest_out/direction_context_battery_2026-09-03.json")
SPLIT_Q = 0.70


def attention_score(df: pd.DataFrame) -> pd.Series:
    score = (
        (df["gap_pct"].abs() >= 3).astype(int) * 25
        + (df["atr_pct_real"] >= 6).astype(int) * 25
        + (df["rvol"] >= 2.0).astype(int) * 15
        + (df["dist_52w_high"] < 0.3).astype(int) * 15
        + (df["lottery_factor"] >= 0.6).astype(int) * 10
        + (df["squeeze_factor"] >= 0.5).astype(int) * 10
    )
    return score


def load() -> pd.DataFrame:
    df = pd.read_csv(CSV, low_memory=False)
    df = df.drop_duplicates(["symbol", "scan_date"], keep="first")
    df = df[(df["price"] >= 1) & df["c2c_5d"].notna() & (df["c2c_5d"].abs() <= 100)].copy()
    df["att"] = attention_score(df)
    df["abs5"] = df["c2c_5d"].abs()
    return df


def matched_diff_signed(df: pd.DataFrame, mask: pd.Series, value: str = "c2c_5d") -> dict:
    """Same-date random control on the SIGNED metric (direction matters here)."""
    diffs = []
    dates = df.loc[mask, "scan_date"].unique()
    for date in dates:
        s = df[(df["scan_date"] == date) & mask]
        u = df[(df["scan_date"] == date) & ~mask]
        if len(s) == 0 or len(u) < len(s):
            continue
        s_med = s[value].median()
        for _ in range(MATCHED_RUNS):
            rand = u.sample(n=len(s), replace=False, random_state=RNG)
            diffs.append(s_med - rand[value].median())
    arr = np.array(diffs) if diffs else np.array([0.0])
    return {
        "median_diff_pp": round(float(np.median(arr)), 4),
        "share_positive": round(float((arr > 0).mean()), 4),
        "n_comparisons": len(diffs),
    }


def summarize(x: pd.DataFrame) -> dict:
    if len(x) == 0:
        return {"n": 0}
    return {
        "n": int(len(x)),
        "median_5d": round(float(x["c2c_5d"].median()), 3),
        "positive_rate": round(float((x["c2c_5d"] > 0).mean()), 4),
        "abs5_median": round(float(x["abs5"].median()), 3),
    }


def h1_regime(df: pd.DataFrame) -> dict:
    att = df["att"] >= 25
    out = {}
    for label, mask in [
        ("att_regime_true", att & (df["regime"] == True)),  # noqa: E712
        ("att_regime_false", att & (df["regime"] == False)),  # noqa: E712
    ]:
        out[label] = summarize(df[mask])
        out[label]["matched_control_vs_rest"] = matched_diff_signed(df, mask)
    return out


def h1_breadth(df: pd.DataFrame) -> dict:
    day_med = df.groupby("scan_date")["gap_pct"].median()
    up_days = set(day_med[day_med >= 0.2].index)
    down_days = set(day_med[day_med <= -0.2].index)
    att = df["att"] >= 25
    out = {"n_up_days": len(up_days), "n_down_days": len(down_days)}
    for label, mask in [
        ("att_breadth_up", att & df["scan_date"].isin(up_days)),
        ("att_breadth_down", att & df["scan_date"].isin(down_days)),
    ]:
        out[label] = summarize(df[mask])
        out[label]["matched_control_vs_rest"] = matched_diff_signed(df, mask)
    return out


def h2_sector(df: pd.DataFrame) -> dict:
    if not SECTOR_MAP.exists():
        return {"status": "skipped", "reason": "sector_map_full.csv missing"}
    sm = pd.read_csv(SECTOR_MAP)[["symbol", "etf"]].dropna()
    d = df.merge(sm, on="symbol", how="left")
    att = d["att"] >= 25
    cluster_size = d[att].groupby(["scan_date", "etf"])["symbol"].transform("size")
    d.loc[att, "cluster_size"] = cluster_size
    clustered = att & (d["cluster_size"].fillna(0) >= 3)
    isolated = att & d["etf"].notna() & (d["cluster_size"].fillna(0) <= 2)

    # within-cluster same-direction share
    same_dir = []
    cd = d[clustered]
    for (_, _), g in cd.groupby(["scan_date", "etf"]):
        signs = np.sign(g["c2c_5d"].dropna())
        if len(signs) >= 2:
            same_dir.append(float(max((signs > 0).mean(), (signs < 0).mean())))

    return {
        "attention_rows_with_sector": int((att & d["etf"].notna()).sum()),
        "clustered": summarize(d[clustered]),
        "isolated": summarize(d[isolated]),
        "clustered_matched_control": matched_diff_signed(d, clustered),
        "within_cluster_same_direction_share": (
            round(float(np.mean(same_dir)), 4) if same_dir else None
        ),
        "n_clusters": len(same_dir),
    }


def h3_opening_range() -> dict:
    files = sorted(INTRADAY.glob("*.json"))
    rows = []
    for f in files:
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
                continue  # no previous close
            today, prev = by_day[day], by_day[days[i - 1]]
            try:
                day_open = float(today[0][1])
                prev_close = float(prev[-1][4])
                day_close = float(today[-1][4])
            except (IndexError, TypeError, ValueError):
                continue
            if prev_close <= 0:
                continue
            gap = (day_open - prev_close) / prev_close * 100
            if abs(gap) < 3 or len(today) < 4:
                continue
            first30 = float(today[min(1, len(today) - 1)][4])  # 2nd bar close ~30min
            or_dir = np.sign(first30 - day_open)
            rest_dir = np.sign(day_close - first30)
            if or_dir == 0 or rest_dir == 0:
                continue
            rows.append({"day": day, "gap": gap, "match": bool(or_dir == rest_dir)})
    if not rows:
        return {"status": "skipped", "reason": "no qualifying gap days in cache"}
    r = pd.DataFrame(rows)
    return {
        "n_gap_days": int(len(r)),
        "symbols": int(len(files)),
        "opening_range_match_rate": round(float(r["match"].mean()), 4),
        "binomial_note": "exploratory; tiny sample, no OOS split possible",
    }


def main() -> None:
    df = load()
    dates = sorted(df["scan_date"].unique())
    cut = dates[int(len(dates) * SPLIT_Q)]
    discovery = df[df["scan_date"] <= cut].copy()
    oos = df[df["scan_date"] > cut].copy()

    result = {
        "status": "exploratory",
        "production_change": False,
        "locked_oos": "not_opened",
        "split": {"cut_date": cut, "discovery_n": len(discovery), "oos_n": len(oos)},
        "discovery": {
            "h1_regime": h1_regime(discovery),
            "h1_breadth": h1_breadth(discovery),
            "h2_sector": h2_sector(discovery),
        },
        "oos": {
            "h1_regime": h1_regime(oos),
            "h1_breadth": h1_breadth(oos),
            "h2_sector": h2_sector(oos),
        },
        "h3_opening_range": h3_opening_range(),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
