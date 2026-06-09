"""End-to-end NASDAQ data verification."""

import json
import urllib.request

BASE = "http://localhost:8001/api/v1"


def get(path):
    with urllib.request.urlopen(f"{BASE}{path}", timeout=30) as r:  # noqa: S310  # nosec B310 — localhost only
        return json.loads(r.read())


print("=" * 60)
print("1) /quotes -- 10 NASDAQ blue-chips (anlik fiyat)")
print("=" * 60)
syms = "AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA,AVGO,AMD,NFLX"
d = get(f"/quotes?symbols={syms}")
ok, bad = [], []
for sym, q in d.items():
    if isinstance(q, dict) and q.get("price"):
        ok.append(sym)
        chg = q.get("change", 0) or 0
        print(f"  {sym:6} ${q['price']:>8}  chg={chg:>+6.2f}  state={q.get('marketState','?')}")
    else:
        bad.append(sym)
print(f"OK: {len(ok)}/{len(d)}  BAD: {bad}")

print()
print("=" * 60)
print("2) /chart 1d -- NVDA last 90 days")
print("=" * 60)
d = get("/chart/NVDA?interval=1d&days=90")
c = d.get("candles", [])
print(f"  candles: {len(c)}")
if c:
    last = c[-1]
    print(f"  last bar: t={last.get('time')}, close=${last.get('close')}, vol={last.get('volume')}")

print()
print("=" * 60)
print("3) /chart 15m -- AAPL last 5 days (intraday)")
print("=" * 60)
d = get("/chart/AAPL?interval=15m&days=5")
c = d.get("candles", [])
print(f"  candles: {len(c)}")
if c:
    last = c[-1]
    print(f"  last bar: t={last.get('time')}, close=${last.get('close')}, vol={last.get('volume')}")

print()
print("=" * 60)
print("4) /chart 1h -- MSFT last 30 days")
print("=" * 60)
d = get("/chart/MSFT?interval=1h&days=30")
c = d.get("candles", [])
print(f"  candles: {len(c)}")
if c:
    last = c[-1]
    print(f"  last bar: t={last.get('time')}, close=${last.get('close')}")

print()
print("=" * 60)
print("5) Preset NASDAQ groups -- 15 sample symbols from 3 presets")
print("=" * 60)
presets = json.load(open("web/public/stock_presets.json", encoding="utf-8"))
sample = []
for k in ["tech_giants", "semiconductors", "ai_leaders"]:
    sample += presets[k]["symbols"][:5]
d = get(f"/quotes?symbols={','.join(sample)}")
ok2 = [s for s, q in d.items() if isinstance(q, dict) and q.get("price")]
bad2 = [s for s in sample if s not in ok2]
print(f"  Tested: {len(sample)} symbols -> {len(ok2)} priced OK")
if bad2:
    print(f"  MISSING PRICE: {bad2}")
else:
    print("  All NASDAQ preset samples returned valid prices.")
