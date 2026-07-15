# FinPilot V2 Precision ve Execution Araştırma Raporu

**Tarih:** 2026-07-15
**Kapsam:** Alpha V2 sinyal seçimi, point-in-time split ve execution P&L
**Amaç:** Başarı oranını artırabilecek filtreleri aynı replay protokolüyle sıralamak

## Yönetici özeti

İlk birleşik execution bataryasında en iyi görünen iki aday:

| Aday | Validation | Locked OOS | Locked OOS PF | OOS işlem |
|---|---:|---:|---:|---:|
| V2 top-10% | -2.7525% | 4.5980% | 1.9345 | 22 |
| V2 top-10% + ATR>=4 + RVOL>=2 | -2.4282% | 5.8916% | 2.1636 | 19 |

Bu sonuçlar umut verici fakat production kararı için yeterli değildir. Her iki aday da validation döneminde negatiftir ve locked OOS örneklemi küçüktür. Bu nedenle şu anki karar:

**V2 ağırlıklarını değiştirme; ATR/RVOL adaylarını paper/shadow test adayı olarak tut; yeni veri gelmeden production filtresi olarak etkinleştirme.**

## Kullanılan protokol

- Canonical V2 source: `enriched_signals_v3.csv`
- Canonical satır sayısı: 4.680
- Sembol sayısı: 1.217 civarı
- Tarih sayısı: 53
- Discovery: `<= 2026-04-17`
- Validation: `2026-04-18..2026-05-21`
- Locked OOS: `> 2026-05-21`
- Score cut: yalnızca discovery döneminden öğrenilen V2 confirmation top-10 cut
- Barrier horizon: 5 bar
- TP: `5x ATR`
- SL: `1.5x ATR`
- Slippage: her yönde 5 bps
- Commission: her yönde 5 bps
- Notional: 1.000 USD
- Same-bar tie: stop-first

Sonuçlar forward favorable movement değil, triple-barrier execution P&L üzerinden hesaplandı. Forward-movement tabanlı eski runner sonuçları ayrıca raporlandı ve execution sonucu gibi yorumlanmadı.

## Yeni birleşik batarya

Çalıştırılan runner: `v2_precision_execution_runner.py`

| Aday | Validation n | Validation expectancy | Validation PF | OOS n | OOS expectancy | OOS PF | Değerlendirme |
|---|---:|---:|---:|---:|---:|---:|---|
| Score top-10% | 173 | 0.6496% | 1.1220 | 62 | -0.0046% | 0.9993 | Nötr, baseline |
| + RVOL>=2 | 55 | -2.7525% | 0.5938 | 22 | 4.5980% | 1.9345 | OOS güçlü, validation zayıf |
| + ATR>=4 + RVOL>=2 | 48 | -2.4282% | 0.6550 | 19 | 5.8916% | 2.1636 | En iyi OOS, küçük örneklem |
| + gap>=3 + RVOL>=2 | 21 | -3.0197% | 0.5394 | 5 | 1.8238% | 1.4462 | Çok küçük örneklem |
| + not extended | 132 | 1.6097% | 1.3212 | 42 | -0.1158% | 0.9821 | OOS iyileştirmiyor |
| + gap>=3 + RVOL>=2 + not extended | 12 | -3.1220% | 0.5250 | 1 | 1.2593% | Yok | Karar verilemez |
| + regime | 30 | 2.6296% | 1.9387 | 28 | 0.6549% | 1.0921 | Hafif pozitif, zayıf edge |
| + first signal only | 26 | -6.8066% | 0.1468 | 10 | -5.5456% | 0.3487 | Reddedilmeli |

### Bu sonuçların anlamı

1. **RVOL ve ATR+RVOL**, OOS’ta daha iyi TP oranı ve PF üretiyor.
2. Aynı filtreler validation’da kötü olduğu için zamana/rejime duyarlı olabilir.
3. `not_extended` tek başına yeterli değil.
4. İlk sinyali zorunlu tutmak bu veri setinde performansı bozuyor.
5. Gap filtresi örneklemi aşırı küçültüyor.
6. Rejim alanı artık `True/False/Trend/Range/0/1` ham değerleriyle normalize edildi; buna rağmen mevcut OOS edge’i production değişikliği için zayıf.
7. OOS’un sonundaki sinyallerin bir bölümünde 5 ileri bar bulunmadı. Baseline’da 92 seçimin 30’u, ATR+RVOL’da 30 seçimin 11’i execution’a giremedi. Bu nedenle bu satırlar başarı oranına dahil edilmedi ve coverage uyarısı olarak tutuldu.

## P0 execution karşılaştırması

### Common universe

Legacy ve V2 aynı canonical `(symbol, date)` kesişiminde karşılaştırıldı.

| Kaynak | Exit | İşlem | Net expectancy | PF | TP | SL | Time |
|---|---|---:|---:|---:|---:|---:|---:|
| Legacy | 2x ATR / 1x ATR | 61 | 2.8707% | 3.1451 | 54.10% | 26.23% | 19.67% |
| V2 | 5x ATR / 1.5x ATR | 28 | 4.0208% | 2.1819 | 7.14% | 28.57% | 64.29% |

### Full source universe

Bu modda kaynak evrenleri aynı değildir; sonuçlar fair A/B olarak kullanılmamalıdır.

| Kaynak | Exit | İşlem | Net expectancy | PF |
|---|---|---:|---:|---:|
| Legacy | 2x ATR / 1x ATR | 901 | 2.0968% | 1.7778 |
| V2 | 5x ATR / 1.5x ATR | 62 | -0.0046% | 0.9993 |

Bu iki tablo çelişmiyor. Common universe V2’nin seçtiği kesişim farklı; full universe ise V2’nin kendi tüm kaynak evrenini gösteriyor. Karar verirken evren, exit ve execution protokolü birlikte belirtilmelidir.

## Önceden çalıştırılan bataryalar

- `alpha_v2_research_runner.py`: 4.680 canonical V2 satırı, 49 constrained candidate. Bu runner forward-movement ve maliyet düşülmüş hedef kullanır; triple-barrier P&L değildir.
- `score_formula_comparison.py`: legacy ve V2 formülleri, top-percentile ve temporal split sonuçları yenilendi.
- `phase1_7_research_runner.py`: 165 constrained candidate ve kalite/replay contract çıktısı yenilendi. `replay_status=partial_replay_only` olduğu için yüksek forward return sonuçları execution kanıtı sayılmadı.
- `common_buy_accuracy.py`: common AL locked OOS örneklemi 44 olarak doğrulandı.
- `tests/test_p0_telemetry.py`: 3 test geçti.
- Tüm merkezi araştırma modülleri `py_compile` ile doğrulandı.

## Veri kalitesi bulguları

V2 artefaktında:

- ATR, gap ve dist52 mevcut.
- RVOL yaklaşık %97 kapsama sahip.
- Short alanı yaklaşık %94 kapsama sahip.
- `direction` alanı V2 artefaktında dolu değil; bu nedenle direction filtresi çalıştırılmadı.
- Spread, dollar ADV, market cap, feature age ve historical short freshness mevcut değil.
- Corporate-action durumunu bu artefakttan doğrulamak mümkün değil.

Bu eksik alanlar tamamlanmadan score’a yeni ağırlık eklemek yerine data contract genişletilmelidir.

## Sıradaki sıra

### P0: Uygulanacak

1. V2 artefaktına feature timestamp ve feature age ekle.
2. Historical short-interest snapshot ve snapshot tarihini ekle.
3. Spread, dollar ADV, market cap ve corporate-action durumunu ekle.
4. OOS sonu için forward-bar coverage kuralını netleştir; eksik horizon satırlarını ayrı censoring raporuna taşı.
5. RVOL ve ATR+RVOL adaylarını rolling walk-forward ile yeniden test et.

### P1: Veri geldikten sonra

1. Spread/impact stress: düşük, baseline ve yüksek maliyet senaryoları.
2. Likidite ve kapasite filtreleri.
3. Short freshness ile `short x RVOL` etkileşimi.
4. Sektör relative strength ve aynı gün cluster exposure.
5. Haber/SEC catalyst için strict pre-signal timestamp penceresi.

### P2: Production öncesi

1. Score calibration ve decile reliability.
2. Nested walk-forward ve locked OOS tekrarı.
3. Cluster bootstrap/Wilson interval.
4. Multiple-testing/FDR raporu.
5. En az birkaç haftalık paper execution ledger.

## Production kararı

Şu an production score veya exit profilinde değişiklik yapılmamalı.

Önerilen kontrollü aday:

```text
V2 score top-10%
AND ATR >= 4
AND RVOL >= 2
TP = 5x ATR
SL = 1.5x ATR
```

Bu kural yalnızca shadow/paper modda izlenmeli. Production’a geçiş için en az üç rolling OOS penceresinde pozitif net expectancy, validation’da tekrar edilebilirlik, cost-stress altında PF>1 ve yeterli işlem sayısı aranmalı.

## Rolling walk-forward sonucu

Yeni runner: `v2_walk_forward_runner.py`
Çıktı: `data/backtest_out/v2_walk_forward/v2_walk_forward_results.json`

Veri setinde 53 sıralı sinyal günü olduğu için üç pencere oluştu. Her pencere 20 discovery, 8 validation ve 8 test gününden oluştu; pencereler 8 gün ilerletildi. Her pencerenin score cut değeri yalnızca kendi discovery bölümünden öğrenildi.

| Aday | Test expectancy, pencere 1 | Pencere 2 | Pencere 3 | Pozitif pencere | Test işlem toplamı |
|---|---:|---:|---:|---:|---:|
| Score top-10% | -2.4676% | 7.6555% | 2.2592% | 2/3 | 212 |
| + RVOL>=2 | -3.5586% | 3.9992% | 10.8877% | 2/3 | 75 |
| + ATR>=4 + RVOL>=2 | -3.2972% | 4.9075% | 14.2787% | 2/3 | 64 |
| + gap>=3 + RVOL>=2 | -2.6040% | -4.7946% | 28.2971% | 1/3 | 28 |
| + regime | -2.6337% | 13.5422% | 11.9708% | 2/3 | 99 |
| + first signal only | -6.6702% | -16.2391% | -3.0137% | 0/3 | 36 |

Rolling sonuç baseline ile ATR/RVOL adayının aynı iki pencereyi kazanıp aynı ilk pencerede kaybettiğini gösteriyor. Dolayısıyla ATR/RVOL filtresi şu an baseline’a karşı kanıtlanmış istikrarlı üstünlük değil; yalnızca daha seçici ve bazı dönemlerde daha yüksek expectancy üreten bir adaydır. Rejim filtresi de benzer şekilde daha iyi görünse de bağımsız üstünlük kanıtı oluşturacak kadar tutarlı değildir.

Bu nedenle production geçiş koşulu karşılanmış sayılmadı. Bir sonraki deneyde spread/ADV ve historical short freshness verileri eklenmeden yeni threshold taraması yapılmamalı.

## Aynı seçimde exit karşılaştırması

Yeni runner: `v2_exit_same_selection_runner.py`
Çıktı: `data/backtest_out/v2_exit_same_selection/v2_exit_same_selection_results.json`

Bu testte V2 confirmation discovery top-10 cut bir kez hesaplandı ve aynı seçili `600` canonical satır iki exit profiline de uygulandı. Score, seçim, universe, horizon, entry drift, slippage ve commission değişmedi; yalnızca SL katsayısı değişti.

| Dönem | Execution n | TP 5x / SL 1x expectancy | PF | TP 5x / SL 1.5x expectancy | PF |
|---|---:|---:|---:|---:|---:|
| Discovery | 333 | 2.4360% | 1.6683 | 2.1083% | 1.5105 |
| Validation | 173 | 1.6123% | 1.3921 | 0.6496% | 1.1220 |
| Locked OOS | 62 | **2.0501%** | **1.4284** | -0.0046% | 0.9993 |

Eşleşmiş execution karşılaştırmasında `568` ortak işlem vardı:

- `5x/1x` daha iyi: 227 işlem
- `5x/1.5x` daha iyi: 57 işlem
- Aynı net barrier sonucu: 496 işlem
- Ortalama net-return farkı: `+0.7096` puan, `5x/1x` lehine
- Eşleşmiş toplam P&L farkı: `+$4,030.63`, `5x/1x` lehine

Bu, önceki exit sensitivity bulgusunu aynı seçili satırlar üzerinde doğruluyor: V2 için mevcut kanıt setinde kilitlenmesi gereken araştırma exit profili `TP=5x ATR / SL=1x ATR` profilidir. Bu sonuç V2 sinyalinin production’da başarılı olduğu anlamına gelmez; yalnızca iki exit arasında, aynı sinyal kümesinde `5x/1x` profilinin açıkça üstün olduğunu gösterir. V2’nin production’a alınması hâlâ forward shadow P&L, spread/impact verisi ve daha büyük OOS örneklemi şartına bağlıdır.

## Üretilen çıktılar

- `data/backtest_out/v2_precision_execution/v2_precision_execution_results.json`
- `data/backtest_out/v2_precision_execution/candidate_summary.csv`
- `data/backtest_out/p0_execution_replay_common_final/p0_execution_results.json`
- `data/backtest_out/p0_execution_replay_all_final/p0_execution_results.json`
- `data/backtest_out/v2_walk_forward/v2_walk_forward_results.json`
- `data/backtest_out/v2_exit_same_selection/v2_exit_same_selection_results.json`
- `data/backtest_out/v2_exit_same_selection/paired_exit_comparison.csv`
- `data/backtest_out/v2_data_quality_cost/v2_data_quality_cost_results.json`

## Veri sözleşmesi ve freshness audit

Üretim sinyal satırına ve `p0.v1` telemetry envelope’una şu nullable alanlar eklendi:

```text
spread_bps
spread_source
dollar_adv
adv_source
short_interest_timestamp
feature_timestamps
feature_age_minutes
data_quality.available
data_quality.missing_fields
```

Bu alanlar mevcut score hesabını değiştirmiyor. CSV ve `signal_events.payload_json` additive alanları taşıdığı için geriye dönük uyumluluk korunuyor.

Audit runner: `v2_data_quality_cost_runner.py`

| Alan | Kapsama | Sonuç |
|---|---:|---|
| Point-in-time dollar ADV | 4.680 / 4.680 | Cache’teki sinyal tarihinden önceki 20 barın `Close*Volume` ortalamasıyla üretildi |
| Observed spread | 0 / 4.680 | Bid/ask veya spread kolonu yok |
| Historical short freshness | 0 / 4.680 | Short-interest observation timestamp yok |

Locked OOS top-10 seçiminde 92 satır incelendi. Üç cost stress senaryosu da `insufficient_data` olarak kaldı; observed spread olmadan execution P&L’ye spread/impact sonucu yazılmadı. Bu bir başarısız test değil, veri sözleşmesinin eksik olduğunu gösteren kontrollü bir sonuçtur.

Bir sonraki veri sağlayıcı entegrasyonunda her sinyal için şu alanlar zorunlu olmalı:

```text
bid_price, ask_price, quote_timestamp
spread_bps
dollar_adv_20d, adv_timestamp
short_interest_pct, short_interest_timestamp
```

Bu alanlar geldikten sonra aynı runner, seçili locked OOS satırlarını baseline, spread-stress ve impact-stress maliyetleriyle yeniden replay etmelidir.
