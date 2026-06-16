import json
import sqlite3

conn = sqlite3.connect("data/finpilot.db")
rows = conn.execute(
    "SELECT id, symbol, ts, score, payload_json FROM signals_archive WHERE score>18 LIMIT 12"
).fetchall()
print("=== score>18 records ts and payload ===")
for r in rows:
    d = json.loads(r[4]) if r[4] else {}
    ep = d.get("entry_price") or d.get("price")
    sd = d.get("signal_date") or d.get("added_at")
    print(
        f"  id={str(r[0])[:30]:30s}  ts={str(r[2])[:20]:20s}  entry_price={ep}  signal_date_in_payload={sd}"
    )
conn.close()
