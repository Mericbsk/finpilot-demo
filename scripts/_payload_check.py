import json
import sqlite3

conn = sqlite3.connect("data/finpilot.db")

# Check what payload keys old records use for price
print("=== NULL STATUS RECORDS (previously open, now reset) ===")
rows = conn.execute(
    "SELECT payload_json FROM signals_archive " "WHERE resolved_status IS NULL LIMIT 5"
).fetchall()
for r in rows:
    d = json.loads(r[0]) if r[0] else {}
    keys = [k for k in d if "price" in k.lower() or k == "entry" or k == "stop" or k == "take"]
    print(
        f"  Price-related keys: {keys}  entry_price={d.get('entry_price')}  price={d.get('price')}"
    )

print()
print("=== COUNTS: entry_price key presence ===")
r = conn.execute(
    "SELECT "
    "SUM(CASE WHEN JSON_EXTRACT(payload_json,'$.entry_price')>0 THEN 1 ELSE 0 END),"
    "SUM(CASE WHEN JSON_EXTRACT(payload_json,'$.price')>0 THEN 1 ELSE 0 END),"
    "COUNT(*) FROM signals_archive WHERE resolved_status IS NULL"
).fetchone()
print(f"  NULL status total={r[2]}  entry_price>0: {r[0]}  price>0: {r[1]}")

print()
print("=== DB barrier/t5 null status after fix ===")
r = conn.execute(
    "SELECT COUNT(*), "
    "SUM(CASE WHEN resolved_pct_barrier IS NOT NULL THEN 1 ELSE 0 END),"
    "SUM(CASE WHEN resolved_pct_t5 IS NOT NULL THEN 1 ELSE 0 END) "
    "FROM signals_archive"
).fetchone()
print(f"  Total={r[0]}  barrier_resolved={r[1]}  t5_resolved={r[2]}")

print()
# What does a score>18 record payload look like?
print("=== score>18 sample payload keys ===")
rows = conn.execute("SELECT payload_json FROM signals_archive WHERE score>18 LIMIT 3").fetchall()
for r in rows:
    d = json.loads(r[0]) if r[0] else {}
    print(
        f"  Keys with price: {[k for k in d if 'price' in k.lower() or k in ('stop_loss','take_profit','entry_price')]}"
    )
    print(
        f"  entry_price={d.get('entry_price')}  stop_loss={d.get('stop_loss')}  take_profit={d.get('take_profit')}"
    )
conn.close()
