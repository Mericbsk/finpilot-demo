#!/usr/bin/env python3
"""
SKOR KALIBRASYON MONITORU — "hangi puan yuzde kac tutuyor" + kriter katkilari
=============================================================================
Tekrar calistirilabilir. Veri buyudukce koş: skorun hala kalibre oldugunu
(skor X -> ~%Y isabet) ve her kriterin marjinal dogruluk katkisini dogrular.
enriched_signals_v3.csv (nokta-zamanli short).
Kullanim:  python score_calibration.py   -> ciktinin TAMAMINI yapistir.
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


def d52(r):
    return ff(r.get("dist_52w_high")) or 0


for r in rows:
    r["y5"] = 1 if ff(r["resolved_pct_t5"]) >= 5 else 0
    r["y10"] = 1 if ff(r["resolved_pct_t5"]) >= 10 else 0


# canli skor (0-100'e olcekli, ALPHA_V2 bilesenleri)
def comp100(r):
    raw = (
        4 * min(sh(r) / 20, 1)
        + 3 * min(atr(r) / 6, 1)
        + 3 * min(max(gap(r), 0) / 5, 1)
        + 2 * min(max(rvol(r) - 1, 0) / 2, 1)
        - 1.5 * min(max(d52(r) - 0.9, 0) / 0.1, 1)
    )
    return max(0, min(100, raw / 12 * 100))


for r in rows:
    r["_s"] = comp100(r)
N = len(rows)
b5 = sum(r["y5"] for r in rows) / N
b10 = sum(r["y10"] for r in rows) / N


def P(sub, k):
    return sum(r[k] for r in sub) / len(sub) if sub else 0


print(f"n={N}  baz >=5% {b5*100:.1f}%  >=10% {b10*100:.1f}%")

print("\n=== 1) SKOR KOVASI -> GERCEK ISABET (kalibrasyon: 'skor X = %Y') ===")
print(f"{'skor araligi':>14}{'n':>6}{'>=5% isabet':>13}{'>=10% isabet':>14}{'guven notu':>14}")
edges = [0, 20, 35, 50, 65, 80, 101]
for i in range(len(edges) - 1):
    lo, hi = edges[i], edges[i + 1]
    sub = [r for r in rows if lo <= r["_s"] < hi]
    if len(sub) < 15:
        print(f"{f'{lo}-{hi if hi<101 else 100}':>14}{len(sub):>6}  (yetersiz)")
        continue
    p5 = P(sub, "y5") * 100
    note = "yuksek" if p5 >= 55 else "orta" if p5 >= 40 else "dusuk"
    print(
        f"{f'{lo}-{hi if hi<101 else 100}':>14}{len(sub):>6}{p5:>12.1f}%{P(sub,'y10')*100:>13.1f}%{note:>14}"
    )
print(
    "  >>> Isabet skorla MONOTON artmali (kalibre). Bozulursa skor guvenilirligi dusmus demektir."
)

print("\n=== 2) KRITER MARJINAL KATKISI (tek basina lift, >=%5) ===")


def lift(name, cond, thr_desc=""):
    sub = [r for r in rows if cond(r)]
    if len(sub) < 30:
        print(f"  {name:22s} n={len(sub)} (yetersiz)")
        return
    print(
        f"  {name:22s} n={len(sub):>5} isabet {P(sub,'y5')*100:5.1f}%  lift {P(sub,'y5')/b5:.2f}  (>=10% {P(sub,'y10')*100:.0f}%)"
    )


lift("short>=20%", lambda r: sh(r) >= 20)
lift("short>=15%", lambda r: sh(r) >= 15)
lift("ATR>=6", lambda r: atr(r) >= 6)
lift("ATR>=4", lambda r: atr(r) >= 4)
lift("gap>=3%", lambda r: gap(r) >= 3)
lift("RVOL>=3", lambda r: rvol(r) >= 3)
lift("RVOL>=2", lambda r: rvol(r) >= 2)
lift("52w-yakin>0.9 (NEG)", lambda r: d52(r) > 0.9)

print("\n=== 3) TIER -> GERCEK ISABET (canli etiket dogrulugu) ===")


def nfac(r):
    return sum([sh(r) >= 15, atr(r) >= 4, gap(r) >= 1, rvol(r) >= 1.5])


def tier(r):
    if sh(r) >= 15 and gap(r) >= 3:
        return "A"
    if (sh(r) >= 15 and atr(r) >= 4) or nfac(r) >= 3:
        return "B"
    if nfac(r) >= 2:
        return "C"
    return ""


_LABEL = {"A": "A (elite)", "B": "B (guclu)", "C": "C (orta)"}
_TARGET = {"A": 73, "B": 63, "C": 56}  # kodda kullanilan conviction_prob (%)
for t in ["A", "B", "C"]:
    sub = [r for r in rows if tier(r) == t]
    if len(sub) >= 15:
        real = P(sub, "y5") * 100
        print(
            f"  Tier {_LABEL[t]:12s} n={len(sub):>5} GERCEK isabet {real:5.1f}%  (kodda varsayilan %{_TARGET[t]})  fark {real-_TARGET[t]:+.0f}p"
        )
print("  >>> Gercek isabet, koddaki conviction_prob'a yakinsa etiketler dogru kalibre.")
print("\nBu monitoru veri buyudukce periyodik koş. Bu ciktinin TAMAMINI Claude'a yapistir.")
