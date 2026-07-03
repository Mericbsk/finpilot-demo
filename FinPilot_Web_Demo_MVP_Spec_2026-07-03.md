# FinPilot — Web Demo MVP Spec
## Kapalı/Yarı-Kapalı Beta · Gerçek Kullanıcı Testi · Geri Bildirim · Ürünleştirme Köprüsü

**Tarih:** 2026-07-03 · **Üst doküman:** GTM Lansman Planı (3 Tem, Bölüm 4) — bu spec onun demo bileşenini uygulama seviyesine indirir.
**Kod tabanı doğrulaması:** `web/src/app/demo/page.tsx` (1028 satır, mevcut), `page.tsx` landing (HeroGrid + Waitlist bileşenleri), FactorBadges/TierBadge/ConvictionBadge bileşenleri, waitlist endpoint'i, history karne panelleri.

> ⚠️ **Kritik mevcut-durum bulgusu:** Bugünkü demo sayfası eski sözlükle konuşuyor — `signal: BUY/SELL`, `stop_loss`, `take_profit`, `kelly_fraction`, `position_size` gösteriyor. Bu, hem üç-skor-dili karmaşasını dışa taşıyor hem de **compliance açısından tam kaçınmamız gereken dil** (al-sat emri + hedef fiyat + pozisyon boyutu = kişisel tavsiye görünümü). Demo MVP'nin ilk işi yeni özellik eklemek değil, **bu sayfayı yeni sözleşmeye göre yeniden çerçevelemek.**

---

## 1. YÖNETİCİ ÖZETİ

Demo MVP tek bir deneyimi kusursuz gösterir: **"Dünün gerçek brifi + sistemin açık karnesi."** Kullanıcı 10 saniyede ne olduğunu anlar, 3 dakikada dünün Top-3'ünü gerekçeleriyle inceler, karneyi görür, iki çıkıştan birine akar: Telegram (bugünün brifi) veya waitlist (tam dashboard beta'sı). Her adım ölçülür; demo sonunda 3 soruluk feedback alınır.

Yapılacak iş küçüktür ve çoğu mevcut koddan türetilir: mevcut demo sayfası daraltılıp yeniden çerçevelenir (BUY/SELL→Grade), günlük snapshot cron'u eklenir, landing'e karne + üçlü mesaj gelir, feedback tablosu açılır. **14 günde canlıya çıkabilir.** Yeni altyapı: yalnız snapshot üretimi + feedback store + analytics.

Başarı tanımı trafik değil öğrenmedir: 25 beta kullanıcısından ≥15 tam akışı bitirir, ≥%50 feedback bırakır, ≥%30 Telegram'a geçer ve "bu ne işe yarıyor?" sorusuna kullanıcıların kendi cümleleriyle verdiği cevap bizim değer önerimizle örtüşür.

---

## 2. DEMO'NUN ANA AMACI

Öncelik sırası (çelişki durumunda üstteki kazanır):
1. **Ürün yönünü valide etmek** — "günlük derecelendirilmiş brif + açık karne" önermesi karşılık buluyor mu?
2. **Kaliteli feedback toplamak** — ilk 25 kullanıcının kafa karışıklıkları ve ödeme sinyalleri.
3. **Funnel'a bağlamak** — Telegram kanalı + waitlist.
4. Etkilemek — evet ama dürüst yolla (gerçek veri + karne); "wow" hedefin sonucu, kendisi değil.
5. Ürünü tam açıklamak — **hayır**; demo sistemin %10'unu gösterir, o %10'u net gösterir.

**İlk 10 saniyede anlaşılacaklar:** (a) her sabah 1800+ hisse taranıyor → günün 3 adayı çıkıyor; (b) her adayın *nedeni* açıklanıyor; (c) sistemin geçmiş isabeti açık karneyle ortada; (d) bu bir araştırma/eğitim aracı, tavsiye değil.

**Demo sonunda kullanıcı ne yapmalı:** Telegram'a katılmalı (birincil CTA) veya waitlist'e yazılmalı (ikincil), ve 3 soruluk formu doldurmalı.

**"Başarılı demo deneyimi" tanımı:** kullanıcı en az 1 adayın gerekçesini açtı + karneyi gördü + bir çıkış CTA'sına tıkladı + kendi cümlesiyle ürünü doğru tarif edebiliyor (feedback formu 1. soru bunu ölçer).

---

## 3. MVP FEATURE SCOPE

**MVP'DE OLACAKLAR**
- Dünün Top-3 brifi (dondurulmuş gerçek snapshot, tarih damgalı)
- Aday kartı: Grade (tek etiket) + kalibre olasılık bandı + faktör rozetleri + 2 cümle gerekçe
- ⓘ terim kartları (rozet→60 kelimelik FinSense açıklaması; 10-15 çekirdek terim)
- Karne bölümü: tier bazlı isabet tablosu (history panellerinden türetilir) + "nasıl ölçüyoruz" kısa metni
- Mini grafik (sinyal günü işaretli, mevcut StockChart yeniden kullanılır)
- Feedback formu (3 soru) + oturum analitiği
- Telegram + waitlist CTA'ları

**MVP'DE OLMAYACAKLAR**
- Canlı tarama / canlı fiyat (620 sn + maliyet + anahtar riski)
- Login (demo herkese açık; beta dashboard ayrı ve davetli)
- BUY/SELL etiketi, stop-loss/take-profit/hedef fiyat, position size/Kelly — **kaldırılıyor, ertelenmiyor**
- DRL/agents/autonomy'ye dair her şey; 15 sayfalık dashboard navigasyonu
- Soru-cevap AI chat'i

**SONRAYA (beta dashboard'da, demo değil):** kullanıcı watchlist'i, alert kurulumu, tam Tier B listesi, FinSense tam sözlük, paper trading.

**Nice-to-have ama dikkat dağıtan (bilinçli yapılmıyor):** canlı sayaç animasyonları, sektör ısı haritası, çoklu tarih arşivinde gezinme (tek "dün" yeter; arşiv merakı Telegram'a itilir — "her sabah yenisi kanalda").

---

## 4. SAYFA/EKRAN BAZLI BİLGİ MİMARİSİ

Tek-akışlı yapı: 9 ekran, 4 fiziksel sayfaya sıkıştırılır (drop-off her sayfa geçişinde arttığı için):
**(A) Landing** = ekran 1+2 · **(B) /demo** = ekran 3+4+5+6 (dikey akış + modal) · **(C) /feedback** = ekran 7 · **(D) çıkış blokları** = ekran 8+9 (B ve C'nin altında gömülü).

| Ekran | Amaç | Değer | İçerik | Ana CTA | Toplanan veri | Cevapladığı soru |
|---|---|---|---|---|---|---|
| 1. Landing hero | 10 sn kancası | Anında kavrama | Başlık + alt mesaj + canlı karne rakamı + Top-3 önizleme kartı (bulanık 3.) | "Dünün brifini gör" | ziyaret, kaynak, CTA-CTR | "Bu ne?" |
| 2. Nasıl çalışır (landing alt) | Güven | Metodoloji şeffaflığı | 4 adım şerit: Tara → Faktörler → Derecelendir → Açıkça Ölç; "neyi yapmaz" kutusu | Demo'ya kay | scroll ≥%50 | "Neden inanayım?" |
| 3. Demo girişi (/demo üst) | Bağlam | Beklenti ayarı | "3 Tem sabahı, 1812 hisse tarandı, 3 aday çıktı" + tarih damgası + disclaimer | aşağı kaydır | demo-start | "Ne göreceğim?" |
| 4. Brif / insight | Çekirdek deneyim | Ürünün kendisi | 3 aday kartı (Bölüm 5 spec) | kart aç | kart-açma oranı | "Ne buldu?" |
| 5. Karne | Kanıt | Güven | Tier isabet tablosu + iyi/kötü hafta birlikte + ölçüm yöntemi linki | "Bugünününkü Telegram'da" | tablo görüntüleme | "İşe yarıyor mu?" |
| 6. Tekil aday detay (modal) | Derinlik | "Neden" cevabı | Grafik (sinyal günü ok) + faktör dökümü + gerekçe + ⓘ kartlar + "ne olabilirdi/ne oldu" yok — sadece dün olduğu için "5 gün sonra ne olduğunu Telegram'da takip et" | Telegram | modal süre, ⓘ tıklar | "Bu hisse neden?" |
| 7. Feedback | Öğrenme | Ses verme | 3 soru (Bölüm 7) | Gönder | yanıtlar | — |
| 8. Waitlist bloğu | Beta hunisi | Erken erişim | "Tam dashboard davetle" + e-posta alanı | Kaydol | kayıt, kaynak | "Fazlasını nasıl alırım?" |
| 9. Telegram bloğu | Kanal | Günlük değer | "Her sabah 08:30, günde 1 mesaj" sözü | Katıl | tıklama→katılım | "Bugünkü nerede?" |

---

## 5. DEMO DASHBOARD (BRİF EKRANI) SPEC

**Görünüm kararı:** research terminal DEĞİL, sade ürün deneyimi. Bilgi yoğunluğu kuralı: **ekranda aynı anda en fazla 5 bilgi bloğu** (3 aday kartı + karne şeridi + bağlam satırı). Mevcut demo'nun 20+ alanlı tablosu (atr, ema_gap, alignment_ratio, kelly...) **gizlenir** — bunlar research dili, güven değil kafa karışıklığı üretir (beta feedback'iyle geri eklenebilir, varsayılan sade).

**Aday kartı anatomisi (mevcut bileşenlerden: TierBadge + ConvictionBadge + FactorBadges birleşir):**
```
┌─────────────────────────────────────────────┐
│ $TICKR  Şirket Adı              Grade A 🟢  │  ← TEK etiket (BUY değil!)
│ Geçmişte bu profildekilerin ~%6X'i          │  ← kalibre olasılık, aralıklı dil
│ 5 gün içinde ≥%5 hareket etti*              │
│ [⚡ Yüksek Short] [📈 Gap] [🔊 RVOL]  ⓘⓘⓘ  │  ← rozetler → terim kartı
│ "Yüksek short oranı + bu sabahki gap        │  ← 2 cümle gerekçe
│ birlikte squeeze koşulu oluşturuyor…"       │
│ [Detayı gör]                                │
└─────────────────────────────────────────────┘
```
- **Skor mu, açıklanabilir set mi?** İkisi birden ama hiyerarşiyle: Grade (tek harf) ana sinyal; faktör rozetleri "neden"i; ham kompozit skor sayısı **gösterilmez** (16.5-üstü-14.2 kimseye bir şey ifade etmez).
- Olasılık dili her zaman geçmiş-frekans çerçevesinde ("geçmişte bu profildekilerin %X'i…"), asla gelecek vaadi ("%X ihtimalle yükselecek" ❌).
- \* dipnotu: ölçüm tanımına link (karne metodolojisi).
- Scanner sonucu + eğitim kartı + CTA kombinasyonu: ✅ tam bu — kartın ⓘ'si FinSense'e, kartın altı Telegram'a akar.

**Karne şeridi spec:** 3 satırlık tablo (Grade A / B / C: adet, ≥%5 isabet, örnek dönem) + "son 4 haftanın en kötü haftası dahil" ibaresi + tarih aralığı. Küçük n uyarısı dürüstçe: "Grade A nadir çıkar (~1/gün); istatistik birikiyor."

---

## 6. KULLANICI AKIŞI

| Adım | Zihindeki soru | Ne görmeli | Drop-off riski | Karşı önlem |
|---|---|---|---|---|
| 1. Landing'e gelir | "Bu da mı sinyal sitesi?" | Karne rakamı + "tavsiye değil, araştırma" netliği | Klişe algısı → kapatma | Dürüst dil + gerçek rakam; abartı sıfır |
| 2. Ne yaptığını anlar | "Nasıl çalışıyor?" | 4 adımlık şerit, 15 sn'de okunur | Uzun metin | Şerit görsel, metin ≤40 kelime/adım |
| 3. Demo başlatır | "Gerçek mi bu?" | Tarih damgası + "dünün gerçek taraması" | Kurgu şüphesi | "Neden dünün? Bugünkü kanalda" açıklaması |
| 4. Top-3'ü görür | "Ne bulmuş?" | 3 sade kart | Bilgi boğulması | 5-blok kuralı |
| 5. Gerekçeleri açar | "Neden bu hisse?" | Modal: grafik + faktör + gerekçe | Jargon | ⓘ kartları; jargonsuz 2 cümle |
| 6. Güven/merak gelişir | "İsabetli mi peki?" | Karne (kötü haftalar dahil) | Şüphe ("seçilmiş sonuçlar") | Metodoloji linki + tüm-tier tablosu |
| 7. Telegram/waitlist | "Devamını nasıl alırım?" | İki net kutu, tek satır söz | Kararsızlık | Birincil CTA tek (Telegram); waitlist ikincil ton |
| 8. Feedback verir | "Uğraşmaya değer mi?" | 3 soru, 60 saniye, açık uçlu 1 | Form yorgunluğu | ≤3 soru; teşekkür ekranında Telegram tekrar |

---

## 7. FEEDBACK SİSTEMİ

**Demo-sonu formu (3 soru — daha fazlası yanıt oranını öldürür):**
1. *"Kendi cümlenle: bu ürün ne işe yarıyor?"* (açık uçlu — value-prop doğrulamasının altın sorusu; bizim cümlemizle örtüşme oranı ölçülür)
2. *"En yararlı ve en kafa karıştıran şey neydi?"* (tek kutu, ikisi birden — kullanıcı doğal yazar)
3. *"Bunun günlük tam sürümü için ayda 9€ öder miydin?"* — Evet / Belki / Hayır + "neden?" (opsiyonel)

**Mikro anketler (ekran içi, oturum başına en fazla 1):** karne bölümünde "Bu tablo güven verdi mi? 👍/👎"; modal kapanışında "Gerekçe anlaşılır mıydı? 👍/👎".

**Quantitative vs qualitative:** MVP'de **qualitative ağırlıklı** (n=25'te oran istatistiği anlamsız; kelimeler yön verir). NPS **sorulmaz** (bu ölçekte gürültü); yerine 3. sorunun ödeme sinyali + davranış (Telegram'a geçiş) izlenir. Ürün yönünü belirlemede en güçlü cevaplar sırasıyla: 1. soru (algı örtüşmesi), davranış verisi (hangi kartlar açıldı, nerede çıkıldı), 3. soru "neden"leri.

Depolama: `demo_feedback` tablosu (session_id, q1, q2, q3, q3_neden, mikro cevaplar, timestamp, kaynak) — GTM planındaki taxonomy'ye Cuma ritüelinde etiketlenir.

---

## 8. TEKNİK MVP SPEC

| Bileşen | Gerekli | MVP'de şart | Geçici çözüm yeterli mi | Ürüne evrim |
|---|---|---|---|---|
| Frontend | ✅ | ✅ | Mevcut Next.js; `/demo` yeniden çerçevelenir, landing hero yenilenir | Beta dashboard'la bileşen paylaşır (TierBadge vs. zaten ortak) |
| Backend/API | ✅ | Minimal | **Statik JSON yeter** — API çağrısı bile gerekmez (aşağıda) | Beta'da gerçek API'ye döner |
| Demo veri kaynağı | ✅ | ✅ | Günlük cron: dünkü taramanın Top-3'ü + karne özeti → `demo_snapshot.json` (build-time veya public/ altına); alan sözleşmesi: ticker, grade, prob_band, badges[], rationale, chart_data[], karne{} | Aynı snapshot Telegram brifini de besler — **tek üretim, iki kanal** |
| Auth | ❌ demo'da | — | Yok (sürtünme) | Beta dashboard mevcut JWT auth'u kullanır |
| Beta access control | ✅ (dashboard için) | ✅ | Davet kodu tablosu + mevcut auth | Feature-flag altyapısına evrilir |
| Analytics | ✅ | ✅ | Plausible/Umami self-host veya cloud (çerezsiz, GDPR-dostu, banner gerekmez) | Funnel dashboard'u |
| Feedback store | ✅ | ✅ | SQLite tek tablo + basit POST endpoint'i | Taxonomy alanları eklenir |
| Feature flags | ⚠️ | Hafif | Env flag yeter (demo varyantı için) | Gerçek flag sistemi sonra |
| Error logging | ✅ | ✅ | Sentry'yi aç (DSN boş duruyor — audit bulgusu; 15 dk iş) | Aynı |
| Session tracking | ✅ | ✅ | Anonim session_id (localStorage değil — cookie'siz random id per pageload zinciri; Plausible custom events) | Kullanıcı hesabına bağlanır |

**Mimari sadelik ilkesi:** Demo'nun çalışması için backend'in ayakta olması **gerekmemeli** — statik snapshot + statik sayfa; tek dinamik uç feedback POST'u. Bu, demo'yu ucuz, hızlı ve kırılmaz yapar (620 sn'lik tarama, API anahtarları, rate limit — hiçbiri demo yüzeyine dokunmaz).

---

## 9. MESAJLAŞMA VE TASARIM DİLİ

**Landing headline (önerilen):**
> **"1.812 hisse her sabah taranıyor. Dikkat çeken 3'ü, nedenleriyle."**
> Alt mesaj: *"FinPilot, büyük fiyat hareketi potansiyeli taşıyan hisseleri erken işaretleyen bir araştırma aracı. Her adayın gerekçesi açık, sistemin karnesi ortada. Karar her zaman senin."*

**Dil kuralları:**
- "AI" vurgusu: araç olarak, sihir olarak değil — "AI destekli araştırma" ✅, "AI kazandırıyor" ❌. AI kelimesi hero'da en fazla 1 kez.
- **Yasak ifadeler:** al/sat/tut tavsiyesi, hedef fiyat, "garantili", "kaçırma", "%X kazanç fırsatı", "sana özel öneri", stop/TP seviyesi gösterimi, "kesin", FOMO dili ("son 3 yer!").
- **Güçlü CTA'lar:** fayda + düşük taahhüt: "Dünün brifini gör" > "Demo'yu dene"; "Her sabah 08:30'da cebine gelsin" > "Kanala abone ol"; "Erken erişim listesine katıl" > "Kaydol".
- **Kaçınılacak vaatler:** getiri vaadi (her türlüsü), "piyasayı yenmek", isabet oranını bağlamsız afişe etmek (her zaman ölçüm tanımıyla birlikte).
- Her sayfada footer disclaimer: *"FinPilot bir araştırma ve eğitim aracıdır; yatırım tavsiyesi vermez. Geçmiş performans gelecek sonuçların garantisi değildir."*

**Görsel stil:** mevcut dark-mode dashboard dili korunur (tutarlılık); fintech ciddiyeti = koyu zemin + tek vurgu rengi + bol boşluk; oyunlaştırma görselleri yok; grafikler gerçek (süslenmemiş) OHLC. Ton: "bilgili arkadaş" — FinSense tasarımıyla aynı ses.

---

## 10. KPI VE BAŞARI ÖLÇÜTLERİ

| Metrik | Tanım | 30-gün hedefi (n küçük — yön göstergesi) |
|---|---|---|
| Landing conversion | ziyaret → demo start | ≥%40 (hedefli trafik geldiği için yüksek beklenir) |
| Demo completion | start → karne bölümünü görme | ≥%60 |
| Kart etkileşimi | ≥1 aday detayı açan | ≥%50 |
| ⓘ terim kartı kullanımı | ≥1 kart açan | ≥%25 (FinSense hipotez testi) |
| Feedback submission | tam akış → form | ≥%50 (beta kohortu), ≥%15 (soğuk trafik) |
| Telegram CTR → katılım | tık → kanala giriş | ≥%30 → ≥%60 |
| Waitlist conversion | demo → kayıt | ≥%15 |
| "Faydalı" sinyali | mikro anket 👍 oranı | ≥%70 |
| Ödeme sinyali | Q3 "Evet+Belki" | ≥%40 (Evet ≥%15) |
| Değer-algı örtüşmesi | Q1 cevabı ≈ bizim önermemiz | ≥%60 |
| Tekrar ziyaret | 7 gün içinde dönüş | ≥%25 (asıl dönüş Telegram'a — kanal açılması sayılır) |

Karar kuralı: 30. günde "değer-algı örtüşmesi" <%40 ise mesajlaşma yanlış (ürün değil, anlatım revize edilir); ödeme sinyali <%20 ise premium paketleme 60. güne ertelenir, kitle büyütmeye devam.

---

## 11. 14 GÜNLÜK UYGULAMA PLANI

**Gün 1-2 — Veri sözleşmesi ve snapshot hattı**
- `demo_snapshot.json` şeması (aday: ticker/grade/prob_band/badges/rationale/chart; karne özeti; tarih).
- Günlük cron job'u: dünkü tarama + tier karnesinden snapshot üret (mevcut scheduler'a 1 job).
- Gerekçe üretimi v1: template-tabanlı (faktör → cümle eşleme; LLM'siz başla, riski sıfırla).

**Gün 3-5 — /demo yeniden çerçeveleme**
- Mevcut 1028 satırlık sayfayı daralt: BUY/SELL, stop/TP, Kelly, 20-alan tablo çıkar; Grade kartı + karne şeridi + modal yapısına geç (TierBadge/ConvictionBadge/StockChart yeniden kullan).
- ⓘ terim kartları: 12 çekirdek terim (squeeze, gap, RVOL, ATR, short interest, tier, kalibrasyon, baz oran, rejim, catalyst, likidite, drawdown) statik içerik olarak (FinSense fabrikası beklemez; sonra oradan beslenir).

**Gün 6-7 — Landing + mesajlaşma**
- Hero yenile (headline + karne rakamı + Top-3 önizleme); "nasıl çalışır" şeridi; yasak-kelime taraması tüm metinlerde; footer disclaimer her sayfaya.

**Gün 8-9 — Ölçüm ve feedback**
- Plausible kur + custom event'ler (demo-start, kart-aç, ⓘ, karne-görüldü, CTA'lar).
- `demo_feedback` tablosu + POST endpoint'i + form sayfası + mikro anketler; Sentry DSN aktif.

**Gün 10-11 — Funnel bağlantıları**
- Telegram kanalını aç; katılım linki + UTM; waitlist'i SQLite'a taşı + davet kodu tablosu; teşekkür ekranları.

**Gün 12 — QA + içerik provası**
- 3 cihazda akış testi; snapshot cron'unun hafta sonu davranışı (piyasa kapalı → Cuma brifi + "piyasa kapalı" notu); yasak-kelime son kontrolü; yük değil ama kırık-link taraması.

**Gün 13-14 — Yumuşak açılış**
- İlk 5 tanıdık kullanıcıyla oturum (sesli düşünme protokolü — ekran başında izle, not al); ilk düzeltme turu; ardından 10 davet daha → GTM planının Hafta-2 ritmine devir.

---
*Bu spec, GTM Lansman Planı'nın (3 Tem) 4. bölümünün uygulama dokümanıdır. Snapshot hattı aynı zamanda Telegram brifinin üretim hattıdır — iki iş tek koddur. Bir sonraki revizyon bu dosyayı supersede etmelidir.*
