# FinPilot — Telegram Bot MVP + Content Ops
## Ücretsiz/Premium Bülten Altyapısı · Otomasyon · Dağıtım · Geri Bildirim · Operasyon

**Tarih:** 2026-07-03 · **Üst dokümanlar:** GTM Lansman Planı (Bölüm 6-9) ve Web Demo MVP Spec (snapshot hattı paylaşılır).
**Kod doğrulaması:** `telegram_bot_runner.py` = ham Bot API + long-polling, tek CHAT_ID (kişisel), komutlar /start /help /scan; `telegram_alerts.py` = TelegramNotifier (sinyal + günlük özet formatı), scheduler ve watchlist router'dan çağrılıyor; kanal/broadcast/abone yönetimi **yok**. MVP'nin inşa edeceği asıl parça budur.

> İçerik konumlandırması: araştırma + eğitim. Yatırım tavsiyesi değildir; bu ibare her yayın şablonunda sabittir.

---

## 1. YÖNETİCİ ÖZETİ

Telegram MVP'si üç parçadan oluşur: **(1) Public kanal** — günlük ücretsiz brifin yayınlandığı tek-yönlü vitrin; **(2) Bot (DM)** — kayıt, /feedback, /today, demo yönlendirme ve ileride premium kapısı; **(3) Content ops hattı** — demo spec'teki `demo_snapshot.json` üretiminin aynısından beslenen, günde bir kez insan onayından geçen otomatik brif üretimi. Premium (private kanal) 4. haftadan önce açılmaz; MVP onun kapısını (davet/webhook mekanizması) hazır eder ama satmaz.

Tasarımın omurgası tek cümle: **tek üretim hattı, üç tüketici** (web demo snapshot'ı, ücretsiz kanal brifi, ileride premium brif) — içerik bir kez üretilir, kanala göre kırpılır. İnsan rolü günde 10 dakikalık onaydır; geri kalan her şey mevcut APScheduler'a eklenen job'larla otomatiktir.

Mevcut kod yeniden kullanılır ama iki yapısal değişiklik şarttır: (a) tek-CHAT_ID mimarisi kanal-yayını + abone-DM'i ayrımına genişler; (b) dışa giden her finansal metin **onay kuyruğundan** geçer (bugünkü notifier doğrudan gönderiyor — beta'da kabul edilemez).

---

## 2. TELEGRAM BOTUN ROLÜ

Rol kombinasyonu (öncelik sırasıyla):
1. **Dağıtım motoru** — günlük brifin ana kanalı (web değil Telegram birincil tüketim yüzeyi).
2. **Alışkanlık/ilişki kurucu** — sabit saat (08:30 CET), sabit format, günde 1 mesaj sözü.
3. **Feedback toplayıcı** — /feedback + haftalık tek soru.
4. **Funnel bağlayıcı** — demo, waitlist, FinSense linkleri; ileride premium kapısı.
5. Alert bot — **beta dashboard kullanıcılarına özel, kanalda değil** (kişisel alert kanala taşınırsa spam + tavsiye görünümü).
6. Komut botu / soru-cevap — bilinçli olarak **minimal** (Bölüm 6'daki 5 komut dışında yok).

Seçilen başlangıç: **Broadcast kanal + hafif etkileşimli DM botu.** Topluluk (grup/tartışma) MVP'de yok — moderasyon insan-saati yer, 100+ abone sonrası "kanala bağlı tartışma grubu" olarak değerlendirilir.

---

## 3. MVP ÖZELLİK LİSTESİ

| Özellik | MVP? | Neden |
|---|---|---|
| Günlük ücretsiz brif (kanala) | ✅ | Çekirdek; alışkanlık bunu üzerine kurulur |
| Haftalık özet (Pazar, kanala) | ✅ | Karne haftalığı = güven ritmi; üretimi zaten cron'da (weekly report) |
| /start /help /feedback /today | ✅ | Minimum etkileşim seti |
| Demo linki paylaşımı | ✅ | Her brif altında sabit satır |
| Günün öne çıkan adayları (Top-3'ten 1-2'si) | ✅ | Brifin gövdesi |
| Kısa açıklamalı aday kartları | ✅ | Grade + rozet + 1-2 cümle (demo spec ile aynı şablon) |
| Mini eğitim içeriği ("günün kavramı") | ✅ | FinSense köprüsü; 1 satır + link |
| Basit kullanıcı etiketleme (kaynak, katılım tarihi) | ✅ pasif | Sonraki segmentasyonun hammaddesi; eylem yok |
| /premium komutu | ⚠️ İskelet | "Yakında + ilgini kaydettim" cevabı — talep ölçer, satmaz |
| Premium içerik dağıtımı | ❌ 4. hafta+ | Karne birikmeden premium açmak GTM planının 1 no'lu yasağı |
| /watchlist /learn komutları | ❌ Sonra | Kapsam sürünmesi; /today yeter |
| Soru-cevap (LLM) | ❌ Sonra | Hallucination + moderasyon riski |
| Anlık alert'ler (kanala) | ❌ | Günde-1-mesaj sözünü bozar; alert beta dashboard'un işi |

---

## 4. GÜNLÜK İÇERİK OPERASYON AKIŞI

| İçerik tipi | Kaynak | Üretim | Otomasyon | İnsan onayı | Uzunluk | Katman |
|---|---|---|---|---|---|---|
| Günlük brif gövdesi (1-2 aday) | snapshot hattı (Top-3 + Grade + rozet) | Template + faktör→cümle eşleme | %95 | ✅ 10 dk (yayın öncesi) | ≤900 karakter | Ücretsiz |
| Market bağlam satırı | FRED makro rejim + endeks kapanışı | Template ("Rejim: risk-on; SPX +0.4%") | %100 | Brif onayının parçası | 1 satır | Ücretsiz |
| Karne satırı | tier karne cron çıktısı | Otomatik hesap | %100 | Haftalık göz | 1 satır | Ücretsiz |
| Günün kavramı | FinSense terim havuzu (12 çekirdek + büyür) | Rotasyon + link | %100 | İçerik zaten denetimli | 1 satır | Ücretsiz |
| Haftalık büyük resim | Edge Report + haftalık karne | LLM taslak + insan edit | %60 | ✅ 30 dk (Pazar) | 1.500-2.500 krk | Ücretsiz (özet) / Premium (tam) |
| Premium: tam Top-3 + Tier B listesi | snapshot (tam) | Template | %95 | Aynı sabah onayı | ≤1.800 krk | Premium |
| Premium: derin gerekçe + risk notları | faktör dökümü + LLM (faktör-kısıtlı) | LLM taslak | %70 | ✅ zorunlu (finansal derinlik) | aday başına ≤500 krk | Premium |
| "Bugün neden önemli?" kartı | EDGAR/haber catalyst cache | Template + LLM özeti | %70 | ✅ (haber yorumu hassas) | ≤400 krk | Premium |

**Cut-off zinciri (hafta içi):** 07:45 snapshot hazır → 07:50 draft üretilir, onay kuyruğuna düşer → 08:00-08:20 insan onayı (mobilden tek tık: onayla / düzelt / bugün yayınlama) → 08:30 kanala yayın. Onay gelmezse **yayın yapılmaz** (sessiz gün > hatalı brif) ve operatöre hatırlatma gider.

---

## 5. OTOMASYON TASARIMI (10 AŞAMA)

| Aşama | Otomasyon | HITL | En büyük risk | Doğruluk koruması |
|---|---|---|---|---|
| 1. Veri toplama | Tam (mevcut scanner/cron zinciri) | — | Bayat/eksik veri | Snapshot'a as-of damgası; veri yaşı > 24s ise draft'a uyarı bayrağı |
| 2. Taslak üretme | Tam (template-first; LLM yalnız gerekçe cümlesi) | — | LLM uydurması | **Faktör-kısıtlı üretim:** cümle yalnız snapshot alanlarından kurulabilir; sayı üretmesi yasak, sayılar template'ten gelir |
| 3. Özet çıkarma | Tam | — | Anlam kayması | Özet = alan seçimi, serbest yeniden yazım değil |
| 4. Başlık | Tam (sabit format: "Daily Brief — {tarih}") | — | Clickbait sürüklenmesi | Başlık template'i sabit, LLM dokunmaz |
| 5. İnsan onayı | — | ✅ günlük 10 dk | Onay darboğazı (tatil/hastalık) | Onaysız = yayınsız kuralı + "işaretle-ve-yayınla" mobil akışı; 2. onaycı yok, sessiz gün kabul edilir |
| 6. Formatlama | Tam (Markdown şablon + karakter limiti denetimi) | — | Kırık format | Şablon birim testi; emoji/bölüm sabit |
| 7. Zamanlama | Tam (APScheduler 08:30 CET job'u) | — | Zaman dilimi hatası | CET sabit; piyasa tatili takvimi kontrolü (tatilde "piyasa kapalı" mini mesajı) |
| 8. Dağıtım | Tam (kanal post + teslimat logu) | — | API kesintisi | Retry ×3 + başarısızlıkta operatöre DM |
| 9. Geri bildirim | Tam (emoji tepki sayımı + /feedback logu) | Haftalık okuma | Gürültü | GTM taxonomy'sine haftalık etiketleme |
| 10. Performans analizi | Tam (haftalık otomatik rapor: görüntülenme, tepki, CTR, abone delta) | Okur | Yanlış metrik kovalamak | KPI tablosu (Bölüm 10) dışına metrik ekleme disiplini |

---

## 6. ÜCRETSİZ vs PREMIUM CONTENT ARCHITECTURE

**Ücretsiz kanal:** her sabah 1 brif (1-2 aday + bağlam + karne satırı + kavram) + Pazar haftalık özeti (karnenin özeti + haftanın dersi). Değer testi: *ücretsiz katman tek başına takip etmeye değer olmalı* — kullanıcı hiç ödemese de her sabah gerçek, tarihli, karneli içerik alıyor. Kalma nedeni: alışkanlık (sabit saat) + güven birikimi (karne) + öğrenme (kavramlar).

**Premium (private kanal, 4. hafta+):** aynı sabah, **daha derin ve daha kapsamlı**: tam Top-3 + Tier B listesi (5-10 aday), aday başına derin gerekçe + risk notu ("neyi bilmelisin" FinSense bağlarıyla), izleme güncellemeleri (önceki adayların seyri), Pazar tam Edge analizi, "bugün neden önemli" catalyst kartı.
- **Fark ilkesi (GTM ile tutarlı):** zamanlama farkı YOK (erken erişim satmak sinyal-satıcılığı görünümü), mesaj sayısı farkı DEĞİL (premium ≠ daha çok bildirim); fark = **derinlik + kapsam + bağlam**. Premium kullanıcı "daha çok mesaj alan" değil "daha derin araştırma okuyan" kişidir.
- Neden ödesin: her gün 5-10 aday yerine 1-2 görüyor olmanın eksikliğini ücretsiz karne satırı kendiliğinden hissettirir ("bugün Grade A 1, Grade B 6 aday vardı — 2'sini gördün").

---

## 7. BOT KOMUT YAPISI

| Komut | Kullanıcı ihtiyacı | Bot cevabı | CTA | MVP? |
|---|---|---|---|---|
| /start | "Bu ne, ne alacağım?" | 3 satır tanıtım + günde-1-mesaj sözü + disclaimer + kaynak etiketi kaydı | Kanala katıl + demo linki | ✅ |
| /today | "Bugünkü brif nerede?" | Son yayınlanan brifi DM'e iletir | Kanal linki | ✅ |
| /feedback | "Söyleyeceğim var" | "Yaz, okuyorum" → serbest metin loglanır + teşekkür | — | ✅ |
| /help | "Ne yapabilirim?" | Komut listesi + SSS linki | — | ✅ |
| /premium | "Fazlası var mı?" | "Premium hazırlanıyor; ilgini kaydettim, ilk açılışta haber vereceğim" → ilgi logu | Waitlist | ✅ iskelet |
| /watchlist, /learn | — | — | — | ❌ sonra (kapsam disiplini) |
| /scan | Sahibin kişisel komutu | Mevcut davranış | — | ✅ ama **yalnız admin ID'ye kilitli** (bugün herkese açık olma riski kapatılır) |

---

## 8. TEKNİK MİMARİ

| Bileşen | Zorunlu | Basit versiyon | Ölçeklenirken |
|---|---|---|---|
| Bot backend | ✅ | Mevcut long-polling runner genişler (ham Bot API korunur; kütüphane şart değil) | Webhook moduna geçiş (>1K abone) |
| Kanal yayını | ✅ | Bot kanal admini; `sendMessage(chat_id=@kanal)` — TelegramNotifier'a `send_to_channel()` eklenir | Aynı |
| Scheduler | ✅ | Mevcut APScheduler'a 3 job: draft-üret (07:50), onay-hatırlat (08:15), yayınla (08:30, onay şartlı) | Aynı |
| Onay kuyruğu | ✅ | SQLite `broadcast_queue` (draft, durum: pending/approved/rejected, onaylayan, ts) + operatöre DM'le draft + "ONAYLA yaz" akışı (ekstra UI gerekmez — Telegram'ın kendisi onay arayüzüdür) | Web admin sayfası |
| Mesaj şablonları | ✅ | `telegram/templates/` altında versiyonlu Markdown şablonları + birim testi | A/B varyantları |
| Abone/etiket store | ✅ | SQLite `tg_users` (user_id, kaynak, katılım, son_etkileşim, premium_ilgi, premium_durum) | Postgres'le birleşir |
| Broadcast logic | ✅ | Kanal = Telegram dağıtır (tek post, abone yönetimi Telegram'da — ilk büyük sadelik kazancı); DM broadcast yalnız kritik durumda | Premium DM dizileri |
| Premium gating | ⚠️ iskelet | Private kanal + tek-kullanımlık davet linki; Stripe webhook → `createChatInviteLink(member_limit=1)` → DM ile gönder; iptal webhook'u → `banChatMember`+unban (çıkarma) | Abonelik durum senkron job'u (günlük) |
| Feedback logu | ✅ | `tg_feedback` tablosu | Taxonomy alanları |
| Analytics | ✅ | Kanal post görüntülenme (Telegram API) + tepki sayımı + UTM'li linkler; haftalık rapor cron'u | Panel |
| Error handling / retry | ✅ | Gönderimde ×3 backoff; başarısızlıkta operatör DM'i; tüm gönderimler `tg_delivery_log`a | Alerting |

**Güvenlik notları:** /scan admin-kilidi; bot token'ı zaten .env'de (git-dışı, doğrulandı); onay kuyruğunda "ONAYLA" yalnız admin user_id'den kabul edilir.

---

## 9. OPERASYON KURALLARI

1. **Yayın saati sabittir:** hafta içi 08:30 CET; tatilde kısa "piyasa kapalı" notu veya sessizlik (takvime bağlı, otomatik).
2. **Cut-off:** 08:20'ye kadar onaylanmayan brif o gün yayınlanmaz; telafi mesajı atılmaz ("özür spam'i" yasak). Haftada >1 sessiz gün → süreç gözden geçirilir.
3. **Günde 1 mesaj tavanı** (Pazar 2: brif yok, haftalık var). İstisna: yok. "Acil piyasa mesajı" diye bir tür MVP'de tanımlı değildir — acil mesaj dürtüsü, spam'in başladığı yerdir.
4. **Format standardı:** şablon dışı yayın yok; emoji seti sabit; her mesajın sonu: demo linki + disclaimer satırı.
5. **Uyum dili:** yasak-kelime listesi (al/sat/hedef fiyat/garanti/kaçırma/sana özel) şablon testinde otomatik taranır; "aday/izleme/geçmişte %X" çerçevesi zorunlu.
6. **Hata protokolü:** yanlış veri yayınlandıysa aynı formatta tek düzeltme mesajı ("Düzeltme: bu sabahki brifte $X'in Y değeri hatalıydı, doğrusu Z") — silme + sessizlik değil; düzeltme şeffaflığı karne kültürünün parçası.
7. **Premium destek:** premium kullanıcı DM'leri 24 saat içinde tek kişi tarafından cevaplanır; SSS'ye dönüşen sorular /help içeriğine işlenir.
8. **Haftalık ritüel (Cuma, GTM ile ortak):** feedback + metrik raporu okunur; 1 iyileştirme kararı alınır ve kanalda "şunu duyduk → şunu değiştirdik" tek satırıyla paylaşılır.

## 10. KPI TABLOSU

| KPI | Ölçüm | 30 gün | 60 gün | 90 gün |
|---|---|---|---|---|
| Abone | kanal üye sayısı | 50+ | 100+ | 200+ |
| Okuma proxy'si | post görüntülenme / abone | ≥%60 | ≥%50 | ≥%45 |
| Tepki oranı | emoji tepki / görüntülenme | ≥%5 | ≥%5 | ≥%5 |
| CTR | brif linklerine tıklama (UTM) | ≥%8 | ≥%8 | ≥%10 |
| Feedback | /feedback + haftalık soru yanıtı | ≥10/ay | ≥15/ay | ≥20/ay |
| Demo dönüşümü | kanal→demo ziyareti | izlenir | ≥%15 | ≥%15 |
| Premium ilgi | /premium tıklayan benzersiz kullanıcı | ≥%10 abone | ≥%12 | dönüşüm testine girer |
| Free→premium | ödeme / abone | — | — | ≥%2 |
| Churn | ayrılan / abone (aylık) | <%10 | <%8 | <%8 |
| Sessiz gün | onay kaçırma | ≤2/ay | ≤1/ay | ≤1/ay |

## 11. 21 GÜNLÜK UYGULAMA PLANI

**Gün 1-3 — Temel altyapı**
- Public kanal aç (@finpilot_brief benzeri); botu admin yap; `send_to_channel()` + `tg_delivery_log`.
- `tg_users`, `tg_feedback`, `broadcast_queue` tabloları; /scan'e admin kilidi.
- Şablon dosyaları (günlük brif, haftalık, düzeltme, tatil) + yasak-kelime testi.

**Gün 4-7 — İçerik hattı**
- Snapshot→draft üretici (demo spec Gün 1-2 çıktısını tüketir; faktör→cümle template'leri).
- Scheduler job'ları: 07:50 draft → operatöre DM → "ONAYLA" akışı → 08:30 yayın (onay şartlı).
- Tatil takvimi kontrolü; retry + hata DM'i.
- **Gün 7'den itibaren:** kanal yalnız beta kullanıcılarına açık halde günlük yayına başlar (prova haftası — gerçek ritim, küçük seyirci).

**Gün 8-12 — Bot etkileşimi**
- /start (kaynak etiketi + söz + disclaimer), /today, /feedback, /help, /premium iskeleti.
- UTM'li linkler; kanal görüntülenme + tepki toplayıcı; haftalık otomatik metrik raporu cron'u.

**Gün 13-15 — Prova değerlendirme + açılış hazırlığı**
- 1 hafta provanın metrikleri + beta feedback'i ile şablon revizyonu (tek tur).
- Pazar haftalık özet formatının ilk gerçek sayısı.
- Landing + demo sayfalarına kanal CTA'larının bağlanması (UTM ile).

**Gün 16-18 — Halka açılış**
- Kanal linki waitlist'e e-postayla + demo sayfasına canlı; build-in-public ilk paylaşım.
- Onay akışının mobil provası (operatör telefondan 10 dk'da yönetebiliyor mu — asıl DoD budur).

**Gün 19-21 — Premium iskeleti (satışsız)**
- Private kanal + davet-link üretimi + Stripe webhook script'inin uçtan uca testi (test modunda 1 ödeme → otomatik davet → iptal → çıkarma).
- /premium ilgi sayacı raporlamaya bağlanır; premium içerik şablonları hazır (yayın 4. hafta GTM kapısına bağlı).
- 21. gün çıktısı: kesintisiz ≥10 yayın günü, ≥50 abone yolu açık, insan yükü ≤15 dk/gün ölçülmüş.

---
*Bu doküman GTM Lansman Planı'nın Telegram kolunun uygulama spec'idir; Web Demo MVP Spec'in snapshot hattını paylaşır (tek üretim, üç tüketici). Bir sonraki revizyon bu dosyayı supersede etmelidir.*
