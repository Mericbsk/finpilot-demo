"""Measure export and production Attention Score overlap on the same live rows.

Only rows with an exact shortlist scan date, local OHLCV coverage, and every
field required by both formulas are compared. Missing overlap is reported as
data availability, never imputed.

Usage:
  python -m research.attention_score_formula_overlap_2026_08_14
  python -m research.attention_score_formula_overlap_2026_08_14 \
      --shortlist data/shortlists/<file>.csv --output data/backtest_out/<name>.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scanner.features import (
    compute_atr_pct,
    compute_dist_52w_high,
    compute_gap_pct,
    compute_rvol_daily,
)

DEFAULT_SHORTLIST = Path("data/shortlists/shortlist_20260814_1157.csv")
PRICE_CACHE = Path("data/price_cache")
DEFAULT_OUTPUT = Path("data/backtest_out/attention_score_formula_overlap_2026-08-14.json")


def export_score(row: dict[str, float]) -> int:
    score = 0
    if abs(row.get("gap_pct", 0.0) or 0.0) >= 3:
        score += 25
    if (row.get("atr_pct_real", 0.0) or 0.0) >= 6:
        score += 25
    if (row.get("rvol", 0.0) or 0.0) >= 2.0:
        score += 15
    if (row.get("dist_52w_high", 1.0) or 1.0) < 0.3:
        score += 15
    if (row.get("lottery_factor", 0.0) or 0.0) >= 0.6:
        score += 10
    if (row.get("squeeze_factor", 0.0) or 0.0) >= 0.5:
        score += 10
    return score


def production_score(row: pd.Series) -> int:
    score = 0
    if (row.get("volume_multiple", 0.0) or 0.0) >= 1.5:
        score += 25
    if (row.get("ann_vol_pct", 0.0) or 0.0) >= 60:
        score += 25
    if (row.get("lottery_factor", 0.0) or 0.0) >= 0.6:
        score += 15
    if (row.get("overnight_gap_factor", 0.0) or 0.0) >= 0.1:
        score += 15
    if (row.get("ema_gap_pct", 0.0) or 0.0) <= -10:
        score += 10
    if (row.get("squeeze_factor", 0.0) or 0.0) >= 0.5:
        score += 10
    return score


def load_cache_frame(symbol: str, scan_date: str) -> pd.DataFrame | None:
    path = PRICE_CACHE / f"{symbol}.json"
    if not path.exists():
        return None
    bars = pd.DataFrame(json.loads(path.read_text(encoding="utf-8")))
    required = {"date", "open", "high", "close", "volume"}
    if not required.issubset(bars.columns):
        return None
    bars["date"] = pd.to_datetime(bars["date"], errors="coerce")
    bars = bars.dropna(subset=["date"])
    bars = bars[bars["date"].dt.strftime("%Y-%m-%d") <= scan_date].copy()
    if bars.empty or bars.iloc[-1]["date"].strftime("%Y-%m-%d") != scan_date:
        return None
    return bars.rename(
        columns={"open": "Open", "high": "High", "close": "Close", "volume": "Volume"}
    ).set_index("date")


def main(shortlist_path: Path = DEFAULT_SHORTLIST, output_path: Path = DEFAULT_OUTPUT) -> None:
    live = pd.read_csv(shortlist_path)
    required_live = {
        "symbol",
        "timestamp",
        "volume_multiple",
        "ann_vol_pct",
        "lottery_factor",
        "overnight_gap_factor",
        "ema_gap_pct",
        "squeeze_factor",
    }
    missing_live = sorted(required_live - set(live.columns))
    live["scan_date"] = pd.to_datetime(live["timestamp"], errors="coerce").dt.strftime("%Y-%m-%d")

    candidates = 0
    exact_date_rows = 0
    comparable: list[dict[str, object]] = []
    for _, row in live.iterrows():
        candidates += 1
        if pd.isna(row["scan_date"]):
            continue
        bars = load_cache_frame(str(row["symbol"]), str(row["scan_date"]))
        if bars is None:
            continue
        exact_date_rows += 1
        if missing_live or row[list(required_live)].isna().any():
            continue
        export_inputs = {
            "gap_pct": compute_gap_pct(bars),
            "atr_pct_real": compute_atr_pct(bars),
            "rvol": compute_rvol_daily(bars),
            "dist_52w_high": compute_dist_52w_high(bars),
            "lottery_factor": float(row["lottery_factor"]),
            "squeeze_factor": float(row["squeeze_factor"]),
        }
        comparable.append(
            {
                "symbol": str(row["symbol"]),
                "scan_date": str(row["scan_date"]),
                "export_score": export_score(export_inputs),
                "production_score": production_score(row),
            }
        )

    export_scores = np.array([item["export_score"] for item in comparable], dtype=float)
    production_scores = np.array([item["production_score"] for item in comparable], dtype=float)
    if len(comparable) >= 2 and export_scores.std() > 0 and production_scores.std() > 0:
        correlation = float(
            pd.Series(export_scores).corr(pd.Series(production_scores), method="spearman")
        )
    else:
        correlation = None
    agreement = float((export_scores == production_scores).mean()) if comparable else None

    result = {
        "status": "exploratory",
        "production_change": False,
        "locked_oos": "not_opened",
        "source_live_shortlist": str(shortlist_path),
        "source_price_cache": str(PRICE_CACHE),
        "formula_definitions": {
            "export": "gap_pct, atr_pct_real, rvol, dist_52w_high, lottery_factor, squeeze_factor",
            "production": "volume_multiple, ann_vol_pct, lottery_factor, overnight_gap_factor, ema_gap_pct, squeeze_factor",
        },
        "candidate_rows": candidates,
        "exact_scan_date_rows": exact_date_rows,
        "missing_live_columns": missing_live,
        "comparable_rows": len(comparable),
        "spearman_correlation": correlation,
        "exact_score_agreement": agreement,
        "comparisons": comparable,
        "interpretation": (
            "No same-date comparable rows; equivalence is not measurable from the available local live data."
            if not comparable
            else "Scores were compared only on exact same-date rows with all required fields."
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--shortlist",
        type=Path,
        default=DEFAULT_SHORTLIST,
        help="Live shortlist CSV to compare against (default: the 2026-08-14 reference CSV).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Artifact path (default: the original 2026-08-14 artifact, unchanged when omitted).",
    )
    args = parser.parse_args()
    main(shortlist_path=args.shortlist, output_path=args.output)
