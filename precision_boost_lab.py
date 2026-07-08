#!/usr/bin/env python3
"""
PRECISION-ARTIRICI MEKANIZMA LABI
=================================
6 mekanizmanin base-kapiya (short>=15 & ATR>=4) kiyasla precision KATKISINI ve
sinyal sayisi etkisini olcer. Amac: daha AZ + daha DOGRU sinyal.
enriched_signals_v3.csv (nokta-zamanli short) uzerinde.

Kullanim:  python precision_boost_lab.py    -> ciktinin TAMAMINI yapistir.
"""

import csv
import os

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


def gap(r):
    return ff(r.get("gap_pct")) or -9


def rvol(r):
    return ff(r.get("rvol")) or 0


def ent(r):
    return ff(r.get("entry")) or 0


def d52(r):
    return ff(r.get("dist_52w_high")) or 0


for r in rows:
    r["y5"] = 1 if ff(r["resolved_pct_t5"]) >= 5 else 0
    r["y10"] = 1 if ff(r["resolved_pct_t5"]) >= 10 else 0
    r["_d"] = r["signal_date"][:10]
N = len(rows)
ndays = len({r["_d"] for r in rows})
b5 = sum(r["y5"] for r in rows) / N
b10 = sum(r["y10"] for r in rows) / N
print(f"n={N} gun={ndays} baz >=5% {b5*100:.1f}% >=10% {b10*100:.1f}%")


def P(sub, k):
    return sum(r[k] for r in sub) / len(sub) if sub else 0


def show(name, sub, ref=None):
    if len(sub) < 20:
        print(f"  {name:34s} n={len(sub)} (yetersiz)")
        return
    d5 = f" (+{(P(sub,'y5')-ref)*100:+.1f}p)" if ref is not None else ""
    print(
        f"  {name:34s} n={len(sub):>4} ~{len(sub)/ndays:4.1f}/gun  >=5% {P(sub,'y5')*100:5.1f}%{d5}  >=10% {P(sub,'y10')*100:5.1f}%"
    )


def BASE(r):
    return sh(r) >= 15 and atr(r) >= 4


base = [r for r in rows if BASE(r)]
bp = P(base, "y5")
print("\n### BASE KAPI: short>=15 & ATR>=4  (kiyas referansi) ###")
show("BASE", base)

print("\n=== M1: FAKTOR CIFTLERI (en dayanikli ikili) ===")
show("short>=15 & gap>=3", [r for r in rows if sh(r) >= 15 and gap(r) >= 3], bp)
show("short>=15 & RVOL>=2", [r for r in rows if sh(r) >= 15 and rvol(r) >= 2], bp)
show("gap>=3 & ATR>=4", [r for r in rows if gap(r) >= 3 and atr(r) >= 4], bp)
show("short>=20 & gap>=1", [r for r in rows if sh(r) >= 20 and gap(r) >= 1], bp)

print("\n=== M2: BASE + LIKIDITE/FIYAT TABANI ===")
for pmin in [3, 5, 10]:
    show(f"BASE & entry>=${pmin}", [r for r in base if ent(r) >= pmin], bp)

print("\n=== M3: BASE + ASIRI-UZAMA SERT FILTRE (dist52<=X) ===")
for c in [0.95, 0.90, 0.85]:
    show(f"BASE & dist52<={c}", [r for r in base if d52(r) <= c], bp)

print("\n=== M4: KALICILIK (persistence) — ayni sembol >=2 gun sinyal ===")
from collections import defaultdict

days_by_sym = defaultdict(set)
for r in rows:
    days_by_sym[r["symbol"]].add(r["_d"])
show("BASE & sembol >=2 gun", [r for r in base if len(days_by_sym[r["symbol"]]) >= 2], bp)
show("BASE & sembol tek gun", [r for r in base if len(days_by_sym[r["symbol"]]) == 1], bp)

print("\n=== M5: OLASILIK TABANI (mutlak) — IS vs OOS stabilite ===")


def comp(r):
    return (
        4 * min(sh(r) / 20, 1)
        + 3 * min(atr(r) / 6, 1)
        + 3 * min(max(gap(r), 0) / 5, 1)
        + 2 * min(max(rvol(r) - 1, 0) / 2, 1)
        - 1.5 * min(max(d52(r) - 0.9, 0) / 0.1, 1)
    )


for r in rows:
    r["_c"] = comp(r)
IS = [r for r in rows if r["_d"] < "2026-01-01"]
OOS = [r for r in rows if r["_d"] >= "2026-01-01"]
for thr in [4.0, 4.8, 6.0]:
    si = [r for r in IS if r["_c"] >= thr]
    so = [r for r in OOS if r["_c"] >= thr]
    pi = P(si, "y5") * 100 if len(si) >= 20 else float("nan")
    po = P(so, "y5") * 100 if len(so) >= 20 else float("nan")
    print(
        f"  skor>={thr}: IS n={len(si)} >=5% {pi:.1f}%  |  OOS n={len(so)} >=5% {po:.1f}%  (fark {po-pi:+.1f}p)"
    )

print("\n=== M6: KOMBINE BEST-OF (kazananlari yigin) ===")
combo = [r for r in rows if sh(r) >= 15 and gap(r) >= 3 and ent(r) >= 3 and d52(r) <= 0.95]
show("short>=15 & gap>=3 & entry>=$3 & dist52<=0.95", combo, bp)
# IS/OOS
ci = [r for r in combo if r["_d"] < "2026-01-01"]
co = [r for r in combo if r["_d"] >= "2026-01-01"]
if len(ci) >= 10 and len(co) >= 10:
    print(
        f"    IS: n={len(ci)} >=5% {P(ci,'y5')*100:.1f}% >=10% {P(ci,'y10')*100:.1f}%  |  OOS: n={len(co)} >=5% {P(co,'y5')*100:.1f}% >=10% {P(co,'y10')*100:.1f}%"
    )
print(
    "\n>>> '+Xp' = base kapiya gore precision KATKISI. Katki + ve sinyal sayisi makul ise mekanizma degerli."
)
print("Bu ciktinin TAMAMINI Claude'a yapistir — sonuca gore karar veririz.")
