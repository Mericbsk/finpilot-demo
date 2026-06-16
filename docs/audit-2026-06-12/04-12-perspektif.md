# Bölüm F — 12 Perspektif Stratejik Analizi

Her perspektif, 2026-06-12 itibarıyla gerçek sistem durumuna (494 test, 21 router, edge-kanıtsız skor, 0 dış kullanıcı, Academy entegre değil) bakıyor.

---

## PERSPEKTİF 1: YENİ BAŞLAYAN BİREYSEL YATIRIMCI
**Kim:** Teknik olmayan, birikimini değerlendirmek isteyen, telefonundan bakan kullanıcı.
**İlk izlenim:** "Çok güçlü görünüyor ama nereden başlayacağımı bilmiyorum." 15+ dashboard sayfası onu korkutur.
**Güçlü:** Türkçe arayüz potansiyeli; Telegram bildirimi alışkanlığına uygun; Academy (entegre olsa) tam ona göre.
**Zayıf:** İlk değer anı yok; "bugün ne yapmalıyım?" sorusunun tek-ekran cevabı yok; mobil doğrulanmamış; jargon yoğun (decile, calibration, DRL).
**5 soru:** Bu uygulama bana para kazandırır mı? Telefonda çalışıyor mu? Ne kadar öder, ne alırım? Sinyale güvenebilir miyim, kanıt nerede? Hiçbir şey bilmiyorum — bana öğretir mi?
**En büyük fırsat:** Academy + günlük tek kart brief = "öğrenirken yatırım yapan" segment, rakiplerin ihmal ettiği alan.
**En büyük tehdit:** İlk 5 dakikada kaybolup bir daha dönmemesi.
**Öneri:** (1) 3 ekranlık basit mod (Bugün/Sinyaller/Öğren). (2) Mobil-öncelikli tek brief kartı. (3) Academy onboarding'i ilk oturuma göm.

## PERSPEKTİF 2: DENEYİMLİ AKTİF TRADER
**Kim:** Günlük işlem yapan, TradingView+broker terminali kullanan, backtest okumayı bilen.
**İlk izlenim:** "Multi-timeframe tarama + ensemble DRL — ilginç. Track record'unu göster."
**Güçlü:** Çok-zaman-dilimli hizalama, earnings blackout, ATR-tabanlı risk, paper trading altyapısı, Alpaca entegrasyonu — dilini konuşuyor.
**Zayıf:** **Canlı doğrulanabilir track record yok** (signals_archive var ama public değil); backtest var ama metodolojisi yayınlanmamış; API erişimi yok; skor edge'i şirket içi audit'te bile negatif.
**5 soru:** Son 90 günün sinyal listesi ve T+5 sonuçları nerede? Slippage dahil mi (slippage_tracker var — artı)? Benim stratejimle entegre olur mu (API/webhook)? Backtest sample dışı mı? Komisyonu kim kazanıyor?
**Fırsat:** signals_archive'i public, imzalı, değiştirilemez track record sayfasına dönüştürmek — güven inşasının en hızlı yolu.
**Tehdit:** Edge'siz sinyal satışı bu segmentte bir hafta içinde teşhir edilir.
**Öneri:** (1) Public track record sayfası. (2) Read-only API beta. (3) "Sinyal" yerine "tarama+filtre aracı" konumlandırması (edge kanıtlanana dek).

## PERSPEKTİF 3: ERKEN AŞAMA ANGEL YATIRIMCI
**Kim:** Pre-seed/seed, ürün-öncesi traction kokusu arayan.
**İlk izlenim:** "Tek kişi bunu mu yaptı? Etkileyici mühendislik. Peki müşteri nerede?"
**Güçlü:** Yürütme hızı kanıtı (198 commit, 43'ü son 3 hafta); tam yığın yetkinlik (RL'den Next.js'e); sprint disiplini; düşük yakım oranı.
**Zayıf:** 0 kullanıcı, 0 gelir, 0 waitlist; moat belirsiz (yfinance+PPO+LLM kombinasyonu kopyalanabilir); tek kurucu riski; pazar konumu seçilmemiş (trader mı, öğrenen mi, B2B mi).
**5 soru:** Neden sen kazanırsın (founder-market fit)? İlk 100 kullanıcı planın ne? Hangi tek metriği büyütüyorsun? Veri flywheel'in nerede? 18 ayda nereye?
**Fırsat:** "Self-evolving finansal eğitim + sinyal verisi" hikâyesi — eğitim verisiyle kişiselleşen flywheel anlatısı fonlanabilir.
**Tehdit:** "Teknoloji arayan çözüm" etiketi.
**Öneri:** (1) 30 günde 100 waitlist kanıtı. (2) Tek north-star metrik seç. (3) Demo videosu + tek sayfalık memo.

## PERSPEKTİF 4: KURUMSAL VC FON YÖNETİCİSİ
**Kim:** Seri A, ARR/CAC/LTV diliyle düşünür.
**İlk izlenim:** "Pre-revenue, pre-user — bizim aşamamız değil. İzleme listesine."
**Güçlü:** Teknik altyapı seri-A sonrası ölçek sancılarını şimdiden çözmüş (cache, queue, audit, kalibrasyon); B2B API'ye dönüşebilir yüzey.
**Zayıf:** Pazar: retail sinyal uygulamaları mezarlık (churn %15-20/ay tipik); regülasyon (yatırım tavsiyesi sınırı) büyümeyi sınırlar; PLG kanıtı yok; rakip landscape (TradingView, Trade Ideas, Danelfin, Zorro...) kalabalık.
**5 soru:** Net revenue retention nasıl olacak? CAC kanalın ne, ölçeklenir mi? Regülasyon stratejin (tavsiye vs. araç) ne? Neden şimdi (timing)? Takım nasıl büyüyecek?
**Fırsat:** B2B API/white-label pivot'u — retail churn'ünden kaçıp altyapı geliri.
**Tehdit:** Retail B2C SaaS olarak kalırsa fonlanabilir hikâye yok.
**Öneri:** (1) Şimdi gelme — 12 ay sonra metriklerle gel. (2) B2B sinyalini erken test et (3 görüşme). (3) Unit economics'i ilk günden ölç.

## PERSPEKTİF 5: HİBE KOMİTESİ ÜYESİ (TÜBİTAK/Horizon/AWS Gründungsfonds)
**Kim:** Akademik özgünlük + toplumsal fayda + etik AI arar.
**İlk izlenim:** "Kalibrasyon, ablation, walk-forward MC — metodolojik olgunluk var. Yazılabilir proje."
**Güçlü:** XAI damarı (skor bileşenleri, ai_explain router'ı), Brier-tabanlı kalibrasyon + rollback, finansal okuryazarlık modülü (kapsayıcılık), grant_documents/ hazırlığı zaten başlamış.
**Zayıf:** Akademik yayın/ortak yok; etik AI çerçevesi (bias, uyarı metinleri) belgelenmemiş; Academy'nin pedagojik etki ölçümü yok; hibe dosyaları 5 Mayıs'tan beri dormant.
**5 soru:** Özgün bilimsel katkı nedir (ensemble DRL mi, kalibrasyon mu)? Etki nasıl ölçülecek? Veri etiği/KVKK planı? Akademik partner kim? Sürdürülebilirlik (hibe sonrası) planı?
**Fırsat:** "Açıklanabilir, kalibre edilmiş, eğitimle birleşik yatırım asistanı" — finansal kapsayıcılık çağrılarına cuk oturur.
**Tehdit:** "Ticari sinyal uygulamasına kamu parası" algısı — Academy öne konmazsa reddedilir.
**Öneri:** (1) Academy'yi başvurunun merkezine koy. (2) Bir üniversiteden ortak/danışman bul. (3) FINANZPLAN dosyasını güncel sistemle yenile.

## PERSPEKTİF 6: AKSELERATÖR PROGRAM MÜDÜRÜ (YC/Techstars)
**Kim:** Founder hızına ve öğrenme döngüsüne bakar.
**İlk izlenim:** "Build kası olağanüstü, talk-to-users kası hiç çalışmamış."
**Güçlü:** Haftada onlarca commit; kendi audit'ini yapıp NO EDGE bulacak kadar entelektüel dürüstlük (bu nadirdir ve mülakatta altın değerinde).
**Zayıf:** Tek varsayım bile gerçek kullanıcıyla test edilmemiş; "kimin, hangi acil problemi?" cevabı yok.
**5 soru:** Bu hafta kaç kullanıcıyla konuştun? İnsanlar bunun için ne bırakıyor (zaman/para)? MVP'nin en küçük hali ne? Neden bunu 10 yıl yapmak istiyorsun? İlk 10 kullanıcın isim isim kim?
**Fırsat:** "AI-native, tek kişilik, tam yığın fintech" profili 2026 batch'leri için çekici arketip.
**Tehdit:** Mülakatta "kullanıcı?" sorusunda sessizlik.
**Öneri:** (1) 2 hafta kod dondur, 20 yatırımcı/trader görüşmesi yap. (2) Tek cümlelik problem tanımı yaz. (3) Başvuruyu Academy-açısıyla değil, en hızlı traction alan açıyla yap.

## PERSPEKTİF 7: FİNTECH STARTUP KURUCU RAKİBİ
**Kim:** Aynı pazarda ürün geliştiren, zaaf arayan.
**İlk izlenim:** "Dağıtımı yok — şu an tehdit değil. Ama altyapısı benden iyi olabilir."
**Güçlü (onun gözünden tehditkâr):** Tam otomatik scheduler döngüsü; çok-agent mimarisi; Academy konsepti (kimsede yok); tek kişi = hızlı pivot.
**Zayıf (saldırı yüzeyi):** Marka/SEO/topluluk sıfır — aynı fikri dağıtımı olan biri 3 ayda pazara sürer; edge kanıtı yokken sinyal pazarına girerse itibar saldırısına açık.
**5 soru:** Veri kaynağı farklı mı (hayır — herkes yfinance/Alpaca)? Kullanıcı verisi birikiyor mu (henüz değil)? Patent/özgün algoritma var mı? Fiyat savaşına dayanır mı? Topluluğu kim?
**Fırsat (FinPilot için ders):** Kopyalanamaz olan tek şey birikecek kullanıcı-öğrenme verisi (Academy×sinyal kesişimi) — oraya koş.
**Tehdit:** Açık kaynak yapılırsa rakip altyapıyı bedavaya alır; yapılmazsa topluluk büyümez — bilinçli lisans kararı gerek.
**Öneri:** (1) Veri flywheel'i ilk günden tasarla. (2) Niş seç (örn. "öğrenen yatırımcı"), genel trader pazarında savaşma. (3) Track record'u markalaş(tır).

## PERSPEKTİF 8: FİNANSAL REGÜLATÖR / UYUM UZMANI (SEC/ESMA/SPK)
**Kim:** Yatırım tavsiyesi sınırını ve tüketici korumasını denetler.
**İlk izlenim:** "Sinyal + 'kazandırır' iması + otomatik işlem = lisans sorusu. Dikkat."
**Güçlü:** audit.py + audit_log (işlem izi), paper-trading-first yaklaşım, risk gate'leri (DD %3), açıklanabilirlik altyapısı.
**Zayıf:** Uyarı metinleri (disclaimer) envanteri belirsiz; "advisory" adlı router/agent — kelime seçimi bile risk; ABD hisseleri + TR kullanıcı = çifte yetki sorusu; KVKK/GDPR veri politikası belgesi yok; auto_trade loglari "otomatik emir" sınırına yaklaşıldığını gösteriyor.
**5 soru:** Yatırım danışmanlığı lisansın var mı / muafiyetin ne? Kullanıcı uygunluk testi yapıyor musun? Geçmiş performans sunumun SEC/ESMA pazarlama kurallarına uygun mu? Kişisel veri nerede, ne kadar tutuluyor? AI kararının gerekçesini kullanıcıya gösterebiliyor musun?
**Fırsat:** "Eğitim + araç" konumlandırması (tavsiye değil) — Academy bu açıdan da stratejik kalkan.
**Tehdit:** Outcome-based pricing veya oto-trade gibi modeller lisanssız yapılırsa varoluşsal risk.
**Öneri:** (1) Tüm yüzeylerde standart disclaimer + "advisory"yi yeniden adlandır. (2) Veri politikası sayfası. (3) Gelir modeli seçiminde uyum ön-kontrolü (özellikle Vizyon 3-4 için).

## PERSPEKTİF 9: FİNANSAL OKURYAZARLIK EĞİTMENİ
**Kim:** Pedagoji gözüyle Academy'ye bakar.
**İlk izlenim:** "İçerik mimarisi (4 seviye, mikro-içerik, yanlış kavramalar) pedagojik olarak doğru kurgulanmış. Ama boş bir okul."
**Güçlü:** Domain→Modül→Ders→Mikro hiyerarşisi; misconceptions + 'gerçek traderlar ne yapar' bölümleri (nadir görülen kalite); quiz+flashcard+simülasyon çeşitliliği; kişiselleştirme şeması.
**Zayıf:** Öğrenme çıktısı ölçümü tanımsız (quiz ≠ davranış değişikliği); LLM içeriğinin finansal doğruluk denetimi golden-set'siz; seviyelendirme (beginner/advanced) kalibre edilmemiş; eğitim-ticaret köprüsü ("öğrendiğini watchlist'inde uygula") kodda yok.
**5 soru:** Bir dersin "öğretildiğini" nasıl kanıtlarsın? Yanlış finansal bilgi yayılırsa sorumluluk zinciri ne? Spaced repetition var mı? İçerik kim tarafından (insan) örneklem denetiminden geçiyor? Davranışsal finans (Domain 9) sadece ders mi, ürüne gömülü uyarı mı?
**Fırsat:** "Trade etmeden önce bu dersi tamamla" köprüsü — eğitimi üründen ayrı değil, ürünün güvenlik kemeri yapmak. Dünyada iyi örneği az.
**Tehdit:** AI-üretimi içerik enflasyonu: 500 vasat ders < 50 mükemmel ders.
**Öneri:** (1) İlk 50 dersi insan denetiminden geçir, golden-set yap. (2) Ders→davranış metriği tanımla ("ders sonrası ilgili göstergeyi watchlist'te kullandı mı"). (3) Spaced repetition'ı flashcard motoruna ekle.

## PERSPEKTİF 10: AÇIK KAYNAK GELİŞTİRİCİSİ
**Kim:** GitHub'da yıldızlamadan önce repo hijyenine bakar.
**İlk izlenim:** "Pre-commit, ruff, mypy, alembic, 494 test — ciddi repo. Ama lisans/katkı altyapısı ve gerçek CI kanıtı eksik."
**Güçlü:** Modüler mimari, type-checking, conventional commits, kapsamlı Makefile.
**Zayıf:** README badge'leri placeholder; CONTRIBUTING yok; API dokümanı yayınlanmamış; sırlar .env'de ama örnek dosya drift'li; testlerin %'si bilinmiyor.
**5 soru:** Lisans gerçekten MIT mi kalacak (sinyal motoru dahil)? CI public mi? İlk dış katkıyı nasıl alırım? Plugin mimarisi var mı (archive'da plugins.py görüyorum — geri mi gelecek)? Veri sağlayıcı soyutlaması değiştirilebilir mi?
**Fırsat:** "Scanner çekirdeği açık + skor/DRL kapalı" open-core modeli — topluluk dağıtımı bedavaya gelir.
**Tehdit:** Tamamı açılırsa ticari moat erir; hiç açılmazsa bu kanal ölü.
**Öneri:** (1) Lisans stratejisine karar ver (open-core öner). (2) CI'ı görünür yap. (3) `indicators`+`data_fetcher`'ı ayrı PyPI paketi olarak dene (topluluk termometresi).

## PERSPEKTİF 11: FİNANSAL MEDYA / KÖŞE YAZARI
**Kim:** Hikâye arar, ürün değil.
**İlk izlenim:** "'Tek kişi, yapay zekâyla kendi kendini geliştiren yatırım okulu kurdu' — bu başlık tıklanır. 'Bir tarama uygulaması daha' tıklanmaz."
**Güçlü:** Self-evolving Academy anlatısı; kendi sistemine NO EDGE diyen kurucu dürüstlüğü ("AI hype çağında kendine karşı dürüst geliştirici" açısı); çok-agent mimarisi.
**Zayıf:** Başarı kanıtı yok (kullanıcı hikâyesi, kazanç hikâyesi); görsel demo yok; kurucu hikâyesi (neden bu problem?) anlatılmamış.
**5 soru:** Kim kullanıyor, hayatı nasıl değişti? Rakamın ne (kullanıcı, isabet, tasarruf)? Neden sen? Küçük yatırımcıya tarafsız mı (broker komisyonu alıyor musun)? AI yanılınca ne oluyor?
**Fırsat:** Build-in-public günlüğü (X/LinkedIn): "her hafta sistemin gerçek sinyal karnesini yayınlıyorum" — gazeteci için hazır malzeme üretir.
**Tehdit:** Kanıtsız "AI kazandırıyor" çıkışı ters haber döndürür.
**Öneri:** (1) Build-in-public'e başla. (2) 90 saniyelik demo videosu. (3) İlk 10 kullanıcının öğrenme hikâyesini belgele.

## PERSPEKTİF 12: GELECEKTEKİ KULLANICI (2027–2030)
**Kim:** GPT-sınıfı asistanların cebinde olduğu dünyada yaşıyor.
**İlk izlenim:** "Genel AI'm zaten hisse analiz ediyor. FinPilot bana ek olarak ne biliyor?"
**Güçlü:** Genel modellerin sahip olmadığı şeyler: benim öğrenme geçmişim, benim portföy davranışım, kalibre edilmiş yerel track record, 7/24 çalışan kişisel döngü.
**Zayıf:** Bugünkü değer önerisinin çoğu (tarama, gösterge, açıklama) 2027'de frontier modellerin bedava yan ürünü; alışkanlık yaratan döngü (streak, günlük brief) henüz yok.
**5 soru:** Verim sende mi birikiyor, modele mi gidiyor? Beni 2 yıl sonra da tanıyacak mısın (taşınabilir profil)? Genel asistanımla konuşabiliyor musun (MCP/API)? Alışkanlık mı ürettin, araç mı? Bensiz de değerli misin (ağ etkisi)?
**Fırsat:** "Kişisel finansal hafıza + eğitim grafiği" — genel modellerin asla sahip olamayacağı kullanıcı-özel veri katmanı. FinPilot'un 2030 sigortası bu.
**Tehdit:** Commodity özellik setiyle kalmak = sessiz buharlaşma.
**Öneri:** (1) Her özelliği "kullanıcı-özel veri biriktiriyor mu?" testinden geçir. (2) Günlük brief'i alışkanlık çapası yap. (3) MCP/API ile genel asistanlara eklenti olmayı şimdiden planla.

---

## 12 PERSPEKTİFİN ORTAK PAYDASI (sentez, G bölümüne girdi)

Aynı üç mesaj her gözden tekrar geliyor:
1. **Kanıt eksik** (P2, P3, P6, P11): track record, kullanıcı, öğrenme çıktısı — hepsi ölçülebilir ama hiçbiri yayınlanmıyor.
2. **Konum seçilmemiş** (P1, P4, P7, P8): trader aracı / öğrenen yatırımcı asistanı / B2B altyapı üçgeninde karar yok; regülasyon en az riskli olanı (eğitim+araç) işaret ediyor.
3. **Birikmeyen değer** (P7, P12): bugünkü özellikler kopyalanabilir; kopyalanamaz olan tek şey kullanıcı-öğrenme-davranış verisi — o da ancak Academy entegre olursa birikmeye başlar.
