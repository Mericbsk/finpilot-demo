# Dikkat Haritası — "Hangi Hisse Olağandışı?" Araştırma Raporu

Date: 2026-08-14
Level: A (araştırma; üretim değişikliği YOK)
Veri: `full_universe_enriched.csv`, 40,834 temiz satır
Kurallar: dedup, artifact filtreleme, tahmin değil tanımlama

## Araştırma Sorusu

> "Hangi hisse yükselecek?" değil, **"hangi hisse olağandışı davranıyor?"** — Dikkat haritası olarak değer üretebilir miyiz?

---

## 1. Olağandışılık Skoru

6 flag tanımlandı (tahmin değil, tanımlama):

| Flag | Eşik | Anlam |
|---|---|---|
| Volume Spike | RVOL ≥ 2.0 | Normalden 2x fazla hacim |
| Volatility Spike | ATR ≥ 6% | Yüksek volatilite |
| Big Gap | \|gap\| ≥ 3% | Büyük açılış farkı |
| Extension Extreme | dist < 0.3 veya ≥ 0.95 | Zirveden çok uzak veya çok yakın |
| High Lottery | lottery ≥ 0.6 | Spekülatif |
| Squeeze | squeeze ≥ 0.5 | Sıkışma |

### Skor dağılımı ve sonuç

| Unusual Score | n | % | 5d Median | +5% Rate | \|5d ret\| Median |
|---|---:|---:|---:|---:|---:|
| 0 (normal) | 17,997 | 44.1% | +0.50% | 18.4% | 2.97% |
| 1 | 13,170 | 32.3% | +0.14% | 20.1% | 3.32% |
| 2 | 6,238 | 15.3% | -1.67% | 22.5% | 6.98% |
| 3 | 2,563 | 6.3% | -3.11% | 21.3% | — |
| 4+ | 866 | 2.1% | -5.12% | 22.4% | — |

**EVIDENCE:** Olağandışılık skoru arttıkça **medyan getiri düşüyor** ama **hareket büyüklüğü artıyor**. Score 0: |5d ret| 2.97%; Score 2: |5d ret| 6.98%. Yön yok, hareket var.

---

## 2. Dikkat Haritası Değeri

### Unusual vs Normal

| Metrik | Unusual (score≥2) | Normal (score≤1) |
|---|---:|---:|
| n | 9,667 | 31,167 |
| 5d median | **-2.32%** | +0.34% |
| 5d \|return\| median | **6.98%** | 3.32% |
| 5d +5% rate | 22.2% | 19.1% |
| 5d <-5% rate | **39.4%** | 15.1% |
| Direction positive | 39.8% | 53.5% |

**EVIDENCE:** Olağandışı hisseler **daha fazla hareket ediyor** (|ret| 7.0% vs 3.3%) ama **daha sık düşüyor** (%39.4 vs %15.1 big loser). Yön yok, volatilite var.

---

## 3. Olağandışılık Tipleri

| Tip | n | 5d Med | \|5d ret\| | Future Interesting | Lift |
|---|---:|---:|---:|---:|---:|
| Big Gap (≥3%) | 3,427 | -2.45% | **7.50%** | **64.6%** | **1.59x** |
| Volatility Spike (ATR≥6) | 13,063 | -1.99% | 7.17% | 63.2% | 1.55x |
| High Lottery (≥0.6) | 5,505 | -2.86% | 6.97% | 61.5% | 1.51x |
| Far from High (<0.3) | 2,798 | -2.08% | 6.73% | 60.3% | 1.48x |
| Volume Spike (RVOL≥2) | 2,594 | +0.05% | 5.29% | 51.2% | 1.26x |
| Squeeze (≥0.5) | 3,168 | -1.05% | 5.24% | 51.7% | 1.27x |
| Near High (≥0.95) | 6,375 | +0.13% | **2.29%** | **23.9%** | **0.59x** |

**EVIDENCE:** "Big Gap" ve "Volatility Spike" en iyi dikkat sinyalleri — gelecekte büyük hareket olasılığı %63-65 (base %41). "Near High" en kötü — %24 (base'in altında).

---

## 4. Dikkat Haritası Ürün Simülasyonu

### Attention = Big Gap OR Volatility Spike

| Metrik | Attention | High Attention | Normal |
|---|---:|---:|---:|
| n | 13,865 | 2,625 | 26,969 |
| 5d \|return\| median | **6.99%** | **8.92%** | 2.97% |
| Future \|ret\|≥5% | **62.1%** | **70.7%** | 29.7% |
| 5d median | -1.79% | -3.85% | +0.34% |

### Coverage ve Precision

- **Coverage:** Tüm büyük hareketlerin (%5+) %51.8'i attention tarafından yakalanıyor
- **Precision:** Flag edilen hisselerin %62.1'i gerçekten büyük hareket yapıyor

### Tipik gün örneği (2026-07-28)

```
65 hisse tarandı
25 attention (38%)
13 high attention (20%)

Öne çıkanlar:
  FCEL: $19.66, ATR=13.3%, gap=-6.3%, rvol=0.69 → 5d: +14.4%
  NBIS: $183.01, ATR=13.3%, gap=-4.8%, rvol=1.54 → 5d: +23.3%
  NUAI: $4.42, ATR=13.2%, gap=-3.7%, rvol=0.60 → 5d: +19.5%
```

---

## 5. Dikkat Haritası vs Tahmin Motoru

| | Tahmin Motoru | Dikkat Haritası |
|---|---|---|
| Soru | "Hangi hisse yükselecek?" | "Hangi hisse olağandışı?" |
| Kanıt | Yok (6 bağımsız yoldan negatif) | Var (lift 1.26-1.59x) |
| Kullanıcı vaadi | "Bu hisseleri al" | "Bu hisselere bak" |
| Compliance riski | Yüksek (yatırım tavsiyesi) | Düşük (bilgi sunumu) |
| Doğruluk oranı | Rastgeleden kötü | %62.1 precision |
| Kullanıcı değeri | Düşük (tahmin tutmuyor) | Yüksek (ilginç olanı gösteriyor) |

---

## 6. Sonuç

**Dikkat haritası çalışıyor.** "Hangi hisse olağandışı?" sorusu cevaplanabilir ve kanıtlanabilir:

- Big Gap + Volatility Spike → %70.7 olasılıkla büyük hareket (5 gün içinde |≥5%|)
- Ama yön bilinmiyor — %40 yukarı, %60 aşağı

**Bu bir tahmin motoru değil.** Kullanıcıya "bu hisseye bak, bir şey oluyor" diyoruz — "bu hisse yükselecek" demiyoruz.

**Ürün olarak:** "Bugün piyasada 12 hisse olağandışı hareket gösteriyor. İşte neden: yüksek volatilite, büyük gap, hacim artışı. Yön bilinmiyor ama izlemeye değer."

---

## Governance

- Hiçbir production/scanner/score/entry-exit/publish davranışı değiştirilmedi.
- Locked OOS NOT_OPENED.
- Dikkat haritası bulguları **EVIDENCE** (lift, coverage, precision hesaplanmış).
- "Yön tahmini" iddiası **yapılmamış** — sadece "olağandışılık" tanımlanmış.
