# FinPilot — KULLANICIYA ÇIKIŞ İŞ PLANI
## Tek Hedef · Tek Odak · Uçtan Uca Çalışana Kadar Başka Hiçbir Şey

**Tarih:** 2026-07-05 · **Taban:** Ticari Katman Uygulama Planı (3 Tem, kodu yazıldı ve doğrulandı) + GTM kapıları.
**Bu planın işi:** Var olan bileşenlerin KALİTESİNİ yükseltmek, İÇERİĞİNİ zenginleştirmek ve sistemi gerçek kullanıcıya çıkabilir hale getirmek. Yeni özellik planı DEĞİLDİR.

---

## 0. GÖRÜŞÜM (net)

Doğru içgüdü — ve tam zamanı. Kod iskeleti bitti; şu andan itibaren en büyük risk teknik değil, **odak kaybı**. Üç tuzağı baştan kapatmalıyız:

1. **Yeniden-tasarım cazibesi:** Ledger×Classroom tasarımını çok sevdik ama o bir V2 işidir. İlk kullanıcıya mevcut (yeniden çerçevelenmiş, temiz) arayüzle çık; tasarımı ilk 25 kullanıcının gerçek feedback'iyle yap. Beğenilmeyen bir üründe güzel tasarım israftır; beğenilen üründe tasarım katlanır. → Master tasarım bu planda **dondurulmuştur** (Claude Design'da denemek serbest — koda dokunmak yasak).
2. **İçerik monotonluğu:** Sistemin en çok "insan eli değmiş" hissetmesi gereken yeri günlük brif metnidir. Template'ten çıkan 2 cümle üç gün sonra kendini tekrar eder — bu planın en büyük kalite yatırımı içerik katmanınadır (Bölüm 3).
3. **"Bitti" yanılgısı:** Kod yazıldı ≠ sistem çalışıyor. Bu plan "çalışır" kanıtını 10 maddelik ölçülebilir bir lansman tanımına bağlar (Bölüm 1) ve her hafta bir kapıdan geçer.

Süre: **6 hafta.** İlk 2 hafta kalite+altyapı, 2 hafta canlı prova, 2 hafta gerçek kullanıcı. Bu tempoda 6. haftanın sonunda "kullanıcıda, kesintisiz, günlük çalışan" bir sistem olur.

---

## 1. TEK HEDEF VE LANSMAN TANIMI (DoD)

> **HEDEF:** 6. haftanın sonunda FinPilot; her sabah kesintisiz brif yayınlayan, web'de dünün gerçek sayısını gösteren, en az 25 gerçek kullanıcının takip ettiği, geri bildirim toplayan, uçtan uca otomatik bir sistem olarak KULLANICIDADIR.

"Kullanıcıya çıkabilir" = aşağıdaki 10 maddenin HEPSİ (kısmi sayılmaz):

| # | Kriter | Ölçüm |
|---|---|---|
| 1 | 10 ardışık işlem günü kesintisiz brif yayını | broadcast_queue: 10 sent, 0 hatalı |
| 2 | Sabah operasyonu ≤15 dk/gün (onay dahil) | 1 hafta ölçüm |
| 3 | www.finpilot.at yeni landing + demo canlı, mobilde kusursuz | 3 cihaz testi + Lighthouse ≥85 |
| 4 | Demo her gün otomatik taze snapshot alıyor | 5 gün üst üste tarih kontrolü |
| 5 | Karne verisi gerçek ve web'de görünür (by_grade dolu) | snapshot.karne ≠ null, n>0 |
| 6 | Brif içeriği "insan yazmış" kalitesinde | Bölüm 3 içerik DoD'u + 3 dış okuyucu testi |
| 7 | ≥25 aktif takipçi (kanal) + ≥10 beta dashboard kullanıcısı | tg üye + davet kodu kullanımı |
| 8 | ≥15 feedback kaydı toplandı ve 2 Cuma ritüeli yapıldı | demo_feedback + tg_feedback |
| 9 | Premium mekaniği test modunda uçtan uca kanıtlı (satış KAPALI) | test ödeme→davet→iptal→çıkarma logu |
| 10 | Kırmızı gün prosedürü 1 kez tatbik edildi | bilinçli hata → düzeltme mesajı akışı |

## 2. KAPSAM DONDURMA — "YAPILMAYACAKLAR" SÖZLEŞMESİ

6 hafta boyunca şunlara **dokunulmaz** (yeni fikirler `PARKING_LOT.md`'ye yazılır, tartışılmaz):

Ledger×Classroom kod uygulaması · yeni skor faktörü/ablation · DRL her şeyi · FinSense fabrikası (Finsense repo) geliştirme · hibe dokümanları · Tauri/masaüstü · Postgres geçişi · canlı işlem · alert sistemi · mobil uygulama · yeni veri sağlayıcı · dashboard yeni sayfa.

**Tek istisna kuralı:** Lansman DoD'unu doğrudan bloke eden bir şey çıkarsa (ör. veri hattı kırığı) kapsamdadır — "güzel olur"lar değildir.

## 3. BİLEŞEN KALİTE MATRİSİ (mevcut → hedef → işler → kabul)

### 3.1 İçerik katmanı (en büyük yatırım — toplam ~6 gün)
| Bileşen | Mevcut | Hedef | Yapılacaklar | Kabul kriteri |
|---|---|---|---|---|
| Gerekçe cümleleri | 9 sabit fragment, birleşik tek kalıp → 3 günde monotonlaşır | Her rozet için 4-5 varyant + bağlam kuralları (fiyat bandı, ATR seviyesi, rejime göre ton) + deterministik seçim (tarih+ticker seed → aynı gün aynı metin) | `rationale.py` fragment havuzu ×5; kombinasyon kuralları; 30 örnek çıktının elle okunması | 10 ardışık günün brifleri yan yana: hiçbir cümle birebir tekrar değil; 3 dış okuyucu "insan yazmış" diyor |
| Market bağlam satırı | Yok (şablonda yer var) | Günlük 1 cümle: rejim + endeks + varsa makro olay | FRED rejim + endeks kapanışı → template; LLM YOK (v1) | Her brifte dolu, lint temiz |
| Risk notları | 3 kalıp | 8-10 kalıp + faktör kombinasyonuna özel (squeeze+düşük fiyat ≠ sadece squeeze) | `_risk_note` genişletme | Aynı hafta içinde aynı not ≥3 kez görünmüyor |
| Günün kavramı | 12 terim | **30 terim** TR+EN, her biri brif-cümlesi + web kartı + 1 gerçek örnek referansı | concepts.py + terms.ts eş genişletme (tek kaynak tablo, ikisi ondan üretilir) | 30 gün tekrarsız rotasyon; iki dosya senkron testi |
| Haftalık sayı | Template iskeleti | Gerçek editoryal format: karne yorumu (iyi+kötü), haftanın vakası (arşivden), haftanın dersi | İlk 2 sayıyı BİRLİKTE yazarız (sen+ben), 3.'den itibaren yarı-otomatik | 2 örnek sayı hazır ve onaylı |
| Metodoloji sayfası | Yok | Web'de tek sayfa: Grade nedir, ≥%5 hedefi ne ölçer/ölçmez, kalibrasyon, veri kaynakları | Statik sayfa (İng.) | Karne linkleri buraya gidiyor; dış okuyucu anlıyor |
| Örnek premium sayı | Yok | 1 adet tam, gerçek, tarihli örnek (funnel'ın silahı) | En iyi gerçek günden derlenir | Lint temiz, offer page'e gömülü |

### 3.2 Veri/motor güvenilirliği (~4 gün)
| Bileşen | Mevcut | Hedef | İşler | Kabul |
|---|---|---|---|---|
| Sabah taraması | Manuel tetik | **Otomatik 07:15 job'u** (bilinen tek boşluk) + başarısızsa 07:40 acil DM | scheduler'a scan job (mevcut /scan mantığını çağıran wrapper) | 5 gün elle dokunmadan export üretildi |
| Snapshot kalitesi | Çalışıyor, karne bağı yeni | Karne HER gün dolu; grade dağılımı sağlıklı (A nadir, C şişkin değil → eşik gözden geçirme) | 1 hafta gerçek çıktı gözlemi + eşik ayarı (yeni faktör YOK, sadece mevcut eşikler) | 5 günlük çıktıda A≤2/gün, toplam aday 5-12 bandı |
| Arşiv sürekliliği | Alarm yok | "Son 24s kayıt yok → DM" alarmı (Audit 7g maddesi) | scheduler'a mini job | Test edildi |
| DB sağlığı | finpilot.db geçmişte bozulmuş | Haftalık otomatik yedek (finpilot.db + distribution.db → dated kopya) + integrity check job'u | 20 satır script + cron | İlk yedek alındı, restore provası yapıldı |
| Dosya bütünlüğü riski | 17 dosya kesilmişti (disk/senkron şüphesi) | Kök neden tespiti: OneDrive/AV taraması kontrolü (SEN) + haftalık `ast-parse-all` CI adımı | CI'a syntax-sweep | 2 hafta temiz |

### 3.3 Dağıtım yüzeyleri (~4 gün)
| Bileşen | Mevcut | Hedef | İşler | Kabul |
|---|---|---|---|---|
| Hosting | Tamamen lokal | Vercel (web) + VPS public-API canlı, finpilot.at bağlı | Uygulama Planı Bölüm 1 aynen; CORS/CSP/env ayarları hazır | DoD #3-4 |
| Landing | Dürüst dile çevrildi | Metin cilası + gerçek karne rakamı canlı + waitlist çalışır | küçük revizyon | dış okuyucu 10-sn testi |
| Demo | Yeniden çerçevelendi | Gerçek snapshot'la 5 gün sorunsuz; feedback ucu canlı | E2E kontrol | DoD #4, #8 |
| Telegram bot+kanal | Kod hazır, kanal yok | Kanal açık, 10 gün prova yayını, /today gerçek | Kurulum (SEN) + prova | DoD #1 |
| Onay akışı | Kod hazır | Telefondan ≤10 dk gerçek kullanım | 1 hafta ritim provası | DoD #2 |
| Premium mekaniği | Kod hazır | Stripe test modunda uçtan uca kanıt (satış kapalı) | Stripe hesabı (SEN) + test | DoD #9 |

## 4. HAFTALIK PROGRAM (6 hafta · her hafta tek tema + kapı)

**HAFTA 1 — "İçerik + Otomasyon temeli"** *(ben: içerik katmanı 3.1'in kod işleri + sabah tarama job'u + yedek/alarm job'ları · sen: domain/Vercel/VPS hesapları, OneDrive-AV kontrolü, BotFather kanal kurulumu)*
→ **Kapı:** lokalde 3 ardışık gün tam otomatik brif taslağı (zengin içerikle) üretildi; hosting hesapları hazır.

**HAFTA 2 — "Canlıya taşıma"** *(ben: Vercel+VPS deploy, metodoloji sayfası, 30 terim, snapshot eşik gözlemi · sen: DNS bağlama, Plausible/Sentry, günlük onay ritmine başlama — henüz kanal beta-özel)*
→ **Kapı:** finpilot.at yeni haliyle canlı; kanal beta modunda ilk gerçek 08:30 yayını yapıldı.

**HAFTA 3 — "Prova haftası"** *(10 kişilik iç beta: tanıdıklar kanalda + 5'i dashboard'da; her gün gerçek yayın; ben: çıkan pürüzler + haftalık sayı 1'i birlikte yazmak · sen: günlük onay + 5 kısa kullanıcı sohbeti)*
→ **Kapı:** 5 ardışık kesintisiz yayın günü; insan yükü ölçüldü ≤15 dk; ilk 5 feedback.

**HAFTA 4 — "Sertleştirme"** *(prova bulguları kapatılır; kırmızı-gün tatbikatı — bilinçli yanlış veri → düzeltme mesajı prosedürü; DB restore provası; premium test-modu uçtan uca; haftalık sayı 2)*
→ **Kapı:** DoD #9 ve #10 tamam; 10 ardışık yayın günü sayacı işliyor.

**HAFTA 5 — "Yarı-açık lansman"** *(kanal linki waitlist'e + demo'ya; build-in-public ilk paylaşımlar; beta daveti 15→25; ilk Cuma ritüeli tam formatta)*
→ **Kapı:** 25+ takipçi; feedback ≥10; açılma oranı ölçülüyor.

**HAFTA 6 — "Stabilizasyon + değerlendirme"** *(hiçbir yeni şey; sadece ritim + ölçüm + küçük düzeltme; 2. Cuma ritüeli; 10 maddelik DoD denetimi birlikte)*
→ **Kapı:** **LANSMAN TANIMI KARŞILANDI** → sonraki dönem kararı (tasarım V2 mi, premium açılışı mı — karne yaşına göre GTM kuralı).

## 5. ÇALIŞMA RİTMİ (senin haftan)

- **Her sabah (hafta içi) 08:00-08:20:** taslak DM'ini oku → ONAYLA/RED (+gerekirse tek cümle düzelt). Bu ritüel kutsaldır; kaçarsa gün sessiz geçer, telafi mesajı atılmaz.
- **Pazartesi 15 dk:** haftalık kapı kontrolü (bu dosyadaki checklist).
- **Cuma 45 dk:** feedback + metrik ritüeli → 1 karar → kanala "duyduk→yaptık" satırı.
- **Fikir geldiğinde:** `PARKING_LOT.md`'ye tek satır. Cuma'da 5 dk bakılır, 6 hafta boyunca hiçbiri işleme alınmaz.

## 6. İLERLEME TAKİBİ

- Repo köküne `LAUNCH_CHECKLIST.md` konur (10 DoD + haftalık kapılar, işaretlenebilir) — tek doğruluk kaynağı; her Pazartesi birlikte güncellenir.
- Sayaçlar otomatik: kesintisiz yayın günü (broadcast_queue'dan), abone, feedback sayısı → haftalık rapor cron'u zaten üretiyor.

## 7. RİSKLER VE SAPMA KURALLARI

| Risk | Erken sinyal | Kural |
|---|---|---|
| Tasarım cazibesi | "Şu ekranı da yenileyelim" | Parking lot. V2 sözü: lansman DoD'u sonrası İLK iş |
| İçerik yorgunluğu (senin) | Onay ritüeli angarya hissi | Sorun formatta demektir → Cuma'da format revizyonu, ritüel atlanmaz |
| Tarama sabahı kırılırsa | 07:40 acil DM | O gün sessiz + gün içinde kök neden; 2 kez üst üste olursa hafta teması değişir (istisna kuralı) |
| Beta feedback'i kapsamı büyütmeye zorlar | "Şu özellik olsa..." ≥3 kişi | Kural-of-3 bile 6 hafta içinde SADECE parking lot'a girer; lansman sonrası ilk sprint adayı |
| Dosya kesilmesi tekrarı | CI syntax-sweep kırmızı | O gün her şey durur, kök neden (disk/senkron) çözülür — veri bütünlüğü her şeyden önce |

---
**Özet söz:** 6 hafta boyunca tek soru sorulur: *"Bu iş, 10 maddelik lansman tanımına hizmet ediyor mu?"* Etmiyorsa yapılmaz. Onaylarsan Hafta 1'in benim tarafımdaki işlerine (içerik katmanı zenginleştirme + sabah tarama job'u) hemen başlarım ve `LAUNCH_CHECKLIST.md`'yi oluştururum.
