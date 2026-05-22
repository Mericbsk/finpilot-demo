"""watchlist_signals table

Revision ID: 002
Revises: 001
Create Date: 2026-05-20
"""

from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS watchlist_signals (
            id           TEXT PRIMARY KEY,
            symbol       TEXT NOT NULL,
            signal       TEXT DEFAULT '—',
            entry_price  REAL DEFAULT 0.0,
            stop_loss    REAL DEFAULT 0.0,
            take_profit  REAL DEFAULT 0.0,
            score        REAL DEFAULT 0.0,
            regime       TEXT DEFAULT '',
            sentiment    TEXT DEFAULT '',
            risk_reward  REAL DEFAULT 0.0,
            reason       TEXT DEFAULT '',
            explanation  TEXT DEFAULT '',
            source_model TEXT DEFAULT 'scanner_v2',
            notes        TEXT DEFAULT '',
            tags         TEXT DEFAULT '[]',
            status_lifecycle TEXT DEFAULT 'new',
            signal_date  TEXT NOT NULL,
            added_at     TEXT NOT NULL
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_watchlist_signals_symbol
        ON watchlist_signals(symbol)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_watchlist_signals_date
        ON watchlist_signals(signal_date)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_watchlist_signals_date")
    op.execute("DROP INDEX IF EXISTS idx_watchlist_signals_symbol")
    op.execute("DROP TABLE IF EXISTS watchlist_signals")
