# R11 — Hipotez Backlog'u

| Alan | Değer |
|---|---|
| Başlık | R11 — Hipotez Backlog'u (WP-12 + WP-14 girdisi) |
| Versiyon | v1 |
| Tarih | 2026-10-19 |
| Durum | DRAFT — Level A araştırma çıktısı; karar değildir |
| HEAD | 93ae83c (branch `review/pending-2026-10-07`) |
| Rol | Quant Research Lead — sentez (alt ajan iskeleti oluşturduktan sonra üç denemede ağ hatası verdi; içerik orkestratör tarafından yazıldı) |
| Kapsam | R0–R9 bulgularından türeyen test edilebilir hipotez kartları, "şimdi değil" tablosu, 30 günlük plan adayları. Kod çalıştırılmadı (orkestratörün salt okunur profilleri hariç). |
| Girdiler | R0, R2, R3, R4, R5, R6, R7, R8, R9 ve R10 (bu klasör). Bu belge Red-Team sonrası sentezdir; bağımsız kör doğrulama değildir. Orkestratör kontrolleri: `data/finpilot.db` (salt okunur) ve `data/shadow/scan_shadow.jsonl` profili |
| Eşik notu | Aşağıdaki tüm başarı/başarısızlık eşikleri **PROPOSED — insan onayı gerekir; kilitli değil** (D7: sayısal OOS eşikleri veri gelene kadar ertelendi). |
| OOS notu | D7 (2026-10-16) gereği mevcut hiçbir veri seti out-of-sample değildir; bağımsız doğrulama yalnız ileriye dönük yapılabilir. |

## 1. Özet

- **Kapsam uyarısı:** R6/R7/R9 farklı kilit yorumları kullandı; bunların yeni sonuç istatistikleri araştırma kararı için karantinadadır (R12 §1). Bu kartlar yeniden hesaplama yetkisi vermez. Erişim kapsamı insan tarafından çözülmeden yeni sonuç analizi yapılmaz.
- Backlog 14 karttan oluşur: 5 **geçerlilik** (P0/P1), 5 **sıralama/seçim**, 3 **strateji ailesi**, 1 **tarama performansı** kartı.
- En yüksek öncelik mevcut kanıtın kendisini düzeltmektir: etiket tarih tabanı (HYP-01), aynı-bar/gap kuralları (HYP-02), geç kohort (HYP-03). Bunlar çözülmeden arşiv üzerinde yeni strateji testi yapmak, bozuk bir ölçüt üzerinde çoklu test yükünü artırır.
- Üç kart (HYP-08, HYP-09, HYP-05'in kayıt kısmı) **sonuç verisi gerektirmez**; kilit veya D7 kısıtına takılmadan hemen yapılabilir.
- "Doğru hisseleri seçiyor muyuz?" sorusunun tek doğrudan testi HYP-06'dır. Gölge defter (118.338 satır, 702 tarama, 2026-07-08 – 2026-10-16) uygun alanları taşır, ancak tamamı 2026-05-21 sonrasıdır; kilit kapsamı insan tarafından netleşmeden (F-PRF-00) sonuç hesaplanmamalıdır.
- Beş strateji ailesi ve iki eski araştırma hattı "şimdi değil" tablosundadır; gerekçe eksik veri veya mevcut olumsuz kanıttır.

## 2. Kanıt temeli

| ID | Bulgu (tek satır) | Etiket | Rapor |
|---|---|---|---|
| B11 / ENX-08 | Çözücü `signal_date`'i önce `ts`'den (arşive yazılma zamanı) alıyor (`scripts/resolve_open_signals.py:331`); saklanan etiketler `ts` çapasıyla %98,3, sinyal tarihi çapasıyla %69,1 yeniden üretiliyor | VERIFIED / REPRODUCED | R10, R6 |
| F-PRF-07 | Toplam brüt bariyer getirisinin %65,9'u 5–145 gün geç yazılan 1.616 satırdan; zamanında yazılan 3.590 satırda ortalama +%0,197, CI [−0,055; +0,461] | MEASURED | R7 |
| INT-08 | ≥4 gün geç yazılan 1.639 satırlık tek kohortta brüt kazanma payı farkı +0,125 [0,046; 0,202] | SUPPORTED | R9 |
| INT-03 / ENX-05 | Çözücü aynı barda TP'yi önce sayar ve gap'te seviye fiyatından çıkar; `scanner/labeling.py` SL'yi önce sayar | SUPPORTED | R9, R6 |
| ENX-10 | Kayıpların %32,7'si gap-through-stop; kazançların %12,6'sı aynı-bar belirsiz (günlük bar yaklaşımı) | MEASURED (yaklaşık) | R6 |
| ENX-11 | Arşivde yalnız 6 satır `entry_ok=True`; 591 tekrar (sembol, sinyal tarihi) satırı | MEASURED | R6 |
| F-PRF-08 / INT-09 | 5 USD altı 344 satır (%6,6) toplamın ≈%56'sı; TP/SL mesafesi ≈5 kat geniş | MEASURED / SUPPORTED | R7, R9 |
| SCR-01 | Yayın sırası: grade → `execution_confidence` → `conviction_prob` → `ranking_score` (= `legacy_quality_score`); `composite_score` sırayı belirlemiyor | SUPPORTED + MEASURED | R5 |
| SCR-05 | Skor → getiri monotonluğu önceki çalışmalarda desteklenmiyor; fiili sıra alanı için kanıt yok | PRIOR | R5 |
| SCR-03 | Composite satır bayraklarıyla %99,88, gözlenen bayraklarla %55,7 yeniden üretiliyor; `legacy_quality_score` yeniden kurulamıyor (`atr_pct` kalıcı değil) | REPRODUCED / NOT_MEASURABLE | R5 |
| SCR-04 | Composite 85 farklı değer; top-50 eşitlik payı medyan 0,78; açık tie-break yok | MEASURED | R5 |
| F-FRM-01 | `volume_spike`, `price_momentum`, `trend_strength` hem `filter_score` içinde hem tek tek sayılıyor; her biri rejimle eşit ağırlıkta | REPRODUCED | R4 |
| F-FRM-10 | Kenet kalıbı NaN'ı üst sınıra eşliyor (`compute_recommendation_strength(nan)` = 100) | REPRODUCED | R4 |
| F-DQ-08 | Alpaca barları `feed="iex"`; 6 büyük hissede `dollar_adv` konsolide tahminin %1,54–%3,85'i; `liquidity_ok` False 1.352/1.518 | MEASURED / SUPPORTED | R3 |
| F-DQ-03 | Skorlanan 1.518 satırın tamamı `partial`; `spread_bps` her satırda eksik | MEASURED | R3 |
| PERF-02/05/07 | Onarım her sembol için üç zaman dilimini yeniden çekiyor; `fast_info.last_price` ek 1 yıllık `history` isteği tetikliyor ve hız sınırlayıcıda sayılmıyor | SUPPORTED | R8 |

## 3. Hipotez kartları

### A. Geçerlilik (mevcut kanıtı geçersiz kılabilecekler)

#### HYP-01 — Etiket tarih tabanı yanlılığı (P0)
- **Hipotez:** Bariyer etiketleri payload `signal_date` ve sinyal anı `entry_price` ile aynı kural setinden yeniden üretildiğinde, geç yazılan satırların ortalama brüt bariyer getirisi düşer ve arşiv ortalaması +%0,3984'ten anlamlı ölçüde aşağı iner.
- **Motivasyon:** Çözücü penceresi `ts`'den başlıyor, giriş fiyatı sinyal anından geliyor; geç satırlarda ikisi farklı günlere ait.
- **Mevcut kanıt:** B11, ENX-08, F-PRF-03, F-PRF-07. R10'un yerel günlük-bar yeniden oynatması (yaklaşık) geç satırlarda +%0,868 → +%0,403 düşüş gösteriyor; ancak bu araç zamanında yazılan satırlarda saklanan etiketle yalnız %83,8 uyuşuyor.
- **Gerekli veri:** `data/price_cache` (mevcut; R6'da 1.118 dosya kullanıldı, 592 geçersiz bar atlandı). Ağ gerekmez.
- **Baseline:** Saklanan etiketler (v1).
- **Ölçüt:** v2 − v1 ortalama ve medyan farkı (sinyal günü kümelenmiş bootstrap); satır bazında durum değişim matrisi (win↔loss).
- **Maliyet modeli:** Uygulanmaz; etiket doğruluğu testidir. Sonuçlar brüttür.
- **Riskler:** Fiyat önbelleği vintaj/ayarlama farkları (F-DQ-06); günlük barda gün içi sıra bilinmez.
- **Test tasarımı:** (1) Araç doğrulaması: zamanında yazılan satırlarda yeniden oynatma ↔ saklanan etiket uyuşması. (2) Doğrulanmış araçla geç satırların v2 etiketi. DB'ye yazılmaz; sürümlü ayrı araştırma artefaktı üretilir.
- **Başarı (PROPOSED):** Araç uyuşması ≥ %95; v2 sonucu tüm alt kümelerle raporlanır. **Başarısızlık (PROPOSED):** Uyuşma < %90 → önce fiyat verisi/araç sorunu çözülür, v2 yayınlanmaz.
- **Maliyet:** Düşük (offline, birkaç CPU-dakikası).
- **Öncelik / neden şimdi:** P0. Arşivden türetilen her iddianın geçerliliğini belirler.

#### HYP-02 — Aynı-bar ve gap kurallarının iyimserliği (P0)
- **Hipotez:** TP-öncelikli aynı-bar kuralı ve gap'te seviye fiyatından çıkış, brüt bariyer ortalamasını muhafazakâr kurallara (SL-öncelikli; gap'te açılıştan çıkış) göre sistematik olarak yükseltir.
- **Motivasyon:** İki etiketleyici aynı olay için zıt sonuç üretiyor (INT-03).
- **Mevcut kanıt:** INT-03, ENX-05, ENX-10.
- **Gerekli veri:** Günlük fiyat önbelleği (mevcut). Gün içi bar geçmişi yok → gün içi sıra NOT_MEASURABLE kalır.
- **Baseline:** v1 kuralları.
- **Ölçüt:** Önceden tanımlı altı varyantta (TP-önce / SL-önce / belirsizi dışla × gap'te seviye / açılış) ortalama, medyan, kazanma oranı, PF.
- **Maliyet modeli:** Uygulanmaz.
- **Riskler:** Sonuca göre kural seçme. Önlem: tüm varyantlar raporlanır; birincil varyant önceden "SL-önce + gap'te açılış" (muhafazakâr) olarak sabitlenir.
- **Test tasarımı:** HYP-01'in v2 tarih tabanıyla birlikte.
- **Başarı / başarısızlık (PROPOSED):** Muhafazakâr varyantın gün-kümelenmiş %95 CI'si sıfırı içeriyorsa "arşivde brüt pozitiflik kanıtı yok" sonucu kayda geçer; dışlıyorsa bulgu HYP-06 için ön koşul sayılır.
- **Maliyet:** Düşük. **Öncelik:** P0.

#### HYP-03 — Geç kohort seçimsiz bir kopya mı? (P0)
- **Hipotez:** 2026-03-01 21:45 partisi (1.616 karar satırı, 11 sinyal günü), aynı günlerin tam tarayıcı çıktısının seçimsiz bir kopyası değildir; sonuç bilgisiyle ilişkili bir alt kümedir.
- **Motivasyon:** Partideki satırların kazanma payı belirgin biçimde yüksek (INT-08). Partiyi yazan kod git'te bulunamadı (R0 açık soru 1; R10 B2).
- **Mevcut kanıt:** F-PRF-07, INT-08, EVI-F01, R10 B2 (yazım anında sonuçların %97,96'sı belirlenmişti; seçimde kullanılıp kullanılmadığı ölçülemedi).
- **Gerekli veri:** Aynı sinyal günlerine ait bağımsız tarayıcı çıktıları (shortlist/export); varlıkları doğrulanmalıdır.
- **Baseline:** Aynı günlerin bağımsız çıktısı.
- **Ölçüt:** Kapsama ve seçim oranı; sonuçtan bağımsız alanlarda (skor, fiyat, hacim) dağılım farkı. Sonuç hesaplanmadan yapılabilir.
- **Riskler:** Bağımsız çıktı yoksa test yapılamaz.
- **Test tasarımı:** Önce yalnız kapsama/özellik karşılaştırması; sonuç verisine bakılmaz.
- **Başarı / başarısızlık (PROPOSED):** Bağımsız çıktı bulunamazsa sonuç UNRESOLVED olarak kayda geçer ve kohort tüm iddialarda ayrı raporlanır.
- **Maliyet:** Düşük. **Öncelik:** P0.

#### HYP-04 — Ayarlı fiyat ile ham giriş fiyatı uyumsuzluğu (P1)
- **Hipotez:** Çözücü `auto_adjust=True` serisini ham `entry_price` ile karşılaştırdığı için, pencerede temettü veya bölünme olan sembollerde etiketler sistematik olarak kayar.
- **Mevcut kanıt:** ENX-05 (çözücü kuralı); R10'da etkisi ölçülmedi olarak işaretli.
- **Gerekli veri:** Fiyat önbelleğindeki `close` ve `adjusted_close` (iki şema/vintaj; F-DQ-06).
- **Baseline:** Ham seri ile etiket.
- **Ölçüt:** Kurumsal işlem içeren satırlarda iki seri arasındaki etiket ve getiri farkı.
- **Riskler:** Önbellekteki ayarlama tutarsızlıkları sonucu kirletebilir.
- **Başarı / başarısızlık (PROPOSED):** Etkilenen satır oranı ve ortalama fark raporlanır; fark gün-kümelenmiş CI'de sıfırı dışlıyorsa çözücü düzeltme adayıdır.
- **Maliyet:** Düşük. **Öncelik:** P1.

#### HYP-05 — IEX hacminin likidite kapısına etkisi (P1)
- **Hipotez:** `feed="iex"` hacmini kullanan likidite kapısı ve ADV tabanlı pozisyon üst sınırı, konsolide hacme göre sistematik olarak daha fazla sembolü eler ya da daha küçük üst sınır verir.
- **Mevcut kanıt:** F-DQ-08; R10 B4 (PARTIALLY VERIFIED: yfinance ile doldurulan veriler tam hacim kullanıyor, yani taramada iki hacim tabanı karışık).
- **Gerekli veri:** Aynı pencerede IEX ve konsolide hacim; mevcut veride pencereler uyuşmuyor (R3) → ileriye dönük çift kayıt gerekir.
- **Baseline:** Konsolide hacimle hesaplanan kapı kararı.
- **Ölçüt:** Kapı kararlarında uyuşmazlık oranı; sembol başına hacim kaynağı dağılımı. Sonuç verisi gerekmez.
- **Riskler:** Feed değişikliği ücretli veri aboneliği gerektirebilir → para kararı (Level C).
- **Başarı / başarısızlık (PROPOSED):** Uyuşmazlık oranı raporlanır; yüksekse veri kaynağı kararı insana sunulur.
- **Maliyet:** Kayıt için düşük mühendislik (Level B kod değişikliği). **Öncelik:** P1; seçimi doğrudan etkiler.

### B. Sıralama ve seçim

#### HYP-06 — Yayın sırasının bilgi içeriği (P1)
- **Hipotez:** Yayınlanan sıra (grade → `execution_confidence` → `conviction_prob` → `legacy_quality_score`), aynı gün uygun ama seçilmeyen sembollere ve rastgele seçime göre daha yüksek v2 etiket getirisi sağlar.
- **Motivasyon:** Üretimde kararı veren alanlar için sonuç kanıtı yok (SCR-01, SCR-05).
- **Mevcut kanıt:** SCR-01, SCR-05, F-PRF-10 (arşivde NOT_MEASURABLE). Gölge defter `selection_eligible`, `reject_reason`, `selected_by_legacy_quality`, `selected_by_v2` alanlarını taşır; fiyat alanı yoktur (orkestratör profili: 118.338 satır, 553 `selection_eligible=true`, 222 `selected_by_legacy_quality=true`).
- **Gerekli veri:** Gölge defter + fiyat serisi. Gölge defterin tamamı 2026-05-21 sonrasıdır → **kilit kapsamı insan kararı (F-PRF-00) olmadan sonuç hesaplanmaz**; aksi durumda test yalnız ileriye dönük yapılır.
- **Baseline:** (1) Aynı gün eligible-seçilmeyen; (2) aynı gün eşit sayıda rastgele eligible; (3) HYP-07 basit sıra.
- **Ölçüt:** Önceden sabit top-N için ortalama ve medyan v2 brüt getiri farkı ve R-multiple farkı; gün-kümelenmiş CI.
- **Maliyet modeli:** 0,10 / 0,25 / 0,55 / 1,00 pp gidiş-dönüş senaryoları; net değil, duyarlılıktır.
- **Riskler:** Kilit ihlali; N, ufuk ve ölçüt seçiminde çoklu test; rejim karışması.
- **Test tasarımı:** Protokol, birincil ölçüt ve N önceden kayda geçer; D7 gereği bağımsız doğrulama ileriye dönüktür.
- **Başarı / başarısızlık (PROPOSED):** Birincil ölçütte üç baseline'a karşı fark CI'si sıfırı dışlarsa sıralamada bilgi var sayılır; içerirse "sıralama bilgisi kanıtlanmadı" kayda geçer.
- **Maliyet:** Orta (veri birleştirme, protokol). **Öncelik:** P1. "Doğru hisseleri seçiyor muyuz?" sorusunun tek doğrudan testidir.

#### HYP-07 — Daha basit bir sıra yeterli mi? (P2)
- **Hipotez:** Birkaç bileşenden (ör. rejim, yön, ham momentum) kurulan eşit ağırlıklı bir sıra, mevcut yayın sırasıyla aynı veya daha iyi v2 sonucunu daha az karmaşıklıkla verir.
- **Mevcut kanıt:** F-FRM-01 (çift sayım), SCR-04 (düşük çözünürlük), SCR-05, INT-12/INT-15 (dört ham kaynak ailesi; `df_1d` en az 16 karar alanının tek girdisi).
- **Gerekli veri / tasarım:** HYP-06 ile aynı veri ve protokol; karşılaştırma önceden tanımlı en fazla üç basit modelle sınırlıdır.
- **Başarı / başarısızlık (PROPOSED):** Eşdeğerlik veya noninferiority marjı ve güç planı sonuçlara bakılmadan tanımlanır. Fark testinin anlamsız olması eşdeğerlik değildir; sadeleştirme önerisi ancak bu ayrı tasarımın kabul koşuluyla Level B olarak sunulur.
- **Maliyet:** Düşük (HYP-06 altyapısını kullanır). **Öncelik:** P2.

#### HYP-08 — Eşitlikler top-N'yi rastgeleleştiriyor mu? (P2; sonuç gerektirmez)
- **Hipotez:** Composite eşitlikleri ve açık tie-break olmaması, composite kullanılan yollarda top-N kümesini iş parçacığı tamamlanma sırasına bağlı kılar.
- **Mevcut kanıt:** SCR-04. Not: `ranking_score` eşitlik payı medyan 0'dır ve yayın anahtarı public satırlarda eşitlik üretmedi (R5); risk esas olarak composite kullanılan yollardadır.
- **Test:** Saklanan shortlist dosyalarında sıralama anahtarı başına eşitlik payı ve rastgele tie-break permütasyonu altında top-N değişim oranı. Offline; sonuç verisi gerekmez.
- **Başarı / başarısızlık (PROPOSED):** Değişim oranı raporlanır; anlamlıysa deterministik tie-break Level B önerisi yapılır.
- **Maliyet:** Çok düşük. **Öncelik:** P2.

#### HYP-09 — NaN girdiler üretimde üst sınır puanı alıyor mu? (P1; sonuç gerektirmez)
- **Hipotez:** Üretim satırlarında NaN girdiler, kenet kalıbı nedeniyle bileşenin maksimum değerini alıyor.
- **Mevcut kanıt:** F-FRM-10 (mekanizma REPRODUCED); R10 B5 (PARTIALLY VERIFIED: üretim verisinde gözlenmedi).
- **Test:** Export ve shortlist satırlarında boş/NaN girdi ile sınır değerli skorun birlikte görülme sayısı. `atr_pct` kalıcı olmadığından legacy tarafı ileriye dönük kayıt gerektirir (SCR-03).
- **Başarı / başarısızlık (PROPOSED):** Sıfırdan farklı sayım → NaN koruması Level B düzeltme adayıdır; sıfır → mekanizma kayda geçer, öncelik düşer.
- **Maliyet:** Çok düşük. **Öncelik:** P1.

#### HYP-10 — Düşük fiyat etkisi seçim becerisi mi, mekanik mi? (P1)
- **Hipotez:** 5 USD altı satırların toplam brüt getiriye orantısız katkısı seçim becerisinden değil, ≈5 kat geniş TP/SL mesafesi ile TP-öncelikli aynı-bar kuralının etkileşiminden kaynaklanır.
- **Mevcut kanıt:** F-PRF-08, INT-09 (+4,58 puan fark; brüt; örneklem içi), ENX-10 (2 USD altı satırlarda stop medyanı ≤ 9 tick).
- **Test:** HYP-02 muhafazakâr kurallarıyla v2 etiketleri; fiyat kovalarında R-multiple normalizasyonu; tick ve spread senaryoları.
- **Başarı / başarısızlık (PROPOSED):** Muhafazakâr kurallar ve R-multiple altında fark kaybolursa etki mekanik kabul edilir.
- **Maliyet:** Düşük. **Öncelik:** P1; maliyet ve portföy değerlendirmesini doğrudan etkiler.

### C. Strateji aileleri (veri mevcut olanlar)

#### HYP-11 — Açılış gap'i giriş kalitesini bozuyor mu? (P2; aile E)
- **Hipotez:** Sinyal fiyatı (son 15 dakikalık `Close`) ile ertesi açılış arasındaki gap, uygulanabilir giriş fiyatını sistematik olarak kötüleştirir; açılış girişli etiketler sinyal fiyatlı etiketlerden düşüktür.
- **Mevcut kanıt:** ENX-03 (kapanmış bar kontrolü yok), ENX-10 (ilk temasın %74,9'u ilk seansta), F-DQ-07.
- **Test:** v2 etiketlerinin iki giriş tabanıyla (sinyal fiyatı; ertesi açılış) üretilmesi ve fark dağılımı.
- **Başarı / başarısızlık (PROPOSED):** Fark gün-kümelenmiş CI'de sıfırı dışlarsa giriş tanımı Level B olarak ürüne sunulur.
- **Maliyet:** Düşük. **Öncelik:** P2.

#### HYP-12 — Kalabalık sinyal günleri ve işlem yapmama (P2; aile I)
- **Hipotez:** Aynı gün çok sayıda sinyal üretilen günlerde başarı oranı düşer; bu bir "işlem yapmama" kuralı için adaydır.
- **Mevcut kanıt:** INT-11 (HYPOTHESIS; R9'da 24 hücre ve 13 karşıtlıktan biri, çoklu test düzeltmesi yapılmadı).
- **Test:** v2 etiketleriyle önceden tanımlı gün-başı sinyal sayısı kovaları; gün-kümelenmiş; aile düzeyinde düzeltme; bağımsız doğrulama ileriye dönük.
- **Maliyet:** Düşük. **Öncelik:** P2.

#### HYP-13 — Ön koşu: devam mı, dönüş mü? (P2; aileler A ve B)
- **Hipotez:** Sinyal öncesi 5 ve 20 seanslık koşusu yüksek sinyallerin sonuç dağılımı, düşük koşulu sinyallerden farklıdır.
- **Mevcut kanıt:** R6 yol istatistikleri (ön koşu ölçümleri R6'da; değerler bu sentezde aktarılmadı); PRIOR `reports/pre_rise_path_battery_2026-08-11.md`.
- **Test:** v2 etiketleri; ön koşu desilleri. Yön önceden belirtilmediği için iki yönlü test ve aile düzeyinde düzeltme.
- **Maliyet:** Düşük. **Öncelik:** P2.

### D. Tarama performansı

#### HYP-14 — Gereksiz yeniden çekme onarım süresini belirliyor mu? (P3)
- **Hipotez:** Onarım yolunda yalnız eksik zaman dilimlerinin çekilmesi ve `fast_info.last_price` kaynaklı ek `history` isteğinin kaldırılması, onarım süresini anlamlı ölçüde kısaltır ve kararları değiştirmez.
- **Mevcut kanıt:** PERF-02/05/07; R10 B8 (kod düzeyinde VERIFIED); PRIOR 2026-09-22 kohortunda `prefetch.repair` medyan payı %86,45 (5 koşu, 200 sembol).
- **Gerekli veri:** Canlı ölçüm (sağlayıcı çağrısı yapar).
- **Test:** Dondurulmuş 200 sembol (`research/scanner_perf_baseline_2026_10_17.py`), izole ortam, 1 soğuk + 5 ölçüm koşusu; aşama zamanlaması açık; `scripts/golden_scan.py compare` ile sıfır karar farkı şartı.
- **Başarı / başarısızlık (PROPOSED):** Medyan `total_s` düşüşü ve sıfır karar farkı → Level B öneri; karar farkı > 0 → değişiklik saf optimizasyon değildir.
- **Maliyet:** Orta; sağlayıcı kotası. **Öncelik:** P3. Canlı ölçüm Level C onay gerektirir.

## 4. Şimdi değil

| Aile / fikir | Neden şimdi değil | Ön koşul |
|---|---|---|
| H — Olay odaklı (earnings, haber, SEC) | `catalyst_factor` 1.518/1.518 satırda 0 (F-DQ-04); sentiment kapalı; makro ve katalizör önbellekleri point-in-time değil (F-DQ-10) | PIT olay verisi ve doğru çalışan katalizör alanı |
| G — Rejime duyarlı modeller | Arşivde rejim 6 farklı kodlamayla; mevcut "Bull/Bear" kodlaması 0 kez (INT-07) | İleriye dönük tutarlı rejim kaydı |
| L — Portföy kurgusu | Arşivde çıkış tarihi ve tutma süresi yok; eşzamanlılık ölçülemiyor (F-PRF-09) | Çıkış tarihli v2 etiketleri |
| C — Breakout / retest | Gün içi bar geçmişi kalıcı değil | Gün içi veri arşivi |
| K — Meta-labeling / kalite modeli | Tüm satırlar `partial` (F-DQ-03); kalite katmanları ayrışmıyor | Tamlık alanlarının dolması |
| D — Volatilite genişlemesi, F — Göreli güç | Veri kısmen var; P0 etiket sorunları çözülmeden yeni aile testi çoklu test yükünü artırır | HYP-01/02 tamamlanması |
| Sabit hedefli TP/SL ızgarası (yeniden açma) | PRIOR: 3.120 konfigürasyon; White RC p 0,741; Hansen SPA p 0,776; PBO 0,6 | Öncelik kaybı; olumsuz kanıt mevcut (yalnız veri eksikliği değil) |
| RX-CAPTURE-1 türevi hedef yakalama | PRIOR: E1 medyanı hedef artefaktı; ortalama −0,83 pp (0,55 maliyet senaryosu) | Öncelik kaybı; olumsuz kanıt mevcut |
| Huni (Blok 2.4 aktivasyonu) | `filter_score` döngüselliği ve gün içi bağımsızlık doğrulanmadı (2026-10-16 kaydı) | Bileşen zaman dilimi doğrulaması ve gölge mod |

## 5. 30 günlük araştırma planı adayları

Ayrıntılı plan ve karar bağımlılıkları R12 §3'tedir. Adaylar:

1. **Etiket v2 (HYP-01 + HYP-02 + HYP-04):** offline, Level A. Arşivden türetilen her iddianın geçerliliğini belirler.
2. **İleriye dönük ölçüm sözleşmesi:** run kimliği, tarama başı bayrak anlık görüntüsü, tam evren sıra listesi ve `atr_pct` dahil bileşenler, sembol başı hacim kaynağı kaydı (HYP-05, HYP-09). Level B kod önerisi; D7'nin ileriye dönük OOS tanımını mümkün kılar.
3. **Seçilen ve seçilmeyen karşılaştırması (HYP-06 + HYP-07):** önce kilit kapsamı insan kararı; sonra gölge defter veya ileriye dönük veri.
4. **Sonuç gerektirmeyen hızlı kontroller (HYP-03, HYP-08, HYP-09):** offline, Level A.
5. **Tarama süresi canlı ölçümü (HYP-14):** Level C onay; izole ortam.

## 6. Sınırlamalar

- Backlog, R0–R9 raporlarının özet ve bulgu bölümlerine dayanır; her bulgu kaynak raporundaki sınırlamalarıyla birlikte geçerlidir.
- Sayısal eşikler önerilerdir; hiçbiri kilitli değildir ve insan onayı gerektirir (D7).
- Kartlar karar değildir. Bir kartın desteklenmesi üretim değişikliği yetkisi vermez ("Evidence is not Action").
- "Şimdi değil" tablosundaki aileler reddedilmiş değildir; olumsuz kanıt yalnız sabit hedefli ızgara ve RX-CAPTURE-1 için vardır.

<!-- END -->
