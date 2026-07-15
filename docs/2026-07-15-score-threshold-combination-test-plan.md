# FinPilot — Score, Threshold ve Factor Combination Test Planı

**Tarih:** 2026-07-15
**Dayanak raporlar:** threshold/false-negative audit, composite/ranking audit, scanner testleri ve sonuçları, scanner algorithm/ranking audit
**Amaç:** Mevcut score, threshold ve factor kombinasyonlarının hareket yakalama değil, mümkün olduğunda uygulanabilir ve maliyet-sonrası işlem kalitesi üretip üretmediğini bağımsız test paketleriyle ölçmek.
**Kapsam:** Research-only. Bu plan production scanner kuralı veya yatırım sinyali değildir.

## 1. Kısa Karar

Evet, 2’li kombinasyonların yanında 3, 4, 5 ve seçilmiş 6 faktörlü kombinasyonları da test etmek anlamlıdır. Ancak şu kural uygulanmalıdır:

> Kombinasyon sayısını artırmak araştırmayı zenginleştirir; kanıtı otomatik olarak güçlendirmez. Her ek kombinasyon yeni bir multiple-testing ve küçük örneklem riski yaratır.

Bu yüzden bütün kombinasyonlar tek bir dev backtest olarak değil, aşağıdaki bağımsız paketler halinde çalıştırılmalıdır:

1. Veri ve production replay doğrulaması
2. Tek faktör threshold taraması
3. 2’li kombinasyon taraması
4. 3’lü kombinasyon taraması
5. 4–6’lı seçilmiş kombinasyon taraması
6. Score/composite ablation ve ranking testi
7. Execution-style barrier testi
8. OOS/walk-forward ve zaman istikrarı
9. Maliyet, kapasite ve risk testi
10. İstatistiksel güven ve multiple-testing düzeltmesi
11. Shadow/paper test

Her paket kendi artifact’ini üretmeli; yalnızca bütün paketlerden geçen kurallar production adayı sayılmalıdır.

## 2. Önce Çözülmesi Gereken Ölçüm Sorunları

Bu testler yapılmadan combination sonucu yorumlanmamalıdır.

### 2.1 Production replay testi

**Soru:** CSV’deki `entry_ok`, aynı tarih ve aynı input ile production scanner bugün tekrar çalıştırıldığında birebir oluşuyor mu?

**Test:**

- Tarih, symbol ve feature snapshot'ını point-in-time olarak sabitle.
- `evaluate_symbol` sonucunu yeniden üret.
- CSV sonucu ile production replay sonucunu satır bazında karşılaştır.
- `entry_ok`, raw score, regime, direction, liquidity ve earnings kararlarını ayrı ayrı karşılaştır.

**Ölçülecekler:**

- Exact match rate
- Her alan için confusion matrix
- Drift nedeni
- Eksik veya sonradan güncellenmiş veri oranı

**Ne işe yarar:** Backtestte ölçülen kuralın gerçekten canlı kural olup olmadığını gösterir. Replay eşleşmiyorsa combination testi yanlış karar yüzeyinde yapılmış olur.

**Başarı şartı:** Önce minimum `%99` karar eşleşmesi hedeflenmeli; kalan farklar gerekçeli ve raporlu olmalıdır.

### 2.2 Reject reason telemetry testi

**Soru:** Favorable mover'ların neden reddedildiğini kesin olarak biliyor muyuz?

**Test:** Her değerlendirme için `reject_reason[]` yazılmalı:

- history
- regime
- direction
- RSI
- volume confirmation
- MACD confirmation
- raw score
- price
- average volume / dollar ADV
- earnings blackout
- market safety
- data quality

**Ne işe yarar:** Önceki `%96,42 entry_ok=False` sonucu proxy nedenlere dayanıyor. Bu test proxy'yi gerçek gate nedenine çevirir ve hangi gate'in recall kaybettirdiğini gösterir.

### 2.3 Point-in-time ve leakage testi

**Soru:** Scan tarihinden sonraki bilgi score veya threshold hesabına sızıyor mu?

**Test:**

- Her feature'ın timestamp'ini kaydet.
- Forward OHLC, sentiment, catalyst, earnings ve fundamentals verisinin yayınlanma zamanını kontrol et.
- Aynı gün kapanışının scan kararından önce erişilebilir olup olmadığını doğrula.
- Random future-value injection testi ile leakage alarmı üret.

**Ne işe yarar:** Özellikle catalyst, sentiment, gap ve forward price eşleştirmelerinde sahte edge'i engeller.

### 2.4 Veri kalite ve entry drift testi

**Soru:** Entry fiyatı ile forward cache aynı fiyat ölçeğinde mi?

**Test:**

- Aynı gün scanner price ve cache close sapmasını dağılım olarak çıkar.
- `%5`, `%10`, `%25`, `%50` drift bucket'ları raporla.
- Split/corporate-action, stale quote, missing bar ve short path kayıtlarını ayrı tut.
- Sonuçları ham ve temizlenmiş veri üzerinde tekrarla.

**Ne işe yarar:** Yüksek ATR, MFE ve expectancy sonuçlarının fiyat ölçeği hatası veya corporate action kaynaklı olup olmadığını ayırır.

## 3. Tek Faktör ve Threshold Testleri

Bu aşama combination testinden önce gelmelidir.

### 3.1 Production gate threshold sweep

Her eşik için aşağıdakiler raporlanmalı:

- coverage
- favorable-mover hit-rate
- favorable-mover recall
- günlük sinyal sayısı
- symbol-day dedup sonucu
- aylık lift
- 95% confidence interval
- execution barrier expectancy ve PF

### Test edilecek eşikler

| Aile | Eşikler |
| --- | --- |
| ATR | `>=2`, `>=4`, `>=6`, `>=8`, `>=10` |
| RVOL | `>=1`, `>=1.5`, `>=2`, `>=3` |
| Gap | `>=1`, `>=3`, `>=5`, `>=8` |
| Raw score | `>=1`, `>=2`, `==3` |
| Composite | `>=30`, `>=40`, `>=50`, `>=58`, `>=60`, `>=70`, `>=80` |
| Direction/regime | strict, balanced, event/reversal shadow mode |
| Liquidity | share volume, dollar ADV, spread/impact proxy |
| Distance | `dist52` için near-high ve not-near-high bucket'ları |

**Ne işe yarar:** Hangi faktörün tek başına hareketle ilişkili olduğunu ve precision-recall tradeoff'unu gösterir. Tek faktör kötü ise onu büyük kombinasyonun içine koymak çoğunlukla çözüm değildir.

### 3.2 Raw score soft-gate testi

Üç ayrı karar modu test edilmeli:

- Strict: `score == 3`
- Balanced: `score >= 2`
- Confirmation: raw score hard gate değil, ranking/sizing katkısı

Her mod için aynı sample, aynı barrier ve aynı OOS bölünmesi kullanılmalı.

**Ne işe yarar:** Önceki auditte raw score'un favorable mover recall'ını ciddi biçimde düşürdüğü görüldü. Bu test, recall kazanımının execution kalitesini bozup bozmadığını ölçer.

### 3.3 Composite ranking testi

Composite için:

- decile hit-rate
- quantile monotonicity
- top-5%, top-10%, top-20% lift
- rank correlation with T+5 return
- score calibration curve
- monthly top-set Jaccard
- regime-specific deciles
- score bucket sample size

raporlanmalı.

**Ne işe yarar:** Composite'in gerçek bir quality ranking mi, yoksa yalnızca açıklanabilir ama zayıf bir feature toplamı mı olduğunu ayırır.

## 4. Kombinasyon Tasarımı

### 4.1 Faktörleri ailelere ayırma

Körlemesine bütün kolonları birleştirmek yerine faktör aileleri kullanılmalı:

| Aile | Örnek faktörler | Aynı anda kaç tane? |
| --- | --- | ---: |
| Volatilite | ATR>=4, ATR>=6, ATR>=8 | En fazla 1 |
| Hacim | RVOL>=1.5, RVOL>=2, volume spike | En fazla 1 |
| Gap/event | gap>=3, gap>=5, catalyst | En fazla 1 |
| Trend | regime, direction, alignment | En fazla 1 |
| Momentum | raw score, momentum ratio, price momentum | En fazla 1 |
| Risk/context | entry_ok, dist52, earnings, liquidity | En fazla 2 |
| Composite | composite>=58, >=70, >=80 | En fazla 1 |

Aynı ailenin `ATR>=4 AND ATR>=6` gibi kombinasyonları yeni bilgi taşımaz; yalnızca daha sert eşiğe eşittir ve test matrisi dışında tutulmalıdır.

### 4.2 2’li kombinasyonlar

**Amaç:** Tek faktörlerin birbirini tamamlayıp tamamlamadığını ölçmek.

Öncelikli kombinasyonlar:

- `ATR>=4 + RVOL>=2`
- `ATR>=6 + RVOL>=2`
- `ATR>=4 + gap>=3`
- `ATR>=6 + gap>=3`
- `ATR>=4 + raw_score>=2`
- `ATR>=6 + raw_score==3`
- `ATR>=6 + direction`
- `ATR>=6 + not_near_52w_high`
- `RVOL>=2 + gap>=3`
- `RVOL>=2 + composite>=58`
- `ATR>=6 + composite>=70`
- `entry_ok + ATR>=6`

**Ne işe yarar:** Volatilite, hacim, event, trend ve score'un bağımsız veya tamamlayıcı katkısını ilk kez gösterir.

### 4.3 3’lü kombinasyonlar

**Amaç:** İki faktörlü bulgunun üçüncü bir bağlamla korunup korunmadığını test etmek.

Öncelikli set:

- `ATR>=6 + RVOL>=2 + gap>=3`
- `ATR>=6 + RVOL>=2 + direction`
- `ATR>=6 + RVOL>=2 + not_near_52w_high`
- `ATR>=6 + RVOL>=2 + composite>=58`
- `ATR>=6 + RVOL>=2 + composite>=70`
- `ATR>=6 + gap>=3 + composite>=58`
- `ATR>=4 + RVOL>=2 + raw_score>=2`
- `ATR>=6 + raw_score>=2 + direction`
- `ATR>=4 + gap>=3 + not_near_52w_high`
- `ATR>=6 + entry_ok + RVOL>=2`

**Ne işe yarar:** İlk raporlarda görünen `ATR6+RVOL2` etkisinin trend, gap, distance veya composite ile gerçekten güçlenip güçlenmediğini gösterir.

### 4.4 4’lü kombinasyonlar

**Amaç:** Araştırma hipotezinin daha sıkı ve uygulanabilir bir trade universe'de devam edip etmediğini ölçmek.

Öncelikli set:

- `ATR>=6 + RVOL>=2 + gap>=3 + direction`
- `ATR>=6 + RVOL>=2 + gap>=3 + not_near_52w_high`
- `ATR>=6 + RVOL>=2 + direction + composite>=58`
- `ATR>=6 + RVOL>=2 + not_near_52w_high + composite>=58`
- `ATR>=4 + RVOL>=2 + raw_score>=2 + direction`
- `ATR>=6 + gap>=3 + raw_score>=2 + not_near_52w_high`
- `ATR>=6 + RVOL>=2 + entry_ok + composite>=58`

**Ne işe yarar:** Daha seçici bir kuralın hit-rate'ini değil, net işlem kalitesini, günlük kapasitesini ve aylar arası stabilitesini ölçer.

### 4.5 5’li kombinasyonlar

**Amaç:** Çoklu confirmation kuralının gerçekten farklı bilgi taşıyıp taşımadığını test etmek.

Öncelikli set:

- `ATR>=6 + RVOL>=2 + gap>=3 + direction + not_near_52w_high`
- `ATR>=6 + RVOL>=2 + gap>=3 + direction + composite>=58`
- `ATR>=6 + RVOL>=2 + direction + not_near_52w_high + composite>=58`
- `ATR>=4 + RVOL>=2 + raw_score>=2 + direction + not_near_52w_high`
- `ATR>=6 + gap>=3 + raw_score>=2 + direction + composite>=58`

**Ne işe yarar:** Kuralın yüksek skor değil, aynı zamanda tutarlı execution sonucu üretip üretmediğini ölçer. Bu aşamada `n`, aylık coverage ve median return özellikle önemlidir.

### 4.6 6’lı kombinasyonlar

**Amaç:** Production kuralı önermek değil; seçilmiş araştırma hipotezlerinin over-filtering sınırını görmek.

En fazla aşağıdaki sınırlı set test edilmeli:

- `ATR>=6 + RVOL>=2 + gap>=3 + direction + not_near_52w_high + composite>=58`
- `ATR>=6 + RVOL>=2 + gap>=3 + raw_score>=2 + direction + not_near_52w_high`
- `ATR>=6 + RVOL>=2 + raw_score>=2 + direction + not_near_52w_high + composite>=58`

**Ne işe yarar:** Her confirmation eklendiğinde recall, n ve günlük kapasitenin nasıl çöktüğünü gösterir. 6’lı kural iyi görünürse bunun nedeni çoğu zaman seçilmiş küçük örneklem olabilir; otomatik olarak daha kaliteli olduğu kabul edilmemelidir.

## 5. Kombinasyonlar İçin Ortak Rapor Şablonu

Her kombinasyon aynı tabloyla raporlanmalı:

### Coverage ve hareket

- total n
- coverage
- favorable-mover hit-rate
- favorable-mover recall
- mean/median T+5
- base ve control karşılaştırması
- Wilson CI

### Zaman ve evren istikrarı

- symbol-day dedup sonucu
- ay bazında n ve lift
- positive-month ratio
- first-half / second-half
- bull/bear/sideways regime
- market benchmark-relative sonuç

### Execution

- TP rate
- SL rate
- time-exit rate
- win-rate
- expectancy
- median return
- profit factor
- MFE / MAE
- average bars-to-exit
- max drawdown
- turnover ve günlük işlem kapasitesi

### Uygulanabilirlik

- günlük sinyal sayısı
- en yoğun sembol payı
- concentration
- missing path oranı
- entry drift oranı
- spread/impact bucket
- minimum n

**Önemli:** Mean expectancy tek başına yeterli değildir. Pozitif mean ve negatif median birlikte görülüyorsa outlier, path veya data-quality incelemesi zorunludur.

## 6. Barrier Test Matrisi

Her seçilmiş 2–6’lı kombinasyon için aynı barrier matrisi uygulanmalı:

| Boyut | Değerler |
| --- | --- |
| Horizon | 3d, 5d |
| TP | 1.5x ATR, 2x ATR, 3x ATR |
| SL | 0.75x ATR, 1x ATR, 1.5x ATR |
| Tie rule | Stop-first |
| Price quality | Drift temizlenmiş ve ham sonuç ayrı |
| Universe | No-dedup ve symbol-day dedup |
| Direction | Long ve short destekleniyorsa ayrı |
| Cost | 0, düşük, orta ve stres maliyet senaryosu |

**Ne işe yarar:** Bir kombinasyonun yalnızca `T+5 high` gördüğü için mi, yoksa stop/TP sırasından sonra gerçekten para ürettiği için mi iyi göründüğünü ayırır.

Mevcut `full_universe_barrier_backtest.py` yalnızca birkaç predicate'i elle tanıyor. 4–6’lı kombinasyonlar için predicate registry veya kombinasyon manifest'i eklenmeli; kombinasyonlar script içine tek tek kopyalanmamalıdır.

## 7. OOS, Walk-Forward ve Regime Testleri

### 7.1 Locked temporal split

Önerilen ilk bölünme:

- Discovery: ilk `%50`
- Validation: sonraki `%25`
- Locked OOS: son `%25`

Daha sonra rolling walk-forward:

- 6 aylık train
- 2 aylık validation
- sonraki 2 aylık test

Tüm eşik ve kombinasyon seçimleri yalnızca train/validation'da yapılmalı; locked OOS yalnızca bir kez açılmalıdır.

### 7.2 Regime split

Her kural ayrı raporlanmalı:

- Bull
- Bear
- Sideways
- High-volatility
- Low-volatility
- Market benchmark positive/negative

**Ne işe yarar:** ATR/RVOL kombinasyonlarının belirli bir kısa döneme veya tek rejime bağımlı olup olmadığını gösterir.

### 7.3 Stability gate

Bir kombinasyon ancak aşağıdaki şartlarla araştırma adayı olarak tutulmalı:

- Locked OOS lift > 1 veya maliyet sonrası expectancy pozitif
- OOS confidence interval tamamen rastgele tabanın altında değil
- En az 3 zaman diliminde aynı yönlü sonuç
- Median return negatifse mean sonucu tek başına kabul edilmemeli
- N ve günlük kapasite minimumları karşılanmalı
- Dedup sonucu yön değiştirmemeli

Bu şartlar production onayı değildir; yalnızca bir sonraki shadow aşamasına geçiş filtresidir.

## 8. İstatistiksel Testler ve Multiple-Testing

### Yapılacaklar

- Symbol-day cluster bootstrap
- Block bootstrap veya date-cluster bootstrap
- Wilson CI hit-rate için
- Bootstrap CI expectancy/PF için
- Discovery/validation/OOS ayrımı
- Benjamini-Hochberg FDR veya family-wise correction
- Deflated Sharpe / selection-bias raporu
- Negative-control factor testi
- Permutation test

### Neden gerekli?

2’den 6 faktöre çıkınca kombinasyon sayısı hızla büyür. Örneğin 14 faktör arasından 6’lı kombinasyonlar `C(14,6)=3.003` adettir. Bu kadar çok denemede rastlantısal olarak çok iyi görünen birkaç kombinasyon çıkması beklenir.

Bu nedenle raporda yalnızca “en iyi 10 kombinasyon” değil, şunlar da bulunmalıdır:

- kaç kombinasyon test edildi
- kaçında `n >= 50`
- kaçında OOS pozitif sonuç var
- kaçında maliyet sonrası sonuç pozitif
- kaçında dedup sonrası sonuç yön değiştirdi
- seçimin hangi veri bölümünde yapıldığı

## 9. Maliyet ve Uygulanabilirlik Testleri

Her seçilmiş combination için en az dört maliyet senaryosu:

1. Maliyetsiz
2. Düşük spread/slippage
3. Orta spread/slippage
4. Stres spread/slippage ve gecikmeli fill

Ayrıca:

- dollar ADV bazlı position size
- estimated market impact
- minimum price ve spread bucket'ları
- günlük maksimum pozisyon sayısı
- aynı symbol'de tekrar sinyal
- portfolio overlap
- sector concentration
- max concurrent positions
- stop/TP gap-through riski

**Ne işe yarar:** Kağıt üzerinde pozitif olan kombinasyonun gerçek fill, likidite ve kapasite altında hâlâ çalışıp çalışmadığını gösterir.

## 10. Score ve Combination Birlikte Testi

Composite score'u yalnızca son filtre olarak eklemek yerine üç farklı rol test edilmeli:

### Model A: Gate sonrası ranking

`entry_ok` sabit kalır; composite yalnızca rank/sizing için kullanılır.

**Soru:** Composite, kabul edilen sinyalleri doğru sıralıyor mu?

### Model B: Soft quality band

`entry_ok` hard gate'i shadow modda tutulur; raw/composite bandları alert ve sizing'i değiştirir.

**Soru:** Daha fazla recall, execution kalitesini bozuyor mu?

### Model C: Combination içinde score

`ATR6 + RVOL2 + composite>=58/70` gibi sınırlı score combinations test edilir.

**Soru:** Composite, bağımsız ATR/RVOL edge'ine gerçekten ek bilgi katıyor mu?

Her model için score'suz baseline ile delta raporlanmalı. Score eklendiğinde lift artmıyor, n küçülüyor ve median kötüleşiyorsa score yalnızca selection bias yaratıyor olabilir.

## 11. Ablation ve Redundancy Testleri

Her kombinasyonun şu varyantları çalıştırılmalı:

- tüm faktörler
- bir faktör çıkarılmış
- yalnızca trend familyası çıkarılmış
- yalnızca momentum familyası çıkarılmış
- yalnızca volume familyası çıkarılmış
- score çıkarılmış
- entry gate çıkarılmış

Örnek:

```text
ATR6 + RVOL2 + gap3 + direction + composite58
ATR6 + RVOL2 + gap3 + direction
ATR6 + RVOL2 + gap3
ATR6 + RVOL2
```

**Ne işe yarar:** Beş faktörlü kuraldaki gerçek katkının hangi faktörden geldiğini ve hangi faktörlerin yalnızca double-counting yaptığını gösterir.

## 12. Önerilen Çalıştırma Sırası

### Faz 0 — Ölçüm kilidi

1. Production replay
2. Reject reason telemetry
3. Point-in-time/leakage
4. Entry drift ve corporate-action temizliği
5. Symbol-day dedup tanımı

**Çıkış:** Güvenilir analiz evreni ve veri sözleşmesi.

### Faz 1 — Tek faktör

1. Threshold sweep
2. Raw score strict/balanced/confirmation
3. Composite decile/calibration
4. Regime ve aylık ayrım

**Çıkış:** Combination'a girecek aday faktörlerin kısa listesi.

### Faz 2 — 2’li ve 3’lü

1. Mevcut robustness scriptini tekrar çalıştır
2. Priority 2’li listesi
3. Priority 3’lü listesi
4. Dedup, aylık, cluster bootstrap
5. İlk barrier testi

**Çıkış:** En fazla 5–10 stabil aday.

### Faz 3 — Seçilmiş 4’lü, 5’li, 6’lı

1. Yalnızca önceki fazda anlamlı görünen familyalardan üret
2. OOS'a dokunmadan train/validation'da seç
3. Her 4–6’lı kural için ablation yap
4. Barrier ve maliyet testini aynı kuralla çalıştır
5. Sample-size ve capacity gate uygula

**Çıkış:** Shadow test için en fazla 1–3 aday.

### Faz 4 — Locked OOS

1. Kuralları kilitle
2. Eşik, weight ve feature seçimini durdur
3. OOS'u bir kez çalıştır
4. Sonuçları maliyet ve dedup ile raporla

**Çıkış:** OOS sonucu; production kararı değil.

### Faz 5 — Shadow/paper

1. Canlı scanner kuralını değiştirmeden adayları paralel üret
2. Reject reason ve score contribution logla
3. Gerçek spread/fill varsayımlarını kaydet
4. En az 4–8 hafta veya yeterli işlem sayısı izle

**Çıkış:** Uygulanabilirlik ve operational stability kararı.

## 13. Mevcut Kodda Gerekli Araştırma Geliştirmeleri

### `full_universe_robustness.py`

Mevcut durum: 2’li ve 3’lü kombinasyonlar otomatik üretiliyor.

Geliştirme:

- `--combination-sizes 2,3,4,5,6`
- family constraint desteği
- combination manifest JSON/CSV
- minimum n ve minimum daily coverage filtresi
- discovery/validation/OOS split
- FDR correction
- selected combination için full stability output

### `full_universe_barrier_backtest.py`

Mevcut durum: birkaç predicate elle tanımlı; generic 4–6’lı kombinasyon yok.

Geliştirme:

- aynı factor registry'yi robustness scriptinden paylaş
- combination manifest oku
- her combination için TP/SL/horizon grid çalıştır
- score-specific MFE/MAE/hold-time üret
- cost/slippage modeli ekle
- no-dedup ve symbol-day dedup'u aynı output'ta tut

### Yeni önerilen artifact'ler

- `data/backtest_out/combination_forward_results.csv`
- `data/backtest_out/combination_barrier_results.csv`
- `data/backtest_out/combination_stability.json`
- `data/backtest_out/combination_oos_results.json`
- `data/backtest_out/combination_multiple_testing.json`
- `data/backtest_out/combination_manifest.json`

## 14. Son Görüş

3–6’lı kombinasyonları denemek gerekir; fakat bunları “daha çok faktör = daha iyi strateji” şeklinde yorumlamamak gerekir.

En doğru yaklaşım:

- 2’li kombinasyonları tamamla.
- 3’lü kombinasyonları ana interaction testi olarak çalıştır.
- 4’lü ve 5’li kombinasyonları yalnızca family constraint ve OOS ayrımıyla test et.
- 6’lı kombinasyonları küçük, önceden tanımlı hipotez setiyle sınırla.
- Her combination için forward movement ve execution barrier testini ayrı çalıştır.
- Sonuçları aylık, dedup, cluster bootstrap, maliyet ve locked OOS ile birlikte değerlendir.
- Hiçbir yüksek hit-rate kombinasyonunu tek başına production gate'e çevirmeme.

**Benim önerim:** Önce 2–3 faktörlü kombinasyon bataryasını tam ve temiz biçimde bitirelim; buradan yalnızca stabil çıkan 5–10 hipotezi 4–6 faktörlü seçici teste taşıyalım. Böylece 6’lı kombinasyonları da denemiş oluruz, fakat binlerce rastgele kombinasyon arasından tesadüfi kazanan seçme hatasına düşmeyiz.
