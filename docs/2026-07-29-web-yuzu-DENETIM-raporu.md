# Web Yüzü — DENETİM Raporu (kanıtlanmış)

Sürüm: 1.0 · Faz 1 (doğrulama) = Level A · Tarih: 2026-07-29
Kaynak: Web Yüzü Envanter v1.0 + Master Prompt (Faz 1 audit → Faz 2 önceliklendir → Faz 3 uygula)
Yöntem: her iddia KOD SATIRI + yerel dosya + (mümkünse) canlı test ile doğrulandı. Kanıtsız hiçbir etiket kesinleşmedi.

## ÖZET SAYIM
- **6 rota** doğrulandı.
- **Mockup olarak KANITLANAN, kullanıcıya görünür & landing'de CANLI:** 1 bölüm (`Newsroom`) + 3 alt bileşen (`TheWire`, `EditorialBoard`, `FactCheckingDesk`).
- **Orphan bileşen: 0** — önceki "5 orphan" iddiası **ÇÜRÜTÜLDÜ** (kanıt aşağıda).
- **Önceki rapordan düzeltilen 3 iddia:** orphan (yanlış), "endpoint yok" (artık **var**), "demo bayat/17 Tem" (artık **taze/30 Tem**).

---

## FAZ 1 — DOĞRULANMIŞ ENVANTER

### 1.1 Rota bazlı

| Rota | İddia | Kanıt (kod/dosya/canlı) | Doğrulanmış durum |
|---|---|---|---|
| `/` landing | Kısmen mockup | `page.tsx:6` `getLedgerSnapshot()` render; `:54` `<Newsroom/>` render | ⚠ **DOĞRU** — mockup bölüm canlı (bkz 1.2) |
| `/demo` | Gerçek, farklı yol | `demo/page.tsx:338` `fetch("/demo_snapshot.json")`; dosya `date=2026-07-30, universe=1812, candidates=4` | ✅ Gerçek + **artık TAZE** (eskiden 17 Tem) |
| `/methodology` | Compliance-hassas | `:64` "not investment advice", `:69` "Past performance does not guarantee future results" | ✅ **Uyumlu** (uyarılar metinde var) |
| `/premium` | Funnel zayıf | `premium/page.tsx:12-13` `NEXT_PUBLIC_STRIPE_LINK_* || ""`; env'de **tanımsız** (yalnız `.env.example:90-91`) | ⚠ **CTA yerelde BOŞ** — Vercel env doğrulanmalı |
| `/academy` | Gerçek | `academy_lessons.json` → `count: 1` (tek ders, domain financial-analysis, disclaimer var) | ⚠ **Neredeyse boş** (1 ders) |
| `/dashboard/finsense` | Public değil | `dashboard/layout.tsx:13` `<AuthProvider>` sarmalı | ⛔ **DOĞRU** — giriş arkasında |

### 1.2 Bileşen bazlı (landing Ledger) — kritik düzeltme

- **Gerçek (snapshot props):** Masthead, EditionArticle, DailyDouble, LedgerStrip, ClassroomPreview. GradeSeal (`DailyDouble:4`, `EditionArticle:3`) ve MarginNote (`EditionArticle:4`) bunların **içinde** kullanılıyor → gerçek.
- **⚠ Newsroom = mockup, ve etiketi kullanıcıya GÖRÜNMÜYOR:** `Newsroom.tsx:6-7` "Illustrative data, not live" yalnız **kod yorumu**. Kullanıcıya görünen metin gerçek yetenek gibi okunuyor: "A sample of the daily scan feed — every symbol, scored and priced before the open" (`:16`), "Three specialised agents vote independently" (`:26`), "Every research read is stress-tested" (`:37`). **Ziyaretçi bunun temsili olduğunu ANLAYAMAZ** → risk büyür.
- **"Orphan" iddiası ÇÜRÜTÜLDÜ:** `TheWire`, `EditorialBoard`, `FactCheckingDesk` → üçü de `Newsroom.tsx:1-3`'te import ediliyor ve Newsroom landing'de render ediliyor. Yani **orphan değil; landing'de CANLI mockup**. `GradeSeal`, `MarginNote` → gerçek bileşenlerce kullanılıyor. **Askıda/orphan hiçbiri yok.**

### 1.3 İki veri yolu + endpoint

- **İki yol DOĞRU:** landing `getLedgerSnapshot()` (server) — `ledgerSnapshot.ts:109` önce Render `/api/v1/distribution/snapshot`'ı dener, sonra yerel dosyaya düşer (`:124`). `/demo` client `fetch("/demo_snapshot.json")` (statik). **Farklı yollar teyitli.**
- **Endpoint artık VAR (önceki iddia güncel değil):** `api/main.py:48` import, `:382` `include_router(distribution.router)`. Kodda kayıtlı.
- **Canlı 404 testi INCONCLUSIVE:** Render endpoint fetch'i boş/yanıtsız döndü (free-tier cold-start olası). Canlı 200/404 ve Render'ın döndürdüğü snapshot **buradan kesinleşmedi** (Render log erişimi yok — kapsam dışı).
- **Ayrışma riski hafifledi ama yapısal olarak duruyor:** şu an her iki yol da aynı taze snapshot'a yakınsıyor (yerel dosya 30 Tem/1812) ve landing'de `isSnapshotStale` guard'ı var (`ledgerSnapshot.ts:128` — tarih≠bugün veya universe≠1812 ise dürüst boş-durum). `/demo`'da bu guard **yok**.

---

## FAZ 2 — ÜÇ HEDEF EKSENİNDE ÖNCELİKLENDİRME

| # | Bulgu | Hedef | Doğrulandı | Öncelik | Seviye |
|---|---|---|---|---|---|
| 1 | Newsroom + 3 alt bileşen landing'de **görünür mockup** (etiket yok) | Kredibilite | ✅ kod | **P0** | B |
| 2 | Premium CTA yerelde **boş Stripe link** (Vercel doğrulanmalı) | Funnel | ✅ kod/env | **P0*** | B |
| 3 | İki veri yolu (landing server-endpoint vs demo statik) | Kredibilite | ✅ kod | **P1** (P0→indirgeme: yakınsıyor + guard var) | B |
| 4 | Academy tek ders (içerik yüzeyi boş) | FinSense/İçerik | ✅ dosya | **P1** | B |
| 5 | FinSense sözlük public değil (positioning ile çelişki) | FinSense | ✅ kod | **P1** | B/C |
| 6 | `/demo`'da staleness guard yok (landing'de var) | Kredibilite | ✅ kod | **P2** | A |

\* Premium'un Vercel'de env'i doluysa P1'e iner; boşsa P0 (satış hunisi tamamen kopuk).

**Önceki "orphan P2" satırı KALDIRILDI** — kanıt çürüttü.

**FinSense positioning kontrolü (2.2):** "public FinSense" bir *taahhüt* mü yoksa *fikir* mi — bunu doğrulamak için strateji/roadmap dokümanına bakılmalı (bu denetimde açılmadı; kapsam dışı, aşağıda). Şu an kanıtlı olan tek şey: FinSense hem `/dashboard/finsense` (sözlük, private) hem `/academy` ("FinSense Academy" eğitim, public ama 1 ders) olarak iki yerde — ikisi de zayıf yüzey.

---

## FAZ 3 — UYGULAMA PLANI (yalnız doğrulanmış bulgular; kabul kriterli)

### 3.1 Kredibilite (önce bu)
- **ADIM:** Newsroom'u ya gerçek `snapshot`'a bağla ya landing'den kaldır (`page.tsx:54`).
  **KABUL:** Landing'de kullanıcıya görünür, kaynağı "sample/illustrative" olan hiçbir veri kalmadı (tarayıcıda gözle doğrula). — **Level B**
- **ADIM:** Landing + `/demo` tek veri yoluna: ikisi de canlı `/api/v1/distribution/snapshot`'tan okusun (endpoint kodda hazır; Render deploy'u ön koşul), statik dosya fallback.
  **KABUL:** İki sayfa aynı anda açıldığında aynı `date`+`generated_at` snapshot'ı gösteriyor. — **Level B**
- **ADIM:** `/demo`'ya landing'deki `isSnapshotStale` guard'ını ekle.
  **KABUL:** Bayat dosyada `/demo` dürüst "no edition" durumu gösteriyor, eski veriyi değil. — **Level A**

### 3.2 Funnel
- **ADIM:** Premium Stripe env'ini doğrula/doldur (Vercel `NEXT_PUBLIC_STRIPE_LINK_FOUNDING/_MONTHLY`).
  **KABUL:** `/premium` butonları gerçek Stripe checkout'a gidiyor (tıklama testi). — **Level B**
- **ADIM:** landing → demo → premium net yol + tek birincil CTA (öneri: Telegram brief).
  **KABUL:** Landing'den premium'a ≤2 tıklama; 5 public rotada aynı birincil CTA görünür. — **Level A/B**

### 3.3 FinSense / İçerik
- **ADIM:** FinSense'i public yüzeye taşı (public `/finsense` veya academy'yi FinSense'le birleştir) + içerik doldur.
  **KABUL:** Çıkış yapılmış tarayıcıda public FinSense açılıyor; yasak-dil filtresinden geçmiş; ≥N terim/ders. — **Level B (compliance)**

---

## FAZ 4 — GOVERNANCE / COMPLIANCE
- Her public değişiklik YONERGE §12 (yasak dil: al/sat/hedef) + `/methodology` "past performance" kuralına karşı yeniden kontrol edilir (her Faz 3 adımının kabul kriterine EK).
- Üretim-kritik yüzey = **Level B**; Meriç onayı olmadan uygulanamaz. Bu rapor onay yerine geçmez — analiz üretir.
- Uygulanan her adım `docs/governance/decision-log.md`'ye Layer (Product/Engineering) + Level etiketiyle işlenir.

---

## FAZ 1 — EK: Formlar (yorum/öneri + e-posta bırakma) — kanıtlanmış

**Özet:** İkisi de **GERÇEK ve uçtan uca bağlı** (mockup DEĞİL). İki risk: waitlist e-posta bildirimi kapalı; feedback gözlemlenebilirliği yok.

| Yüzey | Yol | Kanıt | Durum |
|---|---|---|---|
| **Waitlist** (e-posta) | landing → Colophon → Waitlist → `/api/v1/waitlist` → `data/waitlist_signups.json` | `page.tsx:81` `<Colophon/>`, `Colophon.tsx:3,14` `<Waitlist/>`, `Waitlist.tsx:30` POST, `waitlist_signup.py` `_save`; **4 gerçek kayıt** (email/source/signed_up_at) | ✅ Çalışıyor, veri var |
| **Feedback** (yorum/öneri) | `/demo` → Feedback → `/api/v1/demo/feedback` → SQLite `demo_feedback` | `demo/page.tsx:220,231,456`, `demo_feedback.py` `add_demo_feedback`; **0 satır (yerel DB)** | ✅ Bağlı, yerelde kayıt yok |

**Doğrulanan olumlu:**
- Render `data/` **KALICI disk** (`render.yaml:37` `mountPath:/app/data`) → kayıtlar redeploy'da kaybolmaz (aynı zamanda distribution dosyaları için de geçerli — ayrı bir endişeyi kapatır).
- İki endpoint de **public** (auth yok — doğru; `require_auth`/`Depends` yok).
- Boş feedback gönderimi backend'de yok sayılıyor (`demo_feedback.py`), e-posta regex doğrulaması var (`waitlist_signup.py`).

**Bulgular / öncelik:**
- ⚠ **Waitlist SMTP KAPALI (P1):** `.env`'de `SMTP_HOST/SMTP_PASSWORD` yok → `_notify_waitlist_signup` "skipped" logluyor. Kayıt dosyaya düşer ama **sana e-posta bildirimi gelmez** — yeni kaydı yalnız dosyayı açarak görürsün. Düzeltme: SMTP doldur VEYA Telegram admin ping ekle.
- ⚠ **Feedback gözlemlenebilirlik (P2):** yerelde 0 satır; canlı Render DB'sinde olabilir (buradan görülmez). Yeni yorum için de bildirim/panel yok — geldiğini fark etmezsin.
- ⚠ **PII/gizlilik (Level B/C):** e-posta topluyorsun; e-posta alanının yanında rıza/gizlilik notu olup olmadığı bu denetimde **doğrulanmadı** — compliance açısından kontrol edilmeli.
- Her iki form da proxy → Render'a bağımlı; Render cold-start/uykudaysa gerçek ziyaretçinin gönderimi başarısız olabilir (client tarafı dostça hata/retry önerilir).

## KAPSAM DIŞI (bu denetimin göremediği)
- **E-posta alanında rıza/gizlilik notu (PII):** doğrulanmadı — compliance kontrolü gerekiyor.
- **Canlı tarayıcı-render testi:** JS-render edilen sayfaların görsel çıktısı buradan doğrulanamadı; bulgular kod + yerel dosya kanıtına dayanıyor.
- **Vercel/Render ortam değişkenleri:** Stripe linkleri ve endpoint'in canlı 200/404 davranışı (Render cold-start) doğrulanamadı — panel erişimi gerekiyor.
- **Trafik/dönüşüm analitiği:** funnel yalnız **yapısal** (link haritası) değerlendirildi; gerçek dönüşüm oranı ölçülemez.
- **FinSense "public taahhüt mü" sorusu:** strateji/roadmap dokümanı bu denetimde açılmadı.
