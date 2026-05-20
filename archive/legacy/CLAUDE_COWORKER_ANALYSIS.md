# 🤖 FinPilot × Claude Co-worker — Tam Kapsamlı Entegrasyon Analizi
**Tarih:** 2026-03-26 | **Analist:** Claude Co-worker | **Sürüm:** 1.0

---

## 1. Proje Özeti ve Tarihçe

### 1.1 Nasıl Başladı?

**FinPilot**, yapay zeka destekli bir hisse senedi tarama ve analiz platformudur. Proje, teknik analizi LLM tabanlı öngörülerle birleştirerek yatırımcılara veri odaklı karar destek sistemi sunmak amacıyla kurulmuştur. Git geçmişi incelendiğinde Sprint tabanlı bir geliştirme metodolojisi kullanıldığı görülmektedir; proje Sprint 1'den Sprint 22'ye doğru hızla büyümüş, her sprint belirli bir yetenekler kümesini sisteme entegre etmiştir.

**Motivasyon:** Borsa analizini demokratize etmek; karmaşık teknik analiz ve DRL modellerini, LLM tabanlı yorumlama ile birleştirerek ortalama bir yatırımcı için erişilebilir kılmak.

### 1.2 Mevcut Durum (Sprint 22)

| Bileşen | Durum | Son Sprint |
|---------|-------|------------|
| Streamlit Dashboard | ✅ Çalışıyor | Sprint 9-17 |
| FastAPI Backend | ✅ Çalışıyor | Sprint 20+ |
| Scanner Modülü | ✅ Çalışıyor | Sprint 18 |
| Auth Sistemi | ✅ Çalışıyor | Sprint P8 |
| LLM Router | ✅ Çalışıyor | Sprint 19 |
| DRL Modülleri | ⚠️ Kısmen | Sprint 14-17 |
| Veritabanı | ⚠️ Kısmen | Sprint 20-22 |
| Broker (Alpaca) | ⚠️ Kısmen | Sprint 21 |
| Next.js Frontend | ⚠️ Kısmen | Belirsiz |
| WebSocket Feeds | ⚠️ Kısmen | Sprint N/A |
| Monitoring/Prometheus | ✅ Çalışıyor | Sprint 4 |
| Telegram Bot | ✅ Çalışıyor | Erken sprint |

### 1.3 Yol Haritası & Eksikler

**Roadmap'ten tamamlananlar:**
- [x] Modüler scanner mimarisi
- [x] CI/CD pipeline (GitHub Actions)
- [x] Docker deployment
- [x] Unit test coverage
- [x] Auth sistemi (JWT + SQLite/PostgreSQL)
- [x] LLM abstraction layer (Groq/Claude/Gemini failover)
- [x] DRL training pipeline
- [x] Optuna hyperparameter optimization

**Roadmap'ten eksikler:**
- [ ] WebSocket real-time data (core/websocket_feeds.py var ama production'da aktif değil)
- [ ] Portfolio backtesting (scripts'te var, entegre değil)
- [ ] Mobile app
- [ ] Cloud deployment (AWS/Azure)
- [ ] PostgreSQL migration (şu an SQLite'da takılı)

**Kritik Darboğazlar:**
1. Veritabanı katmanı hâlâ SQLite'ta; PostgreSQL geçişi tamamlanmamış
2. `api/routers/backtest.py` import edilmiş ama dosya eksik (ImportError riski)
3. DRL modelleri `models/` klasöründe ZIP yoksa CI "No artifacts" veriyor
4. Next.js frontend (`web/`) bağımsız çalışıyor ama API entegrasyonu belirsiz
5. `broker/` kısmen geliştirilmiş; gerçek trade execution için yeterli değil

---

> **Tekrarlama Notu — Bölüm 1:**
> - **Ne nedir:** FinPilot, Sprint tabanlı geliştirilen AI destekli hisse senedi analiz platformu
> - **Nasıl çalışır:** Streamlit + FastAPI + DRL + LLM katmanları birlikte çalışıyor
> - **Nasıl test edilir:** `make test` + `pytest tests/ -v`
> - **Sonraki değerlendirme notu:** Sprint 22 veritabanı geçişi tamamlandı mı? Kontrol et.

---

## 2. Bileşen Envanteri

| # | Bileşen | Konum | Açıklama | Durum |
|---|---------|-------|----------|-------|
| 1 | **Frontend (Streamlit)** | `streamlit_app.py`, `views/` | Ana UI katmanı, 8 view modülü | ✅ |
| 2 | **Frontend (Next.js)** | `web/` | TypeScript tabanlı ikinci frontend | ⚠️ |
| 3 | **Backend API** | `api/` | FastAPI, 6 router, rate limiter | ✅ |
| 4 | **Veritabanı** | `auth/database.py`, `auth/db_backend.py` | SQLite (default), PostgreSQL (opsiyonel) | ⚠️ |
| 5 | **Data Pipeline** | `scanner/data_fetcher.py`, `drl/feature_pipeline.py` | yfinance + Polygon.io + altdata | ✅ |
| 6 | **Canlı Veri Kaynakları** | `drl/data_sources/`, `broker/` | yfinance, Alpaca, Polygon, OnChain | ⚠️ |
| 7 | **Dashboard** | `views/dashboard.py`, `views/` | Streamlit tabanlı 5-tab panel | ✅ |
| 8 | **API Katmanı** | `api/routers/` | models, inference, ensemble, optuna, scan, backtest | ✅ |
| 9 | **Auth & Güvenlik** | `auth/` | JWT, bcrypt, session manager | ✅ |
| 10 | **MPC Modülleri** | `broker/` | Alpaca paper trading | ⚠️ |
| 11 | **ML/Agent Modülleri** | `drl/`, `llm/` | DRL (PPO/SAC/TD3), LLM Router | ⚠️ |
| 12 | **Scheduler/Cron** | `apscheduler` (requirements), `scripts/` | APScheduler entegre, betikler manuel | ⚠️ |
| 13 | **Monitoring & Logging** | `core/monitoring.py`, `core/audit.py`, `core/prometheus_exporter.py` | Sentry + Prometheus + structured logging | ✅ |
| 14 | **Deployment & CI/CD** | `Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml` | Docker multi-stage + GitHub Actions | ✅ |
| 15 | **Üçüncü Taraf Servisler** | `llm/`, `broker/`, `telegram_alerts.py` | Groq, Anthropic, Google, Alpaca, Telegram | ⚠️ |
| 16 | **Config & Secrets** | `.env`, `core/config.py`, `.pre-commit-config.yaml` | python-dotenv + detect-secrets | ✅ |

---

## 3. Bileşen Bazında Derin İnceleme

---

### 3.1 Frontend — Streamlit Dashboard

**Teknik Tanım:** `streamlit_app.py` ana giriş noktası. `views/` altında 8+ modül: `dashboard.py`, `demo.py`, `finsense.py`, `landing.py`, `detail_view.py`, `result_view.py`, `scan_history.py`, `settings.py`. `v1.7.0` olarak etiketlenmiş.

**Çalışma Durumu:** ✅ Çalışıyor

**Fonksiyon Listesi:**
- Auth gate (landing → login → panel)
- 5-tab scanner dashboard (Tarama, Sonuçlar, Performans, AI Lab, Ayarlar)
- Demo modu (auth gerektirmez)
- FinSense Akademi (eğitim içerikleri)
- Çok dilli destek (core/i18n.py)
- Kullanıcı ayarları (user_settings.json)

**Kontrol Listesi:**

| Kontrol | Durum | Not |
|---------|-------|-----|
| Health check | ⚠️ | `/_stcore/health` Docker'da kontrol ediliyor ama uygulama içi yok |
| Latency | ⚠️ | Ölçüm kodu yok; Streamlit rerender gecikmesi görülüyor |
| Error rate | ⚠️ | Sentry entegre ama Streamlit exception UI düşüyor |
| Config | ✅ | `user_settings.json` ve session state |
| Env | ✅ | `.env` ile yükleniyor |
| Test coverage | ⚠️ | `test_views_smoke.py` + `test_views_integration.py` var; coverage %50+ |
| Logging | ✅ | `core/logging.py` ile structured logging |
| Tracing | ❌ | Distributed tracing yok |

**Güvenlik & Uyumluluk:** JWT auth korumalı panel, public demo sayfası auth-free. CSRF koruması yok (Streamlit inherent risk). `GLOBAL_CSS` `unsafe_allow_html=True` ile inject ediliyor — XSS riski.

**Performans & Ölçeklenebilirlik:** Streamlit single-threaded; çok kullanıcılı senaryolarda bottleneck. Session state memory'de; büyük dataset'lerde şişme riski.

**Hatalar, Eksikler, Teknik Borç:**
- `unsafe_allow_html=True` yaygın kullanımı — XSS riski
- `utils.py` ve `utils_new.py` — eski/yeni çakışması, temizlenmeli
- Demo ve panel arasında kod tekrarı (`views/demo.py` vs `views/dashboard.py`)
- Sayfa yenileme (`st.rerun()`) çok sık çağrılıyor — UX bozukluğu

**Otomasyona Uygunluk:** **Yüksek**

**Önerilen Otomasyon Türü:** UI smoke test otomasyonu, screenshot diff kontrolü, component rendering testleri

**Düzeltme Önerileri:**
- *Kısa vadeli:* `utils.py` / `utils_new.py` birleştir; `unsafe_allow_html` kullanımlarını denetle
- *Orta vadeli:* Streamlit'ten Next.js frontend'e kısmi geçiş (web/ zaten başlanmış)
- *Uzun vadeli:* React tabanlı tam frontend; Streamlit'i internal tool olarak tut

> **Tekrarlama Notu — Frontend:**
> - **Ne nedir:** Streamlit tabanlı 5-tab borsa analiz arayüzü, auth korumalı
> - **Nasıl çalışır:** `streamlit run streamlit_app.py` → session_state ile sayfa yönetimi → views/ modülleri
> - **Nasıl test edilir:** `pytest tests/test_views_smoke.py -v`
> - **Sonraki değerlendirme notu:** `utils_new.py` temizlendi mi? Next.js geçişinin durumu ne?

---

### 3.2 Frontend — Next.js (web/)

**Teknik Tanım:** `web/` klasöründe TypeScript + Next.js uygulaması. `src/app/`, `src/components/`, `src/lib/` yapısı. Vitest test konfigürasyonu var. `monitoring/grafana/` bu klasörde.

**Çalışma Durumu:** ⚠️ Kısmen (bağımsız çalışıyor; backend entegrasyonu belirsiz)

**Fonksiyon Listesi:**
- Modern React/Next.js frontend shell
- Grafana dashboard konfigürasyonu
- API endpoint bağlantıları (lib/ içinde tanımlanmış)

**Kontrol Listesi:**

| Kontrol | Durum | Not |
|---------|-------|-----|
| Health check | ❌ | Next.js health endpoint yok |
| Test | ⚠️ | Vitest config var, test sayısı belirsiz |
| API entegrasyonu | ❌ | FastAPI'ye bağlantı durumu doğrulanmamış |
| CORS | ✅ | `api/main.py`'de localhost:3000 izinli |
| Build | ⚠️ | `out/` klasörü var; static export yapılmış |

**Hatalar, Eksikler:** Streamlit ve Next.js aynı anda maintenance gerektiriyor — iki frontend yükü. Hangisinin primary olduğu netleşmemiş.

**Otomasyona Uygunluk:** **Orta**

**Önerilen Otomasyon Türü:** Playwright e2e testler, API contract validation (OpenAPI → TypeScript type check)

> **Tekrarlama Notu — Next.js Frontend:**
> - **Ne nedir:** İkincil, henüz tam entegre olmamış modern web frontend
> - **Nasıl çalışır:** `cd web && npm run dev` → Next.js dev server → FastAPI'ye bağlanıyor
> - **Nasıl test edilir:** `cd web && npx vitest`
> - **Sonraki değerlendirme notu:** Streamlit mi, Next.js mi? Frontend strateji kararı verilmeli.

---

### 3.3 Backend API — FastAPI

**Teknik Tanım:** `api/main.py` giriş noktası. 6 router: `models`, `inference`, `ensemble`, `optuna`, `scan`, `backtest`. SlowAPI ile rate limiting (60 req/min/IP). JWT auth middleware. CORS yalnızca localhost:3000 ve localhost:8000'e izin veriyor.

**Çalışma Durumu:** ✅ Çalışıyor (backtest router eksik dosya riski hariç)

**Fonksiyon Listesi:**
- `GET /api/v1/health` — health check
- `POST /api/v1/scan` — hisse tarama
- `POST /api/v1/inference` — model inference
- `POST /api/v1/ensemble` — ensemble prediction
- `POST /api/v1/optuna/*` — HP search endpoints
- `GET/POST /api/v1/models/*` — model registry
- `POST /api/v1/backtest/*` — backtesting

**Kontrol Listesi:**

| Kontrol | Durum | Not |
|---------|-------|-----|
| Health check | ✅ | `/api/v1/health` endpoint var |
| Rate limiting | ✅ | SlowAPI, 60/min/IP |
| Auth | ✅ | JWT Bearer token |
| CORS | ⚠️ | Sadece localhost; production domain eklenmeli |
| OpenAPI docs | ✅ | FastAPI otomatik Swagger UI |
| Error handling | ✅ | Exception handler var |
| Logging | ⚠️ | Temel logging; request tracing yok |
| Test coverage | ⚠️ | API endpoint testleri yetersiz |

**Güvenlik & Uyumluluk:**
- JWT `require_auth` ve `optional_auth` dependency injection — iyi tasarım
- CORS whitelist dar — production'da güncellenmeli
- Rate limit yeterli mi? DRL inference endpoint'leri heavy olabilir

**Hatalar, Eksikler:**
- `backtest` router `api/main.py`'de import ediliyor ama `api/routers/backtest.py` dosyasının varlığı CI'da doğrulanmamış
- Request/response logging (OpenTelemetry/tracing) yok
- API versioning yalnızca v1; v2 planı belirsiz

**Otomasyona Uygunluk:** **Yüksek**

**Önerilen Otomasyon Türü:** API contract testing (Schemathesis), endpoint smoke tests, response validation

> **Tekrarlama Notu — FastAPI:**
> - **Ne nedir:** ML modelleri ile frontend arasında köprü kuran REST API
> - **Nasıl çalışır:** `uvicorn api.main:app` → routers → scanner/drl/llm modülleri
> - **Nasıl test edilir:** `curl http://localhost:8000/api/v1/health` + Schemathesis contract test
> - **Sonraki değerlendirme notu:** `backtest.py` router'ı eksik mi? Import kontrolü yap.

---

### 3.4 Veritabanı

**Teknik Tanım:** `auth/database.py`, `auth/db_backend.py`, `auth/portfolio.py`. SQLite (default, `data/finpilot.db`), PostgreSQL (opsiyonel, docker-compose db profili). Alembic migration hazır. `data/finpilot.db` gerçek verilerle dolu.

**Çalışma Durumu:** ⚠️ Kısmen (SQLite çalışıyor; PostgreSQL geçişi tamamlanmamış)

**Fonksiyon Listesi:**
- User CRUD (auth/users.py)
- Session yönetimi
- Scan history kaydı (Sprint 20)
- Signal persistence
- Portfolio tracking
- Waitlist yönetimi

**Kontrol Listesi:**

| Kontrol | Durum | Not |
|---------|-------|-----|
| Migration | ⚠️ | Alembic var; migrate_sqlite_to_pg.py var ama test edilmemiş |
| Backup | ❌ | DB backup stratejisi yok |
| Connection pooling | ❌ | SQLite pooling yok |
| Index | ⚠️ | `pg_init.sql` var; SQLite'ta eksik |
| Test | ✅ | `test_db_backend.py`, `test_db_repos.py` var |
| Parameterized queries | ✅ | String format SQL yok |

**Güvenlik & Uyumluluk:**
- `data/finpilot.db` canlı veritabanı repoya yakın konumda — backup riski
- Parameterized query kullanımı iyi (SQL injection koruması)
- Şifre hash'leme bcrypt ile — yeterli

**Hatalar, Eksikler:**
- SQLite concurrent write limiti production'da sorun çıkarabilir
- `test_auth.db` test veritabanı data/ klasöründe kalmış
- PostgreSQL geçiş script'i test edilmemiş

**Otomasyona Uygunluk:** **Yüksek**

**Önerilen Otomasyon Türü:** DB migration testi, schema validation, backup otomasyonu

> **Tekrarlama Notu — Veritabanı:**
> - **Ne nedir:** SQLite/PostgreSQL dual-mode auth ve sinyal veri deposu
> - **Nasıl çalışır:** SQLAlchemy ORM / db_backend.py → auth/data tablolar → finpilot.db
> - **Nasıl test edilir:** `pytest tests/test_db_backend.py tests/test_db_repos.py -v`
> - **Sonraki değerlendirme notu:** PostgreSQL geçişi ne zaman? `migrate_sqlite_to_pg.py` test edildi mi?

---

### 3.5 Data Pipeline

**Teknik Tanım:** `scanner/data_fetcher.py` (yfinance tabanlı), `drl/feature_pipeline.py` (özellik mühendisliği), `drl/data_loader.py`, `drl/etl/` dizini. `scripts/` altında `altdata.py`, `polygon_live.py`, `regime_detection.py`.

**Çalışma Durumu:** ✅ Çalışıyor (yfinance pipeline)

**Fonksiyon Listesi:**
- `fetch()` — yfinance'den OHLCV çekme
- `add_indicators()` — EMA, RSI, MACD, BB, ATR hesaplama
- `FeaturePipeline` — DRL için özellik tensörü oluşturma
- `FeaturePipelineArtifact` — pipeline serialize/deserialize
- Sektör bazlı sembol listesi yönetimi (1148 NASDAQ sembolü, 11 sektör)

**Kontrol Listesi:**

| Kontrol | Durum | Not |
|---------|-------|-----|
| Timestamp freshness | ⚠️ | 60s stale threshold tanımlanmış ama otomatik kontrol yok |
| NaN/NULL handling | ✅ | `safe_float()` ve try/except korumaları var |
| Rate limiting | ✅ | `drl/rate_limiter.py` var |
| Caching | ⚠️ | `core/cache.py` var; data_fetcher'da kullanımı kısmi |
| Test | ✅ | `test_data_fetcher.py`, `test_feature_generators.py` var |
| Error logging | ✅ | module logger kullanılıyor |

**Güvenlik & Uyumluluk:**
- yfinance ücretsiz API — rate limit ve güvenilirlik riski
- Polygon.io API key `.env`'de — iyi
- Altdata/onchain verileri `broker/onchain.py`'de — testlenmemiş

**Hatalar, Eksikler:**
- yfinance API değişimleri pipeline'ı bozabilir (harici bağımlılık riski)
- ETL klasörü (`drl/etl/`) içeriği belirsiz
- Veri kalitesi otomatik doğrulaması yok (schema validation)

**Otomasyona Uygunluk:** **Yüksek**

**Önerilen Otomasyon Türü:** Veri kalitesi doğrulama (Great Expectations benzeri), timestamp staleness check, pipeline anomaly detection

> **Tekrarlama Notu — Data Pipeline:**
> - **Ne nedir:** yfinance + Polygon.io veri çekme ve özellik mühendisliği katmanı
> - **Nasıl çalışır:** `fetch(symbol, interval, period)` → `add_indicators()` → DRL feature tensörü
> - **Nasıl test edilir:** `pytest tests/test_data_fetcher.py tests/test_feature_generators.py -v`
> - **Sonraki değerlendirme notu:** yfinance API değişiklik takibi yapılıyor mu?

---

### 3.6 Canlı Veri Kaynakları

**Teknik Tanım:** `drl/data_sources/` (async_base, news, onchain, providers), `broker/` (Alpaca), `core/websocket_feeds.py` (real-time WebSocket).

**Çalışma Durumu:** ⚠️ Kısmen (yfinance aktif; WebSocket/Alpaca live feed pasif)

**Fonksiyon Listesi:**
- yfinance: geçmişe dönük ve güncel OHLCV
- Alpaca: paper trading + market data API
- News API: haber verisi (broker/news.py)
- Onchain: blockchain veri (broker/onchain.py)
- WebSocket: gerçek zamanlı fiyat feed (tanımlanmış, aktif değil)

**Güvenlik:**
- API key'ler `.env`'de — iyi
- Alpaca paper trading modu kullanılıyor — production risk düşük

**Hatalar, Eksikler:**
- WebSocket feed production'da aktif değil — roadmap'teki önemli eksik
- Onchain veri kullanımı belirsiz (tam entegre mi?)

**Otomasyona Uygunluk:** **Orta**

**Önerilen Otomasyon Türü:** Canlı veri timestamp doğrulaması, feed health check, staleness alarm

> **Tekrarlama Notu — Canlı Veri:**
> - **Ne nedir:** Çok kaynaklı piyasa veri altyapısı (yfinance, Alpaca, haber, onchain)
> - **Nasıl çalışır:** `data_sources/providers/` → async veri çekme → cache → pipeline
> - **Nasıl test edilir:** `pytest tests/test_websocket_feeds.py -v` + mock API test
> - **Sonraki değerlendirme notu:** WebSocket production activation ne zaman planlanıyor?

---

### 3.7 Dashboard (Streamlit Views)

**Teknik Tanım:** `views/dashboard.py` ana scanner sayfası. 5-tab yapı: Tarama, Sonuçlar, Performans, AI Lab, Ayarlar. `views/components/` içinde reusable bileşenler. `views/scan_history.py` geçmiş taramalar.

**Çalışma Durumu:** ✅ Çalışıyor

**Fonksiyon Listesi:**
- Hisse tarama başlatma/durdurma
- Sinyal sonuçlarını tablo ve kart görünümünde gösterme
- DRL model performans metrikleri
- AI Lab: LLM analiz ve araştırma
- Tarama geçmişi ve favori semboller
- Kullanıcı ayarları paneli

**Kontrol Listesi:**

| Kontrol | Durum | Not |
|---------|-------|-----|
| Component isolation | ✅ | `views/components/` ayrı modüller |
| State management | ⚠️ | `st.session_state` her yerde; global state karmaşıklığı |
| Responsive | ❌ | Streamlit responsive değil; mobil görünüm kötü |
| Error boundaries | ⚠️ | try/except var ama kullanıcıya gösterilen hata mesajları geliştirilmeli |
| i18n | ✅ | `core/i18n.py` + `views/translations.py` |

**Güvenlik & Uyumluluk:**
- `unsafe_allow_html=True` en büyük risk; tüm CSS injection via Streamlit markdown
- Kimlik doğrulaması dashboard seviyesinde korumalı

**Otomasyona Uygunluk:** **Yüksek**

**Önerilen Otomasyon Türü:** Smoke test, screenshot regression test, sinyal doğrulama otomasyonu

> **Tekrarlama Notu — Dashboard:**
> - **Ne nedir:** 5-tab Streamlit paneli; tarama + AI analiz + performans merkezi
> - **Nasıl çalışır:** `views/dashboard.py` → `render_scanner_page()` → component hierarchy
> - **Nasıl test edilir:** `pytest tests/test_views_smoke.py tests/test_views_integration.py -v`
> - **Sonraki değerlendirme notu:** `st.session_state` yönetimi bir `SessionStateManager`'a taşındı mı?

---

### 3.8 API Katmanı

*(FastAPI bölümüne bakınız — §3.3. Bu bölüm router detaylarını kapsar.)*

**Router Envanteri:**

| Router | Endpoint Sayısı | Auth | Durum |
|--------|----------------|------|-------|
| models.py | 4-5 | Opsiyonel | ✅ |
| inference.py | 2-3 | Gerekli | ✅ |
| ensemble.py | 2 | Gerekli | ✅ |
| optuna.py | 3 | Gerekli | ✅ |
| scan.py | 2-3 | Gerekli | ✅ |
| backtest.py | 2-3 | Gerekli | ⚠️ |

**Otomasyona Uygunluk:** **Yüksek**

**Önerilen Otomasyon Türü:** OpenAPI/Schemathesis contract test, endpoint performance benchmark

> **Tekrarlama Notu — API Katmanı:**
> - **Ne nedir:** FastAPI tabanlı 6 router, JWT auth, rate limiting
> - **Nasıl çalışır:** `uvicorn api.main:app --reload` → Swagger UI: `/docs`
> - **Nasıl test edilir:** `pytest tests/ -k api` + `curl /api/v1/health`
> - **Sonraki değerlendirme notu:** backtest router'ın dosya varlığını doğrula.

---

### 3.9 Auth & Güvenlik

**Teknik Tanım:** `auth/` modülü: `core.py` (JWT config), `tokens.py` (JWTHandler), `users.py` (PasswordHasher, User, UserRole), `sessions.py` (Session), `database.py` (User DB), `db_backend.py` (repository pattern), `streamlit_session.py` (Streamlit session manager).

**Çalışma Durumu:** ✅ Çalışıyor

**Fonksiyon Listesi:**
- JWT access + refresh token çifti
- bcrypt şifre hash'leme
- Kullanıcı rolleri (admin, user, demo)
- Session management (Streamlit state)
- `require_auth` / `optional_auth` FastAPI dependencies
- Development fallback key (hostname bazlı — production risk)

**Kontrol Listesi:**

| Kontrol | Durum | Not |
|---------|-------|-----|
| Token expiry | ✅ | Tanımlanmış (varsayılan config) |
| Refresh token | ✅ | `tokens.py`'de implement |
| Password hashing | ✅ | bcrypt |
| Secret key rotation | ❌ | Key rotation mekanizması yok |
| Brute-force protection | ⚠️ | Rate limiter var ama login-specific değil |
| Audit logging | ✅ | `core/audit.py` ile user action logging |
| Dev fallback | ⚠️ | Hostname-based dev key — production'da asla setlenmemeli |

**Güvenlik & Uyumluluk:**
- JWT algorithm: HS256 (simetrik) — asymmetric (RS256) daha güvenli olurdu
- `FINPILOT_SECRET_KEY` set edilmezse hostname-based key kullanılıyor — production hazırlık eksikliği
- `.env` dosyası repoda mevcut (`.gitignore`'da var ama gerçek değerlerle olması risk)

**Otomasyona Uygunluk:** **Orta**

**Önerilen Otomasyon Türü:** Auth endpoint security test (OWASP), token expiry validation, permission boundary test

> **Tekrarlama Notu — Auth:**
> - **Ne nedir:** JWT tabanlı kullanıcı kimlik doğrulama ve yetkilendirme sistemi
> - **Nasıl çalışır:** `auth/core.py` → JWT + bcrypt → `auth/database.py` → session state
> - **Nasıl test edilir:** `pytest tests/test_auth.py -v`
> - **Sonraki değerlendirme notu:** RS256'ya geçiş planı var mı? Key rotation?

---

### 3.10 MPC / Broker Modülleri

**Teknik Tanım:** `broker/` modülü: `__init__.py`, `async_base.py`, `base.py`, `exceptions.py`, `news.py`, `onchain.py`, `providers/`. Alpaca paper trading entegrasyonu (Sprint 21). `scripts/paper_trading.py`, `scripts/auto_scan_trade.py`.

**Çalışma Durumu:** ⚠️ Kısmen (paper trading için temel yapı var; production trading için hazır değil)

**Fonksiyon Listesi:**
- Alpaca paper trading API bağlantısı
- Order submission (alım/satım emri)
- Haber verisi çekme
- Onchain veri sağlayıcı (DeFi)
- Async provider base class

**Kontrol Listesi:**

| Kontrol | Durum | Not |
|---------|-------|-----|
| Paper trading | ✅ | Alpaca paper mode |
| Live trading | ❌ | Gerçek para ile trade — KESİNLİKLE hazır değil |
| Order validation | ⚠️ | PilotShield risk kontrolleri var (DRL tarafında) |
| Error handling | ⚠️ | `broker/exceptions.py` var; comprehensive değil |
| Test | ✅ | `tests/test_broker.py` var |

**Güvenlik & Uyumluluk:**
- Alpaca API key'leri `.env`'de — iyi
- Live trading için ek güvenlik katmanları gerekli
- Order size limitleri tanımlanmamış

**Otomasyona Uygunluk:** **Düşük** (finansal işlem hassasiyeti nedeniyle insan onayı şart)

**Önerilen Otomasyon Türü:** Paper trading simülasyon testi, order validation, risk limit kontrolü (human-in-the-loop)

> **Tekrarlama Notu — Broker:**
> - **Ne nedir:** Alpaca tabanlı paper trading ve haber/onchain veri sağlayıcı
> - **Nasıl çalışır:** `broker/base.py` → Alpaca REST/WS API → order management
> - **Nasıl test edilir:** `pytest tests/test_broker.py -v` + Alpaca sandbox
> - **Sonraki değerlendirme notu:** Live trading için ne gerekli? PilotShield entegrasyonu tam mı?

---

### 3.11 ML/Agent Modülleri

**Teknik Tanım:**
- **DRL:** `drl/` — 20+ modül. `market_env.py` (Gymnasium env), `training.py` (walk-forward), `optuna_search.py`, `model_registry.py`, `ensemble_router.py`, `hybrid_engine.py`, `specialists.py`. Algorithms: PPO, SAC, TD3, A2C (SB3).
- **LLM:** `llm/` — `router.py` (Groq→Claude→Gemini failover), `groq_provider.py`, `claude_provider.py`, `gemini_provider.py`, `base.py`.

**Çalışma Durumu:** ⚠️ Kısmen (LLM router ✅; DRL modeller ZIP artifact'ları yoksa ⚠️)

**Fonksiyon Listesi (DRL):**
- Walk-forward training (out-of-sample validation)
- Gymnasium-compatible trading environment
- PilotShield risk kontrolleri (max drawdown, position limit)
- Optuna HPO (30+ trial, SQLite/PostgreSQL backend)
- Ensemble routing (regime-weighted)
- Model registry ve versioning
- MLflow tracking (opsiyonel)
- Feature importance / explainability

**Fonksiyon Listesi (LLM):**
- Multi-provider failover (Groq → Claude → Gemini)
- Per-provider latency ve error rate tracking
- Streaming token desteği
- System prompt yönetimi
- Senior financial analyst persona

**Kontrol Listesi:**

| Kontrol | Durum | Not |
|---------|-------|-----|
| Model artifacts | ⚠️ | `models/` klasörü; ZIP yoksa inference çalışmaz |
| Training reproducibility | ✅ | Walk-forward + seed kontrolü |
| Inference latency | ⚠️ | Ölçülmüyor; heavy model ~2-5s |
| LLM failover | ✅ | 3 provider, auto-disable on auth error |
| Test coverage (DRL) | ✅ | `test_drl_integration.py` 478 satır |
| MLflow | ⚠️ | Opsiyonel; production'da tracking yok |

**Güvenlik & Uyumluluk:**
- LLM output sanitization yok — financial advice injection riski
- DRL modeller `models/` klasörüne kaydediliyor; file permission kontrolü yok
- Optuna SQLite backend concurrent access sorunu olabilir

**Otomasyona Uygunluk:** **Orta**

**Önerilen Otomasyon Türü:** Model validation pipeline, LLM output quality check, inference smoke test, Optuna study monitoring

> **Tekrarlama Notu — ML/Agent:**
> - **Ne nedir:** PPO/SAC/TD3 DRL ajanları + Groq/Claude/Gemini LLM router
> - **Nasıl çalışır:** `drl/training.py` → `MarketEnv` → SB3 training → `model_registry.py`; `llm/router.py` → provider chain
> - **Nasıl test edilir:** `pytest tests/test_drl_integration.py tests/test_llm.py -v`
> - **Sonraki değerlendirme notu:** Güncel model artifacts `models/` klasöründe var mı? MLflow tracking aktif mi?

---

### 3.12 Scheduler / Cron

**Teknik Tanım:** `apscheduler>=3.10` requirements'ta mevcut. `scripts/daily_inference.py`, `scripts/daily_paper_trading.py`, `scripts/weekly_paper_trading_report.py`, `scripts/retrain_models.py`. APScheduler'ın uygulama içi entegrasyonu tam değil; betikler manuel çalıştırılıyor.

**Çalışma Durumu:** ⚠️ Kısmen (betikler var; otomatik zamanlama entegre değil)

**Fonksiyon Listesi:**
- Günlük inference çalıştırma
- Günlük paper trading
- Haftalık raporlama
- Model retraining scheduler

**Kontrol Listesi:**

| Kontrol | Durum | Not |
|---------|-------|-----|
| APScheduler entegrasyonu | ❌ | Betikler manuel; scheduler uygulamaya bağlı değil |
| Job persistence | ❌ | Job state kaydedilmiyor |
| Error recovery | ❌ | Başarısız job retry yok |
| Monitoring | ❌ | Job run/fail metrikleri yok |
| Test | ⚠️ | Scheduler testleri yok |

**Otomasyona Uygunluk:** **Çok Yüksek**

**Önerilen Otomasyon Türü:** Claude Co-worker Scheduled Tasks ile tam entegrasyon, cron job monitoring, job failure alerting

> **Tekrarlama Notu — Scheduler:**
> - **Ne nedir:** Günlük/haftalık analiz ve trading betikleri; APScheduler altyapısı var ama entegre değil
> - **Nasıl çalışır:** Manuel: `python scripts/daily_inference.py` — otomatik: YOK
> - **Nasıl test edilir:** Betikleri manuel çalıştır, çıktıları doğrula
> - **Sonraki değerlendirme notu:** APScheduler integration bu hafta yapılabilecek en hızlı kazanım!

---

### 3.13 Monitoring & Logging

**Teknik Tanım:** `core/monitoring.py` (Sentry + Prometheus client + health check + performance tracker), `core/audit.py` (JSON audit log, async write, rotation), `core/prometheus_exporter.py` (HTTP metrics endpoint), `core/logging.py` (structured logging via structlog), `monitoring/grafana/` (Grafana dashboard config).

**Çalışma Durumu:** ✅ Çalışıyor (altyapı hazır; production'da tam aktive edilmesi gerekiyor)

**Fonksiyon Listesi:**
- Sentry error tracking (SENTRY_DSN env ile aktive)
- Prometheus metrikleri (sinyal sayısı, tarama süresi, LLM latency)
- Health check endpoint
- Async audit log (JSON, rotasyonlu)
- Structured logging (structlog)
- Performance decorator (`@track_performance`)
- Grafana dashboard (monitoring/ klasöründe)

**Kontrol Listesi:**

| Kontrol | Durum | Not |
|---------|-------|-----|
| Error tracking | ✅ | Sentry entegre (DSN gerekli) |
| Metrics | ✅ | Prometheus client, custom metrics |
| Alerting | ❌ | Alert thresholds tanımlanmamış |
| Log retention | ⚠️ | Rotation var; merkezi log aggregation yok |
| Distributed tracing | ❌ | OpenTelemetry yok |
| Grafana | ✅ | Config dosyaları var; aktive edilmeli |
| Test | ✅ | `test_prometheus.py` 446 satır |

**Güvenlik & Uyumluluk:**
- Sentry PII leakage riski — financial data Sentry'ye gönderilmemeli
- Prometheus endpoint `/metrics` herkese açık — auth eklenmeli

**Otomasyona Uygunluk:** **Yüksek**

**Önerilen Otomasyon Türü:** Log anomaly detection, alert threshold otomasyonu, health check raporu, metric trending

> **Tekrarlama Notu — Monitoring:**
> - **Ne nedir:** Sentry + Prometheus + strukturlu JSON audit log + Grafana stack
> - **Nasıl çalışır:** `from core.monitoring import metrics, sentry_client` → uygulama genelinde kullanım
> - **Nasıl test edilir:** `pytest tests/test_prometheus.py tests/test_sentry.py -v`
> - **Sonraki değerlendirme notu:** Grafana production'da aktive edildi mi? SENTRY_DSN setlendi mi?

---

### 3.14 Deployment & CI/CD

**Teknik Tanım:** `Dockerfile` (multi-stage: base, development, production), `docker-compose.yml` (5 servis: app, scanner, telegram, redis, postgres; profil tabanlı), `.github/workflows/ci.yml` (5 job: test, lint, security, docker, scanner-integration, drl-pipeline), `Makefile`, `.pre-commit-config.yaml`.

**Çalışma Durumu:** ✅ Çalışıyor

**Fonksiyon Listesi:**
- Multi-stage Docker build
- Docker Compose profil sistemi (scanner/telegram/cache/db opsiyonel)
- GitHub Actions: test (coverage ≥50%), lint (Ruff), security (Bandit+Safety+secret scan), Docker smoke test
- Pre-commit hooks (Ruff, detect-secrets, trailing whitespace)
- DRL pipeline job (main branch'te)

**Kontrol Listesi:**

| Kontrol | Durum | Not |
|---------|-------|-----|
| CI pipeline | ✅ | 5 job, paralel çalışma |
| Test coverage threshold | ⚠️ | %50 threshold — düşük |
| Secret scanning | ✅ | detect-secrets + git grep |
| Docker healthcheck | ✅ | `/_stcore/health` 30s interval |
| Deployment automation | ❌ | CD yok; sadece CI |
| Rollback plan | ❌ | Otomatik rollback yok |
| Staging environment | ❌ | Staging ortamı yok |

**Güvenlik & Uyumluluk:**
- Secret scanning aktif — iyi
- Bandit/Safety `continue-on-error: true` — güvenlik hataları CI'ı kırmıyor (risk!)
- `GROQ_API_KEY` CI secret olarak tanımlanmış

**Otomasyona Uygunluk:** **Yüksek**

**Önerilen Otomasyon Türü:** CD pipeline tamamlama, staging deploy otomasyonu, coverage enforcement yükseltme (%70+)

> **Tekrarlama Notu — CI/CD:**
> - **Ne nedir:** GitHub Actions 5-job pipeline + Docker multi-stage + pre-commit
> - **Nasıl çalışır:** Push → test+lint+security parallel → docker build → scanner integration
> - **Nasıl test edilir:** `make test && make lint && make docker-build`
> - **Sonraki değerlendirme notu:** CD pipeline ne zaman? Coverage threshold %70'e çıkarılsın.

---

### 3.15 Üçüncü Taraf Servisler

| Servis | Kullanım | Auth | Durum |
|--------|---------|------|-------|
| yfinance | Piyasa verisi | API key yok (ücretsiz) | ✅ |
| Groq | LLM inference | GROQ_API_KEY | ✅ |
| Anthropic Claude | LLM fallback | GOOGLE_API_KEY | ✅ |
| Google Gemini | LLM fallback | GOOGLE_API_KEY | ✅ |
| Alpaca | Paper trading | ALPACA_API_KEY + SECRET | ⚠️ |
| Telegram | Bildirim | TELEGRAM_BOT_TOKEN + CHAT_ID | ✅ |
| Polygon.io | Premium veri | POLYGON_API_KEY | ⚠️ |
| News API | Haber | NEWS_API_KEY | ⚠️ |
| Sentry | Error tracking | SENTRY_DSN | ⚠️ |
| MLflow | ML tracking | MLFLOW_TRACKING_URI | ⚠️ |
| Redis | Cache | REDIS_URL | ⚠️ |
| Tavily | Web search | (requirements'ta) | ❓ |

**Hatalar, Eksikler:**
- yfinance dependency — ücretsiz ama güvenilmez; rate limit ve API değişim riski
- 12 farklı üçüncü taraf servis — entegrasyon karmaşıklığı yüksek
- Birçok servis opsiyonel ama fallback kodu yetersiz

**Otomasyona Uygunluk:** **Orta**

**Önerilen Otomasyon Türü:** API health monitoring, rate limit alerting, service dependency check

> **Tekrarlama Notu — 3rd Party:**
> - **Ne nedir:** 12 harici servis (LLM, veri, trading, monitoring, iletişim)
> - **Nasıl çalışır:** `.env` API key'leri → provider class'ları → failover logic
> - **Nasıl test edilir:** Her provider için mock test + entegrasyon test
> - **Sonraki değerlendirme notu:** Hangi servisler production'da kritik path üzerinde? SLA'ları var mı?

---

### 3.16 Konfigürasyon & Secrets Yönetimi

**Teknik Tanım:** `.env` (python-dotenv), `.env.example` (template), `core/config.py` (pydantic-settings), `user_settings.json`, `.pre-commit-config.yaml` (detect-secrets), `.secrets.baseline`.

**Çalışma Durumu:** ✅ Çalışıyor

**Fonksiyon Listesi:**
- `.env` ile tüm API key yönetimi
- `pydantic-settings` ile tip-güvenli config
- `user_settings.json` ile kullanıcı bazlı ayarlar
- detect-secrets baseline ile secret sızma koruması
- Dev ortamda hostname-based fallback key

**Güvenlik:**
- `.env` `.gitignore`'da — iyi
- Gerçek `.env` dosyası repoda var (ancak gerçek değerler kontrol edilmeli)
- `detect-secrets` baseline eski olabilir

**Otomasyona Uygunluk:** **Orta**

**Önerilen Otomasyon Türü:** Secret rotation reminder, config drift detection, `.secrets.baseline` güncelleme otomasyonu

> **Tekrarlama Notu — Config & Secrets:**
> - **Ne nedir:** dotenv + pydantic-settings + detect-secrets tabanlı güvenli config yönetimi
> - **Nasıl çalışır:** `.env` → `os.getenv()` / `pydantic BaseSettings` → uygulama config'i
> - **Nasıl test edilir:** `detect-secrets scan --baseline .secrets.baseline`
> - **Sonraki değerlendirme notu:** `.secrets.baseline` son ne zaman güncellendi? API key rotation planı?

---

## 4. Claude Co-worker Entegrasyon Analizi

### 4.1 Hangi Bölümler Bağlanabilir?

| Bölüm | Bağlantı Türü | Erişim Seviyesi |
|-------|--------------|-----------------|
| `scanner/` | Doğrudan dosya okuma + test çalıştırma | Yüksek |
| `tests/` | Test çalıştırma + sonuç analizi | Yüksek |
| `drl/` | Model metadata okuma + training log analizi | Orta |
| `api/` | Endpoint test + OpenAPI doğrulama | Yüksek |
| `logs/` | Log analizi + anomali tespiti | Yüksek |
| `data/` | Scan sonuçları + Optuna CSV analizi | Yüksek |
| `.github/workflows/` | CI/CD analizi + badge durumu | Orta |
| `core/monitoring.py` | Health check raporu oluşturma | Yüksek |
| `requirements.txt` | Bağımlılık güvenlik taraması | Yüksek |
| `scripts/` | Betik çalıştırma ve doğrulama | Orta |

### 4.2 Hangi Görevler Tamamen Otomatikleştirilebilir?

- ✅ Test suite çalıştırma ve başarısız testlerin raporlanması
- ✅ Kod lint kontrolü (Ruff/mypy çalıştırma)
- ✅ Log dosyası analizi ve anomali tespiti
- ✅ Dependency güvenlik taraması (`safety check`)
- ✅ OpenAPI endpoint envanteri çıkarma
- ✅ Dokümantasyon üretme (modül bazlı)
- ✅ Scan sonuçlarının CSV analizini rapor haline getirme
- ✅ Optuna sonuç CSV'lerinin analizi
- ✅ Günlük sistem sağlık raporu

### 4.3 Hangi Görevler Yarı Otomatik Olmalı? (Human-in-the-Loop)

- ⚡ Kod düzeltme önerileri → insan onayı sonrası commit
- ⚡ DRL model retraining → parametreler doğrulandıktan sonra
- ⚡ API key rotasyonu → insan onayı şart
- ⚡ Veritabanı migration → her zaman insan onayı
- ⚡ Trading sinyali gönderme → kritik finansal karar
- ⚡ Docker deployment → staging sonrası insan onayı

### 4.4 Claude'un Erişmesi Gereken Dosya ve Klasörler

```
# Birincil erişim (salt okunur analiz)
scanner/          # Indicator ve signal logik
drl/              # Model config ve training sonuçları
api/              # Endpoint tanımları
tests/            # Test coverage ve başarı durumu
data/             # Scan geçmişi, Optuna sonuçları
logs/             # Runtime logları
core/             # Config ve monitoring
.github/workflows/ # CI/CD durumu

# İkincil erişim (raporlama)
requirements.txt   # Bağımlılık analizi
pyproject.toml     # Lint/test konfigürasyonu
wfo_grid_search_results.csv # Model performans geçmişi
```

### 4.5 Claude'un Üstlenebileceği Roller

| Rol | Açıklama | Öncelik |
|-----|----------|---------|
| **Kod Analisti** | PR review, refactoring önerileri, teknik borç tespiti | 🔴 Yüksek |
| **Test Otomasyon Botu** | Test üretme, coverage artırma, edge case tespiti | 🔴 Yüksek |
| **Pipeline Doğrulayıcı** | Data freshness, NaN kontrolü, model artifact varlığı | 🔴 Yüksek |
| **Dokümantasyon Üreticisi** | Modül docstring tamamlama, README güncelleme | 🟡 Orta |
| **Log Analist** | Günlük log tarama, anomali raporu | 🟡 Orta |
| **Güvenlik Denetçisi** | Bandit/Safety çalıştırma, secret tarama | 🔴 Yüksek |
| **Raporlama Botu** | Günlük/haftalık sistem durumu raporu | 🟡 Orta |

---

## 5. Otomasyon Fırsatları Haritası

### 5.1 Kod İnceleme Otomasyonu
```
Fırsat: Her commit'te Claude otomatik kod incelemesi yapabilir
Hedef dosyalar: scanner/, drl/, api/, auth/
Öncelik: 🔴 Yüksek
Araçlar: Ruff + mypy + bandit + özel prompt şablonları
```

### 5.2 Test Üretimi
```
Fırsat: Düşük coverage'lı modüller için test üretimi
Hedef: api/routers/, views/, broker/ (coverage <60%)
Öncelik: 🔴 Yüksek
Araçlar: pytest + coverage.xml analizi + Claude test yazımı
```

### 5.3 API Contract Doğrulama
```
Fırsat: FastAPI OpenAPI şeması → TS tiplerini doğrula
Araçlar: Schemathesis, openapi-to-typescript
Öncelik: 🟡 Orta
```

### 5.4 Dashboard Veri Doğrulama
```
Fırsat: Scan sonuçlarındaki verilerin tutarlılık kontrolü
Hedef: data/shortlists/*.csv, data/suggestions/*.csv
Öncelik: 🟡 Orta
Araçlar: pandas validation + schema check
```

### 5.5 Canlı Veri Timestamp Kontrolü
```
Fırsat: yfinance verilerinin tazelik kontrolü (<60s threshold)
Öncelik: 🔴 Yüksek
Araçlar: timestamp comparison + alert (Telegram bildirimi)
```

### 5.6 Log Analizi
```
Fırsat: logs/ klasöründeki hata pattern tespiti
Hedef: finpilot*.log, audit*.jsonl
Öncelik: 🟡 Orta
Araçlar: regex pattern matching + anomaly summary
```

### 5.7 Pipeline Anomaly Detection
```
Fırsat: Optuna sonuçları, walk-forward metrikler anomali tespiti
Hedef: wfo_grid_search_results.csv, data/optuna_*.json
Öncelik: 🟡 Orta
Araçlar: statistical threshold + trend analysis
```

### 5.8 Dokümantasyon Üretimi
```
Fırsat: Eksik/yetersiz docstring'lerin otomatik tamamlanması
Hedef: drl/, api/, core/ modülleri
Öncelik: 🟢 Düşük
Araçlar: AST analizi + Claude docstring üretimi
```

### 5.9 Prompt Şablonları
```
Şablon listesi:
- "Günlük sistem sağlık raporu: [modül] durumu nedir?"
- "Bu scan sonuçlarında anomali var mı? [CSV içeriği]"
- "Bu log dosyasındaki hata pattern'ini özetle: [log]"
- "Bu test coverage raporuna göre öncelikli test ne yazılmalı?"
- "API endpoint [X]'in contract'ı OpenAPI spec'e uygun mu?"
```

### 5.10 Raporlama Otomasyonu
```
Fırsat: Günlük/haftalık PDF/Markdown rapor üretimi
Araçlar: core/monitoring.py + reportlab + Claude analizi
Öncelik: 🟡 Orta
```

---

## 6. Riskler ve Engeller

### 6.1 Güvenlik Riskleri

| Risk | Severity | Açıklama |
|------|---------|----------|
| Production secret key | 🔴 Kritik | `FINPILOT_SECRET_KEY` set edilmezse hostname-based key kullanılıyor |
| unsafe_allow_html | 🔴 Yüksek | Streamlit XSS vektörü |
| Prometheus endpoint | 🟡 Orta | `/metrics` endpoint'i auth gerektirmiyor |
| JWT HS256 | 🟡 Orta | Simetrik algoritma; RS256 daha güvenli |
| Bandit continue-on-error | 🟡 Orta | Güvenlik hataları CI'ı kırkmıyor |
| .env dosyası | 🟡 Orta | Gerçek API key'lerin repoda bulunma riski |

### 6.2 Veri Gizliliği

- Sentry'ye finansal veri gönderimi riski (before_send hook eklenmeli)
- Kullanıcı tarama geçmişi SQLite'da — şifreleme yok
- Audit log'lar rotasyonlu ama merkezi değil — uzun vadeli saklaması belirsiz
- Alpaca paper trading hesabı gerçek olmasa da kullanıcı data'sı bulut servise gidiyor

### 6.3 Yanlış Otomasyon Sonucu Oluşabilecek Hatalar

- **DRL model yanlış seçimi:** Otomatik model deployment kritik kayıplara yol açabilir
- **Yanlış sinyal üretimi:** Telegram bildirimlerinin yanlış otomatik gönderimi
- **DB migration hatası:** Otomatik çalıştırılan migration geri alınamaz veri kaybına yol açabilir
- **API key rotasyonu:** Yanlış zamanlama tüm sistemi duraksatabilir
- **Scanner aggressive mode:** Otomatik tetikleme API rate limit'e çarpabilir

### 6.4 Claude'un Erişim Sınırları

- Gerçek finansal işlem kararları → Her zaman human-in-the-loop
- Production database üzerinde yazma işlemleri → Onay gerekli
- API key yönetimi → Claude asla key'lere erişmemeli
- Telegram bot üzerinden kullanıcılara mesaj gönderme → Onay gerekli
- Docker deployment → Staging validation sonrası onay

---

## 7. 2 Haftalık Otomasyon Yol Haritası

### ⚡ 48 Saat — Hızlı Kazanımlar

| Görev | Süre | Öncelik | Kabul Kriteri |
|-------|------|---------|---------------|
| Claude Co-worker folder erişimi ve proje haritası | 2s | 🔴 P0 | Tüm modüller listelendi |
| Mevcut test suite çalıştırma + başarısız test raporu | 1s | 🔴 P0 | Coverage raporu üretildi |
| Log anomali tarama (son 7 gün) | 1s | 🔴 P0 | Top-5 hata pattern tespit edildi |
| `requirements.txt` güvenlik taraması | 1s | 🔴 P0 | Vulnerable package listesi |
| API endpoint envanteri (OpenAPI parse) | 2s | 🟡 P1 | Tüm endpoint'ler dokümante edildi |

### 1. Hafta — Temel Otomasyonlar

| Görev | Süre | Öncelik | Sorumlu | Kabul Kriteri |
|-------|------|---------|---------|---------------|
| Günlük sistem sağlık raporu | 1 gün | 🔴 P0 | Claude (scheduled) | Her gün 09:00'da health raporu |
| Test coverage artırma (api/ + broker/) | 2 gün | 🔴 P0 | Claude + insan onayı | Coverage %60'a çıktı |
| Canlı veri timestamp kontrolü | 1 gün | 🔴 P0 | Claude | <60s threshold alarm |
| APScheduler entegrasyonu | 2 gün | 🟡 P1 | Claude (öneri) + dev onayı | daily_inference.py schedule edildi |
| Secret key production check | 0.5 gün | 🔴 P0 | Claude + dev | FINPILOT_SECRET_KEY validation |

### 1. Hafta — İleri Seviye Otomasyonlar

| Görev | Süre | Öncelik | Sorumlu | Kabul Kriteri |
|-------|------|---------|---------|---------------|
| Kod inceleme prompt şablonları | 1 gün | 🟡 P1 | Claude | 5 şablon hazır ve test edildi |
| API contract test otomasyonu | 1.5 gün | 🟡 P1 | Claude | Schemathesis çalışıyor |
| Data pipeline kalite kontrolü | 1 gün | 🟡 P1 | Claude | NaN/timestamp alertler aktif |
| Log analizi otomasyonu | 1 gün | 🟡 P1 | Claude | Günlük anomali özeti |
| Optuna sonuç trend analizi | 0.5 gün | 🟢 P2 | Claude | Haftalık model perf raporu |
| Dokümantasyon eksikleri tespiti | 0.5 gün | 🟢 P2 | Claude | Eksik docstring listesi |
| `backtest.py` router dosyasını doğrula/oluştur | 1 gün | 🔴 P0 | Dev + Claude | Import hatası giderildi |
| CI coverage threshold %70'e çıkar | 0.5 gün | 🟡 P1 | Claude (öneri) + dev | CI `--cov-fail-under=70` |

---

## 8. Executive Summary

### Projenin Genel Durumu

**FinPilot** Sprint 22 itibarıyla fonksiyonel bir MVP seviyesine ulaşmıştır. Temel bileşenler (scanner, LLM router, auth, monitoring) stabil çalışmaktadır. Proje, karmaşık bir teknik stack'e (Streamlit + FastAPI + DRL + LLM + Docker + PostgreSQL) sahip olmakla birlikte, scheduler entegrasyonu, frontend geçişi (Streamlit → Next.js) ve production hardening tamamlanmamıştır.

**Test coverage %50 threshold** — production için yetersiz. **SQLite → PostgreSQL geçişi** kritik darboğaz. **WebSocket real-time feed** devre dışı. **CD pipeline** (Continuous Deployment) eksik.

### En Büyük 3 Otomasyon Fırsatı

1. **🥇 Scheduler Entegrasyonu:** `scripts/daily_inference.py`, `scripts/retrain_models.py` gibi betikler APScheduler veya Claude Co-worker Scheduled Tasks ile tam otomatik hale getirilebilir. Günlük analiz, model validation ve raporlama insan müdahalesi gerektirmeden çalışabilir.

2. **🥈 Test & Kalite Güvencesi:** API, broker ve views modüllerinin test coverage'ı düşük. Claude, eksik test case'leri üretebilir, coverage raporlarını analiz edebilir ve CI threshold'ı otomatik olarak izleyebilir. Bu, en yüksek ROI'ye sahip otomasyon fırsatıdır.

3. **🥉 Günlük Sistem Sağlık Raporu:** Monitoring altyapısı (Prometheus + Sentry + audit log) mevcut ama raporlama yoktur. Claude her sabah logları, test sonuçlarını, API sağlığını ve data pipeline tazeliğini analiz ederek günlük bir Markdown/PDF rapor üretebilir.

### En Kritik 3 Eksik

1. **🚨 Production Secret Key:** `FINPILOT_SECRET_KEY` set edilmezse hostname-based fallback devreye giriyor. Production deployment öncesi **zorunlu** düzeltme.

2. **🚨 CD Pipeline Eksikliği:** CI var, CD yok. Staging ortamı tanımlanmamış, otomatik rollback mekanizması yok. Production deploy tamamen manueldir.

3. **🚨 SQLite → PostgreSQL Geçişi:** `migrate_sqlite_to_pg.py` var ama test edilmemiş. Concurrent write ve veri bütünlüğü riski taşıyan SQLite'ın production'da devam etmesi kabul edilemez.

### Claude Co-worker Entegrasyonu için Önerilen İlk Adım

```
1. Bu klasörü Claude Co-worker'a bağla (✅ Zaten bağlı)
2. Günlük health check scheduled task'ı oluştur:
   - Her sabah 08:00'da çalışsın
   - pytest çalıştır, sonuçları özetle
   - data/ klasöründeki scan sonuçlarını kontrol et
   - logs/ anomalilerini raporla
   - Telegram ile günlük özet gönder
3. Test coverage artırma kampanyası başlat:
   - Claude, api/routers/ için test taslakları üretsin
   - Dev onayı sonrası tests/ klasörüne eklensin
4. backtest.py router'ını doğrula (kritik ImportError riski)
```

---

*📋 Bu rapor FinPilot projesinin 2026-03-26 tarihi itibarıyla anlık durumunu yansıtmaktadır. Proje aktif geliştirildiğinden bazı bilgiler hızla güncellenebilir. Bir sonraki değerlendirme önerileri her bölüm sonundaki "Tekrarlama Notu" başlıklarında bulunmaktadır.*
