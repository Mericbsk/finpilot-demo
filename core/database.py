"""SQLAlchemy sync + async engines and session factories (S2-2).

DATABASE_URL env var controls the backend:
  sqlite:///data/finpilot.db   (default, dev)
  postgresql://...             (prod)
  postgresql+asyncpg://...     (prod, async URL)

Provides:
  sync_engine          — synchronous engine (used by services + watchlist router)
  get_sync_session()   — context-manager yielding a sync Session
  async_engine         — async engine (for future async routes)
  get_db()             — FastAPI async dependency yielding AsyncSession
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

_RAW_URL = os.getenv("DATABASE_URL", "sqlite:///data/finpilot.db")

# ─── Derive sync / async URL variants ─────────────────────────────────────────
_IS_SQLITE = _RAW_URL.startswith("sqlite")

if _IS_SQLITE:
    _SYNC_URL = _RAW_URL
    _ASYNC_URL = _RAW_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)
elif "postgresql+asyncpg" in _RAW_URL:
    _ASYNC_URL = _RAW_URL
    _SYNC_URL = _RAW_URL.replace("postgresql+asyncpg://", "postgresql://", 1)
else:
    _SYNC_URL = _RAW_URL
    _ASYNC_URL = _RAW_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# ─── Sync engine ──────────────────────────────────────────────────────────────
if _IS_SQLITE:
    sync_engine = create_engine(
        _SYNC_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    sync_engine = create_engine(
        _SYNC_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )

_SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)


@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """Yield a sync SQLAlchemy session; auto-commit on success, rollback on error."""
    session: Session = _SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ─── Async engine ─────────────────────────────────────────────────────────────
if _IS_SQLITE:
    async_engine = create_async_engine(
        _ASYNC_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    async_engine = create_async_engine(
        _ASYNC_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )

_AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an AsyncSession, auto-commit on success."""
    async with _AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
