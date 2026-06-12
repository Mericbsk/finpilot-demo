"""signal_events table — agent pipeline event log

Revision ID: 003
Revises: 002
Create Date: 2026-06-12

Stores every state-transition emitted by `core/pipeline.py` so that
the UI can render a per-cycle agent activity timeline and operators
can audit which step produced which result.
"""

from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = "003"
down_revision: Union[str, Sequence[str], None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS signal_events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id   TEXT    NOT NULL,
            symbol      TEXT    NOT NULL,
            from_state  TEXT,
            to_state    TEXT    NOT NULL,
            agent       TEXT    NOT NULL,
            payload     TEXT,
            ts          DATETIME NOT NULL DEFAULT (datetime('now')),
            success     BOOLEAN  NOT NULL DEFAULT 1,
            error       TEXT
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_signal_events_symbol
            ON signal_events (symbol, ts DESC)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_signal_events_signal_id
            ON signal_events (signal_id)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS signal_events")
