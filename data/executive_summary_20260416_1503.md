# FinPilot Scanner — Tek Sayfalık Özet

**Tarih:** 2026-04-16  |  **Veri:** 9,646 tarama sinyali, 121 çalışma

---

## Problem

Mevcut tarama sistemi çok katı eşiklerle çalışıyor: 9,646 sinyalden yalnızca **245'i** (2.5%) `entry_ok=True` olarak işaretleniyor.
Agresif mod daha fazla sinyal yakalıyor ama Precision düşüyor.

## Bulgu

3,456 parametre kombinasyonu test edildi.

| | Mevcut | **Önerilen** | Değişim |
|--|--------|------------|---------|
| Profit Score | -945.40 | **8217.32** | **+9162.72** |
| F1 | 0.170 | **0.886** | +0.716 |
| Precision | 1.000 | **1.000** | +0.000 |
| Sinyal/Tarama | 0.3 | **2.8** | +2.5 |

## Önerilen Parametreler (Öneri #1)

```
min_alignment_ratio: 0.6   (mevcut: 0.75)
min_momentum_ratio:  0.4   (mevcut: 0.60)
min_filter_score:    1          (mevcut: 2)
min_signal_score:    2          (mevcut: 2)
min_zscore:          0.0        (mevcut: 1.5)
```

## Sonraki Adımlar

1. **Hemen (Bu hafta):** `scanner/config.py` güncelle, 1 hafta canary test (%10 trafik)
2. **Kısa vade (1 ay):** Dinamik eşik modülü yaz (VIX entegrasyonu)
3. **Orta vade (3 ay):** Ensemble kural + DRL hybrid karar motoru
4. **Uzun vade (6 ay):** Maliyet duyarlı DRL eğitimi, meta-optimizasyon scheduler

## Risk

- Canary'de FP > %25 olursa otomatik rollback
- Haftalık drift monitoring zorunlu
- İnsan onayı: yeni parametreler canlıya geçmeden önce

---
*Bu özet scanner_optimizer.py tarafından otomatik üretildi.*
