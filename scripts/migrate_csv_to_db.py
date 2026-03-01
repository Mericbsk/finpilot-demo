"""
CSV → SQLite Migration Utility — Sprint 20.

Imports existing signal_log.csv and shortlist CSVs into the SQLite database.
Idempotent: can be safely re-run (checks for existing data).

Usage:
    python scripts/migrate_csv_to_db.py [--force]
"""

from __future__ import annotations

import csv
import glob
import logging
import os
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def migrate_signal_log(force: bool = False) -> int:
    """Import signal_log.csv into the signals table."""
    from auth.database import SignalRepository, get_database

    db = get_database()
    repo = SignalRepository(db)

    if not force and repo.count() > 0:
        logger.info(f"Signals table already has {repo.count()} rows — skipping (use --force to override)")
        return 0

    signal_log_path = os.path.join(os.getcwd(), "data", "logs", "signal_log.csv")
    if not os.path.exists(signal_log_path):
        logger.warning(f"Signal log not found: {signal_log_path}")
        return 0

    COLUMNS = [
        "timestamp", "symbol", "price", "stop_loss", "take_profit",
        "score", "strength", "regime", "sentiment", "onchain",
        "entry_ok", "summary", "reason",
    ]

    signals = []
    with open(signal_log_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < 3:
                continue
            rec = dict(zip(COLUMNS, row))
            # Convert types
            for num_field in ("price", "stop_loss", "take_profit", "score", "strength"):
                try:
                    rec[num_field] = float(rec.get(num_field, 0) or 0)
                except (ValueError, TypeError):
                    rec[num_field] = None
            rec["entry_ok"] = str(rec.get("entry_ok", "")).lower() in {
                "1", "true", "evet", "al", "yes",
            }
            signals.append(rec)

    if not signals:
        logger.info("No signals found in CSV")
        return 0

    count = repo.save_batch(signals)
    logger.info(f"Imported {count} signals from CSV → DB")
    return count


def migrate_shortlists(force: bool = False) -> int:
    """Import all shortlist CSVs into the scan_results table."""
    from auth.database import ScanResultRepository, get_database

    import pandas as pd

    db = get_database()
    repo = ScanResultRepository(db)

    if not force and repo.count() > 0:
        logger.info(
            f"Scan results table already has {repo.count()} rows — skipping (use --force)"
        )
        return 0

    shortlist_dir = os.path.join(os.getcwd(), "data", "shortlists")
    if not os.path.isdir(shortlist_dir):
        logger.warning(f"Shortlists directory not found: {shortlist_dir}")
        return 0

    files = sorted(glob.glob(os.path.join(shortlist_dir, "shortlist_*.csv")))
    if not files:
        logger.info("No shortlist CSV files found")
        return 0

    total = 0
    for fpath in files:
        try:
            df = pd.read_csv(fpath)
            if df.empty or "symbol" not in df.columns:
                continue

            basename = os.path.basename(fpath)
            scan_timestamp = _parse_scan_datetime(basename)
            scan_id = basename.replace(".csv", "")

            results = df.to_dict("records")
            count = repo.save_scan(
                scan_id=scan_id,
                scan_timestamp=scan_timestamp,
                results=results,
                source_file=basename,
            )
            total += count
            logger.debug(f"  {basename}: {count} rows")
        except Exception as e:
            logger.error(f"Failed to import {fpath}: {e}")

    logger.info(f"Imported {total} scan results from {len(files)} CSV files → DB")
    return total


def _parse_scan_datetime(filename: str) -> str:
    """Extract ISO datetime from shortlist filename."""
    try:
        base = filename.replace(".csv", "")
        parts = base.split("_")
        for i, p in enumerate(parts):
            if len(p) == 8 and p.isdigit() and p.startswith("20"):
                date_str = p
                time_str = (
                    parts[i + 1]
                    if i + 1 < len(parts) and len(parts[i + 1]) == 4 and parts[i + 1].isdigit()
                    else "0000"
                )
                dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M")
                return dt.isoformat()
    except Exception:
        pass
    return datetime.utcnow().isoformat()


def main() -> None:
    force = "--force" in sys.argv

    logger.info("=" * 50)
    logger.info("FinPilot CSV → SQLite Migration")
    logger.info("=" * 50)

    sig_count = migrate_signal_log(force=force)
    scan_count = migrate_shortlists(force=force)

    logger.info("-" * 50)
    logger.info(f"Done: {sig_count} signals + {scan_count} scan results migrated")


if __name__ == "__main__":
    main()
