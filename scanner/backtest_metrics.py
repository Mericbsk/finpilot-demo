"""Backtest metrics — the honest edge-measurement layer for a full-universe,
point-in-time cross-section (NOT just the triggered BUY shortlist).

Why this module exists
----------------------
The scanner's "good" numbers to date (alpha-v2 decile lift ~1.7, conviction
hit-rate ~73%) come from ``scripts/offline_ablation.py``, which reconstructed the
factors with *current* yfinance data as a proxy for history — a look-ahead
weakness. And the live ``factor_ablation_report.py`` only sees the daily top-N
export shortlist (~12-200 names), not the ~1800-name universe the scanner
actually screens.

To reproduce AND stress-test those claims we need to label EVERY (symbol, date)
observation in the universe by the triple-barrier method and then measure, on
that full cross-section, the exact statistics the developer quoted:

    * decile_lift        — rank observations by a factor into deciles; does the
                           top decile win more than the base rate? (the headline
                           "lift 1.74" metric)
    * conviction_bucket_hitrate — replicate "short>=15 & gap>=3 → >=5%/>=10% hit"
    * spy_relative       — subtract the same-window benchmark move so we separate
                           real edge from beta (a rising tide lifting all boats)
    * median_split_ablation — split a factor at its OWN median (fixes the
                           composite_score n_hi=0 problem where a fixed 55 cut
                           left the HIGH bucket empty)

All functions are pure (no I/O, no network) so they are unit-testable and
deterministic. The universe runner (``scripts/universe_backtest.py``) feeds them
labeled observations; here we only do the statistics.

An "observation" (obs) is a dict carrying at least:
    ``ret``      forward realised return as a fraction (from triple-barrier), and
    ``win``      1/0 outcome (tp hit) — OR we derive win from ``label == 'tp'``,
plus any factor values keyed by name, and optionally ``bench_ret`` for the
same-window benchmark return.
"""

from __future__ import annotations

from collections.abc import Sequence
from statistics import median
from typing import Any


# ── helpers ──────────────────────────────────────────────────────────────────
def _win_of(o: dict[str, Any]) -> float:
    """1.0 if the observation is a win, else 0.0.

    Prefers an explicit ``win``; falls back to ``label == 'tp'``; else uses
    ``ret > 0``.
    """
    if "win" in o and o["win"] is not None:
        return 1.0 if float(o["win"]) > 0 else 0.0
    lbl = o.get("label")
    if lbl is not None:
        return 1.0 if lbl == "tp" else 0.0
    return 1.0 if float(o.get("ret", 0.0)) > 0 else 0.0


def _num(o: dict[str, Any], key: str) -> float | None:
    try:
        v = o.get(key)
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


# ── decile lift (the developer's headline metric) ────────────────────────────
def decile_lift(
    observations: Sequence[dict[str, Any]],
    factor_key: str,
    *,
    n_buckets: int = 10,
    metric: str = "win",
) -> dict[str, Any]:
    """Rank observations by ``factor_key`` into ``n_buckets`` and measure the
    top-bucket lift over the whole-sample base rate.

    ``metric='win'``  → per-bucket win-rate, lift = top_winrate / base_winrate.
    ``metric='ret'``  → per-bucket mean return, lift = top_mean_ret - base_mean_ret
                        (additive, since returns can be negative).

    Returns dict with per-bucket stats, ``base``, ``top_bucket`` and ``lift``.
    Observations lacking a numeric factor value are dropped. A lift computed on
    <~30 per bucket is noise — the caller should check ``n_per_bucket``.
    """
    rows = [(v, o) for o in observations if (v := _num(o, factor_key)) is not None]
    n = len(rows)
    out: dict[str, Any] = {
        "factor": factor_key,
        "metric": metric,
        "n": n,
        "n_buckets": n_buckets,
        "buckets": [],
        "base": None,
        "top_bucket": None,
        "lift": None,
        "n_per_bucket": 0,
    }
    if n < n_buckets:
        return out

    rows.sort(key=lambda t: t[0])
    # base rate over the whole sample
    if metric == "ret":
        base = _mean([float(o.get("ret", 0.0)) for _, o in rows])
    else:
        base = _mean([_win_of(o) for _, o in rows])
    out["base"] = round(base, 6)

    per = n // n_buckets
    out["n_per_bucket"] = per
    buckets = []
    for b in range(n_buckets):
        lo = b * per
        hi = (b + 1) * per if b < n_buckets - 1 else n
        seg = [o for _, o in rows[lo:hi]]
        if metric == "ret":
            val = _mean([float(o.get("ret", 0.0)) for o in seg])
        else:
            val = _mean([_win_of(o) for o in seg])
        fvals = [v for v, _ in rows[lo:hi]]
        buckets.append(
            {
                "bucket": b + 1,
                "n": len(seg),
                "factor_min": round(min(fvals), 6),
                "factor_max": round(max(fvals), 6),
                "value": round(val, 6),
            }
        )
    out["buckets"] = buckets
    top = buckets[-1]["value"]
    out["top_bucket"] = round(top, 6)
    if metric == "ret":
        out["lift"] = round(top - base, 6)  # additive excess
    else:
        out["lift"] = round(top / base, 4) if base > 0 else None
    return out


# ── ATR-scaled barrier parameters ────────────────────────────────────────────
def atr_barrier_params(
    atr_pct: float,
    *,
    k_tp: float = 2.0,
    k_sl: float = 1.0,
    min_tp: float = 0.02,
    min_sl: float = 0.01,
) -> tuple[float, float]:
    """Turn a per-signal ATR% into (tp_pct, sl_pct) fractions.

    The fixed 10%/5% grid is regime-blind: on a quiet name +10% in 10 days is
    unreachable (→ structural time-out), on a volatile name it's noise. Scaling
    the barriers to each signal's own ATR makes the target reachable and the
    stop meaningful. ``atr_pct`` is ATR as a PERCENT of price (e.g. 4.0 = 4%).

    tp = k_tp * ATR, sl = k_sl * ATR, each floored so degenerate quiet names
    don't collapse to a zero-width barrier.
    """
    a = max(float(atr_pct), 0.0) / 100.0
    tp = max(k_tp * a, min_tp)
    sl = max(k_sl * a, min_sl)
    return (round(tp, 6), round(sl, 6))


# ── benchmark-relative (beta vs edge) ────────────────────────────────────────
def spy_relative(observations: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Compare raw vs benchmark-relative expectancy.

    Each obs needs ``ret`` (raw forward return) and ``bench_ret`` (same-window
    benchmark, e.g. SPY, return). Excess = ret - bench_ret. If most of the raw
    expectancy survives as excess, the edge is real; if it vanishes, the signal
    was just riding beta.
    """
    rets, exc = [], []
    for o in observations:
        r = _num(o, "ret")
        b = _num(o, "bench_ret")
        if r is None:
            continue
        rets.append(r)
        if b is not None:
            exc.append(r - b)
    raw_exp = _mean(rets)
    exc_exp = _mean(exc)
    return {
        "n": len(rets),
        "n_with_bench": len(exc),
        "raw_expectancy": round(raw_exp, 6),
        "excess_expectancy": round(exc_exp, 6),
        "beta_share": (round(1 - exc_exp / raw_exp, 4) if raw_exp not in (0.0,) else None),
    }


# ── median-split ablation (fixes composite n_hi=0) ───────────────────────────
def median_split_ablation(
    observations: Sequence[dict[str, Any]],
    factor_key: str,
    *,
    metric: str = "ret",
) -> dict[str, Any]:
    """Split at the factor's OWN median so both buckets are guaranteed non-empty.

    The live ablation used a fixed threshold (composite_score>=55) that left the
    HIGH bucket empty (n_hi=0) because scores never reached it on the sample.
    A median split always fills both sides and asks the same question: does the
    upper half of this factor outperform the lower half?
    """
    rows = [(v, o) for o in observations if (v := _num(o, factor_key)) is not None]
    out: dict[str, Any] = {
        "factor": factor_key,
        "metric": metric,
        "n": len(rows),
        "threshold": None,
        "hi": None,
        "lo": None,
        "lift": None,
        "separates": None,
    }
    if len(rows) < 4:
        return out
    thr = median([v for v, _ in rows])
    out["threshold"] = round(thr, 6)
    hi = [o for v, o in rows if v >= thr]
    lo = [o for v, o in rows if v < thr]
    if not hi or not lo:  # degenerate (many ties at median)
        return out

    def _agg(seg: list[dict[str, Any]]) -> float:
        if metric == "win":
            return _mean([_win_of(o) for o in seg])
        return _mean([float(o.get("ret", 0.0)) for o in seg])

    hv, lv = _agg(hi), _agg(lo)
    out["hi"] = {"n": len(hi), "value": round(hv, 6)}
    out["lo"] = {"n": len(lo), "value": round(lv, 6)}
    out["lift"] = round(hv - lv, 6)
    out["separates"] = bool(hv > lv)
    return out


# ── conviction bucket hit-rate (replicate the developer's claim) ─────────────
def conviction_bucket_hitrate(
    observations: Sequence[dict[str, Any]],
    *,
    squeeze_key: str = "squeeze_factor",
    gap_key: str = "gap_factor",
    squeeze_min: float = 0.5,  # ~short interest >= 15%
    gap_min: float = 0.6,  # ~gap >= 3%
    move_thresholds: Sequence[float] = (0.05, 0.10),
) -> dict[str, Any]:
    """Replicate "short>=15 & gap>=3 → >=5%/>=10% hit-rate" on the cross-section.

    The bucket is the intersection (both factors high). For each move threshold
    we report the share of bucket names whose forward MFE (max favourable
    excursion) reached that move — matching a "did it ever go up X%?" reading.
    Falls back to ``ret`` when ``mfe_pct`` is absent. Also returns the base rate
    over ALL observations so the lift is visible.
    """

    def _reached(o: dict[str, Any], thr: float) -> bool:
        mfe = _num(o, "mfe_pct")
        val = mfe if mfe is not None else _num(o, "ret")
        return val is not None and val >= thr

    bucket = [
        o
        for o in observations
        if (s := _num(o, squeeze_key)) is not None
        and s >= squeeze_min
        and (g := _num(o, gap_key)) is not None
        and g >= gap_min
    ]
    out: dict[str, Any] = {
        "n_bucket": len(bucket),
        "n_total": len(observations),
        "thresholds": {},
    }
    for thr in move_thresholds:
        key = f">={thr:.0%}"
        b_rate = _mean([1.0 if _reached(o, thr) else 0.0 for o in bucket]) if bucket else 0.0
        base = (
            _mean([1.0 if _reached(o, thr) else 0.0 for o in observations]) if observations else 0.0
        )
        out["thresholds"][key] = {
            "bucket_hitrate": round(b_rate, 4),
            "base_hitrate": round(base, 4),
            "lift": round(b_rate / base, 4) if base > 0 else None,
        }
    return out


# ── markdown rendering ───────────────────────────────────────────────────────
def format_decile_md(dl: dict[str, Any]) -> str:
    lines = [
        f"**{dl['factor']}** ({dl['metric']}) · n={dl['n']} · "
        f"base={dl['base']} · top={dl['top_bucket']} · **lift={dl['lift']}** "
        f"(~{dl['n_per_bucket']}/bucket)",
        "",
        "| decile | n | f_min | f_max | value |",
        "|---|---|---|---|---|",
    ]
    for b in dl["buckets"]:
        lines.append(
            f"| {b['bucket']} | {b['n']} | {b['factor_min']} | {b['factor_max']} | {b['value']} |"
        )
    return "\n".join(lines)
