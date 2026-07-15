# FinPilot Scanner — Bugüne Kadarki Testler, Sonuçlar ve Sonraki Yol

**Tarih:** 2026-07-15
**Kapsam:** Scanner auditleri, canlı kriterler, önceki backtestler, bağımsız full-universe testleri, robustness kontrolleri ve execution-style barrier testleri
**Durum:** Araştırma notu; canlı işlem kuralı değildir ve yatırım tavsiyesi değildir.

> Bu dosya, bugüne kadar yapılan testleri tek yerde toplamak için oluşturulmuştur. Amaç yüksek görünen bir sonucu seçip savunmak değil; hangi testin neyi ölçtüğünü, hangi sonuçların güvenilir olduğunu ve hangi boşlukların hâlâ karar vermeyi engellediğini açıkça kaydetmektir.

---

## 1. Yönetici Özeti

### 1.1 Bugüne kadar kanıtlananlar

1. Scanner kodunda önemli düzeltmeler ve yeni araştırma bileşenleri eklendi; bunların temel kod davranışı testlerle doğrulandı.
2. Önceki aday/candidate-only backtestlerin tüm scanner evrenini temsil etmeyebileceği tespit edildi.
3. Bu yanlılığı azaltmak için `data/shortlists/*.csv` kaynaklarından yaklaşık 53 bin satırlık full-universe veri seti oluşturuldu.
4. `entry_ok` canlı gate'i tek başına güçlü bir ayrıştırıcı olarak görünmedi.
5. ATR, özellikle `ATR >= 6`, forward hareket testlerinde genel evrenden daha ilginç bir faktör olarak göründü.
6. `ATR6+RVOL2` kombinasyonu hem favorable-movement hem de ilk barrier koşularında dikkat çekti.
7. Ancak bu sonuçların büyük kısmı yüksek ATR, corporate-action/split benzeri fiyat ölçeği sorunları, dönem yoğunluğu ve MFE ile gerçek işlem getirisi arasındaki fark nedeniyle henüz doğrulanmış edge değildir.
8. `ATR6+RVOL2+composite70` gibi daha seçici görünen bir kuralın favorable high testinde güçlü görünmesine rağmen execution-style barrier testinde kötü performans gösterebildiği görüldü.
9. Canlı scanner şu anda `ATR6+RVOL2` veya bu araştırmadaki barrier kurallarını kullanmıyor.
10. Üretime aktarım için gereken sıra: veri doğruluğu, temiz barrier testi, OOS, rejim/benchmark ayrımı, maliyet ve shadow/paper testidir.

### 1.2 Şu anki karar

> Yüksek ATR ve yüksek RVOL, scanner evreninde ileride büyük fiyat hareketleriyle ilişkili olabilecek bir araştırma hipotezidir. Bu hipotezin maliyet sonrası, uygulanabilir ve dönemler arası istikrarlı bir işlem avantajı olduğu henüz kanıtlanmamıştır.

Bu nedenle canlı scanner karar mantığı değiştirilmemiştir.

---

## 2. Test Türleri ve Kanıt Seviyeleri

Test sonuçlarını üç ayrı seviyede okumak gerekir.

| Test seviyesi | Ölçtüğü şey | Ölçmediği şey |
|---|---|---|
| Kod doğruluğu | Fonksiyonların doğru çalışması, flag kapalıyken davranışın korunması | Para kazanma veya edge |
| Forward movement | Scan tarihinden sonra fiyatın belirli bir high seviyesine ulaşması | Stop yemeden pozisyona girilip çıkılabilmesi |
| Execution-style barrier | TP/SL sırası, time exit, MFE/MAE ve işlem getirisi | Gerçek bid/ask, fill, borrow, tam intraday execution |

Özellikle `T+1..T+5 maximum high >= entry * 1.05` metriği bir **hareket yakalama** metriğidir. Bu hisse daha sonra yüzde 5 yukarıyı görmüş demektir; sinyalin o seviyeye ulaşmadan önce stop yemediğini veya gerçek işlemde o fiyattan çıkılabildiğini göstermez.

Nihai karar metriği olarak maliyet sonrası işlem getirisi, profit factor, drawdown, OOS istikrarı ve uygulanabilir fill birlikte değerlendirilmelidir.

---

## 3. Canlı Scanner'ın Mevcut Kriterleri

Araştırma kriterleri ile canlı production kriterleri birbirine karıştırılmamalıdır.

### 3.1 Canlı sembol değerlendirmesi

Kontrol edilen ana yol:

- `scanner/evaluate.py`
- `scanner/score_engine.py`
- `api/routers/scan.py`
- `agents/alert_agent.py`

Canlı değerlendirmede:

1. Yeterli multi-timeframe geçmiş aranır:
   - 15m: en az 15 bar
   - 1h: en az 10 bar
   - 4h: en az 15 bar
   - 1d: en az 50 bar
2. Günlük rejim değerlendirilir.
3. Günlük kapanışın EMA50 üzerindeki durumu direction için kullanılır.
4. Raw signal koşulları kontrol edilir:
   - RSI yaklaşık `30-70` aralığında olmalı.
   - Hacim 20 günlük medyanın yaklaşık `1.2x` üzerinde olmalı.
   - MACD histogramı pozitif ve yükseliyor olmalı.
5. Canlı `entry_ok` için rejim, yön, raw score ve likidite koşulları birlikte kullanılır.
6. Production varsayılanlarında:
   - minimum fiyat: `2.0`
   - minimum ortalama 10 günlük hacim: `300,000`
7. Global market güvenliği ve earnings blackout kontrolleri uygulanır.
8. Günlük drawdown güvenlik limiti aşılmışsa değerlendirme durdurulabilir.

### 3.2 Composite score

Composite score bileşenleri arasında şunlar bulunur:

- Rejim
- Direction
- Raw score
- Filter score
- Timeframe alignment
- Momentum confluence
- Volume spike
- Positive price momentum
- Trend strength
- Environment flag'leri açık ise sentiment, squeeze, catalyst ve diğer faktörler

Composite skor yaklaşık `0-100` aralığına normalize edilir.

### 3.3 Alert/watchlist geçişi

Temel production geçiş koşulu `entry_ok=True`'dir. Conviction tier flag'i açık olduğunda Tier A/B/C sıralaması ve environment limitleri ek rol oynayabilir. Quality gate degraded durumdaysa alert hattı sinyalleri bastırabilir.

### 3.4 Canlıda henüz olmayan araştırma kuralları

Aşağıdaki kurallar araştırmada test edilmiştir; doğrudan production gate değildir:

- `ATR >= 4`
- `ATR >= 6`
- `RVOL >= 2`
- `ATR6+RVOL2`
- `ATR6+RVOL2+composite70`
- ATR çarpanlı TP/SL barrier kuralları
- 3/5 günlük forward return eşikleri

---

## 4. Önceki Scanner Audit ve Kod Testleri

### 4.1 Scanner audit bulguları

Önceki auditlerde şu başlıklar incelendi:

- `evaluate_symbol` hot path'i
- Alpha-v2 faktörleri
- prefilter sırası
- hidden per-symbol I/O
- kullanılmayan veya zayıf bağlanmış faktörler
- heuristic score yapısı
- decile lift ve ablation gerekliliği
- telemetry ve config-manifest eksikleri
- research code ile product code ayrımı

Alpha-v2 ve erken yakalama bileşenleri için temel tasarım kararı şuydu:

> Kanıtlanmamış yeni faktörler flag kapalı varsayılanla, shadow/research modunda kalmalı; canlı karar yüzeyini değiştirmemelidir.

### 4.2 Kod doğruluğu testleri

Mevcut test defterinde yaklaşık 51 testin geçtiği kaydedildi. Bu testler şunları doğruladı:

- Early detection feature hesapları
- WATCH/SETUP/TRIGGER/CONFIRM merdiveni
- Triple-barrier labeling semantiği
- Edge Report ve factor ablation sayımları
- Volatility regime formülü
- Legacy import/ölü yol kontrolleri
- Slippage çözümlemesi
- Sentiment parse, normalization, cache ve gate davranışı
- Flag kapalıyken additive davranış ve mevcut canlı skorun korunması

Bu sonuçlar kodun beklenen şekilde çalıştığını gösterir; faktörlerin kârlı olduğunu göstermez.

---

## 5. Önceki Bağımsız Edge Ölçümleri

### 5.1 Son iki haftalık factor ablation

Önceki bağımsız ölçümde yaklaşık 249 sinyal üzerinde TP yüzde 10, SL yüzde 5 ve 10 günlük triple-barrier yaklaşımı kullanıldı.

Özet:

- Baseline hit-rate yaklaşık `%6`
- Baseline expectancy yaklaşık `-%1.10`
- CONFIRM/live `entry_ok` grubu yaklaşık `-%1.44`
- WATCH grubu yaklaşık `-%0.73`
- SETUP örneklemi çok küçüktü ve yaklaşık `-%5` seviyesindeydi
- Composite, catalyst, sentiment ve conviction için yüksek bucket örneklemi yoktu
- Squeeze yüksek bucket örneklemi yetersizdi
- Contraction daha az kötü görünse de ayrıştırıcı kriteri geçmedi
- RVOL acceleration yüksek bucket'ta daha kötüydü
- News sentiment yüksek bucket'ı düşük bucket'tan kötü çıktı

Bu testin sonucu: hiçbir faktör canlıya alma kriterini geçmedi.

### 5.2 Bu negatif testin sınırlamaları

Bu test kesin olarak “edge yoktur” dememelidir. Sınırlamalar:

- Örneklem küçüktü.
- İki hafta tek bir piyasa rejimi olabilir.
- TP yüzde 10 hedefi kısa horizon için fazla uzak kalmış olabilir.
- Giriş ve forward data provider'ları farklı ölçek veya zamanlama sorunları taşıyabilir.
- SPY/QQQ benchmark-relative analiz yapılmamıştı.

Doğru ifade şudur:

> Bu kurulumda, bu örneklemle ve bu barrier parametreleriyle edge kanıtlanamadı; sonuç negatifti.

### 5.3 Önceden mevcut audit bulguları

Önceki sistem auditlerinde de şu sonuçlar kaydedilmişti:

- Profit core audit: decile lift `0.728`, p yaklaşık `0.995`; edge lehine kanıt yok.
- Component ablation: bazı score ve risk/reward parçaları zararlı veya nötr görünüyordu.
- Barrier audit: bazı rejim/score bantları arasında ayrışma vardı; yüksek score bantları otomatik olarak daha iyi değildi.
- Eski Alpha-v2 raporlarında yüksek görünen gap/RVOL/conviction lift iddiaları bağımsız ve güncel full-universe testleriyle yeniden doğrulanmamıştı.

Bu nedenle eski raporlardaki yüksek precision oranları işlem kârlılığı olarak okunmamalıdır.

---

## 6. Full-Universe Veri Seti

### 6.1 Neden full universe?

Önceki testlerde watchlist veya aday seçimi üzerinden gelen satırlar kullanıldığı için candidate-selection bias riski vardı. Yani scanner zaten seçmiş olduğu satırlar üzerinde test ediliyor ve bu, tüm input evrenine göre sonucu iyimser gösterebiliyordu.

Bu riski azaltmak için:

- Kaynak: `data/shortlists/*.csv`
- Tüm shortlist satırları birleştirildi.
- Ana analizde duplicate satırlar korunarak no-dedup sonuç üretildi.
- İkincil kontrol olarak `(symbol, scan_date)` dedup uygulandı.
- Günlük OHLCV cache ile forward fiyatlar eşleştirildi.

### 6.2 Üretilen dosyalar

- `fetch_full_universe_and_retest.py`
- `backtest_full_universe.py`
- `full_universe_robustness.py`
- `full_universe_barrier_backtest.py`

Çıktılar:

- `data/backtest_out/full_universe_raw.csv`
- `data/backtest_out/full_universe_enriched.csv`
- `data/backtest_out/full_universe_backtest_results.json`
- `data/backtest_out/full_universe_robustness_results.json`
- `data/backtest_out/full_universe_barrier_results.json`
- `data/backtest_out/full_universe_barrier_grid.csv`

Üretilen CSV/JSON dosyaları araştırma artifact'idir; canlı scanner davranışının parçası değildir.

---

## 7. Full-Universe Forward-Movement Testleri

### 7.1 Ana hedef

Her satır için scan fiyatından sonra `T+1..T+5` arasındaki maksimum high hesaplandı.

Temel hedef:

```text
max(high[T+1:T+5]) >= entry_price * 1.05
```

Bu testte şunlar karşılaştırıldı:

- Tüm evren
- `entry_ok=True`
- `ATR >= 4`
- `ATR >= 6`
- Gap filtreleri
- RVOL filtreleri
- Squeeze filtreleri
- ATR + confirmation
- ATR + entry gate
- ATR + RVOL
- Composite score eşikleri

### 7.2 İlk bulgular

- Tüm evrenin olumlu hareket oranı yaklaşık `%38.6` idi.
- `entry_ok=True` yaklaşık `%43.1` ile biraz daha iyi görünüyordu.
- `entry_ok=False` yaklaşık `%38.5` civarındaydı.
- `entry_ok` pozitif olsa da güçlü bir ayrıştırıcı değildi.
- ATR filtreleri, özellikle `ATR >= 6`, daha belirgin bir hareket ilişkisi gösterdi.
- Küçük örneklemli yüksek composite eşikleri çok iyi görünebildi; bu nedenle örneklem ve OOS kontrolü zorunlu tutuldu.

### 7.3 Yorum sınırı

Forward high sonuçları şu soruyu cevaplar:

> Bu sinyalden sonra fiyat bir süre içinde hedef seviyeyi gördü mü?

Şu soruyu cevaplamaz:

> Gerçek bir işlem, stop yemeden, maliyetlerden sonra bu sonucu elde edebilir miydi?

Bu nedenle forward high sonucu tek başına production gate olarak kullanılamaz.

---

## 8. Combination ve Robustness Testleri

`full_universe_robustness.py` ile:

- 2 faktörlü kombinasyonlar
- 3 faktörlü kombinasyonlar
- Önerilen kurallar
- No-dedup ve `(symbol, scan_date)` dedup
- Aylık performans
- Walk-forward gate
- Symbol-day cluster bootstrap

test edildi.

### 8.1 Cluster bootstrap nedeni

Aynı sembol ve aynı gün kaynaklı kayıtlar bağımsız gözlemler değildir. Ordinary p-value kullanmak bu tekrarlar nedeniyle fazla iyimser olabilir.

Bu nedenle cluster bootstrap kullanıldı. Bu, sonuçları otomatik olarak doğru yapmaz; fakat bağımlı gözlemlerin istatistiksel güveni yapay biçimde yükseltmesini azaltır.

### 8.2 Robustness yorumu

ATR tabanlı geniş gruplar bazı kontrollerden sonra da pozitif görünmeye devam etti. Ancak küçük ve seçici kombinasyonlarda:

- örneklem küçüldü,
- aylar arası sonuçlar ayrıştı,
- seçilen kural aynı veri üzerinde optimize edilmiş olabileceği için OOS gereksinimi doğdu.

Bu nedenle robustness sonucu “production-ready” değil, “daha ileri test için aday” anlamına gelir.

---

## 9. Execution-Style Triple-Barrier Testi

### 9.1 Kullanılan model

Canonical labeling fonksiyonu:

- `scanner/labeling.py`
- `triple_barrier_label()`

Test özellikleri:

- Daily OHLC path
- ATR ölçekli TP
- ATR ölçekli SL
- 3 günlük ve 5 günlük horizon
- TP/SL aynı barda görülürse conservative stop-first
- Hiçbiri görülmezse son kapanışta time exit
- MFE ve MAE hesapları
- Short-side path desteği mevcut, fakat bu raporda ana yorum long yönlü hareketlerle yapılmalıdır

Grid:

- TP: `1.5x`, `2x`, `3x ATR`
- SL: `0.75x`, `1x`, `1.5x ATR`
- Horizon: `3`, `5` gün

### 9.2 Veri kalite düzeltmeleri

İlk koşuda iki problem görüldü:

1. Scanner entry fiyatı ile cache fiyatı arasında ciddi ölçek farkları vardı.
2. Eksik forward path'ler tam horizon sonucu gibi label ediliyordu.

Sonraki düzeltmeler:

- Aynı gün cache kapanışından mutlak `%50`den fazla sapan entry kayıtları dışlandı.
- Dışlanan kayıtlar inventory'de raporlandı.
- Tam horizon uzunluğuna ulaşmayan path'ler ilgili barrier analizinden çıkarıldı.
- Eksik path'ler yine inventory'de ayrı sayıldı.

### 9.3 Son koşu envanteri

Son `full_universe_barrier_results.json` metadata'sına göre:

| Horizon | Tam path sonucu | Kısa path | Entry drift nedeniyle dışlanan | Cache sembolü |
|---|---:|---:|---:|---:|
| 3 gün | 46,644 | 6,687 | 415 | 1,929 |
| 5 gün | 43,031 | 10,300 | 415 | 1,929 |

Toplam input satırı: `53,746`
Dedup satırı: `27,308`
Entry drift filtresi: `0.5` yani `%50`

### 9.4 Örnek barrier sonucu

`ATR6+RVOL2`, TP `2x ATR`, SL `1x ATR`, 5 günlük tam horizon:

- n: `958`
- TP oranı: yaklaşık `%23.9`
- SL oranı: yaklaşık `%46.9`
- Time exit: yaklaşık `%29.2`
- Win rate: yaklaşık `%44.2`
- Expectancy: yaklaşık `%8.82`
- Profit factor: yaklaşık `2.84`
- Median return: yaklaşık `-%5.74`
- Ortalama MFE: yaklaşık `%36.3`
- Ortalama MAE: yaklaşık `-%9.0`

Bu tablo yüzeyde güçlü expectancy gösterse de median return negatif ve MFE çok yüksektir. Bu kombinasyon, az sayıda aşırı kazançlı gözlemin ortalamayı taşıyabileceğine işaret eder.

### 9.5 Diğer önemli sonuçlar

Aynı grid hücresinde:

- Tüm evren: expectancy yaklaşık `%0.83`, PF yaklaşık `1.40`
- `ATR >= 4`: expectancy yaklaşık `%1.32`, PF yaklaşık `1.40`
- `ATR >= 6`: expectancy yaklaşık `%1.61`, PF yaklaşık `1.37`
- `ATR6+confirmation`: expectancy yaklaşık `%3.40`, PF yaklaşık `1.69`
- `ATR6+entry_ok`: expectancy yaklaşık `-%0.10`, PF yaklaşık `0.98`
- `ATR6+RVOL2`: expectancy yaklaşık `%8.82`, PF yaklaşık `2.84`
- `ATR6+RVOL2+composite70`: expectancy yaklaşık `-%1.45`, PF yaklaşık `0.74`

Bu sonuçlar iki şeyi gösterir:

1. ATR/RVOL kombinasyonu araştırmaya değerdir.
2. Daha yüksek composite skor veya mevcut `entry_ok`, barrier execution kalitesini otomatik olarak artırmamaktadır.

---

## 10. Outlier ve Veri Kalitesi Bulguları

### 10.1 Tespit edilen örnekler

Aşırı MFE üreten örnekler arasında şunlar görüldü:

- `RDGT`
- `NAMI`
- `AIIO`
- `CREG`
- `BDRX`
- `ATLN`

Örneğin `RDGT` için scan günü entry yaklaşık `0.0178` iken sonraki günlük seride fiyatların çok farklı ölçeğe sıçradığı görüldü. Aynı gün kapanışı entry ile uyumlu olsa da sonraki günlerde yaklaşık `0.02` seviyelerinden `3` seviyesine geçiş gibi extreme hareketler vardı.

Bu tip olaylar:

- reverse split veya split,
- corporate action,
- adjusted/unadjusted series karışımı,
- cache provider değişimi,
- stale veya yanlış eşlenmiş fiyat,
- gerçek extreme move

olabilir. Her sembol için provider ve corporate-action geçmişiyle doğrulanmadan gerçek edge kabul edilmemelidir.

### 10.2 ATR cap duyarlılığı

Aynı `ATR6+RVOL2`, TP `2x ATR`, SL `1x ATR`, 5 günlük koşulunda:

| ATR sınırı | Expectancy | Profit factor | Ortalama MFE |
|---|---:|---:|---:|
| Sınır yok | `%8.82` | `2.84` | `%36.30` |
| `ATR < 50` | `%1.35` | `1.29` | `%17.45` |
| `ATR < 100` | `%2.02` | `1.43` | `%18.78` |
| `ATR < 200` | `%1.99` | `1.42` | `%18.75` |
| `ATR < 500` | `%2.03` | `1.43` | `%18.84` |
| `ATR < 1000` | `%1.92` | `1.40` | `%18.77` |

Bu duyarlılık testi, yüksek expectancy'nin extreme ATR ve fiyat sıçramalarına ciddi biçimde bağlı olduğunu gösterir.

### 10.3 Bu bulgunun anlamı

Entry alignment filtresi gerekliydi fakat yeterli değildir. Aynı gün entry doğru olabilir; corporate action sonraki barlarda ölçeği bozabilir. Bu nedenle sıradaki veri kalite katmanı:

- split factor,
- reverse split,
- adjusted close/open/high/low tutarlılığı,
- provider as-of zamanı,
- symbol mapping,
- delisting ve survivorship

kontrolleridir.

---

## 11. Zaman İstikrarı

`ATR6+RVOL2`, TP `2x ATR`, SL `1x ATR`, 5 günlük tam path sonucu aylara göre istikrarlı değildi:

- 2025-09: küçük örneklemle güçlü pozitif
- 2026-04: extreme outlier etkisiyle olağanüstü yüksek
- 2026-05: yaklaşık başa baş
- 2026-06: pozitif ama daha düşük
- 2026-07: negatif, stop oranı yüksek

Özellikle Temmuz örneğinde expectancy yaklaşık `-%5.65`, median return yaklaşık `-%7.49` ve stop oranı yaklaşık `%75` oldu.

Bu dağılım, aynı kuralın farklı rejimlerde aynı şekilde çalışmadığını gösterir. Parametre seçimi ve final rapor aynı dönemde yapılmamalıdır.

---

## 12. Neden Henüz Production'a Alınmadı?

Şu nedenlerin her biri tek başına dikkat gerektirir; birlikte değerlendirildiğinde production değişikliği için yeterli kanıt yoktur:

1. Fiyat cache'inde corporate-action/ölçek problemi şüphesi var.
2. Outlier temizliği expectancy'yi `%8.82` seviyesinden yaklaşık `%1-2` seviyesine indirebiliyor.
3. Median return, bazı yüksek ortalama sonuçlarda negatiftir.
4. Aylık sonuçlar istikrarlı değildir.
5. `entry_ok` barrier sonucunda olumlu ayrışmamıştır.
6. Composite threshold daha iyi görünmek yerine bazı koşullarda daha kötü sonuç vermiştir.
7. Gerçek spread, slippage, commission, borrow ve fill modeli henüz tam değildir.
8. Testler daily OHLC ağırlıklıdır; signal zamanı ile gün içi execution farkı bulunmaktadır.
9. OOS ve benchmark-relative sonuçlar tamamlanmamıştır.
10. Hedef değişkeni hareket yakalama ile işlem kârlılığını karıştırmamalıdır.

---

## 13. Sonraki Test Planı

### Faz 1 — Veri doğruluğu

Öncelik sırasıyla:

1. Tüm full-universe satırlarını aynı gün cache OHLC ile karşılaştır.
2. Entry-close, entry-open ve previous-close sapma dağılımlarını çıkar.
3. Aşırı fiyat oranı değişimlerini sembol/tarih bazında listele.
4. Split/reverse split ve corporate-action kaynaklarını kontrol et.
5. Adjusted/unadjusted provider kullanımını tekleştir.
6. Delisted ve survivorship durumunu kontrol et.
7. Her backtest sonucuna provider, as-of ve config manifest ekle.

### Faz 2 — Temiz barrier testi

1. Temizlenmiş fiyat serisini kullan.
2. Tam horizon şartını koru.
3. ATR üst sınırının strateji sonucuna etkisini raporla.
4. No-dedup ve `(symbol, scan_date)` dedup sonuçlarını ayrı tut.
5. Ortalama yanında median, percentile, PF, drawdown ve tail contribution ver.
6. Aşırı kazançlı ilk yüzde 1-5 gözlemin toplam expectancy'ye katkısını hesapla.

### Faz 3 — OOS ve walk-forward

Örnek yapı:

- Train: erken dönem
- Validation: orta dönem
- OOS: en son dönem

TP/SL, ATR sınırı veya filtre eşiği train döneminde seçilmeli; OOS dönemi seçimde kullanılmamalıdır.

Her dönemde raporlanacaklar:

- n
- hit/TP/SL/time oranları
- expectancy
- PF
- median return
- max drawdown
- symbol-cluster bootstrap aralığı

### Faz 4 — Benchmark ve rejim

- SPY/QQQ/IWM forward return çıkarılmalı.
- Sinyal getirisi benchmark-relative olarak raporlanmalı.
- Bull, bear ve range rejimleri ayrılmalı.
- Signal'in yalnızca genel piyasa hareketini tekrar edip etmediği ölçülmeli.

### Faz 5 — Execution ve maliyet

- Signal timestamp ile entry fiyatı ayrılmalı.
- Next-bar open, close ve mümkünse bid/ask senaryoları karşılaştırılmalı.
- Slippage, commission ve düşük fiyatlı hisselerde spread varsayımı eklenmeli.
- Gap ile stop seviyesinin aşılması ayrıca modellenmeli.
- Aynı bar TP/SL tie için stop-first korunmalı.
- Likiditeyi yalnız share volume değil dolar hacmi ve spread ile ölçmek gerekir.

### Faz 6 — Intraday doğrulama

Daily sonuçlar veri kalitesi açısından geçtikten sonra:

- 15m veya daha kısa barlar,
- scanner sinyal zamanı,
- gerçek entry varsayımı,
- intraday TP/SL,
- spread/slippage,
- order fill uygulanabilirliği

birlikte test edilmelidir.

### Faz 7 — Shadow/paper trading

Kural ancak şu aşamalardan sonra canlıya yaklaşmalıdır:

1. Backtest temiz ve OOS pozitif.
2. En az birkaç farklı rejimde tutarlı.
3. Maliyet sonrası pozitif.
4. Shadow mode'da gerçek zamanlı sinyal ve varsayılan execution kaydedilmiş.
5. Paper sonuçları ile backtest dağılımı karşılaştırılmış.
6. Kill-switch, günlük zarar limiti ve rollback tanımlanmış.

---

## 14. Production'a Alma İçin Önerilen Kanıt Kapısı

Bir faktör veya kombinasyon canlı karar yüzeyine alınmadan önce en az şu koşullar aranmalıdır:

- Tam ve doğrulanmış fiyat serisi
- Yeterli örneklem
- Train/validation/OOS ayrımı
- Symbol-day cluster bootstrap
- Maliyet sonrası pozitif expectancy
- PF'nin yalnızca birkaç outlier'a bağlı olmaması
- Median return ve drawdown'ın kabul edilebilir olması
- En az iki veya üç farklı zaman döneminde tutarlılık
- Benchmark-relative üstünlük veya açık bir bağımsız katkı
- Shadow/paper doğrulaması
- Canlı rollback ve feature flag

Bu kapı geçilmeden `ATR6+RVOL2` canlı entry gate'i yapılmamalıdır.

---

## 15. Referans Kod ve Artifact'ler

### Canlı scanner

- `scanner/evaluate.py`
- `scanner/score_engine.py`
- `scanner/config.py`
- `api/routers/scan.py`
- `agents/alert_agent.py`

### Labeling ve mevcut truth parçaları

- `scanner/labeling.py`
- `scanner/backtest_metrics.py`
- `scanner/edge_report.py`
- `scripts/barrier_audit.py`
- `scripts/factor_ablation_report.py`

### Full-universe araştırması

- `fetch_full_universe_and_retest.py`
- `backtest_full_universe.py`
- `full_universe_robustness.py`
- `full_universe_barrier_backtest.py`

### Sonuç artifact'leri

- `data/backtest_out/full_universe_raw.csv`
- `data/backtest_out/full_universe_enriched.csv`
- `data/backtest_out/full_universe_robustness_results.json`
- `data/backtest_out/full_universe_barrier_results.json`
- `data/backtest_out/full_universe_barrier_grid.csv`

### Önceki referans dokümanlar

- `docs/audit-2026-06-12/19-scanner-test-defteri.md`
- `FinPilot_Tam_Sistem_Audit_2026-07-03.md`

---

## 16. Son Cümle

Bugüne kadar yapılan iş, canlı scanner'a rastgele yeni filtre eklemekten çok daha değerli bir şeyi netleştirdi: **hareket yakalama, işlem kârlılığı ve kod doğruluğu ayrı kanıt katmanlarıdır.** Full-universe testleri ATR/RVOL yönünde araştırılabilir bir hipotez verdi; aynı testler bu hipotezin outlier, corporate-action ve rejim etkilerine ne kadar duyarlı olduğunu da gösterdi. Bu nedenle bir sonraki hedef daha yüksek bir backtest rakamı üretmek değil, aynı sonucu temiz veri ve geleceğe dokunmayan OOS ölçümüyle tekrar üretip üretemediğimizi görmektir.
