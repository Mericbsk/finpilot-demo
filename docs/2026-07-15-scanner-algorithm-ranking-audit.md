# FinPilot — Scanner Algoritma, Filtre ve Ranking Kalitesi Sert Audit

**Tarih:** 2026-07-15
**Kapsam:** Canli scanner filtreleri, composite score, alert ranking, full-universe hareket testi ve mevcut ablation/robustness kaniti
**Audit girdisi:** `data/backtest_out/full_universe_enriched.csv`
**Audit scripti:** `scanner_algorithm_ranking_audit.py`
**Durum:** Research ve production-readiness auditidir; canli karar degisikligi yapmaz.

> Audit sonucu birinci el kod incelemesi ile mevcut full-universe sonuc artifact'inin birlikte okunmasina dayanir. Bir feature'in kodda bulunmasi, tarihsel olarak edge urettigi anlamina gelmez.

---

## 1. Executive Summary

### P0 bulgular

1. **Production scanner bir ranking motorundan once hard-gate motorudur.** `scanner/evaluate.py` icinde rejim, direction, raw score ve likidite karar verir. Composite score daha sonra hesaplanir; `alignment_ratio`, `momentum_ratio` ve `filter_score` composite icinde bulunur fakat `entry_ok` hard gate'inin parcasi degildir.
2. **Config ile gercek karar yolu arasinda drift var.** `min_alignment_ratio`, `min_momentum_ratio` ve `min_filter_score` ayarlari mevcut olmasina ragmen production entry kararini beklenen sekilde degistirmiyor. Odak testleri bu davranisi `62 passed` ile tekrar dogruladi; testlerin yesil olmasi drift'in iyi oldugu anlamina gelmez.
3. **Composite ranking monoton degil.** Full-universe auditinde composite decile'lari yuksek skora dogru istikrarlı bir hit-rate artisi gostermiyor. Composite'in en ust decile'i `%40.45`, genel taban `%38.64`; bu kucuk fark ranking edge'ini kanitlamiyor.
4. **ATR hareket yakalama sinyali olarak guclu gorunuyor, ancak islem edge'i olarak henuz temiz degil.** ATR decile'lari `%7.98`den `%62.24`e kadar yukseliyor; buna ragmen onceki barrier testi extreme ATR/corporate-action outlier'larina cok duyarlıydi.
5. **Tarihsel artifact canli karar yolunu birebir yeniden uretmiyor.** CSV'de `entry_ok=True` toplam `%3.20` iken teorik sequential `regime -> direction -> raw_score_3 -> liquidity_ok -> entry_ok` zinciri `%0.60` seviyesine iniyor. Bu fark lineage/config/replay problemi olarak ele alinmali.
6. **`entry_ok` ayrimi zayif.** Full universe'te `entry_ok=True` hit-rate `%43.13`, `entry_ok=False` `%38.5`; lift yaklasik `1.12`. Bu, gate'in tamamen degersiz oldugunu degil, ranking/selection kalitesini tek basina aciklamadigini gosterir.
7. **Gercek compound signal henuz kanitlanmadi.** `ATR6+RVOL2` favorable movement'ta yuksek gorunuyor; ancak interaction faydasi ayni veri, outlier ve hareket hedefi sinirlari icinde. Maliyet-sonrasi, OOS ve cluster-inference olmadan “compound alpha” denemez.

### Net karar

Canli scanner'a yeni ATR/RVOL gate'i veya yeni composite agirligi eklenmemeli. Once:

```text
config/lineage duzeltmesi
-> veri kalite ve corporate-action duzeltmesi
-> production replay
-> OOS ve cluster inference
-> maliyetli barrier/execution testi
-> shadow mode
```

---

## 2. Filtre Mimarisi

### 2.1 Gercek akıs

```text
Sembol evreni
   |
   +--> delisted sembol hard exclusion
   |
   +--> multi-timeframe veri ve minimum bar kontrolu
   |       15m >= 15, 1h >= 10, 4h >= 15, 1d >= 50
   |
   +--> daily regime: close > EMA200 (yoksa EMA50 fallback)
   |
   +--> daily direction: close > EMA50
   |
   +--> raw score:
   |       RSI 30-70
   |       Volume > 20d median * 1.2
   |       MACD histogram > 0 ve oncekinden yuksek
   |
   +--> liquidity:
   |       price >= 2.0
   |       10d average volume >= 300,000
   |
   +--> market safety ve earnings blackout
   |
   +--> feature computation:
   |       filter_score, alignment, momentum confluence,
   |       volatility regime, squeeze, catalyst, sentiment,
   |       lottery ve overnight gap
   |
   +--> composite score 0-100
   |
   +--> regime x score position-size multiplier
   |
   +--> API enrichment / shortlist persistence
   |
   +--> watchlist veya alert secimi
```

### 2.2 Katmanlarin gercek sorumlulugu

| Katman | Kod | Gercek gorev |
|---|---|---|
| Evaluation | `scanner/evaluate.py` | Sembol bazli veri, feature, hard gate ve output contract |
| Score | `scanner/score_engine.py` | Additive composite score ve 0-100 normalization |
| Position sizing | `regime_gate_mult()` | Score/rejim bandina gore sizing multiplier; entry gate degil |
| API | `api/routers/scan.py` | Enrichment, persistence, watchlist ve summarize orkestrasyonu |
| Alert | `agents/alert_agent.py` | `entry_ok` adaylari; conviction flag aciksa rank + cap |
| Summary | `scanner/scan_summary.py` | Ayrı shortlist; conviction prob sonra composite ile siralama |

### 2.3 Sequential mi parallel mi?

- Veri yeterliligi, rejim, direction, raw score ve likidite mantiksal olarak sequential hard gate'tir.
- Feature'larin bir kismi ayni input uzerinde parallel/ayri hesaplanir.
- Composite score hard gate'lerden sonra hesaplanir.
- API ve alert secimi evaluation'dan ayridir.
- Bu ayrim iyi bir sorumluluk siniri yaratir; fakat kullaniciya yansiyan “tek ranking” yoktur. `composite_score`, `conviction_prob`, `conviction_tier`, early tier ve bazen `finpilot_score` farkli karar dilleri olusturur.

### 2.4 Redundant veya cakisan kurallar

1. **Volume tekrarli bilgi:** Raw score icinde current volume / 20d median kontrolu, filter_score icinde volume_spike, composite icinde hem filter_score hem volume_spike bulunur. Ayni hacim olayinin iki kez odullendirilme riski vardir.
2. **Trend tekrarli bilgi:** Regime, direction, trend_strength ve EMA gap ayni trend ailesinin parcasi olabilir. Aralarindaki incremental contribution olculmeden hepsini toplamak weight stacking riskidir.
3. **Momentum tekrarli bilgi:** Raw MACD, price_momentum, momentum_ratio, momentum_confluence ve alignment ayni fiyat hareketini farkli pencerelerde yeniden puanlayabilir.
4. **Composite ve conviction ayrimi:** Ayni sembol hem composite hem conviction probability ile siralanabilir; kullanici bu iki siralamanin neden ayrildigini goremeyebilir.

---

## 3. Kaba Filtreler Analizi

### 3.1 Olcumle gorulen attrition

Audit CSV'sinde hedefi bulunan `53,859` satir icin teorik sequential gate taramasi:

| Asama | n | Tum evrene oran | T+5 >=5 hit-rate |
|---|---:|---:|---:|
| Tum evren | 53,859 | 100.000% | 38.64% |
| Regime | 28,393 | 52.717% | 36.44% |
| Direction | 23,706 | 44.015% | 37.43% |
| Raw score 3 | 1,095 | 2.033% | 39.82% |
| Liquidity | 333 | 0.618% | 47.45% |
| Entry OK | 324 | 0.602% | 48.46% |

Bu tablo canli gate'in birebir production replay'i degildir; cunku CSV satirlarinin bazilarinda config ve output alanlari farkli lineage ile uretilmis olabilir. Yine de erken gate'lerin evreni cok sert daraltabildigini gosterir.

### 3.2 Kaba veya kör olma ihtimali tasiyan filtreler

#### Regime gate

- **Kural:** Daily close EMA200 uzeri; yetersiz gecmiste EMA50 fallback.
- **Risk:** Event-driven, reverse/fade veya yeni breakout setup'lari uzun vadeli EMA rejimi uygun olmadigi icin elenebilir.
- **Veri:** Regime grubunun hareket hit-rate'i tum evrenden dusuk (`%36.44` vs `%38.64`). Bu, “boga rejimi her zaman daha iyi” varsayimini desteklemiyor.
- **Karar:** Kaba ve su an hareket hedefinde faydasi kanitlanmamis; daha cok risk-policy filtresi olarak etiketlenmeli.

#### Direction gate

- **Kural:** Daily close > EMA50.
- **Risk:** Erken reversal, squeeze, catalyst ve short-covering setup'lari dislanabilir.
- **Veri:** Sequential direction cohort `%37.43` ile baseline'a yakin.
- **Karar:** Hareket yakalama icin güçlü bir gate oldugu kanitli degil.

#### Raw score == 3

- **Kural:** RSI bandi + hacim medyan carpani + rising positive MACD'nin ucu birlikte.
- **Risk:** Sadece iki kosulu tasiyan veya RSI 70 uzerinde ama catalyst destekli momentum hisseleri dislanabilir.
- **Veri:** Full artifact'te raw score 3 cohort'u kucuk ve hit-rate `%39.82`; buyuk bir ayrisma gostermiyor.
- **Karar:** “Necessary but not sufficient” gibi davranmali; kesin AL gate'i olarak kullanilmasi yeniden test edilmeli.

#### Minimum fiyat ve hacim

- **Kural:** Fiyat `>=2.0`, 10d average volume `>=300k`.
- **Risk:** Dolar hacmi ve spread bilinmeden share-volume esigi liquidity'yi yanlis olcebilir. Düşük fiyatli ama gercekten likit veya asimetrik payoff tasiyan setup'lar dislanabilir.
- **Kanıt:** Esiklerin her piyasa rejimi ve fiyat segmentinde cost-adjusted fill ile dogrulandigi gosterilmedi.
- **Karar:** “Guvenli” degil; su an “olculmemis kaba” filtredir. Dolar hacmi, spread ve market impact ile yeniden tanimlanmali.

### 3.3 Kaba ama guvenli ile kaba ve kör farki

- **Kaba ama guvenli:** Zarari veya fill riskini azalttigi, farkli rejimlerde stabil oldugu ve kaybettigi setup turlerinin bilincli olarak kabul edildigi filtre.
- **Kaba ve kör:** Threshold'u sezgisel, farkli segmentlerde test edilmemis, kacirdigi setup'lar izlenmeyen ve sonucu yalniz “daha az sinyal” oldugu icin guvenli sanilan filtre.

Mevcut minimum price/volume ve EMA gate'leri ikinci kategoriye daha yakindir; bunlarin risk-policy oldugu kanitlanana kadar alpha filtresi gibi yorumlanmamalidir.

---

## 4. Dar Filtreler Analizi

### 4.1 Asiri dar olma riski

- Raw score 3, erken kombinasyonlarin buyuk kismini eliyor.
- `entry_ok` yalnizca `%3.20` satirda true gorunuyor; teorik cumulative gate ise `%0.60` seviyesine iniyor.
- Bu, guvenli sinyal sayisi degil; replay/lineage farki da iceren bir coverage alarmidir.

### 4.2 Ozellikle kaybolabilecek setup'lar

1. **Event-driven continuation:** RSI 70 ustu oldugu icin raw gate'te elenebilir.
2. **Early breakout:** EMA50/EMA200 henuz hizalanmadan hareket baslayabilir.
3. **Reversal ve short-covering:** Daily direction ve regime negatifken en yuksek asimetrik hareketler olusabilir.
4. **Low-price ama likit momentum:** Fiyat floor'u share price'a bakar; dollar volume ve spread bakmaz.
5. **High-volatility expansion:** ATR/volatility yuksek olan setup'lar riskli diye elenebilir; oysa testlerde ATR hareket yakalama ile en guclu iliskiyi verdi.
6. **Catalyst ile gelen asiri momentum:** RSI/MACD “fazla sicak” oldugu icin filtrelenebilir.

### 4.3 Earnings blackout

Earnings blackout operasyonel risk kontrolu olarak makul olabilir; fakat event-driven alpha'nin buyuk bir kismini bilerek dislar. Bu kural alpha filtresi degil, ayri bir event-risk modu olarak raporlanmali ve earnings sonrasi momentum ile ayri olculmelidir.

---

## 5. Heuristik ve Overfit Riski

### 5.1 Heuristik kurallar

Asagidaki kurallar kodda mevcut, ancak her biri icin ayni veri uzerinde ayrilmis ve cost-adjusted kanit yoktur:

- RSI `30-70`
- Volume `1.2x` 20d median
- `price >= 2.0`
- `average volume >=300k`
- EMA50/EMA200 rejim ve direction
- Fixed composite ceiling `16.5`
- Volatility regime momentum weights `2.5 / 2.0 / 1.5`
- Squeeze `+1.5`
- Catalyst `+/-1.5`
- Lottery penalty `-2.0`
- Overnight penalty `-1.0`
- High score regime threshold `58`
- Bear score band boost `1.3`

Heuristik olmak problem degildir. Problem, bu esiklerin hangi hedef ve hangi OOS doneminde secildiginin tek bir config manifestinde kayitli olmamasidir.

### 5.2 Overfit sinyalleri

1. **Coklu threshold taramasi:** Score, composite, ATR, gap, RVOL ve squeeze icin cok sayida esik test edildi. En iyi bucket'i ayni veride secmek multiple-testing bias yaratir.
2. **Kucuk elit bucket'lar:** Composite `>=80` gibi gruplar kucuk n ile iyi gorunebilir.
3. **Dönem bagimliligi:** ATR/RVOL barrier sonucu Nisan outlier'larindan ve Temmuz negatif performansindan etkileniyor.
4. **Outlier bagimliligi:** ATR cap testinde `ATR` siniri yokken expectancy `%8.82`; `ATR<50` iken `%1.35`.
5. **Score tuning:** Composite'in sabit ceiling'i ve score weight degisiklikleri percentile cut-off'u koruma amaciyla ayarlanmis; bu bir calibration policy'dir, yeni OOS edge kaniti degildir.
6. **Selection bias:** `ATR6+RVOL2` sonucu ayni evren uzerinde hem kesif hem raporlama ile one cikti.

### 5.3 Gercek edge mi ezber mi?

- **ATR:** Full-universe decile'larinda monotonic movement lift verdigi icin en guclu research adayi. Fakat corporate-action ve volatility leakage temizlenmeden edge denemez.
- **RVOL:** Tek basina zayif-orta; decile pattern monotonic degil, esik `>=2` hit-rate `%44.8`.
- **ATR+RVOL:** Interaction movement'ta yuksek; OOS ve cost-adjusted execution kaniti eksik.
- **Composite:** Decile lift duz degil; mevcut composite siralamasinin hareket hedefinde guclu ranking yaptigi kanitlanmadi.
- **entry_ok:** Kucuk pozitif lift; barrier sonucunda `ATR6+entry_ok` avantajli cikmadi.

---

## 6. Ranking Aciklanabilirlik Durumu

### 6.1 Aciklanabilir kisimlar

`scanner/score_engine.py` sabit additive bir formül kullaniyor. Temel agirliklar:

| Bilesen | Agirlik |
|---|---:|
| Regime | +2 |
| Direction | +2 |
| Raw score | `score * 0.5` |
| Filter score | `filter_score * 1.5` |
| Alignment ratio | `ratio * 2` |
| Momentum ratio | volatility regime'e gore `1.5-2.5` |
| Volume spike | +0.5 |
| Price momentum | +0.5 |
| Trend strength | +0.5 |
| Sentiment | opsiyonel `+/-0.5` |
| Squeeze | opsiyonel `0..+1.5` |
| Catalyst | opsiyonel `-1.5..+1.5` |
| Lottery | opsiyonel `0..-2.0` |
| Overnight | opsiyonel `0..-1.0` |

Bu nedenle “skor neden 14?” sorusuna teknik olarak cevap verilebilir.

### 6.2 Aciklanabilir olmayan veya karisan kisimlar

1. Kullaniciya ayni anda composite, finpilot_score, conviction_prob, conviction_tier ve early tier gorunebilir.
2. Bir sinyalin “neden ustte” oldugu ile “neden `entry_ok` oldugu” farkli olabilir.
3. Alert ranking conviction probability -> composite score kullaniyor; summary path de benzer ama ayri selection yapabiliyor.
4. Score decomposition her output'ta normalize edilmis katkilar halinde zorunlu bir trace olarak saklanmiyor.
5. “Bu neden A degil B?” sorusuna kanonik cevap verecek tek Grade fonksiyonu yok.

### 6.3 Gerekli trace alanlari

Her sinyal snapshot'inda saklanmali:

- `config_version`, `git_sha`, `feature_flags`
- hard-gate pass/fail ve fail reason listesi
- raw score componentleri
- filter score componentleri
- her composite componentinin ham degeri, agirligi ve katkisi
- optional feature availability ve neutral fallback durumu
- pre-rank score, final rank score, conviction score
- rank cohort ve selection reason
- data provider, `as_of`, bar timestamp ve adjustment status

---

## 7. Skor Agirliklari Analizi

### 7.1 Agirlik carpikliklari

- Regime + direction toplam `4` puanlik sabit binary katkidir; bu, partial trend evidence'i binary hale getirir.
- Filter score maksimum `4.5` puanla raw score'un maksimum `1.5` katkisini ezer.
- Alignment ve momentum ratio birlikte `4.5`e kadar cikabilir; bunlar trend/momentum ailesiyle korele olabilir.
- Volume bilgisi raw score, filter score ve binary volume_spike uzerinden tekrar gelebilir.
- Optional squeeze/catalyst/lottery agirliklari production varsayilaninda kapali olsa da flag kombinasyonuna gore skor dagilimini degistirir.
- Normalization ceiling `16.5` sabit; optional additive factors ceiling'i genisletmeden numerator'a ekleniyor. Bu calibration'i flag setine duyarlı hale getirir.

### 7.2 Sabit mi dinamik mi?

Agirliklarin hepsini dinamik yapmak dogru ilk adim degil. Once:

1. Korrelated feature gruplarini tek latent aile veya cap ile sinirla.
2. Her aile icin incremental ablation yap.
3. OOS doneminde weight stability kontrol et.
4. Ancak sonra rejim/likidite segmentine gore dynamic scaling dene.

Şu anki en buyuk sorun agirligin sabit olmasi degil; ayni bilginin birden fazla component ile toplam skora girebilmesi ve bunlarin OOS incremental katkisinin kayitli olmamasidir.

---

## 8. Compound Signal Var Mi?

### 8.1 Olcumler

Full-universe movement hedefinde:

| Cohort | n | Hit-rate |
|---|---:|---:|
| Tum evren | 53,859 | 38.64% |
| ATR >= 6 | 12,248 | 59.60% |
| RVOL >= 2 | 4,291 | 44.79% |
| ATR >= 6 + RVOL >= 2 | 1,283 | 64.30% |
| entry_ok | 1,725 | 43.13% |
| ATR >= 6 + entry_ok | 385 | 65.20% |

Bu tablo ATR ile RVOL'un birlikte secilen hareketlerde zenginlesme sagladigini gosteriyor; fakat “synergy” demek icin su ek kontroller gerekir:

- interaction term ve confidence interval
- train/OOS ayrimi
- symbol-day cluster bootstrap
- corporate-action temizligi
- cost-adjusted barrier sonucu
- marginal contribution: ATR varken RVOL ne ekliyor, RVOL varken ATR ne ekliyor?

### 8.2 Sahte compound riskleri

- ATR, RVOL ve gap ayni volatility/attention olayinin farkli gorunumleri olabilir.
- Composite score, trend/momentum feature'larini tekrar topladigi icin “daha cok feature” “daha cok bilgi” anlamina gelmez.
- `ATR6+RVOL2` sonucu favorable high hedefinde iyi olabilir, ancak onceki barrier sonucunda extreme outlier'lara ve donemlere duyarlidir.

**Karar:** Su an gercek compound signal degil, umut verici ama henuz dogrulanmamis bir interaction adayidir.

---

## 9. Yanlis Metrikler ve Yaniltici Optimizasyonlar

### 9.1 Yaniltici metrikler

1. **Maximum favorable high:** Fiyatin sonradan high gormesi, stop yemeden trade edildigini gostermez.
2. **Ortalama expectancy:** Az sayida corporate-action veya extreme move tum ortalamayi tasiyabilir.
3. **MFE:** Cikis uygulanabilirligini kanitlamaz; MFE ile MAE ve barrier sirasi birlikte okunmalidir.
4. **Win-rate:** Stop/TP oranini ve payoff dagilimini tek basina anlatmaz.
5. **Composite score:** Mevcut decile sonuclari monoton olmadigi icin score'un rank kalitesi dusuktur.
6. **p-value:** Repeated intraday observations ve symbol dependency cluster edilmezse iyimser olabilir.
7. **Kucuk top bucket:** `n` dusukken yuksek hit-rate secim bias'i olabilir.
8. **ATR tek basina kalite:** ATR hareket potansiyelini gosterebilir; execution riskini ve data bozulmasini gostermez.

### 9.2 Yararlı metrikler

- Cost-adjusted expectancy
- Profit factor
- Median return
- MAE/MFE birlikte
- TP/SL/time-exit dagilimi
- Max drawdown ve tail contribution
- OOS hit-rate ve OOS PF
- Symbol-day cluster interval
- Benchmark-relative return
- Coverage ve false-negative profile
- Rank stability: ayni sinyalin config/period degisince sirasi

### 9.3 Metrik yeniden dengeleme

Raporlama hiyerarsisi su olmali:

1. Maliyet sonrasi execution P&L
2. OOS ve rejim bazli stability
3. Kalibre probability ve confidence interval
4. Barrier hit/stop/time dagilimi
5. Favorable movement lift
6. Raw score veya tek feature lift'i

---

## 10. Guclu Setup'lari Disarida Birakan Kurallar

Mevcut yapinin sistematik olarak zorlayabilecegi setup'lar:

- Daily EMA rejimi uyumsuzken baslayan breakout'lar
- RSI 70 ustu catalyst continuation
- Low-float/high-short squeeze
- Earnings sonrasi continuation
- Reverse ve short-covering
- Düşük fiyatli ama yuksek dolar hacimli momentum
- High ATR ile asimetrik payoff tasiyan expansion
- Erken tier'da olup henüz raw score 3 olmayan setup

Bunlarin kac tanesinin gercekten false negative oldugu mevcut artifact'ten kesin sayilamaz; cunku elenen satirlar icin point-in-time setup taxonomy ve intraday path yok. Bu nedenle coverage expansion icin ilk adim filtreyi gevsetmek degil, elenen setup'lari etiketleyip outcome'larini olcmektir.

### Onerilen coverage segmentleri

- `event_driven`
- `trend_continuation`
- `reversal`
- `squeeze`
- `volatility_expansion`
- `low_price_high_dollar_volume`
- `early_breakout`

Her segment ayri gate ve ayri baseline ile raporlanmali; tek bir global threshold kullanilmamali.

---

## 11. Ablation ve Deney Plani

### 11.1 Zorunlu deney matrisi

Her deneyde ayni train/validation/OOS split ve ayni hedef kullanilacak:

| Deney | Kapatilan veya degisen bilesen | Olculecekler |
|---|---|---|
| A0 | Mevcut production replay | Baseline coverage, hit, barrier, cost |
| A1 | Regime gate off | False negative, regime-relative return |
| A2 | Direction gate off | Reversal/event coverage |
| A3 | Raw score gate 3 -> 2 / soft rank | Coverage ve precision tradeoff |
| A4 | Liquidity share-volume gate off | Fill risk, dollar-volume cohort |
| A5 | Alignment contribution 0 | Score decile stability |
| A6 | Momentum contribution 0 | Incremental lift |
| A7 | Filter score contribution 0 | Volume/trend redundancy |
| A8 | Raw score contribution 0 | Double-counting testi |
| A9 | Composite yerine ATR/RVOL rank | Rank lift karsilastirmasi |
| A10 | Optional features tek tek off/on | Marginal contribution |
| A11 | Agirlikleri family-normalized | Dominant feature kontrolu |
| A12 | Threshold sweep sadece train'de | OOS curve stability |

### 11.2 Her deneyin zorunlu ciktisi

- n ve coverage
- false positive / false negative proxy
- T+5 movement hit-rate
- 3/5 gun barrier TP/SL/time
- median return
- PF ve cost-adjusted expectancy
- max drawdown
- top-tail contribution
- rank correlation ve rank stability
- symbol-day cluster bootstrap
- runtime/latency impact

### 11.3 Kritik tasarim kurali

Ayni veri hem threshold secimi hem final rapor icin kullanilmayacak. Feature “onemli” denmeden once:

```text
full baseline
-> single ablation
-> group ablation
-> train threshold selection
-> untouched OOS
-> cost-adjusted barrier
-> shadow
```

---

## 12. Reform Onerileri

### 12.1 Kisa vadeli mimari

1. Hard eligibility ile ranking'i ayir.
2. `entry_ok` icin tek bir canonical function kullan.
3. Config'te bulunan ama gate'i etkilemeyen threshold'lari ya uygula ya kaldir; sessiz etkisiz ayar birakma.
4. Composite score'u selection score, conviction'i probability label olarak acikca ayir.
5. Alert ve summary path'lerini tek bir rank contract altinda birlestir.
6. Her sinyal icin score decomposition ve fail reason kaydet.

### 12.2 Feature reformu

1. Raw, filter, alignment ve momentum feature'larini aile bazinda grupla.
2. Hacim/trend/momentum tekrarlarini family cap veya normalization ile sinirla.
3. Share volume yerine dollar volume ve spread modeli ekle.
4. Earnings blackout'i alpha filtresi degil event-risk modu yap.
5. Rejim gate'ini global hard block yerine rejim-specific policy olarak test et.
6. ATR/RVOL'u production'a almadan once corporate-action temiz veri ile tekrar olc.

### 12.3 Ranking reformu

Onerilen ranking contract:

```text
eligibility_status: PASS / WATCH / BLOCK
signal_family: event / trend / squeeze / reversal / expansion
quality_score: normalized, explainable feature-family score
conviction_probability: calibrated, with interval
risk_score: liquidity + spread + volatility + event risk
final_rank: quality_score adjusted for risk and capacity
```

Bu yapi composite, tier ve conviction'in ayni sembol icin neden farkli seyler soyledigini aciklar.

---

## 13. P0 / P1 / P2 / P3 Aksiyon Listesi

### P0 — Karar ve veri guvenilirligi

- `entry_ok` config ve production replay mismatch'ini coz.
- `min_alignment_ratio`, `min_momentum_ratio`, `min_filter_score` icin karar: gercek gate yap veya config'ten kaldir.
- Her scan satirina config/flag/git/as-of/provider lineage ekle.
- Corporate-action ve adjusted/unadjusted fiyat dogrulamasini tamamla.
- Full-universe barrier sonucunu temiz veriyle yeniden uret.
- Composite ranking'i production gate gibi yorumlamayi durdur; decile monotonic olmadigi kayitli.

### P1 — Dogru deney motoru

- Production replay harness yaz.
- Tek canonical `entry_ok` ve canonical rank function olustur.
- Ablation matrix'i train/OOS olarak calistir.
- Symbol-day cluster bootstrap ve confidence interval ekle.
- Maliyetli barrier ve benchmark-relative raporu kanonik truth engine'e bagla.
- Dolar hacmi, spread ve fill modeli ekle.

### P2 — Coverage ve ranking kalitesi

- Setup family taxonomy ve false-negative paneli ekle.
- Raw/filter/alignment/momentum feature ailelerinde redundancy ve incremental contribution olc.
- Composite score decomposition'i API ve Telegram'a ekle.
- Alert ve summary selection yollarini tek rank contract ile birlestir.
- Rejim bazli threshold ve dynamic policy'yi OOS test et.

### P3 — Ileri optimizasyon

- Family-normalized veya regularized ranking modeli.
- Rejim/likidite segmentine gore conditional weights.
- Intraday fill ve spread-aware execution.
- Uzun vadeli calibration, rank stability ve 12 haftalik shadow evidence.

---

## Sonuc

Scanner su an bir “sinyal siralama sistemi”nden cok, hard gate + additive score + ayri selection yollarinin birlesimidir. Bu yapi tamamen rastgele degildir; score decomposition teknik olarak aciklanabilir. Fakat composite score'un tarihsel rank kalitesi monotonic degil, bazi config threshold'lari etkisiz ve ayni bilgi birden fazla feature ile tekrar puanlanabilir.

Full-universe evidence `ATR` ve `ATR+RVOL` icin arastirmaya deger bir hareket hipotezi verdi. Ayni evidence, `entry_ok` ve composite skorun tek basina guvenilir quality rank olmadigini, outlier/corporate-action etkilerinin sonucu tasiyabildigini ve mevcut CSV'nin canli decision path'i birebir temsil etmedigini de gosterdi.

Bu nedenle dogru reform “daha fazla filtre eklemek” degil:

```text
tek eligibility contract
+ tek rank contract
+ score decomposition
+ lineage
+ ablation/OOS
+ cost-adjusted truth engine
```

olmalidir.
