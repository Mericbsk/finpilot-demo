import json
import sqlite3

conn = sqlite3.connect("data/finpilot.db")

print("=== WATCHING RECORDS SAMPLE ===")
rows = conn.execute(
    "SELECT id, symbol, ts, score, resolved_status, payload_json "
    "FROM signals_archive WHERE resolved_status='watching' LIMIT 6"
).fetchall()
for r in rows:
    d = json.loads(r[5]) if r[5] else {}
    print(
        f"  {r[1]:6s} score={r[3]:5.1f} ts={r[2][:10]}  entry_price={d.get('entry_price')} stop={d.get('stop_loss')} tp={d.get('take_profit')}"
    )

print()
print("=== WATCHING: entry_price distribution ===")
r = conn.execute(
    "SELECT COUNT(*), SUM(CASE WHEN JSON_EXTRACT(payload_json,'$.entry_price')>0 THEN 1 ELSE 0 END) "
    "FROM signals_archive WHERE resolved_status='watching'"
).fetchone()
print(f"  Total watching: {r[0]}  with entry_price>0: {r[1]}")

print()
print("=== score>18 watching — full sample ===")
rows = conn.execute(
    "SELECT id, symbol, ts, score, resolved_status, resolved_pct_barrier FROM signals_archive "
    "WHERE resolved_status='watching' AND score>18 LIMIT 8"
).fetchall()
for r in rows:
    print(f"  {r[0][:30]:30s}  score={r[3]:5.1f}  barrier={r[5]}")
conn.close()
