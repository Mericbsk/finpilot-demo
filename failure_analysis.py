#!/usr/bin/env python3
"""
KACIRAN (FAILURE) ANALIZI — Tier A/B icindeki basarisiz sinyaller
=================================================================
Yuksek-konviksiyon kapida (short>=15 & ATR>=4) KAZANAN (>=%5) vs KAYBEDEN
sinyalleri kiyaslar ve precision'i artiracak bir 'diskalifiye edici' filtre arar.
Yeni veri GEREKMEZ. enriched_signals_v3.csv.

Kullanim:  python failure_analysis.py   -> ciktinin TAMAMINI yapistir.
"""

import csv
import os
import statistics as st

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


def g(r, k, d=0.0):
    v = ff(r.get(k))
    return v if v is not None else d


for r in rows:
    r["y5"] = 1 if ff(r["resolved_pct_t5"]) >= 5 else 0

base = [r for r in rows if sh(r) >= 15 and g(r, "atr_pct") >= 4]
W = [r for r in base if r["y5"] == 1]
L = [r for r in base if r["y5"] == 0]
print(
    f"BASE kapi (short>=15 & ATR>=4): n={len(base)}  KAZANAN={len(W)}  KAYBEDEN={len(L)}  precision={len(W)/len(base)*100:.1f}%"
)


# ---- kazanan vs kaybeden ozellik dagilimi ----
def med(sub, fn):
    xs = [fn(r) for r in sub if fn(r) is not None]
    return st.median(xs) if xs else float("nan")


feats = {
    "short%": sh,
    "ATR%": lambda r: g(r, "atr_pct"),
    "gap%": lambda r: g(r, "gap_pct", -99) if g(r, "gap_pct", None) is not None else None,
    "RVOL": lambda r: g(r, "rvol"),
    "entry$": lambda r: g(r, "entry"),
    "float(M)": lambda r: (g(r, "float_shares") / 1e6 if g(r, "float_shares", None) else None),
    "dist52": lambda r: g(r, "dist_52w_high"),
    "resolved_1d%": lambda r: g(r, "resolved_pct_1d"),
}
print("\n=== KAZANAN vs KAYBEDEN (medyan) ===")
print(f"{'ozellik':14s}{'KAZANAN':>10}{'KAYBEDEN':>10}")
for name, fn in feats.items():
    print(f"{name:14s}{med(W,fn):>10.2f}{med(L,fn):>10.2f}")


# ---- diskalifiye edici arama: her aday filtre precision'i ne yapar ----
def prec(sub):
    return sum(r["y5"] for r in sub) / len(sub) if sub else 0


b0 = prec(base)
print(f"\n=== ADAY DISKALIFIYE EDICILER (base precision {b0*100:.1f}%) ===")
print(f"{'kural (hariç tut)':28s}{'kalan n':>8}{'yeni prec':>10}{'kaybeden_elenen%':>16}")


def scan(name, keep):
    kept = [r for r in base if keep(r)]
    removed = [r for r in base if not keep(r)]
    if len(kept) < 30 or not removed:
        print(f"{name:28s}{len(kept):>8}  (yetersiz/etkisiz)")
        return
    lrem = sum(1 for r in removed if r["y5"] == 0)
    eff = lrem / len(removed) * 100
    tag = " <== iyi" if prec(kept) > b0 + 0.02 and eff > b0 * 100 else ""
    print(f"{name:28s}{len(kept):>8}{prec(kept)*100:>10.1f}{eff:>15.0f}%{tag}")


scan("entry < $3 ele", lambda r: g(r, "entry") >= 3)
scan("entry < $5 ele", lambda r: g(r, "entry") >= 5)
scan("entry < $10 ele", lambda r: g(r, "entry") >= 10)
scan("entry > $100 ele", lambda r: g(r, "entry") <= 100)
scan("dist52 > 0.95 ele", lambda r: g(r, "dist_52w_high") <= 0.95)
scan("dist52 > 0.90 ele", lambda r: g(r, "dist_52w_high") <= 0.90)
scan("float < 5M ele", lambda r: (g(r, "float_shares", 1e12) >= 5e6))
scan("float > 500M ele", lambda r: (g(r, "float_shares", 0) <= 500e6))
scan("ATR% > 12 ele (asiri)", lambda r: g(r, "atr_pct") <= 12)
scan("ATR% > 15 ele", lambda r: g(r, "atr_pct") <= 15)
scan("RVOL < 1 ele", lambda r: g(r, "rvol") >= 1)
scan("gap < 0 ele (gap-down)", lambda r: g(r, "gap_pct", 0) >= 0)
scan("short > 40 ele", lambda r: sh(r) <= 40)

# ---- elit grup (short+gap) icindeki kaciranlar ----
elite = [r for r in rows if sh(r) >= 15 and g(r, "gap_pct", -99) >= 3]
eL = [r for r in elite if r["y5"] == 0]
print(
    f"\n=== ELIT (short>=15 & gap>=3) n={len(elite)} precision {prec(elite)*100:.1f}%  kaciran={len(eL)} ==="
)
if eL:
    print(
        "  Kaciranlarin medyani: entry$",
        round(med(eL, lambda r: g(r, "entry")), 1),
        " dist52",
        round(med(eL, lambda r: g(r, "dist_52w_high")), 2),
        " ATR%",
        round(med(eL, lambda r: g(r, "atr_pct")), 1),
        " resolved_1d%",
        round(med(eL, lambda r: g(r, "resolved_pct_1d")), 1),
    )
print(
    "\n>>> 'yeni prec' base'den belirgin yuksek VE kaybeden_elenen% yuksekse o filtre gercek diskalifiye edicidir."
)
print("Bu ciktinin TAMAMINI Claude'a yapistir.")
