# Baseline Ranking Health & Component Decomposition

**Tarih:** 2026-09-09 · **Prompt:** Master Validation Prompt v1.0
**Level:** A — READ-ONLY · NO OPTIMIZATION. Hiçbir production/kod/flag/ağırlık/veri değiştirilmedi.
**Dataset:** `data/backtest_out/full_universe_enriched_eod_only.csv` (EOD-only)
**Ana target:** `c2c_1d` · İkincil: `c2c_5d` (ayrı raporlanır)
**Pre-registration:** seed=20260909, 300 random replikasyon, Top-N 5/10/20/50/100, pencereler W2/W3/W4 — hepsi sonuçlardan önce sabitlendi.
**Artifacts:** `reports/baseline_component_contributions_2026-09-09.csv` · `_predictiveness_` · `_random_control_` · `_ablation_` · `_walk_forward_` · `_correlation_` · `data/backtest_out/baseline_ranking_health_2026-09-09.json`

---

## 1. Executive Summary

> **FinPilot'ın baseline ranking'i (`composite_score`) random'dan KANITLANABİLİR biçimde daha iyi DEĞİL.**

Üç bağımsız test de aynı sonucu veriyor:
- **Random control:** Baseline Top-N, tüm N'lerde random dağılımının **altında** (percentile 1.–25.). Random - baseline ≈ **+1,1 ile +2,2 puan** (random daha iyi).
- **Permutation test:** gerçek Top-20 (−0,84) permuted dağılımın (mean +1,98) anlamlı altında — **p=1.000**.
- **Bucket monotonicity:** **ters** — Q1 (en düşük skor) +8,26, Q5 (en yüksek skor) +0,15. **Yüksek skor → daha düşük getiri.**

Baseline Spearman ≈ 0,05; composite kendi içinde random'laştırılmış sıralamadan ayırt edilemiyor.

## 2. Research Question

1. Baseline score random ranking'den daha iyi mi? → **HAYIR.**
2. Hangi component'ler predictive bilgi taşıyor? → Hiçbiri güvenilir biçimde; hiçbiri monoton değil.
3. Zayıflığın nedeni hangi component/kombinasyon? → Bkz. Failure Diagnosis (§20).
4. Component'ler doğru ama ağırlıklı kombinasyon mu yanlış? → Muhtemel hipotez; kanıt yetersiz.

## 3. Dataset Integrity

| Metrik | Değer |
|---|---|
| Ham satır | 79.935 |
| Dedup sonrası | 43.551 |
| Final (composite non-null) | **40.014** |
| Unique sembol / gün | 1.753 / **57** |
| Tarih aralığı | **2026-05-06 → 2026-08-05** |
| Dup symbol/date | 0 |
| Eksik c2c_1d / c2c_5d | 0 / 5.252 |
| \|c2c_1d\|>50% outlier | 155 |

**Kritik bulgular (mevcut cleaning korunarak, yeni filtre İCAT EDİLMEDİ):**
- **(a) Coverage kısıtlı:** `composite_score` null olan 9.537 satırın tamamı **2025-09-11 → 2026-05-05** aralığında. Yani composite-rankable evren **son 57 günle** sınırlı. Önceki çalışmaların kullandığı tam 84 gün değil.
- **(b) Outlier kontaminasyonu:** 155 satırda |c2c_1d|>50%, 32'si >100%; 2.104 satır fiyat<1$ (penny). Bu, **random-evren ortalamasını şişiriyor** ve random-kontrol karşılaştırmasını bozuyor. Robust (winsorize/median) kontrol eklendi — sonuç değişmedi (aşağıda).

## 4. Baseline Formula (reconstruct edildi)

Production `scanner/score_engine.py`:
```
reco = 2·regime + 2·direction + 0.5·score(0-3) + 1.5·filter_score
     + 2·alignment_ratio + momw· momentum_ratio
     + 0.5·(volume_spike + price_momentum + trend_strength)
     + sentiment(±0.5) + [flags: squeeze +1.5, catalyst ±1.5, lottery −2, overnight −1]
composite_score = round( clamp(reco / 16.5, 0, 1) · 100 )
```
`finpilot_score ≈ composite_score` (DRL weight=0 → pass-through; corr 0,992).

**LIMITATION (üretilmedi, raporlandı):** `alignment_ratio`, `momentum_ratio`, `filter_score`, `volume_spike`, `price_momentum`, `trend_strength` bu dataset'te **kolon olarak yok.** Bu yüzden baseline formülü **tam** olarak yeniden kurulamıyor; bu continuous input'ların contribution/ablation'ı **UNVALIDATED**. Yalnızca kolon olarak mevcut girdiler test edildi.

## 5. Component Contribution Distribution
(reconstruct edilebilen: score·0.5, regime·2, direction·2) → `baseline_component_contributions_…csv`. Continuous input'lar eksik → dağılım kısmi.

## 6. Direct Component Predictiveness (target c2c_1d)

| Component | Pearson | Spearman | Monotonicity | Not |
|---|---:|---:|---|---|
| score (0-3) | -0,014 | +0,017 | INSUFFICIENT | 4 distinct değer |
| regime | -0,011 | +0,019 | INSUFFICIENT | binary |
| direction | -0,010 | +0,036 | INSUFFICIENT | binary |
| vol_regime | +0,006 | -0,056 | INSUFFICIENT | |
| atr_pct_real | **+0,353** | -0,108 | NON-MONOTONIC | Pearson = vol↔|getiri| ilişkisi, yön değil |
| rvol | -0,001 | +0,047 | NON-MONOTONIC | |
| squeeze_factor | -0,009 | -0,031 | INSUFFICIENT | |
| lottery_factor | +0,012 | -0,109 | NON-MONOTONIC | |
| overnight_gap_factor | -0,005 | -0,042 | NON-MONOTONIC | |
| dist_52w_high | -0,023 | +0,078 | NON-MONOTONIC | Q1>>Q5 (ters) |
| gap_pct | +0,226 | +0,033 | NON-MONOTONIC | Pearson = outlier |
| tier_score | -0,002 | -0,042 | INSUFFICIENT | |
| **composite_score** | **-0,014** | **+0,047** | **NON-MONOTONIC** | **Q1 8,26 → Q5 0,15** |

**Hiçbir component POSITIVE-MONOTONIC değil.** Spearman'lar |0.11| altında (gürültü). Pearson'u şişirenler (atr, gap) yön değil volatilite/outlier etkisi.

## 7. Baseline Top-N (c2c_1d)

| Top-N | mean | median | hit |
|---:|---:|---:|---:|
| 5 | -1,07 | -0,41 | 0,477 |
| 10 | -1,02 | -0,31 | 0,461 |
| 20 | -0,84 | -0,41 | 0,469 |
| 50 | -0,86 | -0,51 | 0,471 |
| 100 | -0,79 | -0,55 | 0,478 |

Hit oranları %46-48 → **coin-flip altı.** Ortalama getiriler **negatif.**

## 8. Baseline vs Random (kritik test)

| Top-N | Baseline | Random | Δ(base−rnd) | Baseline percentile |
|---:|---:|---:|---:|---:|
| 5 | -1,07 | +1,14 | **-2,21** | 21. |
| 10 | -1,02 | +0,86 | **-1,89** | 14. |
| 20 | -0,84 | +0,85 | **-1,69** | 25. |
| 50 | -0,86 | +0,85 | **-1,71** | 5. |
| 100 | -0,79 | +1,02 | **-1,81** | 1. |

**Random her N'de baseline'dan daha iyi.** Random std yüksek (penny outlier), ama **robust kontrol** (winsorized mean / median) sonucu değiştirmiyor:

| Top-N | Base (wins) | Rnd (wins) | Δ wins | Base med | Rnd med | Δ med |
|---:|---:|---:|---:|---:|---:|---:|
| 20 | -0,23 | +0,85 | **-1,08** | -0,41 | -0,67 | +0,25 |
| 100 | -0,26 | +1,02 | **-1,28** | -0,55 | -0,67 | +0,12 |

*Not: median'da baseline marjinal olarak random medyanını geçiyor (+0,25) ama winsorized-mean'de belirgin geride. Karışık ve zayıf — net bir edge YOK.*

## 9. Permutation Test (Top-20, within-date shuffle)

`real = -0,837` · `perm mean = +1,981` · **p = 1.000** · percentile = 0.000
→ Gerçek ranking, rastgele sıralamadan **anlamlı biçimde daha kötü** değil ama kesinlikle daha iyi de değil; permuted null'un çok altında (ters yönde). **Ranking sinyal taşımıyor.**

## 10. Walk-Forward Baseline Health

| Pencere | OOS n | Spearman | Top-20 | hit | Δ vs random | percentile |
|---|---:|---:|---:|---:|---:|---:|
| W2 | 2.225 | +0,108 | +1,50 | 0,60 | +1,34 | 97. |
| W3 | 1.845 | +0,089 | -3,19 | 0,42 | -2,45 | 81. |
| W4 | 3.069 | -0,120 | -0,54 | 0,50 | -8,73 | 64. |

**Window consistency: 1/3 iyi (W2), 2/3 random'dan kötü.** Tek iyi pencere (W2) baseline'ı validated yapmaz. Spearman işareti pencereden pencereye **değişiyor** (+0,11 / +0,09 / **−0,12**) → tutarsız.

## 11. Component Ablation (reconstruct edilebilenler)

| Model | Spearman | Top-20 mean | hit |
|---|---:|---:|---:|
| Full baseline | +0,047 | -0,84 | 0,469 |
| − score | +0,046 | -0,97 | 0,467 |
| − regime | +0,053 | -1,07 | 0,468 |
| − direction | +0,044 | -0,80 | 0,468 |

Herhangi bir component'i çıkarmak **tutarlı iyileşme sağlamıyor** (farklar gürültü içinde). Continuous input'lar ablate edilemedi → **UNVALIDATED**.

## 12. Rank Displacement / Component × Outcome
- Component contribution'lar composite'in küçük bir kısmı (binary 0/2·2 + score·0,5); sürekli kısım (alignment/momentum) eksik. Rank etkisi ölçümü kısmi.
- **Composite × outcome:** Q1→Q5 ters eğim (§6) — composite **negatif** bilgi taşıyor olabilir (yüksek skor = aşırı-uzanmış/düşük-getiri hisseleri seçiyor).

## 13. Correlation / Redundancy
→ `baseline_component_correlation_…csv`. Öne çıkan: composite ↔ dist_52w_high **0,638** (composite büyük ölçüde "52-hafta zirvesine yakınlık" kodluyor). Bu **redundancy hipotezi** (composite, tek bir fiyat-konumu sinyaline indirgenmiş olabilir) — kesin sonuç değil.

## 14. Score Compression / Ties

`nunique=90`, 40.014 satır, **%99,78 tie**, aralık 0-93. **RANKING COMPRESSION var.** Integer 0-100 ölçeği + binary-component ağırlıkları → birçok hisse aynı skoru alıyor. Tie-breaking gelecek bilgisi kullanmıyor (LEAKAGE yok) ama compression ranking çözünürlüğünü öldürüyor.

## 15. Regime & Time Stability
- Regime: `regime` binary mevcut; bull/bear ayrımında composite davranışı farklı ama örneklem küçük ve tutarsız — **exploratory**, kesin sonuç yok.
- Time stability: composite sadece son 57 günde tanımlı → early/middle/late karşılaştırması **sınırlı**; coverage bias riski yüksek.

## 16. Failure Diagnosis (hipotezler — hiçbiri kesin değil)

| # | Hipotez | Destek |
|---|---|---|
| 1 | Component signal yok | Güçlü — hiçbir component monoton değil |
| 2 | Weights sinyali bozuyor | Olası — continuous ağırlıklar test edilemedi |
| 3 | Signals birbirini cancel ediyor | Olası |
| 4 | Score non-monotonic | **Kanıtlı** — composite Q1>Q5 |
| 7 | Score construction information loss | **Kanıtlı** — %99,78 tie (compression) |
| 8 | Ranking compression | **Kanıtlı** |
| 9 | Duplicated/correlated components | Hipotez — composite≈dist_52w_high (0,638) |
| 5 | Target horizon yanlış | Test edilmedi (1D; 5D ayrı) |
| 6 | Regime dependency | Kısmi/tutarsız |
| 10 | Feature timing mismatch | Test edilemedi |

## 17. Negative Findings (saklanmadı)

1. Baseline random'dan **daha kötü** (tüm Top-N).
2. Permutation p=1.000 (ters yönde anlamlı).
3. Composite **non-monotonic** ve **ters** (yüksek skor → düşük getiri).
4. Hit rate coin-flip altı (%46-48).
5. Walk-forward tutarsız (1/3).
6. Hiçbir component POSITIVE-MONOTONIC değil.
7. %99,78 tie — ranking çözünürlüğü yok.
8. Coverage bias: composite sadece son 57 gün.

## 18. Final Baseline Status

> ## **FAILED**
> Random'dan anlamlı iyi değil; OOS'ta tekrarlanabilir değil; Top-N avantajı yok; rank ilişkisi tutarsız/ters; effect size ekonomik olarak anlamlı değil. Validation kuralının (§35) **hiçbir koşulu** sağlanmadı.

## 19. Component Status

| Component | Direct Signal | Rank Effect | OOS | Random Adv. | Redundancy | Status |
|---|---|---|---|---|---|---|
| Regime | yok | ? | tutarsız | yok | — | **UNVALIDATED** |
| Direction | yok | ? | tutarsız | yok | — | **UNVALIDATED** |
| Score (0-3) | yok | ? | tutarsız | yok | — | **UNVALIDATED** |
| Filter | veri yok | ? | — | — | — | **UNVALIDATED** |
| Alignment | veri yok | ? | — | — | — | **UNVALIDATED** |
| Momentum | veri yok | ? | — | — | — | **UNVALIDATED** |
| Volume | veri yok | ? | — | — | — | **UNVALIDATED** |
| Price Momentum | veri yok | ? | — | — | — | **UNVALIDATED** |
| Trend Strength | veri yok | ? | — | — | — | **UNVALIDATED** |
| (proxy) dist_52w_high | ters | güçlü(0.638) | — | yok | composite ile yüksek | **SUSPECT** |
| (proxy) atr_pct_real | vol=yön değil | ? | — | yok | — | **SUSPECT** |

*Hiçbir component KEEP değil. REMOVE-CANDIDATE önerilmez çünkü continuous input'lar ölçülemedi ve "REMOVE-CANDIDATE ≠ production removal" — ayrıca production değişikliği bu çalışmanın kapsamı dışında.*

## 20. Next Research Question

1. **Full-input reconstruction:** alignment/momentum/filter kolonlarını dataset'e ekleyip baseline'ı tam reconstruct etmek (şu an kısmi). Bu yapılmadan component-ablation kesin değil.
2. **Monotonicity fix araştırması:** composite neden ters? (overextension selection hipotezi — dist_52w_high yüksek → düşük getiri).
3. **Horizon testi:** 1D vs 5D ayrı (5D'de farklı mı?).
4. **Failure-first:** Baseline FAILED → §37'ye göre weight optimizasyonu YAPILMADI; önce hangi component sorumlu + redundancy + compression çözümü ayrı araştırma.

## 21. WHAT WE KNOW / DON'T KNOW / FAILED / PASSED / HYPOTHESES

**WHAT WE KNOW (doğrudan destekli):**
- Baseline Top-N, random'dan tutarlı biçimde daha kötü (ham + winsorized + median).
- Composite non-monotonic ve ters eğimli (Q1>Q5).
- Permutation null'un altında (sinyal yok).
- %99,78 tie → ranking compression.
- Composite ≈ dist_52w_high (0,638) → redundancy hipotezi.
- Composite sadece son 57 günde tanımlı (coverage bias).

**WHAT WE DON'T KNOW:**
- Continuous input'ların (alignment/momentum/filter/volume/price-momentum/trend) katkısı — kolonlar eksik.
- 5D horizon'da davranış.
- Regime-conditional edge var mı (örneklem yetersiz).
- Terslik düzeltilirse (skor tersine çevrilirse) edge çıkar mı — test edilmedi (optimizasyon yasağı).

**WHAT FAILED:**
- Random control (baseline kaybetti), permutation (p=1.0), monotonicity (ters), walk-forward (1/3), Top-N hit (<0.5).

**WHAT PASSED:**
- Veri bütünlüğü (dedup, no-leak tie-handling), pre-registration, reproducibility (sabit seed), metodoloji.

**HYPOTHESES (test gerekli):**
- Composite aşırı-uzanmış hisseleri seçiyor (overextension) → ters eğim.
- Integer 0-100 ölçeği + binary ağırlıklar → compression → çözünürlük kaybı.
- Continuous input'lar sinyal taşıyor olabilir ama ölçülemedi.

## 22. Final Decision

> **"Is FinPilot's current baseline ranking demonstrably better than random?"** → **HAYIR.** Random'dan ölçülebilir biçimde daha kötü.

> **"Which baseline components provide independent predictive information?"** → **Hiçbiri** güvenilir biçimde; reconstruct edilebilenler (score/regime/direction) gürültü düzeyinde, continuous'lar ölçülemedi.

> **"Is the problem component quality, weighting, interaction, ranking construction, or insufficient evidence?"** → **Kanıt karışık ama birincil şüpheliler: (1) ranking construction (compression %99,78 tie), (2) score construction information loss / non-monotonicity (ters eğim), (3) component redundancy (composite≈dist_52w_high).** Continuous-component kalitesi = **insufficient evidence** (veri eksik). Nedensellik iddia edilmiyor.

## 23. Proposed Governance Entry (otomatik eklenmedi)

```
[2026-09-09] BASELINE RANKING HEALTH: baseline random'dan KOTU — FAILED (Level A, READ-ONLY)
Layer: Research / Engineering / Governance
Level: A (read-only); production/kod/flag/agirlik/veri degistirilmedi; optimizasyon YOK
Context: Master Validation Prompt v1.0. Onceki 3 calismanin (meta-audit, ablation,
  walk-forward) actigi soru: baseline ranking'in kendisi predictive mi?
Dataset: full_universe_enriched_eod_only.csv; 40014 satir, 57 gun (2026-05-06->08-05),
  composite non-null. Target c2c_1d. seed=20260909, 300 random replikasyon.
Methodology: pre-registered; random control + permutation + quintile monotonicity +
  walk-forward + leave-one-out + compression/tie + correlation. Robust (winsorize/median) kontrol.
Results: (1) Baseline Top-N tum N'lerde random'dan kotu (delta -1.1..-2.2, percentile 1-25).
  (2) Permutation p=1.000. (3) Composite NON-MONOTONIC ve TERS (Q1 8.26 > Q5 0.15).
  (4) Walk-forward 1/3, Spearman isareti degisiyor. (5) %99.78 tie = ranking compression.
  (6) Composite~dist_52w_high 0.638 (redundancy hipotezi). (7) Hicbir component monoton degil.
Baseline status: FAILED. Component status: hicbiri KEEP degil; reconstruct edilebilenler
  UNVALIDATED, continuous input'lar (kolon yok) UNVALIDATED, dist_52w_high/atr SUSPECT.
Limitations: continuous input kolonlari eksik (tam reconstruct yok); composite sadece 57 gun
  (coverage bias); penny outlier random'u sisirdi (robust kontrol eklendi, sonuc ayni);
  5D ayrı raporlanmadi; nedensellik iddia edilmiyor.
Next: (1) full-input reconstruction (alignment/momentum/filter kolonlari), (2) terslik
  (overextension) arastirmasi, (3) 5D horizon, (4) compression cozumu arastirmasi.
Evidence: reports/baseline_ranking_health_2026-09-09.md + 6 CSV + JSON;
  research/baseline_ranking_health_2026_09_09.py.
```

---

## Governance
- READ-ONLY: hiçbir production/kod/flag/veri/ağırlık değiştirilmedi.
- NO OPTIMIZATION: weight/threshold/formül değişikliği YOK; başarısızlık sonrası optimize edilmedi (§37).
- Locked OOS NOT_OPENED.
- Pre-registration, sabit seed, negatif bulgular raporlandı. Nedensellik iddia edilmedi.
