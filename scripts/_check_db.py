import sqlite3
from pathlib import Path

db = Path("data/finpilot.db")
print("DB exists:", db.exists(), "size:", db.stat().st_size if db.exists() else "N/A")
if not db.exists():
    print("DB not found - need to run migrate_signal_archive_to_sqlite.py first")
else:
    conn = sqlite3.connect(str(db))
    tables = [
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    ]
    print("Tables:", tables)
    if "signals_archive" in tables:
        total = conn.execute("SELECT COUNT(*) FROM signals_archive").fetchone()[0]
        null_st = conn.execute(
            "SELECT COUNT(*) FROM signals_archive WHERE resolved_status IS NULL"
        ).fetchone()[0]
        non_null = conn.execute(
            "SELECT COUNT(*) FROM signals_archive WHERE resolved_status IS NOT NULL"
        ).fetchone()[0]
        null_fp = conn.execute(
            "SELECT COUNT(*) FROM signals_archive WHERE finpilot_score IS NULL"
        ).fetchone()[0]
        print(f"Total rows: {total}  |  resolved_status NULL: {null_st}  |  resolved: {non_null}")
        print(f"finpilot_score NULL: {null_fp}")
        rows = conn.execute(
            "SELECT id, symbol, ts, score, finpilot_score, resolved_status, resolved_pct FROM signals_archive LIMIT 5"
        ).fetchall()
        for r in rows:
            print(" ", r)
    conn.close()
