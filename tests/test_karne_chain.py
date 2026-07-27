"""Tests for the manual-flow karne chain (Bolum 1):

distribution/karne.py          — direct-from-DB scorecard
distribution/archive_bridge.py — publish-time signal archiving + continuity alarm
"""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta

import pytest
from distribution.archive_bridge import (
    archive_snapshot_candidates,
    check_archive_continuity,
)
from distribution.karne import compute_karne_db

TODAY = date.today().isoformat()


@pytest.fixture()
def db(tmp_path):
    path = tmp_path / "finpilot_test.db"
    con = sqlite3.connect(path)
    con.execute(
        """CREATE TABLE watchlist_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT, entry_price REAL, stop_loss REAL, take_profit REAL,
            score REAL, conviction_tier TEXT, tier TEXT,
            status_lifecycle TEXT, signal_date TEXT)"""
    )
    con.execute(
        """CREATE TABLE signals_archive (
            id TEXT PRIMARY KEY, symbol TEXT, ts TEXT, score REAL,
            finpilot_score REAL, payload_json TEXT, resolved_status TEXT,
            resolved_pct REAL)"""
    )
    con.commit()
    con.close()
    return path


def _add_signal(path, symbol, tier, status, day=TODAY, tier_legacy=""):
    con = sqlite3.connect(path)
    con.execute(
        "INSERT INTO watchlist_signals "
        "(symbol, entry_price, stop_loss, take_profit, score, conviction_tier,"
        " tier, status_lifecycle, signal_date) VALUES (?, 10, 9, 12, 55, ?, ?, ?, ?)",
        (symbol, tier, tier_legacy, status, day),
    )
    con.commit()
    con.close()


# ── compute_karne_db ─────────────────────────────────────────────────────────


def test_karne_counts_only_decided_outcomes(db):
    # maturity_days=0 → same-day fixtures count (gate tested separately below)
    _add_signal(db, "AAA", "B", "resolved_win")
    _add_signal(db, "BBB", "B", "resolved_loss")
    _add_signal(db, "CCC", "B", "watching")  # open — must NOT count
    karne = compute_karne_db(db_path=db, days=5, maturity_days=0)
    # entry 10 / sl 9 / tp 12 → win +20%, loss -10% → avg_pnl = +5.0
    assert karne["by_grade"]["B"] == {"n": 2, "hit_rate": 0.5, "avg_pnl": 5.0}


def test_karne_maps_legacy_confirm_tier_to_b(db):
    _add_signal(db, "AAA", "", "resolved_win", tier_legacy="CONFIRM")
    karne = compute_karne_db(db_path=db, days=5, maturity_days=0)
    assert karne["by_grade"]["B"]["n"] == 1


def test_karne_maturity_gate_excludes_fresh_signals(db):
    # A same-day resolved signal must NOT count under the default maturity gate
    _add_signal(db, "FRESH", "B", "resolved_win")
    assert compute_karne_db(db_path=db, days=365) is None
    # …but counts once the gate is disabled
    assert compute_karne_db(db_path=db, days=5, maturity_days=0)["by_grade"]["B"]["n"] == 1


def test_karne_matured_signal_counts_with_expectancy(db):
    old = (date.today() - timedelta(days=40)).isoformat()
    _add_signal(db, "MAT", "C", "resolved_loss", day=old)  # -10% barrier loss
    karne = compute_karne_db(db_path=db, days=365)  # maturity default 30 → 40d counts
    assert karne["by_grade"]["C"] == {"n": 1, "hit_rate": 0.0, "avg_pnl": -10.0}


def test_karne_respects_window(db):
    old = (date.today() - timedelta(days=40)).isoformat()
    _add_signal(db, "OLD", "C", "resolved_loss", day=old)
    assert compute_karne_db(db_path=db, days=5) is None
    karne = compute_karne_db(db_path=db, days=60)
    assert karne["by_grade"]["C"]["n"] == 1


def test_karne_empty_db_returns_none(db):
    assert compute_karne_db(db_path=db, days=5) is None


def test_karne_missing_db_returns_none(tmp_path):
    assert compute_karne_db(db_path=tmp_path / "nope.db", days=5) is None


# ── archive_snapshot_candidates ──────────────────────────────────────────────


def _snapshot(tickers=("RIOT", "DVN")):
    return {
        "date": TODAY,
        "candidates": [
            {
                "ticker": t,
                "grade": "B",
                "metrics": {"price": 20.0, "stop_loss": 18.0, "take_profit": 25.0},
            }
            for t in tickers
        ],
    }


def test_archive_inserts_and_is_idempotent(db):
    first = archive_snapshot_candidates(_snapshot(), db_path=db)
    second = archive_snapshot_candidates(_snapshot(), db_path=db)
    assert first == {"archived": 2, "skipped": 0, "date": TODAY}
    assert second == {"archived": 0, "skipped": 2, "date": TODAY}


def test_archive_enriches_from_watchlist(db):
    _add_signal(db, "RIOT", "B", "new")  # entry 10 / sl 9 / tp 12 / score 55
    archive_snapshot_candidates(_snapshot(("RIOT",)), db_path=db)
    con = sqlite3.connect(db)
    score, payload = con.execute(
        "SELECT score, payload_json FROM signals_archive WHERE symbol='RIOT'"
    ).fetchone()
    con.close()
    assert score == 55
    assert '"entry_price": 10' in payload  # resolver-ready field from watchlist


def test_archive_falls_back_to_snapshot_metrics(db):
    archive_snapshot_candidates(_snapshot(("DVN",)), db_path=db)
    con = sqlite3.connect(db)
    (payload,) = con.execute(
        "SELECT payload_json FROM signals_archive WHERE symbol='DVN'"
    ).fetchone()
    con.close()
    assert '"entry_price": 20.0' in payload


def test_archive_rows_start_as_new(db):
    archive_snapshot_candidates(_snapshot(), db_path=db)
    con = sqlite3.connect(db)
    statuses = {r[0] for r in con.execute("SELECT resolved_status FROM signals_archive")}
    con.close()
    assert statuses == {"new"}


# ── check_archive_continuity ─────────────────────────────────────────────────


def test_continuity_warns_on_stale_archive(db):
    stale = (date.today() - timedelta(days=30)).isoformat()
    con = sqlite3.connect(db)
    con.execute(
        "INSERT INTO signals_archive (id, symbol, ts, resolved_status) VALUES ('x','AAA',?,'new')",
        (stale + "T09:00:00+00:00",),
    )
    con.commit()
    con.close()
    warning = check_archive_continuity(db_path=db)
    assert warning is not None and "büyümüyor" in warning


def test_continuity_ok_when_fresh(db):
    archive_snapshot_candidates(_snapshot(), db_path=db)
    assert check_archive_continuity(db_path=db) is None


def test_continuity_warns_on_empty_archive(db):
    assert check_archive_continuity(db_path=db) == "signals_archive tamamen boş"
