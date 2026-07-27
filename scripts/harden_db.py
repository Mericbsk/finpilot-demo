"""One-shot DB hardening: convert WAL → DELETE journal mode (corruption fix).

Why: WAL keeps -wal/-shm sidecar files. Under OneDrive sync or antivirus locks
these desync from the main .db and corrupt it on next open — the root cause of
the 2026-07-03 and 2026-07-15 finpilot.db corruption events. FinPilot's manual
single-writer flow does not need WAL concurrency. academy.db (DELETE mode) has
never corrupted; the WAL databases corrupted twice.

For each critical DB this: checkpoints any pending WAL into the main file,
switches journal_mode to DELETE (removes the sidecars, persistent), and runs an
integrity_check. Idempotent — safe to re-run any time.

Usage:
    python scripts/harden_db.py            # harden the standard data/ DBs
    python scripts/harden_db.py PATH ...   # harden specific DB files
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DBS = [
    ROOT / "data" / "finpilot.db",
    ROOT / "data" / "distribution.db",
    ROOT / "data" / "academy.db",
]


def harden(db: Path) -> dict:
    if not db.exists():
        return {"db": db.name, "status": "missing"}
    con = sqlite3.connect(str(db), timeout=30)
    try:
        before = con.execute("PRAGMA journal_mode").fetchone()[0]
        if str(before).lower() == "wal":
            con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        after = con.execute("PRAGMA journal_mode=DELETE").fetchone()[0]
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        con.close()
    return {"db": db.name, "before": before, "after": after, "integrity": integrity}


def main(argv: list[str]) -> int:
    targets = [Path(a) for a in argv] or DEFAULT_DBS
    rc = 0
    for db in targets:
        r = harden(db)
        print(r)
        if r.get("status") != "missing" and r.get("integrity") not in (None, "ok"):
            rc = 1  # integrity failure → loud non-zero exit
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
