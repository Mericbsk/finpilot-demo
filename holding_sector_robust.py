#!/usr/bin/env python3
"""
TUTMA SURESI + SEKTOR ROBUSTLUK
===============================
(1) T+10 getirisi outlier mi: median + tipik drawdown (kapanis bazli).
(2) Sektor precision IS 2025 vs OOS 2026 — dagilim donemler arasi tutuyor mu.
Cache kullanir (test4=daily_cache_h, test5=sector_cache); yoksa EODHD'den ceker.
Kullanim:  python holding_sector_robust.py   -> ciktiyi yapistir.
"""

import csv
import json
import os
import statistics as st
import time
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
bd = os.path.join(ROOT, "data", "backtest_out")
CSVP = os.path.join(bd, "enriched_signals_v3.csv")
if not os.path.exists(CSVP):
    CSVP = os.path.join(bd, "enriched_signals_v2.csv")
DCACHE = os.path.join(ROOT, "data", "daily_cache_h")
os.makedirs(DCACHE, exist_ok=True)
SCACHE = os.path.join(ROOT, "data", "sector_cache.json")
try:
    import requests
except ImportError:
    requests = None


def env():
    e = {}
    for line in open(os.path.join(ROOT, ".env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    return e


KEY = env().get("EODHD_API_KEY", "")


def ff(x):
    try:
        return float(x)
    except Exception:
        return None


rows = [r for r in csv.DictReader(open(CSVP)) if ff(r.get("resolved_pct_t5")) is not None]


def sh(r):
    s = r.get("short_pit")
    s = ff(s) if s not in (None, "") else ff(r.get("short_pct"))
    return s if s is not None else 0.0


for r in rows:
    r["y5"] = 1 if ff(r["resolved_pct_t5"]) >= 5 else 0
    r["y10"] = 1 if ff(r["resolved_pct_t5"]) >= 10 else 0
base = [r for r in rows if sh(r) >= 15 and (ff(r.get("atr_pct")) or 0) >= 4]


def daily(sym):
    cf = os.path.join(DCACHE, f"{sym}.json")
    if os.path.exists(cf):
        try:
            return json.load(open(cf))
        except Exception:
            return []
    if not requests or not KEY:
        return []
    r = requests.get(
        f"https://eodhd.com/api/eod/{sym}.US",
        params={
            "api_token": KEY,
            "fmt": "json",
            "from": "2025-08-01",
            "to": "2026-07-01",
            "period": "d",
        },
        timeout=30,
    )
    out = (
        [(b["date"], ff(b.get("high")), ff(b.get("close"))) for b in r.json()]
        if r.status_code == 200
        else []
    )
    out.sort()
    json.dump(out, open(cf, "w"))
    time.sleep(0.08)
    return out


print(f"BASE (short>=15 & ATR>=4): {len(base)} sinyal")
print("\n=== 1) TUTMA SURESI T+10: outlier mi? (gunluk veri) ===")
cr10 = []
mf10 = []
dd10 = []
done = 0
for r in base:
    bars = daily(r["symbol"])
    if not bars:
        continue
    idx = {d: i for i, (d, _, _) in enumerate(bars)}
    d0 = r["signal_date"][:10]
    di = idx.get(d0)
    if di is None:
        for i, (d, _, _) in enumerate(bars):
            if d >= d0:
                di = i
                break
    if di is None:
        continue
    e = ff(r.get("entry")) or bars[di][2]
    if not e or e <= 0:
        continue
    fwd = bars[di + 1 : di + 11]
    if len(fwd) < 3:
        continue
    cr10.append((fwd[-1][2] - e) / e * 100)
    mf10.append((max(b[1] for b in fwd if b[1]) - e) / e * 100)
    dd10.append((min(b[2] for b in fwd if b[2]) - e) / e * 100)  # en kotu kapanis (drawdown proxy)
    done += 1
    if done % 60 == 0:
        print(f"  {done}...")
if done >= 20:
    print(f"  n={done}")
    print(
        f"  T+10 close getiri: ORT {st.mean(cr10):+.1f}%  MEDYAN {st.median(cr10):+.1f}%  pozitif %{sum(1 for x in cr10 if x>0)/len(cr10)*100:.0f}"
    )
    print(
        f"  T+10 tipik DRAWDOWN (medyan en-kotu kapanis): {st.median(dd10):+.1f}%  |  %10 kotu dilim: {sorted(dd10)[int(len(dd10)*0.1)]:+.1f}%"
    )
    print("  >>> ORT >> MEDYAN ise kazanc birkac outlier'dan; MEDYAN da pozitifse genis/gercek.")
else:
    print(
        f"  Yetersiz gunluk veri ({done}). test4_horizon.py cache'ini olustur ya da EODHD calissin."
    )

print("\n=== 2) SEKTOR IS vs OOS ===")
if os.path.exists(SCACHE):
    sec = json.load(open(SCACHE))

    def P(sub):
        return sum(r["y5"] for r in sub) / len(sub) if sub else 0

    bysec_is = defaultdict(list)
    bysec_oos = defaultdict(list)
    for r in base:
        s = sec.get(r["symbol"], "Unknown")
        (bysec_is if r["signal_date"][:10] < "2026-01-01" else bysec_oos)[s].append(r)
    secs = sorted(set(list(bysec_is) + list(bysec_oos)))
    print(f"  {'sektor':24s}{'IS n':>6}{'IS >=5%':>9}{'OOS n':>7}{'OOS >=5%':>10}{'tutarli?':>10}")
    for s in secs:
        i = bysec_is.get(s, [])
        o = bysec_oos.get(s, [])
        if len(i) >= 10 and len(o) >= 10:
            pi, po = P(i) * 100, P(o) * 100
            tut = "EVET" if abs(pi - po) < 15 else "kaydi"
            print(f"  {s:24s}{len(i):>6}{pi:>8.1f}%{len(o):>7}{po:>9.1f}%{tut:>10}")
    print(
        "  >>> Bir sektor IS ve OOS'ta da yuksek/dusukse -> sektor tilt guvenli. Sallaniyorsa -> ekleme."
    )
else:
    print("  sector_cache.json yok — once test5_sector.py koş.")
print("\nBu ciktinin TAMAMINI Claude'a yapistir.")
