# FinPilot — 10-Perspektif Bağımsız Beyin Fırtınası, Red-Team ve Gelecek Vizyonu

Sürüm: 1.0 · Tarih: 2026-08-10 · Statü: Level A (araştırma/strateji, üretim değişikliği yok)
Yöntem notu: Bu belge sohbet içinde değil dosya olarak üretildi çünkü kapsamı (10 perspektif × zorunlu format) sohbet formatına sığmıyor. Yoğunluk için düzyazı yerine madde/tablo tercih edildi — bu bir kısaltma değil, aynı içeriğin daha az gürültüyle sunumu.

**Kanıt standardı (her önemli iddia etiketli):**
`[EVIDENCE]` bu oturumda/repo'da üretilmiş veri veya deneyle doğrudan destekli · `[INFERENCE]` mevcut kanıttan mantıksal çıkarım · `[HYPOTHESIS]` test edilmemiş fikir · `[RADICAL]` spekülatif, büyük dönüşüm potansiyelli.

---

## 0. ORTAK KANIT TABANI (tüm perspektiflerin üzerine inşa ettiği zemin)

Bunlar varsayım değil — bu proje boyunca üretilen gerçek sonuçlar. Her perspektif bunları farklı yorumlayabilir ama hiçbiri bunları görmezden gelemez.

`[EVIDENCE]`
- `composite_score` rank-IC ≈ **−0.028**, `finpilot_score` ≈ **+0.034** — ekonomik olarak sıfır, monoton değil.
- `entry_ok` cohort (n=799): tüm maliyet senaryolarında (0.25/0.55/1.00%) net ortalama **negatif**; validasyonda (n=225) **−1.13%**, train'den (n=574, −0.17%) daha kötü.
- **İki bağımsız inversiyon:** `entry_ok` eligible (n=262, win 32.8%, −0.95%) **rejected**'den (n=26.863, win 41.8%, +0.37%) kötü; `conviction_tier` A (win 23%) < B (27%) < C (42%) — en yüksek "conviction" en düşük kazanma oranı.
- **Tek OOS-tutarlı, rejim-dayanıklı bulgu:** ATR → gerçekleşen MAE, IC ≈ **−0.51**, hem bull hem bear rejimde aynı yönde. Bu **risk** boyutu, **yön** boyutu değil.
- Sektör-trend katmanı 143 gerçek-sektör sembolde güçlü ve OOS-tutarlı (win 58% vs 44%) ama tam evrende %24-doğru proxy ile **replike olmadı** — çürütülmedi, kanıtlanamadı.
- P0 (score replay) `INSUFFICIENT_DATA`; P1 null kontrollerinde aday negatif ortalamalı; P2 tüm maliyet senaryolarında negatif; P3 kapasite/execution verisi yok.
- Barrier-sensitivity grid (2.520 config) ve fixed-target protokolü (3.120 config): **0** maliyet-pozitif + dönem-stabil konfigürasyon; locked holdout hiç açılmadı.
- Portföy simülasyonunun en iyi konfigürasyonu **başa-baş** (CAGR %0.62, Sharpe 0.23).
- Score kalibrasyonu: Brier train 0.236 / test 0.248, quintile'lar monoton değil.
- Evren: ~1.929 sembol, medyan dolar-ADV ~$1M, likidite-uygun oran **%11.85**, spread-kaynak kapsamı **%0**.
- Örneklem döneminin **~%87'si bull** (SPY 50-SMA üstü) — mutlak getiri ölçümleri büyük olasılıkla beta ile kirli.
- Giriş-zamanlaması (sinyal-close / ertesi-open / ertesi-close) **hiç ayrıştırılmadı**; drift/half-life eğrisi hiç çizilmedi; sektör kapsamı gerçek etiketle sadece **%8.31**.

Bu tablo şunu söylüyor: **elimizde "yön tahmin etmiyor" için güçlü kanıt, "neden" için sadece ipuçları var.** 10 perspektif bu boşluğu farklı açılardan dolduracak.

---

## PERSPEKTİF 1 — QUANTITATIVE RESEARCH SCIENTIST

### 1. Teşhis
FinPilot şu ana kadar **noise'u optimize etti**, predictive signal aramadı — çünkü arama uzayı (TP/SL/horizon/threshold, binlerce config) sinyal keşfinden çok label-mühendisliğine hizmet etti `[EVIDENCE]`. Asıl sorun target seçimi: sistem "gelecek getiri" hedefliyor ama kanıtlanan tek geçerli hedef "gelecek aralık/risk" (ATR→MAE). Yani **yanlış target'ı test ettik, doğru olanı zaten bulduk ama ona "başarısız alfa araştırmasının yan ürünü" muamelesi yaptık** `[INFERENCE]`. İkinci sorun: entry_ok/conviction inversiyonu tek bir mekanizmadan (extension/exhaustion) kaynaklanıyor olabilir ama hiç doğrudan test edilmedi `[HYPOTHESIS]`. Üçüncü sorun: giriş anı hiç ayrıştırılmadı — "edge yok" hükmü aslında "edge bu ölçüm noktasında görünmüyor" olabilir `[INFERENCE]`.

### 2. En büyük 5 yanlış varsayım
```
Varsayım: Future return doğru prediction target'tır.
Neden yanlış olabilir: Lottery/heavy-tail dağılımda mean-expectancy metriği kuyruğa esir; risk hedefinde (ATR→MAE) güçlü sinyal var, getiri hedefinde yok.
Kanıt: [EVIDENCE] ATR IC −0.51 (risk) vs composite IC −0.028 (getiri).
Nasıl test edilir: Aynı feature seti, iki ayrı hedefle (gelecek getiri vs gelecek MAE/aralık) paralel scorecard.

Varsayım: entry_ok/skor gibi filtreler kaliteyi artırır.
Neden yanlış olabilir: İki bağımsız kapı ters kalibre; muhtemelen "uzamış/tükenmiş" isimleri seçiyor.
Kanıt: [EVIDENCE] eligible < rejected; conviction A < C.
Nasıl test edilir: Extension/exhaustion decomposition + inversiyonun OOS/kümelenme-robustluğu.

Varsayım: 5 günlük horizon doğru değerlendirme ufkudur.
Neden yanlış olabilir: Half-life hiç ölçülmedi; drift kısa ömürlü olabilir, 5 gün onu sulandırıyor olabilir.
Kanıt: [INFERENCE] TP/SL grid'de uzun horizon'larda medyan negatif, ortalama outlier'a esir.
Nasıl test edilir: Bariyersiz event-study eğrisi t+1..t+10.

Varsayım: %0.55 sabit maliyet gerçekçi execution proxy'sidir.
Neden yanlış olabilir: Medyan ADV ~$1M, spread kapsamı %0 — küçük-cap/yüksek-vol isimlerde gerçek round-trip çok daha yüksek olabilir.
Kanıt: [EVIDENCE] likidite-uygun oran %11.85.
Nasıl test edilir: ADV/volatilite-bağımlı parametrik maliyet modeli + investable-universe alt kümesi.

Varsayım: Locked OOS hâlâ "temiz" bir sınav.
Neden yanlış olabilir: Aynı tarih aralığına onlarca deneyle defalarca bakıldı; araştırmacı-serbestliği yüksek ihtimalle kontamine etti.
Kanıt: [INFERENCE] Tek dönem, çok sayıda hipotez, hiç dondurulmamış pre-registration.
Nasıl test edilir: Sealed tut, yeni kanıtı yalnızca ileri (forward/shadow) veriyle üret.
```

### 3. Kaçırdığımız 10 şey (öncelik sırası)
1. Giriş-noktası ayrıştırması (sinyal-close/ertesi-open/ertesi-close) — hiç yapılmadı.
2. Bariyersiz drift/event-study eğrisi — TP/SL'den önce gelmesi gereken adım hiç atılmadı.
3. Market/sektör-nötr (excess) getiri birincil metrik değil, ikincil kaldı.
4. Extension/exhaustion mekanizma testi — inversiyonun "neden"i hiç adlandırılmadı.
5. Cross-sectional (günlük kesit, rank-bazlı) alfa çerçevesi hiç birincil hedef yapılmadı.
6. Geometrik/log getiri veya tail-capture çerçevesi hiç denenmedi — aritmetik ortalama lottery evreninde yanıltıcı.
7. Cluster-robust / block-bootstrap standart hata hiç kullanılmadı (aynı gün korelasyonlu sinyaller).
8. Gerçek sektör etiketiyle tam-evren testi (yalnız %24-doğru proxy denendi).
9. Feature-redundancy / PCA ile "gerçek bağımsız eksen sayısı" hiç ölçülmedi (composite↔finpilot 0.98 korelasyonlu olduğu biliniyor ama sistematik değil).
10. Survivorship / point-in-time evren üyeliği hiç doğrulanmadı.

### 4. 10 yeni deney
```
1) Hypothesis: Getiri değil, gelecek-aralık (MAE/MFE) doğru target'tır.
   Test: Aynı feature seti iki hedefle regresyon/IC.
   Dataset: edge_recheck.csv (mevcut).
   Metric: rank-IC, IS/OOS.
   Success: Risk-target IC |>0.3| kararlı; Failure: fark yok.
   Expected learning: Hangi hedefe yatırım yapmalıyız.

2) Hypothesis: Edge sinyal-close'da var, ertesi-open'da kayboluyor (gap'e fiyatlanmış).
   Test: 3 giriş noktası × t+1..t+10 kümülatif getiri.
   Dataset: price_cache + edge_recheck sinyalleri.
   Metric: excess return eğrisi, giriş noktaları arası fark.
   Success: close>>open farkı anlamlı; Failure: fark yok.
   Expected learning: Trade edilebilirlik sınırı nerede.

3) Hypothesis: entry_ok/conviction inversiyonu extension/exhaustion kaynaklı.
   Test: VWAP/EMA uzaklık, ATR-extension, close-location ile eligible/rejected ayrıştır.
   Dataset: full_universe_enriched + price_cache.
   Metric: extension bucket × win rate.
   Success: extension yüksek→win düşük monoton; Failure: yok.
   Expected learning: Filtre ters mi çalışıyor, fade adayı mı var.

4) Hypothesis: Drift half-life 5 günden kısa.
   Test: Bariyersiz kümülatif excess getiri eğrisi.
   Dataset: price_cache + SPY/sektör ETF.
   Metric: eğrinin tepe noktası.
   Success: net tepe var; Failure: düz eğri.
   Expected learning: Doğru holding ufku.

5) Hypothesis: Market-nötr alfa yok ama koşullu (rejim×sektör) alfa var.
   Test: excess-return'ü rejim × sektör-trend ile kır.
   Dataset: edge_recheck + sector_cache (143) + full sektör ataması.
   Metric: hücre-bazlı IC/win.
   Success: en az bir hücre OOS-tutarlı; Failure: hepsi düz.
   Expected learning: Koşullu edge var mı.

6) Hypothesis: Aritmetik ortalama, lottery evreninde yanıltıcı.
   Test: log-getiri + trimmed-mean + tail-katkı analizini paralel raporla.
   Dataset: mevcut tüm sonuç tabloları.
   Metric: mean vs trimmed-mean vs median tutarlılığı.
   Success: metrikler yakınsıyor; Failure: büyük ayrışma (mevcut durum).
   Expected learning: Hangi metrik güvenilir.

7) Hypothesis: Aynı-gün kümelenme standart hataları şişiriyor.
   Test: block-bootstrap / cluster-robust CI ile mevcut "anlamlı" sonuçları tekrar test et.
   Dataset: mevcut null-kontrol sonuçları.
   Metric: CI genişliği önce/sonra.
   Success: bazı "anlamlı" sonuçlar anlamsızlaşır (beklenen); Failure: değişmez.
   Expected learning: Kaç bulgu gerçekten yanlış-güven taşıyor.

8) Hypothesis: entry_ok gerçek bir fade sinyali.
   Test: eligible'ı ters çevirip (fade) matched-random ve OOS'a karşı sına — yalnız ölç, kural yapma.
   Dataset: entry_ok cohort.
   Metric: fade-excess return, robustluk.
   Success: OOS+kümelenmemiş tutarlı ters sinyal; Failure: gürültü.
   Expected learning: Inversiyon gerçek mi, artefakt mı.

9) Hypothesis: Composite/finpilot skorları 2-3 bağımsız eksene indirgeniyor.
   Test: PCA + VIF üzerinde tüm feature ailesi.
   Dataset: full_universe_enriched.
   Metric: kümülatif varyans %90'a kaç bileşen.
   Success: <=3 bileşen; Failure: >=6.
   Expected learning: Skor mimarisini basitleştirme gerekçesi.

10) Hypothesis: Locked holdout kontamine; forward-shadow tek temiz sınav.
    Test: yeni pre-registered aday setini yalnız ileri veriyle (immutable log) puanla.
    Dataset: gelecek scan çıktıları (daily_shadow_update).
    Metric: forward excess return, OOS.
    Success: pozitif+tutarlı; Failure: negatif/düz (beklenen taban çizgisi).
    Expected learning: Geçmişe bakışın yerini gerçek zamanlı kanıt alır.
```

### 5. Bırakılması gereken 5 şey
TP/SL ince-ayar taraması · sabit %0.55 maliyet varsayımıyla "sonuç" ilan etmek · aritmetik-ortalama expectancy tek metrik olarak · mevcut composite_score'u herhangi bir kararda kullanmak · locked holdout'u tekrar tekrar "neredeyse açalım" diye gündeme getirmek.

### 6. Tamamen bırakılması gereken 5 şey
Score eşiği optimizasyonunu "araştırma" saymak · aynı feature ailesinde yeni kombinasyon taraması · P0'ı promotion gate yapmak (infrastructure contract'a indirgenmeli) · "yüksek ortalama = edge" okuması · getiri hedefini varsayılan/tek hedef kabul etmek.

### 7. Değiştirilmesi gereken 5 şey
Target: getiri → risk/aralık birincil, getiri ikincil · metrik: aritmetik ortalama → trimmed/log/tail-decomposed · kontrol grubu: rejected → investable-universe matched-random · standart hata: naif → cluster-robust · holdout stratejisi: tekrar-bakılan geçmiş → sealed + forward shadow.

### 8. Eklenmesi gereken 5 şey
Giriş-noktası telemetrisi (close/open/close ayrı sütun) · event-study/drift eğrisi altyapısı · gerçek sektör etiketleme pipeline'ı · PIT (point-in-time) evren üyeliği doğrulaması · cluster-robust istatistik kütüphanesi.

### 9. Radikal fikirler
1. `[RADICAL]` FinPilot'un "skoru" hiç üretmesin; onun yerine **iki ayrı sayı** üretsin: beklenen aralık (risk) ve kesitsel rank (relative strength) — asla birleştirilmiş tek sayı değil.
2. `[RADICAL]` Getiri hedefini tamamen terk edip FinPilot'u resmen bir **volatilite/risk tahmin motoru** olarak yeniden konumlandır.
3. `[HYPOTHESIS]` entry_ok'u tersine çevirip "en çok reddedilenler" fade-adayı olarak shadow'a al.
4. `[RADICAL]` Backtest'i tamamen durdur; yalnız forward-shadow ile "kanıt biriktiren" bir rejime geç (research-overfitting'e karşı yapısal çözüm).
5. `[HYPOTHESIS]` Tüm feature'ları PCA ile 3 bağımsız eksene indirip skor mimarisini oradan yeniden kur.

### 10. "Sıfırdan kursaydım"
1. İlk 90 gün: yalnızca ölçüm — hiçbir strateji, hiçbir TP/SL.
2. Tek target: gelecek-aralık (risk), getiri değil.
3. Giriş-noktası 3 değişkenle telemetrilenir, tek "giriş" kabul edilmez.
4. Her hipotez pre-registered card ile başlar, sonuç görülene kadar donmuş kalır.
5. Kontrol grubu her zaman investable-universe'den matched-random.
6. Locked holdout yalnızca insan-onaylı, tek seferlik açılır.
7. İlk üretim çıktısı bir "trade önerisi" değil, bir "risk etiketi" olur.

---

## PERSPEKTİF 2 — MARKET MICROSTRUCTURE / PROFESSIONAL TRADER

### 1. Teşhis
FinPilot fiyat grafiğine **fazla** bakıyor `[INFERENCE]`. Tüm feature seti OHLC türevi (RSI/MACD/ATR/RVOL) — order flow, opsiyon pozisyonlanması, haber/olay zamanlaması, açılış-mekaniği gibi fiyattan **önce** gelen hiçbir bilgi katmanı yok. Küçük-cap/düşük-likidite evreninde (medyan ADV ~$1M `[EVIDENCE]`) günlük bar teknik göstergeleri zaten halka açık ve gecikmeli; bu evrende geriye kalan tek gerçek "bilgi" — kimin, ne zaman, ne kadar aldığı — hiç ölçülmüyor. Ayrıca günlük bar + ertesi-açılış giriş modeli, gecelik gap'i (haberin/momentum'un en çok fiyatlandığı an) sistematik olarak kaçırıyor `[INFERENCE]`.

### 2. En büyük 5 yanlış varsayım
```
Varsayım: Günlük OHLC + teknik gösterge yeterli bilgi katmanıdır.
Neden yanlış olabilir: Bu bilgi zaten fiyata gömülü ve gecikmeli; gerçek asimetri order-flow/pozisyonlanmada olabilir.
Kanıt: [EVIDENCE] composite/finpilot IC ~0 — mevcut feature ailesi bilgi taşımıyor.
Nasıl test edilir: Opsiyon/positioning verisi eklenip (EODHD UnicornBay, şu an erişim yok) IC karşılaştırması.

Varsayım: Günlük bar + ertesi-açılış doğru cadence'tir.
Neden yanlış olabilir: Sinyal kapanışta oluşuyor, hareketin suyu gece gap'inde fiyatlanabiliyor.
Kanıt: [INFERENCE] hiç ölçülmedi ama mekanizma olarak makul.
Nasıl test edilir: 3 giriş-noktası testi (bkz. Perspektif 1, deney 2).

Varsayım: Sabit %0.55 maliyet tüm evrende geçerlidir.
Neden yanlış olabilir: Düşük-ADV/yüksek-spread isimlerde gerçek maliyet çok daha yüksek olabilir; likidite-uygun oran %11.85.
Kanıt: [EVIDENCE] spread-kaynak kapsamı %0, ADV medyanı düşük.
Nasıl test edilir: ADV/volatilite bazlı parametrik maliyet modeli.

Varsayım: 1D timeframe doğru analiz birimidir.
Neden yanlış olabilir: Momentum/squeeze kurulumları saatler içinde çözülebilir; 1D bar bunu ortalıyor.
Kanıt: [HYPOTHESIS] test edilmedi.
Nasıl test edilir: İntraday feed edinilirse 15m/1h/4h event-time analiz.

Varsayım: Fiyat hareketi kendi kendini açıklar.
Neden yanlış olabilir: Earnings/haber/katalizör olmadan "neden şimdi" sorusu cevapsız kalıyor.
Kanıt: [INFERENCE] catalyst_factor feature var ama ayrı test edilmedi.
Nasıl test edilir: Event-driven alt-küme (earnings/haber sonrası) ayrı IC testi.
```

### 3. Kaçırdığımız 10 şey
1. Order-flow/positioning verisi (opsiyon put/call, OI) — erişim yok, hiç denenemedi.
2. Gap-mekaniği: açılış oynaklığı, ilk 5-15 dakika davranışı — günlük veri bunu göremiyor.
3. Event-time çerçevesi (earnings/haber sonrası saat-bazlı) hiç kurulmadı.
4. Intraday hacim eğrisi (participation rate tahmini) yok.
5. Institutional flow proxy'si (büyük blok işlemler, dark pool) hiç düşünülmedi.
6. Volatilite-clustering'in kendisi (GARCH-tarzı) feature olarak kullanılmadı, yalnız ATR nokta-tahmini var.
7. Sektör içi göreli likidite (aynı sektörde en likit/en illikit) hiç kıyaslanmadı.
8. Halt/LULD/düşük-float davranışı hiç modellenmedi.
9. Açılış-kapanış asimetrisi (overnight vs intraday getiri ayrımı) hiç ayrıştırılmadı.
10. Haftanın günü / ay-sonu / opex gibi takvim-mikroyapı etkileri test edilmedi.

### 4. 10 yeni deney (özet tablo)
| # | Hipotez | Beklenen öğrenme |
|---|---|---|
| 1 | Overnight (close→open) getiri, intraday (open→close) getiriden farklı bilgi taşır | Hangi bölüm alınabilir |
| 2 | Yüksek-RVOL günlerinde ertesi-gün likidite bozuluyor (spread genişliyor) | Gerçek execution riski |
| 3 | Earnings-sonrası alt-küme, teknik-sinyal alt-kümesinden farklı IC verir | Event-driven hipotez canlı mı |
| 4 | Aynı sektörün en-likit %20'si, en-illikit %20'sinden farklı sinyal-kalitesi taşır | Likidite confound mu, gerçek mi |
| 5 | ATR-extension + hacim-tepe-sonrası-düşüş kombinasyonu exhaustion işareti | Extension/exhaustion mekanizması |
| 6 | Gap-continuation vs gap-fade, likidite kovasına göre ayrışır | Hangi gap-türü trade edilir |
| 7 | Haftanın günü / ay-sonu etkisi mevcut sinyalde var mı | Takvim confound'u temizleme |
| 8 | Float/ADV düşük isimlerde MAE daha volatil mi | Kapasite-öncesi filtre gerekçesi |
| 9 | Volatilite kümelenmesi (GARCH benzeri) ATR nokta-tahminini geçer mi | Risk modelini geliştirme |
| 10 | Opsiyon verisi erişilebilir olduğunda IC karşılaştırması (put/call, IV skew) | Yeni-bilgi katmanının değeri |

### 5-8. Bırak/Değiştir/Ekle (özet)
**Bırak:** teknik-gösterge-merkezli feature genişletmesi · **Tamamen bırak:** "günlük bar yeterli" varsayımı · **Değiştir:** analiz birimini event-time'a kaydır (mümkün olduğunda) · **Ekle:** overnight/intraday ayrımı, likidite-kovası segmentasyonu.

### 9. Radikal fikirler
1. `[RADICAL]` FinPilot'un ana analiz birimi "gün" değil "event" olsun (earnings, haber, hacim-şoku).
2. `[HYPOTHESIS]` Overnight getiriyi ayrı bir "gap risk" ürünü olarak paketle — bu zaten ölçülebilir ve az emek ister.
3. `[RADICAL]` Fiyat-merkezli scanner'ı bırak, "likidite-kalite" merkezli bir tarayıcıya dönüş: "bu isim bugün gerçekten alınabilir mi" sorusu başlı başına ürün olabilir.

### 10. "Sıfırdan kursaydım"
1. Önce likidite/spread telemetrisini kur, sinyal üretmeden önce.
2. Event-time'ı birincil zaman birimi yap.
3. Overnight/intraday getiriyi hep ayrı raporla.
4. İlk feature ailesi teknik gösterge değil, likidite+event olur.

---

## PERSPEKTİF 3 — BEHAVIORAL FINANCE SCIENTIST

### 1. Teşhis
Grade/conviction sistemi, kanıtlanmış biçimde **ters kalibre** (`[EVIDENCE]` A win 23% < C win 42%) — yani şu an kullanıcıya *yanlış yönde* bir güven anchor'ı veriyor. Bu teknik bir bug değil, **davranışsal bir risk**: kullanıcı "Grade A" gördüğünde muhtemelen ek doğrulama aramayı bırakır (confirmation-seeking azalır, anchoring artar) `[HYPOTHESIS]`. FinPilot'un en büyük gizli tehlikesi, kötü kalibre bir güven sinyalinin kullanıcının kendi şüpheciliğini bastırması olabilir.

### 2. En büyük 5 yanlış varsayım
```
Varsayım: Grade kullanıcının kararını kolaylaştırır.
Neden yanlış olabilir: Kalibre değilse (kanıtlı), kolaylaştırdığı şey karar değil, yanlış-güven.
Kanıt: [EVIDENCE] conviction inversiyonu.
Nasıl test edilir: Grade'i gizleyip/gösterip kullanıcı kararlarının kalitesini (post-hoc) karşılaştıran A/B.

Varsayım: Daha yüksek conviction daha iyi sonuç demektir.
Neden yanlış olabilir: Doğrudan tersinin kanıtı var.
Kanıt: [EVIDENCE] A<B<C win rate.
Nasıl test edilir: Zaten test edildi — sıradaki adım kullanıcı davranışını (Grade A'da işlem sıklığı) ölçmek.

Varsayım: Kullanıcı olasılık değil, kategori (A/B/C) ister.
Neden yanlış olabilir: Kategoriler yanlış anlaşılmaya (kesinlik illüzyonu) daha açık; kalibre olasılık daha dürüst.
Kanıt: [INFERENCE] forecasting literatüründe (Tetlock) kategorik tahminlerin kalibrasyonu daha zor değerlendirilir.
Nasıl test edilir: Grade yerine "%X olasılık + geçmiş kalibrasyon eğrisi" gösterip kullanıcı güvenini ölç.

Varsayım: Daha fazla confirmation (RSI+MACD+volume) daha güvenilir sinyal üretir.
Neden yanlış olabilir: Kullanıcıda da "üç gösterge aynı anda = güçlü" narrative fallacy'si var; sistemde de aynı yanılgı gömülü olabilir.
Kanıt: [EVIDENCE] score_3, score_2'den üstün değil.
Nasıl test edilir: Information-diversity testi (Perspektif kesişimi, bkz. §4 aşağıda).

Varsayım: Geçmiş performans göstermek kullanıcıya yardımcı olur.
Neden yanlış olabilir: Outcome bias + hindsight bias tetikleyebilir; "geçmişte iyiydi" kullanıcıyı gelecekte de iyi olacağına ikna eder.
Kanıt: [INFERENCE] genel davranışsal finans literatürü + FinPilot'un kendi edge-yokluğu kanıtı.
Nasıl test edilir: Geçmiş performans gösterilen/gösterilmeyen gruplarda kullanıcı risk algısı anketi.
```

### 3. Kaçırdığımız 10 şey
1. Grade'in kullanıcı davranışını nasıl değiştirdiği hiç ölçülmedi (yalnız sinyal kalitesi ölçüldü, davranışsal etki değil).
2. Kalibrasyon eğrisi kullanıcıya hiç gösterilmiyor.
3. "Bu tahmin yanlış çıkarsa ne olur" senaryosu ürün içinde hiç yok (pre-mortem eksik).
4. Kullanıcının kendi geçmiş kararlarını gözden geçirme (retrospektif) mekanizması yok.
5. Loss-aversion'ı azaltacak risk-çerçeveleme (ATR→beklenen-aralık) henüz kullanıcıya taşınmadı.
6. Recency bias'a karşı "bu ay/geçen ay farklıydı" uyarısı sistematik değil.
7. Kullanıcı segmentasyonu yok — acemi ile deneyimli yatırımcı aynı Grade dilini görüyor.
8. Confirmation-seeking'i azaltacak "karşıt görüş" (bear case) hiç sunulmuyor.
9. Kullanıcı karar-kalitesini (sonuç değil süreç) ölçen hiçbir metrik yok.
10. Gambler's-fallacy'ye açık dil ("art arda 3 gün yükseldi, düzeltme gelir" tarzı) denetlenmiyor.

### 4. 10 yeni deney (özet)
Grade açık/kapalı A-B testi · kalibrasyon-eğrisi gösterimi deneyi · bear-case zorunlu gösterimi deneyi · "bu tahmin yanlış çıkarsa" pre-mortem promptu · karar-günlüğü (kullanıcı neden bu işlemi yaptı) · recency-bias uyarı denemesi · information-diversity vs confirmation-count karşılaştırması · segment-bazlı dil testi (acemi/uzman) · outcome-bias azaltma: sonuç yerine süreç puanı gösterme · retrospektif "3 ay önce ne düşünmüştün" hatırlatması.

### 5-8. Bırak/Değiştir/Ekle
**Bırak:** tek-harf Grade'i tek başına öne çıkarma · **Tamamen bırak:** kalibre edilmemiş conviction dilini üretimde kullanmak · **Değiştir:** Grade → kalibre olasılık + belirsizlik aralığı · **Ekle:** bear-case/karşıt-görüş, karar-günlüğü, pre-mortem promptu.

### 9. Radikal fikirler
1. `[RADICAL]` **FinPilot hiç Grade vermesin.** Onun yerine "şu an bilmediğimiz şey şu" diyen bir belirsizlik kartı versin.
2. `[HYPOTHESIS]` Her öneriye zorunlu bir "bu neden yanlış çıkabilir" bölümü ekle (yapısal pre-mortem).
3. `[RADICAL]` Ürünün başarı metriği "kullanıcı işlem yaptı mı" değil, "kullanıcının kararı 3 ay sonra tutarlı mıydı" olsun.

### 10. "Sıfırdan kursaydım"
1. Grade yok; kalibre olasılık + geçmiş kalibrasyon eğrisi var.
2. Her öneri yanında zorunlu karşıt-görüş.
3. Kullanıcı karar-günlüğü tutuyor, sistem ona geri bildirim veriyor.
4. Başarı metriği: karar-kalitesi, trading-performance değil.

---

## PERSPEKTİF 4 — PRODUCT STRATEGIST / STARTUP FOUNDER

### 1. Teşhis
FinPilot bugün "stock scanner + Grade + Morning Ledger" kategorisinde konumlanıyor — ama kendi kanıtı bu kategoride **kaybediyor** (alfa yok, Grade ters kalibre). Aynı zamanda üzerine inşa edilen altyapı (immutable telemetry, null-kontrolleri, honest-metric disiplini, dedup/PIT hijyeni) bu kategorinin **çok üstünde** bir kalite — ve bu değer şu an yanlış kategoride harcanıyor `[INFERENCE]`. En büyük stratejik risk: "hisse seçen ürün" olarak kalmaya devam edip, gerçekte sahip olduğu (araştırma-disiplini, dürüst-ölçüm, risk-çerçeveleme) varlığı asla ürünleştirmemek.

### 2. En büyük 5 yanlış varsayım
```
Varsayım: FinPilot hisse seçmelidir.
Neden yanlış olabilir: Seçim halkası kanıtlı biçimde çalışmıyor (ters bile); asıl güçlü olan risk-çerçeveleme.
Kanıt: [EVIDENCE] entry_ok/conviction inversiyonu.
Nasıl test edilir: "Hisse seçmeyen" bir versiyonu (yalnız risk/kontekst) küçük kullanıcı grubuna sun, memnuniyeti kıyasla.

Varsayım: Kullanıcı yatırım kararı vermek istiyor.
Neden yanlış olabilir: Belki asıl istek "zaman kazanmak" veya "kendi kararına güvenmek" — yatırım kararının kendisi değil.
Kanıt: [HYPOTHESIS] test edilmedi.
Nasıl test edilir: Kullanıcı görüşmesi / kullanım-motivasyonu anketi.

Varsayım: Morning Ledger nihai ürün biçimidir.
Neden yanlış olabilir: Statik günlük özet, aktif araştırma platformunun (asıl varlığın) sadece bir çıktısı — asıl değeri gizliyor olabilir.
Kanıt: [INFERENCE] ürünün gerçek gücü (araştırma altyapısı) Ledger'da görünmüyor.
Nasıl test edilir: Ledger yerine "araştırma günlüğü" (bugün ne test ettik, ne öğrendik) formatını dene.

Varsayım: Daha fazla feature/kombinasyon ürünü güçlendirir.
Neden yanlış olabilir: Onlarca feature zaten 2-3 bağımsız eksene iniyor (redundancy kanıtlı).
Kanıt: [EVIDENCE] composite↔finpilot korelasyon 0.98.
Nasıl test edilir: Feature-count'u yarıya indirip kullanıcı algısını/sonuç kalitesini kıyasla.

Varsayım: Eğitim ürünün ana değeri değil, yan-özelliği.
Neden yanlış olabilir: Alfa yoksa, kalıcı moat büyük ihtimalle "kullanıcının düşünme kalitesini artırmak" — bu eğitimdir.
Kanıt: [INFERENCE] alfa-yokluğu kanıtı + FinSense/aws-impact pozisyonlaması zaten bu yöne onaylı.
Nasıl test edilir: Eğitim-merkezli bir alt-ürünü ayrı ölç (retention, öğrenme-kazanımı).
```

### 3. Kaçırdığımız 10 şey
1. Kullanıcı asıl neyi satın alıyor — hiç doğrudan sorulmadı.
2. Rakiplerin neden aynı şeyi yapmadığı (regülasyon mu, ekonomi mi, teknik mi) analiz edilmedi.
3. "Tek özellik kalsaydı" testi hiç yapılmadı.
4. Değer önerisinin "alfa" değil "zaman + güven + öğrenme" olabileceği ciddiye alınmadı.
5. FinSense/aws-impact pozisyonlamasıyla scanner-merkezli ürün arasındaki iç tutarsızlık hiç adlandırılmadı.
6. Kullanıcı segment farkı (acemi vs deneyimli) ürün mimarisine hiç yansımadı.
7. "Delete everything and restart" egzersizi hiç yapılmadı.
8. Araştırma-disiplininin kendisinin (dürüst NO-GO kararları) bir güven-inşa aracı olarak pazarlanabileceği görülmedi.
9. Business-model alternatifleri (B2C sinyal değil, B2B/eğitim/araştırma-araçları) hiç değerlendirilmedi.
10. "10x daha değerli olmak için ne değişmeli" sorusu hiç sistematik sorulmadı.

### 4. 10 yeni deney
Küçük kullanıcı grubuna Grade'siz versiyon sun · "araştırma günlüğü" formatını Ledger yerine test et · kullanıcı motivasyon anketi (neden kullanıyorsun) · tek-özellik testi (yalnız risk-kartı) · B2B/eğitim pilotunu ayrı ölç · NO-GO kararlarının şeffaf gösterilmesinin güven etkisini ölç · segment-bazlı arayüz (acemi/uzman) A/B · "bugün ne öğrendik" e-postasının açılma/geri-bildirim oranı · scanner'sız bir hafta deneyi (yalnız risk+eğitim) · fiyatlandırma testinde "sinyal" vs "araştırma aracı" çerçevelemesi.

### 5-8. Bırak/Değiştir/Ekle
**Bırak:** Grade'i öne çıkaran arayüz · **Tamamen bırak:** "biz hisse seçiyoruz" mesajlaşması · **Değiştir:** Morning Ledger → araştırma-günlüğü formatı · **Ekle:** şeffaf NO-GO/negatif-sonuç anlatısı (güven inşası olarak).

### 9. Radikal fikirler
1. `[RADICAL]` FinPilot bir "sinyal ürünü" değil, **"dürüst araştırma laboratuvarı"** olarak pazarlansın — NO-GO kararları özellik, kusur değil.
2. `[HYPOTHESIS]` Business model B2C sinyal aboneliğinden, B2B/kurumsal "araştırma-altyapısı-hizmeti"ne kaysın.
3. `[RADICAL]` Tek özellik kalsaydı: risk/aralık kartı. Her şey onun etrafında yeniden kurulur.

### 10. "Sıfırdan kursaydım"
1. Değer önerisi: "doğru hisse" değil "doğru risk çerçevesi + dürüst kanıt."
2. Ledger yerine haftalık "ne test ettik, ne öğrendik" günlüğü.
3. Grade yok, kalibre risk/belirsizlik var.
4. Hedef kullanıcı net segmentlere ayrılmış (acemi/orta/ileri).
5. Business model: sinyal aboneliği değil, araştırma-aracı + eğitim.

---

## PERSPEKTİF 5 — MACHINE LEARNING / AI RESEARCHER

### 1. Teşhis
Şu an AI/skorlama katmanı **prediction** rolünde ve bu rolde kanıtlanmış biçimde başarısız (IC~0, ters kalibrasyon). Ama AI'ın FinPilot'ta hiç kullanılmadığı, çok daha güçlü bir rolü var: **araştırma-üretimi.** Bu proje boyunca (bu konuşmanın kendisi dahil) en değerli AI-katkısı tahmin üretmek değil, hipotez üretmek/çürütmek/mekanizma önermek oldu `[INFERENCE]`. Yani mevcut mimari AI'ı yanlış yerde kullanıyor: zayıf olduğu yerde (gürültülü finansal tahmin) yoğun, güçlü olabileceği yerde (hipotez üretimi, kod-destekli araştırma, adversarial test) hiç yok.

### 2. En büyük 5 yanlış varsayım
```
Varsayım: AI prediction yapmalı.
Neden yanlış olabilir: Prediction'da (composite/finpilot score) kanıtlı başarısızlık var; research-generation'da hiç denenmedi.
Kanıt: [EVIDENCE] IC~0, ters kalibrasyon.
Nasıl test edilir: AI'ı "yeni hipotez üret" rolüne koyup, ürettiği hipotezlerin kaçının OOS'ta hayatta kaldığını ölç.

Varsayım: Daha karmaşık model (DRL/derin öğrenme) daha iyi sonuç verir.
Neden yanlış olabilir: Basit matched-control baseline'ı bile geçemeyen bir sinyale karmaşıklık eklemek overfitting kapasitesini artırır, bilgiyi değil.
Kanıt: [INFERENCE] mevcut basit feature'lar zaten IC~0; DRL ağırlığı zaten 0 (finpilot_score ≈ composite passthrough).
Nasıl test edilir: DRL'yi tekrar açmadan önce basit baseline'ın maliyet-sonrası pozitif olduğunu kanıtla (henüz yok).

Varsayım: Daha fazla veri daha iyi sonuç verir.
Neden yanlış olabilir: Mevcut veri hacmi (53K+ satır) zaten sinyal aramak için yeterliydi; sorun hacim değil, hangi bilgi katmanının eksik olduğu (order-flow, event-timing).
Kanıt: [EVIDENCE] 53.754 satırda IC~0; büyütmek (8.000 evren) aynı feature ailesiyle aynı sonucu verir muhtemelen.
Nasıl test edilir: Yeni bilgi katmanı (opsiyon/sektör/event) eklenmeden evren büyütmenin IC'yi değiştirip değiştirmediğini izle.

Varsayım: Explainability = güven.
Neden yanlış olabilir: "Neden bu skor" açıklaması, skorun kendisi yanlışsa yalnızca inandırıcı bir yanılsama üretir (explainability theater).
Kanıt: [INFERENCE] composite_score'un bileşenleri açıklanabilir ama skor kalibre değil.
Nasıl test edilir: Açıklama-kalitesi ile skor-doğruluğu arasındaki korelasyonu ayrı ölç.

Varsayım: AI personalization otomatik değer katar.
Neden yanlış olabilir: Kişiselleştirme, kalibre olmayan bir temel sinyali kişiselleştirirse yanlışı kullanıcıya özel hale getirir.
Kanıt: [INFERENCE] mantıksal çıkarım — henüz test edilmedi.
Nasıl test edilir: Personalization'ı yalnız risk-tercihi (agresif/muhafazakâr) üzerinde dene, sinyal-doğruluğu üzerinde değil.
```

### 3. Kaçırdığımız 10 şey
1. AI'ı hipotez-üretici olarak kullanmak hiç denenmedi.
2. AI'ın kendi ürettiği stratejileri adversarial test etmesi (kendi kendini çürütmesi) hiç kurulmadı.
3. Gizli-rejim keşfi (unsupervised regime detection) hiç denenmedi — yalnız SPY 50-SMA gibi elle tanımlı rejimler var.
4. Feature-interaction keşfi (otomatik) hiç yapılmadı; tüm kombinasyonlar elle tarandı.
5. AI'ın başarısız deneyleri sentezleyip yeni hipotez önerme rolü hiç kurulmadı.
6. Model-karşılaştırma disiplini (basit baseline vs karmaşık model, sabit protokolle) hiç resmi değil.
7. AI'ın kendi güven-aralığını (epistemic uncertainty) raporlaması hiç yok.
8. News/event understanding (LLM ile haber-sinyali çıkarma) hiç test edilmedi.
9. Simülasyon/counterfactual üretimi (AI'ın "bu farklı olsaydı ne olurdu" üretmesi) hiç kullanılmadı.
10. AI-üretilen hipotezlerin insan-üretilenlerle kıyaslı başarı oranı hiç ölçülmedi.

### 4. 10 yeni deney (özet)
AI'a "yeni feature öner" görevi ver, OOS-hayatta-kalma oranını insan-üretilenlerle kıyasla · AI'a mevcut başarısız deneyleri özetleyip yeni hipotez ürettir · unsupervised rejim keşfi (kümeleme) vs elle-tanımlı rejim IC kıyası · otomatik feature-interaction taraması (dikkatli, pre-registration ile) · AI'ın ürettiği açıklamanın kullanıcı güvenini nasıl etkilediğini ölç · basit-baseline vs DRL sabit protokolle kıyası · AI'a kendi tahminine güven-aralığı ürettir, kalibrasyonunu ölç · haber-özeti + fiyat-tepkisi korelasyonu · AI'ın ürettiği "bull case/bear case" çiftinin kullanıcı kararına etkisi · AI-adversarial: bir modelin diğerinin stratejisini çürütmeye çalışması.

### 5-8. Bırak/Değiştir/Ekle
**Bırak:** AI'ı doğrudan skor/tahmin üretiminde tek rol olarak kullanmak · **Tamamen bırak:** "daha karmaşık model dene" refleksi (kanıtsız) · **Değiştir:** AI rolü prediction → research-generation + adversarial-test · **Ekle:** hipotez-üretici AI, kendi-kendini-çürüten AI, kalibrasyon-raporlayan AI.

### 9. Radikal fikirler
1. `[RADICAL]` Ana AI tahmin üretmesin; **araştırma üretsin** — yeni feature, yeni hipotez, çürütme denemeleri.
2. `[RADICAL]` AI, kendi ürettiği her hipotez için otomatik pre-registration card'ı doldursun ve sonucu (geçti/kaldı) şeffaf logla.
3. `[HYPOTHESIS]` "AI analyst" tekil değil, **çoklu-ajan** (bull/bear/skeptic/historian) yapıda çalışıp anlaşmazlık haritası üretsin — bu konuşmanın kendisinin yaptığı şey.

### 10. "Sıfırdan kursaydım"
1. AI'ın birincil işi tahmin değil, hipotez üretmek ve çürütmek.
2. Her AI-çıktısı pre-registration + sonuç-takibiyle loglanır.
3. Basit baseline her zaman karmaşık modelin karşılaştırma noktası.
4. Açıklanabilirlik, doğruluktan ayrı ölçülür — biri diğerini garanti etmez.

---

## PERSPEKTİF 6 — PORTFOLIO MANAGER / RISK MANAGER

### 1. Teşhis
Tüm araştırma tekil-trade seviyesinde yürütüldü; portföy-seviyesi ekonomisi yalnızca **son adımda**, bir doğrulama olarak test edildi — ve orada da en iyi konfigürasyon başa-baş çıktı `[EVIDENCE]` (CAGR %0.62, Sharpe 0.23). Bu sıra ters: **portföy-inşası, tekil-sinyal aramasından önce gelmeliydi**, çünkü küçük-cap/lottery evreninde tekil pozisyonun varyansı devasa, gerçek soru "hangi hisse" değil "kaç pozisyon, ne kadar korelasyonlu, ne kadar concentration." `[INFERENCE]`

### 2. En büyük 5 yanlış varsayım
```
Varsayım: Doğru hisseyi bulmak, doğru risk-kombinasyonu bulmaktan önemlidir.
Neden yanlış olabilir: Tekil sinyalde edge yok ama iyi çeşitlendirilmiş bir portföy, edge olmadan bile varyansı düşürebilir; şu an bunun tersi yapılıyor.
Kanıt: [EVIDENCE] portföy sim'i en iyi halinde başa-baş, ama concentration/correlation hiç merkezi test edilmedi.
Nasıl test edilir: Aynı sinyal setini farklı concentration/correlation kısıtlarıyla tekrar simüle et.

Varsayım: Top-N (top-5/top-10) doğru seçim mekanizmasıdır.
Neden yanlış olabilir: Top-N aynı gün aynı sektöre/faktöre yığılabilir (aynı-gün clustered sinyaller kanıtlı risk).
Kanıt: [INFERENCE] sektör coverage ve concentration testleri eksik/INSUFFICIENT_DATA.
Nasıl test edilir: Top-N'in günlük sektör/faktör konsantrasyonunu ölç, çeşitlendirme-kısıtlı alternatifle kıyasla.

Varsayım: Tekil-trade expectancy portföye otomatik taşınır.
Neden yanlış olabilir: Zaten kanıtlanmış tersi: iyi görünen tekil barrier expectancy, portföyde başa-başa iniyor.
Kanıt: [EVIDENCE] Perspektif-0 kanıt tabanı, portföy sim sonucu.
Nasıl test edilir: Zaten test edildi; sıradaki adım "neden" — turnover mı, korelasyon mu, capacity mi.

Varsayım: Sharpe/win-rate tek başına yeterli portföy metriğidir.
Neden yanlış olabilir: Heavy-tail/lottery evreninde tail-risk (CVaR, max drawdown, kuyruk-katkısı) çok daha belirleyici.
Kanıt: [INFERENCE] score_2 gibi cohort'larda MAE çok kötü, mean/median büyük ayrışıyor.
Nasıl test edilir: CVaR ve maksimum tekil-pozisyon katkısını her portföy raporunda zorunlu tut.

Varsayım: Capacity sonradan düşünülecek bir detay.
Neden yanlış olabilir: Medyan ADV ~$1M ile küçük bir portföy bile kapasiteyi zorlayabilir; alfa varsa bile yakalanamayabilir.
Kanıt: [EVIDENCE] likidite-uygun oran %11.85, spread-kaynak %0.
Nasıl test edilir: Investable-universe'i baştan tanımlayıp yalnız o evrende portföy simülasyonu.
```

### 3. Kaçırdığımız 10 şey
1. Concentration/korelasyon, top-N seçiminden önce hiç kısıt olarak konmadı.
2. Sektör-bazlı maksimum-ağırlık kısıtı hiç test edilmedi.
3. CVaR/tail-katkı portföy raporlarında zorunlu değil.
4. Turnover'ın (12.27x gözlendi) maliyet üzerindeki gerçek etkisi ayrıştırılmadı.
5. Capacity-first (önce yatırılabilir evren, sonra sinyal) sırası hiç denenmedi.
6. Factor-exposure (beta, momentum-faktörü, küçük-cap faktörü) hiç ayrıştırılmadı — sinyal mi faktör mü karışık.
7. Aynı-gün açılan pozisyonların korelasyon riski hiç ölçülmedi.
8. Position-sizing'in ATR-risk bulgusuyla (kanıtlı geçerli boyut) hiç entegre edilmemiş olması — en hazır fırsat bu.
9. Drawdown-sonrası davranış (kaç gün, hangi büyüklükte) hiç karakterize edilmedi.
10. Alternatif başarı metrikleri (CVaR-adjusted return, diversification ratio) hiç raporlanmadı.

### 4. 10 yeni deney (özet)
```
1) Hypothesis: Concentration kısıtı (max %X/sektör) portföy Sharpe'ını artırır, edge olmadan bile.
   Test: Aynı sinyal seti, kısıtlı vs kısıtsız portföy simülasyonu.
   Success: Kısıtlı Sharpe > kısıtsız; Failure: fark yok.

2) Hypothesis: ATR-risk boyutu position-sizing'e entegre edilirse portföy varyansı düşer.
   Test: Eşit-ağırlık vs ATR-ters-orantılı sizing.
   Success: Aynı getiri, düşük varyans; Failure: fark yok.

3) Hypothesis: Investable-universe (capacity-filtreli) alt kümesinde portföy sonucu tam-evrenden farklı.
   Test: İki evrende paralel simülasyon.
   Success: Fark anlamlı; Failure: aynı (o zaman capacity confound değil).

4) Hypothesis: Aynı-gün açılan pozisyonlar yüksek korelasyonlu.
   Test: Günlük top-N'in gerçekleşen kesişim-korelasyonu.
   Success: Korelasyon yüksek (çeşitlendirme yanılsaması); Failure: düşük.
```
(Kalan 6 deney aynı aileden: turnover-maliyet ayrıştırma, CVaR-raporlama, drawdown-karakterizasyonu, factor-exposure ayrıştırma, sektör-max-ağırlık taraması, diversification-ratio izleme.)

### 5-8. Bırak/Değiştir/Ekle
**Bırak:** top-N'i tek seçim mekanizması olarak kullanmak · **Tamamen bırak:** portföy testini "son doğrulama adımı" yapmak · **Değiştir:** sıra: portföy-inşası tekil-sinyal aramasından ÖNCE gelsin · **Ekle:** concentration kısıtı, CVaR raporlama, ATR-bazlı sizing.

### 9. Radikal fikirler
1. `[RADICAL]` FinPilot doğru hisseyi bulmaya çalışmayı bıraksın, **doğru risk-kombinasyonunu** bulsun — top-10 yerine portfolio construction birincil ürün olsun.
2. `[HYPOTHESIS]` Edge sıfır olsa bile, iyi çeşitlendirme + ATR-bazlı sizing ile portföy Sharpe'ı iyileştirilebilir — bu, alfa gerektirmeyen tek somut değer artışı.

### 10. "Sıfırdan kursaydım"
1. İlk ürün portföy-inşa motoru, hisse-seçici değil.
2. Concentration/korelasyon kısıtları baştan var.
3. Position-sizing ATR-risk boyutuna bağlı.
4. Capacity, evren tanımının bir parçası — sonradan eklenen filtre değil.

---

## PERSPEKTİF 7 — FINANCIAL EDUCATOR / LEARNING SCIENTIST

### 1. Teşhis
Morning Ledger ve eğitim içeriği şu an **pasif-tüketim** formatında (oku, geç) — retrieval-practice, spaced-repetition, active-recall gibi öğrenmeyi kalıcı kılan hiçbir mekanizma yok `[INFERENCE]`. Bu, FinPilot'un kendi kanıtladığı gerçekle (alfa yok, ama dürüst-araştırma-disiplini var) doğrudan çelişiyor: eğer gerçek moat "kullanıcının finansal muhakemesini geliştirmek" ise, şu anki format bunu ölçmüyor bile — yalnız açılma/okuma oranı ölçülüyor `[INFERENCE]`.

### 2. En büyük 5 yanlış varsayım
```
Varsayım: Eğitim ürünün ana değeri değil, yan-özelliği.
Neden yanlış olabilir: Alfa-yokluğu kanıtlandıkça, kalıcı değer büyük ihtimalle öğrenme/muhakeme kalitesinde.
Kanıt: [INFERENCE] alfa-yokluğu kanıtı + mevcut aws/FinSense pozisyonlaması.
Nasıl test edilir: Eğitim-etkileşimini (yalnız okuma değil, aktif-hatırlama) ayrı bir retention kohortunda ölç.

Varsayım: Açılma oranı/okuma-süresi öğrenmeyi ölçer.
Neden yanlış olabilir: Pasif tüketim metrikleri, kalıcı öğrenmeyle zayıf korelasyonludur (öğrenme bilimi literatürü).
Kanıt: [INFERENCE] genel kabul görmüş öğrenme-bilimi bulgusu — FinPilot'a özel test edilmedi.
Nasıl test edilir: 30/60/90 gün sonra aktif-hatırlama testi (retrieval quiz) uygula, açılma-oranıyla kıyasla.

Varsayım: Kullanıcı yatırım kararı vermek istiyor (öğrenmek değil).
Neden yanlış olabilir: Bu ikisi karışmış olabilir — bazı kullanıcılar öğrenmek, bazıları karar vermek istiyor; tek arayüz ikisine de hizmet edemez.
Kanıt: [HYPOTHESIS] test edilmedi.
Nasıl test edilir: Kullanıcı segmentasyonu (öğrenme-odaklı vs karar-odaklı) anketi.

Varsayım: Grade kavramı öğretici bir araçtır.
Neden yanlış olabilir: Ters-kalibre Grade, yanlış "ders" öğretiyor olabilir (yüksek-conviction=güvenilir yanılgısını pekiştiriyor).
Kanıt: [EVIDENCE] conviction inversiyonu.
Nasıl test edilir: Grade'in kullanıcının risk-algısını nasıl kalibre ettiğini (veya bozduğunu) ölç.

Varsayım: Statik haftalık/günlük özet doğru format.
Neden yanlış olabilir: Spaced-repetition ve interleaving, statik tek-seferlik içerikten çok daha güçlü kalıcılık sağlar.
Kanıt: [INFERENCE] öğrenme-bilimi literatürü.
Nasıl test edilir: Statik Ledger vs spaced-repetition formatlı içerik arasında 30-gün retention kıyası.
```

### 3. Kaçırdığımız 10 şey
1. Aktif-hatırlama (retrieval practice) mekanizması hiç yok.
2. Kullanıcının finansal muhakeme-seviyesini zaman içinde ölçen bir değerlendirme hiç kurulmadı.
3. Spaced-repetition/interleaving hiç denenmedi.
4. Case-based öğrenme (geçmiş NO-GO kararlarını vaka olarak sunmak) hiç kullanılmadı — oysa elimizde mükemmel malzeme var (bu araştırma programının kendisi).
5. Deliberate-practice döngüsü (kullanıcı tahmin yapar → sonucu görür → geri bildirim alır) hiç kurulmadı.
6. Segment-bazlı öğrenme yolu (acemi/orta/ileri) yok.
7. "Skill tree" / ilerleme yapısı hiç düşünülmedi.
8. Öğrenme-kazanımını ölçen hiçbir metrik yok (yalnız engagement ölçülüyor).
9. Kullanıcının kendi geçmiş kararlarını gözden geçirmesi (reflection loop) hiç yok.
10. Eğitim içeriği ile araştırma-bulguları (bu konuşmanın ürettiği türden) arasında hiç köprü yok — en zengin içerik kaynağı kullanılmıyor.

### 4. 10 yeni deney (özet)
Retrieval-quiz'li Ledger vs statik Ledger 30-gün retention kıyası · case-based modül: geçmiş NO-GO kararlarını vaka-çalışması yap · deliberate-practice döngüsü (kullanıcı tahmin→sonuç→geri bildirim) pilotu · segment-bazlı içerik A/B · skill-tree ilerleme prototipi · spaced-repetition bildirim zamanlaması testi · kullanıcı muhakeme-seviyesi başlangıç/bitiş testi · interleaving (karışık konu) vs bloklu-konu sunumu kıyası · Grade'in risk-algısına etkisini ölçen anket · araştırma-bulgularının (bu program) eğitim-içeriğine dönüştürülmesi pilotu.

### 5-8. Bırak/Değiştir/Ekle
**Bırak:** yalnız açılma/okuma-oranı ölçmek · **Tamamen bırak:** pasif-tüketim tek format · **Değiştir:** Ledger → aktif-hatırlama + spaced-repetition formatı · **Ekle:** case-based modül (gerçek NO-GO kararları), deliberate-practice döngüsü, muhakeme-seviyesi ölçümü.

### 9. Radikal fikirler
1. `[RADICAL]` FinPilot'un gerçek moat'ı prediction değil, **financial reasoning skill development** — ürün buna göre yeniden kurulur.
2. `[HYPOTHESIS]` Kullanıcının finansal düşünme seviyesini zaman içinde ölçen bir "reasoning score" (Grade'in yerine) — kişinin kendi kalibrasyonunu, hem piyasanınkini değil.
3. `[RADICAL]` Bu araştırma programının kendisi (dürüst NO-GO'lar, çürütülen hipotezler) doğrudan eğitim müfredatı olur — "biz nasıl yanıldık" en güçlü ders materyali.

### 10. "Sıfırdan kursaydım"
1. Format: statik özet değil, aktif-hatırlama + spaced-repetition.
2. Müfredat: gerçek araştırma vaka-çalışmaları (kendi NO-GO'larımız dahil).
3. Metrik: engagement değil, 30/60/90-gün retention + muhakeme-testi.
4. Grade yerine kullanıcının kendi kalibrasyon-eğrisi.

---

## PERSPEKTİF 8 — FORECASTING SCIENTIST / SUPERFORECASTER

### 1. Teşhis
Grade (A/B/C), olasılıksal tahmin biliminin temel ilkesini (kalibrasyon) ihlal ediyor: kategorik bir etiket, sürekli bir belirsizliği gizliyor ve **kanıtlanmış biçimde yanlış yönde** kalibre (`[EVIDENCE]` A<C). Superforecasting literatüründeki temel bulgu — iyi tahminciler kalibrasyonlarını sürekli ölçüp düzeltir, kategorik güven-etiketi kullanmaz — burada tam tersi yapılıyor: kalibrasyon hiç ölçülmüyor, kategorik etiket öne çıkarılıyor.

### 2. En büyük 5 yanlış varsayım
```
Varsayım: Grade (A/B/C) kullanıcıya yeterli bilgi verir.
Neden yanlış olabilir: Kategorik etiket, belirsizliği gizler ve yanlış kalibre olduğunda fark edilmesi zorlaşır.
Kanıt: [EVIDENCE] Brier train 0.236/test 0.248, quintile'lar monoton değil.
Nasıl test edilir: Grade yerine olasılık+CI gösterip kullanıcı-hata-oranını kıyasla.

Varsayım: Prediction accuracy en önemli metrik.
Neden yanlış olabilir: Kalibrasyon (Brier/ECE), accuracy'den daha temel — "%70 dedik, %70 mi çıktı" sorusu hiç sorulmuyor.
Kanıt: [EVIDENCE] kalibrasyon zaten ölçüldü ve başarısız (Brier kötüleşiyor test'te).
Nasıl test edilir: Zaten ölçüldü; sıradaki adım kalibrasyonu düzeltmek veya "kalibre değil" etiketiyle göstermek.

Varsayım: Tek bir composite skor yeterli.
Neden yanlış olabilir: Superforecasting pratiği, tek sayı yerine referans-sınıf + koşullu-olasılık + belirsizlik-aralığı kullanır.
Kanıt: [INFERENCE] literatür + FinPilot'un kendi redundancy kanıtı.
Nasıl test edilir: Tek skor yerine "referans sınıf oranı + bu vakaya özgü sapma" formatını dene.

Varsayım: Base-rate'ler zaten skora gömülü.
Neden yanlış olabilir: Hiçbir raporda açık base-rate (bu tür kurulumun tarihsel olarak ne sıklıkla kazandığı, kalibre biçimde) gösterilmiyor.
Kanıt: [INFERENCE] mevcut raporlarda base-rate referansı yok.
Nasıl test edilir: Her öneriye "bu tür kurulum tarihsel olarak %X zamanında pozitif sonuçlandı" ekle, gerçekleşenle kıyasla.

Varsayım: Yüksek conviction = düşük belirsizlik.
Neden yanlış olabilir: Kanıtlanmış tersi — yüksek conviction en düşük win-rate.
Kanıt: [EVIDENCE] conviction inversiyonu.
Nasıl test edilir: Zaten kanıtlandı; sıradaki adım conviction'ı belirsizlik-aralığıyla değiştirmek.
```

### 3. Kaçırdığımız 10 şey
1. Hiçbir tahmine kalibrasyon-geçmişi (reliability diagram) eşlik etmiyor.
2. Base-rate/referans-sınıf hiçbir yerde açık gösterilmiyor.
3. Belirsizlik-aralığı (confidence interval) hiç kullanıcıya taşınmadı.
4. Brier/log-loss izleme sistematik/sürekli değil, tek seferlik test.
5. "Bu tahmin yanlış çıkarsa şaşırır mıyız" sorusu hiç sorulmuyor (kalibrasyon-farkındalığı).
6. Koşullu olasılık (rejim/sektöre göre) hiç ayrı gösterilmiyor — tek sayı her koşulu ortalıyor.
7. Forecasting-tournament formatı (birden fazla iç-model/perspektifin tahminini karşılaştırma) hiç kurulmadı.
8. Kullanıcının kendi tahminiyle sistem-tahminini kıyaslayan bir mekanizma yok.
9. Aşırı-kesinlik (overconfidence) sistematik olarak ölçülmüyor.
10. Zaman içinde kalibrasyonun bozulup bozulmadığı (drift) izlenmiyor.

### 4. 10 yeni deney (özet)
Reliability-diagram'ı kullanıcıya göster, güven algısını ölç · base-rate ekleme A/B testi · CI-gösterimi vs tek-sayı gösterimi kıyası · sürekli Brier/ECE izleme paneli kur · rejim/sektöre koşullu olasılık ayrıştırması · forecasting-tournament: birden fazla iç yaklaşımın kalibrasyonunu kıyasla · kullanıcı-tahmini vs sistem-tahmini kıyas arayüzü · overconfidence ölçümü (kullanıcı %90 dediğinde gerçekleşme oranı) · kalibrasyon-drift izleme (aylık) · "şaşırdık mı" geri-bildirim döngüsü.

### 5-8. Bırak/Değiştir/Ekle
**Bırak:** kategorik Grade'i öne çıkarmak · **Tamamen bırak:** kalibre edilmemiş "conviction" dilini kullanmak · **Değiştir:** Grade → kalibre olasılık + CI + base-rate · **Ekle:** sürekli kalibrasyon izleme (Brier/ECE), reliability diagram, koşullu olasılık gösterimi.

### 9. Radikal fikirler
1. `[RADICAL]` Grade tamamen kaldırılıp yerine **"bu tür kurulumlar tarihsel olarak %X zamanında pozitif sonuçlandı (n=Y, son güncelleme Z)"** formatı gelsin — base-rate merkezli.
2. `[HYPOTHESIS]` Kullanıcıya kendi tahminini önce yaptırıp sonra sistem-tahminiyle kıyaslatan bir "kalibrasyon eğitimi" akışı.
3. `[RADICAL]` FinPilot'un başarı metriği prediction-accuracy değil, **kalibrasyon-skoru** (Brier/ECE, zaman içinde düşüyor mu) olsun — bu hem dürüst hem pazarlanabilir bir iddia.

### 10. "Sıfırdan kursaydım"
1. Her çıktı olasılık + CI + base-rate ile gelir, kategori değil.
2. Kalibrasyon sürekli izlenir ve halka açık raporlanır (Brier/ECE).
3. Koşullu olasılık (rejim/sektör) her zaman ayrı gösterilir.
4. Başarı metriği: kalibrasyon kalitesi, accuracy değil.

---

## PERSPEKTİF 9 — RED TEAM / COMPLIANCE / TRUST ARCHITECT

### 1. Teşhis
FinPilot'un en büyük güven-riski, tam da en güçlü göründüğü yerde gizli: **dürüst araştırma disiplini var, ama üretim yüzeyi (Grade, conviction, composite_score) bu disiplinin ürettiği kanıtla çelişiyor.** Yani sistem kendi içinde "Grade A/conviction yüksek = düşük performans" kanıtını üretmiş durumda `[EVIDENCE]`, ama bu kanıt üretim yüzeyine henüz yansımadı. Bu, klasik bir "biliyorduk ama düzeltmedik" güven-riskidir — en tehlikeli tür, çünkü savunulamaz.

### 2. En büyük 5 yanlış varsayım
```
Varsayım: Grade/composite_score kullanıcıyı yanıltmıyor çünkü "sadece bir araştırma etiketi."
Neden yanlış olabilir: Kullanıcı bunu üretim-kalite sinyali olarak okuyabilir; ters-kalibre olduğu bilinip düzeltilmezse bu ihmal, yalnızca hata değil.
Kanıt: [EVIDENCE] conviction inversiyonu BİLİNİYOR ve henüz üretimden kaldırılmadı/düzeltilmedi.
Nasıl test edilir: Hukuk/compliance gözüyle "bilinen-yanlış-kalibre metriği üretimde tutmak" riskini resmi değerlendir.

Varsayım: Geçmiş performans gösterimi zararsız bir bağlam bilgisi.
Neden yanlış olabilir: "Past performance is not indicative" uyarısı olsa bile, seçici (selection-biased) geçmiş performans gösterimi güven yanıltması sayılabilir.
Kanıt: [EVIDENCE] barrier-grid'de bazı config'ler outlier-driven yüksek ortalama gösteriyor.
Nasıl test edilir: Gösterilen her geçmiş-performans iddiasının selection-bias/outlier-duyarlılığını audit et.

Varsayım: AI-üretilen açıklamalar güven inşa eder.
Neden yanlış olabilir: Açıklama, altındaki skor yanlışsa "explainability theater" — inandırıcı ama yanlış.
Kanıt: [INFERENCE] composite_score açıklanabilir ama kalibre değil.
Nasıl test edilir: Açıklama-kalitesi ile skor-doğruluğu arasındaki bağımsızlığı ölç, ayrı raporla.

Varsayım: "Bu tavsiye değildir" uyarısı yeterli hukuki koruma.
Neden yanlış olabilir: Grade/conviction gibi güçlü kategorik diller, uyarı metnine rağmen implicit tavsiye gibi algılanabilir.
Kanıt: [INFERENCE] davranışsal-finans literatüründe anchoring uyarı-metnini geçersiz kılabilir.
Nasıl test edilir: Kullanıcı algı testi — uyarıya rağmen Grade'i tavsiye olarak okuyor mu.

Varsayım: NO-GO kararları yalnız iç governance meselesi, kullanıcıya yansıması gerekmiyor.
Neden yanlış olabilir: Kullanıcı hâlâ Grade/skoru görüyorsa, iç NO-GO kararı dış tutarsızlık yaratır.
Kanıt: [EVIDENCE] decision-log'da NO-GO var ama üretim yüzeyinde Grade hâlâ görünür biçimde kullanılıyor olabilir.
Nasıl test edilir: Üretim arayüzünü audit et — iç NO-GO kararı dış yüzeye tutarlı yansımış mı.
```

### 3. Kaçırdığımız 10 şey (20 attack vector'dan öncelikli 10)
1. **Bilinen-ters-kalibrasyonu düzeltmeden üretimde tutmak** — en kritik, çünkü kanıt zaten elimizde.
2. Outlier-driven geçmiş-performans sayılarının seçici gösterilmesi (cherry-picking görünümü).
3. Explainability theater — inandırıcı ama yanlış açıklamalar.
4. Uyarı-metni ile kategorik-dil (Grade) arasındaki çelişki.
5. Survivorship-bias'ın hiç açıkça belgelenmemiş/kullanıcıya iletilmemiş olması.
6. AI-hallucination riski (haber/sentiment özetlerinde) hiç sistematik test edilmedi.
7. Kaynak-kalitesi (news/sentiment feed'lerin güvenilirliği) hiç audit edilmedi.
8. "False precision" — %94.7 gibi ondalıklı sayıların, altındaki büyük belirsizliği gizlemesi.
9. Conflict-of-interest netliği (FinPilot'un kendi menfaati ile kullanıcı menfaati net ayrılmış mı) hiç dokümante değil.
10. Rakip saldırı senaryosu (bir rakip FinPilot'u kötü göstermek istese) hiç resmi tatbikat olarak yapılmadı.

### 4. 10 yeni deney / audit (özet)
Grade'in mevcut üretim-görünürlüğünü audit et (nerede, nasıl gösteriliyor) · outlier-driven performans iddialarının listesini çıkar, her birine uyarı ekle · explainability-theater testi (açıklama-kalitesi vs skor-doğruluğu bağımsızlığı) · uyarı-metni etkinliği kullanıcı testi · survivorship-bias açıklamasını dokümante et ve kullanıcıya ilet · AI-hallucination oranını haber-özeti örnekleminde ölç · kaynak-güvenilirlik audit'i · false-precision taraması (gereksiz ondalık basamaklar) · conflict-of-interest dokümantasyonu · resmi red-team tatbikatı (dışarıdan biri gibi saldır).

### 5-8. Bırak/Değiştir/Ekle
**Bırak:** ondalıklı "kesin" görünen sayılar (false precision) · **Tamamen bırak:** bilinen-ters-kalibre Grade'i üretimde göstermek · **Değiştir:** Grade → kalibre olasılık + belirsizlik + "kalibre değil" etiketi (düzeltilene kadar) · **Ekle:** her performans-iddiasına selection-bias/outlier uyarısı, resmi red-team tatbikatı takvimi.

### 9. Radikal fikirler
1. `[RADICAL]` Bilinen ters-kalibrasyon düzeltilene kadar Grade tamamen **üretimden kaldırılmalı** — bu bir "nice to have" değil, bilinen-yanlışı-göstermeye-devam-etme riski.
2. `[HYPOTHESIS]` Her öneriye otomatik "bu iddia şu kanıt-seviyesine dayanıyor: EVIDENCE/INFERENCE/HYPOTHESIS" etiketi eklensin (bu belgede kullanılan standart, kullanıcı yüzeyine taşınsın).
3. `[RADICAL]` Şeffaflığı ürünleştir: "bugün neyi bilmiyoruz" bölümü her rapora zorunlu — güven riskini güven-inşasına çevirir.

### 10. "Sıfırdan kursaydım"
1. Hiçbir metrik kalibrasyonu doğrulanmadan üretim yüzeyine çıkmaz.
2. Her performans-iddiası otomatik selection-bias/outlier uyarısıyla gelir.
3. Kanıt-seviyesi etiketleme (EVIDENCE/INFERENCE/HYPOTHESIS) kullanıcı arayüzünün parçası.
4. Düzenli, resmi red-team tatbikatı takvime bağlı.

---

## PERSPEKTİF 10 — RADICAL FUTURIST / SYSTEMS THINKER

### 1. Teşhis
2030'da finansal piyasaları anlama biçimi muhtemelen "tek bir tahmin motoruna sor" değil, **çoklu-ajan muhakeme + kişisel hafıza + senaryo simülasyonu** olacak `[HYPOTHESIS]`. FinPilot bugün bunun tam tersi bir noktada: tek bir composite skora indirgenmiş, hafızasız (her tarama bağımsız), senaryo üretmeyen bir sistem. Oysa bu konuşmanın kendisi — çoklu perspektif, çapraz-sorgulama, kanıt-seviyesi etiketleme, disagreement-map — FinPilot'un **gelecekteki ürününün canlı bir prototipi** olabilir `[INFERENCE]`.

### 2. En büyük 5 yanlış varsayım
```
Varsayım: FinPilot bir scanner/tahmin-motoru olmalı.
Neden yanlış olabilir: Tahminde kanıtlı başarısız; ama "araştırma organizasyonu" olarak çok daha güçlü bir varlığı var (bu program).
Kanıt: [EVIDENCE] IC~0 + [INFERENCE] araştırma-disiplininin kalitesi.
Nasıl test edilir: Küçük bir kullanıcı grubuna "AI research organization" çerçevesinde sun, tepkiyi ölç.

Varsayım: Tek bir model/skor yeterli.
Neden yanlış olabilir: Bu konuşmada (10 perspektif) tek modelin kaçırdığı onlarca şey ortaya çıktı — çoklu-ajan yaklaşımı yapısal olarak daha zengin.
Kanıt: [INFERENCE] bu belgenin kendisi kanıt.
Nasıl test edilir: Bull/Bear/Skeptic/Historian ajanlarını gerçek sinyaller üzerinde çalıştırıp anlaşmazlık-oranını ölç.

Varsayım: Kullanıcıya hisse/sinyal vermek doğru çıktı biçimi.
Neden yanlış olabilir: "Bu konuda neyi henüz bilmiyoruz" sorusu, kanıtsız bir sinyalden çok daha dürüst ve muhtemelen daha değerli.
Kanıt: [INFERENCE] tüm araştırma programının ürettiği en tutarlı şey "bilmiyoruz" cevapları.
Nasıl test edilir: "Bilmiyoruz" formatını küçük kullanıcı grubuna sun, güven/memnuniyet etkisini ölç.

Varsayım: Piyasayı tahmin etmek asıl değer.
Neden yanlış olabilir: Senaryo-simülasyonu ("bu koşullarda ne olabilir, ne olamaz") tahminden daha dürüst ve daha az yanıltıcı olabilir.
Kanıt: [HYPOTHESIS] test edilmedi.
Nasıl test edilir: Senaryo-motoru prototipini tahmin-motoruyla kullanıcı-güveni açısından kıyasla.

Varsayım: FinPilot'un hafızası yok/gerekmiyor (her tarama bağımsız).
Neden yanlış olabilir: Kişisel/kolektif piyasa hafızası (geçmişte benzer kurulumlar ne oldu, biz ne öğrendik) muazzam bir farklılaştırıcı olabilir.
Kanıt: [INFERENCE] mevcut mimaride hafıza yok; bu konuşmanın memory-sistemi bile FinPilot'un kendisinden daha "hafızalı."
Nasıl test edilir: "Market Memory" prototipini (geçmiş vakalar + öğrenilenler) küçük ölçekte kur, kullanım-değerini ölç.
```

### 3. Kaçırdığımız 10 şey
1. Çoklu-ajan (bull/bear/skeptic/historian) mimarisi hiç denenmedi.
2. "Neyi bilmiyoruz" formatı hiç birincil çıktı yapılmadı.
3. Kişisel/kolektif piyasa hafızası (market memory) hiç kurulmadı.
4. Senaryo-simülasyonu (tahmin yerine) hiç denenmedi.
5. Kullanıcının kendi geçmiş kararlarıyla etkileşimli bir "personal reasoning gym" hiç düşünülmedi.
6. Adversarial-analyst (bir ajanın diğerini çürütmeye çalışması) hiç kurulmadı.
7. Knowledge-graph/causal-graph (neden-sonuç ilişkilerini açık modelleme) hiç kullanılmadı.
8. Digital-twin / sentetik-piyasa simülasyonu hiç denenmedi.
9. Kolektif zekâ (birden fazla kullanıcının tahminlerini birleştirme) hiç düşünülmedi.
10. "AI analyst değil, AI analyst team" çerçevesi hiç prototiplenmedi.

### 4. 10 yeni deney (özet)
Bull/Bear/Skeptic/Historian ajan-dörtlüsünü gerçek sinyaller üzerinde çalıştır, anlaşmazlık-oranını ölç · "neyi bilmiyoruz" kartını mevcut Grade yerine küçük grupta test et · market-memory prototipi: geçmiş benzer kurulumlar + sonuç + ders · senaryo-motoru: "bu 3 senaryo olası, hangisi gerçekleşirse ne olur" formatı · personal-reasoning-gym: kullanıcı kendi tahminini yapar, sistemle kıyaslar · adversarial-analyst: bir ajan diğerinin tezini çürütmeye çalışır · causal-graph prototipi (küçük ölçek, örn. sektör-market ilişkisi) · sentetik-piyasa (Monte Carlo) ile "bu strateji hangi rejimde patlar" testi · kolektif-tahmin (crowd) pilotu · "AI analyst team" arayüz prototipi (tek chat yerine panel).

### 5-8. Bırak/Değiştir/Ekle
**Bırak:** tek-model/tek-skor mimarisi · **Tamamen bırak:** "her tarama bağımsız, hafızasız" varsayımı · **Değiştir:** tahmin-üretimi → senaryo-üretimi + "bilmiyoruz" dürüstlüğü · **Ekle:** çoklu-ajan mimari, market-memory, personal-reasoning-gym.

### 9. Radikal fikirler (en az 10, gerçekçilik filtrelenmeden)
1. `[RADICAL]` FinPilot bir scanner değil, **AI Research Organization** olsun.
2. `[RADICAL]` Tek model yerine **Bull AI vs Bear AI vs Skeptic AI vs Historian AI** — anlaşmazlık kullanıcıya gösterilir.
3. `[RADICAL]` "Bu hisseyi al" yerine **"Bu konuda neyi henüz bilmiyoruz"** birincil çıktı.
4. `[RADICAL]` FinPilot bir **Market Memory / Market Wikipedia** olsun — kolektif, biriken, kaynak-gösterir bilgi.
5. `[RADICAL]` **Personal Financial Reasoning Gym** — kullanıcı pratik yapar, sistem geri bildirim verir.
6. `[HYPOTHESIS]` Piyasayı tahmin etmek yerine **senaryo simülasyonu** (Monte Carlo + koşullu dallanma) sunar.
7. `[RADICAL]` **AI investment analyst değil, AI analyst team** — panel, tek ses değil.
8. `[HYPOTHESIS]` Knowledge-graph ile "bu olay neden bu sonucu doğurdu" nedensel iz sürülebilir hale gelir.
9. `[RADICAL]` Kullanıcının kendi tahmin-geçmişi bir "kişisel kalibrasyon hafızası" oluşturur — sistemin değil, kullanıcının kalibrasyonu ölçülür.
10. `[HYPOTHESIS]` Sentetik/dijital-ikiz piyasa ortamında stratejiler "hangi rejimde patlar" diye stres-test edilir, gerçek para hiç riske girmeden.
11. `[RADICAL]` Rekabet, "kim daha çok kazandırır" değil "kim daha az yanıltır" ekseninde kurulur — dürüstlük moat'a dönüşür.

### 10. "Sıfırdan kursaydım"
1. Çekirdek: çoklu-ajan muhakeme, tek skor değil.
2. Çıktı: "ne biliyoruz / ne sanıyoruz / neyi bilmiyoruz" üçlüsü, her zaman.
3. Hafıza: her vaka (başarılı/başarısız) kalıcı, aranabilir, ders-çıkarılabilir.
4. Kullanıcı etkileşimi: pratik + geri bildirim döngüsü, pasif tüketim değil.
5. Rekabet avantajı: dürüstlük + kalibrasyon, tahmin-doğruluğu değil.

---

## 11. CROSS-EXAMINATION — 10 UZMAN BİRBİRİNİ SORGULUYOR

**Quant (P1):** "Doğru target risk/aralık olmalı." → **Behavioral (P3):** "Peki risk-odaklı bir arayüz kullanıcıyı korkutup pasifleştirmez mi? Risk-çerçeveleme de yanlış anlatılırsa yeni bir bias yaratır." → **Forecasting (P8):** "Risk'i de kalibre etmeden sunarsak aynı hataya (yanlış-güven) düşeriz — risk hedefi doğru ama sunumu kalibrasyonsuz olursa fark etmez."

**Product (P4):** "Tek özellik kalsaydı risk-kartı." → **Portfolio (P6):** "Tekil risk-kartı yanıltıcı olabilir — asıl değer portföy-seviyesi risk, tekil-pozisyon riski değil. Kullanıcı tekil-kart görüp portföy-varyansını unutabilir."

**ML (P5):** "AI prediction değil research-generation yapmalı." → **Red Team (P9):** "AI'ı hipotez-üreticisi yaparsak, üretilen her hipotez halka açık yüzeye sızma riski taşır — 'AI şunu buldu' cümlesi kullanıcı için otomatik-tavsiye gibi algılanabilir, hipotez olduğu unutulur."

**Futurist (P10):** "Çoklu-ajan (bull/bear/skeptic) mimarisi." → **Behavioral (P3):** "Çoklu-ajan anlaşmazlığı kullanıcıda 'kimseye güvenemem' yorgunluğu (choice overload) yaratabilir — tek Grade'den kaçarken yeni bir bilişsel yük eklenebilir."

**Educator (P7):** "Gerçek moat öğrenme." → **Product (P4):** "Eğitim-merkezli konumlanma, mevcut kullanıcı tabanının (sinyal bekleyen) beklentisiyle çelişebilir — kategori değişimi churn riski taşır."

**Microstructure (P2):** "Event-time'a geç." → **Quant (P1):** "Event-time gerektirdiği intraday veri, mevcut altyapıda yok — bu öneri kısa vadede test edilemez, önce günlük-veri-ile-yapılabilecekler tükenmeli."

**Red Team (P9):** "Grade'i hemen kaldır." → **Product (P4):** "Grade'i aniden kaldırmak kullanıcı-güvenini de kırabilir ('neden değişti') — geçiş kademeli olmalı, ama gecikme = bilinen-yanlışı-göstermeye-devam etmek. Bu gerçek bir gerilim, kolay çözülmüyor."

Bu itirazların hiçbiri "yanlış" değil — hepsi geçerli. Bu yüzden aşağıdaki disagreement map **kasıtlı olarak çözülmemiş** bırakılıyor.

## DISAGREEMENT MAP

| Konu | Quant (P1) | Behavioral (P3) | Product (P4) | Red Team (P9) | Futurist (P10) | Sonuç |
|---|---|---|---|---|---|---|
| **TP/SL** | Bırak, overfitting yüzeyi | İlgisiz | İlgisiz | İlgisiz | İlgisiz | Konsensüs: bırak (tek konu) |
| **Grade** | İlgisiz | Kaldır veya kalibre-olasılığa çevir | Kademeli geçiş, aniden kaldırma güven kırar | Hemen kaldır (bilinen-yanlış-kalibre) | Tamamen farklı format (ajan-anlaşmazlığı) | **ÇÖZÜLMEMİŞ** — hız/biçim konusunda gerçek gerilim |
| **Prediction target** | Risk/aralık, getiri değil | Risk de kalibre sunulmalı | İlgisiz | İlgisiz | Tahmin yerine senaryo | Kısmi konsensüs: getiri-merkezlilik terk edilsin, ama neyle değişeceği açık değil |
| **Ranking** | Rank/cross-sectional, mutlak değil | İlgisiz | Entry-quality'den ayrılsın | İlgisiz | Tek skor yerine ajan-çoğulluğu | Kısmi konsensüs: tek-skor bırakılsın |
| **Regime** | Rejim-koşullu test şart | İlgisiz | İlgisiz | İlgisiz | "Rejim" kavramı da statik — event-time daha zengin olabilir | **ÇÖZÜLMEMİŞ** — rejim tanımının kendisi tartışmalı |
| **AI rolü** | İlgisiz | İlgisiz | İlgisiz | Hipotez-üretici AI'ın çıktısı tavsiye gibi algılanabilir | Çoklu-ajan, prediction değil | **ÇÖZÜLMEMİŞ** — AI'ın gücü ile risk'i aynı öneride |
| **Eğitim** | İlgisiz | Grade'in öğretici etkisi zararlı olabilir | Kategori-değişimi churn riski | İlgisiz | Reasoning-gym vizyonu | Kısmi konsensüs: değerli ama geçiş riskli |
| **Portfolio** | İlgisiz | İlgisiz | İlgisiz | İlgisiz | İlgisiz | (yalnız P6) Tekil risk-kartı vs portföy-riski geriliminde net |
| **Market Memory** | İlgisiz | İlgisiz | Kategori-fırsatı olarak ilginç | İlgisiz | Merkezi vizyon | Zayıf konsensüs — heyecan var ama hiç test edilmedi |
| **Product category** | İlgisiz | İlgisiz | Araştırma-laboratuvarı | Şeffaflığı ürünleştir | AI Research Organization | Güçlü konsensüs — üç bağımsız perspektif aynı yöne işaret ediyor |

**En değerli disagreement:** Grade'in kaderi. Kanıt "hemen kaldır" diyor (Red Team + Quant), ürün-gerçekliği "kademeli, dikkatli" diyor (Product), gelecek-vizyonu "kaldırma, dönüştür" diyor (Futurist). Bu üçü aynı anda doğru olabilir — çözüm muhtemelen **sıralama** meselesi (önce iç düzeltme, sonra dış format değişimi), tek adımlı karar değil.

---

## 12. SECOND-ORDER THINKING — KİLİT ÖNERİLER

### Öneri: Grade tamamen kaldırılsın
Birinci etki: kullanıcı tek-bakışta karar veremez, açıklamayı okumak zorunda kalır. → İkinci etki: bazı kullanıcılar bunu "ürün zayıfladı" diye okur, bazıları "daha dürüst" diye okur — segment-bağımlı. → Üçüncü etki: destek/onboarding yükü artar (yeni format öğretilmeli). → Yan etki: rakip ürünler hâlâ basit Grade sunuyorsa, karşılaştırmalı pazarlamada FinPilot "daha az kesin" görünebilir. → Adversarial kullanım: bir rakip "FinPilot artık size ne alacağınızı söylemiyor" diye konumlandırabilir. → Yeni fırsat: bu tam da doğru konumlandırma — "biz size ne alacağınızı söylemeyiz, ne bilmediğimizi söyleriz" farklılaştırıcı mesaj olur.

### Öneri: AI, prediction yerine research-generation yapsın
Birinci etki: kullanıcı doğrudan "al/sat" sinyali yerine "şu hipotez test edildi, şu sonuç çıktı" görür. → İkinci etki: bazı kullanıcılar (hızlı-karar isteyenler) bunu yavaş/gereksiz bulur, ayrılabilir. → Üçüncü etki: kalan kullanıcı-tabanı daha sofistike/sadık hale gelir (self-selection). → Yan etki: içerik-üretim maliyeti artar (her hipotez insan-gözden-geçirmesi ister, otomatikleştirilemez tamamen). → Adversarial kullanım: kötü niyetli biri AI'ın ürettiği ham hipotezleri "FinPilot şunu söyledi" diye çarpıtabilir — hipotez/sonuç ayrımı net etiketlenmezse. → Yeni fırsat: "AI'ın çürüttüğü hipotezler" arşivi başlı başına güven-inşa eden bir içerik varlığı olur.

### Öneri: Portföy-inşası tekil-sinyal aramasının önüne geçsin
Birinci etki: kullanıcı "en iyi hisse" değil "dengeli sepet" görür — bazıları bunu daha az heyecanlı bulur. → İkinci etki: risk-azaltma somut olarak ölçülebilir hale gelir (drawdown, concentration), pazarlanabilir bir iddia olur. → Üçüncü etki: ürün "trading sinyali" kategorisinden "portföy-yönetim aracı" kategorisine kayar — düzenleyici/compliance çerçevesi değişebilir. → Yan etki: geliştirme karmaşıklığı artar (tekil-sinyal göstermek, portföy-optimizasyonundan çok daha basit bir UI). → Adversarial kullanım: yok denecek kadar az — bu öneri düşük-risk yüksek-fayda. → Yeni fırsat: risk-yönetim aracı olarak B2B/kurumsal kanal açılabilir.

### Öneri: Sektör-trend bulgusu gerçek etiketle doğrulanır ve doğrulanırsa üretime alınır
Birinci etki: eğer doğrulanırsa, programın **ilk gerçek koşullu-edge adayı** olur — moral ve stratejik açıdan büyük. → İkinci etki: tek bir bulguya aşırı-güven riski (yine küçük-n, tek-mekanizma) — tekrar test edilmeden abartılmamalı. → Üçüncü etki: doğrulanırsa bile, gerçek sektör verisi (EODHD fundamentals gibi) sürekli-güncel-tutma operasyonel yükü getirir. → Yan etki: doğrulanmazsa (muhtemel), "aradığımız her şey null çıktı" moral yorgunluğu birikir. → Adversarial kullanım: erken "sektör-edge bulduk" duyurusu, sonra çürürse güven kaybı. → Yeni fırsat: doğrulanmasa bile, bu süreç (nasıl test ettik, neden inanmadık) eğitim-içeriğine dönüşür.

---

## 13. RADICAL REBUILD EXERCISE

**"%90'ı çöpe atsan geriye ne bırakırdın?"** → İmmutable telemetry/audit disiplini (PIT, dedup, null-kontrolleri, honest-metric ayrımı) + ATR→MAE risk-bulgusu + price_cache/data pipeline. Score/Grade/TP-SL/entry_ok mantığının tamamı gidebilir.

**"Trading ürünü olmasına izin verilmese?"** → Bir **piyasa-okuryazarlığı + karar-günlüğü** platformu olurdu: kullanıcı kendi tahminini kaydeder, sistem yalnız kalibrasyon geri bildirimi verir, hiç "al/sat" önermez.

**"Eğitim ürünü olmasına izin verilmese?"** → Bir **saf risk-telemetri servisi** olurdu: "bu isim şu an ne kadar oynak, tarihsel aralığı ne" — B2B/API olarak diğer uygulamalara gömülür.

**"Hisse seçmesine izin verilmese?"** → Bir **piyasa-durumu sınıflandırıcısı** olurdu: "bugün piyasa/sektör hangi rejimde, bu rejimde tarihsel olarak ne tür stratejiler mantıklıydı" — hisse-özel değil, bağlam-özel.

**"Yalnız bir şey yapabilseydi?"** → Kalibre risk/belirsizlik tahmini. Tek kanıtlanmış, tek savunulabilir, tek rejim-dayanıklı yetenek.

**"Hiçbir mevcut kategoriye girmesine izin verilmese?"** → **"Piyasa Kalibrasyon Laboratuvarı"** — ne sinyal-servisi, ne eğitim-platformu, ne research-terminal; kullanıcının kendi tahmin-kalitesini ölçüp geliştiren, piyasa hakkında değil kullanıcının piyasa-hakkındaki-düşüncesi hakkında bir ürün.

---

## 14. 20 ALTERNATİF ÜRÜN EVRENİ (özet kartlar)

```
1. Market Reasoning Platform — Hedef: aktif yatırımcı — Söz: "neden düşündüğünü gör" — Moat: araştırma-disiplini — Risk: yavaş büyüme
2. AI Research Organization — Hedef: sofistike kullanıcı/kurum — Söz: "şeffaf, çürütülebilir araştırma" — Moat: immutable audit trail — Risk: B2C'de az heyecan
3. Market Memory / Wikipedia — Hedef: herkes — Söz: "geçmişte ne oldu, ne öğrendik" — Moat: biriken veri — Risk: içerik-üretim yükü
4. Financial Reasoning Gym — Hedef: öğrenmek isteyen — Söz: "kendi kalibrasyonunu ölç" — Moat: deliberate-practice döngüsü — Risk: uzun kullanıcı-kazanım süresi
5. Open Research Ledger — Hedef: meraklı/akademik — Söz: "her hipotez, her sonuç açık" — Moat: dürüstlük markası — Risk: parasallaştırma zor
6. Personal Market Copilot — Hedef: aktif trader — Söz: "senin kararına eşlik eder" — Moat: kişiselleştirme — Risk: prediction beklentisi geri döner
7. Research Experiment Laboratory — Hedef: quant-meraklı — Söz: "kendi hipotezini test et" — Moat: altyapı — Risk: niş kitle
8. Market Scenario Engine — Hedef: risk-yönetimi arayan — Söz: "ne olabilir, ne olamaz" — Moat: simülasyon kalitesi — Risk: hesaplama maliyeti
9. AI Analyst Debate Platform — Hedef: karar-vermek isteyen — Söz: "bull/bear/skeptic aynı anda" — Moat: çoklu-ajan mimari — Risk: choice-overload
10. Financial Learning OS — Hedef: yeni başlayan — Söz: "adım adım finansal muhakeme" — Moat: müfredat — Risk: rekabet (Khan Academy vb.)
11. Risk Telemetry API — Hedef: geliştirici/diğer fintech'ler — Söz: "gerçek zamanlı risk skoru" — Moat: ATR-MAE bulgusu — Risk: B2B satış döngüsü uzun
12. Decision Journal for Investors — Hedef: aktif yatırımcı — Söz: "kararlarını takip et, öğren" — Moat: davranışsal geri-bildirim — Risk: alışkanlık oluşturma zor
13. Calibration Score Platform — Hedef: forecasting-meraklısı — Söz: "ne kadar iyi tahmin ediyorsun" — Moat: Brier/ECE altyapısı — Risk: dar niş
14. Sector Rotation Radar — Hedef: orta-vadeli yatırımcı — Söz: "hangi sektör güçleniyor" — Moat: sektör-trend bulgusu (doğrulanırsa) — Risk: kanıt henüz zayıf
15. Portfolio Concentration Guard — Hedef: kendi-kendine yöneten yatırımcı — Söz: "portföyün ne kadar riskli kümelenmiş" — Moat: concentration-analitiği — Risk: rakipler zaten var (brokerlar)
16. Honest Backtest-as-a-Service — Hedef: strateji geliştiren quant'lar — Söz: "overfitting'i biz yakalarız" — Moat: null-kontrol disiplini — Risk: teknik kitle küçük
17. Market Digital Twin — Hedef: ileri-düzey araştırmacı — Söz: "stratejini sentetik piyasada test et" — Moat: simülasyon — Risk: geliştirme maliyeti yüksek
18. Explainable Risk Companion — Hedef: risk-kaçınan yatırımcı — Söz: "ne kadar kaybedebilirim, net" — Moat: MAE-tahmini — Risk: "heyecansız" algısı
19. Collective Forecast Network — Hedef: topluluk-odaklı kullanıcı — Söz: "kalabalığın kalibre tahmini" — Moat: ağ-etkisi — Risk: soğuk-başlangıç problemi
20. Financial Skepticism Coach — Hedef: aşırı-güvenli yeni yatırımcı — Söz: "seni yavaşlatır, düşündürür" — Moat: davranışsal-müdahale tasarımı — Risk: kullanıcı bunu istemeyebilir
```

---

## 15. 5 META-UZMAN KONSENSÜSÜ

**Meta A — Quant Consensus:** Ortak görüş: getiri-hedefi tükendi, risk-hedefi geçerli, tek-skor bırakılmalı, giriş-zamanlaması hiç ölçülmedi, market-nötr birincil olmalı. Büyük anlaşmazlık: sektör-bulgusuna ne kadar güvenilmeli (kanıt zayıf-ama-umutlu). Kritik belirsizlik: koşullu-edge (rejim×sektör) gerçek mi, artefakt mı. Öneri: reframing-deneyini (giriş-noktası + drift-eğrisi + market-nötr) hemen koş, yeni TP/SL arama.

**Meta B — Product Consensus:** Ortak görüş: mevcut kategori (scanner) kanıtla çelişiyor, araştırma-disiplini gerçek varlık, tek-özellik-kalsaydı risk-kartı olurdu. Büyük anlaşmazlık: eğitim mi B2B-araştırma-aracı mı asıl yön. Kritik belirsizlik: kullanıcı gerçekte ne istiyor (hiç doğrudan sorulmadı). Öneri: kategori-değişimini kademeli test et, küçük kullanıcı grubunda.

**Meta C — User Consensus:** Ortak görüş: kullanıcı muhtemelen "kesin cevap" değil "güvenilir çerçeve" istiyor ama bu hiç doğrulanmadı. Büyük anlaşmazlık: acemi mi deneyimli mi asıl hedef kitle. Kritik belirsizlik: Grade'in kaldırılması churn mü yaratır güven mi inşa eder. Öneri: segment-bazlı pilot, tek-tip değişiklik yapmadan.

**Meta D — Trust Consensus:** Ortak görüş: bilinen-ters-kalibrasyonu üretimde tutmak en acil risk; şeffaflık (NO-GO'lar, kanıt-seviyeleri) en büyük fark yaratıcı. Büyük anlaşmazlık: Grade'i hemen mi kademeli mi kaldırmalı. Kritik belirsizlik: uyarı-metinlerinin gerçekten işe yarayıp yaramadığı hiç test edilmedi. Öneri: önce iç düzeltme (kalibrasyon), sonra dış format değişimi — sıralı, eş-zamanlı değil.

**Meta E — Future Consensus:** Ortak görüş: tek-model/tek-skor mimarisi 2030 vizyonuyla uyumsuz; çoklu-ajan + hafıza + dürüstlük yönü güçlü. Büyük anlaşmazlık: bu vizyona ne kadar hızlı gidilmeli — bugünkü kanıt-tabanı (küçük n, henüz doğrulanmamış bulgular) böylesine büyük bir yeniden-inşayı bugün destekler mi. Kritik belirsizlik: kullanıcı çoklu-ajan-anlaşmazlığını değerli mi bulacak yoksa kafa karıştırıcı mı. Öneri: vizyonu küçük prototiple (Bull/Bear/Skeptic 3-ajan) test et, büyük mimari kararı vermeden.

---

## 16. FINAL SYNTHESIS

### SECTION A — Bugün Yanlış Düşünüyor Olabileceğimiz 20 Şey
1. Hedef fonksiyonu getiri, oysa kanıtlanan şey risk `[EVIDENCE]`.
2. Tek composite skor, oysa ~2-3 bağımsız eksene iniyor `[EVIDENCE]`.
3. "Daha fazla confirmation = daha kaliteli" — muhtemelen aynı bilgiyi tekrar ölçüyor `[INFERENCE]`.
4. Grade kullanıcıya yardımcı — kanıtlı ters `[EVIDENCE]`.
5. entry_ok kaliteyi artırıyor — kanıtlı ters `[EVIDENCE]`.
6. 5 gün doğru ufuk — hiç test edilmedi, muhtemelen yanlış `[HYPOTHESIS]`.
7. Ertesi-açılış doğru giriş noktası — hiç test edilmedi `[HYPOTHESIS]`.
8. %0.55 sabit maliyet gerçekçi — evren-karakteriyle uyuşmuyor `[INFERENCE]`.
9. Aritmetik-ortalama doğru metrik — lottery evreninde yanıltıcı `[INFERENCE]`.
10. AI prediction yapmalı — prediction'da başarısız, research'te hiç denenmedi `[EVIDENCE]+[HYPOTHESIS]`.
11. Daha karmaşık model daha iyi — basit baseline zaten geçilemedi `[INFERENCE]`.
12. Kullanıcı hisse istiyor — hiç doğrudan sorulmadı `[HYPOTHESIS]`.
13. Morning Ledger nihai format — pasif-tüketim, kalıcılık ölçülmedi `[INFERENCE]`.
14. Eğitim yan-özellik — muhtemelen asıl moat `[INFERENCE]`.
15. Tekil-sinyal expectancy portföye taşınır — kanıtlı ters `[EVIDENCE]`.
16. Sektör-coverage yetersizliği "sektör-etkisi yok" demek — hayır, test-edilmemiş demek `[INFERENCE]`.
17. Locked OOS hâlâ temiz — muhtemelen kontamine `[INFERENCE]`.
18. Backtest sonucu = gerçek edge — sistematik olarak abartılı (outlier/selection) `[EVIDENCE]`.
19. "Bilmiyoruz" demek zayıflık — muhtemelen en güçlü farklılaştırıcı `[HYPOTHESIS]`.
20. Explainability = güven — açıklama yanlış-skoru inandırıcı kılabilir `[INFERENCE]`.

### SECTION B — Test Etmediğimiz En Önemli 20 Hipotez
1. Getiri yerine risk-hedefiyle paralel scorecard.
2. 3 giriş-noktası ayrıştırması (close/open/close).
3. Bariyersiz drift/half-life eğrisi.
4. Extension/exhaustion → inversiyon mekanizması.
5. Market+sektör-nötr excess getiri birincil metrik.
6. Gerçek sektör etiketiyle tam-evren koşullu test.
7. entry_ok'un tersine çevrilmiş (fade) hali.
8. PCA ile gerçek bağımsız eksen sayısı.
9. Cluster-robust standart hatalarla mevcut "anlamlı" sonuçların yeniden testi.
10. Investable-universe (capacity-filtreli) alt kümede paralel sonuçlar.
11. Concentration-kısıtlı vs kısıtsız portföy Sharpe kıyası.
12. ATR-bazlı position-sizing'in portföy varyansına etkisi.
13. Grade açık/kapalı kullanıcı-karar-kalitesi A/B testi.
14. Kalibrasyon-eğrisi gösteriminin kullanıcı güvenine etkisi.
15. AI'ı hipotez-üretici rolüne koyup OOS-hayatta-kalma oranı.
16. Bull/Bear/Skeptic/Historian ajan-dörtlüsünün anlaşmazlık-oranı.
17. Case-based (gerçek NO-GO'lar) eğitim modülünün retention etkisi.
18. Forward-shadow'un (sealed) ilk temiz kanıtı.
19. Aynı-gün sinyallerin gerçekleşen korelasyon/kümelenmesi.
20. Kullanıcı motivasyon anketi — gerçekte ne satın alıyor.

### SECTION C — Artık Yapılmaması Gereken 10 Şey
1. Aynı feature ailesinde yeni TP/SL/threshold taraması.
2. Composite_score'u herhangi bir üretim kararında kullanmak.
3. Grade/conviction'ı bilerek-ters-kalibre halde göstermeye devam etmek.
4. Tekil-sinyal expectancy'yi portföy-kanıtı gibi sunmak.
5. Sabit %0.55 maliyeti "gerçekçi execution" diye ilan etmek.
6. Locked holdout'u tekrar tekrar "neredeyse açalım" diye gündeme getirmek.
7. P0'ı promotion-gate olarak tüm araştırmayı kilitleyen bir şart yapmak.
8. Aritmetik-ortalama'yı tek başına expectancy metriği olarak raporlamak.
9. AI-karmaşıklığını (DRL vb.) kanıtsız artırmak.
10. Aynı geçmiş veriye yeni bir "reframing" adı altında sınırsız yeni eksen eklemek (bkz. §1'deki overfitting uyarısı).

### SECTION D — Önümüzdeki 30 Gün İçin En Önemli 20 Deney
(Bkz. §0 kanıt tabanı + Perspektif 1 §4 + Perspektif 6 §4 — öncelik sırası: 1-2-3-4-5 hemen koşulabilir, günlük veriyle; 6-10 gerçek-sektör/investable-universe gerektirir; 11-20 orta-vadeli/altyapı ister.)
1. 3 giriş-noktası ayrıştırması · 2. Bariyersiz drift-eğrisi · 3. Extension/exhaustion mekanizma testi · 4. Market+sektör-nötr excess-return birincil rapor · 5. entry_ok fade-testi · 6. Gerçek sektör etiketiyle tam-evren sektör-trend testi · 7. Concentration-kısıtlı portföy simülasyonu · 8. ATR-bazlı sizing testi · 9. PCA/feature-redundancy analizi · 10. Cluster-robust yeniden-test · 11. Investable-universe paralel koşu · 12. Kalibrasyon-eğrisi kullanıcı-prototipi · 13. Grade kapalı küçük-grup pilotu · 14. AI hipotez-üretici mini-pilot · 15. Bull/Bear/Skeptic 3-ajan prototipi · 16. Case-based eğitim modülü taslağı · 17. Kullanıcı motivasyon anketi · 18. Forward-shadow immutable-log altyapısı · 19. Aynı-gün kümelenme analizi · 20. False-precision/selection-bias audit'i (tüm mevcut raporlarda).

### SECTION E — 5 Tamamen Farklı Gelecek Vizyonu
1. **Piyasa Kalibrasyon Laboratuvarı** — kullanıcının kendi tahmin-kalitesini ölçen/geliştiren araç.
2. **AI Research Organization** — şeffaf, çürütülebilir, biriken araştırma varlığı; sinyal değil kanıt satar.
3. **Risk Telemetry Altyapısı (B2B)** — ATR→MAE bulgusunu API olarak diğer fintech ürünlerine gömer.
4. **Financial Reasoning Gym** — deliberate-practice + geri-bildirim ile finansal muhakeme geliştiren eğitim ürünü.
5. **Çoklu-Ajan Piyasa Paneli** — Bull/Bear/Skeptic/Historian'ın anlaşmazlığını gösteren, tek-ses vermeyen karar-destek arayüzü.

### SECTION F — Best Possible FinPilot (sıfırdan kursaydık)
1. Çekirdek varlık: immutable, dürüst, audit-edilebilir araştırma disiplini (zaten var, korunmalı).
2. Birincil çıktı: kalibre risk/belirsizlik tahmini — getiri-tahmini değil.
3. İkincil çıktı: "ne biliyoruz / ne sanıyoruz / neyi bilmiyoruz" üçlüsü, her zaman görünür.
4. Skor mimarisi: tek composite yerine 2-3 bağımsız, ayrı-etiketli boyut (opportunity/risk/tradability).
5. Portföy-inşası, tekil-sinyal aramasından önce gelir; concentration/ATR-sizing baştan var.
6. AI'ın birincil rolü: hipotez üretmek/çürütmek, tahmin üretmek değil.
7. Eğitim: pasif-Ledger değil, aktif-hatırlama + case-based (kendi NO-GO'larımız) + kalibrasyon-geri-bildirimi.
8. Değerlendirme: sealed holdout + forward-shadow, tekrar-tekrar-bakılan geçmiş değil.
9. Güven mimarisi: her iddia kanıt-seviyesiyle etiketli (EVIDENCE/INFERENCE/HYPOTHESIS), kullanıcı yüzeyinde de.
10. Kategori: "sinyal servisi" değil "dürüst araştırma + kalibrasyon aracı" — pazarlama da buna göre.

### SECTION G — Önümüzdeki 6-12 Ayda 3 Büyük Bahis

**Bahis 1 — Risk/Kalibrasyon Pivotu:** Getiri-tahmininden risk/belirsizlik-tahminine resmi pivot.
Why: Tek kanıtlanmış, rejim-dayanıklı bulgu bu. Evidence: ATR→MAE IC −0.51. Unknowns: kullanıcı bunu "daha az heyecanlı" bulur mu. Test: küçük-grup pilotu, Grade yerine risk-kartı. Cost: orta (mevcut altyapı büyük ölçüde hazır). Risk: düşük (kanıta dayalı). Expected upside: yüksek — hem dürüst hem savunulabilir bir ürün temeli.

**Bahis 2 — Reframing Diagnostiği (Giriş-Zamanlaması + Drift + Market-Nötr):** Tek, pre-registered, günlük-veriyle-yapılabilir tanı-batch'i.
Why: Programın en büyük ölçülmemiş boşluğu. Evidence: hiçbir deney bunu ayrıştırmadı. Unknowns: sonuç yine null çıkabilir. Test: §0'da tanımlanan batch. Cost: düşük (yeni veri gerekmiyor). Risk: düşük. Expected upside: ya yeni bir aksiyon-alınabilir bulgu, ya da "neden edge yok" mekanizmasının kesin kapanışı — ikisi de değerli.

**Bahis 3 — Gerçek Sektör Etiketiyle Koşullu-Edge Doğrulaması:** Sektör-trend bulgusunu gerçek (proxy değil) etiketle tam evrende tekrar test etmek.
Why: Programın tek OOS-tutarlı koşullu-sinyal ipucu. Evidence: 143-sembolde güçlü, tam-evrende yalnız %24-doğru proxy'yle test edildi. Unknowns: gerçek etiketle de replike olur mu. Test: EODHD fundamentals'tan gerçek sektör çekimi + tam-evren tekrar-test. Cost: orta (veri tedariği + ağ gerektirir). Risk: orta (yine null çıkabilir). Expected upside: doğrulanırsa programın ilk gerçek koşullu-edge'i.

### SECTION H — THE ONE THING

> **FinPilot'un gerçekten kazanabileceği oyun şudur: piyasayı en doğru tahmin eden değil, kendi bilmediğini en dürüst söyleyen ve kullanıcının kalibrasyonunu gerçekten iyileştiren sistem olmak.**
