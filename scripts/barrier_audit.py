"""Barrier + Schema-Isolated Edge Audit.

Reads directly from signals_archive DB (not JSON files) and runs edge
analysis using the TP/SL/21g barrier label — which matches the product's
actual lifecycle model (watchlist _auto_lifecycle).

Schema isolation:
    new_100  — score > 18   (0-100 composite strength)
    old_3    — score 0-3    (filter_score)
    old_18   — score 3-18   (raw recommendation score)

Output: data/barrier_audit.json
"""

from __future__ import annotations

import json
import math
import random
import sqlite3
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "finpilot.db"
OUT = ROOT / "data" / "barrier_audit.json"


def _decile_analysis(rows: list[tuple[float, float]], n_groups: int = 10) -> list[dict]:
    """rows = [(score, outcome_pct), ...]. Returns per-decile stats."""
    if not rows:
        return []
    rows_sorted = sorted(rows, key=lambda x: x[0])
    chunk = math.ceil(len(rows_sorted) / n_groups)
    result = []
    for i in range(n_groups):
        group = rows_sorted[i * chunk : (i + 1) * chunk]
        if not group:
            continue
        scores = [r[0] for r in group]
        returns = [r[1] for r in group]
        wins = sum(1 for r in returns if r >= 0)
        result.append(
            {
                "decile": i + 1,
                "score_min": round(min(scores), 1),
                "score_max": round(max(scores), 1),
                "n": len(group),
                "win_rate": round(wins / len(group), 3),
                "avg_pct": round(statistics.mean(returns), 3),
                "median_pct": round(statistics.median(returns), 3),
            }
        )
    return result


def _decile_lift(deciles: list[dict], overall_wr: float) -> float:
    if not deciles or overall_wr == 0:
        return 0.0
    top = deciles[-1]  # sorted ascending → top = last
    return round(top["win_rate"] / overall_wr, 3)


def _perm_test(rows: list[tuple[float, float]], seed: int = 42, n: int = 1000) -> float:
    """Permutation test: prob that top-decile mean return > random sample."""
    if len(rows) < 20:
        return 1.0
    rows_sorted = sorted(rows, key=lambda x: x[0])
    chunk = math.ceil(len(rows_sorted) / 10)
    top_returns = [r[1] for r in rows_sorted[-chunk:]]
    top_mean = statistics.mean(top_returns)
    all_returns = [r[1] for r in rows]
    rng = random.Random(seed)
    count = 0
    for _ in range(n):
        sample = rng.choices(all_returns, k=len(top_returns))
        if statistics.mean(sample) >= top_mean:
            count += 1
    return round(count / n, 3)


def _profit_factor(returns: list[float]) -> float:
    gains = sum(r for r in returns if r > 0)
    losses = abs(sum(r for r in returns if r < 0))
    return round(gains / losses, 3) if losses > 0 else 999.0


def _run_schema(conn: sqlite3.Connection, label: str, where: str) -> dict:
    rows_raw = conn.execute(
        f"SELECT score, resolved_pct_barrier, resolved_pct_t5 "
        f"FROM signals_archive WHERE {where} AND resolved_pct_barrier IS NOT NULL"
    ).fetchall()

    if not rows_raw:
        return {"schema": label, "n": 0, "note": "no resolved data"}

    barrier_rows = [(float(r[0]), float(r[1])) for r in rows_raw]
    t5_rows = [(float(r[0]), float(r[2])) for r in rows_raw if r[2] is not None]

    returns_b = [r[1] for r in barrier_rows]
    wins_b = sum(1 for r in returns_b if r >= 0)
    overall_wr = round(wins_b / len(returns_b), 3)

    deciles = _decile_analysis(barrier_rows)
    lift = _decile_lift(deciles, overall_wr)
    perm = _perm_test(barrier_rows)
    pf = _profit_factor(returns_b)

    verdict_parts = []
    verdict_pass = True
    if lift < 1.3:
        verdict_parts.append(f"decile_lift={lift}<1.3 FAIL")
        verdict_pass = False
    if perm >= 0.05:
        verdict_parts.append(f"perm_p={perm}>=0.05 FAIL")
        verdict_pass = False
    if pf < 1.2:
        verdict_parts.append(f"pf={pf}<1.2 FAIL")
        verdict_pass = False

    verdict = "EDGE DETECTED" if verdict_pass else f"NO EDGE — {', '.join(verdict_parts)}"

    # T+5 comparison
    t5_wr = None
    if t5_rows:
        t5_wins = sum(1 for _, r in t5_rows if r >= 0)
        t5_wr = round(t5_wins / len(t5_rows), 3)

    return {
        "schema": label,
        "n": len(barrier_rows),
        "overall": {
            "hit_rate_barrier": overall_wr,
            "hit_rate_t5": t5_wr,
            "expectancy_pct": round(statistics.mean(returns_b), 3),
            "median_pct": round(statistics.median(returns_b), 3),
            "profit_factor": pf,
            "stdev_pct": round(statistics.stdev(returns_b), 3) if len(returns_b) > 1 else 0.0,
        },
        "deciles": deciles,
        "decile_lift": lift,
        "permutation_p": perm,
        "verdict": verdict,
    }


def run(db_path: Path = DB_PATH) -> dict:
    conn = sqlite3.connect(str(db_path))

    schemas = {
        "new_100 (score>18, composite 0-100)": "score > 18",
        "old_filter (score 0-3, filter_score)": "score > 0 AND score <= 3",
        "old_raw (score 3-18, raw reco score)": "score > 3 AND score <= 18",
        "all_combined": "score > 0",
    }

    result = {
        "ran_at": __import__("datetime").datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "label_type": "barrier (TP/SL/21g)",
        "schemas": {},
    }

    for label, where in schemas.items():
        print(f"\n[barrier_audit] Schema: {label}")
        r = _run_schema(conn, label, where)
        result["schemas"][label] = r
        if r["n"] > 0:
            print(
                f"  n={r['n']}  wr={r['overall']['hit_rate_barrier']}  "
                f"exp={r['overall']['expectancy_pct']}%  "
                f"decile_lift={r['decile_lift']}  perm_p={r['permutation_p']}"
            )
            print(f"  VERDICT: {r['verdict']}")
        else:
            print("  No data")

    conn.close()
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[barrier_audit] report -> {OUT}")
    return result


if __name__ == "__main__":
    run()
