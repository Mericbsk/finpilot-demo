"""Pre-publish gate — the export must PROVE it is publishable.

Runs at the very start of publish_now, before any draft is built. Catches the
two silent-failure classes found in the 2026-07-24 diagnosis:

  1. corrupted / stale / incomplete exports (NUL bytes, wrong date, missing
     contract fields) — the integrity class;
  2. "degraded run" exports: a full-universe scan whose enrichment pipeline
     produced ZERO graded / eligible rows, which would silently publish an
     empty brief — the quality class.

The gate only REPORTS (list of problems). The caller decides to stop.
Stdlib only.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from distribution.scan_contract import minimum_results, minimum_usable_results, usable_result_count

# Contract fields every scan row must carry (mirrors tests/test_scanner_contract.py)
REQUIRED_ROW_FIELDS = frozenset(
    {
        "symbol",
        "selection_eligible",
        "entry_ok",
        "execution_feasible",
        "data_quality_tier",
        "ranking_method",
    }
)


def _grade_like(row: dict[str, Any]) -> bool:
    conv = str(row.get("conviction_tier") or "").strip().upper()
    if conv in ("A", "B", "C"):
        return True
    return str(row.get("tier") or "").strip().upper() in ("CONFIRM", "TRIGGER")


def check_export_health(
    export: dict[str, Any],
    today: str | None = None,
) -> list[str]:
    """Return problems that must block a publish. Empty list == healthy."""
    problems: list[str] = []
    today = today or date.today().isoformat()

    export_date = str(export.get("date") or "")
    if export_date != today:
        problems.append(f"export bayat: date={export_date!r}, bugün={today}")

    rows = export.get("results") or []
    if not isinstance(rows, list) or not rows:
        problems.append("export'ta results yok/boş")
        return problems  # row-level checks are meaningless now

    sample = rows[0]
    missing = REQUIRED_ROW_FIELDS - set(sample)
    if missing:
        problems.append(f"sözleşme alanları eksik: {sorted(missing)}")

    if export.get("scan_complete") is False:
        problems.append("scan_complete=False (tamamlanmamış tarama)")

    # Quality class: a full scan with zero enriched rows means the
    # conviction/selection pipeline did not run — publishing would produce a
    # 0-candidate brief while looking perfectly healthy.
    graded = sum(1 for r in rows if isinstance(r, dict) and _grade_like(r))
    eligible = sum(1 for r in rows if isinstance(r, dict) and r.get("selection_eligible") is True)
    if len(rows) >= minimum_results():
        usable = usable_result_count(rows)
        if usable < minimum_usable_results():
            problems.append(
                f"usable/graded oranı düşük: {usable}/{len(rows)} < "
                f"{minimum_usable_results()}/{minimum_results()} minimum"
            )
    if graded == 0 and eligible == 0:
        problems.append(
            f"zenginleştirme boş görünüyor: {len(rows)} satırda 0 grade'li ve "
            "0 eligible satır — bozuk/eksik koşu olabilir (publish_now --force ile geçilebilir)"
        )

    return problems
