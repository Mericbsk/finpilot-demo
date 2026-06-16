"""Resolve open signals in signals_archive with yfinance forward returns.

Produces two label columns per signal (dual-label standard):
    resolved_pct_t5      — fixed T+5 close return  (research comparisons)
    resolved_pct_barrier — first barrier hit: TP / SL / 21-trading-day expiry (product truth)

Updates signals_archive rows where resolved_status IS NULL.

Usage:
    python scripts/resolve_open_signals.py [options]

Options:
    --horizon N     T+N trading-day fixed horizon (default 5)
    --limit N       process at most N symbols (default: all)
    --dry-run       print summary, do not write to DB
    --db PATH       path to finpilot.db (default: data/finpilot.db)
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "data" / "finpilot.db"
BATCH_SIZE = 80  # max symbols per yfinance download call
MAX_BARRIER_DAYS = 30  # calendar days to fetch beyond signal date for barrier search
TRADING_DAY_APPROX = 1.4  # calendar-to-trading-day conversion factor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def _open_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    # Ensure dual-label columns exist (idempotent ALTER TABLE)
    for col, ctype in [
        ("resolved_pct_t5", "REAL"),
        ("resolved_pct_barrier", "REAL"),
        ("resolved_status_barrier", "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE signals_archive ADD COLUMN {col} {ctype}")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists
    return conn


def _load_open_rows(conn: sqlite3.Connection, limit: int | None) -> list[sqlite3.Row]:
    # resolved_status stores 'open' or 'watching' for unresolved rows.
    # 'watching' = watchlist lifecycle active but no TP/SL/expiry yet.
    # 'unresolvable' = previously failed due to parse errors; retry on re-run.
    # Also handle IS NULL for rows added before migration.
    sql = """
        SELECT id, symbol, ts, score, finpilot_score, payload_json
        FROM   signals_archive
        WHERE  resolved_status IS NULL
           OR  resolved_status = 'open'
           OR  resolved_status = 'watching'
           OR  resolved_status = 'unresolvable'
        ORDER  BY ts ASC
    """
    if limit:
        sql += f" LIMIT {limit * 5}"  # over-fetch; we de-dup by symbol later
    cur = conn.execute(sql)
    return cur.fetchall()


def _write_results(
    conn: sqlite3.Connection,
    results: list[dict[str, Any]],
    dry_run: bool,
) -> None:
    if dry_run:
        for r in results:
            logger.info(
                "[DRY-RUN] %s  t5=%s  barrier=%s (%s)",
                r["id"],
                r.get("pct_t5"),
                r.get("pct_barrier"),
                r.get("status_barrier"),
            )
        return
    conn.executemany(
        """
        UPDATE signals_archive
        SET    resolved_pct_t5           = :pct_t5,
               resolved_pct_barrier      = :pct_barrier,
               resolved_status_barrier   = :status_barrier,
               resolved_status           = :status_barrier,
               resolved_pct              = COALESCE(resolved_pct, :pct_barrier)
        WHERE  id = :id
          AND  (resolved_status IS NULL
                OR resolved_status = 'open'
                OR resolved_status = 'watching'
                OR resolved_status = 'unresolvable')
        """,
        results,
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Date / calendar helpers
# ---------------------------------------------------------------------------


def _parse_ts(ts: str | None) -> date | None:
    if not ts:
        return None
    for fmt in (
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
    ):
        try:
            return datetime.strptime(ts[:26], fmt).date()
        except ValueError:
            continue
    return None


def _trading_days_after(closes_index: Any, signal_date: date, n: int) -> date | None:
    """Return the date of the N-th trading day after signal_date in closes_index."""
    future = [d for d in closes_index if d > signal_date]
    if len(future) < n:
        return None
    return future[n - 1]


# ---------------------------------------------------------------------------
# Core resolution logic (per symbol batch)
# ---------------------------------------------------------------------------


def _resolve_symbol(
    symbol: str,
    rows: list[dict],
    horizon_td: int,
    yf_module: Any,
) -> list[dict[str, Any]]:
    """Download history for *symbol* and compute both labels for each row."""
    if not rows:
        return []

    valid_dates = [r["signal_date"] for r in rows if r["signal_date"]]
    if not valid_dates:
        logger.debug("No valid signal_date for %s — skipping", symbol)
        return [
            {"id": r["id"], "pct_t5": None, "pct_barrier": None, "status_barrier": "unresolvable"}
            for r in rows
        ]

    oldest = min(valid_dates)

    start_str = (oldest - timedelta(days=5)).strftime("%Y-%m-%d")
    end_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        hist = yf_module.download(
            symbol,
            start=start_str,
            end=end_str,
            progress=False,
            auto_adjust=True,
        )
    except Exception as exc:
        logger.warning("yfinance download failed for %s: %s", symbol, exc)
        return []

    if hist is None or hist.empty:
        logger.debug("No data for %s", symbol)
        return []

    # Normalise multi-index columns (happens when downloading a single ticker)
    if hasattr(hist.columns, "levels"):
        hist.columns = hist.columns.get_level_values(0)

    closes = hist["Close"].dropna()
    high_s = hist["High"].dropna()
    low_s = hist["Low"].dropna()
    close_dates = [d.date() for d in closes.index]

    results: list[dict[str, Any]] = []

    for row in rows:
        sig_date = row["signal_date"]
        if sig_date is None:
            continue

        entry_price = row.get("entry_price") or 0.0
        take_profit = row.get("take_profit") or 0.0
        stop_loss = row.get("stop_loss") or 0.0

        # --- T+N fixed horizon label ---
        t5_date = _trading_days_after(close_dates, sig_date, horizon_td)
        pct_t5: float | None = None
        if t5_date is not None and entry_price > 0:
            try:
                px = float(closes[closes.index.date == t5_date].iloc[0])  # type: ignore[attr-defined]
                pct_t5 = round((px - entry_price) / entry_price * 100.0, 4)
            except (IndexError, ValueError):
                pass

        # --- Triple-barrier label ---
        pct_barrier: float | None = None
        status_barrier: str | None = None

        if entry_price > 0:
            barrier_dates = [d for d in close_dates if d > sig_date]
            # Max 21 trading days
            barrier_dates = barrier_dates[:21]

            for bd in barrier_dates:
                try:
                    hi = float(high_s[high_s.index.date == bd].iloc[0])  # type: ignore[attr-defined]
                    lo = float(low_s[low_s.index.date == bd].iloc[0])  # type: ignore[attr-defined]
                    float(closes[closes.index.date == bd].iloc[0])  # type: ignore[attr-defined]
                except (IndexError, ValueError):
                    continue

                # TP hit (use intraday high as proxy)
                if take_profit > 0 and hi >= take_profit:
                    pct_barrier = round((take_profit - entry_price) / entry_price * 100.0, 4)
                    status_barrier = "resolved_win"
                    break

                # SL hit (use intraday low as proxy)
                if stop_loss > 0 and lo <= stop_loss:
                    pct_barrier = round((stop_loss - entry_price) / entry_price * 100.0, 4)
                    status_barrier = "resolved_loss"
                    break
            else:
                # 21-day expiry — use final close
                if barrier_dates:
                    last_d = barrier_dates[-1]
                    try:
                        cl_last = float(closes[closes.index.date == last_d].iloc[0])  # type: ignore[attr-defined]
                        pct_barrier = round((cl_last - entry_price) / entry_price * 100.0, 4)
                        status_barrier = "expired_win" if pct_barrier >= 0 else "expired_loss"
                    except (IndexError, ValueError):
                        pass

        if pct_barrier is None and entry_price == 0:
            status_barrier = "unresolvable"

        results.append(
            {
                "id": row["id"],
                "pct_t5": pct_t5,
                "pct_barrier": pct_barrier,
                "status_barrier": status_barrier,
            }
        )

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _parse_payload(payload_json: str | None) -> dict:
    if not payload_json:
        return {}
    import json

    try:
        return json.loads(payload_json)
    except Exception:
        return {}


def run(
    horizon: int = 5,
    limit: int | None = None,
    dry_run: bool = False,
    db_path: Path = DB_PATH,
) -> dict[str, int]:
    try:
        import yfinance as yf
    except ImportError:
        logger.error("yfinance not installed — cannot resolve signals")
        sys.exit(1)

    conn = _open_db(db_path)
    rows_raw = _load_open_rows(conn, limit)
    logger.info("Loaded %d open rows from signals_archive", len(rows_raw))

    # Parse payload, group by symbol
    by_symbol: dict[str, list[dict]] = {}
    seen_symbols: list[str] = []
    for row in rows_raw:
        sym = str(row["symbol"] or "").strip().upper()
        if not sym:
            continue
        payload = _parse_payload(row["payload_json"])
        record = {
            "id": row["id"],
            "signal_date": _parse_ts(row["ts"]) or _parse_ts(payload.get("signal_date")),
            "entry_price": float(payload.get("entry_price") or 0),
            "take_profit": float(payload.get("take_profit") or 0),
            "stop_loss": float(payload.get("stop_loss") or 0),
        }
        if sym not in by_symbol:
            seen_symbols.append(sym)
        by_symbol.setdefault(sym, []).append(record)

    # Apply symbol limit
    if limit:
        seen_symbols = seen_symbols[:limit]
        by_symbol = {s: by_symbol[s] for s in seen_symbols}

    total_symbols = len(seen_symbols)
    logger.info("Resolving %d unique symbols (horizon T+%d)", total_symbols, horizon)

    all_results: list[dict[str, Any]] = []
    unresolvable = 0

    for batch_start in range(0, total_symbols, BATCH_SIZE):
        batch_syms = seen_symbols[batch_start : batch_start + BATCH_SIZE]
        logger.info(
            "Batch %d/%d — symbols %d–%d",
            batch_start // BATCH_SIZE + 1,
            (total_symbols + BATCH_SIZE - 1) // BATCH_SIZE,
            batch_start + 1,
            batch_start + len(batch_syms),
        )
        for sym in batch_syms:
            sym_results = _resolve_symbol(sym, by_symbol[sym], horizon, yf)
            for r in sym_results:
                if r.get("status_barrier") == "unresolvable":
                    unresolvable += 1
            all_results.extend(sym_results)
        # brief pause between batches to be polite to yfinance
        if batch_start + BATCH_SIZE < total_symbols:
            time.sleep(1)

    resolved_t5 = sum(1 for r in all_results if r.get("pct_t5") is not None)
    resolved_barrier = sum(1 for r in all_results if r.get("pct_barrier") is not None)

    logger.info(
        "Resolved: t5=%d  barrier=%d  unresolvable=%d  total_rows=%d",
        resolved_t5,
        resolved_barrier,
        unresolvable,
        len(all_results),
    )

    _write_results(conn, all_results, dry_run)
    conn.close()

    if dry_run:
        logger.info("[DRY-RUN] No DB writes performed.")
    else:
        logger.info("DB updated. Run profitcore_audit.py to recheck edge metrics.")

    return {
        "symbols": total_symbols,
        "rows": len(all_results),
        "t5": resolved_t5,
        "barrier": resolved_barrier,
        "unresolvable": unresolvable,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resolve open signals with yfinance")
    parser.add_argument(
        "--horizon", type=int, default=5, help="T+N trading-day fixed horizon (default 5)"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Process at most N symbols (default: all)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print results without writing to DB"
    )
    parser.add_argument("--db", type=str, default=str(DB_PATH), help="Path to finpilot.db")
    args = parser.parse_args()

    stats = run(
        horizon=args.horizon,
        limit=args.limit,
        dry_run=args.dry_run,
        db_path=Path(args.db),
    )
    print(
        f"\nDone — symbols={stats['symbols']}  rows={stats['rows']}  "
        f"t5={stats['t5']}  barrier={stats['barrier']}  "
        f"unresolvable={stats['unresolvable']}"
    )
