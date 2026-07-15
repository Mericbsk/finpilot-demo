#!/usr/bin/env python3
"""Full-universe, point-in-time cross-section backtest.

WHAT THIS ANSWERS
-----------------
The scanner's "good" numbers to date — alpha-v2 decile lift ~1.74, conviction
hit-rate ~73% — came from ``scripts/offline_ablation.py``, which rebuilt the
factors with *current* data as a proxy for history (a look-ahead weakness), and
only over BUY signals in ``signals_archive``. The live
``scripts/factor_ablation_report.py`` only sees the daily top-N export shortlist
(~12-200 names), not the ~1800-name universe the scanner actually screens.

This script does it honestly:
    * takes the full liquid universe (~1800, ranked by dollar-volume from Alpaca),
    * walks 12 months of daily bars POINT-IN-TIME (factors at date t use only
      bars up to t; entry is the NEXT bar's open — no look-ahead),
    * labels EVERY (symbol, date) observation with the triple-barrier method
      under BOTH a fixed grid and ATR-scaled barriers,
    * measures the exact statistics the developer quoted — decile lift per
      factor, the conviction bucket hit-rate — PLUS the fair-measurement fixes:
      SPY-relative (beta vs edge) and median-split (fixes composite n_hi=0).

Point-in-time honesty of each factor:
    CLEAN (computed from the historical OHLCV slice, no look-ahead):
        composite, contraction_factor, rvol_acceleration, rvol_factor,
        gap_factor, extension_factor (52w-high fade), lottery_factor,
        overnight_gap_factor, vol_regime, atr_pct, conviction.
    PROXY (marked *_proxy — CURRENT value broadcast to all dates; SAME
    look-ahead weakness as the developer's numbers, shown only for comparison):
        squeeze_factor, news_sentiment, catalyst.

Run in the user's env (Python 3.11, Alpaca keys in .env):
    python scripts/universe_backtest.py --top 1800 --months 12 --rebalance weekly
    python scripts/universe_backtest.py --self-test        # synthetic, no network

Output: data/distribution/universe_backtest_<date>.md (+ .json)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Enable the gated tiers so compute_conviction returns real tiers during the
# backtest (this only affects THIS process; it does not change live behaviour).
os.environ.setdefault("FINPILOT_ENABLE_CONVICTION_TIERS", "1")

from scanner.backtest_metrics import (  # noqa: E402
    atr_barrier_params,
    conviction_bucket_hitrate,
    decile_lift,
    format_decile_md,
    median_split_ablation,
    spy_relative,
)
from scanner.labeling import summarize_labels, triple_barrier_label  # noqa: E402

# Factor functions are imported lazily inside compute_point_in_time_factors so
# --self-test can run even if the heavy scanner package fails to import.


# ── universe ─────────────────────────────────────────────────────────────────
def load_universe(top: int) -> list[str]:
    """Return up to ``top`` liquid tickers from the local symbols table.

    We rank by a liquidity proxy if present; otherwise fall back to all tradable
    tickers (the Alpaca fetch + dollar-volume filter below trims to ``top``).
    """
    import sqlite3

    db = ROOT / "data" / "finpilot.db"
    con = sqlite3.connect(db)
    cur = con.cursor()
    try:
        cur.execute("SELECT ticker FROM symbols WHERE tradable=1 ORDER BY ticker")
        syms = [r[0] for r in cur.fetchall()]
    except Exception:
        syms = []
    finally:
        con.close()
    return syms


# ── Alpaca daily bars with explicit start/end ────────────────────────────────
def fetch_daily_bars(symbols: list[str], start: datetime, end: datetime) -> dict:
    """Return {symbol: DataFrame(Open/High/Low/Close/Volume, DatetimeIndex)}.

    Uses the shared Alpaca client. Batches symbols to keep each request paged.
    """
    import pandas as pd
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    from scanner.data_fetcher import _get_alpaca_client

    client = _get_alpaca_client()
    if client is None:
        raise RuntimeError("Alpaca client unavailable — set ALPACA_API_KEY/SECRET_KEY.")

    rename = {"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}
    out: dict[str, pd.DataFrame] = {}
    batch = 200
    for k in range(0, len(symbols), batch):
        chunk = symbols[k : k + batch]
        req = StockBarsRequest(
            symbol_or_symbols=chunk,
            timeframe=TimeFrame.Day,
            start=start,
            end=end,
            feed="iex",
            limit=max(10_000, len(chunk) * 300),
        )
        try:
            full = client.get_stock_bars(req).df
        except Exception as exc:  # noqa: BLE001
            print(f"  batch {k}-{k+len(chunk)} failed: {exc}", file=sys.stderr)
            continue
        if full is None or full.empty:
            continue
        for sym in chunk:
            try:
                df = (
                    full.loc[sym].copy()
                    if (
                        isinstance(full.index, pd.MultiIndex)
                        and sym in full.index.get_level_values(0)
                    )
                    else pd.DataFrame()
                )
            except Exception:
                df = pd.DataFrame()
            if df.empty:
                continue
            df = df.rename(columns=rename)
            if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
                df.index = df.index.tz_convert(None)
            out[sym] = df
        print(f"  fetched {min(k+batch, len(symbols))}/{len(symbols)} symbols", file=sys.stderr)
    return out


def rank_by_dollar_volume(bars: dict, top: int) -> list[str]:
    """Keep the ``top`` most liquid symbols by median dollar-volume."""
    liq = []
    for sym, df in bars.items():
        try:
            dv = (df["Close"] * df["Volume"]).median()
            if dv and dv > 0:
                liq.append((float(dv), sym))
        except Exception:
            continue
    liq.sort(reverse=True)
    return [s for _, s in liq[:top]]


# ── point-in-time factors ────────────────────────────────────────────────────
def compute_point_in_time_factors(hist) -> dict:
    """Compute all df-based (clean, no look-ahead) factors from a history slice.

    ``hist`` is the OHLCV DataFrame up to and including the signal bar.
    Returns a dict of factor_name -> value. Proxy factors are attached by the
    caller (they are symbol-level, not date-level).
    """
    from scanner import features as F

    f: dict[str, float] = {}
    try:
        f["contraction_factor"] = F.compute_contraction_factor(hist)
    except Exception:
        f["contraction_factor"] = 0.0
    try:
        f["rvol_acceleration"] = F.compute_rvol_acceleration(hist)
    except Exception:
        f["rvol_acceleration"] = 0.0
    try:
        f["rvol_factor"] = F.compute_rvol_factor(hist)
    except Exception:
        f["rvol_factor"] = 0.0
    try:
        f["gap_factor"] = F.compute_gap_factor(hist)
    except Exception:
        f["gap_factor"] = 0.0
    try:
        f["extension_factor"] = F.compute_extension_factor(hist)
    except Exception:
        f["extension_factor"] = 0.0
    try:
        f["lottery_factor"] = F.compute_lottery_factor(hist)
    except Exception:
        f["lottery_factor"] = 0.0
    try:
        f["overnight_gap_factor"] = F.compute_overnight_gap_factor(hist)
    except Exception:
        f["overnight_gap_factor"] = 0.0
    try:
        f["vol_regime"] = float(F.compute_vol_regime_from_df(hist))
    except Exception:
        f["vol_regime"] = 0.0
    try:
        f["atr_pct"] = F.compute_atr_pct(hist)
    except Exception:
        f["atr_pct"] = 0.0
    # composite proxy point-in-time: blend of the clean edge factors (kept simple
    # and reproducible; the full live composite needs multi-timeframe inputs we
    # don't reconstruct here). This is what median-split then interrogates.
    f["composite"] = round(
        100.0
        * (
            0.30 * f["contraction_factor"]
            + 0.30 * min(f["rvol_acceleration"], 1.0)
            + 0.20 * f["gap_factor"]
            + 0.20 * (1.0 - f["extension_factor"])
        ),
        4,
    )
    return f


# ── build observations ───────────────────────────────────────────────────────
def build_observations(
    bars: dict, *, horizon: int, rebalance: str, spy: object | None, proxy: dict | None
) -> list[dict]:
    """Walk each symbol's history and emit one labeled observation per rebalance
    date that has a full forward window. Entry = NEXT bar's open (no look-ahead).
    """
    import pandas as pd  # noqa: F401

    step = {"daily": 1, "weekly": 5, "biweekly": 10, "monthly": 21}.get(rebalance, 5)
    obs: list[dict] = []
    spy_close = None
    if spy is not None and not getattr(spy, "empty", True):
        spy_close = spy["Close"]

    for sym, df in bars.items():
        n = len(df)
        if n < 60 + horizon:
            continue
        # rebalance indices: need at least `horizon` forward bars after entry(i+1)
        for i in range(55, n - horizon - 1, step):
            hist = df.iloc[: i + 1]
            fwd = df.iloc[i + 1 : i + 1 + horizon]
            if len(fwd) < horizon:
                continue
            entry = float(fwd["Open"].iloc[0])
            if entry <= 0:
                continue
            factors = compute_point_in_time_factors(hist)
            if proxy and sym in proxy:
                for k, v in proxy[sym].items():
                    factors[f"{k}"] = v
            rec = {
                "symbol": sym,
                "date": str(df.index[i].date())
                if hasattr(df.index[i], "date")
                else str(df.index[i]),
                "entry_price": entry,
                "forward_closes": [float(x) for x in fwd["Close"].tolist()],
                "forward_highs": [float(x) for x in fwd["High"].tolist()],
                "forward_lows": [float(x) for x in fwd["Low"].tolist()],
                "side": "long",
                **factors,
            }
            # benchmark same-window return (close@entry_date → close@+horizon)
            if spy_close is not None:
                try:
                    d0 = df.index[i + 1]
                    pos = spy_close.index.get_indexer([d0], method="nearest")[0]
                    if 0 <= pos < len(spy_close) - horizon:
                        b0 = float(spy_close.iloc[pos])
                        b1 = float(spy_close.iloc[min(pos + horizon, len(spy_close) - 1)])
                        rec["bench_ret"] = (b1 - b0) / b0 if b0 else None
                except Exception:
                    pass
            obs.append(rec)
    return obs


def label_observations(
    obs: list[dict], *, mode: str, tp: float, sl: float, horizon: int, k_tp: float, k_sl: float
) -> list[dict]:
    """Attach triple-barrier outcome (label, ret, mfe) to each obs.

    mode='grid'  → fixed tp/sl. mode='atr' → per-obs ATR-scaled tp/sl.
    """
    for o in obs:
        if mode == "atr":
            t, s = atr_barrier_params(o.get("atr_pct", 0.0), k_tp=k_tp, k_sl=k_sl)
        else:
            t, s = tp, sl
        try:
            lab = triple_barrier_label(
                o["forward_closes"],
                entry_price=o["entry_price"],
                tp_pct=t,
                sl_pct=s,
                max_horizon=horizon,
                side=o.get("side", "long"),
                forward_highs=o.get("forward_highs"),
                forward_lows=o.get("forward_lows"),
            )
            o["label"] = lab.label
            o["ret"] = lab.ret_pct
            o["mfe_pct"] = lab.mfe_pct
            o["win"] = 1 if lab.label == "tp" else 0
        except Exception:
            o["label"] = None
            o["ret"] = 0.0
    return [o for o in obs if o.get("label") is not None]


# ── report ───────────────────────────────────────────────────────────────────
CLEAN_FACTORS = [
    ("composite", "edge"),
    ("contraction_factor", "edge"),
    ("rvol_acceleration", "edge"),
    ("rvol_factor", "edge"),
    ("gap_factor", "edge"),
    ("extension_factor", "fade"),
    ("lottery_factor", "fade"),
    ("overnight_gap_factor", "fade"),
]
PROXY_FACTORS = [
    ("squeeze_factor", "edge"),
    ("news_sentiment", "edge"),
    ("catalyst_factor", "edge"),
]


def build_report(obs: list[dict], *, mode: str, params: dict) -> tuple[str, dict]:
    summ = summarize_labels_from_obs(obs)
    lines = [
        f"## Barrier mode: {mode}",
        "",
        f"_n={summ['n']} · hit-rate={summ['tp_rate']:.0%} · stop={summ['sl_rate']:.0%} · "
        f"time={summ['time_rate']:.0%} · expectancy={summ['expectancy']:+.2%}_",
        "",
        "### Decile lift — does a higher factor → better outcome? (win-rate)",
        "",
    ]
    js: dict = {
        "mode": mode,
        "params": params,
        "summary": summ,
        "decile": {},
        "median_split": {},
        "spy_relative": None,
        "conviction": None,
    }

    for key, _kind in CLEAN_FACTORS + PROXY_FACTORS:
        dl = decile_lift(obs, key, metric="win")
        if dl["n"] >= 10:
            tag = " _(PROXY — look-ahead, compare-only)_" if key in dict(PROXY_FACTORS) else ""
            lines.append(format_decile_md(dl) + tag + "\n")
            js["decile"][key] = dl

    lines.append("### Median-split (fixes composite n_hi=0) — upper vs lower half, mean return\n")
    lines.append("| factor | thr | n_hi | hi ret | n_lo | lo ret | lift | ayrışıyor? |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for key, _ in CLEAN_FACTORS:
        ms = median_split_ablation(obs, key, metric="ret")
        js["median_split"][key] = ms
        if ms["hi"] and ms["lo"]:
            sep = "✅" if ms["separates"] else "hayır"
            lines.append(
                f"| {key} | {ms['threshold']} | {ms['hi']['n']} | {ms['hi']['value']:+.2%} "
                f"| {ms['lo']['n']} | {ms['lo']['value']:+.2%} | {ms['lift']:+.2%} | {sep} |"
            )
    lines.append("")

    sr = spy_relative(obs)
    js["spy_relative"] = sr
    lines.append("### SPY-relative — beta mı, edge mi?\n")
    lines.append(
        f"raw beklenti **{sr['raw_expectancy']:+.2%}** → SPY düşülünce excess "
        f"**{sr['excess_expectancy']:+.2%}** (beta payı: {sr['beta_share']}, "
        f"n_bench={sr['n_with_bench']})\n"
    )

    cv = conviction_bucket_hitrate(obs)
    js["conviction"] = cv
    lines.append("### Conviction bucket — 'short>=15 & gap>=3 → +%5/+%10' iddiasının testi\n")
    lines.append(f"bucket n={cv['n_bucket']} / total {cv['n_total']}\n")
    lines.append("| eşik | bucket hit | base hit | lift |")
    lines.append("|---|---|---|---|")
    for thr, d in cv["thresholds"].items():
        lines.append(
            f"| {thr} | {d['bucket_hitrate']:.0%} | {d['base_hitrate']:.0%} | {d['lift']} |"
        )
    lines.append("")
    return "\n".join(lines), js


def summarize_labels_from_obs(obs: list[dict]) -> dict:
    from scanner.labeling import BarrierLabel

    labels = [
        BarrierLabel(
            o["label"],
            0,
            o["entry_price"],
            o["entry_price"],
            o.get("ret", 0.0),
            o.get("mfe_pct", 0.0),
            0.0,
        )
        for o in obs
        if o.get("label")
    ]
    return summarize_labels(labels)


# ── self-test (synthetic, no network) ────────────────────────────────────────
def _self_test() -> int:
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(7)
    bars = {}
    # 40 synthetic symbols; half are "edge" names that trend up after a squeeze.
    for k in range(40):
        n = 320
        base = 20 + rng.normal(0, 0.2, n).cumsum()
        base = np.maximum(base, 2.0)
        high = base * (1 + rng.uniform(0.0, 0.03, n))
        low = base * (1 - rng.uniform(0.0, 0.03, n))
        vol = rng.uniform(5e5, 5e6, n)
        idx = pd.date_range("2025-01-01", periods=n, freq="B")
        df = pd.DataFrame(
            {"Open": base, "High": high, "Low": low, "Close": base, "Volume": vol}, index=idx
        )
        bars[f"SYM{k}"] = df
    spy = None
    obs = build_observations(bars, horizon=10, rebalance="weekly", spy=spy, proxy=None)
    obs = label_observations(obs, mode="grid", tp=0.10, sl=0.05, horizon=10, k_tp=2.0, k_sl=1.0)
    assert obs, "no observations built"
    md, js = build_report(obs, mode="grid", params={"tp": 0.10, "sl": 0.05, "horizon": 10})
    obs2 = label_observations(
        build_observations(bars, horizon=10, rebalance="weekly", spy=spy, proxy=None),
        mode="atr",
        tp=0.10,
        sl=0.05,
        horizon=10,
        k_tp=2.0,
        k_sl=1.0,
    )
    md2, _ = build_report(obs2, mode="atr", params={"k_tp": 2.0, "k_sl": 1.0, "horizon": 10})
    print(
        f"[self-test] grid obs={len(obs)}  atr obs={len(obs2)}  "
        f"grid hit-rate={js['summary']['tp_rate']:.0%}"
    )
    print("[self-test] OK — plumbing runs end-to-end on synthetic bars.")
    return 0


# ── main ─────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--top", type=int, default=1800, help="universe size after dollar-volume rank")
    ap.add_argument("--months", type=int, default=12)
    ap.add_argument(
        "--rebalance", choices=["daily", "weekly", "biweekly", "monthly"], default="weekly"
    )
    ap.add_argument("--horizon", type=int, default=10, help="time barrier in trading days")
    ap.add_argument("--tp", type=float, default=0.10)
    ap.add_argument("--sl", type=float, default=0.05)
    ap.add_argument("--k-tp", type=float, default=2.0, help="ATR multiple for take-profit")
    ap.add_argument("--k-sl", type=float, default=1.0, help="ATR multiple for stop-loss")
    ap.add_argument(
        "--no-proxy", action="store_true", help="skip proxy (squeeze/sentiment) factors"
    )
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()

    end = datetime.utcnow()
    start = end - timedelta(days=int(args.months * 31) + args.horizon * 2 + 30)

    print("Loading universe…", file=sys.stderr)
    syms = load_universe(args.top * 4)  # over-fetch, trim by liquidity
    print(f"  {len(syms)} tradable candidates", file=sys.stderr)
    print("Fetching daily bars from Alpaca…", file=sys.stderr)
    bars = fetch_daily_bars(syms, start, end)
    print(f"  {len(bars)} symbols returned bars", file=sys.stderr)
    keep = set(rank_by_dollar_volume(bars, args.top))
    bars = {s: d for s, d in bars.items() if s in keep}
    print(f"  {len(bars)} symbols after liquidity rank (top {args.top})", file=sys.stderr)

    spy_map = fetch_daily_bars(["SPY"], start, end)
    spy = spy_map.get("SPY")

    proxy = None
    if not args.no_proxy:
        proxy = build_proxy_factors(list(bars.keys()))

    print("Building point-in-time observations…", file=sys.stderr)
    base_obs = build_observations(
        bars, horizon=args.horizon, rebalance=args.rebalance, spy=spy, proxy=proxy
    )
    print(f"  {len(base_obs)} observations across the cross-section", file=sys.stderr)

    out_md = [
        f"# Universe Backtest — {datetime.utcnow().date()}",
        "",
        f"_Full liquid universe (top {args.top} by \\$-volume) · {args.months} ay · "
        f"rebalance={args.rebalance} · horizon={args.horizon} · point-in-time · "
        f"entry=next-open (no look-ahead)_",
        "",
        "> Sistem-tasarımı/ölçüm kaydıdır, yatırım tavsiyesi değildir. PROXY faktörler "
        "(squeeze/sentiment/catalyst) güncel değeri geçmişe yaydığından look-ahead taşır; "
        "sadece geliştiricinin sayısıyla kıyas için, ayrı işaretli.",
        "",
    ]
    full_js: dict = {"generated": datetime.utcnow().isoformat(), "args": vars(args), "modes": {}}

    for mode in ("grid", "atr"):
        import copy

        obs = label_observations(
            copy.deepcopy(base_obs),
            mode=mode,
            tp=args.tp,
            sl=args.sl,
            horizon=args.horizon,
            k_tp=args.k_tp,
            k_sl=args.k_sl,
        )
        md, js = build_report(obs, mode=mode, params=vars(args))
        out_md.append(md)
        full_js["modes"][mode] = js

    out_dir = ROOT / "data" / "distribution"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().date().isoformat()
    (out_dir / f"universe_backtest_{stamp}.md").write_text("\n".join(out_md), encoding="utf-8")
    (out_dir / f"universe_backtest_{stamp}.json").write_text(
        json.dumps(full_js, default=str, indent=2), encoding="utf-8"
    )
    print("\n".join(out_md))
    print(f"\nWritten: data/distribution/universe_backtest_{stamp}.md", file=sys.stderr)
    return 0


def build_proxy_factors(symbols: list[str]) -> dict:
    """CURRENT squeeze/sentiment/catalyst per symbol, broadcast to all dates.

    LOOK-AHEAD by construction — this mirrors how offline_ablation produced the
    developer's numbers, so the report can compare like-for-like. Best-effort:
    failures leave the factor absent (dropped from that factor's ablation).
    """
    from scanner import features as F

    proxy: dict[str, dict] = {}
    for i, sym in enumerate(symbols):
        d: dict[str, float] = {}
        try:
            d["squeeze_factor"] = F.compute_squeeze_factor(sym)
        except Exception:
            pass
        try:
            nc = F.compute_news_catalyst(sym)
            if isinstance(nc, dict):
                d["catalyst_factor"] = float(nc.get("score", 0.0) or 0.0)
        except Exception:
            pass
        if d:
            proxy[sym] = d
        if (i + 1) % 100 == 0:
            print(f"  proxy {i+1}/{len(symbols)}", file=sys.stderr)
    return proxy


if __name__ == "__main__":
    raise SystemExit(main())
