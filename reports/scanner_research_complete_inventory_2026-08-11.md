# FinPilot Scanner Araştırmaları: Tam Analiz ve Envanter

Tarih: 2026-08-11
Kapsam: Scanner, score, entry/exit, TP/SL, portfolio, execution, data-quality ve bunlara bağlı research-only uygulamalar
Katman: Research / Engineering
Seviye: Level A araştırma ve dokümantasyon
Durum: Üretim promosyonu yok; scanner davranışı değiştirilmedi

## 1. Yönetici özeti

Bugüne kadar yapılan çalışmaların tamamı birlikte okunduğunda şu sonuç çıkıyor:

1. Mevcut composite score ileriye dönük güvenilir bir tahmin sinyali olarak doğrulanmadı. Geçmiş 5 günlük hareketle ilişkisi 0.376 iken ileri 5 günlük close-to-close sonuçla ilişkisi yaklaşık 0.013; score bantları monoton değil ve score, sabit base-rate tahmininden daha iyi kalibre görünmüyor.
2. Mevcut `entry_ok` seçimi maliyet sonrası istikrarlı bir avantaj göstermedi. Aynı score bandı içinde eligible satırlar, not-eligible satırlardan daha kötü sonuç verdiği için sorun yalnızca filtre ayrıntısı değil, score/selection katmanının birlikte ele alınması gereken bir veri ve ölçüm sorunu.
3. Yüksek ham ortalamalar çoğunlukla outlier, hedefe ulaşma kapağı, uzun horizon ve MFE ile gerçek kapanış getirisi arasındaki farkla açıklanabilecek durumdadır. Medyanlar, trimmed mean'ler ve null kontrolleri bu yüksek ortalamaları desteklemiyor.
4. TP/SL ve exit matrisi geniş biçimde tarandı; ancak global reality-check sonuçları anlamlı değil, locked OOS açılmadı ve gözlenen spread/slippage/impact verisi yok. Bu nedenle hiçbir TP/SL veya exit profili üretim adayı değildir.
5. En sağlam ilerleme sinyalde değil, ölçüm sırasındadır: veri etiketi, canonical symbol-day deduplication, etkin örneklem, leakage ayrımı, null kontrolleri ve execution veri eksikleri görünür hale getirildi.
6. Henüz kanıtlanmamış ama araştırma için ilginç yapılar vardır: path-aware MFE capture, gap reversal, RVOL inversion ve ATR-parity sizing. Bunlar bulgu değil, veri onarımı ve ön-kayıt sonrası test edilebilecek hipotezlerdir.

Son karar: Mevcut kanıt düzenli haftalık %5-10 toplam kazancı, üretim score'unu, `entry_ok` edge'ini veya herhangi bir TP/SL kuralını doğrulamıyor. H1/H2/H3 confirmatory testleri, locked OOS ve üretim kuralı değişiklikleri HOLD durumundadır.

## 2. Veri kimliği ve sonuçların neden ayrı tutulduğu

### Güncel ana export

- Girdi: `data/backtest_out/full_universe_enriched.csv`
- Güncel fixed-target artifact SHA-256: `e3b183552c7c38755528d133327a0c0601fe0cfff49ba58b9e360d17716ed3d3`
- Güncel fixed-target sayıları: 100,440 raw; 48,727 canonical; 26,372 path-resolved
- Güncel tarih aralığı: 2025-09-11..2026-07-09
- Güncel split: train 14,515; validation 11,588; locked OOS 269 unopened
- Cache: `data/price_cache/`

### Önceki ana export

- 2026-08-07 P0-P3 koşusunun SHA-256 değeri: `38b981b372571a01b727d6a51f3fd8b918a770f7a53e552ef55e1629c142e896`
- Bu koşuda 53,859 raw satır ve 799 resolved `entry_ok` gözlemi kullanıldı.
- 2026-08-10 Strategic/Ten Perspectives/Mirror laboratuvarları da önceki export kimliğini kullanır: 53,859 raw ve yaklaşık 27,386 deduplicated symbol-day.

Runner'ların raw, canonical ve resolved sayıları horizon, entry-drift ve loader politikasına göre değişir. Bu sayılar tek bir toplam veri kümesiymiş gibi birleştirilmedi. Eski artifact'ler güncel sonuçların yerine geçirilmedi.

## 3. Uygulanan veri ve ölçüm altyapısı

### 3.1 Etiket ve path semantiği

`scanner/labeling.py` ve barrier runner üzerinde günlük OHLC triple-barrier metodolojisi kullanıldı: TP, SL ve time exit; aynı barda TP ve SL görülürse stop-first. Daha sonra export'a gerçek close-to-close sonuçlar (`c2c_1d`, `c2c_5d`) ve adverse excursion (`mae_t5`) eklendi.

Kritik düzeltme: `resolved_pct_t5` MFE benzeri favorable movement ölçüsüdür; beş gün sonraki gerçek getiri değildir. MFE medyanı ile `c2c_5d` medyanı birbirinden ayrıldığı için eski MFE tabanlı sonuçlar kapanış getirisi veya P&L kanıtı olarak yorumlanmadı.

### 3.2 Canonicalization ve effective sample size

Symbol-day deduplication, path resolution, entry-price drift rejection, short-path bildirimi ve tarih bloklu bootstrap kullanıldı. Strategic Lab sonucunda yaklaşık 27,361 satırın etkin örneklemi yaklaşık 620; eligible grubun 799 satırının etkin örneklemi yaklaşık 168 olarak ölçüldü. Bu nedenle satır sayısına dayalı naive confidence interval'lar güvenilir kabul edilmedi.

### 3.3 Leakage ve replay kontrolleri

Feature lineage şu alanları ileriye dönük outcome olarak işaretledi: `resolved_pct_t5`, `resolved_pct_1d`, `c2c_1d`, `c2c_5d`, `mae_t5`. Bunlar feature matrisine giremez.

P0 score replay tam kapanmadı. Eski canonical export zorunlu production score bileşenlerini taşımıyordu; telemetry recovery'de 303 seçili günün tamamı tarihsel `vol_regime` eksikliği nedeniyle strict replay'de geçemedi. Güncel scan export'unda 1,801 satırın 1,570'inde gerekli alanlar bulundu; ancak bağımsız bridge recomputation, korunmayan feature-flag/input alias'ları nedeniyle comparable satırların tamamında mismatch verdi. Gelecek evaluator export'u için contract alanları önerildi; bu Level B scanner/export sözleşmesi kararıdır ve onaysız üretim değişikliği değildir.

## 4. Deneylerin tek tek analizi

### A. Scanner performansı ve veri alma

| Deney | Durum | Ne ölçüldü | Sonuç / anlam |
|---|---|---|---|
| Scanner runtime baseline | COMPLETED diagnostic | API scan, bulk provider, fallback, indicator, evaluation ve persistence timing | Aynı batch büyüklüğünde runtime ciddi değişiyor. 15m/1h Alpaca miss'leri ve yfinance repair yolu önemli şüpheli; nedensellik kesinleşmedi. |
| Stage timing planı | PARTIAL / proposal | Per-provider, retry, cache, indicator, evaluation ve persistence stage timing | Mevcut telemetry yalnızca sınırlı stage sürelerini taşıyor; teorik minimum runtime söylenemez. |
| Price-cache integrity | COMPLETED diagnostic / HOLD | 2,047 symbol, %50 close-jump eşiği | 485 symbol'de büyük sıçrama; işaretli grubun largest-jump medyanı 173.57513%. Corporate action/provider açıklaması olmadan confirmatory kapı kapalı. |
| Adjusted-cache backfill/audit | COMPLETED diagnostic | Adjusted cache ve süreklilik kontrolü | Bazı sıçramalar yeniden işaretlendi; adjusted verinin tüm provider/path sorunlarını çözmediği görüldü. |
| Restatement detector | BLOCKED | Eski immutable bar-cache snapshot ile aynı symbol/date karşılaştırması | Böyle bir snapshot yok. Distribution snapshot bar-cache snapshot yerine kullanılmadı. |

### B. Frozen `entry_ok` P0-P3

Artifact: `data/backtest_out/research_run_2026-08-07_entry_ok_p0_p3.json` ve ilgili rapor.

| Kapı | Durum | Bulgusu |
|---|---|---|
| P0 score equivalence | INSUFFICIENT_DATA | Zorunlu production score alanları yok; tam row-level equivalence kurulamadı. |
| P1 label permutation | COMPLETED diagnostic | 1,000 permutation; candidate percentile 0.020. Pozitif edge değil. |
| P1 signal permutation | COMPLETED diagnostic | 1,000 permutation; candidate percentile 0.272. Pozitif ayrışma yok. |
| P1 time shift | COMPLETED diagnostic | 1,000 permutation; candidate percentile 0.564. |
| P2 cost validation | FAIL | 0.25%, 0.55%, 1.00% senaryolarının tamamında negatif mean. Base cost mean -0.442591%, median -2.693951%. |
| P2 temporal validation | FAIL | Train mean -0.171665%; validation mean -1.133753%; sonraki dönem kötüleşiyor. |
| P3 robustness/capacity | FAIL / INSUFFICIENT_DATA | False rejection %41.7861; spread source %0; historical liquidity join yok. |

### C. Decision quality ve rejection surface

2026-08-06 koşusunda 27,125 resolved gözlemin 26,863'ü rejected, 262'si eligible idi. Eligible grup pozitif net oranında %32.82, mean -0.9465%, median -3.1067%; rejected grup %41.79, mean +0.3695%, median -1.4314% verdi. 2026-08-11 güncel loader'ında eligible 305 gözlemle mean -1.4361%, median -3.3977%, positive rate %30.16; full comparison mean -0.1755%, median -1.8605%, positive rate %39.75 oldu.

Bu sonuçlar yeni No-Trade veto kuralı veya inverse production rule üretmez. Yalnızca mevcut selection yüzeyinin karar kalitesi kanıtlamadığını gösterir.

### D. Score anlamı, ranking ve calibration

#### Strategic Lab: 18 test

Artifact: `data/backtest_out/strategic_lab_2026-08-10.json`.

- V0 label validation: correlation 0.86 olsa da etiket semantiği doğrulanmış sayılmadı.
- R1 backward vs forward: past 5d rho 0.376; forward 5d rho 0.013.
- R2 reverse ranking: eligible median -0.386%, rejected +0.427%; block CI'lar örtüşüyor, yön önceki bulguyu tekrarlıyor.
- R3 decile monotonicity: monotonic değil; decile-vs-median Spearman 0.33.
- R4 rank stability: day-over-day rho 0.742; score sticky ve slow-moving.
- R5 signal decay: horizonlar arasında temiz pozitif pattern yok.
- R10 absolute vs within-day percentile: 0.013 vs -0.040; ikisi de ileri bilgi göstermiyor.
- E1 entry delay: next-open gecikme maliyeti eligible medyanda yaklaşık -0.12pp; günlük ölçekte ana sorun değil.
- E2 drift budget: abs drift <=1% alt kümesinde medyan +0.52%; veri giriş fiyatı kalite sorunu sonucu değiştirebiliyor.
- X1/X3 path: 5d MFE medyanı +4.26%, MAE -4.36%; horizon sonuna kadar tutmak tipik favorable excursion'ın yaklaşık %14'ünü yakalıyor.
- X6 invalidation exit: günlük close proxy'si medianı iyileştirmedi, adayların %90'ını durdurdu; PARTIAL.
- G2/G4 regime: bazı orta-volatility hücreleri pozitif, ancak eligible hücreleri küçük ve tutarsız.
- P1 counterfactual portfolio: eligible, aynı gün random rejected portföylerinden medyan -2.01pp; yalnızca 35 günün %31'inde pozitif.
- P2 candidate correlation: median pairwise 20d correlation 0.19; ana problem redundancy değil selection.
- P7 loss clustering: günlük mean lag-1 autocorrelation 0.23; kayıplar zaman içinde kümeleniyor.
- S1 effective sample: full universe yaklaşık 620, eligible yaklaşık 168 effective observations.

#### Ten Perspectives Lab: 13 test

Artifact: `data/backtest_out/ten_perspectives_lab_2026-08-10.json`.

- Q1 adverse movement: score rho 0.006; 1 ATR adverse movement base rate %86.5, eligible %91.2.
- Q2 failure prediction: lottery_factor rho 0.184, overnight_gap_factor 0.126, atr_pct 0.109; score yaklaşık noise.
- Q3 score semantics: `dist_52w_high` rho 0.667, `past_5d_pct` 0.376; score extension'ı encode ediyor. `catalyst_factor` export'ta constant 0.0.
- Q4 null-feature injection: n=27,361 için spurious-correlation p95 |rho|=0.011; strongest real forward rho 0.110 olsa da ekonomik fayda göstermiyor.
- Q5 benchmark-relative: SPY'ye karşı median -1.22pp, block CI sıfırın altında; IWM karşısı -0.86pp ve CI sıfırı kapsıyor. Beta-neutral değildir.
- Q6 first-passage: eligible P(MFE before MAE)=0.494; günlük OHLC intraday ordering kanıtlamaz.
- F1 calibration: base-rate predictor'a göre Brier skill -0.019 ve -0.030; score doing-nothing base rate'ten iyi değil.
- P1 correlation-cluster selection: median iyileşme 0.0; pozitif gün oranı %38.7.
- P2 sizing: ATR-parity max drawdown -15.9%, equal-weight -24.3%; bu portfolio construction bulgusudur, entry edge değildir.
- P3 tails: eligible CVaR5 -21.3%, rejected -22.9%; fark küçük.
- M1 RVOL: high-RVOL eligible median -1.77%, low-RVOL +0.68%; inversion adayıdır, kanıtlanmış kural değildir.
- M2 gap: gap-up >=3% median -3.04%; gap-down >=3% median +3.05%; extension/reversal adayıdır, confirmatory değildir.
- A1 regimes: tiny extreme clusters mostly data artifacts; regime result production için kullanılamaz.

#### Mirror Analysis: 9 test

Artifact: `data/backtest_out/mirror_analysis_2026-08-10.json`.

Mirror çalışması önceki “score geçmişin aynasıdır” tezini sınadı ve daha hassas sonuca ulaştı: score saf mirror değil; extension ağırlıklı, noise içeren ve ileri bilgi taşımayan composite görünümündedir.

- L1: `dist_52w_high` ve `past_5d_pct` güçlü backward encoding; extension score rank varyansının yaklaşık R²=0.477'sini açıklar.
- L2: extension quintile'ları ileri 5d getiride temiz reverse gradient üretmez.
- L3: extension kontrolünden sonra partial rho 0.025; gizli forward signal yok.
- L4: top score quintile içinde eligible median -0.20%, not-eligible +1.08%; `entry_ok` score bandı içinde adverse selection yapıyor.
- A1/A2/A4/A5: sonuç veri artifact'i, birkaç kötü gün, horizon veya liquidity proxy ile açıklanmadı; rho horizonlar boyunca 0.013-0.038 civarında kaldı.
- Synthesis: score'u follow etmek +0.013, extension'ı fade etmek -0.008; score basitçe ters çevrilecek bir sinyal değil.

### E. Barrier, TP/SL, exit ve target deneyleri

#### 1. ATR barrier grid

2026-08-06'da `TP={1,1.5,2,3,4,5} ATR`, `SL={0.5,0.75,1,1.5,2} ATR`, horizon `{3,5,10,20}` ve %0.55 cost ile 2,520 viable satır üretildi. Ham pozitif expectancy değerleri vardı; ancak 5x ATR, 10-20 gün ve seçici cohort'larda yoğunlaştı. Median, capped mean, date-block ve outlier kontrolleri olmadan bunlar kullanılmadı.

2026-08-11'de aynı tip uzun ATR grid'i başlatıldı fakat daha geniş current fixed-target protokolü tamamlandıktan sonra durduruldu. Bu son koşu için tamamlanmış ATR artifact'i iddia edilmiyor.

#### 2. Fixed-target full-universe protocol

2026-08-05 eski artifact'inde 3,120 konfigürasyon vardı; validation satırı 0 olduğu için gross+period-stable ve cost-positive konfigürasyon sayısı 0 kabul edildi. 2026-08-11 güncel koşusunda yine 3,120 konfigürasyon; FDR discoveries 1,012, CPCV/PBO 0.6, White Reality Check p=0.7413, Hansen SPA p=0.7761, locked OOS unopened.

Güncel 55 bps senaryosunda doğrudan all-candidate fixed-stop matrisinin seçilmiş en iyi mean-net sonuçları bile robust median üretmedi. Örnekler: 2% SL/10% TP/20 bar net mean +0.137%, median -2.550%; 3% SL/10% TP/20 bar net mean +0.222%, median -3.550%; 5% SL/10% TP/20 bar net mean +0.439%, median -5.550%. Bu satırlar grid içinden seçildiği için independent validation değildir.

#### 3. Target-return ve adaptive-target

`target_return_optimization`, `adaptive_target_experiments` ve ilgili runner'lar close-to-close veya favorable-movement proxy'leriyle çalıştı. Peak-touch, exact time-to-hit, realistic fill ordering ve observed cost bulunmadığı için bunlar execution sonucu değildir. Production target kararı çıkarılmadı.

#### 4. Invalidation exit ve score lab exits

Günlük bar üzerinde stop/invalidation proxy'leri incelendi. Naive -1 ATR daily-close invalidation medyanı kötüleştirdi ve adayların çoğunu durdurdu. Intraday path olmadığı için “stop kesin olarak şu fiyattan doldu” sonucu çıkarılmadı.

### F. Portfolio, risk, sizing ve capacity

Portfolio backtest'lerinde 36 konfigürasyon çalıştı. 2026-08-06 koşusundaki en iyi görünen config yaklaşık final equity `$100,515.21`, CAGR `%0.62`, realized daily Sharpe `0.2323`, max drawdown `-4.06%`, 245 trade ve win rate `%40.82` verdi. Bu yaklaşık başa baş sonuçtur.

Ten Perspectives sizing çalışmasında ATR-parity sizing max drawdown'ı -15.9% ile equal-weight -24.3% değerinden düşük yaptı ve Sharpe 0.267 ile en iyi oldu; bu selection edge değil, risk mekanizması gözlemidir.

Historical sector coverage düşük/kararsızdır. Son liquidity snapshot'ında usable dollar ADV 1,561, `liquidity_ok` oranı %11.85 ve observed spread-source rate %0'dır. Snapshot historical outcomes'a join edilmedi; bu nedenle capacity ve executable universe kanıtlanmadı.

### G. Timing, drift ve half-life

Timing/drift çalışması 36,336 resolved satırda signal-close, next-open ve next-close senaryolarını karşılaştırdı. Signal-close bir günlük raw mean %6.8838 olsa da median %0, trimmed mean -0.0290% ve toplam katkının %108'i top 5% outlier'lardan geldi. Next-open mean %0.1130%, trimmed mean -0.0014%; benchmark-adjusted trimmed mean'ler negatif.

Daily half-life: eligible 2,438 satır; day-1 median +0.0311%, positive rate %50.21; day-5 median -0.6711%, positive rate %44.71. Intraday half-life ölçülemedi.

### H. Statistical validation ve null controls

- HAC/Newey-West, FDR, deflated Sharpe, CPCV/PBO, White Reality Check ve Hansen SPA protokollere eklendi.
- 2026-08-07 P0-P3 koşusunda üç null ailesi x 1,000 permutation = 3,000 immutable run.
- 2026-08-11 registry'de 3 experiment ve 6,000 completed run görünür; null family 6,000 run ile selection-bias exposure yaratıyor.
- Null testleri adayın null'dan pozitif ayrışmadığını gösterdi; null sonucu tek başına bir edge kanıtı değildir.
- Multiple testing bütçesi görünür hale getirildi; FDR discovery sayısı üretim onayı sayısı değildir.

## 5. Yapılan altyapı ve uygulama listesi

### Research modülleri ve yardımcıları

Aşağıdaki modüller oluşturuldu, güncellendi veya araştırma hattına alındı; dosyanın mevcut olması tek başına çalışmanın tamamlandığı anlamına gelmez.

- `research/full_universe_barrier_backtest.py` — canonical path, triple-barrier, TP/SL ve grid runner.
- `research/candidate_pipeline.py` — P0-P3 candidate pipeline.
- `research/negative_control.py` — label, signal ve time-shift null aileleri.
- `research/null_preflight_gate.py` — null preflight altyapısı.
- `research/experiment_registry.py` ve `research/registry.py` — immutable experiment/run kayıtları.
- `research/protocol.py` ve `research/statistical_validation.py` — temporal split, HAC, FDR, CPCV/PBO ve robustness yardımcıları.
- `research/evidence_ledger.py` — event identity, feature timestamp, label/cost metadata.
- `research/feature_lineage.py` — forward leakage kontrolü.
- `research/score_bridge.py`, `research/score_replay.py`, `research/build_score_replay_input.py` — production/research score equivalence ve telemetry.
- `research/honest_score_calibration.py` ve `research/score_calibration.py` — temporal calibration.
- `research/decision_quality_experiments.py` — veto/rejection quality.
- `research/stability_concentration_capacity.py` — split, sector, correlation proxy, liquidity ve capacity.
- `research/timing_drift_study.py` ve `research/signal_half_life.py` — entry timing ve signal ömrü.
- `research/price_cache_integrity_audit.py`, `research/backfill_adjusted_price_cache.py`, `research/restatement_detector.py` — price integrity ve restatement.
- `research/strategic_lab_2026_08_10.py` — 18 deney, 17 completed + 1 partial.
- `research/ten_perspectives_lab_2026_08_10.py` — 13 completed deney.
- `research/mirror_analysis_2026_08_10.py` — 9 completed deney.
- `research/score_lab_2_exits.py`, `research/score_lab_3_regime.py`, `research/signal_quality_lab.py`, `research/sweep.py`, `research/walkforward.py`, `research/lgbm_ranker.py`, `research/pipeline.py`, `research/candidate_pipeline.py` — ilgili araştırma/runner yüzeyleri; her birinin production sonucu olarak yorumlanması için ayrı gate gerekir.
- `research/multitimeframe_profiles.py` — eski suggestion tabanlı sınırlı multi-timeframe çalışması.
- `research/collect_sec_companyfacts.py`, `research/sec_companyfacts.py`, `research/news_hypothesis_protocol.py` — fundamentals/news yönleri; PIT ve event coverage eksikleri nedeniyle confirmatory değil.

### Veri ve export uygulamaları

- `fetch_full_universe_and_retest.py` ile enriched export yeniden üretildi.
- `c2c_1d`, `c2c_5d` ve `mae_t5` outcome alanları eklendi.
- MFE/favorable movement ile gerçek close-to-close return ayrıştırıldı.
- Price cache integrity ve adjusted-cache audit çalıştırıldı.
- Score replay input builder, current scan export payload desteği ve future score contract alanları hazırlandı; üretim sözleşmesi Level B pending konusudur.

### Test ve doğrulama uygulamaları

Odaklı research laboratuvarı doğrulaması 27 test ile geçti:

- Strategic Lab: 8 test
- Ten Perspectives Lab: 10 test
- Mirror Analysis: 7 test
- Close-to-close export: 2 test

Buna ek olarak scanner/research test yüzeyinde şu sınıflar vardır:

- score contract, score bridge, score replay
- evidence ledger, research protocol, experiment registry, negative control
- barrier/backtest metrics ve full-universe robustness
- decision quality, stability/capacity, timing drift, honest calibration
- price-cache integrity ve adjusted-cache backfill
- pipeline, evaluator, indicators, data fetcher, ranking guard, scanner contract
- API runtime, distribution/prepublish, reconciliation ve rollout smoke testleri

Bu test dosyalarının mevcut olması, tüm üretim veya canlı kapıların geçtiği anlamına gelmez; testler davranış sözleşmesini doğrular, veri geçerliliği ve gerçek execution kanıtını tek başına kanıtlamaz.

### Rapor ve artifact listesi

Ana karar artifact'leri:

- `reports/research_battery_full_2026-08-11.md`
- `reports/research_battery_consolidated_2026-08-11.md`
- `reports/strategic_lab_experiments_2026-08-10.md`
- `reports/ten_perspectives_lab_2026-08-10.md`
- `reports/mirror_analysis_2026-08-10.md`
- `reports/research_run_2026-08-07_entry_ok_p0_p3.md`
- `reports/end_to_end_experiment_summary_2026-08-07.md`
- `reports/research_program_execution_2026-08-06.md`
- `reports/correct_order_analysis_2026-08-10.md`
- `reports/scanner-performance-research-2026-08-04.md`
- `reports/evidence_matrix_v1_2026-08-07.md`
- `reports/research_test_plan_v2_2026-08-07.md`
- `reports/research_reframing_end_to_end_2026-08-07.md`

Ana data artifact'leri:

- `data/backtest_out/full_universe_enriched.csv`
- `data/backtest_out/research_run_2026-08-07_entry_ok_p0_p3.json`
- `data/backtest_out/end_to_end_negative_controls_2026-08-07.json`
- `data/backtest_out/fixed_target_full_universe_2026-08-11.json`
- `data/backtest_out/strategic_lab_2026-08-10.json`
- `data/backtest_out/ten_perspectives_lab_2026-08-10.json`
- `data/backtest_out/mirror_analysis_2026-08-10.json`
- `data/backtest_out/decision_quality_experiments_2026-08-11.json`
- `data/backtest_out/stability_concentration_capacity_2026-08-11.json`
- `data/backtest_out/honest_score_calibration_2026-08-11.json`
- `data/backtest_out/timing_drift_study_2026-08-11.json`
- `data/backtest_out/negative_controls_2026-08-11.json`
- `data/backtest_out/price_cache_integrity_audit_2026-08-11.json`
- `data/backtest_out/end_to_end_research_experiments.db`

## 6. Tamamlanmamış veya bloklu işler

### Veri ve execution kapıları

- Immutable önceki price-cache snapshot'ı yok; restatement karşılaştırması BLOCKED.
- 485/2,047 symbol için büyük close jump flag'i açıklanmadı.
- Historical PIT sector membership yok.
- Observed spread, slippage, impact ve fill price yok; spread-source rate %0.
- Intraday OHLCV yok; daily bar ile fill ordering, intraday half-life ve auction davranışı kanıtlanamaz.
- ADV snapshot historical outcomes'a join edilmedi; capacity decision-grade değil.
- Feature timestamp/age ve current export score input equivalence tam kapanmadı.

### Confirmatory ve ürün/insan deneyleri

- H1 gap reversal, H2 RVOL inversion ve H3 ATR parity confirmatory koşuları HOLD; veri bütünlüğü gates açılmadan çalıştırılmadı.
- Locked OOS insan onayı olmadan açılmadı.
- Shadow, paper/live emir ve broker aksiyonu yapılmadı.
- PR1-PR7 ve B1-B7 gerçek kullanıcı deneyleri 10-15 kullanıcı gerektiriyor.
- Grounded-rationale audit, adversarial research agent ve AI-free baseline için LLM evaluation harness yok.
- Earnings/news event taxonomy için PIT event timestamp yok.
- DRL/PPO çalışmaları research-only ve production scanner'dan ayrıdır; mevcut sonuçlar production score/entry kuralı değildir.

### Çalıştırılmamış veya yalnızca altyapısı bulunan yüzeyler

- `score_lab_2_exits.py` ve `score_lab_3_regime.py` gibi runner'lar için dosya varlığı tamamlanmış, güncel ve bağımsız kanıt anlamına gelmez.
- Bazı eski planlar ve default path'ler `research/data/backtest_out/enriched_signals_v2.csv` gibi mevcut olmayan göreli yollar kullanıyordu; bu koşular negatif strateji sonucu değil, runner/path defect olarak sınıflandırıldı.
- 2026-08-11 ATR grid'i durduruldu; tamamlanmış sonuç olarak sayılmıyor.

## 7. Kanıtın doğru kullanım sınırı

Bu dosya şu iddiaları desteklemez:

- “Scanner kârlı trade seçiyor.”
- “Score olasılık veya kalite sıralaması olarak kalibre edildi.”
- “TP/SL profili doğrulandı.”
- “Haftalık toplam %5-10 düzenli kazanç gerçekçidir.”
- “Spread, slippage ve capacity ölçülmüştür.”
- “Locked OOS veya live/shadow test geçti.”

Bu dosyanın desteklediği iddia daha sınırlıdır: FinPilot'ın bugüne kadarki scanner araştırması, veri/ölçüm/execution eksiklerini görünür kılmış; mevcut score ve `entry_ok` seçim katmanında forward edge kanıtı bulamamış; yüksek ham sonuçların outlier ve barrier-cap etkilerine açık olduğunu göstermiştir.

## 8. Sonraki doğru sıra

1. Veri: price jump açıklaması, immutable cache snapshot, PIT feature/sector/event metadata.
2. Ölçüm: current export score replay equivalence, experiment budget ve mandatory null preflight.
3. Execution: intraday bars, observed spread/slippage/impact/fill ve capacity join.
4. Confirmatory: yalnızca ön-kayıt, insan onayı ve locked OOS kapıları açıldıktan sonra H1/H2/H3.
5. Sinyal: ancak yukarıdaki katmanlar geçildikten sonra yeni score/entry/exit kuralı Level B/C süreçleriyle ele alınabilir.

Bu rapor Level A research-only kayıt olarak hazırlanmıştır. Üretim scanner'ı, publication, risk, portfolio, broker ve live davranış değiştirilmemiştir.
