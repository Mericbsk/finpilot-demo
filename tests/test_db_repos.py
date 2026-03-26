"""
Tests for Sprint 20 — Signal & Scan Result Repositories.

Uses a temporary SQLite file for isolation (in-memory doesn't persist
across separate connections in the Database context manager).
"""

from __future__ import annotations

import pytest

from auth.database import Database, ScanResultRepository, SignalRepository

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db(tmp_path):
    """Fresh temp-file database for each test."""
    db_path = str(tmp_path / "test.db")
    d = Database(db_path)
    d.initialize()
    yield d
    d.drop_all()


@pytest.fixture()
def signal_repo(db):
    return SignalRepository(db)


@pytest.fixture()
def scan_repo(db):
    return ScanResultRepository(db)


def _make_signal(**overrides) -> dict:
    base = {
        "timestamp": "2025-06-01 14:00",
        "symbol": "AAPL",
        "price": 195.50,
        "stop_loss": 190.0,
        "take_profit": 205.0,
        "score": 7.5,
        "strength": 4.2,
        "regime": "bullish",
        "sentiment": "positive",
        "onchain": "",
        "entry_ok": True,
        "summary": "Strong breakout",
        "reason": "EMA cross + volume",
    }
    base.update(overrides)
    return base


# ===========================================================================
# SIGNAL REPOSITORY
# ===========================================================================


class TestSignalRepoSave:
    def test_save_single(self, signal_repo):
        row_id = signal_repo.save(_make_signal())
        assert row_id >= 1
        assert signal_repo.count() == 1

    def test_save_batch(self, signal_repo):
        signals = [
            _make_signal(symbol="AAPL"),
            _make_signal(symbol="MSFT"),
            _make_signal(symbol="GOOGL"),
        ]
        count = signal_repo.save_batch(signals)
        assert count == 3
        assert signal_repo.count() == 3

    def test_save_batch_empty(self, signal_repo):
        count = signal_repo.save_batch([])
        assert count == 0


class TestSignalRepoQuery:
    def test_get_by_symbol(self, signal_repo):
        signal_repo.save_batch(
            [
                _make_signal(symbol="AAPL"),
                _make_signal(symbol="AAPL"),
                _make_signal(symbol="MSFT"),
            ]
        )
        results = signal_repo.get_by_symbol("AAPL")
        assert len(results) == 2
        assert all(r["symbol"] == "AAPL" for r in results)

    def test_get_recent(self, signal_repo):
        signal_repo.save_batch([_make_signal(symbol=f"SYM{i}") for i in range(5)])
        results = signal_repo.get_recent(limit=3)
        assert len(results) == 3

    def test_get_open(self, signal_repo):
        signal_repo.save(_make_signal(symbol="AAPL"))
        signal_repo.save(_make_signal(symbol="TSLA"))
        open_signals = signal_repo.get_open()
        assert len(open_signals) == 2


class TestSignalRepoOutcome:
    def test_update_outcome(self, signal_repo):
        row_id = signal_repo.save(_make_signal())
        ok = signal_repo.update_outcome(
            signal_id=row_id,
            status="tp_hit",
            outcome_price=205.0,
            outcome_date="2025-06-10",
            outcome_pct=4.9,
        )
        assert ok is True

        # Verify updated
        rows = signal_repo.get_recent(limit=1)
        assert rows[0]["status"] == "tp_hit"
        assert rows[0]["outcome_price"] == 205.0

    def test_update_nonexistent(self, signal_repo):
        ok = signal_repo.update_outcome(signal_id=999, status="sl_hit")
        assert ok is False


class TestSignalRepoStats:
    def test_empty_stats(self, signal_repo):
        stats = signal_repo.get_stats()
        assert stats["total"] == 0
        assert stats["win_rate"] == 0.0

    def test_stats_with_data(self, signal_repo):
        signal_repo.save_batch(
            [
                _make_signal(symbol="AAPL"),
                _make_signal(symbol="MSFT"),
                _make_signal(symbol="GOOGL"),
            ]
        )
        # Close one as TP
        signal_repo.update_outcome(1, "tp_hit")
        signal_repo.update_outcome(2, "sl_hit")

        stats = signal_repo.get_stats()
        assert stats["total"] == 3
        assert stats["open"] == 1
        assert stats["tp_hit"] == 1
        assert stats["sl_hit"] == 1
        assert stats["unique_symbols"] == 3
        assert stats["win_rate"] == 50.0


# ===========================================================================
# SCAN RESULT REPOSITORY
# ===========================================================================


class TestScanResultRepoSave:
    def test_save_scan(self, scan_repo):
        results = [
            {"symbol": "AAPL", "price": 195.5, "score": 8},
            {"symbol": "MSFT", "price": 420.0, "score": 7},
        ]
        count = scan_repo.save_scan(
            scan_id="scan_20250601_1400",
            scan_timestamp="2025-06-01T14:00:00",
            results=results,
            source_file="shortlist_20250601_1400.csv",
        )
        assert count == 2
        assert scan_repo.count() == 2

    def test_save_scan_empty(self, scan_repo):
        count = scan_repo.save_scan("id", "ts", [])
        assert count == 0


class TestScanResultRepoQuery:
    def test_get_scan(self, scan_repo):
        results = [
            {"symbol": "AAPL", "price": 195.5, "score": 8},
            {"symbol": "MSFT", "price": 420.0, "score": 6},
        ]
        scan_repo.save_scan("s1", "2025-06-01T14:00:00", results)

        rows = scan_repo.get_scan("s1")
        assert len(rows) == 2
        # Ordered by score DESC
        assert rows[0]["symbol"] == "AAPL"

    def test_get_recent_scans(self, scan_repo):
        for i in range(5):
            scan_repo.save_scan(
                f"scan_{i}",
                f"2025-06-0{i + 1}T10:00:00",
                [{"symbol": "AAPL", "price": 100 + i, "score": i}],
            )
        recent = scan_repo.get_recent_scans(limit=3)
        assert len(recent) == 3
        # Most recent first
        assert recent[0]["scan_id"] == "scan_4"

    def test_get_symbol_history(self, scan_repo):
        scan_repo.save_scan(
            "s1",
            "2025-06-01",
            [
                {"symbol": "AAPL", "price": 195, "score": 7},
                {"symbol": "MSFT", "price": 420, "score": 6},
            ],
        )
        scan_repo.save_scan(
            "s2",
            "2025-06-02",
            [
                {"symbol": "AAPL", "price": 200, "score": 8},
            ],
        )

        history = scan_repo.get_symbol_history("AAPL")
        assert len(history) == 2

    def test_count_and_scan_count(self, scan_repo):
        scan_repo.save_scan("s1", "ts1", [{"symbol": "A", "price": 1, "score": 1}])
        scan_repo.save_scan(
            "s2",
            "ts2",
            [
                {"symbol": "B", "price": 2, "score": 2},
                {"symbol": "C", "price": 3, "score": 3},
            ],
        )
        assert scan_repo.count() == 3
        assert scan_repo.scan_count() == 2

    def test_get_all_as_dataframe(self, scan_repo):
        scan_repo.save_scan(
            "s1",
            "2025-06-01",
            [
                {"symbol": "AAPL", "price": 195, "score": 7},
            ],
        )
        df = scan_repo.get_all_as_dataframe()
        assert len(df) == 1
        assert "symbol" in df.columns
