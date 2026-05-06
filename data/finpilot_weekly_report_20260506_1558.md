# FinPilot Haftalık Test Raporu — 2026-05-06 15:58

---

## 1. A/B Backtest Özeti

| Metrik | Strateji A | Strateji B | Fark |
|--------|-----------|-----------|------|
| TP (Doğru Pozitif) | 0 | 14 | +14.0 |
| FP (Yanlış Pozitif) | 0 | 24 | +24.0 |
| FN (Kaçırılan) | 264 | 250 | -14.0 |
| Precision | 0 | 0.3684 | +0.37 |
| Recall | 0.0 | 0.053 | +0.05 |
| F1 Skoru | 0 | 0.0927 | +0.09 |
| Kâr ($) | -1320.0 | -1256.64 | +63.36 |
| Toplam Sinyal | 0 | 38 | +38.0 |

> **Kazanan:** Strateji **B** — Kâr farkı $63.36

---

## 2. Walk-Forward Doğrulama

- Veri aralığı: `2025-09-01 → 2027-12-17`
- Pencere sayısı: **24** (90g eğitim / 30g test)

| Metrik | A | B |
|--------|---|---|
| OOS Toplam Kâr ($) | -1090.0 | -1087.6 |
| Deflated Sharpe | -64.035 | -29.144 |
| Kazançlı Pencere % | 0.0 | 0.0 |
| IS/OOS Korelasyon | 0.047 | 0.056 |

---

## 3. Monte Carlo Anlamlılık

**Strateji A:**
- Gerçek getiri: **-13.2%**  (MC ortanca: -13.2%)
- Sharpe p-değeri: **1.0**
- ❌ Şansa dayalı: sonuç rastgele dağılımdan ayırt edilemiyor

**Strateji B:**
- Gerçek getiri: **-12.57%**  (MC ortanca: -12.566%)
- Sharpe p-değeri: **0.1867**
- ⚠️  Zayıf edge: şans payı yüksek

---

## 4. Slippage Kalibrasyon

> ⚠️ 'NoneType' object has no attribute '__dict__'

---

## 5. Öneri Özeti

| Kriter | Durum |
|--------|-------|
| Strateji B kârlı mı? | ❌ $-1,256.64 |
| Walk-Forward DSR > 0.5? | ❌ -29.144 |
| Monte Carlo p < 0.05? | ⚠️ 0.1867 |
| Kazançlı pencere > 50%? | ⚠️ 0% |
| Slippage kalibre mi? | ⚠️ Veri biriksin  |

> 🔴 **Strateji B henüz canlıya alınmamalı.** Daha fazla veri birikmeli.

---
*FinPilot otomatik rapor — 2026-05-06 15:58*
