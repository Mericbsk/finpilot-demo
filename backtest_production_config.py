#!/usr/bin/env python3
"""
UCTAN-UCA URETIM-CONFIG BACKTEST + GUNLUK TAVAN TARAMASI
=======================================================
Canlidaki TAM kurali gun-gun tarihsel veride simule eder:
  1) Siki giris kapisi: ATR>=4 VEYA gap>=3 VEYA RVOL>=2
  2) Konviksiyon tier (A: short>=15&gap>=3 | B: short>=15&ATR>=4 ya da >=3 faktor | C: >=2 faktor)
  3) Gunluk tavan: Tier A hepsi + B/C skorca doldurma, top-N'e kadar
Cikti: N taramasi -> sinyal/gun + precision (>=5/>=10), tier kirilimini, IS/OOS.

enriched_signals_v3.csv (nokta-zamanli short) uzerinde. Kullanim: python backtest_production_config.py
"""

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


def atr(r):
    return ff(r.get("atr_pct")) or 0


def gap(r):
    return ff(r.get("gap_pct")) or -9


def rv(r):
    return ff(r.get("rvol")) or 0


def d52(r):
    return ff(r.get("dist_52w_high")) or 0


def comp(r):
    return (
        4 * min(sh(r) / 20, 1)
        + 3 * min(atr(r) / 6, 1)
        + 3 * min(max(gap(r), 0) / 5, 1)
        + 2 * min(max(rv(r) - 1, 0) / 2, 1)
        - 1.5 * min(max(d52(r) - 0.9, 0) / 0.1, 1)
    )


def tier(r):
    ss = sh(r) >= 15
    gs = gap(r) >= 3
    gp = gap(r) >= 1
    rp = rv(r) >= 1.5
    ap = atr(r) >= 4
    nf = sum([ss, ap, gp, rp])
    if ss and gs:
        return "A"
    if (ss and ap) or nf >= 3:
        return "B"
    if nf >= 2:
        return "C"
    return ""


def gate(r):
    return atr(r) >= 4 or gap(r) >= 3 or rv(r) >= 2


for r in rows:
    r["y5"] = 1 if ff(r["resolved_pct_t5"]) >= 5 else 0
    r["y10"] = 1 if ff(r["resolved_pct_t5"]) >= 10 else 0
    r["_d"] = r["signal_date"][:10]
    r["_c"] = comp(r)
    r["_t"] = tier(r)

N_all = len(rows)
ndays = len({r["_d"] for r in rows})
b5 = sum(r["y5"] for r in rows) / N_all
b10 = sum(r["y10"] for r in rows) / N_all
print(
    f"Toplam sinyal={N_all}  gun={ndays}  baz >=5% {b5*100:.1f}% >=10% {b10*100:.1f}%  (~{N_all/ndays:.0f} ham sinyal/gun)"
)

# giris kapisindan gecenler + tier atanmis
pool = [r for r in rows if gate(r) and r["_t"] in ("A", "B", "C")]
print(
    f"Siki kapi + tier havuzu: {len(pool)} ({len(pool)/N_all*100:.0f}%), ~{len(pool)/ndays:.1f}/gun"
)


def select_day(rs, N):
    A = sorted([r for r in rs if r["_t"] == "A"], key=lambda r: -r["_c"])
    B = sorted([r for r in rs if r["_t"] == "B"], key=lambda r: -r["_c"])
    C = sorted([r for r in rs if r["_t"] == "C"], key=lambda r: -r["_c"])
    out = list(A)
    for g in (B, C):
        for r in g:
            if len(out) >= N:
                break
            out.append(r)
    return out


byday = defaultdict(list)
for r in pool:
    byday[r["_d"]].append(r)


def P(sub, k):
    return sum(r[k] for r in sub) / len(sub) if sub else 0


def IS(sub):
    return [r for r in sub if r["_d"] < "2026-01-01"]


def OOS(sub):
    return [r for r in sub if r["_d"] >= "2026-01-01"]


print("\n=== GUNLUK TAVAN N TARAMASI (Tier A + B/C doldurma, skorca) ===")
print(f"{'N':>3}{'toplam':>8}{'/gun':>6}{'>=5%':>7}{'>=10%':>7}{'IS>=5%':>8}{'OOS>=5%':>9}")
for N in [1, 2, 3, 5, 8, 10, 15]:
    sel = []
    for _d, rs in byday.items():
        sel += select_day(rs, N)
    isP = P(IS(sel), "y5") * 100 if IS(sel) else 0
    oosP = P(OOS(sel), "y5") * 100 if OOS(sel) else 0
    print(
        f"{N:>3}{len(sel):>8}{len(sel)/ndays:>6.1f}{P(sel,'y5')*100:>7.1f}{P(sel,'y10')*100:>7.1f}{isP:>8.1f}{oosP:>9.1f}"
    )

print("\n=== TIER KIRILIMI (havuz geneli) ===")
for t in ["A", "B", "C"]:
    sub = [r for r in pool if r["_t"] == t]
    if sub:
        print(
            f"  Tier {t}: n={len(sub):>4} ~{len(sub)/ndays:.1f}/gun  >=5% {P(sub,'y5')*100:5.1f}%  >=10% {P(sub,'y10')*100:5.1f}%  (IS {P(IS(sub),'y5')*100:.0f}% / OOS {P(OOS(sub),'y5')*100:.0f}%)"
        )

print("\n=== KIYAS: sadece skorca top-N (tier'siz) vs tier'li ===")
for N in [3, 5]:
    seln, selt = [], []
    for _d, rs in byday.items():
        seln += sorted(rs, key=lambda r: -r["_c"])[:N]
        selt += select_day(rs, N)
    print(f"  N={N}: skor-top {P(seln,'y5')*100:.1f}%  |  tier-oncelikli {P(selt,'y5')*100:.1f}%")
print("\n>>> Karar: precision hedefine gore gunluk N sec. IS/OOS yakinsa config dayanikli.")
print("Bu ciktinin TAMAMINI Claude'a yapistir.")
