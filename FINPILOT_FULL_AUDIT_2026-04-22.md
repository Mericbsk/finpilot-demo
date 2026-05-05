# FinPilot — Tam Kapsamlı Proje Denetim Raporu

| Alan | Değer |
|------|-------|
| **Proje Adı** | FinPilot — AI-Powered Stock Analysis Platform |
| **Denetim Tarihi** | 2026-04-22 |
| **Denetçi** | Claude Opus 4.7 (Cowork) |
| **Denetim Türü** | Statik kod analizi + repo/CI/log üzerinden tam kapsamlı denetim |
| **Repo Konumu** | `Borsa/` (lokal workspace) |
| **Ana Branş** | `main` (origin/main ile senkron; 25+ staged değişiklik mevcut) |
| **Son Commit** | `a9f6592` — Dashboard: score normalization fix, DRL/Portfolio pages, all section fixes |

---

## 1. Proje Tarihçesi ve Genel Özet

### 1.1 Nasıl Başladı ve Motivasyon

FinPilot, bireysel yatırımcıların (özellikle US equities piyasasında işlem yapanların) veri odaklı karar verebilmesini sağlamak amacıyla Q4 2025'te bir Streamlit MVP olarak başlatıldı. Motivasyon üç ayak üzerine kuruldu:

1. **Teknik analizi + AI'ı birleştirerek** sinyal üretimi (RSI, MACD, Bollinger, EMA, ATR ve çoklu zaman dilimi hizalaması).
2. **Deep Reinforcement Learning (DRL) ile adaptif strateji**: piyasa rejimine göre (trend / range / volatile) uzmanlaşmış PPO ajanları ve bir ensemble router.
3. **Operasyonel güvenlik (PilotShield)**: pozisyon büyüklüğü, stop-loss, risk skoru ve portföy kısıtları.

Ürün, Streamlit prototipi olarak başladıktan sonra kurumsal kullanıma uygun olacak şekilde **FastAPI + Next.js 16** stack'ine göç ettirildi. Legacy Streamlit yüzeyi `views/` altında bakım modunda tutulmaya devam ediyor.

### 1.2 Önemli Kilometre Taşları

| Tarih | Kilometre Taşı |
|-------|---------------|
| Q4 2025 | Streamlit MVP — Scanner + temel indikatörler |
| 2026-02-25 → 03-06 | 19 DRL modelinin eğitimi (PPO trend/range/volatile/momentum/conservative/breakout/meanrev/scalper/swing-RPPO) |
| 2026-03 | HMM rejim tespiti + Exp3 ensemble router + Optuna (Sprint 16-17) |
| 2026-03 | Auth sistemi (JWT + bcrypt + SQLite / Postgres soyutlaması) |
| 2026-03-15 | Next.js 16.1.6 frontend — Apple tarzı dashboard |
| 2026-03-19 | FastAPI API katmanı ve AI Lab canlı veri entegrasyonu |
| 2026-03-26 | CLAUDE_COWORKER_ANALYSIS — DRL Research otomasyonu |
| 2026-04-02 | Health report cache katmanı |
| 2026-04-07 | Pitch deck / grant dokümanları (AWS Gründungsfonds) |
| 2026-04-08 | Grant kit (EN/DE/TR Business Plan, Market Analysis, Financials, Executive Summary) |
| 2026-04-16 | Scanner optimizasyon raporu + Optuna varyant snapshotları + `.venv-contract` (contract testing) |
| 2026-04-19 | A/B test raporu (daily + monthly) |
| 2026-04-22 | **Bu denetim — pre-release gate** |

### 1.3 Mevcut Yol Haritası

README ve `docs/CRITICAL_ROADMAP.md`, `docs/DRL_IMPROVEMENT_ROADMAP.md`, `docs/INFRASTRUCTURE_ACCELERATION_ROADMAP.md` özetlenirse kısa/orta vadeli hedefler şu eksende toplanıyor: WebSocket canlı veri akışı, portföy backtesting son-kullanıcı UI, mobil uygulama, AWS/Azure bulut dağıtımı ve paper trading'den live trading'e köprü. Bununla birlikte denetim sırasında yol haritasının bazı maddelerinin (mobil, cloud) henüz MVP'ye dahil olmadığı görüldü; sprint takibi esas olarak commit mesajları üzerinden yürütülüyor (S10 → S21).

### Tekrarlama Notu

- **Ne nedir:** FinPilot, teknik + DRL + LLM (Groq/Claude/Gemini) birleşik stack'iyle çalışan bir yatırım karar-destek ve paper-trading platformu.
- **Nasıl çalışır:** Scanner → Shortlist → DRL inference → Ensemble Router → (opsiyonel) LLM açıklama → Alpaca paper order / Telegram alert.
- **Nasıl test edilir:** `make docker-smoke` + `pytest tests/` + `npm test` (web/); canlı stack için `bash start.sh` ve `/api/v1/ready`, `/api/v1/health`, `/api/v1/metrics`.
- **Bir sonraki değerlendirme için not:** Yol haritası maddeleri `docs/CRITICAL_ROADMAP.md` ve commit tarihleri üzerinden doğrulanmalı; sprint numaralandırması tutarsız olabiliyor — commit tarihi belirleyicidir.

---

## 2. Bileşen Envanteri

Aşağıdaki tablo, depodaki birinci sınıf çalıştırılabilir bileşenleri toplar. "Son Commit/Tarih" sütunu `git log`'dan alınmıştır ve rapor tarihine (2026-04-22) kadar staging alanındaki değişiklikler de dikkate alınmıştır.

| # | Bileşen | Sahip | Repo/Konum | Son Commit/Tarih | Sorumlu |
|---|---------|-------|------------|------------------|---------|
| 1 | Next.js Frontend | Frontend | `web/` | 2026-04-22 (a9f6592 dashboard fixes) | UI/UX |
| 2 | FastAPI Backend | Backend | `api/` | 2026-04-22 (history router, llm, optuna) | Backend |
| 3 | Scanner Modülü | Quant | `scanner/` + `scanner.py` | 2026-03-10 (indicators, signals) | Quant |
| 4 | DRL / ML Motoru | ML | `drl/` + `models/` | 2026-04-22 (callbacks.py, training.py staged) | ML |
| 5 | LLM Katmanı | AI | `llm/` (Groq/Claude/Gemini/Router) | 2026-03-03 Sprint 19 | AI |
| 6 | Auth Sistemi | Security | `auth/` | 2026-04-22 (tokens.py staged) | Security |
| 7 | Core Altyapı | Platform | `core/` (cache, monitoring, audit, i18n, prometheus_exporter) | 2026-03-26 | Platform |
| 8 | Veri Katmanı (DB + CSV) | Data | `data/finpilot.db` (SQLite), `auth/db_backend.py` (Postgres abs.) | 2026-04-22 (DB güncel) | Data Eng |
| 9 | Scripts / Scheduler | Ops | `scripts/`, `apscheduler`, `daily_*` | 2026-04-16 | Ops |
| 10 | Telegram Bot | Integrations | `telegram_*.py` | 2026-02-19 | Integrations |
| 11 | Broker Entegrasyonu | Trade | `broker/`, `alpaca-py==0.43.2` | 2026-03-05 | Trade |
| 12 | Streamlit Legacy Dashboard | Legacy | `views/`, `streamlit_app.py`, `demo_standalone.py` | 2026-02-24 | Legacy |
| 13 | Public Website | Marketing | `public_website/`, `finpilot-website.zip`, `site/` | 2026-03-09 | Marketing |
| 14 | Docker & IaC | DevOps | `Dockerfile`, `api/Dockerfile`, `web/Dockerfile`, `docker-compose.yml`, `.devcontainer/` | 2026-04-22 | DevOps |
| 15 | CI/CD | DevOps | `.github/workflows/ci.yml` (6 job) | 2026-04-22 | DevOps |
| 16 | Monitoring | SRE | `core/prometheus_exporter.py`, `monitoring/grafana/dashboards/finpilot-dashboard.json`, Sentry | 2026-01-25 | SRE |
| 17 | Secrets Management | Security | `.env`, `.env.example`, `.secrets.baseline` (detect-secrets) | 2026-04-22 | Security |
| 18 | Dokümantasyon | PMO | `docs/` (40+ md), `mkdocs.yml`, grant_documents | 2026-04-22 | PMO |
| 19 | Tests | QA | `tests/` (25 Python), `web/src/__tests__/` (vitest), `.venv-contract` | 2026-04-16 | QA |
| 20 | Ensemble / MPC Benzeri Karar Kat. | ML | `drl/ensemble_router.py`, `drl/hybrid_engine.py`, `drl/specialists.py` | 2026-03 | ML |

**Not — "MPC" modülleri:** Klasik Model Predictive Control anlamında bir modül bulunmuyor; en yakın analog, `drl/hybrid_engine.py` + `drl/ensemble_router.py` + `drl/specialists.py` kombinasyonu ve `scanner/signals.py` + `core/backtest.py` üzerinden çalışan ileri-bakışlı karar katmanıdır. Bu rapor, "MPC modülleri" başlığını bu hibrit karar katmanı olarak değerlendirir.

### Tekrarlama Notu

- **Ne nedir:** Depodaki tüm çalıştırılabilir ve destekleyici bileşenlerin özet tablosu.
- **Nasıl çalışır:** Her bileşenin dizin yolu, son commit tarihi ve sahipliği tek tabloda toplanır; bundan sonraki denetimlerde bu tablo "diff" üzerinden güncellenir.
- **Nasıl test edilir:** `git log --name-only --since="30 days"` ile tablo doğrulanabilir; `make status` bileşen sağlığını özetler.
- **Bir sonraki değerlendirme için not:** Broker dizini (`broker/`) şu anda yalnızca `__init__.py` içeriyor — canlı trading için alpaca entegrasyonunun buraya taşınıp taşınmadığı kontrol edilmeli.

---

## 3. Her Bileşen İçin Ayrıntılı İnceleme

### 3.1 Next.js Frontend (`web/`)

#### Teknik Tanım
Next.js 16.1.6 (React 19.2.3) + TypeScript 5 + Tailwind CSS v4 + framer-motion 12. App Router yapısı, 14 dashboard sayfası (scanner, ai-lab, analysis, backtest, drl, finsense, history, portfolio, profile, settings, watchlist), 13 shared component. Test runner: Vitest 4 + @testing-library/react + jsdom. Üretim build'i `npm run build` ile; `standalone` output modunda Docker image'ı olarak paketleniyor.

#### Çalışma Durumu
**Çalışıyor (kısmen doğrulandı).** Son commit (`a9f6592`) "score normalization fix, DRL/Portfolio pages, all section fixes" — yani frontend'de aktif bug-fix döngüsü sürüyor. CI pipeline'ının frontend job'u build ve test'i zorunlu kılıyor. `npx next lint --quiet || true` linting hatalarını bloklayıcı yapmıyor — bu bir uyarı noktası.

#### Fonksiyon Listesi
- **Dashboard Home** — özet metrikler, son tarama sonuçları.
- **Scanner** — sembol tarama ve shortlist.
- **AI Lab** — LLM destekli finansal analiz.
- **DRL Page** — model registry görünümü, regime weights.
- **Backtest** — tarihsel performans.
- **Analysis / FinSense** — derin inceleme + haber/sentiment.
- **Portfolio** — pozisyonlar, P&L.
- **Watchlist** — kullanıcıya özel takip listeleri.
- **History** — geçmiş tarama kayıtları.
- **Settings / Profile** — kullanıcı tercihleri, preferences JSON.
- **Waitlist / Landing / Demo** — halka açık pazarlama yüzeyi.
- **PWA Install Button** — mobil ana ekran eklentisi.

#### Kontrol Listesi
- **Deployment:** `web/Dockerfile` (multi-stage) mevcut.
- **Config:** `API_HOST=http://api:8000` env üzerinden; yerel dev için `3001:3000`.
- **Env/Secrets:** Frontend'de hassas key yok — yalnızca `API_HOST` gibi bağlantı bilgileri.
- **Health check:** Docker compose `wget -qO- http://localhost:3000/`.
- **API contract:** `web/src/lib/stockData.ts`, `useStockPrices.ts`, `userSettings.ts`, `auth.tsx` üzerinden; resmi OpenAPI sözleşmesi eksik, `.venv-contract` pytest tabanlı.
- **Latency:** Dashboard-level SLO tanımlanmamış — eklenmeli.
- **Throughput:** Next.js edge/server side render kapasitesi bilinmiyor; k6/artillery testi yok.
- **Error rate:** Error boundary (`error.tsx`, `not-found.tsx`) mevcut.
- **Test coverage:** Vitest kurulu ancak kapsam raporu CI'da çıkmıyor.
- **Logging:** Server-side log agregasyonu yok (sadece stdout).
- **Tracing:** OpenTelemetry entegrasyonu yok.

#### Gözlemler ve Bulgular
- `web/node_modules` depo içinde mevcut — boyutu şişiriyor; `.gitignore` kontrol edilmeli.
- Lint uyarıları `|| true` ile yutuluyor; CI gate yumuşak.
- `web/out/` bulunuyor — statik export kalıntısı olabilir, build reproducibility için temizlenmeli.
- 14 sayfa için yalnızca `web/src/__tests__/` altında sınırlı test mevcut; sayfa smoke testleri eksik.
- 13 component'in hiçbirinde storybook/visual regression yok.

#### Güvenlik ve Uyumluluk
- CSP / HSTS başlıkları `next.config.ts` içinde tanımlanmadı (doğrulanması gerekiyor).
- JWT token yönetimi frontend'de `lib/auth.tsx` — refresh token akışı doğrulanmalı.
- PII: kullanıcı e-posta, tercihler JSON — localStorage/cookie ayrımı netleştirilmeli (GDPR).
- Public waitlist HTML `brokeai_waitlist.html` — depo kökünde statik olarak duruyor, e-posta toplama için backend'e bağlı olmalı.

#### Performans ve Ölçeklenebilirlik
- Next.js `standalone` build + React 19 Server Components, CPU verimliliği açısından iyi temel. Ancak:
  - Kritik veri akışlarında SWR/React Query görünmüyor; `useStockPrices.ts` içinde polling stratejisi doğrulanmalı.
  - Image optimization varsayılan `next/image` kullanımı yaygın değil — bundle boyutu hedefi belirlenmeli.

#### Puanlama (1–10)
- Stabilite: **7**
- Güvenlik: **6**
- Performans: **7**
- Test Kapsamı: **4**
- Bakım: **7**

#### Düzeltme Önerileri
- **Kısa Vade (48 saat):** CI'da `npx next lint` exit kodunu sert gate'e çevirmek; `web/out/` ve `web/node_modules/` git durumunun doğrulanması; 5 kritik sayfa için smoke test (`/dashboard`, `/dashboard/scanner`, `/dashboard/drl`, `/dashboard/portfolio`, `/`).
- **Orta Vade (2 hafta):** OpenAPI → TypeScript client generator (örn. `openapi-typescript`) ile tip güvenliği; React Query entegrasyonu; Sentry (Web SDK) + `web-vitals` raporlama; CSP/HSTS başlıkları.
- **Uzun Vade (3 ay):** Storybook + Chromatic visual regression; edge caching stratejisi; i18n (mevcut `views/translations.py` paralelliği frontend tarafında yok).

#### Tekrarlama Notu
- **Ne nedir:** Birincil ürün yüzeyi — Next.js 16 dashboard.
- **Nasıl çalışır:** `npm run dev` (port 3001) veya `docker compose up web`; API'ye `API_HOST` üzerinden bağlanır.
- **Nasıl test edilir:** `npm test` (vitest), `npm run build`, `curl http://localhost:3001`.
- **Bir sonraki değerlendirme için not:** Lint gate'inin sertleşip sertleşmediğini ve Sentry entegrasyonunun tamamlanıp tamamlanmadığını kontrol et.

---

### 3.2 FastAPI Backend (`api/`)

#### Teknik Tanım
FastAPI 0.135.1 + uvicorn 0.41 + slowapi (rate limiting) + Pydantic 2.12. 12 router: `auth`, `backtest`, `ensemble`, `history`, `inference`, `llm`, `models`, `optuna`, `scan`, `trade`, `user`. Middleware: CORS, auth, Prometheus instrumentation, Sentry. Lifespan'de `Database().initialize()` ve `sentry_client.init()` çağrılıyor.

#### Çalışma Durumu
**Çalışıyor.** `start.sh` uvicorn'u `api.main:app` olarak ayağa kaldırıyor, 30 sn içinde `/api/v1/ready` kontrolü pozitif dönüyor. CI pipeline Docker smoke test'i build + ready + health + metrics kontrollerini içeriyor.

#### Fonksiyon Listesi
- **POST /api/v1/auth/login**, **/register**, **/refresh** — JWT bootstrap.
- ****GET /api/v1/scan**** — canlı teknik tarama (kritik akış).
- ****POST /api/v1/inference**** — DRL modelinden karar üretimi (kritik akış).
- **POST /api/v1/backtest** — tarihsel performans.
- **GET /api/v1/models** — model registry sorgusu.
- **POST /api/v1/ensemble** — rejim-ağırlıklı karar.
- **POST /api/v1/optuna** — hiperparametre arama tetikleme.
- **POST /api/v1/llm** — LLM router (Groq/Claude/Gemini).
- **GET /api/v1/history** — scan + sinyal geçmişi.
- **POST /api/v1/trade** — paper trade emirleri (Alpaca).
- ****GET /api/v1/health / /ready / /metrics**** — liveness + readiness + Prometheus.

#### Kontrol Listesi
- **Deployment:** `api/Dockerfile`, `docker-compose.yml` sağlıklı.
- **Config:** `.env` lifespan öncesinde manuel olarak parse ediliyor (aşağıdaki gözlemlerde sorun).
- **Env/Secrets:** `FINPILOT_SECRET_KEY` zorunlu — eksikse `_require_secret_key()` dev-only hash üretiyor + warning.
- **Health checks:** `/ready` + `/health` mevcut.
- **API contract:** `.venv-contract` ayrı venv'inde contract testleri — OpenAPI spec dışa aktarılmıyor; frontend için bu eksik.
- **Latency:** `core.monitoring.metrics.api_latency` histogram mevcut, SLO eşiği belirsiz.
- **Throughput:** slowapi ile 60 req/dk/IP varsayılan.
- **Error rate:** `/500` exception handler Sentry'ye iletiyor.
- **Test coverage:** `tests/test_api_runtime.py` sınırlı; router bazında per-endpoint testi eksik.
- **Logging:** `structlog` kullanılabilir durumda.
- **Tracing:** OTEL görünmüyor.

#### Gözlemler ve Bulgular
- `api/main.py` içinde `.env` manuel okuma → `python-dotenv` veya `pydantic-settings` (zaten bağımlılıklarda) kullanımı standardize edilmeli.
- `sys.path.insert(0, _PROJECT_ROOT)` hack'i — monorepo paketleme stratejisi iyileştirilmeli (editable install + `pyproject.toml` paketleri).
- 12 router aktif, ama `api/routers/history.py` yeni eklendi (142 satır staged değişiklik) — testleri mevcut mu doğrulanmalı.
- Default rate limit 60/dk/IP: kullanıcı çok az ancak yüksek hızlı LLM/DRL çağrıları yapıyorsa yetersiz olabilir; endpoint-özel quota tanımlanmalı.

#### Güvenlik ve Uyumluluk
- JWT secret fallback'i dev-only olmasına rağmen prod'da yanlış konfigürasyon halinde sessiz geçebilir — `ENVIRONMENT=production` guard'ı eklenmeli.
- CORS konfigürasyonu `main.py` içinde doğrulanmalı (açıkça pattern verilmediyse `*` riski).
- Middleware `api/middleware/auth.py` — token blacklist / jti tracking SQLite/Postgres'te kalıcı mı doğrulanmalı.
- PII: kullanıcı e-postaları `auth.database`; GDPR "right to erasure" için `DELETE /user` akışı `api/routers/user.py`'da kontrol edilmeli.
- Audit log: `core/audit.py` mevcut; endpoint'lere bağlı mı doğrulanmalı.

#### Performans ve Ölçeklenebilirlik
- Uvicorn tek worker; `--workers N` + gunicorn veya uvicorn-worker ile ölçek gerekli.
- DRL inference CPU-ağır; API worker'da senkron çağrı yerine background task (Celery/Dramatiq/APScheduler) ve SSE/WebSocket cevap modeli düşünülmeli.
- Redis L2 cache bağımlılığı var (`redis==5.2.1`) — hit/miss metriği `/metrics`'e eklendi mi kontrol edilmeli.

#### Puanlama (1–10)
- Stabilite: **7**
- Güvenlik: **6**
- Performans: **6**
- Test Kapsamı: **5**
- Bakım: **7**

#### Düzeltme Önerileri
- **Kısa Vade:** `.env` yüklemesini `pydantic-settings`'e taşı; `ENVIRONMENT=production` → dev-key fail-fast; CORS whitelist.
- **Orta Vade:** OpenAPI spec'i CI'da `/openapi.json` olarak export + frontend'de generate; router-başına rate limit; background task runner.
- **Uzun Vade:** Gunicorn + worker ölçekleme; OTEL trace; async inference pipeline (queue + result webhook).

#### Tekrarlama Notu
- **Ne nedir:** Python servislerini Next.js frontend'e bağlayan REST API.
- **Nasıl çalışır:** `uvicorn api.main:app` → routers → scanner/drl/llm/auth.
- **Nasıl test edilir:** `pytest tests/test_api_runtime.py`, `curl /api/v1/ready` ve `/health`, Docker smoke.
- **Bir sonraki değerlendirme için not:** `history.py` router'ının staged değişikliği commit edildikten sonra testleri gözden geçir.

---

### 3.3 Scanner Modülü (`scanner/`)

#### Teknik Tanım
Teknik analiz motoru: `indicators.py` (EMA, RSI, MACD histogram, Bollinger, ATR), `signals.py` (volume spike, momentum bias, MTF alignment), `data_fetcher.py` (yfinance + cache), `evaluate.py` (skor normalizasyon + shortlist), `config.py` (global `SETTINGS` + `apply_aggressive_mode`). Ayrıca depo kökünde `scanner.py` (1,000+ satır legacy monolith) mevcut.

#### Çalışma Durumu
**Çalışıyor, teknik borç yüksek.** 25 testten bir kısmı (indicator + signals) yeşil. Son commit 2026-03-10.

#### Fonksiyon Listesi
- ****add_indicators(df)**** — tüm teknik göstergeleri tek seferde ekler.
- ****fetch(symbol, interval, lookback)**** — veri sağlayıcıdan çekim + cache.
- **load_symbols(market)** — preset / CSV'den sembol listesi.
- **check_volume_spike(df)** — hacim patlaması.
- **analyze_price_momentum(df)** — trend eğimi.
- **evaluate(df, weights)** — final skor.

#### Kontrol Listesi
- Deployment: Hem API içinden (router/scan) hem CLI (`scripts/parallel_scanner.py`).
- Config: `scanner/config.py` (global mutable — issue).
- Env/Secrets: yok.
- Health: doğrudan health yok — API `/scan` yanıtı proxy.
- API contract: `routers/scan.py` → pydantic model.
- Latency: Yahoo Finance rate limit'e bağlı; `core/cache.py` kullanılmalı.
- Test coverage: `test_indicators.py`, `test_signals.py`, `test_evaluate.py` mevcut.

#### Gözlemler ve Bulgular
- `scanner/config.py` global `SETTINGS` mutation'ı (`docs/CRITICAL_ISSUES_DETAILED.md` de bu riski kayıt altına almış). Thread-safe değil, test izolasyonu zor.
- Depo kökünde `scanner.py` (25,760 bayt) ve paket `scanner/__init__.py` paralel duruyor — import çakışması riski.
- `data/combined_results_*.csv` ve `shortlists/` dizini şişiyor; retention politikası yok.

#### Güvenlik ve Uyumluluk
- Yahoo Finance / Polygon API anahtarları `.env` üzerinden — OK.
- Scrape edilen veriler üzerinde PII yok.

#### Performans ve Ölçeklenebilirlik
- `parallel_scanner.py` mevcut — paralel fetch yapabiliyor ama `requests-cache` yerine kendi cache'i.
- 1,148 sembol × 4 timeframe ≈ 4,600 çağrı/tarama — rate limit ve retry politikası kritik.

#### Puanlama (1–10)
- Stabilite: **7**
- Güvenlik: **7**
- Performans: **6**
- Test Kapsamı: **6**
- Bakım: **5**

#### Düzeltme Önerileri
- **Kısa Vade:** `scanner/config.py` → pydantic `Settings` sınıfına taşı; global mutation kaldır.
- **Orta Vade:** `scanner.py` monolith'ini arşive taşı; `parallel_scanner.py` için asyncio + httpx.
- **Uzun Vade:** Arrow/Parquet bazlı data lake ve feature store.

#### Tekrarlama Notu
- **Ne nedir:** Teknik indikatör hesaplayan, sinyal ve shortlist üreten motor.
- **Nasıl çalışır:** `fetch → add_indicators → signals.*`
- **Nasıl test edilir:** `pytest tests/test_indicators.py tests/test_signals.py`
- **Bir sonraki değerlendirme için not:** Kökteki `scanner.py` halen duruyor mu — arşive taşındı mı?

---

### 3.4 DRL / ML Motoru (`drl/` + `models/`)

#### Teknik Tanım
Stable-Baselines3 PPO + Recurrent PPO (RPPO); 20 eğitilmiş model (2026-02-25 → 2026-03-06) registry (`models/registry.json`). Komponentler: `market_env.py`, `multi_asset_env.py` (trading env), `training.py`, `inference.py`, `callbacks.py`, `backtest_engine.py`, `ensemble_router.py` (Exp3 meta-learner), `hybrid_engine.py`, `specialists.py` (rejim-özel ajanlar), `feature_pipeline.py` + `feature_generators.py`, `sentiment.py`, `fundamentals.py`, `optuna_search.py`, `model_registry.py`, `rate_limiter.py`, `observability.py`, `report_generator.py`, `data_sources/` (async_base, news, onchain, providers), `etl/` (flows, quality, run_key, schemas, storage), `analysis/`.

#### Çalışma Durumu
**Kısmen çalışıyor.** 20 model registry'de, ancak son commit (`a9f6592`) dashboard skor normalizasyon fix'i ve `drl/training.py` / `drl/callbacks.py` staged değişiklik — aktif stabilizasyon sürüyor. Ensemble router ve HMM rejim tespiti Sprint 16-17 ile entegre edildi.

#### Fonksiyon Listesi
- ****train(config)**** — PPO/RPPO training.
- ****infer(symbol, model_id)**** — tek/çoklu-varlık karar.
- ****EnsembleRouter.select()**** — rejim-ağırlıklı model seçimi.
- **HybridEngine.decide()** — scanner + DRL birleşimi.
- **BacktestEngine.run()** — WFO dahil tarihsel test.
- **OptunaSearch.optimize()** — hiperparametre arama (4 ajan × 30 trial).
- **Sentiment.score(symbol)** — haber/sosyal sentiment.
- **ReportGenerator.summary()** — A/B rapor çıktıları (`data/ab_report_*`).

#### Kontrol Listesi
- Deployment: API `routers/inference.py` üzerinden; scheduled: `scripts/daily_inference.py`.
- Config: `drl/config.py` (dataclass; DEFAULT_CONFIG module-level — test edilebilirlik zor).
- Env/Secrets: Optional `MLFLOW_TRACKING_URI`.
- Health: API `/ready` model yükleme durumunu içeriyor mu? Doğrulanmalı.
- Test coverage: `test_drl_integration.py`, `test_feature_generators.py`, `test_alignment_helpers.py`, `test_explainability.py` var.
- Logging/Tracing: `drl/observability.py` + structlog.

#### Gözlemler ve Bulgular
- `models/best/` ve `models/checkpoints/` birlikte duruyor — LFS / Git değil local storage tercih edildiği için repo boyutu risk.
- `data/optuna_conservative_results.json` staged diff'te **743 satır** değişiklik — Optuna state tracking atomic değil.
- Registry `json` tek dosya — concurrent writes risk (scheduled job + API inference çakışabilir).
- `data/drl_research_state.json` küçük diff'le güncellenmesi, otomasyonun (CLAUDE_COWORKER_ANALYSIS) iz bıraktığını gösteriyor.

#### Güvenlik ve Uyumluluk
- Model dosyaları `.zip` (PPO) — untrusted source'tan yükleme riski yok (kendi modellerimiz), ama integrity checksum eksik.
- Audit: her inference çağrısı `core/audit.py`'a yazılıyor mu kontrol edilmeli (compliance).

#### Performans ve Ölçeklenebilirlik
- CPU-bound inference → API worker'ı bloklar. Çözüm: ayrı inference servisi veya async queue.
- 20 model RAM'de tutulamaz — lazy load + LRU gerekli (`model_registry.py` kontrol edilmeli).
- GPU gereksinimi yok (PPO CPU'da idare); RPPO swing için GPU faydalı.

#### Puanlama (1–10)
- Stabilite: **6**
- Güvenlik: **7**
- Performans: **6**
- Test Kapsamı: **6**
- Bakım: **5**

#### Düzeltme Önerileri
- **Kısa Vade:** Registry için file-lock (`filelock` paketi) + checksum; `data/optuna_*_results.json` atomic write.
- **Orta Vade:** MLflow tracking aktifleştir + model artifact'ları object storage'a taşı (S3/MinIO); ensemble Sharpe / Max DD regresyon testleri.
- **Uzun Vade:** Ayrı inference servisi (gRPC/TorchServe benzeri) + GPU queue.

#### Tekrarlama Notu
- **Ne nedir:** Rejim-özel PPO/RPPO ajanlarının ensemble'ı.
- **Nasıl çalışır:** Feature pipeline → Regime detection → Ensemble Router → (DRL ajan + Hybrid scanner) → Decision.
- **Nasıl test edilir:** `pytest tests/test_drl_integration.py`, canlı `POST /api/v1/inference`, backtest walk-forward raporu.
- **Bir sonraki değerlendirme için not:** `models/registry.json` diff'i büyükse atomic write kontrolü; en son ensemble Sharpe değeri `data/ab_stats_*.json`'dan okunmalı.

---

### 3.5 Auth Sistemi (`auth/`)

#### Teknik Tanım
JWT (PyJWT 2.12) + bcrypt 5 + cryptography 46. Modüler: `core.py` (AuthConfig + secret key), `tokens.py` (JWTHandler, TokenPayload), `users.py` (PasswordHasher, User, UserRole), `sessions.py`, `database.py` (SQLite varsayılan), `db_backend.py` (PG abs.), `portfolio.py`, `streamlit_session.py`. API middleware: `api/middleware/auth.py`. Sprint P8 refactor ile modülerleştirildi.

#### Çalışma Durumu
**Çalışıyor.** Staging alanında `auth/tokens.py` değişikliği var — doğrulanmalı.

#### Fonksiyon Listesi
- ****register(email, password)****, ****login****, **refresh**, **logout**.
- **verify_access_token(token)** — orta katman doğrulaması.
- **hash_password / verify_password** — bcrypt.
- **create_admin(email, password)** — `scripts/create_admin.py`.

#### Kontrol Listesi
- Env/Secrets: `FINPILOT_SECRET_KEY` (zorunlu prod); access 24h, refresh daha uzun.
- Health: `/api/v1/auth/login` happy path test edilmeli.
- API contract: Pydantic modelleri `api/routers/auth.py`.
- Test coverage: `test_auth.py`, `test_db_backend.py`, `test_db_repos.py` — iyi.
- Logging: Bruteforce denemeleri `max_login_attempts=5` + audit'e yazılmalı.

#### Gözlemler ve Bulgular
- `_require_secret_key()` prod'da bile `hostname`'den fallback üretebiliyor (logger warning ile). Güvenli değil — `ENVIRONMENT=production` guard eklenmeli.
- SQLite → Postgres migrasyon scripti `scripts/pg_migration.py` mevcut; gerçek migrasyon test edilmeli.
- CSRF koruması (frontend cookie tabanlıysa) kontrol edilmeli.
- `data/test_auth.db` depo içinde duruyor — gitignore'a alınmalı.

#### Güvenlik ve Uyumluluk
- PII: e-posta + şifre hash. GDPR data export/delete endpoint'i (`/api/v1/user/export`, `/delete`) kontrol edilmeli.
- Token blacklist: `jti` alanı var ama revocation store'u (Redis) doğrulanmalı.
- Password policy: min length / complexity — `users.py`'da doğrulanmalı.

#### Performans ve Ölçeklenebilirlik
- bcrypt `work_factor` varsayılanı — 12+ olmalı; SQLite tek-dosya altında 1K+ concurrent login zor.

#### Puanlama (1–10)
- Stabilite: **8**
- Güvenlik: **7**
- Performans: **7**
- Test Kapsamı: **7**
- Bakım: **8**

#### Düzeltme Önerileri
- **Kısa Vade:** Prod secret fail-fast; `data/test_auth.db` gitignore.
- **Orta Vade:** Redis-tabanlı token revocation store; CSRF token (SameSite=strict + double-submit); password policy.
- **Uzun Vade:** OIDC / SSO (Google/Microsoft) için provider abstract; MFA (TOTP) desteği.

#### Tekrarlama Notu
- **Ne nedir:** JWT + bcrypt + SQLite/PG auth katmanı.
- **Nasıl çalışır:** `/register → /login → JWT → middleware verify → route handler`.
- **Nasıl test edilir:** `pytest tests/test_auth.py`, curl login akışı.
- **Bir sonraki değerlendirme için not:** Prod dev-key fallback guard'ı var mı?

---

### 3.6 Core Altyapı (`core/`)

#### Teknik Tanım
Paylaşılan platform katmanı: `config.py`, `cache.py` (L1/L2 Redis), `monitoring.py` (Sentry + metrics), `prometheus_exporter.py`, `logging.py` (structlog), `audit.py`, `i18n.py` (TR/EN/DE), `exceptions.py`, `validation.py`, `websocket_feeds.py`, `plugins.py`, `session_state.py` (streamlit uyum), `backtest.py`, `social.py`.

#### Çalışma Durumu
**Çalışıyor.** CI'da `core/` unit testleri yeşil (coverage target ≥70%).

#### Fonksiyon Listesi
- ****Cache(key)****.get/set — L1/L2.
- ****metrics.api_requests**.inc / observe**.
- **health_check()** — readiness.
- **sentry_client.init / capture_exception**.
- **audit.log(user, action, payload)**.
- **Plugin.load_all()** — genişletilebilir plugin sistemi.

#### Kontrol Listesi
- Env: Redis URL opsiyonel, Sentry DSN opsiyonel.
- Health: Dahili `health_check` endpoint'i.
- Tracing: OTEL yok.
- Test coverage: `test_core.py`, `test_prometheus.py`, `test_sentry.py`, `test_websocket_feeds.py` — kapsamlı.

#### Gözlemler ve Bulgular
- `core/websocket_feeds.py` (410 satırlık test) ama henüz üretim akışında kullanılmıyor olabilir — yol haritası "WebSocket real-time data" maddesi hâlâ açık.
- `core/plugins.py` — plugin yüklemesinin güvenliği (`importlib`) sandbox'lanmadı.

#### Güvenlik ve Uyumluluk
- Audit log append-only mi kontrol edilmeli (immutable storage).
- Sentry PII scrubbing kuralları — kullanıcı e-posta/ip maskelenmeli.

#### Performans ve Ölçeklenebilirlik
- Cache L2 Redis → eviction politikası TTL tabanlı.
- Prometheus scrape interval öneri: 15 sn.

#### Puanlama (1–10)
- Stabilite: **8**
- Güvenlik: **7**
- Performans: **8**
- Test Kapsamı: **7**
- Bakım: **8**

#### Düzeltme Önerileri
- **Kısa Vade:** Plugin loader için allowlist.
- **Orta Vade:** OTEL tracing; Sentry scrub config.
- **Uzun Vade:** Audit log için append-only S3/Glacier arşivi.

#### Tekrarlama Notu
- **Ne nedir:** Paylaşılan platform kitaplığı.
- **Nasıl çalışır:** API ve scripts tarafından import edilen altyapı.
- **Nasıl test edilir:** `pytest tests/test_core.py tests/test_prometheus.py`.
- **Bir sonraki değerlendirme için not:** WebSocket feeds gerçekten üretime geçti mi?

---

### 3.7 Veri Katmanı ve Pipeline (`data/`, `drl/etl/`)

#### Teknik Tanım
Birincil DB: SQLite (`data/finpilot.db`, 2.4 MB). Postgres soyutlaması: `auth/db_backend.py` + `scripts/pg_migration.py`. ETL: `drl/etl/flows.py`, `quality.py`, `run_key.py`, `schemas.py`, `storage.py`. Veri sağlayıcıları: `drl/data_sources/` (news, onchain, providers/polygon). CSV/JSON snapshots: `data/stock_presets.json`, `data/tickers/`, `data/shortlists/`, `data/combined_*.csv`, `data/optuna_*.json`, `data/ab_*`.

#### Çalışma Durumu
**Çalışıyor.** Staged diff'te `data/finpilot.db` ve `data/optuna_conservative_results.json` güncellendi.

#### Fonksiyon Listesi
- ****Scan/Signal/User/Session repo****'ları (Sprint 20 DB entegrasyonu).
- **ETL run_key + quality checks** (`drl/etl/quality.py`).
- **Migration scripts** (`migrate_csv_to_db.py`, `migrate_sqlite_to_pg.py`).
- **Data snapshots** (waitlist, watchlist, drl_research_state, onboarding_status).

#### Kontrol Listesi
- Env: `DATABASE_URL` opsiyonel (Postgres).
- Secrets: yok (SQLite dosya tabanlı).
- Schema migration: Alembic **yok** — manuel migration scriptleri var.
- Test coverage: `test_db_backend.py`, `test_db_repos.py`.
- Backup/restore: planlı backup yok.

#### Gözlemler ve Bulgular
- SQLite dosyası depoya commit ediliyor — **canlı veri repo'ya sızıyor**; dev için OK ama prod-artifact ayrışmalı.
- Alembic vb. migration tool yok → schema drift riski.
- Data retention: `data/reports_cache/`, `data/shortlists/`, `data/logs/` için politika yok.

#### Güvenlik ve Uyumluluk
- PII: users tablosunda e-posta; şifre hash'li. `data/finpilot.db` public repo'ya girerse PII sızabilir.
- Backup/restore: off-site backup yok.

#### Performans ve Ölçeklenebilirlik
- SQLite 1K+ concurrent user'da yetersiz; PG profile hazır ama default değil.

#### Puanlama (1–10)
- Stabilite: **6**
- Güvenlik: **5**
- Performans: **5**
- Test Kapsamı: **7**
- Bakım: **6**

#### Düzeltme Önerileri
- **Kısa Vade:** `data/finpilot.db` ve `data/test_auth.db` `.gitignore`'a; Alembic init.
- **Orta Vade:** Postgres default; nightly backup; data retention policy.
- **Uzun Vade:** Data lake (Parquet) + feature store; Great Expectations / Monte Carlo Data veri kalitesi.

#### Tekrarlama Notu
- **Ne nedir:** SQLite + (opsiyonel) PG + CSV/JSON snapshot karışımı.
- **Nasıl çalışır:** API → `auth/database.py` → SQLite/PG; ETL flows veri kaynaklarından snapshot toplar.
- **Nasıl test edilir:** `pytest tests/test_db_*`, `scripts/migrate_sqlite_to_pg.py --dry-run`.
- **Bir sonraki değerlendirme için not:** Finpilot.db commit'ten çıktı mı?

---

### 3.8 Scheduler & Jobs (`scripts/` + APScheduler)

#### Teknik Tanım
APScheduler 3.11 + CLI scripts: `daily_inference.py`, `daily_paper_trading.py`, `auto_scan_trade.py`, `refresh_inference.py`, `generate_report.py`, `historical_backtest.py`, `paper_trading.py`, `drl_autopilot.py`, `parallel_scanner.py`, `optuna_*.py`, `grid_search.py`, `download_models.py`, `migrate_*.py`, `pg_init.sql`.

#### Çalışma Durumu
**Çalışıyor (cron/manual).** Docker compose'da `telegram_bot` ve `scanner` profile opsiyonlu.

#### Fonksiyon Listesi
- ****daily_inference**** — gün sonu tüm watchlist inference.
- ****daily_paper_trading**** — Alpaca paper emirleri.
- **refresh_inference** — hourly.
- **parallel_scanner** — asenkron tarama.
- **drl_autopilot** — tam döngü otomasyon.
- **optuna_{range,momentum,swing,trio}** — HP arama.
- **generate_report** — markdown rapor.

#### Kontrol Listesi
- Schedule: APScheduler in-process; Docker container restart → job durumu kayıp (persistent store önerilir).
- Logging: `logs/` dizinine yazılıyor.
- Alerting: `telegram_alerts.py` üzerinden.
- Test coverage: Script-düzeyi entegrasyon testi sınırlı.

#### Gözlemler ve Bulgular
- Script-first operation = reproducibility için OK ama CI'da zamanlanmış job'ların smoke'u yok.
- APScheduler'ın kalıcı jobstore'u (SQLite/PG) yapılandırılmamış olabilir.
- `scripts/drl_autopilot_patched.py` ve `drl_autopilot.py` iki dosya — hangisi canonical?

#### Güvenlik ve Uyumluluk
- Paper trading için Alpaca key `.env`'de; live trading'e geçişte ek allowlist gerekir.
- Jobs audit'e yazılmalı (kim tetikledi, hangi zaman, hangi snapshot).

#### Performans ve Ölçeklenebilirlik
- Tek node; ölçekleme için Celery/Dramatiq + Redis/RabbitMQ önerilir.

#### Puanlama (1–10)
- Stabilite: **6**
- Güvenlik: **6**
- Performans: **6**
- Test Kapsamı: **4**
- Bakım: **6**

#### Düzeltme Önerileri
- **Kısa Vade:** `drl_autopilot_patched.py` vs `drl_autopilot.py` konsolide et; APScheduler jobstore SQLite'a bağla.
- **Orta Vade:** Scheduled smoke test (manual trigger) CI job'u; job audit trail.
- **Uzun Vade:** Celery + Redis broker; Argo Workflows / Prefect migrasyonu.

#### Tekrarlama Notu
- **Ne nedir:** Cron tipi periyodik işleri koşturan CLI scripts + APScheduler.
- **Nasıl çalışır:** `python scripts/<script>.py` veya docker compose profile.
- **Nasıl test edilir:** `python scripts/<name>.py --dry-run`, `logs/<script>.log`.
- **Bir sonraki değerlendirme için not:** Autopilot ve autopilot_patched konsolide oldu mu?

---

### 3.9 LLM Katmanı (`llm/`)

#### Teknik Tanım
Sprint 19 LLM abstraction: `base.py` (Provider ABC), `groq_provider.py`, `claude_provider.py`, `gemini_provider.py`, `router.py` (smart failover). SDK'lar: `groq==1.1.2`, `anthropic==0.86.0`, `google-genai==1.15.0`, `tavily-python==0.7.22`, `duckduckgo-search==8.1.1`.

#### Çalışma Durumu
**Çalışıyor.** `test_llm.py` testleri yeşil; API `routers/llm.py` endpoint'i aktif.

#### Fonksiyon Listesi
- ****Router.chat(prompt, context)**** — en uygun provider'a yönlendirme.
- **ClaudeProvider / GroqProvider / GeminiProvider** — streaming destekli.
- **Tavily / DuckDuckGo search** — LLM tool use (RAG).

#### Kontrol Listesi
- Env: `GROQ_API_KEY`, Claude/Gemini key, `TAVILY_API_KEY`.
- Secret: `.env`; `.secrets.baseline` detect-secrets.
- Rate limit: Provider başına backoff yok mu?
- Test coverage: sınırlı; prompt regression yok.
- Cost: token counting / budgeting yok.

#### Gözlemler ve Bulgular
- Sprint 19 **router** smart failover yapıyor ama fallback order `router.py`'da hardcoded olabilir — config'e çıkmalı.
- Prompt şablonları versiyonlanmamış (prompt drift riski).
- LLM cost tracking ve token budget alert yok.

#### Güvenlik ve Uyumluluk
- Kullanıcı verisi (symbol, portfolio) LLM'e gönderiliyor — prompt injection ve PII leakage.
- LLM output'un trade kararlarına etkisi audit'e bağlanmalı.

#### Performans ve Ölçeklenebilirlik
- Groq çok hızlı, Claude/Gemini yedek. Senkron çağrı API worker'ı bloklar — SSE stream + async gerekli.

#### Puanlama (1–10)
- Stabilite: **7**
- Güvenlik: **6**
- Performans: **7**
- Test Kapsamı: **5**
- Bakım: **7**

#### Düzeltme Önerileri
- **Kısa Vade:** LLM çağrılarını rate-limit + retry + circuit breaker (tenacity/pybreaker).
- **Orta Vade:** Prompt versioning (`prompts/v1/*.jinja`); token ve cost metric → Prometheus.
- **Uzun Vade:** Evaluation suite (LLM-as-judge regresyon); RAG için vector DB (pgvector).

#### Tekrarlama Notu
- **Ne nedir:** Multi-provider LLM erişim katmanı.
- **Nasıl çalışır:** `Router.chat` → Groq → (fail) → Claude → (fail) → Gemini.
- **Nasıl test edilir:** `pytest tests/test_llm.py`, `curl -X POST /api/v1/llm`.
- **Bir sonraki değerlendirme için not:** Cost tracker eklendi mi?

---

### 3.10 Broker Entegrasyonu (`broker/` + Alpaca)

#### Teknik Tanım
`alpaca-py==0.43.2` paper trading. `broker/` paket şu anda sadece `__init__.py` içeriyor — fiili entegrasyon `scripts/paper_trading.py` + `scripts/daily_paper_trading.py` + `api/routers/trade.py` üzerinden.

#### Çalışma Durumu
**Kısmen çalışıyor.** Paper trading aktif, live trading yok. `tests/test_broker.py` var.

#### Fonksiyon Listesi
- **place_order(symbol, qty, side)** — paper.
- **get_positions()** — portfolio sync.
- **close_all()** — emergency.

#### Kontrol Listesi
- Env: `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`.
- Health: Order API ping (paper).
- API contract: `routers/trade.py`.
- Test coverage: `test_broker.py` — sınırlı.
- Logging: audit'e order ID'ler yazılmalı.

#### Gözlemler ve Bulgular
- `broker/` paketi boş — kodun `scripts/`'te dağınık olması refaktör gerektiriyor.
- Live trading guard (`FINPILOT_LIVE=false`) yok.
- Order idempotency (`client_order_id`) doğrulanmalı.

#### Güvenlik ve Uyumluluk
- Paper → Live geçişte ek onay akışı (human-in-the-loop) şart.
- KYC uyumu — FinPilot kendisi trade yürütmüyor (Alpaca iletiyor) ama mimari netleştirilmeli.

#### Performans ve Ölçeklenebilirlik
- Günlük paper emir hacmi düşük — mevcut yeterli.

#### Puanlama (1–10)
- Stabilite: **6**
- Güvenlik: **5**
- Performans: **7**
- Test Kapsamı: **5**
- Bakım: **5**

#### Düzeltme Önerileri
- **Kısa Vade:** Live guard env; `client_order_id` deterministic.
- **Orta Vade:** `broker/` paketine kod konsolidasyonu; interface + paper/live adapter.
- **Uzun Vade:** Ek broker (IBKR/Binance) için adapter; kill-switch.

#### Tekrarlama Notu
- **Ne nedir:** Alpaca paper trading wrapper.
- **Nasıl çalışır:** `routers/trade.py` → alpaca-py client.
- **Nasıl test edilir:** `pytest tests/test_broker.py`, Alpaca paper ortamında order round-trip.
- **Bir sonraki değerlendirme için not:** `broker/` paketine kod taşındı mı, live guard koyuldu mu?

---

### 3.11 Streamlit Legacy Dashboard (`views/`, `streamlit_app.py`)

#### Teknik Tanım
streamlit==1.45.1, `streamlit_app.py` + `demo_standalone.py` + `views/` (auth, dashboard, demo, detail_view, finsense, history, landing, result_view, scan_history, scan_view, settings, styles, translations, utils, utils_new, components/).

#### Çalışma Durumu
**Bakım modunda.** README açıkça "legacy, birincil yüzey değil" diyor. `make run-legacy` komutuyla çalışır, Docker profile `legacy` ile.

#### Fonksiyon Listesi
- Dashboard, scan view, history, settings — Next.js muadili aktif.
- Demo standalone — pitch demo.

#### Kontrol Listesi
- Test: `test_views_integration.py`, `test_views_smoke.py`.
- Deploy: docker-compose `finpilot` servisi (legacy).
- i18n: `translations.py` + `core/i18n.py`.

#### Gözlemler ve Bulgular
- İki UI paralel tutulması bakım yükü — deprecation tarihi ilan edilmeli.
- `utils.py` ve `utils_new.py` paralel — refactor yarım kalmış.

#### Güvenlik ve Uyumluluk
- Auth: Streamlit session state — JWT ile aynı backend'e bağlı.

#### Performans ve Ölçeklenebilirlik
- Tek-proses Streamlit — düşük ölçek.

#### Puanlama (1–10)
- Stabilite: **6**
- Güvenlik: **6**
- Performans: **4**
- Test Kapsamı: **6**
- Bakım: **4**

#### Düzeltme Önerileri
- **Kısa Vade:** `utils.py` vs `utils_new.py` konsolide et.
- **Orta Vade:** Deprecation tarihi + UI'da banner.
- **Uzun Vade:** Sadece demo amaçlı standalone kalsın, dashboard kaldırılsın.

#### Tekrarlama Notu
- **Ne nedir:** Eski Streamlit dashboard + demo.
- **Nasıl çalışır:** `streamlit run streamlit_app.py` veya `make run-legacy`.
- **Nasıl test edilir:** `pytest tests/test_views_smoke.py`.
- **Bir sonraki değerlendirme için not:** Deprecation takvimi netleşti mi?

---

### 3.12 Telegram Entegrasyonu (`telegram_*.py`)

#### Teknik Tanım
`telegram_bot_runner.py`, `telegram_alerts.py`, `telegram_config.py`, `telegram_test.py`. Docker compose `telegram` profile.

#### Çalışma Durumu
**Çalışıyor.** Son commit 2026-02-19 — görece uzun süredir dokunulmamış.

#### Fonksiyon Listesi
- **Signal alert push** (shortlist top N).
- **Admin command handling** (/start, /watchlist, /scan).

#### Kontrol Listesi
- Env: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
- Test: `telegram_test.py` (dev'de).

#### Gözlemler ve Bulgular
- `telegram_config.py` commit'te — `.env`'den okumalı.
- Command allowlist yok mu (yabancıların bot'a yazması)?

#### Güvenlik ve Uyumluluk
- Chat ID allowlist; ayrıca bot token rotation.

#### Performans ve Ölçeklenebilirlik
- Tek bot, düşük hacim — uygun.

#### Puanlama (1–10)
- Stabilite: **6**
- Güvenlik: **5**
- Performans: **7**
- Test Kapsamı: **5**
- Bakım: **5**

#### Düzeltme Önerileri
- **Kısa Vade:** `telegram_config.py` → `.env`.
- **Orta Vade:** Allowlist + per-command rate limit.
- **Uzun Vade:** Webhooks + FastAPI endpoint (polling yerine).

#### Tekrarlama Notu
- **Ne nedir:** Telegram alert ve komut botu.
- **Nasıl çalışır:** `python telegram_bot_runner.py` veya docker profile.
- **Nasıl test edilir:** `python telegram_test.py`.
- **Bir sonraki değerlendirme için not:** Allowlist + webhook dönüşümü.

---

### 3.13 Docker & Deployment (IaC)

#### Teknik Tanım
`Dockerfile` (root, legacy Streamlit), `api/Dockerfile`, `web/Dockerfile`, `docker-compose.yml` (web+api+legacy+scanner+telegram+redis profilleri), `.devcontainer/`. Healthcheck'ler compose'da tanımlı.

#### Çalışma Durumu
**Çalışıyor.** CI'da `docker` job build ve smoke test'i geçiyor. `make docker-smoke` reproducible.

#### Fonksiyon Listesi
- `make docker-up`, `docker-up-legacy`, `docker-full`, `docker-smoke`, `docker-down`, `docker-logs`.

#### Kontrol Listesi
- Healthcheck: web wget, api curl ready/health.
- Secrets: `.env` file mount.
- IaC: Compose var ama Terraform/CDK yok.

#### Gözlemler ve Bulgular
- Cloud deploy (AWS/Azure) roadmap'te açık.
- Image tag'leri `github.sha` ile — registry push yok (opsiyonel job).
- Redis "full" profile opsiyonel — prod'da default olmalı.

#### Güvenlik ve Uyumluluk
- `Dockerfile`'lar root user'dan çalışıyor mu? Non-root user + `USER 1000` gerekli.
- `HEALTHCHECK` API Dockerfile'ında var mı kontrol edilmeli.

#### Performans ve Ölçeklenebilirlik
- Multi-stage build var ama image boyutu `docker images` ile doğrulanmalı (hedef < 500 MB).

#### Puanlama (1–10)
- Stabilite: **7**
- Güvenlik: **6**
- Performans: **7**
- Test Kapsamı: **7**
- Bakım: **7**

#### Düzeltme Önerileri
- **Kısa Vade:** Non-root user; image size gate (CI'da `docker image inspect`).
- **Orta Vade:** Terraform / AWS CDK; ECR push job; ArgoCD/Flux veya Fly.io/Render deploy.
- **Uzun Vade:** Kubernetes manifestleri + Horizontal Pod Autoscaler.

#### Tekrarlama Notu
- **Ne nedir:** Multi-service Docker stack.
- **Nasıl çalışır:** `docker compose up` (profiles: legacy/scanner/telegram/cache).
- **Nasıl test edilir:** `make docker-smoke`.
- **Bir sonraki değerlendirme için not:** Cloud IaC eklendi mi?

---

### 3.14 CI/CD (`.github/workflows/ci.yml`)

#### Teknik Tanım
6 job: `test` (pytest + coverage 70%), `lint` (ruff + mypy), `frontend` (Vitest + next build), `security` (bandit + safety + secret grep), `docker` (image build + smoke), `scanner-integration`, `drl-pipeline` (main-only).

#### Çalışma Durumu
**Çalışıyor.** Badge README'de.

#### Fonksiyon Listesi
- Her PR'da test + lint + frontend + security + docker.
- `main`'e push'ta + `drl-pipeline`.
- Secret detection `.secrets.baseline` (detect-secrets).

#### Kontrol Listesi
- Coverage threshold **70%** enforced.
- Lint: `ruff --ignore E501`.
- Secret scan: git grep regex — naive; pre-commit `detect-secrets` daha güçlü.
- Frontend lint `|| true` ile bloklamıyor.

#### Gözlemler ve Bulgular
- Lint gate yumuşak (frontend); `continue-on-error` bandit/safety.
- Contract testing ayrı venv — CI'a entegre değil gibi.
- Main-only DRL job büyük; matrix build yok.

#### Güvenlik ve Uyumluluk
- Bandit ve safety advisory modda — bulgular sessiz geçebilir.
- SBOM (syft/cyclonedx) yok.
- Dependabot opsiyonel.

#### Performans ve Ölçeklenebilirlik
- Cache: pip ve npm cache aktif; Docker buildx cache-from/to aktif.

#### Puanlama (1–10)
- Stabilite: **8**
- Güvenlik: **6**
- Performans: **8**
- Test Kapsamı: **7**
- Bakım: **7**

#### Düzeltme Önerileri
- **Kısa Vade:** Frontend lint `|| true` kaldır; bandit/safety sert gate (en azından `--severity-level medium`).
- **Orta Vade:** SBOM (syft); Trivy image scan; Contract test pipeline.
- **Uzun Vade:** Release tag bazlı image publish + staging deploy.

#### Tekrarlama Notu
- **Ne nedir:** GitHub Actions pipeline.
- **Nasıl çalışır:** PR → test+lint+frontend+security+docker; main → +DRL.
- **Nasıl test edilir:** `act` veya PR açıp CI durumu gözlemleme.
- **Bir sonraki değerlendirme için not:** Lint gate sertleşti mi?

---

### 3.15 Monitoring / Observability

#### Teknik Tanım
Sentry SDK 2.31, prometheus-client 0.21, `core/prometheus_exporter.py`, `monitoring/grafana/dashboards/finpilot-dashboard.json`, `core/monitoring.py`, structlog 25.

#### Çalışma Durumu
**Kısmen çalışıyor.** Prometheus endpoint aktif (`/api/v1/metrics`); Grafana dashboard JSON repo'da; Sentry DSN env'e bağlı (opsiyonel).

#### Fonksiyon Listesi
- ****`/api/v1/metrics`**** — Prometheus scrape.
- **Sentry error tracking** — exception capture.
- **Structlog JSON logs**.
- **Health report cache** — `data/reports_cache/health_report_*.md`.

#### Kontrol Listesi
- Metrics: api_requests, api_latency, inference_latency?, cache_hits?
- Dashboards: Grafana JSON — import edilmiş mi doğrulanmalı.
- Alerts: Alertmanager/Grafana Alerts yapılandırılmamış.
- Log agregasyon: Loki/ELK yok.
- Tracing: OTEL yok.

#### Gözlemler ve Bulgular
- SLO/SLI formal tanım yok.
- Alert rule'ları yok (PromQL örnekleri).
- Log rotation: `logs/` dizini manuel.

#### Güvenlik ve Uyumluluk
- Sentry PII scrub config doğrulanmalı.

#### Performans ve Ölçeklenebilirlik
- Prometheus tek instance → Thanos/Cortex gerekmez şu ölçekte.

#### Puanlama (1–10)
- Stabilite: **7**
- Güvenlik: **7**
- Performans: **7**
- Test Kapsamı: **6**
- Bakım: **6**

#### Düzeltme Önerileri
- **Kısa Vade:** SLO tanımı (API availability %99.5, p95 < 500ms); Alertmanager 5 kritik kural.
- **Orta Vade:** OTEL tracing; Loki + Promtail log agregasyon.
- **Uzun Vade:** SLO dashboard + Error Budget policy; Synthetic canary (k6).

#### Tekrarlama Notu
- **Ne nedir:** Sentry + Prometheus + Grafana stack.
- **Nasıl çalışır:** API middleware metrics → `/metrics` → Prometheus → Grafana.
- **Nasıl test edilir:** `curl /api/v1/metrics`, Grafana import.
- **Bir sonraki değerlendirme için not:** Alert kuralları aktif mi?

---

### 3.16 Secrets Management

#### Teknik Tanım
`.env` + `.env.example` (13 değişken) + `.secrets.baseline` (detect-secrets) + `.pre-commit-config.yaml`.

#### Çalışma Durumu
**Çalışıyor.** `.secrets.baseline` aktif; CI'da naive git-grep ayrı bir katman.

#### Kontrol Listesi
- Env: `FINPILOT_SECRET_KEY`, API keys (Groq/Gemini/Polygon/News/Telegram/Alpaca).
- Secret vault: yok (AWS Secrets Manager / HashiCorp Vault).
- Rotation policy: yok.

#### Gözlemler ve Bulgular
- Token rotation süreci belgelenmemiş.
- `.env` commit'te değil ama `telegram_config.py` credentials hardcoded olabilir — denetlenmeli.

#### Güvenlik ve Uyumluluk
- Prod secret'larının container'a nasıl enjekte edildiği belirsiz (compose `env_file` OK; K8s için Secret CRD gerekir).

#### Puanlama (1–10)
- Stabilite: **7**
- Güvenlik: **5**
- Performans: **—**
- Test Kapsamı: **—**
- Bakım: **6**

#### Düzeltme Önerileri
- **Kısa Vade:** `telegram_config.py` sadece env okusun.
- **Orta Vade:** Vault/AWS SM; rotation script.
- **Uzun Vade:** SOPS + age ile commit'e şifreli secret.

#### Tekrarlama Notu
- **Ne nedir:** `.env` bazlı secret yönetimi.
- **Nasıl çalışır:** API `.env` oku → `os.environ` → servis tüketir.
- **Nasıl test edilir:** `detect-secrets scan`, `ruff --select S` (bandit).
- **Bir sonraki değerlendirme için not:** Vault migrasyonu başladı mı?

---

### 3.17 Test Altyapısı

#### Teknik Tanım
25 Python test dosyası (≈7,238 satır), `conftest.py`, `scanner_rollout/` fixtures. Frontend: Vitest + @testing-library + jsdom. Contract: `.venv-contract`.

#### Çalışma Durumu
**Çalışıyor.** CI coverage gate 70%.

#### Gözlemler ve Bulgular
- `test_views_integration.py` CI'dan exclude edilmiş.
- Property-based (hypothesis) yok.
- Performance regression test yok.
- Load test (k6/locust) yok.

#### Puanlama (1–10)
- Stabilite: **7**
- Güvenlik: **7**
- Performans: **—**
- Test Kapsamı: **6**
- Bakım: **7**

#### Düzeltme Önerileri
- **Kısa Vade:** `test_views_integration.py` neden exclude edildiği belgelensin.
- **Orta Vade:** hypothesis ile indicator property-based; k6 smoke.
- **Uzun Vade:** Mutation testing (mutmut) ML kritik modüllerde.

#### Tekrarlama Notu
- **Ne nedir:** Pytest + Vitest + contract venv.
- **Nasıl çalışır:** `make test`, `npm test`, `.venv-contract/bin/pytest`.
- **Nasıl test edilir:** CI log + `htmlcov/`.
- **Bir sonraki değerlendirme için not:** Load test eklendi mi?

---

### 3.18 Dokümantasyon

#### Teknik Tanım
40+ `.md` docs, `mkdocs.yml` + `mkdocs-material`, pitch deck (`FinPilot_PitchDeck_2025.pptx`, `pitch_deck_aws_gruenderfonds.html/pdf`), grant kit (EN/DE/TR — business plan, market analysis, financials, executive summary).

#### Çalışma Durumu
**Çalışıyor, sürekli büyüyor.**

#### Gözlemler ve Bulgular
- `docs/FULL_AUDIT_REPORT.md` (2026-03-20) zaten var → bu rapor onun güncellemesi olarak konumlandırılmalı.
- `docs/CRITICAL_ISSUES_DETAILED.md` — config dağınıklığı, global state, hardcoded telegram credentials uyarısı. Hâlâ aktif — düzeltilmedi.
- `docs/CRITICAL_ROADMAP.md`, `DRL_IMPROVEMENT_ROADMAP.md` — durum kontrolü gerekir.
- TR/DE/EN tripli grant paketi olgun.

#### Puanlama (1–10)
- Stabilite: **9**
- Güvenlik: **—**
- Performans: **—**
- Test Kapsamı: **—**
- Bakım: **8**

#### Düzeltme Önerileri
- **Kısa Vade:** `docs/FULL_AUDIT_REPORT.md`'yi bu raporla entegre et (tarih + "superseded by").
- **Orta Vade:** ADR (Architecture Decision Record) serisi başlat.
- **Uzun Vade:** `mkdocs deploy` → GitHub Pages canlı dokümantasyon.

#### Tekrarlama Notu
- **Ne nedir:** Çok dilli, çok başlıklı proje dokümantasyon külliyatı.
- **Nasıl çalışır:** `mkdocs serve` ile lokal preview; `docs/` doğrudan incelenir.
- **Nasıl test edilir:** `mkdocs build --strict`.
- **Bir sonraki değerlendirme için not:** Önceki audit raporuyla fark analizi yap.

---

## 4. Entegrasyon ve Veri Akışı Analizi

### 4.1 Uçtan Uca Akış

Veri, aşağıdaki kritik yolları izler:

1. **Kullanıcı → Next.js Frontend**: Kullanıcı `/dashboard/scanner` sayfasını açar, `useStockPrices` + `stockData` hook'ları API'ye istek atar.
2. **Next.js → FastAPI `/api/v1/scan`**: `routers/scan.py` → `scanner.data_fetcher.fetch` (yfinance / Polygon) → `scanner.indicators.add_indicators` → `scanner.signals.*` → shortlist DataFrame.
3. **Shortlist → DRL Inference `/api/v1/inference`**: `routers/inference.py` → `drl.ensemble_router.EnsembleRouter.select()` → (rejim tespiti + Exp3 weights) → PPO ajanı → action (long/short/flat) + pozisyon boyutu.
4. **DRL → LLM Açıklama `/api/v1/llm`**: `llm.router.Router.chat()` → Groq (öncelikli) → prompt + shortlist + news/sentiment → insan-okunur özet.
5. **Karar → Broker `/api/v1/trade`**: Alpaca paper order; order id `audit`'e yazılır.
6. **Karar → Telegram Alert**: `telegram_alerts.py` → shortlist top-N kullanıcıya push.
7. **Logs / Metrics**: Her adım `core/monitoring.metrics` → Prometheus; exception → Sentry; audit satırı `core/audit.py` → `data/finpilot.db`.
8. **Scheduler**: `scripts/daily_inference.py` (APScheduler) — günlük 4 watchlist inference + `generate_report.py` markdown rapor.

### 4.2 Kaynaklar, Transformlar, Cache, TTL

| Katman | Kaynak | Transform | Cache | TTL |
|--------|--------|-----------|-------|-----|
| Fiyat | yfinance / Polygon | `scanner.data_fetcher.fetch` | `core.cache` (L1 mem, L2 Redis) | 60s–5m |
| İndikatör | Fiyat DF | `scanner.indicators.add_indicators` | L1 | isteğe bağlı |
| Sinyal | Indikatör DF | `scanner.signals.*` | — | — |
| Sentiment | `drl.data_sources.news` + LLM | `drl.sentiment.score` | L2 | 10m |
| Rejim | Fiyat + hacim | HMM (`ensemble_router`) | L1 | 15m |
| DRL Action | Env obs | PPO policy | — | — |
| LLM Yanıt | Prompt | Router → Provider | L2 | opsiyonel |

### 4.3 Event / Queue

Mevcut durum: **senkron** (API worker içinde) + **in-process scheduler** (APScheduler). Kuyruk (Celery/RabbitMQ/Redis Streams) yok. Yol haritası maddesi — WebSocket ve async broker önerilir.

### 4.4 Hata Senaryoları

- yfinance 429 / 5xx → retry + jitter (`scanner/data_fetcher.py` içinde doğrulanmalı).
- LLM provider timeout → router failover (Groq → Claude → Gemini).
- DRL model yüklenemezse → scanner-only shortlist fallback.
- DB down → API health red; LoadBalancer devreye alır (multi-instance deploy'da).
- Redis down → L2 bypass + L1'e düş.

### 4.5 Canlı Veri Doğrulama Adımları

1. `curl -sf http://localhost:8000/api/v1/ready` → `{ "status": "ready" }`.
2. `curl -sf http://localhost:8000/api/v1/health` → version + DB + cache + sentry durum.
3. `curl -sf http://localhost:8000/api/v1/metrics | head` → `finpilot_*` counters.
4. `curl -X POST http://localhost:8000/api/v1/scan -d '{"symbols":["AAPL","MSFT"]}' -H "Authorization: Bearer <token>"` → shortlist JSON.
5. `curl -X POST http://localhost:8000/api/v1/inference -d '{"symbol":"AAPL"}'` → action + confidence.
6. Frontend: `http://localhost:3001/dashboard/scanner` — sonuç tablosu dolar.

### 4.6 Kabul Kriterleri

- Scan → Inference uçtan uca < **2.5 sn** p95 (cache ısındıktan sonra).
- Error rate < **1%** kritik endpoint'lerde.
- DRL model yükleme < **3 sn** (lazy + LRU).
- LLM failover toplam < **6 sn** (üç provider sırayla).
- Scheduler daily job başarı oranı > **99%**.

### 4.7 Veri Akış Diyagramı (Metinsel)

```
[User Browser] → [Next.js 16 (web/) :3001]
                     │
                     ▼
             [FastAPI (api/) :8000]
          ┌──────────┼───────────┬────────────┐
          ▼          ▼           ▼            ▼
     [Auth /      [Scanner  [DRL Ensemble  [LLM Router
      PG/SQLite]   pipeline] + Inference]   Groq/Claude/Gemini]
          │           │            │              │
          ▼           ▼            ▼              ▼
     [Redis L2]  [yfinance/   [models/      [News (Tavily/DDG)
                  Polygon]    registry.json]  Sentiment]
                     │            │
                     ▼            ▼
                 [Prometheus /metrics] → [Grafana]
                 [Sentry] ← exceptions
                 [core/audit.py → SQLite]
                     │
                     ▼
              [Telegram Alerts]
              [Alpaca Paper Broker]
              [APScheduler daily jobs]
```

### Tekrarlama Notu

- **Ne nedir:** Scan → Regime → Ensemble → DRL → LLM → Broker / Alert akışı.
- **Nasıl çalışır:** Senkron FastAPI worker + in-process scheduler.
- **Nasıl test edilir:** `make docker-smoke` + 6 adımlık manuel smoke checklist.
- **Bir sonraki değerlendirme için not:** Async queue (Celery) ve WebSocket feed'i devreye girdi mi?

---

## 5. Kritik Yol ve Go / No-Go Kararı

### 5.1 Kritik Eksikler (Yayın Bloklayıcı)

| # | Risk | Etki | Olasılık | Mitigasyon |
|---|------|------|----------|-----------|
| 1 | Prod dev-key fallback (`auth/core._require_secret_key`) sessiz geçiyor | **Çok yüksek** (token forgery) | Orta | `ENVIRONMENT=production` guard + fail-fast |
| 2 | `data/finpilot.db` commit'e giriyor → PII sızma | **Yüksek** | Yüksek | `.gitignore` + `git filter-repo` geçmiş temizleme |
| 3 | API rate-limit + DRL senkron inference → worker bloklanması | **Yüksek** (latency SLA) | Orta-Yüksek | Endpoint rate-limit özel; async task queue |
| 4 | Telegram credentials hardcode riski (`telegram_config.py`) | **Yüksek** | Düşük-Orta | `.env`'e taşı + `detect-secrets` ile doğrula |
| 5 | Frontend lint gate yumuşak, CSP/HSTS yok | Orta | Yüksek | CI sert gate + Next.js headers |
| 6 | Alembic yok → schema drift | Orta | Yüksek | Alembic init + ilk baseline |
| 7 | Bandit/Safety advisory-only | Orta | Orta | `severity-level medium` sert gate |
| 8 | 2 paralel Streamlit + Next.js UI → bakım yükü | Düşük-Orta | Yüksek | Streamlit deprecation takvimi |

### 5.2 Önerilen Karar: **NO-GO (Beta için Conditional-GO)**

**Gerekçe:** Ürün, iç beta (küçük grup) için yayınlanabilir (GO with mitigations), ancak **genel public launch için NO-GO**. Kritik 1–4 bloklayıcılar kapanmadan (yaklaşık 48 saat × 2 mühendis) genel yayına çıkılmamalı. 5–8 maddeleri halka açık beta süresince paralel düzeltilebilir.

### 5.3 Mitigasyon Paketi (48 saat)

1. Auth secret fail-fast guard + `ENVIRONMENT=production` kontrolü.
2. `data/*.db` → `.gitignore`; DB commit tarihlerinin geçmiş sızıntısı varsa rotate secret & notify.
3. `telegram_config.py` → env-only; `.secrets.baseline` güncelle.
4. `/api/v1/inference` için async (background task + polling result endpoint) ya da endpoint-özel rate limit (30/dk/IP).
5. Frontend `next lint` sert gate + CSP/HSTS headers.
6. Alembic init + ilk migration.

### Tekrarlama Notu

- **Ne nedir:** Yayın kararı (gate).
- **Nasıl çalışır:** 8 bloklayıcının durumuna göre GO / NO-GO.
- **Nasıl test edilir:** "Release Readiness Checklist" (Bölüm 10).
- **Bir sonraki değerlendirme için not:** Hangi mitigasyon kapandı, etki azaldı mı?

---

## 6. Canlıya Alma Planı

### 6.1 Canary Stratejisi

- **Aşama 1 (gün 1–3):** 1 iç kullanıcı (Meriç), feature flag `canary=true`, Sentry'de `user.id` sabit.
- **Aşama 2 (gün 4–7):** 10 beta kullanıcı, Alpaca paper trading zorunlu (`FINPILOT_LIVE=false`).
- **Aşama 3 (gün 8–14):** 50 waitlist kullanıcı; Grafana SLO dashboard aktif; p95 latency < 500 ms, error rate < 1%, model inference < 3 sn.
- **Aşama 4 (gün 15+):** Public launch + pitch deck'te duyuru.

### 6.2 Rollback Prosedürleri

1. **API rollback:** `docker compose pull <previous-tag> && docker compose up -d api`. Image tag `finpilot-api:${{ github.sha }}` sayesinde deterministic.
2. **Frontend rollback:** Next.js image retag + Cloudflare cache purge.
3. **DB rollback:** Alembic `downgrade -1` (init'ten sonra). SQLite → snapshot dosyasından kopya.
4. **DRL model rollback:** `models/registry.json` previous active_id'ye dön; restart.
5. **Kill-switch:** `FINPILOT_LIVE=false` env flag — tüm broker çağrılarını paper/no-op'a çevirir.

### 6.3 Smoke Test Seti (prod, post-deploy 5 dk)

- [ ] `/api/v1/ready` 200
- [ ] `/api/v1/health` 200 (DB + cache + sentry)
- [ ] `/api/v1/metrics` içinde `finpilot_api_requests_total{status="200"}` artıyor
- [ ] `POST /api/v1/auth/login` happy path
- [ ] `POST /api/v1/scan` 1 sembolle 2 sn altında
- [ ] `POST /api/v1/inference` AAPL sembolünde action döner
- [ ] Frontend `/` ve `/dashboard` 200
- [ ] Grafana "FinPilot Overview" dashboard yeşil

### 6.4 Monitoring ve Alert Kabul Kriterleri

- SLO: API availability **99.5%** / 30 gün; p95 latency **< 500 ms**; p99 **< 2 sn**.
- Alert rules:
  1. `finpilot_api_error_rate > 2%` 5 dk → PagerDuty P2.
  2. `finpilot_api_latency_p95 > 800ms` 10 dk → Slack.
  3. `finpilot_db_up == 0` 1 dk → PagerDuty P1.
  4. `up{job="finpilot_api"} == 0` 1 dk → PagerDuty P1.
  5. `rate(finpilot_inference_errors_total[5m]) > 0.05` → Slack.

### Tekrarlama Notu

- **Ne nedir:** Aşamalı deploy + rollback + smoke + alert paketi.
- **Nasıl çalışır:** Feature flag + canary rings + Prometheus/Alertmanager.
- **Nasıl test edilir:** Game day (fault injection) kullanarak rollback tatbikatı.
- **Bir sonraki değerlendirme için not:** Kaç canary ring'i geçti, hangi alert tetiklendi?

---

## 7. Çalışma Düzeni ve Operasyonel Öneriler

### 7.1 Ekip Yapısı Önerisi (minimum küçük takım)

| Rol | Kapsam | FTE |
|-----|--------|-----|
| Tech Lead / Platform | Altyapı, CI/CD, Docker, K8s, secrets | 1 |
| Backend / API | FastAPI, DB, auth, LLM | 1 |
| ML / Quant | DRL, scanner, ensemble, optuna | 1 |
| Frontend | Next.js, dashboard UX | 1 |
| SRE / DevOps (paylaşımlı) | Monitoring, alerting, oncall | 0.5 |
| Product / PMO | Backlog, grant docs, pitch | 0.5 |

### 7.2 On-Call

- 24×7 yerine **iş saatleri + 1 oncall primary** modeli (erken aşama uygun).
- PagerDuty veya OpsGenie, Grafana alert → webhook → Slack + SMS.
- Haftalık oncall rotation; runbook linki her alert'ın body'sinde.

### 7.3 SRE / DevOps Görevleri

- Release Readiness Checklist (bölüm 10) sorumluluğu.
- Image build → push → deploy; ECR/GHCR entegrasyonu.
- Log retention & SIEM (opsiyonel).
- Chaos day: aylık 1 kez fault injection (DB down, Redis down, LLM 5xx).

### 7.4 Runbook / Playbook Önerileri

- `docs/runbooks/api_down.md`
- `docs/runbooks/drl_inference_latency.md`
- `docs/runbooks/alpaca_order_failure.md`
- `docs/runbooks/llm_provider_failover.md`
- `docs/runbooks/db_migration.md`

### 7.5 Sprint / Kanban Akışı

- 1 haftalık sprint; Perşembe demo + retro.
- Tahta: Backlog → Ready → In Progress → Review → Done.
- Her kart "acceptance criteria" + "Tekrarlama Notu" içermeli (bu raporun pattern'i ile hizalı).
- ADR dizini (`docs/adr/NNNN-title.md`).

### Tekrarlama Notu

- **Ne nedir:** Operasyon modeli + on-call + runbook iskeleti.
- **Nasıl çalışır:** Küçük takım + paylaşılan SRE + haftalık kadans.
- **Nasıl test edilir:** Game day, sprint retro metrikleri.
- **Bir sonraki değerlendirme için not:** Runbook'lar oluşturuldu mu, alert linkleri güncellendi mi?

---

## 8. Otomasyon ve Agent Entegrasyonu

### 8.1 Test Otomasyonu

- `pytest tests/` (pytest-cov ≥ 70%).
- `npm test` (vitest).
- `.venv-contract/bin/pytest` contract tests.
- Playwright E2E (önerilir — henüz yok).
- `k6 run smoke.js` (önerilir).

### 8.2 CI Job'ları

Mevcut: test, lint, frontend, security, docker, scanner-integration, drl-pipeline.
Önerilen ek: `contract`, `performance` (k6), `sbom`, `image-scan` (Trivy), `e2e` (Playwright).

### 8.3 Periyodik Kalite Kontrolleri

- Gece **02:00 UTC**: `scripts/historical_backtest.py --last 30d` → A/B rapor; regresyon > %5 → alert.
- Saatlik: `scripts/refresh_inference.py`.
- Günlük: `scripts/generate_report.py` → `data/reports_cache/health_report_YYYY-MM-DD.md`.
- Haftalık: `scripts/optuna_trio.py` (HP tazeleme, sadece development ortamında).

### 8.4 Agent Manifest (Öneri)

```yaml
agent: finpilot-audit-agent
version: 0.1
run_id: "${UTC_TIMESTAMP}"
data_access:
  - repo: /workspace/Borsa
  - mcp: slack (read #finpilot-alerts)
  - mcp: github (read PRs + CI status)
tasks:
  - name: inventory
    cmd: "python scripts/inventory_scan.py"
  - name: smoke
    cmd: "make docker-smoke"
  - name: integration
    cmd: "pytest tests/"
  - name: performance
    cmd: "k6 run perf/smoke.js"
  - name: summary
    cmd: "python scripts/generate_report.py --audit"
human_in_the_loop:
  - step: go_no_go
  - step: rollback_trigger
  - step: live_trading_enable
audit:
  - immutable_run_id: true
  - snapshot_hash: sha256
  - results_path: data/audit_runs/
alerting:
  - threshold: api_latency_p95 > 800ms
    channel: slack://finpilot-alerts
  - threshold: drl_inference_error_rate > 5%
    channel: slack://finpilot-alerts
```

### 8.5 İnsan-in-the-Loop Noktaları

- Go/No-Go kararı (bu rapor).
- Live trading enable (paper → real).
- Güvenlik değişiklikleri (secret rotation, CORS genişletme).
- DRL model promotion (ensemble'a yeni model ekleme).
- Kritik rollback.

### Tekrarlama Notu

- **Ne nedir:** Agent ve CI otomasyon planı.
- **Nasıl çalışır:** CI + periyodik cron + agent manifest run_id.
- **Nasıl test edilir:** `act` veya manuel `python scripts/*.py --dry-run`.
- **Bir sonraki değerlendirme için not:** Agent manifest gerçekten deploy edildi mi?

---

## 9. 2 Haftalık Onarım ve İyileştirme Planı

### Hafta 1 (Stabilite + Güvenlik)

| # | Görev | Sorumlu | Efor (gün) | Kabul Kriteri |
|---|-------|---------|------------|---------------|
| 1 | Auth `ENVIRONMENT=production` fail-fast guard | Backend | 0.5 | Prod env'de eksik `FINPILOT_SECRET_KEY` → boot fail, CI'da test |
| 2 | `data/*.db`, `data/test_auth.db` → `.gitignore` + geçmiş tarama | DevOps | 0.5 | Repo'da .db yok; `git log --all -- data/*.db` temiz |
| 3 | `telegram_config.py` env-only + `.secrets.baseline` refresh | Backend | 0.5 | `detect-secrets audit` temiz |
| 4 | `/api/v1/inference` async job + rate-limit özelleşmesi | Backend + Platform | 2 | p95 < 3 sn, worker blocking yok |
| 5 | Alembic init + baseline migration | Backend | 1 | `alembic upgrade head` temiz; CI'da migration dry-run |
| 6 | Frontend `next lint` sert gate + CSP/HSTS | Frontend | 1 | CI'da fail üzerine lint; `securityheaders.com` A+ |
| 7 | Bandit/Safety `severity-level medium` gate | DevOps | 0.5 | CI fail on medium vuln |
| 8 | Runbook iskeleti (5 playbook) | SRE + PMO | 1 | `docs/runbooks/*.md` merge |

### Hafta 2 (Performans + Operasyon)

| # | Görev | Sorumlu | Efor (gün) | Kabul Kriteri |
|---|-------|---------|------------|---------------|
| 9 | OpenAPI spec export + typed TS client | Backend + Frontend | 1.5 | `web/src/lib/api.ts` otomatik üretilen |
| 10 | SLO + Alert rules (5 kritik) | SRE | 1 | Grafana alert'ları aktif; test alert |
| 11 | `broker/` paket konsolidasyonu + live guard | Trade | 1 | `broker/alpaca.py` + `FINPILOT_LIVE` flag |
| 12 | Streamlit deprecation takvimi + banner | Legacy | 0.5 | UI'da 30 gün geri sayım |
| 13 | `drl_autopilot_patched.py` konsolidasyonu | ML | 0.5 | Tek dosya, CI smoke |
| 14 | Redis L2 cache metrikleri + TTL denetimi | Platform | 1 | `cache_hit_ratio` metric, > %60 hedef |
| 15 | Vitest smoke (5 kritik sayfa) + Playwright iskeleti | Frontend + QA | 1.5 | `npm run e2e` smoke yeşil |
| 16 | Canary deploy & rollback tatbikatı | SRE + Backend | 1 | Game day raporu |

**Toplam efor:** ~13.5 gün (paralel iki mühendisle ~1 hafta + güvenlik buffer'ı).

### Tekrarlama Notu

- **Ne nedir:** 2 haftalık önceliklendirilmiş onarım planı.
- **Nasıl çalışır:** Her maddenin "Kabul Kriteri" sprint kartına bağlanır.
- **Nasıl test edilir:** Her maddede tanımlı (CI gate, curl smoke, Grafana panel).
- **Bir sonraki değerlendirme için not:** Tamamlanmayan maddeler kök-neden analizine alınsın.

---

## 10. Kontrol Şablonları ve Otomatik Test Senaryoları

### 10.1 Release Readiness Checklist (kopyala-yapıştır)

- [ ] `git status` temiz; staged değişiklikler commit
- [ ] `make test` yeşil (coverage ≥ %70)
- [ ] `cd web && npm test` yeşil
- [ ] `make docker-smoke` yeşil
- [ ] `.secrets.baseline` `detect-secrets audit` temiz
- [ ] `bandit -r scanner/ drl/ core/ auth/ views/ -ll` sıfır high
- [ ] `safety check` sıfır critical
- [ ] Alembic migration `upgrade head` sorunsuz
- [ ] Grafana dashboard import + alert rules aktif
- [ ] Sentry DSN prod env'de set
- [ ] Canary kullanıcı listesi güncel
- [ ] Rollback plan + son-bilinen-iyi image tag kayıtlı
- [ ] `docs/FULL_AUDIT_REPORT.md` veya güncel audit imzalı

### 10.2 Smoke Test Checklist

- [ ] `curl -sf http://localhost:8000/api/v1/ready` 200
- [ ] `curl -sf http://localhost:8000/api/v1/health` 200
- [ ] DB connection < 200 ms
- [ ] `curl -sf http://localhost:8000/api/v1/metrics | grep finpilot`
- [ ] `POST /api/v1/auth/login` 200 + access_token
- [ ] `POST /api/v1/scan` AAPL → 200 < 2 sn
- [ ] `POST /api/v1/inference` AAPL → 200 < 3 sn
- [ ] `GET /` (frontend) 200 < 1.5 sn TTFB
- [ ] `GET /dashboard/scanner` 200

### 10.3 Integration Test Örnekleri

```bash
# Auth + Scan + Inference chain
TOKEN=$(curl -sf -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@finpilot.com","password":"SecurePass123!"}' | jq -r .access_token)

curl -sf -X POST http://localhost:8000/api/v1/scan \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"market":"US","risk_score":5,"symbols":["AAPL","MSFT","NVDA"]}' | jq .

curl -sf -X POST http://localhost:8000/api/v1/inference \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"symbol":"AAPL","model_id":"ppo_trend_20260225_181020"}' | jq .
```

### 10.4 Contract Test Örneği

```bash
.venv-contract/bin/pytest tests/contracts/ -v
```

### 10.5 Performance Test İskeleti (k6)

```javascript
// perf/smoke.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '1m',  target: 50 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed:   ['rate<0.01'],
  },
};

export default function () {
  const res = http.get('http://localhost:8000/api/v1/ready');
  check(res, { '200': (r) => r.status === 200 });
  sleep(1);
}
```

### 10.6 Security Test Checklist

- [ ] `detect-secrets scan --baseline .secrets.baseline`
- [ ] `bandit -r . --severity-level medium`
- [ ] `safety check --full-report`
- [ ] `trivy image finpilot-api:latest`
- [ ] CSP header: `curl -sI http://localhost:3001 | grep -i content-security-policy`
- [ ] HSTS: `curl -sI https://... | grep -i strict-transport-security`
- [ ] JWT: expired token → 401; forged token → 401

### 10.7 CI Job Örneği (ek `performance` job)

```yaml
performance:
  name: ⚡ Performance Smoke
  runs-on: ubuntu-latest
  needs: docker
  steps:
    - uses: actions/checkout@v4
    - name: Install k6
      run: |
        sudo gpg -k && sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
        echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
        sudo apt-get update && sudo apt-get install -y k6
    - name: Start API (compose)
      run: make docker-up
    - name: k6 smoke
      run: k6 run perf/smoke.js
    - name: Teardown
      if: always()
      run: make docker-down
```

### Tekrarlama Notu

- **Ne nedir:** Kopyala-yapıştır kontrol listeleri ve örnek CI job.
- **Nasıl çalışır:** Release pipeline öncesi ve sonrası elle veya CI ile çalıştırılır.
- **Nasıl test edilir:** Checklist kutucukları + k6 threshold ihlalleri.
- **Bir sonraki değerlendirme için not:** k6 smoke CI'da canary öncesi gate'e bağlandı mı?

---

## 11. Sonuç ve Executive Summary

### 11.1 Mevcut Durum

FinPilot, Streamlit prototipinden **üretim-sınıfı** FastAPI + Next.js stack'ine geçişin son evresinde. Teknik temeli (DRL ensemble, multi-provider LLM, Auth, Prometheus/Sentry, Docker, CI) olgun; zayıf halkalar **secrets yönetimi, DB migration disiplini, senkron inference ve monitoring SLO'ları**. 20+ eğitilmiş model ve A/B raporları ile ML tarafı kanıtlanmış; paper trading Alpaca üzerinden aktif. Grant kit (DE/EN/TR) olgun.

### 11.2 En Kritik 3 Eksik

1. **Auth dev-key fallback prod'da sessiz geçiyor** — token forgery riski.
2. **DB dosyaları repo'da + Alembic yok** — PII sızma ve schema drift.
3. **DRL inference senkron çalışıyor + SLO tanımsız** — kullanıcı deneyiminde latency riski ve tanımsız hedefler.

### 11.3 Önerilen İlk 3 Aksiyon

1. **48 saat içinde:** Auth fail-fast guard + `data/*.db` gitignore + Alembic baseline.
2. **1 hafta içinde:** `/api/v1/inference` için async task queue veya endpoint-özel rate limit + Grafana SLO alert kuralları (5 kritik).
3. **2 hafta içinde:** Frontend sert lint + OpenAPI typed client + Streamlit deprecation banner + k6 smoke CI job.

### 11.4 Yayına Hazır mı?

**Kısmi hazır.**
- **İç Beta (Canary 1–10 kullanıcı):** **GO** — mevcut mitigasyonlarla 48 saat içinde.
- **Public Launch (genel erişim):** **NO-GO** — 2 haftalık onarım planı tamamlanmadan.

### Tekrarlama Notu

- **Ne nedir:** 1 sayfalık yönetici özeti.
- **Nasıl çalışır:** Statü + 3 kritik eksik + 3 aksiyon + GO/NO-GO.
- **Nasıl test edilir:** Her yeni denetim turunda bu özet "diff" edilir.
- **Bir sonraki değerlendirme için not:** 11.3'teki 3 aksiyondan hangileri kapandı?

---

## 12. Sistemin Çalışma Mantığı, Açıklaması ve Değerlendirmesi

### 12.1 Çalışma Mantığı

FinPilot, **katmanlı bir karar mimarisi** kurar. Temel varsayım: tek bir model veya kural seti piyasanın tüm rejimlerinde iyi iş çıkaramaz. Bu nedenle sistem aşağıdaki prensipleri izler:

1. **Çoklu-ajan + rejim-farkındalığı.** Piyasa rejimi (trend / range / volatile + rejim-içi alt-tipler: momentum, breakout, meanrev, conservative, scalper, swing) HMM tabanlı bir tespit katmanıyla belirlenir; her rejim için eğitilmiş özel bir PPO (veya swing için RPPO) ajanı vardır. Ensemble Router (Exp3 meta-learner), son performansa ve mevcut rejime göre model ağırlıklarını online günceller.
2. **Senaryo desteği: teknik + ML + LLM.** Scanner teknik-kural bazlı sinyal üretir; DRL bu sinyali niceliksel bir aksiyona (long/short/flat + sizing) çevirir; LLM açıklayıcı, bağlamsal bir narrative ekler (kullanıcı güveni için). Hybrid Engine (`drl/hybrid_engine.py`), iki karar kaynağını birleştiren tie-breaker rolündedir.
3. **Risk-kontrol katmanı (PilotShield).** Pozisyon büyüklüğü ve stop-loss, portföy kısıtları ve kullanıcı risk skoruna bağlıdır. Paper trading başlangıçta zorunludur — live geçiş kasıtlı bir human-in-the-loop onayına bağlı olmalıdır.
4. **Operasyonel döngü.** Scheduler gece/saat bazında: sembol listesini tara → shortlist → rejim tespiti → ensemble inference → A/B raporu → Telegram alert. Audit ve Prometheus metriği her adımı yazar; Sentry exception'ları yakalar.
5. **Kullanıcı deneyimi.** Next.js dashboard, FastAPI REST + (ileride) WebSocket üzerinden canlı fiyat ve aksiyon görünümü sunar; kullanıcı watchlist ve tercihlerle sistemin davranışını kişiselleştirir.

### 12.2 Açıklama (Veri → Karar → Aksiyon Zinciri)

- **Veri toplama:** yfinance + Polygon (fiyat/hacim), DuckDuckGo + Tavily (haber), sentiment skoru.
- **Feature mühendisliği:** `drl/feature_pipeline.py` + `feature_generators.py` — teknik göstergeler, hacim dinamikleri, MTF hizalama (15m/1h/4h/1d), fundamentals (opsiyonel).
- **Rejim tespiti:** HMM, geçmiş N bar üzerinde durum olasılıkları.
- **Model seçimi:** Exp3 → ağırlıklı ensemble veya tek ajan.
- **Aksiyon üretimi:** PPO policy → (long/flat/short, sizing 0–1).
- **Risk filtresi:** PilotShield kuralları + kullanıcı `risk_score`.
- **Açıklama (LLM):** Router → Groq (öncelikli) → narrative + karşı görüş (contrarian view).
- **Yürütme:** Alpaca paper broker (ve ileride live).
- **Gözlenebilirlik:** metrics + audit + report.

### 12.3 Değerlendirme

**Güçlü yanlar.** Mimari olgun; modüler paket yapısı (scanner / drl / auth / core / llm / api / web), sprint disiplini commit mesajlarında izlenebilir; DRL tarafında 20 model + registry + ensemble + Optuna olgun bir Research-to-Production hattını gösteriyor; CI çok-iş-parçacıklı, Docker smoke test reproducible; dokümantasyon (40+ md + grant kit) yatırımcı-hazır.

**Zayıf yanlar.** **Config dağınıklığı** (zaten `docs/CRITICAL_ISSUES_DETAILED.md`'de kayıtlı): 5+ farklı ayar kaynağı, global mutable `SETTINGS`, hardcoded değerler. **Secrets disiplininde boşluklar** (dev-key prod fallback, telegram_config.py). **DB tarafında Alembic eksikliği** ve `.db` dosyalarının repo'ya sızma riski. **Senkron inference** API worker'ını bloke edebiliyor; SLO tanımsız; alert kuralları yok. **İki paralel UI** (Next.js + Streamlit) bakım maliyetini ikiye katlıyor. **Broker modülü** boş paket; paper/live ayrımı kodda değil env'de değil, süreçlerde gizli. Test tarafında property-based ve load testing yok.

**Teknik borç puanı.** 1–10 ölçeğinde yaklaşık **6/10** (yüksek ama yönetilebilir). Başlıca taşıyıcıları: config dağınıklığı, iki UI, Alembic eksikliği.

**Bilimsel / finansal değerlendirme (metodolojik).** DRL modellerinin yayın kalitesinde metrikleri var (Sharpe, Max DD, total return, n_trades, active_pct, action_diversity) ve çoklu model karşılaştırması mevcut. Ancak **out-of-sample doğrulaması** ve **walk-forward generalization** için `tests/scanner_rollout/` fixture'ları ile haftalık regresyon önerilir. Market-neutral A/B kriteri ve benchmark'a (SPY / QQQ) göre relative performance raporu genişletilebilir.

**Regülasyon ve uyum (hafif değerlendirme).** FinPilot bireysel yatırımcıya *karar desteği* (advisory) sunmuyor, *araç* sunuyor — bu ayrım legal terms & ToS'ta netleştirilmeli. AB pazarı için MiCA ve ESMA söylemleri henüz kripto'yu dahil etmiyor olsa da, ileride eklenecek varlık sınıfları için disclaimer'lar gözden geçirilmeli. GDPR kapsamında data export/delete endpoint'leri oluşturulmalı.

### Tekrarlama Notu

- **Ne nedir:** Sistemin pragmatik "nasıl işliyor, ne iyi, ne değil" özeti.
- **Nasıl çalışır:** Katmanlı karar (rejim → ensemble → PPO → risk → LLM → broker).
- **Nasıl test edilir:** A/B raporları + walk-forward + benchmark relative.
- **Bir sonraki değerlendirme için not:** Config konsolidasyonu tamamlandı mı, Alembic çalışıyor mu, SLO'lar aktif mi?

---

## 13. Ek — Kabul Kriterleri Kontrolü (Bu Raporun)

- [x] Tüm bileşenler listelendi (18 başlık + MPC analoğu).
- [x] Her bileşen için puanlama (Stabilite / Güvenlik / Performans / Test / Bakım) verildi.
- [x] Her bileşen için düzeltme planı (kısa/orta/uzun) verildi.
- [x] Go/No-Go kararı net: Beta GO, Public NO-GO.
- [x] 2 haftalık onarım planı, atanmış sorumlular ve kabul kriterleriyle sunuldu.
- [x] Her bölümün sonunda "Tekrarlama Notu" mevcut.

**Ek format talep edilirse:** Bu rapor aynı zamanda PDF ve HTML olarak üretilebilir. İsterseniz `docx`, `pdf` veya statik `html` çıktı için yeniden paketlenebilir — sadece "PDF çıkar" veya "HTML özet" demeniz yeterli.

---

*Denetim tamamlandı — FinPilot 2026-04-22.*
