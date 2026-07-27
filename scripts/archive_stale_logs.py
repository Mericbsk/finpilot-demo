"""Archive stale log files to logs/_archive/ (log hygiene).

Moves top-level logs/*.log older than KEEP_DAYS into logs/_archive/, EXCEPT the
live api.log and its RotatingFileHandler backups (api.log.1 … api.log.5).
The many Feb–May training/backtest logs clutter logs/ and bury real errors;
archiving (not deleting) keeps them recoverable. Idempotent.

Usage:
    python scripts/archive_stale_logs.py             # default --days 14
    python scripts/archive_stale_logs.py --days 30
    python scripts/archive_stale_logs.py --dry-run
"""

from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
ARCHIVE = LOG_DIR / "_archive"


def _is_live_api_log(name: str) -> bool:
    # keep api.log and its rotation backups (api.log.1 … api.log.5)
    return name == "api.log" or name.startswith("api.log.")


def archive_stale(days: int = 14, dry_run: bool = False, log_dir: Path | None = None) -> dict:
    ldir = log_dir or LOG_DIR
    if not ldir.exists():
        return {"error": f"no logs dir: {ldir}"}
    archive = ldir / "_archive"
    cutoff = time.time() - days * 86400
    moved: list[str] = []
    kept = 0
    for f in sorted(ldir.glob("*.log")):
        if _is_live_api_log(f.name) or f.stat().st_mtime >= cutoff:
            kept += 1
            continue
        if not dry_run:
            archive.mkdir(parents=True, exist_ok=True)
            shutil.move(str(f), str(archive / f.name))
        moved.append(f.name)
    return {"archived": len(moved), "kept": kept, "dry_run": dry_run, "files": moved}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--days", type=int, default=14)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    print(archive_stale(args.days, args.dry_run))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
