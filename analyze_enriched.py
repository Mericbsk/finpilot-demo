#!/usr/bin/env python3
"""
enriched_signals.csv'yi (yeni ozelliklerle) analiz eder ve TUMUNU metin olarak basar.
Ciktiyi komple kopyalayip Claude'a yapistir. (Sadece stdlib; numpy gerekmez.)
Kullanim:  python analyze_enriched.py
"""

import csv
import math
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
CSVP = os.path.join(ROOT, "data", "backtest_out", "enriched_signals.csv")
IS_END = "2026-01-01"
MINN = 30


def f(x):
    try:
        return float(x)
    except:
        return None


rows = []
with open(CSVP) as fh:
    for r in csv.DictReader(fh):
        rows.append(r)
print("CSV satir (veri):", len(rows), " dosya:", CSVP)


def gf(r, k):
    return f(r.get(k, ""))


# hedef
def yv(r):
    v = gf(r, "resolved_pct_t5")
    return None if v is None else (1 if v >= 5 else 0)


valid = [r for r in rows if yv(r) is not None]
N = len(valid)
ybase = sum(yv(r) for r in valid) / N if N else float("nan")
print(f"Cozulmus (resolved_pct_t5 var): {N}")
print(f"BAZ ORAN (T+5 maks >=5%): {ybase*100:.1f}%")


# ek baz oranlar
def rate(fn):
    xs = [r for r in valid if fn(r) is not None]
    return (sum(fn(r) for r in xs) / len(xs)) if xs else None


y10 = rate(lambda r: (1 if (gf(r, "resolved_pct_t5") or -99) >= 10 else 0))
print(f"BAZ ORAN >=10%: {y10*100:.1f}%")


def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def ztest(sa, na, sb, nb):
    if na == 0 or nb == 0:
        return None
    p1, p2 = sa / na, sb / nb
    pp = (sa + sb) / (na + nb)
    se = (pp * (1 - pp) * (1 / na + 1 / nb)) ** 0.5
    return 1.0 if se == 0 else 2 * (1 - ncdf(abs((p1 - p2) / se)))


def metric(name, fn, recs=None, base=None):
    recs = recs or valid
    base = ybase if base is None else base
    sub = [r for r in recs if fn(r)]
    if len(sub) < MINN:
        return None
    h = sum(yv(r) for r in sub) / len(sub)
    ctrl = [r for r in recs if not fn(r)]
    p = (
        ztest(sum(yv(r) for r in sub), len(sub), sum(yv(r) for r in ctrl), len(ctrl))
        if ctrl
        else None
    )
    return dict(name=name, n=len(sub), hit=h, lift=h / base if base else None, p=p)


def show(title, items):
    print(f"\n=== {title} ===")
    print(f"{'sinyal':30s}{'n':>6}{'hit%':>7}{'lift':>6}{'p':>9}")
    for m in items:
        if m:
            print(
                f"{m['name']:30s}{m['n']:>6}{m['hit']*100:>7.1f}{(m['lift'] or 0):>6.2f}{(m['p'] if m['p'] is not None else 0):>9.4f}"
            )


# ---- tekli sinyaller (YENI ozellikler dahil) ----
singles = [
    metric("score>=3", lambda r: (gf(r, "score") or -9) >= 3),
    metric("rr>=2.6", lambda r: (gf(r, "rr") or -9) >= 2.6),
    metric("rr>=3.0", lambda r: (gf(r, "rr") or -9) >= 3.0),
    metric(
        "regime=Range/0/False",
        lambda r: str(r.get("regime", "")).strip() in ("0", "False", "Range"),
    ),
    metric("RVOL>=1.5", lambda r: (gf(r, "rvol") or 0) >= 1.5),
    metric("RVOL>=2", lambda r: (gf(r, "rvol") or 0) >= 2),
    metric("RVOL>=3", lambda r: (gf(r, "rvol") or 0) >= 3),
    metric("RVOL>=5", lambda r: (gf(r, "rvol") or 0) >= 5),
    metric("gap>3%", lambda r: (gf(r, "gap_pct") or -99) > 3),
    metric("gap>5%", lambda r: (gf(r, "gap_pct") or -99) > 5),
    metric("ATR%>=3", lambda r: (gf(r, "atr_pct") or 0) >= 3),
    metric("ATR%>=4", lambda r: (gf(r, "atr_pct") or 0) >= 4),
    metric("ATR%>=6", lambda r: (gf(r, "atr_pct") or 0) >= 6),
    metric("52w-high yakin>0.9", lambda r: (gf(r, "dist_52w_high") or 0) > 0.9),
    metric("52w-high yakin>0.95", lambda r: (gf(r, "dist_52w_high") or 0) > 0.95),
    metric("short%>=10", lambda r: (gf(r, "short_pct") or -1) >= 10),
    metric("short%>=20", lambda r: (gf(r, "short_pct") or -1) >= 20),
]
show("TEK SINYAL (baz=%.1f%%)" % (ybase * 100), [m for m in singles if m])

# ---- ikili kombinasyonlar ----
F = {
    "RVOL>=2": lambda r: (gf(r, "rvol") or 0) >= 2,
    "RVOL>=3": lambda r: (gf(r, "rvol") or 0) >= 3,
    "gap>5%": lambda r: (gf(r, "gap_pct") or -99) > 5,
    "ATR%>=4": lambda r: (gf(r, "atr_pct") or 0) >= 4,
    "ATR%>=6": lambda r: (gf(r, "atr_pct") or 0) >= 6,
    "52w>0.9": lambda r: (gf(r, "dist_52w_high") or 0) > 0.9,
    "rr>=3": lambda r: (gf(r, "rr") or -9) >= 3.0,
    "score>=3": lambda r: (gf(r, "score") or -9) >= 3,
}
import itertools

combos = []
for a, b in itertools.combinations(F, 2):
    m = metric(f"{a} + {b}", lambda r, fa=F[a], fb=F[b]: fa(r) and fb(r))
    if m:
        combos.append(m)
combos.sort(key=lambda m: -(m["lift"] or 0))
show("EN IYI 12 IKILI KOMBINASYON", combos[:12])

# ---- walk-forward (IS<2026, OOS>=2026) ----
IS = [r for r in valid if (r.get("signal_date") or "") < IS_END]
OOS = [r for r in valid if (r.get("signal_date") or "") >= IS_END]
bIS = sum(yv(r) for r in IS) / len(IS) if IS else float("nan")
bOOS = sum(yv(r) for r in OOS) / len(OOS) if OOS else float("nan")
print(
    f"\n=== WALK-FORWARD (IS n={len(IS)} baz%{bIS*100:.1f} | OOS n={len(OOS)} baz%{bOOS*100:.1f}) ==="
)
print(f"{'sinyal':22s}{'IS lift':>8}{'OOS lift':>9}{'OOS p':>9}  karar")
for name, fn in [
    ("RVOL>=2", F["RVOL>=2"]),
    ("RVOL>=3", F["RVOL>=3"]),
    ("gap>5%", F["gap>5%"]),
    ("ATR%>=4", F["ATR%>=4"]),
    ("ATR%>=6", F["ATR%>=6"]),
    ("52w>0.9", F["52w>0.9"]),
    ("rr>=3", F["rr>=3"]),
    ("score>=3", F["score>=3"]),
]:
    mi = metric(name, fn, IS, bIS)
    mo = metric(name, fn, OOS, bOOS)
    if mi and mo:
        ok = mo["lift"] and mo["lift"] > 1.3 and mo["p"] is not None and mo["p"] < 0.05
        print(
            f"{name:22s}{mi['lift']:>8.2f}{mo['lift']:>9.2f}{(mo['p'] or 0):>9.4f}  {'DAYANDI' if ok else 'zayif'}"
        )
    else:
        print(f"{name:22s}{'-':>8}{'-':>9}{'-':>9}  yetersiz n")

# feature coverage (kac sinyalde dolu)
print("\n=== OZELLIK KAPSAMI (dolu kayit sayisi) ===")
for col in ["rvol", "gap_pct", "atr_pct", "dist_52w_high", "short_pct", "float_shares"]:
    c = sum(1 for r in valid if gf(r, col) is not None)
    print(f"  {col:16s} {c}/{N}")
