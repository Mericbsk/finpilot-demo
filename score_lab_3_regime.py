#!/usr/bin/env python3
"""
ASAMA 3 — Rejim Kapisi Validasyonu + Rejim-Kosullu Edge
========================================================
enriched_signals_v2.csv uzerinde calisir.

Testler:
  T6a  Eski 'score' bantlari: gate'in "30-55 boost / >58 suppress" mantigi gercekle uyuyor mu?
  T6b  Yeni sinyaller (short>=20 / ATR>=6 / gap>=3) rejime gore degisiyor mu?
       - Donem: 2025 (IS) vs 2026 (OOS)  (kaba rejim vekili)
       - Sinyalin kendi regime alani: Trend vs Range
  Cikti: yeni skora rejim-farkinda agirlik gerekli mi?

Not: Gate'in orijinali 0-100 CANLI composite + SPY-EMA200 bull/bear kullanir; enriched 'score'
bu olmayabilir (dagilim basta yazdirilir) ve donem/regime kaba vekildir. Kesin gate ayari icin
sinyalleri score_engine ile yeniden skorlamak gerekir.

Kullanim:  python score_lab_3_regime.py   ->  ciktinin TAMAMINI yapistir.
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
    if mfe is None:
        continue
    R.append(
        dict(
            mfe=mfe,
            score=g(r, "score", 0.0),
            short=g(r, "short_pct", 0.0),
            atr=g(r, "atr_pct", 0.0),
            gap=g(r, "gap_pct", 0.0),
            regime=str(r.get("regime", "")).strip(),
            date=(r.get("signal_date") or ""),
        )
    )
N = len(R)
mfe = np.array([x["mfe"] for x in R])
sc = np.array([x["score"] for x in R])
base5 = (mfe >= 5).mean()
print(f"n={N}  baz(>=5%)={base5*100:.1f}%")
print(
    f"ESKI score dagilimi: min={sc.min():.0f} medyan={np.median(sc):.0f} "
    f"q75={np.percentile(sc,75):.0f} q90={np.percentile(sc,90):.0f} max={sc.max():.0f}"
)


def hit(mask):
    n = mask.sum()
    if n < 30:
        return None
    return n, (mfe[mask] >= 5).mean(), (mfe[mask] >= 5).mean() / base5


# ---- T6a: eski score bantlari (gate mantigi) ----
print("\n=== T6a: ESKI SCORE BANTLARI (gate: 30-55 boost, >58 suppress varsayimi) ===")
bands = [
    ("0-1", sc <= 1),
    ("2-3", (sc >= 2) & (sc <= 3)),
    ("4-10", (sc >= 4) & (sc <= 10)),
    ("11-30", (sc >= 11) & (sc <= 30)),
    (">30", sc > 30),
]
for name, m in bands:
    r = hit(m)
    if r:
        print(f"  score {name:8s} n={r[0]:>5} hit>=5%={r[1]*100:>5.1f}% lift={r[2]:.2f}")
print(
    "  >>> Gate 'yuksek skoru baskila' diyor; bantlarda lift artmiyor/monoton degilse gate hakli."
)

# ---- T6b: yeni sinyaller rejime gore ----
dates = np.array([x["date"] for x in R])
sh = np.array([x["short"] for x in R])
at = np.array([x["atr"] for x in R])
gp = np.array([x["gap"] for x in R])
reg = np.array([x["regime"] for x in R])
IS = dates < "2026-01-01"
OOS = ~IS
isRange = np.array([x["regime"] in ("0", "False", "Range") for x in R])
isTrend = np.array([x["regime"] in ("1", "True", "Trend") for x in R])


def cond(mask, label):
    for seg_name, seg in [
        ("TUMU", np.ones(N, bool)),
        ("2025(IS)", IS),
        ("2026(OOS)", OOS),
        ("Range", isRange),
        ("Trend", isTrend),
    ]:
        m = mask & seg
        n = m.sum()
        if n < 30:
            print(f"    {seg_name:10s} n={n:<5} (yetersiz)")
            continue
        b = (mfe[seg] >= 5).mean()
        h = (mfe[m] >= 5).mean()
        print(
            f"    {seg_name:10s} n={n:<5} hit={h*100:>5.1f}%  segbaz={b*100:>5.1f}%  lift={h/b:.2f}"
        )


print("\n=== T6b: YENI SINYALLER REJIME GORE (lift = segment-ici baz orana gore) ===")
print("  [short>=20%]")
cond(sh >= 20, "short>=20")
print("  [ATR>=6]")
cond(at >= 6, "ATR>=6")
print("  [gap>=3]")
cond(gp >= 3, "gap>=3")

print(
    "\n>>> Bir sinyalin lift'i bir rejimde belirgin dusukse, o rejimde agirligini azalt (rejim-farkinda)."
)
print("Bu ciktinin TAMAMINI Claude'a yapistir.")
