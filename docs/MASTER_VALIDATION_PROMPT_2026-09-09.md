# FINPILOT FULL BASELINE RECONSTRUCTION & RANKING COMPRESSION FORENSICS

## MASTER VALIDATION PROMPT v1.0

**Tarih:** 2026-09-09
**Çalışma tipi:** READ-ONLY / PRE-REGISTERED / FORENSIC RESEARCH
**Amaç:** Production baseline ranking'in eksiksiz yeniden oluşturulması ve mevcut ranking failure'ın gerçek kaynağının belirlenmesi.

---

# 0. KRİTİK ARAŞTIRMA PRENSİBİ

Bu çalışma bir **optimization çalışması değildir.**

Amaç:

> Mevcut FinPilot production baseline score'un nasıl üretildiğini eksiksiz ve birebir anlamak; score compression, information loss, redundancy, inverted relationship, timing/coverage bias ve component construction problemlerinin hangilerinin gerçekten mevcut olduğunu belirlemek.

### KESİNLİKLE YAPMA

* weight optimization
* grid search
* parameter optimization
* threshold optimization
* reverse-score üretip başarı testi
* yeni feature ekleme
* mevcut feature'ları tuning
* BUY/SELL sonucu üretme
* production score değiştirme
* `.env` flag değiştirme
* feature flag açma/kapatma
* database değiştirme
* cache değiştirme
* scheduler değiştirme
* live system değiştirme
* publish sistemi değiştirme
* mevcut governance kararlarını otomatik değiştirme

### YAPILABİLİR

* production kodunu okumak
* production formula'yı yeniden oluşturmak
* mevcut datasetleri okumak
* mevcut historical artifact'ları analiz etmek
* component contribution hesaplamak
* score construction adımlarını forensic olarak incelemek
* compression/tie analizi
* redundancy analizi
* information-loss analizi
* timing/provenance analizi
* pre-registered diagnostic tests
* random/permutation controls
* walk-forward descriptive validation
* mevcut sonuçlarla karşılaştırma
* reproducibility testleri

**Hiçbir production dosyası değiştirilmemelidir.**

---

# 1. ARAŞTIRMA SORUSU

Ana soru:

> **FinPilot'ın gerçek production baseline ranking'i eksiksiz olarak yeniden oluşturulduğunda, ranking'in başarısız görünmesinin temel nedeni gerçekten feature signal'ının yokluğu mu, yoksa score construction / compression / redundancy / timing / information-loss problemi mi?**

Alt sorular:

1. Production composite_score tam olarak nasıl hesaplanıyor?
2. Önceki baseline audit'te eksik kalan input'lar nereden geliyor?
3. Production score historical dataset üzerinde birebir reconstruct edilebilir mi?
4. Reconstruction ile mevcut `composite_score` aynı mı?
5. Değilse farkın nedeni nedir?
6. %99.78 tie gerçekten score construction'dan mı kaynaklanıyor?
7. Integer 0–100 compression predictive information kaybettiriyor mu?
8. Binary weighting score'u aşırı sıkıştırıyor mu?
9. `dist_52w_high` gibi component'ler aynı bilgiyi tekrar tekrar mı taşıyor?
10. Composite score neden non-monotonic / inverted görünüyor?
11. Coverage bias sonucu etkiliyor mu?
12. Target horizon mismatch var mı?
13. Timing/provenance problemi var mı?
14. Production baseline ile random karşılaştırması reconstruction sonrasında hâlâ başarısız mı?
15. Eğer başarısızlık gerçekse, failure'ın hangi mekanizması en güçlü kanıtla destekleniyor?

---

# 2. AUTHORITATIVE FILES

Önce repository'yi keşfet.

Öncelikli kaynaklar:

```text
scanner/score_engine.py

data/backtest_out/full_universe_enriched_eod_only.csv
data/backtest_out/full_universe_enriched_labeled.csv
data/backtest_out/full_universe_enriched.csv

data/backtest_out/sector_map_full.csv

reports/baseline_ranking_health_2026-09-09.md
reports/walk_forward_scoring_validation_2026-09-08.md
reports/scoring_ablation_audit_2026-09-08.md
reports/meta_validation_audit_2026-09-08.md

docs/governance/decision-log.md
```

Ayrıca `score_engine.py` tarafından import edilen veya çağrılan:

* helper functions
* indicator calculators
* normalization functions
* score functions
* filter functions
* regime functions
* ranking functions
* clipping/rounding functions
* data transformation functions

bulunmalıdır.

**Sadece dosya adına bakma. Gerçek execution path'i takip et.**

---

# 3. PRODUCTION SCORE RECONSTRUCTION

Önce `scanner/score_engine.py` satır satır incelensin.

Aşağıdakiler kesin olarak çıkarılsın:

### 3.1 Base components

Her component için:

* gerçek kaynak
* function adı
* input kolonları
* normalization
* threshold
* weight
* clipping
* rounding
* missing-value davranışı
* default value
* binary/categorical/continuous olup olmadığı

çıkarılsın.

Özellikle:

```text
regime
direction
score
filter_score
alignment_ratio
momentum_ratio
volume_spike
price_momentum
trend_strength
```

gibi baseline bileşenlerinin production'daki gerçek hesaplanma yolları bulunmalıdır.

---

# 4. FLAG SEPARATION

Aşağıdaki flag'ler baseline'dan ayrı tutulmalıdır:

```text
catalyst
squeeze
lottery
overnight
FRED
fundamentals
news
alpha_v2
shadow
```

Bu araştırmanın primary baseline reconstruction'ı:

> **FLAG-OFF BASELINE**

olmalıdır.

Ancak production code'da flags'in baseline'a nasıl bağlandığı ayrıca belgelenmelidir.

Flag'lerin production score'u nasıl değiştirdiği yalnızca forensic olarak raporlanabilir.

**Flag enable/disable yapılmayacaktır.**

---

# 5. RECONSTRUCTION MODES

En az üç reconstruction üret:

### R1 — Production formula reconstruction

Kodda görülen gerçek formula.

### R2 — Production intermediate reconstruction

Her component'in final score'a girmeden önceki değeri.

### R3 — Final score reconstruction

Tüm component contribution'larının toplamından elde edilen final score.

Her satır için:

```text
component_raw
component_normalized
component_weight
component_contribution
component_final
```

mümkün olduğunca saklansın.

---

# 6. EXACT MATCH TEST

Reconstructed score ile dataset'teki mevcut `composite_score` karşılaştırılsın.

Ölç:

```text
n
exact_match_rate
mean_abs_error
median_abs_error
max_abs_error
p95_abs_error
p99_abs_error
correlation
rank_correlation
```

Ayrıca:

```text
reconstructed_score != stored_score
```

olan satırlar ayrı analiz edilsin.

Mismatch nedenleri kategorize edilsin:

```text
missing_input
different_formula
different_timestamp
different_normalization
different_rounding
different_flag_state
data_version_mismatch
unknown
```

### Kritik karar

Eğer exact reconstruction yapılamıyorsa:

> **PRODUCTION BASELINE = NOT FULLY RECONSTRUCTED**

olarak açıkça işaretle.

Eksik parçaları tahmin ederek doldurma.

---

# 7. INPUT COVERAGE FORENSICS

Her baseline input için:

```text
column
total_rows
non_null_rows
null_rows
coverage_pct
first_valid_date
last_valid_date
```

hesapla.

Özellikle önceki audit'te eksik olduğu görülen:

```text
alignment
momentum
filter
volume
price_momentum
trend_strength
```

için production source bulunmalıdır.

### Coverage classification

Her input:

* FULL
* HIGH
* PARTIAL
* LOW
* MISSING
* UNKNOWN

olarak sınıflandırılsın.

---

# 8. TIME / PROVENANCE FORENSICS

Her component'in hangi timestamp'e ait olduğu belirlenmeli.

Kontrol:

```text
scan_ts
entry timestamp
label_entry_basis
EOD vs intraday
market close
future target timestamp
```

Amaç:

> score calculation ile future return label arasında accidental timing mismatch olup olmadığını bulmak.

Özellikle:

```text
eod_close
intraday
```

ayrımı korunmalıdır.

`full_universe_enriched_eod_only.csv` primary dataset olmalıdır.

---

# 9. SCORE COMPRESSION FORENSICS

Bu çalışmanın ana bölümlerinden biridir.

Final score için:

```text
unique_score_count
total_rows
unique_score_ratio
tie_ratio
largest_tie_group
median_tie_group
p90_tie_group
p99_tie_group
```

hesapla.

Ayrıca her score değeri için:

```text
score
n
percentage
mean_forward_return
median_forward_return
hit_rate
```

çıkar.

---

# 10. EFFECTIVE RANK RESOLUTION

Sadece score range'e bakma.

Gerçek ranking resolution hesapla.

Her gün/universe için:

```text
n_stocks
unique_scores
unique_score_pct
effective_rank_resolution
largest_tie
median_tie
```

hesapla.

Aşağıdaki soruyu cevapla:

> 100 seviyeli integer score teorik olarak 100 rank sağlayabilirken pratikte günlük universe içinde kaç bağımsız ranking level'i gerçekten oluşuyor?

---

# 11. RAW VS COMPRESSED SCORE

Production formula izin veriyorsa iki temsil karşılaştır:

### A — Raw / pre-rounding score

### B — Final production compressed score

**Burada yeni weight uygulanmayacak.**

Amaç yalnızca:

> compression sırasında ranking information kayboluyor mu?

bunu ölçmek.

Karşılaştır:

```text
Spearman
Kendall
unique ranks
tie ratio
Top-N overlap
forward-return ordering
```

Eğer raw score ile final score arasında ciddi rank degradation varsa:

> **COMPRESSION INFORMATION LOSS = SUPPORTED**

aksi durumda:

> **COMPRESSION INFORMATION LOSS = NOT SUPPORTED**

---

# 12. ROUNDING / CLIPPING FORENSICS

Production formula'daki her:

```text
round()
floor()
ceil()
astype(int)
clip()
min/max
bucket
threshold
```

işlemi tespit et.

Her transformation için:

```text
before_unique
after_unique
information_loss_pct
tie_increase
rank_correlation
```

hesapla.

Ama transformation'ı değiştirme.

---

# 13. COMPONENT CONTRIBUTION ANALYSIS

Her baseline component için:

```text
mean
median
std
min
max
p01
p05
p25
p50
p75
p95
p99
zero_pct
negative_pct
positive_pct
```

hesapla.

Ayrıca:

```text
contribution variance
contribution share
rank contribution
```

çıkar.

Amaç:

> Score'un gerçekte hangi component'ler tarafından domine edildiğini anlamak.

---

# 14. COMPONENT → OUTCOME

Primary target:

```text
c2c_1d
```

Secondary:

```text
c2c_5d
```

Ayrı ayrı analiz et.

Her component için:

```text
Pearson
Spearman
rank IC
quintile mean return
quintile median return
quintile hit rate
monotonicity
```

hesapla.

Monotonicity:

```text
POSITIVE_MONOTONIC
NEGATIVE_MONOTONIC
NON_MONOTONIC
FLAT
INSUFFICIENT_DATA
```

olarak sınıflandır.

---

# 15. COMPOSITE SCORE → OUTCOME

Final reconstructed production baseline için:

```text
Pearson
Spearman
Kendall
rank IC
```

hesapla.

Sonra score quintiles:

```text
Q1
Q2
Q3
Q4
Q5
```

ve mümkünse deciles.

Her biri:

```text
n
mean
median
hit_rate
```

versin.

### Kritik test

Beklenen pattern:

```text
Q1 < Q2 < Q3 < Q4 < Q5
```

olmak zorunda değildir.

Ama gözlenen pattern açıkça raporlanmalıdır.

Eğer:

```text
Q1 > Q2 > Q3 > Q4 > Q5
```

veya benzeri inverse pattern varsa:

> **INVERTED RELATIONSHIP**

olarak işaretle.

---

# 16. RANDOM CONTROL

Aynı:

* date
* universe
* sample size
* target

koşullarında random selection yap.

Top:

```text
Top-5
Top-10
Top-20
Top-50
Top-100
```

baseline ile karşılaştır.

Random selection en az:

```text
100
```

replication yapmalı.

Mümkünse:

```text
500
```

replication.

Fixed random seed kullan.

Çıktı:

```text
baseline_mean
random_mean
random_std
random_p05
random_p50
random_p95
baseline_percentile
delta
```

---

# 17. PERMUTATION TEST

Mümkünse baseline score ile target arasındaki ilişki için permutation test yap.

En az:

```text
1000 permutations
```

kullanılabilir.

Amaç:

> gözlenen ranking performance'ın random ordering altında ne kadar sıra dışı olduğunu test etmek.

p-value raporla.

Önceki sonucu doğrulamak için özellikle:

```text
permutation_p
```

sakla.

---

# 18. WALK-FORWARD RECHECK

Daha önce kullanılan pre-registered windows mümkün olduğunca aynen korunmalı.

Yeni window seçme.

Yeni cutoff seçme.

Her window için:

```text
Spearman
Top-20 mean
Top-20 hit
random comparison
```

raporla.

Amaç:

> Baseline failure tek bir split'e özgü mü, yoksa zaman içinde tekrarlanıyor mu?

---

# 19. LEAVE-ONE-COMPONENT-OUT

Optimization yapmadan:

```text
FULL BASELINE
- component A
- component B
- component C
...
```

testleri yap.

**Weights yeniden ayarlanmayacak.**

Amaç:

> Hangi component baseline'ın başarısızlığını yaratıyor veya azaltıyor?

Her model için:

```text
Spearman
Top-20 mean
Top-20 hit
random delta
```

raporla.

### Önemli

Bir component çıkarıldığında sonuç iyileşirse:

> bu component otomatik olarak REMOVE değildir.

Sadece:

> **REMOVE-CANDIDATE**

olarak işaretlenebilir.

---

# 20. REDUNDANCY ANALYSIS

Baseline component'leri arasında:

```text
Pearson
Spearman
```

correlation matrix çıkar.

Özellikle:

```text
composite_score
dist_52w_high
```

ilişkisini doğrula.

Ayrıca component pairs için:

```text
high correlation
near duplication
directional redundancy
```

tespit edilmeye çalışılsın.

Threshold sonradan seçilmesin.

Mevcut standart correlation seviyeleri kullanılabilir ancak seçilen threshold raporda açıkça belirtilmelidir.

---

# 21. INFORMATION DOMINANCE

Her component için:

```text
variance contribution
rank contribution
unique contribution
correlation with composite
```

incelensin.

Amaç:

> Composite score'un görünürde birçok component içermesine rağmen gerçekte 1–2 component tarafından domine edilip edilmediğini görmek.

Özellikle:

```text
dist_52w_high
ATR
direction
regime
alignment
momentum
filter
```

ayrı incelensin.

---

# 22. COVERAGE BIAS

Composite score'un yalnızca son ~57 günde tanımlı olduğu önceki audit bulgusunu doğrula.

Score availability:

```text
date
rows
valid_score
null_score
coverage_pct
```

şeklinde çıkar.

Aşağıdakileri karşılaştır:

```text
FULL PERIOD
SCORE-COVERAGE PERIOD
```

Aynı metric'ler:

```text
Spearman
Top-N
hit rate
quintile return
```

üzerinden karşılaştırılsın.

Amaç:

> baseline failure gerçekten ranking probleminden mi, yoksa coverage regime değişiminden mi kaynaklanıyor?

---

# 23. UNIVERSE EFFECT

Dataset içindeki universe yapısını incele.

Özellikle:

* penny stocks
* extreme return outliers
* illiquid names
* highly volatile names

ayrı raporlanabilir.

Ancak:

**Yeni filtre veya exclusion kuralı oluşturma.**

Sadece sensitivity analysis yap.

Önceki penny-outlier bulgusu yeniden kontrol edilsin.

Robustness:

```text
raw
winsorized
median-based
```

sonuçları karşılaştır.

Amaç:

> tekil outlier'ların baseline-vs-random sonucunu açıklayıp açıklamadığını görmek.

---

# 24. HORIZON ANALYSIS

Primary:

```text
c2c_1d
```

Secondary:

```text
c2c_5d
```

Ayrı raporlanmalı.

Eğer veri uygunsa descriptive olarak:

```text
1D
3D
5D
```

karşılaştırılabilir.

Ancak:

> "best horizon" seçilmeyecek.

Amaç yalnızca:

> ranking signal'ın horizon-dependent olup olmadığını görmek.

---

# 25. REGIME ANALYSIS

Yeni regime tanımlama.

Mevcut dataset/code içindeki regime labels kullan.

Her regime için:

```text
n
Spearman
Top-20 mean
Top-20 hit
quintile behavior
```

çıkar.

Amaç:

> baseline'ın yalnızca belirli regime'lerde çalışıp çalışmadığını anlamak.

---

# 26. TIME STABILITY

Monthly veya mümkün olan doğal zaman bloklarıyla:

```text
score → forward return
```

ilişkisini izle.

Her period:

```text
n
Spearman
Top-N
hit rate
```

versin.

Amaç:

> signal'ın kalıcı mı, geçici mi, yoksa tamamen noise mu olduğunu görmek.

---

# 27. FAILURE MECHANISM CLASSIFICATION

Aşağıdaki hipotezleri test et:

### H1 — Signal absent

Baseline components future return hakkında bilgi taşımıyor.

### H2 — Ranking construction failure

Components'te bilgi olabilir fakat composite ranking bunu doğru aktarmıyor.

### H3 — Compression information loss

Raw score'da ranking information varken integer/bucket/rounding sonrası kayboluyor.

### H4 — Redundancy

Aynı bilgi birden fazla component tarafından tekrar tekrar taşınıyor.

### H5 — Inverted relationship

Yüksek score aslında sistematik olarak daha kötü outcome ile ilişkili.

### H6 — Coverage bias

Score yalnızca belirli tarih aralığında mevcut ve bu selection bias yaratıyor.

### H7 — Timing mismatch

Score ve label farklı timestamp bilgileri kullanıyor.

### H8 — Horizon mismatch

Ranking signal mevcut olabilir ancak seçilen target horizon ile uyumsuz.

### H9 — Universe contamination

Extreme/penny/illiquid names sonucu bozuyor.

### H10 — Missing reconstruction

Önceki audit gerçek production baseline'ı tam olarak reconstruct edemediği için failure yanlış sınıflandırılmış olabilir.

Her hipotez:

```text
SUPPORTED
PARTIALLY_SUPPORTED
NOT_SUPPORTED
UNVALIDATED
```

olarak işaretlensin.

Her kararın yanında evidence verilsin.

---

# 28. CRITICAL DECISION TREE

## Case A

Eğer:

```text
production score == reconstructed score
AND
compression explains failure
```

ise:

> PRIMARY FAILURE = SCORE CONSTRUCTION / COMPRESSION

## Case B

Eğer:

```text
raw score also fails
AND
components individually fail
```

ise:

> PRIMARY FAILURE = SIGNAL ABSENCE / COMPONENT QUALITY

## Case C

Eğer:

```text
raw score works
but compressed score fails
```

ise:

> PRIMARY FAILURE = INFORMATION LOSS THROUGH COMPRESSION

## Case D

Eğer:

```text
production score != reconstructed score
```

ise:

> PRIMARY STATUS = NOT FULLY RECONSTRUCTED

ve failure conclusion provisional kalmalıdır.

## Case E

Eğer:

```text
baseline works only in certain regimes
```

ise:

> REGIME-CONDITIONAL SIGNAL

olarak raporla.

Production değişikliği yapma.

---

# 29. NO OPTIMIZATION FIREWALL

Bu çalışma sırasında şu düşünceler uygulanmayacaktır:

> "Bu ağırlığı 2 yerine 1 yapalım."

> "Reverse ranking daha iyi görünüyor."

> "Top score'u ters çevirelim."

> "Bu component'i kaldıralım."

> "Şu threshold'u değiştirelim."

> "Score'u float yaparsak daha iyi olabilir."

Bunlar **gelecek araştırma hipotezleridir**, mevcut çalışmanın sonucu değildir.

Sonuç:

```text
OBSERVATION
→ EVIDENCE
→ HYPOTHESIS
→ FUTURE EXPERIMENT
```

şeklinde ayrılmalıdır.

---

# 30. REQUIRED OUTPUT FILES

Script:

```text
research/full_baseline_reconstruction_compression_forensics_2026_09_09.py
```

Report:

```text
reports/full_baseline_reconstruction_compression_forensics_2026-09-09.md
```

Component contribution:

```text
reports/baseline_reconstruction_components_2026-09-09.csv
```

Compression:

```text
reports/baseline_compression_forensics_2026-09-09.csv
```

Coverage:

```text
reports/baseline_input_coverage_2026-09-09.csv
```

Component predictiveness:

```text
reports/baseline_component_predictiveness_2026-09-09.csv
```

Random control:

```text
reports/baseline_random_control_2026-09-09.csv
```

Ablation:

```text
reports/baseline_leave_one_out_2026-09-09.csv
```

Walk-forward:

```text
reports/baseline_reconstruction_walk_forward_2026-09-09.csv
```

Correlation:

```text
reports/baseline_component_correlation_2026-09-09.csv
```

---

# 31. REPRODUCIBILITY

Script başında:

```text
DATASET PATH
DATASET SHA256
SCRIPT VERSION
DATE
RANDOM SEED
TARGET
WINDOW DEFINITIONS
```

kaydedilsin.

Dataset SHA-256 hesaplanmalı.

Önceki known SHA'larla farklıysa raporda açıkça belirtilmeli.

---

# 32. REPORT STRUCTURE

Final report şu sırada olmalı:

1. Executive Summary
2. Research Question
3. Dataset & SHA-256
4. Production Score Execution Path
5. Full Baseline Formula
6. Reconstruction Fidelity
7. Input Coverage
8. Timestamp / Provenance
9. Component Contributions
10. Score Compression
11. Raw vs Final Score
12. Composite Predictiveness
13. Component Predictiveness
14. Quintile Analysis
15. Top-N Analysis
16. Random Control
17. Permutation Test
18. Walk-Forward
19. Leave-One-Component-Out
20. Rank Displacement
21. Redundancy
22. Coverage Bias
23. Universe Sensitivity
24. Horizon Sensitivity
25. Regime Stability
26. Time Stability
27. Failure Mechanisms
28. Robustness
29. Negative Findings
30. What We Know
31. What We Don't Know
32. What Failed
33. What Passed
34. Final Baseline Status
35. Component Status
36. Next Research Question

---

# 33. FINAL STATUS VOCABULARY

Baseline:

```text
STRONG
MODERATE
WEAK
FAILED
NOT_FULLY_RECONSTRUCTED
UNVALIDATED
```

Component:

```text
KEEP
SUSPECT
REMOVE-CANDIDATE
UNVALIDATED
DATA-UNAVAILABLE
```

Compression:

```text
SUPPORTED
PARTIALLY_SUPPORTED
NOT_SUPPORTED
UNVALIDATED
```

---

# 34. FINAL DECISION TABLE

Report sonunda:

| Component      | Production Present | Reconstructed | Direct Signal | Rank Effect | OOS Effect | Compression Effect | Redundancy | Status |
| -------------- | -----------------: | ------------: | ------------: | ----------: | ---------: | -----------------: | ---------: | ------ |
| regime         |                    |               |               |             |            |                    |            |        |
| direction      |                    |               |               |             |            |                    |            |        |
| score          |                    |               |               |             |            |                    |            |        |
| filter         |                    |               |               |             |            |                    |            |        |
| alignment      |                    |               |               |             |            |                    |            |        |
| momentum       |                    |               |               |             |            |                    |            |        |
| volume         |                    |               |               |             |            |                    |            |        |
| price momentum |                    |               |               |             |            |                    |            |        |
| trend strength |                    |               |               |             |            |                    |            |        |
| dist_52w_high  |                    |               |               |             |            |                    |            |        |
| ATR            |                    |               |               |             |            |                    |            |        |

---

# 35. REQUIRED FINAL STATEMENT

Rapor sonunda aşağıdaki dört başlık kesinlikle bulunmalı:

## WHAT WE KNOW
Sadece kanıtlanan bulgular.

## WHAT WE DON'T KNOW
Henüz kanıtlanamayan noktalar.

## WHAT FAILED
Başarısız olan testler ve hypotheses.

## WHAT PASSED
Başarılı olan reconstruction / integrity / robustness testleri.

---

# 36. GOVERNANCE

Araştırma sonunda governance değişikliği otomatik yapılmayacaktır.

Eğer sonuç yeni bir governance kararı gerektiriyorsa:

```text
PROPOSED GOVERNANCE ACTION
```

başlığı altında öner.

Ancak:

* decision-log otomatik değiştirme
* `.env` değiştirme
* production code değiştirme
* flag değiştirme

yapma.

Mevcut governance kararları ile çelişen bir bulgu varsa çelişkiyi açıkça raporla.

---

# 37. CATALYST / FLAG SCOPE

Catalyst bu çalışmanın ana konusu değildir.

Mevcut catalyst cache regression:

```text
1801 / 548
→
8 / 0
```

ayrı technical/data-pipeline issue olarak raporlanabilir.

Bu çalışma catalyst predictive value hakkında yeni karar üretmemelidir.

Aynı şekilde:

```text
squeeze
lottery
overnight
catalyst
FRED
fundamentals
news
alpha_v2
shadow
```

flag'leri açma/kapatma.

Flag decision:

> **BASELINE FAILURE RESOLUTION SONRASINA DEFERRED**

olarak korunmalıdır.

---

# 38. ATTENTION MAP SCOPE

Attention map:

> VALIDATED-DESCRIPTIVE-RESEARCH

olarak korunacaktır.

Bu çalışma attention map'i direction predictor olarak yeniden sınıflandırmayacaktır.

Ayrıca:

```text
weighted 6-flag attention
```

ile:

```text
Big Gap OR Volatility Spike
```

tanımlarını birbirine karıştırma.

---

# 39. OPENING-RANGE FADE SCOPE

Opening-range fade:

> CONFIRMATORY_CANDIDATE

olarak kalacaktır.

Bu çalışma onu production strategy olarak test etmeyecektir.

Önceden belirtilen üç koşul korunacaktır:

1. wider intraday cache
2. realistic cost model
3. single-shot pre-registration on NEW data

Aynı 698 observation üzerinde yeni mining yapılmayacaktır.

---

# 40. IMPORTANT INTERPRETATION RULE

Şu sonuçlardan herhangi biri tek başına "signal var" anlamına gelmez:

```text
positive mean return
positive hit rate
high correlation
good single split
good Top-N
one profitable bucket
one successful walk-forward window
```

Signal iddiası için:

> repeatability + out-of-sample + random control + effect size + stability

birlikte değerlendirilmelidir.

---

# 41. RESEARCH DISCIPLINE

Bu çalışmanın amacı bir sonucu "iyi" veya "kötü" yapmak değildir.

Amaç:

> **FinPilot'ın mevcut ranking sisteminin gerçekte ne yaptığını mümkün olan en dürüst ve yeniden üretilebilir şekilde ortaya çıkarmaktır.**

Özellikle şu ihtimale açık kal:

> Baseline gerçekten kötü olabilir.

Ama aynı şekilde şu ihtimale de açık kal:

> Önceki audit baseline'ın production'daki gerçek formunu tam reconstruct edemediği için failure'ın bir kısmını yanlış teşhis etmiş olabilir.

Bu iki ihtimal araştırma başlamadan eşit derecede açık tutulmalıdır.

---

# 42. FINAL RESEARCH PRINCIPLE

### Evidence > intuition
### Reconstruction > assumption
### Reproducibility > one good backtest
### Random control > absolute return
### OOS > in-sample
### Negative result > false confidence
### Diagnosis > optimization
### Production change only after validation
### IMPLEMENTED ≠ ACTIVE ≠ INFLUENTIAL ≠ PREDICTIVE
### SCORE CHANGE ≠ RANKING INFORMATION
### RANKING INFORMATION ≠ PREDICTIVE VALUE

---

# 43. SUCCESS CONDITION

Bu araştırma ancak aşağıdaki soruya net cevap verebildiğinde başarılı kabul edilir:

> **"FinPilot baseline ranking neden random'dan kötü görünüyor ve bu başarısızlık production formula'nın kendisinden mi, eksik reconstruction'dan mı, compression'dan mı, redundancy'den mi, inverted relationship'ten mi, timing/coverage'dan mı, yoksa gerçekten predictive signal eksikliğinden mi kaynaklanıyor?**

Cevap bilinmiyorsa:

> **UNKNOWN**

de.

Tahmin etme.

---

# END OF MASTER PROMPT
