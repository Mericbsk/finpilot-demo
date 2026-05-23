"""Migrate data/signal_archive/*.json → SQLite signals_archive table.

Idempotent: uses INSERT OR IGNORE keyed on signal id.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DIR = ROOT / "data" / "signal_archive"
DB_PATH = ROOT / "data" / "finpilot.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS signals_archive (
    id              TEXT PRIMARY KEY,
    symbol          TEXT,
    ts              TEXT,
    score           REAL,
    finpilot_score  REAL,
    payload_json    TEXT,
    resolved_status TEXT,
    resolved_pct    REAL
);
CREATE INDEX IF NOT EXISTS ix_signals_archive_symbol ON signals_archive(symbol);
CREATE INDEX IF NOT EXISTS ix_signals_archive_ts     ON signals_archive(ts);
"""


def _row(record: dict, fallback_date: str) -> tuple:
    sid = str(
        record.get("id")
        or f"{record.get('symbol', '?')}_{record.get('signal_date') or fallback_date}"
    )
    symbol = str(record.get("symbol") or "")
    ts = str(record.get("added_at") or record.get("signal_date") or fallback_date)
    score = record.get("score")
    fp = record.get("finpilot_score")
    sl = record.get("status_lifecycle") or {}
    if isinstance(sl, dict):
        status = sl.get("outcome") or sl.get("status")
        rpct = sl.get("outcome_pct") or sl.get("profit_pct")
    else:
        status = str(sl) if sl else None
        rpct = None
    return (
        sid,
        symbol,
        ts,
        float(score) if score is not None else None,
        float(fp) if fp is not None else None,
        json.dumps(record, ensure_ascii=False),
        str(status) if status is not None else None,
        float(rpct) if rpct is not None else None,
    )


def main() -> int:
    if not ARCHIVE_DIR.exists():
        print(f"archive dir missing: {ARCHIVE_DIR}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    files = sorted(ARCHIVE_DIR.glob("*.json"))
    inserted = 0
    total = 0
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                continue
            for rec in data:
                total += 1
                try:
                    cur = conn.execute(
                        "INSERT OR IGNORE INTO signals_archive "
                        "(id, symbol, ts, score, finpilot_score, payload_json, resolved_status, resolved_pct) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        _row(rec, f.stem),
                    )
                    inserted += cur.rowcount
                except Exception as exc:
                    print(f"[warn] {f.name} row failed: {exc}", file=sys.stderr)
        except Exception as exc:
            print(f"[warn] {f.name}: {exc}", file=sys.stderr)
    conn.commit()
    conn.close()
    print(f"files={len(files)} rows_seen={total} inserted={inserted} db={DB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
