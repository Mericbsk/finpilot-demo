# Bölüm C — Modül Analiz Kartları (01–14)

Format: her kart tam şablonu izler; kanıt = dosya içeriği, git log, LOC sayımı, 2026-05-23 audit'i.

---

## MODÜL 01: start.sh / Makefile / fp / launch scripts

**Amaç:** Tek resmi dev giriş noktası (start.sh), yönetim CLI (fp), build/test/docker hedefleri (Makefile).
**Konum:** `/` (root)
**Alt bileşenler:** `start.sh` → port temizliği, .next izin fix, API+Web başlatma, PID yönetimi, watchdog. `stop.sh` → temiz kapatma. `fp` → start/stop/status/log + docker compose sarmalayıcı + Sentry uyarısı. `Makefile` → 30+ hedef (test, lint, security, docker, scanner). `finpilot.bat`/`stop.bat` → Windows eşleniği.
**Veri akışı:** Girdi: yok. Çıktı: çalışan API (8000) + Web (3001) süreçleri, `logs/*.pid`, `logs/api.log`, `logs/web.log`.
**Bağımlılıklar:** uvicorn, next dev, curl, fuser. Kendisini çağıran: insan + finpilot.bat.
**Mevcut durum:** [x] Tam çalışıyor
**Sorunlar:**
- Sorun: `pkill -9` ile agresif süreç öldürme → Neden: PID dosyaları güvenilmez bulunmuş → Sonuç: aynı makinedeki başka uvicorn/next süreçleri de ölür → Çözüm: PID-dosyası + port doğrulamalı kademeli kill → Öncelik: P2
- Sorun: `sudo chown` start script içinde → Neden: .next izin sorunu workaround'u → Sonuç: parolasız sudo yoksa start kırılır, taşınabilirlik düşer → Çözüm: kök nedeni (docker volume izni) çöz → P2
- Sorun: finpilot.bat 2 aydır güncellenmemiş, start.sh ile drift riski → Çözüm: bat'ı `wsl bash start.sh` sarmalayıcısına indir → P3
**Performans:** start ~15-30sn (next dev cold). Kabul edilebilir.
**Kod kalitesi:** Shell iyi yorumlanmış, Türkçe açıklamalı. Test yok (shell için normal).
**Belge durumu:** README "Runtime Contract" bölümü doğru ve güncel. ✅
**İyileştirme:** Bu hafta: bat senkronu. Bu ay: kademeli kill. 90 gün: tek `fp` altında start/stop/make birleşimi.
**Academy bağlantısı:** Academy scheduler'ı start.sh'a eklenirse otomatik içerik döngüsü dev ortamında da yaşar.
**Stratejik değer:** Yatırımcıya "tek komutla ayağa kalkan sistem" demosu — due diligence'ta olgunluk sinyali.

---

## MODÜL 02: docker-compose.yml

**Amaç:** Prod-benzeri stack: web, api, finpilot, scanner, telegram_bot, redis, postgres, prometheus, grafana.
**Konum:** `/docker-compose.yml` (tek dosya — Mayıs'taki çoklu-compose sorunu çözülmüş ✅)
**Veri akışı:** .env → servis env'leri; volumes: finpilot_logs, redis_data, postgres_data, prometheus_data, grafana_data.
**Mevcut durum:** [x] Kısmen çalışıyor — tanım güncel (06-11) ama günlük geliştirme start.sh ile; compose stack düzenli ayağa kaldırılmıyor.
**Sorunlar:**
- Sorun: `finpilot` ve `api` ayrı servisler — rol ayrımı belirsiz → Neden: legacy Streamlit döneminden kalan servis adı → Sonuç: yeni geliştirici hangi servisin ürün olduğunu çözemez → Çözüm: `finpilot` servisini kaldır veya yeniden adlandır → P1
- Sorun: prometheus+grafana tanımlı ama dev'de hiç çalışmıyor → Sonuç: monitoring "kağıt üstünde var" → Çözüm: ya compose profile'a al (`--profile observability`) ya da kaldır → P2
- Sorun: compose stack'in uçtan uca çalıştığına dair düzenli smoke kanıtı yok (`scripts/docker_smoke.sh` var ama cron'da değil) → Çözüm: CI'da haftalık compose smoke job → P1
**Belge durumu:** README quick start docker bölümü var; Makefile `docker-up-legacy` hedefleri kafa karıştırıcı (legacy compose silinmiş) → temizle.
**Academy bağlantısı:** Academy ayrı servis olarak compose'a eklenmeli (cron'lu worker).
**Stratejik değer:** B2B/API satışı senaryosunda deploy edilebilirlik kanıtı; hibe başvurularında "production-ready altyapı" maddesi.

---

## MODÜL 03: .env ve env dosyaları

**Amaç:** Sır ve yapılandırma yönetimi.
**Alt bileşenler:** `.env` (13 anahtar: FINPILOT_SECRET_KEY, GROQ, GOOGLE, TELEGRAM×2, POLYGON, NEWS, ALPACA×3, MLFLOW, REDIS×2), `.env.example` (şablon, daha kapsamlı).
**Mevcut durum:** [x] Tam çalışıyor
**Sorunlar:**
- Sorun: `.env.example` (1.660B) ≠ `.env` (826B) — örnek dosyada olup gerçekte olmayan anahtarlar var (SENTRY_DSN dahil; fp CLI bunu uyarıyor) → Sonuç: hangi anahtarların gerçekten zorunlu olduğu belirsiz → Çözüm: README'ye "zorunlu / opsiyonel anahtar" tablosu → P2
- Sorun: Sır rotasyon politikası yok; `.secrets.baseline` var (iyi) ama anahtar yaşı izlenmiyor → P3
**Belge durumu:** feature_flags.md (05-23) env flag'lerini belgeliyor — iyi durumda.
**Stratejik değer:** Güvenlik hijyeni (pre-commit + secrets baseline + trivyignore) due diligence'ta artı puan.

---

## MODÜL 04: api/ — FastAPI backend

**Amaç:** Tüm ürün yüzeyinin tek backend'i; 21 router `/api/v1` altında.
**Konum:** `/api/` (31 dosya, ~6.040 LOC)
**Alt bileşenler (başlıca):** `main.py` (389) → app, middleware, health/ready/metrics; `routers/watchlist.py` (1.019 — en büyük router), `agent.py` (751), `scan.py` (518), `llm.py` (318), `history.py` (308), `closed_loop.py` (300), `advisory.py` (270), `inference.py` (224), `ai_explain.py` (213), `market_data.py`, `prices.py`, `auth.py`, `trade.py`, `backtest.py`, `user.py`, `analytics.py`, `models.py`, `ensemble.py`, `optuna.py`, `research.py`, `profitcore.py`; `services/watchlist_db.py` (204).
**Veri akışı:** Girdi: web/ HTTP istekleri, scheduler iç çağrıları. Çıktı: JSON; SQLite/Postgres yazımları; Telegram tetikleri. Bağlı: scanner, core, agents, llm, drl, auth.
**Mevcut durum:** [x] Tam çalışıyor (06-12'de aktif geliştirme; watchlist 500 fix, chart clamp fix yakın tarihli)
**Sorunlar:**
- Sorun: `watchlist.py` 1.019 LOC tek router → Neden: Sinyal Takip sekmesinin tüm iş mantığı router'a gömülmüş → Sonuç: test edilemez, regresyon üretiyor (son 3 haftada 3 watchlist fix commit'i) → Çözüm: service katmanına böl (`services/` zaten başlatılmış) → **P1**
- Sorun: Auth regresyonu — `test_compute_surface_requires_auth` 200≠401 bilinen fail → Neden: korumalı endpoint'lerden `require_auth` kaldırılmış → Sonuç: scan endpoint'i kimliksiz erişime açık → Çözüm: S1-6 görevi uygulanmalı → **P0 (canlıya çıkmadan)**
- Sorun: 21 router'ın önemli kısmı hâlâ sadece happy-path smoke testli → P1
- Sorun: Academy için router YOK → Academy ürün dışında yaşıyor → Çözüm: `routers/academy.py` → P1 (Bölüm H planının ilk adımı)
**Performans:** Scanner çağrıları artık chunked concurrency ile (b5561d9) — son darboğaz fix'leri taze. `/chart` yfinance limit clamp'i eklendi.
**Kod kalitesi:** Orta-iyi; router'lar arası tutarlılık var, ama iş mantığı/router ayrımı zayıf.
**Belge durumu:** OpenAPI otomatik; ayrıca el yazımı API belgesi yok (B2B API vizyonu için gerekecek).
**İyileştirme:** Hafta: auth fix. Ay: watchlist servisleştirme + academy router. 90 gün: API anahtar yönetimi + rate limit (B2B hazırlığı).
**Academy bağlantısı:** Router eklenmesi Academy'yi üründe görünür yapar — aktivasyon hunisinin ön şartı.
**Stratejik değer:** 21 router'lık olgun yüzey, B2B API vizyonunun (G bölümü, Vizyon 5) doğrudan hammaddesi.

---

## MODÜL 05: scanner/ — hisse tarama motoru

**Amaç:** Sembol evreninde çok-zaman-dilimli teknik tarama, sinyal üretimi, skor.
**Konum:** `/scanner/` (11 dosya, 2.832 LOC)
**Alt bileşenler:** `data_fetcher.py` (953) → yfinance + Alpaca bulk bars (yeni, aiolimiter'lı); `signals.py` (511) → sinyal kuralları + `signal_score_row`; `evaluate.py` (402) → değerlendirme döngüsü (artık paralel); `config.py` (181); `indicators.py` (173) → RSI/MACD/BB/EMA/ATR; `features.py` (124); `risk_engine.py` (118); `earnings_blackout.py` (116); `finpilot_score.py` (113) → **tek public skor API'si**; `score_engine.py` (60) → re-export shim.
**Veri akışı:** Girdi: sembol evreni (9 preset), OHLCV (Alpaca bulk → yfinance fallback). Çıktı: shortlist + skorlar → api/scan, signals_archive (SQLite), Telegram.
**Mevcut durum:** [x] Tam çalışıyor — son 2 hafta yoğun optimizasyon (3.7x hızlanma, chunked concurrency, smart TTL).
**Sorunlar:**
- Sorun: **Skorun kanıtlanmış edge'i yok** (Profit Core: decile_lift 0.728, p=0.995 — ters yönlü) → Neden: ablation'a göre score & R/R bileşenleri zararlı, regime nötr → Sonuç: ürünün ana vaadi ("kazandıran sinyal") veriyle desteklenmiyor → Çözüm: skor bileşenlerini ablation sonuçlarına göre yeniden ağırlıklandır; outcomes_horizon (T+3/5/10) verisiyle haftalık kalibrasyonu edge ölçümüne bağla; edge kanıtlanana kadar pazarlama dilini "karar destek/eğitim" olarak konumla → **P0 (stratejik)**
- Sorun: yfinance hâlâ fallback bağımlılığı (rate limit, shape değişimleri — 2 test bu yüzden fail) → Çözüm: Alpaca'yı birincil yap, yfinance'i mock'la test et → P1
- Sorun: `score_engine.py`/`risk_engine.py` shim olarak duruyor → kafa karışıklığı sürüyor → 90 günde tamamen sil → P2
**Performans:** 3.7x iyileşme taze; 8 worker + 3 batch chunked. İzlenmeli (yeni commit'ler fix-fix-fix paterni gösteriyor).
**Kod kalitesi:** İyi; modüler. `tests/test_signals.py` hâlâ ignore listesinde — sinyal kontratı testsiz → P1.
**Belge durumu:** Scanner optimizasyon raporları `data/` içinde dağınık → docs/'a taşı.
**Academy bağlantısı:** Tarama çıktıları ders örneklerinin ("gerçek hayat örneği: AAPL") otomatik hammaddesi olabilir — Content Generator'a canlı veri beslemesi.
**Stratejik değer:** En değerli teknik varlık; ama değeri "edge kanıtı"na kilitli. Edge'siz haliyle bile B2B "tarama altyapısı" olarak satılabilir (sinyal ≠ tavsiye).

---

## MODÜL 06: score_engine / finpilot_score (scoring)

**Amaç:** Tarama sonuçlarını tek skora indirme.
**Konum:** `scanner/finpilot_score.py` (kanonik) + `score_engine.py` (shim) + `core/calibration.py` (599 LOC, Brier history + rollback strikes ile kalibrasyon).
**Mevcut durum:** [x] Kısmen çalışıyor — mekanik olarak çalışıyor, istatistiksel olarak edge üretmiyor (bkz. Modül 05 P0).
**Sorunlar:**
- Sorun: Kalibrasyon döngüsü (haftalık retrain cron, Pzt 02:00 UTC) skoru kalibre ediyor ama **skorun kendisi ters** → kalibre edilmiş yanlışlık → Çözüm: önce bileşen seçimi (ablation'ı uygula), sonra kalibrasyon → P0
- Sorun: Skor formülünün tek sayfalık matematiksel belgesi yok → hibe/akademik değerlendirmede (XAI) zayıflık → Çözüm: `docs/SCORING_SPEC.md` → P1
**Stratejik değer:** "Açıklanabilir skor + kalibrasyon + rollback" hikâyesi hibe komitesi (P5) için güçlü; ama önce edge.

---

## MODÜL 07: drl/ — Deep Reinforcement Learning

**Amaç:** PPO tabanlı specialist ensemble (trend/momentum/conservative), backtest, optuna araması, inference.
**Konum:** `/drl/` (45 dosya, 12.452 LOC — repo'nun en büyük Python modülü)
**Alt bileşenler:** `backtest_engine.py` (1.038), `ensemble_router.py` (808), `report_generator.py` (754), `specialists.py` (713), `inference.py` (707), `data_loader.py` (667), `callbacks.py` (596), `optuna_search.py` (521), `model_registry.py` (474), `sentiment.py` (434), `training.py` (424), `market_env.py` (407), `multi_asset_env.py` (379), `train_private.py` (351)...
**Veri akışı:** Girdi: OHLCV + sentiment. Çıktı: aksiyon önerileri → api/inference, api/ensemble; `models/` ağırlıkları; MLflow izleme.
**Mevcut durum:** [x] Kısmen çalışıyor — kod canlı (06-10), inference fix'leri yakın tarihli (801f015), ama **model ağırlıkları Mart 2026'dan** (ppo_trend 03-05, ppo_momentum 03-06, ppo_conservative 03-06). 3 ay yeniden eğitim yok.
**Sorunlar:**
- Sorun: Stale modeller — Mart rejiminde eğitilmiş ağırlıklar Haziran piyasasında inference yapıyor → Neden: eğitim pipeline'ı manuel, pahalı, sahipsiz → Sonuç: DRL çıktısının güncel geçerliliği bilinmiyor; "AI-powered" iddiasının en zayıf halkası → Çözüm: ya (a) aylık otomatik retrain cron + walk-forward doğrulama, ya (b) DRL'yi "research preview" etiketiyle üründen ayır → **P1 (karar)**
- Sorun: 12.5K LOC'luk modülün bakım maliyeti, kanıtlanmış katkısının çok üstünde → Çözüm: backtest_engine + report_generator'ı koru (genel değerli), specialist eğitimini dondur → P2
- Sorun: DRL belgeleri (6+ MD) Şubat-Mayıs arası, birbiriyle çelişen roadmap'ler → P2
**Kod kalitesi:** Yüksek (registry, callbacks, optuna entegrasyonu profesyonel). Sorun kalite değil, sahiplik ve güncellik.
**Academy bağlantısı:** DRL kavramları "Algoritmik Trading ve AI" domain'inin (Domain 10) ders materyali; backtest motoru Academy mini-simülasyonlarının altyapısı olabilir — bu, DRL yatırımını gelire bağlamanın en kısa yolu.
**Stratejik değer:** Yatırımcı/hibe anlatısında "derin teknoloji" kanıtı (P3, P5 perspektifleri için altın). Ürün katkısı bugün için sınırlı.

---

## MODÜL 08: agents/ — LLM agent sistemi

**Amaç:** LLM tabanlı analiz/karar katmanı: advisory, CEO raporu, alpha takibi, sosyal istihbarat.
**Konum:** `/agents/` (20 dosya, 3.869 LOC)
**Alt bileşenler:** `alpha_tracker.py` (396 — weighted_score wr×log(1+pf), dashboard Alpha Leaders), `advisory.py` (375), `registry.py` (289 — AgentMeta + katman/durum sorguları), `ceo.py` (285 — haftalık CEO raporu), `social_intelligence_agent.py` (268 — YENİ, Polymarket/HN/DDG), `market_intelligence.py` (244), `strategy_optimizer.py` (236), `research_agent.py` (217), `analysis_agent.py` (197), `feedback.py` (180), `performance_monitor.py` (178), `combo_testing.py` (168), `data_quality.py` (151), `report_agent.py` (142)...
**Veri akışı:** Girdi: scanner çıktıları, fiyat verisi, haber/sosyal kaynaklar. Çıktı: advisory metinleri, CEO raporları, alpha skorları → api/agent, api/advisory, scheduler job'ları.
**Mevcut durum:** [x] Tam çalışıyor (Mayıs audit: "tümü çağrılıyor"; sosyal agent + headroom compression Haziran'da eklendi).
**Sorunlar:**
- Sorun: Agent çıktı kalitesinin nicel ölçümü yok (advisory tavsiyesi isabetli mi?) → Neden: feedback.py var ama outcome'a bağlı skor döngüsü kapalı değil → Sonuç: LLM maliyeti ölçülemeyen değer üretiyor → Çözüm: closed_loop + outcomes_horizon verisiyle agent-bazlı isabet skoru → P1
- Sorun: 19 agent'lık registry'de katman/rol dokümantasyonu kod içinde, mimari diyagram yok → P2
- Sorun: Headroom compression yeni — token maliyet izlemesi (maliyet/agent/gün) dashboard'da yok → P2
**Academy bağlantısı:** Bu agent mimarisi (registry + orchestration kalıbı) Academy'nin 8-agent sisteminin şablonu — `academy/agents/` zaten aynı kalıbı kopyalamış. Ortak base class çıkarılabilir.
**Stratejik değer:** "Multi-agent finansal istihbarat" — medya (P11) ve yatırımcı (P3) hikâyesinin en parlak parçası. Maliyet disipliniyle desteklenmeli.

---

## MODÜL 09: core/ — temel altyapı

**Amaç:** Scheduler, cache, monitoring, KPI, kalibrasyon, backtest, audit, config.
**Konum:** `/core/` (31 dosya, 11.761 LOC)
**Alt bileşenler:** `scheduler.py` (1.247 — aşağıda Modül 10), `monitoring.py` (1.212), `backtest.py` (885), `cache.py` (828 — Redis + smart TTL), `exceptions.py` (621), `calibration.py` (599), `logging.py` (591), `audit.py` (591), `config.py` (541), `kpi_tracker.py` (538), `session_state.py` (463), `slippage_tracker.py` (450), `outcome_reconciler.py` (345), `prometheus_exporter.py` (337), + pipeline, services, tracing, agent_state, pending_actions, audit_log...
**Mevcut durum:** [x] Tam çalışıyor — Mayıs'taki 5 orphan arşivlendi; kalanlar üretimde.
**Sorunlar:**
- Sorun: `exceptions.py` 621 LOC — Mayıs audit'inde orphan listesindeydi, hâlâ duruyor → kullanım analizi yapılıp karar verilmeli → P2
- Sorun: `monitoring.py` (1.212) + `prometheus_exporter.py` + `tracing.py` üç ayrı gözlemleme katmanı; hangisinin canlı veri ürettiği belirsiz (Grafana dev'de kapalı) → Çözüm: tek "observability nedir, nerede görünür" sayfası + ölü kısmı arşiv → P2
- Sorun: `session_state.py` + `auth/streamlit_session.py` Streamlit kalıntısı çifti → P2
**Kod kalitesi:** Yüksek; exception hiyerarşisi, tracing, audit-log kurumsal seviye.
**Stratejik değer:** B2B güven katmanı: audit.py + slippage_tracker + outcome_reconciler = "kurumsal hesap verebilirlik" anlatısı.

---

## MODÜL 10: scheduler (core/scheduler.py)

**Amaç:** APScheduler ile otomasyon kalbi: eval, reconcile, kalibrasyon, haftalık retrain, open-signal çözümleme, haftalık rapor, research pipeline, drift, CEO raporu, auto-approve.
**Konum:** `core/scheduler.py` (1.247 LOC, tek dosya)
**Veri akışı:** Girdi: semboller, cron tanımları. Çıktı: tüm otomatik döngüler; 10dk timeout watchdog'lu job'lar.
**Mevcut durum:** [x] Tam çalışıyor
**Sorunlar:**
- Sorun: 10+ job tek 1.247 LOC dosyada → Neden: organik büyüme → Sonuç: tek job değişikliği tüm scheduler'ı riske atar; test izolasyonu zor → Çözüm: job'ları `core/jobs/` paketine böl, scheduler sadece kayıt yapsın → P2
- Sorun: Job başarı/başarısızlık geçmişi dashboard'da görünmüyor (sessiz başarısızlık riski D.4) → Çözüm: job-run tablosu + UI kartı → **P1**
- Sorun: Academy'nin kendi `academy/scheduler.py`'si (89 LOC) ayrı — iki scheduler (D.1 duplicate) → birleştir → P1
**Academy bağlantısı:** Academy günlük/haftalık/90-günlük döngüleri buraya job olarak bağlanmalı — ayrı scheduler yaşatmak sessiz ölüm reçetesi.
**Stratejik değer:** "İnsansız çalışan döngü" iddiasının teknik kanıtı — otomasyon vizyonlarının (Kısım 5) omurgası.

---

## MODÜL 11: kpi_tracker (core/kpi_tracker.py)

**Amaç:** Sistem ve sinyal KPI'larının takibi.
**Konum:** `core/kpi_tracker.py` (538 LOC)
**Mevcut durum:** [x] Çalışıyor; alpha_tracker ile birlikte weighted_score dashboard'a taşınmış.
**Sorunlar:**
- Sorun: KPI'lar sistem-içi; "işletme KPI'sı" yok (kullanıcı, retention, gelir) → Sonuç: stratejik kararlar (G bölümü) ölçüsüz alınacak → Çözüm: north-star metrik seti tanımla (aktif kullanıcı, sinyal-sonrası işlem korelasyonu, win-rate kanıtı) → P1
**Academy bağlantısı:** Academy Analytics Agent'ın metrikleri (tamamlama, quiz başarı, retention) buraya akmalı — tek KPI omurgası.
**Stratejik değer:** Yatırımcı görüşmesinde gösterilecek traction dashboard'unun temeli.

---

## MODÜL 12: data/ — veri yönetimi

**Amaç:** SQLite DB'ler, sinyal arşivi, ticker evreni, deney çıktıları.
**Konum:** `/data/` (943 dosya)
**Alt bileşenler:** `finpilot.db` (6.9MB — canlı, signals_archive 5.722 satır migrasyonlu), `academy.db` + `academy_v2.db` (4KB — boş), ticker listeleri, calibration history JSON'ları, daily_reports/, 20+ eski deney raporu (ab_report, wf_mc, executive_summary...), 2 docx rapor.
**Mevcut durum:** [x] Çalışıyor ama kirli.
**Sorunlar:**
- Sorun: Deney raporları (Nisan-Mayıs) veri klasöründe → Neden: script'ler çıktıyı data/'ya yazıyor → Sonuç: veri/rapor ayrımı yok, yedekleme stratejisi kurulamıyor → Çözüm: raporları `reports/`'a taşı, script çıktı yollarını düzelt → P2
- Sorun: academy.db ve academy_v2.db ikisi de boş ve V1/V2 ayrımı belirsiz → tek DB'ye karar ver (Bölüm H) → P1
- Sorun: SQLite tek dosya — eşzamanlı yazma sınırı; compose'ta postgres var ama finpilot.db hâlâ SQLite → Çözüm: prod yolunda Postgres migrasyonu netleştir (alembic hazır) → P2
**Stratejik değer:** signals_archive (5.722 satır) + outcomes_horizon = edge kanıtı üretebilecek tek veri varlığı. **Bu repo'daki en stratejik tablo.**

---

## MODÜL 13: cache (core/cache.py)

**Amaç:** Redis destekli önbellek + smart TTL (yeni).
**Konum:** `core/cache.py` (828 LOC)
**Mevcut durum:** [x] Tam çalışıyor — scanner hızlandırmasının ana bileşenlerinden.
**Sorunlar:**
- Sorun: Redis kapalıyken davranışın (in-memory fallback?) belgelenmemiş olması → test et + belgele → P2
- Sorun: Cache hit-rate metriği dashboard'da yok → P3
**Stratejik değer:** Operasyonel; doğrudan stratejik anlam taşımıyor ama API ürünleşmesinde maliyet kontrolü demek.

---

## MODÜL 14: db / migrations (alembic)

**Amaç:** Şema versiyonlama (5 migration), auth + portfolio + signals + outcomes tabloları.
**Konum:** `/migrations/`, `alembic.ini`, `auth/database.py` (1.410 LOC — SQLite/Postgres soyutlaması)
**Mevcut durum:** [x] Tam çalışıyor
**Sorunlar:**
- Sorun: `auth/database.py` 1.410 LOC — auth'tan çok genel DB katmanı olmuş → Neden: organik büyüme → Sonuç: "DB erişimi nerede?" sorusunun 3 cevabı var (auth/database, api/services/watchlist_db, model repository'leri) → Çözüm: `db/` paketi altında repository kalıbını standartlaştır → P2
- Sorun: outcomes_horizon yeni tablosunun migration + test kapsamı doğrulanmalı → P2
**Stratejik değer:** Postgres-hazır şema = ölçeklenme anlatısının sessiz ön şartı.
