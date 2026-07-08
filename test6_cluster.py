#!/usr/bin/env python3
"""TEST 6 — Cluster / korelasyon. enriched_v3, yeni veri gerekmez."""

import csv
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


def comp(r):
    atr = ff(r.get("atr_pct")) or 0
    gap = ff(r.get("gap_pct")) or 0
    rvol = ff(r.get("rvol")) or 1
    d52 = ff(r.get("dist_52w_high")) or 0
    return (
        4 * min(sh(r) / 20, 1)
        + 3 * min(atr / 6, 1)
        + 3 * min(max(gap, 0) / 5, 1)
        + 2 * min(max(rvol - 1, 0) / 2, 1)
        - 1.5 * min(max(d52 - 0.9, 0) / 0.1, 1)
    )


for r in rows:
    r["y5"] = 1 if ff(r["resolved_pct_t5"]) >= 5 else 0
    r["y10"] = 1 if ff(r["resolved_pct_t5"]) >= 10 else 0
    r["_d"] = r["signal_date"][:10]
    r["_c"] = comp(r)
base = [r for r in rows if sh(r) >= 15 and (ff(r.get("atr_pct")) or 0) >= 4]


def P(sub, k):
    return sum(r[k] for r in sub) / len(sub) if sub else 0


byday = defaultdict(list)
for r in base:
    byday[r["_d"]].append(r)
print(f"BASE n={len(base)} precision >=5% {P(base,'y5')*100:.1f}%  gun={len(byday)}")

print("\n=== A) GUNLUK CLUSTER BUYUKLUGUNE GORE precision ===")
buckets = {"1": [], "2-5": [], "6-20": [], ">20": []}
for _d, rs in byday.items():
    n = len(rs)
    k = "1" if n == 1 else "2-5" if n <= 5 else "6-20" if n <= 20 else ">20"
    buckets[k] += rs
for k, rs in buckets.items():
    if len(rs) >= 20:
        print(
            f"  cluster {k:>5}: n={len(rs):>4} >=5% {P(rs,'y5')*100:5.1f}%  >=10% {P(rs,'y10')*100:5.1f}%"
        )
    else:
        print(f"  cluster {k:>5}: n={len(rs)} (yetersiz)")

print("\n=== B) TOP-1/gun (cluster'dan en iyi skor) vs HEPSI ===")
top1 = [max(rs, key=lambda r: r["_c"]) for rs in byday.values()]
print(
    f"  HEPSI:      n={len(base):>4} >=5% {P(base,'y5')*100:5.1f}% >=10% {P(base,'y10')*100:5.1f}%"
)
print(
    f"  TOP-1/gun:  n={len(top1):>4} >=5% {P(top1,'y5')*100:5.1f}% >=10% {P(top1,'y10')*100:5.1f}%"
)

print("\n=== C) AYNI-GUN KO-HAREKET (cluster gunlerinde birlikte kazan/kaybet) ===")
multi = [rs for rs in byday.values() if len(rs) >= 3]
allw = sum(1 for rs in multi if all(r["y5"] for r in rs))
alll = sum(1 for rs in multi if not any(r["y5"] for r in rs))
print(
    f"  >=3 sinyalli gun: {len(multi)}  hepsi-kazanan: {allw}  hepsi-kaybeden: {alll}  karisik: {len(multi)-allw-alll}"
)
print(
    "  (Yuksek 'hepsi-kaybeden' -> o gunler index/rejim etkisi; cluster gununu tek-pozisyona indirmek riski azaltir.)"
)
print("\nBu ciktinin TAMAMINI Claude'a yapistir.")
