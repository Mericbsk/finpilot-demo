#!/usr/bin/env python3
"""
ONCESI / SONRASI SKOR KARSILASTIRMASI
=====================================
ESKI FinPilot skoru (arsivdeki 'score' kolonu) ile YENI ALPHA_V2 kompozitini
(short + ATR + gap + RVOL - extension) ayni sinyaller uzerinde kiyaslar.
Metrik: en iyi %20 sinyalin gercek >=%5 / >=%10 yakalama lift'i, IS(2025)/OOS(2026).

Yeni kompozit, canliya gonderdigimiz ALPHA_V2 mantigini yansitir:
   NEW = 4*short_n + 3*atr_n + 3*gap_n + 2*rvol_n - 1.5*ext_n
short icin varsa NOKTA-ZAMANLI (short_pit) kullanilir (look-ahead'siz).

Kullanim:  python score_compare.py
Ciktiyi Claude'a yapistir.
"""

import csv
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(ROOT, "data", "backtest_out")
CSVP = os.path.join(base_dir, "enriched_signals_v3.csv")
if not os.path.exists(CSVP):
    CSVP = os.path.join(base_dir, "enriched_signals_v2.csv")


def ff(x):
    try:
        return float(x)
    except:
        return None


rows = [r for r in csv.DictReader(open(CSVP)) if ff(r.get("resolved_pct_t5")) is not None]
print(f"Kaynak: {os.path.basename(CSVP)}  n={len(rows)}")


def new_score(r):
    short = r.get("short_pit")
    short = ff(short) if short not in (None, "") else ff(r.get("short_pct"))
    short = short if short is not None else 0.0
    atr = ff(r.get("atr_pct")) or 0.0
    gap = ff(r.get("gap_pct")) or 0.0
    rvol = ff(r.get("rvol")) or 1.0
    fl = ff(r.get("float_shares"))
    d52 = ff(r.get("dist_52w_high")) or 0.0
    short_n = min(short / 20.0, 1.0)
    atr_n = min(atr / 6.0, 1.0)
    gap_n = min(max(gap, 0) / 5.0, 1.0)
    rvol_n = min(max(rvol - 1, 0) / 2.0, 1.0)
    ext_n = min(max(d52 - 0.9, 0) / 0.1, 1.0)
    return 4 * short_n + 3 * atr_n + 3 * gap_n + 2 * rvol_n - 1.5 * ext_n


for r in rows:
    r["_new"] = new_score(r)
    r["_old"] = ff(r.get("score")) or 0.0


def y(r, thr):
    return 1 if ff(r["resolved_pct_t5"]) >= thr else 0


def quantile(vals, q):
    s = sorted(vals)
    return s[min(len(s) - 1, int(len(s) * q))]


def eval_top(sub, key, thr, topq=0.80):
    if len(sub) < 40:
        return None
    base = sum(y(r, thr) for r in sub) / len(sub)
    cut = quantile([r[key] for r in sub], topq)
    top = [r for r in sub if r[key] >= cut]
    if not top:
        return None
    hit = sum(y(r, thr) for r in top) / len(top)
    return dict(n=len(top), hit=hit, lift=(hit / base if base else 0), base=base)


def block(title, sub):
    print(f"\n=== {title} (n={len(sub)}) ===")
    for thr in (5, 10):
        o = eval_top(sub, "_old", thr)
        n = eval_top(sub, "_new", thr)
        if not o or not n:
            print(f"  >={thr}%: yetersiz")
            continue
        print(f"  >={thr}% hareket (baz %{o['base']*100:.1f}):")
        print(f"     ESKI score  top-%20: hit {o['hit']*100:5.1f}%  lift {o['lift']:.2f}")
        print(
            f"     YENI ALPHA2 top-%20: hit {n['hit']*100:5.1f}%  lift {n['lift']:.2f}   -> {'+' if n['lift']>o['lift'] else ''}{(n['lift']-o['lift']):.2f}"
        )


block("TUM DONEM", rows)
block("IS 2025", [r for r in rows if r["signal_date"][:10] < "2026-01-01"])
block("OOS 2026", [r for r in rows if r["signal_date"][:10] >= "2026-01-01"])

# ek: tam-sistem 'AL' esigi kiyasi (en iyi %10)
print("\n=== En iyi %10 (daha secici) — TUM DONEM ===")
for thr in (5, 10):
    o = eval_top(rows, "_old", thr, 0.90)
    n = eval_top(rows, "_new", thr, 0.90)
    if o and n:
        print(
            f"  >={thr}%: ESKI lift {o['lift']:.2f} (n{o['n']})  |  YENI lift {n['lift']:.2f} (n{n['n']})"
        )
print("\n>>> YENI lift ESKI'den yuksekse reweight ise yariyor. Sonra ince ayara gecebiliriz.")
print("Bu ciktinin TAMAMINI Claude'a yapistir.")
