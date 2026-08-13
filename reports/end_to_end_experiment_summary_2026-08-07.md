# FinPilot Uctan Uca Arastirma Ozeti

Tarih: 2026-08-07
Kapsam: research-only, tarihsel veri, production degisikligi yok
Karar seviyesi: Level A arastirma kosusu; herhangi bir canli kural veya yayin karari degildir.

## Yonetici Ozeti

Bu kosu, raporlarda daha once gecen yeniden uretilebilir deneylerin ayni ana
veriyle tekrar calistirilmasini ve yeni yon onerilerinin veri yeterliligini
kontrol etmeyi kapsar.

Ana sonuc: mevcut kanit, `entry_ok` veya skor tabanli bir giris kuralinin
dogrulanmis ve maliyet-sonrasi saglam bir avantaj oldugunu gostermiyor.

- `entry_ok` 5 gunluk, 2x ATR hedef / 1x ATR stop ve %0,55 maliyet kosulunda
  799 gozlende net ortalama `-%0,6387` uretmistir.
- Standardized P2 kosusunda `entry_ok` icin temel maliyet net ortalama
  `-%0,4426`; sonraki validation doneminde `-%1,1338` olarak raporlanmistir.
- Barrier gridinde 2.520 kombinasyon arasinda cok yuksek ham expectancy
  degerleri vardir; fakat en iyi gorunen secici profillerde medyan getiri
  negatiftir. Ornek: 5x ATR / 20 gun / 1x ATR stop profili `%94,745` ortalama
  ve `-%7,66` medyan uretmistir. Bu outlier ve donem yogunlasmasi bulgusudur.
- Portfoy kosusu 36 konfigurasyonda, %0,55 maliyetle en iyi ekranda yaklasik
  basa bas kalmistir: final equity `$100.515,21`, CAGR `%0,62`, gerceklesen
  gunluk Sharpe `0,2323`, maksimum dusus `-%4,06`, 245 islem.
- Score calibration test Brier `0,248426` ve score bandlari monoton degildir;
  testte 80-100 bandi `n=12` ile yetersizdir.
- Market-neutral excess return, PIT sektor ve bagimsiz forward-range/MAE
  tahmini bu export ile olculemez: benchmark, sektor ve forward high/low
  alanlari yoktur. Bu hipotezler negatif degil, `INSUFFICIENT_DATA` durumundadir.

Bu nedenle sonuc `NO-GO / promotion yok` seklindedir. Locked OOS acilmadi,
shadow baslatilmadi, paper/live emir gonderilmedi ve broker aksiyonu alinmadi.

## Veri Kimligi

- Ana girdi: `data/backtest_out/full_universe_enriched.csv`
- Ana girdi SHA-256: `38b981b372571a01b727d6a51f3fd8b918a770f7a53e552ef55e1629c142e896`
- CSV satiri: target-return kosusunda `53.859`; barrier/portfolio/fixed-target
  kosularinda kullanilan path girdisi `53.746` raw, `27.308` canonical.
- Tarih araligi: `2025-09-11..2026-07-13`; fixed-target artifactinin path
  kapsami `2025-09-11..2026-06-30`.
- Cache: `data/price_cache/`, sembol kapsami `1.929`.
- Standart path modeli: daily OHLC triple-barrier, ayni barda stop-first,
  kayitli scan price girisi, ileri daily path.

Farkli runner'larin raw/canonical sayilari ayni degildir. Bu nedenle her
sonuc kendi artifact'indeki satir sayisi ve input tanimiyla birlikte
yorumlanmistir; sayilar birbirine sessizce birlestirilmemistir.

## Calistirilan Deneyler

### 1. P0-P3 frozen `entry_ok`

Artifact: [end_to_end_entry_ok_p0_p3_2026-08-07.json](../data/backtest_out/end_to_end_entry_ok_p0_p3_2026-08-07.json)

- P0 score replay: `INSUFFICIENT_DATA`; canonical export gerekli score alanlarini tasimiyor.
- P1 matched nulls: label permutation, signal permutation ve time shift aileleri, her biri `1.000` permutation.
- P2: 2x ATR / 1x ATR / 5 gun; maliyetler `%0,25`, `%0,55`, `%1,00` olarak ayri raporlandi. Base maliyet net ortalama `-%0,442591`; validation `-%1,133753`.
- P3: raw execution spread/impact/capacity alanlari bulunmadigi icin `INSUFFICIENT_DATA`.

### 2. Matched null controls

Artifact: [end_to_end_negative_controls_2026-08-07.json](../data/backtest_out/end_to_end_negative_controls_2026-08-07.json)

`entry_ok` adayinin 5 gunluk net ortalamasi `-%0,638710`. Candidate percentile label permutationda `0,020`, signal permutationda `0,272`, time shiftte `0,564` olmustur. Null kosulari bir promotion testi degildir; aday ile null ailelerinin ayri sorular oldugu korunmustur.

### 3. Decision quality / rejection quality

Artifact: [end_to_end_decision_quality_2026-08-07.json](../data/backtest_out/end_to_end_decision_quality_2026-08-07.json)

27.125 resolved gozlemde 26.863 gozlem reddedilmis, ancak reddedilenlerin counterfactual pozitif net orani `%41,7861` olmustur. Eligible alt kume `n=262`, pozitif oran `%32,8244`, net ortalama `-%0,946484` ile tum evrenden daha iyi degildir. Bu, mevcut rejection katmaninin karar-kalitesi kanitini uretmedigini gosterir; yeni veto kurali onaylamaz.

### 4. Score calibration

Artifact: [end_to_end_score_calibration_2026-08-07.json](../data/backtest_out/end_to_end_score_calibration_2026-08-07.json)

23.345 resolved gozlemde train `n=12.403`, test `n=10.942`dir. Brier train `0,236069`, test `0,248426`dir. Test score bantlari artan skorla duzenli sekilde iyilesmemistir; 80-100 bandi `n=12` oldugu icin `insufficient_data`dir.

### 5. Stability, concentration and capacity

Artifact: [end_to_end_stability_capacity_2026-08-07.json](../data/backtest_out/end_to_end_stability_capacity_2026-08-07.json)

Train `n=8.343`, pozitif oran `%36,6535`, ortalama net `%0,2605`; validation `n=8.149`, pozitif oran `%43,4777`, ortalama net `%0,4815`, ancak her iki donemde medyan negatiftir. Sector coverage karar-grade degildir; mevcut likidite snapshot'i tarihsel outcome'lara join edilmemistir. Capacity bu nedenle `INSUFFICIENT_DATA`dir.

### 6. Barrier sensitivity

Artifactlar: [full_universe_barrier_results.json](../data/backtest_out/end_to_end_entry_exit_sweep_2026-08-07/full_universe_barrier_results.json) ve [full_universe_barrier_grid.csv](../data/backtest_out/end_to_end_entry_exit_sweep_2026-08-07/full_universe_barrier_grid.csv)

`TP={1,1.5,2,3,4,5}xATR`, `SL={0.5,0.75,1,1.5,2}xATR`, horizon `{3,5,10,20}` ve `%0,55` maliyet ile `2.520` viable sonuc uretildi. En iyi ham ortalamalar kucuk secici gruplarda ve 10-20 gun horizonlarda toplandi. Median, stop orani, capped mean ve ay bazli dagilim birlikte okunmadan bu ortalama degerler kullanilamaz. Bu grid parametre secimi icin promotion kaniti degildir.

### 7. Fixed-target protocol

Artifactlar: [end_to_end_fixed_target_2026-08-07.md](../data/backtest_out/end_to_end_fixed_target_2026-08-07.md) ve [end_to_end_fixed_target_2026-08-07.json](../data/backtest_out/end_to_end_fixed_target_2026-08-07.json)

`3.120` konfigurasyon yeniden calistirildi. Path coverage `24.731`, train `2.022`, validation `0`, locked holdout unopened kaldi. FDR discovery sayisi tek basina anlamli degildir; gross+period-stable ve cost-positive konfigurasyon sayisi `0`dir. Bu kosu, validation bosken strateji sonucu iddia edilemeyecegini tekrar dogrulamistir.

### 8. Target-return ve adaptive-target deneyleri

Target-return kosusu: [end_to_end_target_return_optimization_2026-08-07.json](../data/backtest_out/end_to_end_target_return_optimization_2026-08-07.json) ve [end_to_end_target_return_optimization_2026-08-07.md](../data/backtest_out/end_to_end_target_return_optimization_2026-08-07.md).

Bu runner yalnizca 1 ve 5 gunluk close-to-close alanlarini kullanir. Peak-touch, exact time-to-hit ve forward high/low MAE/MFE yoktur. Dolayisiyla bu sonuc path aware execution sonucu degil, kapanis-getiri proxy'sidir. Eski adaptive-target artifacti [adaptive_target_experiments.json](../data/backtest_out/adaptive_target_experiments.json) ayni veri sinirini tasir; yeni production target karari icin kullanilmamistir.

### 9. Portfolio simulation

Artifact: [end_to_end_portfolio_2026-08-07](../data/backtest_out/end_to_end_portfolio_2026-08-07)

53.746 input, 53.115 resolved, 36 konfigurasyon ve %0,55 round-trip senaryosu calistirildi. En iyi ekran composite top-10 / ATR-risk / wide-volatility'dir: final equity `$100.515,21`, CAGR `%0,62`, realized daily Sharpe `0,2323`, max drawdown `-%4,06`, 245 trade. Sonuc yaklasik basa bas ve forward execution kaniti degildir.

### 10. Multi-timeframe profiles

Mevcut [multitimeframe_profile_experiment_2026-08-06.md](multitimeframe_profile_experiment_2026-08-06.md) 602 eski suggestion satirindan 265 canonical path sonucu raporlamistir. Confirmatory `n=200`, cost-adjusted expectancy `-%0,377`; early `n=24`, `-%0,315` ve yetersiz orneklemdir. Canonical full-universe export bu alanlari tasimadigi icin bu deney yeni ana veriyle yeniden kosulamamistir; eski sonuc `INSUFFICIENT_DATA` olarak korunmustur.

## Yeni yon hipotezlerinin durumu

| Hipotez | Durum | Neden |
| --- | --- | --- |
| SPY/IWM/sector benchmark'a gore excess return | INSUFFICIENT_DATA | Benchmark forward return alanlari yok |
| Extension/exhaustion ve entry inversion | PARTIAL | gap, ATR ve 52-week distance mevcut; PIT decomposition ve bagimsiz validation yok |
| ATR -> forward range / MAE tahmini | INSUFFICIENT_DATA | export forward high/low tasimiyor; barrier MAE yalnizca outcome summary |
| Gercek PIT sektor analizi | INSUFFICIENT_DATA | sektor coverage ve zaman kesiti decision-grade degil |
| Capacity-first investable universe | INSUFFICIENT_DATA | ADV, spread, impact ve historical liquidity join yok |

ETF proxy veya mevcut sektor cache'i, bu eksikleri benchmark-relative excess return kaniti haline getirmez. Eksik alanlar doldurulmadan bu hipotezler icin negatif sonuc da iddia edilmemelidir.

## Kapilar ve Sinirlar

- P0 tam score equivalence: `INSUFFICIENT_DATA`.
- P1 null diagnostics: calisti; aday-level promotion kaniti degil.
- P2/P3: negatif veya yetersiz; maliyet, median ve zaman istikrari sorunlu.
- Locked OOS: `NOT_OPENED`; insan onayi olmadan acilamaz.
- Execution: `UNKNOWN/INSUFFICIENT_DATA`; gozlenen spread, impact ve fill yok.
- Capacity: `INSUFFICIENT_DATA`; ADV/impact tabanli feasible universe yok.
- Shadow: baslatilmadi.
- Paper/live order, broker aksiyonu, risk limiti, scanner/score/entry-exit ve production/public yayin degisikligi: yapilmadi.

## Sonraki Kanit Ihtiyaci

Bir sonraki research artifacti ancak yeni PIT export su alanlari tasidiginda anlamli olur: benchmark ve sector return serileri, sektor uyeligi zaman kesiti, forward OHLC high/low, feature timestamp/age, ADV, spread/impact, fill price, market-neutral hedge tanimi ve locked validation ayrimi. Bu alanlar geldikten sonra extension/exhaustion, range/MAE ve capacity-first deneyleri yeniden pre-register edilmelidir. Herhangi bir canli kurala ceviri Level B/C onayi gerektirir.
