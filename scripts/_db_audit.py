import sqlite3

conn = sqlite3.connect("data/finpilot.db")

print("=== SCORE BUCKETS IN DB ===")
for label, where in [
    ("score=0", "score=0"),
    ("score 0-3", "score>0 AND score<=3"),
    ("score 3-18", "score>3 AND score<=18"),
    ("score >18", "score>18"),
]:
    r = conn.execute(
        f"SELECT COUNT(*), ROUND(AVG(resolved_pct),3), "
        f"SUM(CASE WHEN resolved_status NOT IN ('open') THEN 1 ELSE 0 END) "
        f"FROM signals_archive WHERE {where}"
    ).fetchone()
    print(f"  {label:12s}: n={r[0]:5d}  avg_pct={r[1]}  lifecycle_resolved={r[2]}")

print()
print("=== BARRIER STATUS DISTRIBUTION ===")
rows = conn.execute(
    "SELECT resolved_status_barrier, COUNT(*) FROM signals_archive "
    "GROUP BY resolved_status_barrier ORDER BY 2 DESC"
).fetchall()
for row in rows:
    print(f"  {row[0]}: {row[1]}")

print()
print("=== score>18 samples (0-100 scale) ===")
rows = conn.execute(
    "SELECT symbol, score, resolved_status, resolved_pct, resolved_pct_barrier, resolved_status_barrier "
    "FROM signals_archive WHERE score>18 LIMIT 8"
).fetchall()
for r in rows:
    print(" ", r)

conn.close()
