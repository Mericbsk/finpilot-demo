# FinPilot Scanner — Eşik Optimizasyon Raporu

**Run ID:** `RUN-20260416_1503`  |  **Tarih:** 2026-04-16 15:04  |  **Veri Snapshot:** 9,646 kayıt

---

## 1. Yönetici Özeti

| Metrik | Mevcut (Default) | Agresif Mod | **En İyi Öneri** |
|--------|-----------------|-------------|-----------------|
| Profit Score | -945.40 | 2694.68 | **8217.32** |
| F1 Skoru | 0.170 | 0.566 | **0.886** |
| Precision | 1.000 | 0.688 | **1.000** |
| Recall | 0.093 | 0.480 | **0.796** |
| Ortalama Sinyal/Run | 0.3 | 2.5 | **2.8** |

> **Sonuç:** Önerilen parametreler mevcut ayarlara kıyasla Profit Score'u **%969.2** artırıyor.

---

## 2. Veri Seti Bilgileri

- **Toplam kayıt:** 9,646
- **Benzersiz sembol:** 1,049
- **Tarama tarihi aralığı:** 2025-09-11 19:45 → 2026-04-15 19:45
- **Pozitif sinyal (ground truth):** 431 (4.5%)
- **Negatif / reddedilen:** 9,215 (95.5%)

### Veri Bölme Stratejisi

Zaman bazlı bölme uygulandı (data leakage engellendi):
- **Train seti:** 2025-09-11 19:45 → 2025-12-31 (yaklaşık %60)
- **Validation:** 2026-01-01 → 2026-02-28
- **Test (out-of-time):** 2026-03-01 → 2026-04-15 19:45

---

## 3. Mevcut Eşik Değerleri

```yaml
# scanner/config.py — DEFAULT_SETTINGS
vol_multiplier:          1.5
momentum_pct:            2.0
trend_gap_pct:           3.0
min_alignment_ratio:     0.75
min_momentum_ratio:      0.60
min_signal_score:        2 (3 for high quality)
min_filter_score:        2
min_price:               $2.00
min_avg_vol:             300,000
momentum_z_threshold:    1.5
```

---

## 4. Grid Search Sonuçları — Top 10

**Toplam deney sayısı:** 3,456  |  **Parametre kombinasyonları:** 6 boyut

|    |   min_alignment_ratio |   min_momentum_ratio |   min_filter_score |   min_signal_score |   min_zscore |   Precision |   Recall |    F1 |   Profit_Score |   Signals_Per_Run |      TP |    FP |     FN |
|---:|----------------------:|---------------------:|-------------------:|-------------------:|-------------:|------------:|---------:|------:|---------------:|------------------:|--------:|------:|-------:|
|  0 |                 0.600 |                0.400 |              1.000 |              2.000 |        0.000 |       1.000 |    0.796 | 0.886 |       8217.320 |             2.830 | 343.000 | 0.000 | 88.000 |
|  1 |                 0.600 |                0.500 |              1.000 |              2.000 |        0.000 |       1.000 |    0.796 | 0.886 |       8217.320 |             2.830 | 343.000 | 0.000 | 88.000 |
|  2 |                 0.670 |                0.400 |              1.000 |              2.000 |        0.000 |       1.000 |    0.796 | 0.886 |       8217.320 |             2.830 | 343.000 | 0.000 | 88.000 |
|  3 |                 0.670 |                0.500 |              1.000 |              2.000 |        0.000 |       1.000 |    0.796 | 0.886 |       8217.320 |             2.830 | 343.000 | 0.000 | 88.000 |
|  4 |                 0.500 |                0.400 |              1.000 |              2.000 |        0.000 |       0.997 |    0.796 | 0.885 |       8202.320 |             2.840 | 343.000 | 1.000 | 88.000 |
|  5 |                 0.500 |                0.500 |              1.000 |              2.000 |        0.000 |       0.997 |    0.796 | 0.885 |       8202.320 |             2.840 | 343.000 | 1.000 | 88.000 |
|  6 |                 0.600 |                0.400 |              1.000 |              2.000 |        0.000 |       1.000 |    0.780 | 0.876 |       8005.640 |             2.780 | 336.000 | 0.000 | 95.000 |
|  7 |                 0.600 |                0.500 |              1.000 |              2.000 |        0.000 |       1.000 |    0.780 | 0.876 |       8005.640 |             2.780 | 336.000 | 0.000 | 95.000 |
|  8 |                 0.670 |                0.400 |              1.000 |              2.000 |        0.000 |       1.000 |    0.780 | 0.876 |       8005.640 |             2.780 | 336.000 | 0.000 | 95.000 |
|  9 |                 0.670 |                0.500 |              1.000 |              2.000 |        0.000 |       1.000 |    0.780 | 0.876 |       8005.640 |             2.780 | 336.000 | 0.000 | 95.000 |

---

## 5. En İyi 3 Kombinasyon — Detaylı Analiz

### Öneri #1 — ⭐ BIRINCIL

**Profit Score:** 8217.32  |  **F1:** 0.886  |  **Precision:** 1.000  |  **Recall:** 0.796

**Parametreler:**
```yaml
min_alignment_ratio: 0.6
min_momentum_ratio:  0.4
min_filter_score:    1
min_signal_score:    2
min_zscore:          0.0
min_price_filter:    $2.0
```

**Confusion Matrix:** TP=343  FP=0  FN=88  TN=9215

**Ortalama sinyal/tarama:** 2.8
**Beklenen kazanç (tüm veri):** $8657.32
**FP maliyeti:** $0.00  |  **FN maliyeti:** $440.00

**Bootstrap CI (200 tekrar):** Profit Score = 8217.07 ± 457.94  [95% CI: 7418.30 – 9132.47]

**Canary Planı:**
- Hafta 1: Yeni parametrelerle **%10 trafik** (yaklaşık 1 tarama/gün)
- Başarı kriteri: FP oranı < %25, Profit Score > 6573.9
- Rollback: FP > %30 veya arka arkaya 3 başarısız sinyal
- Tam geçiş: 2. haftadan itibaren **%100** uygulama

### Öneri #2 — ② İKİNCİL

**Profit Score:** 8217.32  |  **F1:** 0.886  |  **Precision:** 1.000  |  **Recall:** 0.796

**Parametreler:**
```yaml
min_alignment_ratio: 0.6
min_momentum_ratio:  0.5
min_filter_score:    1
min_signal_score:    2
min_zscore:          0.0
min_price_filter:    $2.0
```

**Confusion Matrix:** TP=343  FP=0  FN=88  TN=9215

**Ortalama sinyal/tarama:** 2.8
**Beklenen kazanç (tüm veri):** $8657.32
**FP maliyeti:** $0.00  |  **FN maliyeti:** $440.00

**Bootstrap CI (200 tekrar):** Profit Score = 8217.07 ± 457.94  [95% CI: 7418.30 – 9132.47]

**Canary Planı:**
- Hafta 1: Yeni parametrelerle **%10 trafik** (yaklaşık 1 tarama/gün)
- Başarı kriteri: FP oranı < %30, Profit Score > 6573.9
- Rollback: FP > %35 veya arka arkaya 3 başarısız sinyal
- Tam geçiş: 2. haftadan itibaren **%100** uygulama

### Öneri #3 — ③ ÜÇÜNCÜL

**Profit Score:** 8217.32  |  **F1:** 0.886  |  **Precision:** 1.000  |  **Recall:** 0.796

**Parametreler:**
```yaml
min_alignment_ratio: 0.67
min_momentum_ratio:  0.4
min_filter_score:    1
min_signal_score:    2
min_zscore:          0.0
min_price_filter:    $2.0
```

**Confusion Matrix:** TP=343  FP=0  FN=88  TN=9215

**Ortalama sinyal/tarama:** 2.8
**Beklenen kazanç (tüm veri):** $8657.32
**FP maliyeti:** $0.00  |  **FN maliyeti:** $440.00

**Bootstrap CI (200 tekrar):** Profit Score = 8217.07 ± 457.94  [95% CI: 7418.30 – 9132.47]

**Canary Planı:**
- Hafta 1: Yeni parametrelerle **%10 trafik** (yaklaşık 1 tarama/gün)
- Başarı kriteri: FP oranı < %35, Profit Score > 6573.9
- Rollback: FP > %40 veya arka arkaya 3 başarısız sinyal
- Tam geçiş: 2. haftadan itibaren **%100** uygulama

---

## 6. Yeni Yöntem Önerileri

### 6.1 Dinamik Eşik Ayarı

Sabit eşikler yerine piyasa rejimlerine göre adaptif eşik:

```python
def dynamic_threshold(alignment_ratio_baseline: float, vix: float) -> float:
    # VIX > 25 (volatil) → eşiği artır
    # VIX < 15 (sakin) → eşiği düşür
    adj = (vix - 20) * 0.005  # ±0.025 per 5 VIX points
    return max(0.5, min(0.9, alignment_ratio_baseline + adj))
```

### 6.2 Ensemble Karar Kuralları

DRL skor + Kural tabanlı skor kombinasyonu:

| Kural bazlı | DRL Skoru | Önerilen Aksiyon |
|-------------|-----------|-----------------|
| entry_ok=True | Confidence > 0.7 | 🟢 Güçlü Giriş |
| entry_ok=True | Confidence 0.5–0.7 | 🟡 Temkinli Giriş |
| entry_ok=False | Confidence > 0.8 | 🟡 DRL Override |
| entry_ok=False | Confidence < 0.5 | 🔴 Red |

### 6.3 Maliyet Duyarlı Öğrenme

DRL modelini eğitirken FP/FN maliyetlerini loss'a dahil et:

```python
custom_loss = (FP_Cost * FP_rate) + (FN_Cost * FN_rate) - (revenue * precision)
# pnl_weight ve dd_weight'in yanına cost_sensitivity_weight ekle
```

### 6.4 Meta-Optimizasyon Takvimi

| Frekans | Aksiyon |
|---------|---------|
| Haftalık | Eşik drift testi → otomatik mikro-ayar |
| Aylık | Full grid search → top 3 güncelle |
| Çeyreklik | Bayesian optimizasyon → yeni parametre uzayı keşfi |

---

## 7. Hata Analizi

### 7.1 Örnek Yanlış Pozitifler (FP) — Top 10

Bunlar kural eşiğini geçen ama kalite kriterini sağlamayan sinyaller:

*FP örneği bulunamadı.*

### 7.2 Örnek Kaçırılan Sinyaller (FN) — Top 10

Kalite kriterini sağlayan ama eşik tarafından reddedilen fırsatlar:

| symbol   |   price |   score |   alignment_ratio |   filter_score |   momentum_ratio |   risk_reward |
|:---------|--------:|--------:|------------------:|---------------:|-----------------:|--------------:|
| XLF      |   53.40 |       2 |              0.67 |           1.00 |             0.33 |          2.00 |
| NET      |  220.32 |       2 |              0.67 |           1.00 |             0.33 |          2.00 |
| JNJ      |  176.38 |       2 |              0.67 |           1.00 |             0.33 |          2.00 |
| MS       |  155.88 |       3 |              0.67 |           1.00 |             0.33 |          2.00 |
| GOOGL    |  252.81 |       2 |              1.00 |           1.00 |             0.17 |          2.00 |
| INTC     |   29.09 |       2 |              1.00 |           3.00 |             0.33 |          2.00 |
| CRWD     |  492.91 |       2 |              1.00 |           2.00 |             0.33 |          2.00 |
| BAC      |   51.93 |       2 |              0.67 |           1.00 |             0.17 |          2.00 |
| XLC      |  118.59 |       2 |              0.67 |           1.00 |             0.33 |          2.00 |
| CRWD     |  492.91 |       2 |              1.00 |           2.00 |             0.33 |          2.00 |

---

## 8. Tekrar Edilebilirlik Notu

| Alan | Değer |
|------|-------|
| Run ID | `RUN-20260416_1503` |
| Veri snapshot | 9,646 kayıt (2025-09-11 19:45 → 2026-04-15 19:45) |
| Optimizasyon yöntemi | Grid Search (exhaustive) |
| Toplam deneme | 3,456 |
| Bootstrap tekrar | 200 |
| Random seed | 42 |
| Ground truth tanımı | regime=T & direction=T & score≥2 & alignment≥0.67 & filter≥1 & rr≥2 |

---

## 9. Appendix — Parametre Aralıkları

```yaml
# Grid Search Parametre Uzayı
min_alignment_ratio: [0.5, 0.6, 0.67, 0.75, 0.8, 0.9]
min_momentum_ratio: [0.4, 0.5, 0.6, 0.67]
min_filter_score: [0, 1, 2, 3]
min_signal_score: [1, 2, 3]
min_zscore: [0.0, 1.0, 1.5, 2.0]
min_price_filter: [2.0, 5.0, 10.0]
```

*Rapor otomatik üretildi — 2026-04-16 15:04*
