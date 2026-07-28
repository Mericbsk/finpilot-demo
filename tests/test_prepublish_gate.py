"""Tests for the pre-publish gate + the repaired NUL integrity check (Bolum 3)."""

from __future__ import annotations

from datetime import date

import pytest
from distribution.prepublish_gate import check_export_health

TODAY = date.today().isoformat()


def _row(**overrides):
    base = {
        "symbol": "RIOT",
        "selection_eligible": True,
        "entry_ok": True,
        "execution_feasible": True,
        "data_quality_tier": "Tier 1",
        "ranking_method": "legacy_quality",
        "conviction_tier": "B",
        "tier": "",
    }
    base.update(overrides)
    return base


def _export(rows=None, **overrides):
    base = {
        "date": TODAY,
        "universe": 1812,
        "scan_complete": True,
        "results": rows if rows is not None else [_row()],
    }
    base.update(overrides)
    return base


def test_healthy_export_passes():
    assert check_export_health(_export()) == []


def test_stale_date_blocks():
    problems = check_export_health(_export(date="2026-01-01"))
    assert any("bayat" in p for p in problems)


def test_empty_results_block():
    problems = check_export_health(_export(rows=[]))
    assert any("results" in p for p in problems)


def test_missing_contract_fields_block():
    row = _row()
    del row["selection_eligible"]
    del row["ranking_method"]
    problems = check_export_health(_export(rows=[row]))
    assert any("sözleşme alanları eksik" in p for p in problems)


def test_incomplete_scan_blocks():
    problems = check_export_health(_export(scan_complete=False))
    assert any("scan_complete" in p for p in problems)


def test_degraded_run_blocks():
    """The 2026-07-24 class: full scan, zero graded & zero eligible rows."""
    rows = [
        _row(symbol=f"S{i}", selection_eligible=False, conviction_tier="", tier="")
        for i in range(50)
    ]
    problems = check_export_health(_export(rows=rows))
    assert any("zenginleştirme boş" in p for p in problems)


def test_low_usable_ratio_blocks_full_scan():
    rows = [_row(symbol="GOOD", scan_status="graded")]
    rows.extend(_row(symbol=f"MISSING{i}", scan_status="unavailable") for i in range(1800))
    problems = check_export_health(_export(rows=rows))
    assert any("usable/graded oranı düşük" in p for p in problems)


def test_graded_but_ineligible_rows_do_not_trip_quality_gate():
    """A day where grades exist but nothing passes selection is legitimate."""
    rows = [_row(selection_eligible=False)]  # still has conviction_tier=B
    assert check_export_health(_export(rows=rows)) == []


def test_legacy_confirm_tier_counts_as_enriched():
    rows = [_row(selection_eligible=False, conviction_tier="", tier="CONFIRM")]
    assert check_export_health(_export(rows=rows)) == []


# ── repaired NUL check (snapshot_builder.read_json_object) ───────────────────
# Requires Python 3.11+ (repo standard); skipped on older interpreters.

try:
    from distribution import snapshot_builder
except ImportError:  # pragma: no cover - sandbox interpreters below 3.11
    snapshot_builder = None

needs_311 = pytest.mark.skipif(snapshot_builder is None, reason="needs Python 3.11+ (datetime.UTC)")


@needs_311
def test_read_json_object_rejects_real_nul_bytes(tmp_path):
    bad = tmp_path / "corrupt.json"
    bad.write_bytes(b'{"date": "2026-07-24"}\x00\x00\x00')
    with pytest.raises(ValueError, match="NUL"):
        snapshot_builder.read_json_object(bad)


@needs_311
def test_read_json_object_accepts_clean_json(tmp_path):
    good = tmp_path / "ok.json"
    good.write_bytes(b'{"date": "2026-07-24"}')
    assert snapshot_builder.read_json_object(good) == {"date": "2026-07-24"}


@needs_311
def test_company_from_db_uses_symbols_table(tmp_path, monkeypatch):
    import sqlite3

    db = tmp_path / "fp.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE symbols (ticker TEXT PRIMARY KEY, name TEXT)")
    con.execute("INSERT INTO symbols VALUES ('RIOT', 'Riot Platforms, Inc. Common Stock')")
    con.commit()
    con.close()
    monkeypatch.setenv("FINPILOT_DB", str(db))
    snapshot_builder._COMPANY_CACHE.clear()
    assert snapshot_builder._company_from_db("RIOT") == "Riot Platforms, Inc."
    assert snapshot_builder._company_from_db("NOPE") == ""
