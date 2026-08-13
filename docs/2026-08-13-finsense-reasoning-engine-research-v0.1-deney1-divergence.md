# FinSense Reasoning Engine Research v0.1 — Deney 1: Divergence

Sürüm: 0.1 · Tarih: 2026-08-13 · Statü: Level A (araştırma, üretim değişikliği yok)

Yöntem notu: `docs/2026-08-10-finpilot-10-perspektif-red-team-vizyon-arastirmasi.md`'deki formatı izliyor — dosya olarak üretildi çünkü kapsam (10 perspektif × 10 sabit soru) sohbete sığmıyor. 10 perspektif birbirini görmedi; bu bilinçli — amaç konsensüs değil, mümkün olduğunca farklı hipotez. Collision (Deney 2) ve Convergence (Deney 3) ayrı belgelerde, bu turda değil.

**Kanıt standardı:** `[EVIDENCE]` bu repoda/oturumda üretilmiş veri veya deneyle doğrudan destekli · `[EXTERNAL]` bu turda web araştırmasıyla toplanmış dış literatür/ürün bulgusu · `[INFERENCE]` mevcut kanıttan mantıksal çıkarım · `[HYPOTHESIS]` test edilmemiş fikir · `[RADICAL]` spekülatif.

---

## 0. Ortak Kanıt Tabanı

### 0.1 FinSense — bilinen durum (repo-içi)

`[EVIDENCE]`
- Academy altyapısı var (6 agent: generator/quality-guard/gap-detector/analytics/personalization/updater + orchestrator) ama içerik neredeyse boş — yayınlanmış tek ders "Likidite Oranları"; Bollinger/RSI/MACD hiçbir derste kapsanmıyor.
- `dashboard/analysis/page.tsx` zaten RSI/MACD/SMA/BB'yi ham değer olarak gösteriyor, gerçek trafiği var, hiç açıklama yoktu.
- Bugün (2026-08-13) bu sayfaya minimal bir prob eklendi: RSI aşırı bölgedeyken (>70/<30) tek cümlelik açıklama + 👍/👎, Plausible event'leriyle ölçülüyor (`indicator_caveat_shown`/`indicator_caveat_feedback`). Henüz production'a push edilmedi (git lock nedeniyle bekliyor). Bu, aşağıdaki H1'in en küçük canlı testi — sonuç henüz yok.
- VS-01 (Case/Classroom akışı) production'da doğrulanmış durumda ama gerçek insan testi (Phase 8, 5-10 kullanıcı) henüz başlamadı — 0 gerçek katılımcı.
- FinPilot tarafında (skor/sinyal motoru, FinSense değil): score ileri getiriyi tahmin etmiyor (`finpilot-score-backward-looking-central-finding`), seçim katmanı (entry_ok/conviction) değer eksiltiyor, tek OOS-tutarlı bulgu ATR→MAE (risk boyutu, yön değil), sektör-trend rejim katmanı kısmen hayatta kalan tek getiri-koşullayan sinyal ama tam evrende replike edilmedi.
- `lottery_factor` (rho=-0.204) rigor'dan düşmeden hayatta kalan tek başka bulgu; concentration/ATR-parity rigor'dan düştü.

### 0.2 Dış literatür ve ürün ortamı (bu turda toplanan, EXTERNAL)

`[EXTERNAL]`
- **Overconfidence / indikatör okuma:** Perakende yatırımcılar kolay erişilebilir bilgiye (grafikler, tanınmış göstergeler) yöneliyor, temel analizi karmaşık bulup reddediyor; representativeness bias, "tanınmış göstergeyi etkili varsayma" şeklinde çalışıyor. Overconfidence deneyime ve geçmiş sonuçlara göre değişiyor. 137 yayınlık sistematik derleme bunu doğruluyor. [Business Perspectives — Overconfidence bias among retail investors](https://businessperspectives.org/journals/investment-management-and-financial-innovations/issue-447/overconfidence-bias-among-retail-investors-a-systematic-review-and-future-research-directions)
- **Finansal okuryazarlık programları:** Oyun-tabanlı kısa kurslar 2-3 haftada ölçülebilir kazanç gösteriyor ama kalıcılık test edilmemiş; ayrılmış (dedicated) ders > entegre yaklaşım. ABD'de genel finansal okuryazarlık 8 yıldır durgun. **"Grafik okuma" spesifik olarak literatürde neredeyse hiç doğrudan çalışılmamış** — bu, FinSense'in iddiasını destekleyecek doğrudan kanıt tabanının aslında var olmadığı anlamına geliyor. [Frontiers — youth financial literacy](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2024.1397060/full), [ScienceDirect — what works in financial education](https://www.sciencedirect.com/science/article/pii/S2214804325000679)
- **AI açıklama / güven kalibrasyonu:** Belirsizlik bilgisi göstermek güveni artırıyor ama **yalnızca düşük bilişsel yükte**; yüksek bilişsel yükte belirsizlik göstermek güveni **azaltıyor**. Açıklama kullanıcının anlama eşiğini aşarsa güven düşüyor; aşırı basit açıklama da küçümseyici görünüp şüphe yaratıyor. [Frontiers — explanations with uncertainty](https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2025.1560448/full), [Rapid Trust Calibration through Interpretable AI](https://pmc.ncbi.nlm.nih.gov/articles/PMC7660448/)
- **Rakip ortam (2026):** TradingView, Nisan 2026'da **Chart Copilot**'u yayınladı — grafik hakkında soru sorma, seviyede alarm kurma, haber/temel veri çekme (20M+ aktif kullanıcı). ChartingLens "verdict-first" konuşkan AI + düz-İngilizce backtesting sunuyor. Investopedia simulator'da hiç grafik/indikatör yok — saf al-sat. Trade Ideas' Holly AI aktif trader'lar için otonom sinyal üretiyor. **Yani "indikatörü sade dile çevir" fikri zaten kısmen pazarda var** — FinSense'in farkı olmalı. [ChartingLens best AI trading assistants 2026](https://chartinglens.com/blog/best-ai-trading-assistants), [Investopedia simulator review 2026](https://stockmarketgame.net/investopedia-simulator-the-ultimate-review)
- **Sokratik/soru-sorduran AI tutoring:** 2026 çalışması, sokratik-diyalog kullanan öğrencilerin doğrudan-cevap alanlara göre daha iyi transfer (yeni probleme uygulama) gösterdiğini buluyor. Ama bir Avrupa K-12 denemesi: sokratik AI daha zengin diyalog ürettirdi, **test sonuçlarında ölçülebilir fark yok**, öğrenciler "daha az yardımcı" olarak derecelendirdi — öğrenme kazanımı ile kullanıcı memnuniyeti ayrışabiliyor. [Journal of Computer Assisted Learning 2026](https://onlinelibrary.wiley.com/doi/10.1002/jcal.70210), [Brookings — generative AI in tutoring](https://www.brookings.edu/articles/what-the-research-shows-about-generative-ai-in-tutoring/)

---

## PERSPEKTİF 1 — QUANTITATIVE RESEARCHER

1. **Tanım:** FinSense şu an "indikatör sözlüğü + açıklama katmanı" — ama asıl soru şu: açıklama bir *feature dönüşümü* mü (RSI+trend+volume → tek bağlamsal skor), yoksa sadece *sunum katmanı* mı (aynı sayı, daha güzel cümle)? Bunlar farklı ürünler.
2. **Kullanıcı problemi:** Kullanıcı tek göstergeye bakıp aşırı-genelleme yapıyor (RSI 72 → "satılır"). `[EXTERNAL]` representativeness bias tam olarak bu.
3. **Yanlış olan:** Şu an dashboard'daki 8 gösterge birbirinden bağımsız kutucuklar — aralarındaki korelasyon/redundancy hiç gösterilmiyor. FinPilot tarafında zaten biliniyor ki composite/finpilot skorları yüksek korelasyonlu (`[EVIDENCE]` önceki PCA bulgusu, ~0.98 korelasyon) — aynı redundancy sorunu burada da olabilir.
4. **Ne olmalı:** Gösterge kümesini bağımsız eksenlere indirgeyen (PCA/faktör analizi tarzı) bir "kaç farklı şey söylüyor" katmanı — 8 gösterge değil, gerçekte 2-3 bağımsız boyut olabilir.
5. **En sıra dışı fikir:** Kullanıcıya göstergeleri değil, göstergeler arası *anlaşmazlığı* göster — "RSI ve MACD aynı şeyi söylemiyor, işte bu neden önemli."
6. **Çöpe atardı:** Redundant göstergelerin (SMA50+SMA200+BB'nin üçü de trend söylüyor) ayrı ayrı kutu olarak gösterilmesini.
7. **Merkez yapardı:** Bir "kaç bağımsız sinyal var" özeti.
8. **Deney:** Mevcut 8 göstergeye PCA uygula, kaç bileşenin varyansın %90'ını açıkladığını ölç. `[HYPOTHESIS]` ≤3 bileşen çıkarsa "translation" değil "compression" asıl değer.
9. **Vazgeçme kriteri:** PCA ≥6 bağımsız bileşen gösterirse (yani göstergeler gerçekten farklı bilgi taşıyorsa), "compress et" fikrimden vazgeçerim.
10. **5 yıl vizyonu:** FinSense'in çekirdeği bir "gösterge azaltma motoru" olur — kullanıcı 8 sayı değil, 2-3 gerçekten bağımsız boyut görür.

## PERSPEKTİF 2 — TECHNICAL ANALYST

1. **Tanım:** Şu anki FinSense bir "indikatör kataloğu"; profesyonel bir analist hiçbir göstergeye tek başına bakmaz, her zaman zaman-dilimi + hacim + yapı (support/resistance) üçlüsüyle okur.
2. **Kullanıcı problemi:** Acemi kullanıcı bağlamsız sayıya bakıyor (RSI 72) ve zaman dilimi/trend rejimini hiç sormuyor.
3. **Yanlış olan:** `regime` alanı (Trend/Volatile/Range/Breakout/Mean-Revert) zaten hesaplanıyor ama RSI/MACD kutucuklarıyla hiç birleştirilmiyor — regime ayrı bir metin, göstergeler ayrı kutular.
4. **Ne olmalı:** Her göstergenin yanına, o anki rejimle çelişip çelişmediğini gösteren tek bit bilgi: "RSI aşırı alımda AMA rejim=Trend → tek başına satış sinyali sayılmaz."
5. **En sıra dışı fikir:** Göstergeyi değil, göstergenin *tarihsel bu ticker'daki davranışını* göster — "Bu hissede RSI>70 olduğunda son 20 seferin X'i devam etti."
6. **Çöpe atardı:** BB Upper/BB Lower'ın "Key Levels" panelinde ayrı ayrı statik sayı olarak durmasını — fiyatın banda göre pozisyonu (üstte/altta/ortada) tek cümleyle daha nettir.
7. **Merkez yapardı:** Regime + gösterge birleşimi ("contextual reading").
8. **Deney:** RSI-caveat deneyinin (şu an sahada) bir varyantını regime bilgisiyle birlikte göster, feedback oranını karşılaştır.
9. **Vazgeçme kriteri:** Regime eklenmiş versiyon feedback'te fark yaratmıyorsa, "bağlam önemli" varsayımım yanlış demektir.
10. **5 yıl vizyonu:** FinSense, göstergeyi değil "bu ticker'ın bu anki rejimde ne yaptığını" anlatan bir motor olur.

## PERSPEKTİF 3 — BEHAVIORAL FINANCE SCIENTIST

1. **Tanım:** FinSense şu haliyle bir "bilgi sunumu" ürünü — ama davranışsal literatür bilginin kendisinin değil, bilginin *nasıl işlendiğinin* sorun olduğunu gösteriyor. `[EXTERNAL]` overconfidence sistematik derlemesi.
2. **Kullanıcı problemi:** Kullanıcı zaten RSI'nin ne olduğunu "biliyor" (Investopedia bir tık uzakta) — asıl sorun bilgi eksikliği değil, *representativeness bias* (tanınmış göstergeyi otomatik güvenilir sayma).
3. **Yanlış olan:** Açıklama eklemek (RSI-caveat deneyi gibi) davranışsal olarak riskli — `[EXTERNAL]` düşük bilişsel yükte belirsizlik bilgisi güveni artırıyor ama yüksek yükte azaltıyor. Dashboard zaten yoğun (8 gösterge + skor + haberler); RSI'ye eklenen caveat kullanıcının zaten yüklü olduğu bir ekranda mı, yoksa izole mi görünüyor, bu fark yaratır.
4. **Ne olmalı:** Açıklama değil, *sürtünme* — kullanıcı "BUY" görmeden önce kendi tahminini yazmaya zorlanmalı (Classroom/Case akışı zaten bunu yapıyor; dashboard'da yok).
5. **En sıra dışı fikir:** FinSense kullanıcının *kendi* geçmiş yanlışlarını ona göstersin ("son 5 kez RSI>70'te 'satılır' dedin, 3'ünde trend devam etti") — dışarıdan bilgi değil, kendi davranış aynası.
6. **Çöpe atardı:** Statik açıklama metinlerini (herkese aynı cümle) — kişiselleştirilmemiş "eğitim" davranış değiştirmiyor `[INFERENCE]` overconfidence deneyime göre değişiyor, tek-tip mesaj herkese aynı etkiyi yapmaz.
7. **Merkez yapardı:** Kullanıcının kendi tahmin geçmişiyle karşılaştırma (bu zaten Classroom'da var — Academy/dashboard'a taşınmalı).
8. **Deney:** RSI-caveat'ı iki grupta test et: (a) genel mesaj, (b) kullanıcının kendi geçmiş tahminine referans veren mesaj (bu ikincisi için önce kullanıcı geçmişi lazım — Classroom verisi olmadan yapılamaz).
9. **Vazgeçme kriteri:** Kişiselleştirilmiş mesaj genel mesajdan farksız çıkarsa, "kendine ayna tutma" hipotezim çürür.
10. **5 yıl vizyonu:** FinSense dış bilgi vermez, kullanıcıya kendi karar tarihini gösterir — bir "davranış aynası."

## PERSPEKTİF 4 — FINANCIAL EDUCATOR

1. **Tanım:** Academy şu an "tanım sözlüğü" olmaya aday (37 terim glossary + 1 ders) — ama `[EXTERNAL]` finansal okuryazarlık literatüründe "grafik okuma" ayrı bir beceri olarak neredeyse hiç çalışılmamış, yani kanıtlanmış bir müfredat şablonu yok, kendi bulmamız gerekiyor.
2. **Kullanıcı problemi:** RSI 72 gören acemi, "yüksek = kötü" gibi tek boyutlu okuyor; asıl eksik olan *koşullu düşünme* ("yüksek AMA ...").
3. **Yanlış olan:** Academy içeriği (var olan tek ders) pasif okuma — `[EXTERNAL]` oyun-tabanlı kısa kurslar 2-3 haftada ölçülebilir kazanç gösteriyor ama kalıcılık kanıtlanmamış; pasif ders formatı muhtemelen daha da zayıf.
4. **Ne olmalı:** Tanım değil, "bu grafikte ne görüyorsun?" tipi aktif alıştırma — Classroom'un case formatı aslında Academy'den daha iyi bir eğitim şablonu.
5. **En sıra dışı fikir:** Academy'yi tamamen kaldır, tüm eğitim akışını Classroom'un (gözlem→tahmin→sonuç) formatına taşı.
6. **Çöpe atardı:** Statik glossary sayfasını (37 terim, pasif okuma) — kimse sözlük okuyarak öğrenmiyor `[INFERENCE]`.
7. **Merkez yapardı:** Vaka-tabanlı, aktif-tahmin gerektiren mikro-dersler (Classroom paterni).
8. **Deney:** Aynı konsepti (RSI aşırı bölge) iki formatta test et — (a) statik açıklama (bugün shipped), (b) "sen ne düşünürdün?" sorup sonra açıklama gösteren format. Hangisi feedback'te daha iyi.
9. **Vazgeçme kriteri:** Aktif-soru formatı statik formattan feedback'te iyi çıkmazsa, `[EXTERNAL]` sokratik-tutoring bulgusundaki "daha az yardımcı bulundu" riski gerçekleşmiş demektir — o zaman basit açıklamada kalırım.
10. **5 yıl vizyonu:** Academy diye ayrı bir bölüm kalmaz; her ekran (dashboard, Classroom) zaten öğretici — ayrı "ders" kavramı ortadan kalkar.

## PERSPEKTİF 5 — UX / PRODUCT SCIENTIST

1. **Tanım:** FinSense şu an dashboard'a gömülü, keşfedilmesi zor bir katman (`/classroom`'a site içi link bile yok — önceki tur bulgusu). Ürün olarak henüz "bulunabilir" değil.
2. **Kullanıcı problemi:** Kullanıcı analysis sayfasına geldiğinde ilk 10 saniyede "ne yapmalıyım" istiyor, gösterge tanımı değil — sayfada zaten "Ne yapmalı?" kutusu var (satır 738), RSI caveat'ı bununla çakışmasın, onu güçlendirsin.
3. **Yanlış olan:** İki paralel "açıklama" yüzeyi oluşuyor: "AI Summary + Ne yapmalı" kutusu (üstte) ve şimdi RSI caveat (Technical sekmesinde) — kullanıcı hangisine güvenecek belli değil.
4. **Ne olmalı:** Tek, tutarlı "açıklama sesi" — ya hepsi AI Summary'ye toplanır ya hepsi gösterge yanına dağılır, ikisi birden karışıklık yaratır.
5. **En sıra dışı fikir:** Açıklamayı ayrı bir yerde göstermek yerine, kullanıcı bir göstergenin üstüne geldiğinde (hover) göster — ekranı kalabalıklaştırmadan, isteyen görür.
6. **Çöpe atardı:** Şu an her sekmede tekrar eden "~ Tahmini" rozetlerini — sekiz kez aynı uyarı, dikkat yorgunluğu yaratıyor.
7. **Merkez yapardı:** Progressive disclosure — varsayılan ekran sade, "neden?" tıklanınca detay açılır (ExplainPanel zaten bu paterni kısmen kullanıyor, genişletilebilir).
8. **Deney:** RSI caveat'ı iki yerleşimde test et — (a) bugünkü gibi her zaman görünür (aşırı bölgede), (b) hover/tıkla-aç. Feedback oranı ve "faydalı" tıklama oranını karşılaştır.
9. **Vazgeçme kriteri:** Her-zaman-görünür versiyon hover versiyonundan daha yüksek etkileşim alırsa, "kalabalık ekrandan kaçının" varsayımım yanlış.
10. **5 yıl vizyonu:** FinSense ayrı bir sayfa değil, FinPilot'un her ekranına gömülü, isteğe bağlı açılan bir "neden" katmanı olur.

## PERSPEKTİF 6 — PORTFOLIO / RISK MANAGER

1. **Tanım:** FinSense şu an tek-hisse, tek-gösterge odaklı — risk yönetimi perspektifinden bu eksik bir çerçeve, çünkü hiçbir gösterge portföy bağlamından bağımsız anlamlı değil.
2. **Kullanıcı problemi:** Kullanıcı "bu hisse RSI'ya göre ne yapmalı" diye düşünüyor, "bu pozisyon portföyümü nasıl etkiler" diye düşünmüyor.
3. **Yanlış olan:** `[EVIDENCE]` FinPilot'ta tek OOS-tutarlı bulgu ATR→MAE (risk boyutu) — yani sistemin zaten kanıtlanmış güçlü tarafı risk, ama FinSense hiç risk-çevirisi yapmıyor, yön-çevirisi (RSI/MACD) yapıyor. Kanıtlanmış güçlü tarafı görmezden geliyoruz.
4. **Ne olmalı:** "İndikatör çevirisi" değil "risk çevirisi" — ATR'yi "bu hisse ortalama %X hareket ediyor, stop'un bu kadar mantıklı" diye çevirmek, RSI'yi çevirmekten daha kanıta-dayalı.
5. **En sıra dışı fikir:** FinSense'in ilk ve tek odağı ATR/volatilite/stop-loss çevirisi olsun — RSI/MACD'ye hiç dokunma, çünkü onların yön-tahmin değeri kanıtsız, ATR'nin risk-tahmin değeri kanıtlı.
6. **Çöpe atardı:** RSI/MACD/BB çevirisi projesinin şimdiki önceliğini — kanıtsız bir alana emek harcıyoruz.
7. **Merkez yapardı:** Stop-loss/pozisyon-büyüklüğü/ATR açıklaması.
8. **Deney:** RSI caveat'ın ATR/Stop-Loss kutusuna eklenen bir versiyonunu paralel test et (örn. "Stop %X uzaklıkta — bu hissenin ortalama günlük hareketinin Y katı").
9. **Vazgeçme kriteri:** ATR-çevirisi feedback'te RSI-çevirisinden iyi çıkmazsa, "kanıtlanmış tarafa odaklan" argümanım zayıflar.
10. **5 yıl vizyonu:** FinSense yön tahmin etmeyi hiç iddia etmez, sadece "bu ne kadar riskli, ne kadar hareket eder" çevirir — FinPilot'un gerçekten kanıtlı olduğu tek alanla hizalanır.

## PERSPEKTİF 7 — DATA SCIENTIST

1. **Tanım:** FinSense şu an ölçülemeyen bir ürün — "kullanıcı daha iyi anlıyor mu" sorusunun cevabı yok, bugüne kadar hiç veri toplanmadı.
2. **Kullanıcı problemi:** Biz bile "grafik okuma" ne demek tam tanımlayamıyoruz — ölçülebilir bir tanım yok.
3. **Yanlış olan:** RSI caveat deneyi (bugün shipped) iyi bir başlangıç ama tek metriği var (👍/👎) — "faydalı buldum" ile "doğru yorumladım" aynı şey değil, ikincisi ölçülmüyor.
4. **Ne olmalı:** Öncesi/sonrası test — kullanıcıya açıklamadan önce "bu grafikte ne görüyorsun?" sor, açıklamadan sonra yeni bir grafikte tekrar sor, cevap kalitesini karşılaştır (`[EXTERNAL]`'daki AI-tutoring çalışmalarının metodolojisi tam bu).
5. **En sıra dışı fikir:** "Faydalı buldum" oranı ile gerçek anlama arasındaki korelasyonu ölçmeyi ayrı bir hipotez yap — ikisi ayrışabilir (`[EXTERNAL]` sokratik-tutoring: öğrenme arttı ama memnuniyet düştü, ters yönde de olabilir).
6. **Çöpe atardı:** Sadece 👍/👎'yi "başarı" saymayı — bu bir vekil metrik, hedef değil.
7. **Merkez yapardı:** Basit bir "önce tahmin et, sonra gör" mikro-testi (Classroom'daki pattern zaten var, dashboard'a taşınabilir).
8. **Deney:** RSI caveat gösterilen ve gösterilmeyen kullanıcılarda (A/B, aynı ticker'a farklı zamanlarda bakanlar) sonraki "Ne yapmalı?" kutusuyla etkileşim oranını karşılaştır — dolaylı bir "anlama" proxy'si.
9. **Vazgeçme kriteri:** 👍 oranı yüksek ama davranışta (etkileşim, geri dönüş) hiç fark yoksa, metrik boş sinyal demektir.
10. **5 yıl vizyonu:** FinSense'in her özelliği "anlama" için doğrulanmış, birden fazla bağımsız metrikle çapraz kontrol edilmiş bir ölçüm çerçevesine sahip olur.

## PERSPEKTİF 8 — AI RESEARCHER

1. **Tanım:** Şu anki RSI caveat statik, kural-tabanlı bir cümle (`rsi > 70 ? metin1 : metin2`) — "AI" değil, if-else. Bu dürüst olarak isimlendirilmeli.
2. **Kullanıcı problemi:** Kullanıcı tek göstergeye bakıp tek yorum yapıyor; asıl eksik gözlem→hipotez→karşı-hipotez zinciri.
3. **Yanlış olan:** Statik metin ölçeklenmiyor — 8 gösterge × N durum için elle yazılmış cümle sürdürülemez. `[EXTERNAL]` TradingView'in Chart Copilot'u (Nisan 2026) bunu konuşkan/generatif olarak çözüyor, biz statik kalıyoruz.
4. **Ne olmalı:** Kural-tabanlı prototip (bugünkü RSI caveat) önce ölçülmeli — eğer 👍 oranı düşükse, "daha akıllı" (LLM-üretilmiş) versiyon sorunu çözmez, çünkü sorun akıllılık değil alaka olabilir.
5. **En sıra dışı fikir:** Karşı-hipotez üretmeyi dene — "Bullish yorum: X. Ama şuna dikkat: Y." Bu, statik template'te bile (LLM olmadan) denenebilir; RSI caveat'a bir "ama" cümlesi eklemek bunun en küçük hali zaten.
6. **Çöpe atardı:** Şu an hiçbir şey — henüz LLM-tabanlı bir şey yok ki atılacak olsun.
7. **Merkez yapardı:** Gözlem→bağlam→yorum→karşı-argüman zincirini *önce statik template'lerle* prototipleyip, hangi adımın gerçekten değer kattığını ölçmeden LLM'e geçmemek.
8. **Deney:** RSI caveat'a "ama" cümlesini kaldırılmış bir kontrol versiyonuyla karşılaştır ("Momentum güçlü." vs "Momentum güçlü — ama tek başına düşüş sinyali değil.") — karşı-argüman cümlesinin kendisi fark yaratıyor mu?
9. **Vazgeçme kriteri:** "Ama" cümlesi olan/olmayan versiyonlar arasında feedback farkı yoksa, "counter-reasoning" fikrimin en basit hali bile boş sinyal demektir — LLM'e hiç gitmeden burada dururum.
10. **5 yıl vizyonu:** Eğer statik counter-argüman çalışırsa, o zaman LLM üretimi ölçeklendirme sorunu (8 gösterge × sonsuz durum) için gerekçelenir — ama sıralama önce kanıt, sonra teknoloji.

## PERSPEKTİF 9 — FUTURIST / FOUNDER

1. **Tanım:** Bugünün FinSense'i küçük — bir gösterge kutusuna eklenen bir cümle. Büyük resim: piyasa verisini pasif izlemekten aktif muhakemeye geçiş katmanı.
2. **Kullanıcı problemi:** 5 yıl sonra bile insanlar RSI hesaplamayı öğrenmeyecek — ama "bu bilgiye ne kadar güvenmeliyim" sorusunu her zaman soracaklar.
3. **Yanlış olan:** Şu an her şey tek-yönlü (sistem → kullanıcı bilgi). Gelecekte kullanıcı → sistem geri bildirimi (bugünkü 👍/👎 gibi) döngüye girmeli, zamanla kişiselleşmeli.
4. **Ne olmalı:** Bugünkü küçük deney (RSI caveat + feedback) aslında doğru ilk adım — büyük vizyona küçük, ölçülebilir adımlarla gidilmeli, tek seferde büyük motor kurulmamalı.
5. **En sıra dışı fikir:** FinSense'in nihai ürünü bir "gösterge açıklayıcı" değil, kullanıcının zaman içindeki karar kalitesini izleyen bir "düşünme günlüğü" olabilir — Classroom zaten bunun tohumunu içeriyor.
6. **Çöpe atardı:** Hiçbir şey — 5 yıllık vizyon bugünkü küçük deneyleri gereksiz kılmaz, üzerine inşa eder.
7. **Merkez yapardı:** Kullanıcı geri bildirim döngüsünü (feedback verisi) — bu, gelecekteki her şeyin (kişiselleştirme, market memory, vs.) ham malzemesi.
8. **Deney:** Yok — bu perspektif spesifik bir deney önermiyor, mevcut küçük deneylerin veri toplama disiplinini savunuyor.
9. **Vazgeçme kriteri:** Küçük deneyler (RSI caveat gibi) 3-6 ay içinde hiçbir tutarlı sinyal üretmezse (ne olumlu ne olumsuz, sadece gürültü), büyük vizyonun temelsiz olduğunu kabul ederim.
10. **5 yıl vizyonu:** FinSense, kullanıcının finansal düşünme tarzını zamanla öğrenen ve ona özel geri bildirim veren bir sistem olur — ama oraya küçük, ölçülen adımlarla gidilir, bugün yazılan büyük mimari şemalarla değil.

## PERSPEKTİF 10 — DEVIL'S ADVOCATE

1. **Tanım:** FinSense şu an çözümü olmayan bir soruna çözüm arıyor olabilir. `[EXTERNAL]` TradingView zaten Nisan 2026'da Chart Copilot'u (20M+ kullanıcıya) yayınladı — "indikatörü konuşkan dille açıkla" pazarda zaten var, üstelik bizden büyük bir dağıtım ağıyla.
2. **Kullanıcı problemi:** Belki de kullanıcının asıl problemi "göstergeyi anlamamak" değil, "hangi bilgiye güveneceğini bilmemek" — ve bu, açıklama eklemekle çözülmüyor, aksine `[EXTERNAL]` yüksek bilişsel yükte belirsizlik/açıklama göstermek güveni *azaltabiliyor*.
3. **Yanlış olan:** Şu ana kadarki tüm tartışma ("indicator translator" mı "reasoning engine" mi) bir varsayımı hiç sorgulamadı: kullanıcının bunu *istediği* varsayımı. RSI caveat'ın 👍/👎 oranı düşük çıkarsa, bu sadece "metni değiştir" değil, "kullanıcı bunu hiç istemiyor" anlamına da gelebilir.
4. **Ne olmalı:** Belki hiçbir şey — belki FinSense'in doğru hamlesi Academy/gösterge-açıklama yatırımını bırakıp, zaten kanıtlanan tek şeye (Classroom/Case akışı, tahmin-taahhüt-sonuç döngüsü) odaklanmak.
5. **En sıra dışı fikir:** "İndikatörleri sadeleştirmek güzel ama kullanıcının asıl problemi bu değil" — bu bir başarısızlık değil, değerli bir bulgu olurdu. Bunu gerçek bir olasılık olarak baştan kabul etmeliyiz.
6. **Çöpe atardı:** Academy'nin tamamını (6 agent'lık altyapı, boş içerik) — kanıtsız bir yatırım, kimse kullanmıyor (1 yayınlanmış ders).
7. **Merkez yapardı:** Hiçbir yeni "açıklama" özelliği değil — sadece Phase 8'i (5-10 gerçek kullanıcı, Classroom) bitirmek, çünkü FinSense'in tek gerçekten test edilmiş varlığı o.
8. **Deney:** RSI caveat'ın 👍/👎 oranını, aynı sayfadaki *ilgisiz* bir kontrol elementiyle (örn. "Bu sayfa faydalı mıydı?" genel sorusu) karşılaştır — eğer ikisi de benzer oranda olumlu geliyorsa, RSI caveat'a özgü bir sinyal yok, genel bir "kullanıcılar her şeye 👍 basar" artefaktı var demektir.
9. **Vazgeçme kriteri:** Eğer RSI caveat feedback oranı kontrol elementinden belirgin şekilde yüksekse VE kullanıcılar organik olarak yorum/talep bırakıyorsa, "kullanıcı bunu istemiyor" iddiamdan vazgeçerim.
10. **5 yıl vizyonu:** Belki FinSense'in 5 yıllık vizyonu hiç yok olmalı — belki FinPilot'un kendisi (araştırma/karar-destek) yeterli, "eğitim katmanı" ayrı bir ürün olarak hiç var olmamalı. Bu ihtimali ciddiye almadan yapılan hiçbir vizyon belgesi tam değildir.

---

## Kapanış — Deney 2'ye (Collision) köprü

Bu turda üretilmedi. On perspektif arasında en azından şu açık çelişkiler var, sonraki turda çarpıştırılmalı: Quant/Data Scientist ("compress et, ölç") vs Futurist ("küçük adımlarla ilerle, zaten doğru yoldasın") vs Devil's Advocate ("belki hiç yapma, TradingView zaten yapıyor"); Portfolio Manager ("RSI'ı bırak, ATR'ye odaklan") vs bugün shipped edilen deneyin kendisi (RSI'a odaklanıyor); Behavioral Scientist ("kişiselleştirilmemiş mesaj işe yaramaz") vs bugünkü deneyin tasarımı (genel/kişiselleştirilmemiş mesaj).

**Önemli:** bu belgedeki hiçbir hipotez henüz doğrulanmadı. RSI caveat deneyi (Perspektif 1-10'un hepsinin atıfta bulunduğu tek canlı veri kaynağı) henüz production'a push edilmedi — `.git/index.lock` nedeniyle bekliyor. Deney 2 (Collision), bu ilk gerçek sinyal gelmeden yapılırsa, sadece varsayımları varsayımlara çarpıştırmış oluruz.
