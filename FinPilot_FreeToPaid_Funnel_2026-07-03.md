# FinPilot — Free-to-Paid Funnel Tasarımı
## Ücretsiz Kullanıcıdan İlk Ödeyen Kullanıcıya: Mesajlaşma · Fiyatlama · Dönüşüm · Retention

**Tarih:** 2026-07-03 · **Üst dokümanlar:** GTM Lansman Planı (fiyat çapaları, 4-hafta karne kapısı), Telegram Bot MVP (premium gating mekaniği), Web Demo Spec (funnel giriş kapısı). Bu doküman o üçünün **dönüşüm katmanını** tek akışta birleştirir ve derinleştirir.
**İlke:** İlk para, büyüklüğü için değil; gerçek değer karşılığında ödeme alma sinyali olduğu için önemlidir.

---

## 1. YÖNETİCİ ÖZETİ

Bu funnel maksimum dönüşüm için değil, **öğrenerek dönüşüm** için tasarlandı: ilk 5-10 ödeme, "kim, neye, neden ödüyor" sorusunun cevabıdır — gelir değil, ürün yönü verisidir. Tasarımın üç direği:

1. **Değer önce, teklif sonra:** 4 hafta boyunca hiçbir satış mesajı yok; karne + günlük brif güveni biriktirir. Teklif, kullanıcının *zaten hissettiği* eksikliğin (karne satırındaki "bugün 7 aday vardı, 2'sini gördün") adlandırılmasıdır — yaratılmış kıtlık değil, gerçek fark.
2. **Tek premium nesne, iki paket:** Premium = derin günlük brif + Tier B kapsamı + risk notları + haftalık tam analiz. Paketler: Founding Member (20 kişi, €99/yıl, kalıcı ayrıcalık) ve standart aylık (€9). Lifetime (10 adet, €149) yalnız nakit + taahhüt sinyali için.
3. **Sürtünmesiz mekanik:** Stripe Payment Link → webhook → otomatik private-kanal daveti (Telegram dokümanında kuruldu). Ödeme ile değer teslimi arasında insan yok, bekleme yok.

**30 gün hedefi (premium açılışından itibaren):** ≥%10 premium-ilgi (tık), ≥%2 ödeme dönüşümü, ilk 10 ödemenin ≥7'si 30. günde hâlâ aktif okuyucu, churn nedenlerinin %100'ü kayıtlı.

---

## 2. FUNNEL'IN AMACI

Öncelik sırası: **(1) öğrenme** (ödeme sinyalinin kimden ve neden geldiği), **(2) ilk 5-10 doğru ödeme** (referans + güven çekirdeği), **(3) segment ayrıştırma** (kim asla ödemez → onlara farklı değer yolu), **(4) premium değer teklifinin testi**. Maksimum dönüşüm bilinçli olarak hedef değil — erken agresif dönüşüm, yanlış kullanıcıyı içeri alır ve churn/güven maliyeti öğrenme değerini aşar.

- **Premium'a yakın kullanıcı:** her sabah brifi açan + karneye dönen + ⓘ kartlarını kurcalayan + /premium'a kendiliğinden tıklayan aktif takipçi.
- **Ücretsiz kalması doğru kullanıcı:** haftada 1-2 açan pasif meraklı, yalnız öğrenme amaçlı gelen (FinSense yolu — ileride kendi premium'u), ve "kesin kazanç" arayan sadakatsiz kullanıcı (dönüştürme; hayal kırıklığı churn'ü ve kötü yorum üretir).
- **Ücretsiz kullanıcı neden kalır:** sabah ritüeli (sabit saat, 1 mesaj), gerçek içerik (dünün değil o sabahın adayları), açık karne (merak + güven), günün kavramı (birikimli öğrenme hissi).

## 3. KULLANICI SEGMENTLERİ

| Segment | Dönüşüm ihtimali | Tepki verdiği değer | Onu taşıyan içerik | Uygun teklif |
|---|---|---|---|---|
| Meraklı pasif | Düşük (%0-1) | Merak tatmini | Karne + kavramlar | Teklif gösterme; kitle/yayılım değeri |
| Aktif trader adayı | **Yüksek (%5-10)** | Kapsam + derinlik + zaman tasarrufu | Tam aday listesi, faktör dökümü | Founding €99/yıl (kimlik + ayrıcalık dili) |
| Gerçek piyasa takipçisi | Orta-yüksek (%3-6) | Güvenilir günlük süzgeç | Brif düzeni + izleme güncellemeleri | Aylık €9 (düşük taahhüt girişi) |
| Sadece öğrenmek isteyen | Düşük şimdi (FinSense sonrası orta) | Anlama, jargon çözme | ⓘ kartlar, replay'ler | Şimdi teklif yok → FinSense premium (90+ gün) |
| İçgörü/watchlist isteyen | Orta (%2-4) | "Ne izlemeliyim" netliği | Tier B listesi + risk notları | Aylık €9; watchlist özelliği beta dashboard'a bağlar |
| Hızlı sonuç bekleyen sadakatsiz | Negatif değer | "Kesin sinyal" (veremeyiz) | — | **Bilinçli dönüştürmeme**; disclaimer dili bunları doğal filtreler |

Segment tespiti pasif etiketlerden: katılım kaynağı, açma düzeni, tıklama türü (karne mi aday mı kavram mı), /premium tıkı. İlk 10 ödemede her ödeyenin segmenti kaydedilir — funnel'ın asıl çıktısı bu tablodur.

## 4. ÜCRETSİZ KATMAN TASARIMI

**Denge ilkesi:** tatmin edici VE eksik hissettiren — çelişki değil, sıralama: önce tatmin (tek başına takip etmeye değer), sonra eksikliğin *görünürlüğü* (kısıtlanmış değil, kapsamı belli).

- **Mutlaka gösterilecek değer:** her sabah 1-2 gerçek aday (Grade + rozet + gerekçe), karne satırı, günün kavramı, Pazar özeti. Bu çekirdek asla zayıflatılmaz — ücretsiz katmanı cezalandırmak (içeriği kasıtlı kötüleştirmek) güven modelini çökertir.
- **Doğal sınırlar (yapay değil):** aday sayısı (1-2 / tam liste), gerekçe derinliği (2 cümle / tam faktör dökümü + risk notu), izleme güncellemeleri (yok / var), haftalık analiz (özet / tam).
- **Eksikliği hissettiren mekanizma:** karne satırı her gün toplam aday sayısını söyler — *"Bugün: 1 Grade A, 6 Grade B adayı. Yukarıda 2'sini görüyorsun."* Bu tek satır, funnel'ın en güçlü dönüşüm aracıdır çünkü satış değil, şeffaflıktır.
- **Asla ücretsiz olmayacaklar:** tam Tier B listesi, aday başına risk notu, izleme güncellemeleri, tam haftalık Edge analizi. (Karne asla premium'a kilitlenmez — o güven varlığıdır, satış varlığı değil.)

## 5. PREMIUM DEĞER TEKLİFİ

| Teklif | Güç | Op. yükü | İlk aşamada | Gerçek ödeme sebebi mi |
|---|---|---|---|---|
| Tam aday listesi (Top-3 + Tier B) | **Yüksek** | Sıfır (snapshot'ta var) | ✅ | ✅ Kapsam en somut fark |
| Derin gerekçe + risk notları | **Yüksek** | Düşük (template+LLM+onay) | ✅ | ✅ "Neden"in tamamı |
| İzleme güncellemeleri (önceki adayların seyri) | Orta-yüksek | Düşük (arşivden otomatik) | ✅ | ✅ Süreklilik hissi |
| Haftalık tam analiz | Orta | 30 dk/hafta | ✅ | ⚠️ Destekleyici |
| Premium Telegram kanalı (teslim biçimi) | — | Kuruldu | ✅ | Teklif değil, kanal |
| Daha erken içerik | — | — | ❌ **yapılmaz** | Sinyal-satıcılığı görünümü (GTM kuralı) |
| FinSense premium modülleri | Gelecek | İçerik hacmi ister | ❌ 90+ gün | Ayrı ürün hattı |
| Trade review / learning feedback | Güçlü ama erken | Orta | ❌ beta dashboard işi | Sonraki katman |
| "Daha kişisel içgörüler" | — | — | ❌ **asla** | Kişiselleştirilmiş tavsiye = compliance sınırı |

**Premium tek cümlesi:** *"Ücretsiz brif sana günün 2 adayını gösterir; Premium, sistemin gördüğü her şeyi gösterir — tam liste, tam gerekçe, riskleriyle."*

## 6. FİYATLAMA STRATEJİSİ

- **Yapı:** Founding Member **€99/yıl** (20 kişi, sabit kontenjan, "kurucu üye" rozeti + fiyat ömür boyu kilitli) → dolunca standart **€9/ay veya €79/yıl**. Lifetime **€149** (10 adet, yalnız ilk açılışta).
- **Haftalık fiyat yok** (haftalık ödeme = "bu hafta sinyal alayım" zihniyeti çeker — yanlış segment). Aylık, düşük-taahhüt giriş; yıllık, ciddiyet sinyali.
- **Çok ucuz güveni zedeler mi:** €9 alt sınırdır; €3-5 "spam kanalı" çağrışımı yapar. Çok pahalı (€29+) erken dönüşümü öldürür ve n'i sıfırlar — öğrenme durur. €9-12 bandı doğru test alanı.
- **"İlk 10/20 kullanıcı fiyatı" mantıklı mı:** Evet ama *indirim* olarak değil *statü* olarak: founding fiyatı sonsuza dek kilitli + isimleri (izinle) "kurucu üyeler" olarak anılır. "İlk 10'a %50!" dili yasak (kıtlık pazarlaması); "20 kurucu üyelik var, doldu mu kapandı" gerçek ve sabit olduğu sürece meşru.
- **Segment farklı fiyat:** Hayır — bu ölçekte fiyat ayrımı karmaşa + adaletsizlik algısı üretir. Segment farkı fiyatta değil *mesajda* (Bölüm 8).
- **Fiyat testi:** founding dolana kadar test yok (sabit). Sonra €9 vs €12 iki Stripe link, kohort bazlı (A/B aynı anda değil, ikişer haftalık dönüşümlü — n küçükken eşzamanlı split anlamsız). Deneme süresi v1'de yok; yerine **14 gün koşulsuz iade** (aynı işlevi görür, "trial bitti" churn duvarı yaratmaz).

## 7. DÖNÜŞÜM AKIŞI

| Adım | Psikoloji | Risk / drop-off | Güçlü mesaj | CTA |
|---|---|---|---|---|
| 1. Ücretsiz kanala katılır | "Bakalım neymiş" | Beklenti belirsiz | /start'ta net söz: günde 1 mesaj, tavsiye yok | — |
| 2. Düzenli değer görür (hafta 1-4) | Ritüel oluşuyor | Tekdüzelik | Karne satırının günlük dürüstlüğü (kötü gün dahil) | — (satış sıfır) |
| 3. Bazı içerikler ilgisini çeker | "Diğer 5 aday neydi?" | Merak cevapsız kalırsa küsme | Karne satırı toplam adayı her gün gösterir | /premium (pasif keşif) |
| 4. Premium farkını anlar | "Değer mi?" | Fark soyut kalması | **Ayda 1 kez tam premium sayı herkese açık örnek olarak yayınlanır** — fark anlatılmaz, gösterilir | "Bunu her sabah al" |
| 5. Doğru anda teklif görür | "Şimdi mi?" | Zamanlama saldırgan hissi | Tetik-tabanlı (aşağıda), takvim-tabanlı değil | Tek link |
| 6. Düşük sürtünmeyle öder | Risk hissi | Ödeme formu terki | Stripe link (2 tık) + 14 gün iade + "istediğin an çık" | Öde |
| 7. Premium onboarding | "Doğru mu yaptım?" | İlk dakika boşluğu | Otomatik hoş geldin DM'i + davet linki + "yarın 08:30'da ilk tam brifin" | — |
| 8. İlk hafta değer hisseder | Onay arayışı | İlk hafta zayıf içerik denk gelmesi | İlk 7 günde 1 kez "founding üye notu" (kişisel dokunuş, tek seferlik) | — |
| 9. Retention | Alışkanlık | Değer körleşmesi | Bölüm 9 | — |

**Teklif tetikleri (takvim değil davranış):** (a) /premium'a tıkladı → 24 saat içinde tek DM; (b) örnek premium sayı gününde kanal postu; (c) 4 hafta boyunca ≥%60 açma oranına ulaşan aktif kullanıcıya tek DM ("en düzenli okuyucularımızdansın…"); (d) founding kontenjan güncellemesi yalnız gerçek eşiklerde (15/20 dolunca bir kez). Kişi başına toplam teklif mesajı tavanı: **ayda 2.**

## 8. MESAJLAŞMA VE OFFER YAPISI

**Dil:** yumuşak, değer-odaklı, statü-bilinçli; aciliyet/kıtlık teatralliği yasak. "Şimdi yükselt!" yerine: *"Sistemin gördüğü her şeyi görmek istersen, kurucu üyelik açık."*

**Offer page (tek sayfa) iskeleti:** başlık: "Tam brif, her sabah." → fark tablosu (ücretsiz | premium, 5 satır) → örnek tam sayı (gerçek, tarihli) → karne linki → fiyat + 14 gün iade → SSS (4 soru: tavsiye mi? [hayır, araştırma] · iptal? [tek tık] · neden bu fiyat? · founding nedir?) → disclaimer.

**Telegram içi teklif mesajı (örnek, ayda ≤2):**
> *Bu sabahki brif ücretsiz sürümde 2 adayı gösterdi; sistem toplam 7 aday işaretledi. Ayda bir yaptığımız gibi, bugünkü TAM sayıyı herkese açıyoruz: [link]. Her sabah bunu almak istersen: kurucu üyelik 20 kişiyle sınırlı, 14 gün koşulsuz iade. Acelesi yok — karne ortada, kararı verilerle ver.*

**Follow-up mantığı:** ödeme sayfasını açıp ödemeyene 72 saat sonra tek DM ("takıldığın bir şey mi var? soru varsa buradayım") — satış değil destek tonu; cevapsızsa akış biter, tekrar denenmez (o kullanıcı bir sonraki doğal tetiği bekler).

## 9. RETENTION PLANI (ÖDEME SONRASI)

- **Onboarding (ilk 10 dk, tam otomatik):** hoş geldin DM'i → private kanal daveti → "nasıl okumalı" 5 maddelik mini kılavuz (Grade nedir, risk notu nasıl okunur, izleme güncellemesi nedir) → beklenti sıfırlama cümlesi: *"Kötü haftalar olacak; karnede hepsini göreceksin. Bu ürün kesinlik değil, disiplinli araştırma satar."* (Churn'ün 1 numaralı panzehiri baştan dürüstlük.)
- **İlk 7 gün:** tam brif ritmi + 1 kişisel founding notu + hafta sonunda "ilk haftan: şu 5 tam sayıyı aldın, karnesi şu" mini özeti — "boşa para vermedim" duygusu somut sayıyla kurulur.
- **Farkındalık hissi:** kurucu rozeti, ayda 1 "kurucu üyelere soru" (ürün kararına katılım — sahiplik), fiyat-kilidi hatırlatması yıl dönümünde.
- **Churn sinyalleri:** 5 gün üst üste premium brif açmama → yumuşak tek DM ("format mı yoğun geldi? kısa sürüm ister misin?"); iade/iptal → tek soruluk çıkış anketi (zorunlu değil) + kapı açık mesajı. Her churn nedeni kaydedilir — ilk 10 ödemede churn nedeni, dönüşüm oranından değerli veridir.
- **Yeniden kazanım:** ayrılana 30 gün sonra tek mesaj (yeni özellik/karne gelişimi olduğunda); ısrar yok.

## 10. KPI VE DENEY ÇERÇEVESİ

| Metrik | Tanım | Hedef (premium açılışı +30g) |
|---|---|---|
| Free signup | demo/landing → kanal | GTM/Telegram KPI'ları geçerli (200+ yolunda) |
| Content engagement | açma ≥%45, tepki ≥%5 | sürdürülüyor |
| Premium interest | /premium veya offer-page tık / abone | ≥%10 |
| Offer→payment | offer page → ödeme | ≥%15 |
| Toplam dönüşüm | ödeme / abone | ≥%2 |
| İlk 10 ödeme süresi | açılış → 10. ödeme | ≤30 gün (aşarsa paket/mesaj revizyonu) |
| Retention 7g/30g | premium açma sürekliliği | ≥%80 / ≥%70 |
| Churn (aylık) | iptal+iade / ödeyen | <%15 (n küçük — neden kaydı zorunlu) |
| ARPU | gelir / ödeyen | ~€8-9/ay eşdeğeri |
| İade oranı | 14g iade / ödeme | <%15 |

**Deneyler (sıralı, eşzamanlı değil — n küçük):** (1) örnek-tam-sayı sıklığı: ayda 1 vs 2 (ilgi tıkı etkisi); (2) teklif başlığı: kapsam-vurgusu ("her şeyi gör") vs zaman-vurgusu ("araştırmanı 10 dakikaya indir"); (3) founding sonrası €9 vs €12 (ikişer haftalık kohort); (4) aktif-kullanıcı DM tetiği açık vs kapalı (rahatsızlık/çıkış etkisiyle birlikte ölçülür). Her deney tek değişken, min. 2 hafta, sonuç Cuma ritüel raporuna.

## 11. 30 GÜNLÜK UYGULAMA PLANI
*(Takvim, GTM Gün 61-90 penceresine oturur — ön koşul: 4+ hafta karne ve ≥100 abone.)*

**Hafta 1 — Hazırlık (satışsız):**
- Offer page yaz + fark tablosu + SSS + yasak-kelime taraması; Stripe linkleri (founding/aylık/lifetime) + webhook→davet ucu test (Telegram dokümanı Gün 19-21 çıktısı).
- Onboarding otomasyonu (hoş geldin + kılavuz + beklenti cümlesi); churn-sinyal job'u; çıkış anketi.
- İlk örnek-tam-sayı hazırlığı (en güçlü gerçek gün seçilir — ama kötü gün karnesi saklanmaz).

**Hafta 2 — Yumuşak açılış:**
- Örnek tam sayı kanala + offer page canlı; /premium gerçek cevaba geçer.
- Beta kullanıcılarına (en sıcak segment) tek duyuru; aktif-kullanıcı tetiği açılır.
- İlk ödemeler: her ödeyenle 15 dk hoş-geldin sohbeti (öğrenme görüşmesi — neden ödedin?).

**Hafta 3 — Ritim:**
- Premium içerik ritmi tam (günlük tam brif + risk notları + izleme güncellemeleri); ilk haftalık tam analiz sayısı.
- Follow-up akışı (72 saat destek DM'i) devrede; ilk churn/iade olursa neden kaydı.

**Hafta 4 — Değerlendirme:**
- Metrik + segment tablosu: kim ödedi, hangi tetikle, hangi mesajla; kim tıklayıp ödemedi, neden (görüşme notları).
- Karar: founding hızı yeterli mi (≥10 ödeme) → devam; değilse revizyon sırası: (1) örnek-sayı sıklığı, (2) teklif metni, (3) paket içeriği — fiyat en son oynanır.
- 30. gün çıktısı: ilk ödeyen kohort profili + churn nedenleri + bir sonraki 60 günün fiyat/paket kararı.

---
*Bu doküman GTM Lansman Planı'nın Bölüm 7-8'ini uygulama seviyesine indirir; Telegram Bot MVP'nin premium gating mekaniğini ve Demo Spec'in funnel girişini varsayar. Bir sonraki revizyon bu dosyayı supersede etmelidir.*
