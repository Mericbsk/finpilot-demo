"""Enrich the symbols table with market-cap data and build named symbol lists.

Two-layer approach
------------------
Layer A — Preset 1500
    Extract all unique tickers from data/stock_presets.json (every preset,
    every category).  Store as  list_name="preset_1500"  in symbol_lists.

Layer B — Small-cap universe ($50M – $300M)
    Scan tradable symbols NOT already in preset_1500 (up to --scan-limit).
    For each symbol fetch market_cap via yfinance fast_info.
    Keep only symbols with market_cap in [50M, 300M].
    Store as  list_name="iwm_300m".

Combined universe
    Union of preset_1500 ∪ iwm_300m, cross-referenced with symbols.tradable=1.
    Store as  list_name="combined_2026".

market_cap column
    Updated in the symbols table for every symbol processed in Layer A + B.

Usage
-----
    python scripts/enrich_market_caps.py               # full run
    python scripts/enrich_market_caps.py --layer a     # preset only
    python scripts/enrich_market_caps.py --layer b     # small-cap scan only
    python scripts/enrich_market_caps.py --layer b --scan-limit 5000   # cap scan size
    python scripts/enrich_market_caps.py --stats       # show DB stats
    python scripts/enrich_market_caps.py --dry-run     # no writes
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core.config import DB_PATH  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("enrich_market_caps")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PRESETS_PATH = REPO_ROOT / "data" / "stock_presets.json"
SMALLCAP_MIN = 50_000_000  # $50M
SMALLCAP_MAX = 300_000_000  # $300M
BATCH_SIZE = 100
MAX_WORKERS = 20
DEFAULT_SCAN_LIMIT = 4000  # max symbols to scan for Layer B (randomised)


# ---------------------------------------------------------------------------
# Layer A — extract all preset symbols
# ---------------------------------------------------------------------------


def extract_preset_symbols(presets_path: Path = PRESETS_PATH) -> list[str]:
    """Return deduplicated list of all tickers across every preset."""
    if not presets_path.exists():
        logger.warning("Presets file not found: %s", presets_path)
        return []

    data = json.loads(presets_path.read_text(encoding="utf-8"))
    seen: set[str] = set()
    result: list[str] = []
    for preset in data.values():
        for sym in preset.get("symbols", []):
            sym = sym.strip().upper()
            if sym and sym not in seen:
                seen.add(sym)
                result.append(sym)

    logger.info("Layer A: %d unique symbols from %d presets", len(result), len(data))
    return result


# ---------------------------------------------------------------------------
# Layer B — small-cap DB scan
# ---------------------------------------------------------------------------


def get_scan_candidates(
    db_path: str | Path,
    exclude_list: str = "preset_1500",
    limit: int = DEFAULT_SCAN_LIMIT,
) -> list[str]:
    """Return tradable symbols NOT in the named list, up to *limit*.

    Symbols are shuffled randomly so each run samples broadly across the DB.
    Already-enriched symbols (market_cap IS NOT NULL) are prioritised last
    so we don't re-fetch what we already know.
    """
    import random

    with sqlite3.connect(str(db_path)) as conn:
        # Check whether exclude_list exists
        already_listed: set[str] = set()
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='symbol_lists'"
        ).fetchone()
        if exists:
            rows = conn.execute(
                "SELECT ticker FROM symbol_lists WHERE list_name=?", (exclude_list,)
            ).fetchall()
            already_listed = {r[0] for r in rows}

        # Tradable symbols, NOT in the exclusion list
        all_tradable = conn.execute("SELECT ticker FROM symbols WHERE tradable=1").fetchall()

    candidates = [r[0] for r in all_tradable if r[0] not in already_listed]
    random.shuffle(candidates)
    candidates = candidates[:limit]
    logger.info(
        "Layer B: %d scan candidates (excl. %s, limit=%d)",
        len(candidates),
        exclude_list,
        limit,
    )
    return candidates


# ---------------------------------------------------------------------------
# Market cap fetch
# ---------------------------------------------------------------------------


def _fetch_market_cap(symbol: str) -> tuple[str, int | None]:
    """Fetch market cap for a single symbol via yfinance fast_info."""
    try:
        import yfinance as yf

        fi = yf.Ticker(symbol).fast_info
        cap = getattr(fi, "market_cap", None)
        if cap and cap > 0:
            return symbol, int(cap)
    except Exception as exc:
        logger.debug("market_cap fetch error %s: %s", symbol, exc)
    return symbol, None


def fetch_market_caps(
    symbols: list[str],
    workers: int = MAX_WORKERS,
    batch_size: int = BATCH_SIZE,
    rate_limit_pause: float = 0.5,
) -> dict[str, int | None]:
    """Parallel market-cap fetch for a list of symbols.

    Returns {ticker: market_cap_int_or_None}.
    Processes in batches to avoid overwhelming yfinance rate limits.
    """
    result: dict[str, int | None] = {}
    total = len(symbols)
    done = 0

    for batch_start in range(0, total, batch_size):
        batch = symbols[batch_start : batch_start + batch_size]
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_fetch_market_cap, s): s for s in batch}
            for future in as_completed(futures):
                sym, cap = future.result()
                result[sym] = cap
                done += 1

        pct = done / total * 100
        logger.info(
            "  market_cap fetch: %d / %d (%.0f%%) — batch %d–%d",
            done,
            total,
            pct,
            batch_start + 1,
            min(batch_start + batch_size, total),
        )
        if batch_start + batch_size < total:
            time.sleep(rate_limit_pause)

    return result


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Create symbol_lists table and ensure market_cap column exists."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS symbol_lists (
            list_name TEXT NOT NULL,
            ticker    TEXT NOT NULL,
            PRIMARY KEY (list_name, ticker)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol_lists_name ON symbol_lists(list_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol_lists_ticker ON symbol_lists(ticker)")
    # Add market_cap / float_shares columns if missing (idempotent)
    existing = {row[1] for row in conn.execute("PRAGMA table_info(symbols)")}
    if "market_cap" not in existing:
        conn.execute("ALTER TABLE symbols ADD COLUMN market_cap INTEGER DEFAULT NULL")
        logger.info("Migration: added market_cap column")
    if "float_shares" not in existing:
        conn.execute("ALTER TABLE symbols ADD COLUMN float_shares INTEGER DEFAULT NULL")
        logger.info("Migration: added float_shares column")


def update_market_caps(
    caps: dict[str, int | None],
    db_path: str | Path,
    dry_run: bool = False,
) -> int:
    """Write market_cap values into symbols table. Returns update count."""
    updates = [(cap, sym) for sym, cap in caps.items() if cap is not None]
    if dry_run:
        logger.info("Dry run: would update %d market_cap rows", len(updates))
        return len(updates)

    with sqlite3.connect(str(db_path)) as conn:
        conn.executemany("UPDATE symbols SET market_cap = ? WHERE ticker = ?", updates)
    logger.info("Updated market_cap for %d symbols", len(updates))
    return len(updates)


def upsert_list(
    list_name: str,
    tickers: list[str],
    db_path: str | Path,
    dry_run: bool = False,
) -> int:
    """Replace all rows for list_name in symbol_lists. Returns count."""
    if dry_run:
        logger.info("Dry run: would upsert %d rows for list '%s'", len(tickers), list_name)
        return len(tickers)

    with sqlite3.connect(str(db_path)) as conn:
        _ensure_schema(conn)
        conn.execute("DELETE FROM symbol_lists WHERE list_name = ?", (list_name,))
        conn.executemany(
            "INSERT OR IGNORE INTO symbol_lists (list_name, ticker) VALUES (?, ?)",
            [(list_name, t) for t in tickers],
        )
        count = conn.execute(
            "SELECT COUNT(*) FROM symbol_lists WHERE list_name = ?", (list_name,)
        ).fetchone()[0]

    logger.info("symbol_lists['%s']: %d tickers", list_name, count)
    return count


def get_tradable_set(db_path: str | Path) -> set[str]:
    """Return set of tradable=1 tickers from symbols table."""
    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute("SELECT ticker FROM symbols WHERE tradable = 1").fetchall()
    return {r[0] for r in rows}


def print_stats(db_path: str | Path) -> None:
    with sqlite3.connect(str(db_path)) as conn:
        total = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
        tradable = conn.execute("SELECT COUNT(*) FROM symbols WHERE tradable=1").fetchone()[0]
        with_cap = conn.execute(
            "SELECT COUNT(*) FROM symbols WHERE market_cap IS NOT NULL"
        ).fetchone()[0]
        lists_exist = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='symbol_lists'"
        ).fetchone()
        list_rows: list[tuple] = []
        if lists_exist:
            list_rows = conn.execute(
                "SELECT list_name, COUNT(*) AS n "
                "FROM symbol_lists GROUP BY list_name ORDER BY n DESC"
            ).fetchall()

    print(f"\n{'─' * 55}")
    print(f"  symbols total   : {total:>6}")
    print(f"  tradable        : {tradable:>6}")
    print(f"  with market_cap : {with_cap:>6}")
    if list_rows:
        print("\n  symbol_lists:")
        for list_name, count in list_rows:
            print(f"    {list_name:<28} {count:>5}")
    print(f"{'─' * 55}\n")


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------


def run_layer_a(db_path: Path, dry_run: bool) -> list[str]:
    """Extract preset symbols → upsert to symbol_lists['preset_1500']."""
    logger.info("=== Layer A: preset symbols ===")
    symbols = extract_preset_symbols()
    if not symbols:
        return []

    # Validate against tradable symbols in DB
    tradable = get_tradable_set(db_path)
    valid = [s for s in symbols if s in tradable]
    removed = len(symbols) - len(valid)
    if removed:
        logger.info("Layer A: removed %d delisted/untradable symbols", removed)

    upsert_list("preset_1500", valid, db_path, dry_run=dry_run)
    return valid


def run_layer_b(
    db_path: Path,
    dry_run: bool,
    workers: int,
    cap_min: int = SMALLCAP_MIN,
    cap_max: int = SMALLCAP_MAX,
    scan_limit: int = DEFAULT_SCAN_LIMIT,
) -> list[str]:
    """Scan DB for small-cap candidates → fetch market caps → filter to [cap_min, cap_max].

    Instead of downloading IWM holdings (which requires bot-accessible URLs),
    this function scans tradable symbols from our own DB that are NOT already
    in preset_1500 and fetches their market caps via yfinance.
    """
    logger.info(
        "=== Layer B: small-cap DB scan ($%dM–$%dM) ===", cap_min // 1_000_000, cap_max // 1_000_000
    )
    candidates = get_scan_candidates(db_path, exclude_list="preset_1500", limit=scan_limit)
    if not candidates:
        logger.warning("Layer B: no scan candidates — skipping")
        return []

    # Fetch market caps
    logger.info(
        "Layer B: fetching market caps for %d symbols (workers=%d)…", len(candidates), workers
    )
    caps = fetch_market_caps(candidates, workers=workers)

    # Update symbols table
    update_market_caps(caps, db_path, dry_run=dry_run)

    # Filter by cap range
    in_range = [sym for sym, cap in caps.items() if cap is not None and cap_min <= cap <= cap_max]
    logger.info(
        "Layer B: %d symbols in $%dM–$%dM range (out of %d with valid caps)",
        len(in_range),
        cap_min // 1_000_000,
        cap_max // 1_000_000,
        sum(1 for cap in caps.values() if cap is not None),
    )

    upsert_list("iwm_300m", in_range, db_path, dry_run=dry_run)
    return in_range


def build_combined(db_path: Path, dry_run: bool) -> list[str]:
    """Merge preset_1500 ∪ iwm_300m → combined_2026."""
    logger.info("=== Combined universe ===")
    with sqlite3.connect(str(db_path)) as conn:
        rows_a = conn.execute(
            "SELECT ticker FROM symbol_lists WHERE list_name='preset_1500'"
        ).fetchall()
        rows_b = conn.execute(
            "SELECT ticker FROM symbol_lists WHERE list_name='iwm_300m'"
        ).fetchall()

    set_a = {r[0] for r in rows_a}
    set_b = {r[0] for r in rows_b}
    combined = sorted(set_a | set_b)

    logger.info(
        "Combined: preset_1500=%d  iwm_300m=%d  union=%d  overlap=%d",
        len(set_a),
        len(set_b),
        len(combined),
        len(set_a & set_b),
    )
    upsert_list("combined_2026", combined, db_path, dry_run=dry_run)
    return combined


def run_layer_a_cap_fetch(
    db_path: Path,
    layer_a_symbols: list[str],
    iwm_fetched: set[str],
    dry_run: bool,
    workers: int,
) -> None:
    """Fetch market caps for preset symbols not already covered by IWM fetch."""
    remaining = [s for s in layer_a_symbols if s not in iwm_fetched]
    if not remaining:
        logger.info("Layer A cap fetch: all preset symbols already covered by IWM")
        return
    logger.info(
        "Layer A cap fetch: fetching market caps for %d additional symbols…", len(remaining)
    )
    caps = fetch_market_caps(remaining, workers=workers)
    update_market_caps(caps, db_path, dry_run=dry_run)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Enrich market caps and build named symbol universes"
    )
    parser.add_argument(
        "--layer",
        choices=["a", "b", "both"],
        default="both",
        help="Which layer to run (default: both)",
    )
    parser.add_argument(
        "--cap-min", type=int, default=SMALLCAP_MIN, help="Min market cap (default 50M)"
    )
    parser.add_argument(
        "--cap-max", type=int, default=SMALLCAP_MAX, help="Max market cap (default 300M)"
    )
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help="Thread pool size")
    parser.add_argument(
        "--scan-limit",
        type=int,
        default=DEFAULT_SCAN_LIMIT,
        help="Max DB symbols to scan in Layer B",
    )
    parser.add_argument("--stats", action="store_true", help="Print DB stats after run")
    parser.add_argument("--dry-run", action="store_true", help="Fetch but don't write")
    parser.add_argument("--db", default=str(DB_PATH), help="SQLite DB path")
    args = parser.parse_args()

    db_path = Path(args.db)

    # Load .env
    try:
        from dotenv import load_dotenv

        load_dotenv(REPO_ROOT / ".env")
    except ImportError:
        pass

    # Ensure schema exists
    if not args.dry_run:
        with sqlite3.connect(str(db_path)) as conn:
            _ensure_schema(conn)

    layer_a_symbols: list[str] = []
    iwm_fetched: set[str] = set()

    if args.layer in ("a", "both"):
        layer_a_symbols = run_layer_a(db_path, dry_run=args.dry_run)

    if args.layer in ("b", "both"):
        iwm_in_range = run_layer_b(
            db_path,
            dry_run=args.dry_run,
            workers=args.workers,
            cap_min=args.cap_min,
            cap_max=args.cap_max,
            scan_limit=args.scan_limit,
        )
        # Track which symbols had cap fetched in layer B (to avoid refetching)
        iwm_fetched = set(iwm_in_range)

    if args.layer == "both":
        # Fetch caps for preset symbols not covered by IWM
        run_layer_a_cap_fetch(db_path, layer_a_symbols, iwm_fetched, args.dry_run, args.workers)
        build_combined(db_path, dry_run=args.dry_run)

    if args.stats:
        print_stats(db_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
