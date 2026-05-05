# FinPilot Proje İncelemesi ve Bölüm Bazlı Denetim

**Denetim tarihi:** 16 Nisan 2026
**Analiz tipi:** Repo-bazlı + lokal runtime + log + statik CI/doküman incelemesi
**Kapsam:** Frontend, backend, auth, veri hattı, DRL/ML, LLM, gözlemlenebilirlik, CI/infra, legacy yüzeyler

## Girdi Özeti

| Alan | Değer |
|------|-------|
| **Proje adı** | FinPilot |
| **Kısa özet** | FinPilot, trader ve yatırımcılar için teknik analiz, DRL tabanlı modelleme ve LLM destekli açıklama üreten bir analiz platformudur. Kod tabanı modernleşerek Next.js + FastAPI mimarisine geçmiş görünmektedir; ancak dokümantasyon, CI ve legacy Streamlit yüzeyi hâlâ eski mimarinin izlerini taşımaktadır. Lokal ortamda ana uygulama çalışmaktadır, ancak üretim hazırlığı açısından belirgin sözleşme ve kurulum boşlukları vardır. |
| **Mevcut en büyük 3 sorun** | 1) Mimari drift: çalışan sistem ile README, OpenAPI, Docker ve CI aynı şeyi anlatmıyor. 2) Kurulum zinciri kararsız: `requirements.txt` ile temiz kurulum doğrulanamadı. 3) Güvenlik ve işletim kontrolü eksik: JWT dokümante edilmiş ama API route'larında uygulanmıyor; readiness/metrics canlı uygulamada yok. |
| **Erişimler** | Repo erişimi var. Lokal runtime erişimi var. Lokal log erişimi var (`logs/api.log`, `logs/web.log`). CI için yalnızca workflow dosyası görüldü; canlı CI sonucu ve prod infra linki yok. Bu nedenle inceleme kısmen doküman-bazlıdır. |
| **İletişim ve sorumlular** | Kod tabanı ve yatırım dokümanları solo-founder yapısına işaret ediyor. Varsayılan sorumlu: **Ibrahim Meriç Başak** (kurucu, doğrulanmalı). Rol bazlı sahiplikler bu raporda öneri olarak atanmıştır. |
| **Opsiyonel metrikler** | Lokal health: frontend `200`, API `200`. Python test envanteri: `497` test toplandı. Frontend test dosyası: `1` aktif test dosyası. Frontend build: başarılı. |

## Yöntem ve Kanıtlar

- Kod ve yapı incelemesi: `README.md`, `start.sh`, `docker-compose.yml`, `api/main.py`, `web/package.json`, `web/next.config.ts`, `requirements.txt`, `pyproject.toml`
- Dokümanlar: `docs/FINPILOT_EVOLUTION_TIMELINE.md`, `docs/CRITICAL_ROADMAP.md`, `docs/api/openapi.yaml`
- Lokal doğrulama: `bash start.sh`, `curl http://localhost:8000/api/v1/health`, `curl -I http://localhost:3001`
- Test doğrulaması: `python3 -m pytest ...`, `npm run build`, `npx vitest run --pool=threads`
- Log incelemesi: `logs/api.log`, `logs/web.log`

---

## 1. Proje Tarihçesi ve Yol Haritası

FinPilot, 2024 sonunda basit bir Streamlit MVP olarak başlamış, ardından teknik analiz ve scanner katmanı eklenmiş, 2025 sonunda DRL ve model registry ile daha ciddi bir quant/ML platformuna evrilmiştir. 2026 başında backtest motoru ve auth modülü eklenmiş, 2026 Mart-Nisan döneminde ise Next.js + FastAPI geçişiyle ürün yüzeyi modernleştirilmiş görünmektedir. Aynı zaman diliminde yatırım hazırlıkları ve aws Gründungsfonds başvurusu için finansal plan/pitch deck üretimi yapılmıştır.

### Kronolojik Özet

| Dönem | Faz | Kilometre Taşı | Kanıt |
|------|-----|----------------|-------|
| Q4 2024 | Phase 1 | Streamlit tabanlı MVP, temel veri çekme ve grafikleme | `docs/FINPILOT_EVOLUTION_TIMELINE.md` |
| Q4 2024 - Q1 2025 | Phase 2 | Scanner, teknik göstergeler, sinyal üretimi | `scanner/`, `views/` |
| Kasım 2025 | Phase 3 | DRL training pipeline, model registry, inference | `drl/` |
| Ocak 2026 | Phase 4 | Backtest engine, WFO, report generation | `drl/backtest_engine.py`, `drl/report_generator.py` |
| Ocak 2026 | Phase 5 | Auth, session, SQLite persistence | `auth/` |
| Mart 2026 | Phase 6a | Web app + FastAPI runtime yüzeyi | `web/`, `api/`, `start.sh` |
| Nisan 2026 | Phase 6b | Funding/audit/pitch hazırlığı | `docs/FINANZPLAN_AWS_GRUENDUNGSFONDS.md`, `docs/FINPILOT_EVOLUTION_TIMELINE.md` |

### Mevcut Yol Haritası ve Hedef Tarihler

| Hedef | Hedef Tarih | Gözlem |
|------|-------------|--------|
| Next.js + FastAPI yüzeyini stabilize etmek | Nisan 2026 | Lokal runtime çalışıyor, fakat dokümantasyon ve CI tam hizalı değil |
| Seed başvuru paketini tamamlamak | Nisan 2026 | Pitch deck ve finans planı mevcut |
| Series A hazırlık eşiği | H1 2027 | Finans planında ARR/MRR hedefleri tanımlı |
| Real-time data / WebSocket / monitoring tamamlama | Belirsiz, dokümanlarda “sonraki adım” | Kodda parçalı temel var, uçtan uca canlı wiring eksik |

### Yol Haritası Değerlendirmesi

- Ürün geliştirme tarafı finansman hazırlığından daha hızlı ilerlemiş; operasyonel hizalama geride kalmış.
- Kod kapasitesi ve modül sayısı artmış, fakat “tek doğru runtime” tanımı netleştirilmemiş.
- Önümüzdeki kritik faz yeni özellik geliştirmek değil, **runtime contract consolidation** olmalıdır.

**Tekrarlama Notu**

- **Ne nedir:** Bu bölüm projenin nereden nereye geldiğini ve hangi fazların bugün canlı risk yarattığını özetler.
- **Nasıl çalışır:** Timeline dokümanları, güncel runtime dosyaları ve commit tarihleri birlikte okunur.
- **Nasıl test edilir:** Timeline’daki iddialar klasör yapısı, giriş noktaları ve aktif servislerle çapraz doğrulanır.
- **Bir sonraki değerlendirme için not:** Faz bazlı dokümanlar ile çalışan mimarinin tek sayfalık bir “source of truth” belgesinde birleştirilmesi gerekir.

---

## 2. Bileşen Envanteri

| Bileşen | Sahip | Repo/Konum | Son Commit Tarihi | Sorumlu Kişi |
|--------|-------|------------|-------------------|--------------|
| Frontend Web | Product / UI | `web/` | 2026-03-30 | Ibrahim Meriç Başak (varsayılan) |
| Backend API | Platform | `api/` | 2026-03-30 | Ibrahim Meriç Başak (varsayılan) |
| Auth & Session | Security / Platform | `auth/` | 2026-03-26 | Ibrahim Meriç Başak (varsayılan) |
| Scanner & Data Pipeline | Quant / Research | `scanner/` | 2026-03-30 | Ibrahim Meriç Başak (varsayılan) |
| DRL / ML Engine | ML / Quant | `drl/` | 2026-03-26 | Ibrahim Meriç Başak (varsayılan) |
| LLM / AI Layer | AI / Product | `llm/` | 2026-03-26 | Ibrahim Meriç Başak (varsayılan) |
| Observability & Reliability | Platform / Ops | `core/` | 2026-03-26 | Ibrahim Meriç Başak (varsayılan) |
| Infra / CI / Delivery | DevOps / Platform | `.github/workflows/ci.yml`, `docker-compose.yml`, `start.sh` | 2026-03-30 / 2026-03-26 / 2026-04-07 | Ibrahim Meriç Başak (varsayılan) |
| Legacy Streamlit Surface | Legacy Support | `streamlit_app.py`, `views/` | 2026-02-24 | Ibrahim Meriç Başak (varsayılan) |

### Meta Envanter

| Alan | Değer |
|------|-------|
| Python test adedi | 497 toplandı |
| Frontend aktif test dosyası | 1 test dosyası + 1 setup dosyası |
| Frontend kaynak dosyası | 44 TS/TSX dosyası |
| API router sayısı | 10 |
| Scanner Python dosyası | 6 |
| DRL Python dosyası | 42 |
| Legacy view Python dosyası | 39 |

### Envanter Gözlemi

- Teknik sahiplik yapısı resmileştirilmemiş; bütün bileşenler fiilen tek kişide toplanmış görünüyor.
- `views/` ve `streamlit_app.py` hâlâ ciddi bir bakım yükü oluşturuyor.
- `core/` içinde config/logging/monitoring mevcut; fakat bunlar canlı API’ye tam bağlanmamış.

**Tekrarlama Notu**

- **Ne nedir:** Bu bölüm denetlenecek sistem parçalarının katalogudur.
- **Nasıl çalışır:** Klasör bazlı ana bileşenler, son commit tarihi ve sorumluluk ile eşleştirilir.
- **Nasıl test edilir:** Her komponentin giriş noktası, aktif test dosyası ve çalışma komutları doğrulanır.
- **Bir sonraki değerlendirme için not:** CODEOWNERS ya da bileşen sahipliği matrisi eklenirse bu tablo operasyonel olarak anlam kazanır.

---

## 3. Her Bileşen İçin Ayrıntılı İnceleme

### 3.1 Frontend Web (Next.js)

**Teknik Tanım**
`web/` klasörü Next.js 16 App Router tabanlı ana kullanıcı yüzeyidir. Dashboard, scanner, AI Lab, history, portfolio ve settings gibi sayfaları barındırır; `/py-api/*` isteklerini backend FastAPI servisine rewrite eder ve `/api/quotes` ile Yahoo Finance’tan doğrudan batch quote çeker.

**Çalışma Durumu**
**Kısmen çalışıyor.** 16 Nisan 2026 tarihinde `http://localhost:3001` üzerinde `200 OK` döndü. `npm run build` başarılı oldu. Varsayılan `npm test` komutu worker timeout verdi; `npx vitest run --pool=threads` ile 12/12 test geçti, ancak React `act(...)` uyarıları üretildi.

**Fonksiyon Listesi**

- **DashboardOverview** — üst seviye dashboard verilerini toplar.
- **ScannerPage** — tarama ekranı ve işlem akışı.
- **AILabPage** — model, inference ve LLM etkileşim yüzeyi.
- **GET /api/quotes** — Yahoo batch quote rotası ve 30 saniye TTL cache.
- **useStockPrices** — fiyat polling ve batch bölme mantığı.

**Kontrol Listesi**

| Kontrol | Durum | Kanıt |
|---------|-------|-------|
| Deployment | Kısmen | `npm run build` başarılı; prod deploy script ayrı yönetilmiyor |
| Config | Var | `web/next.config.ts` rewrite ve security headers tanımlı |
| Env | Var | `API_HOST` ile backend rewrite yapılabiliyor |
| Secrets | Sınırlı | Frontend’de doğrudan secret yok; backend auth’e güveniyor |
| Health checks | Zayıf | Kök route `200`; ayrı frontend readiness standardı yok |
| API contract | Kısmen | `/py-api/*` contract var; backend ile tam test yok |
| Latency | Kısmen ölçülü | `logs/web.log` içinde `/api/quotes` için ~62ms–1563ms aralığı görüldü |
| Throughput | Ölçülmedi | Batch quote var ama yük testi yok |
| Error rate | Ölçülmüyor | Merkezi FE error telemetry kanıtı yok |
| Test coverage | Düşük | 1 aktif test dosyası, 12 test |
| Logging | Sınırlı | Next dev logları var |
| Tracing | Kısmen | Next trace artefact üretimi var, ancak ürün seviyesi tracing yok |

**Gözlemler ve Bulgular**

- `web/README.md` hâlâ create-next-app varsayılan metninde; ürün gerçekliğini yansıtmıyor.
- Frontend testleri varsayılan koşuda worker timeout verebiliyor; stabil test setup eksik.
- `dashboard-pages.test.tsx` yalnızca temel render smoke kapsıyor; kritik kullanıcı yolculukları yok.
- `/api/quotes` batch yaklaşımı iyi, ancak dashboard çok geniş sembol listeleri için sık tekrar çağrı yapıyor.

**Güvenlik ve Uyumluluk**

- CSP, HSTS, `X-Frame-Options`, `Referrer-Policy` ve `Permissions-Policy` header’ları tanımlı.
- Global error boundary mevcut (`web/src/app/error.tsx`).
- Asıl güvenlik açığı frontend’de değil, backend route’larının public olması nedeniyle rewrite edilen çağrıların auth’suz kalmasıdır.

**Performans ve Ölçeklenebilirlik**

- `/api/quotes` tarafında batch + kısa TTL cache güçlü bir temel sağlıyor.
- Büyük sembol setlerinde Next.js dev server loglarında belirgin varyans görülüyor; SSR/route handler profillemesi yapılmalı.
- Frontend tarafında E2E ve gerçek kullanıcı ölçümleri (Web Vitals, Sentry Browser, RUM) yok.

**Puanlama**

| Kriter | Puan |
|--------|------|
| Stabilite | 7 |
| Güvenlik ve Uyumluluk | 7 |
| Performans ve Ölçeklenebilirlik | 7 |
| Test Kapsamı ve Otomasyon | 5 |
| Bakım ve Dokümantasyon | 5 |
| Teknik Borç (ters etki düşükse yüksek puan) | 6 |
| **Ağırlıklı Toplam** | **6.4 / 10 — B** |

**Düzeltme Önerileri**

- **Kısa Vadeli (48 saat):** `web/README.md` güncelle; `npm test` komutunu stabil havuz ayarıyla düzelt; temel dashboard smoke testlerini artır.
- **Orta Vadeli (2 hafta):** auth gerektiren sayfalar için gerçek contract testleri ve MSW tabanlı entegrasyon testleri ekle.
- **Uzun Vadeli (3 ay):** RUM, frontend error telemetry, E2E suite ve performans bütçesi tanımla.

**Tekrarlama Notu**

- **Ne nedir:** Kullanıcının gördüğü ana ürün yüzeyi ve dashboard deneyimi burada çalışır.
- **Nasıl çalışır:** App Router sayfaları `/py-api/*` ile FastAPI’ye, `/api/quotes` ile Yahoo Finance’a bağlanır.
- **Nasıl test edilir:** `npm run build`, `npx vitest run --pool=threads`, dashboard ana sayfa ve scanner sayfası smoke test edilir.
- **Bir sonraki değerlendirme için not:** `/api/quotes` polling sıklığı, kullanıcı başına çağrı sayısı ve `/py-api/*` hata oranı izlenmelidir.

### 3.2 Backend API (FastAPI)

**Teknik Tanım**
`api/` klasörü FastAPI tabanlı Python servisidir ve `scan`, `trade`, `models`, `inference`, `llm`, `history`, `user` gibi route’ları expose eder. Next.js tarafı bu API’ye `/py-api/*` rewrite ile erişir.

**Çalışma Durumu**
**Kısmen çalışıyor.** 16 Nisan 2026 tarihinde `http://localhost:8000/api/v1/health` `200 OK` döndü. `start.sh` ile API ayağa kalktı. Ancak yalnızca minimal health endpoint canlı; readiness/metrics/tracing wiring görülmedi.

**Fonksiyon Listesi**

- **health** — minimal servis sağlık dönüşü.
- **run_scan** — thread pool içinde scanner çağrısı.
- **shortlist_status** — legacy shortlist staleness kontrolü.
- **analyze_symbol** — LLM analiz endpoint’i.
- **get_settings / save_settings / patch_settings** — kullanıcı ayarı persistence rotaları.

**Kontrol Listesi**

| Kontrol | Durum | Kanıt |
|---------|-------|-------|
| Deployment | Kısmen | `start.sh` ile lokal ayağa kalkıyor |
| Config | Var ama dağınık | `api/main.py` `.env` dosyasını manuel parse ediyor; ayrıca `core/config.py` var |
| Env | Var | `.env.example` mevcut |
| Secrets | Kısmen | Örnek secret yönetimi var, ancak merkezi secret store kanıtı yok |
| Health checks | Zayıf | Sadece `/api/v1/health` var |
| API contract | Drift var | `docs/api/openapi.yaml` `/health`, `/ready`, `/metrics` ve JWT zorunluluğu belgeliyor; runtime bunu karşılamıyor |
| Latency | Sınırlı | Sadece health ve web log dolaylı kanıtı var |
| Throughput | Ölçülmedi | Load test yok |
| Error rate | Ölçülmüyor | Prod metrik route yok |
| Test coverage | Orta | Temsili auth/prometheus/sentry testleri geçiyor; tam API contract suite görünmüyor |
| Logging | Temel | Uvicorn logları aktif |
| Tracing | Eksik | slowapi limit var, distributed tracing yok |

**Gözlemler ve Bulgular**

- `requirements.txt` içinde `fastapi`, `uvicorn`, `slowapi` pinlenmemiş; temiz kurulum zinciri bu yüzden güvenilir değil.
- OpenAPI dokümanı ile runtime uyumsuz.
- API auth middleware’i var (`api/middleware/auth.py`) fakat router’larda kullanılmıyor.
- `user/settings` default kullanıcıyla public şekilde yazılabiliyor.

**Güvenlik ve Uyumluluk**

- JWT ve bearer middleware teorik olarak mevcut, pratikte route enforcement görünmüyor.
- CORS allowlist tanımlı, bu olumlu.
- Dokümanda auth zorunlu denirken gerçekte public route olması, hem güvenlik hem uyumluluk açısından riskli.
- PII içeren ayar/veri akışları için audit log zinciri görünmüyor.

**Performans ve Ölçeklenebilirlik**

- `scan` route’u thread pool ile sınırlandırılmış ve 300sn timeout taşıyor; bu iyi bir koruma.
- Ancak API katmanında queue, worker isolation veya backpressure stratejisi yok.
- Health ve metrics wiring eksik olduğu için üretim ölçeklenebilirliğini operasyonel olarak izlemek zor.

**Puanlama**

| Kriter | Puan |
|--------|------|
| Stabilite | 6 |
| Güvenlik ve Uyumluluk | 4 |
| Performans ve Ölçeklenebilirlik | 6 |
| Test Kapsamı ve Otomasyon | 6 |
| Bakım ve Dokümantasyon | 4 |
| Teknik Borç | 4 |
| **Ağırlıklı Toplam** | **5.2 / 10 — C** |

**Düzeltme Önerileri**

- **Kısa Vadeli (48 saat):** `requirements.txt` içine API runtime bağımlılıklarını ekle; `/ready` ve `/metrics` rotalarını canlı uygulamaya bağla.
- **Orta Vadeli (2 hafta):** route bazında auth dependency enforcement uygula ve OpenAPI’yi runtime’dan üret.
- **Uzun Vadeli (3 ay):** async job queue, request telemetry ve contract regression suite kur.

**Tekrarlama Notu**

- **Ne nedir:** Frontend’in arkasındaki iş mantığı ve Python servis yüzeyidir.
- **Nasıl çalışır:** Next.js `/py-api/*` isteklerini `api/v1/*` endpoint’lerine rewrite eder; router’lar scanner, auth, model ve LLM katmanlarını çağırır.
- **Nasıl test edilir:** `curl /api/v1/health`, `python3 -m pytest` ile route’a komşu testler, rewrite altından gerçek endpoint çağrıları çalıştırılır.
- **Bir sonraki değerlendirme için not:** Auth enforcement, `/ready`, `/metrics`, install reproducibility ve OpenAPI drift öncelikle yeniden denetlenmelidir.

### 3.3 Auth & Session

**Teknik Tanım**
`auth/` modülü JWT, bcrypt tabanlı parola güvenliği, session yönetimi ve SQLite/PostgreSQL abstractions içerir. Kod kalitesi modül seviyesinde güçlüdür; fakat modern web/API yüzeyine tam entegrasyon eksiktir.

**Çalışma Durumu**
**Kısmen çalışıyor.** `python3 -m pytest tests/test_auth.py ...` çalıştırmasında auth testleri başarılı geçti. Ancak API route’ları bu katmanı aktif şekilde zorunlu kılmıyor.

**Fonksiyon Listesi**

- **AuthManager.login** — kullanıcı doğrulama ve lockout akışı.
- **AuthManager.refresh_tokens** — token yenileme.
- **JWTHandler.encode / decode** — token üretim ve doğrulama.
- **PasswordHasher.hash / verify** — bcrypt parola işlemleri.
- **get_backend** — SQLite / PostgreSQL backend seçimi.

**Kontrol Listesi**

| Kontrol | Durum | Kanıt |
|---------|-------|-------|
| Deployment | Kısmen | Auth daha çok modül olarak hazır; API entegrasyonu eksik |
| Config | Var | `auth/core.py`, `core/config.py`, `.env.example` |
| Env | Var | `FINPILOT_SECRET_KEY` örneği mevcut |
| Secrets | Kısmen | secret zorunlu öneriliyor; ama config fallback anahtar içeriyor |
| Health checks | Yok | Auth’a özel readiness yok |
| API contract | Tutarsız | Doküman auth istiyor, route’lar istemiyor |
| Latency | Ölçülmedi | Auth request metrikleri görünmüyor |
| Throughput | Ölçülmedi | Multi-user auth benchmark yok |
| Error rate | Ölçülmüyor | Audit/event stream yok |
| Test coverage | Orta-iyi | Auth testleri başarılı geçti |
| Logging | Temel | standart logger kullanılıyor |
| Tracing | Yok | auth trace zinciri görünmüyor |

**Gözlemler ve Bulgular**

- `auth/core.py` güvenli anahtarın `.env` içinden gelmesini istiyor; fakat `core/config.py` içinde insecure default secret fallback mevcut.
- `auth/database.py` “connection pooling” ifadesi kullanıyor ama SQLite tarafında gerçek pool yok; bağlantı her kullanımda açılıp kapanıyor.
- `auth/db_backend.py` PostgreSQL için `_pool` alanı tanımlıyor fakat connection pooling uygulanmamış.
- `user/settings` rotaları public ve default user id ile çalışıyor; multi-user izolasyonu zayıf.

**Güvenlik ve Uyumluluk**

- Güçlü yanlar: bcrypt, lockout, refresh token, role-based altyapı.
- Zayıf yanlar: route enforcement yok, audit trail görünür değil, veri erişim kontrolü pratikte gevşek.
- GDPR açısından kullanıcı ayarları ve session verileri yerelde tutuluyor; retention/silme prosedürü görünmüyor.

**Performans ve Ölçeklenebilirlik**

- SQLite, demo ve düşük trafikli kullanım için yeterli.
- Çok kullanıcılı SaaS senaryosunda connection management ve write concurrency yetersiz kalabilir.
- PostgreSQL backend düşünülmüş ama tam üretim sertliği yok.

**Puanlama**

| Kriter | Puan |
|--------|------|
| Stabilite | 6 |
| Güvenlik ve Uyumluluk | 6 |
| Performans ve Ölçeklenebilirlik | 5 |
| Test Kapsamı ve Otomasyon | 7 |
| Bakım ve Dokümantasyon | 6 |
| Teknik Borç | 5 |
| **Ağırlıklı Toplam** | **5.9 / 10 — C** |

**Düzeltme Önerileri**

- **Kısa Vadeli (48 saat):** insecure default secret’ı kaldır; `user/settings` dahil auth gerektiren route’ları koru.
- **Orta Vadeli (2 hafta):** auth middleware’ini route bazında uygula, DB backend için gerçek pooling veya SQLAlchemy seçeneği ekle.
- **Uzun Vadeli (3 ay):** audit log, session revocation list ve veri silme süreçlerini formalize et.

**Tekrarlama Notu**

- **Ne nedir:** Kullanıcı kimliği, token üretimi ve kalıcı user data katmanıdır.
- **Nasıl çalışır:** JWT ve bcrypt ile kimlik doğrulama yapılır, ayarlar ve oturumlar veritabanında tutulur.
- **Nasıl test edilir:** login, refresh, lockout, invalid token ve settings isolation test edilir.
- **Bir sonraki değerlendirme için not:** Auth’ın sadece modül değil, gerçek route enforcement olarak aktif olup olmadığı tekrar denetlenmelidir.

### 3.4 Scanner & Data Pipeline

**Teknik Tanım**
`scanner/` modülü Yahoo Finance verisini çekip teknik indikatör ve sinyal skorları üretir. `api/routers/scan.py` bu modülü thread pool içinde çağırır ve sonuçları `data/shortlists/` altına CSV olarak yazar.

**Çalışma Durumu**
**Kısmen çalışıyor.** Scan endpoint kodu mevcut ve canlı backend içinde kayıtlı. Ancak bu denetimde ağ bağımlı tam scan senaryosu prod benzeri yük altında koşturulmadı.

**Fonksiyon Listesi**

- **fetch** — OHLCV çekimi ve temel validasyon.
- **fetch_with_indicators** — veri + indikatör katmanı.
- **fetch_multi_timeframe** — paralel çok zaman dilimli veri çekimi.
- **evaluate_symbols_parallel** — sembol değerlendirme akışı.
- **shortlist_status** — stale shortlist uyarısı.

**Kontrol Listesi**

| Kontrol | Durum | Kanıt |
|---------|-------|-------|
| Deployment | Kısmen | API route üzerinden kullanılabiliyor |
| Config | Var | `scanner/config.py`, `SETTINGS` |
| Env | Kısmen | Veri sağlayıcı anahtarları opsiyonel |
| Secrets | Düşük risk | PII barındırmıyor, provider key gerekiyor |
| Health checks | Zayıf | Kaynak endpoint health’i ayrı probe olarak expose edilmiyor |
| API contract | Kısmen | Scan request modeli var |
| Latency | Ölçülmedi | Scan için benchmark yok |
| Throughput | Sınırlı | ThreadPoolExecutor `max_workers=4` |
| Error rate | Kısmen | Fail-safe empty DataFrame ve warnings var |
| Test coverage | Orta | Tüm suite içinde çok sayıda scanner testi tanımlı |
| Logging | Kısmen | logger + bazı `print` çağrıları birlikte kullanılıyor |
| Tracing | Yok | veri hattı trace zinciri yok |

**Gözlemler ve Bulgular**

- Cache TTL yaklaşımı var: scanner fetch tarafında 300s, quote tarafında 30s, core cache’de 60s/300s/3600s katmanları tanımlı.
- `shortlist_status` stale dosya uyarısı iyi bir operasyonel koruma.
- Dış veri sağlayıcıları için schema contract testleri görünmüyor.
- `print` ve `logger` karışımı üretim log standardını zayıflatıyor.

**Güvenlik ve Uyumluluk**

- PII riski düşük; ana risk provider key yönetimi ve dış veri güvenilirliği.
- Stale veya malformed data durumunda boş DataFrame dönüşü sessiz hata maskelemesi yaratabilir.

**Performans ve Ölçeklenebilirlik**

- Paralel fetch ve cache iyi bir temel.
- Provider rate limit ve Yahoo response varyansı büyük ölçekli taramayı etkileyebilir.
- Queue / batch orchestration / retry policy merkezi değil.

**Puanlama**

| Kriter | Puan |
|--------|------|
| Stabilite | 7 |
| Güvenlik ve Uyumluluk | 6 |
| Performans ve Ölçeklenebilirlik | 7 |
| Test Kapsamı ve Otomasyon | 7 |
| Bakım ve Dokümantasyon | 6 |
| Teknik Borç | 6 |
| **Ağırlıklı Toplam** | **6.6 / 10 — B** |

**Düzeltme Önerileri**

- **Kısa Vadeli (48 saat):** `print` çağrılarını standart logger’a taşı; scan request/response örneklerini testlerle bağla.
- **Orta Vadeli (2 hafta):** veri kaynakları için schema contract test ve stale fallback alarmı ekle.
- **Uzun Vadeli (3 ay):** event-driven batch scan, queue ve backoff/telemetry katmanını kur.

**Tekrarlama Notu**

- **Ne nedir:** Piyasa verisini çekip teknik sinyal üreten quant veri hattıdır.
- **Nasıl çalışır:** Veri çekilir, normalize edilir, indikatörler eklenir, sinyaller üretilir ve shortlist dosyası yazılır.
- **Nasıl test edilir:** geçerli sembol, geçersiz sembol, stale shortlist, rate limit ve multi-timeframe senaryoları test edilir.
- **Bir sonraki değerlendirme için not:** scan başarısızlık oranı, stale shortlist süresi ve kaynak hata oranı metrikleştirilmelidir.

### 3.5 DRL / ML Engine

**Teknik Tanım**
`drl/` klasörü feature engineering, training, inference, model registry, optuna araması, backtest ve rapor üretimi için geniş bir ML/quant katmanı sunar. Kod hacmi projedeki en büyük modüllerden biridir.

**Çalışma Durumu**
**Kısmen çalışıyor.** Kod ve registry/persistence yüzeyi mevcut. Model eğitim veya inference job’ları bu denetimde uçtan uca koşturulmadı. Dashboard sayfalarında model yönetim rotaları çağrılıyor.

**Fonksiyon Listesi**

- **ModelRegistry.save_model / load_model / load_best**
- **BacktestEngine.run**
- **training pipeline**
- **optuna_search**
- **report_generator**

**Kontrol Listesi**

| Kontrol | Durum | Kanıt |
|---------|-------|-------|
| Deployment | Kısmen | API ve dashboard entegrasyon izleri var |
| Config | Var | `drl/config.py`, schema version, persistence |
| Env | Kısmen | MLflow ve provider bağımlılıkları opsiyonel |
| Secrets | Düşük-orta | Doğrudan gizli veri az, ama model artefact yönetimi lokal |
| Health checks | Yok | model serving readiness görünmüyor |
| API contract | Kısmen | models/inference route’ları mevcut |
| Latency | Ölçülmedi | inference benchmark kanıtı yok |
| Throughput | Ölçülmedi | batch inference için prod metriği yok |
| Error rate | Ölçülmüyor | model görevleri için merkezi run-id metriği yok |
| Test coverage | Orta | çok sayıda test dosyası var, tam suite koşulmadı |
| Logging | Kısmen | logger kullanımı var |
| Tracing | Kısmen | MLflow/monitoring altyapısı var, wiring zayıf |

**Gözlemler ve Bulgular**

- Model registry ve persistence katmanı, reproducibility açısından pozitif.
- `drl/rate_limiter.py` ve backoff decorator’ları iyi bir temel sunuyor.
- Buna karşılık canlı inference ve benchmark kapıları resmi teslim pipeline’ına bağlı görünmüyor.
- Model artefact sürümleme var; fakat release gate ve rollback politikası belgesel düzeyde eksik.

**Güvenlik ve Uyumluluk**

- Model dosyaları lokal filesystem üzerinde yönetiliyor; imzalı artefact veya immutable registry yok.
- Hassas kullanıcı verisi düşük, ancak model karar açıklanabilirliği ve auditability kurumsal kullanımda daha fazla olgunluk ister.

**Performans ve Ölçeklenebilirlik**

- Geniş modül yapısı ölçeklenmeye açık; ancak eğitim, inference ve backtest CPU/RAM sınırları operasyonel olarak ölçülmüyor.
- Async job queue ve worker isolation olmayışı production ML workload’ları için risk.

**Puanlama**

| Kriter | Puan |
|--------|------|
| Stabilite | 6 |
| Güvenlik ve Uyumluluk | 5 |
| Performans ve Ölçeklenebilirlik | 6 |
| Test Kapsamı ve Otomasyon | 7 |
| Bakım ve Dokümantasyon | 6 |
| Teknik Borç | 6 |
| **Ağırlıklı Toplam** | **6.0 / 10 — B** |

**Düzeltme Önerileri**

- **Kısa Vadeli (48 saat):** aktif model, inference cache ve backtest sonuçları için smoke komutları standartlaştır.
- **Orta Vadeli (2 hafta):** benchmark dataset, reproducibility manifest ve run-id raporlama ekle.
- **Uzun Vadeli (3 ay):** worker queue, offline evaluation store ve model promotion gate tasarla.

**Tekrarlama Notu**

- **Ne nedir:** DRL eğitimi, model sürümleme ve backtest katmanıdır.
- **Nasıl çalışır:** veri feature pipeline’dan geçer, model eğitilir/kaydedilir, inference ve backtest ile kullanılır.
- **Nasıl test edilir:** registry save-load, inference smoke, backtest metric doğrulama ve optuna sonuç bütünlüğü test edilir.
- **Bir sonraki değerlendirme için not:** model benchmarkları, training cost ve artefact rollback akışı izlenmelidir.

### 3.6 LLM / AI Analysis Layer

**Teknik Tanım**
`llm/` ve `api/routers/llm.py` katmanı Groq → Claude → Gemini fallback zinciriyle yatırımcı raporu ve analiz metni üretir. Caching, provider status ve dil seçimi desteklenir.

**Çalışma Durumu**
**Kısmen çalışıyor.** Endpoint kodu mevcut. Çalışma sağlayıcı anahtarlarına bağlı. Bu denetimde canlı sağlayıcı anahtarıyla üretim çağrısı yapılmadı.

**Fonksiyon Listesi**

- **llm_status** — sağlayıcı durum yüzeyi.
- **_generate_report** — cache’li içerik üretimi.
- **analyze_symbol** — ana LLM analiz endpoint’i.
- **get_router** — sağlayıcı router seçimi.
- **_parse_sections** — markdown section parse.

**Kontrol Listesi**

| Kontrol | Durum | Kanıt |
|---------|-------|-------|
| Deployment | Kısmen | API route mevcut, env anahtarlarına bağlı |
| Config | Var | `.env.example` içinde API key alanları var |
| Env | Var | GROQ / GOOGLE / diğer anahtar alanları tanımlı |
| Secrets | Kısmen | env tabanlı, secret manager görünmüyor |
| Health checks | Kısmen | `/llm/status` var |
| API contract | Kısmen | request/response modeli tanımlı |
| Latency | Kısmen | response içinde `latency_ms` dönüyor, merkezi metrik yok |
| Throughput | Ölçülmedi | rate/queue yönetimi üst düzeyde yok |
| Error rate | Kısmen | logger ve HTTP 502 var; alarm yok |
| Test coverage | Belirsiz | tam LLM route testi doğrulanmadı |
| Logging | Var | backend logger |
| Tracing | Yok | provider bazlı dağıtık tracing yok |

**Gözlemler ve Bulgular**

- LLM sonuçları 30 dakika cache’leniyor; bu maliyet açısından iyi.
- Promptlar kod içinde sabit; versiyonlama ve prompt governance zayıf.
- Failover tasarımı güçlü, fakat gerçek provider availability ve quota izleme görünmüyor.

**Güvenlik ve Uyumluluk**

- Kullanıcı context’i prompta eklenebiliyor; veri minimizasyon ve log redaction kontrolü görünmüyor.
- Sentry PII default kapalı; bu olumlu.

**Performans ve Ölçeklenebilirlik**

- Cache ve fallback olumlu.
- Dış API bağımlılığı nedeniyle latency ve quota riski yüksek.
- Offline fallback veya queued enrichment yok.

**Puanlama**

| Kriter | Puan |
|--------|------|
| Stabilite | 6 |
| Güvenlik ve Uyumluluk | 5 |
| Performans ve Ölçeklenebilirlik | 6 |
| Test Kapsamı ve Otomasyon | 5 |
| Bakım ve Dokümantasyon | 5 |
| Teknik Borç | 5 |
| **Ağırlıklı Toplam** | **5.6 / 10 — C** |

**Düzeltme Önerileri**

- **Kısa Vadeli (48 saat):** LLM smoke testi ve provider availability probe ekle.
- **Orta Vadeli (2 hafta):** prompt versioning, contract fixtures ve quota alarmı kur.
- **Uzun Vadeli (3 ay):** prompt registry, evaluation dataset ve safety review süreci tanımla.

**Tekrarlama Notu**

- **Ne nedir:** Finansal açıklama ve analiz metni üreten AI katmanıdır.
- **Nasıl çalışır:** endpoint isteği cache katmanına, sonra provider router’a, sonra section parser’a gider.
- **Nasıl test edilir:** status endpoint, force-refresh senaryosu, provider unavailable senaryosu ve schema doğrulaması test edilir.
- **Bir sonraki değerlendirme için not:** quota tüketimi, provider fallback sıklığı ve latency dağılımı izlenmelidir.

### 3.7 Observability & Reliability

**Teknik Tanım**
`core/monitoring.py`, `core/prometheus_exporter.py` ve `core/logging.py` projedeki monitoring, health, structured logging ve Sentry entegrasyonu için altyapı sağlar. Bu katman güçlü bir kütüphane yüzeyi sunar, ancak canlı uygulamaya kısmen bağlanmıştır.

**Çalışma Durumu**
**Kısmen çalışıyor.** `python3 -m pytest tests/test_prometheus.py tests/test_sentry.py -q` sonucu 53/53 geçmiştir. Buna rağmen canlı FastAPI içinde `/metrics` ve `/ready` rotaları yoktur; Sentry init ve structured logging wiring kanıtı bulunmadı.

**Fonksiyon Listesi**

- **SentryClient.init / capture_exception**
- **health_check.run**
- **PrometheusExporter**
- **start_metrics_server**
- **get_logger / log_context**

**Kontrol Listesi**

| Kontrol | Durum | Kanıt |
|---------|-------|-------|
| Deployment | Kısmen | Kod mevcut ama app wiring eksik |
| Config | Var | `core/config.py` monitoring alanları mevcut |
| Env | Var | `SENTRY_DSN`, `MLFLOW_TRACKING_URI`, `REDIS_URL` alanları var |
| Secrets | Kısmen | DSN env bazlı |
| Health checks | Kütüphane düzeyinde var | `health_check` database/cache/memory kontrolleri içeriyor |
| API contract | Drift var | OpenAPI `/metrics` ve `/ready` diyor; app expose etmiyor |
| Latency | Ölçülmüyor | canlı histogram export yok |
| Throughput | Ölçülmüyor | request metrikleri API yüzeyine bağlı değil |
| Error rate | Kısmen | Sentry wrapper var ama init kanıtı yok |
| Test coverage | İyi | Prometheus ve Sentry testleri geçiyor |
| Logging | Altyapı güçlü | canlıda çoğu modül hâlâ standart logger kullanıyor |
| Tracing | Zayıf | distributed tracing / OTel yok |

**Gözlemler ve Bulgular**

- Kütüphane seviyesi olgunluk, uygulama entegrasyonundan daha ileri.
- `core/logging.py` structured JSON logging sunuyor, ancak modüllerin çoğu `logging.getLogger` ile doğrudan çalışıyor.
- Health checker iyi tasarlanmış olsa da FastAPI route’una bağlı değil.

**Güvenlik ve Uyumluluk**

- Audit log ve immutable security event zinciri görünmüyor.
- PII gönderimi Sentry’de default kapalı, olumlu.

**Performans ve Ölçeklenebilirlik**

- Prometheus text exporter ve health checker ölçek için iyi başlangıç.
- Wiring eksikliği nedeniyle operasyon ekipleri gerçek zamanlı SLO takibi yapamaz.

**Puanlama**

| Kriter | Puan |
|--------|------|
| Stabilite | 5 |
| Güvenlik ve Uyumluluk | 6 |
| Performans ve Ölçeklenebilirlik | 5 |
| Test Kapsamı ve Otomasyon | 7 |
| Bakım ve Dokümantasyon | 6 |
| Teknik Borç | 5 |
| **Ağırlıklı Toplam** | **5.7 / 10 — C** |

**Düzeltme Önerileri**

- **Kısa Vadeli (48 saat):** `/ready` ve `/metrics` expose et; startup’ta Sentry/logging init ekle.
- **Orta Vadeli (2 hafta):** request latency, error rate ve scan duration SLO dashboard’ı kur.
- **Uzun Vadeli (3 ay):** distributed tracing, alert routing ve runbook entegrasyonu tamamla.

**Tekrarlama Notu**

- **Ne nedir:** Sistem sağlığı, log, metrik ve hata izleme katmanıdır.
- **Nasıl çalışır:** kütüphane seviyesi metrik/health/log objeleri uygulamaya bağlandığında gözlemlenebilirlik sağlar.
- **Nasıl test edilir:** health checker, Prometheus exporter ve Sentry wrapper testleri ile route seviyesi smoke testleri birlikte çalıştırılır.
- **Bir sonraki değerlendirme için not:** canlı metrik endpoint’inin gerçekten scrape edildiği ve alert ürettiği doğrulanmalıdır.

### 3.8 Infra / CI / Delivery

**Teknik Tanım**
Bu katman `start.sh`, `stop.sh`, Dockerfile’lar, `docker-compose.yml` ve GitHub Actions workflow’larını içerir. Lokal runtime güncel mimariyi çalıştırırken, Docker ve CI tarafında legacy Streamlit kalıntıları sürmektedir.

**Çalışma Durumu**
**Kısmen çalışıyor.** `bash start.sh` başarılı oldu ve frontend + API ayağa kalktı. Buna karşılık `pip install -r requirements.txt` lokal olarak başarısız oldu; CI ve Docker zincirinde de bu bağımlılık seti risk yaratır.

**Fonksiyon Listesi**

- **start.sh** — resmi lokal start akışı.
- **stop.sh** — servis durdurma.
- **docker-compose services** — web, api, legacy finpilot, scanner, telegram, redis, postgres.
- **GitHub Actions jobs** — test, lint, frontend, security, docker, scanner-integration.
- **next rewrites + API_HOST** — frontend/backend bağlama katmanı.

**Kontrol Listesi**

| Kontrol | Durum | Kanıt |
|---------|-------|-------|
| Deployment | Kısmen | Lokal `start.sh` iyi; Docker/CI drift var |
| Config | Kısmen | Birden fazla giriş noktası ve farklı port varsayımları var |
| Env | Var | `.env.example` iyi başlangıç |
| Secrets | Kısmen | env kullanım modeli var; secret manager / vault yok |
| Health checks | Tutarsız | start script 8000/3001; compose ve root Dockerfile Streamlit 8501 referanslıyor |
| API contract | Tutarsız | OpenAPI ve runtime farklı |
| Latency / Throughput | Yok | performans pipeline’ı yok |
| Error rate | Yok | deploy sonrası otomatik alarm / rollback şartı tanımlı değil |
| Test coverage | Orta | CI var ama bazı adımlar legacy varsayımlı |
| Logging | Var | log dosyalarına yazılıyor |
| Tracing | Yok | deploy pipeline traceability yok |

**Gözlemler ve Bulgular**

- `README.md` hâlâ Streamlit’i ana çalışma yolu olarak anlatıyor.
- Root `Dockerfile` ve compose içindeki `finpilot` servisi legacy Streamlit yüzeyine dayanıyor.
- CI docker smoke test’i Streamlit health check bekliyor.
- `requirements.txt` içinde `fastapi`, `uvicorn`, `slowapi` yok; buna rağmen API Dockerfile uvicorn ile başlatıyor.
- `lxml==6.1.1` lokal kurulumda bulunamadı; reproducibility kırık.

**Güvenlik ve Uyumluluk**

- Compose içinde default postgres şifresi bulunuyor; prod için uygun değil.
- Secret scan workflow’u olumlu bir kontrol.
- Rollback ve canary prosedürü doküman seviyesinde değil.

**Performans ve Ölçeklenebilirlik**

- Containerization ve ayrı servis düşüncesi olumlu.
- Cost monitoring, quota alerts, autoscaling ve prod release gating görünmüyor.

**Puanlama**

| Kriter | Puan |
|--------|------|
| Stabilite | 4 |
| Güvenlik ve Uyumluluk | 5 |
| Performans ve Ölçeklenebilirlik | 5 |
| Test Kapsamı ve Otomasyon | 4 |
| Bakım ve Dokümantasyon | 4 |
| Teknik Borç | 4 |
| **Ağırlıklı Toplam** | **4.4 / 10 — C** |

**Düzeltme Önerileri**

- **Kısa Vadeli (48 saat):** tek resmi runtime tanımını belirle; CI, README, Docker ve compose’u buna hizala.
- **Orta Vadeli (2 hafta):** requirements lock üret, deploy smoke + contract + readiness gate ekle.
- **Uzun Vadeli (3 ay):** canary release, rollback automation ve prod environment parity kur.

**Tekrarlama Notu**

- **Ne nedir:** Çalıştırma, dağıtım, build ve otomasyon katmanıdır.
- **Nasıl çalışır:** lokal start script, container tanımları ve CI job’ları birlikte release zincirini oluşturur.
- **Nasıl test edilir:** temiz kurulum, docker build, health probe, smoke test ve rollback dry-run birlikte denenir.
- **Bir sonraki değerlendirme için not:** tek-source-of-truth release pipeline oluşturulmadan yeniden yayına hazır kararı verilmemelidir.

### 3.9 Legacy Streamlit Surface

**Teknik Tanım**
`streamlit_app.py` ve `views/` klasörü projenin önceki nesil kullanıcı yüzeyidir. Hâlâ ciddi miktarda iş mantığı ve UI rendering barındırdığı için teknik borç ve bakım maliyeti yaratmaktadır.

**Çalışma Durumu**
**Kısmen çalışıyor / legacy.** Dosyalar mevcut. Root Dockerfile ve CI’nin bir kısmı bu yüzeyi referanslamaya devam ediyor. `tests/test_views_smoke.py` altındaki 4 hata, lokal ortamda eksik dependency (`openpyxl`) yüzünden görüldü.

**Fonksiyon Listesi**

- **streamlit_app** — legacy giriş noktası.
- **render_scanner_page** — Streamlit scanner ekranı.
- **render_tabs** — result tab yapısı.
- **render_export_panel** — export ve Excel fonksiyonları.
- **protected_page** — auth/streamlit koruma örüntüleri.

**Kontrol Listesi**

| Kontrol | Durum | Kanıt |
|---------|-------|-------|
| Deployment | Legacy | Root Dockerfile ve compose hâlâ bunu kullanıyor |
| Config | Var | Streamlit tabanlı config akışları mevcut |
| Env | Kısmen | export ve auth bağımlılıkları var |
| Secrets | Kısmen | eski auth akışlarıyla entegre |
| Health checks | Legacy | `_stcore/health` beklentisi CI/Docker’da duruyor |
| API contract | Uyuşmuyor | yeni web yüzeyi ile paralel yaşıyor |
| Latency / Throughput | Ölçülmedi | modern ölçüm yok |
| Error rate | Ölçülmüyor | prod telemetry görünmüyor |
| Test coverage | Orta | smoke testleri var ama import bağımlılığı kırılgan |
| Logging | Düşük | legacy yüzey ağırlıklı |
| Tracing | Yok | yok |

**Gözlemler ve Bulgular**

- Legacy yüzeyin tamamen kaldırılmaması yeni mimariyle sürekli drift yaratıyor.
- Export katmanında `openpyxl` bağımlılığı var; kurulum zinciri kırılınca view import testleri de kırılıyor.
- `views/` klasörü büyük ve hâlâ iş değeri taşıyan kod içeriyor; plansız silinemez.

**Güvenlik ve Uyumluluk**

- Eski auth/state örüntüleri modern web güvenlik modelinden sapabilir.
- Kullanıcı verisi ve export akışları üzerinde audit izleri sınırlı.

**Performans ve Ölçeklenebilirlik**

- Streamlit yüzeyi primary deploy olmamalı.
- İş mantığının bir kısmı legacy UI içinde kalırsa bakım ve performans parçalanması sürer.

**Puanlama**

| Kriter | Puan |
|--------|------|
| Stabilite | 4 |
| Güvenlik ve Uyumluluk | 4 |
| Performans ve Ölçeklenebilirlik | 4 |
| Test Kapsamı ve Otomasyon | 6 |
| Bakım ve Dokümantasyon | 3 |
| Teknik Borç | 3 |
| **Ağırlıklı Toplam** | **4.0 / 10 — C** |

**Düzeltme Önerileri**

- **Kısa Vadeli (48 saat):** legacy yüzeyin destek durumu resmi olarak tanımlansın.
- **Orta Vadeli (2 hafta):** modern web’e taşınan ve taşınmayan parçalar için migration matrix çıkarılsın.
- **Uzun Vadeli (3 ay):** Streamlit yüzeyini ya tamamen devreden çıkar ya da sadece admin/internal tool olarak ayır.

**Tekrarlama Notu**

- **Ne nedir:** Projenin önceki nesil UI yüzeyidir ve bugün hem değer hem teknik borç taşır.
- **Nasıl çalışır:** Streamlit üzerinden views modüllerini render eder, auth ve export fonksiyonlarını kullanır.
- **Nasıl test edilir:** view import, export, auth render ve basic navigation smoke testleri çalıştırılır.
- **Bir sonraki değerlendirme için not:** legacy yüzeyin kaderi netleşmeden CI ve Docker sadeleşmeyecektir.

---

## 4. Entegrasyon ve Veri Akışı Analizi

### Metin Tabanlı Veri Akışı

1. Kullanıcı tarayıcıda `web/` Next.js arayüzüne gelir.
2. UI iki farklı veri yolu kullanır:
3. Anlık quote verileri için `/api/quotes` route handler’ı doğrudan Yahoo Finance batch endpoint’lerine gider.
4. Ürün iş mantığı için `/py-api/*` çağrıları `web/next.config.ts` rewrite ile `http://localhost:8000/api/v1/*` adresine yönlenir.
5. FastAPI router’ları scanner, auth, trade, history, model ve LLM modüllerine dağıtır.
6. Scanner sonuçları `data/shortlists/` altında CSV’ye yazılır; user settings `data/finpilot.db` içine gider.
7. DRL model metadata’sı `models/registry.json` ve model klasörlerine yazılır.
8. LLM katmanı dış sağlayıcılara çıkar ve `core.cache` üzerinden cache’lenir.
9. Monitoring kütüphaneleri teorik olarak metrics/health/log üretir, ancak canlı API yüzeyine tam bağlanmamıştır.

### Önerilen Görselleştirme Alanları

- **Component diagram:** Browser → Next.js → FastAPI → Scanner/Auth/DRL/LLM → Data/Models
- **Sequence diagram:** scanner çalıştırma ve AI Lab inference akışı
- **Risk overlay:** auth enforcement, metrics exposure ve legacy Streamlit drift noktaları

### Önerilen Mermaid Şeması

```mermaid
flowchart LR
  U[Kullanıcı] --> W[Next.js Web]
  W --> Q[/api/quotes route]
  Q --> Y[Yahoo Finance]
  W --> R[/py-api rewrite]
  R --> A[FastAPI api/v1]
  A --> S[Scanner]
  A --> H[Auth & User Settings]
  A --> D[DRL / Models]
  A --> L[LLM Router]
  S --> DS[(data/shortlists)]
  H --> DB[(SQLite / PostgreSQL)]
  D --> MR[(models/registry.json)]
  L --> GP[Groq / Claude / Gemini]
  A -. intended .-> M[Metrics / Ready / Health]
```

### Kaynaklar, Transformlar, Cache, TTL, Event/Queue

| Alan | Durum |
|------|-------|
| Kaynaklar | Yahoo Finance, LLM sağlayıcıları, opsiyonel Polygon/Google/Alpaca |
| Transformlar | Scanner indikatörleri, DRL feature pipeline, LLM section parsing |
| Cache | `core.cache` L1/L2; scanner TTL 300s; web quote TTL 30s; LLM analyze TTL 1800s |
| TTL | market data 60s, feature 300s, model 3600s, web quote 30s |
| Event/queue | Resmi queue yok; `ThreadPoolExecutor` kullanımı var |
| Hata senaryoları | provider timeout, stale shortlist, missing env, auth enforcement eksikliği, install failure |

### Canlı Veri Doğrulama Adımları

1. `curl http://localhost:8000/api/v1/health`
2. `curl -I http://localhost:3001`
3. `curl "http://localhost:3001/api/quotes?symbols=AAPL,MSFT"`
4. `curl http://localhost:8000/api/v1/scan/shortlist/status`
5. Settings kaydı yazıp DB’de persisted olduğunu doğrula

### Acceptance Kriterleri

- Frontend root ve API health `200` dönmeli.
- `/py-api/scan`, `/py-api/models`, `/py-api/user/settings` contract’ları beklenen schema ile dönmeli.
- `/ready` ve `/metrics` canlıda erişilebilir olmalı.
- Auth gerektiren route’lar anonim erişime kapalı olmalı.
- Shortlist staleness alarmı ve model registry erişimi gözlemlenebilir olmalı.

**Tekrarlama Notu**

- **Ne nedir:** Bu bölüm bileşenler arası veri ve kontrol akışını gösterir.
- **Nasıl çalışır:** Web, hem doğrudan quote route’una hem de FastAPI rewrite yoluna ayrılır.
- **Nasıl test edilir:** health, quote, scan, settings ve model çağrıları canlı akış üstünden kontrol edilir.
- **Bir sonraki değerlendirme için not:** cache hit oranı, rewrite error rate ve LLM/provider timeout oranı ayrıca izlenmelidir.

---

## 5. Kritik Yol ve Go / No-Go Kararı

### Kritik Eksikler

| ID | Kritik Eksik | Etki | Olasılık | Sınıf |
|----|--------------|------|----------|-------|
| C1 | Kurulum zinciri kırık: `requirements.txt` temiz kurulumda başarısız, API runtime deps eksik | Çok yüksek | Yüksek | **Kritik** |
| C2 | Çalışan mimari ile README / Docker / CI / OpenAPI arasında drift var | Çok yüksek | Yüksek | **Kritik** |
| C3 | JWT auth dokümante edilmiş ama API router’larında enforcement yok | Çok yüksek | Yüksek | **Kritik** |
| C4 | `/ready` ve `/metrics` canlı uygulamada yok, monitoring yalnızca kütüphane seviyesinde | Yüksek | Yüksek | **Kritik** |
| C5 | Frontend test komutu varsayılan çalışmada stabil değil; E2E yok | Orta | Yüksek | Yüksek |
| C6 | Legacy Streamlit yüzeyi hâlâ CI ve Docker zincirini etkiliyor | Orta | Yüksek | Yüksek |

### Etki / Olasılık Matrisi

| | Düşük Olasılık | Orta Olasılık | Yüksek Olasılık |
|---|---|---|---|
| **Çok Yüksek Etki** | - | - | C1, C2, C3 |
| **Yüksek Etki** | - | - | C4 |
| **Orta Etki** | - | - | C5, C6 |

### Proje Düzeyi Puanlama

| Kriter | Puan |
|--------|------|
| Stabilite | 6.0 |
| Güvenlik ve Uyumluluk | 5.2 |
| Performans ve Ölçeklenebilirlik | 6.2 |
| Test Kapsamı ve Otomasyon | 5.7 |
| Bakım ve Dokümantasyon | 4.8 |
| Teknik Borç | 4.8 |
| **Ağırlıklı Toplam** | **5.7 / 10 — C** |

### Go / No-Go Kararı

**Karar: NO-GO**

**Gerekçe:** Kurala göre 3 veya daha fazla kritik eksik varsa No-Go verilmelidir. Bu incelemede en az 4 kritik eksik teyit edilmiştir: kurulum zinciri, mimari drift, auth enforcement eksikliği ve readiness/metrics eksikliği. Uygulama lokal olarak ayağa kalkıyor olsa da üretim güvenilirliği ve operasyonel kontrol seviyesi yayına hazır değil.

### Koşullu Go İçin Minimum Mitigasyonlar

1. Tek resmi runtime sözleşmesini tanımla ve README/CI/Docker/OpenAPI’yi buna hizala.
2. `requirements.txt` ve lock stratejisini düzelt; temiz kurulum + docker build kanıtı al.
3. Auth enforcement’i route bazında etkinleştir.
4. `/ready` ve `/metrics` rotalarını canlı API’ye bağla.

**Tekrarlama Notu**

- **Ne nedir:** Bu bölüm ürünün bugün neden yayına girmemesi gerektiğini açıklar.
- **Nasıl çalışır:** Kritik eksikler etki ve olasılığa göre sınıflandırılır; kurala göre karar verilir.
- **Nasıl test edilir:** Kritik eksikler kapatıldıktan sonra smoke, contract, security ve deploy testleri birlikte tekrar çalıştırılır.
- **Bir sonraki değerlendirme için not:** No-Go kararı ancak C1–C4 kapandıktan sonra yeniden gözden geçirilmelidir.

---

## 6. 2 Haftalık Onarım ve Test Planı

Detaylı tablo ayrı dosyada verilmiştir: `docs/audits/2026-04-16/repair_plan_2_weeks.md`

### Özet Öncelikler

| Öncelik | İş Paketi | Sonuç |
|---------|-----------|-------|
| P0 | Runtime contract consolidation | Tek giriş noktası ve güncel doküman |
| P0 | Dependency fix + clean install | Reproducible build |
| P0 | Auth enforcement | Protected API surface |
| P1 | Ready/metrics wiring | Canlı gözlemlenebilirlik |
| P1 | Frontend test stabilization | Güvenilir CI |
| P2 | Legacy Streamlit karar planı | Sadeleştirilmiş bakım yüzeyi |

### Uygulama Sırası ve Güncel Durum

| Sıra | İş Paketi | Neden Önce | Durum | Yapılan İş | Kalan Gap |
|------|-----------|------------|-------|------------|-----------|
| 1 | Runtime contract consolidation | Önce tek doğru giriş noktası tanımlanmalıydı | **Tamamlandı** | `start.sh`, `README.md`, `api/main.py`, CI smoke sözleşmesi `3001/8000` ve `/api/v1/health` + `/api/v1/ready` + `/api/v1/metrics` eksenine taşındı | `docker-compose.yml` içinde web servisi hâlâ `3000:3000`; legacy servisler aynı dosyada duruyor |
| 2 | Dependency fix + clean install | Diğer tüm işler reproducible build gerektiriyordu | **Tamamlandı** | `requirements.txt` API runtime bağımlılıklarıyla güncellendi, `lxml` ve `pandas` pinleri uyumlu hale getirildi, temiz sanal ortam kurulum testi başarıyla geçti | Henüz lock file yok; `requirements-*.txt` ailesi ayrıca sadeleştirilmeli |
| 3 | Auth enforcement | Açık yüzeyin önce yüksek riskli kısmı daraltılmalıydı | **Tamamlandı (ilk güvenli faz)** | Frontend’e login/register/session akışı eklendi; dashboard seviyesinde JWT-aware fetch katmanı kuruldu; trade, model activation, Optuna trigger, `scan`, `backtest`, `inference/run`, `ensemble`, `llm/analyze` route’ları JWT arkasına alındı; anonymous settings demo profile ile sınırlandı | Password reset, 2FA ve daha ince rol bazlı yetki matrisi henüz placeholder seviyesinde |
| 4 | Ready/metrics wiring | Ops görünürlüğü için health tek başına yeterli değildi | **Tamamlandı** | `/api/v1/ready` ve `/api/v1/metrics` canlı FastAPI uygulamasına bağlandı; `start.sh` gerçek ready probe ile doğrulandı | Alerting, scrape hedefi ve dashboard wiring henüz yok |
| 5 | Frontend test stabilization | CI güvenilirliği için varsayılan test komutu çalışmalıydı | **Tamamlandı** | Vitest worker pool `forks` olarak sabitlendi; `npm test` artık başarıyla geçiyor | Hâlâ tek aktif test dosyası var; E2E bulunmuyor |
| 6 | Legacy Streamlit karar planı | Kalan teknik borç ve compose karmaşası bununla çözülecek | **Taslak hazır** | Ayrı karar planı oluşturuldu: `docs/audits/2026-04-16/legacy_streamlit_decision_plan.md` | Root Dockerfile, legacy compose bağımlılıkları ve CI artık bu plana göre sadeleştirilmeli |

### Detaylı Gap Notları

1. **Runtime contract consolidation**
  `start.sh` artık gerçek kaynak doğrusu, fakat compose topolojisi ve root Dockerfile hâlâ legacy ile modern yüzeyi birlikte taşıyor.
2. **Dependency fix + clean install**
  Temiz kurulum kanıtı alındı; buna rağmen hash-locked bir çözüm yok. Yani kurulum bugün reproducible, fakat tedarik zinciri sertliği tam değil.
3. **Auth enforcement**
  Backend tarafında güvenli temel ve frontend session/JWT header akışı artık mevcut. Açık kalan kısım auth kapsamı değil, hesap yönetimi derinliği: password rotation, 2FA, role matrix ve self-service account actions.
4. **Ready/metrics wiring**
  Endpoint’ler canlıda çalışıyor. Eksik olan kısım scrape, dashboard, alarm ve SLO tablosu.
5. **Frontend test stabilization**
  Worker startup problemi çözüldü. Eksik olan kısım davranışsal kapsam: contract test ve E2E yok.
6. **Legacy Streamlit karar planı**
  Karar taslağı var, ama operasyonel etkisi ancak root Dockerfile, compose bağımlılıkları ve scanner/telegram servis bağları temizlenince ortaya çıkacak.

**Tekrarlama Notu**

- **Ne nedir:** Bu bölüm ilk 2 haftada yapılması gereken düzeltmeleri sıralar.
- **Nasıl çalışır:** P0 işleri önce release blocker’ları kaldırır, sonra kalite işleri gelir.
- **Nasıl test edilir:** Her iş paketi için kabul kriteri ve rollback adımı tanımlanır.
- **Bir sonraki değerlendirme için not:** Günlük burn-down ve risk register tutulmalıdır.

---

## 7. Kontrol Şablonları ve Otomatik Test Senaryoları

Detaylı checklist seti ayrı dosyadadır: `docs/audits/2026-04-16/checklists.md`

### Minimum Smoke Komutları

```bash
cd /workspaces/Borsa
bash start.sh
curl -sf http://localhost:8000/api/v1/health
curl -I http://localhost:3001
python3 -m pytest tests/test_prometheus.py tests/test_sentry.py -q
cd web && npx vitest run --pool=threads
```

### Minimum Contract Kontrolleri

```bash
curl -s http://localhost:8000/api/v1/health
curl -s "http://localhost:3001/api/quotes?symbols=AAPL,MSFT"
curl -s http://localhost:8000/api/v1/scan/shortlist/status
curl -s http://localhost:8000/api/v1/user/settings
```

**Tekrarlama Notu**

- **Ne nedir:** Bu bölüm operasyon ekibinin doğrudan kopyalayıp çalıştıracağı kontrol setlerini tanımlar.
- **Nasıl çalışır:** smoke → integration → contract → performance → security sıralı ilerlenir.
- **Nasıl test edilir:** her template aynı run id ile immutable şekilde çalıştırılır.
- **Bir sonraki değerlendirme için not:** komut setleri CI job’larına birebir çevrilmelidir.

---

## 8. Sonuç ve Executive Summary

Detaylı tek sayfalık özet ayrı dosyadadır: `docs/audits/2026-04-16/executive_summary.md`

### Mevcut Durum

- Ürün lokal olarak çalışıyor ve modern web + API yüzeyi var.
- Kod tabanı işlevsel açıdan güçlü; özellikle scanner, DRL ve auth modülleri ciddi yatırım barındırıyor.
- Operasyonel sözleşme tekilleştirilmediği için üretim hazırlığı yetersiz.

### En Kritik 3 Eksik

1. Kurulum ve dependency zinciri güvenilir değil.
2. Çalışan mimari ile dokümantasyon / CI / Docker / OpenAPI hizalı değil.
3. Auth enforcement ve readiness/metrics gibi production kontrolleri eksik.

### Önerilen İlk 3 Aksiyon

1. Tek resmi runtime ve port sözleşmesini tüm dosyalarda standardize et.
2. Dependency setini düzeltip temiz kurulum + docker build kanıtı al.
3. Protected route, readiness ve metrics wiring’i canlı API’ye ekle.

### Yayına Hazır mı?

**Hayır.** Bu denetim kapsamında sonuç **No-Go**’dur.

**Tekrarlama Notu**

- **Ne nedir:** Bu bölüm yönetici özetinin kısa versiyonudur.
- **Nasıl çalışır:** bulgular, riskler ve ilk aksiyonlar karar verici seviyesinde sıkıştırılır.
- **Nasıl test edilir:** ilk 3 aksiyon kapandıktan sonra tüm denetim kısa tur olarak tekrar edilir.
- **Bir sonraki değerlendirme için not:** yeniden değerlendirme en geç 2 haftalık onarım sprinti sonunda yapılmalıdır.
