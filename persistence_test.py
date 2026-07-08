#!/usr/bin/env python3
"""
KALICILIK TESTI (look-ahead'SIZ)
================================
Onceki testte 'sembol >=2 gun sinyal' TUM donemi sayiyordu (gelecek dahil = look-ahead).
Bu script SADECE sinyal gununden ONCEKI K takvim gununde ayni sembolun kac kez
sinyal verdigine bakar. Boylece kalicilik gercek/kullanilabilir bir sinyal olur.

Base kapi: short>=15 & ATR>=4. Onceki-sinyal sayisina gore precision.
Kullanim:  python persistence_test.py   -> ciktiyi yapistir.
"""

import csv
import datetime as dt
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
bd = os.path.join(ROOT, "data", "backtest_out")
CSVP = os.path.join(bd, "enriched_signals_v3.csv")
if not os.path.exists(CSVP):
    CSVP = os.path.join(bd, "enriched_signals_v2.csv")


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


def atr(r):
    return ff(r.get("atr_pct")) or 0


for r in rows:
    r["y5"] = 1 if ff(r["resolved_pct_t5"]) >= 5 else 0
    r["y10"] = 1 if ff(r["resolved_pct_t5"]) >= 10 else 0
    r["_d"] = dt.date.fromisoformat(r["signal_date"][:10])

# sembol -> sirali sinyal gunleri
bysym = defaultdict(list)
for r in sorted(rows, key=lambda r: r["_d"]):
    bysym[r["symbol"]].append(r["_d"])


def prior_count(sym, d, K):
    return sum(1 for dd in bysym[sym] if dd < d and (d - dd).days <= K)


def P(sub, k):
    return sum(r[k] for r in sub) / len(sub) if sub else 0


N = len(rows)
ndays = len({r["_d"] for r in rows})
b5 = P(rows, "y5")
base = [r for r in rows if sh(r) >= 15 and atr(r) >= 4]
print(
    f"n={N} gun={ndays}  BASE (short>=15&ATR>=4): n={len(base)} >=5% {P(base,'y5')*100:.1f}% >=10% {P(base,'y10')*100:.1f}%"
)

for K in [5, 10]:
    print(f"\n=== ONCEKI {K} GUN icinde ayni sembolun onceki sinyal sayisi ===")
    for label, cond in [
        ("0 (ilk kez)", lambda c: c == 0),
        (">=1 onceki", lambda c: c >= 1),
        (">=2 onceki", lambda c: c >= 2),
    ]:
        sub = [r for r in base if cond(prior_count(r["symbol"], r["_d"], K))]
        if len(sub) < 20:
            print(f"  {label:14s} n={len(sub)} (yetersiz)")
            continue
        print(
            f"  {label:14s} n={len(sub):>4} ~{len(sub)/ndays:4.1f}/gun  >=5% {P(sub,'y5')*100:5.1f}%  >=10% {P(sub,'y10')*100:5.1f}%"
        )

# IS/OOS dayaniklilik: >=1 onceki (K=10)
print("\n=== >=1 onceki (K=10) IS vs OOS ===")
sub = [r for r in base if prior_count(r["symbol"], r["_d"], 10) >= 1]
IS = [r for r in sub if r["_d"] < dt.date(2026, 1, 1)]
OOS = [r for r in sub if r["_d"] >= dt.date(2026, 1, 1)]
baseIS = [r for r in base if r["_d"] < dt.date(2026, 1, 1)]
baseOOS = [r for r in base if r["_d"] >= dt.date(2026, 1, 1)]
if len(IS) >= 15:
    print(f"  IS: kalici n={len(IS)} >=5% {P(IS,'y5')*100:.1f}%  (base {P(baseIS,'y5')*100:.1f}%)")
if len(OOS) >= 15:
    print(
        f"  OOS: kalici n={len(OOS)} >=5% {P(OOS,'y5')*100:.1f}%  (base {P(baseOOS,'y5')*100:.1f}%)"
    )
print(
    "\n>>> Onceki-sinyal olan grup base'den YUKSEKSE kalicilik gercek (look-ahead'siz) bir precision sinyalidir."
)
print("Bu ciktinin TAMAMINI Claude'a yapistir.")
