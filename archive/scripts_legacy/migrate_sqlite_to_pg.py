#!/usr/bin/env python3
r"""
FinPilot — SQLite → PostgreSQL Migration Script
================================================

Sprint 22: Tek seferlik veri göçü.

Usage:
    # PostgreSQL çalıştır
    docker-compose --profile db up -d

    # Migrate et
    DATABASE_URL=postgresql://finpilot:finpilot_secret@localhost:5432/finpilot \  # pragma: allowlist secret
        python scripts/migrate_sqlite_to_pg.py [--sqlite-path data/finpilot.db] [--dry-run]

Prerequisites:
    - PostgreSQL running (docker-compose --profile db up -d)
    - pg_init.sql already applied (Docker entrypoint auto-applies)
    - pip install psycopg2-binary

What it migrates:
    - users, sessions, portfolios, positions, trades
    - watchlists, user_settings, quiz_scores

Column mapping handles SQLite ↔ PostgreSQL differences:
    - TEXT id → UUID (auto-cast via uuid_generate_v4 or existing UUID strings)
    - INTEGER booleans → BOOLEAN
    - TEXT timestamps → TIMESTAMPTZ
    - TEXT JSON → JSONB
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ============================================
# Table migration config
# ============================================
# Each entry: (table_name, sqlite_columns, pg_columns, column_transform_fn)
# If pg_columns is None, same as sqlite_columns.

TABLES = [
    "users",
    "sessions",
    "portfolios",
    "positions",
    "trades",
    "watchlists",
    "user_settings",
    "quiz_scores",
]

# SQLite column → PG column renames (per table)
COLUMN_RENAMES: dict[str, dict[str, str]] = {
    "positions": {
        "shares": "quantity",
        "avg_price": "avg_entry_price",
    },
    "trades": {
        "shares": "quantity",
        "executed_at": "created_at",
    },
    "user_settings": {
        "settings_json": "settings",
    },
    "quiz_scores": {
        "category": "quiz_type",
        "played_at": "created_at",
    },
}


def get_sqlite_conn(db_path: str) -> sqlite3.Connection:
    """Open SQLite connection."""
    if not Path(db_path).exists():
        logger.error("SQLite database not found: %s", db_path)
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_pg_conn(dsn: str):
    """Open PostgreSQL connection."""
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        logger.error("psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)
    conn = psycopg2.connect(dsn)
    return conn


def get_sqlite_tables(sqlite_conn: sqlite3.Connection) -> list[str]:
    """Return tables that actually exist in the SQLite DB."""
    cursor = sqlite_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return [row[0] for row in cursor.fetchall()]


def get_sqlite_columns(sqlite_conn: sqlite3.Connection, table: str) -> list[str]:
    """Return column names for a SQLite table."""
    cursor = sqlite_conn.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cursor.fetchall()]


def get_pg_columns(pg_conn, table: str) -> list[str]:
    """Return column names for a PostgreSQL table."""
    cursor = pg_conn.cursor()
    cursor.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = %s ORDER BY ordinal_position",
        (table,),
    )
    return [row[0] for row in cursor.fetchall()]


def transform_value(table: str, col: str, value):
    """Transform a SQLite value to PostgreSQL-compatible value."""
    if value is None:
        return None

    # Boolean columns (SQLite INTEGER → PG BOOLEAN)
    bool_columns = {"is_active", "is_verified"}
    if col in bool_columns:
        return bool(value)

    # JSON columns (SQLite TEXT → PG JSONB)
    json_columns = {"settings_json", "settings", "symbols", "metadata", "details", "raw_response"}
    if col in json_columns:
        if isinstance(value, str):
            try:
                # Validate JSON and return as string (psycopg2 handles JSONB casting)

                parsed = json.loads(value)
                return json.dumps(parsed)
            except (json.JSONDecodeError, ValueError):
                return value
        return json.dumps(value) if not isinstance(value, str) else value

    return value


def migrate_table(
    sqlite_conn: sqlite3.Connection,
    pg_conn,
    table: str,
    dry_run: bool = False,
) -> int:
    """Migrate a single table from SQLite to PostgreSQL."""
    # Get SQLite data
    sqlite_columns = get_sqlite_columns(sqlite_conn, table)
    rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()  # nosec B608 — table is from internal schema, not user input

    if not rows:
        logger.info("  ⏭  %s: empty table, skipping", table)
        return 0

    # Get PG columns
    pg_columns = get_pg_columns(pg_conn, table)
    renames = COLUMN_RENAMES.get(table, {})

    # Build column mapping: sqlite_col → pg_col
    col_mapping: list[tuple[str, str]] = []
    for sqlite_col in sqlite_columns:
        pg_col = renames.get(sqlite_col, sqlite_col)
        if pg_col in pg_columns:
            col_mapping.append((sqlite_col, pg_col))
        else:
            logger.debug("  Column %s.%s → %s not in PG, skipping", table, sqlite_col, pg_col)

    if not col_mapping:
        logger.warning("  ⚠️  %s: no matching columns, skipping", table)
        return 0

    # Extra PG columns with defaults (updated_at if not in SQLite)
    pg_target_cols = [pg_col for _, pg_col in col_mapping]
    placeholders = ", ".join(["%s"] * len(pg_target_cols))
    col_list = ", ".join(pg_target_cols)

    # Build ON CONFLICT clause for upsert (skip duplicates)
    # Primary key is typically 'id' or composite
    conflict_col = "id" if "id" in pg_target_cols else pg_target_cols[0]
    insert_sql = (  # nosec B608 — table/columns from internal schema
        f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "
        f"ON CONFLICT ({conflict_col}) DO NOTHING"
    )

    if dry_run:
        logger.info("  🔍 %s: %d rows → DRY RUN (columns: %s)", table, len(rows), col_list)
        return len(rows)

    cursor = pg_conn.cursor()
    migrated = 0
    errors = 0

    for row in rows:
        values = []
        for sqlite_col, pg_col in col_mapping:
            raw = (
                row[sqlite_col]
                if isinstance(row, sqlite3.Row)
                else row[sqlite_columns.index(sqlite_col)]
            )
            values.append(transform_value(table, pg_col, raw))

        try:
            cursor.execute(insert_sql, values)
            migrated += 1
        except Exception as e:
            errors += 1
            if errors <= 3:
                logger.warning("  ⚠️  %s row error: %s", table, e)
            pg_conn.rollback()
            # Continue with next row after rollback — re-open implicit transaction
            continue

    pg_conn.commit()
    logger.info("  ✅ %s: %d/%d rows migrated (%d errors)", table, migrated, len(rows), errors)
    return migrated


def main():
    parser = argparse.ArgumentParser(description="Migrate FinPilot SQLite → PostgreSQL")
    parser.add_argument(
        "--sqlite-path",
        default="data/finpilot.db",
        help="Path to SQLite database (default: data/finpilot.db)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without writing to PostgreSQL",
    )
    args = parser.parse_args()

    # PostgreSQL DSN from environment
    dsn = os.environ.get("DATABASE_URL", "")
    if not dsn.startswith("postgresql://") and not dsn.startswith("postgres://"):
        logger.error(
            "DATABASE_URL must be set to a PostgreSQL DSN.\n"
            "Example: DATABASE_URL=postgresql://finpilot:finpilot_secret@localhost:5432/finpilot"  # pragma: allowlist secret
        )
        sys.exit(1)

    # Connect
    logger.info("=" * 60)
    logger.info("FinPilot SQLite → PostgreSQL Migration")
    logger.info("=" * 60)
    logger.info("SQLite : %s", args.sqlite_path)
    logger.info("PG DSN : %s", dsn.split("@")[-1] if "@" in dsn else "(hidden)")
    logger.info("Dry run: %s", args.dry_run)
    logger.info("-" * 60)

    sqlite_conn = get_sqlite_conn(args.sqlite_path)
    existing_tables = get_sqlite_tables(sqlite_conn)
    logger.info("SQLite tables found: %s", existing_tables)

    pg_conn = get_pg_conn(dsn) if not args.dry_run else None

    total = 0
    for table in TABLES:
        if table not in existing_tables:
            logger.info("  ⏭  %s: not in SQLite, skipping", table)
            continue
        if pg_conn is not None or args.dry_run:
            count = migrate_table(
                sqlite_conn,
                pg_conn if not args.dry_run else sqlite_conn,  # dry-run only reads
                table,
                dry_run=args.dry_run,
            )
            total += count

    sqlite_conn.close()
    if pg_conn and not args.dry_run:
        pg_conn.close()

    logger.info("-" * 60)
    logger.info("Migration complete. Total rows processed: %d", total)
    if args.dry_run:
        logger.info("(DRY RUN — no data was written to PostgreSQL)")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
