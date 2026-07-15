# FinPilot Precision-First Selectivity Optimization

## 1. Yonetici ozeti

Bu rapor, `data/backtest_out/full_universe_enriched.csv` icindeki tum evreni kullanarak sinyal hacmini azaltma ve precision'i artirma deneylerini toplar. Calisma research-only'dir; production threshold, score agirligi veya strategy selection degistirilmemistir.

Ana sonuc: mevcut artifact'te problem yaklasik 200 kabul sinyali/gun olarak gorunmuyor. Canonical symbol-day seviyesinde `entry_ok` ortalamasi **12.1/gun**, raw satir seviyesinde **26.1/gun**. Full universe'in tamaminda ise ortalama **414.9 satir/gun** taraniyor. Bu nedenle once sinyal, tarama satiri ve duplicate snapshot ayrimi production telemetry ile netlestirilmelidir.

Precision-first sonuclar:

- Canonical `entry_ok`: 801 sinyal, 12.1/gun, `%41.6` hit rate.
- `strict_confirmation` (`entry_ok + liquidity + regime + direction + ATR>=4 + RVOL>=1.2`): 203 sinyal, 3.1/gun, `%48.3` hit rate.
- Composite top-20/gun: 1,138 sinyal, 17.2/gun, `%32.9` hit rate. Bu, entry gate precision'inden daha zayif.
- Composite top-1%/gun: 314 sinyal, 4.8/gun, `%36.9` hit rate. Hacim azalir, fakat precision entry_ok/strict_confirmation seviyesine cikmaz.
- Barrier locked OOS'ta daha once kesfedilen `ATR6+RVOL2`, 5 gun, ATR cap 100 icin `n=347`, gross expectancy `%2.832`, cost-adjusted expectancy `%2.282`, PF `1.631` gorunmustur. Ancak bu sonuc discovery selection ve cap/backtest pipeline'ina bagimli oldugu icin production GO degildir.
- Daha kucuk ve daha gercekci Alpha V2 locked OOS'ta ayni tip kurallar negatif veya PF<1 kalmistir. Bu, edge'in donem ve sample secimine hassas oldugunu gosterir.

**Karar: NO-GO.** Bu rapor yeni filtreyi production'a almayi onaylamaz. Once point-in-time replay, canonical reject telemetry, corporate-action temizligi, spread/impact verisi ve yeni bagimsiz locked OOS gerekir.

## 2. Veri ve metodoloji

Girdi:

- `data/backtest_out/full_universe_enriched.csv`
- 53,859 raw satir
- 1,932 sembol
- 66 scan gunu
- 27,386 canonical symbol-day satiri
- 26,473 duplicate symbol-day satiri

Canonical kural, ayni symbol-day icin en erken scan timestamp'ini tutar. Primary target `resolved_pct_t5 >= 5%` ve favorable movement hedefidir; dogrudan execution P&L degildir.

Test matrisi:

1. Full-universe signal volume map ve duplicate analizi.
2. Baseline: all universe, `entry_ok`, precision core, strict confirmation.
3. ATR, RVOL, gap, squeeze, composite, score, regime ve direction threshold sweep.
4. Gate ablation: regime, direction, raw score, liquidity ve entry gate etkisi.
5. 2 ve 3 factor, farkli factor family'lerden constrained combinations.
6. Per-day top-20/top-50/top-100/top-200 ve %1/%5/%10/%20 ranking quota.
7. Bull/bear ve low/normal/high volatility splitleri.
8. Discovery/validation/locked OOS temporal split.
9. Maliyet senaryolari: none `%0`, low `%0.30`, baseline `%0.55`, stress `%1.00`.
10. Ayrica mevcut barrier engine ile ATR cap ve execution-style triple-barrier sonuclari.

Yeni runner:

- `precision_selectivity_runner.py`
- `data/backtest_out/precision_selectivity/precision_selectivity_results.json`
- `data/backtest_out/precision_selectivity/precision_selectivity_summary.csv`

Son full matrix kosusu `bootstrap=0` ile tamamlandi. Genis combination matrisinde clustered bootstrap pratik calisma suresini asiri artirdigi icin bu artifact'te yeni bootstrap CI yoktur; Wilson araliklari ve onceki `full_universe_robustness.py` cluster-bootstrap sonuclari ayri kanit olarak ele alinmalidir.

## 3. Sinyal hacmi ve duplicate etkisi

| Evren | Satir | Ortalama/gun | Entry OK | Entry OK/gun |
| --- | ---: | ---: | ---: | ---: |
| Raw full universe | 53,859 | 816.0 | 1,725 | 26.1 |
| Canonical symbol-day | 27,386 | 414.9 | 801 | 12.1 |
| Strict confirmation | 203 | 3.1 | 203 | 3.1 |

Raw ve canonical arasindaki fark buyuk: satirlerin yaklasik `%49`'u duplicate symbol-day gozlemleridir. Bu nedenle 200/gun iddiasi bu CSV ile dogrulanmiyor; gercek production alert count, reject reason ve repeated snapshot telemetry ile ayri olculmelidir.

Signal inflation icin mevcut artifact'te kanitlanan baslica nedenler:

- Ayni symbol-day icinde birden fazla snapshot.
- Full universe satirlarinin entry sinyaliyle karistirilmasi.
- Composite score alaninin 10,858 raw satirda eksik olmasi.
- Component-level reject reason ve feature age bilgisinin bulunmamasi.
- `entry_ok` kararinin historical CSV'de mevcut olmasina ragmen hangi gate tarafindan elendigini gosteren canonical reason dizisinin bulunmamasi.

## 4. Baseline precision

| Kural | N | Sinyal/gun | Precision / hit | False positive | Mean T+5 | Recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| All canonical universe | 27,386 | 414.9 | `%39.5` | `%60.5` | `10.28%` | `%100.0` |
| `entry_ok` | 801 | 12.1 | `%41.6` | `%58.4` | `6.59%` | `%3.1` |
| Precision core | 799 | 12.1 | `%41.4` | `%58.6` | `6.26%` | `%3.1` |
| Strict confirmation | 203 | 3.1 | `%48.3` | `%51.7` | `8.14%` | `%0.9` |

Strict confirmation sinyal sayisini azaltirken hit rate'i artiriyor. Ancak recall'in cok dusuk olmasi ve forward target'in execution P&L olmamasi nedeniyle tek basina production karari degildir.

## 5. Threshold ve ablation bulgulari

Threshold sweep'in en tutarli yonu, volatility/volume kombinasyonlarinin hareket hedefinde daha secici olmasidir. Gap ve direction eklemek her zaman iyilestirmiyor; barrier OOS'ta `ATR6+RVOL2+gap3` PF `0.754`, direction eklenmis varyant PF `0.683` seviyesine gerilemistir.

Composite threshold'lari canonical forward hedefte monoton ve guvenilir bir kalite siralamasi kanitlamiyor. Barrier full-universe OOS'ta 5 gunluk, 2x ATR TP / 1x ATR SL sonuclari:

| Kural | N | Gross expectancy | Cost-adjusted expectancy | PF |
| --- | ---: | ---: | ---: | ---: |
| All | 9,970 | `%0.519` | cost raporundaki baseline | `1.197` |
| Composite >=40 | 1,066 | `%1.299` | `%0.749` | `1.396` |
| Composite >=47 | 712 | `%1.394` | `%0.844` | `1.409` |
| `ATR6+RVOL2` | 347 | `%2.832` | `%2.282` | `1.631` |
| `ATR6+RVOL2+gap3` | 90 | `-%1.628` | `-%2.178` | `0.754` |

Bu tablo discovery ve locked OOS siniflarini karistirmamasi gereken bir execution-style snapshot'tir. `ATR6+RVOL2` sonucu ilgi cekici olsa da tek basina strategy selection icin yeterli degildir.

Ablation yorumu: retrospective ablation, live scanner'i her gate kombinasyonunda yeniden calistirmadigi icin nedensel degildir. Hangi gate'in sinyal kaybettirdigini kesinlestirmek icin production replay ve canonical reject reason telemetry gerekir.

## 6. Top-N ve percentile quota

| Quota | N | Sinyal/gun | Precision | Mean T+5 | Recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| Top-20/gun | 1,138 | 17.2 | `%32.9` | `4.95%` | `%3.5` |
| Top-50/gun | 2,653 | 40.2 | `%32.8` | `8.42%` | `%8.0` |
| Top-100/gun | 4,967 | 75.3 | `%33.5` | `10.72%` | `%15.4` |
| Top-200/gun | 9,045 | 137.0 | `%34.0` | `11.32%` | `%28.4` |
| Top-1%/gun | 314 | 4.8 | `%36.9` | `5.42%` | `%1.1` |
| Top-5%/gun | 1,406 | 21.3 | `%34.6` | `4.88%` | `%4.5` |
| Top-10%/gun | 2,774 | 42.0 | `%34.5` | `6.20%` | `%8.8` |
| Top-20%/gun | 5,507 | 83.4 | `%35.7` | `6.12%` | `%18.2` |

Composite ranking quota, mevcut artifact'te `entry_ok` precision'ini gecmiyor. Bu nedenle “sadece top-N yapalim” cozum olarak GO degildir. Ranking'in quality signal olarak iyilestirilmesi veya score component telemetry'si gerekir.

## 7. Rejim ve volatility

Forward target sonuclarinda bull/bear ayrimi belirgin, volatility regime ayrimi daha serttir:

- Bull canonical universe: `%36.6` hit.
- Bear canonical universe: `%42.4` hit.
- High-volatility: `%46.7` hit.
- Normal-volatility: `%20.8` hit.
- Low-volatility: `%3.0` hit.

High-volatility'te top-50 quota `%40.8` hit verirken normal-volatility'te `%15.8`, low-volatility'te `%2.5` kalmistir. Bu, sabit gunluk quota yerine regime-aware quota veya low-volatility NO-TRADE politikasinin test edilmesini destekler. Ancak vol_regime alaninin point-in-time uretim ve feature age bilgisi artifact'te yoktur.

## 8. Locked OOS ve multiple testing

Temporal split canonical tarihlerde:

- Discovery sonu: `2026-05-13`
- Validation sonu: `2026-06-16`
- Locked OOS: `2026-06-16` sonrasi

Runner'in corrected OOS metrikleri:

| Kural | Discovery N | Validation N | Locked OOS N | OOS precision | OOS mean T+5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `entry_ok` | 576 | 199 | 26 | `%26.9` | `3.22%` |
| Strict confirmation | 149 | 47 | 7 | `%28.6` | `2.25%` |
| Composite >=70 | 86 | 122 | 53 | `%37.7` | `6.34%` |
| ATR >=6 | 1,430 | 2,179 | 3,193 | `%54.2` | `19.89%` |
| RVOL >=2 | 654 | 500 | 1,127 | `%44.0` | `14.58%` |

Bu OOS forward hareket sonuclarinda ATR>=6 yuksek gorunse de, barrier locked OOS ve corporate-action/price-scale kontrolleri olmadan execution edge olarak yorumlanmamalidir. `entry_ok` ve strict confirmation kucuk OOS N nedeniyle karar verici degildir.

## 9. Barrier ve cost karari

Barrier engine ile test edilen grid: 2x ATR TP, 1x ATR SL, 3/5 gun horizon, max entry drift `%0.5`, ATR cap `100`, round-trip cost `%0.55`.

Daha once secilmis full-universe OOS barrier sonucu `ATR6+RVOL2` icin 5 gunde PF `1.631` ve cost-adjusted expectancy `%2.282` vermistir. Buna karsin Alpha V2 locked OOS'ta:

- `composite>=52`: n=53, cost-adjusted expectancy `%0.775`, PF `1.332`.
- `composite>=47`: n=77, cost-adjusted expectancy `-%0.351`, PF `1.046`.
- `ATR6+RVOL2`: n=12, cost-adjusted expectancy `-%1.702`, PF `0.802`.
- All: n=301, cost-adjusted expectancy `-%0.501`, PF `1.018`.

Bu fark, edge'in zaman araligi, artifact ve selection pipeline'ina hassas oldugunu gosterir. Bu nedenle barrier sonucunun production'a tasinmasi **NO-GO**'dur.

Ayrica mevcut barrier grid PF'i gross return uzerinden raporlamaktadir; cost-adjusted expectancy ayri alandir. Gercek cost-adjusted PF icin gross kar/zarar akimlarina execution cost uygulanarak PF yeniden hesaplanmalidir.

## 10. Kullanilmayan ama gerekli deneyler

Asagidaki alanlar enriched CSV'de olmadigi icin sonucu uydurulmadi:

- Sector ve industry concentration.
- Market cap bucket ve capacity.
- Dollar ADV, spread ve market impact.
- Feature age / freshness ve point-in-time component values.
- Canonical reject reason array.
- Corporate action ve split adjustment metadata.
- Full component contribution: filter score, alignment, momentum ve optional factor raw inputs.
- Gercek production replay.
- Duplicate-pattern suppression'in live davranisla yeniden testi.

Bu eksikler tamamlanmadan score weight veya threshold production'da degistirilmemelidir.

## 11. Action plan ve karar kapilari

### P0

1. Production'da her symbol-day icin canonical signal id ve reject reason array persist et.
2. Feature timestamp/age, raw component contribution, spread, dollar ADV, market cap ve sector bilgilerini artifact'e ekle.
3. Corporate action ve price-scale anomaly temizligi yap.
4. Barrier PF'i cost-adjusted gross P&L akimlariyla yeniden hesapla.

### P1

1. Discovery/validation/locked OOS'i rolling walk-forward olarak yenile.
2. Regime-aware quota ve low-volatility NO-TRADE politikasini test et.
3. `entry_ok`, strict confirmation ve top-N icin ayni point-in-time replay'i calistir.
4. Symbol-day cluster bootstrap'i optimize edilmis runner'a 400+ tekrar ile ekle.

### P2

1. Sector/capacity-aware quota.
2. Duplicate snapshot suppression ve signal aging.
3. Rank stability: Spearman rank correlation, top-k overlap ve month-to-month churn.
4. Negative control ve placebo target testleri.

### P3

1. Shadow mode.
2. Paper execution.
3. Drift monitoring ve rollback threshold'lari.

## 12. GO / NO-GO gates

Production degisikligi ancak su kosullarda GO olabilir:

- Locked OOS en az 3 bagimsiz donem veya yeterli trade sayisi.
- Baseline'a gore precision artisi ve recall kaybinin onceden tanimli limit icinde olmasi.
- Aylik pozitiflik ve rejim stabilitesi.
- ATR cap senaryolarinda edge'in korunmasi.
- Cost-adjusted expectancy pozitif ve cost-adjusted PF > 1.
- Cluster bootstrap CI'nin edge'i sifirin ustunde tutmasi.
- Sector/capacity/spread/impact kontrollerinin tamamlanmasi.
- Shadow/paper izleme ve rollback hazirligi.

Mevcut kanit bu kapilari gecmiyor. Son karar: **production threshold/weight/strategy degisikligi yapma; research ve data-contract iyilestirmesine devam et.**

## 13. Artifact listesi

- [Precision selectivity runner](../precision_selectivity_runner.py)
- [Selectivity JSON](../data/backtest_out/precision_selectivity/precision_selectivity_results.json)
- [Selectivity summary CSV](../data/backtest_out/precision_selectivity/precision_selectivity_summary.csv)
- [Full-universe enriched input](../data/backtest_out/full_universe_enriched.csv)
- [Full-universe barrier OOS](../data/backtest_out/phase1_7/barrier_oos_atr100/full_universe_barrier_results.json)
- [Phase 1-7 results](../data/backtest_out/phase1_7/phase1_7_results.json)
- [Alpha V2 locked OOS barrier](../data/backtest_out/alpha_v2/barrier_locked_oos/full_universe_barrier_results.json)
