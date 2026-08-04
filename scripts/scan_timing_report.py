"""Scanner timing report — P0.1 (2026-07-31 scanner audit).

Reads the append-only ``data/distribution/scan_timing.jsonl`` (one line per /scan
call, written by api.routers.scan._append_scan_timing_log) and aggregates it into
the full-universe view that was previously a blind spot:

  * per-day wall-clock span (first→last batch of the day)
  * summed eval seconds (compute cost across all batches)
  * total symbols scanned and total yfinance-fallback symbols (+ ratio)
  * per-timeframe Alpaca(IEX) miss totals — WHICH timeframe drove the fallback

Observation only — reads a log, changes nothing. Safe to run anytime.

Usage:
    python scripts/scan_timing_report.py                 # default log path
    python scripts/scan_timing_report.py path/to.jsonl   # explicit path
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

_DEFAULT_PATH = Path("data/distribution/scan_timing.jsonl")


def load_records(path: Path) -> list[dict]:
    """Load JSONL timing records; skip malformed lines defensively."""
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except (ValueError, TypeError):
            continue
    return out


def aggregate_by_day(records: list[dict]) -> dict[str, dict]:
    """Group per-batch records into per-day rollups.

    Returns {date: {batches, symbols, eval_s_sum, yf_fallback, ts_min, ts_max,
    alpaca_miss{tf: n}}}. Pure function — unit-testable without any live scan.
    """
    days: dict[str, dict] = {}
    for r in records:
        date = str(r.get("date") or (str(r.get("ts") or "")[:10]) or "?")
        d = days.setdefault(
            date,
            {
                "batches": 0,
                "symbols": 0,
                "eval_s_sum": 0.0,
                "yf_fallback": 0,
                "ts_min": None,
                "ts_max": None,
                "alpaca_miss": defaultdict(int),
            },
        )
        d["batches"] += 1
        d["symbols"] += int(r.get("symbols") or 0)
        d["eval_s_sum"] += float(r.get("eval_s") or 0.0)
        yf = r.get("yf_fallback")
        if isinstance(yf, (int, float)) and yf >= 0:
            d["yf_fallback"] += int(yf)
        ts = r.get("ts")
        if ts:
            d["ts_min"] = ts if d["ts_min"] is None else min(d["ts_min"], ts)
            d["ts_max"] = ts if d["ts_max"] is None else max(d["ts_max"], ts)
        for tf, n in (r.get("alpaca_miss") or {}).items():
            try:
                d["alpaca_miss"][tf] += int(n)
            except (TypeError, ValueError):
                continue
    return days


def _wall_clock_seconds(ts_min: str | None, ts_max: str | None) -> float | None:
    if not ts_min or not ts_max:
        return None
    try:
        from datetime import datetime

        return (datetime.fromisoformat(ts_max) - datetime.fromisoformat(ts_min)).total_seconds()
    except Exception:
        return None


def format_report(days: dict[str, dict]) -> str:
    if not days:
        return (
            "Kayıt yok. Bir tarama çalıştıktan sonra "
            "data/distribution/scan_timing.jsonl dolacak ve bu rapor anlam kazanacak."
        )
    lines = ["=== Scanner Timing Raporu (gün bazında) ===", ""]
    for date in sorted(days):
        d = days[date]
        wall = _wall_clock_seconds(d["ts_min"], d["ts_max"])
        wall_txt = f"{wall / 60:.1f} dk" if wall is not None else "bilinmiyor"
        ratio = (d["yf_fallback"] / d["symbols"] * 100) if d["symbols"] else 0.0
        miss = ", ".join(f"{tf}={n}" for tf, n in sorted(d["alpaca_miss"].items())) or "—"
        lines += [
            f"{date}:",
            f"  batch sayısı         : {d['batches']}",
            f"  toplam sembol        : {d['symbols']}",
            f"  eval_s toplamı       : {d['eval_s_sum']:.1f}s  (~{d['eval_s_sum'] / 60:.1f} dk hesap)",
            f"  tam-tur duvar-saati  : {wall_txt}  (ilk→son batch)",
            f"  yfinance fallback    : {d['yf_fallback']}  ({ratio:.1f}% sembol)",
            f"  Alpaca-miss (tf)     : {miss}",
            "",
        ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else _DEFAULT_PATH
    records = load_records(path)
    days = aggregate_by_day(records)
    print(format_report(days))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
