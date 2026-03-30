"""
Tests for auth.db_backend — Sprint 22.

Validates the SQLite/PostgreSQL backend abstraction layer.
"""

from __future__ import annotations

import pytest


class TestSQLiteBackend:
    """SQLite backend tests (default path)."""

    def test_sqlite_is_default(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        from auth.db_backend import get_backend, reset_backend

        reset_backend()
        backend = get_backend()
        assert backend.backend_name == "sqlite"
        reset_backend()

    def test_sqlite_connection_works(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        from auth.db_backend import SQLiteBackend

        db_path = str(tmp_path / "test.db")
        backend = SQLiteBackend(db_path=db_path)

        with backend.connection() as conn:
            conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
            conn.execute("INSERT INTO t (val) VALUES (?)", ("hello",))

        with backend.connection() as conn:
            row = conn.execute("SELECT val FROM t").fetchone()
            assert row[0] == "hello"

    def test_sqlite_rollback_on_error(self, tmp_path):
        from auth.db_backend import SQLiteBackend

        db_path = str(tmp_path / "test_rb.db")
        backend = SQLiteBackend(db_path=db_path)

        with backend.connection() as conn:
            conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")

        with pytest.raises(Exception), backend.connection() as conn:
            conn.execute("INSERT INTO t (id) VALUES (1)")
            raise RuntimeError("force rollback")

        with backend.connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM t").fetchone()
            assert row[0] == 0  # rolled back


class TestBackendFactory:
    """Test the get_backend() factory function."""

    def test_default_is_sqlite(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        from auth.db_backend import get_backend, reset_backend

        reset_backend()
        backend = get_backend()
        assert backend.backend_name == "sqlite"
        reset_backend()

    def test_postgres_url_selects_postgres(self, monkeypatch):
        monkeypatch.setenv(
            "DATABASE_URL", "postgresql://user:pass@localhost:5432/db"
        )  # pragma: allowlist secret
        from auth.db_backend import get_backend, reset_backend

        reset_backend()
        backend = get_backend()
        assert backend.backend_name == "postgresql"
        reset_backend()

    def test_sqlite_url_selects_sqlite(self, tmp_path, monkeypatch):
        db_path = str(tmp_path / "custom.db")
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
        from auth.db_backend import get_backend, reset_backend

        reset_backend()
        backend = get_backend()
        assert backend.backend_name == "sqlite"
        reset_backend()

    def test_singleton_returns_same_instance(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        from auth.db_backend import get_backend, reset_backend

        reset_backend()
        b1 = get_backend()
        b2 = get_backend()
        assert b1 is b2
        reset_backend()

    def test_reset_clears_singleton(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        from auth.db_backend import get_backend, reset_backend

        reset_backend()
        b1 = get_backend()
        reset_backend()
        b2 = get_backend()
        assert b1 is not b2
        reset_backend()
