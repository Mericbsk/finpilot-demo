#!/usr/bin/env python3
"""
ESKI vs V2 SCANNER — KAFA KAFAYA SECIM VERIMLILIGI
==================================================
"Az ama secici + kaliteli" ana temasini test eder: ayni full-universe evreninde
iki secim mantigini esit gunluk butcede yaristirir.
  ESKI: entry_ok (score==3 kapisi) + eski composite_score ile sirala
  V2  : siki kapi (ATR/gap/RVOL, dusuk-vol ele) + V2 composite ile sirala
Metrik: sinyal/gun, precision >=%5/%10, recall, ort/medyan getiri (maliyet %0.55 notu).
Kaynak: data/backtest_out/full_universe_enriched.csv (senin uretimin).
Kullanim:  python scanner_ab_test.py   -> ciktinin TAMAMINI yapistir.
"""

import csv
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
CSVP = os.path.join(ROOT, "data", "backtest_out", "full_universe_enriched.csv")
COST = 0.55


def ff(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


rows = []
for r in csv.DictReader(open(CSVP)):
    y = ff(r.get("resolved_pct_t5"))
    if y is None:
        continue
    rows.append(
        {
            "day": (r.get("scan_date") or r.get("scan_ts", "") or "")[:10],
            "y5": 1 if y >= 5 else 0,
            "y10": 1 if y >= 10 else 0,
            "ret": y,
            "atr": ff(r.get("atr_pct_real")) or ff(r.get("atr")) or 0,
            "gap": ff(r.get("gap_pct")) if ff(r.get("gap_pct")) is not None else -9,
            "rvol": ff(r.get("rvol")) or 0,
            "sq": ff(r.get("squeeze_factor")) or 0,
            "d52": ff(r.get("dist_52w_high")) or 0,
            "oldc": ff(r.get("composite_score")) or 0,
            "entry_ok": str(r.get("entry_ok")).strip().lower() == "true",
        }
    )
N = len(rows)
ndays = len({r["day"] for r in rows if r["day"]})


def P(sub, k):
    return sum(r[k] for r in sub) / len(sub) if sub else 0


def med(sub):
    xs = sorted(r["ret"] for r in sub)
    return xs[len(xs) // 2] if xs else 0


b5 = P(rows, "y5")
b10 = P(rows, "y10")
tot5 = sum(r["y5"] for r in rows)
print(
    f"n={N} gun={ndays} (~{N / ndays:.0f}/gun)  baz >=5% {b5 * 100:.1f}% >=10% {b10 * 100:.1f}%  (maliyet %{COST} round-trip)"
)


# --- V2 secim mantigi ---
def v2_gate(r):
    return (r["atr"] >= 4 or r["gap"] >= 3 or r["rvol"] >= 2) and r["atr"] >= 2  # dusuk-vol ele


def v2_comp(r):
    return (
        3 * min(r["atr"] / 6, 1)
        + 3 * min(max(r["gap"], 0) / 5, 1)
        + 2 * min(max(r["rvol"] - 1, 0) / 2, 1)
        + 3 * max(0, min(1, r["sq"]))
        - 1.5 * min(max(r["d52"] - 0.9, 0) / 0.1, 1)
    )


for r in rows:
    r["_v2c"] = v2_comp(r)

byday = defaultdict(list)
for r in rows:
    byday[r["day"]].append(r)


def eval_sel(name, pool_fn, rank_key):
    """pool_fn(r)->bool aday mi; rank_key(r) siralama. Tum + top-N tabloları."""
    pool = [r for r in rows if pool_fn(r)]
    print(f"\n### {name} ###")
    print(
        f"  TUM aday: n={len(pool):>6} ~{len(pool) / ndays:5.1f}/gun  >=5% {P(pool, 'y5') * 100:5.1f}% (lift {P(pool, 'y5') / b5:.2f})  >=10% {P(pool, 'y10') * 100:5.1f}%  medyan getiri {med(pool):+.1f}% (net ~{med(pool) - COST:+.1f}%)"
    )
    print(
        f"  {'N/gun':>6}{'gercek/gun':>11}{'>=5%':>8}{'lift':>6}{'>=10%':>8}{'recall5':>9}{'medRet':>8}"
    )
    for nn in [3, 5, 10, 20]:
        picks = []
        for _day, rs in byday.items():
            cand = [r for r in rs if pool_fn(r)]
            picks += sorted(cand, key=rank_key, reverse=True)[:nn]
        if not picks:
            continue
        rec = sum(r["y5"] for r in picks) / tot5 if tot5 else 0
        print(
            f"  {nn:>6}{len(picks) / ndays:>11.1f}{P(picks, 'y5') * 100:>7.1f}%{P(picks, 'y5') / b5:>6.2f}{P(picks, 'y10') * 100:>7.1f}%{rec * 100:>8.1f}%{med(picks):>7.1f}%"
        )


# ESKI: entry_ok kapisi, eski composite ile sirala
eval_sel("ESKI (entry_ok + eski composite sirali)", lambda r: r["entry_ok"], lambda r: r["oldc"])
# ESKI-2: sadece eski composite ile sirala (kapisiz)
eval_sel("ESKI-2 (kapisiz, eski composite sirali)", lambda r: True, lambda r: r["oldc"])
# V2: siki kapi + V2 composite sirali
eval_sel("V2 (siki kapi + V2 composite sirali)", v2_gate, lambda r: r["_v2c"])

print(
    "\n>>> KARAR: ayni N/gun'de en yuksek >=5%/>=10% precision + makul recall veren versiyon kazanir."
)
print(">>> 'Az ama kaliteli' = V2 daha az aday uretip ayni butcede daha yuksek isabet vermeli.")
print("Bu ciktinin TAMAMINI Claude'a yapistir.")
