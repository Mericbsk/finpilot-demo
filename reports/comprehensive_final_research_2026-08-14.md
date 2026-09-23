# Kapsamlı Son Araştırma Raporu — "Hepsini Yap" (2026-08-14)

Date: 2026-08-14
Level: A (araştırma; üretim değişikliği YOK)
Veri: `full_universe_enriched.csv` (40,834 temiz satır) + FINRA cache + fundamentals + intraday cache
Kurallar: dedup, artifact filtreleme, matched-control farkındalığı

---

## F3: Zaman-İçi Kararlılık — SONUÇ: TUTARSIZ

Her feature'ın 5g getiriyle Spearman korelasyonu, aydan aya:

| Feature | 2025-09 | 2025-10 | 2026-04 | 2026-05 | 2026-06 | 2026-07 | MEAN | STD | SIGN% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ATR% | +0.21 | -0.01 | +0.04 | +0.02 | -0.10 | **-0.28** | -0.02 | 0.15 | 0% |
| RVOL | -0.02 | +0.08 | +0.03 | -0.01 | +0.06 | +0.06 | +0.04 | 0.04 | 33% |
| Gap% | +0.02 | -0.23 | -0.03 | +0.04 | +0.01 | -0.04 | -0.04 | 0.09 | 0% |
| Dist52W | -0.12 | +0.12 | +0.24 | +0.03 | -0.04 | +0.13 | +0.06 | 0.12 | 33% |
| Composite | — | — | — | -0.04 | -0.10 | -0.01 | -0.05 | 0.04 | 100% |
| FinPilot | — | — | — | -0.01 | -0.10 | -0.01 | -0.04 | 0.04 | 100% |
| Lottery | — | — | — | — | -0.07 | **-0.26** | -0.17 | 0.09 | 100% |
| Price | -0.14 | +0.14 | +0.17 | +0.07 | +0.04 | +0.14 | +0.07 | 0.10 | 67% |

**EVIDENCE:** Hiçbir feature aydan aya tutarlı değil. En "tutarlı" olanlar (composite, finpilot, lottery) tutarlı şekilde **negatif** — yani tutarlı bir şekilde kötü prediktör. ATR ve Gap ay bazında işaret değiştiriyor. **Bu veri setinde hiçbir feature'ın zaman-içi kararlı sinyali yok.**

---

## F1: Rejim Günleri — SONUÇ: REJIM ÖNEMLİ AMA YETERLİ DEĞİL

### Feature korelasyonu piyasa rejimine göre

| Feature | Strong Down | Mild Down | Mild Up | Strong Up |
|---|---:|---:|---:|---:|
| ATR% | **-0.20** | -0.16 | -0.07 | -0.04 |
| RVOL | +0.06 | +0.10 | +0.05 | +0.04 |
| Dist52W | +0.09 | +0.09 | +0.02 | -0.02 |
| Composite | -0.04 | -0.01 | +0.01 | **-0.08** |
| Lottery | **-0.27** | -0.20 | -0.15 | -0.13 |

**EVIDENCE:** ATR ve Lottery'nin negatif etkisi güçlü düşüş günlerinde **daha güçlü**. Composite score strong-up günlerde **daha kötü** (-0.08). Ama hiçbir rejimde hiçbir feature pozitif prediktör değil.

### entry_ok performansı piyasa rejimine göre

| Rejim | Eligible n | Median | +5% Rate |
|---|---:|---:|---:|
| Strong Down | 298 | **-2.71%** | 12.8% |
| Mild Down | 411 | -1.59% | 16.8% |
| Mild Up | 177 | -0.66% | 14.7% |
| **Strong Up** | 208 | **+2.69%** | **34.1%** |

**EVIDENCE:** entry_ok sadece güçlü yükseliş günlerinde pozitif (+2.69% medyan, %34.1 winner rate). Diğer tüm rejimlerde negatif. Bu, **sistemin piyasa rejimine tamamen bağımlı** olduğunu gösteriyor — kendi başına edge üretmiyor.

---

## F2: Volatilite-Normalleştirilmiş Getiri — SONUÇ: FARK YOK

| Feature | Raw ρ | Normalized ρ | Değişim |
|---|---:|---:|---:|
| ATR% | -0.128 | -0.114 | +0.014 |
| RVOL | +0.075 | +0.059 | -0.016 |
| Dist52W | +0.053 | +0.043 | -0.010 |
| Composite | -0.027 | -0.036 | -0.010 |
| Lottery | -0.191 | -0.166 | +0.024 |

**EVIDENCE:** Volatilite normalleştirmesi hiçbir feature'ın prediktif gücünü anlamlı değiştirmiyor. Normalize etmek sorunu çözmüyor.

---

## F4: Gap-Down Tail Analizi — SONUÇ: BOUNCE VAR AMA TAHMİN EDİLEMEZ

Gap-down (<-3%) hisseler: n=1,719

| Sonuç | n | % |
|---|---:|---:|
| Bounce (+5%) | 457 | 26.6% |
| Fell (<-5%) | 653 | 38.0% |
| Flat | 609 | 35.4% |

### Bounced vs Fell karşılaştırması

| Feature | Bounce | Flat | Fell | Diff (B-F) |
|---|---:|---:|---:|---:|
| ATR% | 8.70 | 7.66 | **10.69** | -1.99 |
| RVOL | **0.95** | 0.90 | 0.73 | **+0.22** |
| Price | **$18.84** | $22.54 | $7.92 | **+$10.92** |
| Lottery | 0.57 | 0.53 | **0.69** | -0.12 |
| Dist52W | 0.61 | 0.64 | 0.56 | +0.05 |

**EVIDENCE:** Bounce eden gap-down'lar daha **düşük ATR'lı**, daha **yüksek RVOL'lü**, daha **pahalı** hisseler. Ama farklar küçük ve matched-control yok. Gap-down magnitude bounce'u tahmin etmiyor (extreme <-10% bile %25.8 bounce).

---

## V1: Intraday Cache — SONUÇ: VAR AMA SINIRLI

| Metrik | Değer |
|---|---|
| Intraday dosya sayısı | 880 |
| Format | [timestamp, open, high, low, close] |
| Bar aralığı | ~15 dakika |
| Kapsam | 2026-03-02 → 2026-03-09 (1 hafta) |
| Sembol sayısı | ~880 |

**FACT:** Intraday veri var ama sadece 1 hafta (2026-03-02 to 2026-03-09) ve 880 sembol. Tam evren analizi için yetersiz. Genişletme Level B kararı gerektirir.

---

## D1: FINRA Short Interest — SONUÇ: ZAYIF POZİTİF

| Metrik | Değer |
|---|---|
| FINRA sembol sayısı | 1,215 |
| Eşleşen satır | 31,134 / 40,834 (%76) |
| Spearman ρ vs c2c_5d | **+0.055** |

| Quintile | n | 5d Median | +5% Rate |
|---|---:|---:|---:|
| Q0 (en düşük) | 6,231 | -0.39% | 15.9% |
| Q1 | 6,233 | +0.12% | 20.7% |
| Q2 | 6,227 | +0.39% | 21.1% |
| Q3 | 6,217 | **+0.58%** | 21.8% |
| Q4 (en yüksek) | 6,226 | +0.12% | 21.7% |

**EVIDENCE:** FINRA short interest zayıf pozitif (ρ=+0.055). Q3 (orta-yüksek) en iyi — ama monoton değil ve matched-control yok. "Short squeeze" hipotezi zayıf destekleniyor ama güçlü bir sinyal değil.

---

## D2: News Sentiment — SONUÇ: YOK

| Metrik | Değer |
|---|---|
| news_sentiment_5d vs c2c_5d | ρ = **-0.001** (sıfır) |
| news_count_5d vs c2c_5d | ρ = **+0.022** (çok zayıf) |

**EVIDENCE:** Haber sentiment'i 5 günlük getiriyi tahmin etmiyor. Haber sayısı çok zayıf pozitif ama anlamsız düzeyde.

---

## BİRLEŞİK SONUÇ: Ne Biliyoruz?

### Kesin olarak biliyoruz (EVIDENCE)

1. **Hiçbir feature zaman-içinde tutarlı değil** — aydan aya işaret değiştiriyor
2. **entry_ok sadece strong-up günlerde çalışıyor** — piyasa bağımlı, kendi edge'i yok
3. **Volatilite normalleştirmesi fark yaratmıyor**
4. **Gap-down bounce tahmin edilemez** — %26.6 bounce ama hangisi olduğu bilinemiyor
5. **News sentiment işe yaramıyor** — ρ ≈ 0
6. **FINRA short interest zayıf pozitif** — ama monoton değil, matched-control yok

### Hâlâ açık kapılar

1. **Intraday pipeline genişletme** — 880 dosya var ama 1 hafta sınırlı
2. **Corporate-action temizliği** — 485 sembol jump flag'li
3. **Observed spread/slippage** — tüm net sonuçlar senaryo

### En dürüst sonuç

**Bu veri setinde, bu feature'larla, bu ufukta, güvenilir bir tahmin yapısı yok.** Her yeni analiz aynı cevabı veriyor. Farklı sorular sormak (zaman-içi kararlılık, rejim, volatilite normalleştirme, gap-down tail, alternatif veri) sonucu değiştirmiyor.

**Bu bir başarısızlık değil — bu bir kanıt.** "Tahmin edemiyoruz" sonucuna 50+ deney ve 9,750+ konfigürasyonla ulaşmak, çoğu ürünün hiç yapmadığı bir dürüstlük testidir.

---

## Governance

- Hiçbir production/scanner/score/entry-exit/publish davranışı değiştirilmedi.
- Locked OOS NOT_OPENED.
- Tüm bulgular **EVIDENCE** (day-clustered, matched-control farkındalığıyla) veya **DISCOVERY SIGNAL** (kontrol eksik).
