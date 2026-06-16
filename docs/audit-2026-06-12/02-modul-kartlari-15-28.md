# Bölüm C — Modül Analiz Kartları (15–28)

---

## MODÜL 15: web/ — Next.js frontend

**Amaç:** Gerçek ürün arayüzü — dashboard 15+ sayfa (advisory, agent, ai-lab, analysis, autonomy, backtest, calibration, drl, finsense, scan, watchlist/Sinyal Takip...).
**Konum:** `/web/` (Next.js 16, src/: app + components + hooks + lib + __tests__)
**Veri akışı:** Girdi: `/api/v1/*` (REST). Çıktı: kullanıcı arayüzü; `py-api` proxy katmanı.
**Mevcut durum:** [x] Tam çalışıyor — en aktif geliştirilen yüzeylerden (Sinyal Takip lazy-load, arşiv normalizasyonu, paralel batch fetch hepsi Haziran).
**Sorunlar:**
- Sorun: Dashboard 15+ sayfa ama hedef persona belirsiz — "trader terminali" mi "yatırımcı asistanı" mı karar verilmemiş → Neden: her yeni özellik sayfa olarak eklenmiş → Sonuç: yeni kullanıcı ilk değer anına (aha moment) ulaşamıyor; P1/P12 perspektifleri için kritik zayıflık → Çözüm: 3 sayfalık çekirdek akış tanımla (Bugün → Sinyaller → Takip), kalanını "Pro" menüsüne kaldır → **P1**
- Sorun: E2E test yok (`__tests__` birim seviyesi) → dashboard regresyonları manuel yakalanıyor (son haftalardaki fix zinciri kanıt) → Çözüm: Playwright 5 kritik akış → P1
- Sorun: `web/` repo içinde 33.6K dosya (node_modules + out + dev.log commit edilmemiş olmalı — .gitignore doğrula) → P2
- Sorun: Mobil deneyim doğrulanmamış (P1 perspektifinin ilk sorusu) → P1
**Belge durumu:** web/README.md var; sayfa envanteri/akış diyagramı yok.
**Academy bağlantısı:** Academy UI'sı buraya sayfa olarak eklenmeli (`/dashboard/academy`) — FinanceAcademy/app.py'deki ayrı yüzey ölü yatırım.
**Stratejik değer:** Satılabilir tek görünür varlık. Demo videosunun hammaddesi; ilk gelir senaryolarının hepsi bu yüzeyden geçiyor.

---

## MODÜL 16: academy/ + FinanceAcademy/ — eğitim modülü (ÖZEL DETAY)

**Amaç:** Self-evolving finansal eğitim: 12 domain, ders/quiz/flashcard üretimi, kişiselleştirme.
**Konum:** İKİ kopya: `/academy/` (13 dosya, 3.194 LOC) ve `/FinanceAcademy/` (20 dosya, 1.937 LOC)
**Alt bileşenler (academy/):** `models.py` (619 — Lesson/Job/User repository'leri, init_db), `seed_content.py` (491), `orchestrator.py` (283 — günlük/haftalık/90g döngü tanımlı), `domains.py` (223 — 12 domain), `scheduler.py` (89), `agents/`: content_generator (325), personalization (313), analytics (244), quality_guard (229), gap_detector (202), content_updater (157). **Trend Scout YOK** (master prompt 8 agent istiyor; README "8 agent" diyor; kodda 6 + orchestrator var).
**Veri akışı:** Girdi: domain tanımları, kullanıcı aktivitesi (teoride), LLM (Groq/Gemini). Çıktı: academy.db'ye ders/quiz/flashcard. **Gerçekte: DB'ler 4KB — döngü hiç dolu çalışmamış.**
**Mevcut durum:** [x] Bağlı değil — kod var, ürün entegrasyonu yok, kullanıcı 0.
**Sorunlar:**
- Sorun: **Tam duplikasyon** — academy/ ve FinanceAcademy/ aynı sistemin iki evrimi (models.py'ler farklılaşmış) → Neden: FinanceAcademy standalone prototip olarak başlamış, academy/ repo'ya entegre versiyon olarak yeniden yazılmış, eskisi silinmemiş → Sonuç: hangi DB, hangi şema, hangi seed otoriter belli değil; iki tarafa yapılan değişiklikler kaybolacak → Çözüm: `academy/` kanonik ilan et, FinanceAcademy/'yi `archive/`'a taşı, README'yi taşı → **P0 (bu hafta, 1 saat)**
- Sorun: API router + web sayfası yok → kullanıcının Academy'ye ulaşma yolu yok → P1
- Sorun: Quality Guard LLM-bağımlı kalite kontrolü henüz finansal doğruluk golden-set'iyle test edilmemiş → yanlış finansal bilgi yayını riski (P8 regülatör perspektifi) → P1
- Sorun: Personalization'ın beslendiği "platform davranışı" sinyali bağlı değil (watchlist/scan verisi akmıyor) → P2
**Belge durumu:** FinanceAcademy/README.md güncel görünüyor ama yanlış klasörü ve "8 agent"ı anlatıyor → güncelle.
**İyileştirme:** Hafta: duplikasyonu çöz + seed'i çalıştır + DB'yi doldur. Ay: router + 1 dashboard sayfası + Trend Scout & Sınav/Simülasyon agent'ları (8'e tamamla). 90 gün: kişiselleştirme döngüsünü canlı veriyle kapat (tam tasarım: `07-academy-self-evolving.md`).
**Stratejik değer:** Regülasyon-hafif, içerik-temelli, edge-kanıtı GEREKTİRMEYEN tek gelir yolu. "Sinyal edge'i kanıtlanana kadar Academy önde" stratejisinin (G.1 yol 04) taşıyıcısı.

---

## MODÜL 17: tests/

**Amaç:** Pytest altyapısı — 511 test toplanıyor; 494 pass / 4 bilinen fail / 10 skip.
**Konum:** `/tests/` (67 dosya) + `tests/eval/`, `tests/scanner_rollout/`
**Mevcut durum:** [x] Çalışıyor; markers (unit/integration/slow) + xdist kurulu.
**Sorunlar:**
- Sorun: 4 bilinen fail 3 haftadır baseline'da — biri **auth güvenlik regresyonu** → P0 (bkz. Modül 04)
- Sorun: `test_signals.py` ve `scanner_rollout/` kalıcı ignore'da → en kritik iş mantığı (sinyal kontratı) testsiz → P1
- Sorun: Coverage ölçümü 05-23'ten beri çalıştırılmamış; oran bilinmiyor → CI'da coverage gate yok → P2
- Sorun: Academy'nin testi YOK (yeni modül, 0 test) → P1
**Stratejik değer:** "494 yeşil test" due diligence cümlesi; ama iki ignore + 4 fail dipnotu temizlenmeli.

---

## MODÜL 18: eval (tests/eval/ + scanner/evaluate.py + scripts/component_*)

**Amaç:** Sinyal/skor değerlendirme: ablation, korelasyon, walk-forward MC.
**Mevcut durum:** [x] Kısmen — script'ler çalışıyor (component_ablation.json, component_correlation.json üretilmiş), ama düzenli değerlendirme ritmi yok.
**Sorunlar:**
- Sorun: Ablation "score & R/R harmful" buldu ama skor formülü henüz buna göre değişmedi → ölçüm-aksiyon döngüsü kopuk → **P0 (stratejik, Modül 05 ile aynı kök)**
- Sorun: Eval çıktıları data/'ya dağılmış, tek "edge durumu" sayfası yok → Çözüm: haftalık otomatik "Edge Report" (scheduler job) → P1
**Stratejik değer:** Edge kanıtı üretildiği gün ürünün değeri katlanır; üretilemezse pivot kararının (G bölümü) verisi olur. Her iki durumda da en yüksek getirili yatırım.

---

## MODÜL 19: logs/

**Amaç:** Çalışma logları: api, web, auto_scan_trade, auto_trade/, startup logları, PID'ler.
**Mevcut durum:** [x] Çalışıyor.
**Sorunlar:**
- Sorun: Log rotasyonu görünmüyor (api.log büyüme sınırı?) → logrotate veya RotatingFileHandler doğrula → P2
- Sorun: Yapılandırılmış log (JSON) var mı belirsiz; core/logging.py 591 LOC ama log tüketim aracı (grep dışında) yok → P3
**Stratejik değer:** Operasyonel.

---

## MODÜL 20: monitoring/

**Amaç:** Prometheus + Grafana + alerts.yml tanımları.
**Mevcut durum:** [x] Bağlı değil (dev akışında çalışmıyor; compose'ta tanımlı, en son 05-23).
**Sorunlar:**
- Sorun: Alert'ler hiç ateşlenmemiş ortamda yaşıyor → "izleme var" yanılsaması → Çözüm: ya dev'de hafif çalıştır (compose profile) ya da "prod'a kadar dormant" diye belgele → P2
- Sorun: Grafana paneli (profitcore metrics, ab11d54) eklenmişti — kullanılmıyorsa emek kaybı → P3
**Stratejik değer:** B2B/uptime taahhüdü gerektiren vizyonlarda ön şart; bugün için düşük öncelik.

---

## MODÜL 21: docs/

**Amaç:** 45 MD — roadmap'ler, DRL analizleri, rehberler, hibe dokümanları, audit raporları.
**Mevcut durum:** [x] Kısmen — FULL_AUDIT_REPORT (05-23) ve feature_flags.md güncel; ~15 dosya Ocak-Mart'tan kalma ve fiilen geçersiz (ROADMAP_Q1_2025, CRITICAL_ROADMAP, INTEGRATION_PLAN, eski DRL roadmap'leri...).
**Sorunlar:**
- Sorun: Çelişen roadmap'ler (en az 5 roadmap dosyası) → yeni okuyucu hangisinin geçerli olduğunu bilemez → Çözüm: tek `ROADMAP.md` + eskileri `archive/docs_legacy/` → P1
- Sorun: DEPENDENCIES.md ×2 (root + docs) → P2
- Sorun: mkdocs `site/` build'i git'te → `.gitignore`'a ekle, sil → P2
**Belge tablosu (özet — tam tablo `03-yatay-sorunlar.md` D.7'de).**
**Stratejik değer:** Hibe başvurusu yeniden canlandırılırsa docs/ kalitesi doğrudan puan.

---

## MODÜL 22: scripts/

**Amaç:** 29 aktif yardımcı: paper trading (daily/weekly), backtest, raporlar, admin, smoke.
**Mevcut durum:** [x] Çalışıyor — Mayıs'taki 34 ölü script arşivlendi, kalanlar makul.
**Sorunlar:**
- Sorun: `_analyze_shortlist.py`, `_check_db.py` gibi alt-tireli geçici script'ler root/scripts'te birikmeye başlıyor (yenisi 06-09) → aylık süpürme kuralı → P3
- Sorun: Script'lerin hangileri scheduler'dan, hangileri elle çağrılıyor haritası yok → P2
**Stratejik değer:** daily_paper_trading + weekly_report = track record üretim hattı; vizyon 1-2'nin (sinyal servisi) kanıt makinesi.

---

## MODÜL 23: reports/

**Amaç:** Sprint gap raporları (8-16), audit_2026.md, backtest çıktıları.
**Mevcut durum:** [x] Tarihsel arşiv — aktif yazım 05-23'te durmuş.
**Sorunlar:** reports/ vs data/ rapor karmaşası (D.1); audit raporlarının otoriter zinciri belirsiz → Çözüm: `reports/INDEX.md` + tek adlandırma şeması → P2
**Stratejik değer:** Sprint disiplini kanıtı (P6 accelerator perspektifi olumlu okur).

---

## MODÜL 24: notebooks / research/

**Amaç:** `research/` (6 dosya) — research pipeline (scheduler'da job'u var); ipynb pratiği yok.
**Mevcut durum:** [x] Kısmen — pipeline job tanımlı, çıktısının nerede tüketildiği belirsiz.
**Sorunlar:** Research çıktısı → agent'lara mı, rapora mı akıyor? İzlenebilirlik yok → P2
**Stratejik değer:** Düşük; headroom enrichment ile birleşirse içerik motoruna (newsletter vizyonu) dönüşebilir.

---

## MODÜL 25: archive/ / legacy

**Amaç:** Bilinçli mezarlık: core_legacy, docs_legacy, scanner_stubs, scripts_legacy, public_website_for_extraction.
**Mevcut durum:** [x] Legacy — doğru kullanılıyor (Mayıs temizliğinin ürünü).
**Sorunlar:** public_website "for_extraction" etiketi — çıkarılacak içerik 3 haftadır bekliyor; landing ihtiyacı doğarsa burası hammadde → P3. FinanceAcademy/ buraya taşınmalı (Modül 16).
**Stratejik değer:** Yok (hijyen göstergesi).

---

## MODÜL 26: landing / marketing (site/ + archive/public_website)

**Amaç:** mkdocs çıktısı (site/) + arşivlenmiş eski statik tanıtım sitesi.
**Mevcut durum:** [x] Bağlı değil — **canlı landing page YOK.**
**Sorunlar:**
- Sorun: Hiçbir gelir senaryosu (G.2) landing'siz çalışmaz; waitlist toplayacak yer yok → Çözüm: 1 günlük tek-sayfa landing (web/ içinde route veya Vercel'de ayrı) + e-posta toplama → **P1 (gelir öncesi ilk adım)**
**Stratejik değer:** En düşük maliyetli, en yüksek kaldıraçlı eksik parça.

---

## MODÜL 27: infra (Dockerfile'lar, .devcontainer, .streamlit, .vscode)

**Amaç:** Konteyner + geliştirme ortamı tanımları.
**Mevcut durum:** [x] Çalışıyor; Dockerfile hardening (9aaf80d) yakın tarihli, headroom runner stage eklendi.
**Sorunlar:** `.streamlit/` kalıntı (Streamlit silindi) → sil → P3. `.venv` + `.venv-contract` iki sanal ortam — contract testleri için ayrı venv belgelenmemiş → P3.
**Stratejik değer:** Deploy edilebilirlik.

---

## MODÜL 28: CI/CD (.github/workflows/ci.yml)

**Amaç:** Tek CI workflow.
**Mevcut durum:** [x] Kısmen — dosya 03-10'dan beri değişmemiş; bu sürede pytest markers, xdist, yeni modüller (academy) eklendi.
**Sorunlar:**
- Sorun: CI, Mart'taki repo'ya göre yazılmış → academy testleri (yok zaten), compose smoke, coverage gate kapsam dışı → Çözüm: ci.yml'i güncel Makefile hedefleriyle hizala; haftalık scheduled compose-smoke job ekle → P1
- Sorun: README'deki CI badge "yourusername" placeholder → repo gerçekten GitHub'da mı, CI çalışıyor mu doğrula → P2
**Stratejik değer:** Açık kaynak vizyonu (G.1 yol 09) seçilirse CI vitrine çıkar.

---

## MODÜL DURUM ÖZETİ

| Durum | Modüller |
|---|---|
| Tam çalışıyor | start/fp, .env, api, scanner, agents, llm, core, scheduler, cache, migrations, web, tests, scripts, infra |
| Kısmen / izlenmeli | compose, score (edge yok), drl (stale models), kpi, data (kirli), eval (ritim yok), docs (bayat), CI (eski) |
| Bağlı değil | **academy (ürün entegrasyonu yok)**, monitoring, landing (yok) |
| Redundant / karar gerekli | **FinanceAcademy/ (duplicate)**, site/, .streamlit, score_engine shim |
