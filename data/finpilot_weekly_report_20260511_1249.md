# FinPilot Haftalık Test Raporu — 2026-05-11 12:49

---

## 1. A/B Backtest Özeti

| Metrik | Strateji A | Strateji B | Fark |
|--------|-----------|-----------|------|
| TP (Doğru Pozitif) | 640 | 4202 | +3562.0 |
| FP (Yanlış Pozitif) | 0 | 263 | +263.0 |
| FN (Kaçırılan) | 4818 | 1256 | -3562.0 |
| Precision | 1.0 | 0.9411 | -0.06 |
| Recall | 0.1173 | 0.7699 | +0.65 |
| F1 Skoru | 0.2099 | 0.8469 | +0.64 |
| Kâr ($) | -7936.4 | 95833.48 | +103769.88 |
| Toplam Sinyal | 640 | 4465 | +3825.0 |

> **Kazanan:** Strateji **B** — Kâr farkı $103,769.88

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
- Gerçek getiri: **-79.36%**  (MC ortanca: -79.364%)
- Sharpe p-değeri: **1.0**
- ❌ Şansa dayalı: sonuç rastgele dağılımdan ayırt edilemiyor

**Strateji B:**
- Gerçek getiri: **958.33%**  (MC ortanca: 958.335%)
- Sharpe p-değeri: **0.08**
- ⚠️  Zayıf edge: şans payı yüksek

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
| Strateji B kârlı mı? | ✅ $95,833.48 |
| Walk-Forward DSR > 0.5? | ❌ -999.000 |
| Monte Carlo p < 0.05? | ⚠️ 0.0800 |
| Kazançlı pencere > 50%? | ⚠️ 0% |
| Slippage kalibre mi? | ⚠️ Veri biriksin  |

> 🟡 **Strateji B ek doğrulama gerektiriyor.** Zayıf kriterler var.

---
*FinPilot otomatik rapor — 2026-05-11 12:49*