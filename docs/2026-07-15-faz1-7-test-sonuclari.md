# FinPilot Faz 1-7 Test Sonuclari

**Tarih:** 2026-07-15
**Kapsam:** Production replay/data contract, data quality, single-factor thresholds, family-constrained combinations, cost scenarios ve locked OOS barrier
**Durum:** Research-only. Production scanner kurallari degistirilmedi.

## 1. Calistirilan Pipeline

Yeni research runner:

- `phase1_7_research_runner.py`
- cikti: `data/backtest_out/phase1_7/phase1_7_results.json`
- combination cikti: `data/backtest_out/phase1_7/constrained_combinations.csv`

Execution-style OOS:

- `full_universe_barrier_backtest.py`
- tarih filtresi ve round-trip cost alanlari eklendi
- cikti: `data/backtest_out/phase1_7/barrier_oos_atr100/`

Runner su ciktilari ayni artifact'te topluyor:

1. Partial production replay contract.
2. Component availability ve eksik contribution alani.
3. Canonical symbol-day secimi.
4. Missingness, duplicate ve ATR cap senaryolari.
5. Tek faktorlu threshold metrikleri.
6. No-dedup ve symbol-day metrikleri.
7. No-cost, low-cost, baseline `%0,55`, stress `%1,00` senaryolari.
8. Family-constrained 2-6 factor combinations.
9. Discovery/validation/locked OOS split.
10. Monthly output, median, favorable recall, PF ve drawdown.

## 2. Faz 1: Production Replay ve Veri Kontrati

### 2.1 Yeniden uretilen alanlar

Enriched CSV'den su alanlar ayni snapshot kaydina baglanabiliyor:

- `scan_ts`
- symbol
- entry price
- raw score
- composite score
- regime
- direction
- entry_ok
- FinPilot score, mevcutsa

Toplam satir `53.859`. `scan_ts`, symbol, price, raw score, regime, direction ve entry_ok alanlari dolu. Composite score `10.858` satirda, FinPilot score `24.196` satirda eksik.

`scan_ts + composite + entry_ok` birlikte bulunan satir sayisi `43.001`.

FinPilot ve composite degerleri ikisinin de mevcut oldugu `24.325` satirda ayni. Tum satirlara oran `%45,16`; bu oran FinPilot eksikligi nedeniyle dusuk gorunuyor. Iki alanin da mevcut oldugu alt-kohort icinde pass-through davranisi bekleniyor.

### 2.2 Neden tam replay tamamlanamadi?

Historical enriched CSV production'in gercek point-in-time girdilerinin tamamini tasimiyor. Eksik olanlar:

- 15m, 1h, 4h, 1d OHLCV snapshot'lari,
- her feature'in kendi timestamp'i,
- feature age,
- volume spike, price momentum ve trend strength ham girdileri,
- timeframe alignment oranini olusturan alt girdiler,
- momentum confluence'in alti kriteri,
- canonical `reject_reason[]`,
- spread, dollar ADV ve estimated market impact,
- corporate-action/split adjustment metadata.

Bu nedenle runner'in status'u `partial_replay_only`. CSV'den tam production karari yeniden uretilmis gibi yorumlanmadi.

### 2.3 Component contributions

CSV'den guvenilir olarak yeniden hesaplanabilen contribution prefix:

$$
2 \times regime + 2 \times direction + 0.5 \times raw\_score
$$

Eksik contribution'lar:

- `1.5 × filter_score`
- `2 × alignment_ratio`
- volatility regime'e bagli momentum contribution
- volume spike, price momentum, trend strength
- optional sentiment/catalyst/squeeze/lottery/gap contributions

Sonuc: Her aday icin tam `score_components` kaydi bugunku artifact'ten uretilemiyor. Bunun icin production scanner'in her emitted row'da component breakdown yazmasi gerekir.

### 2.4 Reject reason

CSV'de canonical `reject_reason[]` yok. `entry_ok=False` nedeninin history, regime, direction, raw score, liquidity, earnings veya market safety'den hangisi oldugu tek bir production contract ile ayrilamiyor.

**Faz 1 cikis kriteri:** Basarisiz. Replay ile enriched CSV arasindaki farklarin bir kismi aciklanabiliyor, ancak tam aciklanamayan kisimlar icin gerekli input ve telemetry henuz persist edilmiyor.

## 3. Faz 2: Veri Kalitesi ve Universe Temizligi

### 3.1 Canonical symbol-day

| Olcu | Sonuc |
|---|---:|
| Raw satir | 53.859 |
| Unique symbol-day | 27.386 |
| Duplicate satir | 26.473 |
| Maximum ayni symbol-day satir | 17 |

Canonical observation olarak `(symbol, scan_date)` basina en erken `scan_ts` secildi. Forward ve combination metrikleri hem raw hem canonical olarak uretildi.

### 3.2 Missingness

| Alan | Eksik |
|---|---:|
| Composite | 10.858 |
| FinPilot | 24.196 |
| ATR | 3 |
| Gap | 3 |
| RVOL | 1.949 |
| Target | 0 |

### 3.3 ATR cap senaryolari

| Cap | Tutulan satir | Elenen satir | Elenen oran |
|---:|---:|---:|---:|
| Yok | 53.856 | 3 | `%0,0056` |
| `%50` | 53.653 | 206 | `%0,3825` |
| `%100` | 53.785 | 74 | `%0,1374` |
| `%200` | 53.822 | 37 | `%0,0687` |

Fiyat `<$1` veya ATR `>200%` olan suspicious satir sayisi `2.754`. Bu satirlarin corporate action kaynakli olup olmadigi CSV'den kesinlestirilemiyor.

### 3.4 Eksik veri kalite alanlari

- Corporate-action ve split adjustment metadata yok.
- Dollar ADV yok.
- Bid/ask spread yok.
- Estimated impact yok.

**Faz 2 cikis kriteri:** Kismen tamamlandi. Canonicalization ve ATR cap sensitivity var; corporate-action, spread, dollar ADV ve impact icin veri kaynagi eklenmesi gerekiyor.

## 4. Faz 3: Tek Faktorlu Threshold Testleri

Metrikler su alanlari kapsiyor:

- coverage,
- favorable recall,
- hit-rate,
- mean ve median T+5 return,
- cost-adjusted expectancy,
- PF,
- max drawdown,
- monthly output,
- daily signal count.

Baseline cost `0.55` percentage point olarak uygulandi. Ancak bu metrikler forward T+5 hedefinden gelir; execution-style barrier P&L degildir.

Canonical symbol-day, baseline cost ve ATR `%100` cap sonuclari:

| Factor | n | Coverage | Favorable recall | Hit-rate | Mean net return | Median net return |
|---|---:|---:|---:|---:|---:|---:|
| ATR `>=6` | 6.760 | `%24,72` | `%37,56` | `%59,99` | `%20,27` | `%6,71` |
| RVOL `>=2` | 2.266 | `%8,29` | `%9,50` | `%45,28` | `%15,65` | `%3,63` |
| Gap `>3` | 1.739 | `%6,36` | `%8,84` | `%54,86` | `%19,49` | `%5,44` |
| Raw score `>=3` | 967 | `%3,54` | `%3,65` | `%40,74` | `%17,41` | `%3,11` |
| Composite `>=58` | 1.706 | `%6,24` | `%5,47` | `%34,64` | `%5,30` | `%2,57` |
| Composite `>=70` | 261 | `%0,95` | `%0,99` | `%41,00` | `%6,56` | `%2,90` |
| entry_ok | 801 | `%2,93` | `%3,08` | `%41,57` | `%6,59` | `%3,53` |

Bu tablodaki buyuk mean/PF degerleri suspicious price/ATR satirlari ve `resolved_pct_t5` target'inin olcek anomalilerine duyarlidir. Ayni sebeple max drawdown degerleri bazilarinda `-%100` seviyesine ulasiyor. Bunlar production edge kaniti degildir.

**Interpretation:** ATR>=6 hareket recall'i acisindan raw score ve composite cutoff'larindan daha anlamli; composite>=58 bu temizleme/canonical cohort'ta guclu bir ranking ayrimi gostermiyor.

## 5. Faz 4: 2'li ve 3'lu Combinations

Family constraints uygulandi:

- volatility ailesinden en fazla bir ATR factor,
- volume ailesinden en fazla bir RVOL factor,
- gap/event ailesinden en fazla bir gap factor,
- trend ailesinden en fazla bir direction/regime factor,
- momentum ailesinden en fazla bir raw score factor,
- composite ailesinden en fazla bir composite factor,
- context ailesinden en fazla iki factor.

Boylece `ATR>=4 AND ATR>=6` gibi redundant combination'lar elendi. Toplam aile-kisitli candidate sayisi `165`.

Discovery cohort'ta en ust kombinasyonlar:

1. `ATR>=6 AND RVOL>=2 AND not_near_52w_high`
2. `ATR>=6 AND RVOL>=2`
3. `ATR>=4 AND RVOL>=2 AND not_near_52w_high`
4. `ATR>=4 AND RVOL>=2`
5. `ATR>=6 AND raw_score>=3 AND not_near_52w_high`

Ancak locked OOS'ta ilk iki kombinasyonun mean T+5 sonucu hala cok yuksek ve median ile arasinda buyuk fark var. Ornegin `ATR>=6 AND RVOL>=2`:

- discovery n: `180`
- validation n: `191`
- locked OOS n: `331`
- locked OOS mean net T+5: `%35,04`
- locked OOS median net T+5: `%8,32`
- locked OOS PF: `27,10`
- locked OOS max drawdown: yaklasik `-%99,60`

Bu olcek, target/corporate-action contamination incelemesi tamamlanmadan kullanilamaz. OOS’ta pozitif yon korunuyor gibi gorunse de, drawdown ve mean/median ayrismasi sonucu “stabil trade edge” yapmiyor.

**Faz 4 cikis kriteri:** Family constraint ve split tamamlandi; combination adayligi tamamlanmadi. OOS ve veri kalitesi kapilari gecilmedi.

## 6. Faz 5: Secilmis 4-6 Factor Kurallari

Ilk taramadaki `%68-81` forward hit-rate kazananlari redundant kosullar ve kucuk `n` nedeniyle elenmişti. Family-constrained runner 4-6 factor kombinasyonlarini uretiyor; ancak bunlar discovery sonucu ile otomatik production adayi yapilmiyor.

Secim kurali:

- 3'lu combination once canonical, monthly, cluster ve validation kontrolunden gecmeli.
- Sonra en fazla 5-10 hipotez 4/5 factor'a tasinmali.
- 6 factor onceden tanimli az sayida hypothesis olmali.

Bu raporun current artifact'i family constraint'i uyguluyor, fakat tam 3'lu cluster bootstrap/FDR pipeline'i henuz final gate olarak baglamiyor. Bu nedenle 4-6 sonuclari exploratory kalmaya devam ediyor.

## 7. Faz 6-7: Maliyet ve Locked OOS Barrier

### 7.1 OOS tanimi

Canonical tarih sirasi:

- Discovery: ilk `%50`, son tarih `2026-05-13`
- Validation: sonraki `%25`, son tarih `2026-06-16`
- Locked OOS: `2026-06-17` sonrasi

Barrier OOS konfigurasyonu:

- ATR cap: `%100`
- max entry drift: `%50`
- horizon: `3,5` gun
- TP: `2x ATR`
- SL: `1x ATR`
- same-bar tie: stop-first
- baseline round-trip cost: `%0,55`

Barrier JSON her result icin `cost_adjusted_expectancy_pct = gross expectancy - 0.55` alanini tasiyor. PF burada gross PF olarak kalir; cost-adjusted PF icin trade-level cost uygulanmis P&L serisi gerekir.

### 7.2 Locked OOS barrier sonuclari

| Cohort | n | TP rate | SL rate | Win-rate | Gross expectancy | Cost-adjusted expectancy | Median | Gross PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All | 9.970 | `%25,87` | `%41,38` | `%46,33` | `%0,52` | `-%0,03` | `-%0,50` | `1,20` |
| ATR6+RVOL2 | 347 | `%30,26` | `%45,53` | `%46,97` | `%2,83` | `%2,28` | `-%1,06` | `1,63` |
| ATR6+RVOL2+gap3 | 90 | `%22,22` | `%62,22` | `%35,56` | `-%1,63` | `-%2,18` | `-%7,37` | `0,75` |
| ATR6+RVOL2+direction | 99 | `%21,21` | `%65,66` | `%26,26` | `-%1,81` | `-%2,36` | `-%6,50` | `0,68` |
| ATR6+RVOL2+gap3+not_near_52w_high | 75 | `%24,00` | `%57,33` | `%40,00` | `-%1,08` | `-%1,63` | `-%6,90` | `0,83` |

`ATR6+RVOL2` gross ve cost-adjusted expectancy ile digerlerinden ayriliyor; fakat median negatif, MFE/MAE farki yuksek ve veri olcek anomalileri henuz temizlenmis degil. Bu nedenle “OOS’ta kanitlandi” degil, “OOS’ta tekrar test edilmeye deger ama veri kalite kapisina takildi” demektir.

Composite filtresinin bu interaction'i guclendirdigine dair kanit yok. Onceki barrier testinde composite58 eklenmesi PF'yi `0.46` seviyesine dusurmustu.

## 8. Faz Cikis Kriterleri Durumu

| Faz | Durum | Gerekce |
|---|---|---|
| Faz 1 replay | Kismi | Point-in-time timeframe input, feature age ve reject reason yok |
| Faz 2 data quality | Kismi | Canonical ve ATR cap var; corporate action/spread/ADV yok |
| Faz 3 thresholds | Arastirma tamam | Cost/monthly/recall metrikleri var; target contamination suruyor |
| Faz 4 2-3 combinations | Kismi | Family constraint ve split var; final bootstrap/FDR gate yok |
| Faz 5 4-6 combinations | Exploratory | OOS ve veri kalite sonucu production adayi yapmiyor |
| Faz 6 costs | Kismi | Forward cost ve barrier expectancy subtraction var; trade-level spread/impact yok |
| Faz 7 locked OOS | Kismi | Temporal OOS ve barrier calisti; tam production replay ve temiz target yok |

## 9. Ne Beklemeliyiz?

### Pozitif kabul icin gerekli davranis

Bir combination su kosullari ayni anda saglamali:

1. ATR cap `50/100/200` senaryolarinda isaretini korumali.
2. Median return pozitif veya mean ile makul yakinlikta olmali.
3. Cost-adjusted expectancy pozitif kalmali.
4. Dedup sonrasi PF ve expectancy korunmali.
5. Aylik sonuclar birkac aya bagli olmamali.
6. Rejimlerde tamamen tersine donmemeli.
7. Locked OOS'ta discovery yonunu korumali.
8. Trade-level spread/impact sonrasi halen uygulanabilir olmali.
9. Corporate-action temizliginden sonra performans kaybolmamali.
10. Sinyal hacmi kapasite ve likiditeye uygun olmali.

### Su anki sonuc ne soyluyor?

- `ATR6+RVOL2` arastirma hipotezi olarak tutulabilir.
- `gap3` ve `direction` eklemek mevcut OOS barrier'da performansi bozuyor.
- Composite `>=58/70` production quality gate'i olarak desteklenmiyor.
- Raw score `>=3` secici ama recall'i dusuk.
- OOS'taki cok yuksek forward mean/PF degerleri target/fiyat scale contamination sinyali tasiyor.
- Production replay tamamlanmadan `entry_ok` false-negative sonuclari dogrudan scanner bug'i sayilamaz.

## 10. Sonraki Zorunlu Isler

1. Production scanner her snapshot'ta `score_components`, `component_contributions`, `reject_reason[]`, feature timestamp/age ve data-quality flag yazmali.
2. Enriched dataset'e OHLC adjustment ve corporate-action flag eklenmeli.
3. Dollar ADV, spread ve estimated impact eklenmeli.
4. Barrier trade-level P&L'e spread/slippage uygulanmali; PF de cost-adjusted hesaplanmali.
5. ATR cap senaryolari ayni selected candidate set ile no-cap/50/100/200 olarak tekrarlandirilmali.
6. 3'lu combinations icin monthly stability, symbol-day cluster bootstrap ve FDR final gate yapilmali.
7. Sadece bu gate'leri gecen 5-10 aday 4/5 factor'a tasinmali.
8. Locked OOS tek seferlik degil, rolling walk-forward ile tekrarlanmali.
9. OOS'ta threshold veya weight ayari yapilmamali.
10. Son adaylar shadow/paper modunda izlenmeli.

## 11. Nihai Karar

Bu test bataryasi production stratejisi secmedi; olcum altyapisinin hangi noktalarda guvenilir, hangi noktalarda eksik oldugunu ortaya cikardi.

**Production karari: NO-GO.**

Su an composite weight, entry gate, ATR/RVOL/gap hard gate veya 4-6 factor winner canliya alinmamali. `ATR6+RVOL2` yalnızca veri temizligi, trade-level maliyet ve rolling OOS sonrasi yeniden degerlendirilecek bir arastirma hipotezi olarak tutulmalidir.
