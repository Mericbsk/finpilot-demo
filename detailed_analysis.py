#!/usr/bin/env python3
"""
DETAYLI ANALIZ — etkilesim gridi + bootstrap GA + ince esik gridi
=================================================================
enriched_signals_v3.csv. Yeni veri gerekmez.
Kullanim:  python detailed_analysis.py   -> ciktinin TAMAMINI yapistir.
"""

import csv
import itertools
import os
import random

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


for r in rows:
    r["y5"] = 1 if ff(r["resolved_pct_t5"]) >= 5 else 0
    r["y10"] = 1 if ff(r["resolved_pct_t5"]) >= 10 else 0
    r["_d"] = r["signal_date"][:10]
N = len(rows)
base = sum(r["y5"] for r in rows) / N


def P(sub):
    return sum(r["y5"] for r in sub) / len(sub) if sub else 0


def P10(sub):
    return sum(r["y10"] for r in sub) / len(sub) if sub else 0


print(f"n={N} baz >=5% {base*100:.1f}%")

F = {
    "short>=15": lambda r: sh(r) >= 15,
    "short>=20": lambda r: sh(r) >= 20,
    "ATR>=4": lambda r: atr(r) >= 4,
    "ATR>=6": lambda r: atr(r) >= 6,
    "gap>=3": lambda r: gap(r) >= 3,
    "RVOL>=2": lambda r: rvol(r) >= 2,
    "RVOL>=3": lambda r: rvol(r) >= 3,
}

# === 1) ETKILESIM GRIDI: 2'li/3'lu; super-additive mi? ===
print("\n=== 1) ETKILESIM GRIDI (n>=30, precision'a gore; SA=super-additive) ===")


def sub_of(keys):
    return [r for r in rows if all(F[k](r) for k in keys)]


res = []
for k in range(2, 4):
    for combo in itertools.combinations(F, k):
        s = sub_of(combo)
        if len(s) < 30:
            continue
        # super-additive testi: kombo lift'i, en iyi tekil bileseninin lift'inden belirgin yuksek mi
        singles = [P(sub_of((c,))) / base for c in combo]
        combo_lift = P(s) / base
        sa = combo_lift - max(singles)
        res.append((P(s), P10(s), len(s), combo_lift, sa, " + ".join(combo)))
res.sort(reverse=True)
print(f"{'>=5%':>7}{'>=10%':>7}{'n':>5}{'lift':>6}{'SA':>7}  kombinasyon")
for p5, p10, n, lift, sa, c in res[:12]:
    flag = " ⭐SA" if sa > 0.25 else ""
    print(f"{p5*100:>6.1f}%{p10*100:>6.1f}%{n:>5}{lift:>6.2f}{sa:>+7.2f}  {c}{flag}")
print(
    "  ⭐SA = kombo, en iyi tekil bileseninden >0.25 lift fazla -> gercek etkilesim (short+gap gibi)"
)

# === 2) BOOTSTRAP GUVEN ARALIGI (Tier + top kombolar) ===
print("\n=== 2) BOOTSTRAP %90 GUVEN ARALIGI (>=%5 isabet) ===")


def nfac(r):
    return sum([sh(r) >= 15, atr(r) >= 4, gap(r) >= 1, rvol(r) >= 1.5])


def tier(r):
    if sh(r) >= 15 and gap(r) >= 3:
        return "A"
    if (sh(r) >= 15 and atr(r) >= 4) or nfac(r) >= 3:
        return "B"
    if nfac(r) >= 2:
        return "C"
    return "-"


random.seed(42)


def boot_ci(sub, B=2000):
    if len(sub) < 20:
        return None
    ys = [r["y5"] for r in sub]
    n = len(ys)
    ps = []
    for _ in range(B):
        ps.append(sum(ys[random.randrange(n)] for _ in range(n)) / n)
    ps.sort()
    return ps[int(B * 0.05)] * 100, ps[int(B * 0.95)] * 100


for name, sub in [
    ("Tier A", [r for r in rows if tier(r) == "A"]),
    ("Tier B", [r for r in rows if tier(r) == "B"]),
    ("Tier C", [r for r in rows if tier(r) == "C"]),
    ("short>=20 & ATR>=4", [r for r in rows if sh(r) >= 20 and atr(r) >= 4]),
    ("short>=15 & gap>=3", [r for r in rows if sh(r) >= 15 and gap(r) >= 3]),
]:
    ci = boot_ci(sub)
    if ci:
        print(
            f"  {name:22s} n={len(sub):>4} isabet {P(sub)*100:5.1f}%  GA[%{ci[0]:.0f} – %{ci[1]:.0f}]  genislik {ci[1]-ci[0]:.0f}p"
        )
print("  >>> Dar GA (<15p) -> guvenilir; genis GA (>25p) -> kucuk-n, 'kesin' sunma.")

# === 3) INCE ESIK GRIDI (IS/OOS) ===
print("\n=== 3) INCE ESIK GRIDI (>=%5, IS 2025 / OOS 2026) ===")
IS = [r for r in rows if r["_d"] < "2026-01-01"]
OOS = [r for r in rows if r["_d"] >= "2026-01-01"]


def seg(fn):
    si = [r for r in IS if fn(r)]
    so = [r for r in OOS if fn(r)]
    pi = P(si) * 100 if len(si) >= 20 else None
    po = P(so) * 100 if len(so) >= 20 else None
    return len(si), pi, len(so), po


for name, thrs, fn in [
    ("short", [12, 15, 18, 20, 25], lambda t: (lambda r: sh(r) >= t)),
    ("ATR", [3, 4, 5, 6, 8], lambda t: (lambda r: atr(r) >= t)),
    ("gap", [1, 2, 3, 5], lambda t: (lambda r: gap(r) >= t)),
]:
    print(f"  [{name}] esik -> IS isabet / OOS isabet (n)")
    for t in thrs:
        ni, pi, no, po = seg(fn(t))

        def ps(x):
            return f"{x:.0f}%" if x is not None else "-"

        print(f"    >={t:<3} IS {ps(pi):>4}(n{ni:>4}) | OOS {ps(po):>4}(n{no:>4})")
print(
    "  >>> Hem IS hem OOS'ta en yuksek + n yeterli olan esik = optimal (ikisinde birden tutmali)."
)
print("\nBu ciktinin TAMAMINI Claude'a yapistir.")
