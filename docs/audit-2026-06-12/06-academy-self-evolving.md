# Bölüm H — Finance Academy Self-Evolving Sistemi

**Tasarım ilkesi:** Sıfırdan tasarım DEĞİL — `academy/` modülünde 6 agent + orchestrator + 12 domain + repository katmanı zaten yazılmış. Bu bölüm: mevcut kodu kanonikleştirir, 8 agent'a tamamlar, ürüne bağlar ve döngüyü gerçek veriyle kapatır.

## H.0 — MEVCUT DURUM ↔ HEDEF EŞLEMESİ

| Master prompt istegi | Kodda karşılığı | Boşluk |
|---|---|---|
| 12 domain | `academy/domains.py` (223 LOC, 12 domain tanımlı) ✅ | — |
| 4 seviyeli hiyerarşi | `models.py` Lesson/Module şeması | Mikro-içerik (cheat sheet, case study, "biliyor muydun") kısmen |
| Agent 1 Content Generator | `agents/content_generator.py` (325) ✅ | Canlı piyasa örneği beslemesi (scanner'dan) yok |
| Agent 2 Quality Guard | `agents/quality_guard.py` (229) ✅ | Golden-set + finansal doğruluk testi yok; 2 saat SLA izlenmiyor |
| Agent 3 Personalization | `agents/personalization.py` (313) ✅ | Platform davranış sinyali (watchlist/scan) bağlı değil |
| Agent 4 Gap Detector | `agents/gap_detector.py` (202) ✅ | Arama logu kaynağı yok (üründe arama yok) |
| Agent 5 Trend Scout | **YOK** | Yazılacak — social_intelligence_agent.py (agents/) yeniden kullanılabilir |
| Agent 6 Content Updater | `agents/content_updater.py` (157) ✅ | 90-gün denetim cron'u core scheduler'a bağlı değil |
| Agent 7 Analytics | `agents/analytics.py` (244) ✅ | Ölçecek kullanıcı yok; KPI omurgasına (kpi_tracker) bağlı değil |
| Agent 8 (öneri: Examiner/Simulator) | **YOK** | Quiz üretimi generator içinde; sınav/simülasyon ayrı agent olmalı |
| Orchestrator | `orchestrator.py` (283; günlük/haftalık/90g akış tanımlı) ✅ | core/scheduler'a kayıtlı değil — hiç çalışmıyor |
| DB | academy.db (4KB boş) + academy_v2.db | Tekille, seed'i çalıştır, migrate alembic'e bağla |

## H.1 — İÇERİK MİMARİSİ (onaylanan hiyerarşi)

SEVİYE 1: 12 domain (domains.py'dekiyle birebir — master prompt listesiyle uyumlu).
SEVİYE 2-3: Her domain 3-10 modül, her modül 3-15 ders; ders şeması models.py Lesson alanlarına ek olarak şunları kazanmalı: `misconceptions[]`, `real_traders_do`, `real_example{ticker, as_of, context}` (scanner'dan otomatik), `difficulty`, `estimated_minutes`, `related_lessons[]`.
SEVİYE 4 mikro-içerik öncelik sırası: (1) quiz, (2) flashcard, (3) glossary — ilk 30 gün; (4) mini-simülasyon (drl/backtest_engine'i sandbox olarak kullan), (5) case study (signals_archive'den gerçek sinyal vakaları), (6) cheat sheet, (7) "biliyor muydun", (8) hata analizi — 90 gün.

**FinPilot'a özgü süper güç:** Gerçek hayat örnekleri statik yazılmaz — Content Generator, scanner'ın güncel taramasından ve signals_archive'deki gerçek (anonim) sinyal sonuçlarından örnek çeker. "MACD dersi"ndeki grafik, bu haftanın gerçek AAPL verisi olur. Hiçbir kurs platformu bunu yapamıyor.

## H.2 — 8 AGENT EKOSİSTEMİ (nihai)

**A1 Content Generator** (var, geliştirilecek): Tetik: Pzt haftalık cron + Gap/Trend sinyali. Yeni girdi: scanner güncel verisi + signals_archive vakaları. Çıktı JSON'u master prompt şemasıyla uyumlu (lesson_id, difficulty, key_takeaways, misconceptions, quiz_questions, flashcards, related_lessons, real_example, version).
**A2 Quality Guard** (var, sertleştirilecek): 8 kontrol boyutu + YENİ: golden-set regresyonu (50 el-denetimli ders referans), sayısal iddia doğrulaması (orandan tarihe), disclaimer zorunluluğu (P8). SLA: 2 saat — job-run tablosunda izlenir. Karar: APPROVED / REVISION_NEEDED(liste) / REJECTED(gerekçe).
**A3 Personalization** (var, bağlanacak): Sinyaller: tamamlanan dersler, quiz hataları, oturum süreleri + YENİ: watchlist sembolleri, bakılan sinyal türleri ("opsiyon sinyaline bakıyorsun ama Domain 8'de 0'sın" uyarısı — master prompt'taki 'ticaret yapıyorsun ama öğrenmedin' kartı). Çıktı: kişisel yol + günlük "bugün bunu öğren" kartı (dashboard ana ekranına).
**A4 Gap Detector** (var, kaynak eklenecek): Mevcut kaynaklar: quiz hata oranları, job logları. Eklenecek: ürün-içi arama (arama özelliğiyle birlikte), Telegram'da sorulan sorular. Çıktı: P0-P3 öncelikli gap → Content Generator job kuyruğu. Sıklık: günlük.
**A5 Trend Scout** (YENİ — 1 hafta iş): `agents/social_intelligence_agent.py` (268 LOC, Polymarket/HN/DDG zaten bağlı) academy bağlamına uyarlanır; haftalık 5 trend konu + domain eşlemesi + aciliyet puanı. Fed/earnings takvimi research pipeline'dan gelir.
**A6 Content Updater** (var, cron'a bağlanacak): 90 günde bir içerik denetimi + büyük piyasa olayı tetiklemesi (Trend Scout'tan event sinyali). Eski tarih/deprecated gösterge/kırık referans kontrolü.
**A7 Analytics** (var, KPI'ya bağlanacak): Metrikler core/kpi_tracker omurgasına yazılır: tamamlama, oturum, quiz başarı, retention, streak ve **köprü metriği: "ders sonrası ilgili aracı kullandı mı"** (P9'un istediği davranış kanıtı). Haftalık rapor weekly_report'a bölüm olarak girer.
**A8 Examiner/Simulator** (YENİ — 2-3 hafta): Seviye atlama sınavları + mini-simülasyonlar: kullanıcıya signals_archive'den GERÇEK tarihsel senaryo verilir ("gün T'desin, bu veriyle gir/girme?"), karar T+5 gerçek sonuçla karşılaştırılır. drl/backtest_engine altyapısı sandbox motoru olur. Bu, DRL yatırımını gelire bağlayan en kısa köprüdür.

**Orchestration:** academy/scheduler.py SİLİNİR; orchestrator'ın günlük (Gap→Generator), haftalık (Analytics→Updater, Trend Scout, Generator cron), 90-günlük (Updater review) döngüleri core/scheduler.py'a 3 job olarak kaydedilir (timeout watchdog'u bedavaya gelir). Her içerik durumu ContentJobRepository'de; job-run tablosu dashboard Sistem Sağlığı kartında.

## H.3 — ÜRÜN ENTEGRASYONU (kritik eksik katman)

1. `api/routers/academy.py`: GET domains/lessons/lesson/{id}, POST progress, quiz-answer, GET daily-card, GET dashboard. (~2-3 gün)
2. `web/src/app/dashboard/academy/`: domain haritası, ders görünümü, quiz, streak. Günlük kart ana dashboard'a widget. (~1 hafta)
3. Auth bağlantısı: mevcut JWT kullanıcısı = academy user_id (FinanceAcademy'deki ayrı onboard akışı atılır).
4. Telegram köprüsü: günlük kart, isteğe bağlı Telegram mesajı olarak da gider (mevcut bot'tan) — sıfır maliyetli retention kanalı.

## H.4 — UYGULAMA SIRASI

Hafta 1: FinanceAcademy→archive; academy.db tekille + seed; orchestrator'ı core scheduler'a bağla; ilk 20 dersi üret, elle denetle (golden-set başlangıcı).
Hafta 2-3: Router + dashboard sayfası + günlük kart; Quality Guard golden-set otomasyonu; Analytics→kpi_tracker.
Hafta 4-6: Trend Scout (A5); Personalization'a watchlist sinyali; Telegram günlük kart.
Hafta 7-12: Examiner/Simulator (A8); spaced repetition; 12 domain × ilk modüller dolu (≥150 ders); "ders→davranış" metriği canlı.

**Başarı kriterleri:** 30. gün: 1 gerçek kullanıcı (Meriç) günlük kartla 7-gün streak. 60. gün: 10 dış beta kullanıcısı, ders tamamlama >%40. 90. gün: 150+ yayınlanmış ders (hepsi Quality Guard'dan geçmiş), haftalık otonom üretim insan müdahalesiz, "ders sonrası araç kullanımı" metriği raporda.
