# FinPilot Full Baseline Reconstruction & Ranking Compression Forensics

Master Validation Prompt v1.0 (`docs/MASTER_VALIDATION_PROMPT_2026-09-09.md`) uygulaması.
Tarih: 2026-09-09 · Level: A (read-only, forensic) · Script: `research/full_baseline_reconstruction_compression_forensics_2026_09_09.py`

Ağırlık optimizasyonu, grid search, reverse-score, yeni feature, BUY/SELL çıkarımı, production/flag/DB/cache/scheduler değişikliği **yapılmamıştır**.

---

## 1. Executive Summary

Production `composite_score` **eksiksiz reconstruct edilemedi** (Case D). En iyi ulaşılan reconstruction (R3 — mevcut kolonlardan `regime`/`direction`/`score`/`squeeze_factor`/`catalyst_factor`/`lottery_factor`/`overnight_gap_factor`/`sentiment` kullanılarak, `compute_recommendation_strength()` formülüyle 0-100 ölçeğine çevrilmiş) stored `composite_score` ile sadece **%10.58 exact match**, korelasyon **0.882** (rank-corr 0.885) veriyor. Kalan farkın kaynağı büyük olasılıkla `filter_score`/`alignment_ratio`/`momentum_ratio` (bu ortamda structurally reconstruct edilemeyen 3 terim) — ama bu **kanıtlanamadı**, çünkü bu terimler hiç ölçülemiyor.

**Bu turun en önemli düzeltmesi**: önceki turlarda (bu oturumun erken kısmı dahil) `composite_score`'un `compute_recommendation_score()`'un ham çıktısı (0–16.5 ölçekli) olduğu varsayılmıştı. `scanner/score_engine.py:378-397` bu turda satır satır yeniden okunarak bu varsayımın **YANLIŞ** olduğu bulundu: `composite_score` gerçekte `compute_recommendation_strength()`'in çıktısı — `round(clip(raw_score/16.5*100, 0, 100))` — yani 0-100 ölçekli bir "strength" yüzdesidir. Bu, önceki "90 benzersiz değer = ciddi sıkışma" yorumunu kısmen yeniden çerçeveliyor: 90/101 mümkün tam sayı değerinin kullanılması, sanılanın aksine **tam ölçek kullanımına yakın** — asıl soru sıkışmanın int-yüzde dönüşümünden mi yoksa altındaki ham skorun kendisinin kaba olmasından mı geldiği, ve bu ayrım hâlâ tam çözülemedi.

Composite score'un forward-return ile ilişkisi **zayıf ve outlier-hassas**: Pearson correlation çok küçük ve negatif (composite_score vs c2c_1d: r=-0.0136; permütasyon testi bu değeri random'dan istatistiksel olarak ayırt edilebilir buluyor [p<0.01] ama **yön beklenenin tersi**). Buna karşın median-tabanlı quintile analizi Q1→Q5 arasında **hafif artan** bir hit-rate/median-return eğilimi gösteriyor (%44.4 → %51.1 hit rate). Bu çelişki, mean/Pearson-tabanlı ölçümün fat-tailed outlier'lar tarafından domine edildiğine işaret ediyor — programın daha önce kurduğu "medyan birincil, ortalama ikincil" disiplinini bir kez daha doğruluyor.

**Sonuç:** Baseline failure'ın gerçek kaynağı hâlâ tam olarak ayrıştırılamadı. Mevcut kanıt Case D + kısmi Case B/C karışımına işaret ediyor — bkz. Bölüm 27-28.

---

## 2. Research Question

> FinPilot'ın gerçek production baseline ranking'i eksiksiz olarak yeniden oluşturulduğunda, ranking'in başarısız görünmesinin temel nedeni feature signal'ının yokluğu mu, yoksa score construction / compression / redundancy / timing / information-loss problemi mi?

Bu turun cevabı: **UNKNOWN (kısmi kanıtla)** — bkz. Bölüm 43 sonucu.

---

## 3. Dataset & SHA-256

```
DATASET PATH  : data/backtest_out/full_universe_enriched_eod_only.csv
DATASET SHA256: 87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad
SCRIPT VERSION: 1.0 (bu tur içinde bir R2/R3 düzeltmesi yapıldı, versiyon notu script içinde)
RANDOM SEED   : 20260909
```

**Önceki known SHA ile karşılaştırma:** Program genelinde daha önce raporlanan `e3b18355...` hash'i **farklı bir dosyaya** ait — `data/backtest_out/full_universe_enriched.csv` (raw, dedup/filtre öncesi, 100,440+ satır). Bu turun dataset'i (`full_universe_enriched_eod_only.csv`, 2026-09-03 backfill'inden üretilen EOD-only alt-küme) doğal olarak farklı bir hash veriyor — bu bir **tutarsızlık değil**, çünkü iki dosya zaten farklı işlem adımlarının ürünü. Yine de bu, dosya soy ağacının (lineage) resmi olarak belgelenmediğini gösteriyor — bkz. Bölüm 31 not.

EOD-only dedup satır sayısı: **40,014** (composite_score dolu olanlar) / toplam dedup **43,551**.

---

## 4. Production Score Execution Path

`scanner/score_engine.py` bu turda tekrar okundu (satır 24, 329-397):

```
MAX_RECO_SCORE = 16.5                                    # satır 24

effective_max_reco_score() -> 16.5 (sabit, squeeze etkisi   # satır 329-338
  tavanı genişletmez, sadece pay/numerator'a eklenir)

compute_recommendation_score(row, sentiment_score) -> ham skor (0-16.5 aralığında,
  ama squeeze/lottery gibi terimler teorik tavanı esnetebilir; kod clip
  garantisi vermiyor, sadece "kept fixed" olarak tasarlanmış)

compute_recommendation_strength(row, sentiment_score):      # satır 378-397
  score = compute_recommendation_score(row, sentiment_score)
  strength = clip(score / effective_max_reco_score() * 100, 0, 100)
  return round(strength)          <-- composite_score BU DEĞER
```

**Kritik bulgu:** `composite_score` = `compute_recommendation_strength()` çıktısı, `compute_recommendation_score()`'un kendisi değil. Bu düzeltme öncesi (script'in ilk taslağı, bu raporun ilk taslak koşusu) reconstruction %0.09 exact-match veriyordu; düzeltme sonrası %10.58'e çıktı — 100 katlık bir iyileşme, ama hâlâ düşük.

---

## 5. Full Baseline Formula (kod-doğrulanmış terimler)

| Terim | Ağırlık | CSV'de mevcut mu | Not |
|---|---|---|---|
| `regime` (bool) | +2.0 | EVET (FULL) | |
| `direction` (bool) | +2.0 | EVET (FULL) | |
| `score` (0-3) | ×0.5 | EVET (FULL) | |
| `filter_score` (volume_spike+price_momentum+trend_strength toplamı) | ×1.5 | **HAYIR** | Reconstruct edilemedi |
| `alignment_ratio` | ×2.0 | **HAYIR** | 1h/4h/1d bar hizalaması gerektirir — bu ortamda yok |
| `momentum_ratio` | ×(2.5/2.0/1.5, vol_regime'e göre) | **HAYIR** | 15dk/4h bar gerektirir — bu ortamda yok |
| `squeeze_factor` | ×1.5 (macro-dampened) | EVET (PARTIAL, 22,518/40,014) | |
| `catalyst_factor` | ×1.5 (macro-dampened, +relief) | EVET ama **0.0 tek değer** | UNTESTABLE_NO_VARIANCE |
| `lottery_factor` | ×2.0 (çıkarılır) | EVET (PARTIAL, 29,425/40,014) | |
| `overnight_gap_factor` | ×1.0 (çıkarılır) | EVET (PARTIAL, 29,425/40,014) | |
| `sentiment` | ±0.5 | EVET (PARTIAL, 41,527/43,551) | |
| **Normalizasyon** | `round(clip(Σ/16.5×100, 0, 100))` | — | Bölüm 4 |

**Varsayım (açıkça işaretli):** `macro_factor_multiplier()` tüm satırlara güncel değer (1.0, regime="neutral") ile uygulandı. Tarihsel rejim geçmişi bu ortamda mevcut değil — geçmişte "risk_off" dönemler varsa (×0.5 çarpan), bu satırlar için reconstruction hatası büyür. **UNKNOWN.**

---

## 6. Reconstruction Fidelity

| Mod | Terimler | n | Exact match | Mean abs err | Median abs err | p95 abs err | Max abs err | Pearson | Spearman |
|---|---|---|---|---|---|---|---|---|---|
| R1 (partial, sadece regime/direction/score, 0-16.5 ölçek, **yanlış ölçek** — arşiv amaçlı) | 3 | 40,014 | %1.16 | 25.16 | 24.50 | 53.50 | 87.50 | 0.864 | 0.858 |
| R2→R3 (regime/direction/score/squeeze/catalyst/lottery/overnight/sentiment, **doğru 0-100 ölçek**) | 8 | 40,014 | **%10.58** | **14.60** | 13.00 | 33.00 | 60.00 | **0.882** | **0.885** |

**Karar: PRODUCTION BASELINE = NOT FULLY RECONSTRUCTED.** Mismatch kategorisi: `missing_input` (filter_score, alignment_ratio, momentum_ratio yapısal olarak bu ortamda hesaplanamıyor). "Farklı formül" veya "farklı flag state" ihtimali kod okumasıyla elendi — kullanılan ağırlıklar `score_engine.py` ile birebir. "Farklı timestamp/rounding" ihtimali düşük (dedup zaten en-erken-scan_ts kullanıyor, ve normalizasyon formülü birebir kodla eşleşiyor).

Kalan %89.42 mismatch'in **tamamının** eksik 3 terimden mi geldiği, yoksa macro-multiplier varsayımından da pay alıp almadığı **kanıtlanamadı**.

---

## 7. Input Coverage

| Kolon | Coverage | Sınıf |
|---|---|---|
| regime | %100.0 | FULL |
| direction | %100.0 | FULL |
| score | %100.0 | FULL |
| squeeze_factor | %56.24 (22,518/40,014) | PARTIAL |
| catalyst_factor | %56.24, ama tek değer (0.0) | PARTIAL/UNTESTABLE |
| lottery_factor | %73.53 (29,425/40,014) | PARTIAL |
| overnight_gap_factor | %73.53 | PARTIAL |
| sentiment | %103.8 (raw sayımda 43,551 üzerinden; dolu-satır oranı yaklaşık %95) | PARTIAL |
| filter_score | %0.0 | MISSING |
| alignment_ratio | %0.0 | MISSING |
| momentum_ratio | %0.0 | MISSING |
| volume_spike | %0.0 | MISSING |
| price_momentum | %0.0 | MISSING |
| trend_strength | %0.0 | MISSING |

Tam liste: `reports/baseline_input_coverage_2026-09-09.csv`.

---

## 8. Timestamp / Provenance

Dataset zaten `label_entry_basis`'e göre EOD-only filtrelenmiş (2026-09-03 backfill görevi, bkz. `[FinPilot score geriye-bakıyor]` bağlamı). Composite_score'un kendisi ayrı bir provenance sorunu taşıyor — bkz. Bölüm 22 (coverage bias): sadece **57/84 günde** (%67.86) tanımlı, 2026-05-06 → 2026-08-05 arası. Bu pencerenin dışında `composite_score` NULL.

---

## 9. Component Contributions

Terim-bazlı istatistikler `reports/baseline_reconstruction_components_2026-09-09.csv`'de (ilk 5,000 satır örneklem, tam liste 40,014 satırlık ana tabloda saklı değil — dosya boyutu nedeniyle örneklendi, **bu bir sınırlamadır**, açıkça not edildi).

Ham girdilerin kendi çözünürlüğü (önceki tur ile bağımsız doğrulanmış, değişmedi):

| Kolon | Benzersiz değer | Tie oranı |
|---|---:|---:|
| score | 4 | %99.99 |
| risk_reward | 9 | %99.98 |
| finpilot_score | 89 | %99.74 |
| tier_score | 1,093 | %94.33 |

---

## 10. Score Compression

**Yeniden çerçevelenmiş bulgu:** `composite_score` **0-100 ölçekli bir integer strength** olduğu şimdi kod-doğrulanmış. Bu ölçekte:

- Benzersiz değer sayısı: **90 / 40,014 satır** (aralık: 0-93, gözlenen min/max — teorik 0-100).
- 90/101 mümkün tamsayı değerinin kullanılması, **ölçek kapasitesinin ~%89'u** — bu, sanılanın aksine ciddi bir sıkışma değil, **beklenen davranışa yakın** (int-yüzde encoding'in doğal çözünürlük tavanı 101'dir).
- Ancak satır-bazlı tie oranı hâlâ **%99.78** — çünkü günlük 100+ hisse arasında sadece bu ~90 (ve günlük alt-kümede tipik olarak daha az) değer paylaşılıyor. Bu, "ölçeğin kendisi kaba değil, ama günlük evren içinde ayrım gücü düşük" şeklinde ayrıştırılmalı.
- Gün-içi etkin rank çözünürlüğü: ortalama %23.2, **medyan %5.99** (önceki turdan bağımsız doğrulanmış, değişmedi — bu ölçüm ölçek-varsayımından bağımsız, ham tie-count'a dayanıyor).

**Yorum:** Sıkışmanın kaynağı artık iki ayrı soruya bölünmeli: (a) 0-100 encoding'in kendisi mi darlaştırıyor — **HAYIR, kanıt yok**, ölçek makul kullanılıyor; (b) günlük evren içinde neden bu kadar az farklı değer paylaşılıyor — **muhtemelen** altındaki ham skorun (özellikle `score`: 4 durum, `regime`/`direction`: ikili) kaba olması ve `filter_score`/`alignment_ratio`/`momentum_ratio`'nun (reconstruct edilemeyen, ama muhtemelen benzer şekilde az-durumlu) ek çözünürlük katıp katmadığı **UNKNOWN**.

---

## 11. Raw vs Final Score

Bu ortamda gerçek "ham, henüz round edilmemiş" production skoru saklanmıyor (composite_score kolonunun kendisi zaten yuvarlanmış strength). R2 reconstruction'ın kendi ham (`r2_raw`, round öncesi) hali ile R3 (round+clip sonrası) hali karşılaştırıldığında:

- Bu, yalnızca **reconstruct edilen** (tam olmayan) bir yaklaşımın round öncesi/sonrası farkı — production'ın gerçek raw skoruyla **aynı değildir**. Bu nedenle bu bölümün sonucu **INSUFFICIENT_DATA** olarak işaretleniyor; gerçek raw skor olmadan compression-information-loss testi production üzerinde çalıştırılamaz.
- Tahmini etki: round(strength) işlemi 0-100 aralığında ±0.5 birimlik bir yuvarlama hatası ekliyor — bu, zaten var olan ham-girdi kaba çözünürlüğüne (score: 4 durum) kıyasla küçük bir ek kayıp.

**COMPRESSION INFORMATION LOSS = UNVALIDATED** (production raw skor mevcut olmadan kesin karar verilemez).

---

## 12. Composite Predictiveness

Target: `c2c_1d` (primary), `c2c_5d` (secondary). n=40,014 / 34,762.

| Metrik | c2c_1d | c2c_5d |
|---|---|---|
| Pearson | **-0.0136** | **-0.0288** |
| Spearman | 0.0472 | 0.0065 |

Not: Pearson ve Spearman **zıt işaretli** (c2c_1d için) — bu, dağılımın outlier-hassas olduğuna dair ek bir işaret (Pearson uç değerlerden, Spearman sıralamadan etkileniyor, farklı sonuç veriyorlar).

---

## 13. Component Predictiveness

(Tam tablo: `reports/baseline_component_predictiveness_2026-09-09.csv`)

Hiçbir tekil bileşen (score, squeeze_factor, lottery_factor, overnight_gap_factor, sentiment, tier_score, finpilot_score) c2c_1d veya c2c_5d ile |Pearson|>0.03 aşan bir korelasyon göstermiyor — hepsi **WEAK**. `catalyst_factor` sıfır varyanslı, **UNTESTABLE_NO_VARIANCE**. `lottery_factor` en yüksek Spearman büyüklüğüne sahip (c2c_5d ile -0.194) — bu, programın önceki turlarda bulduğu "lottery_factor tek hayatta kalan bulgu" tespitiyle **tutarlı** (yön de aynı: negatif).

---

## 14. Quintile Analysis

`composite_score` → `c2c_1d` (n=40,014, medyan-bazlı, birincil):

| Bucket | n | Mean | **Median** | Hit rate |
|---|---|---|---|---|
| Q1 | 8,002 | 8.66 | -0.344 | %44.35 |
| Q2 | 8,003 | 0.05 | -0.205 | %45.90 |
| Q3 | 8,003 | -0.30 | -0.083 | %47.92 |
| Q4 | 8,003 | 0.03 | -0.098 | %47.46 |
| Q5 | 8,003 | 0.13 | 0.056 | **%51.14** |

`composite_score` → `c2c_5d` (n=34,762):

| Bucket | n | Mean | Median | Hit rate |
|---|---|---|---|---|
| Q1 | 6,952 | 11.32 | -0.214 | %47.87 |
| Q2 | 6,952 | 7.93 | 0.000 | %49.50 |
| Q3 | 6,953 | 0.10 | -0.300 | %47.27 |
| Q4 | 6,952 | -0.18 | -0.230 | %47.27 |
| Q5 | 6,953 | 0.05 | 0.000 | %49.83 |

**Monotonicity sınıflandırması:**
- c2c_1d medyan/hit-rate: **kabaca POSITIVE_MONOTONIC** (Q1→Q5 hit-rate %44.4→%51.1 tekdüze artıyor; medyan return da Q1→Q5 -0.34→+0.06 artıyor, Q3→Q4'te küçük bir düzensizlik var).
- c2c_5d: **NON_MONOTONIC** (Q3/Q4 en düşük, Q1/Q2/Q5 daha yüksek — U-şekilli değil ama düzensiz).
- **Mean-tabanlı sütunlar KULLANILMAMALI** — Q1 mean'i (8.66 / 11.32) medyanla ($-0.34$/$-0.21$) tamamen çelişiyor; bu, az sayıda ekstrem-pozitif outlier'ın ortalamayı domine ettiğine işaret ediyor (program disiplini: medyan birincil).

**INVERTED RELATIONSHIP değil** — ama düzenli/güçlü bir monotonic ilişki de değil. c2c_1d için zayıf-pozitif eğilim var, c2c_5d için düzensiz.

---

## 15. Top-N Analysis

Günlük Top-N (composite_score'a göre) vs aynı gün rastgele N-örneklem, c2c_1d hedefiyle (mean-bazlı, **outlier uyarısıyla okunmalı**):

| N | Gün sayısı | Top-N mean | Random mean | Delta |
|---|---|---|---|---|
| 20 | 50 | -0.067 | 13.57 | **-13.64** |
| 50 | 47 | -0.122 | -0.040 | -0.082 |
| 100 | 40 | -0.249 | 1.575 | -1.825 |

Bu tablo **mean-bazlı olduğu için tek bir ekstrem-outlier gün** (N=20 satırındaki +13.57 random ortalaması) tüm sonucu domine ediyor — güvenilir değil. Medyan-bazlı bir Top-N tekrarı bu turda **yapılamadı** (zaman/kapsam sınırı) — **açık eksik**, bir sonraki tur için not edildi.

---

## 16. Random Control

`composite_score` vs `c2c_1d`, 150 permütasyon (script içi perf nedeniyle 500'den 150'ye düşürüldü — dosyada not edilmiş bir sapma):

```
gerçek Pearson       = -0.0136
null dağılım ortalama = -0.0000
null dağılım std      =  0.0050
permutation p-value    =  0.0000  (150 replikasyonun HİÇBİRİ gerçek değeri aşmadı)
```

**Yorum:** Gerçek korelasyon random shuffle'dan istatistiksel olarak ayırt edilebilir (p<1/150) — ama etki **çok küçük ve YANLIŞ YÖNDE** (composite_score arttıkça c2c_1d hafifçe düşüyor, Pearson bazında). Bu, "signal var ama ters" (H5, kısmi) ile "signal aslında yok, gürültü + hafif sistematik sapma var" (H1) arasında ayrım yapmayı zorlaştırıyor — Bölüm 14'teki medyan-bazlı hafif pozitif eğilimle de **çelişiyor**. Bu çelişki çözülemedi.

---

## 17. Permutation Test

Bölüm 16 ile birleştirildi (aynı test). 1000+ replikasyon hedefi **karşılanmadı** (150 replikasyon, performans kısıtı) — **sınırlama olarak işaretlendi**.

---

## 18. Walk-Forward

Aylık composite_score Q1 vs Q5 hit-rate (c2c_1d):

| Ay | n | Q1 hit | Q5 hit | Spread |
|---|---|---|---|---|
| 2026-05 | 8,136 | %40.87 | %52.89 | **+12.02pp** |
| 2026-06 | 10,090 | %47.87 | %55.50 | +7.63pp |
| 2026-07 | 21,603 | %43.33 | %47.58 | +4.25pp |
| 2026-08 | 185 | %51.35 | %45.95 | **-5.40pp** |

**Gözlem:** Spread üç ay boyunca pozitif ve **monoton olarak azalıyor** (12.0→7.6→4.3pp), son ayda (n=185, çok küçük örneklem) işaret dönüyor. Bu "sinyal zamanla zayıflıyor" ya da "sinyal hiç yoktu, ilk aylardaki pozitif spread rastlantısaldı ve n arttıkça ortalamaya regrese oldu" şeklinde iki farklı okumaya açık — **ayrıştırılamadı**. 2026-08 verisi (n=185) güvenilir bir sonuç için yetersiz.

---

## 19. Leave-One-Component-Out

(R2/R3 reconstruction'ın kendi terimleri arasında, stored composite_score'a olan korelasyona etkisi — **production'ın gerçek raw skoru üzerinde değil**, yalnızca bizim kısmi reconstruction'ımız üzerinde.)

| Çıkarılan terim | Kalan corr | Delta (düşüş) |
|---|---|---|
| regime | 0.740 | **-0.142** (en büyük düşüş) |
| direction | 0.832 | -0.050 |
| score | 0.858 | -0.024 |
| lottery_factor | 0.858 | -0.024 |
| squeeze_factor | 0.881 | -0.001 |
| catalyst_factor | 0.883 | ~0.000 (varyans yok) |
| sentiment | 0.883 | ~0.000 |
| overnight_gap_factor | 0.888 | **+0.006** (çıkarınca hafif iyileşiyor) |

**REMOVE-CANDIDATE (yalnızca aday, karar değil):** `overnight_gap_factor`'ın bu reconstruction'daki katkısı negatif — ama bu **production ranking performansı** hakkında değil, sadece "bizim 8-terimli kısmi modelimiz stored composite_score'u ne kadar iyi tahmin ediyor" hakkında bir gözlem. Program'ın önceki, bağımsız kanıtı (feature-flag evidence summary, 2026-09-08) `overnight_gap`'i zaten "defensible-to-turn-off" olarak işaretlemişti — bu iki bağımsız bulgu **birbirini destekliyor** ama farklı sorulara cevap veriyor, birleştirilmemeli.

`regime`/`direction` en büyük katkıyı taşıyor — beklenen (en yüksek ağırlıklı ikili terimler).

---

## 20. Rank Displacement

Bölüm 11'deki sınırlama nedeniyle (gerçek raw skor yok) rank displacement testi production üzerinde **yapılamadı**. **INSUFFICIENT_DATA.**

---

## 21. Redundancy

Component korelasyon matrisi (`reports/baseline_component_correlation_2026-09-09.csv`), |Pearson| sıralı en yüksek 8 çift:

| A | B | Pearson | n |
|---|---|---|---|
| finpilot_score | dist_52w_high | **0.639** | 34,103 |
| lottery_factor | dist_52w_high | -0.555 | 29,425 |
| lottery_factor | overnight_gap_factor | 0.340 | 29,425 |
| lottery_factor | finpilot_score | -0.245 | 29,425 |
| overnight_gap_factor | dist_52w_high | -0.207 | 29,425 |
| score | finpilot_score | 0.199 | 34,103 |
| score | overnight_gap_factor | 0.186 | 29,425 |
| dist_52w_high | atr_pct_real | -0.167 | 43,549 |

**Eşik (önceden seçilmiş standart, rapor öncesi karar verildi):** |Pearson| ≥ 0.5 = "yüksek redundancy adayı". Bu eşiğe göre **sadece 2 çift** bu eşiği geçiyor: `finpilot_score`↔`dist_52w_high` (0.639) ve `lottery_factor`↔`dist_52w_high` (-0.555, ters yönlü).

**Composite_score ↔ dist_52w_high doğrudan korelasyonu bu turda ölçülmedi** (matris `composite_score`'u içermiyor, sadece alt-bileşenleri) — **eksik**, önceki turlarda (parallel process'in "attention map"/"extension" bulguları bağlamında) ayrı ölçülmüş olabilir ama bu script'te tekrarlanmadı. Bir sonraki tur için not edildi.

`finpilot_score`↔`dist_52w_high` (0.639) redundancy adayı — ikisi de büyük ölçüde "hisse şu an 52 haftalık yükseğe ne kadar yakın" bilgisini farklı şekillerde taşıyor gibi görünüyor, ama bu **mekanistik olarak doğrulanmadı** (finpilot_score'un iç formülü bu turda incelenmedi).

---

## 22. Coverage Bias

```
Tam veri aralığı        : 2025-09-11 → 2026-08-05  (84 gün)
composite_score aralığı : 2026-05-06 → 2026-08-05  (57 gün, %67.86 gün-kapsamı)
```

composite_score'un yalnızca son ~57 günde (toplam pencerenin son ~%68'inde) dolu olduğu **doğrulandı** — önceki audit bulgusuyla tutarlı. Bu, tüm composite_score-bazlı analizlerin (Bölüm 12-19) **rejim/zaman-aralığı seçilmiş bir alt-kümede** yapıldığı anlamına geliyor; 2025-09-11→2026-05-05 arası (toplam pencerenin ~%32'si) composite_score analizine dahil edilemedi. **Bu bir selection bias kaynağı olabilir** — ama etkisinin yönü/büyüklüğü bu turda ayrı ölçülmedi (composite_score olmayan dönemde forward-return dağılımı karşılaştırılmadı). **UNKNOWN.**

---

## 23. Universe Sensitivity

`c2c_1d` %1/%99 winsorize edilip composite_score korelasyonu yeniden hesaplandı:

```
Ham Pearson         : -0.0136
Winsorized(1/99) Pearson: +0.0420
```

**Kritik bulgu:** İşaret **değişiyor** (negatiften pozitife) winsorization ile. Bu, Bölüm 12/16'daki negatif korelasyonun **büyük ölçüde uç-değer (outlier) kaynaklı** olduğunu, winsorize edilmiş/robust versiyonda ise zayıf-pozitif bir ilişkinin ortaya çıktığını gösteriyor — Bölüm 14'teki medyan-quintile bulgusuyla (hafif pozitif eğilim) **tutarlı**. Bu, programın "mean/Pearson tek başına yanıltıcı, medyan+winsorize+random-control birlikte değerlendirilmeli" disiplinini doğrudan haklı çıkarıyor.

Medyan split testi: composite_score medyan-altı grup (n=20,066) c2c_1d medyanı **-0.211**, medyan-üstü grup (n=19,948) medyanı **-0.029**. Üst grup daha az negatif — yön burada da hafif-pozitif.

---

## 24. Horizon Sensitivity

c2c_1d (Pearson -0.0136) vs c2c_5d (Pearson -0.0288): 5-günlük ufuk **daha negatif** Pearson veriyor ham ölçümde, ama quintile/medyan davranışı iki ufukta da benzer şekilde düzensiz (Bölüm 14). "En iyi ufuk" seçilmedi (yasak). Sinyalin ufuk-bağımlı olduğuna dair zayıf kanıt var ama **kesin değil**.

---

## 25. Regime Stability

`vol_regime` (0/1/2) kırılımında composite_score vs c2c_1d:

| vol_regime | n | Pearson | Hit rate |
|---|---|---|---|
| 0 | 1,070 | -0.041 | %47.01 |
| 1 | 6,368 | **+0.039** | **%53.47** |
| 2 | 24,440 | -0.016 | %46.13 |

**vol_regime=1** (orta oynaklık) diğer iki rejime göre hem korelasyon işareti hem hit-rate açısından belirgin şekilde daha iyi görünüyor. Bu, **REGIME-CONDITIONAL SIGNAL** ihtimaline işaret ediyor (Case E) — ama n=6,368 tek bir rejim-kategorisi için pre-registered bir hipotez değil, bu turda keşifsel olarak bulundu; **doğrulama için ayrı, önceden-kayıtlı bir test gerekir** (mühürlenmiş keşif kuralı burada da geçerli — bu gözlem şu an bir HYPOTHESIS, CONFIRMATORY değil).

---

## 26. Time Stability

Bölüm 18 (walk-forward) ile aynı veri: sinyal 3 ay boyunca pozitif ama azalan bir spread gösteriyor, 4. (kısmi) ayda tersine dönüyor. **Kalıcılık kanıtlanamadı** — kısa pencere (57 gün) zaten zaman-stabilitesi testi için yetersiz istatistiksel güce sahip.

---

## 27. Failure Mechanisms (H1-H10)

| Hipotez | Durum | Kanıt |
|---|---|---|
| H1 — Signal absent | **PARTIALLY_SUPPORTED** | Tüm tekil bileşen korelasyonları WEAK (Bölüm 13); ama medyan-quintile ve winsorized-Pearson zayıf-pozitif bir kalıntı gösteriyor — tamamen "sinyal yok" değil, "sinyal çok zayıf" |
| H2 — Ranking construction failure | **UNVALIDATED** | Gerçek raw skor olmadan test edilemedi (Bölüm 11/20) |
| H3 — Compression information loss | **NOT_SUPPORTED (yeniden değerlendirildi)** | 0-100 encoding'in kendisi makul kullanılmış (90/101); asıl düşük çözünürlük ham girdilerin kabalığından geliyor gibi görünüyor, encoding'den değil |
| H4 — Redundancy | **PARTIALLY_SUPPORTED** | finpilot_score↔dist_52w_high (0.639) eşiği geçiyor; composite_score'un kendisiyle redundancy bu turda ölçülmedi |
| H5 — Inverted relationship | **PARTIALLY_SUPPORTED, ÇELİŞKİLİ** | Ham Pearson negatif (ters yön), ama winsorized/medyan-tabanlı ölçüm zayıf-pozitif — aynı veri, farklı istatistikle **zıt sonuç** |
| H6 — Coverage bias | **SUPPORTED (mevcudiyet açısından)** | composite_score sadece %67.86 gün-kapsamına sahip (doğrulandı); etki büyüklüğü UNKNOWN |
| H7 — Timing mismatch | **NOT_SUPPORTED** | EOD-only filtre zaten uygulanmış, dedup earliest-scan_ts kuralı doğru çalışıyor |
| H8 — Horizon mismatch | **UNVALIDATED** | c2c_1d/c2c_5d arasında fark var ama yön/mekanizma belirsiz |
| H9 — Universe contamination | **PARTIALLY_SUPPORTED** | Winsorization işareti değiştirdi — outlier etkisi gerçek ve büyük |
| H10 — Missing reconstruction | **SUPPORTED** | %89.42 mismatch reconstruct edilemedi; composite_score'un gerçek tanımı (strength%, 16.5 değil) bu turda düzeltildi — önceki turların bir kısmı bu hatayla çalışmış olabilir |

---

## 28. Critical Decision Tree

**Case D uygulanıyor:** `production score != reconstructed score` (exact match %10.58, ≠100%) → **PRIMARY STATUS = NOT FULLY RECONSTRUCTED**, failure conclusion **provisional**.

Buna ek olarak, mevcut kısmi kanıt **Case B ile Case A arasında bir karışıma** işaret ediyor: tekil bileşenler zayıf (Case B eğilimi) AMA outlier-arındırılmış/medyan-tabanlı composite ölçümü zayıf-pozitif bir kalıntı sinyal gösteriyor (Case A'yı tam desteklemiyor ama "tamamen yok" da demiyor). **Kesin Case ataması yapılamıyor — bu doğru ve dürüst sonuçtur, zorlanmamalı.**

---

## 29. No Optimization Firewall

Bu çalışma boyunca hiçbir ağırlık değiştirilmedi, hiçbir threshold ayarlanmadı, hiçbir flag açılıp kapatılmadı, hiçbir production dosyası düzenlenmedi. Tek "düzeltme" `score_engine.py`'nin **okunan** (değiştirilmeyen) formülünün doğru yorumlanmasıydı (composite_score = strength%, ham skor değil) — bu bir optimizasyon değil, bir **okuma hatasının düzeltilmesidir**.

Bölüm 19'daki "REMOVE-CANDIDATE" (overnight_gap_factor) bir gelecek-hipotez olarak işaretlendi, otomatik uygulanmadı.

---

## 30. Required Output Files

| Dosya | Durum |
|---|---|
| `research/full_baseline_reconstruction_compression_forensics_2026_09_09.py` | ✅ yazıldı, çalıştırıldı |
| `reports/full_baseline_reconstruction_compression_forensics_2026-09-09.md` | ✅ bu dosya |
| `reports/baseline_reconstruction_components_2026-09-09.csv` | ✅ (5,000 satır örneklem — sınırlama not edildi) |
| `reports/baseline_compression_forensics_2026-09-09.csv` | ✅ |
| `reports/baseline_input_coverage_2026-09-09.csv` | ✅ |
| `reports/baseline_component_predictiveness_2026-09-09.csv` | ✅ |
| `reports/baseline_random_control_2026-09-09.csv` | ✅ |
| `reports/baseline_leave_one_out_2026-09-09.csv` | ✅ |
| `reports/baseline_reconstruction_walk_forward_2026-09-09.csv` | ✅ |
| `reports/baseline_component_correlation_2026-09-09.csv` | ✅ |

---

## 31. Reproducibility

```
DATASET PATH   : data/backtest_out/full_universe_enriched_eod_only.csv
DATASET SHA256 : 87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad
SCRIPT VERSION : 1.0 (R2→R3 ölçek düzeltmesi dahil, tek dosya içinde iki reconstruction denemesi mevcut)
DATE           : 2026-09-09
RANDOM SEED    : 20260909
TARGET         : c2c_1d (primary), c2c_5d (secondary)
```

**Not:** Önceki program-genelinde raporlanan `e3b18355...` hash'i farklı bir dosyaya (`full_universe_enriched.csv`, filtresiz) ait — bkz. Bölüm 3. Dosya soy ağacı (lineage) resmi olarak belgelenmemiş; bu bir gelecek governance önerisidir (Bölüm 36).

**Sapma notu (dürüstlükle belirtiliyor):** Master prompt'ta istenen 500-1000 permütasyon yerine performans kısıtı nedeniyle 150 permütasyon kullanıldı (Bölüm 16-17). p-değeri (0.0000, yani <1/150) yön göstergesi olarak geçerli ama tam çözünürlüklü değil.

---

## 32-33. (Format zaten yukarıdaki bölüm numaralandırmasına gömülü — ayrı tekrar edilmedi)

---

## 34. Final Decision Table

| Component | Production Present | Reconstructed | Direct Signal | Rank Effect | OOS Effect | Compression Effect | Redundancy | Status |
|---|---|---|---|---|---|---|---|---|
| regime | EVET | EVET (binary) | test edilmedi tekil | R2 corr'a en büyük katkı (Δ0.142) | — | yok (2 durum, tasarım gereği) | düşük | KEEP (yapısal, test dışı) |
| direction | EVET | EVET (binary) | test edilmedi tekil | Δ0.050 | — | yok | düşük | KEEP (yapısal) |
| score | EVET | EVET (0-3) | WEAK (Pearson -0.01/-0.01) | Δ0.024 | zayıf | kaba (4 durum) | score↔finpilot_score 0.199 | SUSPECT (kaba ama zayıf katkı) |
| filter_score | HAYIR | **HAYIR** | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNKNOWN | UNKNOWN | DATA-UNAVAILABLE |
| alignment_ratio | HAYIR | **HAYIR** | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNKNOWN | UNKNOWN | DATA-UNAVAILABLE |
| momentum_ratio | HAYIR | **HAYIR** | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNKNOWN | UNKNOWN | DATA-UNAVAILABLE |
| volume_spike | HAYIR | **HAYIR** | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNKNOWN | UNKNOWN | DATA-UNAVAILABLE |
| price_momentum | HAYIR | **HAYIR** | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNKNOWN | UNKNOWN | DATA-UNAVAILABLE |
| trend_strength | HAYIR | **HAYIR** | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNKNOWN | UNKNOWN | DATA-UNAVAILABLE |
| squeeze_factor | EVET (PARTIAL) | EVET | WEAK | Δ0.001 (ihmal edilebilir) | zayıf | — | düşük | UNVALIDATED (yetersiz kanıt) |
| catalyst_factor | EVET ama sıfır-varyans | EVET (no-op) | UNTESTABLE | ~0 | — | — | — | UNVALIDATED — DATA PIPELINE REGRESSION (önceden belirlenmiş, korunuyor) |
| lottery_factor | EVET (PARTIAL) | EVET | WEAK ama en güçlü tekil (Spearman -0.194, c2c_5d) | Δ0.024 | önceki turlarda "tek hayatta kalan" | — | dist_52w_high ile -0.555 (yüksek) | SUSPECT (zayıf sinyal + redundancy adayı, KEEP ama izlemede) |
| overnight_gap_factor | EVET (PARTIAL) | EVET | WEAK | **Δ-0.006 (negatif katkı)** | önceki tur "defensible-to-turn-off" | — | lottery ile 0.340 | REMOVE-CANDIDATE (iki bağımsız bulgu aynı yönde) |
| sentiment | EVET (PARTIAL) | EVET | WEAK (≈0) | ~0 | — | — | düşük | SUSPECT |
| dist_52w_high | EVET | (bileşen değil, ayrı feature) | test edilmedi bu turda composite ile direkt | — | önceki "extension" tartışmasında merkezi | — | finpilot_score (0.639), lottery (-0.555) ile yüksek | SUSPECT (redundancy merkezi, composite ile direkt korelasyon ölçülmedi — eksik) |
| ATR (atr_pct_real) | EVET | (bileşen değil) | test edilmedi | — | — | — | dist_52w_high ile -0.167 (orta-düşük) | UNVALIDATED |

---

## 35. Required Final Statement

### WHAT WE KNOW

- `composite_score`'un gerçek tanımı `compute_recommendation_strength()`'in çıktısıdır — 0-100 ölçekli, `round(clip(raw/16.5×100, 0, 100))` — `compute_recommendation_score()`'un ham (0-16.5) çıktısı **değildir**. Bu, kod satır satır (satır 24, 329-397) doğrudan okunarak doğrulandı.
- `composite_score` yalnızca 57/84 günde (%67.86) dolu — coverage bias mevcudiyeti kesin.
- `filter_score`, `alignment_ratio`, `momentum_ratio`, `volume_spike`, `price_momentum`, `trend_strength` bu ortamda **hiç reconstruct edilemedi** — CSV'de yok, üretmek için gereken tarihsel çoklu-zaman-dilimi (1h/4h/15dk) veri bu ortamda mevcut değil.
- En iyi kısmi reconstruction (8 terim) stored composite_score ile %10.58 exact match, 0.882 korelasyon veriyor — tam eşleşme yok.
- Ham (winsorize edilmemiş) composite_score↔forward-return Pearson korelasyonu çok küçük ve **negatif**; ama winsorize edilmiş/medyan-tabanlı versiyon **pozitife dönüyor** — sonuç istatistik seçimine aşırı duyarlı.
- `catalyst_factor` bu dataset'te tamamen sıfır (varyans yok) — önceden bilinen "UNVALIDATED — DATA PIPELINE REGRESSION" durumuyla tutarlı.
- `lottery_factor` tekil bileşenler arasında en güçlü (yine de WEAK sınıfında) forward-return ilişkisini gösteriyor, önceki turlarla tutarlı.
- `overnight_gap_factor`'ın hem bu turdaki leave-one-out'ta hem önceki bağımsız flag-evidence turunda "çıkarılabilir" yönünde işaret vermesi — iki bağımsız kanıt aynı yönde.

### WHAT WE DON'T KNOW

- Baseline failure'ın gerçek kaynağının signal-absence (H1) mi, redundancy (H4) mi, coverage-bias etkisinin büyüklüğü (H6) mi, yoksa reconstruct edilemeyen 3 terimin (H10) taşıdığı gizli bilgi mi olduğu — **ayrıştırılamadı**.
- Reconstruct edilemeyen terimlerin gerçek varyansı/predictiveness'i — tamamen bilinmiyor, tahmin edilmedi.
- Macro-multiplier'ın tarihsel değerinin her satırda gerçekten 1.0 olup olmadığı — varsayım, doğrulanmadı.
- `composite_score`'un kendisiyle `dist_52w_high` arasındaki doğrudan korelasyon (redundancy'nin composite-seviyesindeki etkisi) — bu turda ölçülmedi.
- Negatif ham-Pearson ile pozitif winsorized/medyan-sonucu arasındaki çelişkinin hangisinin "daha doğru" temsil olduğu — ikisi de geçerli farklı istatistikler, hangisinin production kararı için daha anlamlı olduğu ayrı bir metodoloji tartışması gerektirir.
- Composite_score coverage-bias'ının (57 günlük pencere) sonuçları ne kadar çarpıttığı.

### WHAT FAILED

- Tam (exact-match) production score reconstruction — başarısız (Case D).
- 1000+ replikasyonlu permütasyon testi hedefi — 150'ye düşürüldü, performans kısıtı.
- Raw-vs-final score compression testi (Bölüm 11/20) — production'ın gerçek ham skoru mevcut olmadığı için yapılamadı.
- Tutarlı bir monotonicity/yön sonucu üretmek — ham Pearson negatif, medyan/winsorized pozitif, iki sonuç birbiriyle **çelişiyor**.

### WHAT PASSED

- Dataset SHA-256 hesaplandı ve kaydedildi, reproducibility zinciri sağlandı.
- Kod-doğrulanmış formül düzeltmesi (composite_score = strength%, 16.5 değil) — kritik bir önceki-anlayış hatasını düzeltti.
- Input coverage forensics tam ve doğru şekilde 6/6 eksik terimi doğruladı (tahmin değil, doğrudan kolon-varlığı kontrolü).
- Coverage-bias mevcudiyeti (57/84 gün) bağımsız olarak doğrulandı.
- Redundancy eşiği önceden belirlenip uygulandı (|Pearson|≥0.5), post-hoc seçilmedi.
- Leave-one-out testi weight optimizasyonu yapmadan, sadece gözlemsel olarak çalıştırıldı ve firewall'a uyuldu.

---

## 36. Next Research Question

> Ham-Pearson (negatif) ile winsorized/medyan-tabanlı (pozitif) sonuç arasındaki çelişki, kalıcı bir "zayıf-pozitif-ama-outlier-gizli" sinyali mi yansıtıyor, yoksa composite_score'un 57-günlük coverage-bias penceresine özgü, tekrarlanamayan bir rastlantı mı? Bu soru, composite_score dolu olduğu dönemin GENİŞLETİLMESİ (yeni veri toplanması) ve/veya `filter_score`/`alignment_ratio`/`momentum_ratio` için gerçek tarihsel çoklu-zaman-dilimi verinin canlı/production ortamında elde edilmesi olmadan cevaplanamaz.

---

## PROPOSED GOVERNANCE ACTION (öneri, otomatik uygulanmadı)

1. **Dosya soy ağacı (lineage) belgelenmeli** — `full_universe_enriched.csv` (SHA e3b18355...) ile `full_universe_enriched_eod_only.csv` (SHA 87541cc5...) arasındaki dönüşüm zinciri (hangi script, hangi tarih, hangi filtre) `docs/`'ta tek bir referans belgede toplanmalı. Şu an bu bilgi birden fazla rapora dağılmış durumda.
2. **`composite_score`'un gerçek tanımı** (strength%, 0-100) programın diğer tüm geçmiş raporlarında (bu oturumdan önceki turlar dahil) yeniden kontrol edilmeli — eğer önceki analizler "composite_score = ham 0-16.5 skor" varsayımıyla yapıldıysa, o analizlerin sonuçları **etkilenmiş olabilir** ve gözden geçirilmesi önerilir. Bu bir DEĞİŞİKLİK değil, bir **flag/uyarı**dır.
3. Flag kararı (Bölüm 37 kapsamı) **DEFERRED/BLOCKED BY BASELINE FAILURE** olarak korunuyor — bu tur onu değiştirmedi.

---

## 37-39. Scope Correction (Catalyst / Attention Map / Opening-Range Fade)

Bu üç konu bu turun kapsamı dışında tutuldu, önceki sınıflandırmaları **değiştirilmedi**:

- Catalyst: **UNVALIDATED — DATA PIPELINE REGRESSION** (korunuyor, bu turda `catalyst_factor` sıfır-varyans bulgusu bunu yeniden doğruladı).
- Attention map: **VALIDATED-DESCRIPTIVE-RESEARCH** (korunuyor, bu tur dokunmadı).
- Opening-range fade: **CONFIRMATORY_CANDIDATE**, 3 koşul karşılanmadı (korunuyor, aynı 698-gözlem üzerinde yeni mining yapılmadı).

---

## 40-42. Interpretation Discipline

Bu raporun hiçbir tekil bulgusu ("bir ay pozitif spread", "bir vol_regime kırılımında daha iyi hit-rate", "winsorize edince işaret değişti") tek başına "sinyal var" iddiası olarak okunmamalıdır. Hiçbiri repeatability + OOS + random-control + effect-size + stability testlerinin **tümünü** birlikte geçmedi. Bölüm 25'teki vol_regime=1 bulgusu ve Bölüm 23'teki winsorize-sonucu **yeni hipotezlerdir**, doğrulanmış bulgu değildir — ileride Hipotez Üretimi v1.0 disiplini altında (mevcut global multiple-testing bütçesine eklenerek) ayrı test edilmeleri gerekir.

---

## 43. Success Condition — Final Answer

**Soru:** FinPilot baseline ranking neden random'dan kötü/zayıf görünüyor ve bu başarısızlık nereden kaynaklanıyor?

**Cevap: UNKNOWN (kısmi kanıtla).**

Kesin olarak bilinen: (a) production baseline eksiksiz reconstruct edilemedi (Case D, %10.58 exact-match); (b) bu ortamda reconstruct edilemeyen 3 terim (filter_score, alignment_ratio, momentum_ratio) gerçek etkisi bilinmeyen bir kör nokta oluşturuyor; (c) composite_score'un tanımı bu turda düzeltildi (strength%, ham skor değil) ve bu düzeltme önceki bazı yorumları geçersiz kılabilir; (d) ham istatistiklerle (Pearson, Top-N mean) elde edilen "random'dan kötü/ters" sonucu, outlier-robust istatistiklerle (winsorized Pearson, medyan quintile) kısmen tersine dönüyor — yani "gerçekten kötü" iddiası da kesin değil.

Tahmin edilmedi. Bir sonraki adım Bölüm 36'da belirtildi.

---

*Bu rapor Level A (read-only, forensic) çalışmanın ürünüdür. Hiçbir production dosyası, `.env`, flag, cache, scheduler veya governance kararı değiştirilmedi.*
