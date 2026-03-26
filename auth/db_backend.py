"""
Database backend abstraction for FinPilot — Sprint 22.

Provides a unified DatabaseBackend interface that supports both:
  - SQLite  (default, zero-config, single-user dev/demo)
  - PostgreSQL (production, multi-user, concurrent access)

The active backend is selected by the DATABASE_URL environment variable:
  - Not set / "sqlite:///..."  → SQLite (existing behaviour)
  - "postgresql://..."         → PostgreSQL via psycopg2

Usage:
    from auth.db_backend import get_backend

    backend = get_backend()
    with backend.connection() as conn:
        conn.execute("SELECT 1")

Migration path:
    1. Set DATABASE_URL=postgresql://finpilot:pw@localhost:5432/finpilot  # pragma: allowlist secret
    2. Run: docker-compose --profile db up -d
    3. The pg_init.sql script auto-creates all tables
    4. Use scripts/migrate_csv_to_db.py to migrate existing data
"""

from __future__ import annotations

import logging
import os
import sqlite3
from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DatabaseBackend(ABC):
    """Abstract database backend — SQLite or PostgreSQL."""

    @abstractmethod
    @contextmanager
    def connection(self) -> Generator[Any, None, None]:
        """Yield a DB-API 2.0 connection with auto-commit/rollback."""
        ...

    @abstractmethod
    def initialize(self) -> None:
        """Create tables if they don't exist."""
        ...

    @property
    @abstractmethod
    def backend_name(self) -> str: ...


class SQLiteBackend(DatabaseBackend):
    """SQLite backend — existing behaviour, zero config."""

    def __init__(self, db_path: str = "data/finpilot.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    @property
    def backend_name(self) -> str:
        return "sqlite"

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        """Delegate to existing Database.initialize() logic."""
        # Import here to avoid circular deps
        from auth.database import Database

        db = Database(self.db_path)
        db.initialize()


class PostgreSQLBackend(DatabaseBackend):
    """PostgreSQL backend — production, multi-user."""

    def __init__(self, dsn: str):
        self.dsn = dsn
        self._pool = None

    @property
    def backend_name(self) -> str:
        return "postgresql"

    def _get_connection(self):
        """Create a psycopg2 connection (lazy import)."""
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError as exc:
            raise ImportError(
                "psycopg2 is required for PostgreSQL backend. "
                "Install with: pip install psycopg2-binary"
            ) from exc
        conn = psycopg2.connect(self.dsn)
        conn.autocommit = False
        return conn

    @contextmanager
    def connection(self) -> Generator[Any, None, None]:
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        """Tables created by pg_init.sql via Docker entrypoint."""
        logger.info("PostgreSQL backend — tables managed by pg_init.sql")
        # Verify connectivity
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            logger.info("✅ PostgreSQL connection verified")


# ===========================================================================
# Factory
# ===========================================================================

_backend_instance: DatabaseBackend | None = None


def get_backend() -> DatabaseBackend:
    """
    Return the active DatabaseBackend singleton.

    Selection logic:
      1. DATABASE_URL env var → parse scheme
      2. If starts with "postgresql://" → PostgreSQLBackend
      3. Otherwise → SQLiteBackend (default)
    """
    global _backend_instance
    if _backend_instance is not None:
        return _backend_instance

    database_url = os.environ.get("DATABASE_URL", "")

    if database_url.startswith("postgresql://") or database_url.startswith("postgres://"):
        _backend_instance = PostgreSQLBackend(dsn=database_url)
        logger.info("Database backend: PostgreSQL")
    else:
        # Default: SQLite
        db_path = (
            database_url.replace("sqlite:///", "")
            if database_url.startswith("sqlite:")
            else "data/finpilot.db"
        )
        _backend_instance = SQLiteBackend(db_path=db_path)
        logger.info(f"Database backend: SQLite ({db_path})")

    return _backend_instance


def reset_backend() -> None:
    """Reset singleton — useful for testing."""
    global _backend_instance
    _backend_instance = None
