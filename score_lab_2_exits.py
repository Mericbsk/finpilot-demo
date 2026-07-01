#!/usr/bin/env python3
"""
ASAMA 2 — Cikis (TP/Stop) Optimizasyonu + Giris Kapisi (entry_ok) Testi
========================================================================
enriched_signals_v2.csv uzerinde calisir.
Veri siniri: elimizde T+5 MAKS lehte hareket (resolved_pct_t5=MFE) ve T+1 kapanis var;
tam intraday yol (MAE/stop-out) YOK. Bu yuzden:
  - TP tarafi TAM test edilir (MFE ile).
  - Stop tarafi SINIRLI (T+1 kapanis ile yaklasik); tam stop testi intraday veri gerektirir.

Testler:
  T4a  ATR-carpani TP erisim orani + beklenen yakalama (mevcut tp2 kalibre mi?)
  T4b  Sabit-% TP (5/10/15/20) erisim orani
  T4c  ATR vs sabit-% hangisi daha verimli
  T5   Giris kapisi: eski score==yuksek kapisi vs short/ATR/gap kapisi (precision + recall)

Kullanim:  python score_lab_2_exits.py   ->  ciktinin TAMAMINI yapistir.
"""

import csv
import os

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
CSVP = os.path.join(ROOT, "data", "backtest_out", "enriched_signals_v2.csv")


def ff(x):
    try:
        return float(x)
    except:
        return None


rows = list(csv.DictReader(open(CSVP)))


def g(r, k, d=None):
    v = ff(r.get(k))
    return v if v is not None else d


R = []
for r in rows:
    mfe = g(r, "resolved_pct_t5")
    atr = g(r, "atr_pct")
    if mfe is None:
        continue
    R.append(
        dict(
            mfe=mfe,
            r1=g(r, "resolved_pct_1d", 0.0),
            atr=atr,
            short=g(r, "short_pct", 0.0),
            gap=g(r, "gap_pct", 0.0),
            rvol=g(r, "rvol", 1.0),
            score=g(r, "score", 0.0),
            date=(r.get("signal_date") or ""),
        )
    )
N = len(R)
print(f"n={N}")
mfe = np.array([x["mfe"] for x in R])
print(
    f"MFE (T+5 maks lehte hareket %): medyan={np.median(mfe):.1f}  ort={mfe.mean():.1f}  "
    f">=5%:{(mfe>=5).mean()*100:.1f}%  >=10%:{(mfe>=10).mean()*100:.1f}%  >=20%:{(mfe>=20).mean()*100:.1f}%"
)

# ---- T4a: ATR-carpani TP ----
atr = np.array([x["atr"] if x["atr"] else np.nan for x in R])
ok = ~np.isnan(atr)
print("\n=== T4a: ATR-CARPANI TP (tp_dist = m x ATR%) ===")
print(f"{'m':>5}{'tp_dist medyan%':>16}{'erisim%':>10}{'E[yakalama]%':>14}")
for m in [3, 4, 5, 5.5, 6.5, 8]:
    tp_dist = m * atr[ok]
    reach = mfe[ok] >= tp_dist
    reach_rate = reach.mean()
    # beklenen yakalama ~ erisim orani x tp mesafesi (medyan)
    exp_cap = reach_rate * np.median(tp_dist)
    print(f"{m:>5.1f}{np.median(tp_dist):>16.1f}{reach_rate*100:>10.1f}{exp_cap:>14.1f}")
print("  (mevcut: Normal tp2=5.5xATR, Sniper=5x, Defansif=6.5x)")

# ---- T4b: sabit-% TP ----
print("\n=== T4b: SABIT-% TP ===")
print(f"{'seviye%':>8}{'erisim%':>10}{'E[yakalama]%':>14}")
for lv in [5, 8, 10, 15, 20]:
    reach = (mfe >= lv).mean()
    print(f"{lv:>8}{reach*100:>10.1f}{reach*lv:>14.1f}")

# ---- T4c: yorum otomatik ----
best_atr = max(
    [3, 4, 5, 5.5, 6.5, 8], key=lambda m: (mfe[ok] >= m * atr[ok]).mean() * np.median(m * atr[ok])
)
best_fix = max([5, 8, 10, 15, 20], key=lambda lv: (mfe >= lv).mean() * lv)
print(f"\n  En yuksek E[yakalama]: ATR-carpani ~{best_atr}x  |  sabit ~%{best_fix}")

# ---- T5: giris kapisi ----
print("\n=== T5: GIRIS KAPISI (entry_ok) TESTI ===")
base = (mfe >= 5).mean()


def gate(mask, name):
    n = mask.sum()
    if n < 30:
        print(f"  {name:34s} n={n} (yetersiz)")
        return
    hit = (mfe[mask] >= 5).mean()
    hit10 = (mfe[mask] >= 10).mean()
    recall = (mfe[mask] >= 5).sum() / (mfe >= 5).sum()
    print(
        f"  {name:34s} n={n:>5} hit>=5%={hit*100:>5.1f}% (lift {hit/base:.2f}) hit>=10%={hit10*100:>5.1f}% recall={recall*100:>4.1f}%"
    )


sc = np.array([x["score"] for x in R])
sh = np.array([x["short"] for x in R])
at = np.array([x["atr"] if x["atr"] else 0 for x in R])
gp = np.array([x["gap"] for x in R])
rv = np.array([x["rvol"] for x in R])
print(f"  baz (kapisiz): hit>=5%={base*100:.1f}%  toplam >=5% kazanan={int((mfe>=5).sum())}")
gate(sc >= np.quantile(sc, 0.66), "ESKI: yuksek score (ust %33)")
gate(sc >= np.quantile(sc, 0.9), "ESKI: cok yuksek score (ust %10)")
gate((sh >= 15) | (at >= 4) | (gp >= 3), "YENI kapi: short>=15 VEYA ATR>=4 VEYA gap>=3")
gate((sh >= 20) | (at >= 6), "YENI kapi (siki): short>=20 VEYA ATR>=6")
gate((at >= 4), "Sadece ATR>=4")

# walk-forward kontrol: yeni kapi 2026'da da iyi mi
print("\n  --- yeni kapinin donemsel tutarliligi (short>=15|ATR>=4|gap>=3) ---")
dates = np.array([x["date"] for x in R])
for lab, msk in [("IS 2025", dates < "2026-01-01"), ("OOS 2026", dates >= "2026-01-01")]:
    sub = msk
    b = (mfe[sub] >= 5).mean()
    gt = sub & ((sh >= 15) | (at >= 4) | (gp >= 3))
    if gt.sum() >= 30:
        print(
            f"    {lab}: kapi hit>=5%={(mfe[gt]>=5).mean()*100:.1f}%  baz={b*100:.1f}%  lift={(mfe[gt]>=5).mean()/b:.2f}"
        )
print("\nBu ciktinin TAMAMINI Claude'a yapistir.")
