# FinPilot — Hızlı Canlıya Alma ve Gelir Başlatma Planı

| Alan | Değer |
|------|-------|
| **Proje** | FinPilot — AI-Powered Stock Analysis Platform |
| **Kısa Özet** | Rejim-farkındalığı olan DRL ensemble + teknik analiz + LLM açıklayıcı ile bireysel yatırımcıya karar-destek ve paper/live trading köprüsü sunan SaaS. Next.js 16 + FastAPI + PPO/RPPO + Groq/Claude/Gemini + Alpaca. |
| **Tarih** | 2026-04-22 |
| **Bağlam** | `FINPILOT_FULL_AUDIT_2026-04-22.md` denetiminin ardından go-to-market yol haritası. |
| **Hedef Pazar (varsayım)** | US equities takip eden DACH + TR + US bireysel yatırımcı; fiyat aralığı **aylık €19 – €79** (Basic/Pro/Edge) |
| **Beta Hedefi** | 50 aktif beta kullanıcı (2 hafta içinde); hedef persona: *"Elif — 32, yazılımcı, QQQ/SPY + 3–5 single-name pozisyon, haftada 30 dk analiz zamanı"* |
| **Uyumluluk Notu** | Ürün **yatırım tavsiyesi değildir** — araç/karar desteği. ToS + Risk Disclaimer zorunlu. GDPR: export/delete endpoint'leri. Alpaca paper default; live için ek onay akışı. |

---

## 1. MCS (Mission-Critical Systems) Doğrulama Raporu

### 1.1 MCS Fonksiyon Listesi

| # | Fonksiyon | Endpoint / Akış | Kritiklik |
|---|-----------|-----------------|-----------|
| 1 | Kullanıcı kaydı | `POST /api/v1/auth/register` + e-posta doğrulama | **P0** |
| 2 | Giriş / JWT | `POST /api/v1/auth/login`, `/refresh` | **P0** |
| 3 | Scanner tarama | `POST /api/v1/scan` → shortlist | **P0** |
| 4 | DRL inference | `POST /api/v1/inference` | **P0** |
| 5 | Ödeme (Stripe / Lemon Squeezy) | `POST /billing/checkout` — *yok, açık* | **P0** |
| 6 | Abonelik yaşam döngüsü | Stripe webhook → DB `subscriptions` | **P0** |
| 7 | Telegram alert | `telegram_alerts.send()` | **P1** |
| 8 | Paper trade | `POST /api/v1/trade` (Alpaca) | **P1** |
| 9 | Dashboard UI | `/dashboard/*` sayfaları | **P0** |
| 10 | Watchlist / Portfolio | `GET/POST /api/v1/user/watchlist` | **P1** |
| 11 | Logging / Audit | `core/audit.py` | **P1** |
| 12 | Monitoring / Alert | Prometheus + Grafana + Sentry | **P1** |
| 13 | Backup / Disaster Recovery | DB nightly backup — *yok, açık* | **P0** |
| 14 | GDPR export / delete | `GET /api/v1/user/export`, `DELETE` — *doğrulanmalı* | **P0** |
| 15 | Destek kanalı | Help widget / Intercom / mail — *yok, açık* | **P1** |

### 1.2 Smoke Test Sonuçları (hedef tablo — 48 saat içinde doldurulacak)

| Test | Beklenen | Gözlenen | Durum |
|------|----------|----------|-------|
| `/api/v1/ready` 200 | < 200 ms | Docker smoke yeşil (CI) | ✅ |
| `/api/v1/health` JSON | DB+cache+sentry OK | Doğrulanmalı | 🟡 |
| Auth login happy path | 200 + access_token | CI testi var (`test_auth.py`) | ✅ |
| `/api/v1/scan` AAPL | < 2 sn | Elle doğrulanmalı | 🟡 |
| `/api/v1/inference` AAPL | < 3 sn | Senkron; async önerisi açık | 🟡 |
| Stripe checkout | 3DS → webhook → DB | **YOK** | 🔴 |
| GDPR export/delete | 200 + zip / 204 | **Doğrulanmalı** | 🟡 |
| Grafana "FinPilot Overview" | Yeşil | Dashboard JSON var; import test edilmeli | 🟡 |
| Sentry prod DSN | event arrive | **Doğrulanmalı** | 🟡 |
| Daily backup script | `.dump` + S3 PUT | **YOK** | 🔴 |

### 1.3 Kritik Hatalar / Bloklayıcılar

- **B1 — Ödeme altyapısı yok.** `routers/billing` ve Stripe entegrasyonu planlanmamış. Gelir için P0.
- **B2 — Auth prod dev-key fallback (`auth/core._require_secret_key`).** Token forgery riski. Denetim raporundan devreden.
- **B3 — DB commit'e giriyor + Alembic yok.** PII sızma + schema drift.
- **B4 — DRL inference senkron.** API worker bloke, p95 latency riski.
- **B5 — GDPR export/delete doğrulanmadı.** AB beta için gerekli.
- **B6 — Backup/DR yok.** SQLite dosyası için bile nightly dump yok.
- **B7 — Destek kanalı yok.** Beta'da olmazsa olmaz.

### 1.4 MCS Geçiş Skoru

Mevcut **6/10** — temel çekirdek (auth+scan+inference) çalışır; monetizasyon (ödeme), veri uyumu (GDPR+backup) ve operasyonel destek (help) eksik.

---

## 2. Önceliklendirilmiş Gelir Modelleri

| # | Model | Uygulanma | Beklenen Gelir (ilk 90 gün) | Öncelik |
|---|-------|-----------|-----------------------------|---------|
| 1 | **SaaS Subscription (Basic/Pro/Edge)** | Stripe Checkout + Billing Portal; Basic €19/ay, Pro €49/ay, Edge €79/ay | 50 kullanıcı × €35 ort. MRR = **€1,750/ay** → 90g **~€3,500** | **P0** |
| 2 | **Lifetime Deal (LTD) — AppSumo tarzı** | Limited seat (ilk 100 × €199 one-time) Pro-özellikli | 40 × €199 = **€7,960** tek seferlik | **P0** |
| 3 | **Telegram Premium Signal Channel** | Ücretli kanal (Stripe veya Telegram Stars), €9/ay | 200 × €9 = **€1,800/ay** MRR | **P1** |
| 4 | **Annual Pre-pay (20% indirimli)** | Yıllık ödeme incentive'i | Abonelerin %30'u yıllık → **tek seferde € cashflow** | **P1** |
| 5 | **API / White-label** | Pro Plan üstü €199/ay — kurumsal / fintech | 2 pilot × €199 = **€400/ay** | **P2** |
| 6 | **Affiliate — Alpaca / Interactive Brokers** | Broker referral (açılan hesap başına €30–€80) | 20 dönüşüm = **€600–€1,600** tek sefer | **P2** |
| 7 | **Grant / Non-dilutive** | AWS Gründungsfonds (hazır dosya) + Exist / EU Horizon | **€50k–€200k** (2–6 ay) — gelir değil runway | **P1** (paralel) |

### 2.1 Tercih Edilen Sıralama (2 hafta içinde pilot)

1. **SaaS** (Stripe) — kaldıraç yüksek, tekrar eden gelir.
2. **LTD** — cash infusion + topluluk oluşturma.
3. **Telegram Premium** — düşük sürtünme, topluluk sinyali.

Diğerleri paralel pipeline'a alınır (affiliate + grant + API) — 30–90 gün penceresinde.

### 2.2 Uygulanma Adımları (SaaS — P0)

1. Stripe hesabı + ürün/price objeleri (3 plan).
2. `api/routers/billing.py` — checkout session + webhook handler (auth ile eşle).
3. `auth/db_backend.py` `subscriptions` tablosu (plan, status, current_period_end).
4. Next.js `/pricing` + `/dashboard/settings/billing`.
5. Feature gating: Basic (1 watchlist × 10 symbol), Pro (5 watchlist + DRL + LLM 100 req/ay), Edge (unlimited + Telegram premium + API).
6. Email: onboarding + trial ending + failed payment (Resend/Postmark).
7. Go-live banner + "Launch %25 off" kupon (ilk 72 saat).

### 2.3 Uygulanma Adımları (LTD — P0)

1. Ayrı landing `/lifetime` + seat sayacı (örn. `47/100 alınmış`).
2. Stripe one-time product €199.
3. Feature flag `lifetime=true` — Pro özelliklerini kalıcı aç.
4. AppSumo veya PitchGround başvurusu (2. hafta).
5. Twitter/LinkedIn + r/algotrading + Hacker News launch thread.

### 2.4 Uygulanma Adımları (Telegram Premium — P1)

1. Ayrı bot/kanal (veya Telegram Stars "Paid Post" ile test).
2. `/subscribe` komutu → Stripe Checkout → webhook → `/invite` link (expiring).
3. Sinyal frekansı: günlük top-3 + haftalık performance snapshot.
4. Risk disclaimer kanalın pinned mesajında.

---

## 3. Deney Matrisi

| ID | Hipotez | KPI | Süre | Başarı Eşiği | Sorumlu |
|----|---------|-----|------|--------------|---------|
| E1 | Landing'de "14 gün ücretsiz" CTA koyarsak sign-up conversion %30 artar | Visitor → Sign-up oranı | 10 gün | > %3.0 (mevcut ~%2.3 varsayımı) | Frontend |
| E2 | €19 Basic planı koyarsak ödeyen %40 Basic seçer, PMF sinyali artar | Paid mix %Basic | 14 gün | ≥ %35 Basic | Backend + Product |
| E3 | Onboarding'de DRL demo oynatırsak 7-gün aktivasyon %20 artar | 7-day active % | 14 gün | > %55 (mevcut %46 varsayımı) | Frontend + ML |
| E4 | Telegram premium €9 → €14 upsell yaparsak ARPU %30 artar | ARPU | 14 gün | ≥ €12 ARPU | Product |
| E5 | Stripe "failed payment" retry 3x + email yaparsak churn %25 azalır | Involuntary churn | 30 gün | < %1.5 / ay | Backend |
| E6 | LTD AppSumo launch 100 seat/14 gün satar | LTD seats sold | 14 gün | ≥ 60 seat | Product + Marketing |
| E7 | "Daily Top-3 Ideas" e-posta dijesti 40% open + 8% click | Open rate / CTR | 14 gün | OR ≥ 40%, CTR ≥ 8% | Growth |
| E8 | Reddit r/algotrading weekly "transparent performance" post 200+ upvote | Upvotes + sign-up spike | 14 gün | ≥ 150 upvote + 50 sign-up | Community |
| E9 | DACH pazar için DE çeviri + €-cinsinden fiyatla conversion %15 artar | DACH conversion | 14 gün | ≥ %1.5 DACH visit→paid | Frontend |
| E10 | Product Hunt launch #1–#3 Day ≥ 200 upvote | PH rank + traffic | 24 saat | ≥ #3, ≥ 500 sign-up | Founder |

### 3.1 A/B Test Yapısal Şablonu (hypothesis.md)

```
Hipotez:  Eğer [değişiklik] yaparsak, [metrik] % [X] artar.
Neden:    [bulgu / müşteri sinyali / analitik]
Ölçüm:    [event], [kohort], [kontrol vs variant]
Süre:     [gün]
Başarı:   [eşik]
Sonlanma: p < 0.1 veya min-sample 300/ko­hort
```

*CSV çıktı istenirse:* aynı tabloyu `experiment_matrix.csv` olarak export edebilirim — sadece söyleyin.

---

## 4. 2 Haftalık Uygulama Planı (Gün Gün)

### Hafta 1 — Kritik Bloklayıcıları Kapat + Ödeme Ayağa Kaldır

| Gün | Görev | Sorumlu | Kabul Kriteri |
|-----|-------|---------|---------------|
| **D1 (Çar)** | B2 fix: Auth `ENVIRONMENT=production` fail-fast guard | Backend | Prod env'de eksik key → boot fail, CI testi yeşil |
| **D1** | B3 fix: `data/*.db` .gitignore + rotate secret + history audit | DevOps | `git ls-files data/*.db` boş; secret rotate edildi |
| **D1** | Landing `/pricing` + Stripe hesabı + 3 product/price | Founder + FE | 3 plan görünür; Stripe test mode çalışır |
| **D2 (Per)** | `api/routers/billing.py` + webhook handler | Backend | `checkout.session.completed` → DB subscription; Stripe test mode e2e |
| **D2** | `auth` tablolarına `subscriptions` + feature gating middleware | Backend | Pro endpoint 402 for Basic |
| **D3 (Cum)** | Next.js `/dashboard/settings/billing` + upgrade modal | Frontend | Kullanıcı upgrade butonu → Stripe → dönüş OK |
| **D3** | B4 fix: `/api/v1/inference` arka plan + polling result endpoint (queue: Redis Streams) | Backend + Platform | p95 inference job < 3 sn; API worker bloke olmuyor |
| **D4 (Cts)** | Alembic init + baseline migration | Backend | `alembic upgrade head` CI'da yeşil |
| **D4** | Email (Resend) — welcome, trial-ending, failed-payment | Backend + Growth | 3 şablon + test send başarılı |
| **D5 (Paz)** | GDPR export/delete endpoint'leri + dashboard düğmesi | Backend | `/user/export` zip, `/user/delete` 204; log |
| **D5** | Nightly DB backup script (SQLite → S3 / B2 / local) | DevOps | `backup.sh` cron; restore drill başarılı |
| **D6 (Pzt)** | Beta davet e-postası + waitlist blast (mevcut `data/waitlist.json`) | Growth | 500+ e-posta gönderildi; open rate ölçümü |
| **D6** | Intercom / Crisp widget + mail destek inbox | Support | Dashboard'da help widget görünür; SLA 24h |
| **D7 (Sal)** | Game day: canary deploy + rollback prova | SRE | Rollback < 2 dk; smoke OK |

### Hafta 2 — Büyüme, Telegram Premium, LTD, Otomasyon

| Gün | Görev | Sorumlu | Kabul Kriteri |
|-----|-------|---------|---------------|
| **D8 (Çar)** | Telegram premium bot: `/subscribe` + paid channel flow | Integrations | Stripe test mode → invite link; revoke çalışır |
| **D8** | Frontend sert lint + CSP/HSTS + Sentry Web SDK | Frontend | securityheaders.com A+ |
| **D9 (Per)** | LTD landing `/lifetime` + seat counter + 100 seat satışa aç | Founder + FE | Stripe one-time product canlı |
| **D9** | OpenAPI export → TS client (`web/src/lib/api.ts` otomatik) | BE + FE | `npm run generate-api` yeşil |
| **D10 (Cum)** | Grafana SLO dashboard + 5 alert rule + PagerDuty/OpsGenie | SRE | Test alert yankılanıyor |
| **D10** | Daily Top-3 Ideas e-posta dijesti (cron) | Growth + ML | 07:30 UTC; mevcut abonelere |
| **D11 (Cts)** | Hacker News "Show HN" + Reddit launch threads hazır | Founder | Post'lar draft; tarih D13 belirlendi |
| **D11** | Product Hunt listing + tease tweet | Founder | PH draft onaylandı |
| **D12 (Paz)** | Canary Ring 2 genişletme (10 → 50 kullanıcı) | SRE + Product | Error rate < %1, p95 < 500 ms |
| **D13 (Pzt)** | **Public Launch** — PH + HN + Reddit + email blast | Herkes | PH #1–#3 hedefi; 500+ sign-up, ≥ 30 ödeyen |
| **D13** | Affiliate program Alpaca referral link | Growth | Dashboard'da "Açık Alpaca hesabı →" butonu |
| **D14 (Sal)** | Retro + KPI raporu + H3 backlog hazırlığı | Founder + PM | Rapor Slack'te; öncelikler belli |

**Paralel pipeline:** Grant başvurusu (AWS Gründungsfonds — dosyalar `grant_documents/` altında hazır) — hafta 1 sonunda gönderilir.

---

## 5. Teknik ve Operasyonel Checklist

### 5.1 CI/CD

- [ ] Frontend `next lint` sert gate (`|| true` kaldırıldı)
- [ ] Bandit/Safety `severity-level medium` → fail
- [ ] Trivy image scan job
- [ ] SBOM (syft) artefakt
- [ ] Contract test job aktif
- [ ] k6 performance smoke CI job (canary öncesi gate)
- [ ] Release branch + image tag `finpilot-api:vX.Y.Z` + GHCR push
- [ ] Dependabot / Renovate weekly

### 5.2 Monitoring

- [ ] Prometheus `/metrics` — `api_requests`, `api_latency`, `inference_latency`, `drl_errors`, `llm_cost`, `cache_hit_ratio`
- [ ] Grafana dashboards: Overview, DRL, Billing, Errors
- [ ] Alertmanager: 5 kritik kural (bkz. canary bölümü)
- [ ] Sentry DSN prod + `Environment=production` + release tag
- [ ] Structlog JSON log + (stretch) Loki/Promtail
- [ ] Uptime external probe (UptimeRobot / BetterStack) — /ready/health 1 dk interval

### 5.3 Ödeme (Stripe)

- [ ] Test mode ürün/price/webhook uçtan uca
- [ ] Live mode anahtar + restricted webhook secret
- [ ] `customer.subscription.*`, `invoice.*`, `checkout.session.completed` webhook'ları idempotent
- [ ] Failed payment retry 3 kez + dunning e-mail
- [ ] Fatura/PDF: Stripe varsayılan + Stripe Tax (EU VAT OSS)
- [ ] Refund policy sayfası + Terms & Privacy
- [ ] PCI-DSS: Stripe Checkout (kredi kartı bilgisi bizde asla tutulmaz)

### 5.4 Backup & DR

- [ ] Nightly `sqlite3 .dump | gzip | aws s3 cp` (veya Postgres `pg_dump`)
- [ ] Retention 30 gün + haftalık snapshot 12 hafta
- [ ] Restore drill aylık (game day)
- [ ] RPO < 24 saat, RTO < 4 saat

### 5.5 Destek

- [ ] Help widget (Crisp/Intercom) dashboard'da
- [ ] Destek kutusu `support@finpilot.app` + SLA 24h iş günü
- [ ] Public status page (statuspage.io / BetterStack)
- [ ] `docs/support/` FAQ + 10 en sık soru
- [ ] Runbook (`docs/runbooks/`) ilk 5 playbook

### 5.6 Yasal

- [ ] Terms of Service + Privacy Policy + Risk Disclaimer
- [ ] Cookie consent (AB kullanıcılar için)
- [ ] Impressum (Almanya yayını için yasal zorunluluk)
- [ ] DPA template (kurumsal müşteri için)
- [ ] "Not investment advice" disclaimer her DRL çıktısının altında
- [ ] GDPR: export/delete + data retention policy

### 5.7 Güvenlik (Launch Sertliği)

- [ ] WAF (Cloudflare) önde
- [ ] Rate limit endpoint-özel
- [ ] CORS whitelist
- [ ] CSP + HSTS + X-Frame-Options
- [ ] JWT revocation store (Redis)
- [ ] Secret vault (min: GitHub Actions encrypted secrets + production'da env injection)

---

## 6. KPI Dashboard ve Günlük Raporlama

### 6.1 Ana KPI'lar

| Kategori | KPI | Hedef (H2 sonu) |
|----------|-----|-----------------|
| **Growth** | Sign-up / gün | ≥ 30 |
| | Activation rate (D7 aktif) | ≥ %55 |
| | Waitlist → sign-up dönüşümü | ≥ %20 |
| **Revenue** | MRR | ≥ €1,200 |
| | Paid conversion (trial → paid) | ≥ %8 |
| | LTD seats | ≥ 60 / 100 |
| | ARPU | ≥ €28 |
| | Churn (monthly, involuntary) | < %2 |
| **Product** | Scan → Inference chain p95 | < 2.5 sn |
| | API error rate | < %1 |
| | DRL model Sharpe (30-day rolling) | ≥ 0.8 |
| | LLM cost / aktif kullanıcı | < €0.50/ay |
| **Ops** | Uptime | ≥ %99.5 |
| | Support median reply | < 4 saat |
| | Alert MTTA | < 10 dk |

### 6.2 Günlük Rapor Şablonu (Slack + e-posta)

```
📊 FinPilot Daily — YYYY-MM-DD

## Growth
- Sign-ups (24h): XX (WoW %X)
- D7 active: XX% (hedef 55%)
- Waitlist conversion: XX%

## Revenue
- MRR: €X,XXX (Δ€XXX)
- New paid: X | Churned: X
- LTD seats: XX/100

## Product
- API p95: XXX ms | Error rate: X.XX%
- DRL inference avg: XXX ms
- Top 3 signals (24h): AAPL long, NVDA long, TSLA flat

## Ops
- Uptime 24h: XX.XX%
- Alerts: 0 P1, X P2
- Support inbox: X open, median reply Xh

## En Kritik 3 Konu
1. ...
2. ...
3. ...
```

### 6.3 Dashboard Kurulumu

- **Grafana:** Overview + DRL paneli (mevcut JSON) + Billing paneli (Stripe → Prometheus exporter veya ClickHouse/Metabase).
- **Metabase (Postgres):** Growth + Revenue SQL dashboard'ları (Stripe sync).
- **PostHog veya Plausible:** Web analytics + funnel (Sign-up → Activate → Pay).

---

## 7. Canary Deploy ve Rollback Prosedürü

### 7.1 Canary Aşamaları

| Aşama | Kullanıcı | Süre | Başarı Eşiği |
|-------|-----------|------|--------------|
| **Ring 0** | iç (founder + 1 QA) | 4 saat | Smoke 100% pass |
| **Ring 1** | 10 beta | 24 saat | p95 < 600 ms, error rate < %2, 0 P1 alert |
| **Ring 2** | 50 waitlist | 48 saat | p95 < 500 ms, error rate < %1, NPS ≥ 30 |
| **GA** | tüm | — | Ring 2 eşikleri 48 saat sürdürüldü |

### 7.2 Metrik Eşikleri (Otomatik Rollback Tetikleyicileri)

| Metrik | Eşik (5 dk window) | Aksiyon |
|--------|--------------------|---------|
| `finpilot_api_error_rate` | > %2 | Auto rollback (CI job: `rollback.yml`) |
| `finpilot_api_latency_p95_ms` | > 1,000 | Alert → manuel karar |
| `finpilot_db_up` | == 0 | PagerDuty P1 + rollback |
| `finpilot_drl_errors_rate` | > %5 | Alert + DRL model previous_active'e |
| `stripe_webhook_fail_rate` | > %5 | PagerDuty P1 |
| `sentry_new_issues_per_min` | > 3 | Alert → manuel inceleme |

### 7.3 Rollback Prosedürü

```bash
# 1. API/Web image rollback
docker compose -f docker-compose.yml pull api web
export FINPILOT_RELEASE=<previous-known-good-sha>
make docker-up

# 2. DRL model rollback (registry pointer)
python scripts/populate_registry.py --activate <previous_model_id>

# 3. DB rollback (migration)
alembic downgrade -1

# 4. Kill-switch (live trading off)
export FINPILOT_LIVE=false && make docker-up-reload

# 5. Post-mortem başlat
cp docs/runbooks/postmortem_template.md docs/postmortems/$(date +%F)-<slug>.md
```

### 7.4 Acceptance (Ring → Ring geçişi)

- Tüm smoke testler yeşil
- 0 P1 alert (son 24 saat)
- Error rate < %1 (son 24 saat)
- En az 3 ödeyen müşteri aktif trial/paid (Ring 1'den itibaren)

---

## 8. Otomasyon Manifestosu

### 8.1 Agent Görevleri

```yaml
agent: finpilot-ops-agent
version: 0.2
run_id: "${UTC_TIMESTAMP}"

data_access:
  - repo: /workspace/Borsa (read)
  - db: postgres://.../finpilot (read; write sadece `agent_runs`)
  - mcp: stripe (read invoices, subscriptions)
  - mcp: slack (post #finpilot-alerts)
  - mcp: email (send digest via Resend)

tasks:
  - name: smoke_daily
    schedule: "*/30 * * * *"  # 30 dk
    cmd: "bash scripts/docker_smoke.sh"
    on_fail: slack_alert(channel="#finpilot-alerts")

  - name: performance_report
    schedule: "0 7 * * *"  # 07:00 UTC daily
    cmd: "python scripts/generate_report.py --audit"
    output: data/reports_cache/health_report_{date}.md

  - name: drl_backtest_regression
    schedule: "0 2 * * *"  # 02:00 UTC daily
    cmd: "python scripts/historical_backtest.py --last 30d"
    threshold: sharpe_delta < -0.2 → human_gate(gate="drl_model_rollback")

  - name: top3_digest_email
    schedule: "30 7 * * 1-5"  # 07:30 UTC hafta içi
    cmd: "python scripts/daily_inference.py --emit-email"

  - name: stripe_reconcile
    schedule: "0 3 * * *"
    cmd: "python scripts/stripe_reconcile.py"
    alert: mismatch > 3 → human_gate(gate="billing_audit")

  - name: churn_win_back
    schedule: "0 9 * * 1"  # Pzt 09:00
    cmd: "python scripts/churn_winback.py --send"

human_in_the_loop:
  - go_no_go_release
  - drl_model_promotion
  - live_trading_enable (paper → real)
  - secret_rotation
  - billing_audit (stripe_reconcile mismatch)
  - rollback_trigger

audit:
  immutable_run_id: true
  snapshot_hash: sha256
  results_path: data/audit_runs/{run_id}/

alerting:
  - channel: slack://finpilot-alerts
  - channel: pagerduty (P1 only)
```

### 8.2 İnsan-in-the-Loop Gate'leri

1. **Release GO/NO-GO** — her minor release öncesi
2. **DRL model promotion** — Ensemble'a yeni model eklemek
3. **Live trading enable** — paper'dan live'a geçiş (Alpaca)
4. **Secret rotation** — API keys ve FINPILOT_SECRET_KEY
5. **Billing audit** — Stripe reconcile sapma > 3 fatura
6. **Rollback trigger** — otomatik tetiklenmezse manuel

---

## 9. Üç Hızlı Gelir Fikri (Önceliklendirilmiş)

### 9.1 🥇 SaaS Subscription — Basic/Pro/Edge (Öncelik P0)

- **Beklenen gelir (90 gün):** ~€3,500 MRR (kümülatif)
- **Uygulanma süresi:** 5 gün (D1–D5)
- **Adımlar:** Stripe Checkout + webhook + feature gating + email otomasyonu + upgrade modal.
- **Neden hızlı:** Altyapı (auth + DB) zaten var; Stripe tek dış bağımlılık.
- **Risk:** GDPR/EU VAT; Stripe Tax aktive edilmeli.

### 9.2 🥈 Lifetime Deal (AppSumo tarzı) (Öncelik P0)

- **Beklenen gelir (90 gün):** 60 seat × €199 = **€11,940** (tek sefer cash)
- **Uygulanma süresi:** 3 gün (D9–D11)
- **Adımlar:** `/lifetime` landing + seat counter + Stripe one-time + feature flag + AppSumo/PitchGround başvurusu.
- **Neden hızlı:** Pazarlama kolay (scarcity + community); PMF testi.
- **Risk:** LTD, aktif kullanıcı maliyetini karşılamayabilir (LLM maliyeti) → LTD fiyatlama net maliyet analiziyle (LLM + Alpaca commission + hosting) yapılmalı.

### 9.3 🥉 Telegram Premium Signal Channel (Öncelik P1)

- **Beklenen gelir (90 gün):** 200 abone × €9 × 3 ay = **€5,400**
- **Uygulanma süresi:** 2 gün (D8)
- **Adımlar:** `/subscribe` → Stripe → invite link; günlük top-3 + haftalık performans snapshot.
- **Neden hızlı:** Telegram topluluğunun düşük sürtünmesi; ödeme akışı zaten var.
- **Risk:** Sinyal transparency (performans raporu) olmadan güven düşük → hafta sonu "Performance Thread" yayımlanmalı.

---

## 10. Go / No-Go Kriterleri ve Risk Mitigasyon Planı

### 10.1 Launch (D13) için Go Kriterleri

- [ ] MCS smoke testleri 100% geçti
- [ ] Stripe live mode webhook uçtan uca test edildi
- [ ] GDPR export/delete çalışıyor
- [ ] Nightly backup + restore drill başarılı
- [ ] Canary Ring 2 48 saat eşiklere uygun
- [ ] Terms & Privacy & Risk Disclaimer canlı
- [ ] Destek widget + status page aktif
- [ ] Sentry + Prometheus alert'leri test edildi (synthetic alert)
- [ ] Grafana SLO dashboard yeşil
- [ ] Auth prod-key guard devrede
- [ ] DB `.gitignore` + Alembic baseline

**Kural:** Listede **12/12 yeşil değilse NO-GO**.

### 10.2 Risk Mitigasyon Planı

| Risk | Olasılık | Etki | Mitigasyon |
|------|----------|------|-----------|
| Stripe webhook kaçıyor → sub aktive olmuyor | Orta | Yüksek | Idempotent + daily `stripe_reconcile.py` agent görevi |
| DRL model canlıda Sharpe negatif | Orta | Yüksek | 30-gün rolling Sharpe threshold alert → previous_active'e rollback |
| LLM maliyeti beklenen 3x aşıyor | Orta | Orta | Per-user daily budget + 429 soft-throttle; Groq-öncelik |
| Yoğun sign-up sonrası yfinance 429 | Yüksek | Orta | Polygon + Alpha Vantage yedek provider; L2 cache TTL artır |
| DDoS / script-kiddie | Orta | Orta | Cloudflare WAF + rate limit + challenge |
| GDPR şikayeti (AB kullanıcısı) | Düşük | Yüksek | Terms + export/delete canlı; Avukat review (1 sayfa memo) |
| Yasal: "yatırım tavsiyesi" iddiası | Düşük | Yüksek | "Not investment advice" disclaimer her output'ta + Terms |
| Kilit kişi (founder) hasta / yoğun | Orta | Orta | Runbook + 2. oncall; Stripe/DNS/GitHub owner + backup admin |
| Single SQLite tek node → veri kaybı | Orta | Yüksek | PG profile default; S3 nightly backup |
| Negatif review (Reddit / HN) | Yüksek | Düşük-Orta | Launch day'de founder aktif yanıtta; transparent performance |

---

## 11. Hemen Kullanılabilir Şablonlar

### 11.1 Beta Davet E-postası

```
Konu: FinPilot Beta Daveti — 14 Gün Ücretsiz + Launch %25 İndirim

Merhaba {FIRST_NAME},

FinPilot, DRL ensemble ve LLM açıklayıcılı karar desteği ile US equities
piyasasında daha hızlı, daha net kararlar almanızı sağlar.

Beta'ya katıldığınızda şunları alırsınız:
  • 14 gün ücretsiz erişim (kart bilgisi istenmez)
  • Launch haftası %25 indirim kuponu: LAUNCH25
  • Telegram'da özel beta-tester kanalı
  • Founder ile 30 dk feedback çağrısı (opsiyonel)

Katılmak için: https://finpilot.app/beta?ref={REF_CODE}

Soru & öneriye açığız — bu e-postayı yanıtlamanız yeterli.

Teşekkürler,
Meriç Başık
FinPilot Kurucusu
```

### 11.2 Landing Page CTA

```
Başlık:   Daha hızlı, daha net yatırım kararları — bugün deneyin.
Alt:      Rejim-farkındalığı olan DRL ensemble + günlük top-3 fikri
          · Ücretsiz 14 gün · Kurulum 5 dakika · Kart bilgisi gerekmez
CTA 1:    [Hemen Başla — Ücretsiz]
CTA 2 (ikincil):  Demo'yu izle (90 sn)
Sosyal kanıt:  "47/100 lifetime seat alındı · 320 aktif beta kullanıcı"
Disclaimer (altta): Yatırım tavsiyesi değildir. Karar desteği aracıdır.
```

### 11.3 A/B Test Hipotez Şablonu

```
Hipotez: Eğer {değişiklik} yaparsak, {metrik} % {X} artar.
Neden:   {bulgu / müşteri sinyali / analitik}.
Ölçüm:   {event}, {kohort}, {kontrol vs variant}.
Süre:    {gün}
Başarı:  {eşik} (p < 0.1 veya min-sample 300/ko­hort).
Sahip:   {isim}
Bitir:   {tarih + post-mortem notu}
```

### 11.4 Twitter / LinkedIn Launch Thread (İlk Post)

```
🚀 FinPilot canlıda!

Bireysel yatırımcıların US equities'te daha hızlı + daha net karar
vermesi için DRL ensemble + LLM açıklayıcı ile inşa ettik.

- Rejim-farkındalıklı 20 PPO/RPPO ajanı
- Günlük top-3 fikir (e-posta + Telegram)
- Alpaca paper trading köprüsü
- 14 gün ücretsiz → LAUNCH25 ile %25 indirim

https://finpilot.app

(1/8) 🧵
```

### 11.5 Stripe Webhook Event Taslağı (Test Plan)

```
1. checkout.session.completed → subscriptions INSERT + user.plan='pro'
2. customer.subscription.updated → subscriptions UPDATE (status, plan)
3. customer.subscription.deleted → subscriptions status='canceled'
4. invoice.payment_failed → email + retry 3x over 7d → cancel
5. invoice.paid → revenue_events INSERT + Slack notify
```

---

## 12. Kabul Kriterleri (Bu Planın)

- [x] MCS smoke testleri matrisi + açık bloklayıcı listesi (bölüm 1)
- [x] Önceliklendirilmiş gelir modelleri + uygulama adımları (bölüm 2)
- [x] Deney matrisi (10 deney, KPI, süre, eşik, sorumlu) (bölüm 3)
- [x] 2 haftalık gün-gün uygulama planı (bölüm 4)
- [x] Teknik + operasyonel checklist (bölüm 5)
- [x] KPI dashboard + günlük rapor şablonu (bölüm 6)
- [x] Canary + rollback prosedürü ve metrik eşikleri (bölüm 7)
- [x] Otomasyon manifestosu + insan-in-the-loop (bölüm 8)
- [x] 3 hızlı gelir fikri, beklenen gelir + süre (bölüm 9)
- [x] Go/No-Go kriterleri + risk mitigasyon (bölüm 10)
- [x] Şablonlar (beta e-posta, landing CTA, hipotez, thread, webhook) (bölüm 11)

---

## 13. Sonraki Adım

**Bu planı "play"e almak için:**
1. D1 görevlerini (Auth fail-fast + `.gitignore` + Stripe product creation) bugün atayın.
2. Waitlist e-postalarını (mevcut `data/waitlist.json` üzerinden) D6'da blastlayın.
3. D13 launch için PH / HN / Reddit post taslaklarını D10'da hazırlayın.
4. Rapor formatı için CSV deney matrisi isterseniz `experiment_matrix.csv` olarak export edebilirim — sadece söyleyin.

*Doküman tamamlandı. FinPilot 2026-04-22 — GTM Playbook v1.*
