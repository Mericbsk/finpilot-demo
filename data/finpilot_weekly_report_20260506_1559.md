# FinPilot Haftalık Test Raporu — 2026-05-06 15:59

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

- Veri aralığı: `N/A`
- Pencere sayısı: **?** (?g eğitim / ?g test)

| Metrik | A | B |
|--------|---|---|
| OOS Toplam Kâr ($) | — | — |
| Deflated Sharpe | — | — |
| Kazançlı Pencere % | — | — |
| IS/OOS Korelasyon | — | — |

---

## 3. Monte Carlo Anlamlılık

**Strateji A:**
- Gerçek getiri: **—%**  (MC ortanca: —%)
- Sharpe p-değeri: **—**
- —

**Strateji B:**
- Gerçek getiri: **—%**  (MC ortanca: —%)
- Sharpe p-değeri: **—**
- —

---

## 4. Slippage Kalibrasyon

- Kayıt sayısı: **0** (varsayılan değerler)
- Alış slippage: **0.200%**
- Satış slippage: **0.150%**
- Kyle λ: **0.1000** (piyasa etkisi katsayısı)
- Gidiş-dönüş maliyet ≈ **0.450%** ($3K pozisyon)

---

## 5. Öneri Özeti

| Kriter | Durum |
|--------|-------|
| Strateji B kârlı mı? | ❌ $-1,256.64 |
| Walk-Forward DSR > 0.5? | ❌ -999.000 |
| Monte Carlo p < 0.05? | ⚠️ 1.0000 |
| Kazançlı pencere > 50%? | ⚠️ 0% |
| Slippage kalibre mi? | ⚠️ Veri biriksin  |

> 🔴 **Strateji B henüz canlıya alınmamalı.** Daha fazla veri birikmeli.

---
*FinPilot otomatik rapor — 2026-05-06 15:59*
