"""Regime Cross-Section Analysis.

Splits signals by regime/vol_regime/sector_rs and computes win rate + edge
metrics per segment. Answers: "does the score work in a specific regime?"

Uses signals_archive DB with barrier outcomes.

Output: data/regime_cross_section.json
"""

from __future__ import annotations

import json
import math
import sqlite3
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "finpilot.db"
OUT = ROOT / "data" / "regime_cross_section.json"


def _stats(returns: list[float]) -> dict:
    if not returns:
        return {"n": 0}
    wins = sum(1 for r in returns if r >= 0)
    gains = sum(r for r in returns if r > 0)
    losses = abs(sum(r for r in returns if r < 0))
    return {
        "n": len(returns),
        "win_rate": round(wins / len(returns), 3),
        "avg_pct": round(statistics.mean(returns), 3),
        "median_pct": round(statistics.median(returns), 3),
        "stdev_pct": round(statistics.stdev(returns), 3) if len(returns) > 1 else 0.0,
        "profit_factor": round(gains / losses, 3) if losses > 0 else 999.0,
    }


def _score_corr(pairs: list[tuple[float, float]]) -> float:
    """Pearson correlation between score and return."""
    if len(pairs) < 5:
        return 0.0
    scores = [p[0] for p in pairs]
    returns = [p[1] for p in pairs]
    n = len(scores)
    mean_s = sum(scores) / n
    mean_r = sum(returns) / n
    num = sum((s - mean_s) * (r - mean_r) for s, r in zip(scores, returns, strict=False))
    den_s = math.sqrt(sum((s - mean_s) ** 2 for s in scores))
    den_r = math.sqrt(sum((r - mean_r) ** 2 for r in returns))
    if den_s == 0 or den_r == 0:
        return 0.0
    return round(num / (den_s * den_r), 4)


def run(db_path: Path = DB_PATH) -> dict:
    conn = sqlite3.connect(str(db_path))

    # Load all barrier-resolved rows with payload
    rows_raw = conn.execute(
        "SELECT id, symbol, score, resolved_pct_barrier, payload_json "
        "FROM signals_archive "
        "WHERE resolved_pct_barrier IS NOT NULL AND score > 0"
    ).fetchall()
    conn.close()

    print(f"[regime_cs] Loaded {len(rows_raw)} barrier-resolved rows")

    # Parse payload for regime fields
    records = []
    for row in rows_raw:
        d = json.loads(row[4]) if row[4] else {}
        records.append(
            {
                "symbol": row[1],
                "score": float(row[2]),
                "ret": float(row[3]),
                "regime": d.get("regime"),  # bool or "Bull"/"Bear"
                "vol_regime": d.get("vol_regime"),  # int 1/2 or None
                "sector_rs": d.get("sector_rs"),  # float or None
                "earnings_blackout": d.get("earnings_blackout"),  # bool
            }
        )

    result = {
        "ran_at": __import__("datetime").datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "total_barrier_resolved": len(records),
        "segments": {},
    }

    # ── 1. Overall ──────────────────────────────────────────────────────────
    all_pairs = [(r["score"], r["ret"]) for r in records]
    overall_stats = _stats([r["ret"] for r in records])
    overall_stats["corr_score_return"] = _score_corr(all_pairs)
    result["segments"]["overall"] = overall_stats
    print(
        f"  Overall: n={overall_stats['n']}  wr={overall_stats['win_rate']}  "
        f"avg={overall_stats['avg_pct']}%  corr={overall_stats['corr_score_return']}"
    )

    # ── 2. Regime split ─────────────────────────────────────────────────────
    regime_groups: dict[str, list] = {"Bull": [], "Bear": [], "unknown": []}
    for r in records:
        rv = r["regime"]
        if rv is True or str(rv).lower() in ("true", "bull", "1"):
            regime_groups["Bull"].append(r)
        elif rv is False or str(rv).lower() in ("false", "bear", "0"):
            regime_groups["Bear"].append(r)
        else:
            regime_groups["unknown"].append(r)

    result["segments"]["by_regime"] = {}
    for grp, rows in regime_groups.items():
        if not rows:
            continue
        pairs = [(r["score"], r["ret"]) for r in rows]
        s = _stats([r["ret"] for r in rows])
        s["corr_score_return"] = _score_corr(pairs)
        result["segments"]["by_regime"][grp] = s
        print(
            f"  Regime {grp}: n={s['n']}  wr={s['win_rate']}  "
            f"avg={s['avg_pct']}%  corr={s['corr_score_return']}"
        )

    # ── 3. Vol-regime split ─────────────────────────────────────────────────
    vol_groups: dict[str, list] = {"low_vol(1)": [], "high_vol(2)": [], "unknown": []}
    for r in records:
        vr = r["vol_regime"]
        if vr is None:
            vol_groups["unknown"].append(r)
        elif int(float(vr)) == 1:
            vol_groups["low_vol(1)"].append(r)
        elif int(float(vr)) == 2:
            vol_groups["high_vol(2)"].append(r)
        else:
            vol_groups["unknown"].append(r)

    result["segments"]["by_vol_regime"] = {}
    for grp, rows in vol_groups.items():
        if not rows:
            continue
        pairs = [(r["score"], r["ret"]) for r in rows]
        s = _stats([r["ret"] for r in rows])
        s["corr_score_return"] = _score_corr(pairs)
        result["segments"]["by_vol_regime"][grp] = s
        print(
            f"  Vol regime {grp}: n={s['n']}  wr={s['win_rate']}  "
            f"avg={s['avg_pct']}%  corr={s['corr_score_return']}"
        )

    # ── 4. Sector RS split ──────────────────────────────────────────────────
    rs_groups: dict[str, list] = {"high_rs(>0.5)": [], "low_rs(<=0.5)": [], "no_data": []}
    for r in records:
        rs = r["sector_rs"]
        if rs is None:
            rs_groups["no_data"].append(r)
        elif float(rs) > 0.5:
            rs_groups["high_rs(>0.5)"].append(r)
        else:
            rs_groups["low_rs(<=0.5)"].append(r)

    result["segments"]["by_sector_rs"] = {}
    for grp, rows in rs_groups.items():
        if not rows:
            continue
        pairs = [(r["score"], r["ret"]) for r in rows]
        s = _stats([r["ret"] for r in rows])
        s["corr_score_return"] = _score_corr(pairs)
        result["segments"]["by_sector_rs"][grp] = s
        print(
            f"  Sector RS {grp}: n={s['n']}  wr={s['win_rate']}  "
            f"avg={s['avg_pct']}%  corr={s['corr_score_return']}"
        )

    # ── 5. Earnings blackout split ──────────────────────────────────────────
    eb_groups: dict[str, list] = {"blackout": [], "no_blackout": [], "unknown": []}
    for r in records:
        eb = r["earnings_blackout"]
        if eb is None:
            eb_groups["unknown"].append(r)
        elif eb is True or str(eb).lower() == "true":
            eb_groups["blackout"].append(r)
        else:
            eb_groups["no_blackout"].append(r)

    result["segments"]["by_earnings_blackout"] = {}
    for grp, rows in eb_groups.items():
        if not rows:
            continue
        s = _stats([r["ret"] for r in rows])
        result["segments"]["by_earnings_blackout"][grp] = s
        print(f"  Earnings {grp}: n={s['n']}  wr={s['win_rate']}  avg={s['avg_pct']}%")

    # ── 6. Score quartile × regime interaction ──────────────────────────────
    bull_records = regime_groups.get("Bull", [])
    bear_records = regime_groups.get("Bear", [])
    result["segments"]["score_quartile_by_regime"] = {}
    for regime_label, reg_rows in [("Bull", bull_records), ("Bear", bear_records)]:
        if len(reg_rows) < 20:
            continue
        sorted_rows = sorted(reg_rows, key=lambda x: x["score"])
        q = len(sorted_rows) // 4
        quartiles = {}
        for i, label in enumerate(["Q1_low", "Q2", "Q3", "Q4_high"]):
            chunk = sorted_rows[i * q : (i + 1) * q] if i < 3 else sorted_rows[i * q :]
            if chunk:
                s = _stats([r["ret"] for r in chunk])
                s["score_range"] = f"{chunk[0]['score']:.1f}–{chunk[-1]['score']:.1f}"
                quartiles[label] = s
        result["segments"]["score_quartile_by_regime"][regime_label] = quartiles
        print(
            f"  Score quartile × {regime_label}: "
            + " | ".join(
                f"{k}: wr={v['win_rate']} avg={v['avg_pct']}%" for k, v in quartiles.items()
            )
        )

    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[regime_cs] report -> {OUT}")
    return result


if __name__ == "__main__":
    run()
