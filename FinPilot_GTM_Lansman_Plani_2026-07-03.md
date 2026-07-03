# FinPilot — İlk Kullanıcılara Açılma, Web Demo, Telegram ve Erken Nakit Akışı
## Go-to-Market + Productization Planı

**Tarih:** 2026-07-03 · **Taban:** Tam Sistem Audit (3 Tem), Konviksiyon Raporu (2 Tem), FinSense Tasarımı (3 Tem), kod doğrulaması (demo sayfası, telegram_bot_runner, waitlist endpoint, ödeme altyapısı = yok).
**İlke:** İlk amaç mükemmel ürün değil; gerçek kullanıcıyla temas kuran, değer gösteren, geri bildirim toplayan ve küçük de olsa gelir üreten çalışan bir dağıtım-öğrenme sistemi.

> Bu plan pazarlama/ürün operasyon tasarımıdır; hiçbir içerik yatırım tavsiyesi olarak konumlandırılmaz.

---

## 1. YÖNETİCİ ÖZETİ

FinPilot'un dışa açılma sorunu ürün eksikliği değil, **paketleme ve kanal eksikliği**. Konviksiyon raporu satılabilir nesneyi zaten üretti: *"Günün En İyi 3'ü — kalibre olasılık + gerekçe + açık karne."* Bu nesne üç kanala aynı anda dağıtılabilir: web demo (dünün gerçek Top-3'ü, sandbox), Telegram ücretsiz kanal (günlük brif) ve premium katman (tam liste + derin gerekçe + risk notları).

**Beş kritik karar:**
1. **Tek ürün nesnesi:** Her şeyi değil, yalnız Top-3 brifini + karneyi aç. Scanner'ın tamamı, agents, DRL, autonomy — hepsi kapalı kalır.
2. **Demo = dünün gerçek verisi, dondurulmuş:** canlı tarama değil (620 sn + maliyet + anahtar riski). "Bu, dün sabahki gerçek brif" dürüstlüğü, kurgu demodan daha etkileyici.
3. **Telegram = broadcast kanal + minimal bot;** mevcut polling bot (/scan) kişisel kalır, dağıtım kanal üzerinden yapılır. Bot ilk sürümde yalnız /start, /feedback, /brief.
4. **Gelir = Founding Member (20 kişi, sınırlı) + premium kanal;** ödeme Stripe Payment Link ile (altyapı yazılmaz). İlk 4 hafta tamamen ücretsiz değer, sonra yumuşak premium.
5. **Dil = research/eğitim;** "sinyal", "al", "kazandırır" kelimeleri dış yüzeyde yasak. Karne (açık track-record) pazarlamanın kendisidir.

**90 gün hedefi:** 100+ Telegram abonesi, 15-25 aktif beta kullanıcısı, 8-12 haftalık kesintisiz karne, ilk 10 ödeme (~€300-700 MRR-öncesi doğrulama), haftada ≤4 saat insan operasyonu.

---

## 2. FİNPİLOT'IN İLK DIŞA AÇILABİLİR SÜRÜMÜ

**Bugünkü aşama:** İç geliştirme/araştırma bitmek üzere; ölçüm döngüsü canlı (arşiv → kalibrasyon → Edge Report → tier karnesi). Dışa dönük katman yok denecek kadar ince (waitlist endpoint'i JSON'a yazıyor, demo tek sayfa, bülten yok).

| Demo-ready (aç) | Hazır değil (kapalı tut) |
|---|---|
| Top-3 sabah brifi (tier + conviction + rozet gerekçeleri) | Canlı tam tarama (süre/maliyet/anahtar) |
| Tier/Conviction karne panelleri (history) — "kanıt ekranı" | DRL, ai-lab, autonomy, agents sayfaları (bayat model + karmaşa) |
| Rozet açıklamaları (FinSense terim kartları v1) | Paper trading / portfolio (yarı-otonom izlenimi verir) |
| Watchlist görünümü (örnek, salt-okunur) | Auth'lu tam dashboard (beta'ya özel kalır) |
| FinSense sözlük (standalone-lite vitrin) | Academy üretim hattı (fabrika içeride) |

**Çekirdek değer önerisi (kullanıcı diliyle):**
> *"Her sabah, 1800+ hissenin taranmasından süzülen en dikkat çekici 3 aday — neden dikkat çektiğinin açıklaması ve sistemin geçmiş isabetinin açık karnesiyle. Karar senin; biz araştırmayı ve dürüst ölçümü getiriyoruz."*

**İlk lansman çerçevesi:** "FinPilot Daily Brief (beta)" — web'de dünün brifi herkese açık; bugünün brifi Telegram'da; tam dashboard davetli beta'da.

---

## 3. BETA KULLANICI STRATEJİSİ

| Segment | Neden uygun | Ne bekler | Ne gösterilir | Verdiği feedback | Ödeme ihtimali |
|---|---|---|---|---|---|
| 1. Yakın çevre (5-8) | Hızlı, dürüst, sabırlı | Arkadaşa yardım | Tam beta dashboard | Kullanılabilirlik, kafa karışıklığı | Düşük (ödetme) |
| 2. Finans meraklısı erken benimseyen (5-10) | Yeniliğe toleranslı, yayar | "Yeni bir şey görmek" | Brif + karne + FinSense | Fayda algısı, güven, viral dil | Orta |
| 3. Trader adayı / aktif trader (5-10) | Gerçek hedef kitle | Edge, hız, derinlik | Brif + watchlist + rozet gerekçeleri | En değerli: eksik özellik, ödeme isteği | **En yüksek** |
| 4. Okuryazarlık arayan (3-5) | FinSense doğrulaması | Öğrenmek | FinSense + brifin eğitim katmanı | Anlaşılırlık, ton | Düşük-orta (FinSense premium sonra) |
| 5. Telegram topluluk kullanıcısı (açık) | Ölçek + alışkanlık | Günlük değer | Ücretsiz kanal brifi | Tepki oranları (davranışsal) | Funnel kaynağı |
| 6. Free→premium adayları | Dönüşüm testi | Daha fazlası | 4 hafta free sonra premium teklif | Fiyat sinyali | Test edilir |

**Kurallar:** Kapalı beta **15-25 kişi** (10 altı istatistik vermez, 25 üstü destek yükü). **Davet kodu** sistemi (waitlist'ten elle seçim — segment dengesi kurulur: en az 8 trader). Waitlist herkese açık kalır ve Telegram'a yönlendirir (bekleyen boş beklemesin, kanalda değer alsın). İlk 30 gün kapalı; sonra haftada 10 davet ile yarı-açık.

---

## 4. WEB DEMO YAPISI

**Genel kararlar:** Demo login istemez. Veri = **dünün gerçek taramasının dondurulmuş anlık görüntüsü** (tarih damgalı — "sandbox kurgusu" değil, "dünün gerçeği"; hem wow hem dürüst). Canlı veri yok → maliyet ve zayıflık sergileme riski sıfır. "Wow ama zayıflık gösterme" dengesi: geçmiş isabeti karne gösterir (güçlü), canlı belirsizliği göstermez; her ekranda "geçmiş performans gelecek sonucu garanti etmez" satırı güveni artırır (paradoks ama çalışır: dürüstlük = fark).

| # | Sayfa | Amaç | Ana mesaj | CTA | Toplanan metrik |
|---|---|---|---|---|---|
| 1 | Landing | 10 sn'de değer + güven | "1800 hisse → günün 3 adayı, açık karneyle" + karne özeti (canlı sayı) | "Dünün brifini gör" (demo) + "Günlük brifi Telegram'dan al" | ziyaret, CTA-CTR, kaynak |
| 2 | Nasıl çalışır | Güven inşası, metodoloji | tarama → faktörler → kalibre derecelendirme → açık ölçüm (şema) | Demo'ya geç | scroll derinliği |
| 3 | Demo ekranı | Ürünü hissettir | Dünün Top-3'ü: Grade, rozetler, 2-cümle gerekçe, ⓘ terim kartları | "Bugünününkini almak için Telegram" | rozet-tık, kart-açma, süre |
| 4 | Karne / örnek sonuçlar | **Kanıt** | Tier bazlı isabet tablosu + "nasıl ölçüyoruz" linki | Waitlist | tablo etkileşimi |
| 5 | Feedback formu | Öğrenme | 3 soru: "Ne bekledin? Ne gördün? Öder miydin?" | Gönder → teşekkür + Telegram | yanıt oranı, NPS-benzeri |
| 6 | Waitlist / kayıt | Beta hunisi | "Tam dashboard davetle açılıyor" | E-posta bırak | kayıt, kaynak |
| 7 | Telegram yönlendirme | Kanal büyütme | "Her sabah 08:30'da cebinde" | Kanala katıl | katılım dönüşümü |
| 8 | Premium tanıtım (4. haftadan sonra) | Gelir zemini | "Tam liste + derin gerekçe + risk notları" | Founding Member | tıklama→ödeme dönüşümü |

**İlk 10 saniye testi:** kullanıcı landing'de şunu anlamalı: *ne yapıyor* (günlük 3 aday), *neden güvenilir* (açık karne), *ne DEĞİL* (tavsiye değil, araştırma). Bu üçlü tek ekranda.

---

## 5. GERİ BİLDİRİM SİSTEMİ

**Kaynaklar ve araçlar:** demo-sonrası 3-soru formu (sayfa 5) · dashboard içi mikro-anket (tek soru, oturum başına ≤1: "bu brif işine yaradı mı? 👍/👎") · Telegram /feedback komutu + haftalık tek soru mesajı · 1:1 görüşme (beta'nın ilk 10'uyla 20 dk; kayıt notu şablonlu) · davranış analitiği (Plausible/Umami: sayfa, rozet-tık, drop-off) · drop-off analizi (landing→demo→Telegram→waitlist hunisi).

**Feedback taxonomy (etiket seti):**
`ilk-izlenim · anlaşılırlık · güven · fayda-algısı · en-sevilen · en-zayıf · ödeme-niyeti · eksik-özellik · kafa-karışıklığı · bug · dil/ton`
+ ikincil boyut: segment (1-6), kanal, tarih.

**Sinyal/gürültü ayrımı:**
- **Söylenen vs yapılan:** "öderim" diyen ≠ ödeyen; davranış metrikleri (7 gün üst üste brif açma, karne sayfasına dönüş) niyet beyanından üstün tutulur.
- **Tekil istek ≠ desen:** bir özellik isteği ≥3 bağımsız kullanıcıdan gelmeden roadmap'e giremez ("kural-of-3").
- **Segment ağırlığı:** trader segmentinin ürün-yönü feedback'i, yakın-çevre nezaket feedback'inden ağır basar.

**Haftalık döngü (Cuma, 45 dk, yarısı otomatik):** LLM tüm haftanın feedback'ini taxonomy'ye göre özetler (otomatik) → insan 15 dk okur → 3 karar: (1) bu hafta düzeltilecek 1 şey, (2) roadmap'e giren/çıkan, (3) beta'ya gönderilecek "şunu duyduk, şunu yaptık" mesajı (güven döngüsü — feedback'in işlendiğini göstermek retention'ın kendisidir).

---

## 6. TELEGRAM BOT MVP PLANI

**Mevcut durum:** tek-kullanıcılı polling bot (/scan, /help) + TelegramNotifier (sinyal + günlük özet gönderimi). Broadcast/kanal yapısı yok — kurulacak asıl parça bu.

**Mimari karar:** *Kanal* (tek yönlü yayın: ücretsiz brif) + *bot* (etkileşim: kayıt, feedback, yönlendirme). Bot herkese /scan **vermez** (maliyet + kötüye kullanım); mevcut /scan sahibin özel komutu kalır.

| Görev | İlk sürümde? | Gelire katkı | Operasyon yükü |
|---|---|---|---|
| 1. Ücretsiz günlük brif (kanala) | ✅ Çekirdek | Dolaylı (funnel) | Düşük (otomatik + 10 dk insan onayı) |
| 2. Premium brif (özel kanal) | 4. haftadan sonra | **Doğrudan** | Düşük-orta |
| 3. Günün öne çıkanları | ✅ (brifin kendisi) | Dolaylı | — |
| 4. Mini "neden önemli?" açıklamaları | ✅ (brif içinde 1 cümle + FinSense linki) | Güven | Düşük |
| 5. Komutla veri çekme (/ticker) | ❌ Sonra (maliyet+kapsam) | Düşük | Yüksek |
| 6. Soru-cevap | ❌ Sonra (hallucination riski) | Düşük | Yüksek |
| 7. Web demo'ya trafik | ✅ (her brif altında link) | Dolaylı | Sıfır |
| 8. FinSense yönlendirme | ✅ (terim linkleri) | Dolaylı + FinSense doğrulama | Sıfır |
| 9. /feedback komutu | ✅ | Öğrenme | Düşük |
| 10. Segmentasyon (katılım kaynağı + tepki) | ✅ pasif (etiketle, eyleme sonra) | Sonra | Düşük |

**Başlangıç kombinasyonu: Broadcast bot (kanal) + hafif interactive bot (/start, /feedback, /brief "son brifi göster").** Alert-bot ve education-companion modları 60+ günde.

**Brif formatı (ücretsiz, her sabah 08:30 CET, şablon):**
> 📊 *FinPilot Daily Brief — 3 Tem* (dünkü tarama: 1812 hisse)
> Bugünün dikkat çeken 3 adayı: $XXX (Grade A — yüksek short + gap, ⓘ squeeze nedir?) …
> 🎯 Dünkü brif karnesi: 2/3 aday ≥%5 hareket etti → tam karne (link)
> 📚 Günün kavramı: RVOL (40 sn)
> *Araştırma ve eğitim amaçlıdır; yatırım tavsiyesi değildir.*

---

## 7. ÜCRETSİZ / PREMIUM BÜLTEN MODELİ

**A) Ücretsiz günlük brif:** Amaç güven + kitle + alışkanlık. İçerik: Top-3'ten **1-2 aday** (tam liste değil), 1 cümle piyasa bağlamı, karne linki, günün kavramı. Günlük (alışkanlık günlükle kurulur; haftalık ile kitle büyümez).

**B) Premium (private kanal + haftalık derin sayı):**
- Günlük: **tam Top-3 + Tier B listesi** (5-10 aday), her aday için derin gerekçe (faktör dökümü + risk notu + "neyi bilmelisin" FinSense bağları), izleme güncellemeleri.
- Haftalık: sistem karne analizi ("bu hafta neyi doğru/yanlış ölçtük"), rejim notu, 1 eğitim-uygulama vakası (arşiv replay).
- **Doğru free/premium farkı:** *zamanlama değil derinlik ve kapsam.* Free kullanıcı da aynı sabah 1-2 aday alır (geciktirme güven bozar, "erken erişim" satmak sinyal-satıcılığına kayar); premium *daha fazla aday + daha derin gerekçe + risk katmanı* alır.
- **"Sinyal satışı gibi görünmeme":** ürün adı "research brief"; her aday "izleme adayı" dili; al/sat/hedef fiyat asla; karne hem doğruları hem yanlışları gösterir; her sayıda disclaimer. Premium'un satın alınan şeyi "daha derin araştırma ve eğitim", "kazanç" değil.

**Fiyat ve zamanlama:** İlk 4 hafta her şey ücretsiz (karne birikir, güven oluşur). Sonra: premium **€9/ay veya €79/yıl** (düşük-orta çapa; erken aşamada fiyat sinyal toplama aracı, gelir aracı değil). Çok erken ücret istemek hata mı? — 4 haftadan önce evet (karne yok = değer iddiası boş); 8 haftadan sonra da hata (bedava alışkanlığı kemikleşir). 4-6. hafta penceresi doğru.

---

## 8. İLK NAKİT AKIŞI STRATEJİSİ

| Model | Kurulum | Güven eşiği | Op. yükü | İlk 10 ödeme için | Uzun vade |
|---|---|---|---|---|---|
| 1. Premium Telegram kanalı | Kolay (Stripe link + davet) | Orta | Düşük | ✅ **Birincil** | ✅ |
| 2. Ücretli bülten (e-posta) | Orta (ek kanal) | Orta | Orta | ⚠️ Telegram'la birleşik tut | ✅ |
| 3. Erken erişim üyeliği | Kolay | Düşük | Düşük | ⚠️ Founding'e katla | — |
| 4. **Founding Member (20 kişi, €99/yıl, ömür boyu %50)** | Kolay | Orta | Düşük | ✅ **En iyi ilk-10 aracı** | ✅ (sadakat çekirdeği) |
| 5. FinSense premium | İçerik hacmi ister | Düşük | Orta | ❌ Erken (90+ gün) | ✅ |
| 6. Özel watchlist/insight | Kişiselleştirilmiş tavsiyeye kayar | — | — | ❌ **Compliance riski — yapma** | ❌ |
| 7. Onboarding görüşmesi (€29) | Anında | Düşük | **Yüksek (insan-saat)** | ⚠️ Yalnız öğrenme aracı olarak 5 adet | ❌ ölçeklenmez |
| 8. Lifetime paketi | Kolay | Yüksek | Düşük | ⚠️ 10 adet sınırlı (€149) — nakit + sinyal | ⚠️ gelir tavanı |

**Karar:** Founding Member (birincil) + premium kanal (sürekli) + sınırlı lifetime (nakit enjeksiyonu). Ödeme: **Stripe Payment Link** — kod yazılmaz, KYC/fatura Stripe'ta; bot davet linkini ödeme webhook'una bağlayan 30 satırlık script yeter.
**Hedefler:** ilk 10 ödeme = 90. gün; dönüşüm beklentisi ücretsiz kitleden %2-5 (100 abone → 2-5 ödeme; o yüzden kanal 200+ hedefler). **Fiyat testi:** ilk 20 kişiye founding fiyatı sabit; sonrasında €9 vs €12 A/B'si (Stripe iki link). Agresif fiyat değil düşük fiyatla sinyal toplamak doğru — ama **€0'a premium verme** (bedava premium, fiyat sinyalini yok eder).

---

## 9. OTOMASYON-FIRST OPERASYON TASARIMI

| İş | Otomasyon seviyesi | İnsan rolü | Risk |
|---|---|---|---|
| Günlük brif draft'ı | Tam otomatik (Top-3 + şablon + LLM gerekçe) | **10 dk sabah onayı — finansal içerikte zorunlu** (ilk 90 gün) | LLM gerekçe hatası → faktör-kısıtlı üretim (yalnız mevcut alanlardan cümle) |
| Telegram dağıtımı | Tam otomatik (scheduler 08:30, onay sonrası) | Yok | Gönderim hatası → teslimat logu + kendine test mesajı |
| Karne güncelleme | Tam otomatik (mevcut cron zinciri) | Haftalık göz | Veri hatası karneyi bozarsa güven ölür → Truth Engine tutarlılık testi |
| İçerik özetleme (haftalık sayı draft'ı) | Yarı otomatik | 30 dk edit | Derinlik kaybı |
| Kullanıcı segmentleme | Tam otomatik (pasif etiket) | Yok | Yanlış eylem yok (pasif) |
| FAQ yanıtları | Şablon (bot /help genişler) | Ayda bir güncelleme | Soru-cevap LLM'i erken — açma |
| Feedback özetleme | Tam otomatik (LLM + taxonomy) | 15 dk Cuma okuma | Nüans kaybı → ham veriye link |
| Haftalık ürün içgörü raporu | Tam otomatik (metrik + feedback birleşik) | Okur | — |
| Waitlist yönetimi | Otomatik (kayıt→e-posta→Telegram yönlendirme) | Haftalık davet seçimi (10 dk) | — |
| Trial→paid mesajları | Otomatik dizi (4. hafta tetikli, kişi başı ≤2 mesaj) | Metinleri 1 kez yazar | Spam algısı → frekans tavanı |
| Churn sinyali | Otomatik (7 gün brif açmama → tek "seni özledik + tek soru") | Yok | — |

**Toplam insan bütçesi hedefi:** günlük 10-15 dk (brif onayı) + haftalık ~2 saat (feedback + haftalık sayı + davetler) = **≤4 saat/hafta.** Kural: insan onayı yalnız *dışa giden finansal içerikte*; iç metrik ve operasyon tam otonom.

---

## 10. FUNNEL VE BÜYÜME AKIŞI

| Aşama | Hedef | Psikoloji | Drop-off nedeni | İyileştirme |
|---|---|---|---|---|
| 1. Landing | 10 sn'de anlama | Şüphe ("yine bir sinyal sitesi mi?") | Jargon, abartı | Karne rakamı hero'da; dürüst dil |
| 2. Demo inceleme | Değeri hissetme | Merak | Kafa karışıklığı (3 skor dili!) | Tek Grade + ⓘ kartları |
| 3. Telegram/e-posta bırakma | Kalıcı kanal | "Spam gelir mi?" | Değer belirsiz | "Her sabah 1 mesaj, o kadar" sözü |
| 4. Ücretsiz brif alma | Alışkanlık | Rutin arayışı | Düzensizlik, sıkıcılık | 08:30 sabitliği; kısalık; karne satırı |
| 5. Düzenli açma | Güven birikimi | "Bu iş yarıyor mu?" | İsabet dalgalanması | Karneyi saklamamak — kötü haftayı da yaz (güveni asıl bu kurar) |
| 6. Premium teklif | Dönüşüm | "Değer mi?" | Fark algısı zayıf | Bir kez tam premium sayıyı herkese göster ("bunu her gün alırsın") |
| 7. İlk ödeme | Taahhüt | Risk hissi | Ödeme sürtünmesi | Stripe link, 2 tık; iade garantisi 14 gün |
| 8. Retention | Alışkanlık + topluluk | "Hâlâ değer var mı?" | İçerik tekdüzeliği | Haftalık derin sayı + founding topluluk hissi |
| 9. Feedback→ürün | Sahiplik | "Sesim duyuluyor" | Kara delik feedback | "Şunu duyduk→yaptık" ritmi (Bölüm 5) |

---

## 11. TEKNİK YAPI TAŞLARI

| Bileşen | Şart mı | MVP'de | Not / sıra |
|---|---|---|---|
| Web demo frontend | ✅ | ✅ | Var (demo sayfası) — Top-3 + karne görünümüne daraltılır. **Sıra 1** |
| Landing yenileme | ✅ | ✅ | page.tsx üstüne karne + üçlü mesaj. **Sıra 1** |
| Statik demo snapshot üretimi | ✅ | ✅ | Günlük cron: dünün brifi → JSON → statik sayfa. **Sıra 1** |
| Waitlist | ✅ | ✅ | Var (endpoint) → SQLite'a taşı + e-posta alanı doğrulama. **Sıra 2** |
| Analytics | ✅ | ✅ | Plausible/Umami (GDPR-dostu, çerezsiz — AB için doğru). **Sıra 2** |
| Feedback store | ✅ | ✅ | Tek tablo + taxonomy etiketi. **Sıra 2** |
| Telegram kanal + broadcast bot | ✅ | ✅ | Kanal aç; TelegramNotifier'ı kanala yayın yapacak şekilde genişlet. **Sıra 3** |
| Message scheduler | ✅ | ✅ | Mevcut APScheduler'a 1 job (08:30 brif). **Sıra 3** |
| Bülten içerik pipeline | ✅ | ✅ | Top-3 + şablon + LLM gerekçe + onay kuyruğu. **Sıra 3** |
| Payment | ✅ (4. hafta) | ⚠️ | Stripe Payment Link + webhook→davet script'i. Kendi ödeme kodun: **yazma.** **Sıra 4** |
| CRM / user tracking | ⚠️ | Hafif | SQLite tablosu (kaynak, segment, durum) yeter; araç alma. **Sıra 4** |
| Admin dashboard | ❌ | ❌ | Mevcut Sistem Sağlığı kartı + haftalık otomatik rapor yeter |
| Feature flag / beta access | ✅ | ✅ | Davet kodu tablosu + mevcut auth. **Sıra 2** |

Yeni altyapı neredeyse sıfır: en büyük iş **broadcast yayın + snapshot üretimi + onay kuyruğu** — üçü de mevcut scheduler/notifier üzerine eklenti.

---

## 12. RİSKLER VE KAÇINILACAK HATALAR

| Hata | Neden tehlikeli | Nasıl fark edilir | Önleme |
|---|---|---|---|
| Çok erken herkese açılmak | Ham izlenim kalıcıdır; ikinci şans pahalı | Waitlist'i hemen boşaltma dürtüsü | 15-25 tavanı; haftalık 10 davet kuralı |
| Çok ham demo | "Karışık/amatör" algısı | Demo'da 3 skor dili, 15 sayfa | Tek Grade, 4 sayfa, dondurulmuş veri |
| Feedback toplayıp işlememek | Kullanıcı küser, veri çürür | Form doluyor, roadmap değişmiyor | Cuma ritüeli + "duyduk→yaptık" mesajı |
| Telegram'ı spam'e çevirmek | Tek varlığın (dikkat) tükenir | Ayrılma oranı, susturma | Günde 1 mesaj tavanı; her mesajda değer |
| Premium'u erken ve zayıf açmak | Fiyat sinyali kirlenir, güven kırılır | 2 haftada premium isteme dürtüsü | 4 hafta karne şartı; premium = derinlik farkı |
| Aşırı vaat | Tek kötü hafta = ihanet algısı; compliance | "kazandırır" dili metinlere sızması | Yasak-kelime listesi + karnede kötü haftayı gösterme |
| Çok manuel operasyon | 4 saat/hafta → 20 saat; tükeniş | Sabah brifi 1 saat sürüyor | Otomasyon-first (Bölüm 9); insan yalnız onay |
| Segmentleri ayırmamak | Trader feedback'i ile nezaket feedback'i karışır | "Herkes beğendi" yanılsaması | Taxonomy'de segment alanı zorunlu |
| Free kullanıcının kalma nedenini düşünmemek | Kanal büyür ama ölür | Açılma oranı düşer | Free brif tek başına değerli olmalı (1-2 gerçek aday + karne) |
| Nakit uğruna güven zedelemek | Erken €'lar, marka ölümüne değmez | "Bu hafta premium'a geçin yoksa kaçırırsınız" dili | Kıtlık pazarlaması yasak; founding sınırı gerçek ve sabit |
| **Compliance dili kayması** | AB/Avusturya'da kişiselleştirilmiş tavsiye görünümü regülasyon riski | "sana özel", "al", hedef fiyat | Genel research çerçevesi; disclaimer her yüzeyde; kişiye özel yatırım önerisi asla |

---

## 13. 30 / 60 / 90 GÜNLÜK YOL HARİTASI

**Gün 1-30 — AŞAMA 1+2: DEMO + KAPALI BETA** *(Audit'in Truth Engine/tek-Grade işleriyle paralel — karne o işlerin çıktısını gösterir)*
- Hafta 1: Landing yenile (karne hero + üçlü mesaj); demo sayfasını Top-3+karne'ye daralt; günlük snapshot cron'u; waitlist→SQLite + davet kodu; Plausible kur; feedback tablosu + formu.
- Hafta 2: İlk 10 davet (5 tanıdık + 5 trader); 1:1 görüşme şablonu; yasak-kelime listesi + tüm yüzeylere disclaimer.
- Hafta 3-4: 15-25 kullanıcıya çık; Cuma feedback ritüeli başlat; demo iyileştirme turu (en büyük 3 kafa karışıklığı); Telegram kanalı aç ve brif otomasyonunu kur (önce beta'ya).
- **Kapı metriği:** ≥15 aktif beta, ≥%50'si haftada 3+ gün brif açıyor, feedback döngüsü 2 kez döndü.

**Gün 31-60 — AŞAMA 3: TELEGRAM MVP + KİTLE**
- Kanal herkese açılır (waitlist + demo trafiği yönlendirilir); 08:30 ücretsiz brif ritmi kesintisiz.
- Bot: /start onboarding, /feedback, /brief; pasif segmentasyon etiketleri.
- Build-in-public başlangıcı (X/LinkedIn haftada 2 içerik: karne + öğrenilen ders — trafik kaynağı).
- Karne sayfası public; FinSense terim kartları brif linklerinde canlı.
- **Kapı metriği:** 100+ kanal abonesi, brif açılma ≥%40, 6+ haftalık kesintisiz karne.

**Gün 61-90 — AŞAMA 4+5: PREMIUM TEST + ÜRÜNLEŞME KÖPRÜSÜ**
- Founding Member lansmanı (20 kişilik, €99/yıl; 10 adet lifetime €149): önce beta + kanala, bir "tam premium örnek sayı" herkese gösterilerek.
- Premium private kanal: tam Top-3 + Tier B + derin gerekçe + haftalık analiz sayısı.
- Stripe link + webhook→davet otomasyonu; trial→paid mesaj dizisi; churn sinyali otomasyonu.
- Fiyat A/B (€9 vs €12 aylık) founding dolduktan sonra.
- Demo→ürün köprüsü: demo kullanıcısına "kendi watchlist'ini kur" daveti (beta genişlemesi haftada 10).
- **Kapı metriği:** ilk 10 ödeme, ücretsiz→premium ≥%2, insan operasyonu ≤4 saat/hafta, churn <%20/ay.
- **90. gün kararı:** metrikler tuttuysa → yarı-açık büyüme + FinSense premium hazırlığı; tutmadıysa → fiyat/paket revizyonu, kitle büyütmeye devam (gelir denemesi 2. tur 120. günde).

---
*Bu plan, Tam Sistem Audit (3 Tem) Bölüm 11 yol haritasının ticari kolunu detaylandırır; teknik kol (Truth Engine, tek Grade) ile paralel yürür ve onun çıktısı olan karneyi pazarlamanın merkezine koyar.*
