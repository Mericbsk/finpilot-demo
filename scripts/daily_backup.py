"""Daily backup for FinPilot critical data.

Called automatically at the end of a successful publish_now run, or manually:
    python scripts/daily_backup.py

- Copies SQLite DBs via the sqlite3 backup API (safe against mid-write WAL state).
- Copies latest snapshot/export JSONs.
- Verifies integrity of every copied DB; a failed check exits non-zero (loud).
- Prunes backup folders older than KEEP_DAYS.
- If FINPILOT_BACKUP_EXTERNAL_DIR is set (a folder OUTSIDE OneDrive), Mondays
  also mirror the day's backup there.
"""

from __future__ import annotations

import datetime as dt
import os
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP_ROOT = ROOT / "backups"
KEEP_DAYS = 14

DB_FILES = [
    ROOT / "data" / "finpilot.db",
    ROOT / "data" / "distribution.db",
    ROOT / "data" / "academy.db",
]
JSON_FILES = [
    ROOT / "data" / "distribution" / "snapshot_latest.json",
    ROOT / "data" / "distribution" / "snapshot_en_latest.json",
    ROOT / "web" / "public" / "demo_snapshot.json",
]


def _backup_db(src: Path, dest: Path) -> None:
    """Copy a SQLite DB (backup API, file-copy fallback), then verify integrity."""
    try:
        with sqlite3.connect(f"file:{src}?mode=ro", uri=True) as src_con:
            dest_con = sqlite3.connect(dest)
            try:
                src_con.backup(dest_con)
            finally:
                dest_con.close()
    except sqlite3.Error:
        # Fallback for filesystems where the backup API fails: plain copy
        # including any WAL/SHM sidecars, verified below like the main path.
        shutil.copyfile(src, dest)  # copyfile overwrites in place
        for suffix in ("-wal", "-shm"):
            side = src.parent / (src.name + suffix)
            if side.exists():
                shutil.copyfile(side, dest.parent / (dest.name + suffix))
    _verify_db(dest)


def _verify_db(dest: Path) -> None:
    """integrity_check on a local temp copy (WAL recovery needs a writable,
    lock-friendly filesystem; the backup destination may be neither)."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_db = Path(tmp) / dest.name
        shutil.copyfile(dest, tmp_db)
        for suffix in ("-wal", "-shm"):
            side = dest.parent / (dest.name + suffix)
            if side.exists():
                shutil.copyfile(side, Path(tmp) / (dest.name + suffix))
        check = sqlite3.connect(tmp_db)
        try:
            result = check.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            check.close()
    if result != "ok":
        raise RuntimeError(f"integrity_check failed for {dest.name}: {result}")


def _prune(root: Path, keep_days: int) -> list[str]:
    removed: list[str] = []
    cutoff = dt.date.today() - dt.timedelta(days=keep_days)
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        try:
            day = dt.date.fromisoformat(entry.name)
        except ValueError:
            continue  # not a dated backup dir — never touch
        if day < cutoff:
            shutil.rmtree(entry)
            removed.append(entry.name)
    return removed


def run_backup() -> Path:
    today = dt.date.today().isoformat()
    dest_dir = BACKUP_ROOT / today
    dest_dir.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    for db in DB_FILES:
        if db.exists():
            _backup_db(db, dest_dir / db.name)
            copied.append(db.name)
    for jf in JSON_FILES:
        if jf.exists():
            shutil.copyfile(jf, dest_dir / jf.name)
            copied.append(jf.name)

    removed = _prune(BACKUP_ROOT, KEEP_DAYS)

    external = os.environ.get("FINPILOT_BACKUP_EXTERNAL_DIR", "").strip()
    mirrored = False
    if external and dt.date.today().weekday() == 0:  # Monday
        ext_dir = Path(external) / today
        ext_dir.mkdir(parents=True, exist_ok=True)
        for f in dest_dir.iterdir():
            shutil.copyfile(f, ext_dir / f.name)
        mirrored = True

    print(
        f"backup ok → {dest_dir} | files: {len(copied)}"
        + (f" | pruned: {removed}" if removed else "")
        + (" | external mirror: yes" if mirrored else "")
    )
    return dest_dir


if __name__ == "__main__":
    try:
        run_backup()
    except Exception as exc:  # loud failure — a broken backup must never be silent
        print(f"BACKUP FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
