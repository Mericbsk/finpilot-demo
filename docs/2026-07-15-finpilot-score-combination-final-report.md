# FinPilot Composite Score, Threshold ve Combination Testleri

**Tarih:** 2026-07-15
**Kapsam:** Production score yapisi, giris/exit mantigi, ranking, threshold'lar, full-universe factor combinations ve execution-style barrier dogrulamasi
**Durum:** Research-only. Production threshold, weight, entry veya exit davranisi degistirilmedi.

## 1. Bu Raporun Sorusu

Bu calismanin ana sorusu suydu:

> Mevcut FinPilot composite score ve ona bagli factor/threshold yapisi tum evrende daha iyi adaylari secip siraliyor mu; secilen kurallar gercekci execution kosullarinda, maliyet ve zaman disinda da dayanikli mi?

Bu soruyu tek bir backtest ile cevaplamak yerine asagidaki sirayla inceledik:

1. Production score ve karar yolunu haritaladik.
2. CSV veri kalitesini ve production replay sinirlarini kontrol ettik.
3. Composite, raw/entry score ve threshold davranisini test ettik.
4. Tek faktorlu esikleri ve false-negative kohortlarini olctuk.
5. 2'li ve 3'lu interaction altyapisini, sonra secilmis 4-6'li kombinasyonlari calistirdik.
6. Forward movement sonucunu execution-style triple-barrier testiyle karsilastirdik.
7. ATR/outlier duyarliligini ayri cap senaryolariyla kontrol ettik.

Temel karar: **Mevcut composite score production'da agirlik veya threshold degisikligi icin henuz yeterli kanit uretmiyor.** Bazi factor combinations arastirmaya deger; ancak uncapped barrier sonucu, maliyet, locked OOS ve production replay tamamlanmadan strateji secimi yapilamaz.

## 2. Production Yapisi Nasil Calisiyor?

### 2.1 Karar akisi

Mevcut sistem tek bir score ile karar vermiyor:

```text
multi-timeframe input
  -> history / liquidity / safety / earnings gates
  -> regime + direction + raw score
  -> entry_ok
  -> composite_score
  -> finpilot_score / conviction / ranking / sizing
  -> ATR veya Yang-Zhang tabanli stop, TP ve time exit
```

Bu siralama onemlidir. `entry_ok`, aday kabul/red kararidir. `composite_score` esas olarak kabul edilmis veya raporlanmis adaylarin kalitesini siralar ve sizing/risk katmanina bilgi verir. Composite score, mevcut kod akisinda tek basina entry admission gate degildir.

### 2.2 Raw score / entry score

`scanner/evaluate.py` tarafindaki raw score `0-3` araligindadir:

- RSI kosulu,
- volume confirmation,
- rising-positive MACD confirmation.

Production `entry_ok` icin raw score'un tam `3` olmasi gerekir. Bu score, composite score ile ayni sey degildir. Raw score bir eligibility confirmation'i gibi kullanilirken composite daha genis additive recommendation score'udur.

### 2.3 Composite score

`scanner/score_engine.py` composite score'u additive bir formulle hesaplar. Ozetle su aileleri kullanir:

- regime katkisi,
- direction katkisi,
- raw score katkisi,
- filter score,
- timeframe alignment,
- volatility regime'e gore momentum ratio agirligi,
- volume spike, price momentum ve trend-strength gibi kucuk katkilar,
- env ile acilabilen squeeze, catalyst, sentiment, lottery ve gap etkileri.

Teorik maksimum recommendation score `16.5` olarak normalize edilerek `0-100` araligina tasinir. Bu normalization skoru olasilik yapmaz. Ornegin `composite=70`, otomatik olarak `%70 kazanma olasiligi demek degildir`.

### 2.4 FinPilot score

`scanner/finpilot_score.py` su an:

- DRL agirligi: `0.0`
- scanner composite agirligi: `1.0`

Dolayisiyla FinPilot score, mevcut default ayarlarda bagimsiz bir ikinci alpha kaynagi degil; composite score'un pass-through versiyonudur. Kullanici arayuzunde iki ayri skor gibi gorunmesi yanlis bir bagimsizlik algisi yaratabilir.

### 2.5 Exit score

Production'da ayri bir `exit_score` bulunmuyor. Cikislar:

- ATR veya Yang-Zhang volatility tabanli stop/TP,
- momentum tier'ina gore risk parametresi,
- time exit,
- research barrier testinde TP/SL/time barrier.

Trade lifecycle boyunca score decay, exit score update, score aging veya score-based exit state machine telemetry'si yok. Bu nedenle “exit score basarisi” olculemez; exit mantigi ayri bir risk/lifecycle davranisi olarak test edilmelidir.

## 3. Veri ve Production Replay Durumu

### 3.1 Evrensel veri envanteri

`full_universe_enriched.csv`:

| Olcu | Sonuc |
| --- | ---: |
| Toplam satir | 53.859 |
| Unique symbol | 1.932 |
| Scan date | 66 |
| Unique symbol-day | 27.386 |
| Duplicate symbol-day satiri | 26.473 |
| Ayni symbol-day icin maksimum satir | 17 |
| Target eksigi | 0 |
| Composite eksigi | 10.858 |
| FinPilot score eksigi | 24.196 |
| RVOL eksigi | 1.949 |
| ATR eksigi | 3 |
| Gap eksigi | 3 |

Ayni sembol ve ayni gun icin birden cok satir bulunmasi, satirlari bagimsiz gozlem gibi saymayi riskli hale getiriyor. Bu nedenle sonuclari hem raw/no-dedup hem de symbol-day dedup ve cluster bootstrap ile okumak gerekiyor.

### 3.2 Replay siniri

Historical enriched CSV production scanner'in tum point-in-time girdilerini tasimiyor. Bilesen-level score input'lari, timestamp, feature age ve her gate'in gercek reject nedeni her satirda mevcut degil. Bu nedenle su an yapilan testler:

- production kodunun ayni anda yeniden calistirildigi tam replay degil,
- enriched artifact uzerinden retrospective research testidir.

Bunun sonucu olarak `entry_ok=False` veya composite sonucu production'da ayni anda uretilen tam karar olarak yorumlanmamalidir. P0 isi, timestamp-senkron production replay ve `reject_reason[]` telemetry'sidir.

### 3.3 Veri kalitesi uyarisi

Bazi satirlarda ATR ve fiyat olcegi piyasa davranisiyla uyumsuz gorunen extreme observations verdi. Ornek sinif: cok dusuk entry fiyati, cok yuksek ATR yuzdesi ve sonraki barlarda buyuk fiyat olcek degisimi. Bu tip satirlar forward movement ve ATR-scaled barrier expectancy'sini yapay olarak yukseltebilir.

Bu nedenle uncapped sonuclar cap/outlier sensitivity olmadan kullanilamaz.

## 4. Composite Score Audit Sonuclari

### 4.1 Monotonicity testi

Composite score decile'larini T+5 favorable movement hedefiyle karsilastirdik. Taban favorable-mover orani `%38,64`.

| Decile | Hit-rate |
| ---: | ---: |
| 1 | `%42,72` |
| 2 | `%43,86` |
| 3 | `%42,23` |
| 4 | `%39,00` |
| 5 | `%38,12` |
| 6 | `%37,77` |
| 7 | `%39,12` |
| 8 | `%40,54` |
| 9 | `%38,23` |
| 10 | `%42,34` |

Adjacent hit-rate artisi yalnizca `%44,4` oraninda dogru yonde. Dusuk ve yuksek score bucket'lari arasinda tutarli bir monotonluk yok. En ust decile tabanin biraz uzerinde olsa da bu, quality ranking'in guvenilir oldugunu kanitlamiyor.

**Yorum:** Composite score su an “score arttikca beklenen kalite duzenli artar” seklinde kullanilamaz. Score daha cok heuristic bir ranking/summary alanidir; calibrated probability degildir.

### 4.2 Cutoff testi

| Cutoff | Coverage | Hit-rate | Yorum |
| --- | ---: | ---: | --- |
| `composite >=58` | `%6,37` | `%40,37` | Tabandan guclu ayrisma yok |
| `composite >=70` | `%1,07` | `%43,77` | Kucuk ve kırılgan cohort |
| `composite >=80` | `%0,20` | `%50,46` | `n=109`; overfit/kucuk n riski |

Bu cutoffs ayni artifact uzerinde kesfedilip degerlendirildigi icin selection bias vardir. Locked OOS olmadan production cutoff yapilamaz.

### 4.3 Component ve redundancy sorunu

Composite formulu aciklanabilir olsa da her satirda component contribution breakdown bulunmuyor. Ayrica asagidaki aileler ayni bilgiyi birden fazla kez sayabilir:

- trend: regime, direction, trend strength, EMA gap, alignment,
- momentum: MACD, price momentum, momentum ratio, confluence,
- volume: raw volume, volume spike, RVOL,
- event: catalyst, sentiment, gap, squeeze.

Bu double-counting, skorun gercek marginal contribution'ini belirsizlestiriyor. Score ablation ve feature-family attribution, weight degisikliginden once zorunlu.

## 5. Threshold ve False-Negative Testleri

Bu testte false negative tanimi `resolved_pct_t5 >= 5%` favorable mover olup `entry_ok=False` olan satirdir. Bu, otomatik olarak trade edilebilir kâr demek degildir; fill, spread, slippage, stop/TP yolu ve corporate-action kalitesi bu hedefte yoktur.

### 5.1 Ana sonuclar

- Favorable mover sayisi: `20.811`.
- `entry_ok=False` olan favorable mover: `20.067` (`%96,42`).
- Bu proxy tanima gore entry gate recall'i yaklasik `%3,58`.
- Raw score `>=3`: `%4,35` coverage, `%42,56` hit-rate, favorable recall `%4,80`.
- ATR `>=6`: `%22,74` coverage, `%59,60` hit-rate, favorable recall `%35,08`.
- Gap `>=3`: `%5,99` coverage, `%55,03` hit-rate, recall `%8,52`.
- RVOL `>=2`: `%7,97` coverage, `%44,79` hit-rate, recall `%9,24`.

### 5.2 Ne anliyoruz?

Raw score==3 daha secici olsa da hareketlerin buyuk kismini disarida birakiyor. ATR>=6 hareket yakalama acisindan daha anlamli bir proxy; fakat bu tablo execution P&L veya maliyet-sonrasi edge gostermiyor.

Bu nedenle:

- raw score hard gate gevsetilmeli karari henuz verilmedi,
- ATR/gap/RVOL yeni production gate'i yapilmadi,
- bunlar alpha gate'i yerine risk/expansion research feature'i olarak test edilmeli.

## 6. Combination Testleri

### 6.1 Forward movement testi

`full_universe_robustness.py` 2-6 factor combinations icin forward movement sonuclarini, dedup, aylik stability ve symbol-day cluster bootstrap ile calistiracak sekilde genisletildi.

Ilk 4/5/6 factor taramasinda 239 combination uretildi. En iyi gorunen bazi kurallar:

- `ATR>=4 AND ATR>=6 AND RVOL>=2 AND composite>=70`: `n=79`, hit-rate `%81,0`.
- `ATR>=6 AND RVOL>=2 AND direction_up AND composite>=70`: `n=79`, hit-rate `%81,0`.
- Bazi diger 4-6 factor kurallari: `%68-81` hit-rate.

Bu sonuclar aday strateji olarak kabul edilmedi. Nedenleri:

1. `ATR>=4 AND ATR>=6` gibi redundant ayni-aile kosullari taramaya girmisti.
2. Orneklemler `n=61-142` gibi kucuktu.
3. Forward movement hedefi tradeable execution P&L degildir.
4. Ayni tarih ve sembol bagimliligi vardir.
5. Ayni artifact uzerinde cok sayida hipotez tarandi; multiple-testing bias vardir.
6. Maliyet, outlier filtresi ve locked OOS henuz uygulanmamisti.

**Ders:** Daha cok faktorden olusan kural daha iyi kanit anlamina gelmez. Factor sayisi arttikca selection bias, redundancy ve kucuk-n riski hizla buyur.

### 6.2 Barrier predicate registry

Secilmis interaction'lar execution-style barrier testine eklendi:

- `ATR6+RVOL2`
- `ATR6+RVOL2+gap3`
- `ATR6+RVOL2+direction`
- `ATR6+RVOL2+gap3+direction`
- `ATR6+RVOL2+gap3+not_near_52w_high`
- `ATR6+RVOL2+gap3+direction+composite58`
- `ATR6+RVOL2+gap3+direction+not_near_52w_high+composite58`

Barrier modeli:

- ATR-scaled TP/SL,
- 3 ve 5 gun horizon,
- TP multiplier `1.5, 2, 3`,
- SL multiplier `0.75, 1, 1.5`,
- ayni bar TP ve SL olursa stop-first,
- scan-date entry ve sonraki available daily bar path,
- entry drift `0.5` ustu observations rejection.

## 7. Execution-Style Barrier Sonuclari

Asagidaki tablo `TP=2xATR`, `SL=1xATR`, `horizon=5d`, max entry drift `%50` konfigurasyonunu gosterir.

| Cohort | n | Win-rate | Expectancy | Median return | PF |
| --- | ---: | ---: | ---: | ---: | ---: |
| All | 43.031 | `%45,99` | `%0,83` | `-%0,50` | `1,40` |
| `ATR6+RVOL2` | 958 | `%44,15` | `%8,82` | `-%5,74` | `2,84` |
| `ATR6+RVOL2+gap3` | 285 | `%34,39` | `%0,22` | `-%6,68` | `1,03` |
| `ATR6+RVOL2+direction` | 396 | `%30,81` | `-%0,91` | `-%6,60` | `0,83` |
| `ATR6+RVOL2+gap3+direction` | 163 | `%28,22` | `-%1,88` | `-%6,81` | `0,72` |
| `...+not_near_52w_high` | 246 | `%34,55` | `%0,39` | `-%6,75` | `1,06` |
| `...+composite58` | 80 | `%20,00` | `-%3,50` | `-%6,74` | `0,46` |
| `...+not_near_52w_high+composite58` | 49 | `%14,29` | `-%3,95` | `-%6,89` | `0,43` |

### 7.1 Bu tablo neyi gosteriyor?

Uncapped `ATR6+RVOL2` sonucu ilk bakista cok guclu gorunuyor. Ancak:

- Ortalama MFE `%36,30`.
- Ortalama MAE `-%8,96`.
- Medyan getiri `-%5,74`.
- Ortalama ile medyan arasinda buyuk fark var.

Bu pattern, birkac extreme path'in mean expectancy'yi tasiyabilecegini gosterir. Bu nedenle sonucu “tradeable strategy edge” diye adlandirmiyoruz.

Daha da onemlisi, composite filtresi interaction'i iyilestirmedi. `composite58` eklenince PF `0.46` ve expectancy `-%3.50` oldu. Bu, mevcut composite'in bu factor ailesi icin ek kalite sinyali tasimadigina dair guclu bir research negative bulgudur; fakat baska sample veya OOS'ta tamamen ayni kalacagi henuz kanitlanmamistir.

## 8. ATR Outlier Sensitivity

Ayni barrier modeli ATR outlier exclusion ile tekrarlandi. Bu test ATR'yi clamp etmiyor; ATR sinirini asan satirlari cikartiyor.

| Max ATR | ATR6+RVOL2, 5d, TP2/SL1 n | Expectancy | PF |
| ---: | ---: | ---: | ---: |
| Uncapped | 958 | `%8,82` | `2,84` |
| `100%` | 937 | `%2,02` | `1,43` |
| `200%` | 950 | `%1,99` | `1,42` |
| `50%` | 922 | `%1,36` | `1,29` |

Bu test en kritik bulgulardan biridir. Edge'in `%8,82`'den `%1,36-2,02` araligina dusmesi, extreme ATR/fiyat olcegi observations temizlenmeden yuksek expectancy'nin guvenilmez oldugunu gosteriyor.

Repository maliyet modeli round-trip maliyeti `%0,55` varsayiyor. Cap sonrasi `%1,36-2,02` gross expectancy teorik olarak maliyeti asabilir; ancak bu fark:

- spread ve market impact'in tam modellenmesi,
- slippage'in trade bazinda uygulanmasi,
- daily stability,
- locked OOS,
- cluster confidence interval,
- corporate-action temizligi

olmadan production karari icin yeterli degildir.

## 9. Simdiye Kadar Kanitlananlar

### Kanitlanan veya guclu sekilde gozlenenler

1. Composite score decile'lari monoton degil.
2. FinPilot score mevcut default agirliklarla bagimsiz DRL alpha degil.
3. Production'da ayri exit score yok.
4. Raw score==3 ve mevcut hard gate hareket recall'ini ciddi bicimde kisitliyor.
5. ATR/gap/RVOL esikleri forward movement hedefinde secicilik ve recall tradeoff'u yaratıyor.
6. Ilk 4-6 factor taramasinda redundant kosullar ve kucuk-n selection bias uretiyor.
7. Uncapped `ATR6+RVOL2` barrier sonucu outlier'a cok duyarlı.
8. Composite filtresi secilen ATR/RVOL interaction'larinda barrier performansini iyilestirmedi; test edilen ornekte kotulestirdi.

### Henuz kanitlanmayanlar

1. Herhangi bir yeni threshold'un maliyet-sonrasi production edge'i.
2. ATR>=6 veya ATR+RVOL interaction'inin locked OOS'ta stabil kalacagi.
3. `entry_ok` gate'inin gercek trade P&L'ini azalttigi veya artirdigi.
4. Composite agirliklarinin degistirilmesinin alpha yaratacagi.
5. Forward `T+5` hareketinin uygulanabilir fill ve execution sonucuna donusecegi.
6. Sonuclarin farkli rejimlerde ve aylarda tekrarlanacagi.

## 10. Beklememiz Gerekenler

Mevcut sonuclardan sonra beklenmesi gereken sey “tek bir en iyi kombinasyon” degil, asagidaki filtrelerden gecen kucuk bir aday listesidir.

### Beklenen pozitif senaryo

Bir factor combination ancak su davranisi gosterirse umut verici sayilabilir:

- ATR cap sonrasinda expectancy tamamen kaybolmaz.
- Maliyet sonrasi expectancy pozitif kalir.
- Median return ve mean return arasindaki fark makul olur.
- PF `1`'in anlamli bicimde ustunde kalir.
- Aylik sonuclarin buyuk kismi pozitif veya en azindan tutarlidir.
- Symbol-day dedup ve cluster bootstrap sonrasi sonuclar korunur.
- Bull/bear/sideways rejimlerin en az ikisinde tamamen bozulmaz.
- Discovery disindaki locked OOS'ta ayni yonu korur.
- Kucuk factor degisikliklerinde performans cliff yapmaz.
- Gunluk sinyal sayisi ve likidite uygulanabilir kalir.

### Beklenen negatif veya alarm senaryosu

Asagidaki durumlardan biri varsa hipotez production'da elenir veya yeniden tasarlanir:

- Capped ve uncapped sonuclar arasinda buyuk fark.
- Mean pozitifken median belirgin negatif.
- PF `1` civarina maliyetle iner.
- Edge bir-iki ay veya birkac sembol tarafindan tasinir.
- Dedup sonrasi `n` ve expectancy cok duser.
- Composite eklenince performance kotulesir.
- OOS'ta isaret tersine doner.
- Sadece cok kucuk `n` ile yuksek hit-rate gorulur.
- Ayni factor ailesinden redundant kosullar sonucu sisirir.

## 11. Siradaki Test Sirasi

### Faz 1: Production replay ve veri kontrati

1. Aynı timestamp'te production input'larini yeniden uret.
2. Her aday icin `score_components` ve component contributions kaydet.
3. Her reddedilme icin canonical `reject_reason[]` yaz.
4. Feature timestamp, feature age, missingness ve data-quality flag ekle.
5. `entry_ok`, composite ve FinPilot score'un ayni snapshot'tan geldigini dogrula.

**Cikis kriteri:** Replay ile enriched CSV arasindaki farklar aciklanabilir olmali.

### Faz 2: Veri kalite ve universe temizligi

1. Symbol-day canonical observation sec.
2. Corporate-action ve fiyat scale anomalilerini ayir.
3. ATR cap senaryolarini `none/50/100/200` olarak standardize et.
4. Dollar ADV, spread ve estimated impact ekle.
5. Her testte outlier exclusion count raporla.

**Cikis kriteri:** Sonuc birkac bozuk fiyat/ATR satirina bagli olmamali.

### Faz 3: Tek faktorlu threshold testleri

ATR, RVOL, gap, raw score, regime, direction ve composite threshold'lari ayri test et.

Her threshold icin ayni anda su metrikler raporlanmali:

- coverage,
- favorable recall,
- daily signal count,
- barrier win/loss/time,
- median return,
- cost-adjusted expectancy,
- PF,
- max drawdown,
- aylik stability.

**Cikis kriteri:** Threshold sadece hit-rate ile secilmemeli.

### Faz 4: 2'li ve 3'lu combinations

2'li combinations tamamlanmali; 3'lu combinations ana interaction testi olarak calistirilmali. Factor registry aile bazli olmali:

- volatility: en fazla bir ATR threshold,
- volume: en fazla bir RVOL/volume factor,
- gap/event: en fazla bir,
- trend: direction/regime/alignment ailesinden en fazla bir,
- momentum: en fazla bir,
- context: en fazla iki,
- composite: en fazla bir.

`ATR>=4 AND ATR>=6` gibi redundant combinations elenmeli.

**Cikis kriteri:** 3'lu combination ancak dedup, aylik stability, cluster bootstrap ve discovery/validation split sonrasinda aday olabilir.

### Faz 5: Secilmis 4/5/6 combinations

Yalnizca 3'lu testte stabil gorunen 5-10 hipotez yuksek dereceli kombinasyonlara tasinmali. 6'li combinations onceden tanimli, az sayida hypothesis olarak kalmali.

**Cikis kriteri:** Her secilmis combination forward movement ve barrier testinden ayri ayri gecmeli.

### Faz 6: Maliyet ve execution

En az su senaryolar raporlanmali:

- no-cost,
- dusuk maliyet,
- repository baseline round-trip `%0,55`,
- stress slippage/spread.

Cost-adjusted expectancy, PF, turnover, daily capacity ve impact birlikte verilmeli.

### Faz 7: Locked OOS ve walk-forward

Ilk onerilen temporal split:

- discovery: ilk `%50`,
- validation: sonraki `%25`,
- locked OOS: son `%25`.

OOS esikleri ve weights ayarlamak icin kullanilmamali. Daha sonra rolling walk-forward ile farkli rejimlerde tekrar edilmelidir.

### Faz 8: Shadow/paper

Backtestten gecen adaylar production scanner'a davranis degistirmeden shadow olarak eklenmeli. En az:

- sinyal gecikmesi,
- fill/entry drift,
- spread/slippage,
- reject reason,
- score component stability,
- exit reason,
- realized MFE/MAE,
- capacity

loglanmali.

## 12. Production Karari

### Su an yapilmamasi gerekenler

- Composite weight degistirmek.
- `composite>=58/70/80` cutoff'unu BUY gate yapmak.
- Raw score hard gate'ini gevsetmek veya kaldirmak.
- ATR>=6, RVOL>=2 veya gap>=3'u production hard gate yapmak.
- Uncapped `ATR6+RVOL2` barrier sonucuna dayanarak strateji secmek.
- Kucuk-n 4-6 factor winner'larini canliya almak.
- Ayrica bir exit score uydurmak.

### Su an yapilmasi gerekenler

1. Production replay ve reject telemetry.
2. Canonical symbol-day ve corporate-action veri temizligi.
3. Family-constrained combination manifest.
4. Cost-adjusted capped barrier testleri.
5. Monthly/regime/dedup/cluster bootstrap raporu.
6. Locked temporal OOS.
7. Sonuclari shadow/paper ortaminda izlemek.

## 13. Son Nihai Degerlendirme

FinPilot composite score aciklanabilir bir additive formula olsa da bugunku artifact'te guvenilir, monoton ve kalibre bir quality ranking olarak kanitlanmamistir. Raw/entry gate hareket recall'ini ciddi bicimde kisitliyor gorunmektedir; ancak bu bulgu production replay olmadan dogrudan gate bug'i olarak adlandirilamaz.

ATR ve RVOL birlikte kullanildiginda hareket ve barrier sonuclarinda ilgi cekici bir signal goruluyor. Fakat uncapped sonucu ATR outlier'larina cok duyarli; cap sonrasi edge belirgin bicimde kuculuyor. Gap, direction ve composite eklemek mevcut sample'da bu edge'i korumadi. Bu nedenle su anki en dogru yorum:

> Bir strateji kesfi tamamlanmadi; veri ve scoring pipeline'inin hangi kosullarda guvenilir olabilecegini gosteren bir arastirma haritasi cikarildi.

Bir sonraki guvenilir kilometre tasi, production replay + temizlenmis veri + cost-adjusted locked OOS barrier testidir. Bu kapilar gecilmeden production'da score, threshold veya strategy selection degisikligi yapilmamalidir.

## 14. Ilgili Artifact ve Raporlar

- [Composite score ve ranking audit](2026-07-15-composite-score-ranking-audit.md)
- [Threshold ve false-negative audit](2026-07-15-threshold-false-negative-audit.md)
- [Score/threshold/combination test plani](2026-07-15-score-threshold-combination-test-plan.md)
- [Composite audit JSON](../data/backtest_out/composite_score_audit.json)
- [Threshold audit JSON](../data/backtest_out/threshold_false_negative_audit.json)
- [Barrier grid CSV](../data/backtest_out/full_universe_barrier_grid.csv)
- [Uncapped barrier results](../data/backtest_out/full_universe_barrier_results.json)
- [ATR 50% cap results](../data/backtest_out/barrier_atr50/full_universe_barrier_results.json)
- [ATR 200% cap results](../data/backtest_out/barrier_atr200/full_universe_barrier_results.json)

## 15. Faz 1-7 Uygulama Sonuclari

Faz 1-7 test programinin calistirilmis, artifact'e bagli sonuclari ayri raporda
toplandi: [Faz 1-7 test sonuclari](2026-07-15-faz1-7-test-sonuclari.md).

Ozet karar degismedi:

- production replay status `partial_replay_only`;
- 53.859 raw satir, 27.386 unique symbol-day ve 26.473 duplicate satir;
- family-constrained candidate sayisi 165;
- locked OOS baslangici `2026-06-17`;
- execution-style OOS'ta `ATR6+RVOL2` gross expectancy `%2,832`, baseline `%0,55`
  subtraction sonrasi `%2,282`;
- ayni OOS'ta `ATR6+RVOL2+gap3` `-%2,178`,
  `ATR6+RVOL2+direction` `-%2,355` cost-adjusted expectancy;
- bu degerler trade-level spread/impact ve corporate-action temizligi olmadan
  production kaniti sayilmaz.

Bu nedenle composite weight, entry gate, exit multiplier veya yeni 4-6 factor
strategy canliya alinmadi. `ATR6+RVOL2` yalnizca yeniden test edilecek arastirma
hipotezi olarak tutuldu.

Alpha V2'nin ayri olarak yeniden kurulan Faz 1-7 bataryasi icin [Alpha V2 Faz 1-7
test sonuclari](2026-07-15-alpha-v2-faz1-7-test-sonuclari.md) raporuna bakiniz.
Bu testte offline V2 score forward harekette secici gorunse de locked execution
OOS'ta baseline maliyet sonrasi pozitif kalmadi. Ayrica Alpha V2'nin gap/RVOL/
extension faktorlari mevcut production composite score yoluna bagli degil; bu
nedenle offline V2 sonucu production V2 kaniti degildir.
