# FinPilot — Ticari Katman Uygulama Planı
## Web Demo Spec + Telegram Bot MVP + Free-to-Paid Funnel'ın Hayata Geçirilmesi

**Tarih:** 2026-07-03 · **Uyguladığı dokümanlar:** `FinPilot_Web_Demo_MVP_Spec` (14 gün), `FinPilot_Telegram_Bot_MVP_ContentOps` (21 gün), `FinPilot_FreeToPaid_Funnel` (30 gün).
**Kod doğrulaması bu plan için yapıldı:** `data/daily_reports/*.json` mevcut ama **eski dilde** (BUY/stop/TP) ve tier/conviction alanları YOK; `signals_archive` + `GET /watchlist/performance` (by_tier/by_conviction) karne kaynağı olarak hazır; waitlist JSON dosyasına yazıyor; sistem **tamamen lokal** çalışıyor (public hosting yok — bu planın gizli en büyük işi).

---

## 0. BÜYÜK RESİM

Üç doküman tek ürün hattını tarif ediyor; uygulama **4 iş kolu + 1 ön koşul** olarak örgütlenir:

```
ÖN KOŞUL: Public hosting (şu an her şey lokal!)
        │
İŞ KOLU A: Snapshot/İçerik Hattı  ←← ortak çekirdek, her şey buna bağlı
        ├── İŞ KOLU B: Web Demo + Landing + Feedback
        ├── İŞ KOLU C: Telegram Kanal + Bot + Onay Akışı
        └── İŞ KOLU D: Premium + Ödeme + Funnel   (4-hafta karne kapısına bağlı)
```

**Toplam efor tahmini:** ~18-24 geliştirme günü (A:5, B:5, C:5, D:4, hosting:2-3, tampon dahil) → 30 takvim gününe rahat sığar; D'nin *yayına alınması* karne kapısı gereği 5. haftaya sarkar (mekanik 4. haftada hazır ve test edilmiş olur).

---

## 1. ÖN KOŞUL — PUBLIC HOSTING (gizli blokör, ilk karar)

**Sorun:** Demo, feedback endpoint'i, Telegram webhook'ları ve Stripe webhook'u internetten erişilebilir olmalı. Bugün `start.sh` lokal; hiçbir deploy hedefi yok (Haziran audit bulgusu).

**Önerilen mimari (minimum maliyet, minimum yeni parça):**

| Parça | Nerede | Neden |
|---|---|---|
| Web (landing + demo + offer page) | **Vercel veya Cloudflare Pages** (Next.js statik export — `web/out` zaten üretiliyor) | Ücretsiz, CDN, sıfır bakım; demo zaten statik-snapshot tasarımı |
| Küçük API (feedback POST, waitlist POST, Stripe webhook) | **Fly.io / Hetzner küçük VPS** üzerinde FastAPI'nin daraltılmış "public profili" (yalnız 3-4 router) | Tam FinPilot API'sini internete açmak gereksiz risk; ayrı hafif `api-public` compose profili |
| Scanner + scheduler + bot + snapshot üretimi | **Meriç'in makinesi (mevcut düzen)** — üretilen snapshot'ı public tarafa iter | Tarama altyapısını taşımak bu fazın işi değil; push-tabanlı ayrım güvenli |
| Snapshot aktarımı | Cron sonunda `demo_snapshot.json` → web repo'suna commit/Vercel API/S3-R2 upload (tek script) | Statik dosya = en kırılmaz köprü |

**Karar gereken:** Vercel vs Cloudflare Pages (ikisi de olur; Vercel önerilir — Next uyumu) ve VPS sağlayıcı. **Meriç aksiyonu:** hesap açma + domain (örn. finpilot.app benzeri) bağlama. Efor: 2-3 gün (ilk kurulum + CI'a `deploy-web` adımı).

---

## 2. İŞ KOLU A — SNAPSHOT / İÇERİK HATTI (ortak çekirdek)

**Amaç:** Günde bir kez, tier/conviction dilinde, üç tüketiciye (demo, ücretsiz brif, premium brif) yetecek tek veri paketi üretmek.

**Yeni modül: `distribution/`** (research/product ayrımı gereği scanner'a gömülmez):

| Dosya | İçerik |
|---|---|
| `distribution/snapshot_builder.py` | Günün scan sonucundan (evaluate çıktısı: `conviction_tier`, `conviction_prob`, `tier`, rozet faktörleri) Top-3 + Tier B listesi + karne özetini (`watchlist_db` by_tier/by_conviction + sistem-geneli arşiv isabeti) derler → `data/distribution/snapshot_YYYY-MM-DD.json` |
| `distribution/rationale.py` | Faktör→cümle template motoru (LLM'siz v1): `{"squeeze":"Yüksek short oranı...", "gap":"Bu sabahki gap..."}` eşleme tablosu + birleştirme kuralları |
| `distribution/templates/` | `daily_brief_free.md.j2`, `daily_brief_premium.md.j2`, `weekly.md.j2`, `correction.md.j2`, `holiday.md.j2` |
| `distribution/lint.py` | Yasak-kelime denetçisi (al/sat/hedef fiyat/garanti/kaçırma/sana özel + stop/TP sayısı sızıntısı) — şablon render çıktısında çalışır, ihlalde draft bloke |
| `distribution/publish.py` | Snapshot'ı public web'e iter (commit/upload) + Telegram draft'ını kuyruğa yazar |

**Veri sözleşmesi (`snapshot_vN` şeması — versiyonlu):**
```json
{ "schema": 1, "date": "...", "generated_at": "...", "config_sha": "...",
  "universe": 1812, "candidates": [ { "ticker","company","grade","prob_band",
  "badges": ["squeeze","gap","rvol"], "rationale","chart": [...OHLC 30g...],
  "premium_only": false, "risk_note": "(premium)", "factor_detail": {...} } ],
  "karne": { "window":"...", "by_grade": {"A":{"n":..,"hit5":..}, ...}, "toplam_aday_bugun": {"A":1,"B":6} } }
```
`config_sha` = Tam Sistem Audit'in config-manifest kararıyla aynı damga (iki iş tek taşla).

**Kritik entegrasyon işi:** `daily_reports` yazarı eski dilde → snapshot_builder **daily_reports'u KULLANMAZ**; scan sonucunun tam payload'ından (scan router'ın döndürdüğü / arşive yazılan kayıt) beslenir. Gerekirse `core/pipeline` sonuna "distribution export" adımı eklenir (±30 satır).

**Scheduler job'ları (mevcut APScheduler'a):** `dist_snapshot` (07:45 CET, hafta içi, tatil takvimi kontrolü) → `dist_draft` (07:50, şablon + lint + kuyruk + operatöre DM) → `dist_publish` (08:30, yalnız `approved` ise kanal + web push) → `dist_weekly` (Pazar 10:00).

**DoD:** 3 ardışık gün, elle müdahalesiz snapshot + draft üretimi; lint testleri yeşil; snapshot şema birim testi; kötü-veri günü (eksik karne) → draft'a uyarı bayrağı düşüyor.
**Efor:** 5 gün.

---

## 3. İŞ KOLU B — WEB DEMO + LANDING + FEEDBACK

| İş | Dosya/Yer | Detay | Efor |
|---|---|---|---|
| B1. Demo sayfası yeniden çerçeveleme | `web/src/app/demo/page.tsx` (1028 satır) | BUY/SELL, stop/TP, Kelly, 20-alan tablo ÇIKAR; `snapshot.json`'dan Grade kartları + karne şeridi + detay modalı; TierBadge/ConvictionBadge/StockChart yeniden kullan | 2 gün |
| B2. ⓘ terim kartları | `web/src/lib/terms.ts` (statik, 12 terim) + `TermCard` bileşeni | FinSense fabrikası beklenmez; içerik bu plandaki ekle, sonra content-pack'ten beslenir | 0.5 gün |
| B3. Landing hero | `web/src/app/page.tsx` + HeroGrid | Headline ("1.812 hisse her sabah taranıyor...") + canlı karne rakamı (snapshot'tan) + nasıl-çalışır şeridi + footer disclaimer her sayfaya | 1 gün |
| B4. Feedback | Yeni `api/routers/demo_feedback.py` + `demo_feedback` tablosu + `/feedback` sayfası + 2 mikro-anket | 3-soru formu; public-API profiline dahil | 1 gün |
| B5. Waitlist sertleştirme | `api/routers/waitlist_signup.py` | JSON→SQLite taşı; e-posta doğrulama regex'i; kaynak/UTM alanı; davet kodu tablosu (`beta_invites`) | 0.5 gün |
| B6. Analytics + hata | Plausible script'i (layout.tsx) + custom event'ler (demo-start, kart-aç, ⓘ, CTA'lar); Sentry DSN aktive | 0.5 gün |

**DoD:** Lighthouse'da temel skorlar makul; tüm CTA'lar UTM'li; yasak-kelime taraması web metinlerinde temiz; 3 cihazda akış testi; feedback kaydı uçtan uca düşüyor.
**Efor:** 5 gün (B1 en riskli — mevcut sayfayı bozmadan daraltma; gerekirse yeni sayfa yazıp eskisini `demo-legacy`'ye taşı, daha hızlı olabilir).

---

## 4. İŞ KOLU C — TELEGRAM KANAL + BOT + ONAY AKIŞI

| İş | Dosya/Yer | Detay | Efor |
|---|---|---|---|
| C1. Kanal + bot kurulumu | BotFather (Meriç) | Public kanal; botu admin yap; token .env'de kalır | 0.5 gün (Meriç) |
| C2. Kanal yayını | `telegram_alerts.py` → `send_to_channel(text)` + `tg_delivery_log` tablosu + retry ×3 | Mevcut Notifier deseni genişler | 0.5 gün |
| C3. Onay kuyruğu | `broadcast_queue` tablosu + akış: draft → operatöre DM → operatör "ONAYLA"/"RED" yazar (yalnız admin user_id) → durum güncellenir | Telegram'ın kendisi onay UI'sı; ekstra panel yok | 1 gün |
| C4. Bot komutları | `telegram_bot_runner.py` refactor: `/start` (kaynak etiketi + söz + disclaimer + `tg_users` kaydı), `/today`, `/feedback` (→`tg_feedback`), `/help`, `/premium` (ilgi logu); **`/scan`'e admin-ID kilidi** | Mevcut polling korunur | 1.5 gün |
| C5. Metrik toplayıcı | Kanal post görüntülenme + tepki sayımı + UTM raporu → haftalık otomatik rapor cron'u (`dist_weekly_metrics`) | | 1 gün |
| C6. Tatil takvimi | `distribution/market_calendar.py` (NYSE tatilleri statik liste, yıllık güncelleme) | dist_snapshot bunu kontrol eder | 0.5 gün |

**DoD:** 5 ardışık iş günü prova yayını (beta izleyiciyle); onay akışı telefondan ≤10 dk; onay gelmeyince yayın YOK ve hatırlatma düşüyor; teslimat logu dolu; /scan artık yalnız admin.
**Efor:** 5 gün.

---

## 5. İŞ KOLU D — PREMIUM + ÖDEME + FUNNEL MEKANİĞİ

| İş | Dosya/Yer | Detay | Efor |
|---|---|---|---|
| D1. Stripe kurulumu | Stripe hesabı (Meriç) + 3 Payment Link (founding €99/yıl, aylık €9, lifetime €149) + 14g iade politikası metni | Kod yok | 0.5 gün (Meriç) |
| D2. Webhook→davet | `api/routers/stripe_webhook.py` (public-API profili): `checkout.session.completed` → `createChatInviteLink(member_limit=1)` → e-posta/DM ile gönder → `tg_users.premium_durum=aktif`; iptal/iade webhook'u → `banChatMember`+unban | ~120 satır + imza doğrulama | 1.5 gün |
| D3. Private kanal + premium şablon | Kanal (Meriç) + `daily_brief_premium.md.j2` aktivasyonu (snapshot'ta zaten tam veri var — sadece şablon farkı) | | 0.5 gün |
| D4. Offer page | `web/src/app/premium/page.tsx`: fark tablosu + örnek tam sayı (gerçek, tarihli) + SSS + disclaimer | Statik | 1 gün |
| D5. Onboarding + churn otomasyonu | Hoş geldin DM dizisi (kılavuz + beklenti cümlesi), 5-gün-açmama sinyali, çıkış anketi; hepsi scheduler job'u + şablon | | 1 gün |
| D6. Aylık örnek-tam-sayı job'u | Ayda 1, tam premium sayının ücretsiz kanala yayını (funnel'ın ana silahı) | dist hattına bayrak | 0.25 gün |

**DoD:** Test modunda uçtan uca: ödeme → otomatik davet → kanala giriş → iptal → otomatik çıkarma; onboarding mesajları tetikleniyor; offer page yasak-kelime temiz. **Yayın kapısı:** ≥4 hafta kesintisiz karne + ≥100 abone (GTM kuralı) — mekanik hazır bekler.
**Efor:** 4 gün.

---

## 6. VERİTABANI DEĞİŞİKLİKLERİ (tek migration seti)

`migrations/` altına tek dosya (mevcut alembic düzenine): `tg_users`, `tg_feedback`, `tg_delivery_log`, `broadcast_queue`, `demo_feedback`, `beta_invites`, `waitlist` (JSON'dan taşınan) + `premium_ilgi` sayaç alanları. Hepsi SQLite-uyumlu, Postgres go/no-go kararını (audit 90-gün maddesi) beklemez.

## 7. HESAP / ERİŞİM KURULUMLARI — MERİÇ'İN YAPACAKLARI

| # | İş | Süre | Ne zaman |
|---|---|---|---|
| 1 | Domain seçimi + satın alma | 30 dk | Gün 1 |
| 2 | Vercel (veya CF Pages) hesabı + repo bağlama | 30 dk | Gün 1-2 |
| 3 | VPS/Fly.io hesabı (public-API için) | 30 dk | Gün 2-3 |
| 4 | BotFather: bot (mevcut token olur) + public kanal + private kanal | 30 dk | Gün 8 |
| 5 | Plausible hesabı (veya self-host kararı) | 15 dk | Gün 4 |
| 6 | Sentry projesi + DSN | 15 dk | Gün 4 |
| 7 | Stripe hesabı (kimlik doğrulama + banka) — **tüzel kişilik sorusu:** başlangıçta şahıs (Einzelunternehmen) olarak alınabilir; GmbH kararı hibe planındaki takvime bağlı, ödemeyi bloke etmez ama vergi kaydı (Avusturya, Kleinunternehmer eşiği) muhasebeciye danışılmalı | 1-2 saat + danışma | Gün 15-20 |
| 8 | Günlük onay ritüeli (08:00-08:20, telefondan) | 10 dk/gün | Gün 10'dan itibaren |
| 9 | Cuma feedback ritüeli | 45 dk/hafta | Hafta 2'den itibaren |

Kod tarafındaki her şeyi (A-D kollarının tamamı, migration'lar, şablonlar, testler) ben yazabilirim; 7. maddedeki vergi/tüzel konu bu planın tek "dışarıdan görüş" gerektiren kalemi.

## 8. 30 GÜNLÜK BİRLEŞİK TAKVİM

**Hafta 1 (Gün 1-7) — Temel + çekirdek hat**
- G1-2: Hosting kararı + hesaplar (Meriç ¹²³) · snapshot şeması + `snapshot_builder` v1 (A) — paralel
- G3-4: `rationale` template motoru + lint + şablonlar (A) · pipeline'a distribution export adımı (A)
- G5: Scheduler job'ları (dist_snapshot/draft) + 12 terim içeriği (B2)
- G6-7: Demo sayfası yeniden yazımı başlar (B1) · public-API profili iskeleti + VPS deploy (hosting)
- ✔ Hafta sonu kontrol: snapshot 2 gün üretti mi, lint yeşil mi

**Hafta 2 (Gün 8-14) — Demo canlı + Telegram prova**
- G8: Kanallar + bot kurulumu (Meriç ⁴) · `send_to_channel` + delivery log (C2)
- G9-10: B1 biter; landing hero (B3); feedback + waitlist (B4-B5); Plausible+Sentry (B6, Meriç ⁵⁶)
- G11: Onay kuyruğu (C3) · bot komutları başlar (C4)
- G12: Web deploy → **demo yumuşak açılış: ilk 5 tanıdık kullanıcı, sesli-düşünme oturumu**
- G13-14: C4 biter · **Telegram prova yayını başlar (beta izleyiciyle, gerçek 08:30 ritmi)** · ilk düzeltme turu
- ✔ Kapı: demo canlı + 5 kullanıcı verisi + prova yayını dönüyor

**Hafta 3 (Gün 15-21) — Beta genişleme + halka açık kanal**
- G15-16: Beta 15-25 kişiye (davet kodları) · metrik toplayıcı + haftalık rapor cron'u (C5) · tatil takvimi (C6)
- G17: **Kanal halka açılır** (waitlist e-postası + demo CTA'ları canlı) · build-in-public ilk paylaşım
- G18-19: Stripe + webhook→davet geliştirme (D1-D2, Meriç ⁷ başlatır) · Pazar haftalık formatının ilk gerçek sayısı
- G20-21: İlk Cuma ritüeli (feedback taxonomy + "duyduk→yaptık" mesajı) · offer page taslağı (D4)
- ✔ Kapı: kesintisiz ≥7 yayın günü, ≥30-50 abone, insan yükü ≤15 dk/gün ölçüldü

**Hafta 4 (Gün 22-30) — Premium mekaniği hazır (satış kapalı) + değerlendirme**
- G22-23: D2 uçtan uca test (test ödemesi → davet → iptal → çıkarma) · premium şablon (D3)
- G24-25: Onboarding/churn otomasyonu (D5) · örnek-tam-sayı job'u (D6) · offer page yayına hazır (gizli URL)
- G26-27: /premium ilgi sayacı raporda · demo feedback'in ilk 3 düzeltmesi işlendi
- G28-30: **30-gün değerlendirmesi:** GTM kapı metrikleri (beta aktifliği, abone, açılma, feedback) + karar: karne 4 haftayı doldurduğunda (takvimce ~hafta 5-6) funnel dokümanının Hafta-2'si ("yumuşak açılış") tetiklenir.

**Hafta 5+ (funnel dokümanına devir):** örnek tam sayı → offer canlı → founding satışı → ilk 10 ödeme döngüsü (Funnel dokümanı Hafta 2-4 planı aynen).

## 9. TEST VE KALİTE

- **Birim:** snapshot şema doğrulama, lint yasak-kelime seti, template render'ları, webhook imza doğrulama, davet-link üretimi (mock Bot API).
- **Entegrasyon:** dist_snapshot→draft→onay→yayın zinciri (staging kanalında); ödeme→davet→iptal zinciri (Stripe test modu).
- **Manuel prova:** operatör onayı telefondan; tatil günü davranışı; kötü-veri günü (karne boş) davranışı.
- **Sürekli:** her yayın `tg_delivery_log`a; her draft lint'ten; CI'a `distribution/` testleri + web build eklenir.

## 10. RİSKLER VE KARAR KAPILARI

| Risk | Erken sinyal | Önlem |
|---|---|---|
| Hosting işi tahmini aşar | G7'de public-API ayakta değil | Fallback: feedback/waitlist için geçici form servisi (Tally) + demo tam statik — lansman gecikmez |
| Snapshot verisi eksik/eski dil sızıyor | Lint ihlalleri, boş tier alanları | Snapshot builder scan payload'ından okur (daily_reports'tan değil); şema zorunlu alan testi |
| Onay ritüeli aksar | Haftada >1 sessiz gün | Ritüel saatini Meriç'in gerçek sabahına göre kaydır (08:30 yayını 09:00'a almak serbest — sabitlik saatten önemli) |
| Beta feedback'i demoyu büyütmeye zorlar | "Şu özelliği de ekle" baskısı | Kapsam bekçisi: MVP-dışı istekler funnel/backlog'a, kural-of-3 |
| Karne 4 haftayı doldurmadan satış baskısı | Erken /premium ilgisi yüksek | Kapı esnemez; ilgiyi kaydet, "yakında" de — GTM 1 no'lu yasağı |
| Stripe/vergi belirsizliği | D1 gecikir | Satış kapısı zaten hafta 5+; muhasebeci görüşmesi G15'te başlarsa yetişir |

**Karar kapıları:** G7 (snapshot hattı dönüyor mu) · G12 (demo canlı mı) · G17 (kanal açılışı) · G21 (yayın ritmi + insan yükü) · Hafta 5 (karne + abone eşiği → satış açılışı).

---
*Bu plan üç spec dokümanını tek mühendislik takvimine indirir. Uygulamaya `distribution/snapshot_builder.py` + şema ile başlanır — her şeyin bağımlı olduğu tek parça odur. Bir sonraki revizyon bu dosyayı supersede etmelidir.*
