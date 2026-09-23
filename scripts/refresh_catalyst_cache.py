#!/usr/bin/env python3
"""refresh_catalyst_cache.py — SEC EDGAR catalyst cache'i evren-capli yeniler.

Level B (Meric onayi, 2026-09-03): scanner/catalyst.py::refresh_catalyst_cache
fonksiyonunu universe sembolleri icin calistirir ve refresh sonrasi kalite
kapisini artifact olarak raporlar.

Guvenlik:
- Varsayilan DRY-RUN (--report-only): ag cagrisi YOK, yalnizca mevcut cache
  ve evren kapsama raporu basar.
- Gercek fetch icin --fetch gerekir. SEC rate-limit ~6.6 istek/sn
  (_RATE_LIMIT_SLEEP=0.15). FINPILOT_ENABLE_EDGAR_CATALYST flag'ine DOKUNMAZ;
  bu script yalnizca cache'i doldurur, production skoru degistirmez.

Kullanim (repo kokunden):
  python scripts/refresh_catalyst_cache.py --report-only
  python scripts/refresh_catalyst_cache.py --fetch --limit 40      # pilot
  python scripts/refresh_catalyst_cache.py --fetch                 # tam evren

Kaynak: reports/data_repair_diagnosis_2026-09-03.md (catalyst koken analizi)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CACHE = Path("data/catalyst_cache.json")
EDGAR_DIR = Path("data/edgar_cache")
UNIVERSE_SOURCES = [
    Path("data/distribution/scan_export_latest.json"),
    Path("data/backtest_out/sector_map_full.csv"),
]
OUT = Path("data/backtest_out/catalyst_refresh_quality.json")


def load_universe(limit: int | None) -> list[str]:
    """Evren sembollerini topla (scan export -> sector map sirasiyla)."""
    syms: list[str] = []
    exp = UNIVERSE_SOURCES[0]
    if exp.exists():
        try:
            data = json.loads(exp.read_text(encoding="utf-8"))
            rows = data.get("results") or []
            syms = [
                str(r.get("symbol", "")).upper()
                for r in rows
                if isinstance(r, dict) and r.get("symbol")
            ]
        except (OSError, ValueError):
            syms = []
    if not syms and UNIVERSE_SOURCES[1].exists():
        import csv

        with UNIVERSE_SOURCES[1].open(encoding="utf-8") as f:
            syms = [row["symbol"].upper() for row in csv.DictReader(f) if row.get("symbol")]
    syms = sorted(dict.fromkeys(syms))
    return syms[:limit] if limit else syms


def quality_gate(factors: dict[str, float], universe: list[str], meta: dict) -> dict:
    """Refresh sonrasi kalite kapisi — artifact olarak yazilir."""
    n = len(universe)
    covered = [s for s in universe if s in factors]
    nonzero = {k: v for k, v in factors.items() if v}
    vals = list(factors.values())
    return {
        "timestamp": datetime.now(tz=UTC).isoformat(),
        "universe_n": n,
        "covered_n": len(covered),
        "coverage_pct": round(100 * len(covered) / n, 2) if n else 0.0,
        "nonzero_n": len(nonzero),
        "nonzero_pct_of_covered": round(100 * len(nonzero) / len(covered), 2) if covered else 0.0,
        "factor_distribution": {
            "min": min(vals) if vals else None,
            "max": max(vals) if vals else None,
            "mean": round(sum(vals) / len(vals), 4) if vals else None,
        },
        "sign_counts": dict(
            Counter("pos" if v > 0 else ("neg" if v < 0 else "zero") for v in vals)
        ),
        "meta": meta,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="EDGAR catalyst cache refresh + quality gate")
    ap.add_argument("--fetch", action="store_true", help="Gercek SEC fetch (yoksa report-only)")
    ap.add_argument("--limit", type=int, default=None, help="Pilot: ilk N sembol")
    ap.add_argument("--days", type=int, default=7, help="Filing lookback (varsayilan 7)")
    ap.add_argument("--report-only", action="store_true", help="Ag yok, yalniz rapor")
    args = ap.parse_args()

    os.environ.setdefault("SEC_EDGAR_USER_AGENT", "FinPilot/1.0 (contact: admin@finpilot.local)")
    universe = load_universe(args.limit)
    print(f"[catalyst] universe: {len(universe)} sembol (limit={args.limit})")

    if not args.fetch or args.report_only:
        # Guvenli rapor: mevcut cache + edgar ham verisi durumu
        existing = {}
        if CACHE.exists():
            try:
                existing = json.loads(CACHE.read_text(encoding="utf-8")).get("factors", {})
            except (OSError, ValueError):
                existing = {}
        edgar_files = len(list(EDGAR_DIR.glob("sub_*.json"))) if EDGAR_DIR.exists() else 0
        gate = quality_gate(
            existing,
            universe,
            {
                "mode": "report-only",
                "edgar_raw_files": edgar_files,
                "cache_updated": (
                    json.loads(CACHE.read_text(encoding="utf-8")).get("updated")
                    if CACHE.exists()
                    else None
                ),
            },
        )
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(gate, indent=2), encoding="utf-8")
        print(json.dumps(gate, indent=2))
        print("[catalyst] REPORT-ONLY: fetch yapilmadi. Gercek fetch icin --fetch kullan.")
        return 0

    # Gercek fetch — scanner.catalyst.refresh_catalyst_cache
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scanner.catalyst import refresh_catalyst_cache

    print(f"[catalyst] FETCH basliyor: {len(universe)} sembol, days={args.days}")
    factors = refresh_catalyst_cache(universe, days=args.days)
    gate = quality_gate(factors, universe, {"mode": "fetch", "days": args.days})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(gate, indent=2), encoding="utf-8")
    print(json.dumps(gate, indent=2))
    ok = gate["coverage_pct"] >= 90.0
    print(
        f"[catalyst] kalite kapisi: coverage={gate['coverage_pct']}% -> {'PASS' if ok else 'BELOW-90'}"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
