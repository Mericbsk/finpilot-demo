# FinPilot Strategic Thinking Lab v1.0 — Divergence / Collision / Convergence

Sürüm: 1.0 · Tarih: 2026-08-10 · Statü: Level A (araştırma/strateji, üretim değişikliği yok)
İlişkili belge: `2026-08-10-finpilot-10-perspektif-red-team-vizyon-arastirmasi.md` (bu belge onun devamı/farklı mekaniği — kanıt tabanı ortak, tekrar üretilmedi).

**Kanıt etiketleri (bu çalışmanın kendi şeması):** `FACT` (veriyle doğrudan destekli) · `EVIDENCE` (sınırlı ama gerçek kanıt) · `HYPOTHESIS` (test edilmesi gereken fikir) · `SPECULATION` (yaratıcı, kanıtsız) · `UNKNOWN` (mevcut bilgiyle cevaplanamaz).

---

## 0. ORTAK KANIT TABANI (özet — tam hâli önceki belgenin §0'ında)

`FACT`: composite_score IC ≈ −0.028, finpilot_score ≈ +0.034, monoton değil · entry_ok tüm maliyet senaryolarında negatif, validasyonda daha kötü (−1.13%) · entry_ok eligible (n=262) rejected'den (n=26.863) kötü · conviction_tier A(23%)<B(27%)<C(42%) win-rate — iki bağımsız inversiyon · ATR→gerçekleşen MAE IC ≈ −0.51, bull/bear'da aynı yön (tek rejim-dayanıklı bulgu, risk boyutu) · barrier-grid (2.520 config) ve fixed-target (3.120 config): 0 maliyet-pozitif+dönem-stabil konfigürasyon, locked holdout hiç açılmadı · portföy sim en iyi hâliyle başa-baş (CAGR 0.62%, Sharpe 0.23) · Brier train 0.236/test 0.248, kalibre değil · evren ~1.929 sembol, medyan ADV ~$1M, likidite-uygun %11.85, spread-kaynak %0 · örneklem ~%87 bull.

`EVIDENCE`: sektör-trend katmanı 143 gerçek-sektör sembolde güçlü+OOS-tutarlı (win 58% vs 44%), tam-evrende %24-doğru proxy ile replike olmadı (çürütülmedi, kanıtlanamadı).

`UNKNOWN`: giriş-noktası ayrıştırması (sinyal-close/ertesi-open/ertesi-close) hiç yapılmadı · bariyersiz drift/half-life eğrisi hiç çizilmedi · gerçek sektör kapsamı yalnız %8.31.

---

# AŞAMA 1 — DIVERGENCE

Not: Quant Researcher, Portfolio Manager, Behavioral Scientist, Product Strategist, AI/Agent Architect, Futurist personaları önceki belgede (P1, P6, P3, P4, P5, P10) zaten derinlemesine işlendi. Burada onları **tekrar üretmek yerine delta** veriyorum — bu promptun sorduğu, önceki belgenin sormadığı yeni açılar. Market Microstructure, Data Scientist, Risk Scientist ve Devil's Advocate bu promptta gerçekten farklı çerçeveli — onları tam-taze işliyorum.

---

## PERSONA 1 — QUANT RESEARCHER (delta)

Önceki belgeden farklı olarak burada özellikle **"reverse ranking neden çalışıyor olabilir"** ve **"score ile forward return arasındaki negatif ilişki bize ne söylüyor"** soruları öne çıkıyor — bunlar önceki turda "inversiyon" olarak adlandırıldı ama mekanizması hâlâ test edilmedi.

**1. Biggest Blind Spots (10):** (1) Reverse-ranking hiç canlı test edilmedi — yalnız gözlemlendi. (2) Score'un negatif IC'sinin *rejime göre* değişip değişmediği (bull'da negatif, bear'da pozitif olabilir) hiç kırılmadı. (3) Entry_ok'un "kaç confirmation" değil "hangi confirmation'ların çakıştığı" test edilmedi. (4) Signal decay (sinyal ne kadar süre "taze" kalıyor) hiç ölçülmedi. (5) Cross-sectional ranking (günlük kesit) vs time-series (mutlak eşik) hiç ayrı test edilmedi — ikisi karışık kullanılıyor. (6) Mean-reversion vs momentum rejiminin kendisi (piyasa hangi rejimde) hiç ayrı feature değil. (7) Relative-strength (sembolün kendi sektörüne göre) hiç birincil ranking değişkeni değil. (8) Volatilite-rejimi (yüksek/düşük ATR-rejimi) ile fiyat-rejimi (bull/bear) karıştırılıyor — ikisi farklı eksen. (9) Factor-combination'ların (RSI+MACD+volume) gerçekten **bağımsız** bilgi taşıyıp taşımadığı formal test edilmedi (yalnız korelasyon gözlemlendi). (10) "En iyi backtest" ile "gerçek edge" arasındaki farkın miktarı (ne kadar overfitting payı var) hiç sayısallaştırılmadı.

**2. Wrong Assumptions (10):** Yüksek skor = yüksek gelecek getiri `EVIDENCE ters` · TP/SL doğru abstraction `EVIDENCE zayıf` · Exit problemi entry probleminden ayrı `UNKNOWN` · Confirmation sayısı arttıkça kalite artar `EVIDENCE ters (score_3 score_2'den iyi değil)` · Composite skor kalibre bir olasılık gibi okunabilir `FACT hayır` · Ranking doğru hedefi (getiri) optimize ediyor `EVIDENCE hayır` · Daha fazla feature daha bilgilendirici `EVIDENCE hayır (redundancy 0.98 korelasyon)` · Skor zamanla stabil `UNKNOWN` · Sinyal oluştuğu an trade edilebilir `UNKNOWN` · Backtest ile production tutarlı `EVIDENCE hayır (P0 INSUFFICIENT_DATA)`.

**3. Optimizing Incorrectly (10):** TP/SL ince-ayarı (asıl sorun target-tanımı) · sabit-maliyet varsayımıyla "sonuç" ilan etmek · aritmetik-ortalama expectancy (kuyruk-esiri) · tek-composite-skor (2-3 eksene iniyor) · 5-gün horizon (half-life ölçülmeden) · locked-holdout'u tekrar-tekrar gündeme getirmek · entry_ok'u "filtre kalitesi" diye optimize etmek (ters kalibre) · P0'ı promotion-gate yapmak · aynı feature ailesinde yeni kombinasyon aramak · getiriyi birincil hedef tutmak (risk zaten kanıtlı).

**4. New Opportunities (10):** Reverse-ranking'i pre-registered biçimde fade-stratejisi olarak test etmek · risk-hedefli paralel scorecard · giriş-noktası ayrıştırması · drift/half-life eğrisi · market+sektör-nötr excess-return birincil metrik · gerçek sektör etiketiyle tam-evren testi · PCA ile bağımsız eksen sayısını bulmak · cluster-robust istatistikle mevcut "anlamlı" sonuçları yeniden sınamak · investable-universe alt kümesinde paralel test · tail-capture çerçevesi (mean-expectancy yerine).

**5. Radical Alternatives (5):** `HYPOTHESIS` FinPilot iki ayrı sayı üretsin: risk (kalibre) + kesitsel rank (getiri değil relative) · `SPECULATION` Skor tamamen kaldırılıp yalnız "bu tür kurulum tarihsel olarak %X zamanında pozitifti (n=Y)" formatı · `HYPOTHESIS` entry_ok tersine çevrilip fade-adayı olarak shadow'a alınır · `SPECULATION` FinPilot backtest'i durdurup yalnız forward-shadow ile kanıt biriktirir · `HYPOTHESIS` Ranking cross-sectional/market-nötr'e indirgenir, mutlak eşik tamamen terk edilir.

**6. Quant/Product Experiments (10):** bkz. §Quant War Room ve §Experiment Factory — burada tekrar edilmiyor.

**7. Unknown Unknowns (10):** Skor gerçekten kaç bağımsız bilgi biti taşıyor (entropi-bazlı ölçüm hiç yapılmadı) · Sinyal-üretim frekansı (günde kaç sinyal) getiri-kalitesiyle ilişkili mi · Aynı sembolün ardışık günlerde tekrar sinyal vermesi (persistence) hiç ölçülmedi · Skor bileşenlerinin *ayrı ayrı* değil *etkileşimli* (interaction term) etkisi hiç test edilmedi · Backtest'in kaç farklı versiyonu koşulup en iyisinin seçildiği (meta-multiple-testing) hiç sayılmadı · Sinyal, piyasa-yapıcıların/algoritmaların davranışına bir tepki mi yoksa bağımsız bir gözlem mi · "Skor yüksek ama trade edilemez" (illikit) oranı ne · Composite skorun zaman içinde hangi bileşeni domine ediyor (drift var mı) · Sinyal başka bir varlık sınıfında (ETF, futures) da geçerli mi · Skorun "false negative" oranı (kaçırılan gerçek fırsatlar) hiç ölçülmedi.

**8. Kill Criteria:** Reverse-ranking OOS+matched-control'de tutarsızsa terk. Risk-hedefi de rejim-değiştirirse (bull'da geçerli bear'da değilse) "evrensel risk-boyutu" iddiası terk edilir, yalnız koşullu kalır.

**9. Three Biggest Bets:** (1) Risk-hedefi birincil metrik yapmak. (2) Giriş-noktası+drift diagnostiği. (3) Reverse-ranking'i pre-registered test etmek.

---

## PERSONA 2 — PORTFOLIO MANAGER (delta)

Yeni kavram istenmiş: **Portfolio Opportunity Quality (POQ)** — bir fırsatın tekil-kalitesi değil, mevcut portföye **eklediği marjinal-değer** (çeşitlendirme + risk-katkısı + korelasyon-maliyeti düşüldükten sonra).

**1. Blind Spots (10):** Top-N seçimi POQ değil tekil-skor kullanıyor · aynı-gün sinyallerin gerçekleşen korelasyonu hiç ölçülmedi · "birbirini tamamlayan 10 fırsat" hiç aranmadı, yalnız "en iyi 10" arandı · sektör/faktör-yığılması top-N içinde sistematik olabilir · turnover (12.27x gözlendi) maliyetin gerçek sürücüsü olabilir, sinyal-kalitesi değil · portföy-drawdown'ın tekil-trade drawdown'lardan nasıl türediği (toplama mı, kümelenme mi) belirsiz · opportunity-cost (bir pozisyon açıkken kaçırılan başka sinyal) hiç fiyatlanmadı · redundant sinyaller (aynı hareketi ölçen farklı isimler) portföyde etkin çeşitlendirme sağlamıyor olabilir · capacity, portföy-büyüklüğüyle birlikte hiç ölçeklenmedi · risk-bütçeleme (position-sizing) ATR-bulgusuyla hiç entegre değil.

**2. Wrong Assumptions (10):** En iyi tekil-trade'ler en iyi portföyü yapar `EVIDENCE ters` · Top-N sabit büyüklükte olmalı · Eşit-ağırlık doğru varsayılan · Sinyal-sayısı arttıkça çeşitlendirme artar (yığılma riskini görmezden gelir) · Portföy-riski tekil-risklerin toplamıdır (korelasyonu görmezden gelir) · Turnover maliyeti sabit-yüzdeyle temsil edilebilir · Capacity sonradan eklenir · Sharpe tek başına yeterli · Drawdown yalnız kötü-şans · Diversifikasyon otomatik gerçekleşir (isim-sayısı arttıkça).

**3. Optimizing Incorrectly (10):** Top-N seçimini tekil-skora göre yapmak · concentration kısıtı olmadan simülasyon · CVaR/tail-katkı raporlanmıyor · position-sizing risk-boyutundan (ATR) bağımsız · turnover'ın maliyet-etkisi ayrıştırılmadı · aynı-gün kümelenme kontrol edilmiyor · capacity portföy-büyüklüğüyle test edilmiyor · sektör-max-ağırlık kısıtı yok · factor-exposure (beta, momentum-faktörü) ayrıştırılmadı · drawdown-sonrası davranış karakterize edilmedi.

**4. New Opportunities (10):** POQ metriğini formalize etmek (marjinal-Sharpe-katkısı) · concentration-kısıtlı simülasyon · ATR-bazlı position-sizing · CVaR raporlama zorunluluğu · investable-universe'de capacity-testi · aynı-gün korelasyon-analizi · sektör-max-ağırlık taraması · factor-exposure ayrıştırma (market/sektör/momentum beta) · turnover-optimize edilmiş rebalans sıklığı · redundancy-filtreli top-N (aynı-hareketi-ölçen isimleri ele).

**5. Radical Alternatives (5):** `HYPOTHESIS` FinPilot doğru hisseyi bulmayı bırakır, doğru risk-kombinasyonunu bulur — top-10 yerine portfolio-construction birincil ürün · `SPECULATION` Edge sıfır olsa bile POQ-optimize portföy, edge'siz-eşit-ağırlıktan daha iyi risk-ayarlı sonuç verir · `HYPOTHESIS` Sinyal seçimi yerine "hangi mevcut pozisyonu azalt/artır" (rebalancing-motoru) birincil çıktı · `SPECULATION` Kullanıcıya "hisse" değil "portföy-sağlığı skoru" gösterilir · `HYPOTHESIS` Capacity, evren-tanımının parçası olur, sonradan filtre değil.

**6-9.** (Deneyler §Experiment Factory'de; Kill: concentration-kısıtlı portföy kısıtsızdan iyi değilse POQ kavramı terk edilir; Three Bets: POQ formalizasyonu, ATR-sizing, concentration-kısıtı.)

---

## PERSONA 3 — MARKET MICROSTRUCTURE SPECIALIST (tam-taze)

Bu promptun özel açısı: **"opportunity'nin ömrü ne kadar"** — sinyal 15 dakika sonra, 1 saat sonra, ertesi gün hâlâ geçerli mi? Bu hiç sorulmamış bir soru.

**1. Blind Spots (10):** Sinyal oluştuğu anda gerçekten trade-edilebilir miydi (fiyat hâlâ o seviyede miydi) hiç doğrulanmadı · fırsatın "yarı-ömrü" (opportunity decay) hiç ölçülmedi · günlük bar, gün-içi fırsatın ne zaman doğduğunu gizliyor (kapanışta mı, öğlen mi oluştu) · gap-davranışı (gece açığı) ile intraday-davranış hiç ayrıştırılmadı · likidite, sinyal-anında değil yalnızca genel/tarihsel olarak biliniyor · execution-gecikmesi (sinyal→emir→fill) hiç modellenmedi · açılış-ilk-30dk oynaklığı ayrı bir rejim olarak tanınmıyor · event-timing (earnings/haber) ile teknik-sinyal aynı havuzda karışık · slippage/price-impact yalnız sabit-yüzde varsayımıyla temsil ediliyor · institutional-flow/opsiyon-pozisyonlanması hiç erişilemedi (plan kısıtı).

**2. Wrong Assumptions (10):** Günlük kapanış-fiyatı = gerçek karar-anı fiyatı · Ertesi-açılış = makul giriş noktası `UNKNOWN, test edilmedi` · Sabit %0.55 maliyet her likidite-seviyesinde geçerli `EVIDENCE muhtemelen hayır` · Sinyal, oluştuğu andan t+5'e kadar sabit-kalitede · 1D timeframe doğru analiz birimi `UNKNOWN` · Fiyat-hareketi kendi kendini açıklar (katalizör gerekmez) · Likidite zaman-içinde durağan · Spread sabit/ihmal-edilebilir · Açılış ve kapanış aynı mikroyapı davranışını gösterir · Opsiyon/order-flow verisi olmadan "bilgi eksikliği yok" varsayımı.

**3. Optimizing Incorrectly (10):** Ertesi-açılış girişini sorgulamadan optimize etmek · sabit-maliyet modeliyle "edge" ilan etmek · günlük-bar'ı intraday-fırsatın vekili saymak · gap-davranışını ayrı analiz etmemek · event-driven alt-kümeyi teknik alt-kümeden ayırmamak · likidite-kovası olmadan tüm evreni tek havuzda test etmek · execution-gecikmesini sıfır varsaymak · açılış-ilk-30dk'yı normal bar gibi işlemek · fırsat-ömrünü ölçmeden "5 gün tut" kararı vermek · order-flow eksikliğini "önemsiz" varsaymak (test edilmeden).

**4. New Opportunities (10):** 3-giriş-noktası testi (close/open/close) · overnight vs intraday getiri ayrıştırması · gap-continuation vs gap-fade alt-küme testi · likidite-kovası segmentasyonu · event-driven (earnings/haber) alt-küme IC testi · açılış-ilk-30dk'yı ayrı rejim olarak tanımlama (intraday veri gelirse) · execution-gecikme-duyarlılığı testi (1 bar gecikmeli giriş vs anlık) · opsiyon-verisi erişilebilir olduğunda pozisyonlanma-faktörleri · takvim-mikroyapı etkileri (opex, ay-sonu) · sektör-içi göreli-likidite kıyası.

**5. Radical Alternatives (5):** `HYPOTHESIS` Analiz birimi "gün" değil "event" olur · `SPECULATION` FinPilot fiyat-tahmini yerine "bu isim şu an gerçekten alınabilir mi" (tradability) sorusuna odaklanan bir likidite-tarayıcısına dönüşür · `HYPOTHESIS` Overnight-getiri ayrı bir "gap-risk" ürünü olarak paketlenir · `SPECULATION` Event-time birincil zaman-birimi olur, takvim-zamanı ikincil · `HYPOTHESIS` Fırsat-ömrü (decay-eğrisi) her sinyalin yanında gösterilir — "bu fırsat X saat/gün taze kalır."

**6-9.** (Kill: 3-giriş-noktası arasında anlamlı fark çıkmazsa "giriş-zamanlaması sorunu" hipotezi terk edilir; Three Bets: giriş-noktası testi, gap-ayrıştırması, likidite-kovası segmentasyonu.)

---

## PERSONA 4 — BEHAVIORAL SCIENTIST (delta)

Önceki belgede Grade-inversiyonu ve pre-mortem işlendi. Burada yeni: **Top-10 listesinin ve yeşil/kırmızı UI'ın kendisinin** davranışsal etkisi — bu hiç sorulmadı.

**1. Blind Spots (10):** Top-10 listesi "bu 10'un dışı kötü" yanılgısını yaratabilir (mevcut kanıt: rejected, eligible'dan iyi!) · yeşil/kırmızı renk-kodlaması, altındaki kalibrasyon-kalitesinden bağımsız güven yaratır · günlük ritüel (her sabah bakma) kendi başına bir bağımlılık-döngüsü olabilir, karar-kalitesini artırmayabilir · geçmiş-performans gösterimi (outlier-driven olsa bile) overconfidence besler · "AI dedi ki" çerçevesi authority-bias'ı güçlendirir · kullanıcının kendi tahminiyle sistem-tahminini kıyaslaması hiç yok (anchoring'i azaltacak tek mekanizma) · kayıp-senaryosu hiç gösterilmiyor (yalnız fırsat gösteriliyor, loss-aversion'ı dengelenmemiş bırakıyor) · listenin sırası (1. sırada olan) orantısız ağırlık kazanıyor olabilir (ilk-madde etkisi) · kullanıcı "bugün sinyal yok" durumunu nasıl yorumluyor (FOMO mu, rahatlama mı) hiç ölçülmedi · Grade'in ters-kalibre olduğu bilinip düzeltilmemesi, kullanıcı-güvenini kötüye kullanma riski taşıyor.

**2-3-4-5.** (Önceki belgeyle büyük örtüşme — bkz. Persona 3 orada. Buradaki net *yeni* madde: Top-10/renk-kodlama/ritüel-döngüsü davranışsal etkisi hiç test edilmedi; bunlar Experiment Factory'de "Learning/Behavior Experiments" kategorisine eklendi.)

**9. Three Biggest Bets:** (1) Grade yerine kalibre-olasılık. (2) Top-10 yerine "neden bu 10, neden diğerleri değil" şeffaflığı. (3) Kayıp-senaryosu zorunlu gösterimi.

---

## PERSONA 5 — DATA SCIENTIST (tam-taze, Quant'tan ayrı)

Bu persona quant'tan farklı: quant "doğru hipotez mi test ediyoruz" sorar, data scientist **"veri süreci bize yalan söylüyor olabilir mi"** sorar — daha temel, daha altyapısal.

**1. Blind Spots (10):** Kaç farklı deney koşulup en iyi sonucun seçildiği hiç formal sayılmadı (meta-multiple-testing) `EVIDENCE — binlerce config koşuldu` · look-ahead bias'ın ATR/RVOL gibi "aynı-gün" hesaplanan feature'larda tam giderilip giderilmediği şüpheli (gün henüz kapanmadan hesaplanan ATR, gün-sonu verisini sızdırabilir) · survivorship-bias hiç formal test edilmedi (evren bugün-hayatta-olan sembollerden mi oluşuyor) · universe-drift (zaman içinde evrenin bileşimi değişti mi) hiç izlenmedi · missing-data'nın rastgele mi yoksa sistematik mi (örn. düşük-likidite isimlerde daha sık eksik) olduğu bilinmiyor · p-hacking riski yüksek (binlerce config, resmi pre-registration yok) · regime-imbalance (%87 bull) örneklem-dengesizliği hiç düzeltilmedi · temporal-leakage'ın (train/validation ayrımının gerçekten zaman-sıralı mı) her deneyde tutarlı uygulandığı doğrulanmadı · sample-size küçük hücrelerde (conviction A n=13, sektör n=142) büyük-iddia riski · corporate-action (bölünme/birleşme) düzeltmelerinin fiyat serisine doğru yansıdığı hiç audit edilmedi.

**2. Wrong Assumptions (10):** Mevcut evren PIT (point-in-time) doğru `UNKNOWN, hiç doğrulanmadı` · ATR/RVOL hesaplaması look-ahead-free `UNKNOWN` · Train/validation ayrımı her deneyde tutarlı `UNKNOWN` · Missing-data rastgele `UNKNOWN, muhtemelen değil` · Binlerce config aramak "keşif," hipotez-testi değil-sayılabilir `EVIDENCE — ama sonuçlar hipotez gibi sunuldu` · Corporate-action düzeltmeleri doğru `UNKNOWN` · Küçük-n bulgular (n=13, n=142) büyük-n bulgularla aynı güvenilirlikte `EVIDENCE hayır` · Sample tüm evreni temsil ediyor `EVIDENCE hayır (%87 bull)` · Veri-kaynağı (EODHD/Alpaca/yfinance fallback) tutarlı kalite sağlıyor `UNKNOWN — fallback oranı %19-39 arası değişken, önceki scanner-performans raporunda gözlendi` · Dedup/canonical-identity politikası (earliest-timestamp) sonuçları sistematik etkilemiyor `UNKNOWN`.

**3. Optimizing Incorrectly (10):** Pre-registration olmadan geniş config-taraması yapmak · look-ahead-riskli feature'ları audit etmeden kullanmak · survivorship-bias'ı hiç ölçmeden "sonuç" ilan etmek · küçük-n hücrelerden büyük-iddia çıkarmak (conviction A, sektör-143) · regime-imbalance'ı düzeltmeden mutlak-getiri raporlamak · fallback-kaynaklı veri-kalite-farkını sinyal-kalitesinden ayırmamak · missing-data'yı rastgele varsayıp imputation/exclusion etkisini test etmemek · her deneyde train/validation tutarlılığını yeniden doğrulamamak (kopyala-yapıştır risk) · corporate-action düzeltmesini hiç audit etmeden fiyat-serisine güvenmek · dedup-politikasının (earliest-timestamp) sonuç üzerindeki etkisini hiç izole etmemek.

**4. New Opportunities (10):** Formal look-ahead audit (her feature için `feature_asof <= decision_time` testi) · survivorship-bias formal testi (delisted sembolleri dahil edip sonucu kıyaslama) · PIT universe-membership doğrulaması · fallback-kaynaklı veri-kalite ile sinyal-IC ilişkisini ayrıştırma · missing-data mekanizması testi (MCAR/MAR/MNAR) · corporate-action audit'i · dedup-politika-duyarlılık testi (earliest vs latest vs median) · regime-dengeli (bull/bear eşit-ağırlık) yeniden-örnekleme ile sonuçları tekrar hesaplama · meta-multiple-testing düzeltmesi (kaç config denendiği resmi kayıt altına alınıp Bonferroni/FDR uygulanması) · veri-kaynağı-bazlı (EODHD vs yfinance-fallback) IC kıyası.

**5. Radical Alternatives (5):** `HYPOTHESIS` Tüm geçmiş sonuçlar, formal look-ahead+survivorship audit'inden geçmeden "kanıt" sayılmaz — retroaktif audit zorunlu · `SPECULATION` FinPilot'un veri-pipeline'ı kendi bias-skorunu (leakage-risk-skoru) her deney için otomatik üretir · `HYPOTHESIS` Regime-dengeli yeniden-örnekleme mevcut "pozitif" sonuçların çoğunu değiştirir · `SPECULATION` Her config-taraması otomatik olarak "kaç test yapıldı" sayacı tutar, sonuçlar bu sayıya göre düzeltilir (FDR) · `HYPOTHESIS` Fallback-kaynaklı sinyaller ayrı bir "düşük-güven" etiketiyle işaretlenir.

**9. Three Biggest Bets:** (1) Formal look-ahead/survivorship audit'i — bu, tüm programın güvenilirliğinin temeli ve hiç yapılmadı. (2) Meta-multiple-testing düzeltmesi. (3) Regime-dengeli yeniden-örnekleme.

---

## PERSONA 6 — RISK SCIENTIST (tam-taze, Quant'tan ayrı)

Quant "getiri var mı" sorar, risk scientist **"kaybın nasıl oluştuğunu anlıyor muyuz"** sorar — bu FinPilot'un tek kanıtlanmış gücüyle (ATR→MAE) doğrudan örtüşüyor, o yüzden bu persona en somut/en az spekülatif olan.

**1. Blind Spots (10):** ATR→MAE bulgusu (IC −0.51) kanıtlı ama *neden* güçlü olduğu (mekanizma) hiç açıklanmadı · tail-risk (en kötü %1-5) ayrı karakterize edilmedi — yalnız ortalama-MAE biliniyor · gap-risk (gece açığında stop'un delinmesi) hiç ayrı ölçülmedi · loss-clustering (art arda kayıplar aynı rejimde/sektörde yığılıyor mu) hiç test edilmedi · recovery-time (kayıptan sonra ne kadar sürede telafi) hiç ölçülmedi · volatilite-expansion'ın (ATR aniden büyümesi) önceden görülüp görülemeyeceği hiç test edilmedi · stop-davranışı (ilk-temas-süresi, kaç kez "az kalsın" tetiklenip tetiklenmedi) hiç karakterize edilmedi · regime-bağımlı kayıp-profili (bear'da kayıplar farklı mı) yalnız kabaca (bull/bear ATR-IC) test edildi, derinlemesine değil · portföy-seviyesi tail-risk (birden fazla pozisyonun aynı anda kötü gitme olasılığı) hiç ölçülmedi · "bu trade'in başarısız olacağını önceden görebilir miyiz" sorusu hiç doğrudan modellenmedi (yalnız risk-büyüklüğü, risk-*olasılığı* değil).

**2. Wrong Assumptions (10):** MAE yalnız raporlama-amaçlı, entry-kararına girdi değil `EVIDENCE — kullanılmıyor ama kullanılabilir` · ATR tek risk-göstergesi yeterli `EVIDENCE — Test 1'de kombine-risk ATR'den kötü çıktı, yani ATR zaten en iyisi ama "yeterli" mi hâlâ açık` · Sabit TP/SL tüm risk-profillerine uyar · Stop-first-same-bar varsayımı gerçek execution'ı temsil eder `UNKNOWN` · Kayıplar birbirinden bağımsız (kümelenme yok) `UNKNOWN, muhtemelen yanlış` · Risk, yalnız fiyat-oynaklığından kaynaklanır (likidite-riski ayrı değil) · Gap-riski ATR'ye zaten gömülü `UNKNOWN` · Recovery her zaman gerçekleşir (yalnız süre değişir) · Tail-risk normal-dağılıma yakın (heavy-tail değil) `EVIDENCE hayır — lottery-evren` · Portföy-tail-risk tekil-tail-risklerin toplamı.

**3-4.** (Optimizing-incorrectly ve opportunities §Experiment Factory'deki Regime/Portfolio kategorileriyle örtüşüyor, tekrar edilmiyor — yalnız şu ikisi net-yeni: tail-decomposition hiç yapılmadı, gap-risk hiç ayrı ölçülmedi.)

**5. Radical Alternatives (5):** `HYPOTHESIS` FinPilot'un birincil çıktısı "beklenen kayıp senaryosu" (worst-case path) olur, "beklenen kazanç" değil · `SPECULATION` Kullanıcıya "bu trade %X olasılıkla stop'a çarpar, ortalama %Y kayıpla" gösterilir · `HYPOTHESIS` Gap-riski ayrı bir "gecelik-tutma-riski" skoru olarak paketlenir · `SPECULATION` Loss-clustering tespit edilirse, "bugün piyasa kayıp-kümelenmesi rejiminde" uyarısı verilir · `HYPOTHESIS` Recovery-time dağılımı kullanıcıya "bu tür kayıp tarihsel olarak ortalama N günde telafi edildi" olarak sunulur.

**9. Three Biggest Bets:** (1) Tail-decomposition (worst-5%'i ayrı karakterize et). (2) Gap-risk'i ayrı ölç. (3) MAE'yi entry-kararına (yalnız raporlamaya değil) girdi yap.

---

## PERSONA 7 — PRODUCT STRATEGIST (delta)

Önceki belgede kategori-alternatifleri işlendi. Burada net-yeni: **signal/research/education/confidence/speed/explanation/understanding/decision-support/habit/accountability**'yi birbirinden ayırma talebi — bunlar önceki belgede tek "değer önerisi" başlığı altında birleşikti, burada ayrıştırılmalı.

**Ayrıştırma:**
| Bileşen | FinPilot bugün sağlıyor mu | Kanıt |
|---|---|---|
| Signal (ne alayım) | Evet ama kanıtsız/ters-kalibre | `EVIDENCE ters` |
| Research (neden) | Kısmen — bileşen-açıklaması var, kalite-kanıtı yok | `EVIDENCE zayıf` |
| Education (öğren) | Zayıf — pasif format | `HYPOTHESIS` |
| Confidence (güven) | Evet ama yanlış-yönde (ters-kalibre Grade) | `EVIDENCE riskli` |
| Speed (zaman kazandır) | Muhtemelen evet | `UNKNOWN, ölçülmedi` |
| Explanation (açıkla) | Var ama explainability-theater riski | `HYPOTHESIS` |
| Understanding (piyasayı anla) | Zayıf — tek-skor, bağlam yok | `HYPOTHESIS` |
| Decision-support (karar-destek) | Zayıf — karar-kalitesi hiç ölçülmedi | `UNKNOWN` |
| Habit (alışkanlık/ritüel) | Muhtemelen güçlü (Morning Ledger) | `UNKNOWN, ölçülmedi` |
| Accountability (hesap-verebilirlik) | Güçlü — NO-GO kararları şeffaf | `FACT` |

**En büyük kaçırılan kısım:** Accountability zaten güçlü (governance-disiplini) ama bu **kullanıcıya hiç taşınmıyor** — yalnız iç-süreç. Bu, Product-Strategist'in en somut önerisi: mevcut-en-güçlü-varlığı (dürüstlük) dış-yüzeye taşımak.

**9. Three Biggest Bets:** (1) Accountability'i (NO-GO şeffaflığı) kullanıcı-yüzeyine taşı. (2) Habit-değerini (Speed dahil) formal ölç — belki asıl satılan bu. (3) Signal/Education/Understanding'i ayrı ürün-yüzeyleri yap, tek arayüzde karıştırma.

---

## PERSONA 8 — AI/AGENT ARCHITECT (delta)

Önceki belgede "AI prediction değil research yapmalı" işlendi. Burada net-yeni: her öneri **gerçek-fayda/veri-gereksinimi/maliyet/güvenilirlik/uygulanabilirlik** beşlisiyle değerlendirilmeli — hype üretmeden.

| Alternatif mimari | Gerçek fayda | Veri gereksinimi | Maliyet | Güvenilirlik | Uygulanabilirlik |
|---|---|---|---|---|---|
| AI research agent (hipotez üretir) | Yüksek — bu konuşmanın kendisi kanıt | Mevcut veri yeterli | Orta | Orta (insan-gözden-geçirme gerekir) | Yüksek — bugün başlanabilir |
| Market memory (biriken vaka-tabanı) | Orta-Yüksek — moat potansiyeli | Zaman gerektirir (birikmeli) | Düşük (altyapı basit) | Yüksek | Yüksek |
| Event intelligence (haber→sinyal) | Belirsiz | Yeni veri kaynağı gerekir (haber-feed) | Orta-Yüksek | Düşük (LLM-hallucination riski) | Orta |
| Autonomous research loop (kendi kendine deney tasarlar) | Yüksek potansiyel ama riskli | Mevcut veri yeterli | Düşük | Düşük (denetimsiz overfitting riski) | Düşük — insan-onayı şart |
| Hypothesis/experiment engine (pre-registration otomasyonu) | Yüksek — disiplin zaten var, otomasyon güçlendirir | Mevcut veri yeterli | Düşük | Yüksek | Yüksek — bugün başlanabilir |
| Multi-agent lab (bull/bear/skeptic) | Orta — kullanıcı-değeri belirsiz, araştırma-değeri yüksek | Mevcut veri yeterli | Orta | Orta | Orta — küçük pilotla test edilebilir |

**Net sonuç:** En yüksek fayda/maliyet oranı **hypothesis/experiment-engine** ve **market-memory**'de — ikisi de mevcut disiplinin doğal uzantısı, yeni veri gerektirmiyor, düşük-risk. Autonomous-loop ve event-intelligence şu an **hype-riski yüksek**, ertelenmeli.

**9. Three Biggest Bets:** (1) Hypothesis/experiment-engine'i otomatikleştir (bu belgenin ürettiği pre-registration formatını sistematikleştir). (2) Market-memory'yi küçük ölçekte başlat (her NO-GO/GO kararı kalıcı, aranabilir vaka olsun). (3) Multi-agent'ı yalnız-araştırma-aracı olarak pilotla, kullanıcı-yüzeyine henüz taşıma.

---

## PERSONA 9 — FUTURIST / SERIAL FOUNDER (delta)

Önceki belgede 2030-vizyonu işlendi. Burada 2031 ve "scanner mı/research-platform mu/learning-platform mu/market-memory mi/personal-reasoning-engine mi/AI-research-organization mı/market-operating-system mi" sorusu net-kategorik.

**5 farklı gelecek (kategorik seçim gerektiren format):**
1. `SPECULATION` **Market Operating System** — kullanıcının tüm finansal-karar-akışının (araştırma+risk+portföy+öğrenme) tek altyapısı; FinPilot arka-planda çalışan bir işletim-katmanı, ön-planda görünmeyen.
2. `SPECULATION` **Personal Financial Reasoning Engine** — kullanıcının kendi düşünme-sürecini dışsallaştırıp geliştiren bir düşünme-aracı; piyasa hakkında değil, kullanıcının piyasa-hakkındaki-muhakemesi hakkında.
3. `HYPOTHESIS` **Market Memory** — kolektif, biriken, kaynak-gösteren bir hafıza; "bu daha önce oldu mu, ne öğrendik" sorusuna cevap veren bir kurum-hafızası.
4. `SPECULATION` **AI Research Organization** — sinyal satmayan, kanıt-üreten ve çürüten, şeffaf bir araştırma-kurumu; müşterisi bireysel yatırımcı değil, kurumlar/analistler olabilir.
5. `HYPOTHESIS` **Research Platform (mevcut yörüngenin en gerçekçi uzantısı)** — bugünkü altyapının doğal büyümesi; scanner kalır ama ikincil, birincil değer araştırma-şeffaflığı.

**En gerçekçi (kanıta en yakın):** #5, çünkü mevcut altyapı zaten oraya yakın. **En yüksek-potansiyel ama en riskli:** #1 (Market OS), çünkü kategori-yaratma gerektirir, kanıt yok.

**9. Three Biggest Bets:** (1) #5'i (Research Platform) 12 ay içinde gerçekleştir — düşük risk. (2) #3'ü (Market Memory) paralel küçük-pilotla başlat — düşük maliyet, yüksek-moat potansiyeli. (3) #1 ve #2'yi (Market OS, Reasoning Engine) 2027+ vizyonu olarak parked tut, bugün kaynak ayırma.

---

## PERSONA 10 — DEVIL'S ADVOCATE (tam-taze)

Görev: her varsayımı saldırıya uğratmak ve **en az 20 alternatif açıklama** üretmek.

**Saldırılan varsayımlar ve alternatif açıklamalar (20):**
1. "Kullanıcı her sabah finans-içeriği istiyor" → *Alternatif:* Kullanıcı yalnız açık-kaldığı için okuyor, aktif istek yok (habit ≠ desire).
2. "Açık karne güven yaratıyor" → *Alternatif:* Açık karne yalnız "biz dürüstüz" hissi yaratıyor, kullanıcı asıl performansı hiç anlamıyor (karmaşıklık-perdesi).
3. "Grade değerli" → *Alternatif:* Grade yalnız karar-yorgunluğunu azaltıyor (bilişsel-rahatlık), doğruluğuyla ilgisi yok — kullanıcı Grade'i "doğru olduğu için" değil "seçmek zorunda kalmadığı için" seviyor olabilir.
4. "Kullanıcı araştırma-adaylarını önemsiyor" → *Alternatif:* Kullanıcı yalnız sonucu (al/sat) önemsiyor, "aday" kavramı bizim iç-dilimiz, kullanıcı dili değil.
5. "AI açıklaması değerlidir" → *Alternatif:* AI açıklaması yalnız "bir şey düşünülmüş" hissi veriyor, kullanıcı içeriği gerçekten okumuyor (explainability theater).
6. "Market Memory moat olabilir" → *Alternatif:* Herkes aynı halka açık veriye erişiyor, "hafıza" rakiplerce kolayca kopyalanabilir — gerçek moat değil.
7. "Günlük ritüel retention yaratır" → *Alternatif:* Günlük ritüel yorgunluk yaratır (notification-fatigue), retention'ı düşürür.
8. "Quant edge bulunabilir" → *Alternatif:* Bu evrende (küçük-cap, düşük-likidite, halka-açık teknik-veri) edge yapısal olarak imkânsız — aranan şey yok.
9. "Daha iyi ranking daha iyi sonuç verir" → *Alternatif:* Ranking'in kendisi (herhangi bir ranking) piyasaya etkisiz; asıl belirleyici execution-disiplini/risk-yönetimi, ranking değil.
10. "Kullanıcı decision-quality'sini geliştirmek ister" → *Alternatif:* Kullanıcı hızlı-karar ister, "geliştirme" süreç uzatır, kullanıcı bunu istemez.
11. "FinPilot bir ürün-fırsatı" → *Alternatif:* FinPilot çözülemez bir problemi (kanıtsız-alfa-arayışı) çözmeye çalışan, temelden yanlış-kurulmuş bir proje olabilir.
12. "Dürüstlük (NO-GO'lar) farklılaştırıcı" → *Alternatif:* Kullanıcılar dürüstlüğü değil, kesinliği (yanlış bile olsa) tercih eder — dürüstlük ticari-olarak cezalandırılabilir.
13. "Risk-hedefi (ATR-MAE) ürünleştirilebilir" → *Alternatif:* Risk-bilgisi zaten herkeste var (broker-marj-ekranları), farklılaştırıcı değil.
14. "Sektör-trend bulgusu gerçek" → *Alternatif:* 143-sembol küçük-n, tesadüf; tam-evrende replike-olmaması zaten bunu gösteriyor.
15. "Composite-skor düzeltilebilir" → *Alternatif:* Skor kavramının kendisi (tek-sayıya-indirgeme) yapısal olarak yanlış, "düzeltme" değil "terk" gerekir.
16. "Portföy-yaklaşımı edge-olmadan bile değer katar" → *Alternatif:* Kullanıcılar zaten kendi portföylerini yönetiyor (broker/robo-advisor), bu segment doymuş.
17. "AI multi-agent kullanıcı-değeri yaratır" → *Alternatif:* Çoklu-ses kullanıcıyı felç eder (analysis-paralysis), tek-ses (yanlış bile olsa) daha kullanılabilir.
18. "Eğitim asıl moat" → *Alternatif:* Eğitim-pazarı zaten kalabalık (Khan Academy, Investopedia, YouTube), farklılaşma zor.
19. "Forward-shadow temiz kanıt üretir" → *Alternatif:* Piyasa-rejimi değişirse (bugünkü ~%87-bull dönem sona ererse) forward-shadow da yalnız yeni-bir-dönem-özel sonuç üretir, "temiz" değil sadece "farklı-kontamine."
20. **En radikal:** "FinPilot'un temel tezi (teknik-sinyal+skor+scanner ile bireysel-yatırımcıya-değer-katmak) baştan yanlış problem seçimi olabilir" → *Alternatif:* Doğru problem hiç "hangi hisse" değil, "yatırımcının kendi davranışını nasıl disipline ederiz" — bu, tamamen farklı bir ürün (davranış-koçluğu) gerektirir, mevcut kod-tabanının %95'i ilgisiz kalır.

**"FinPilot'un temel tezi yanlışsa ne olur?"** → En olası senaryo: alfa hiçbir zaman bulunmaz (kanıt zaten bu yönde), ama şirket bunu "henüz bulmadık" diye erteleyerek kaynak yakmaya devam eder. Doğru tepki, tezin kendisini (bireysel-hisse-seçim-değeri) periyodik olarak **yeniden-oylamak** — her 2-3 ayda "hâlâ bu tezle mi devam ediyoruz" sorusunu resmi olarak sormak.

**9. Three Biggest Bets:** (1) Her 2-3 ayda temel-tezi resmi olarak yeniden-oylama ritüeli kur. (2) #11 ve #20'yi ciddiye alıp "davranış-koçluğu" alternatifini küçük bir pilotla test et. (3) #6/#12/#13'ü (moat-iddiaları) kanıtsız-varsayım olarak işaretle, doğrulanana kadar pazarlama-dilinde kullanma.

---

# AŞAMA 2 — COLLISION

## Collision Protokolü (7 named collision, her biri Support/Attack/Modify/Test/Kill)

### COLLISION 1 — Quant × Product
**Soru:** İstatistiksel-olarak-iyi olan gerçekten kullanıcı-değerli mi? Kullanıcı-değerli olan ölçülebilir-edge gerektiriyor mu?

**Support:** Risk-hedefi (ATR-MAE) hem istatistiksel-olarak-geçerli hem ürün-değerli — bu ender bir kesişim, öncelik burada olmalı.
**Attack:** Product'ın "accountability zaten güçlü, dış-yüzeye taşı" önerisi istatistiksel-kanıt gerektirmiyor — quant'ın "önce kanıt" ısrarı burada gereksiz-yavaşlatıcı olabilir.
**Modify:** İkisini ayır — kanıt-gerektiren iddialar (risk-hedefi, sinyal-kalitesi) quant-standardına tabi; kanıt-gerektirmeyen değer-önerileri (şeffaflık, dürüstlük) hemen ürünleştirilebilir.
**Test:** Şeffaflık-özelliğini (NO-GO-görünürlüğü) hiçbir yeni istatistiksel-kanıt beklemeden küçük-grupta pilotla; risk-hedefini kanıt-standardına tabi tut.
**Kill:** Şeffaflık-pilotu kullanıcı-güvenini düşürürse ("neden bu kadar çok başarısızlık gösteriyorlar") bu yaklaşım terk edilir.

### COLLISION 2 — Quant × Behavior
**Soru:** Daha-iyi-sinyal daha-iyi-karar demek mi? Grade yanlış-yönlendirebilir mi? Daha-fazla-veri karar-kalitesini artırır mı?

**Support:** Behavioral'ın Grade-inversiyon-uyarısı quant'ın kendi kanıtıyla (`FACT` A<B<C) doğrudan destekleniyor — bu nadir bir tam-hemfikirlik.
**Attack:** Quant "daha-fazla-veri" ister (evren-genişletme, yeni-feature) ama Behavioral bunun karar-kalitesini artırmayacağını, yalnız karmaşıklığı artıracağını iddia eder — ikisi de kanıtsız, ikisi de test-edilebilir.
**Modify:** Veri-genişletmesi yalnız *risk-hedefi* için yapılsın (kanıtlı-geçerli alan), *getiri-hedefi* için yeni-veri aramayı ertele.
**Test:** Grade kaldırıldığında kullanıcı karar-hızı/memnuniyeti değişir mi — küçük A/B.
**Kill:** Grade kaldırıldığında kullanıcı-terk-oranı belirgin artarsa, "kademeli-geçiş" (Product'ın önerisi) devreye girer.

### COLLISION 3 — Quant × Portfolio
**Soru:** Trade-level optimizasyon yanlış abstraction mı? Portfolio-level opportunity-selection daha doğru mu?

**Support:** Kanıt zaten bunu gösteriyor — tekil-barrier-expectancy portföye taşınmıyor (`FACT` portföy sim başa-baş).
**Attack:** Portfolio-level'a geçmek, tekil-sinyal araştırmasının "boşa gitti" anlamına gelmez — POQ formülasyonu hâlâ tekil-sinyal-kalitesine muhtaç (girdi olarak).
**Modify:** İkisi ayrı katmanlar: tekil-sinyal-kalitesi (şu an zayıf) *girdi*, portföy-inşası (hiç test edilmemiş) *çıktı-katmanı* — biri diğerini geçersiz kılmaz, sıralamayı değiştirir.
**Test:** POQ-optimize portföy vs eşit-ağırlık portföy, edge-sıfır varsayımıyla bile Sharpe-kıyası.
**Kill:** POQ, eşit-ağırlıktan anlamlı-iyi değilse, portföy-katmanının "edge-olmadan-değer" iddiası terk edilir.

### COLLISION 4 — Data × Quant
**Soru:** Her önemli quant-iddiası hangi veri-yanlılığıyla açıklanabilir?

Data Scientist'in Persona 5 kanıt-tablosu buraya doğrudan uygulanıyor: composite-IC~0 → *survivorship veya regime-imbalance'tan bağımsız mı?* Henüz test edilmedi, `UNKNOWN`. entry_ok-inversiyonu → *dedup-politikası (earliest-timestamp) bu inversiyonu yaratıyor olabilir mi?* Test edilmedi, `UNKNOWN`. ATR→MAE (−0.51) → *bu, look-ahead'siz mi hesaplandı (aynı-gün ATR, gün henüz kapanmadan)?* Kritik-soru, hiç doğrulanmadı.
**Attack en kritik:** Eğer ATR aynı-günün-verisiyle (gün kapanmadan) hesaplanıyorsa, ATR→MAE ilişkisi **kısmen look-ahead-artefaktı olabilir** — bu, programın TEK kanıtlanmış bulgusunu tehdit eden en ciddi itiraz.
**Test:** ATR'yi yalnız *önceki-günün-kapanışına-kadarki* veriyle yeniden hesapla, IC'nin −0.51'den ne kadar değiştiğini ölç. **Bu, tüm programın en yüksek-öncelikli doğrulama-testi olmalı.**
**Kill:** Look-ahead-düzeltilmiş ATR'nin IC'si anlamlı-düşerse (örn. |IC|<0.2), risk-hedefi de "kanıtlanmış" statüsünü kaybeder ve programın **hiçbir** doğrulanmış bulgusu kalmaz — bu en kötü ama en önemli-bilinmesi-gereken senaryo.

### COLLISION 5 — AI × Data
**Soru:** AI gerçekten açıklama mı yapıyor, yoksa veriden-sonra hikâye mi uyduruyor (source-grounding)?

**Support:** Bu konuşmanın kendisi (bu belge dahil) her iddiayı FACT/EVIDENCE/HYPOTHESIS ile etiketlemeye çalışıyor — source-grounding disiplini var.
**Attack:** Composite-skorun "bileşen-açıklaması" (RSI+MACD+volume katkısı) skorun kendisi kalibre-değilken **anlamsız bir hikâye** olabilir — sayılar doğru toplanıyor ama toplamın kendisi bilgi taşımıyor.
**Modify:** Her AI-açıklamasının yanına, açıklanan-skorun kendi-geçerlilik-durumu (kalibre mi, değil mi) otomatik eklensin.
**Test:** Composite-skor açıklamasını kullanıcıya gösterip "bu skor kalibre değildir" uyarısıyla/uyarısız iki grupta güven-algısını kıyasla.
**Kill:** Uyarı eklense bile kullanıcı-güveni değişmiyorsa, açıklama-arayüzünün kendisi "explainability theater" olarak kabul edilip kaldırılır.

### COLLISION 6 — Product × Behavior
**Soru:** Kullanıcı gerçekten bunu kullanmak istiyor mu, yoksa ürün bizim-istediğimiz-davranışı mı ölçüyor?

**Support:** Devil's Advocate'in #1 ve #7 maddeleri (habit≠desire, ritüel yorgunluk-yaratabilir) bu şüpheyi doğrudan besliyor.
**Attack:** Product'ın "accountability/dürüstlük farklılaştırıcı" iddiası da aynı riski taşıyor — belki kullanıcı dürüstlüğü değil kesinliği istiyor (Devil's Advocate #12).
**Modify:** Her iki iddiayı da (habit-değeri VE dürüstlük-değeri) doğrudan kullanıcıya sormadan varsaymamak — ikisi de `UNKNOWN`, ikisi de test edilmeli, ikisi de öncelik-değil-hipotez.
**Test:** Kullanıcı-motivasyon-anketi (Product P4'ün de önerdiği) — bu collision'ın çözümü aynı zamanda o eksik-testin çözümü.
**Kill:** Anket "kullanıcı kesinlik istiyor, dürüstlük değil" sonucu verirse, mevcut governance-disiplinini pazarlama-dili yapma stratejisi terk edilir (iç-disiplin olarak kalır, dış-mesaj olmaz).

### COLLISION 7 — Futurist × Skeptic (Devil's Advocate)
**Her gelecek-vizyonuna karşı "neden gerçekleşmeyebilir":**
- Market OS → *Neden olmayabilir:* Kategori-yaratma başarısızlık-oranı çok yüksek (çoğu "OS" iddiası pazarlama-abartısı kalır); mevcut kaynak-ölçeği bunu desteklemiyor.
- Personal Reasoning Engine → *Neden olmayabilir:* Kullanıcılar "düşünmeyi öğrenmek" için değil "hızlı-karar" için ürün seçer (Devil's Advocate #10) — pazar-talebi ters yönde olabilir.
- Market Memory → *Neden olmayabilir:* Halka-açık veriye dayanan hafıza kolayca kopyalanabilir (Devil's Advocate #6), moat değil.
- AI Research Organization → *Neden olmayabilir:* B2C'den B2B'ye geçiş yeni satış-döngüsü/yeni-kitle gerektirir, mevcut varlıkla (kullanıcı-tabanı) uyumsuz olabilir.
- Research Platform (en gerçekçi) → *Neden olmayabilir:* Bu bile "araştırma sonuçta hiçbir zaman pozitif kanıt üretmezse" (Devil's Advocate #8: edge yapısal-olarak-imkânsız) sonunda "biz sürekli negatif-sonuç üreten bir laboratuvarız" konumuna sıkışabilir — sürdürülebilir ama heyecansız.

**Collision-7 sonucu:** Hiçbir vizyon risksiz değil; en-az-riskli olan (Research Platform) aynı zamanda en-az-heyecanlı olan. Bu gerilim **çözülmedi, kasıtlı olarak açık bırakılıyor** — Aşama 3'te Big Bet seçiminin parçası.

---

# QUANT RESEARCH WAR ROOM

Bu bölüm mevcut kanıta dayanarak, sorulan her soruyu doğrudan cevaplıyor — spekülasyon değil, elimizdeki veriyle mümkün olan en dürüst yanıt.

## ENTRY
- **Entry gerçekten gerekli mi?** `UNKNOWN` — hiç "entry'siz" (yalnız gözlem) bir kontrol test edilmedi. Test edilebilir: sinyal-close fiyatını "sanal giriş" sayıp gerçek-entry'siz drift ölç.
- **Entry-delay test edildi mi?** Hayır `FACT`. En yüksek-öncelikli boşluk (bkz. §0 UNKNOWN).
- **Confirmation entry?** Kısmen — score_3 (üç confirmation) test edildi ama score_2'den üstün değil `EVIDENCE`.
- **Pullback entry?** Hiç test edilmedi `FACT`.
- **Relative entry (sektöre göre)?** Hiç test edilmedi, ama sektör-trend bulgusu (143-sembol) bunun için umut verici bir zemin `EVIDENCE zayıf`.
- **Event entry?** Hiç test edilmedi (catalyst_factor feature var ama ayrı IC'si hiç ölçülmedi) `FACT`.
- **Multi-stage entry (kademeli giriş)?** Hiç düşünülmedi `FACT`.
- **Regime-specific entry?** Kısmen (SPY 50-SMA rejim taşınıyor) ama entry-kuralı rejime göre hiç değişmiyor, yalnız *ölçülüyor* `EVIDENCE`.

## EXIT
- **TP gerçekten gerekli mi?** `HYPOTHESIS` — bariyersiz drift-eğrisi çizilmeden bu soru cevaplanamaz. En kritik eksik test.
- **SL gerçekten gerekli mi?** Risk-yönetimi açısından muhtemelen evet (tail-risk kanıtlı, MAE dağılımı heavy), ama *mesafesi* hiç ATR-bulgusuyla entegre optimize edilmedi.
- **Time exit?** Hiç sistematik test edilmedi (yalnız sabit-5-gün horizon var, "ne zaman çık" değil "ne kadar tut" test edildi).
- **Thesis exit?** Hiç kavramsallaştırılmadı — mevcut sistemde "tez" diye bir şey yok, yalnız fiyat-bariyeri var.
- **Momentum decay?** Hiç ölçülmedi — sinyal sonrası momentum'un ne zaman söndüğü bilinmiyor.
- **Volatility exit?** Hiç test edilmedi (ATR-genişlemesi bir exit-tetikleyicisi olarak kullanılmadı, yalnız sizing için önerildi).
- **Regime exit?** Hiç test edilmedi.
- **Opportunity-cost exit?** Hiç test edilmedi (portföy-katmanı zaten eksik).
- **MFE-based exit?** Kısmen var (mfe5 raporlanıyor) ama exit-kuralı olarak kullanılmıyor.
- **Portfolio exit?** Hiç yok.

**Net sonuç:** Exit-tarafında **hiçbir alternatif gerçekten test edilmedi** — yalnız TP/SL'nin sayısal-parametreleri (2xATR/1xATR) tarandı. Bu, tüm War Room'un en çarpıcı bulgusu: "exit araştırması" dediğimiz şey aslında yalnız **tek bir exit-türünün parametre-taraması.**

## RANKING
- **High score neden kötü performans gösteriyor?** `HYPOTHESIS` — en olası açıklama extension/exhaustion (uzamış/tükenmiş isimleri seçme), hiç doğrudan test edilmedi.
- **Reverse ranking neden çalışıyor olabilir?** `HYPOTHESIS` — eğer skor sistematik-yanlış-yönlüyse (uzamışı-kaliteli-sanıyorsa), tersi otomatik "az-uzamışı" seçer — bu mean-reversion'a benzer bir mekanizma olabilir, test edilmedi.
- **Score monotonic mi?** Hayır `FACT` (composite quintile azalan, finpilot düz).
- **Score calibration yapılmış mı?** Evet, test edildi ve başarısız `FACT` (Brier 0.236/0.248, ECE yüksek).
- **Rank stability var mı?** `UNKNOWN` — hiç ölçülmedi (aynı sembolün ardışık günlerde rank'inin ne kadar tutarlı olduğu).
- **Signal decay var mı?** `UNKNOWN` — hiç ölçülmedi.

## MAE/MFE
- **Kazananlar ne kadar adverse-excursion yaşıyor?** `UNKNOWN` — MAE raporlanıyor ama kazanan/kaybeden ayrımıyla path-decomposition hiç yapılmadı.
- **Kaybedenler ne kadar favorable-excursion yaşıyor?** `UNKNOWN` — aynı boşluk.
- **MFE ne kadar erken gerçekleşiyor?** `UNKNOWN` — time-to-MFE hiç ölçülmedi.
- **MAE ile final-return ilişkisi nedir?** Kısmen — ayrı ayrı IC'leri var (mae5, c2c5_net) ama aralarındaki path-ilişkisi (MAE önce mi geliyor final-return'den) hiç modellenmedi.
- **Exit-timing MFE'nin ne kadarını yakalıyor?** `UNKNOWN` — hiç ölçülmedi, ama bu tam olarak "capture-efficiency" sorusu ve muhtemelen en değerli tek metrik.

## REGIME
- **Trend/Range?** Hiç ayrı rejim olarak tanımlanmadı (yalnız bull/bear SPY-50SMA var).
- **High/Low volatility?** ATR-rejimi hesaplanabilir ama fiyat-rejiminden ayrı formal-kategori değil.
- **Bull/Bear?** Var (`FACT`), ama yalnız ikili, geçiş-dönemleri (transition) ayrı ele alınmıyor.
- **Sector-specific regime?** Bu tam sektör-trend bulgusu — `EVIDENCE zayıf`, tam-evrende doğrulanamadı.

## PORTFOLIO
Bkz. Persona 2 — concentration/redundancy/factor-exposure hiç test edilmedi, tekil-trade-optimizasyonundan hiç ayrılmadı.

## STATISTICS
- **Sample size?** Çoğu ana-tabloda yeterli (n=binlerce) ama kritik alt-kümelerde kırılgan (conviction A n=13, sektör n=142).
- **Confidence intervals?** Çoğu raporda yok — nokta-tahminler (mean/median) CI'sız sunuluyor.
- **Bootstrap?** Kısmen kullanıldı (bazı raporlarda) ama sistematik-standart değil.
- **Out-of-sample?** Var (IS/OOS split) ama tekrar-tekrar-bakılmış, muhtemelen kontamine.
- **Walk-forward?** Kısmen (train/validation split zaman-sıralı) ama gerçek rolling walk-forward değil.
- **Purged CV?** Hiç kullanılmadı `FACT`.
- **Multiple testing correction?** Hiç formal uygulanmadı `FACT` — binlerce config, hiç FDR/Bonferroni yok.
- **Parameter stability?** Kısmen incelendi (TP/SL komşu-değer-testi önerildi) ama sistematik uygulanmadı.

**War Room özet-hükmü:** Program istatistiksel-olgunluk açısından güçlü (IS/OOS, null-kontroller, honest-metrik ayrımı var) ama **iki temel eksik** her şeyin üstünde: (1) multiple-testing-correction hiç yok, (2) exit-alanının kendisi hiç gerçekten çeşitlendirilip test edilmedi — yalnız tek-exit-türünün parametreleri tarandı.

---

# UNKNOWN-UNKNOWN ENGINE

**30 soru (dünyanın en iyi quant/PM/behavioral/product/AI ekiplerinin FinPilot'u ilk kez görseydi soracağı):**

1. Bu sistemin "başarı" tanımı kim tarafından, ne zaman belirlendi — ve hâlâ doğru mu?
2. FinPilot'un rakipleri gerçekten aynı problemi mi çözüyor, yoksa biz yanlış rakip-setini mi kıyaslıyoruz?
3. Kullanıcı-tabanının kaçı gerçekten "yatırımcı," kaçı "meraklı-gözlemci" — bu ayrım hiç yapıldı mı?
4. ATR→MAE bulgusu, look-ahead'den arındırıldığında hâlâ ayakta kalır mı? (Collision-4'te işaretlendi — en kritik.)
5. FinPilot'un veri-sağlayıcı-fallback-oranı (yfinance'a düşme) sinyal-kalitesini sistematik mi bozuyor?
6. Şirketin kendi zaman/mühendislik-bütçesinin yüzde kaçı hâlâ "yeni TP/SL" tipi düşük-EV işlere gidiyor?
7. Eğer yarın regülasyon "Grade" gibi kategorik-dilleri yasaklarsa, ürün ne kadar hızlı adapte olabilir?
8. Kullanıcı FinPilot'u terk ettiğinde gerçek sebep nedir — hiç çıkış-anketi yapıldı mı?
9. Şirketin 12 ay sonra hâlâ var-olması için hangi 1-2 metrik gerçekten belirleyici?
10. "Edge yok" sonucu kesinleşirse, şirketin business-model'i hâlâ ayakta kalır mı?
11. FinPilot'un mevcut kullanıcıları, üründen "aldatıldıklarını" hissederlerse nasıl tepki verir?
12. Rakip bir ürün, FinPilot'un kendi NO-GO-raporlarını alıp "bakın, bu şirket kendi ürününün işe yaramadığını söylüyor" diye pazarlarsa ne olur?
13. Şirketin en değerli çalışanı/kurucusu yarın ayrılırsa, hangi bilgi (araştırma-tarihçesi, neden-null-çıktı) kaybolur — dokümantasyon yeterli mi?
14. FinPilot bugün kapansaydı, hangi varlık (kod, veri, marka, kullanıcı) başka bir şirkete satılabilir olurdu?
15. Kullanıcılar arasında "süper-kullanıcı" (yüksek-engagement) segmenti var mı, ne istiyorlar, kalanlardan farklı mı?
16. Piyasa-rejimi (şu anki ~%87-bull dönem) tersine dönerse, mevcut TÜM null-sonuçlar (edge-yok) da mı tersine döner, yoksa kalıcı mı?
17. FinPilot'un veri-gizliliği/kullanıcı-verisi-işleme süreci, gelecekteki bir "personal reasoning engine" vizyonuyla uyumlu mu (kullanıcı-verisi toplamaya hazır mı altyapı)?
18. Şirketin "araştırma-disiplini" iddiası, dışarıdan bağımsız bir denetçi tarafından doğrulanabilir mi (üçüncü-parti-audit)?
19. Kullanıcılar Grade'in ters-kalibre olduğunu öğrenirse (şeffaflık-politikası gereği açıklanırsa) güven artar mı azalır mı — hiç test edilmedi.
20. FinPilot'un en büyük maliyet-kalemi ne (veri, hesaplama, mühendislik, pazarlama) ve bu, seçilen stratejik-yönle uyumlu mu?
21. "Risk-hedefi" pivotu yapılırsa, mevcut marka/pazarlama-varlıkları (scanner-imajı) bir yük mü avantaj mı olur?
22. Kullanıcılar arasında gerçek-para-kaybı yaşayanlar var mı, bu deneyim hiç sistematik toplandı mı (kullanıcı-geri-bildirimi olarak)?
23. FinPilot'un mevcut kod-tabanının ne kadarı, "risk-odaklı-pivotta" hâlâ kullanılabilir — teknik-borç ne kadar?
24. Eğer aws-grant/positioning (FinSense/impact) resmi taahhüt haline geldiyse, bugünkü scanner-merkezli-çalışma bu taahhütle ne kadar tutarlı?
25. Kullanıcıların finansal-okuryazarlık-seviyesi ürün-tasarımını ne kadar etkiliyor — hiç segment-bazlı ölçüldü mü?
26. FinPilot'un Telegram/web dağıtım-kanalları, mesajın (dürüstlük/risk-odaklılık) taşınmasına uygun mu, yoksa "hızlı-sinyal" formatına mı zorluyor?
27. Şirketin decision-log'undaki NO-GO-kararlarının kaçı gerçekten *uygulandı* (kod/ürüne yansıdı) vs yalnızca *kaydedildi*?
28. Kullanıcı-tabanı büyürse (8.000-evren genişlemesi), mevcut null-sonuçlar ölçek-etkisiyle değişir mi (daha fazla veri = daha net null, ya da gizli-sinyal ortaya çıkar mı)?
29. FinPilot'un "dürüstlük" pazarlama-stratejisi, kısa-vadede kullanıcı-kaybına yol açarsa, şirket bu kısa-vadeli-maliyeti karşılayacak zamana/sermayeye sahip mi?
30. En basit olası açıklama gözden mi kaçıyor: belki FinPilot'un asıl sorunu strateji değil, **yanlış-pazarda-yanlış-zamanda** (küçük-cap-momentum, tükenmiş bir faktör) olmak — hiçbir yeniden-çerçeveleme bunu çözemez.

**Bu 30'dan yönü-tamamen-değiştirebilecek 10:**
1. #4 (ATR-look-ahead doğrulaması) — **en kritik, programın temelini sarsabilir.**
2. #16 (rejim-tersine-dönerse null-sonuçlar da değişir mi) — mevcut tüm "edge-yok" hükmünün rejim-bağımlı olabileceğini gösterir.
3. #10 (business-model edge-olmadan ayakta kalır mı) — stratejik-pivotun zorunlu mu tercih mi olduğunu belirler.
4. #6 (mühendislik-bütçesinin hâlâ düşük-EV işlere gitmesi) — organizasyonel-atalet sinyali.
5. #30 (yanlış-pazar-yanlış-zaman) — en radikal, en az ele alınan olası açıklama.
6. #19 (şeffaflığın kullanıcı-güvenine gerçek etkisi) — tüm "dürüstlük-moat" tezinin ampirik-temeli.
7. #2 (yanlış rakip-kıyası) — kategori-seçiminin kendisini sorgulatır.
8. #28 (ölçek büyürse null değişir mi) — 8.000-evren-genişleme kararını doğrudan etkiler.
9. #12 (rakip NO-GO-raporlarını silah yapabilir mi) — şeffaflık-stratejisinin risk-tarafı.
10. #23 (kod-tabanının pivotta yeniden-kullanılabilirliği) — pivot-maliyetinin gerçek büyüklüğü.

---

# EXPERIMENT FACTORY

## ENTRY EXPERIMENTS (10)
1. **[High]** 3-giriş-noktası ayrıştırması (close/open/close) — bkz. §0.
2. **[High]** Pullback-entry vs immediate-entry kıyası (günlük-proxy: kırmızı-gün-sonrası-giriş vs sinyal-günü-giriş).
3. **[Medium]** Confirmation-entry'nin (score_3) score_2'ye marjinal-katkısını cluster-robust CI ile yeniden test.
4. **[Medium]** Event-driven (earnings-sonrası) alt-küme IC testi (catalyst_factor kullanarak).
5. **[Low]** Multi-stage/kademeli giriş simülasyonu (yalnız günlük-veriyle yaklaşık).
6. **[Parked]** Regime-specific entry-kuralı (intraday veri gerektirir).
7. **[High]** Entry-delay duyarlılığı (1-2-3 bar gecikmeli giriş, drift ne kadar sönüyor).
8. **[Medium]** Relative-entry (sektöre-göre-erken/geç giriş) — sektör-trend bulgusuyla birleşik.
9. **[Low]** Gap-büyüklüğüne göre entry-filtrelemesi (büyük-gap'te giriş erteleme).
10. **[Parked]** Order-type simülasyonu (limit vs market) — execution-verisi gerektirir.

## EXIT EXPERIMENTS (10)
1. **[High]** Bariyersiz drift/half-life eğrisi (TP/SL olmadan kümülatif getiri).
2. **[High]** Time-exit vs fixed-barrier kıyası (sabit-gün-sayısında kapat vs bariyer-bekle).
3. **[Medium]** MFE-capture-efficiency (gerçekleşen exit, teorik-MFE'nin yüzde kaçını yakalıyor).
4. **[Medium]** Volatility-exit (ATR aniden genişlerse erken-çık) simülasyonu.
5. **[Low]** Trailing-stop (ATR-bazlı) vs sabit-SL kıyası.
6. **[Parked]** Opportunity-cost-exit (portföy-katmanı gerektirir).
7. **[Medium]** Thesis-exit proxy'si (rejim değişirse çık) — SPY-50SMA-flip'inde pozisyon kapatma testi.
8. **[High]** Random-entry + mevcut-exit kıyası (edge entry'de mi exit'te mi ayrıştırma — reframing-raporunun önerisi).
9. **[Low]** Momentum-decay-bazlı exit (RVOL sönerse çık).
10. **[Parked]** Portfolio-seviyesi exit (bir pozisyon kapatılırken sermaye başka-fırsata mı kayıyor).

## RANKING EXPERIMENTS (10)
1. **[High]** Reverse-ranking'in pre-registered, OOS+matched-control testi.
2. **[High]** PCA/VIF ile bağımsız-eksen-sayısı tespiti.
3. **[Medium]** Cross-sectional (günlük-kesit, market-nötr) rank-IC — mutlak-eşik yerine.
4. **[Medium]** Rank-stability (ardışık-gün otokorelasyonu).
5. **[Low]** Signal-decay eğrisi (skorun "tazeliği").
6. **[High]** Kalibrasyon-yeniden-deneme (yalnız risk-hedefinde, getiri değil).
7. **[Medium]** Extension/exhaustion ile skor-inversiyonu mekanizma-testi.
8. **[Low]** Skor-bileşenlerinin interaction-term (etkileşimli) etkisi.
9. **[Parked]** Entropi-bazlı bilgi-içeriği ölçümü (skorun kaç bit taşıdığı).
10. **[Medium]** Conviction-tier'ın küçük-n (A=13) genişletilmiş-örneklemde tekrar-testi.

## REGIME EXPERIMENTS (10)
1. **[High]** Gerçek-sektör-etiketiyle tam-evren sektör-trend testi (Meriç'in onayladığı, sıradaki somut adım).
2. **[High]** ATR-look-ahead düzeltmesi + IC yeniden-hesaplama (Collision-4'ün kritik testi).
3. **[Medium]** Bull/bear/transition (3-kategori) rejim-ayrıştırması.
4. **[Medium]** Volatilite-rejimi (yüksek/düşük-ATR) ile fiyat-rejiminin (bull/bear) çapraz-etkileşimi.
5. **[Low]** Regime-dengeli yeniden-örnekleme (bull/bear eşit-ağırlık) ile tüm ana-sonuçları yeniden-hesaplama.
6. **[Medium]** Sektör-görece-güç (S_rs) ile sektör-trend (S_trend) ayrımının tekrar-doğrulanması.
7. **[Parked]** Makro-rejim (faiz/enflasyon) katmanı — yeni veri gerektirir.
8. **[Low]** Rejim-geçiş-dönemlerinin (flip-sonrası N gün) ayrı karakterize edilmesi.
9. **[Medium]** Likidite-rejimi (piyasa-geneli likidite-daralması) katmanı.
10. **[Parked]** Event-rejimi (earnings-sezonu vs normal-dönem) ayrımı.

## PORTFOLIO EXPERIMENTS (10)
1. **[High]** Concentration-kısıtlı vs kısıtsız portföy Sharpe-kıyası.
2. **[High]** ATR-bazlı position-sizing'in portföy-varyansına etkisi.
3. **[Medium]** POQ (Portfolio Opportunity Quality) formülasyonu ve pilot-testi.
4. **[Medium]** Aynı-gün-açılan-sinyallerin gerçekleşen-korelasyonu.
5. **[Low]** Turnover-optimize rebalans-sıklığı taraması.
6. **[Medium]** Investable-universe'de (capacity-filtreli) paralel portföy-simülasyonu.
7. **[Low]** Sektör-max-ağırlık kısıtı taraması.
8. **[Parked]** Factor-exposure (market/sektör/momentum-beta) ayrıştırması.
9. **[Medium]** CVaR/tail-katkı zorunlu-raporlama altyapısı.
10. **[Low]** Redundancy-filtreli top-N (yüksek-korelasyonlu isimleri ele).

## MARKET MEMORY EXPERIMENTS (5)
1. **[Medium]** Küçük-ölçekli "vaka-tabanı" prototipi: her GO/NO-GO kararı kalıcı+aranabilir kayıt.
2. **[Low]** Geçmiş benzer-kurulumların ("bu daha önce oldu mu") arama-arayüzü prototipi.
3. **[Parked]** Kullanıcı-katkılı market-memory (kolektif) — moderasyon-riski yüksek.
4. **[Low]** NO-GO-kararlarının otomatik eğitim-içeriğine dönüştürülmesi pilotu.
5. **[Medium]** Market-memory'nin gerçekten "kopyalanamaz" olup olmadığının rakip-analiz-testi (Devil's Advocate #6'ya cevap).

## PRODUCT EXPERIMENTS (5)
1. **[High]** Kullanıcı-motivasyon-anketi (Collision-6'nın çözümü — en yüksek-EV, en düşük-maliyet).
2. **[Medium]** Accountability/şeffaflık-özelliğinin (NO-GO-görünürlüğü) küçük-grup pilotu.
3. **[Medium]** Grade-kapalı vs Grade-açık A/B testi.
4. **[Low]** Segment-bazlı arayüz (acemi/uzman) A/B.
5. **[Parked]** B2B/kurumsal-kanal keşif-görüşmeleri.

## LEARNING/BEHAVIOR EXPERIMENTS (5)
1. **[Medium]** Top-10-listesinin ve renk-kodlamasının davranışsal-etkisi (kullanıcı "liste-dışı"nı nasıl yorumluyor).
2. **[Medium]** Retrieval-quiz'li Ledger vs statik Ledger 30-gün-retention kıyası.
3. **[Low]** Case-based (gerçek NO-GO'lar) eğitim-modülü pilotu.
4. **[Low]** Kayıp-senaryosu zorunlu-gösteriminin loss-aversion-etkisi.
5. **[Parked]** Kullanıcı-karar-günlüğü (deliberate-practice) tam-döngü prototipi.

---

## EXPERIMENT SCORECARD (en yüksek-öncelikli 8 deney)

| Alan | #1 ATR Look-Ahead Düzeltmesi | #2 Giriş-Noktası Ayrıştırması | #3 Bariyersiz Drift Eğrisi | #4 Sektör Gerçek-Etiket Tam-Evren | #5 Reverse-Ranking Testi | #6 Concentration-Kısıtlı Portföy | #7 Kullanıcı-Motivasyon Anketi | #8 Random-Entry+Mevcut-Exit |
|---|---|---|---|---|---|---|---|---|
| **Hypothesis** | ATR→MAE kısmen look-ahead artefaktı | Edge sinyal-close'da var, açılışta kayboluyor | Drift 5 günden kısa ömürlü | Sektör-trend tam-evrende de geçerli | Skor sistematik-ters, tersi fade-edge | Kısıt edge'siz bile Sharpe'ı artırır | Kullanıcı sinyal değil güven/hız istiyor | Edge entry'de değil exit'te |
| **Baseline** | Mevcut ATR (aynı-gün) IC −0.51 | Mevcut ertesi-open sonucu | Mevcut 5-gün sabit horizon | %24-doğru proxy sonucu (null) | Mevcut composite IC~0 | Mevcut kısıtsız top-N | Yok (hiç sorulmadı) | Mevcut composite-entry sonucu |
| **Variable** | ATR hesaplama-penceresi (look-ahead var/yok) | Giriş-noktası (close/open/close) | Holding-süresi (bariyersiz) | Sektör-etiket-kaynağı (proxy/gerçek) | Ranking yönü (normal/ters) | Concentration-kısıtı (var/yok) | Kullanıcı-segment | Entry-kaynağı (sinyal/random) |
| **Control** | Önceki-gün-kapanışına-kadarki ATR | — | — | 143-sembol gerçek-etiket | Matched-random | Kısıtsız top-N | — | Sabit-exit, random-entry |
| **Test** | Aynı-gün (mevcut) ATR | 3 paralel ölçüm | t+1..t+10 kümülatif | Tüm-evren gerçek-etiket | Ters-composite top-20% | Kısıtlı top-N | Anket-sonucu | Mevcut-entry, sabit-exit |
| **Dataset** | price_cache + edge_recheck | price_cache + edge_recheck | price_cache + SPY/sektör ETF | EODHD fundamentals (yeni) + edge_recheck | edge_recheck | edge_recheck + portföy-sim | Kullanıcı-tabanı | edge_recheck |
| **Sample size** | ~53.754 satır | ~53.754 satır | ~53.754 satır | ~53.754 satır (tam-evren) | ~53.754 satır | 36+ config | n=kullanıcı-sayısı | 799 (entry_ok) |
| **Evaluation metric** | rank-IC farkı | excess-return farkı (3 nokta) | eğrinin tepe-noktası | win%/medRet, IS/OOS | excess-return, OOS+robustluk | Sharpe/CVaR farkı | segment-dağılımı | excess-return farkı |
| **Leakage risk** | Yüksek (bu testin amacı bu) | Düşük | Düşük | Orta (yeni veri-kaynağı doğrulaması gerek) | Orta (yine-mevcut-veri) | Düşük | Yok | Düşük |
| **Multiple testing risk** | Düşük (tek test) | Düşük (3 karşılaştırma) | Düşük | Orta (yine mevcut-veriye-bakma) | Yüksek (yine-eski-veriye-bakma riski) | Düşük | Yok | Düşük |
| **Expected information gain** | **Çok yüksek** — programın temelini doğrular/çürütür | **Çok yüksek** — mekanizma-ayrıştırması | Yüksek | Yüksek (tek OOS-tutarlı ipucunun kaderi) | Orta-yüksek | Orta | Yüksek (stratejik-yön belirler) | Yüksek (mekanizma-ayrıştırması) |
| **Cost** | Düşük (mevcut veri) | Düşük (mevcut veri) | Düşük (mevcut veri) | Orta (yeni veri-tedariği+ağ) | Düşük (mevcut veri) | Düşük (mevcut sim) | Düşük (anket-altyapısı) | Düşük (mevcut veri) |
| **Kill criterion** | IC \|<0.2\| düşerse → risk-hedefi de kanıtsız | Fark yoksa → giriş-zamanlaması sorunu değil | Düz-eğri → hiçbir exit-kuralı kurtarmaz | Replike-olmazsa → koşullu-edge terk | OOS-tutarsızsa → gürültü, terk | Fark yoksa → POQ terk | — (bilgilendirici, öldürmez) | Fark yoksa → edge her ikisinde de yok |

**Not:** #1 (ATR look-ahead) ve #7 (kullanıcı-anketi), maliyeti en düşük ve **expected-information-gain'i en yüksek** ikili — Kural'ın vurguladığı "düşük-maliyet-yüksek-öğrenme" ilkesine tam uyuyor. İkisi de 30 gün içinde bitebilir.

---

# AŞAMA 3 — CONVERGENCE

Skorlar (1-10, nitel-değerlendirmeden **sonra**, tek-başına-karar-mekanizması değil):

| Bahis | Impact | Evidence | Differentiation | Testability | Cost(düşük=iyi→ters-skorlanmadı, ham) | Time-to-Learn | Risk | Reversibility |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| Risk/Kalibrasyon Pivotu | 9 | 8 | 7 | 8 | 4 | 6 | 3 | 8 |
| Giriş-Zamanlaması+Drift Diagnostiği | 8 | 3 (henüz test-öncesi) | 5 | 10 | 1 | 9 | 1 | 10 |
| ATR Look-Ahead Doğrulaması | 10 (temel-sarsıcı) | 2 (henüz test-öncesi) | 3 | 10 | 1 | 9 | 1 | 10 |
| Gerçek-Sektör Koşullu-Edge | 7 | 5 | 6 | 7 | 5 | 5 | 4 | 7 |
| Portföy/POQ Pivotu | 7 | 4 | 6 | 7 | 4 | 6 | 3 | 7 |
| Market Memory / Araştırma-Kurumu Kimliği | 6 | 2 (vizyon, kanıt-öncesi) | 8 | 5 | 5 | 3 | 5 | 6 |

**Nitel-okuma (skorların ötesinde):** ATR-Look-Ahead-Doğrulaması ve Giriş-Zamanlaması-Diagnostiği en düşük-maliyetli, en yüksek-tersinirlik, en kısa-öğrenme-süreli ikili — ama Impact'leri farklı karakterde: biri (ATR) **mevcut-en-güçlü-bulguyu tehdit ediyor** (yıkıcı-ama-gerekli), diğeri (giriş-zamanlaması) **yeni-bir-bulgu-kapısı açabilir** (yapıcı). İkisi birlikte, aynı ay içinde, aynı veriyle koşulabilir — bu yüzden ayrı bahisler değil, **tek "Foundational Integrity Sprint"** olarak birleştiriliyor aşağıda.

## BIG BET #1 — Foundational Integrity Sprint (ATR Look-Ahead + Giriş-Zamanlaması + Drift)

**Hypothesis:** Programın tek kanıtlanmış bulgusu (ATR→MAE) kısmen look-ahead-artefaktı olabilir VE mevcut "edge yok" hükmü kısmen yanlış-ölçüm-noktasından (ertesi-açılış) kaynaklanıyor olabilir. Bu ikisi doğrulanmadan hiçbir stratejik-pivot güvenilir bir temele oturmaz.

**Why It Matters:** Bu, tüm önceki iki belgenin (10-perspektif + bu belge) üzerine inşa edildiği zeminin kendisini sorguluyor. Eğer ATR-bulgusu artefaktsa, "risk-hedefine pivot" tezi de çöker. Eğer giriş-zamanlaması sorunsa, "alfa yok" hükmü de kısmen yanlış-ölçümdür.

**Evidence:** `UNKNOWN` — hiçbiri hiç test edilmedi. Bu tam da "en yüksek expected-information-gain, en düşük-maliyet" deneyi.

**Unknowns:** ATR'nin gün-içi mi gün-sonu mu hesaplandığı kod-seviyesinde henüz doğrulanmadı; giriş-noktası-farkının pratik-anlamda (maliyet-sonrası) trade-edilebilir olup olmadığı.

**What Could Prove It Wrong?** ATR look-ahead-düzeltmesi sonrası IC değişmezse (|IC|>0.4 kalırsa) → bulgu sağlam. 3-giriş-noktası arasında anlamlı-fark çıkmazsa → giriş-zamanlaması-hipotezi çürür (bu da değerli — "gerçekten alfa yok" hükmünü güçlendirir).

**Minimum Test:** (a) ATR'yi yalnız önceki-gün-kapanışına-kadarki veriyle yeniden hesapla, IC'yi kıyasla. (b) 3 giriş-noktasından t+1..t+10 kümülatif excess-getiri eğrisi çiz.

**Required Data:** Yalnız mevcut price_cache — yeni veri gerekmiyor.

**Expected Learning:** Ya mevcut-tek-bulgu doğrulanır (temel sağlamlaşır) ya da çürür (programın gerçekten sıfırdan başlaması gerektiği netleşir) — ikisi de kritik.

**Failure Learning:** ATR-bulgusu çürürse: programın hiçbir doğrulanmış bulgusu kalmaz, ama bu en azından **dürüst bir sıfır-nokta** verir. Giriş-zamanlaması fark-yaratmazsa: "alfa yok" hükmü zamanlama-artefaktı değil, gerçekten yapısal — bu da pivotu (risk-odaklılık) daha da güçlü haklı-çıkarır.

**Decision:** **Continue** — bu, tüm programın önündeki tek en-yüksek-öncelikli adım.

---

## BIG BET #2 — Risk/Kalibrasyon Pivotu (Getiri-Hedefinden Risk-Hedefine)

**Hypothesis:** FinPilot'un savunulabilir ürün-temeli getiri-tahmini değil, kalibre risk/belirsizlik-tahminidir.

**Why It Matters:** Tek rejim-dayanıklı, OOS-tutarlı bulgu bu. Aynı zamanda Grade'in kanıtlı-ters-kalibrasyon riskini de çözüyor (kalibre-olasılık, kategori-Grade yerine).

**Evidence:** `EVIDENCE` — ATR→MAE IC −0.51, bull/bear'da aynı yön (ama bkz. Big Bet #1 — bu bulgu doğrulanma-bekliyor).

**Unknowns:** Kullanıcılar risk-odaklı bir ürünü "daha az heyecanlı" bulup terk eder mi; risk-tahmininin kendisi ne kadar kalibre (Brier/ECE hiç risk-hedefi için ölçülmedi, yalnız getiri-hedefi için ölçüldü).

**What Could Prove It Wrong?** Big Bet #1 ATR-bulgusunu çürütürse, bu bahis de otomatik-geçersiz olur (bağımlılık kasıtlı). Risk-hedefinin kendi kalibrasyonu (Brier/ECE) kötü çıkarsa da geçersiz.

**Minimum Test:** Risk-hedefi için ayrı Brier/ECE hesapla (mevcut yalnız getiri-hedefi için var); küçük kullanıcı-grubuna Grade yerine risk-kartı sun, tepkiyi ölç.

**Required Data:** Mevcut edge_recheck + kullanıcı-pilot-grubu.

**Expected Learning:** Risk-hedefinin ürünleştirilebilir kalitede olup olmadığı.

**Failure Learning:** Risk-tahmini de kalibre-değilse, programın **hiçbir** ürünleştirilebilir sinyali kalmaz — bu, Devil's Advocate #8'i (edge yapısal-imkânsız) doğrular ve tam bir kategori-değişimi (davranış-koçluğu, saf-şeffaflık-ürünü) zorunlu kılar.

**Decision:** **Continue, Big Bet #1'e bağımlı** — #1 tamamlanmadan başlatılmamalı.

---

## BIG BET #3 — Gerçek-Sektör Koşullu-Edge Doğrulaması

**Hypothesis:** Sektör-trend katmanı (sembol-bullish × sektör-yükseliş) gerçek sektör etiketiyle tam evrende de OOS-tutarlı kalır.

**Why It Matters:** Programın tek koşullu-getiri-ipucu; doğrulanırsa ilk gerçek "yön" bulgusu olur (risk değil, getiri).

**Evidence:** `EVIDENCE zayıf` — 143-sembolde güçlü, %24-doğru proxy'yle tam-evrende replike olmadı.

**Unknowns:** Gerçek-sektör-etiketle de replike olur mu, yoksa 143-sembol küçük-n tesadüfü mü.

**What Could Prove It Wrong?** Gerçek etiketle tam-evrende IS/OOS işaret-tutarsızsa → küçük-n tesadüfü, terk.

**Minimum Test:** EODHD fundamentals'tan (veya benzeri) gerçek GICS-sektör çek, tam-evrende sektör-trend testini tekrarla.

**Required Data:** Yeni veri-tedariği (ağ-erişimi gerektirir, kullanıcı zaten bunu onaylamıştı).

**Expected Learning:** Koşullu-edge var mı, yoksa risk-hedefi tek kanıtlanmış-alan olarak mı kalır.

**Failure Learning:** Replike-olmazsa, programın "yalnız risk, hiçbir yön-bulgusu yok" hükmü kesinleşir — bu da net ve kullanışlı bir sonuç.

**Decision:** **Continue** — kullanıcı zaten bu yönde ilerlemeyi onaylamıştı, bağımsız-koşulabilir (Big Bet #1/#2'yi beklemez).

---

# AŞAMA 4 — SON RAPOR

## 1. Executive Summary (10 en önemli keşif)
1. Programın tek kanıtlanmış bulgusu (ATR→MAE) **hiç look-ahead-audit'inden geçmedi** — en kritik açık boşluk.
2. Giriş-zamanlaması (close/open/close) hiç ayrıştırılmadı — "edge yok" hükmü kısmen yanlış-ölçüm-noktası olabilir.
3. Exit-araştırması aslında yalnız **tek-exit-türünün** (fixed-barrier) parametre-taraması — gerçek alternatif hiç test edilmedi.
4. Multiple-testing-correction hiç formal uygulanmadı — binlerce config, hiç FDR/Bonferroni yok.
5. entry_ok/conviction'ın iki-bağımsız-inversiyonu hâlâ mekanizmasız (extension/exhaustion hipotezi doğrulanmadı).
6. Tekil-sinyal-kalitesi ile portföy-sonucu arasındaki uçurum (başa-baş) hiç portföy-katmanı-önce-tasarlanarak kapatılmaya çalışılmadı.
7. Sektör-trend, programın tek koşullu-getiri-ipucu ama tam-evrende doğrulanmadı (yalnız %24-doğru proxy'yle test edildi).
8. Grade bilinen-biçimde-ters-kalibre ve hâlâ düzeltilmeden kullanımda — en acil güven-riski.
9. Kullanıcının gerçekte ne istediği (sinyal/eğitim/güven/hız/hesap-verebilirlik) hiç doğrudan sorulmadı.
10. En yüksek expected-information-gain'li iki deney (#ATR-look-ahead, #giriş-zamanlaması) sıfır-yeni-veri ile 30 gün içinde koşulabilir — ama henüz koşulmadı.

## 2. Biggest Blind Spots (20)
(Bkz. §Divergence, her personadan 10'ar madde — en kritik 20'si: ATR-look-ahead, giriş-zamanlaması, exit-çeşitlendirmesi-eksikliği, multiple-testing, survivorship/PIT-audit-eksikliği, extension/exhaustion-mekanizması, POQ/portföy-önce-tasarım, sektör-tam-evren-doğrulaması, Grade-düzeltme-gecikmesi, kullanıcı-motivasyon-bilgisizliği, top-10/renk-kodlama-davranışsal-etkisi, fırsat-ömrü/opportunity-decay, gap-riski-ayrı-ölçüm-eksikliği, tail-decomposition-eksikliği, dedup-politika-duyarlılığı, fallback-veri-kalite-etkisi, aynı-gün-korelasyon-riski, capacity-önce-sıralama-eksikliği, market-memory'nin-gerçek-moat-olup-olmadığı, temel-tez-periyodik-yeniden-oylama-eksikliği.)

## 3. Assumptions We Should Stop Believing
Yüksek-skor=yüksek-getiri · entry_ok/conviction kalite-göstergesi · TP/SL doğru abstraction · sabit-%0.55-maliyet gerçekçi · aritmetik-ortalama doğru metrik · locked-holdout hâlâ temiz · composite-skor kalibre-okunabilir · tekil-sinyal-expectancy portföye-otomatik-taşınır.

## 4. Assumptions Worth Testing (henüz terk edilmemiş)
ATR→MAE gerçek (look-ahead-audit bekliyor) · sektör-trend gerçek (tam-evren-doğrulama bekliyor) · reverse-ranking gerçek fade-edge olabilir · Grade kaldırılırsa kullanıcı-terk-riski · market-memory gerçek moat olabilir · dürüstlük/şeffaflık ticari-farklılaştırıcı olabilir.

## 5. New Strategic Directions (10)
Risk/kalibrasyon-pivotu · giriş-zamanlaması+drift-mimarisi · portföy-önce-tasarım (POQ) · gerçek-sektör-koşullu-edge · reverse-ranking-fade-adayı · hypothesis/experiment-engine (AI'ın yeni rolü) · market-memory-pilotu · accountability/şeffaflığın dış-yüzeye-taşınması · davranış-koçluğu-alternatifi (Devil's Advocate #11/#20) · periyodik temel-tez-yeniden-oylama-ritüeli.

## 6. Quant Research Reframing
Getiri-hedefi ikincil, risk-hedefi birincil olana kadar yeni-threshold-taraması yok. Her yeni-iddia FACT/EVIDENCE/HYPOTHESIS/SPECULATION/UNKNOWN etiketiyle gelir. Multiple-testing-correction ve look-ahead-audit her deneyde zorunlu-standart olur.

## 7. Product Reframing
Signal/Research/Education/Confidence/Speed/Explanation/Understanding/Decision-support/Habit/Accountability bileşenleri ayrı ölçülür, tek-arayüzde-karıştırılmaz. Accountability (zaten güçlü) dış-yüzeye taşınır.

## 8. Data Reframing
PIT-universe-doğrulaması, survivorship-audit'i, corporate-action-audit'i, dedup-duyarlılık-testi — hepsi zorunlu, retroaktif uygulanmalı.

## 9. AI Reframing
Prediction → hypothesis-generation + adversarial-test + market-memory-küratörlüğü. Autonomous-loop ve event-intelligence (LLM-haber-analizi) şimdilik parked (hype-riski yüksek).

## 10. Market Memory
`HYPOTHESIS` — gerçek moat olabilir ama Devil's Advocate'in itirazı (kolayca-kopyalanabilir) ciddiye alınmalı; küçük-pilotla test edilmeden iddia edilmemeli.

## 11. Decision Process Quality
`UNKNOWN` şu an — hiç ölçülmüyor. Ölçülebilir hedef önerisi: kullanıcı-karar-günlüğü + 30/60/90-gün-sonra-kendi-tahminiyle-kıyaslama.

## 12. 30+ New Experiments
Bkz. §Experiment Factory (72 deney, 8 kategori, önceliklendirilmiş).

## 13. 3–5 BIG BETS
Bkz. §Convergence: (1) Foundational Integrity Sprint, (2) Risk/Kalibrasyon Pivotu, (3) Gerçek-Sektör Doğrulaması.

## 14. Kill List
Yeni TP/SL-taraması · getiri-hedefini birincil-tutmak · Grade'i düzeltmeden-kullanmaya-devam · sabit-maliyet-varsayımıyla-sonuç-ilan-etmek · P0'ı-promotion-gate-yapmak · autonomous-AI-loop (şimdilik) · event-intelligence/LLM-haber-analizi (şimdilik).

## 15. 90-Day Research Roadmap
**Gün 1-30 (Foundational Integrity):** ATR-look-ahead-audit + 3-giriş-noktası-testi + bariyersiz-drift-eğrisi + kullanıcı-motivasyon-anketi — hepsi düşük-maliyet, sıfır-yeni-veri.
**Gün 31-60 (Koşullu-Doğrulama):** Gerçek-sektör-etiketle-tam-evren-testi + concentration-kısıtlı-portföy-simülasyonu + reverse-ranking-pre-registered-testi.
**Gün 61-90 (Karar-Noktası):** Big Bet #1/#2/#3 sonuçlarına göre resmi git/no-git kararı; risk-hedefi doğrulandıysa Grade→kalibre-risk-kartı geçişinin küçük-pilotu başlar; doğrulanmadıysa davranış-koçluğu/saf-şeffaflık alternatifleri ciddi-değerlendirmeye alınır.

---

# FİNAL ÇIKTI

## A. STRATEGIC MAP (FinPilot'un olası gelecekleri)
```
                    [Foundational Integrity Sprint]
                     (ATR-audit + giriş-zamanlaması)
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
     ATR-bulgusu DOĞRULANIR          ATR-bulgusu ÇÜRÜR
              │                               │
              ▼                               ▼
   Risk/Kalibrasyon Pivotu           Programın hiçbir
   (Research Platform vizyonu)       kanıtlanmış-bulgusu kalmaz
              │                               │
              ▼                               ▼
   + Sektör-doğrulama başarılıysa:   Davranış-Koçluğu /
   Koşullu-edge de eklenir           Saf-Şeffaflık-Ürünü
   → "Dürüst Araştırma Kurumu"       (tamamen farklı tez)
     (en gerçekçi 12-ay vizyonu)
```

## B. RESEARCH MAP (test edilmesi gereken hipotezler ve deneyler)
Öncelik-sırası: **Foundational Integrity (Big Bet #1)** → **Risk/Kalibrasyon (Big Bet #2, #1'e bağımlı)** paralelinde **Sektör-Doğrulama (Big Bet #3, bağımsız)** → 90-gün-roadmap'in gün-61-90 karar-noktasında sonuçlara göre dallanma. Tam deney-listesi §Experiment Factory (72 deney), en yüksek-öncelikli-8'i §Experiment Scorecard'da.

## C. BIG BETS (özet)

| Bahis | Neden şimdi? | Kanıt | Bilmediğimiz | Nasıl test | Ne zaman öldür |
|---|---|---|---|---|---|
| #1 Foundational Integrity Sprint | Her şeyin temeli; sıfır-yeni-veri, 30-günde biter | `UNKNOWN`, test-öncesi | ATR gerçekten look-ahead mi, giriş-zamanlaması fark yaratır mı | ATR yeniden-hesapla + 3-nokta-drift-eğrisi | IC \|<0.2\| olursa / fark yoksa |
| #2 Risk/Kalibrasyon Pivotu | Tek savunulabilir, rejim-dayanıklı bulgu | `EVIDENCE` (Big Bet#1'e bağımlı) | Kullanıcı risk-odaklı ürünü nasıl karşılar | Küçük-pilot + risk-hedefi Brier/ECE | Risk de kalibre-değilse |
| #3 Gerçek-Sektör Doğrulaması | Programın tek koşullu-getiri-ipucu, bağımsız-koşulabilir | `EVIDENCE zayıf` | Gerçek-etiketle replike olur mu | EODHD fundamentals + tam-evren-tekrar | IS/OOS tutarsızsa |

---

## SON SORU

**"10 uzmanın 8'i aynı şeyi söylüyorsa, bu gerçek consensus mu, ortak-kör-nokta mı?"**

En net örnek: hem Quant, hem Data, hem Risk, hem Microstructure — dördü de bağımsız olarak **"giriş-zamanlaması hiç test edilmedi"** dedi. Bu ya gerçekten kritik bir boşluk ya da hepsinin aynı zımni-varsayımı (günlük-bar-yeterli) paylaşmasından kaynaklanan ortak-körlük. Ayırt etmenin tek yolu: **Big Bet #1'i koşmak.** Eğer sonuç "fark yok" çıkarsa, bu dörtlü-consensus bir kör-nokta değil, gerçekten-yanlış-bir-sezgiymiş demektir — ki bu da değerli bir öğrenme.

**"FinPilot'u bugün sıfırdan kursaydık, neyi tamamen farklı yapardık?"**

Skor-üretmeden önce **audit-üretirdik.** Mevcut sıralama tersti: önce binlerce config tarandı, sonra (bu iki belgede) audit-eksiklikleri fark edildi. Sıfırdan kursak: ilk 30 gün hiçbir strateji yazılmaz, yalnız look-ahead/survivorship/PIT-audit altyapısı kurulur — ve **hiçbir bulgu, bu audit'ten geçmeden "kanıt" sayılmaz.** Bu, tek-cümlelik-fark: *disiplin sona değil, en başa konur.*
