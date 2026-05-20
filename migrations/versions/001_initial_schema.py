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
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # Dialect-specific column types
    pk_int = "INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    bool_default_true = "BOOLEAN DEFAULT TRUE" if is_pg else "INTEGER DEFAULT 1"
    bool_default_false = "BOOLEAN DEFAULT FALSE" if is_pg else "INTEGER DEFAULT 0"
    bool_zero = "BOOLEAN DEFAULT FALSE" if is_pg else "INTEGER DEFAULT 0"
    ts_default_now = "TIMESTAMPTZ NOT NULL DEFAULT NOW()" if is_pg else "TEXT NOT NULL DEFAULT (datetime('now'))"
    ts_optional = "TIMESTAMPTZ" if is_pg else "TEXT"
    ts_required = "TIMESTAMPTZ NOT NULL" if is_pg else "TEXT NOT NULL"
    real_t = "DOUBLE PRECISION" if is_pg else "REAL"

    op.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            display_name TEXT,
            avatar_url TEXT,
            role TEXT DEFAULT 'user',
            is_active {bool_default_true},
            is_verified {bool_default_false},
            created_at {ts_required},
            updated_at {ts_required},
            last_login {ts_optional},
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until {ts_optional}
        )
    """)

    op.execute(f"""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            access_token TEXT NOT NULL,
            refresh_token TEXT NOT NULL,
            device_info TEXT,
            ip_address TEXT,
            user_agent TEXT,
            created_at {ts_required},
            expires_at {ts_required},
            last_activity {ts_required},
            is_active {bool_default_true},
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    op.execute(f"""
        CREATE TABLE IF NOT EXISTS portfolios (
            id TEXT PRIMARY KEY,
            user_id TEXT UNIQUE NOT NULL,
            cash {real_t} DEFAULT 0,
            created_at {ts_required},
            updated_at {ts_required},
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    op.execute(f"""
        CREATE TABLE IF NOT EXISTS positions (
            id TEXT PRIMARY KEY,
            portfolio_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            shares {real_t} NOT NULL,
            avg_price {real_t} NOT NULL,
            opened_at {ts_required},
            updated_at {ts_required},
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
            UNIQUE(portfolio_id, symbol)
        )
    """)

    op.execute(f"""
        CREATE TABLE IF NOT EXISTS trades (
            id TEXT PRIMARY KEY,
            portfolio_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            shares {real_t} NOT NULL,
            price {real_t} NOT NULL,
            total {real_t} NOT NULL,
            commission {real_t} DEFAULT 0,
            executed_at {ts_required},
            notes TEXT,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
        )
    """)

    op.execute(f"""
        CREATE TABLE IF NOT EXISTS watchlists (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            symbols TEXT NOT NULL,
            created_at {ts_required},
            updated_at {ts_required},
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    op.execute(f"""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id TEXT PRIMARY KEY,
            settings_json TEXT NOT NULL,
            updated_at {ts_required},
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    op.execute(f"""
        CREATE TABLE IF NOT EXISTS quiz_scores (
            id {pk_int},
            user_id TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            category TEXT,
            played_at {ts_required},
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    op.execute(f"""
        CREATE TABLE IF NOT EXISTS signals (
            id {pk_int},
            timestamp {ts_required},
            symbol TEXT NOT NULL,
            price {real_t},
            stop_loss {real_t},
            take_profit {real_t},
            score {real_t},
            strength {real_t},
            regime TEXT,
            sentiment TEXT,
            onchain TEXT,
            entry_ok {bool_zero},
            summary TEXT,
            reason TEXT,
            status TEXT DEFAULT 'open',
            outcome_price {real_t},
            outcome_date {ts_optional},
            outcome_pct {real_t},
            created_at {ts_default_now}
        )
    """)

    op.execute(f"""
        CREATE TABLE IF NOT EXISTS scan_results (
            id {pk_int},
            scan_id TEXT NOT NULL,
            scan_timestamp {ts_required},
            symbol TEXT NOT NULL,
            price {real_t},
            stop_loss {real_t},
            take_profit {real_t},
            score {real_t},
            strength {real_t},
            regime TEXT,
            sentiment TEXT,
            entry_ok {bool_zero},
            summary TEXT,
            source_file TEXT,
            created_at {ts_default_now}
        )
    """)

    op.execute(f"""
        CREATE TABLE IF NOT EXISTS buy_signals (
            id {pk_int},
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            entry_price {real_t} NOT NULL,
            stop_loss {real_t},
            take_profit {real_t},
            risk_reward {real_t},
            score {real_t},
            strength {real_t},
            regime TEXT,
            sentiment {real_t},
            position_size {real_t},
            kelly_fraction {real_t},
            reason TEXT,
            scan_source TEXT,
            status TEXT DEFAULT 'active',
            exit_price {real_t},
            exit_date {ts_optional},
            pnl_pct {real_t},
            pnl_dollar {real_t},
            alpaca_order_id TEXT,
            created_at {ts_default_now},
            UNIQUE(date, symbol)
        )
    """)

    op.execute(f"""
        CREATE TABLE IF NOT EXISTS alpaca_orders (
            id {pk_int},
            order_id TEXT UNIQUE NOT NULL,
            buy_signal_id INTEGER,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            qty {real_t} NOT NULL,
            order_type TEXT DEFAULT 'limit',
            limit_price {real_t},
            stop_price {real_t},
            time_in_force TEXT DEFAULT 'day',
            status TEXT DEFAULT 'new',
            filled_price {real_t},
            filled_qty {real_t},
            filled_at {ts_optional},
            submitted_at {ts_required},
            raw_response TEXT,
            created_at {ts_default_now},
            FOREIGN KEY (buy_signal_id) REFERENCES buy_signals(id)
        )
    """)

    # Indexes (dialect-agnostic)
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
