#!/usr/bin/env python3
"""TEST 5 — Sektor. EODHD fundamentals'tan sektor; base kapi precision'i sektore gore."""

import csv
import json
import os
import time
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
bd = os.path.join(ROOT, "data", "backtest_out")
CSVP = os.path.join(bd, "enriched_signals_v3.csv")
if not os.path.exists(CSVP):
    CSVP = os.path.join(bd, "enriched_signals_v2.csv")
CACHE = os.path.join(ROOT, "data", "sector_cache.json")
try:
    import requests
except ImportError:
    raise SystemExit("pip install requests") from None


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
cache = {}
if os.path.exists(CACHE):
    try:
        cache = json.load(open(CACHE))
    except Exception:
        cache = {}
syms = sorted({r["symbol"] for r in base})
print(f"BASE {len(base)} sinyal, {len(syms)} sembol; sektor cekiliyor...")
for i, s in enumerate(syms, 1):
    if s in cache:
        continue
    try:
        r = requests.get(
            f"https://eodhd.com/api/fundamentals/{s}.US",
            params={"api_token": KEY, "filter": "General::Sector"},
            timeout=25,
        )
        cache[s] = (r.text.strip().strip('"') if r.status_code == 200 else "") or "Unknown"
    except Exception:
        cache[s] = "Unknown"
    time.sleep(0.08)
    if i % 40 == 0:
        print(f"  {i}/{len(syms)}...")
        json.dump(cache, open(CACHE, "w"))
json.dump(cache, open(CACHE, "w"))


def P(sub, k):
    return sum(r[k] for r in sub) / len(sub) if sub else 0


b5 = P(base, "y5")
bysec = defaultdict(list)
for r in base:
    bysec[cache.get(r["symbol"], "Unknown")].append(r)
print(f"\n=== SEKTORE GORE precision (base >=5% {b5*100:.1f}%) ===")
for sec, rs in sorted(bysec.items(), key=lambda kv: -P(kv[1], "y5")):
    if len(rs) >= 15:
        print(
            f"  {sec:26s} n={len(rs):>4} >=5% {P(rs,'y5')*100:5.1f}%  >=10% {P(rs,'y10')*100:5.1f}%"
        )
print("\n>>> Bazi sektorler belirgin yuksek/dusukse, sektor-farkinda agirlik/filtre eklenebilir.")
print("Bu ciktinin TAMAMINI Claude'a yapistir.")
