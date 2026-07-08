# FinPilot — UÇTAN UCA ÜRÜN PLANI
## "The Morning Ledger × Classroom" · Landing + Public Yüzey + TAM DASHBOARD
### Her ekran gerçek bir uca bağlı; her gelecek özellik için yuva hazır

**Tarih:** 2026-07-05 · **Supersedes:** Master Tasarım dokümanının kapsam bölümü (tasarım dili aynen geçerli; bu plan onu dashboard dahil tüm sisteme genişletir).
**Endpoint envanteri bu plan için koddan doğrulandı** (watchlist 11 uç, history 5, closed_loop 8, trade, academy 7, scan, analytics, profitcore).

---

## 0. İLKELER

1. **Tek tasarım dili, iki yüzey:** Public (Ledger×Classroom master şablonu) ve auth'lu Dashboard ("The Reader's Desk") aynı token setini kullanır — kullanıcı giriş yaptığında başka bir ürüne düşmez, gazetenin "editör masasına" geçer.
2. **Sahte ekran yok:** Her dashboard bileşeni ya (A) bugün çalışan bir uca bağlıdır, ya (B) env-flag arkasında hazır uca bağlıdır, ya da (C) "yuva" (slot) olarak tasarlanmış ve veri sözleşmesi şimdiden tanımlanmıştır. A/B/C etiketi her bileşende bu planda yazılıdır.
3. **Compliance her yüzeyde:** BUY/SELL, stop/TP, pozisyon boyutu kullanıcı yüzeyinde YOK (backend alanları durur, UI Grade diline çevirir). Kolofon disclaimer her ekranda.
4. **Tek Grade dili:** Dashboard'daki eski üç sözlük (score/tier/conviction) kullanıcıya tek Grade + olasılık bandı + faktör rozeti olarak sunulur (Audit P0 kararı burada ürünleşir). Ham skorlar yalnız "Labs"ta.
5. **Uzun işlem dürüstlüğü:** Tarama 1-10 dk sürebilir — sahte spinner değil, gerçek aşama göstergesi (backend timing logları zaten var).

---

## 1. SİSTEM HARİTASI

```
                    ┌────────────── PUBLIC (Vercel) ──────────────┐
Ziyaretçi ──────►  Landing → Yesterday's Edition → Ledger → Classroom-lite → Full Edition
                    └───────────────┬──────────────┘
                          waitlist / davet kodu / Telegram
                                    ▼
                    ┌────────── DASHBOARD (auth, "Reader's Desk") ─────────┐
Üye ─── JWT ──►    D1 Today  D2 Scanner  D3 Watchlist  D4 Ledger  D5 Classroom
                    D6 Paper Desk  D7 Settings  [Labs: DRL/AI — experimental]
                    └───────────────┬──────────────────────────────────────┘
                                    ▼  /api/v1/*
   FastAPI: scan · watchlist · history · closed_loop · academy · trade · auth · analytics
                                    ▼
   Motor: scanner/evaluate → distribution (snapshot/brif) → scheduler → Truth zinciri
```

Veri tazeliği modeli: Dashboard **polling + manuel yenile** (websocket yok, v1'de gerekmez); snapshot dosyası + API uçları karışık beslenir; her panel sağ üstte "as of 08:31" damgası taşır (amber=bugün, mürekkep=arşiv kuralı burada da geçerli).

---

## 2. TASARIM SİSTEMİ — DASHBOARD EKLERİ

Master şablonun tüm token'ları geçerli (ink navy, chalk cream, gold/steel/gray Grade, violet FinSense, amber=canlı, sage/brick sonuç). Dashboard'a özgü ekler:

- **Desk yoğunluğu:** Public serif-ferah; Desk'te tablolar `JetBrains Mono` + 13px sıkı satır, ama başlıklar yine serif — "editör masası" hissi.
- **Panel çerçevesi:** Her panel gazete kutusu gibi ince çift çizgili başlık taşır: `— WATCHLIST · 12 items · as of 09:14 —`.
- **Uzun işlem bileşeni (ScanProgress):** aşama şeridi `Sweep → Enrich → Grade → Done` + geçen süre mono sayaç + iptal; arkada kalan aşamalar soluk.
- **Boş durum sesi:** her boş panel tek cümle "öğretmen sesi" taşır (ör. watchlist boş: "An empty watchlist is a choice, not a failure. Today's edition has 3 candidates →").
- **Hata standardı:** kırmızı banner yok; panel içinde brick renkli tek satır + "retry" + hata kodu mono.

---

## 3. PUBLIC YÜZEY (özet — master şablon geçerli)

| Sayfa | Kaynak veri | Durum |
|---|---|---|
| Landing S1-S8 | `demo_snapshot.json` (S2, S4), statik içerik | **A** — snapshot canlı |
| Yesterday's Edition | `demo_snapshot.json` | **A** |
| The Ledger (public) | snapshot.karne + haftalık edge özeti (statik export'a eklenecek alan) | **A** (karne) / **B** (edge özeti — export'a 1 alan) |
| Classroom-lite (sözlük + 3 örnek ders) | `terms.ts` + statik ders içeriği | **A** |
| Full Edition | Stripe linkleri (env) | **B** — linkler girilince canlı |

---

## 4. DASHBOARD — "THE READER'S DESK" (ekran ekran)

Navigasyon: sol ince ray (Desk ikonografisi): **Today · Scanner · Watchlist · Ledger · Classroom · Paper Desk · Settings** + altta küçük "Labs" (soluk). Üst bar: çift saat (Vienna/NY), piyasa fazı (PRE-MARKET/OPEN/CLOSED — `market_calendar` mantığı frontend'e util), streak noktaları, avatar.

### D1 — TODAY (giriş ekranı; "günün masası")
**Amaç:** Sabah 60 saniyede: brif + dünün sonucu + günün dersi + sistem sağlığı.
| Bileşen | Uç | Durum |
|---|---|---|
| Daily Double (ders ↔ vaka köprüsü) | snapshot_latest + `concepts.py` günün kavramı (snapshot'a `concept` alanı eklenir — 5 satır iş) | **B** |
| Bugünün tam brifi (üye = tam liste) | `data/distribution/snapshot_latest.json` → yeni uç `GET /distribution/snapshot` (20 satırlık router; dosyayı servis eder, auth'lu tam görünüm) | **B** |
| "Dün ne oldu" sonuç kartı + refleksiyon | `/watchlist/performance?days=5` + snapshot arşivi | **A** |
| Sistem Sağlığı kartı (Audit P1 borcu burada ödenir) | `/closed_loop/status` + scheduler job-run özeti (var olan status ucu; job geçmişi için `tg_delivery_log`+`broadcast_queue` sayımı) | **A/B** |
| Onay hatırlatıcısı (admin'e özel): bekleyen taslak varsa altın bant | `broadcast_queue` (yeni mini uç `GET /distribution/pending`, admin-auth) | **B** |

### D2 — SCANNER ("The Press Room")
**Amaç:** Tam evren taramasını çalıştır, sonucu Grade dilinde incele, watchlist'e ekle.
| Bileşen | Uç | Durum |
|---|---|---|
| Tarama başlat (preset: full-1812 / tech / custom) | `POST /scan` (mevcut; 200'lük batch'ler frontend'te sıralı çağrılır — bugünkü davranış korunur) | **A** |
| ScanProgress aşama şeridi | mevcut timing logları + batch ilerlemesi (frontend sayacı) | **A** |
| Sonuç tablosu — Grade görünümü (varsayılan): TICKER · GRADE · P-BAND · FACTORS · RISK; "Analyst view" toggle'ı ham alanları açar (composite, atr…) — Labs ruhu, tek tıkla | `/scan` cevabı → frontend `gradeOf()` util'i (backend `_grade_of` mantığının TS kopyası — tek kaynak yorumu planın 7. bölümünde) | **A** |
| Satırdan watchlist'e ekle (tier/conviction alanlarıyla) | `POST /watchlist` (mevcut, migration 003 alanları kabul ediyor) | **A** |
| Son shortlist'i yükle (yeniden taramadan) | `GET /scan/shortlist/latest` | **A** |
| Tarama sonrası brif üretimi kısayolu (admin): "bu taramadan taslak üret" | `distribution.jobs.job_draft` tetik ucu `POST /distribution/draft` (admin) | **B** |

### D3 — WATCHLIST ("The Clipboard")
| Bileşen | Uç | Durum |
|---|---|---|
| Aktif liste (Grade rozetli kartlar/tablo) | `GET /watchlist`, `GET /watchlist/today` | **A** |
| Ekle/sil/temizle/arşivle | POST/DELETE `/watchlist*`, `/watchlist/archive` | **A** |
| "Hepsini değerlendir" (sonuçları damgala) | `POST /watchlist/evaluate-all` | **A** |
| Tarih bazlı geçmiş gezinme | `/watchlist/dates`, `/watchlist/history` | **A** |
| Sonuç damgaları (HIT/MISS/OPEN) — outcome stamp bileşeni | evaluate sonuçları | **A** |
| Karar-öncesi mini brif (FinSense füzyonu): ekleme anında hissenin faktör profiline göre 1 satır eğitim + zayıf-mastery uyarısı | terms + (ileride) learning profili | **B/C** — v1: terim linki (B); mastery kişiselleştirme (C, yuva hazır) |

### D4 — THE LEDGER ("kendi karnen + motorun karnesi", tek ekran iki sütun)
| Bileşen | Uç | Durum |
|---|---|---|
| Motor karnesi: grade bazlı isabet + probability tape (iddia bandı içinde/dışında iğne) | `/watchlist/performance` (by_tier/by_conviction) + `/history/stats` | **A** |
| Kalibrasyon eğrisi (motor) | `/closed_loop/calibration`, `/calibration/stats` | **A** |
| Aylık rapor kartları + en kötü hafta sabit kutusu | `/history/signals` + `/history/returns` üzerinden hesap (frontend agregasyon) | **A** |
| Edge Report görüntüleyici (haftalık) | `data/backtest_out`/rapor dosyası → `GET /research/edge-report` (research router'da var mı doğrula; yoksa 15 satır uç) | **B** |
| OKUYUCU karnesi: güven-vs-isabet grafiği (kalibrasyon antrenörü çıktısı) | yeni tablo `learning_answers` (distribution.db) + `POST/GET /classroom/answers` | **C→B** — şema bu planda tanımlı (bölüm 7), uç 30 dk iş |

### D5 — CLASSROOM (FinSense; Şablon-3 omurgası aynen)
| Bileşen | Uç | Durum |
|---|---|---|
| Yollar + modül rafları + mastery ringleri | `GET /academy/status`, `GET /academy/dashboard/{user}` | **A** (academy router canlı; içerik fabrikası Finsense reposundan content-pack ile beslenir) |
| Ders sayfası (Explain/Show/Try) | `GET /academy/lesson/{id}` + arşiv vakası: `/history/ohlcv` (5-gün scrub slider verisi!) | **A** — ohlcv ucu scrub için hazır |
| Onboarding (yol seçimi) | `POST /academy/onboard` | **A** |
| Confidence slider + cevap kaydı | `POST /classroom/answers` (yeni, D4 ile ortak) | **C→B** |
| Blind-Spot Map | terms × learning_answers × snapshot rozet frekansı (frontend hesap) | **C** — yuva: boş durumda "cevap verdikçe haritan oluşur" |
| Sözlük (120+ terim) | `terms.ts` v1 → content-pack v2 | **A** |

### D6 — PAPER DESK ("sanal defter"; canlı işlem YOK)
| Bileşen | Uç | Durum |
|---|---|---|
| Açık/kapalı sanal pozisyonlar + equity eğrisi | `/closed_loop/portfolio`, `/portfolio/open`, `/portfolio/closed` | **A** |
| Bekleyen onaylar (auto-approve kuyruğu) + denetim izi | `/closed_loop/pending` | **A** |
| "Top-3'ü paper-izle" modu anahtarı (Audit 30g maddesi) | mevcut paper altyapısı + scheduler flag | **B** |
| Broker hesabı görünümü | `/trade/account`, `/trade/positions` — **UI'da salt-okunur**, buy/sell butonları YOK (uçlar durur, yüzeye çıkmaz) | **A (salt-okunur)** |

### D7 — SETTINGS + Labs
- Profil/JWT oturum, bildirim tercihi (Telegram bağlama: bot /start derin-linki `t.me/bot?start=<userid>`), dil (EN v1). Uç: `/user`, `/auth/*` — **A**.
- **Labs** (soluk giriş, "experimental" bandı): mevcut drl/ai-lab/autonomy sayfaları OLDUĞU GİBİ buraya taşınır — silinmez, vitrine çıkmaz. **A (mevcut)**.

---

## 5. ENTEGRASYON-HAZIRLIK MATRİSİ (özet)

| Özellik | Bugün | Tasarımda yuva | Açılma koşulu |
|---|---|---|---|
| Brif/snapshot, scanner, watchlist, history, paper, academy çekirdek, auth | ✅ A | — | — |
| /distribution/snapshot + pending + draft uçları | B | D1/D2 | 3 küçük router (≤1 gün) |
| Günün kavramı snapshot alanı | B | Daily Double | 5 satır |
| learning_answers + okuyucu karnesi | C→B | D4/D5 | şema hazır, 0.5 gün |
| Blind-Spot Map kişiselleştirme | C | D5 | learning_answers verisi birikince |
| Premium gating (dashboard'da tam liste) | B | D1 | Stripe canlı + `premium_status` kontrolü (tg_users/waitlist eşleşmesi) |
| Alert kurma (kullanıcıya özel) | C | D3 sağ rayında "Alerts (coming)" yuvası | Telegram derin-link + alert servisi (faz 4 sonrası) |
| Canlı işlem | ✗ bilinçli yok | — | Edge kanıtı (Audit kapısı) — tasarımda yeri bile yok |

---

## 6. ÇAPRAZ KESİTLER

- **Auth akışı:** JWT mevcut (`/auth/login|register|me`). Beta: davet kodu kayıtta zorunlu (`beta_invites` tablosu — hazır). Public→Desk geçişi: landing S8 waitlist → davet e-postası → kayıt.
- **Yükleme/boş/hata:** her panel 3 durumu da tanımlı taşır (bölüm 2 standartları); global skeleton yok, panel bazlı folding-paper shimmer.
- **Telemetri sözlüğü (Plausible):** `desk-login, scan-start, scan-done, wl-add, ledger-view, lesson-start, lesson-done, confidence-answer, paper-view, premium-view` — funnel dokümanının metrikleriyle bire bir.
- **Erişilebilirlik:** Grade renkleri + harf her zaman birlikte (renk körlüğü); tüm mono sayılarda `tabular-nums`; klavye ile modal/margin-note gezinme.
- **Performans:** snapshot ve terms statik; ağır uçlar (scan) kullanıcı tetikli; history sayfalama `limit` paramlarıyla.

## 7. VERİ SÖZLEŞMELERİ — YENİ/DEĞİŞEN

1. **snapshot v2 (geriye uyumlu, +2 alan):** `concept: {slug,name,line}` ve `edge_summary: {week,one_liner}` — üretici: `snapshot_builder` (+15 satır), tüketici: D1, public Ledger.
2. **`GET /api/v1/distribution/snapshot`** (auth): tam snapshot (premium_only dahil; `premium_status` yoksa free görünüm). **`GET /distribution/pending`**, **`POST /distribution/draft`** (admin).
3. **`learning_answers` tablosu (distribution.db):** `id, user_id, lesson_id, question_id, answer, confidence (50-95), correct (bool), ts` + uçlar `POST/GET /classroom/answers`. Okuyucu karnesi = confidence-bucket'lara göre isabet.
4. **Grade eşleme tek kaynak:** `distribution/snapshot_builder._grade_of` referans; TS kopyası `web/src/lib/grade.ts` — üstünde "mirror of snapshot_builder._grade_of; change both" bandı + iki tarafta aynı 6 birim test vakası.

## 8. İNŞA FAZLARI

**FAZ 1 — Tasarım sistemi + Public (1 hafta):** Claude Design çıktısı → token'lar (`globals.css` değişkenleri) + 7 imza bileşen (GradeSeal, MarginNote, DailyDoubleBracket, OutcomeStamp, ProbabilityTape, ConfidenceSlider, ColophonBar) Storybook'suz ama `components/ledger/` altında izole → landing S1-S8 + edition + public ledger. **Kapı:** mevcut demo akışı yeni deriyle çalışıyor, lint temiz, mobil OK.

**FAZ 2 — Desk çekirdeği (1.5 hafta):** D1 + D2 + D3 + D4 (A-etiketli her şey) + 3 küçük distribution ucu + snapshot v2. Eski dashboard sayfaları `/dashboard-legacy/*` altında erişilebilir kalır (güvenlik ağı), navigasyondan çıkar. **Kapı:** tarama→watchlist→değerlendir→karne döngüsü yeni UI'da uçtan uca; timing/hata durumları test edildi.

**FAZ 3 — Classroom + Paper Desk (1 hafta):** D5 (academy uçları + ohlcv scrub + confidence slider + learning_answers) + D6 + okuyucu karnesi D4'e bağlanır. **Kapı:** bir kullanıcı onboard olup ders bitirip cevabının Ledger'a düştüğünü görüyor; paper defteri canlı veriyle doluyor.

**FAZ 4 — Premium + cila (0.5-1 hafta):** premium_status kontrolü + tam-liste gating + Full Edition sayfası canlı; Labs taşıma; telemetri tam; legacy sayfaların emekliliği kararı. **Kapı:** test ödemesi → dashboard'da tam liste açılıyor; GTM 4-hafta karne kapısıyla senkron.

Toplam: **~4-5 hafta**, tamamı mevcut backend üstünde; backend yeni işi ≤3 gün (uçlar + snapshot v2 + tablo).

## 9. CLAUDE DESIGN — DASHBOARD EK BLOĞU
*(Master şablonun kod bloğunun SONUNA eklenerek yapıştırılır; aynı brief'in Part 2'si)*

```
═══════════════ PART 2 — "THE READER'S DESK" (authenticated dashboard) ═══════════════
Extend the same design system into the member dashboard. The metaphor shifts
from reading the paper to sitting at the editor's desk: denser, mono-numbered,
but the same ink-navy paper, serif section heads, grade seals, margin notes,
amber-live/ink-archive color rule, and the colophon disclaimer bar.

LAYOUT: thin left rail (icons + smallcaps labels): Today, Scanner, Watchlist,
Ledger, Classroom, Paper Desk, Settings — plus a dimmed "Labs" entry at the
bottom with an EXPERIMENTAL tag. Top bar: dual clock (Vienna/New York),
market-phase chip (PRE-MARKET amber / OPEN green-tick / CLOSED ink),
reading-streak dots, avatar. Every panel is framed like a newspaper box with
a thin double-rule header: "— WATCHLIST · 12 items · as of 09:14 —".

SCREEN D1 · TODAY: top = the Daily Double (lesson card ↔ live case card,
hand-drawn bracket, amber glow on the live side). Middle = today's FULL brief
(members see all candidates; each item = grade seal, probability sentence,
factor badges with margin-note terms, risk note in editor's-note style).
Bottom row of three: "Yesterday — what happened" outcome card with a serif
reflection question + confidence slider (50–95%); a compact System Health box
(last scan time, calibration check, next publish 08:30 — engraved instrument
labels); mini Ledger.
SCREEN D2 · SCANNER ("The Press Room"): preset chips (Full universe 1,812 /
Tech / Custom), a big gold "Run the morning sweep" button, and the honest
long-task component: stage tape "Sweep → Enrich → Grade → Done" with a mono
elapsed counter and per-stage ticks (this can take minutes — design for it,
no fake spinners). Results as a dense mono table: TICKER · GRADE (seal) ·
P-BAND · FACTORS (badges) · RISK, with an "Analyst view" toggle that reveals
raw columns in a muted drawer. Row action: "clip to watchlist" (scissors
icon, newspaper clipping metaphor — the row briefly lifts like a cut paper
strip).
SCREEN D3 · WATCHLIST ("The Clipboard"): clipped-article cards (slightly
rotated 1°, pin visual) each with grade seal, added-date, current outcome
stamp if evaluated; toolbar: evaluate-all, archive, date-browser (a small
calendar strip of past dates). Adding from anywhere shows a one-line teaching
note ("You're clipping a high-ATR candidate — wide daily ranges cut both
ways" with a margin-note link).
SCREEN D4 · THE LEDGER: two columns under one serif headline "Two ledgers,
one standard." LEFT = the engine: per-grade probability tapes (claimed band
shaded, actual needle on/off it), monthly report cards, pinned worst-week
correction notice. RIGHT = the reader: their confidence-vs-accuracy chart
drawn with the SAME tape component, built from lesson answers; empty state:
"Answer questions in the Classroom and your ledger draws itself."
SCREEN D5 · CLASSROOM: identical to the public Classroom spec (two shelves,
metro-map line, lesson page with Explain/Show/Try, 5-day scrub slider on a
real dated chart, confidence slider, blind-spot constellation) — now with
the member's mastery rings live everywhere.
SCREEN D6 · PAPER DESK: virtual positions as ledger-book rows (open in
amber, closed stamped sage/brick), an equity line drawn like a fever chart
in a newspaper, and a "pending approvals" tray with an audit-trail drawer.
A locked, greyed "Live trading" slot exists ONLY as a note: "Unlocks when
the public record earns it." No buy/sell controls anywhere.
SCREEN D7 · SETTINGS: quiet form page (serif labels, mono values): profile,
Telegram link button ("connect the morning delivery"), invite codes, plan
status (Free / Full Edition with founding badge).
STATES: every panel designs its loading (folding-paper shimmer), empty
(one-sentence teacher voice) and error (single brick line + retry + mono
code) states. Market closed: Today swaps the case card for a lesson
suggestion. Long scan: stage tape persists across navigation as a slim
top progress ribbon.
```

## 10. AÇIK KARARLAR / RİSKLER

| Konu | Karar önerisi |
|---|---|
| Eski 15+ dashboard sayfası | Silme yok: `/dashboard-legacy` + Labs; 60 gün kullanılmayanlar Faz 4'te emekli |
| research/edge-report ucu var mı | Faz 2 başında doğrula; yoksa 15 satırlık uç yaz |
| Premium durumunun dashboard'a bağlanması | v1: waitlist e-postası ↔ Stripe müşteri eşleşmesi (webhook zaten kaydediyor); tam üyelik sistemi Faz 4 |
| Tarama süresi UX'i | 200'lük batch ilerlemesi frontend'te sayılır; 10 dk üstü → "arka planda sürüyor" bandı + bitince Today'e rozet |
| Content-pack (Finsense fabrikası) gecikirse | Classroom v1 statik 12 ders + terms ile açılır (A); pack geldiğinde şema zaten uyumlu |

---
*Bu plan; Master Tasarım (görsel dil), Tam Sistem Audit (tek-Grade ve dürüstlük kararları), GTM/Demo/Telegram spec'leri (dağıtım) ve FinSense tasarımının (Classroom omurgası) tek uygulama çatısıdır. Onayınla Faz 1'den başlarım.*
