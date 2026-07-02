#!/usr/bin/env python3
"""
SINYAL KALITESI LABI — az ama dogru sinyal (precision maksimizasyonu)
=====================================================================
Amac: sinyal sayisini AZALTIP isabet oranini (precision) YUKSELTMEK.
enriched_signals_v3.csv (yoksa v2) uzerinde 7 test.

Kompozit skor (canliya gonderdigimiz ALPHA_V2 mantigi):
  NEW = 4*short_n + 3*atr_n + 3*gap_n + 2*rvol_n - 1.5*ext_n
  (short icin varsa NOKTA-ZAMANLI short_pit)

Kullanim:  python signal_quality_lab.py     -> ciktinin TAMAMINI yapistir.
"""

import csv
import itertools
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
bd = os.path.join(ROOT, "data", "backtest_out")
CSVP = os.path.join(bd, "enriched_signals_v3.csv")
if not os.path.exists(CSVP):
    CSVP = os.path.join(bd, "enriched_signals_v2.csv")


def ff(x):
    try:
        return float(x)
    except:
        return None


rows = [r for r in csv.DictReader(open(CSVP)) if ff(r.get("resolved_pct_t5")) is not None]


def short_of(r):
    s = r.get("short_pit")
    s = ff(s) if s not in (None, "") else ff(r.get("short_pct"))
    return s if s is not None else 0.0


def comp(r):
    short = short_of(r)
    atr = ff(r.get("atr_pct")) or 0
    gap = ff(r.get("gap_pct")) or 0
    rvol = ff(r.get("rvol")) or 1
    d52 = ff(r.get("dist_52w_high")) or 0
    return (
        4 * min(short / 20, 1)
        + 3 * min(atr / 6, 1)
        + 3 * min(max(gap, 0) / 5, 1)
        + 2 * min(max(rvol - 1, 0) / 2, 1)
        - 1.5 * min(max(d52 - 0.9, 0) / 0.1, 1)
    )


for r in rows:
    r["_c"] = comp(r)
    r["_d"] = r["signal_date"][:10]
    r["y5"] = 1 if ff(r["resolved_pct_t5"]) >= 5 else 0
    r["y10"] = 1 if ff(r["resolved_pct_t5"]) >= 10 else 0
N = len(rows)
ndays = len({r["_d"] for r in rows})
b5 = sum(r["y5"] for r in rows) / N
b10 = sum(r["y10"] for r in rows) / N
print(f"Kaynak {os.path.basename(CSVP)}  n={N}  gun={ndays}  (~{N/ndays:.0f} sinyal/gun)")
print(f"Baz oran: >=5% {b5*100:.1f}%  >=10% {b10*100:.1f}%")


def prec(sub, k="y5"):
    return sum(r[k] for r in sub) / len(sub) if sub else 0


# ---- A) SECICILIK EGRISI ----
print("\n=== A) SECICILIK EGRISI (kompozite gore en iyi %) ===")
print(
    f"{'dilim':>8}{'n':>6}{'sinyal/gun':>11}{'>=5%prec':>10}{'lift':>6}{'>=10%prec':>11}{'lift':>6}"
)
sc = sorted(r["_c"] for r in rows)
for q in [0.50, 0.30, 0.20, 0.10, 0.05, 0.02]:
    cut = sc[int(N * (1 - q))]
    top = [r for r in rows if r["_c"] >= cut]
    print(
        f"{'top'+str(int(q*100))+'%':>8}{len(top):>6}{len(top)/ndays:>11.1f}{prec(top,'y5')*100:>10.1f}{prec(top,'y5')/b5:>6.2f}{prec(top,'y10')*100:>11.1f}{prec(top,'y10')/b10:>6.2f}"
    )

# ---- B) KONVIKSIYON KATMANLARI (AND) ----
print("\n=== B) KONVIKSIYON KATMANLARI (her katman precision'i yukseltmeli) ===")


def f_atr(r, t=4):
    return (ff(r.get("atr_pct")) or 0) >= t


def f_short(r, t=15):
    return short_of(r) >= t


def f_gap(r, t=3):
    return (ff(r.get("gap_pct")) or -9) >= t


def f_rvol(r, t=2):
    return (ff(r.get("rvol")) or 0) >= t


layers = [
    ("ATR>=4", f_atr),
    ("+ short>=15", f_short),
    ("+ gap>=1", lambda r: (ff(r.get("gap_pct")) or -9) >= 1),
    ("+ RVOL>=1.5", lambda r: (ff(r.get("rvol")) or 0) >= 1.5),
]
cur = rows
active = []
for name, fn in layers:
    active.append(fn)
    cur = [r for r in rows if all(f(r) for f in active)]
    if len(cur) < 15:
        print(f"  {name:16s} n={len(cur)} (yetersiz)")
        continue
    print(
        f"  {name:16s} n={len(cur):>5} >=5%prec {prec(cur,'y5')*100:5.1f}% (lift {prec(cur,'y5')/b5:.2f})  >=10%prec {prec(cur,'y10')*100:5.1f}%"
    )

# ---- C) EN YUKSEK PRECISION KOVA (n>=40) ----
print("\n=== C) EN YUKSEK PRECISION KOMBINASYONLAR (n>=40) ===")
F = {
    "short>=20": lambda r: short_of(r) >= 20,
    "short>=15": lambda r: short_of(r) >= 15,
    "ATR>=6": lambda r: (ff(r.get("atr_pct")) or 0) >= 6,
    "ATR>=4": lambda r: (ff(r.get("atr_pct")) or 0) >= 4,
    "gap>=3": lambda r: (ff(r.get("gap_pct")) or -9) >= 3,
    "RVOL>=3": lambda r: (ff(r.get("rvol")) or 0) >= 3,
    "RVOL>=2": lambda r: (ff(r.get("rvol")) or 0) >= 2,
}
res = []
for k in range(1, 4):
    for combo in itertools.combinations(F, k):
        sub = [r for r in rows if all(F[c](r) for c in combo)]
        if len(sub) >= 40:
            res.append((prec(sub, "y5"), prec(sub, "y10"), len(sub), " + ".join(combo)))
res.sort(reverse=True)
print(f"{'>=5%':>7}{'>=10%':>7}{'n':>5}  kombinasyon")
for p5, p10, n, c in res[:12]:
    print(f"{p5*100:>6.1f}%{p10*100:>6.1f}%{n:>5}  {c}")

# ---- D) GUNLUK BUTCE ----
print("\n=== D) GUNLUK SINYAL BUTCESI (siki gate: ATR>=4 & short>=15) ===")
gate = lambda r: f_atr(r) and f_short(r)
byday = {}
for r in rows:
    if gate(r):
        byday.setdefault(r["_d"], []).append(r)
cnts = sorted(len(v) for v in byday.values())
if cnts:
    import statistics as st

    print(
        f"  sinyal ureten gun: {len(byday)}/{ndays}  medyan {st.median(cnts):.0f}/gun  max {max(cnts)}/gun"
    )
    print(
        f"  gunlerin %{sum(1 for c in cnts if c<=5)/len(cnts)*100:.0f}'inde <=5 sinyal (top-5/gun uygulanabilir)"
    )

# ---- E) KALIBRASYON (decile) ----
print("\n=== E) KALIBRASYON: kompozit decile -> gercek >=%5 orani ===")
srt = sorted(rows, key=lambda r: r["_c"])
for i in range(10):
    seg = srt[int(N * i / 10) : int(N * (i + 1) / 10)]
    print(
        f"  decile {i+1:>2} (skor {seg[0]['_c']:.1f}-{seg[-1]['_c']:.1f}): >=5% {prec(seg,'y5')*100:5.1f}%  >=10% {prec(seg,'y10')*100:5.1f}%"
    )

# ---- F) TOP-N/GUN SIMULASYONU ----
print("\n=== F) TOP-N/GUN (her gun en iyi N'i al) ===")
byd = {}
for r in rows:
    byd.setdefault(r["_d"], []).append(r)
for Ntop in [1, 2, 3, 5]:
    picks = []
    for d, rs in byd.items():
        picks += sorted(rs, key=lambda r: -r["_c"])[:Ntop]
    print(
        f"  top-{Ntop}/gun: n={len(picks)} (~{Ntop}/gun)  >=5%prec {prec(picks,'y5')*100:5.1f}% (lift {prec(picks,'y5')/b5:.2f})  >=10%prec {prec(picks,'y10')*100:5.1f}%"
    )

# ---- G) TIER A/B/C (kac dogrulanmis sinyal hizali) ----
print("\n=== G) KONVIKSIYON TIER (kac guclu faktor VAR: short>=15, ATR>=4, gap>=1, RVOL>=1.5) ===")


def nfac(r):
    return sum(
        [
            short_of(r) >= 15,
            (ff(r.get("atr_pct")) or 0) >= 4,
            (ff(r.get("gap_pct")) or -9) >= 1,
            (ff(r.get("rvol")) or 0) >= 1.5,
        ]
    )


for k in [1, 2, 3, 4]:
    sub = [r for r in rows if nfac(r) >= k]
    if len(sub) >= 20:
        print(
            f"  >={k} faktor: n={len(sub):>5} (~{len(sub)/ndays:.1f}/gun) >=5%prec {prec(sub,'y5')*100:5.1f}% (lift {prec(sub,'y5')/b5:.2f})  >=10%prec {prec(sub,'y10')*100:5.1f}%"
        )
print("\nBu ciktinin TAMAMINI Claude'a yapistir — kapsamli raporu ondan uretecegim.")
