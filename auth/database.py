"""
Database Layer for FinPilot Authentication.

Provides SQLite-based persistence for users, sessions, portfolios, and settings.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Type, TypeVar

from .core import Session, User, UserRole

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ============================================================================
# DATABASE CONNECTION
# ============================================================================


class Database:
    """
    SQLite database manager with connection pooling.

    Example:
        >>> db = Database("finpilot.db")
        >>> db.initialize()
        >>>
        >>> with db.connection() as conn:
        ...     cursor = conn.execute("SELECT * FROM users")
        ...     users = cursor.fetchall()
    """

    def __init__(self, db_path: str = "data/finpilot.db"):
        self.db_path = db_path
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Ensure database directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection context manager."""
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
        """Initialize database schema."""
        with self.connection() as conn:
            # Users table
            conn.execute(
                """
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
            """
            )

            # Sessions table
            conn.execute(
                """
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
            """
            )

            # Portfolios table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS portfolios (
                    id TEXT PRIMARY KEY,
                    user_id TEXT UNIQUE NOT NULL,
                    cash REAL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """
            )

            # Positions table
            conn.execute(
                """
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
            """
            )

            # Trades table
            conn.execute(
                """
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
            """
            )

            # Watchlists table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS watchlists (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    symbols TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """
            )

            # Settings table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id TEXT PRIMARY KEY,
                    settings_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """
            )

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_positions_portfolio ON positions(portfolio_id)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_portfolio ON trades(portfolio_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")

            logger.info(f"Database initialized: {self.db_path}")

    def drop_all(self) -> None:
        """Drop all tables (for testing)."""
        with self.connection() as conn:
            conn.execute("DROP TABLE IF EXISTS trades")
            conn.execute("DROP TABLE IF EXISTS positions")
            conn.execute("DROP TABLE IF EXISTS portfolios")
            conn.execute("DROP TABLE IF EXISTS watchlists")
            conn.execute("DROP TABLE IF EXISTS user_settings")
            conn.execute("DROP TABLE IF EXISTS sessions")
            conn.execute("DROP TABLE IF EXISTS users")
        logger.warning("All tables dropped")


# ============================================================================
# REPOSITORIES
# ============================================================================


class BaseRepository(ABC):
    """Base repository class."""

    def __init__(self, db: Database):
        self.db = db

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[Any]:  # noqa: A002
        ...

    @abstractmethod
    def save(self, entity: Any, *args: Any) -> None: ...

    @abstractmethod
    def delete(self, id: str) -> bool:  # noqa: A002
        ...


class UserRepository(BaseRepository):
    """Repository for User entities."""

    def get_by_id(self, id: str) -> Optional[User]:  # noqa: A002
        """Get user by ID."""
        with self.db.connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (id,)).fetchone()

            if row:
                return self._row_to_user(row)
        return None

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        with self.db.connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()

            if row:
                return self._row_to_user(row)
        return None

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        with self.db.connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

            if row:
                return self._row_to_user(row)
        return None

    def save(self, entity: User, *args: Any) -> None:  # type: ignore[override]
        """Save or update user."""
        user = entity
        with self.db.connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO users
                (id, email, username, password_hash, salt, display_name, avatar_url,
                 role, is_active, is_verified, created_at, updated_at, last_login,
                 failed_login_attempts, locked_until)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user.id,
                    user.email.lower(),
                    user.username,
                    user.password_hash,
                    user.salt,
                    user.display_name,
                    user.avatar_url,
                    user.role.value,
                    int(user.is_active),
                    int(user.is_verified),
                    user.created_at.isoformat(),
                    user.updated_at.isoformat(),
                    user.last_login.isoformat() if user.last_login else None,
                    user.failed_login_attempts,
                    user.locked_until.isoformat() if user.locked_until else None,
                ),
            )

    def delete(self, id: str) -> bool:  # noqa: A002
        """Delete user."""
        with self.db.connection() as conn:
            cursor = conn.execute("DELETE FROM users WHERE id = ?", (id,))
            return cursor.rowcount > 0

    def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users."""
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)
            ).fetchall()

            return [self._row_to_user(row) for row in rows]

    def _row_to_user(self, row: sqlite3.Row) -> User:
        """Convert database row to User object."""
        return User(
            id=row["id"],
            email=row["email"],
            username=row["username"],
            password_hash=row["password_hash"],
            salt=row["salt"],
            display_name=row["display_name"],
            avatar_url=row["avatar_url"],
            role=UserRole(row["role"]),
            is_active=bool(row["is_active"]),
            is_verified=bool(row["is_verified"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            last_login=datetime.fromisoformat(row["last_login"]) if row["last_login"] else None,
            failed_login_attempts=row["failed_login_attempts"],
            locked_until=(
                datetime.fromisoformat(row["locked_until"]) if row["locked_until"] else None
            ),
        )


class SessionRepository(BaseRepository):
    """Repository for Session entities."""

    def get_by_id(self, id: str) -> Optional[Session]:  # noqa: A002
        """Get session by ID."""
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ? AND is_active = 1", (id,)
            ).fetchone()

            if row:
                return self._row_to_session(row)
        return None

    def get_by_token(self, access_token: str) -> Optional[Session]:
        """Get session by access token."""
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE access_token = ? AND is_active = 1", (access_token,)
            ).fetchone()

            if row:
                return self._row_to_session(row)
        return None

    def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all active sessions for a user."""
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE user_id = ? AND is_active = 1 ORDER BY last_activity DESC",
                (user_id,),
            ).fetchall()

            return [self._row_to_session(row) for row in rows]

    def save(self, entity: Session, *args: Any) -> None:  # type: ignore[override]
        """Save or update session."""
        session = entity
        with self.db.connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sessions
                (id, user_id, access_token, refresh_token, device_info, ip_address,
                 user_agent, created_at, expires_at, last_activity, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session.id,
                    session.user_id,
                    session.access_token,
                    session.refresh_token,
                    session.device_info,
                    session.ip_address,
                    session.user_agent,
                    session.created_at.isoformat(),
                    session.expires_at.isoformat(),
                    session.last_activity.isoformat(),
                    int(session.is_active),
                ),
            )

    def delete(self, id: str) -> bool:  # noqa: A002
        """Delete (deactivate) session."""
        with self.db.connection() as conn:
            cursor = conn.execute("UPDATE sessions SET is_active = 0 WHERE id = ?", (id,))
            return cursor.rowcount > 0

    def delete_all_for_user(self, user_id: str) -> int:
        """Delete all sessions for a user."""
        with self.db.connection() as conn:
            cursor = conn.execute("UPDATE sessions SET is_active = 0 WHERE user_id = ?", (user_id,))
            return cursor.rowcount

    def cleanup_expired(self) -> int:
        """Remove expired sessions."""
        now = datetime.utcnow().isoformat()
        with self.db.connection() as conn:
            cursor = conn.execute("UPDATE sessions SET is_active = 0 WHERE expires_at < ?", (now,))
            return cursor.rowcount

    def _row_to_session(self, row: sqlite3.Row) -> Session:
        """Convert database row to Session object."""
        return Session(
            id=row["id"],
            user_id=row["user_id"],
            access_token=row["access_token"],
            refresh_token=row["refresh_token"],
            device_info=row["device_info"],
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
            last_activity=datetime.fromisoformat(row["last_activity"]),
            is_active=bool(row["is_active"]),
        )


class PortfolioRepository(BaseRepository):
    """Repository for Portfolio data."""

    def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:  # noqa: A002
        """Get portfolio by ID."""
        with self.db.connection() as conn:
            row = conn.execute("SELECT * FROM portfolios WHERE id = ?", (id,)).fetchone()

            if row:
                return self._row_to_dict(row)
        return None

    def get_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get portfolio for a user."""
        with self.db.connection() as conn:
            row = conn.execute("SELECT * FROM portfolios WHERE user_id = ?", (user_id,)).fetchone()

            if row:
                portfolio = self._row_to_dict(row)
                portfolio["positions"] = self._get_positions(conn, row["id"])
                return portfolio
        return None

    def _get_positions(self, conn: sqlite3.Connection, portfolio_id: str) -> List[Dict]:
        """Get positions for a portfolio."""
        rows = conn.execute(
            "SELECT * FROM positions WHERE portfolio_id = ?", (portfolio_id,)
        ).fetchall()

        return [dict(row) for row in rows]

    def save(self, entity: Dict[str, Any], *args: Any) -> None:  # type: ignore[override]
        """Save portfolio."""
        portfolio = entity
        with self.db.connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO portfolios
                (id, user_id, cash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    portfolio["id"],
                    portfolio["user_id"],
                    portfolio.get("cash", 0),
                    portfolio.get("created_at", datetime.utcnow().isoformat()),
                    datetime.utcnow().isoformat(),
                ),
            )

            # Save positions
            if "positions" in portfolio:
                for pos in portfolio["positions"]:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO positions
                        (id, portfolio_id, symbol, shares, avg_price, opened_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            pos["id"],
                            portfolio["id"],
                            pos["symbol"],
                            pos["shares"],
                            pos["avg_price"],
                            pos.get("opened_at", datetime.utcnow().isoformat()),
                            datetime.utcnow().isoformat(),
                        ),
                    )

    def delete(self, id: str) -> bool:  # noqa: A002
        """Delete portfolio and all positions."""
        portfolio_id = id
        with self.db.connection() as conn:
            conn.execute("DELETE FROM positions WHERE portfolio_id = ?", (portfolio_id,))
            cursor = conn.execute("DELETE FROM portfolios WHERE id = ?", (portfolio_id,))
            return cursor.rowcount > 0

    def add_trade(self, trade: Dict[str, Any]) -> None:
        """Record a trade."""
        with self.db.connection() as conn:
            conn.execute(
                """
                INSERT INTO trades
                (id, portfolio_id, symbol, side, shares, price, total, commission, executed_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    trade["id"],
                    trade["portfolio_id"],
                    trade["symbol"],
                    trade["side"],
                    trade["shares"],
                    trade["price"],
                    trade["total"],
                    trade.get("commission", 0),
                    trade.get("executed_at", datetime.utcnow().isoformat()),
                    trade.get("notes"),
                ),
            )

    def get_trades(
        self, portfolio_id: str, symbol: Optional[str] = None, limit: int = 100
    ) -> List[Dict]:
        """Get trades for a portfolio."""
        with self.db.connection() as conn:
            if symbol:
                rows = conn.execute(
                    "SELECT * FROM trades WHERE portfolio_id = ? AND symbol = ? ORDER BY executed_at DESC LIMIT ?",
                    (portfolio_id, symbol, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM trades WHERE portfolio_id = ? ORDER BY executed_at DESC LIMIT ?",
                    (portfolio_id, limit),
                ).fetchall()

            return [dict(row) for row in rows]

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        return dict(row)


class SettingsRepository(BaseRepository):
    """Repository for user settings."""

    def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:  # noqa: A002
        """Get settings for a user."""
        user_id = id
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM user_settings WHERE user_id = ?", (user_id,)
            ).fetchone()

            if row:
                return json.loads(row["settings_json"])
        return None

    def save(self, entity: Dict[str, Any], *args: Any) -> None:  # type: ignore[override]
        """Save user settings."""
        # entity is the settings dict, args[0] is user_id if provided
        if args:
            user_id = str(args[0]) if args[0] else ""
            settings = entity
        else:
            user_id = entity.get("user_id", "")
            settings = entity
        with self.db.connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO user_settings
                (user_id, settings_json, updated_at)
                VALUES (?, ?, ?)
            """,
                (user_id, json.dumps(settings, ensure_ascii=False), datetime.utcnow().isoformat()),
            )

    def delete(self, id: str) -> bool:  # noqa: A002
        """Delete user settings."""
        user_id = id
        with self.db.connection() as conn:
            cursor = conn.execute("DELETE FROM user_settings WHERE user_id = ?", (user_id,))
            return cursor.rowcount > 0

    def update(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update specific settings (merge with existing)."""
        current = self.get_by_id(user_id) or {}
        current.update(updates)
        self.save(current, user_id)  # entity first, then user_id
        return current


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

_default_db: Optional[Database] = None


def get_database(db_path: str = "data/finpilot.db") -> Database:
    """Get or create default database."""
    global _default_db
    if _default_db is None:
        _default_db = Database(db_path)
        _default_db.initialize()
    return _default_db


__all__ = [
    "Database",
    "UserRepository",
    "SessionRepository",
    "PortfolioRepository",
    "SettingsRepository",
    "get_database",
]
