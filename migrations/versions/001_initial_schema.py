"""initial_schema

Revision ID: 001
Revises:
Create Date: 2026-05-08 18:36:39.108274

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            display_name TEXT,
            avatar_url TEXT,
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            is_verified INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_login TEXT,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until TEXT
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            access_token TEXT NOT NULL,
            refresh_token TEXT NOT NULL,
            device_info TEXT,
            ip_address TEXT,
            user_agent TEXT,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            last_activity TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            id TEXT PRIMARY KEY,
            user_id TEXT UNIQUE NOT NULL,
            cash REAL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id TEXT PRIMARY KEY,
            portfolio_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            shares REAL NOT NULL,
            avg_price REAL NOT NULL,
            opened_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
            UNIQUE(portfolio_id, symbol)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id TEXT PRIMARY KEY,
            portfolio_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            shares REAL NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL,
            commission REAL DEFAULT 0,
            executed_at TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS watchlists (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            symbols TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id TEXT PRIMARY KEY,
            settings_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS quiz_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            category TEXT,
            played_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            price REAL,
            stop_loss REAL,
            take_profit REAL,
            score REAL,
            strength REAL,
            regime TEXT,
            sentiment TEXT,
            onchain TEXT,
            entry_ok INTEGER DEFAULT 0,
            summary TEXT,
            reason TEXT,
            status TEXT DEFAULT 'open',
            outcome_price REAL,
            outcome_date TEXT,
            outcome_pct REAL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS scan_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id TEXT NOT NULL,
            scan_timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            price REAL,
            stop_loss REAL,
            take_profit REAL,
            score REAL,
            strength REAL,
            regime TEXT,
            sentiment TEXT,
            entry_ok INTEGER DEFAULT 0,
            summary TEXT,
            source_file TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS buy_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            entry_price REAL NOT NULL,
            stop_loss REAL,
            take_profit REAL,
            risk_reward REAL,
            score REAL,
            strength REAL,
            regime TEXT,
            sentiment REAL,
            position_size REAL,
            kelly_fraction REAL,
            reason TEXT,
            scan_source TEXT,
            status TEXT DEFAULT 'active',
            exit_price REAL,
            exit_date TEXT,
            pnl_pct REAL,
            pnl_dollar REAL,
            alpaca_order_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(date, symbol)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS alpaca_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            buy_signal_id INTEGER,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            qty REAL NOT NULL,
            order_type TEXT DEFAULT 'limit',
            limit_price REAL,
            stop_price REAL,
            time_in_force TEXT DEFAULT 'day',
            status TEXT DEFAULT 'new',
            filled_price REAL,
            filled_qty REAL,
            filled_at TEXT,
            submitted_at TEXT NOT NULL,
            raw_response TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (buy_signal_id) REFERENCES buy_signals(id)
        )
    """)

    # Indexes
    op.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_positions_portfolio ON positions(portfolio_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_trades_portfolio ON trades(portfolio_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_quiz_user ON quiz_scores(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_scan_results_scan ON scan_results(scan_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_scan_results_symbol ON scan_results(symbol)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_buy_signals_date ON buy_signals(date)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_buy_signals_symbol ON buy_signals(symbol)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_alpaca_orders_symbol ON alpaca_orders(symbol)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS alpaca_orders")
    op.execute("DROP TABLE IF EXISTS buy_signals")
    op.execute("DROP TABLE IF EXISTS scan_results")
    op.execute("DROP TABLE IF EXISTS signals")
    op.execute("DROP TABLE IF EXISTS quiz_scores")
    op.execute("DROP TABLE IF EXISTS trades")
    op.execute("DROP TABLE IF EXISTS positions")
    op.execute("DROP TABLE IF EXISTS portfolios")
    op.execute("DROP TABLE IF EXISTS watchlists")
    op.execute("DROP TABLE IF EXISTS user_settings")
    op.execute("DROP TABLE IF EXISTS sessions")
    op.execute("DROP TABLE IF EXISTS users")
