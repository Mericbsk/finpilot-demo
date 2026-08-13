"""Restatement detector pilot (Gate 1.4) — research-only, Level A.

Detects silent historical revisions in the price cache: if a bar for the same
(symbol, date) changes between two cache snapshots, that is a restatement.
This pilot compares the current cache against a reference snapshot and reports
any drifted bars.

Rationale: backtests assume historical bars are immutable. If the provider
restates them, past results silently shift. This detector makes restatement
visible.
"""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_CACHE = Path("data/price_cache")


def load_bars_map(cache_dir: Path, symbol: str) -> dict[str, dict]:
    """Return {date: bar} for a symbol, tolerating dirty rows."""
    path = cache_dir / f"{symbol}.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out = {}
    for item in raw if isinstance(raw, list) else []:
        if isinstance(item, dict) and item.get("date"):
            out[str(item["date"])] = item
    return out


def detect_restatements(
    reference: dict[str, dict], current: dict[str, dict], *, tol: float = 1e-9
) -> list[dict]:
    """Compare two {date: bar} maps; return bars whose close changed."""
    drifted = []
    for date, ref_bar in reference.items():
        cur_bar = current.get(date)
        if cur_bar is None:
            continue
        ref_close = ref_bar.get("close")
        cur_close = cur_bar.get("close")
        if ref_close is None or cur_close is None:
            continue
        if abs(float(cur_close) - float(ref_close)) > tol:
            drifted.append(
                {
                    "date": date,
                    "ref_close": ref_close,
                    "cur_close": cur_close,
                    "abs_change_pct": abs(float(cur_close) / float(ref_close) - 1.0) * 100.0
                    if float(ref_close) > 0
                    else None,
                }
            )
    return drifted


def pilot_report(reference_dir: Path, current_dir: Path, symbols: list[str]) -> dict:
    """Compare a set of symbols between two cache snapshots."""
    per_symbol = {}
    total_drifted = 0
    for sym in symbols:
        ref = load_bars_map(reference_dir, sym)
        cur = load_bars_map(current_dir, sym)
        drifted = detect_restatements(ref, cur)
        per_symbol[sym] = {
            "bars_compared": len(ref),
            "drifted": len(drifted),
            "examples": drifted[:3],
        }
        total_drifted += len(drifted)
    return {
        "symbols": len(symbols),
        "total_drifted_bars": total_drifted,
        "per_symbol": per_symbol,
        "interpretation": (
            "no restatement detected"
            if total_drifted == 0
            else f"{total_drifted} bars restated — historical results may shift"
        ),
    }
