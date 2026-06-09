import csv
import os

# Sort by modification time to get the actual latest file
files = [
    os.path.join("data/shortlists", f)
    for f in os.listdir("data/shortlists")
    if f.startswith("shortlist_") and f.endswith(".csv")
]
files.sort(key=os.path.getmtime, reverse=True)
latest = files[0]
print(f"Analyzing: {os.path.basename(latest)}")

rows = list(csv.DictReader(open(latest, encoding="utf-8")))
print(f"Total rows: {len(rows)}")

print("\nTop 10 by finpilot_score:")
rows_sorted = sorted(rows, key=lambda r: float(r.get("finpilot_score", 0) or 0), reverse=True)
for r in rows_sorted[:10]:
    sym = r["symbol"]
    score = r.get("score", "?")
    direction = r.get("direction", "?")
    entry_ok = r.get("entry_ok", "?")
    mkt = r.get("market_status", "?")
    composite = r.get("composite_score", "?")
    fp = r.get("finpilot_score", "?")
    liq = r.get("liquidity_ok", "?")
    print(
        f"  {sym:6s} score={score} dir={direction} entry_ok={entry_ok} liq={liq} mkt={mkt} composite={composite} fp={fp}"
    )

from collections import Counter

score_dist = Counter(r["score"] for r in rows)
dir_dist = Counter(r["direction"] for r in rows)
print(f"\nScore distribution: {dict(sorted(score_dist.items()))}")
print(f"Direction distribution: {dict(dir_dist)}")
print(f'entry_ok True: {sum(1 for r in rows if r["entry_ok"]=="True")}')
print(f'entry_ok False: {sum(1 for r in rows if r["entry_ok"]=="False")}')
