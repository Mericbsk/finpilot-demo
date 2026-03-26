"""PostgreSQL Migration Helper — Sprint 5 R6

Provides utilities to migrate from SQLite to PostgreSQL.
The actual migration is a phased plan:

Phase 1 (Current): SQLite remains for dev/single-user mode
Phase 2 (Next):    PostgreSQL for production multi-user deployment
Phase 3 (Future):  Connection pooling, read replicas

Usage:
    python -m scripts.pg_migration --check      # Verify PG connectivity
    python -m scripts.pg_migration --migrate     # Run migration
    python -m scripts.pg_migration --rollback    # Revert to SQLite
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)

# PostgreSQL connection params from environment
PG_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", "5432")),
    "database": os.getenv("PG_DATABASE", "finpilot"),
    "user": os.getenv("PG_USER", "finpilot"),
    "password": os.getenv("PG_PASSWORD", ""),
}

SQLITE_PATH = os.getenv("FINPILOT_DB_PATH", "data/finpilot.db")

# Table mapping: SQLite DDL → PostgreSQL DDL differences
SCHEMA_TRANSFORMS = {
    "INTEGER PRIMARY KEY AUTOINCREMENT": "SERIAL PRIMARY KEY",
    "TEXT": "TEXT",
    "REAL": "DOUBLE PRECISION",
    "INTEGER DEFAULT 1": "BOOLEAN DEFAULT TRUE",
    "INTEGER DEFAULT 0": "BOOLEAN DEFAULT FALSE",
}


def check_pg_available() -> bool:
    """Check if PostgreSQL is reachable."""
    try:
        import psycopg2

        conn = psycopg2.connect(**PG_CONFIG)
        conn.close()
        logger.info(
            "PostgreSQL connection OK: %s:%s/%s",
            PG_CONFIG["host"],
            PG_CONFIG["port"],
            PG_CONFIG["database"],
        )
        return True
    except ImportError:
        logger.error("psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    except Exception as e:
        logger.error("PostgreSQL connection failed: %s", e)
        return False


def export_sqlite_data(db_path: str = SQLITE_PATH) -> dict[str, list[dict[str, Any]]]:
    """Export all SQLite tables to a dict of lists of dicts."""
    if not os.path.exists(db_path):
        logger.warning("SQLite database not found: %s", db_path)
        return {}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row["name"] for row in cursor.fetchall()]

    data: dict[str, list[dict[str, Any]]] = {}
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")  # noqa: S608  # nosec B608
        rows = cursor.fetchall()
        data[table] = [dict(row) for row in rows]
        logger.info("Exported %d rows from %s", len(rows), table)

    conn.close()
    return data


def generate_pg_schema() -> str:
    """Generate PostgreSQL CREATE TABLE statements from the auth schema."""
    return """
-- FinPilot PostgreSQL Schema (auto-generated from SQLite)
-- Sprint 5 R6 migration target

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    display_name TEXT,
    avatar_url TEXT,
    role TEXT DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    last_login TIMESTAMPTZ,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    device_info TEXT,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    last_activity TIMESTAMPTZ NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS portfolios (
    id TEXT PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cash DOUBLE PRECISION DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS positions (
    id TEXT PRIMARY KEY,
    portfolio_id TEXT NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    shares DOUBLE PRECISION NOT NULL,
    avg_price DOUBLE PRECISION NOT NULL,
    opened_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE(portfolio_id, symbol)
);

CREATE TABLE IF NOT EXISTS trades (
    id TEXT PRIMARY KEY,
    portfolio_id TEXT NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    shares DOUBLE PRECISION NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    total DOUBLE PRECISION NOT NULL,
    commission DOUBLE PRECISION DEFAULT 0,
    executed_at TIMESTAMPTZ NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS watchlists (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    symbols TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS user_settings (
    user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    settings_json JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS quiz_scores (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    category TEXT,
    played_at TIMESTAMPTZ NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_positions_portfolio ON positions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_trades_portfolio ON trades(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_quiz_user ON quiz_scores(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_played ON quiz_scores(played_at);
"""


def migrate_data_to_pg(data: dict[str, list[dict[str, Any]]]) -> bool:
    """Insert exported SQLite data into PostgreSQL."""
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        logger.error("psycopg2 not installed")
        return False

    conn = psycopg2.connect(**PG_CONFIG)
    cursor = conn.cursor()

    try:
        # Create schema
        cursor.execute(generate_pg_schema())

        # Insert data table by table
        for table, rows in data.items():
            if not rows:
                continue
            columns = rows[0].keys()
            col_str = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(columns))
            insert_sql = (
                f"INSERT INTO {table} ({col_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"  # noqa: S608
            )

            values = [tuple(row[c] for c in columns) for row in rows]
            psycopg2.extras.execute_batch(cursor, insert_sql, values)
            logger.info("Migrated %d rows to %s", len(values), table)

        conn.commit()
        logger.info("Migration complete!")
        return True
    except Exception as e:
        conn.rollback()
        logger.error("Migration failed: %s", e)
        return False
    finally:
        cursor.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="FinPilot SQLite → PostgreSQL migration")
    parser.add_argument("--check", action="store_true", help="Check PostgreSQL connectivity")
    parser.add_argument("--migrate", action="store_true", help="Run full migration")
    parser.add_argument("--export-schema", action="store_true", help="Print PG schema SQL")
    parser.add_argument("--export-data", action="store_true", help="Export SQLite data to JSON")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if args.check:
        ok = check_pg_available()
        raise SystemExit(0 if ok else 1)

    if args.export_schema:
        print(generate_pg_schema())
        return

    if args.export_data:
        data = export_sqlite_data()
        print(json.dumps(data, indent=2, default=str))
        return

    if args.migrate:
        if not check_pg_available():
            raise SystemExit(1)
        data = export_sqlite_data()
        if not data:
            logger.warning("No data to migrate")
            raise SystemExit(0)
        ok = migrate_data_to_pg(data)
        raise SystemExit(0 if ok else 1)

    parser.print_help()


if __name__ == "__main__":
    main()
