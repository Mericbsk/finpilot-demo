# "Sıfırdan Çekseydin Ne Yapardık?" — Alternatif Vizyonlar ve Otomatik Gelir Modelleri

## 1) YÖNETİCİ ÖZETİ

**En iyi 3 vizyon:** (V7) Kişisel AI Yatırım Copilot'u — mevcut agent+scheduler altyapısının doğal ürünü, alışkanlık yaratır, edge kanıtı gerektirmez; (V6) Otomatik Bülten Flywheel — en hızlı başlatılabilir, %90 altyapı hazır, dağıtım motoru olur; (V10) Portföy İzleme + Uyarı — pasif kullanım, regülasyon-hafif, "uyuyan koruyucu" konumu rakipsiz değil ama FinPilot'un scheduler+telegram hattıyla 2 haftada MVP.
**Bu hafta başlanabilir 2 aksiyon:** (1) Landing+waitlist (tüm vizyonların ortak ön şartı), (2) weekly_report→Beehiiv otomatik bülten (V6 gün 1).
**Maksimum otomasyon kombinasyonu:** V6 (acquisition) + V7 (activation/retention) + V10 (premium tetiği) — üçü aynı scheduler'dan beslenir, haftalık insan emeği toplamı <5 saat.

## 2) SIFIRDAN BAKIŞ — 7 SORU

**1. En değerli varlık:** Otonom döngü altyapısı (scheduler+agents+rapor üretimi+telegram) — sinyalin kendisi değil, *sinyali üretip izleyip raporlayan insansız makine*.
**2. En az kullanılan boyutu:** Rapor/anlatı üretimi (report_generator 754 LOC, weekly_report, CEO raporu) — şu an tek okuyucusu Meriç. Aynı çıktı 10.000 kişiye gidebilir, maliyet değişmez.
**3. En büyük kör nokta (insan olsaydı):** "Önce mükemmelleştir, sonra göster" — kimsenin görmediği şeyi mükemmelleştiriyor. Kör nokta: dağıtım da bir mühendislik problemi ve o problem hiç ele alınmamış.
**4. Rakiplerin dokunmadığı, FinPilot'un doğal yapabileceği:** Eğitim ↔ gerçek sinyal verisi köprüsü: "dersteki örnek, bu haftanın gerçek taraması; sınavdaki senaryo, arşivdeki gerçek sinyal." Kurs platformlarında canlı veri yok, sinyal platformlarında pedagoji yok.
**5. 10.000 kullanıcıda en değerli veri:** Kullanıcı davranışı × sinyal sonucu kesişimi: kim hangi sinyale baktı, ne öğrendi, ne yaptı, sonuç ne oldu. Bu, hem kişiselleştirme hem de "retail davranış" veri seti olarak B2B değer.
**6. İnsan müdahalesi sıfırlansa otomatik üretilebilecek gelir:** Bülten aboneliği (üretim+gönderim otomatik), portföy uyarı aboneliği (scheduler izler, telegram uyarır), API metered billing. Üçü de "içerik/izleme" satar, "tavsiye" satmaz.
**7. Mevcut iş modelinin dayandığı varsayım:** "Skor edge üretir ve insanlar edge için öder." Bu varsayım şu an kendi audit'iyle ÇÜRÜTÜLMÜŞ durumda (decile_lift 0.728). Varsayım yanlışsa: değer, sinyalin doğruluğundan değil, *zamandan tasarruf + disiplin + öğrenme*den gelmeli — vizyonlar buna göre seçildi.

## 3) 10 VİZYON KARTI

### VİZYON 1: Yüksek Win-Rate Sinyal Makinesi ("az ama öldüren")
**Tek cümle:** Günde 1-3 yüksek-conviction sinyal; her biri geçmiş win-rate ve R/R kanıtıyla.
**Sıfırdan:** Scanner'ı 500 sembolden 50'ye daraltır, kaliteyi eşiklerle değil outcome-verisiyle filtrelerdim; signals_archive ilk günden public olurdu.
**Nasıl çalışır:** Tarama → conviction filtresi (kalibre olasılık eşiği) → günlük max 3 sinyal → otomatik T+5/T+10 sonuç güncelleme → public karne.
**Nakit:** Aylık $29-49 abonelik. 30 gün: $0 (kanıt dönemi); 90 gün: 50 abone ~$2k; 1 yıl: 300-500 abone $12-20k/ay (eğer win-rate gerçekse).
**Otomasyon:** Üretim %100 otomatik; haftada 2 saat insan (kalite gözü).
**İlk müşteri:** Public track record sayfası + X/Reddit'te haftalık karne paylaşımı.
**Altyapıdan:** scanner, calibration, signals_archive, outcomes_horizon, telegram — hepsi doğrudan. Yeniden yazılacak: conviction eşiği + public sayfa.
**Rakip:** Trade Ideas, sayısız Telegram kanalı. Fark: imzalı, değiştirilemez, kötü haftaları da gösteren karne.
**Risk:** **Edge yoksa bu vizyon YOKTUR.** Mevcut audit ters sinyal veriyor — bu vizyon ancak Sorun Kartı #1 çözülürse açılır.
**Ölçek:** Karne viral döngüsü. **Neden yapılmadı:** Herkes yapıyor ama kimse dürüst karne yayınlamıyor — çünkü çoğununki kötü. Dürüstlük = moat; ama önce matematik.

### VİZYON 2: Telegram/Discord Otomatik Gelir Kanalı
**Tek cümle:** Bot sinyal/brief dağıtır, Stripe abonelik tahsil eder, insan dokunmaz.
**Sıfırdan:** Web dashboard'u hiç yapmazdım; Telegram tek arayüz olurdu (TR pazarında zaten alışkanlık).
**Nasıl:** Public kanal (günlük brief, ücretsiz) → premium kanal (detay+anlık) → Stripe payment link → üyelik bot'u otomatik ekler/çıkarır.
**Nakit:** $15-25/ay. 30 gün: ilk 10-30 üye; 1 yıl: 200-500 üye $4-10k/ay.
**Otomasyon:** %95; haftada 1-2 saat moderasyon. **İlk müşteri:** TR finans Twitter/Reddit'te karne paylaşımı.
**Altyapıdan:** telegram_bot_runner hazır; eksik: Stripe webhook + üyelik yönetimi (3-5 gün).
**Rakip:** Binlerce sinyal kanalı (çoğu scam). **Risk:** İtibar kategorisi kirli; edge'siz sinyalle girilirse intihar — brief/karne diliyle girilmeli. **Neden yapılmadı:** Yapılıyor; FinPilot farkı otomasyon + dürüstlük; engel yine edge.

### VİZYON 3: Broker Referral / Komisyon Ekonomisi
**Tek cümle:** FinPilot bedava; gelir, kullanıcıların açtığı broker hesaplarının referral komisyonundan.
**Sıfırdan:** İlk gün IBKR/Alpaca/eToro affiliate anlaşmaları, ürün "broker'ına bağlan" akışıyla başlardı.
**Nasıl:** Ücretsiz tarama+eğitim → "uygula" butonu broker'a yönlendirir → CPA ($50-200/hesap) veya gelir paylaşımı.
**Nakit:** 1 yıl: ayda 50 hesap açılışı × $100 ≈ $5k/ay (yüksek trafik ister).
**Otomasyon:** %100. **Risk:** P8 çatışması — "bedava ama broker'a itiyor" tarafsızlık sorusu (P11 medya da sorar); TR'de yabancı broker tanıtımı regülasyon grisi. **Neden yapılmadı:** Yapılıyor (çoğu finans sitesinin gizli modeli); FinPilot için ancak İKİNCİL gelir katmanı olmalı, ana model değil.

### VİZYON 4: Sonuç Bazlı Fiyatlandırma
**Tek cümle:** Kullanıcı yalnız kazandığında öder ("kazandırdıysam %X").
**Değerlendirme:** En güçlü güven mesajı ama: P&L doğrulama (broker API zorunlu), fraud, ve en önemlisi **performans ücreti almak çoğu yargıda lisanslı danışman/fon faaliyetidir** (P8 perspektifi: varoluşsal risk). **Karar: REDDET** — yerine "kazanmadıysan iade" garantili normal abonelik (aynı psikolojik etki, sıfır lisans sorunu). **Neden yapılmadı sorusunun cevabı tam da bu:** regülasyon duvarı gerçek.

### VİZYON 5: AI Sinyal API'si — B2B Veri Servisi
**Tek cümle:** Kullanıcıya değil, fintech ürünlere satar: tarama/skor/rejim verisi API'den akar.
**Sıfırdan:** Frontend hiç yapılmaz; OpenAPI + docs portalı + Stripe metered billing ile pure-API şirketi kurulurdu.
**Nasıl:** API key + kota + tier (free 100 çağrı/gün → $99 → $499 → enterprise). Satılan şey "edge" değil "altyapı": çok-zaman-dilimli hizalama, earnings blackout, rejim etiketi, kalibre olasılık.
**Nakit:** 90 gün: 1-2 müşteri $0.5-1k/ay; 1 yıl: 5-10 müşteri $3-8k/ay.
**Otomasyon:** %95 (satış hariç). **İlk müşteri:** Robo-advisor/portföy uygulaması yapan 10 TR/EU fintech'e doğrudan ulaşım; indie hacker topluluğu.
**Altyapıdan:** api/ 21 router hazır; eksik: key yönetimi, rate limit, docs portalı (~2-3 hafta).
**Risk:** Tek müşteri konsantrasyonu; veri kaynağı lisansları (yfinance ToS! — Alpaca/Polygon ile temizlenmeli). **Neden yapılmadı:** Yapan var (Danelfin API vb.) ama TR/EU orta segment boş; FinPilot'un engeli sadece paketleme.

### VİZYON 6: Otomatik Bülten Flywheel ⭐
**Tek cümle:** Sistem her hafta kendi piyasa karnesini ve taramasını insansız yazıp gönderir; bülten hem gelir hem kullanıcı-edinme motorudur.
**Sıfırdan:** İlk yazdığım şey weekly_report→e-posta hattı olurdu; ürün, bültenin "premium eki" olarak doğardı (önce dağıtım, sonra ürün).
**Nasıl:** Pazar gecesi cron: scanner özeti + headroom-enriched haber bağlamı + geçen haftanın sinyal karnesi + 1 Academy dersi → Beehiiv API → gönderim. Ücretsiz sürüm: karne+özet; premium ($8-12/ay): tam shortlist+gerekçeler.
**Nakit:** 30 gün: $0-200; 90 gün: 1-2k abone, 30-60 premium ≈ $400-700/ay; 1 yıl: 8-15k abone, %4 dönüşüm ≈ $3-6k/ay + sponsorluk.
**Otomasyon:** Üretim/gönderim %100; haftada 1 saat son-okuma (ilk 6 ay önerilir).
**İlk müşteri:** X/LinkedIn build-in-public + Reddit r/algotrading'e metodoloji yazısı.
**Altyapıdan:** report_generator, weekly_report.py, agents, headroom — %90 hazır. Eksik: Beehiiv entegrasyonu + şablon (3-5 gün).
**Rakip:** Yüzlerce finans bülteni. Fark: **insan yazmıyor ve bunu saklamıyoruz** — "tamamen otonom analist" hikâyesinin kendisi pazarlama; + gerçek karne şeffaflığı.
**Risk:** İçerik kalitesi LLM-vasatlığına düşerse churn; ilk 6 ay insan son-okuma şart. **Neden yapılmadı:** Otonom üretim altyapısı (agents+rapor+karne verisi) kimsede birlikte yok; FinPilot'ta var.

### VİZYON 7: Kişisel AI Yatırım Copilot'u ⭐
**Tek cümle:** Kullanıcı her sabah tek kart alır: "Bugün senin için ne önemli" — portföyü, izlediği hisseler, öğrenme durumu ve piyasa bir arada.
**Sıfırdan:** 15 sayfalık dashboard yerine TEK ekran yapardım: sabah brief'i + soru kutusu. Bütün agent'lar bu tek kartın arkasında çalışırdı.
**Nasıl:** Gece scheduler: kullanıcının watchlist'i × tarama sonucu × haber × Academy ilerlemesi → kişisel 5 maddelik brief → push/Telegram/e-posta. Gün içinde "neden?" diye sorabilir (ai_explain hazır).
**Nakit:** Freemium: 1 portföy/3 hisse bedava; $9-15/ay sınırsız + anlık uyarı. 1 yıl: 500-1500 ödeyen ≈ $6-18k/ay.
**Otomasyon:** %95. **İlk müşteri:** Waitlist'ten 20 beta; her birine ilk hafta elle kalibrasyon (concierge MVP).
**Altyapıdan:** scheduler, agents/advisory, ai_explain, watchlist, telegram — neredeyse tamamı. Eksik: brief şablonu + tek-ekran UI (2 hafta).
**Rakip:** 2026'da herkes "AI copilot" diyor; fark: kullanıcının ÖĞRENME profili brief'i şekillendiriyor (Academy köprüsü) — genel asistanlar bunu bilmiyor (P12 moat'ı).
**Risk:** Brief sıkıcılaşırsa alışkanlık ölür; kişiselleştirme verisi birikene dek soğuk başlangıç. **Neden yapılmadı:** Copilot'lar genel; "eğitim grafiği + portföy davranışı" birleşimini kuracak veri modeli kimsede yok.

### VİZYON 8: Topluluk Zekâsı — Kolektif Sinyal Platformu
**Tek cümle:** Kullanıcılar tahmin/sinyal girer, sistem her birinin karnesini otomatik tutar, en iyiler öne çıkar.
**Nasıl:** Tahmin girişi → outcomes_horizon ile otomatik puanlama → lider tablosu → en iyilerin akışı premium.
**Nakit:** Premium izleme $10/ay + ileri aşamada gelir paylaşımı. **Otomasyon:** Puanlama %100; moderasyon insan ister (haftada 5+ saat).
**Risk:** Soğuk başlangıç ağ etkisi problemi (boş platform); manipülasyon; pump-grupları çekme riski. **Karar:** 1.000+ kullanıcıdan önce AÇMA — V6/V7 kitlesi üzerine 2. yıl katmanı. **Neden yapılmadı:** Stocktwits/eToro var ama "otomatik doğrulanmış karne" yok — FinPilot'un outcome altyapısı tam bunu yapar; engel kitle.

### VİZYON 9: White Label / Franchise
**Tek cümle:** Eğitmenler ve broker'lar FinPilot'u (özellikle Academy'yi) kendi markasıyla satar.
**Nasıl:** Tenant'lı kurulum: logo/renk/domain + içerik seti seçimi; $5-15k kurulum + $500-1500/ay veya gelir paylaşımı.
**İlk müşteri:** TR'deki finans eğitmenleri/YouTuber'lar (kitlesi var, teknolojisi yok) — Academy white-label'ı sinyalden daha kolay satılır ve regülasyon-hafif.
**Otomasyon:** Kurulum sonrası %90; satış+destek insan işi (haftada 5-10 saat/müşteri başı ilk ay).
**Risk:** Tek kişiyle kurumsal SLA taahhüdü; markanın başkasının eline geçmesi. **Karar:** 2. yarıyıl; ilk 1-2 pilot eğitmenle. **Neden yapılmadı:** LMS white-label var, "canlı piyasa verili finans academy" white-label'ı yok; engel: önce kendi Academy'nin kanıtı.

### VİZYON 10: Otomatik Portföy İzleme + Uyarı ("uyuyan koruyucu") ⭐
**Tek cümle:** Kullanıcı portföyünü bağlar/girer; sistem 7/24 izler, yalnız kritik anda konuşur: "XYZ'de momentum kırıldı, earnings 3 gün sonra."
**Sıfırdan:** "Sinyal üret" yerine "sahip olunanı koru" ile başlardım — pazar 10x daha geniş (herkes pozisyon taşır, az kişi aktif trade eder) ve tavsiye değil İZLEME sattığı için regülasyon-hafif.
**Nasıl:** Portföy girişi (CSV/manuel; sonra broker API read-only) → scheduler her saat kontrol: trend kırılımı, ATR spike, earnings blackout, DD eşiği → eşik aşımında push/Telegram. Uyarı yoksa SESSİZ (anti-spam = güven).
**Nakit:** 3 pozisyon bedava; $7-12/ay sınırsız+anlık. 90 gün: 50-100 ödeyen; 1 yıl: 1-3k ödeyen ≈ $10-25k/ay.
**Otomasyon:** %98 — bu vizyonun bütün mekaniği zaten scheduler+indicators+earnings_blackout+telegram olarak YAZILMIŞ durumda; eksik yalnız portföy-giriş UI'sı ve uyarı kişiselleştirmesi (~2 hafta).
**Rakip:** Broker uygulamalarının ilkel alarmları (fiyat eşiği); fark: bağlam-bilen uyarı ("fiyat düştü" değil "trend yapısı bozuldu + earnings yaklaşıyor + senin maliyetine göre R düşüyor").
**Risk:** Yanlış-alarm oranı yüksekse güven biter; uyarı eşiği kalibrasyonu işin %80'i. **Neden yapılmadı:** Pull-tabanlı uygulama kültürü (kullanıcı açar bakar) — push-tabanlı sessiz koruyucu UX'i yeni; FinPilot'un izleme altyapısı hazır olduğu için first-mover şansı gerçek.

## 4) KARŞILAŞTIRMALI TABLO

| # | Vizyon | Otomasyon | İlk gelir | 12 ay potansiyel | Teknik yük | İnsan saat/hafta | Altyapı uyumu |
|---|---|---|---|---|---|---|---|
| 1 | Win-rate makinesi | %95 | 60-90 gün | $12-20k/ay | Orta | 2 | Yüksek ama **edge'e kilitli** |
| 2 | Telegram kanalı | %95 | 2-4 hafta | $4-10k/ay | Düşük | 1-2 | Çok yüksek |
| 3 | Broker referral | %100 | 60+ gün | $3-5k/ay | Düşük | 1 | Orta (trafik ister) |
| 4 | Outcome pricing | — | — | — | — | — | **RED (regülasyon)** |
| 5 | B2B API | %95 | 30-60 gün | $3-8k/ay | Orta | 3-5 | Yüksek |
| 6 | **Bülten flywheel** | %95 | 30-60 gün | $3-6k/ay + liste | Düşük | 1 | **%90 hazır** |
| 7 | **Kişisel copilot** | %95 | 45-60 gün | $6-18k/ay | Orta | 2-3 | **%80 hazır** |
| 8 | Topluluk zekâsı | %80 | 6+ ay | Yüksek (geç) | Yüksek | 5+ | Orta (kitle yok) |
| 9 | White label | %90 | 90+ gün | $2-5k/ay/müşteri | Orta | 5-10 | Orta |
| 10 | **Portföy koruyucu** | %98 | 30-45 gün | $10-25k/ay | Düşük | 1-2 | **%85 hazır** |

**Bu hafta başlanabilir:** V6, V10. **En yüksek 12-ay:** V10, V7 (V1 edge şartlı). **En az emek:** V3, V6, V10. **En mantıklı kombinasyon:** **V6 → V7 → V10 zinciri** — bülten kitle toplar, copilot alışkanlık yapar, koruyucu premium'a çevirir; üçü aynı scheduler/agent altyapısından beslenir, birbirinin pazarlamasıdır.

## 5) "SIFIRDAN ÇEKSEYDİN" KARAR TABLOSU

| Alan | Bugünkü karar | Sıfırdan yapılacak | Neden farklı | Geçiş maliyeti |
|---|---|---|---|---|
| Para modeli | (Yok — varsayım: SaaS) | İzleme+içerik aboneliği; tavsiye asla | Edge kanıtsız + regülasyon | Düşük — sadece karar |
| Edinme kanalı | (Yok) | Otonom bülten + build-in-public | İçerik makinesi zaten var | Düşük (1 hafta) |
| Sinyal dağıtımı | Dashboard'a çek (pull) | Push: brief/uyarı; dashboard detay için | Alışkanlık push'ta kurulur | Orta (UI sadeleşmesi) |
| Fiyatlama | (Yok) | Freemium: 3 pozisyon/1 portföy bedava | Değer anı önce, ödeme sonra | Düşük |
| Onboarding | 15 sayfalık dashboard | 3 soru → ilk brief 60 saniyede | P1 perspektifi kayboluyor | Orta |
| İnsan müdahale noktaları | Her yerde örtük | Yalnız: içerik son-okuma + müşteri konuşması | Geri kalanı watchdog'lu cron | Düşük |
| Ölçekleme | Dikey (özellik ekle) | Yatay (aynı çıktıyı N kullanıcıya) | Rapor üretiminin marjinal maliyeti ~0 | Düşük |
| Veri birikimi | Sistem-verisi (sinyal) | Kullanıcı-verisi (davranış×öğrenme×sonuç) | Kopyalanamaz olan bu | Orta (event şeması) |
| Topluluk | Yok | Bülten yanıtları + Telegram'dan organik | Soğuk platform kurma (V8 erken) hatası önlenir | — |
| Stack | Python+Next.js+SQLite | Aynı (doğru seçim) + Postgres'e erken geçiş | Eşzamanlı yazma duvarı | Orta (alembic hazır) |

## 6) "NEDEN HENÜZ KİMSE YAPMADI?" — EN YENİLİKÇİ 3

**V10 Portföy Koruyucu:** Engel teknik değil kültürel — finans uygulamaları engagement (açılış sayısı) optimize eder; "az konuşan" ürün metriklerini öldürür, o yüzden büyükler yapmaz. FinPilot abonelikle (engagement'la değil) para kazanacağı için sessizlik satabilir. First-mover süresi: 12-18 ay (broker'lar kopyalar ama alarm kültürünü değiştiremez). Eksik tek şey: portföy giriş UI'sı + eşik kalibrasyonu.
**V7 Öğrenme-bilen Copilot:** Engel veri modeli — copilot yapanlar (broker'lar, genel AI) kullanıcının *bilgi seviyesini* modellemiyor; eğitim platformları da *portföyü* görmüyor. İki grafiği birleştiren şema FinPilot'ta (academy.models × watchlist × outcomes) fiilen kurulu. First-mover: 18-24 ay. Eksik tek şey: Academy'nin canlıya alınması (Bölüm H, hafta 1-3).
**V6 İnsansız Bülten (şeffaf otonom):** Engel itibar cesareti — herkes AI ile yazıyor ama insan-yazmış gibi sunuyor; "bunu makine yazdı ve karnesi burada" demek markalaşma riski sayılıyor. FinPilot için bu dürüstlük (NO EDGE audit'ini yayınlayabilen kültür) zaten karakter. First-mover: 6-12 ay (kopyalanır ama 'ilk dürüst otonom analist' unvanı kopyalanmaz). Eksik tek şey: Beehiiv entegrasyonu.

## 7) OTOMATİK GELİR MİMARİSİ (5 katman)

| Katman | Mekanizma | Besleyen vizyon | Otomasyon | İnsan saat/hafta | Beklenen katkı (12 ay) |
|---|---|---|---|---|---|
| 1 Acquisition | Haftalık otonom bülten + public karne sayfası + build-in-public | V6 (+V1 karnesi) | %95 | 1 (son-okuma) | 8-15k e-posta listesi |
| 2 Activation | 3-soru onboarding → 60 saniyede ilk kişisel brief + günlük Academy kartı | V7 + Bölüm H | %100 | 0 | Kayıt→aktif %40+ |
| 3 Revenue | Abonelik: koruyucu uyarılar ($7-12) + copilot premium ($9-15) + API tier | V10, V7, V5 | %98 (Stripe) | 0.5 | $10-25k MRR hedef |
| 4 Retention | Streak + sessiz-ama-isabetli uyarı + kişiselleşen brief + spaced repetition | V7, V10, H | %100 | 0 | Aylık churn <%6 hedef |
| 5 Referral | "Bu brief'i arkadaşına ilet" + bülten içi referral + affiliate (broker İKİNCİL) | V6, V3 | %100 | 0 | Yeni kullanıcının %20'si |
| **Toplam** | | | **~%97** | **<5 saat/hafta** | |

## 8) 90 GÜN UYGULAMA PLANI → ayrıntı `08-90-gun-plani.md`

## 9) SON KARAR

Üç vizyonun zinciri (V6 bülten → V7 copilot → V10 koruyucu), Academy (H) ile birlikte tek bir üründe birleşir: **"Seni tanıyan, senin için izleyen, sana öğreten otonom finans yardımcısı."** Sinyal-doğruluğu iddiası, edge kanıtlanana kadar vitrine çıkmaz; kanıtlanırsa V1 premium katman olarak açılır.

"FinPilot'un sıfırdan çekilmiş resmi şunu gösteriyor: Mevcut teknik güç zaten var — eksik olan şey, bu gücü doğru kanala, doğru modele ve minimum insan müdahalesine yönlendiren netlik ve cesarettir."
