"""Double-Sort: Momentum × Volume Turnover

Hypothesis: High momentum + high turnover → potential mean-reversion risk
            High momentum + low turnover → genuine breakout candidate

Method:
  1. Load all barrier-resolved signals from DB
  2. Primary sort (Dimension 1): momentum signal
       - Preferred: momentum_3d_pct from payload (new scanner_v2+)
       - Fallback:  score (0-18 range, available in all records)
  3. Secondary sort (Dimension 2): volume quality
       - Preferred: volume_multiple from payload (new scanner_v2+)
       - Fallback:  risk_reward (available in all records as quality proxy)
  4. Build 3×3 sort table → win_rate, avg_pct per cell
  5. Save to data/momentum_turnover_sort.json + print summary
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "finpilot.db"
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "momentum_turnover_sort.json"


def _tertile_label(rank: int) -> str:
    return {1: "Low", 2: "Mid", 3: "High"}[rank]


def main() -> None:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    cur.execute(
        """
        SELECT id, payload_json, resolved_pct_barrier, resolved_status_barrier
        FROM signals_archive
        WHERE resolved_pct_barrier IS NOT NULL
          AND resolved_status_barrier IN ('resolved_win', 'resolved_loss', 'expired_win', 'expired_loss')
        """
    )
    rows = cur.fetchall()
    con.close()

    print(f"Loaded {len(rows):,} barrier-resolved signals")

    records = []
    dim1_source = "unknown"
    dim2_source = "unknown"

    for row in rows:
        try:
            payload = (
                json.loads(row["payload_json"])
                if isinstance(row["payload_json"], str)
                else (row["payload_json"] or {})
            )
        except Exception:
            payload = {}

        dim1 = None  # momentum proxy
        dim2 = None  # volume/quality proxy

        # Dimension 1: momentum_3d_pct → score fallback
        for key in ("momentum_3d_pct", "momentum_3d", "mom_3d_pct"):
            v = payload.get(key)
            if v is not None:
                try:
                    dim1 = float(v)
                    dim1_source = "momentum_3d_pct"
                    break
                except (ValueError, TypeError):
                    pass
        if dim1 is None:
            v = payload.get("score")
            if v is not None:
                try:
                    dim1 = float(v)
                    dim1_source = "score (fallback)"
                except (ValueError, TypeError):
                    pass

        # Dimension 2: volume_multiple → risk_reward fallback
        for key in ("volume_multiple", "vol_mult", "volume_mult"):
            v = payload.get(key)
            if v is not None:
                try:
                    dim2 = float(v)
                    dim2_source = "volume_multiple"
                    break
                except (ValueError, TypeError):
                    pass
        if dim2 is None:
            v = payload.get("risk_reward")
            if v is not None:
                try:
                    dim2 = float(v)
                    dim2_source = "risk_reward (fallback)"
                except (ValueError, TypeError):
                    pass

        if dim1 is None or dim2 is None:
            continue

        outcome = float(row["resolved_pct_barrier"])
        win = 1 if row["resolved_status_barrier"] in ("resolved_win", "expired_win") else 0
        records.append(
            {
                "dim1": dim1,
                "dim2": dim2,
                "outcome_pct": outcome,
                "win": win,
            }
        )

    print(f"Usable records: {len(records):,} | Dim1={dim1_source} | Dim2={dim2_source}")

    if len(records) < 30:
        print("Insufficient usable records. Saving stub.")
        result = {
            "ran_at": pd.Timestamp.now().isoformat(timespec="seconds"),
            "n_usable": len(records),
            "dim1_source": dim1_source,
            "dim2_source": dim2_source,
            "note": "Insufficient data.",
            "grid": {},
        }
        OUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return

    df = pd.DataFrame(records)

    # ── Dimension 1: Score-band (fixed-boundary cut) ─────────────────────────
    # Score dist: 0→1057, 1-3→3710, 4-18→135, 18+→218 (new_100 schema)
    # Use schema-aligned bins so ties don't collapse tertiles.
    def _score_band(s: float) -> str:
        if s <= 0:
            return "zero"
        if s <= 3:
            return "low_1-3"
        if s <= 18:
            return "mid_4-18"
        return "high_19+"

    df["dim1_band"] = df["dim1"].apply(_score_band)
    # Ordered categories for display
    band_order = ["zero", "low_1-3", "mid_4-18", "high_19+"]

    # ── Dimension 2: Risk-Reward (fixed bins: 0 / 1-2 / >2) ─────────────────
    # RR unique: {0.0, ~1.0, 2.0, 2.67, 3.67} (only ~7 values)
    def _rr_band(r: float) -> str:
        if r <= 0:
            return "none"
        if r <= 2:
            return "normal"
        return "high_RR"

    df["dim2_band"] = df["dim2"].apply(_rr_band)
    rr_order = ["none", "normal", "high_RR"]

    grid: dict[str, dict] = {}
    print(f"\n  {'Score Band':>12} × {'Risk-Reward':<10} | n    | WR%   | Avg%   | PF")
    print("  " + "-" * 67)

    for sb in band_order:
        for rb in rr_order:
            mask = (df["dim1_band"] == sb) & (df["dim2_band"] == rb)
            sub = df[mask]
            if len(sub) == 0:
                continue
            n = len(sub)
            wr = sub["win"].mean()
            avg = sub["outcome_pct"].mean()
            wins = sub[sub["win"] == 1]["outcome_pct"]
            losses = sub[sub["win"] == 0]["outcome_pct"]
            pf = (
                (wins.sum() / abs(losses.sum()))
                if len(losses) > 0 and losses.sum() != 0
                else float("inf")
            )

            key = f"score_{sb}_rr_{rb}"
            grid[key] = {
                "score_band": sb,
                "rr_band": rb,
                "n": n,
                "win_rate": round(wr, 4),
                "avg_pct": round(avg, 4),
                "profit_factor": round(pf, 3) if pf != float("inf") else None,
            }
            print(f"  {sb:>12}  RR={rb:<10} | {n:<4} | {wr*100:5.1f} | {avg:+7.3f} | {pf:.2f}")

    valid = {k: v for k, v in grid.items() if v["n"] >= 20}
    best_key = max(valid, key=lambda k: valid[k]["win_rate"]) if valid else None
    worst_key = min(valid, key=lambda k: valid[k]["win_rate"]) if valid else None

    if best_key:
        print(
            f"\nBest  cell (n≥20): {best_key} → wr={valid[best_key]['win_rate']*100:.1f}% avg={valid[best_key]['avg_pct']:+.3f}%"
        )
    if worst_key:
        print(
            f"Worst cell (n≥20): {worst_key} → wr={valid[worst_key]['win_rate']*100:.1f}% avg={valid[worst_key]['avg_pct']:+.3f}%"
        )

    result = {
        "ran_at": pd.Timestamp.now().isoformat(timespec="seconds"),
        "n_total_barrier": len(rows),
        "n_usable": len(df),
        "n_dropped_missing_fields": len(rows) - len(records),
        "dim1_source": dim1_source,
        "dim2_source": dim2_source,
        "hypothesis": (
            "Dim1=momentum proxy, Dim2=volume/quality proxy. "
            "High momentum + High vol → mean-reversion risk. "
            "High momentum + Low vol → breakout candidate."
        ),
        "note": (
            "Using fallback fields (score, risk_reward) because momentum_3d_pct "
            "and volume_multiple are only present in signals generated after scanner_v2 "
            "with full payload. Rerun after 200+ new signals to get proper double-sort."
        )
        if dim1_source != "momentum_3d_pct"
        else None,
        "best_cell": best_key,
        "worst_cell": worst_key,
        "grid": grid,
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved → {OUT_PATH}")


if __name__ == "__main__":
    main()
