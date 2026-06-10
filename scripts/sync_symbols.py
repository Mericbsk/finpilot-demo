"""Sync tradable US equity symbols from Alpaca into the local SQLite database.

Creates (or updates) a `symbols` table with every active US stock / ETF that
Alpaca supports, enriched with name, exchange, and asset-class metadata.

Usage
-----
    python scripts/sync_symbols.py              # full sync
    python scripts/sync_symbols.py --dry-run    # count only, no writes
    python scripts/sync_symbols.py --stats      # show table stats after sync

Schedule this daily (e.g. 02:00 UTC) so new IPOs and delistings are reflected
automatically.
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap — allow running directly without installing the package
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core.config import DB_PATH  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sync_symbols")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TABLE_DDL = """
CREATE TABLE IF NOT EXISTS symbols (
    ticker       TEXT PRIMARY KEY,
    name         TEXT,
    exchange     TEXT,
    asset_class  TEXT,
    status       TEXT,
    tradable     INTEGER DEFAULT 1,
    shortable    INTEGER DEFAULT 0,
    marginable   INTEGER DEFAULT 0,
    market_cap   INTEGER DEFAULT NULL,
    float_shares INTEGER DEFAULT NULL,
    updated_at   TEXT
);
CREATE INDEX IF NOT EXISTS idx_symbols_exchange   ON symbols(exchange);
CREATE INDEX IF NOT EXISTS idx_symbols_tradable   ON symbols(tradable);
CREATE INDEX IF NOT EXISTS idx_symbols_market_cap ON symbols(market_cap);
"""

SYMBOL_LISTS_DDL = """
CREATE TABLE IF NOT EXISTS symbol_lists (
    list_name TEXT NOT NULL,
    ticker    TEXT NOT NULL,
    PRIMARY KEY (list_name, ticker)
);
CREATE INDEX IF NOT EXISTS idx_symbol_lists_name   ON symbol_lists(list_name);
CREATE INDEX IF NOT EXISTS idx_symbol_lists_ticker ON symbol_lists(ticker);
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _migrate_columns(conn: sqlite3.Connection) -> None:
    """Idempotent ALTER TABLE — adds new columns to existing symbols table."""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(symbols)")}
    migrations = [
        ("market_cap", "ALTER TABLE symbols ADD COLUMN market_cap   INTEGER DEFAULT NULL"),
        ("float_shares", "ALTER TABLE symbols ADD COLUMN float_shares INTEGER DEFAULT NULL"),
    ]
    for col, sql in migrations:
        if col not in existing:
            conn.execute(sql)
            logger.info("Migration: added column '%s' to symbols", col)


def _get_alpaca_client():
    """Return an authenticated Alpaca TradingClient (paper or live)."""
    import os

    from alpaca.trading.client import TradingClient

    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    paper = os.getenv("ALPACA_PAPER", "true").lower() != "false"

    if not api_key or not secret_key:
        raise OSError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in .env")

    return TradingClient(api_key, secret_key, paper=paper)


def fetch_all_assets(client) -> list[dict]:
    """Fetch all active US equity + ETF assets from Alpaca."""
    from alpaca.trading.enums import AssetClass, AssetStatus
    from alpaca.trading.requests import GetAssetsRequest

    logger.info("Fetching asset list from Alpaca…")

    rows: list[dict] = []
    for asset_class in (AssetClass.US_EQUITY,):
        req = GetAssetsRequest(
            asset_class=asset_class,
            status=AssetStatus.ACTIVE,
        )
        assets = client.get_all_assets(req)
        logger.info("  %s: %d assets", asset_class.value, len(assets))
        for a in assets:
            rows.append(
                {
                    "ticker": a.symbol,
                    "name": a.name or "",
                    "exchange": str(a.exchange) if a.exchange else "",
                    "asset_class": str(a.asset_class) if a.asset_class else "",
                    "status": str(a.status) if a.status else "",
                    "tradable": int(bool(a.tradable)),
                    "shortable": int(bool(a.shortable)),
                    "marginable": int(bool(a.marginable)),
                    "updated_at": datetime.now(UTC).isoformat(),
                }
            )

    return rows


def upsert_symbols(rows: list[dict], db_path: str | Path) -> tuple[int, int]:
    """Insert or replace rows into the symbols table. Returns (inserted, total)."""
    db_path = str(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(TABLE_DDL)
        conn.executescript(SYMBOL_LISTS_DDL)
        _migrate_columns(conn)
        conn.executemany(
            """
            INSERT INTO symbols
                (ticker, name, exchange, asset_class, status,
                 tradable, shortable, marginable, updated_at)
            VALUES
                (:ticker, :name, :exchange, :asset_class, :status,
                 :tradable, :shortable, :marginable, :updated_at)
            ON CONFLICT(ticker) DO UPDATE SET
                name        = excluded.name,
                exchange    = excluded.exchange,
                asset_class = excluded.asset_class,
                status      = excluded.status,
                tradable    = excluded.tradable,
                shortable   = excluded.shortable,
                marginable  = excluded.marginable,
                updated_at  = excluded.updated_at
            """,
            rows,
        )
        total = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
    return len(rows), total


def print_stats(db_path: str | Path) -> None:
    """Print summary statistics from the symbols + symbol_lists tables."""
    with sqlite3.connect(str(db_path)) as conn:
        total = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
        tradable = conn.execute("SELECT COUNT(*) FROM symbols WHERE tradable=1").fetchone()[0]
        with_cap = conn.execute(
            "SELECT COUNT(*) FROM symbols WHERE market_cap IS NOT NULL"
        ).fetchone()[0]
        by_exchange = conn.execute(
            "SELECT exchange, COUNT(*) AS n FROM symbols GROUP BY exchange ORDER BY n DESC LIMIT 10"
        ).fetchall()
        updated = conn.execute("SELECT MAX(updated_at) FROM symbols").fetchone()[0]

        # symbol_lists summary
        lists_exist = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='symbol_lists'"
        ).fetchone()
        list_rows = []
        if lists_exist:
            list_rows = conn.execute(
                "SELECT list_name, COUNT(*) AS n FROM symbol_lists GROUP BY list_name ORDER BY n DESC"
            ).fetchall()

    print(f"\n{'─' * 50}")
    print(f"  Total symbols   : {total:>6}")
    print(f"  Tradable        : {tradable:>6}")
    print(f"  With market_cap : {with_cap:>6}")
    print(f"  Last updated    : {updated}")
    print("\n  By exchange (top 10):")
    for exchange, count in by_exchange:
        print(f"    {exchange:<20} {count:>5}")
    if list_rows:
        print("\n  symbol_lists:")
        for list_name, count in list_rows:
            print(f"    {list_name:<25} {count:>5}")
    print(f"{'─' * 50}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Alpaca symbols to local DB")
    parser.add_argument("--dry-run", action="store_true", help="Fetch but don't write")
    parser.add_argument("--stats", action="store_true", help="Show table stats after sync")
    parser.add_argument("--db", default=str(DB_PATH), help="SQLite DB path")
    args = parser.parse_args()

    # Load .env
    try:
        from dotenv import load_dotenv

        load_dotenv(REPO_ROOT / ".env")
    except ImportError:
        pass

    try:
        client = _get_alpaca_client()
        rows = fetch_all_assets(client)
    except Exception as exc:
        logger.error("Failed to fetch assets: %s", exc)
        return 1

    if not rows:
        logger.warning("No assets returned — aborting write")
        return 1

    if args.dry_run:
        logger.info("Dry run: would upsert %d symbols (no write)", len(rows))
        return 0

    inserted, total = upsert_symbols(rows, args.db)
    logger.info("Upserted %d rows → %d total in symbols table", inserted, total)

    if args.stats:
        print_stats(args.db)

    return 0


if __name__ == "__main__":
    sys.exit(main())
