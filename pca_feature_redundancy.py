#!/usr/bin/env python3
"""
pca_feature_redundancy.py — Persona-1 Deney #9: gerçek bağımsız-eksen-sayısı.

full_universe_enriched.csv'deki sayısal skor/feature ailesi üzerinde PCA:
kümülatif varyans %90'a kaç bileşen gerekiyor? composite_score↔finpilot_score
0.98 korelasyonunun ötesinde sistematik redundancy var mı?
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

df = pd.read_csv("data/backtest_out/full_universe_enriched.csv", low_memory=False)

cols = [
    "score",
    "composite_score",
    "finpilot_score",
    "squeeze_factor",
    "lottery_factor",
    "overnight_gap_factor",
    "atr",
    "gap_pct",
    "rvol",
    "atr_pct_real",
    "dist_52w_high",
]  # catalyst_factor/tier_score/sentiment: sabit-varyans veya çok düşük kapsam (intersect'te std=0)
avail = [c for c in cols if c in df.columns]
print(f"kullanılan {len(avail)} feature: {avail}")

X = df[avail].apply(pd.to_numeric, errors="coerce")
X = X.dropna()
print(f"tam-satır (NaN'sız) n={len(X)}")

# standardize
Xs = (X - X.mean()) / X.std(ddof=0)
Xs = Xs.replace([np.inf, -np.inf], np.nan).dropna()
print(f"standardize sonrası n={len(Xs)}")

# korelasyon matrisi
corr = Xs.corr()
print("\n=== Korelasyon matrisi (|r|>0.5 çiftler) ===")
for i, a in enumerate(avail):
    for b in avail[i + 1 :]:
        if a in corr.columns and b in corr.columns:
            r = corr.loc[a, b]
            if abs(r) > 0.5:
                print(f"  {a:22} ↔ {b:22} r={r:+.3f}")

# PCA (eig üzerinden, sklearn'siz)
C = np.cov(Xs.values.T)
eigvals, eigvecs = np.linalg.eigh(C)
eigvals = eigvals[::-1]
eigvecs = eigvecs[:, ::-1]
eigvals = np.clip(eigvals, 0, None)
var_ratio = eigvals / eigvals.sum()
cum = np.cumsum(var_ratio)

print("\n=== PCA açıklanan-varyans ===")
for i, (v, c) in enumerate(zip(var_ratio, cum, strict=False)):
    print(f"  PC{i+1}: {v*100:5.1f}%  kümülatif={c*100:5.1f}%")
n90 = int(np.searchsorted(cum, 0.90) + 1)
n95 = int(np.searchsorted(cum, 0.95) + 1)
print(f"\n%90 varyansa yetecek bileşen sayısı: {n90} / {len(avail)}")
print(f"%95 varyansa yetecek bileşen sayısı: {n95} / {len(avail)}")

print("\n=== İlk 3 PC'ye en çok katkı yapan feature'lar (yükler) ===")
for i in range(min(3, len(avail))):
    load = eigvecs[:, i]
    order = np.argsort(-np.abs(load))
    top = [(avail[j], round(load[j], 3)) for j in order[:5]]
    print(f"  PC{i+1}: {top}")

# VIF-benzeri: her feature'ın diğerleri tarafından ne kadar açıklandığı (R^2 diagonal-inverse)
try:
    inv_corr = np.linalg.inv(corr.values)
    vif = np.diag(inv_corr)
    print("\n=== VIF (yaklaşık, >5 yüksek-redundant sayılır) ===")
    for c, v in sorted(zip(avail, vif, strict=False), key=lambda t: -t[1]):
        print(f"  {c:22} VIF={v:6.2f}")
except np.linalg.LinAlgError:
    print(
        "\n(korelasyon matrisi tekil — VIF hesaplanamadı, bazı feature'lar mükemmel-korelasyonlu)"
    )
