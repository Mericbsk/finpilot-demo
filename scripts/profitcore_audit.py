"""Profit Core Audit — measure whether the current scoring core has edge.

Outputs:
    - data/profitcore_audit.json  (full report)
    - terminal: decile lift table, hit rate, expectancy, component summary

Sources resolved outcomes from (in order):
    1. core.kpi_tracker (Redis or in-memory live signals with `outcome`)
    2. data/signal_archive/*.json with status_lifecycle.outcome populated
    3. on-demand yfinance T+5 close lookup for archive BUY signals with entry_price

Usage:
    python scripts/profitcore_audit.py [--resolve] [--days 60] [--horizon 5]

Flags:
    --resolve   fetch yfinance closes to resolve unresolved archive BUYs
    --days N    only look at signals from the last N days (default 60)
    --horizon H hold horizon in trading days for T+H return (default 5)
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DIR = ROOT / "data" / "signal_archive"
OUTPUT_PATH = ROOT / "data" / "profitcore_audit.json"


def _parse_date(s: str | None) -> datetime | None:
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(s[: len(fmt) + 6], fmt)
        except Exception:
            continue
    return None


def load_archive_signals(days: int) -> list[dict]:
    if not ARCHIVE_DIR.exists():
        return []
    cutoff = datetime.now().date() - timedelta(days=days)
    items: list[dict] = []
    for f in sorted(ARCHIVE_DIR.glob("*.json"), reverse=True):
        try:
            d = datetime.strptime(f.stem, "%Y-%m-%d").date()
            if d < cutoff:
                continue
            data = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for s in data:
                    s.setdefault("_archive_date", str(d))
                    items.extend([s])
        except Exception:
            continue
    return items


def load_live_signals() -> list[dict]:
    try:
        from core.kpi_tracker import _load_all_signals

        return list(_load_all_signals())
    except Exception:
        return []


def resolve_outcomes_yf(signals: list[dict], horizon_days: int) -> int:
    """Fill `_resolved_pct` for BUYs with entry_price + signal_date using yfinance."""
    try:
        import yfinance as yf
    except ImportError:
        print("[warn] yfinance not installed — cannot resolve outcomes", file=sys.stderr)
        return 0

    by_symbol: dict[str, list[dict]] = {}
    for s in signals:
        if str(s.get("signal", "")).upper() != "BUY":
            continue
        entry = s.get("entry_price") or s.get("price")
        date = s.get("signal_date") or s.get("_archive_date")
        if entry and date and s.get("_resolved_pct") is None:
            by_symbol.setdefault(str(s.get("symbol", "")), []).append(s)

    resolved = 0
    for symbol, sigs in by_symbol.items():
        if not symbol:
            continue
        oldest = min(
            _parse_date(s.get("signal_date") or s.get("_archive_date")) or datetime.now()
            for s in sigs
        )
        start = (oldest - timedelta(days=2)).strftime("%Y-%m-%d")
        end = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            hist = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)
            if hist is None or hist.empty:
                continue
            closes = hist["Close"].squeeze()
            dates = [d.date() for d in closes.index]
        except Exception:
            continue

        for s in sigs:
            entry_price = float(s.get("entry_price") or s.get("price") or 0)
            if entry_price <= 0:
                continue
            entry_dt = _parse_date(s.get("signal_date") or s.get("_archive_date"))
            if not entry_dt:
                continue
            entry_date = entry_dt.date()
            future = [d for d in dates if (d - entry_date).days >= horizon_days]
            if not future:
                continue
            target = min(future, key=lambda d: (d - entry_date).days)
            try:
                price_t = float(closes[closes.index.date == target].iloc[0])  # type: ignore[attr-defined]
                pct = (price_t - entry_price) / entry_price * 100.0
                s["_resolved_pct"] = round(pct, 3)
                resolved += 1
            except Exception:
                continue
    return resolved


def extract_score(s: dict) -> float | None:
    for k in ("score", "finpilot_score", "composite_score", "strength"):
        v = s.get(k)
        if v is None:
            continue
        try:
            return float(v)
        except Exception:
            continue
    return None


def extract_outcome_pct(s: dict) -> float | None:
    # Live signals from kpi_tracker
    p = s.get("profit_pct")
    if p is not None:
        try:
            return float(p)
        except Exception:
            pass
    # Archive lifecycle
    sl = s.get("status_lifecycle") or {}
    if isinstance(sl, dict):
        p = sl.get("outcome_pct") or sl.get("profit_pct")
        if p is not None:
            try:
                return float(p)
            except Exception:
                pass
    # Resolved by yfinance in this run
    r = s.get("_resolved_pct")
    if r is not None:
        try:
            return float(r)
        except Exception:
            pass
    return None


def decile_lift(rows: list[tuple[float, float]], n_bins: int = 10) -> list[dict]:
    """rows = list of (score, pct_return). Returns bin stats sorted high→low score."""
    if not rows:
        return []
    rows = sorted(rows, key=lambda r: r[0])
    n = len(rows)
    if n < n_bins:
        n_bins = max(2, n // 2)
    bins: list[dict] = []
    for i in range(n_bins):
        lo = i * n // n_bins
        hi = (i + 1) * n // n_bins if i < n_bins - 1 else n
        chunk = rows[lo:hi]
        if not chunk:
            continue
        wins = [r for r in chunk if r[1] > 0]
        bins.append(
            {
                "decile": i + 1,
                "score_min": round(chunk[0][0], 3),
                "score_max": round(chunk[-1][0], 3),
                "n": len(chunk),
                "win_rate": round(len(wins) / len(chunk), 3),
                "avg_pct": round(statistics.mean(r[1] for r in chunk), 3),
                "median_pct": round(statistics.median(r[1] for r in chunk), 3),
            }
        )
    return list(reversed(bins))


def permutation_test(rows: list[tuple[float, float]], n_iter: int = 1000) -> float:
    """p-value for: top-decile mean return > random."""
    if len(rows) < 20:
        return 1.0
    sorted_rows = sorted(rows, key=lambda r: r[0])
    top_size = max(1, len(sorted_rows) // 10)
    actual_top_mean = statistics.mean(r[1] for r in sorted_rows[-top_size:])
    rng = random.Random(42)
    pcts = [r[1] for r in rows]
    hits = 0
    for _ in range(n_iter):
        sample = rng.sample(pcts, top_size)
        if statistics.mean(sample) >= actual_top_mean:
            hits += 1
    return round(hits / n_iter, 4)


def summary_stats(rows: list[tuple[float, float]]) -> dict:
    if not rows:
        return {"n": 0}
    pcts = [r[1] for r in rows]
    wins = [p for p in pcts if p > 0]
    losses = [p for p in pcts if p <= 0]
    profit_factor: float | str = (
        round(sum(wins) / abs(sum(losses)), 3) if losses and sum(losses) != 0 else "inf"
    )
    return {
        "n": len(rows),
        "hit_rate": round(len(wins) / len(rows), 3),
        "expectancy_pct": round(statistics.mean(pcts), 3),
        "median_pct": round(statistics.median(pcts), 3),
        "profit_factor": profit_factor,
        "stdev_pct": round(statistics.stdev(pcts), 3) if len(pcts) > 1 else 0.0,
    }


def print_table(rows: list[dict]) -> None:
    if not rows:
        print("(no rows)")
        return
    headers = list(rows[0].keys())
    widths = {h: max(len(h), max(len(str(r.get(h, ""))) for r in rows)) for h in headers}
    print("  ".join(h.ljust(widths[h]) for h in headers))
    print("  ".join("-" * widths[h] for h in headers))
    for r in rows:
        print("  ".join(str(r.get(h, "")).ljust(widths[h]) for h in headers))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=60)
    ap.add_argument("--horizon", type=int, default=5)
    ap.add_argument("--resolve", action="store_true", help="fetch yfinance closes")
    args = ap.parse_args()

    print(f"[audit] days={args.days} horizon=T+{args.horizon} resolve={args.resolve}")
    live = load_live_signals()
    archive = load_archive_signals(args.days)
    print(f"[audit] live={len(live)} archive={len(archive)}")

    all_sigs = live + archive

    if args.resolve:
        n = resolve_outcomes_yf(all_sigs, args.horizon)
        print(f"[audit] resolved via yfinance: {n}")

    rows: list[tuple[float, float]] = []
    skipped_no_score = 0
    skipped_no_outcome = 0
    for s in all_sigs:
        sc = extract_score(s)
        pct = extract_outcome_pct(s)
        if sc is None:
            skipped_no_score += 1
            continue
        if pct is None:
            skipped_no_outcome += 1
            continue
        rows.append((sc, pct))

    print(
        f"[audit] usable rows: {len(rows)} (skipped no_score={skipped_no_score} no_outcome={skipped_no_outcome})"
    )

    overall = summary_stats(rows)
    bins = decile_lift(rows)
    top_wr = bins[0]["win_rate"] if bins else None
    overall_wr = overall.get("hit_rate")
    decile_lift_ratio = (
        round(top_wr / overall_wr, 3) if (top_wr and overall_wr and overall_wr > 0) else None
    )
    perm_p = permutation_test(rows) if rows else 1.0

    report = {
        "ran_at": datetime.now().isoformat(timespec="seconds"),
        "params": {"days": args.days, "horizon": args.horizon, "resolve": args.resolve},
        "data": {
            "live_signals": len(live),
            "archive_signals": len(archive),
            "usable_rows": len(rows),
            "skipped_no_score": skipped_no_score,
            "skipped_no_outcome": skipped_no_outcome,
        },
        "overall": overall,
        "deciles": bins,
        "decile_lift": decile_lift_ratio,
        "permutation_p": perm_p,
        "verdict": _verdict(overall, decile_lift_ratio, perm_p),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2))

    print(f"\n=== OVERALL (n={overall.get('n')}) ===")
    for k, v in overall.items():
        print(f"  {k}: {v}")
    print("\n=== DECILE LIFT (top to bottom) ===")
    print_table(bins)
    print(f"\ndecile_lift (top_wr/overall_wr) = {decile_lift_ratio}")
    print(f"permutation_p (top-decile mean > random) = {perm_p}")
    print(f"\nVERDICT: {report['verdict']}")
    print(f"\n[audit] report -> {OUTPUT_PATH.relative_to(ROOT)}")
    return 0


def _verdict(overall: dict, lift: float | None, p: float) -> str:
    n = overall.get("n", 0)
    if n < 30:
        return f"INSUFFICIENT DATA (n={n}). Resolve outcomes first (--resolve) or wait for fill."
    hr = overall.get("hit_rate") or 0
    pf = overall.get("profit_factor")
    pf_num = pf if isinstance(pf, (int, float)) else math.inf
    edge_signals: list[str] = []
    if lift and lift >= 1.3:
        edge_signals.append(f"decile_lift={lift}>=1.3 OK")
    else:
        edge_signals.append(f"decile_lift={lift}<1.3 FAIL")
    if p < 0.05:
        edge_signals.append(f"perm_p={p}<0.05 OK")
    else:
        edge_signals.append(f"perm_p={p}>=0.05 FAIL")
    if pf_num >= 1.2:
        edge_signals.append(f"profit_factor={pf}>=1.2 OK")
    else:
        edge_signals.append(f"profit_factor={pf}<1.2 FAIL")
    has_edge = sum(1 for s in edge_signals if "OK" in s) >= 2
    return (
        ("EDGE PRESENT — " if has_edge else "NO EDGE DETECTED — ")
        + f"hit_rate={hr}, "
        + ", ".join(edge_signals)
    )


if __name__ == "__main__":
    sys.exit(main())
