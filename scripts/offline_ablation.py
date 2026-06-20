"""Offline ablation script for the 3 new data factors.

Uses signals_archive (5719 rows, resolved_status_barrier) to measure
the baseline score→win-rate curve, then simulates the new factors
using current yfinance data as a proxy for historical squeeze potential.

Usage:
    python scripts/offline_ablation.py
    python scripts/offline_ablation.py --no-network   # skip yfinance, show DB stats only
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "data" / "finpilot.db"
RESULT_PATH = ROOT / "data" / "offline_ablation.json"

WIN_STATUSES = {"resolved_win", "expired_win"}
LOSS_STATUSES = {"resolved_loss", "expired_loss"}


def load_resolved(conn: sqlite3.Connection) -> list[dict]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT symbol, score, resolved_status_barrier, resolved_pct_barrier
        FROM signals_archive
        WHERE resolved_status_barrier IS NOT NULL
        """
    )
    rows = []
    for sym, score, status, pct in cur.fetchall():
        if status in WIN_STATUSES or status in LOSS_STATUSES:
            rows.append(
                {
                    "symbol": sym,
                    "score": score or 0,
                    "win": status in WIN_STATUSES,
                    "pct": pct or 0.0,
                }
            )
    return rows


def score_band_stats(rows: list[dict]) -> dict:
    """Win rate by score decile (0-9, 10-19, … 80-89)."""
    bands: dict[str, list] = {}
    for r in rows:
        band = f"{(int(r['score']) // 10) * 10}-{(int(r['score']) // 10) * 10 + 9}"
        bands.setdefault(band, []).append(r["win"])
    result = {}
    for band, wins in sorted(bands.items()):
        n = len(wins)
        wr = round(sum(wins) / n * 100, 1) if n else 0.0
        result[band] = {"n": n, "win_rate": wr}
    return result


def pct_move_stats(rows: list[dict]) -> dict:
    """How many signals captured each move bucket."""
    buckets = {"<5": 0, "5-10": 0, "10-30": 0, "30-100": 0, ">100": 0, "loss": 0}
    for r in rows:
        if not r["win"]:
            buckets["loss"] += 1
            continue
        p = float(r["pct"])
        if p < 5:
            buckets["<5"] += 1
        elif p < 10:
            buckets["5-10"] += 1
        elif p < 30:
            buckets["10-30"] += 1
        elif p < 100:
            buckets["30-100"] += 1
        else:
            buckets[">100"] += 1
    return buckets


def fetch_squeeze_sample(symbols: list[str], max_symbols: int = 80) -> dict[str, float]:
    """Fetch current squeeze factors for a sample of symbols (proxy ablation)."""
    sample = list(dict.fromkeys(symbols))[:max_symbols]
    factors: dict[str, float] = {}

    from scanner.features import compute_squeeze_factor  # noqa: PLC0415

    print(f"\n[ablation] Fetching squeeze factors for {len(sample)} symbols …")
    for i, sym in enumerate(sample, 1):
        try:
            factors[sym] = compute_squeeze_factor(sym)
        except Exception:
            factors[sym] = 0.0
        if i % 10 == 0:
            print(f"  {i}/{len(sample)} …")
        time.sleep(0.25)  # yfinance rate limit
    return factors


def squeeze_cohort_analysis(rows: list[dict], factors: dict[str, float]) -> dict:
    """Split rows into high/low squeeze cohorts, compare win rates."""
    scored = [(r, factors.get(r["symbol"], 0.0)) for r in rows if r["symbol"] in factors]
    if not scored:
        return {}

    # Tertile split on squeeze factor
    vals = sorted({sq for _, sq in scored})
    if len(vals) < 3:
        return {}
    low_thresh = vals[len(vals) // 3]
    high_thresh = vals[2 * len(vals) // 3]

    low_cohort = [r for r, sq in scored if sq <= low_thresh]
    high_cohort = [r for r, sq in scored if sq >= high_thresh]

    def wr(cohort):
        if not cohort:
            return 0.0, 0
        return round(sum(r["win"] for r in cohort) / len(cohort) * 100, 1), len(cohort)

    low_wr, low_n = wr(low_cohort)
    high_wr, high_n = wr(high_cohort)

    return {
        "low_squeeze": {"n": low_n, "win_rate": low_wr, "threshold": round(low_thresh, 3)},
        "high_squeeze": {"n": high_n, "win_rate": high_wr, "threshold": round(high_thresh, 3)},
        "lift": round(high_wr - low_wr, 1),
        "verdict": "DIRECTIONAL" if high_wr > low_wr else "NO_LIFT",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-network", action="store_true", help="Skip yfinance calls; show DB stats only"
    )
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"[ablation] DB not found: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    rows = load_resolved(conn)
    conn.close()

    n_win = sum(r["win"] for r in rows)
    n_loss = len(rows) - n_win
    overall_wr = round(n_win / len(rows) * 100, 1) if rows else 0.0

    print(f"\n{'='*60}")
    print("FinPilot Offline Ablation Report")
    print(f"{'='*60}")
    print(f"Resolved signals: {len(rows):,}  (win={n_win}, loss={n_loss})")
    print(f"Overall win rate: {overall_wr}%\n")

    bands = score_band_stats(rows)
    print("Score band → Win rate:")
    for band, s in bands.items():
        bar = "█" * max(1, int(s["win_rate"] / 3))
        print(f"  {band:10s}  {s['win_rate']:5.1f}%  n={s['n']:5d}  {bar}")

    moves = pct_move_stats(rows)
    print("\nMove capture (winning signals):")
    for bucket, count in moves.items():
        print(f"  {bucket:10s}: {count}")

    squeeze_result = {}
    if not args.no_network:
        unique_syms = list({r["symbol"] for r in rows})
        factors = fetch_squeeze_sample(unique_syms, max_symbols=80)
        squeeze_result = squeeze_cohort_analysis(rows, factors)

        if squeeze_result:
            print(f"\nSqueeze Factor Cohort Analysis (proxy, n={len(factors)} symbols):")
            print(
                f"  Low-squeeze cohort : wr={squeeze_result['low_squeeze']['win_rate']}%  (n={squeeze_result['low_squeeze']['n']})"
            )
            print(
                f"  High-squeeze cohort: wr={squeeze_result['high_squeeze']['win_rate']}%  (n={squeeze_result['high_squeeze']['n']})"
            )
            print(f"  Lift: {squeeze_result['lift']:+.1f}pp  →  {squeeze_result['verdict']}")

    report = {
        "n_resolved": len(rows),
        "n_win": n_win,
        "n_loss": n_loss,
        "overall_win_rate": overall_wr,
        "score_bands": bands,
        "move_buckets": moves,
        "squeeze_cohort": squeeze_result,
    }
    RESULT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n[ablation] report → {RESULT_PATH.name}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
