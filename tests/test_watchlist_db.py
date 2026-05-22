"""Tests for api/services/watchlist_db.py (S2-8 CRUD layer).

Uses an in-memory SQLite database injected via monkeypatching get_sync_session,
so no on-disk DB or environment setup is needed.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _in_memory_session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def _make_get_sync_session(factory):
    @contextmanager
    def _get_sync_session():
        session = factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    return _get_sync_session


@pytest.fixture()
def wdb():
    """Isolated watchlist_db module backed by an in-memory SQLite DB."""
    factory = _in_memory_session_factory()
    mock_session = _make_get_sync_session(factory)

    import api.services.watchlist_db as module

    with patch.object(module, "get_sync_session", mock_session):
        module.ensure_table()
        yield module


def _entry(**overrides) -> dict:
    base = {
        "id": "test-id-1",
        "symbol": "AAPL",
        "signal": "BUY",
        "entry_price": 180.0,
        "stop_loss": 170.0,
        "take_profit": 200.0,
        "score": 75.0,
        "regime": "bull",
        "sentiment": "positive",
        "risk_reward": 2.0,
        "reason": "RSI oversold",
        "explanation": "Test signal",
        "source_model": "scanner_v2",
        "notes": "",
        "tags": ["tech"],
        "status_lifecycle": "new",
        "signal_date": "2024-01-15",
        "added_at": "2024-01-15T10:00:00",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# ensure_table
# ---------------------------------------------------------------------------


class TestEnsureTable:
    def test_idempotent(self, wdb):
        wdb.ensure_table()
        wdb.ensure_table()

    def test_empty_after_creation(self, wdb):
        assert wdb.load_active() == []


# ---------------------------------------------------------------------------
# upsert_signal
# ---------------------------------------------------------------------------


class TestUpsertSignal:
    def test_insert_new_signal(self, wdb):
        wdb.upsert_signal(_entry())
        items = wdb.load_active()
        assert len(items) == 1
        assert items[0]["symbol"] == "AAPL"

    def test_upsert_replaces_same_symbol(self, wdb):
        wdb.upsert_signal(_entry(id="id-1", entry_price=180.0))
        wdb.upsert_signal(_entry(id="id-2", entry_price=190.0))
        items = wdb.load_active()
        assert len(items) == 1
        assert items[0]["entry_price"] == 190.0

    def test_tags_roundtrip(self, wdb):
        wdb.upsert_signal(_entry(tags=["tech", "growth"]))
        assert wdb.load_active()[0]["tags"] == ["tech", "growth"]

    def test_multiple_different_symbols(self, wdb):
        wdb.upsert_signal(_entry(id="id-1", symbol="AAPL"))
        wdb.upsert_signal(_entry(id="id-2", symbol="NVDA"))
        symbols = {i["symbol"] for i in wdb.load_active()}
        assert symbols == {"AAPL", "NVDA"}


# ---------------------------------------------------------------------------
# load_active
# ---------------------------------------------------------------------------


class TestLoadActive:
    def test_empty_returns_empty_list(self, wdb):
        assert wdb.load_active() == []

    def test_returns_all_signals(self, wdb):
        for i in range(3):
            wdb.upsert_signal(_entry(id=f"id-{i}", symbol=f"SYM{i}"))
        assert len(wdb.load_active()) == 3

    def test_items_are_dicts_with_symbol(self, wdb):
        wdb.upsert_signal(_entry())
        item = wdb.load_active()[0]
        assert isinstance(item, dict)
        assert "symbol" in item


# ---------------------------------------------------------------------------
# update_field
# ---------------------------------------------------------------------------


class TestUpdateField:
    def test_updates_single_field(self, wdb):
        wdb.upsert_signal(_entry(id="id-1"))
        assert wdb.update_field("id-1", status_lifecycle="active") is True
        assert wdb.load_active()[0]["status_lifecycle"] == "active"

    def test_returns_false_for_missing_id(self, wdb):
        assert wdb.update_field("nonexistent", status_lifecycle="active") is False

    def test_updates_tags_as_list(self, wdb):
        wdb.upsert_signal(_entry(id="id-1"))
        wdb.update_field("id-1", tags=["updated"])
        assert wdb.load_active()[0]["tags"] == ["updated"]

    def test_updates_multiple_fields(self, wdb):
        wdb.upsert_signal(_entry(id="id-1"))
        wdb.update_field("id-1", notes="note", status_lifecycle="tp_hit")
        item = wdb.load_active()[0]
        assert item["notes"] == "note"
        assert item["status_lifecycle"] == "tp_hit"

    def test_no_fields_returns_false(self, wdb):
        assert wdb.update_field("id-1") is False


# ---------------------------------------------------------------------------
# delete_by_symbol
# ---------------------------------------------------------------------------


class TestDeleteBySymbol:
    def test_deletes_existing(self, wdb):
        wdb.upsert_signal(_entry())
        assert wdb.delete_by_symbol("AAPL") == 1
        assert wdb.load_active() == []

    def test_returns_zero_for_missing(self, wdb):
        assert wdb.delete_by_symbol("NOEXIST") == 0

    def test_deletes_only_target(self, wdb):
        wdb.upsert_signal(_entry(id="id-1", symbol="AAPL"))
        wdb.upsert_signal(_entry(id="id-2", symbol="NVDA"))
        wdb.delete_by_symbol("AAPL")
        remaining = wdb.load_active()
        assert len(remaining) == 1
        assert remaining[0]["symbol"] == "NVDA"


# ---------------------------------------------------------------------------
# clear_active
# ---------------------------------------------------------------------------


class TestClearActive:
    def test_clears_all(self, wdb):
        for i in range(3):
            wdb.upsert_signal(_entry(id=f"id-{i}", symbol=f"SYM{i}"))
        wdb.clear_active()
        assert wdb.load_active() == []

    def test_clear_empty_is_safe(self, wdb):
        wdb.clear_active()
        assert wdb.load_active() == []


# ---------------------------------------------------------------------------
# replace_all_active
# ---------------------------------------------------------------------------


class TestReplaceAllActive:
    def test_replaces_all(self, wdb):
        wdb.upsert_signal(_entry(id="old-1", symbol="AAPL"))
        new_items = [
            _entry(id="new-1", symbol="NVDA"),
            _entry(id="new-2", symbol="MSFT"),
        ]
        wdb.replace_all_active(new_items)
        items = wdb.load_active()
        assert len(items) == 2
        assert {i["symbol"] for i in items} == {"NVDA", "MSFT"}

    def test_replace_with_empty_clears(self, wdb):
        wdb.upsert_signal(_entry())
        wdb.replace_all_active([])
        assert wdb.load_active() == []


# ---------------------------------------------------------------------------
# migrate_from_json
# ---------------------------------------------------------------------------


class TestMigrateFromJson:
    def test_imports_valid_json(self, wdb, tmp_path):
        entries = [_entry(id="m1", symbol="AAPL")]
        json_file = tmp_path / "watchlist.json"
        json_file.write_text(json.dumps(entries))

        imported = wdb.migrate_from_json(json_file)
        assert imported == 1
        assert wdb.load_active()[0]["symbol"] == "AAPL"

    def test_skips_if_table_has_data(self, wdb, tmp_path):
        wdb.upsert_signal(_entry())
        json_file = tmp_path / "watchlist.json"
        json_file.write_text(json.dumps([_entry(id="m2", symbol="NVDA")]))

        assert wdb.migrate_from_json(json_file) == 0

    def test_returns_zero_if_file_missing(self, wdb, tmp_path):
        assert wdb.migrate_from_json(tmp_path / "nonexistent.json") == 0

    def test_skips_entries_without_id(self, wdb, tmp_path):
        entries = [{"symbol": "AAPL", "signal": "BUY"}]  # no "id" field
        json_file = tmp_path / "watchlist.json"
        json_file.write_text(json.dumps(entries))

        assert wdb.migrate_from_json(json_file) == 0
