# FinPilot — Productivity Stack & Tooling Research

**Tarih:** 2026-05-11
**Hazırlayan:** Principal Productivity Architect (Cowork sandbox)
**Versiyon:** 1.0
**Statü:** İnternet erişimi olmadan üretildi → eğitim verisi + FinPilot iç audit bağlamı tabanlı. Versiyon/fiyat detayları `[verify]` etiketi ile işaretli.

---

## 0. Bağlam ve Başlangıç Noktası

Audit raporundan FinPilot'un **şu an sahip olduğu** araçlar:

| Katman | Mevcut |
|---|---|
| Web | Next.js 16.1.6 + React 19 |
| API | FastAPI 0.135.1 + uvicorn |
| Worker / Scheduler | **APScheduler 3.11 (in-process)** |
| Cache | Redis 5.2 |
| DB | SQLite (default), Postgres optional, **Alembic YOK** |
| LLM | Multi-router (Groq + Claude + Gemini) — **ad-hoc, gözlemlenebilirlik yok** |
| Observability | Sentry SDK 2.31 + Prometheus + Grafana |
| CI/CD | GitHub Actions (test/lint/frontend/security/docker) |
| Container | Docker + docker-compose |
| Billing | Stripe (planlı, henüz değil) |
| Auth | PyJWT + bcrypt (dev-key fallback'i var) |
| Data | yfinance + Polygon + Tavily/DDG |
| Broker | alpaca-py (paper) |

FinPilot'un **gerçek boşlukları** (bu rapor bunlara odaklanır):

1. **LLM observability ve eval yok** — promptlar, maliyetler, hallucination'lar görünmüyor
2. **Experiment tracking yok** — DRL modelleri `models/registry.json` ile manuel
3. **Feature flags yok** — tier ayrımı (Basic/Pro/Edge) için kritik
4. **DB migration yok** — Alembic eksik
5. **Data quality kontratları yok** — Pydantic var ama veri pipeline tarafında değil
6. **Secrets management primitive** — `.env` dosyaları
7. **Background job sistemi APScheduler in-process** — restart=data loss, multi-worker scaling yok
8. **Admin paneli yok** — kullanıcı / abone / model yönetimi manuel
9. **Product analytics yok** — kim ne yapıyor görünmüyor
10. **Docs yok** — kullanıcıya gösterilecek API/help merkezi yok

Rapor bu **10 boşluğa** karşı tool önerileri üretir. "Popüler ama bize uymayanları" Tier 3/4'e atar.

---

## 1) YÖNETİCİ ÖZETİ

### En çok hızlandıracak ana kategori grupları

1. **LLM lifecycle stack** (gateway + observability + eval) — bizim hâlâ en gri katmanımız
2. **Background job + job orchestration** — APScheduler bizi production'da kıracak
3. **Feature flags + experiment system** — tier'lı ürün ve A/B test bunsuz olmaz
4. **DB migration + data quality** — Alembic + Pandera, ucuz ama kritik
5. **Internal admin tooling** — manuel SQL koşmayı bırakmak için

### En güçlü 10 araç/platform adayı

1. **LiteLLM** — multi-LLM proxy, ad-hoc router yerine
2. **Langfuse** — LLM trace + cost + prompt management (self-hosted veya cloud)
3. **Promptfoo** — LLM eval (regression test)
4. **Inngest** veya **Trigger.dev** — event-driven background jobs (APScheduler yerine)
5. **GrowthBook** — feature flags + A/B test (OSS)
6. **PostHog** — product analytics + session replay + flags (alternatif)
7. **Alembic** — DB migration (zaten standart, kurulmamış olması garip)
8. **Pandera** — data validation (light, pydantic dostu)
9. **MLflow** — DRL experiment tracking + model registry
10. **Doppler** veya **Infisical** — secrets management

### Hemen başlanması gereken 5 entegrasyon

| # | Araç | Niye hemen | Tahmini efor |
|---|---|---|---|
| 1 | **Alembic** | DB migration olmadan production'a çıkamayız | 0.5 gün |
| 2 | **Langfuse + LiteLLM** | LLM faturası + hata gri kutu, görünmeden ölçeklenmez | 1 gün |
| 3 | **GrowthBook** | Tier ayrımı (Basic/Pro/Edge) kanary deploy bunsuz olmaz | 0.5 gün |
| 4 | **Promptfoo (CI'a entegre)** | LLM regression — release güvenliği | 0.5 gün |
| 5 | **Pandera (yfinance/Polygon output)** | Gelen veri silently corrupt olduğunda sinyal de bozulur | 0.5 gün |

Toplam: 3 gün yatırım → 3 ay teknik borç önlenir.

---

## 2) Kategori Bazlı Harita

| Kategori | Amaç | Öne Çıkan Araçlar | FinPilot'te Kullanım |
|---|---|---|---|
| AI Coding Assistant | Geliştirme hızı | Claude Code (var), Cursor, Aider, Continue.dev | Solo geliştirici için 3x velocity |
| Repo Intelligence | Cross-file arama, refactor | Sourcegraph, Greptile, ast-grep | 1.4M satır arttıkça kritik |
| LLM Gateway | Multi-provider yönetimi, fallback, cache | LiteLLM, Portkey, Helicone | Mevcut ad-hoc router'ı değiştirir |
| LLM Observability | Trace, cost, prompt versiyonu | Langfuse, Phoenix, LangSmith | Şu an tamamen kör |
| LLM Eval | Hallucination + regression test | Promptfoo, DeepEval, Ragas | Release öncesi geçilmesi şart |
| Background Jobs | Restart-safe, retry'lı task çalıştırma | Inngest, Trigger.dev, Celery, Dramatiq, Arq | APScheduler yerine |
| Experiment Tracking | DRL run + model registry | MLflow, Aim, W&B | `models/registry.json` yerine |
| Feature Flags | Tier ayrımı + canary | GrowthBook, Unleash, PostHog, Flagsmith | Stripe tier'larıyla bağlı |
| Product Analytics | Funnel, retention, session replay | PostHog, Mixpanel, June | "Kim ne yapıyor" gri kutusu |
| Data Quality | Schema doğrulama, anomali | Pandera, Great Expectations, Soda | yfinance/Polygon kötü veri |
| DB Migration | Şema değişikliği versiyonlama | Alembic, Atlas, Bytebase | **kritik boşluk** |
| Internal Admin | Kullanıcı/abone/model UI | Streamlit (var), Tooljet, Appsmith, Retool | Manuel SQL'i bitir |
| Secrets | API key yönetimi | Doppler, Infisical, SOPS, 1Password CLI | `.env` dosyalarından çıkış |
| Error Tracking | Exception + replay | Sentry (var), Better Stack | Sentry'i AI-context ile genişlet |
| Observability (APM) | Metric + log + trace | Grafana stack (var), OpenTelemetry, Honeycomb | OTel'i merkez yap |
| Notification | İç alarmlar | Discord webhook, Slack, ntfy, Resend | Alert routing |
| Docs | API + help merkezi | Mintlify, Docusaurus, Nextra | Beta için açılış |
| Local Dev | Komut runner + env mgmt | Just, mise, direnv, pre-commit | `start.sh` modernizasyonu |
| CI/CD Helpers | Bağımlılık + cache | Renovate, BuildJet, Trunk.io | Maintenance burnout'u azalt |
| Vector DB | Memory / RAG | Qdrant, Weaviate, Chroma, pgvector | Tavily/DDG cache + agent memory |
| Hosting | Backend + worker deploy | Fly.io, Railway, Render, Coolify | Docker-compose'un üstüne |

---

## 3) Araç Detayları (Tier 1 öncelikli)

### 3.1 LiteLLM
- **Kategori:** LLM Gateway
- **Ana amacı:** OpenAI-uyumlu tek API arkasında 100+ provider; otomatik fallback, cost tracking, rate limit, retry, cache
- **FinPilot'te kullanım:** `llm_router.py`'deki Groq/Claude/Gemini multiplex'i değiştir. Tek `litellm.completion(model="groq/llama-3.1", fallbacks=["claude-haiku","gemini-flash"])` çağrısı yeter.
- **Entegrasyon:** Python paket olarak veya proxy server (Redis/Postgres state). Proxy mode + Postgres → kullanıcı bazında budget cap koyabilirsin.
- **Güçlü:** OSS (MIT), self-hostable, çok geniş model katalogu, Langfuse/Helicone callback'leri built-in
- **Zayıf:** Versiyonlama agresif (haftalık release), büyük dependency tree
- **Karar:** **Hemen dene (POC 1 gün)**, mevcut router'ı tedricen değiştir

### 3.2 Langfuse
- **Kategori:** LLM Observability + Prompt Management
- **Ana amacı:** Her LLM çağrısının trace'i, latency, token, cost, kullanıcı bazlı; prompt version control; LLM-as-judge eval
- **FinPilot'te kullanım:** `@observe` decorator ile FinSense, AI explanation, agent chains. PostgreSQL + ClickHouse self-host opsiyonu var.
- **Entegrasyon:** LiteLLM ile native (callback). Standalone Python SDK de var.
- **Güçlü:** OSS Apache-2.0, self-host kolay, OpenAI/Anthropic/Gemini tracing native, prompt CMS UI'ı temiz
- **Zayıf:** Self-host'ta ClickHouse operasyonu öğrenme eğrisi, küçük takım için cloud daha kolay
- **Karar:** **Hemen dene**, LLM faturası görünmeden ölçeklenemeyiz

### 3.3 Promptfoo
- **Kategori:** LLM Eval
- **Ana amacı:** YAML-based eval suite, regression test, prompt karşılaştırma, CI entegrasyonu
- **FinPilot'te kullanım:** CI'a koy → her prompt değişikliğinde "AI analysis quality" gold-set ile test. Hallucination scorer + grounded check (Tavily kaynaklarına atıfta bulunma).
- **Entegrasyon:** Node CLI, `promptfoo eval` GitHub Actions step
- **Güçlü:** OSS MIT, prompt diff UI, model karşılaştırma matrisi, custom assertion
- **Zayıf:** Node yığını eklenir (FinPilot zaten Next.js var, sorun değil)
- **Karar:** **Hemen ekle**, ilk 30 prompt için gold-set hazırla

### 3.4 Inngest (alternatif: Trigger.dev)
- **Kategori:** Background Jobs / Event-driven workflows
- **Ana amacı:** Restart-safe, durable, event-tetiklemeli işler. Retry, throttle, fan-out, sleep-until, conditional steps.
- **FinPilot'te kullanım:** Tarama, Telegram alert, DRL retrain pipeline, Stripe webhook handler. APScheduler in-process scheduling = restart'ta data kaybı.
- **Entegrasyon:** Python SDK var. Self-hosted veya cloud.
- **Güçlü:** Step-function semantics (multi-step durable workflows), great DX, OSS dev server
- **Zayıf:** Python SDK Node SDK'dan biraz geri kalıyor; Trigger.dev'in v3'ü Python first-class değil — Python ekibi için Inngest seçilmeli `[verify]`
- **Karar:** **POC yap**, sonra APScheduler'ı tedricen taşı

### 3.5 GrowthBook
- **Kategori:** Feature Flags + A/B test
- **Ana amacı:** Self-hosted feature flag platformu, SQL-based experiment analysis, % rollout, sticky bucketing
- **FinPilot'te kullanım:**
  - Tier-based feature gating: `feature("ai.debate.enabled", user)` → sadece Edge tier'a açık
  - Canary deploy: yeni signal engine değişikliği %5 → %25 → %100
  - A/B: "Bull/Bear debate UI vs liste UI" → conversion karşılaştır
- **Entegrasyon:** Python SDK + JS SDK. PostgreSQL backend.
- **Güçlü:** OSS MIT, SQL connector ile Bayesian/frequentist analiz, code-side basit
- **Zayıf:** UI yer yer çekirdek, mobile push uzantısı sınırlı
- **Karar:** **Hemen dene**, beta tier'ı bunsuz yönetilmez

### 3.6 PostHog (GrowthBook'a alternatif veya tamamlayıcı)
- **Kategori:** Product Analytics + Flags + Session Replay
- **Ana amacı:** Open-source PostHog stack: event tracking, funnel, retention, session replay, flags, surveys
- **FinPilot'te kullanım:** "Kim hangi sinyale tıkladı, kaç saniye sonra Stripe checkout'a gitti" → ürün karar tabanı
- **Entegrasyon:** JS snippet (Next.js) + Python SDK (FastAPI events)
- **Güçlü:** Tek araçta 5 ürün, self-hostable, generous free tier
- **Zayıf:** Self-host Kubernetes önerir, küçük ekip için cloud daha rasyonel
- **Karar:** **POC yap**, cloud free tier'da başla

### 3.7 Alembic
- **Kategori:** DB Migration
- **Ana amacı:** SQLAlchemy modellerinden migration üretme, versiyonlama, rollback
- **FinPilot'te kullanım:** Audit'te tespit edildiği gibi production'a Alembic'siz çıkamayız. Şu an manuel `CREATE TABLE` çıktısı = yarın "kullanıcı tablosuna 1 sütun ekle" demek production downtime.
- **Entegrasyon:** `alembic init`, `auto-generate revision`, CI step ekle (forward migration check)
- **Güçlü:** Python ekosisteminin de facto standardı, SQLite + Postgres ikisinde de çalışır
- **Zayıf:** SQLite'ta `ALTER` kısıtları (table rebuild gerekir) — workaround standart
- **Karar:** **Bugün ekle**

### 3.8 Pandera
- **Kategori:** Data Quality / Schema Validation
- **Ana amacı:** Pandas DataFrame'lere schema kontrol (column types, ranges, null'lar, custom checks) — `@pa.check_input` decorator
- **FinPilot'te kullanım:**
  ```python
  schema = pa.DataFrameSchema({
      "Open": pa.Column(float, pa.Check.greater_than(0)),
      "Volume": pa.Column(int, pa.Check.greater_than_or_equal_to(0)),
      "Close": pa.Column(float, pa.Check.less_than(1e6)),
  })
  @pa.check_input(schema, "df")
  def compute_indicators(df): ...
  ```
  yfinance / Polygon → Pandera kapısından geçer → silently corrupt veri sinyal mühendislerini soğukkanlı tutar
- **Entegrasyon:** pip install, 1 günlük öğrenme
- **Güçlü:** OSS MIT, çok ışık, Pydantic-benzeri ergonomi
- **Zayıf:** Great Expectations kadar derin profil/anomali değil — basit kontratlar için ideal
- **Karar:** **Hemen ekle**

### 3.9 MLflow
- **Kategori:** Experiment Tracking + Model Registry
- **Ana amacı:** Her PPO/RPPO run'ı için hyperparam, metric, artifact, model versiyonu kayıt
- **FinPilot'te kullanım:** `models/registry.json` yerine MLflow Model Registry. Her train run sharpe/drawdown grafiğiyle UI'da görünür.
- **Entegrasyon:** `mlflow.start_run()` + Stable-Baselines3 ile callback. SQLite veya Postgres backend.
- **Güçlü:** OSS Apache-2.0, sektör standardı, S3-compatible artifact store
- **Zayıf:** UI biraz eski; Aim daha modern ama küçük topluluk
- **Karar:** **Bu sprint ekle**

### 3.10 Doppler veya Infisical
- **Kategori:** Secrets Management
- **Ana amacı:** API key + secret rotation, env-per-environment, audit log
- **FinPilot'te kullanım:** `.env.example`'daki 13 değişken (FINPILOT_SECRET_KEY, GROQ_API_KEY, ALPACA keys, TELEGRAM_BOT_TOKEN) artık plaintext repo riski değil
- **Karşılaştırma:**
  - **Doppler** — SaaS, generous free tier, CLI mükemmel
  - **Infisical** — OSS self-host, daha genç, hızlı büyüyor
- **Entegrasyon:** `doppler run -- uvicorn main:app` veya `infisical run --env=prod`
- **Karar:** **POC ikisini de**, küçük ekip için Doppler daha az operasyon

---

### 3.11 İkinci Daire Araçlar (kısa)

#### Sourcegraph / Greptile (Repo Intelligence)
- 1.4M+ satıra çıkınca cross-file aramada AI assistant'ı çok güçlendirir
- Self-hosted Sourcegraph veya cloud Greptile
- **POC yap**, kullanıcı kaybetmeyecek seviyede premium

#### Mintlify (Docs)
- Markdown'dan profesyonel docs site. API reference auto-gen.
- FinPilot kullanıcı/dev docs için → Beta lansman engelini kaldırır
- **Şu hafta dene**

#### Renovate
- Bağımlılık update bot. Dependabot'tan daha güçlü gruplama + scheduling
- Self-hosted veya GitHub App. CI maintenance yükünü %70 azaltır.
- **Bugün kur**

#### Just (Command Runner)
- `make` yerine modern, cross-platform, env-aware
- `start.sh`'i modernize eder, README'deki "how to run" 10 satırı 1 satıra düşer
- **Hızlı kazanım**

#### Pre-commit
- Black, Ruff, mypy, eslint, prettier, security check'leri commit'ten önce
- Zaten Ruff var, formalize et
- **Bugün kur**

#### OpenTelemetry
- Sentry + Prometheus + Grafana var ama her biri kendi formatında. OTel ortak protokol.
- Geçiş tedrici, ama uzun vadede vendor lock-in'i bitirir
- **3 aylık plan**

#### Honeycomb veya Better Stack
- Distributed tracing — Sentry başlangıç seviyesinde
- Premium kademeye gerek olduğunda
- **İzle**

#### Vercel + Fly.io
- Vercel: Next.js native, web tarafı için en hızlı path
- Fly.io: FastAPI + worker + Redis tek platform, regional, ucuz
- **Production deploy'da değerlendir**

#### Tooljet / Appsmith / Streamlit
- Internal admin paneli. Streamlit zaten requirements'ta var (legacy UI?), Tooljet daha "internal CRM" karakterli
- Kullanıcı, abone, model, sistem ayarları → manuel SQL'i bitir
- **POC**

#### Qdrant (veya pgvector)
- Vector DB. Agent memory + Tavily/DDG cache + similarity-based "benzer karar" lookup
- pgvector zaten Postgres içinde olur → ekstra servis yok
- **Önce pgvector**, ölçek arttıkça Qdrant

#### Discord webhook / ntfy
- Internal alert sistemi. Sentry → Discord, Stripe → Discord, CI fail → Discord
- 30 dakikalık iş, eko sistem dışı çıkmaz
- **Bugün kur**

#### k6 / Locust
- Load test. API + scan endpoint için ölçek doğrulaması
- Beta öncesi bir kez koş, sonra ayda 1
- **Beta öncesi**

---

## 4) Stack Önerileri

### 4.1 Minimal Viable Productivity Stack (1 hafta yatırım, 3x velocity)

```
DEV
  Claude Code (var) + Aider/Cursor          ← AI coding
  Just + pre-commit + Renovate              ← local + CI maintenance
  Doppler                                    ← secrets
DATA
  Alembic                                    ← migrations
  Pandera                                    ← data contracts
LLM
  LiteLLM + Langfuse + Promptfoo            ← gateway + observability + eval
RUNTIME
  Inngest                                    ← jobs (APScheduler retire)
PRODUCT
  GrowthBook                                 ← flags + canary
OBSERVABILITY
  Sentry (var) + Prometheus/Grafana (var) + Discord webhook
DOCS
  Mintlify                                   ← public docs + API
```

Tahmini integrasyon süresi: **5–7 gün** solo. Aylık external cost (cloud kullanırsan): ~$0–50 (çoğu free tier).

### 4.2 Mid-tier Stack (3–4 hafta, beta-ready)

Minimal + ekleyin:

```
ANALYTICS
  PostHog (cloud free)                       ← funnel + session replay + flags
ML
  MLflow                                     ← experiment + model registry
ADMIN
  Tooljet veya genişletilmiş Streamlit       ← internal CRM
SEARCH/MEMORY
  pgvector                                   ← agent memory + RAG cache
HOSTING
  Fly.io (api+worker) + Vercel (web)         ← prod deploy
```

Aylık external cost: ~$50–150.

### 4.3 Premium / Level-up Stack (3 ay, takım ölçeği)

Mid-tier + ekleyin:

```
REPO INTEL
  Sourcegraph                                ← cross-file AI search
APM
  Honeycomb veya Datadog                     ← distributed tracing
LLM GATEWAY
  Portkey (LiteLLM'den geçiş)                ← enterprise grade
QUEUES
  Temporal (Inngest'ten kompleks workflow'lara)
STORAGE
  Qdrant cluster (pgvector'den)
SECURITY
  Snyk + GitGuardian                         ← supply chain + secret leak
DOCS+SUPPORT
  Mintlify + Plain veya Pylon                ← support inbox
```

Aylık external cost: ~$500–2.000 (5+ kişilik ekip senaryosu).

---

## 5) Tier Matrisi

| Araç | Kategori | Etki | Entegrasyon | Zaman Kazancı | Uzun Vadeli Değer | Karmaşıklık | **Tier** |
|---|---|---|---|---|---|---|---|
| Alembic | DB migration | 10 | 9 | 8 | 10 | 2 | **T1** |
| LiteLLM | LLM gateway | 9 | 9 | 8 | 9 | 3 | **T1** |
| Langfuse | LLM observability | 10 | 8 | 9 | 10 | 4 | **T1** |
| Promptfoo | LLM eval | 8 | 9 | 7 | 9 | 3 | **T1** |
| GrowthBook | Feature flags | 9 | 8 | 8 | 9 | 4 | **T1** |
| Pandera | Data quality | 8 | 10 | 7 | 8 | 2 | **T1** |
| Doppler / Infisical | Secrets | 9 | 9 | 6 | 9 | 3 | **T1** |
| Renovate | Deps | 8 | 10 | 8 | 8 | 1 | **T1** |
| Pre-commit | Code quality | 7 | 10 | 7 | 8 | 1 | **T1** |
| Just | Command runner | 6 | 10 | 7 | 7 | 1 | **T1** |
| Inngest | Background jobs | 9 | 7 | 8 | 9 | 5 | **T2** |
| MLflow | Experiment track | 8 | 8 | 6 | 9 | 4 | **T2** |
| PostHog | Product analytics | 9 | 8 | 7 | 9 | 5 | **T2** |
| Mintlify | Docs | 8 | 9 | 6 | 8 | 3 | **T2** |
| pgvector | Vector store | 7 | 9 | 6 | 8 | 3 | **T2** |
| Tooljet / Streamlit | Admin panel | 7 | 8 | 7 | 7 | 4 | **T2** |
| Fly.io | Hosting | 8 | 7 | 7 | 8 | 5 | **T2** |
| Discord webhook | Notifications | 6 | 10 | 7 | 6 | 1 | **T2** |
| Sourcegraph | Repo intelligence | 7 | 6 | 8 | 8 | 5 | **T3** |
| OpenTelemetry | APM standardı | 8 | 5 | 5 | 10 | 7 | **T3** |
| Honeycomb | Distributed trace | 7 | 6 | 6 | 8 | 6 | **T3** |
| Vercel | Web deploy | 7 | 9 | 6 | 7 | 3 | **T3** |
| k6 / Locust | Load test | 6 | 8 | 5 | 7 | 4 | **T3** |
| Aider / Cursor | AI coding | 8 | 9 | 9 | 6 | 2 | **T3** (preference) |
| Qdrant | Vector DB cluster | 6 | 5 | 5 | 7 | 7 | **T3** |
| Temporal | Durable workflows | 7 | 4 | 5 | 8 | 9 | **T4** |
| Datadog | APM premium | 8 | 6 | 6 | 7 | 6 | **T4** (maliyet) |
| Retool | Admin (proprietary) | 7 | 8 | 7 | 5 | 4 | **T4** (lock-in) |
| LangSmith | LLM obs (LangChain) | 6 | 7 | 6 | 5 | 4 | **T4** (lock-in) |
| New Relic | APM | 7 | 7 | 6 | 6 | 6 | **T4** |

**Tier sınıfları:**
- **T1** = Hemen başla (bu hafta)
- **T2** = POC yap (2–4 hafta içinde)
- **T3** = İzleme listesi (ihtiyaç doğunca)
- **T4** = Şimdilik gereksiz (lock-in / maliyet / overkill)

---

## 6) Hızlı Kazanımlar

### 1 günde uygulanabilecekler
- **Alembic init + ilk migration** — mevcut şemayı baseline olarak yakala
- **Doppler veya Infisical setup** — `.env` dosyalarını dışarı al
- **Renovate config (renovate.json)** — bağımlılık update bot'u aç
- **Pre-commit hooks** — ruff + mypy + eslint commit'ten önce
- **Just file** — `just start`, `just test`, `just deploy`, `just scan-now` shortcuts
- **Discord webhook** — Sentry alert + CI fail → Discord channel
- **Pandera kontratları (ilk 3)** — yfinance OHLCV + Polygon quote + Tavily news output

### 1 haftada uygulanabilecekler
- **LiteLLM proxy POC** — mevcut router'ı paralel çalıştır, sonuçları karşılaştır
- **Langfuse self-host (Docker)** — LiteLLM'den callback aktif
- **Promptfoo CI step** — ilk 20 prompt için gold-set
- **GrowthBook self-host** — `feature("debate.enabled")` ilk flag
- **MLflow tracking server** — bir sonraki PPO train run otomatik logla
- **pgvector** — Postgres'e eklenti olarak ekle, ilk 1000 doküman embed et

### 1 sprintte (2 hafta) uygulanabilecekler
- **Inngest entegrasyonu** — APScheduler job'larını tedricen taşı (önce non-critical)
- **PostHog (cloud)** — Next.js JS SDK + FastAPI events
- **Mintlify docs site** — `/docs` altında API reference + beta guide
- **Streamlit internal admin v2** — kullanıcı/abone/model yönetimi
- **Fly.io staging deploy** — production'a paralel staging env

---

## 7) Entegrasyon Fikirleri (Combo Reçeteleri)

### Combo 1: LLM Lifecycle Pipeline
```
Request → LiteLLM (gateway, fallback)
         → Langfuse (trace, cost log)
         → response
Daily CI: Promptfoo eval suite → fail → Slack alarm
Weekly: Langfuse dashboard → maliyet/p95 latency raporu
```
Bu üçlü birlikte: **LLM "siyah kutu" olmaktan çıkar.**

### Combo 2: Release Safety Net
```
PR merge → GitHub Actions
         → Promptfoo eval gate
         → Migration check (Alembic forward+backward)
         → Container build
         → Fly.io canary deploy
         → GrowthBook %5 rollout
         → PostHog conversion delta watch (24h)
         → otomatik %25 → %100 veya rollback
```
Bu zincir bizi "umuyorum çalışır" deploy'dan **kanıt-tabanlı progressive release'e** taşır.

### Combo 3: Research Acceleration
```
Notebook → MLflow.start_run()
         → PPO/RPPO trainer (Stable-Baselines3)
         → MLflow artifact (model + plots)
         → Promptfoo equivalent for DRL ("backtest gold set")
         → Model Registry (staging → production)
         → Inngest job: weekly auto-retrain
         → GrowthBook flag: "use model v23 for tier=Edge"
```
Her DRL deneyi **versiyonlu + karşılaştırılabilir + canlıya bağlı.**

### Combo 4: Data Contract Wall
```
yfinance / Polygon / Tavily fetch
   → Pandera schema check
   → bad rows quarantine table
   → Sentry breadcrumb
   → fallback provider tetikle (Polygon'a düşmüşse Yahoo)
```
Sinyal mühendisi bozuk veriyle uğraşmayı bırakır.

### Combo 5: Internal Operations Cockpit
```
Tooljet/Streamlit admin
   ← Langfuse trace links
   ← MLflow model versions
   ← GrowthBook flag toggles
   ← PostHog funnel embed
   ← Stripe customer link
```
Tek panel, 5 sistemi tek görünüm. Müşteri sorduğunda 3 saniyede cevap.

### Combo 6: Solo Developer 3x Loop
```
Cursor / Aider (AI coding)
   ← Sourcegraph repo intelligence
   ← MCP'le Linear/GitHub issue context
   ← pre-commit + ruff + mypy hızlı feedback
   ← Just shortcuts (start, test, deploy)
   ← Promptfoo CI guard
```
Tek geliştirici, 5 kişilik velocity.

---

## 8) Dikkat Edilmesi Gerekenler

### Vendor lock-in riskleri
- **LangSmith** — LangChain ekosistemine bağlar; LangChain kullanmıyorsanız Langfuse daha açık
- **Retool** — Görsel adım kod-dışı tutar; geçişte yeniden yazma
- **Datadog** — Maliyet hızla ölçeklenir, OTel'le geçişe izin verir ama hâlâ formatlama farkı
- **Vercel** — Next.js native, başka platforma taşımak istediğinde ISR/Edge Runtime farkları kanlı

**Anti-pattern hafifletmesi:** OpenTelemetry'i tüm yeni instrumentasyonun standardı yap, vendor SDK'ları üstüne ekle.

### Güvenlik / gizlilik riskleri
- **LLM gateway'leri** prompt'ları log'lar → PII filtreleme katmanı şart (LiteLLM'in `redact` özelliği)
- **Session replay** (PostHog) → maskeleme zorunlu; finansal veri görseli rakam siliciden geçmeli
- **Self-hosted Langfuse/Inngest** → kendi infra güvenliğin senin sorumluluğunda; cloud free tier'lar müşteri verisi için daha temiz başlangıç
- **MCP / agent tools** → her açtığın connector saldırı yüzeyi; least-privilege

### Fazla araç yükü (anti-pattern: tool sprawl)
- 3+ aynı iş yapan tool → karar paralizi
- Önerim: **her kategoride 1 winner**, alternatifi sadece kanıtlı eksiklikte değiştir
- Aylık bir "tool audit": son 30 günde hiç açılmayan tool'u devre dışı bırak

### Çakışan sistemler
- **PostHog (flag) vs GrowthBook** — ikisini birlikte alma, GrowthBook flag'i + PostHog analytics seç
- **MLflow vs W&B** — biri seç (MLflow OSS, W&B premium UI)
- **Sentry + Honeycomb** — Sentry exception tracking, Honeycomb tracing; çakışmazlar, **tamamlayıcılar**
- **APScheduler + Inngest** — geçiş süresinde dual-run kaçınılmaz, ama hedef Inngest

### Bakım maliyeti (gizli kuyrukta)
- Self-hosted her şey → 1 kişi sırf "operasyon" olur
- Küçük ekip için **cloud-first kural:** ücretsiz tier yetiyorsa cloud, ölçek arttıkça self-host
- "Self-host edebilirim" ≠ "self-host etmeliyim"

---

## 9) SON KARAR

İlk 14 gün için **kesinleşmiş eylem listesi:**

| Gün | İş | Etki |
|---|---|---|
| D1 | Alembic init + baseline migration | Production'a çıkmanın ön şartı |
| D1 | Doppler / Infisical secrets | `.env` riskini kapat |
| D1 | Renovate + pre-commit + Just | CI maintenance otomasyonu |
| D2 | LiteLLM POC (paralel router) | LLM gateway zemini |
| D3 | Langfuse self-host (Docker) | LLM trace + cost başlat |
| D4 | Promptfoo CI step + 20 gold prompt | Release guard |
| D5 | GrowthBook self-host + 3 flag | Tier ayrımı altyapısı |
| D6 | Pandera kontratları (3 endpoint) | Data quality wall |
| D7 | Discord webhook + Sentry → Discord | Alarm routing |
| D8 | MLflow tracking server + ilk train run | DRL kayıt zemini |
| D9 | pgvector + ilk RAG cache | Memory altyapısı |
| D10 | Inngest dev env + 2 job port | APScheduler taşıma başla |
| D11 | PostHog cloud + JS snippet | Funnel görünürlüğü |
| D12 | Mintlify docs iskelet | Public API ref + beta guide |
| D13 | Streamlit admin v2 | Internal ops cockpit |
| D14 | E2E retrospektif + Tier 1 closeout | Stack stabilize |

**Toplam external maliyet:** ~$0–50/ay (cloud free tier'lar) ilk üç ay.
**Toplam efor:** ~10 mühendis-günü.
**Beklenen kazanç:** 3 aylık teknik borç önlenmesi + beta lansman önceliği.

---

> "FinPilot için en doğru yaklaşım, araç sayısını artırmak değil; geliştirme, araştırma, kalite ve görünürlük akışlarını birlikte hızlandıran küçük ama güçlü bir productivity stack kurmaktır."

---

## Ek A — `[verify]` İşaretli Bilgiler

İnternet erişimi olmadığı için aşağıdakileri canlı doğrulaman lazım:
- Inngest Python SDK olgunluğu (v3'te first-class Python?)
- Langfuse self-host minimum requirements (ClickHouse zorunlu mu, Postgres-only build var mı?)
- Doppler vs Infisical free tier limitleri
- Promptfoo Node bağımlılığı (Python-only alternatifi: DeepEval)
- GrowthBook Python SDK API uyumluluğu
- Fly.io free tier 2026 durumu
- PostHog session replay financial-data masking yetenekleri
- Mintlify pricing (open source mu, freemium mi?)

## Ek B — Birinci Hafta İçin "Tek Komut" Setup

`justfile` taslağı:
```just
default: setup

setup:
    pip install alembic pandera mlflow litellm langfuse promptfoo-py
    npm install -g renovate
    pre-commit install
    alembic init alembic
    docker compose -f tools/langfuse.docker-compose.yml up -d
    docker compose -f tools/growthbook.docker-compose.yml up -d
    @echo "Stack scaffold ready. Next: configure secrets via 'doppler setup'"

start:
    doppler run -- uvicorn api.main:app --reload &
    cd web && npm run dev

scan-now:
    doppler run -- python -m inference.scan --output scan_$(date +%Y%m%d).csv

test:
    pytest -q && promptfoo eval --config evals/promptfoo.yaml

deploy-staging:
    fly deploy --config fly.staging.toml
```
