"""Selectivity funnel report — how does 1800+ scanned become N published?

Reads the immutable published-evidence export (scan_export_<date>_published.json,
written by publish_now) or any export file, and prints the elimination funnel
stage by stage. Answers the Bolum 3.3 question: is high selectivity intended
design or a broken filter?

Usage:
    python scripts/funnel_report.py                     # today's published copy
    python scripts/funnel_report.py --file path.json    # any export
    python scripts/funnel_report.py --date 2026-07-25

Stdlib only, read-only.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "data" / "distribution"


def _grade_like(row: dict) -> bool:
    conv = str(row.get("conviction_tier") or "").strip().upper()
    if conv in ("A", "B", "C"):
        return True
    return str(row.get("tier") or "").strip().upper() in ("CONFIRM", "TRIGGER")


STAGES = [
    ("taranan satır", lambda r: True),
    (
        "veri kalitesi ok/partial (missing değil)",
        lambda r: str(r.get("data_quality_status")) != "missing",
    ),
    ("yön sinyali var (direction=True)", lambda r: r.get("direction") is True),
    ("edge pozitif (edge_label=ok)", lambda r: str(r.get("edge_label")) == "ok"),
    ("grade'li (conviction/tier)", _grade_like),
    ("entry_ok", lambda r: r.get("entry_ok") is True),
    ("selection_eligible", lambda r: r.get("selection_eligible") is True),
    ("execution_feasible", lambda r: r.get("execution_feasible") is True),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", help="explicit export json path")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()

    if args.file:
        path = Path(args.file)
    else:
        path = EXPORT_DIR / f"scan_export_{args.date}_published.json"
        if not path.exists():
            path = EXPORT_DIR / "scan_export_latest.json"
            print(f"(published kopya yok — {path.name} kullanılıyor)")
    if not path.exists():
        print(f"export bulunamadı: {path}", file=sys.stderr)
        return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    rows = [r for r in (data.get("results") or []) if isinstance(r, dict)]
    print(
        f"\nSEÇİCİLİK HUNİSİ — {path.name} (date={data.get('date')}, "
        f"universe={data.get('universe')}, run_id={data.get('run_id', '—')})\n"
    )

    remaining = rows
    prev = len(rows)
    for label, pred in STAGES:
        remaining = [r for r in remaining if pred(r)]
        dropped = prev - len(remaining)
        print(f"  {label:<42} {len(remaining):>5}  (-{dropped})")
        prev = len(remaining)

    survivors = [str(r.get("symbol")) for r in remaining][:20]
    print(f"\n  huniden çıkanlar: {survivors or 'YOK'}")
    if len(rows) and not remaining:
        print("  ⚠️ hiç aday kalmadı — hangi aşamada sıfırlandığına yukarıdan bak.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
