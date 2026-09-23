# Winner Anatomy — Geniş Kapsamlı Düşünce Deneyi Sonuçları

Date: 2026-08-14
Level: A (araştırma; üretim değişikliği YOK)
Veri: `full_universe_enriched.csv`, 48,760 dedup satır → 40,834 temiz satır (price≥$1, |c2c_5d|≤100%)
Kurallar: dedup, gün-kümeli farkındalık, artifact filtreleme, matched-control

## Araştırma Sorusu

> "Geçmişte gerçekten güçlü hareket yapan hisseler, tarama anında nasıl bir davranış sergiliyordu ve FinPilot bugün bunların hangisini yakalıyor, hangisini kaçırıyor?"

---

## 1. Winner Bucket Dağılımı (temiz veri)

| Bucket | n | % |
|---|---:|---:|
| <0% | 20,298 | 49.7% |
| 0-1% | 3,379 | 8.3% |
| 1-3% | 5,265 | 12.9% |
| 3-5% | 3,790 | 9.3% |
| 5-10% | 4,557 | 11.2% |
| 10-20% | 2,604 | 6.4% |
| >20% | 941 | 2.3% |

**FACT:** +5% ve üzeri hareket yapan 8,102 satır var — evrenin %19.8'i.

---

## 2. Winner Fingerprint — Tek Özellik Medyan Karşılaştırması

| Feature | <0% | 0-1% | 1-3% | 3-5% | 5-10% | 10-20% | >20% |
|---|---:|---:|---:|---:|---:|---:|---:|
| ATR% | 4.82 | 3.07 | 3.44 | 3.72 | 4.54 | 5.84 | 7.90 |
| RVOL | 0.82 | 0.84 | 0.85 | 0.86 | 0.88 | 0.91 | 0.93 |
| Gap% | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.15 |
| Dist52W% | 0.76 | 0.88 | 0.83 | 0.80 | 0.74 | 0.67 | 0.60 |
| Lottery | 0.44 | 0.29 | 0.31 | 0.32 | 0.38 | 0.47 | 0.62 |
| Price | 28.1 | 39.7 | 46.6 | 50.5 | 41.7 | 25.8 | 10.2 |
| FinPilot Score | 29 | 30 | 29 | 29 | 28 | 29 | 29 |
| Composite Score | 29 | 31 | 29 | 28 | 26 | 26 | 26 |

### Kritik gözlemler

1. **ATR tek başına en güçlü winner prediktörü** — monoton artış: <0% grubunda 4.82 → >20% grubunda 7.90. **EVIDENCE**.
2. **Score'lar winner'ları ayırt etmiyor** — finpilot_score tüm bucket'larda ~29; composite_score winner'larda hafifçe **düşük** (26 vs 29). **EVIDENCE**.
3. **RVOL doz-response gösteriyor ama zayıf** — 0.82 → 0.93 monoton ama fark küçük. **EVIDENCE**.
4. **Dist52W ters yönde** — winner'lar 52-haftalık zirveye daha uzak (0.60 vs 0.88). **EVIDENCE**.
5. **Price ters U-şekilli** — 3-5% bucket'ta en yüksek ($50), >20% bucket'ta en düşük ($10). **EVIDENCE**.

---

## 3. Feature Lift Analizi (Winner vs Control)

| Feature | Range | Control% | +5% Winner% | Lift | Yorum |
|---|---|---:|---:|---:|---|
| ATR% | low (<3) | 25.1% | 11.4% | **0.45x** | Winner'larda düşük ATR yarı yarıya az |
| ATR% | high (5-8) | 24.1% | 30.2% | **1.26x** | Winner'larda yüksek ATR daha yaygın |
| ATR% | extreme (>8) | 23.1% | 27.3% | **1.18x** | Extreme ATR da winner'larda yaygın |
| RVOL | low (<0.8) | 48.4% | 41.5% | **0.86x** | Düşük RVOL winner'larda daha az |
| RVOL | extreme (>3) | 3.1% | 4.2% | **1.34x** | Extreme RVOL winner'larda daha yaygın |
| Dist52W | very_far (>0.95) | 15.8% | 8.9% | **0.56x** | Zirveden uzak olanlar winner değil |
| Lottery | low (<0.2) | 7.3% | 4.7% | **0.64x** | Düşük lottery winner'larda az |
| Price | penny (<$5) | 24.5% | 26.9% | 1.10x | Penny hisseler hafifçe daha yaygın |
| Gap | big_down (<-3%) | 5.1% | 7.3% | **1.41x** | Büyük gap-down winner'larda daha yaygın |

**En güçlü lift'ler:** ATR low→0.45x (negatif), Dist52W very_far→0.56x (negatif), Gap big_down→1.41x (pozitif).

---

## 4. KRITIK BULGU: Feature Interaction (ATR × RVOL)

Winner rate (+5% olma olasılığı) ATR ve RVOL kombinasyonuna göre dramatik değişiyor:

| ATR \ RVOL | low | normal | elevated | high | extreme |
|---|---:|---:|---:|---:|---:|
| **low** (<3) | 8.1% | 9.8% | 10.2% | 10.0% | 10.5% |
| **med** (3-5) | 18.2% | 22.1% | 22.6% | **26.7%** | **27.3%** |
| **high** (5-8) | 21.9% | **27.2%** | **30.1%** | **29.3%** | **31.8%** |
| **extreme** (>8) | 21.1% | **27.8%** | **30.7%** | **29.8%** | 28.8% |

**EVIDENCE:** ATR low + RVOL low hücresinde winner rate %8.1; ATR high + RVOL elevated'de **%30.1**. Fark 3.7x.

### Ama: Medyan getiri farklı bir hikâye anlatıyor

| ATR \ RVOL | low | normal | elevated | high | extreme |
|---|---:|---:|---:|---:|---:|
| **low** | +0.24% | +0.45% | +0.45% | +0.25% | -0.06% |
| **med** | +0.28% | **+0.67%** | **+0.74%** | **+1.06%** | +0.61% |
| **high** | -1.05% | +0.00% | +0.21% | -0.34% | -0.07% |
| **extreme** | **-3.76%** | -1.78% | -0.92% | -2.17% | -3.73% |

**EVIDENCE:** Winner rate en yüksek hücreler (high/extreme ATR) medyan getiride **negatif**. Çünkü winner rate ≠ beklenen getiri — yüksek ATR'de kazananlar büyük kazanıyor ama kaybedenler daha büyük kaybediyor.

**Bu, "ATR yüksek = iyi" demek DEĞİL.** ATR yüksek = daha fazla winner VAR ama aynı zamanda daha fazla büyük loser VAR.

---

## 5. KRITIK BULGU: entry_ok %97.5 Winner Kaçırıyor

| Kategori | n | % |
|---|---:|---:|
| Eligible + Winner (+5%) | 204 | 2.5% (true positive) |
| Eligible + Loser (<0%) | 612 | (false positive) |
| Rejected + Winner (+5%) | 7,898 | **97.5% (FALSE NEGATIVE)** |
| Rejected + Loser (<0%) | 20,877 | (true negative) |

**EVIDENCE:** entry_ok, +5% winner'ların %97.5'ini kaçırıyor. Ama bu otomatik olarak "entry_ok kötü" demek değil — çünkü rejected'ın da %29.3'ü +5% winner çıkıyor. Sorun: eligible precision sadece %25.1 — rejected'dan **daha düşük**.

### Missed winners vs captured winners karşılaştırması

| Feature | Missed (rejected +5%) | Captured (eligible +5%) | Fark |
|---|---:|---:|---:|
| Composite Score | 22 | 62 | -40 |
| FinPilot Score | 26 | 55 | -29 |
| Price | $25.83 | $62.19 | -$36.37 |
| Dist52W | 0.665 | 0.886 | -0.221 |
| RVOL | 0.876 | 1.076 | -0.200 |
| ATR% | 5.57 | 5.37 | +0.21 |

**EVIDENCE:** entry_ok yüksek skorlu, pahalı, zirveye yakın hisseleri seçiyor — ama bunlar daha iyi winner değil. Kaçırılan winner'lar daha düşük skorlu, daha ucuz, zirveden daha uzak.

---

## 6. Regime × Direction: Beklenmedik Sonuç

| Regime | Direction | n | +5% Rate | Median | Mean |
|---|---|---:|---:|---:|---:|
| True | True | 18,152 | 17.9% | 0.00% | -0.32% |
| True | False | 4,179 | 17.7% | -0.05% | -0.62% |
| False | True | 3,670 | 21.6% | 0.00% | -0.04% |
| **False** | **False** | **14,833** | **22.4%** | **+0.19%** | **+0.23%** |

**EVIDENCE:** "Her şey yanlış" (regime=False, direction=False) hücresi en yüksek winner rate'e sahip (%22.4) VE tek pozitif medyan/mean'e sahip. Bu, mevcut regime/direction tanımının **ters çalıştığını** gösteriyor — ya da regime/direction'ın winner tahminiyle ilgisi yok.

### Derinleştirme: regime=False neden daha iyi?

**regime=True aslında ne ölçüyor?** Spearman korelasyonları:

| Feature | ρ vs regime |
|---|---:|
| dist_52w_high | **+0.671** |
| price | +0.289 |
| composite_score | (medyan: T=43, F=9) |
| atr_pct_real | **-0.167** |

**EVIDENCE:** regime=True, "52 haftalık zirveye yakın, pahalı, yüksek skorlu, düşük ATR" hisseleri seçiyor. Bu, momentum'un en uç noktası — ve momentum'un en uç noktası bu veri setinde **en kötü** sonuçları veriyor.

**Matched control:** regime=False vs regime=True (aynı tarih): medyan fark **+0.092pp**, %51.7 pozitif tarih — **anlamlı değil** (şans seviyesinde).

**Aylık stabilite:** regime=False bazı aylarda daha iyi (2026-06: +1.70% vs +0.42%), bazı aylarda daha kötü (2025-10: -1.45% vs -1.21%). **Tutarlı değil.**

**Sonuç:** "regime=False daha iyi" bulgusu **gerçek ama anlamlı değil** — matched control'de fark şans seviyesinde. regime=True'nun daha kötü olması beklenen bir şey (momentum uçları zaten kötü biliniyor), ama regime=False'un "daha iyi" olduğu iddiası desteklenmiyor.

---

## 7. Winner Magnitude Gradienti

| Feature | +5-10% | +10-20% | >20% | Trend |
|---|---:|---:|---:|---|
| ATR% | 4.54 | 5.83 | 7.90 | +3.37 (monoton ↑) |
| RVOL | 0.88 | 0.91 | 0.93 | +0.05 (zayıf ↑) |
| Dist52W | 0.74 | 0.67 | 0.60 | -0.14 (monoton ↓) |
| Lottery | 0.38 | 0.47 | 0.62 | +0.24 (monoton ↑) |
| Price | $41.7 | $26.0 | $10.0 | -$31.7 (monoton ↓) |

**EVIDENCE:** Daha büyük winner'lar daha yüksek ATR, daha yüksek lottery, daha düşük fiyat, daha uzak zirve ile karakterize. Bunlar "riskli, spekülatif, düşük fiyatlı" hisseler.

---

## 8. DERİNLEŞTİRME: Bulgu 1 — entry_ok Kapı Analizi

### Hangi kapı kaç winner öldürüyor?

| Kapı | Killed Winners | % of 8,102 |
|---|---:|---:|
| regime=False | 4,110 | **50.7%** |
| direction=False | 4,057 | **50.1%** |
| ATR/gap/RVOL fail | 2,155 | 26.6% |
| **All gates (entry_ok)** | **5,890** | **72.7%** |

### Kapıları gevşetmek ne olur?

| Konfigürasyon | n | +5% Rate | Median | Mean |
|---|---:|---:|---:|---:|
| Current (all gates) | 9,171 | 24.1% | -1.00% | -1.00% |
| No regime | 11,513 | 24.3% | -0.89% | -0.87% |
| No direction | 11,737 | 23.5% | -1.04% | -1.08% |
| No ATR/gap/RVOL | 18,152 | 17.9% | +0.00% | -0.32% |
| No gates | 40,834 | 19.8% | +0.04% | -0.12% |

**EVIDENCE:** Hiçbir kapıyı gevşetmek genel sonucu anlamlı iyileştirmiyor. "No gates" (tüm evren) medyanı +0.04% — pozitif ama maliyet sonrası negatif. Sorun kapıların varlığı değil, **seçim kriterinin kendisi**.

---

## 9. DERİNLEŞTİRME: Bulgu 2 — ATR×RVOL Sweet Spot Matched Control

| Metrik | Değer |
|---|---|
| Sweet spot (ATR 3-8 × RVOL 0.8-1.5) | n=9,986, +5% rate=25.0%, median=+0.515% |
| Rest of universe | n=30,848, +5% rate=18.2%, median=-0.014% |
| Matched control (same-date random) | median diff=**+0.792pp**, %71.4 pozitif |
| Matched control p-value | **0.286** (anlamlı değil) |
| Day-clustered 95% CI | **[-0.142, +1.186]** (sıfırı kapsıyor) |

**EVIDENCE:** Sweet spot'un matched-control farkı +0.79pp ama p=0.286 — **istatistiksel olarak anlamlı değil**. 72 gün üzerinden bootstrap CI sıfırı kapsıyor. Bu bir **DISCOVERY SIGNAL**, EVIDENCE değil.

**Ama:** Sweet spot'un loser rate'i (%46.4) evrenin (%50.1) altında, big-loser rate'i (%20.2) evrenin (%21.0) altında. Yani sweet spot "daha fazla winner" üretmiyor ama "daha az loser" üretiyor olabilir.

---

## 10. DERİNLEŞTİRME: Bulgu 3 — Score Neden Ayırt Etmiyor?

### Score decile vs outcome

| Decile | n | +5% Rate | Median | Mean |
|---|---:|---:|---:|---:|
| 0 (en düşük) | 4,177 | **22.2%** | +0.00% | +0.21% |
| 1 | 3,432 | **23.9%** | **+0.49%** | **+0.35%** |
| 2 | 3,728 | 21.7% | +0.27% | +0.13% |
| 3 | 4,149 | 20.1% | +0.08% | -0.01% |
| 4 | 3,661 | 16.0% | -0.45% | -1.04% |
| 5 | 3,704 | 17.6% | -0.07% | -0.73% |
| 6 | 3,238 | 17.6% | -0.33% | -1.04% |
| 7 | 3,767 | 19.9% | -0.02% | -0.29% |
| 8 | 3,631 | 18.9% | +0.03% | -0.11% |
| 9 (en yüksek) | 3,627 | 18.4% | -0.16% | -0.30% |

**EVIDENCE:** En yüksek score decile'ı (9) en iyi sonucu VERMİYOR. En iyi decile **1** (ikinci en düşük) — %23.9 winner rate, +0.49% medyan. Score ile sonuç arasında **ters U-şekilli** ilişki var: en düşük ve en yüksek decile'lar orta decile'lardan daha iyi.

### Score neyle korele?

| Feature | ρ vs composite_score |
|---|---:|
| dist_52w_high | **+0.657** |
| price | +0.314 |
| rvol | +0.175 |
| gap_pct | +0.124 |
| atr_pct_real | **-0.207** |

**EVIDENCE:** composite_score esas olarak "52 haftalık zirveye yakınlık" ve "fiyat seviyesi" ölçüyor. ATR ile **negatif** korele — yani yüksek skorlu hisseler daha düşük volatiliteye sahip. Bu, winner'ların yüksek ATR'lı olmasıyla çelişiyor.

### Ne gerçekten winner'ları öngörüyor?

| Feature | ρ vs c2c_5d |
|---|---:|
| lottery_factor | **-0.190** |
| atr_pct_real | **-0.143** |
| price | +0.089 |
| rvol | +0.081 |
| dist_52w_high | +0.048 |
| composite_score | **-0.027** |
| finpilot_score | +0.001 |

**EVIDENCE:** En güçlü bireysel prediktör **lottery_factor** (negatif) ve **ATR** (negatif). Ama bunlar da zayıf (|ρ| < 0.2). Score'lar neredeyse sıfır. **Hiçbir tek feature winner'ı güvenilir öngörmüyor.**

---

## 11. DERİNLEŞTİRME: Bulgu 5 — Kaçırılan Winner Profili

### Hangi kapı kaç winner'ı öldürdü?

| Kapı | Killed | % | Medyan getiri |
|---|---:|---:|---:|
| regime=False | 4,110 | 52.0% | — |
| direction=False | 739 | 9.4% | — |
| ATR/gap/RVOL fail | 988 | 12.5% | — |

### Regime-killed winners (en büyük grup)

| Metrik | Değer |
|---|---|
| n | 591 |
| Medyan getiri | **+10.54%** |
| Ortalama getiri | +14.32% |
| Medyan ATR | 5.74% |
| Medyan fiyat | $13.12 |
| Medyan composite | 22 |
| Medyan dist_52w | 0.550 |

**EVIDENCE:** Regime kapısının öldürdüğü winner'lar ortalama **+14.3%** kazandırmış — captured winner'ların ortalamasından çok daha yüksek. Bunlar ucuz ($13), düşük skorlu (22), zirveden uzak (0.55) hisseler.

### ATR/gap/RVOL-killed winners ("sessiz" winner'lar)

| Metrik | Değer |
|---|---|
| n | 988 |
| Medyan getiri | +6.98% |
| Medyan ATR | 3.08% |
| Medyan RVOL | 0.892 |
| Medyan gap | +0.13% |
| Medyan fiyat | **$95.69** |
| Medyan composite | 46 |

**EVIDENCE:** Bu grup **pahalı, sessiz, düşük volatiliteli** hisseler — ATR<4, |gap|<3%, RVOL<2 ama yine de +7% kazandırmışlar. Bunlar "haber katalizörlü" veya "kurumsal hareket" hisseler olabilir — teknik sinyal olmadan yükselen.

---

## 12. Sentez: Derinleştirme Sonrası Güncellenmiş Resim

### Ne biliyoruz?

1. **entry_ok %97.5 winner kaçırıyor** ama gevşetmek genel sonucu iyileştirmiyor — sorun kapıların varlığı değil, seçim kriterinin kendisi. **EVIDENCE**.
2. **ATR×RVOL sweet spot** var ama matched-control'de anlamlı değil (p=0.286). **DISCOVERY SIGNAL**.
3. **Score winner ayırt etmiyor** çünkü score esas olarak "zirveye yakınlık" ölçüyor, ve zirveye yakınlık bu veri setinde **negatif** prediktör. **EVIDENCE**.
4. **regime=False daha iyi görünüyor** ama matched control'de fark şans seviyesinde. **DISCOVERY SIGNAL**.
5. **Kaçırılan winner'ların en büyük grubu** regime=False tarafından öldürülüyor — ve bunlar en yüksek getiriyi üretmiş (median +10.5%). **EVIDENCE**.

### Ne yapmalıyız?

| Öncelik | Aksiyon | Neden |
|---|---|---|
| 1 | Regime tanımını sorgula — "EMA200 üstü" mü doğru tanım? | En büyük winner kaybı burada |
| 2 | "Sessiz winner" araştırması — haber/katalist tespiti | 988 winner hiçbir teknik sinyal olmadan yükselmiş |
| 3 | ATR×RVOL sweet spot'u yeni veriyle test et | Mevcut veriyle double-dip riski |
| 4 | Lottery_factor'ü score'dan çıkarma simülasyonu | En güçlü bireysel prediktör ama score'da negatif ağırlıklı |
